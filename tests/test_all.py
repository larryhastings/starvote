#!/usr/bin/env python3

import builtins
import fractions
import glob
import os.path
import pathlib
import sys
import unittest

def preload_local_starvote():
    """
    Pre-load the local "starvote" module, to preclude finding
    an already-installed one on the path.
    """
    import sys
    import pathlib
    argv_0 = pathlib.Path(sys.argv[0])
    starvote_dir = argv_0.parent.resolve()
    while True:
        starvote_init = starvote_dir / "starvote" / "__init__.py"
        if starvote_init.is_file():
            break
        starvote_dir = starvote_dir.parent
    sys.path.insert(0, str(starvote_dir))
    import starvote
    return starvote_dir

starvote_dir = preload_local_starvote()
import starvote

#
# Useless testing-only tiebreakers
#

import harness

def inject_test_elections(cls, argv): # pragma: no cover
    """
    Finds all the test_election/{*.starvote, *.csv} files,
    runs the elections within, and compares the results to
    the corresponding .txt file.

    Creates one callable for each test file and injects it into cls.
    The name of the callable is based on the name of the file,
    so you can figure it out from the name of the test function that failed.
    """

    def make_test_runner(election_path, output_path):
        def run_test(self):

            text_clear, text_print, text_getvalue = starvote._printer()

            try:
                starvote.main_with_usage(["-r", election_path], print=text_print)
                got = text_getvalue().strip().split("\n")
            except Exception as e: # pragma: no cover
                got = [str(e)]

            with output_path.open("rt") as f:
                expected = f.read().strip().split('\n')

            # only fail if the smushed_and_lowered version
            # of the output doesn't match... but use the
            # real versions so the diff is readable
            smush_and_lower = lambda l: "\n".join(l).replace(' ', '').replace('\t', '').lower()
            smushed_and_lowered_expected = smush_and_lower(expected)
            smushed_and_lowered_got = smush_and_lower(got)

            if smushed_and_lowered_expected != smushed_and_lowered_got: # pragma: no cover
                self.maxDiff = 2**32
                self.assertEqual("\n".join(expected) + "\n", "\n".join(got) + "\n")
        return run_test

    work = []

    argv = sys.argv[1:]

    # check .starvote before .csv
    # if we have both, only run the .starvote
    #
    # If you want to change options for a .csv file,
    # create a .starvote file with the same basename
    # and use the csv_path option to load the ballots.
    # That's what I do!
    test_suffixes = [".starvote", ".csv"]
    output_suffix = ".txt"

    for path in argv:
        path = pathlib.Path(path)
        if path.suffix in test_suffixes:
            output_path = path.with_suffix(output_suffix)
            work.append((path, output_path))
            continue
        if path.suffix == output_suffix:
            for suffix in test_suffixes:
                test_path = path.with_suffix(suffix)
                if test_path.is_file():
                    work.append((test_path, path))
                    break
            else:
                sys.exit(f"invalid file {path}, no .starvote or .csv found")

    stems_seen = {}
    if not work:  # pragma: no cover
        os.chdir(starvote_dir)

        test_directory = pathlib.Path("test_elections")
        for extension in test_suffixes:
            for election_path in test_directory.glob(f"*{extension}"):
                stem = election_path.with_suffix('')
                already_seen_as = stems_seen.get(stem)
                if already_seen_as:
                    print(f"Skipping '{election_path}', already processed '{already_seen_as}'")
                    continue
                stems_seen[stem] = election_path
                output_path = election_path.with_suffix(".txt")
                work.append((election_path, output_path))

        work.sort()

    for i, (election_path, output_path) in enumerate(work, 1):
        if not output_path.is_file():
            print(f"Skipping '{election_path}', no '{output_path}' output file.")
            continue
        runner = make_test_runner(election_path, output_path)
        runner.__name__ = str(election_path)
        runner_name = "test_elections__slash__" + str(election_path).rpartition('/')[2].replace('.', '_dot_')
        setattr(cls, runner_name, runner)


tied_election = """
[options]
    method = star
    verbosity = 1
    {options}

[ballots]

    4 ballots:
        A = 4
        B = 4
        C = 4
"""


class StarvoteTests(unittest.TestCase):

    def test_import_star(self):
        # test that import * works
        # (it will fail if there's a bug with the definition of __all__)

        # test should still work even if we can't load numpy / pandas
        try:
            import starvote.reference
            module = "import starvote.reference\nstarvote.reference.monkey_patch()\ndel starvote\nfrom starvote import *"
            reference_imported_ok = True
        except ImportError: # pragma: no cover
            module = "from starvote import *"
            reference_imported_ok = False

        import starvote
        g = {}
        exec(module, g, g)
        self.assertEqual(g['STAR_Voting'], starvote.STAR_Voting)
        if reference_imported_ok:
            self.assertEqual(g['allocated_r'], starvote.reference.allocated_r)

    def test_random_tiebreaker(self):
        election = tied_election.format(options="tiebreaker = on_demand_random_tiebreaker")
        kwargs = starvote.parse_starvote(election)

        text_clear, text_print, text_getvalue = starvote._printer()
        result = starvote.election(**kwargs, print=text_print)
        self.assertTrue(result)
        self.assertIn(result[0], ['A', 'B', 'C'])
        output = text_getvalue()
        self.assertIn("Tie-breaking winners will be chosen at random, on demand.", output)

    def test_no_candidates_tiebreaker(self):
        election = tied_election.format(options="")
        kwargs = starvote.parse_starvote(election)
        text_clear, text_print, text_getvalue = starvote._printer()
        kwargs['tiebreaker'] = starvote.predefined_permutation_tiebreaker(candidates=[])
        with self.assertRaises(ValueError):
            starvote.election(**kwargs, print=text_print)

    def test_no_candidates_tiebreaker_with_description(self):
        election = tied_election.format(options="")
        kwargs = starvote.parse_starvote(election)
        text_clear, text_print, text_getvalue = starvote._printer()
        with self.assertRaises(ValueError):
            kwargs['tiebreaker'] = starvote.predefined_permutation_tiebreaker(candidates=[], description="Hey yo")

    def test_hardcoded_candidates_tiebreaker_with_no_description(self):
        election = tied_election.format(options="")
        kwargs = starvote.parse_starvote(election)
        kwargs['tiebreaker'] = starvote.predefined_permutation_tiebreaker(candidates="C B A".split())
        text_clear, text_print, text_getvalue = starvote._printer()
        result = starvote.election(**kwargs, print=text_print)
        self.assertEqual(result, ['C'])
        output = text_getvalue()
        self.assertIn("externally", output)

    def test_hardcoded_candidates_tiebreaker_with_description(self):
        election = tied_election.format(options="")
        kwargs = starvote.parse_starvote(election)
        description_string = "Fanciful Snoodles"
        kwargs['tiebreaker'] = starvote.predefined_permutation_tiebreaker(candidates="C B A".split(), description=description_string)
        text_clear, text_print, text_getvalue = starvote._printer()
        result = starvote.election(**kwargs, print=text_print)
        self.assertEqual(result, ['C'])
        output = text_getvalue()
        self.assertIn(description_string, output)

    def test_tiebreaker_wrapper_cover(self):
        def fake_tiebreaker(): # pragma: no cover
            pass
        tw = starvote.TiebreakerFunctionWrapper(fake_tiebreaker)
        self.assertIn("TiebreakerFunctionWrapper(function=", repr(tw))

    def test_options(self):
        with self.assertRaises(ValueError):
            starvote.Options(method=starvote.STAR_Voting, maximum_score="abc")
        with self.assertRaises(ValueError):
            starvote.Options(method=starvote.STAR_Voting, seats="abc")

        with self.assertRaises(ValueError):
            starvote.Options(method=starvote.STAR_Voting, seats=2)
        with self.assertRaises(ValueError):
            starvote.Options(method=starvote.Bloc_STAR_Voting, seats=1)

        o = starvote.Options(method=starvote.STAR_Voting, verbosity=1)
        self.assertEqual(o._print, builtins.print)

        with self.assertRaises(ValueError):
            o.election_result(winners=None, tie=None)
        with self.assertRaises(ValueError):
            o.election_result(winners=1, tie=1)

        with self.assertRaises(TypeError):
            o.break_tie(text="foo", candidates=3.14159, desired=1)
        with self.assertRaises(ValueError):
            o.break_tie(text="foo", candidates=[], desired=1)
        with self.assertRaises(ValueError):
            o.break_tie(text="foo", candidates=['a', 'b'], desired=3)

        o = starvote.Options(method=starvote.STAR_Voting, verbosity=1, tiebreaker=lambda options, tie, desired, exception: 3.1415)
        with self.assertRaises(TypeError):
            o.break_tie(text="foo", candidates=['a', 'b'], desired=1)

        o = starvote.Options(method=starvote.STAR_Voting, verbosity=1, tiebreaker=lambda options, tie, desired, exception: ['a', 'b', 'c', 'd', 'e'])
        with self.assertRaises(TypeError):
            o.break_tie(text="foo", candidates=['a', 'b'], desired=1)

    def test_method(self):
        def fake_method(): # pragma: no cover
            pass

        with self.assertRaises(TypeError):
            starvote.Method(name=3.14159, function=fake_method, multiwinner=False)
        with self.assertRaises(TypeError):
            starvote.Method(name="method", function=3.14159, multiwinner=False)

        m = starvote.Method(name="method", function=fake_method, multiwinner=False)
        self.assertIn("<Method", repr(m))

    def test_election(self):
        with self.assertRaises(TypeError):
            starvote.election(3.14159, [])
        with self.assertRaises(ValueError):
            starvote.election("beard blade", [])
        with self.assertRaises(ValueError):
            starvote.election("star", [])

    def test_sorting(self):
        unsortable_list = [{1:1}, {3:3}, {2.2}]
        copy_of_unsortable_list = list(unsortable_list)
        starvote._attempt_to_sort(copy_of_unsortable_list)
        self.assertEqual(unsortable_list, copy_of_unsortable_list)

    def test_invalid_ballots(self):
        with self.assertRaises(ValueError):
            starvote.star_voting([])

        with self.assertRaises(ValueError):
            starvote.star_voting([{'A': 80, 'B': 90}])
        with self.assertRaises(ValueError):
            starvote.star_voting([{'A': 1.5, 'B': 3.5}])

        with self.assertRaises(ValueError):
            starvote.star_voting([{'': 5, 'B': 3}])

    def test_module_main(self):
        UE = starvote.UsageException
        main = starvote.main

        good_starvote_file = "test_elections/test_election_all_threes_star.starvote"

        with self.assertRaises(UE):
            main([])

        with self.assertRaises(UE):
            main('-m'.split())

        with self.assertRaises(UE):
            main(f"-m=star -m rrv {good_starvote_file}".split())

        with self.assertRaises(UE):
            main(f"-method=bafflegab {good_starvote_file}".split())

        with self.assertRaises(UE):
            main("-s eighty-eleven".split())

        with self.assertRaises(UE):
            main(f"-z {good_starvote_file}".split())

        with self.assertRaises(UE):
            main("foo.csv bar.csv".split())

        with self.assertRaises(UE):
            main("-m star".split())

        with self.assertRaises(UE):
            main("-m star badfile.starvote".split())

        with self.assertRaises(UE):
            main(f"-m star {good_starvote_file.replace('.starvote', '.txt')}".split())

        UI_or_I = (UE, ImportError)
        with self.assertRaises(UI_or_I):
            main(f"--reference -r {good_starvote_file}".split())

        with self.assertRaises(UI_or_I):
            main(f"--force-reference -R {good_starvote_file}".split())

        with self.assertRaises(UI_or_I):
            main(f"--force-reference -r {good_starvote_file}".split())

        with self.assertRaises(UI_or_I):
            main(f"--reference -R {good_starvote_file}".split())

        text_clear, text_print, text_getvalue = starvote._printer()

        result = main(f"-s 2 -x 5 -m rrv -v -v -t none -- {good_starvote_file}".split(), print=text_print)
        self.assertEqual(result, 0)
        self.assertIn("Tie between ", text_getvalue())

    def test_against_allocated_score_voting_reference(self):
        election = """
        [options]

            method = allocated
            seats = 3
            verbosity = 0

        [ballots]

            Amy = 1
            Brian = 3
            Chuck = 5
            Darcy = 5

            Amy = 3
            Brian = 2
            Chuck = 3
            Darcy = 5

            Amy = 2
            Brian = 1
            Chuck = 4
            Darcy = 2

            Amy = 3
            Brian = 3
            Chuck = 4
            Darcy = 3
        """

        kwargs = starvote.parse_starvote(election)
        kwargs['tiebreaker'] = starvote.predefined_permutation_tiebreaker
        results = starvote.election(**kwargs)
        self.assertEqual(results, ['Amy', 'Chuck', 'Darcy'])

        try :
            from starvote import reference
        except ImportError: # pragma: no cover
            return

        kwargs['method'] = reference.allocated_r
        kwargs['tiebreaker'] = None
        reference_results = starvote.election(**kwargs)
        self.assertEqual(reference_results, results)

    def test_fraction_formatting(self):
        for i, t in (
            (1, ('1', '', '', '') ),
            (-1, ('-1', '', '', '') ),
            (234, ('234', '', '', '') ),
            (-234, ('-234', '', '', '') ),
            (fractions.Fraction(11,34), ('', '', '11', '/34') ),
            (fractions.Fraction(-11,34), ('', '-', '11', '/34') ),
            (1+fractions.Fraction(11,34), ('1', '+', '11', '/34') ),
            (-1+fractions.Fraction(-11,34), ('-1', '-', '11', '/34') ),
            (234+fractions.Fraction(11,34), ('234', '+', '11', '/34') ),
            (-234+fractions.Fraction(-11,34), ('-234', '-', '11', '/34') ),
            ):
            self.assertEqual(starvote.split_int_or_fraction_as_str(i), t)

        for i, width in (
            (0, 1),
            (1, 1),
            (234, 3),
            (-1, 2),
            (-234, 4),
            ):
            self.assertEqual(starvote._width(i), width)

    def test_int_to_words(self):

        with self.assertRaises(ValueError):
            starvote.int_to_words(234.5)

        def test(i, normal, flowery):
            got = starvote.int_to_words(i, flowery=False)
            self.assertEqual(got, normal)
            got = starvote.int_to_words(i, flowery=True)
            self.assertEqual(got, flowery)

        test(                    0,
            'zero',
            'zero')

        test(                    1,
            'one',
            'one')

        test(                   -1,
            'negative one',
            'negative one')

        test(                    2,
            'two',
            'two')

        test(                    3,
            'three',
            'three')

        test(                    4,
            'four',
            'four')

        test(                    5,
            'five',
            'five')

        test(                    6,
            'six',
            'six')

        test(                    7,
            'seven',
            'seven')

        test(                    8,
            'eight',
            'eight')

        test(                    9,
            'nine',
            'nine')

        test(                   10,
            'ten',
            'ten')

        test(                   11,
            'eleven',
            'eleven')

        test(                   12,
            'twelve',
            'twelve')

        test(                   13,
            'thirteen',
            'thirteen')

        test(                   14,
            'fourteen',
            'fourteen')

        test(                   15,
            'fifteen',
            'fifteen')

        test(                   16,
            'sixteen',
            'sixteen')

        test(                   17,
            'seventeen',
            'seventeen')

        test(                   18,
            'eighteen',
            'eighteen')

        test(                   19,
            'nineteen',
            'nineteen')

        test(                   20,
            'twenty',
            'twenty')

        test(                   21,
            'twenty-one',
            'twenty-one')

        test(                   22,
            'twenty-two',
            'twenty-two')

        test(                   23,
            'twenty-three',
            'twenty-three')

        test(                   24,
            'twenty-four',
            'twenty-four')

        test(                   25,
            'twenty-five',
            'twenty-five')

        test(                   26,
            'twenty-six',
            'twenty-six')

        test(                   27,
            'twenty-seven',
            'twenty-seven')

        test(                   28,
            'twenty-eight',
            'twenty-eight')

        test(                   29,
            'twenty-nine',
            'twenty-nine')

        test(                   30,
            'thirty',
            'thirty')

        test(                   40,
            'forty',
            'forty')

        test(                   41,
            'forty-one',
            'forty-one')

        test(                   42,
            'forty-two',
            'forty-two')

        test(                   50,
            'fifty',
            'fifty')

        test(                   51,
            'fifty-one',
            'fifty-one')

        test(                   52,
            'fifty-two',
            'fifty-two')

        test(                   60,
            'sixty',
            'sixty')

        test(                   61,
            'sixty-one',
            'sixty-one')

        test(                   62,
            'sixty-two',
            'sixty-two')

        test(                   70,
            'seventy',
            'seventy')

        test(                   71,
            'seventy-one',
            'seventy-one')

        test(                   72,
            'seventy-two',
            'seventy-two')

        test(                   80,
            'eighty',
            'eighty')

        test(                   81,
            'eighty-one',
            'eighty-one')

        test(                   82,
            'eighty-two',
            'eighty-two')

        test(                   90,
            'ninety',
            'ninety')

        test(                   91,
            'ninety-one',
            'ninety-one')

        test(                   92,
            'ninety-two',
            'ninety-two')

        test(                  100,
            'one hundred',
            'one hundred')

        test(                  101,
            'one hundred one',
            'one hundred and one')

        test(                  102,
            'one hundred two',
            'one hundred and two')

        test(                  200,
            'two hundred',
            'two hundred')

        test(                  201,
            'two hundred one',
            'two hundred and one')

        test(                  202,
            'two hundred two',
            'two hundred and two')

        test(                  211,
            'two hundred eleven',
            'two hundred and eleven')

        test(                  222,
            'two hundred twenty-two',
            'two hundred and twenty-two')

        test(                  300,
            'three hundred',
            'three hundred')

        test(                  301,
            'three hundred one',
            'three hundred and one')

        test(                  302,
            'three hundred two',
            'three hundred and two')

        test(                  311,
            'three hundred eleven',
            'three hundred and eleven')

        test(                  322,
            'three hundred twenty-two',
            'three hundred and twenty-two')

        test(                  400,
            'four hundred',
            'four hundred')

        test(                  401,
            'four hundred one',
            'four hundred and one')

        test(                  402,
            'four hundred two',
            'four hundred and two')

        test(                  411,
            'four hundred eleven',
            'four hundred and eleven')

        test(                  422,
            'four hundred twenty-two',
            'four hundred and twenty-two')

        test(                  500,
            'five hundred',
            'five hundred')

        test(                  501,
            'five hundred one',
            'five hundred and one')

        test(                  502,
            'five hundred two',
            'five hundred and two')

        test(                  511,
            'five hundred eleven',
            'five hundred and eleven')

        test(                  522,
            'five hundred twenty-two',
            'five hundred and twenty-two')

        test(                  600,
            'six hundred',
            'six hundred')

        test(                  601,
            'six hundred one',
            'six hundred and one')

        test(                  602,
            'six hundred two',
            'six hundred and two')

        test(                  611,
            'six hundred eleven',
            'six hundred and eleven')

        test(                  622,
            'six hundred twenty-two',
            'six hundred and twenty-two')

        test(                  700,
            'seven hundred',
            'seven hundred')

        test(                  701,
            'seven hundred one',
            'seven hundred and one')

        test(                  702,
            'seven hundred two',
            'seven hundred and two')

        test(                  711,
            'seven hundred eleven',
            'seven hundred and eleven')

        test(                  722,
            'seven hundred twenty-two',
            'seven hundred and twenty-two')

        test(                  800,
            'eight hundred',
            'eight hundred')

        test(                  801,
            'eight hundred one',
            'eight hundred and one')

        test(                  802,
            'eight hundred two',
            'eight hundred and two')

        test(                  811,
            'eight hundred eleven',
            'eight hundred and eleven')

        test(                  822,
            'eight hundred twenty-two',
            'eight hundred and twenty-two')

        test(                  900,
            'nine hundred',
            'nine hundred')

        test(                  901,
            'nine hundred one',
            'nine hundred and one')

        test(                  902,
            'nine hundred two',
            'nine hundred and two')

        test(                  911,
            'nine hundred eleven',
            'nine hundred and eleven')

        test(                  922,
            'nine hundred twenty-two',
            'nine hundred and twenty-two')

        test(                 1000,
            'one thousand',
            'one thousand')

        test(                 1001,
            'one thousand one',
            'one thousand and one')

        test(                 1002,
            'one thousand two',
            'one thousand and two')

        test(                 1023,
            'one thousand twenty-three',
            'one thousand and twenty-three')

        test(                 1034,
            'one thousand thirty-four',
            'one thousand and thirty-four')

        test(                 1456,
            'one thousand four hundred fifty-six',
            'one thousand, four hundred and fifty-six')

        test(                 1567,
            'one thousand five hundred sixty-seven',
            'one thousand, five hundred and sixty-seven')

        test(                 2000,
            'two thousand',
            'two thousand')

        test(                 2001,
            'two thousand one',
            'two thousand and one')

        test(                 2002,
            'two thousand two',
            'two thousand and two')

        test(                 2023,
            'two thousand twenty-three',
            'two thousand and twenty-three')

        test(                 2034,
            'two thousand thirty-four',
            'two thousand and thirty-four')

        test(                 2456,
            'two thousand four hundred fifty-six',
            'two thousand, four hundred and fifty-six')

        test(                 2567,
            'two thousand five hundred sixty-seven',
            'two thousand, five hundred and sixty-seven')

        test(                 3000,
            'three thousand',
            'three thousand')

        test(                 3001,
            'three thousand one',
            'three thousand and one')

        test(                 3002,
            'three thousand two',
            'three thousand and two')

        test(                 3023,
            'three thousand twenty-three',
            'three thousand and twenty-three')

        test(                 3034,
            'three thousand thirty-four',
            'three thousand and thirty-four')

        test(                 3456,
            'three thousand four hundred fifty-six',
            'three thousand, four hundred and fifty-six')

        test(                 3567,
            'three thousand five hundred sixty-seven',
            'three thousand, five hundred and sixty-seven')

        test(                 4000,
            'four thousand',
            'four thousand')

        test(                 4001,
            'four thousand one',
            'four thousand and one')

        test(                 4002,
            'four thousand two',
            'four thousand and two')

        test(                 4023,
            'four thousand twenty-three',
            'four thousand and twenty-three')

        test(                 4034,
            'four thousand thirty-four',
            'four thousand and thirty-four')

        test(                 4456,
            'four thousand four hundred fifty-six',
            'four thousand, four hundred and fifty-six')

        test(                 4567,
            'four thousand five hundred sixty-seven',
            'four thousand, five hundred and sixty-seven')

        test(                 5000,
            'five thousand',
            'five thousand')

        test(                 5001,
            'five thousand one',
            'five thousand and one')

        test(                 5002,
            'five thousand two',
            'five thousand and two')

        test(                 5023,
            'five thousand twenty-three',
            'five thousand and twenty-three')

        test(                 5034,
            'five thousand thirty-four',
            'five thousand and thirty-four')

        test(                 5456,
            'five thousand four hundred fifty-six',
            'five thousand, four hundred and fifty-six')

        test(                 5567,
            'five thousand five hundred sixty-seven',
            'five thousand, five hundred and sixty-seven')

        test(                 6000,
            'six thousand',
            'six thousand')

        test(                 6001,
            'six thousand one',
            'six thousand and one')

        test(                 6002,
            'six thousand two',
            'six thousand and two')

        test(                 6023,
            'six thousand twenty-three',
            'six thousand and twenty-three')

        test(                 6034,
            'six thousand thirty-four',
            'six thousand and thirty-four')

        test(                 6456,
            'six thousand four hundred fifty-six',
            'six thousand, four hundred and fifty-six')

        test(                 6567,
            'six thousand five hundred sixty-seven',
            'six thousand, five hundred and sixty-seven')

        test(                 7000,
            'seven thousand',
            'seven thousand')

        test(                 7001,
            'seven thousand one',
            'seven thousand and one')

        test(                 7002,
            'seven thousand two',
            'seven thousand and two')

        test(                 7023,
            'seven thousand twenty-three',
            'seven thousand and twenty-three')

        test(                 7034,
            'seven thousand thirty-four',
            'seven thousand and thirty-four')

        test(                 7456,
            'seven thousand four hundred fifty-six',
            'seven thousand, four hundred and fifty-six')

        test(                 7567,
            'seven thousand five hundred sixty-seven',
            'seven thousand, five hundred and sixty-seven')

        test(                 8000,
            'eight thousand',
            'eight thousand')

        test(                 8001,
            'eight thousand one',
            'eight thousand and one')

        test(                 8002,
            'eight thousand two',
            'eight thousand and two')

        test(                 8023,
            'eight thousand twenty-three',
            'eight thousand and twenty-three')

        test(                 8034,
            'eight thousand thirty-four',
            'eight thousand and thirty-four')

        test(                 8456,
            'eight thousand four hundred fifty-six',
            'eight thousand, four hundred and fifty-six')

        test(                 8567,
            'eight thousand five hundred sixty-seven',
            'eight thousand, five hundred and sixty-seven')

        test(                 9000,
            'nine thousand',
            'nine thousand')

        test(                 9001,
            'nine thousand one',
            'nine thousand and one')

        test(                 9002,
            'nine thousand two',
            'nine thousand and two')

        test(                 9023,
            'nine thousand twenty-three',
            'nine thousand and twenty-three')

        test(                 9034,
            'nine thousand thirty-four',
            'nine thousand and thirty-four')

        test(                 9456,
            'nine thousand four hundred fifty-six',
            'nine thousand, four hundred and fifty-six')

        test(                 9567,
            'nine thousand five hundred sixty-seven',
            'nine thousand, five hundred and sixty-seven')

        test(                10000,
            'ten thousand',
            'ten thousand')

        test(                10001,
            'ten thousand one',
            'ten thousand and one')

        test(                10002,
            'ten thousand two',
            'ten thousand and two')

        test(                10023,
            'ten thousand twenty-three',
            'ten thousand and twenty-three')

        test(                10034,
            'ten thousand thirty-four',
            'ten thousand and thirty-four')

        test(                10456,
            'ten thousand four hundred fifty-six',
            'ten thousand, four hundred and fifty-six')

        test(                10567,
            'ten thousand five hundred sixty-seven',
            'ten thousand, five hundred and sixty-seven')

        test(                11000,
            'eleven thousand',
            'eleven thousand')

        test(                11001,
            'eleven thousand one',
            'eleven thousand and one')

        test(                11002,
            'eleven thousand two',
            'eleven thousand and two')

        test(                11023,
            'eleven thousand twenty-three',
            'eleven thousand and twenty-three')

        test(                11034,
            'eleven thousand thirty-four',
            'eleven thousand and thirty-four')

        test(                11456,
            'eleven thousand four hundred fifty-six',
            'eleven thousand, four hundred and fifty-six')

        test(                11567,
            'eleven thousand five hundred sixty-seven',
            'eleven thousand, five hundred and sixty-seven')

        test(                 1234,
            'one thousand two hundred thirty-four',
            'one thousand, two hundred and thirty-four')

        test(                 2468,
            'two thousand four hundred sixty-eight',
            'two thousand, four hundred and sixty-eight')

        test(           1234567890,
            'one billion two hundred thirty-four million five hundred sixty-seven thousand eight hundred ninety',
            'one billion, two hundred and thirty-four million, five hundred and sixty-seven thousand, eight hundred and ninety')

        test(        1234567890123,
            'one trillion two hundred thirty-four billion five hundred sixty-seven million eight hundred ninety thousand one hundred twenty-three',
            'one trillion, two hundred and thirty-four billion, five hundred and sixty-seven million, eight hundred and ninety thousand, one hundred and twenty-three')

        test(     1234567890123456,
            'one quadrillion two hundred thirty-four trillion five hundred sixty-seven billion eight hundred ninety million one hundred twenty-three thousand four hundred fifty-six',
            'one quadrillion, two hundred and thirty-four trillion, five hundred and sixty-seven billion, eight hundred and ninety million, one hundred and twenty-three thousand, four hundred and fifty-six')

        test(  1234567890123456789,
            'one quintillion two hundred thirty-four quadrillion five hundred sixty-seven trillion eight hundred ninety billion one hundred twenty-three million four hundred fifty-six thousand seven hundred eighty-nine',
            'one quintillion, two hundred and thirty-four quadrillion, five hundred and sixty-seven trillion, eight hundred and ninety billion, one hundred and twenty-three million, four hundred and fifty-six thousand, seven hundred and eighty-nine')

        test(451234567890123456789,
            'four hundred fifty-one quintillion two hundred thirty-four quadrillion five hundred sixty-seven trillion eight hundred ninety billion one hundred twenty-three million four hundred fifty-six thousand seven hundred eighty-nine',
            'four hundred and fifty-one quintillion, two hundred and thirty-four quadrillion, five hundred and sixty-seven trillion, eight hundred and ninety billion, one hundred and twenty-three million, four hundred and fifty-six thousand, seven hundred and eighty-nine')

        test((10**75) + 1,
            '1000000000000000000000000000000000000000000000000000000000000000000000000001',
            '1000000000000000000000000000000000000000000000000000000000000000000000000001')

if __name__ == '__main__':
    # is_ok imports this to get the test tiebreakers
    inject_test_elections(StarvoteTests, sys.argv[1:])
    unittest.main()
