# starvote

## A STAR Voting election tabulator

## Copyright 2023 by Larry Hastings

[STAR voting](https://www.starvoting.org/) is a
relatively-new ["electoral system"](https://en.wikipedia.org/wiki/Electoral_system)--a
method of running an election.  STAR Voting is simple--it's
simple to vote, and simple to tabulate.  And while a completely
fair and perfect electoral system is impossible,
STAR Voting's approach makes sensible tradeoffs
and avoids the worst pitfalls.  It's really great!

This module, **starvote**, implements a STAR Voting tabulator.
It requires Python 3.7 or newer, but also supports CPython 3.6.
(**starvote** relies on dictionaries preserving insertion order,
which is guaranteed as of Python 3.7, but happened to work in CPython 3.6.)

Features:

* Supports four
  [electoral systems](https://en.wikipedia.org/wiki/Electoral_system):

  - [STAR Voting](https://www.starvoting.org/star), the snazzy
    new single-winner voting system.
  - [Bloc STAR Voting](https://www.starvoting.org/multi_winner),
    a multiwinner variant of STAR voting that fills multiple
    seats with the *most popular* candidates.
  - [Allocated Score Voting](https://electowiki.org/wiki/Allocated_Score),
    a [proportional representation](https://en.wikipedia.org/wiki/Proportional_representation)
    electoral system, and so far the only such system officially
    authorized to be a "Proportional STAR Voting" method.
  - [Reweighted Range Voting](https://rangevoting.org/RRV.html)
    (aka "RRV"), an alternative proportional representation
    electoral system.  RRV isn't a STAR variant, but like STAR
    it's a form of
    [score voting.](https://en.wikipedia.org/wiki/Score_voting)
    So the ballot and instructions to the voter are identical
    to a STAR-PR election.  The RRV algorithm is much simpler
    than Proportional STAR Voting, and its "never discard a voter"
    approach is appealing.
  - [Sequentially Spent Score](https://electowiki.org/wiki/Sequentially_Spent_Score),
    a third variety of score-based proportional representation
    electoral system.

* Implements the
  [Official Tiebreaker Protocol](https://www.starvoting.org/ties)
  for STAR Voting and Bloc STAR Voting elections.

* Provides a user-configurable final tiebreaker mechanism
  if the election (or one round in the election) ends in a tie.

  - The default tiebreaker mechanism randomly shuffles
    all the candidates in advance of running the election,
    then breaks the tie in favor of the candidate(s) that
    appear earliest in the list.
  - Alternatively, you can break ties by randomly picking
    a candidate (or candidates) from the tied candidates,
    on demand.
  - You can also implement your own custom tiebreaker.
  - If you specify that there should be no tiebreaker,
    and the election ends in an unbreakable tie, it will
    raise an `UnbreakableTieError` exception.

* All election tabulation calculations are performed using only integers
  and [fractions](https://docs.python.org/3/library/fractions.html).
  This guarantees results are 100% consistent and accurate
  across all platforms.  Floating-point rounding errors are
  impossible--because floats are never used!

* Supports running elections specified in CSV files using
  [`https://star.vote/`](https://star.vote/) format.

* Also supports running elections specified in
  a convenient custom file format called *starvote format*.

* **starvote** 2.0.3 passes its test suite with 100% coverage on
  all supported versions.

* **starvote** has no external dependencies.


## A quick STAR Voting primer

When you vote using STAR Voting, your ballot looks something like this:

```
Amy    0 1 2 3 4 5
Brad   0 1 2 3 4 5
Chuck  0 1 2 3 4 5
Darcy  0 1 2 3 4 5
```

To vote, give every candidate a score from 0 to 5.  5 means you like
them the most, 0 means you like them the least.  (If you don't pick one
of the scores, that's the same as a 0.)  If you give two candidates
the same score, that means you like them equally--you don't have a
preference between them.

Tabulating the election is easy!  You apply the **STAR** method:
**S**core, **T**hen **A**utomatic **R**unoff.

In the first round, the *Scoring Round,* you add up the scores of all the
candidates.  The top two scoring candidates automatically advance to
the second round.

In the second round, the *Automatic Runoff Round,* you examine every
ballot to see which of the two remaining candidates they preferred.
If one has a higher score, that ballot prefers that candidate.  If the
ballot scored both candidates the same, they have no preference.
The candidate preferred by more ballots wins the election.  It's that
simple!

And notice--you always examine every ballot.  STAR Voting never throws
away ballots.  When you vote, your vote always matters,
every step of the way.


## What's so good about STAR Voting?

Electoral systems are a surprisingly deep topic.  They've been studied
for hundreds of years, and there are many *many* different approaches.
There are a number of desirable properties *and* undesirable properties
that electoral systems can have.  And here's the bad news: it's
*impossible* for there to be one best-possible voting system.  There
are mutually exclusive desirable properties, and there are desirable
properties that bring with them downsides.  You just can't make a
one-size-fits-all best system that avoids every problem--every electoral
system has to be a compromise.  Wikipedia has
[a comprehensive article](https://en.wikipedia.org/wiki/Comparison_of_electoral_systems)
on the topic.

STAR Voting avoid the worst problems of electoral systems.
The remaining undesirable properties were chosen as the least-bad
option.

Here are some desirable properites STAR Voting has:

* It's [monotonic.](https://en.wikipedia.org/wiki/Monotonicity_criterion)
  Giving a candidate a higher score can never hurt them, and
  giving a candidate a lower score can never help them.  (And yes,
  this is not always true of voting systems.  The increasingly popular
  [Instant Runoff Voting](https://en.wikipedia.org/wiki/Instant-runoff_voting)
  fails this; paradoxically, it's possible to *hurt* a candidate you
  prefer by giving them a *higher* score.)
* It's [resolvable.](https://en.wikipedia.org/wiki/Resolvability_criterion)
  Ties are unlikely.
* It complies with the [majority loser criterion.](https://en.wikipedia.org/wiki/Majority_loser_criterion)
  If a majority of candidates like one candidate the least, that candidate will
  never win a STAR Voting election.

But here are some desirable properties STAR Voting doesn't have:

* It's not a [Condorcet method,](https://en.wikipedia.org/wiki/Condorcet_winner_criterion)
  which is a very particular property of an electoral system.
  Let's say you have an election with three candidates, A, B, and C.  You ask each voter
  to vote in three head-to-head races: "which do you like better, A or B?", "which do
  you like better, B or C?", and "which do you like better, A or C?"  If there's one
  candidate that wins in every such head-to-head vote in the election, they would be
  the "Condorcet winner", and an electoral system that guarantees the "Condorcet winner"
  will win the election is called a "Condorcet method".  STAR isn't a Condorcet method,
  because Condorcet doesn't take into consideration the strength of preference.  So
  STAR can arguably give a better result.  (On the other hand, STAR does guarantee
  the opposite: a [Condorcet loser](https://en.wikipedia.org/wiki/Condorcet_loser_criterion)
  will never win a STAR election.  And, as a practical matter, it's frequently true
  that the winner of a STAR election just happens to be the Concorcet winner.)
* It doesn't satisfy the [majority criterion.](https://en.wikipedia.org/wiki/Majority_criterion)
  The majority criterion requires: *"if one candidate is ranked first by a majority of voters,
  that candidate must win".*
* It doesn't satisfy the [later-no-harm criterion.](https://en.wikipedia.org/wiki/Later-no-harm_criterion)
  Later-no-harm requires that if you've already expressed a preference for a candidate on your
  ballot, you shouldn't be able to harm that candidate by expressing another preference for
  another candidate later on the ballot.  STAR fails this; giving a higher vote to a
  less-preferred candidate might mean that your more-preferred candidate doesn't get
  elected.  The STAR Voting team [wrote an essay on why they gave up on this criterion.](https://www.starvoting.org/pass_fail)
  The short version is: electoral systems that satisfy later-no-harm generally also
  exhibit
  [the spoiler effect,](https://en.wikipedia.org/wiki/Vote_splitting#%22Spoiler_effect%22)
  which is a worse property.  But achieving later-no-harm *and* avoiding the spoiler effect
  makes your electoral system even worse!

(If there isn't a best-possible voting system, is there a worst-possible?  Maybe!
If there *is* a worst electoral system, it's almost certainly
[Plurality voting](https://en.wikipedia.org/wiki/Plurality_voting)...
the predominant electoral system used here in the United States.  Sigh.)


## API

### `election`

To use `starvote`, first `import starvote`,
then call its `election` function:

```Python
def election(method, ballots, *,
    maximum_score=5,
    print=None,
    seats=1,
    verbosity=0,
    ):
```

`election` tabulates an election based on the
arguments you pass in and returns a `list` containing
the winners. (Even for single-winner STAR Voting--in
that case, the list will only contain one element.)

`method` specifies which method (which "election system")
you want to use in this election, via predefined `Method`
objects. The supported values are:

* `starvote.STAR_Voting`,
* `starvote.Bloc_STAR_Voting`,
* `starvote.Allocated_Score_Voting`,
* `starvote.Reweighted_Range_Voting`, and
* `starvote.Sequentially_Spent_Score`.

Since those are a lot to type, `starvote` also provides
nicknames for these methods, respectively:

* `starvote.star`,
* `starvote.bloc`,
* `starvote.allocated`,
* `starvote.rrv`, and
* `starvote.sss`, and

`ballots` should be an iterable containing individual ballots.
A ballot is a `dict` mapping the candidate to that ballot's
score for that candidate.  The candidate can be any hashable
Python value; the score must be an `int`.

`maximum_score` specifies the maximum score allowed for
any vote on any ballot.

`seats` specifies how many seats the election should fill.
STAR Voting is a single-winner method, so this should be
`1` when using STAR Voting; for the other methods,
`seats` must be greater than or equal to `2`.

`verbosity` specifies how much output you want.
The current supported values are `0` (no output)
and `1` (output); values higher than `1` are
currently equivalent to `1`.

`print` lets you specify your own printing function.
By default `election` will use `builtins.print`;
your replacement `print` function should have the
same signature.



### Functions for specific electoral systems

`starvote` also exports functions implementing each of
the supported electoral systems:

* `star_voting` implements single-winner STAR Voting.
* `bloc_star_voting` implements multiwinner Bloc STAR Voting.
* `allocated_score_voting` implements Allocated Score Voting.
* `reweighted_range_voting` implements Reweighted Range Voting.
* `sequentially_spent_score` implements Sequentially Spent Score.

These functions have much the same signature as `election`,
with the following changes:

* They don't have a `method` parameter; the method is implicit
  in the function.  All four only take one positional parameter,
  `ballots`, which is required.
* `star` doesn't have a `seats` parameter.  The other three
  have a `seats` keyword-only parameter, and this parameter
  is required--it doesn't have a default.  (A *required*
  keyword-only parameter is pretty rare in Python!)
* Note that, like `election`, these functions always
  return a list, even `star_voting`.

#### Reference implementation of Allocated Score Voting

`starvote` ships a copy of the reference implementation
of Allocated Score Voting.  Since this requires both
[NumPy](https://numpy.org/)
and
[Pandas](https://pandas.pydata.org/),
it's not imported by default.  (I didn't want
`starvote` to have any external dependencies.  The unit
test suite runs correctly whether or not these external
dependencies are installed.)

You can import it with `import starvote.reference`;
the directly-callable function is
`starvote.reference.allocated_score_voting_reference`.
You can also use the `Method` object
`starvote.reference.Allocated_Score_Voting_reference`,
with the nickname
`starvote.reference.allocated_r`.

If you want to integrate it into the `starvote` module,
call`starvote.reference.monkey_patch()`.  This does
three things:

* Adds the function and `Method` objects to the `starvote`
  module directly.

  - Also adds them to `starvote.__all__` so they get
    brought in by `from starvote import *`.

* Adds the appropriate `Method` object
  to `starvote.methods`, using the name
  `'Allocated Score Voting (reference)'`
  and the nickname `allocated_r`.

*Note:* the reference implementation doesn't support
tiebreakers.  `allocated_score_voting_reference` *does*
accept a `tiebreaker` argument, but currently it *must*
be `None`.

### Ties

STAR Voting elections rarely result in a tie in the real world.
But ties can still happen.  The good news is, STAR Voting has a
sensible, thorough protocol on how to break a tie.  The bad news is,
not all ties are breakable--some ties genuinely represent the
indecisive will of the voters.

**starvote** gives you control over how to break ties in elections,
through the `tiebreaker` parameter to `election` and the election-specific
functions.  **starvote** also has two predefined tiebreaker functions,
but you can substitute your own--or none at all.

The default tiebreaker in **starvote** is
`predefined_permutation_tiebreaker`, passing
in `candidates=None`.

#### `predefined_permutation_tiebreaker`

The main tiebreaker for **starvote** is
`predefined_permutation_tiebreaker`.  This
is a class; you should instantiate it and
pass in the instance as the `tiebreaker`
argument when you run the election.

`predefined_permutation_tiebreaker`
resolves the tie in favor of an ordered
list of candidates.

Given these three variables, defined
at the time it breaks the tie:

* `candidates`, an ordered list of *all*
  candidates participating in the election,
* `tie`, an iterable of the tied candidates, and
* `desired`, the number of winners we wanted.

`predefined_permutation_tiebreaker` computes
the winners of the tie as follows:

```
winners = [c for c in candidates if c in tie][:desired]
```

In other words, it returns a *desired*-length
subset of *tie*, preferring candidates that
appear earlier in *candidates* over those that
appear later.

`predefined_permutation_tiebreaker` accepts
a `candidates` argument, which should be
an ordered pre-chosen list of all candidates.
The default value is `None`, which instructs
`predefined_permutation_tiebreaker` to scan
the ballots at the start of the election,
produce its own list of all the candidates,
randomly shuffle that list, and use that list
as the `candidates` list.

If you pass in your own `candidates` list,
you may also pass in a string for the
`description` keyword-only parameter, which
should be text describing the source of
this ordered list of candidates.

Note that, if you pass in your own
`candidates` list, **starvote**'s tabulation
of the election will be 100% deterministic
and repeatable.  You can run that election
a million times and you'll always get the
same result.


#### `on_demand_random_tiebreaker`

If you prefer more unpredictability in your life,
you can choose `on_demand_random_tiebreaker`
to break ties.  `on_demand_random_tiebreaker` will
simply pick a random candidate (or candidates)
on demand, using Python's `random.sample` function.
`on_demand_random_tiebreaker` is a function;
you should simply pass it in as the `tiebreaker`
parameter.

#### `UnbreakableTieError`

If you explicitly set `tiebreaker` to `None`,
and an election results in a tie, `starvote` will
raise an `UnbreakableTieError` exception.  You can
get a text description of the tie by calling `str` on the exception;
you can also get a list of the tied candidates in its `candidates`
attribute.

#### Writing your own tiebreaker

You can write your own tiebreaker and pass it in
in the `tiebreaker` parameter to your chosen election
function.  Custom tiebreakers can be either a function
or a class.

A custom tiebreaker function should have this signature:

```Python
def custom_tiebreaker(options, tie, desired, exception):
```

Here's what these four parameters will contain:

* `options` is a **starvote** `Options` object.  `options`
  has attributes mapping to the arguments you passed in to
  `election`.  You should obey `options.verbosity` when
  deciding whether or not to print, and you should print
  using `options.print`.  `options` also has the following
  convenience methods:

  - `options.heading` is a context manager that prints
    a heading to the output if `options.verbosity` is 1
    or greater.  You pass in the heading as a string.
    You can nest headings.
  - `options.print_candidates` will print an iterable
    of candidates.  You pass in the iterable as the
    first (and only) positional argument.  Also accepts
    a `numbered` parameter; if `numbered` is true, it
    prints the candidates in order, prepended by their
    ordinal number (starting with 1).  If `numbered` is
    false, `print_candidates` attempts to sort the
    candidates before printing them.

* `tie` is a list of the tied candidates.

* `desired` is the desired number of winners.

* `exception` is the `UnbreakableTieError` for this
  tie.  If you can't break the tie, you should raise
  this object.

Note that **starvote** will also parse the tiebreaker
function's docstring.  The first line of the docstring
will be used as a "heading" printed during election
initialization, with the rest of the docstring will be
printed as the body of that heading if `options.verbosity`
is 1 or greater.

You can also write a custom tiebreaker class.  The only
requirement is that the class inherits from
`starvote.Tiebreaker`, and it supports a `__call__` method
with the same signature as a custom tiebreaker function.
(However, here the docstring is ignored; it's up to you
to call `options.heading` and `options.print`.)

`Tiebreaker` classes can also optionally have an
`initialize` method:

```Python
def initialize(self, options, ballots):
```

This will be called during initialization of the
election, before any processing of the votes.
Here's an explanation of the two parameters:

* `options` is the same object as the `options` passed in
  to a custom tiebreaker function.

* `ballots` is the iterable
  of ballots passed in to the election function.

Whichever kind of tiebreaker you write, you should
add it to `starvote.tiebreakers`.  That's a dict
mapping names to tiebreakers.  Tiebreakers you
add to that dict will be available to *starvote
format elections* parsed by `parse_starvote`.

### Code example

Here's an example of computing a poll between Amy, Brian, and Chuck:

```Python
import starvote

ballots = [
    {'Amy': 1, 'Brian': 3, 'Chuck': 5},
    {'Amy': 5, 'Brian': 2, 'Chuck': 3},
    {'Amy': 4, 'Brian': 4, 'Chuck': 5},
]

winners = starvote.election(starvote.STAR, ballots, verbosity=1)
```

(This example is included as `example.py` in the `starvote`
Git repo.)

After this example code finishes,
the `winners` variable will contain the list `['Chuck']`.
The example also produces this output:

```
[STAR Voting]
  Tabulating 3 ballots.
  Maximum score is 5.
[STAR Voting: Initializing ordered permutation tiebreaker]
  Computing a random permutation of all the candidates.
  Permuted list of candidates:
    1. Brian
    2. Chuck
    3. Amy
  Tiebreaker candidates will be selected from this list, preferring candidates with lower numbers.
[STAR Voting: Scoring Round]
  The two highest-scoring candidates advance to the next round.
    Chuck -- 13 (average 4+1/3) -- First place
    Amy   -- 10 (average 3+1/3) -- Second place
    Brian --  9 (average 3)
  Chuck and Amy advance.
[STAR Voting: Automatic Runoff Round]
  The candidate preferred in the most head-to-head matchups wins.
    Chuck         -- 2 -- First place
    Amy           -- 1
    No Preference -- 0
  Chuck wins.
[STAR Voting: Winner]
  Chuck
```


### *starvote format*

`starvote` also defines a custom text format for specifying
elections called *starvote format*.  It's heavily used for
testing `starvote` itself, though it could be used to run
real elections.

*starvote format* looks kind of like
[INI format,](https://en.wikipedia.org/wiki/INI_file)
but it isn't exactly the same.

Why'd I write this?  I got tired of CSV files.  It's very handy
to add metadata about how to run the election to the election
file itself.  And *starvote format* is so much easier to read
and edit than the equivalent
[`https://star.vote/`](https://star.vote/)-format
CSV file.


#### Definition

A string that contains an election in *starvote format*
is called a *starvote format election*.

*starvote format* is a line-oriented format.
Leading and trailing whitespace per-line is ignored (and stripped).
Lines that start with `#` are comments.
Empty lines and comments are (mostly) ignored.

Non-empty lines that aren't comments are either an
*assignment* line, a *pragma* line, or a *section* line.

A *pragma* line ends with a colon (`:`).  Pragma lines are
free-form; currently there's only one defined pragma.
(When parsing a line, pragma take precedence over assignment.)

An *assignment* line must contain an equals sign (`=`);
the text before the equals sign is the "name", and the text
after the equals sign is the "value".  What effect this has
depends on what section we're in.

A line that starts with `[` and ends with `]` defines a
*section*.  You specify the name of the section between
the square brackets.  You can only specify a section once.
Only two sections are supported: `options` and `ballots`.

The `options` section specifies how to run the election.
Assignment lines in the `options` section specify options;
each name maps to a parameter to the `election` function.
Here are all the supported names:

```
    csv_path = <string>
    maximum score = <integer>
    method = <string>
    seats = <integer>
    starvote_path = <string>
    tiebreaker = <string | list>
    verbosity = <integer>
```

A *starvote format election* can specify each of these a maximum of once.

An assignment line in the `options` section can also use
*list mode*.  *list mode* allows you to set an option to
a list of values, rather than a single value.
To use, set a name to the value `[`.
The "name" is set to an empty string, and the
*starvote format* parser activates *list mode*.
While in *list mode,* non-empty lines are appended
to the list currently being defined.  To deactivate
*list mode* and finish defining the list, specify
`]` on a line by itself.  Notes:

* If you set a value to `[]`, it's set to an empty
  list, and the parser doesn't enable *list mode.*
* You can't use pragmas or change sections while
  in *list mode.*
* You can't nest lists.

The only assignment that supports lists is the
`tiebreaker` option in the `options` section.
If `tiebreaker` is set to a string, this specifies
the name of the tiebreaker in the `starvote.tiebreakers`
dict to use for this election.  If `tiebreaker` is set
to a string, `parse_starvote` looks up that string in
the `options.tiebreakers` dict and uses the tiebreaker
found there.  If `tiebreaker` is set
to a list, this defines a pre-permuted list of candidates
which is passed in to `predefined_permutation_tiebreaker`.
(This lets you predefine a permuted list of candidates.
You shouldn't use this in a real election, but it's useful
in test elections as it makes the election deterministic.)

The `ballots` section defines ballots.  In this section,
names are candidate names, and values are the score for that
candidate.  Individual ballots are separated by blank lines
and/or comment lines--to start a new ballot, just add a blank
line, or a comment line.

The `ballots` section supports one pragma: `ballots`.
This lets you repeat a ballot multiple times.  To use, add
a line to the `ballots` section as follows:
```
    n ballots:
```

where `n` is the number of times you want to repeat a ballot.
This will repeat the subsequent ballot `n` times.
For example, to repeat a ballot 5 times, add this line
just above the ballot:

```
    5 ballots:
```

(You're explicitly permitted to have blank lines between the
`ballots` pragma and the ballot it's repeating.)

The `starvote_path` and `csv_path` options allow you to
"import" another file into the current election.  They
can specify relative or absolute paths; if relative,
they will be resolved using the directory the *starvote
format* file is in (if the *starvote format election* was
loaded from a file) or the current directory.  Both settings
will load ballots from the file specified; `starvote_path`
will also load the options from the file specified, however
any options set in the current election will override those
options.

#### Example

Here's a sample starvote format election:

    [options]

    seats=3
    method=Bloc
    tiebreaker = [
      Chuck
      Brian
      Amy
      ]
    verbosity = 1

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

### APIs

The `starvote` module provides two functions that handle
*starvote format*.

The first is `parse_starvote`:

```Python
starvote.parse_starvote(starvote, *, path="<string>")
```


`parse_starvote` takes
one positional parameter: `election`, which must be a
string in *starvote format*.  It parses the string
and returns a `kwargs` dict.  You can run that election
by calling `election` and passing in this dict, using
`**` to turn the contents of the dict into keyword arguments:

```Python
starvote.election(**kwargs)
```

You may also pass in a keyword-only parameter `path`, which
should represent the filename if the *starvote format election*
was loaded from a file; if specified, it'll be included in
exceptions, for context.

The second is `load_starvote_file`:

```Python
starvote.load_starvote_file(path, *, encoding='utf-8')
```

`load_starvote_file` takes one positional parameter:
`path`, which must be a `str`, `bytes`, or `pathlib.Path` object.
It opens that file, reads the contents, passes those
contents in to `parse_starvote`, and returns the result.
You may specify the text encoding using the
`encoding` keyword-only parameter; the default
encoding is `'utf-8'`.


### Command-line module

The `starvote` module supports being run as a script
(`python -m starvote`).
Run it without arguments to see usage.

To use, specify the path to a single file on the
command-line.  `starvote` will read in the file,
run the election, and print the result.

The path may be a
[CSV file.](https://en.wikipedia.org/wiki/Comma-separated_values)
CSV files should end with the file extension `.csv`,
and be in
[`https://star.vote/`](https://star.vote/)
format.  By default elections in CSV files are run
using STAR Voting, for one seat, with `verbosity=1`
and the default tiebreaker.

Alternatively, the path may be a *starvote format* file.
*starvote format* files should end with the file extension
`.starvote` and contain a *starvote format election* in
UTF-8 format.  *starvote format elections* explicitly
specify all the parameters of the election.

For example, you can run this from the root of the
source-code repository:

```
% python3 -m starvote test_elections/test_election_breakable_tie_in_automatic_runoff_round_using_max_score_count_round.starvote
```

to see how **starvote** handles ties during the automatic runoff round.


## Multiple-winner elections

**starvote** also implements several multiwinner electoral systems.
All you need to do is pass in one of the multiwinner methods, such as
`starvote.bloc`, `starvote.allocated`,
or `starvote.rrv`, when you call `election`:

```Python
poll = election(starvote.bloc, ballots, seats=2)
```

You can experiment with these with the command-line version of the
module too.  Simply specify the method with `-m`,
the number of seats with `-s`,
and the maximum score with `-x`.
These will override the settings from inside a *starvote format* file
(and the default settings for CSV files).

### Multiwinner vs proportional

Here's a quick explanation about what "proportional voting" means,
in the context of multiwinner elections.
As with every other topic, you can read more about it
[at Wikipedia.](https://en.wikipedia.org/wiki/Proportional_representation)

A straight multiwinner election simply means you're electing
2 or more candidates instead of one candidate.  The candidates
that get the most votes--or however the election is tabulated--win.

But electing only the most popular candidates can be a poor
representation of the electorate.  Let's say you have a city
election to fill five seats.  In this city, 60% of the voters
vote only for party A, and 40% of the voters vote only for
party B.  Bloc STAR Voting would very likely award all five
seats to party A candidates.  Is that fair?  It seems like the
["tyranny of the majority".](https://en.wikipedia.org/wiki/Tyranny_of_the_majority)

There's an alternate approach to apportioning seats, used
in political systems across the world, called "Proportional
Representation".  The idea is, you have N seats, and you
assign portions of them based on representing portions of
the populace.  In the above example, you'd *want* to give
three seats to party A and two seats to party B.  What
system could do that?

Often proportional representation is done based on voting
for parties rather than voting for candidates.  This is
called
[Party-list proportional representation,](https://en.wikipedia.org/wiki/Party-list_proportional_representation)
and it's used to elect governmental bodies across the world.

But there are voting methods that permit voting directly for
candidates and produces proportional representation.
Allocated Score Voting, Reweighted Range Voting, and
Sequentially Spent Score are three such methods.
They all work something like this:

* Each vote is a number, with higher numbers
  indicating a stronger preference.
* You run N rounds of the election to fill N seats,
  each round electing one candidate.
* When a candidate is elected, we may *allocate* ballots
  to that candidate, which means we consider them used-up
  and we remove them from the election.  If you vote
  for candidate A1, and candidate A1 wins the first round,
  your ballot might get "allocated" to candidate A1 and
  ignored for the rest of the election.
* Alternatively, we may *re-weigh* the
  ballots of voters who voted for that candidate.
  That means we reduce the voting power of those ballots.
  If in the election, you voted for candidate A1, and A1
  wins the first round, in the second round your vote
  will count for less.  But if I gave A1 a score of 0,
  my ballot would still be at full strength.

The differences between the three is how they allocate
vs. reweigh ballots. Allocated Score Voting and Sequentially
Spent Score both allocate ballots, Reweighted Range Voting
never does--with RRV every vote is counted in every round.
Also, the three systems use different formulae to compute the
new weight of a ballot after each round.  In Allocated Score
and Sequentially Spent Score,
the new weight is based on how many excess voters were needed
to fill a quota (called a
[Hare quota](https://en.wikipedia.org/wiki/Hare_quota));
in Reweighted Range Voting, the new weight is based on the
sum of the score(s) you contribute to the winning candidate(s).

**starvote** ships a sample election that nicely demonstrates
how direct-elected proportional representation elections can work:

```
test_elections/test_election_reweighted_range_sample_election.starvote
```

This election is like the example election I used in the description
above.  It uses Reweighted Range Voting to fill three seats, and each
vote has a maximum score of 10.
60 of the voters prefer party A, and give high scores to candidates A1, A2, and A3;
40 of the voters prefer party B, and give high scores to candidates B1 and B2.

You can run the election in the `starvote` main directory with this command:

```
% python3 -m starvote test_elections/test_election_reweighted_range_sample_election.starvote
```

To see how the tabulation works using Allocated Score Voting, run this:

```
% python3 -m starvote -m allocated test_elections/test_election_reweighted_range_sample_election.starvote
```

You can also see how it changes with Sequentially Spent Score by running this:

```
% python3 -m starvote -m allocated test_elections/test_election_reweighted_range_sample_election.starvote
```

And to see the tyrrany of the majority in action, this command will tabulate the election using Bloc STAR Voting:

```
% python3 -m starvote -m bloc test_elections/test_election_reweighted_range_sample_election.starvote
```

### Warning

I haven't found a single test corpus for Bloc STAR Voting.
I'm following the rules as best I can, and the results I'm getting
make sense.  But so far I can't confirm my implementation is
correct--there's a very real possibility I got something wrong.

I do have one sample poll for Reweighted Range Voting, so I
have some confidence that my implementation is okay.  And I
do test against the
[reference implementation of Allocated Score Voting](https://www.starvoting.org/technical_specifications)
a little.


## Thanks

Huge thanks to Tim Peters for his continuous input during the
development of this library.  Although Tim didn't have any input
on the library itself--if you don't like the library it's 100%
my fault!--he tirelessly answered all my questions about voting
during its development, and convinced me to change my approach
several times.  In particular, Tim's feedback pushed me to
develop the `tiebreaker` plug-in interface.


## License

**starvote** is licensed using the
[MIT license.](https://opensource.org/license/mit/)
See the `LICENSE` file.

It seems particularly relevant to repeat here:
*there is no warranty for this software.*
I've done the best job I can implementing this election system
tabulator.  But this software could have bugs,
or my understanding of the rules could be wrong,
and either of these could affect the results of elections
you run with this software.
**Use at your own risk.**

The source code repository includes sample ballots downloaded from
[`https://star.vote/`](https://star.vote/).  The licensing of these
sample ballots is unclear, but they're assumed to be public-domain
or otherwise freely redistributable.


## Changelog

**2.0.4** - *2023/06/05*

* Added support for Sequentially Spent Score voting.
* Changed presentation slightly for Allocated Score:
  the average vote is now computed using the count of
  *all* ballots in the election, including allocated
  ballots.  (Previously the average was computing using
  just the *remaining* ballots.)  This doesn't change
  the outcome of the election, it's just a presentation
  change.
* Removed last traces of "STAR-PR", which I thought was
  an alternate name for Allocated Score.
* Doc changes.  Standardized on the spelling "multiwinner",
  instead of "multi-winner".


**2.0.3** - *2023/06/01*

* Normalized nomenclature for `Method` objects.  Now,
  every method has an official correctly-spelled
  correctly-capitalized name, and exactly one "nickname".
  The nickname is always lowercase, and would return
  True for `isidentifier`.  These are used in the
  `starvote.method` map; a variant of these names is
  also bound as module attributes (changed so they're
  valid identifiers).
* Improved `starvote.reference.monkey_patch`.  It's now
  data-driven and thus more reliable.
* Added `starvote.reference.__all__`, in case you want
  to `from starvote.reference import *`.
* Doc fixes.

**2.0.2** - *2023/06/01*

* Renamed the `tiebreaker` parameter `candidates` to `tie`.
* Evicted some testing-only tiebreakers from the `starvote`
  module.  They're now in their own script, which only gets
  loaded when working with the test suite.

**2.0.1** - *2023/06/01*

* Changed the nickname of the reference version of
  Allocated Score Voting to "Allocated-R".

**2.0** - *2023/06/01*

A complete rewrite!  The 1.x code base was pretty smelly.
This codebase is much, much cleaner--and I think I squashed
one or two bugs too.

`starvote` has an entirely new, functional API. `election`
runs the election for you, and takes two required positional
parameters: `method`, which specifies which
electoral system you want, and `ballots`, an iterable
of ballot dicts.

You can also now pass in a handler for unbreakable ties.
By default, unbreakable ties are now broken using a
pre-chosen randomize list of candidates.  (`election` can
still raise `UnbreakableTieError` exceptions if you prefer.)

You can also call the voting method functions directly:
`star`, `bloc_star`, `proportional_star`, `reweighted_range`,
are all functions, too.  These omit the `method` parameter
but still require the `ballots` parameter.

There's also a new text format for storing an election,
*starvote format,* with the `.starvote` file extension.
*starvote format* is a nice alternative to `.csv` files.

* Added the `election`, `star_voting`, `bloc_star_voting`,
  `allocated_score_voting`, and `reweighted_range_voting` functions.

  - Removed the `Poll` class.

* Now consistently use the official names for all methods:

  - STAR Voting
  - Bloc STAR Voting
  - Allocated Score Voting
  - Reweighted Range Voting

  ("Proportional STAR Voting" is a *category* of electoral systems.
  It's *not* itself a voting system, and it's definitely not restricted
  to "Allocated Score Voting".  "STAR-PR" is another name that category.)

* Replaced the `ElectoralSystem` enum with the `Method` class.  Instances
  (e.g. `starvote.STAR_Voting`) contain all the metadata needed by `election`
  to run the election.

  - `methods` is a module-level dict mapping strings to `Method` objects.

* Implemented the
  [STAR Voting Official Tiebreaker Protocol](https://www.starvoting.org/ties)
  for STAR Voting and Bloc STAR Voting.

* All vote tabulation uses strictly `int` and
  [fractions.Fraction](https://docs.python.org/3/library/fractions.html)
  objects.  Vote tabulation is now 100% consistent and accurate,
  from run to run, across all platforms.

* Added the `parse_starvote` function, which parses a *starvote format*
  string, runs the election, and returns the result.

* Added the `load_starvote_file` function, which loads a *starvote format*
  file from disk and parses it with `parse_starvote`.

* Added the `Tiebreaker` class, and the `on_demand_random_tiebreaker`
  and `predefined_permutation_tiebreaker` tiebreakers.

  - `tiebreakers` is a module-level dict mapping strings to tiebreakers.

* Added the reference implementation of Allocated Score Voting.  This
  requires both NumPy and Pandas, so it's not imported by default.
  You can import it with `import starvote.reference`, and you can
  integrate it into the `starvote` module by calling
  `starvote.reference.monkey_patch()`.  The reference implementation
  doesn't support tiebreakers.

* When running the module from the command-line
  using `python -m starvote`:

  - You may now specify a `.starvote` file.
    Its should be in UTF-8, and the contents should be
    a *starvote format election.*

  - When specifying a `.csv` file, `starvote` uses several default
    values: method is STAR Voting, seats is 1, verbosity is 1.


**1.5.1** - *2023/05/24*

* Renamed a bunch of names in the API.
  * Renamed `PollVariant` enum to `ElectoralSystem`.
  * Renamed `variant` parameter to `electoral_system`.
  * Renamed `max_score` parameter to `maximum_score`.
* Changed command-line module options to match.
  * Changed `-v|--variant` to `-e|--electoral-system`.
  * Changed `-m|--max_score` to `-m|--maximum_score`.

**1.5** - *2023/05/22*

* Added support for
  [Reweighted Range Voting](https://rangevoting.org/RRV.html),
  an attractive alternative to Proportional STAR.
  Like STAR-PR, RRV is a proportional representation electoral
  system.  But RRV is simpler to understand, simpler to
  implement, and it never throws away votes.
  Thanks to Tim Peters for suggesting it!
* Added the `max_score` parameter to the `Poll` constructor.
  Now you can use whatever range you like.  (The minimum score
  is still always 0.)
* Changed the spelling of "Bloc STAR".  I thought the "Bloc"
  was always properly capitalized (as "BLOC STAR"), but nope,
  it's not.

**1.4** - *2023/05/21*

* Automated the test suite.
* Add logging prints for tie-breaker preference round
  for Proportional STAR.
* Fixed presentation in `__main__` for multiple winner
  elections that end in a tie.

**1.3** - *2023/05/21*

* Added support for
  [Proportional STAR](https://www.starvoting.org/star-pr)
  polls.  The only visible external change is the new
  `Proportional_STAR` enum value.
* Renamed the `winners` parameter on the `Poll` constructor to `seats`.
  Sorry to break your code, all zero people planetwide who already started
  using the parameter!  But this new name is a big improvement.

**1.2** - *2023/05/20*

* Add support for [Bloc STAR](https://www.starvoting.org/multi_winner)
  polls:

  * Added `PollVariant` enum containing `STAR` and `BLOC_STAR` values.
  * Added `variant` and `winners` parameters to `Poll`.

* Add the list of tied candidates to the `UnbreakableTieError`
  exception as the new `candidates` attribute.

**1.1** - *2023/05/20*

* Bugfix: raise `UnbreakableTieError` if there's a three-way
  tie for *second* place.  Previously **starvote** only noticed
  if there was a three-way tie for *first* place.
* Added sample output for every sample poll in `sample_polls/`.
  These outputs have been confirmed correct by inspection, and
  could in the future be used as part of an automated test suite.

**1.0** - *2023/05/20*

* Initial release.
