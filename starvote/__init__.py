#!/usr/bin/env python3

##
## TODO
##
## * write a unit test that checks the code examples
##   in README.md are up to date
##     * confirms "example.py" and the output in README.md matches
##     * confirms the "multi-winner elections" cmdline works
##   (I keep breaking 'em.)
##
## * have starvote format import detect a recursion loop and complain
##   A imports B, B imports A, you blow your stack.
##
## * output
##     * alternate output format idea:
##         * make something more computer-readable.
##         * maybe just super-regular HTML, with classes and names to make it easy?
##     * allow displaying in floats
##     * restore printing the preference matrix (it's lurking in 1.x versions)
##

__doc__ = "An election tabulator for the STAR electoral system, and others"

__version__ = "2.0.6"

__all__ = [
    'Allocated_Score_Voting', # Method
    'allocated', # Method (nickname)
    'allocated_score_voting', # function
    'Bloc_STAR_Voting', # Method
    'bloc', # Method (nickname)
    'bloc_star_voting', # function
    'Method', # class for method metadata
    'methods', # maps string to Methods
    'load_starvote_file', # function
    'main', # function
    'Options', # class
    'predefined_permutation_tiebreaker', # tiebreaker class
    'parse_starvote', # function
    'on_demand_random_tiebreaker', # tiebreaker function
    'Reweighted_Range_Voting', # Method
    'rrv', # Method (nickname)
    'reweighted_range_voting', # function
    'Sequentially_Spent_Score', # Method
    'sss', # Method (nickname)
    'sequentially_spent_score', # function
    'STAR_Voting', # Method
    'star', # Method (nickname)
    'star_voting', # function
    'Tiebreaker', # class
    'tiebreakers', # maps string to tiebreakers
    'UnbreakableTieError', # exception class
    'UsageException', # exception class
    ]


LICENSE = """
starvote
Copyright 2023 by Larry Hastings

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""".strip()

import builtins
from collections import defaultdict
from contextlib import contextmanager
import csv
from fractions import Fraction
import enum
import itertools
from math import floor, log10
import os
import pathlib
import random
import re
import sys
import types


# use a function for this just so we don't clutter our namespace
def _version_float():
    # returns 3.09 for Python 3.9
    vi = sys.version_info
    return vi.major + (vi.minor / 100)

def _check_version(): # pragma: no cover
    exception = ImportError("unsupported version of Python (starvote requires dicts to preserve order)")
    version = _version_float()

    if version > 4:
        return # 4.0+ is okay... probably!  who knows!
    if version < 3:
        # python 2 is unsupported.  (how is this even running?!)
        raise exception

    # okay, we're on python 3.  what minor version?
    if version >= 3.07:
        return # 3.7+ is fine.
    if version < 3.06:
        raise exception # 3.5 and earlier is unsupported.

    # okay, version is exactly 3.6.
    # if we're using cpython, we're fine, as dicts are ordered in 3.6.
    if sys.implementation.name == "cpython":
        return
    raise exception

_check_version()


try:
    from enum import global_enum
except ImportError: # pragma: no cover
    def global_enum(fn):
        return fn



if _version_float() >= 3.10:
    from bisect import bisect_left
else: # pragma: no cover
    # bisect_left "key" parameter is new in 3.10.
    # we want to support older versions.
    # so we implement it ourselves
    import bisect
    def bisect_left(a, x, lo=0, hi=None, *, key=None):
        if key:
            a = [key(o) for o in a]
        if hi is None:
            hi = len(a)
        return bisect.bisect_left(a, x, lo, hi)


#
# See formatting_fractions_in_columns_of_text.txt
# for information on how starvote formats fractions.
#
def split_int_or_fraction_as_str(i):
    assert isinstance(i, (int, Fraction))

    if not i:
        return ('0', '', '', '')

    is_negative = i < 0
    if is_negative:
        i = -i

    # generate empty strings for either
    # the integer or the fraction, if they
    # are zero.
    #
    # note we already handled the entire number
    # being zero.
    #
    # so, in this section, we're guaranteed
    # that either integer will be nonzero,
    # or fraction will be nonzero.
    # (or both are nonzero).

    integer = int(i)
    fraction = i - integer
    if integer:
        integer_str = str(integer)
    else:
        integer_str = ''

    if fraction:
        fraction_str = str(fraction)
        numerator_str, _, denominator_str = fraction_str.partition('/')
        denominator_str = '/' + denominator_str
    else:
        numerator_str = denominator_str = ''

    plus_str = '+' if (integer_str and numerator_str) else ''
    if is_negative:
        if integer_str:
            integer_str = f'-{integer_str}'
        if numerator_str:
            plus_str = '-'
    return (integer_str, plus_str, numerator_str, denominator_str)

def measure_int_or_fraction_as_str(i):
    # returns *five* widths:
    #    merged_width, integer_width, plus_width, numerator_width, denominator_width
    assert isinstance(i, (int, Fraction))
    if not i:
        return (1, 0, 0, 0)

    integer_str, plus_str, numerator_str, denominator_str = split_int_or_fraction_as_str(i)

    integer_width = len(integer_str)
    plus_width = 1 if plus_str else 0
    numerator_width = len(numerator_str)
    denominator_width = len(denominator_str)

    return (integer_width, plus_width, numerator_width, denominator_width)

def max_widths(widths, update):
    max_integer_width, max_plus_width, max_plus_numerator_width, max_denominator_width, max_merged_width, max_no_plus_numerator_width = widths
    integer_width, plus_width, numerator_width, denominator_width = update

    max_integer_width = max(max_integer_width, integer_width)
    if plus_width:
        max_plus_width = 1
        max_plus_numerator_width = max(max_plus_numerator_width, numerator_width)
    else:
        max_no_plus_numerator_width = max(max_no_plus_numerator_width, numerator_width)
        merged_width = max(integer_width, max_no_plus_numerator_width)
        max_merged_width = max(max_merged_width, merged_width)
    max_denominator_width = max(max_denominator_width, denominator_width)

    return (max_integer_width, max_plus_width, max_plus_numerator_width, max_denominator_width, max_merged_width, max_no_plus_numerator_width)


def format_int_or_fraction(i, widths):
    assert len(widths) == 6
    integer_width, plus_width, plus_numerator_width, denominator_width, merged_width, no_plus_numerator_width = widths
    integer_str, plus_str, numerator_str, denominator_str = split_int_or_fraction_as_str(i)

    if plus_width:
        overall_width = integer_width + plus_width + plus_numerator_width + denominator_width

    if plus_str:
        strings = []
        formats = ('>', '<', '>', '<')
        for s, format, width in zip(split_int_or_fraction_as_str(i), formats, widths):
            strings.append(f"{s:{format}{width}}")
        s = "".join(strings)
    else:
        if not plus_width:
            integer_width = no_plus_numerator_width = merged_width
            overall_width = merged_width + denominator_width

        if integer_str:
            s = f"{integer_str:>{integer_width}}"
        else:
            s = f"{numerator_str:>{no_plus_numerator_width}}{denominator_str:<{denominator_width}}"
    return f"{s:<{overall_width}}"


class UnbreakableTieError(ValueError):
    def __init__(self, description, candidates, desired):
        super().__init__(description)
        self.candidates = tuple(candidates)
        self.desired = desired


class Tiebreaker:
    def initialize(self, options, ballots): # pragma: no cover
        pass

    def __call__(self, options, tie, desired, exception): # pragma: no cover
        pass

    def print_description(self, options, description):
        if not description: # pragma: no cover
            return
        if isinstance(description, str):
            options.print(description)
            return
        for line in description:
            options.print(line.strip())


class TiebreakerFunctionWrapper(Tiebreaker):
    def __init__(self, function):
        self.function = function

        doc = function.__doc__ or ""
        heading, _, description = doc.strip().partition("\n")
        description = description.strip()

        if description:
            heading = heading.strip()
            description = [line.strip() for line in description.strip().split('\n')]
        elif heading:
            raise ValueError("if tiebreaker function docstring isn't empty, it must have at least two lines")
        else:
            heading = description = None

        self.heading = heading
        self.description = description

    def __repr__(self):
        return f"TiebreakerFunctionWrapper(function={self.function})"

    def initialize(self, options, ballots):
        if self.heading:
            with options.heading(self.heading):
                self.print_description(options, self.description)

    def __call__(self, options, tie, desired, exception):
        return self.function(options, tie, desired, exception)


tiebreakers = {'None': None, 'none': None}

def _add_tiebreaker(o):
    tiebreakers[o.__name__] = o
    return o

@_add_tiebreaker
def on_demand_random_tiebreaker(options, tie, desired, exception):
    """
    On-demand random tiebreaker

    Tie-breaking winners will be chosen at random, on demand.
    """
    result = random.sample(population=tie, k=desired)
    with options.heading("On-demand random tiebreaker"):
        if options.verbosity:
            two_candidates = "two candidates" if desired == 2 else "one candidate"
            options.print(f"Choosing {two_candidates} from this list:")
            options.print_candidates(tie)
            if desired == 1:
                options.print(f"Randomly chose winner: {result[0]}")
            else:
                options.print(f"Randomly chose winners: {' and '.join(result)}")
    return result


@_add_tiebreaker
class predefined_permutation_tiebreaker(Tiebreaker):
    def __init__(self, candidates=None, *, description=None):
        if (not candidates) and description:
            raise ValueError("you can't specify a message unless you specify an iterable of candidates")
        self.candidates = candidates
        self._description = description
        self.description = None

    def __repr__(self): # pragma: no cover
        if self.description:
            contents = f"candidates={self.candidates} description='{self.description}'"
        else:
            contents = f"<not yet initialized>"
        return f"predefined_permutation_tiebreaker({contents})"

    def initialize(self, options, ballots):
        all_candidates = _candidates(ballots)
        if self.candidates is None:
            self.candidates = all_candidates
            random.shuffle(self.candidates)
            self.description = "Computing a random permutation of all the candidates."
        else:
            if not self.candidates:
                raise ValueError("no candidates")
            self_candidates_set = set(self.candidates)
            all_candidates_set = set(all_candidates)
            if self_candidates_set != all_candidates_set:
                missing = all_candidates_set - self_candidates_set
                extraneous = self_candidates_set - all_candidates_set
                assert missing or extraneous
                problems = []
                if missing:
                    problems.append("missing " + str(list(missing)))
                if extraneous:
                    problems.append("extraneous " + str(list(extraneous)))
                problems = ", ".join(problems)
                raise ValueError(f"candidates list doesn't exactly match ballot, {problems}")
            if self._description:
                self.description = self._description
            else:
                self.description = "Permutation was externally defined."

        if options.verbosity:
            with options.heading("Initializing ordered permutation tiebreaker"):
                self.print_description(options, self.description)
                options.print("Permuted list of candidates:")
                options.print_candidates(self.candidates, numbered=True)
                options.print("Tiebreaker candidates will be selected from this list, preferring candidates with lower numbers.")

    def __call__(self, options, tie, desired, exception):
        tie_set = set(tie)
        result = [candidate for candidate in self.candidates if candidate in tie_set][:desired]
        if options.verbosity:
            with options.heading("Predefined permutation tiebreaker"):
                two = "two " if desired == 2 else ""
                options.print(f"Choosing the earliest {two}of these candidates from the permuted list:")
                options.print_candidates(tie)
                if desired == 1:
                    options.print(f"Selected winner: {result[0]}")
                else:
                    options.print(f"Selected winners: {' and '.join(result)}")
        return result





_DEFAULT_MAXIMUM_SCORE = 5
_DEFAULT_PRINT = None
_DEFAULT_SEATS = 1
_DEFAULT_TIEBREAKER = predefined_permutation_tiebreaker
_DEFAULT_VERBOSITY = 0

class Options:
    """
    Utility class bundling up all the options for an election.

    Validates inputs, provides utility functions for printing
    and handling an unbreakable tie.
    """

    def __init__(self,
        method,
        *,
        maximum_score = _DEFAULT_MAXIMUM_SCORE,
        print = _DEFAULT_PRINT,
        seats = _DEFAULT_SEATS,
        tiebreaker = _DEFAULT_TIEBREAKER,
        verbosity = _DEFAULT_VERBOSITY,
        ):
        if not isinstance(maximum_score, int):
            raise ValueError(f"invalid maximum score {maximum_score}")
        if not isinstance(seats, int):
            raise ValueError(f"invalid seats {seats}")

        if method.multiwinner:
            if seats < 2:
                raise ValueError(f"seats must be 2+ when using {method.name}")
        else:
            if seats != 1:
                raise ValueError(f"seats must be 1 when using {method.name}")

        if verbosity:
            if print is None:
                print = builtins.print
        else:
            print = None

        self.method = method
        self.maximum_score = maximum_score
        self._print = print
        self.seats = seats
        self.tiebreaker = tiebreaker
        self.verbosity = verbosity

        self.headers = []
        self.header = None
        self.last_printed_header = None
        self.printed_headings = set()

        self.last_printed_ballot_count = None

    def __repr__(self): # pragma: no cover
        return f"<Options {self.method.name!r} maximum_score={self.maximum_score} seats={self.seats} tiebreaker={self.tiebreaker} verbosity={self.verbosity}>"

    @property
    def header(self):
        if self._header is None:
            self._header = ": ".join(self.headers)
        return self._header

    @header.setter
    def header(self, value):
        self._header = value

    def print(self, *a, sep=" ", end="\n"):
        if not self._print: # pragma: no cover
            return
        if not self._header:
            header = self.header
            if self.last_printed_header != header:
                self.last_printed_header = header
                continued = ""
                if header not in self.printed_headings:
                    self.printed_headings.add(header)
                else: # pragma: no cover
                    continued = " (continued)"
                self._print(f"[{header}{continued}]")
        self._print(" ", *a, sep=sep, end=end)

    def enter(self, header):
        self.headers.append(header)
        self.header = None

    def exit(self):
        self.headers.pop()
        self.header = None

    @contextmanager
    def heading(self, header):
        self.enter(header)
        yield None
        self.exit()

    @contextmanager
    def round_heading(self, header):
        self.enter(header)
        self.already_printed_first_advances = False
        self.printed_a_tie = False
        yield None
        self.exit()

    @contextmanager
    def subround_heading(self, header):
        self.enter(header)
        yield None
        self.exit()

    def initialize(self, ballots, *, messages=[]):
        if not ballots:
            raise ValueError("ballots is empty")

        maximum_score = self.maximum_score
        for ballot in ballots:
            for candidate, score in ballot.items():
                if not (candidate and isinstance(candidate, str)):
                    raise ValueError(f"invalid candidate {candidate!r}")
                if not isinstance(score, int):
                    raise ValueError(f"ballot[{candidate!r}] score is invalid, all scores must be integer, ballot={ballot} score={score}")
                if not (0 <= score <= maximum_score):
                    raise ValueError(f"ballot[{candidate!r}] score {score} isn't in the range 0..{maximum_score}, ballot={ballot} score={score}")

        if self.verbosity:
            self.enter(self.method.name) # stay in this heading forever
            self.print_ballot_count_if_changed(ballots)
            self.print(f"Maximum score is {maximum_score}.")

            if self.method.multiwinner:
                self.print(f"Want to fill {self.seats} seats.")

        for message in messages:
            self.print(message)

        if (type(self.tiebreaker) == type) and issubclass(self.tiebreaker, Tiebreaker):
            self.tiebreaker = self.tiebreaker()
        elif type(self.tiebreaker) == types.FunctionType:
            self.tiebreaker = TiebreakerFunctionWrapper(self.tiebreaker)

        if isinstance(self.tiebreaker, Tiebreaker):
            self.tiebreaker.initialize(self, ballots)

    def print_ballot_count_if_changed(self, ballots):
        ballot_count = len(ballots)
        if self.last_printed_ballot_count != ballot_count:
            remaining = "remaining " if self.last_printed_ballot_count is not None else ""
            self.last_printed_ballot_count = ballot_count
            self.print(f"Tabulating {ballot_count} {remaining}ballots.")

    def print_candidates(self, candidates, *, numbered=False):
        """
        Convenience function: prints the candidates using options.print.
        If numbered is true, prints the candidates in order, prepended with
          their index in the list (1-based).
        If numbered is false, prints the candidates, preferably in sorted
          order.
        """
        if numbered:
            width = _width(len(candidates))
        else:
            candidates = list(candidates)
            _attempt_to_sort(candidates)
        for i, candidate in enumerate(candidates, 1):
            if numbered:
                prefix = f"{i:>{width}}. "
            else:
                prefix = ''
            self.print(f"  {prefix}{candidate}")

    def print_result(self, first, second, tie, advance=False): # for scoring round
        print = self.print

        if not isinstance(advance, str):
            advance = "advance" if advance else "win"
            if not second:
                advance = f"{advance}s"

        if not tie:
            if second:
                print(f"{first} and {second} {advance}.")
                return
            print(f"{first} {advance}.")
            return

        still = "still " if self.printed_a_tie else ""
        self.printed_a_tie = True
        tie_description = f"{int_to_dashed_words(len(tie))}-way tie"
        if not first:
            print(f"There's {still}a {tie_description} for first.")
            return

        # tie for second
        if self.already_printed_first_advances:
            print(f"There's {still}a {tie_description} for second.")
            return

        print(f"{first} {advance}, but there's {still}a {tie_description} for second.")
        self.already_printed_first_advances = True

    def print_scores(self, scores, first, second, tie, *, advance=False, averages=None, no_preference=None):
        """
        averages is optional.  if specified, it must also be a sorted score dict.

        no_preference is optional.  if specified, it will be displayed as if it's a candidate.
        """
        print = self.print

        assert scores
        if no_preference is not None:
            scores = dict(scores)
            scores['No Preference'] = no_preference

        def annotation(candidate):
            if candidate == first:
                return ' -- First place'
            if candidate == second:
                return ' -- Second place'
            if tie and (candidate in tie):
                if first is None:
                    return ' -- Tied for first place'
                return ' -- Tied for second place'
            return ""

        candidate_width = 0
        score_widths = average_widths = (0, 0, 0, 0, 0, 0)

        # round 1: measure
        for candidate, score in scores.items():
            candidate_width = max(candidate_width, len(candidate))
            score_widths = max_widths(score_widths, measure_int_or_fraction_as_str(score))
            if averages:
                average_widths = max_widths(average_widths, measure_int_or_fraction_as_str(averages[candidate]))

        # round 2: print
        print = self.print
        average = ''
        for candidate, score in scores.items():
            score = format_int_or_fraction(score, score_widths)
            if averages:
                average = format_int_or_fraction(averages[candidate], average_widths)
                stripped = average.rstrip()
                delta = len(average) - len(stripped)
                spacer = ' ' * delta
                average = f" (average {stripped}){spacer}"
            a = annotation(candidate)
            print(f"  {candidate:{candidate_width}} -- {score}{average}{a}".rstrip())

        self.print_result(first, second, tie, advance=advance)

    def print_scores_and_averages(self, ballots, scores, first, second, tie, *, advance=False, no_preference=None, ballot_count=None):
        if ballot_count is None:
            ballot_count = len(ballots)
        averages = {candidate: Fraction(score, ballot_count) for candidate, score in scores.items()}
        self.print_scores(scores, first, second, tie, advance=advance, averages=averages, no_preference=no_preference)

    def election_result(self, winners, tie, *, raise_tie=True):
        if not (winners or tie):
            raise ValueError("winners and tie are both false, exactly one must be true")
        if winners and tie:
            raise ValueError("winners and tie are both true, exactly one must be true")

        if self.verbosity:
            if tie:
                if len(tie.candidates) == 2:
                    s = f"Tie between {tie.candidates[0]} and {tie.candidates[1]}."
                else:
                    candidates = list(tie.candidates)
                    last_candidate = candidates.pop()
                    s = f"Tie between {', '.join(candidates)}, and {last_candidate}."

                with self.heading("Unbreakable Tie"):
                    self.print(s)
            else:
                with self.heading(f"Winner{pluralizer(len(winners))}"):
                    for winner in winners:
                        self.print(f"{winner}")

        if tie and raise_tie:
            raise tie

        return winners


    def unbreakable_tie(self, text, candidates, desired):
        s = f"{self.header}: {text}"
        return UnbreakableTieError(s, candidates, desired)

    def break_tie(self, text, candidates, desired):
        if not isinstance(candidates, list):
            raise TypeError(f"candidates must be a list, candidates={candidates!r}")
        if len(candidates) < 2:
            raise ValueError(f"candidates must have at least two entries, candidates={candidates!r}")
        if len(candidates) <= desired:
            raise ValueError(f"candidates must have more than desired entries, candidates={candidates!r} desired={desired!r}")

        tie = self.unbreakable_tie(text, candidates, desired)

        if self.tiebreaker:
            result = self.tiebreaker(self, candidates, desired, tie)
            if not isinstance(result, list):
                raise TypeError(f"tiebreaker result must be a list, result={result!r}")
            if len(result) != desired:
                raise TypeError(f"tiebreaker result must have exactly {desired} elements, result={result!r}")
            return result

        raise tie


##
## A "score dict" maps candidates to scores.
## An individual ballot is a "score dict".
## A score dict is also used to store the result
## of summing all scores (e.g. a STAR score round).
##
## There are times when we want the scores in sorted
## order.  Python dicts retain insertion order,**
## so starvote can create "sorted" score dicts by
## creating a new dict and inserting the items in
## sorted order.  If you want to examine particular
## items (the first? the last? the top two?),
## convert the sorted score dict to a score list:
##    score_list = list(score_dict.items())
##
## ** CPython dicts have retained insertion order since
##    CPython 3.6, but it wasn't guaranteed until 3.7.
##    starvote relies on dicts retaining insertion order.
##    So we confirm this, in _check_version() at import time.

def _sort_score_list(score_list, *, reverse=False):
    """
    Sort a score list with the highest score first,
    and then by candidate.

    (You can always sort by candidate--they're a key in a dict!)
    """
    score_list.sort(key=lambda t: (-t[1], t[0]), reverse=reverse)

def _sort_score_dict(score_dict, *, reverse=False):
    """
    Sort a score dict with the highest score first.
    """
    score_list = list(score_dict.items())
    _sort_score_list(score_list, reverse=reverse)
    return dict(score_list)

def _attempt_to_sort(l):
    try:
        l.sort()
    except TypeError:
        pass

def _width(i):
    """
    Calculate the justification width of integer i.
    """
    adjustment = 1
    if i < 0:
        i = -i
        adjustment = 2
    if i < 1:
        return adjustment
    return floor(log10(i)) + adjustment

def _fraction_or_int(numerator, denominator=1):
    """
    Utility function with a sliiightly smelly API.

    With two arguments:
      f = Fraction(numerator, denominator),
      then falls through to the one-argument case.

    With one argument, numerator:
      f = numerator

      if f is a Fraction object, and
      f.denominator == 1, returns f.numerator.

      Else, if f is not an int, tries to convert
      f into an int, and if it succeeds and the
      resulting int is exactly equal to f, returns
      int(f).

      Otherwise returns f.

    Note: you can pass in a Fraction into
    either the numerator or denominator of the
    Fraction constructor, and it normalizes the
    value internally--the resulting Fraction
    will have integers for the numerator and
    denominator.  Thanks, Sjoerd and Jeffrey!
    """
    assert isinstance(numerator, (int, Fraction))
    assert isinstance(denominator, (int, Fraction))

    if denominator == 1:
        f = numerator
        is_fraction = isinstance(f, Fraction)
    else:
        f = Fraction(numerator, denominator)
        is_fraction = True

    if is_fraction and (f.denominator == 1):
        return f.numerator
    return f


def int_to_words(i, flowery=True):
    """
    Converts an integer into the equivalent English string.

    int_to_words(2) -> "two"
    int_to_words(35) -> "thirty-five"

    If the keyword-only parameter "flowery" is true,
    you also get commas and the word "and" where you'd expect them.
    (When "flowery" is True, int_to_words(i) produces identical
    output to inflect.engine().number_to_words(i).)

    Numbers >= 10*75 (one quadrillion vigintillion)
    are only converted using str(i).  Sorry!
    """
    if not isinstance(i, int):
        raise ValueError("i must be int")

    if (i >= 10**75) or (i <= -10**75):
        return str(i)

    is_negative = i < 0
    if is_negative:
        i = -i

    first_twenty = (
        "zero",
        "one", "two", "three", "four", "five",
        "six", "seven", "eight", "nine", "ten",
        "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
        )
    tens = (
        None, None, "twenty", "thirty", "forty", "fifty",
        "sixty", "seventy", "eighty", "ninety",
        )

    # leave a spot to put in "negative " if needed
    strings = ['']
    append = strings.append
    spacer = ''
    written = False

    # go-faster stripes shortcut:
    # most numbers are small.
    # the fastest route is for numbers < 100.
    # the next-fastest is for numbers < 1 trillion.
    # the slow route handles numbers < 10**66.
    if i >= 100:
        if i >= 10**12:
            quantities = (
            # note!        v  leading spaces!
            (10**63,      " vigintillion"),
            (10**60,    " novemdecillion"),
            (10**57,     " octodecillion"),
            (10**54,     " septdecillion"),
            (10**51,      " sexdecillion"),
            (10**48,      " qindecillion"),
            (10**45, " quattuordecillion"),
            (10**42,      " tredecillion"),
            (10**39,      " duodecillion"),
            (10**36,       " undecillion"),
            (10**33,       "   decillion"),
            (10**30,       "   nonillion"),
            (10**27,       "   octillion"),
            (10**24,       "  septillion"),
            (10**21,       "  sextillion"),
            (10**18,       " quintillion"),
            (10**15,       " quadrillion"),
            (10**12,          " trillion"),
            (10** 9,           " billion"),
            (10** 6,           " million"),
            (10** 3,          " thousand"),
            (10** 2,           " hundred"),
            )
        else:
            quantities = (
            # note!             v  leading spaces!
            (10** 9,           " billion"),
            (10** 6,           " million"),
            (10** 3,          " thousand"),
            (10** 2,           " hundred"),
            )

        for threshold, english in quantities:
            if i >= threshold:
                upper = i // threshold
                i = i % threshold
                append(spacer)
                append(int_to_words(upper, flowery=flowery))
                append(english)
                spacer = ', ' if flowery else ' '
                written = True

    if written:
        spacer = " and " if flowery else " "

    if i >= 20:
        t = i // 10
        append(spacer)
        append(tens[t])
        written = True
        spacer = '-'
        i = i % 10

    # don't add "zero" to the end if we already have strings
    if i or (not written):
        append(spacer)
        append(first_twenty[i])

    if is_negative:
        strings[0] = "negative "

    return "".join(strings)

def int_to_dashed_words(i):
    return int_to_words(i, flowery=False).replace(" ", "-")

def pluralizer(i):
    return "" if i == 1 else "s"


def _candidates(ballots):
    """
    Compute a list of all candidates voted for in ballots.
    """
    candidates = set()
    for ballot in ballots:
        candidates |= set(ballot)
    candidates = list(candidates)
    _attempt_to_sort(candidates)
    return candidates

##
## Utility functions for the high-level election system functions.
##

def _score_groups(scores, max_groups):
    """
    Iterate over a sorted scores dict, and group together
    candidates with the same score.
    Return a list of lists of candidates with the same score.

    Since a sorted scores dict sorts higher scores first,
    _score_groups also has higher scoring candidates first.

    In *every* case where we need score groups, we only
    need the first one or two.  We never need three or
    more.  max_groups limits the number of groups
    _score_groups generates.
    """
    score_groups = []
    score_group = None
    current_score_group_score = None
    # return an empty list if score_groups is 0
    for candidate, score in scores.items():
        if current_score_group_score != score:
            if len(score_groups) == max_groups:
                break
            score_group = []
            score_groups.append(score_group)
            current_score_group_score = score
        score_group.append(candidate)
    return score_groups


def _compute_first_from_scores(scores):
    """
    Determines the single winner from a sorted scores dict.
    If there's a tie, returns the tie.

    Returns a 2-tuple:
        (first, tie)

    If there's no tie for first, first will be the winner,
        and tie will be None.

    If there's a tie for first, first will be None,
        and tie will be a list.
    """
    score_group = _score_groups(scores, 1)[0]
    if len(score_group) == 1:
        return score_group[0], None
    return None, score_group

def _compute_first_and_second_from_score(scores, first):
    """
    Determines first and second place winners from a sorted scores dict.

    If first is not None, this is the already-established first place
    winner.

    Returns a 3-tuple:
        (first, second, tie)

    If there are winners for first and second, first and second
        will be candidates, and tie will be None.

    If there's a tie for second, first will be a candidate,
        second will be None, and tie will be a list.

    If there's a tie for first, first and second will be None,
        and tie will be a list.
    """
    if first:
        score_group = _score_groups(scores, 1)[0]
    else:
        score_groups = _score_groups(scores, 2)

        score_group_0 = score_groups[0]
        len_score_group_0 = len(score_group_0)

        if len_score_group_0 == 2:
            first, second = score_group_0
            return first, second, None
        if len_score_group_0 > 2:
            first = score_group_0
            return None, None, score_group_0

        first = score_group_0[0]

        score_group = score_groups[1]

    if len(score_group) == 1:
        return first, score_group[0], None
    return first, None, score_group



##
## Bare-metal score tabulators.
##
## API notes:
##     * All functions return a sorted score dict.
##     * All functions accept a "candidates" argument.
##       "candidates" must be either None or a container of
##       candidates.  When "candidates" is true, the function
##       will restrict the round to just those candidates.
##       It may iterate over "candidates" (possibly multiple times),
##       and/or it may perform membership testing.
##           * If "candidates" is true:
##               * It MUST contain ONLY candidates found in ballots.
##               * It MUST NOT contain repeats.
##           * If "candidates" is false, or the function
##             doesn't accept a "candidates" parameter,
##             the function will process all votes on every ballot.
##           * You are explicitly permitted to pass in an empty
##             container for "candidates", and this is equivalent
##             to passing in None.
##     * All functions guarantee that every candidate
##       examined will be in the returned score dict(s):
##         * If "candidates" is not None, the dict returned will
##           contain every candidate found in "candidates".
##           (len(candidates) == len(returned_dict))
##         * If "candidates" is None, the dict returned will
##           contain every candidate found in "ballots".
##     * These functions don't print anything.

def _scoring_round(ballots, candidates=None):
    """
    Score is the sum of all votes the candidate received.
    """

    if candidates:
        scores = {candidate: 0 for candidate in candidates}
        if not isinstance(candidates, (set, frozenset)):
            candidates = frozenset(candidates)
        for ballot in ballots:
            for candidate, score in ballot.items():
                if candidate in candidates:
                    scores[candidate] += score
    else:
        scores = {}
        for ballot in ballots:
            for candidate, score in ballot.items():
                if candidate not in scores:
                    scores[candidate] = 0
                scores[candidate] += score

    scores = _sort_score_dict(scores)

    return scores


def _maximum_score_count_round(ballots, maximum_score, candidates):
    """
    Score is the number of maximum_score votes each candidate
    received.
    """
    if len(candidates) == 2:
        # optimize for most common case
        candidate0, candidate1 = candidates
        score0 = score1 = 0
        for ballot in ballots:
            ballot_get = ballot.get
            if ballot_get(candidate0, 0) == maximum_score:
                score0 += 1
            if ballot_get(candidate1, 1) == maximum_score:
                score1 += 1
        scores = {candidate0: score0, candidate1: score1}
    else:
        scores = {candidate: 0 for candidate in candidates}
        for ballot in ballots:
            for candidate, score in ballot.items():
                if (candidate in candidates) and (score == maximum_score):
                    scores[candidate] += 1

    scores = _sort_score_dict(scores)

    return scores


def _preference_round(ballots, candidates):
    """
    Tabulates a "preference round".

    This function returns a 2-tuple:
        (scores, no_preference)

    no_preference is the number of ties in the
    head-to-head matchups.

    The score for each candidate is the number of
    head-to-head matchups they won:

    For every ballot, you compare the scores of every unique
    pair of candidates on that ballot.  (You compute A vs B
    once; you don't also compute B vs A.  Also, you can skip
    A vs A--that's always a tie!)  In each mini-contest, the
         with the higher score.  (If they
    have the same score, it's a tie.)  Add one to the score
    of the winner.

    Let's say there's only one ballot, and it looks like this:
        A = 5
        B = 4
        C = 3
        D = 4

    You'd compute the preferences as follows:
        A vs B: A=5 B=4, A>B, A wins
        A vs C: A=5 C=3, A>C, A wins
        A vs D: A=5 D=4, A>D, A wins
        B vs C: B=4 C=3, A>C, B wins
        B vs D: B=4 D=4, A>D, tie
        C vs D: C=3 D=4, A>D, D wins

    The score for this round would be:
        {'A': 3, 'B': 1, 'D': 1}

    And no_preference would be 1.
    """
    no_preference = 0
    if len(candidates) == 2:
        # Hand-optimized for two candidates,
        # because this case is super common.
        candidate0, candidate1 = candidates
        preference0 = preference1 = 0
        for ballot in ballots:
            ballot_get = ballot.get
            score0 = ballot_get(candidate0, 0)
            score1 = ballot_get(candidate1, 0)
            if score0 == score1:
                no_preference += 1
                continue
            if score0 > score1:
                preference0 += 1
            else:
                preference1 += 1

        preferences = [(candidate0, preference0), (candidate1, preference1)]
    else:
        # this relies on the fact that iterating over candidates
        # always yields the candidates in the same order.
        preferences = {candidate: 0 for candidate in candidates}
        for ballot in ballots:
            ballot_get = ballot.get
            for skip_until, candidate0 in enumerate(candidates):
                for i, candidate1 in enumerate(candidates):
                    if i <= skip_until:
                        continue
                    score0 = ballot_get(candidate0, 0)
                    score1 = ballot_get(candidate1, 0)
                    if score0 == score1:
                        no_preference += 1
                        continue
                    if score0 > score1:
                        winner = candidate0
                    else:
                        winner = candidate1
                    preferences[winner] += 1
        preferences = list(preferences.items())

    _sort_score_list(preferences)
    scores = dict(preferences)

    return (scores, no_preference)


def _star_round(options, ballots, candidates=None):
    """
    Execute one round of "STAR Voting".
    Used to compute a single-winner "STAR Voting" election,
    or a single round of a "Bloc STAR" election.

    Returns a single candidate, the winner.
    (Or, raises UnbreakableTieError).
    """

    verbosity = options.verbosity
    print = options.print


    @contextmanager
    def score_round_heading():
        with options.round_heading("Scoring Round"):
            if verbosity:
                print("The two highest-scoring candidates advance to the next round.")
            yield None

    @contextmanager
    def score_tiebreaker_1_heading():
        with options.subround_heading("First tiebreaker"):
            if verbosity:
                if first:
                    print("The candidate preferred in the most head-to-head matchups advances.")
                else:
                    print("The two candidates preferred in the most head-to-head matchups advance.")
            yield None

    @contextmanager
    def score_tiebreaker_2_heading():
        with options.subround_heading("Second tiebreaker"):
            if verbosity:
                with_the_most_votes = f"with the most votes of score {options.maximum_score}"
                if first:
                    print(f"The candidate {with_the_most_votes} advances.")
                else:
                    print(f"The two candidates {with_the_most_votes} advance.")
            yield None

    @contextmanager
    def automatic_runoff_heading():
        with options.round_heading("Automatic Runoff Round"):
            if verbosity:
                print("The candidate preferred in the most head-to-head matchups wins.")
            yield None

    @contextmanager
    def automatic_runoff_tiebreaker_1_heading():
        with options.subround_heading("First tiebreaker"):
            if verbosity:
                print("The highest-scoring candidate wins.")
            yield None

    @contextmanager
    def automatic_runoff_tiebreaker_2_heading():
        with options.subround_heading("Second tiebreaker"):
            if verbosity:
                with_the_most_votes = f"with the most votes of score {options.maximum_score}"
                print(f"The candidate {with_the_most_votes} wins.")
            yield None


    with score_round_heading():
        scores = _scoring_round(ballots, candidates)

        if len(scores) == 1:
            if verbosity:
                options.print("Only one candidate, they win.")
            return list(scores)[0][0]

        first, second, tie = _compute_first_and_second_from_score(scores, None)

        if verbosity:
            options.print_scores_and_averages(ballots, scores, first, second, tie, advance=True)

        if tie:
            with score_tiebreaker_1_heading():
                scores, no_preference = _preference_round(ballots, tie)
                first, second, tie = _compute_first_and_second_from_score(scores, first)
                if verbosity:
                    options.print_scores(scores, first, second, tie, no_preference=no_preference, advance=True)

            if tie:
                with score_tiebreaker_2_heading():
                    scores = _maximum_score_count_round(ballots, options.maximum_score, tie)
                    first, second, tie = _compute_first_and_second_from_score(scores, first)
                    if verbosity:
                        options.print_scores(scores, first, second, tie, advance=True)

                if tie:
                    needed = 1 if first else 2
                    winners = options.break_tie("{int_to_words(len(tie), flowery=False)}-way tie in Scoring Round", tie, needed)
                    if needed == 1:
                        second = winners[0]
                    else:
                        first, second = winners

    with automatic_runoff_heading():
        scores, no_preference = _preference_round(ballots, (first, second))
        first, tie = _compute_first_from_scores(scores)
        if verbosity:
            options.print_scores(scores, first, None, tie, no_preference=no_preference)

        if tie:
            with automatic_runoff_tiebreaker_1_heading():
                scores = _scoring_round(ballots, tie)
                first, tie = _compute_first_from_scores(scores)
                if verbosity:
                    options.print_scores(scores, first, None, tie)

            if tie:
                with automatic_runoff_tiebreaker_2_heading():
                    scores = _maximum_score_count_round(ballots, options.maximum_score, tie)
                    first, tie = _compute_first_from_scores(scores)
                    if verbosity:
                        options.print_scores(scores, first, None, tie)

                if tie:
                    winners = options.break_tie("{int_to_words(len(tie), flowery=False)}-way tie in Automatic Runoff Round", tie, 1)
                    first = winners[0]

    return first


class Method:
    def __init__(self, name, function, multiwinner):
        if not isinstance(name, str):
            raise TypeError(f"name should be str, is {name!r}")
        self.name = name

        if not callable(function):
            raise TypeError(f"function should be a callable, is {function!r}")
        self.function = function

        self.multiwinner = bool(multiwinner)

    def __repr__(self):
        multiwinner = " multiwinner" if self.multiwinner else ""
        return f"<Method '{self.name}' {self.function.__name__}{multiwinner}>"

methods = {}


def star_voting(ballots, *,
    maximum_score=_DEFAULT_MAXIMUM_SCORE,
    print=_DEFAULT_PRINT,
    tiebreaker=_DEFAULT_TIEBREAKER,
    verbosity=_DEFAULT_VERBOSITY,
    ):
    """
    Tabulates an election using STAR Voting:
        https://www.starvoting.org/

    Returns a list of results (which will only contain one winner).

    Takes one required positional parameter:
    * "ballots" should be an iterable of ballot dicts.

    Also accepts five optional keyword-only parameters:
    * "maximum_score" specifies the maximum score allowed
      per vote, default 5.
    * "print" is a function called to print output.
    * "seats" specifies the number of seats,
      for multiwinner elections.
    * "tiebreaker" specifies how to break ties;
      should be a tiebreaker function or Tiebreaker
      object.
    * "verbosity" is an int specifying how much output
      you want; 0 indicates no output, higher numbers
      add more output.
    """
    options = Options(
        STAR_Voting,

        maximum_score=maximum_score,
        print=print,
        seats=1,
        tiebreaker=tiebreaker,
        verbosity=verbosity,
        )
    options.initialize(ballots)

    try:
        winners = [_star_round(options, ballots)]
        tie = None
    except UnbreakableTieError as e:
        winners = None
        tie = e
    return options.election_result(winners, tie)


STAR_Voting = star = Method("STAR Voting", star_voting, False)
for _ in ('STAR Voting', 'star'):
    methods[_] = STAR_Voting



def bloc_star_voting(ballots, *,
    maximum_score=_DEFAULT_MAXIMUM_SCORE,
    print=_DEFAULT_PRINT,
    seats,
    tiebreaker=_DEFAULT_TIEBREAKER,
    verbosity=_DEFAULT_VERBOSITY,
    ):
    """
    Tabulates an election using Bloc STAR:
        https://www.starvoting.org/multi_winner

    Returns a list of results.

    Takes one required positional parameter:
    * "ballots" should be an iterable of ballot dicts.

    Also accepts five optional keyword-only parameters:
    * "maximum_score" specifies the maximum score allowed
      per vote, default 5.
    * "print" is a function called to print output.
    * "seats" specifies the number of seats,
      for multiwinner elections.
    * "tiebreaker" specifies how to break ties;
      should be a tiebreaker function or Tiebreaker
      object.
    * "verbosity" is an int specifying how much output
      you want; 0 indicates no output, higher numbers
      add more output.
    """
    options = Options(
        Bloc_STAR_Voting,

        maximum_score=maximum_score,
        print=print,
        seats=seats,
        tiebreaker=tiebreaker,
        verbosity=verbosity,
        )
    options.initialize(ballots)

    scores = _scoring_round(ballots)
    if len(scores) == seats:
        with options.heading(f"Round 1"):
            if options.verbosity:
                options.print(f"There are exactly {seats} candidates seeking {seats} seats.  Every candidate wins.")
        winners = list(scores)
        _attempt_to_sort(winners)
        return winners

    # go-faster stripe: don't pass in list of candidates
    # to _star_round until round 2.
    _candidates_waiting = set(scores)
    candidates = None

    try:
        winners = []
        for round in range(1, seats + 1):
            with options.heading(f"Round {round}"):
                winner = _star_round(options, ballots, candidates)
                winners.append(winner)
            if not candidates:
                candidates = _candidates_waiting
            candidates.remove(winner)

        tie = None
    except UnbreakableTieError as e:
        winners = None
        tie = e
    return options.election_result(winners, tie)

Bloc_STAR_Voting = bloc = Method("Bloc STAR", bloc_star_voting, True)
for _ in ('Bloc STAR Voting', 'bloc'):
    methods[_] = Bloc_STAR_Voting



def allocated_score_voting(ballots, *,
    maximum_score=_DEFAULT_MAXIMUM_SCORE,
    print=_DEFAULT_PRINT,
    seats,
    tiebreaker=_DEFAULT_TIEBREAKER,
    verbosity=_DEFAULT_VERBOSITY,
    ):
    """
    Tabulates an election using Allocated Score Voting:

        https://www.starvoting.org/technical_specifications

    (See "Appendix F: Technical Description and Python Code
    for Allocated Score Voting".)

    Returns a list of results.

    Takes one required positional parameter:
    * "ballots" should be an iterable of ballot dicts.

    Also accepts five optional keyword-only parameters:
    * "maximum_score" specifies the maximum score allowed
      per vote, default 5.
    * "print" is a function called to print output.
    * "seats" specifies the number of seats,
      for multiwinner elections.
    * "tiebreaker" specifies how to break ties;
      should be a tiebreaker function or Tiebreaker
      object.
    * "verbosity" is an int specifying how much output
      you want; 0 indicates no output, higher numbers
      add more output.

    Allocated Score Voting is (currently) the only
    proportional representation voting system authorized
    as a "Proportional STAR Voting" method by "STAR
    Voting Action 501c4".
    """

    options = Options(
        Allocated_Score_Voting,

        maximum_score=maximum_score,
        print=print,
        seats=seats,
        tiebreaker=tiebreaker,
        verbosity=verbosity,
        )

    original_ballot_count = len(ballots)
    hare_quota = _fraction_or_int(original_ballot_count, seats)

    options.initialize(ballots, messages=[f"Hare quota is {hare_quota}."])

    scores = _scoring_round(ballots)
    if len(scores) == seats:
        with options.heading(f"Round 1"):
            if options.verbosity:
                options.print(f"There are exactly {seats} candidates seeking {seats} seats.  Every candidate wins.")
        winners = list(scores)
        _attempt_to_sort(winners)
        return winners

    winners = []
    first = None

    # decorated_ballots is a list of lists.
    # each sublist contains four things with these indices:
    INDEX_SCORE = 0            # the
    key_score = lambda t: t[0] # fn to use as key parameter to sort
    INDEX_WEIGHT = 1           # the weight
    INDEX_WEIGHTED_BALLOT = 2  # the ballot with weighting applied
    INDEX_BALLOT = 3           # the original ballot

    decorated_ballots = [[None, 1, dict(ballot), dict(ballot)] for ballot in ballots]
    # "ballots" is just column 3 of this list.  we need a list
    # of just the ballots to pass in to _scoring_round.
    # sometimes (but not always) we throw away ballots in the
    # allocation round, which means that sometimes (but not always)
    # we need to recalculate this list during the loop.
    recalculate_weighted_ballots = True

    candidates = None

    try:
        for polling_round in range(1, seats+1):
            with options.round_heading(f"Round {polling_round}"):
                if recalculate_weighted_ballots:
                    weighted_ballots = [t[INDEX_WEIGHTED_BALLOT] for t in decorated_ballots]
                    recalculate_weighted_ballots = False

                scores = _scoring_round(weighted_ballots, candidates)
                first, tie = _compute_first_from_scores(scores)

                if candidates is None:
                    candidates = set(scores)

                if options.verbosity:
                    options.print_ballot_count_if_changed(weighted_ballots)
                    options.print("The highest-scoring candidate wins a seat.")
                    options.print_scores_and_averages(weighted_ballots, scores, first, None, tie, advance="wins a seat", ballot_count=original_ballot_count)

                if tie:
                    tie_winner = options.break_tie(f"{int_to_words(len(tie), flowery=False)}-way tie in Scoring Round", tie, 1)
                    first = tie_winner[0]

                winners.append(first)
                candidates.remove(first)
                if len(winners) == seats:
                    # success!
                    break

                with options.subround_heading("Ballot allocation round"):
                    quota = hare_quota

                    if options.verbosity:
                        options.print(f"Allocating {''.join(split_int_or_fraction_as_str(quota))} ballots.")

                    # Ballots that gave a zero vote to the winner
                    # go in non_supporters, ballots that gave a
                    # nonzero vote to the winner go in supporters.
                    supporters = []
                    non_supporters = []

                    for t in decorated_ballots:
                        score = t[INDEX_WEIGHTED_BALLOT].get(first, None)
                        if score:
                            t[INDEX_SCORE] = score
                            l = supporters
                        else:
                            l = non_supporters
                        l.append(t)

                    supporters.sort(key=key_score)

                    allocation_round = 0
                    while supporters:
                        allocation_round += 1
                        with options.subround_heading(f"Round {allocation_round}"):

                            if options.verbosity:
                                if allocation_round != 1:
                                    options.print(f"Remaining allocation quota is {quota}.")

                            # supporters is sorted by score, therefore the last entry has the highest score.
                            # note that this might not be an integer!
                            # after the first scoring round, it's likely there will be non-integer votes.
                            score = key_score(supporters[-1])

                            # bisect_left "key" parameter is new in 3.10.
                            # we want to support older versions.  we gotta do this the hard way.
                            score_start = bisect_left(supporters, score, key=key_score)

                            allocation_count = len(supporters) - score_start

                            if options.verbosity:
                                options.print(f"Allocating {allocation_count} ballot{pluralizer(allocation_count)} at score {score}.")
                            if allocation_count <= quota:
                                del supporters[score_start:]
                                quota = _fraction_or_int(quota - allocation_count)
                                # deleted some ballots, so we have to
                                # recalculate both weighted_ballots and decorated_ballots
                                recalculate_weighted_ballots = True
                                if not quota:
                                    break
                                continue

                            # this group has more supporters than we need to fill the quota.
                            # reduce every supporter's vote by the surplus, then keep them in play.
                            # since this fills the quota, we always exit the loop after this.
                            score_group = supporters[score_start:]

                            weight_reduction_ratio = _fraction_or_int(quota, allocation_count)
                            one_minus_weight_reduction_ratio = 1 - weight_reduction_ratio

                            if options.verbosity:
                                weight_reduction_ratio_as_percentage = float(100 * weight_reduction_ratio)

                                remaining = "remaining " if quota != hare_quota else ""
                                if len(score_group) == 1: # pragma: no cover
                                    these_ballots = "this ballot"
                                    their_weights = "its weight"
                                else:
                                    these_ballots = "these ballots"
                                    their_weights = "their weights"

                                options.print(f"This allocation overfills the {remaining}quota.  Returning fractional surplus.")
                                options.print(f"Allocating only {weight_reduction_ratio_as_percentage:2.2f}% of {these_ballots}.")
                                options.print(f"Keeping {these_ballots}, but multiplying {their_weights} by {one_minus_weight_reduction_ratio}.")

                                counts = defaultdict(int)
                                modified = 0

                            for t in score_group:
                                _, weight, weighted_ballot, ballot = t

                                starting_weight = weight
                                weight = _fraction_or_int(weight * one_minus_weight_reduction_ratio)
                                t[INDEX_WEIGHT] = weight

                                for candidate, score in ballot.items():
                                    weighted_ballot[candidate] = score * weight

                                if options.verbosity:
                                    key = (starting_weight, weight)
                                    counts[key] += 1
                                    modified += 1

                            for t in supporters:
                                _, weight, weighted_ballot, ballot = t
                                del weighted_ballot[first]
                                del ballot[first]

                            if options.verbosity:
                                counts = list(counts.items())
                                if len(counts) == 1:
                                    prefix = ""
                                else: # pragma: no cover
                                    options.print(f"Reweighted {modified} ballot{pluralizer(modified)}:")
                                    prefix = "   "
                                    # convert counts to list,
                                    # then sort by a) count, b) starting weight, c) ending weight, highest first.
                                    counts.sort(key=lambda t: (t[1], t[0][0], t[0][1]), reverse=True)

                                for key, count in counts:
                                    starting_weight, weight = key
                                    options.print(f"{prefix}{count} ballot{pluralizer(count)} reweighted from {starting_weight} to {weight}.")

                            break

                    if recalculate_weighted_ballots:
                        decorated_ballots = non_supporters + supporters

        _attempt_to_sort(winners)
        tie = None
    except UnbreakableTieError as e:
        winners = None
        tie = e
    return options.election_result(winners, tie)

Allocated_Score_Voting = allocated = Method("Allocated Score Voting", allocated_score_voting, True)
for _ in ('Allocated Score Voting', 'allocated'):
    methods[_] = Allocated_Score_Voting


def reweighted_range_voting(ballots, *,
    maximum_score=_DEFAULT_MAXIMUM_SCORE,
    print=_DEFAULT_PRINT,
    seats,
    tiebreaker=_DEFAULT_TIEBREAKER,
    verbosity=_DEFAULT_VERBOSITY,
    ):
    """
    Tabulates an election using Reweighted Range Voting:
        https://rangevoting.org/RRV.html

    Returns a list of results.

    Takes one required positional parameter:
    * "ballots" should be an iterable of ballot dicts.

    Also accepts five optional keyword-only parameters:
    * "maximum_score" specifies the maximum score allowed
      per vote, default 5.
    * "print" is a function called to print output.
    * "seats" specifies the number of seats,
      for multiwinner elections.
    * "tiebreaker" specifies how to break ties;
      should be a tiebreaker function or Tiebreaker
      object.
    * "verbosity" is an int specifying how much output
      you want; 0 indicates no output, higher numbers
      add more output.
    """

    options = Options(
        Reweighted_Range_Voting,

        maximum_score=maximum_score,
        print=print,
        seats=seats,
        tiebreaker=tiebreaker,
        verbosity=verbosity,
        )
    options.initialize(ballots)

    scores = _scoring_round(ballots)
    if len(scores) == seats:
        with options.heading(f"Round 1"):
            if options.verbosity:
                options.print(f"There are exactly {seats} candidates seeking {seats} seats.  Every candidate wins.")
        winners = list(scores)
        _attempt_to_sort(winners)
        return winners

    C = maximum_score
    weight = 1 # aka C/C
    # t = [weighted_ballot, ballot, C, weight]
    INDEX_WEIGHTED_BALLOT = 0
    INDEX_BALLOT = 1
    INDEX_C_PLUS_SCORES = 2
    INDEX_WEIGHT = 3
    decorated_ballots = [ [dict(b), dict(b), C, weight] for b in ballots ]
    ballots = [t[INDEX_WEIGHTED_BALLOT] for t in decorated_ballots]
    winners = []
    first = None
    candidates = None

    try:
        for polling_round in range(1, seats + 1):
            with options.round_heading(f"Round {polling_round}"):
                with options.subround_heading(f"Score round"):
                    scores = _scoring_round(ballots, candidates)
                    first, tie = _compute_first_from_scores(scores)

                    if candidates is None:
                        candidates = set(scores)

                    if options.verbosity:
                        options.print("The highest-scoring candidate wins a seat.")
                        options.print_scores_and_averages(ballots, scores, first, None, tie, advance="wins a seat")

                    if tie:
                        first = options.break_tie(f"{int_to_dashed_words(len(tie))}-way tie", tie, 1)[0]

                    winners.append(first)
                    candidates.remove(first)

                    if len(winners) == seats:
                        # success!
                        break

                with options.subround_heading("Reweighing Ballots"):
                    if options.verbosity:
                        counts = defaultdict(int)
                        modified = 0

                    for t in decorated_ballots:
                        weighted_ballot, ballot, C_plus_scores, weight = t

                        score = ballot.get(first, None)
                        if score is not None:
                            del ballot[first]
                            del weighted_ballot[first]
                            if score:
                                starting_weight = weight
                                C_plus_scores += score
                                weight = _fraction_or_int(C, C_plus_scores)

                                for candidate, score in ballot.items():
                                    if score:
                                        weighted_ballot[candidate] = _fraction_or_int(score * weight)
                                t[INDEX_C_PLUS_SCORES] = C_plus_scores
                                t[INDEX_WEIGHT] = weight
                                if options.verbosity:
                                    key = (starting_weight, weight)
                                    counts[key] += 1
                                    modified += 1

                    if options.verbosity:
                        counts = list(counts.items())
                        if len(counts) == 1:
                            prefix = ""
                        else:
                            options.print(f"Reweighted {modified} ballot{pluralizer(modified)}:")
                            prefix = "  "
                            # sort by a) count, b) starting weight, c) ending weight, highest first.
                            counts.sort(key=lambda t: (t[1], t[0][0], t[0][1]), reverse=True)

                        for key, count in counts:
                            starting_weight, weight = key
                            options.print(f"{prefix}{count} ballot{pluralizer(count)} reweighted from {starting_weight} to {weight}.")

        _attempt_to_sort(winners)
        tie = None
    except UnbreakableTieError as e:
        winners = None
        tie = e
    return options.election_result(winners, tie)

Reweighted_Range_Voting = rrv = Method("Reweighted Range Voting", reweighted_range_voting, True)
for _ in ('Reweighted Range Voting', 'rrv'):
    methods[_] = Reweighted_Range_Voting


def sequentially_spent_score(ballots, *,
    maximum_score=_DEFAULT_MAXIMUM_SCORE,
    print=_DEFAULT_PRINT,
    seats,
    tiebreaker=_DEFAULT_TIEBREAKER,
    verbosity=_DEFAULT_VERBOSITY,
    ):
    """
    Tabulates an election using Sequentially Spent Score:
        https://electowiki.org/wiki/Sequentially_Spent_Score

    Returns a list of results.

    Takes one required positional parameter:
    * "ballots" should be an iterable of ballot dicts.

    Also accepts five optional keyword-only parameters:
    * "maximum_score" specifies the maximum score allowed
      per vote, default 5.
    * "print" is a function called to print output.
    * "seats" specifies the number of seats,
      for multiwinner elections.
    * "tiebreaker" specifies how to break ties;
      should be a tiebreaker function or Tiebreaker
      object.
    * "verbosity" is an int specifying how much output
      you want; 0 indicates no output, higher numbers
      add more output.
    """

    options = Options(
        Sequentially_Spent_Score,

        maximum_score=maximum_score,
        print=print,
        seats=seats,
        tiebreaker=tiebreaker,
        verbosity=verbosity,
        )

    original_ballot_count = len(ballots)
    hare_score_quota = _fraction_or_int(original_ballot_count * maximum_score, seats)
    presentation_hare_score_quota = "".join(split_int_or_fraction_as_str(hare_score_quota))

    options.initialize(ballots, messages=[f"Hare score quota is {presentation_hare_score_quota}."])

    scores = _scoring_round(ballots)
    if len(scores) == seats:
        with options.heading(f"Round 1"):
            if options.verbosity:
                options.print(f"There are exactly {seats} candidates seeking {seats} seats.  Every candidate wins.")
        winners = list(scores)
        _attempt_to_sort(winners)
        return winners

    stars = maximum_score
    weight = 1
    # t = [weighted_ballot, ballot, stars, weight]

    INDEX_WEIGHTED_BALLOT = 0
    INDEX_BALLOT = 1
    INDEX_STARS = 2
    INDEX_WEIGHT = 3
    decorated_ballots = [ [dict(b), dict(b), stars, weight] for b in ballots ]
    weighted_ballots = [t[INDEX_WEIGHTED_BALLOT] for t in decorated_ballots]
    winners = []
    first = None
    candidates = None

    try:
        for polling_round in range(1, seats+1):
            with options.round_heading(f"Round {polling_round}"):

                scores = _scoring_round(weighted_ballots, candidates)
                first, tie = _compute_first_from_scores(scores)

                if candidates is None:
                    candidates = set(scores)

                if options.verbosity:
                    options.print_ballot_count_if_changed(ballots)
                    options.print("The highest-scoring candidate wins a seat.")
                    options.print_scores_and_averages(ballots, scores, first, None, tie, advance="wins a seat")

                if tie:
                    tie_winner = options.break_tie(f"{int_to_words(len(tie), flowery=False)}-way tie in Scoring Round", tie, 1)
                    first = tie_winner[0]

                winners.append(first)
                candidates.remove(first)

                if len(winners) == seats:
                    # success!
                    break

                with options.subround_heading("Ballot allocation round"):
                    winner_score = scores[first]
                    if not winner_score:
                        # all votes for candidate were zero.
                        # nobody has to give back any stars.
                        continue

                    weight_reduction_ratio = min( _fraction_or_int(hare_score_quota, winner_score), 1)
                    one_minus_weight_reduction_ratio = 1 - weight_reduction_ratio
                    have_surplus = weight_reduction_ratio < 1

                    if options.verbosity:
                        counts = defaultdict(int)
                        modified = 0
                        if have_surplus:
                            giving_back_surplus = "giving back surplus"
                            # no need to normalize this for presentation via split_fraction_or_int,
                            # one_minus_weight_reduction_ratio is guaranteed to be either 1 or a fraction < 1
                            reduction = f" * {one_minus_weight_reduction_ratio}"
                        else:
                            giving_back_surplus = "no surplus to give back"
                            reduction = ""

                        presentation_winner_score = "".join(split_int_or_fraction_as_str(winner_score))
                        options.print(f"Total score is {presentation_winner_score}, Hare score quota is {presentation_hare_score_quota}, {giving_back_surplus}.")
                        options.print(f"Reducing each ballot's stars by their vote{reduction}.")

                        remaining_decorated_ballots = []
                        remaining_weighted_ballots = []

                        allocated = 0
                        for t in decorated_ballots:
                            weighted_ballot, ballot, stars, weight = t

                            score = weighted_ballot.get(first, 0)

                            if score:
                                starting_stars = stars
                                star_reduction = score
                                if have_surplus:
                                    star_reduction = _fraction_or_int(star_reduction * weight_reduction_ratio)

                                stars = max(stars - star_reduction, 0)
                                if stars != starting_stars:
                                    if not stars:
                                        # remove, uh I mean "allocate", ballot
                                        # (don't append to remaining_decorated_ballots)
                                        allocated += 1
                                        continue

                                    t[INDEX_STARS] = stars

                                    weight = _fraction_or_int(stars, maximum_score)
                                    t[INDEX_WEIGHT] = weight

                                    for c, s in ballot.items():
                                        weighted_ballot[c] = s * weight

                                    if options.verbosity:
                                        key = (score, weight, starting_stars, stars)
                                        counts[key] += 1
                                        modified += 1

                                remaining_decorated_ballots.append(t)
                                remaining_weighted_ballots.append(weighted_ballot)

                        if allocated:
                            decorated_ballots = remaining_decorated_ballots
                            weighted_ballots = remaining_weighted_ballots

                        if options.verbosity:
                            if allocated:
                                options.print(f"Allocated {allocated} ballot{pluralizer(allocated)}.")

                            # convert counts to list,
                            counts = list(counts.items())
                            if len(counts) == 1:
                                prefix = ""
                            else: # pragma: no cover
                                options.print(f"Reweighted {modified} ballot{pluralizer(modified)}:")
                                prefix = "   "
                                # then sort by count then key, highest first.
                                counts.sort(key=lambda t: (t[1], t[0]), reverse=True)

                            for key, count in counts:
                                score, weight, starting_stars, stars = key
                                options.print(f"{prefix}{count} ballot{pluralizer(count)} voted {score}, stars reduced from {starting_stars} to {stars}, reweighted to {weight}.")


        _attempt_to_sort(winners)
        tie = None
    except UnbreakableTieError as e:
        winners = None
        tie = e
    return options.election_result(winners, tie)

Sequentially_Spent_Score = sss = Method("Sequentially Spent Score", sequentially_spent_score, True)
for _ in ('Sequentially Spent Score', 'sss'):
    methods[_] = Sequentially_Spent_Score


def election(method, ballots, *,
    maximum_score=_DEFAULT_MAXIMUM_SCORE,
    print=_DEFAULT_PRINT,
    seats=_DEFAULT_SEATS,
    tiebreaker=_DEFAULT_TIEBREAKER,
    verbosity=_DEFAULT_VERBOSITY,
    ):
    """
    Tabulates an election.  Returns a list of results.

    Takes two required positional parameters:
    * "method" should be a string or a Method object.
    * "ballots" should be an iterable of ballot dicts.

    Also accepts five optional keyword-only parameters:
    * "maximum_score" specifies the maximum score allowed
      per vote, default 5.
    * "print" is a function called to print output.
    * "seats" specifies the number of seats,
      for multiwinner elections.
    * "tiebreaker" specifies how to break ties;
      should be a tiebreaker function or Tiebreaker
      object.
    * "verbosity" is an int specifying how much output
      you want; 0 indicates no output, higher numbers
      add more output.
    """

    if isinstance(method, str):
        if method not in methods:
            raise ValueError(f"undefined method '{method}'")
        method = methods[method]
    if not isinstance(method, Method):
        raise TypeError(f"method is {method}, must be str or Method")

    extra_kwargs = {}
    if method.multiwinner:
        extra_kwargs['seats'] = seats

    return method.function(
        ballots,

        maximum_score=maximum_score,
        print=print,
        tiebreaker=tiebreaker,
        verbosity=verbosity,

        **extra_kwargs
        )



def parse_starvote(starvote, *, path=None):
    """
    Parses a custom election text format called "starvote format".
    Returns a kwargs dict usable for running an election, e.g.
        result = election(**parse_starvote(s))

    parse_starvote takes one required parameter: starvote, which
    must be a "starvote format" election string.  parse_starvote
    parses the string, runs the election, and returns the result.
    You may also pass in a keyword-only parameter "path", which
    should represent the filename if the starvote format text
    was loaded from a file; if specified, it'll be included in
    exceptions, for context.

    starvote format looks kind of like INI format, but isn't exactly the same.

    It's a line-oriented format.
    Leading and trailing whitespace per-line is ignored (and stripped).
    Lines that start with '#' are comments.
    Empty lines and comments are mostly ignored.

    Non-empty lines that aren't comments are either "assignments",
    "pragmas", or "sections".

    A line that starts with '[' and ends with ']' defines a
    "section".  You specify the name of the section between
    the square brackets.  You can only specify a section once.
    Only two sections are supported: "options" and "ballots".

    A "pragma" line ends with a colon (':').  Pragma lines are
    free-form; currently there's only one defined pragma.
    (When parsing a line, pragma take precedence over assignment.)

    An "assignment" line must contain an equals sign ('=');
    the text before the equals sign is the "name", and the text
    after the equals sign is the "value".

    Normally the value in an assignment is simply a string.
    However, in some sections, a value can also be a *list*
    of strings.  If the value is an opening square bracket "[",
    this starts "list mode":
    * The value in this assignment will be a list.
    * List mode ends when it encounters a line containing
      just a closing square bracket ("]").
    * Empty lines and comments are completely ignored.
    * All other lines are appended to the list as strings.

    The "options" section specifies how to run the election.
    On an assignment line, the name maps to a parameter to the
    starvote.election function.  Here are all the supported names:
        maximum score = <integer>
        method = <string>
        seats = <integer>
        verbosity = <integer>
        tiebreaker = <list>|<string>
    A starvote file can specify each of these options a maximum
    of once.

    The "tiebreaker" is slightly special.  It can either be a
    string, or a list of strings.  If "tiebreaker" is a string,
    this must be the name of a starvote module tiebreaker
    (found in the "tiebreakers" dict).  If "tiebreaker" is a list
    of strings, this is used as a hard-coded pre-permuted list of
    candidates for the predefined_permutation_tiebreaker tiebreaker.
    (This isn't a good idea for real elections, but it's useful
    for testing.)

    The "options" section doesn't define any pragmas; it does
    however permit list values.

    The "ballots" section defines ballots.  In this section,
    names are candidate names, and values are the score for that
    candidate.  In the "ballots" section, individual ballots are
    separated by blank lines and/or comment lines--to start a new
    ballot, just add a blank line, or a comment line.

    The "ballots" section supports one pragma: "ballots".
    This lets you repeat a ballot multiple times.  To use, add
    a line to the "ballots" section as follows:
        n ballots:
    where "n" is the number of times you want to repeat a ballot.
    This will repeat the subsequent ballot "n" times.
    For example, to repeat a ballot 5 times, add this line
    just above the ballot:
        5 ballots:
    (You're explicitly permitted to have blank lines between the
    "ballots" pragma and the ballot it's repeating.)

    (The "ballots" section does not permit list values.)

    Here's a sample starvote format election:

        [options]

        seats=3
        method=Bloc
        verbosity = 1
        tiebreaker = [
            Chuck
            Amy
            Brian
        ]

        [ballots]

        Amy = 1
        Brian = 2
        Chuck = 5

        Amy = 1
        Brian = 5
        Chuck = 3

        Amy = 1
        Brian = 3
        Chuck = 3

        3 ballots:
        Amy = 1
        Brian = 3
        Chuck = 3

    (Why'd I write this?  I got tired of CSV files.)
    """

    exception_prefix_format = "Line {line_number}: " # deliberately not f-string

    if path:
        exception_prefix_format = f"File '{path}', " + exception_prefix_format
        current_directory = pathlib.Path(path).parent
    else:
        current_directory = pathlib.Path(os.getcwd())
        path = "<string>"


    ballots = []
    kwargs = {}
    _sentinel = object()

    option_to_kwarg = {
        'maximum score': 'maximum_score',
    }

    def tiebreaker_converter(value):
        if isinstance(value, list):
            if not value:
                raise ValueError("tiebreaker list must not be empty")
            return predefined_permutation_tiebreaker(value, description=f"Permutation was defined in '{path}'.")
        if isinstance(value, str):
            t = tiebreakers.get(value, _sentinel)
            if t is not _sentinel:
                return t
        raise ValueError(f"{exception_prefix}invalid tiebreaker {value!r}")

    def method_converter(value):
        m = methods.get(value, _sentinel)
        if m is not _sentinel:
            return m
        raise ValueError(f"{exception_prefix}invalid method {value!r}")

    def path_converter(extension):
        def path_converter(s):
            path = pathlib.Path(s)

            if not path.is_absolute():
                path = current_directory / path

            if not path.is_file():
                raise ValueError(f"'{s}' does not exist")
            if path.suffix != extension:
                raise ValueError(f"'{s}' is not a {extension} file")
            return path
        return path_converter

    # defines the function called to convert an option value
    # from the starvote file into a native value for kwargs.
    #
    # (use a function of 'str' if a str is okay.)
    kwargs_converters = {
        'csv_path': path_converter('.csv'),
        'maximum_score': int,
        'method': method_converter,
        'seats': int,
        'starvote_path': path_converter('.starvote'),
        'tiebreaker': tiebreaker_converter,
        'verbosity': int,
        }

    def options_pragma(pragma):
        raise ValueError(f"{exception_prefix}unknown pragma {pragma}")

    def options_handler(d):
        for key, value in d.items():
            kwarg = option_to_kwarg.get(key, key)
            converter = kwargs_converters.get(kwarg, None)
            if not converter:
                raise ValueError(f"{exception_prefix}unknown option '{key}'")
            if kwarg in kwargs:
                raise ValueError(f"{exception_prefix}specified option '{key}' twice")
            kwargs[kwarg] = converter(value)

    repetitions = 1

    def ballots_pragma(pragma):
        nonlocal repetitions

        for _ in (" ballots", " ballot"):
            if pragma.endswith(_):
                s = _
                break
        else:
            s = None

        if s:
            number, r, empty = pragma.partition(s)
            if r and (not empty.strip()):
                repetitions = int(number.strip())
                # let's *do* this.
                if s == " ballots":
                    if repetitions < 2:
                        raise ValueError(f"{exception_prefix}ballots pragma must specify 2 or more repetitions")
                else:
                    if repetitions != 1:
                        raise ValueError(f"{exception_prefix}ballot pragma must specify exactly 1 repetition")
                return

        raise ValueError(f"{exception_prefix}unsupported pragma {pragma}")

    def ballots_handler(d):
        nonlocal repetitions
        ballot = {k: int(v) for k, v in d.items()}
        for _ in range(repetitions):
            if _:
                ballot = dict(ballot)
            ballots.append(ballot)
        repetitions = 1


    section = None
    section_handler = pragma_handler = flush_after_every_line = None

    # section handler functions *must not keep a reference to d.*
    # we reuse a single dict for all parsing.
    section_handlers = {
        'options': (options_handler, options_pragma, True),
        'ballots': (ballots_handler, ballots_pragma, False),
    }

    d = {}

    def flush():
        nonlocal list_mode
        if d:
            section_handler(d)
            d.clear()
            list_mode = False

    sections_seen = set()
    list_mode = False
    key = value = None
    exception_prefix = None

    for line_number, line in enumerate(starvote.split('\n'), 1):
        exception_prefix = exception_prefix_format.format(line_number=line_number)
        line = line.strip()

        is_empty_line_or_comment = (not line) or line.startswith('#')

        if is_empty_line_or_comment:
            if not list_mode:
                flush()
            continue

        if line.startswith('['):
            if list_mode:
                raise ValueError(f"{exception_prefix}you can't change sections inside a list")
            flush()
            if not line.endswith(']'):
                raise ValueError(f"{exception_prefix}bad syntax {line!r}")
            section = line[1:-1].strip()
            if section in sections_seen:
                raise ValueError(f"{exception_prefix}section [{section}] specified twice")
            sections_seen.add(section)
            section_handler, pragma_handler, flush_after_every_line = section_handlers[section]
            continue

        if not section:
            raise RuntimeError(f"{exception_prefix}no section specified")

        if line.endswith(':'):
            if list_mode:
                raise ValueError(f"{exception_prefix}you can't use pragmas inside a list")
            pragma_handler(line[:-1].strip())
            continue

        if list_mode:
            # value still contains the list we created for list mode.
            if line == ']':
                list_mode = False
                d[key] = value
                if flush_after_every_line:
                    flush()
                continue
            value.append(line)
            continue

        key, equals, value = line.rpartition('=')
        if not equals:
            raise ValueError(f"Line {line_number}: bad syntax {line!r}")
        key = key.strip()
        value = value.strip()
        if value.startswith('['):
            # allow x = [] and x = [ ]
            value = value[1:].strip()
            if not value:
                value = []
                list_mode = True
                continue
            if value == ']':
                d[key] = []
                continue
            raise ValueError(f"Line {line_number}: bad syntax {line!r}")

        d[key] = value
        if flush_after_every_line:
            flush()

    flush()
    if repetitions != 1:
        raise ValueError(f"'{repetitions} ballots: invalid as last line of a starvote format election")

    csv_path = kwargs.pop('csv_path', None)
    if csv_path:
        csv_ballots = load_csv_file(csv_path)
    else:
        csv_ballots = []

    starvote_path = kwargs.pop('starvote_path', None)
    if starvote_path:
        starvote_kwargs = load_starvote_file(starvote_path)
        starvote_ballots = starvote_kwargs.pop('ballots', [])

        starvote_kwargs.update(kwargs) # kwargs takes precedence
        kwargs = starvote_kwargs
    else:
        starvote_ballots = []

    if csv_ballots or starvote_ballots:
        ballots = csv_ballots + starvote_ballots + ballots

    if not ballots:
        raise ValueError("no ballots defined")

    kwargs['ballots'] = ballots

    return kwargs


def load_starvote_file(path, *, encoding='utf-8'):
    """
    Loads a text file from disk, parses it with parse_starvote,
    and returns the result.

    Take one required positional parameter: "path", which specifies
    the path to a starvote format file.  By convention, starvote
    files should end with the extension ".starvote", but this is not
    mandatory.

    You may optionally specify an encoding for the file with
    the "encoding" keyword-only parameter; default is "utf-8".
    """
    if not isinstance(path, pathlib.Path): # pragma: no cover
        path = pathlib.Path(path)

    with path.open("rt", encoding=encoding) as f:
        election = f.read()

    return parse_starvote(election, path=path)


def load_csv_file(path):
    """
    Loads ballots from a 'https://star.vote/'-format CSV file.

    Returns a list of ballots.
    """
    if not isinstance(path, pathlib.Path): # pragma: no cover
        path = pathlib.Path(path)

    ballots = []
    with path.open("rt") as f:
        reader = csv.reader(f)
        candidates = None
        for row in reader:
            # clip off voterid, date, and pollid
            row = row[3:]
            if candidates == None:
                candidates = row
                continue
            ballot = {candidate: int(vote) for candidate, vote in zip(candidates, row)}
            ballots.append(ballot)

    return ballots


def _printer():
    text = []

    def text_clear():
        text.clear()

    def text_print(*a, sep=" ", end="\n"):
        text.append(sep.join(str(o) for o in a))
        text.append(end)

    def text_getvalue():
        output = "".join(text)
        text_clear()
        return output

    return text_clear, text_print, text_getvalue


class UsageException(Exception):
    def __init__(self, s=''):
        super().__init__(s)


def main(argv, print=builtins.print):
    import os.path

    if print == builtins.print: # pragma: no cover
        text_clear, text_print, text_getvalue = _printer()
    else:
        text_print = print

        def text_clear(): # pragma: no cover
            pass
        def text_getvalue():
            return None
        def text_flush(): # pragma: no cover
            pass

    if not argv:
        raise UsageException()

    argi = iter(argv)

    extraneous_args = []
    allow_options = True

    class FalseObject:
        def __init__(self, name=None):
            self.name = name
        def __repr__(self): # pragma: no cover
            return self.name or "<FalseObject>"
        def __bool__(self):
            return False

    uninitialized = FalseObject('uninitialized')

    path = uninitialized
    reference = uninitialized

    cmdline_kwargs = {}

    def process_option(key, arg, test, cast, long_option=None, short_option=None):
        description = key.replace("_", " ")

        if long_option == None:
            long_option = '--' + key.replace('_', '-')

        if short_option == None:
            short_option = long_option[1:3]

        if arg.startswith(short_option + "=") or arg.startswith(long_option + "="):
            value = arg.partition('=')[2]
        elif arg.startswith(short_option) or arg.startswith(long_option):
            try:
                value = next(argi)
            except StopIteration:
                raise UsageException(f"no value supplied for {arg}")
        else:
            return False

        existing_value = cmdline_kwargs.get(key, uninitialized)
        if existing_value is not uninitialized:
            raise UsageException(f"{description} specified twice")
        if test and (not test(value)):
            raise UsageException(f"illegal value {value!r} for {description}")

        cmdline_kwargs[key] = cast(value)
        return True

    def test_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def process_option_int(key, arg, long_option=None, short_option=None):
        return process_option(key, arg,
            test_int, int,
            long_option=long_option, short_option=short_option,
            )

    def process_option_method(key, arg, long_option=None, short_option=None):
        return process_option(key, arg,
            methods.__contains__, methods.__getitem__,
            long_option=long_option, short_option=short_option,
            )

    def process_option_tiebreaker(key, arg, long_option=None, short_option=None):
        return process_option(key, arg,
            tiebreakers.__contains__, tiebreakers.__getitem__,
            long_option=long_option, short_option=short_option,
            )

    def process_positional_argument(arg):
        nonlocal path
        if path is uninitialized:
            path = pathlib.Path(arg)
            return
        extraneous_args.append(arg)

    for arg in argi:
        if isinstance(arg, pathlib.Path):
            process_positional_argument(arg)
            continue

        if allow_options:
            if process_option_method('method', arg):
                continue

            if process_option_int('maximum_score', arg, "--maximum-score", "-x"):
                continue

            if arg in ("-r", "--reference"):
                if reference:
                    raise UsageException(f"{arg} specified twice")
                reference = True
                try:
                    from . import reference
                    reference.monkey_patch()
                except ImportError: # pragma: no cover
                    pass
                continue

            if arg in ("-R", "--force-reference"):
                if reference:
                    raise UsageException(f"{arg} specified twice")
                reference = True
                from . import reference
                reference.monkey_patch()
                continue

            if process_option_int("seats", arg):
                continue

            if process_option_tiebreaker("tiebreaker", arg):
                continue

            if arg in ("-v", "--verbose"):
                if cmdline_kwargs.get('verbosity', uninitialized) is uninitialized:
                    cmdline_kwargs['verbosity'] = 0
                cmdline_kwargs['verbosity'] += 1
                continue

            if arg == "--":
                allow_options = False
                continue

            if arg.startswith('-'):
                raise UsageException(f"unknown option {arg}")

        process_positional_argument(arg)

    if extraneous_args:
        raise UsageException("too many arguments: " + " ".join(extraneous_args))

    if path is uninitialized:
        raise UsageException("no csv or starvote file specified.")
    if not path.is_file():
        raise UsageException(f"invalid file specified: {path}")

    def load_election_from_csv_file(path):
        return {
            'ballots': load_csv_file(path),
            'method': STAR_Voting,
            'verbosity': 1,
            'tiebreaker': None,
            }

    extension = path.suffix
    loader = {
        '.csv': load_election_from_csv_file,
        '.starvote': load_starvote_file,
    }.get(extension.lower())
    if not loader:
        raise UsageException(f"invalid file extension: {extension} (should be either '.csv' or '.star')")

    # the kwargs from the command-line take precedence.
    try:
        kwargs = loader(path)
    except Exception as e:
        s = str(e)
        if not s.startswith("File '"):
            # format the string ourselves.
            # in Python 3.6, repr(ValueError) has extra gunk.
            # it looks like this:
            #    ValueError("invalid literal for int() with base 10: 'steve'",)
            #                                                                ^ >:(
            # s = repr(e)
            name = e.__class__.__name__
            s = f"{name}({repr(str(s))})"
        raise UsageException(s)

    # in order of arguments to election():
    kwargs.update(cmdline_kwargs)
    kwargs['print'] = text_print

    if 'method' not in kwargs:
        print("electoral system undefined, specify with -e|--electoral-system")
        if extension == ".starvote":
            print("(or with method= in the [options] section of your starvote file)")
        print()
        raise UsageException()

    try:
        winners = election(**kwargs)
        tie = None
    except UnbreakableTieError as e:
        winners = None
        tie = e
    except Exception as e:
        winners = tie = None
        # format the string ourselves.
        # in Python 3.6, repr(ValueError) has extra gunk.
        # it looks like this:
        #    ValueError("invalid literal for int() with base 10: 'steve'",)
        #                                                                ^ >:(
        # s = repr(e)
        name = e.__class__.__name__
        s = f"{name}({repr(str(e))})"
        text_print(s)

    if (winners or tie) and (not kwargs.get('verbosity', 0)):
        # no output!  print the results ourselves.
        fake_options = Options(STAR_Voting, print=text_print, verbosity=1, seats=1, tiebreaker=None, maximum_score=5)
        fake_options.election_result(winners, tie, raise_tie=False)

    s = text_getvalue()
    if s: # pragma: no cover
        print(s, end='')

    return 0

def main_with_usage(argv, print=builtins.print):
    try:
        main(argv, print=print)
    except UsageException as e:
        s = str(e)
        if s:
            print(s)
            print()
        print(f'''
usage: starvote.py [options] <ballots_file>

Tabulates an election based on votes in a CSV or starvote file.
The parameters for the election can be inferred from the CSV filename,
or explicitly specified via options.

Options:

    -m|--method <method>

        Specifies the electoral system.
        Supported methods are 'star', 'bloc', 'allocated', 'rrv', and 'sss'.

    -r|--reference

        Adds the available reference implementations of methods.
        Continues even if any reference implementations are unavailable.

    -R|--force-reference

        Adds the available reference implementations of methods.
        If any reference implementations are unavailable, exits.

    -s|--seats <seats>

        Specifies number of seats, default {_DEFAULT_SEATS}.
        Required when method is not STAR.

    -v|--verbose

        Increments verbosity, default {_DEFAULT_VERBOSITY}.
        Can be specified more than once.

    -x|--maximum-score <maximum_score>

        Specifies the maximum score per vote, default {_DEFAULT_MAXIMUM_SCORE}.

ballots_file should be a path to a file ending either in '.csv' or '.star':

    * .csv files must be in https://start.vote CSV format.
      When loading a .csv file, starvote defaults to STAR Voting,
      one seat, verbosity 1, and
    * .starvote files must be in "starvote format".

'''.strip() + "\n")

        return -1
