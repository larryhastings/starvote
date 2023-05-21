# starvote

## A simple STAR vote tabulator

## Copyright 2023 by Larry Hastings

[STAR voting](https://www.starvoting.org/) is a
relatively-new [electoral system](https://en.wikipedia.org/wiki/Electoral_system).
It's simple to vote and simple to tabulate.  While a completely fair and perfect
electoral system is impossible, STAR voting's approach makes reasonable tradeoffs
and avoids the worst electoral system pitfalls.  It's really great!

This module, **starvote**, implements a simple STAR vote tabulator.
To use, `import starvote`, then instantiate a `starvote.Poll` object.
Feed in the ballots using `poll.add_ballot(ballot)`; ballots are `dict` objects,
mapping the candidate to the ballot's vote for the candidate
(an `int` in the range 0 to 5 inclusive).

Once you've added all the ballots, call `poll.result` to compute the winner.
If there's an unbreakable tie, `poll.result` will raise an
`UnbreakableTieError`.  You can get a text description of the tie by calling
`str` on the exception; also, you can get a list of the tied candidates
in its `candidates` attribute.

The following scenarios produce an unbreakable tie:

* If the top two candidates tie during the automated runoff round
  *and* their scores are also a tie.
* If the second and third candidates during the score round tie,
  and their preference scores are also a tie.
* If three or more candiates are tied for first *or* second place
  during the score round.

(These scenarios are highly unlikely with real-world data.)

If you want to see how the vote was tabulated, pass in an argument
to the `print` keyword-only argument to `poll.result`.  This should
be a function that behaves like the builtin `print` function; it
will only ever be called with positional parameters.

Here's an example of computing a poll between Amy, Brian, and Chuck:

```Python
import starvote

poll = starvote.Poll()
poll.add_ballot({'Amy': 1, 'Brian': 3, 'Chuck': 5})
poll.add_ballot({'Amy': 5, 'Brian': 2, 'Chuck': 3})
poll.add_ballot({'Amy': 4, 'Brian': 4, 'Chuck': 5})
winner = poll.result(print=print)
print()
print(f"[Winner]\n{winner}")
```

Here's what the output of this program looks like:

```
[Score round]
  Chuck -- 13 (average 4.33)
  Amy   -- 10 (average 3.33)
  Brian --  9 (average 3.00)
[Automatic runoff round]
  Chuck         -- 2
  Amy           -- 1
  No preference -- 0

[Winner]
Chuck
```

If the module is executed as a script, it will read a single
[CSV file](https://en.wikipedia.org/wiki/Comma-separated_values)
in [*star.vote*](https://star.vote/) format, tabulate, and print
the result.  For example, you can run this from the root of the
source-code repository:

```
% python3 -m starvote sample_polls/sample_poll_automatic_runoff_breakable_tie.csv
```

to see how **starvote** handles a tie during the automatic runoff round.

## Multiple-winner elections

**starvote** also implements the
[Bloc STAR](https://www.starvoting.org/multi_winner)
and
[Proportional STAR](https://www.starvoting.org/star-pr)
(aka [Allocated Score](https://electowiki.org/wiki/Allocated_Score))
variants of STAR for multi-winner elections.  Simply
instantiate your `Poll` object passing in the enum constant
`starvote.BLOC_STAR` or `starvote.Proportional_STAR`
for the `variant` parameter, and the number of seats in
the `seats` keyword-only parameter:

```Python
poll = starvote.Poll(variant=starvote.BLOC_STAR, seats=2)
```

This changes `poll.result` to return a list of winners instead
of a single winner.

You can experiment with these with the command-line version of the
module, too.  You can specify the variant with `-v` and the
number of seats with `-s`:

```
% python3 -m starvote -v BLOC_STAR -s 2 sample_polls/starvote_ballots_dd1wc4yx_20230520050413.csv
```

### Warning

I haven't found a test corpus for either of these voting methods.
I'm following the rules, as best I can, and the results I'm getting
make sense.  But, so far, my implementations of BLOC STAR
and Proportional STAR definitely could be wrong.

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
[https://star.vote/](https://star.vote/).  The licensing of these
sample ballots is unclear, but they're assumed to be public-domain
or otherwise freely redistributable.

## Changelog

**1.3** *2023/05/21*

* Added support for
  [Proportional STAR](https://www.starvoting.org/star-pr)
  polls.  The only visible external change is the new
  `Proportional_STAR` enum value.
* Renamed the `winners` parameter on the `Poll` constructor to `seats`.
  Sorry to break your code, all zero people planetwide who already started
  using the parameter!  But this new name is a big improvement.

**1.2** *2023/05/20*

* Add support for [Bloc STAR](https://www.starvoting.org/multi_winner)
  polls:

  * Added `PollVariant` enum containing `STAR` and `BLOC_STAR` values.
  * Added `variant` and `winners` parameters to `Poll`.

* Add the list of tied candidates to the `UnbreakableTieError`
  exception as the new `candidates` attribute.

**1.1** *2023/05/20*

* Bugfix: raise `UnbreakableTieError` if there's a three-way
  tie for *second* place.  Previously **starvote** only noticed
  if there was a three-way tie for *first* place.
* Added sample output for every sample poll in `sample_polls/`.
  These outputs have been confirmed correct by inspection, and
  could in the future be used as part of an automated test suite.

**1.0** *2023/05/20*

* Initial release.
