## Test elections

The `starvote_ballots_*.csv` files were downloaded from [https://star.vote](https://star.vote)
in May 2023, and the `starvote_ballots_*.pdf` files are the result of "Save to PDF" saving the
matching web pages, showing results.  The site doesn't make it clear what the files and data
can be used for, but the STAR voting team is generally pretty open and easygoing, so I assume
redistribution is okay.

The `*.starvote` files were hand-written by Larry Hastings.

`test_elections_reweighted_range_3_seats_max-score_10.html` was downloaded from
[https://rangevoting.org/RRVr.html](https://rangevoting.org/RRVr.html), and
`test_elections_reweighted_range.starvote` models the election
shown on that page.

The `*.txt` files are the expected results from the matching `*.csv` or `*.starvote`
test election files; these `*.txt` files are used by the test runner to confirm the
election was tabulated correctly.  The `*.csv` files were tabulated with these defaults:

* `method` is STAR voting
* `tiebreaker` is `None`
* `verbosity` is 1
