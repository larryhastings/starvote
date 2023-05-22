# starvote

## A simple STAR vote tabulator

## Copyright 2023 by Larry Hastings

[STAR voting](https://www.starvoting.org/) is a
relatively-new [electoral system](https://en.wikipedia.org/wiki/Electoral_system).
It's simple to vote and simple to tabulate.  While a completely fair and perfect
electoral system is impossible, STAR voting's approach makes reasonable tradeoffs
and avoids the worst electoral system pitfalls.  It's really great!

## A quick STAR voting primer

When you vote using STAR voting, your ballot looks something like this:

```
STAR voting ballot

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

To figure out who won, you apply the **STAR** methd: **S**core,
**T**hen **A**utomatic **R**unoff.

In the first round, the score round, you add up the scores of all the
candidates.  The top two scoring candidates automatically advance to
the second round.

In the second round, you examine every ballot to see which of the
two remaining candidates they preferred.  If one has a higher score,
that ballot prefers that candidate.  If the ballot scored both
candidates the same, they have no preference.  The candidate that
was preferred by more ballots wins the election.  It's that simple!

## What's so good about STAR voting?

Electoral systems are a surprisingly deep topic.  They've been studied
for hundreds of years, and there are many many different approaches.
There are a number of desirable properties *and* undesirable properties
that electoral systems can have.  And, bad news: it's impossible for
there to be one best-possible voting system.  There are mutually
exclusive desirable properties.  You can't make a one-size-fits-all
system that avoids every problem.

STAR voting avoid the worst problems of electoral systems.
The remaining undesirable properties were chosen as the least-bad
option.

Here are some desirable properites STAR voting displays:

* It's [monotonic.](https://en.wikipedia.org/wiki/Monotonicity_criterion)
  Giving a candidate a higher score can never hurt them, and
  giving a candidate a lower score can never help them.  (And yes,
  this is not always true of voting systems.  The increasingly popular
  [Instant Runoff Voting](https://en.wikipedia.org/wiki/Instant-runoff_voting)
  fails this; it's possible to hurt a candidate you like by giving them
  a higher score.)
* It's [resolvable.](https://en.wikipedia.org/wiki/Resolvability_criterion)
  Ties are unlikely.
* It complies with the [majority loser criterion.](https://en.wikipedia.org/wiki/Majority_loser_criterion)
  If a majority of candidates like one candidate the least, that candidate will
  never win a STAR voting election.


Here are some desirable properties STAR voting doesn't have,
or undesirable properites STAR voting has:

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
  will never win a STAR election.)
* It doesn't satisfy the [majority criterion.](https://en.wikipedia.org/wiki/Majority_criterion)
  The majority criterion requires: *"if one candidate is ranked first by a majority of voters,
  that candidate must win".*
* It doesn't satisfy the [later-no-harm criterion.](https://en.wikipedia.org/wiki/Later-no-harm_criterion)
  Later-no-harm requires that if you've already expressed a preference for a candidate on your
  ballot, you shouldn't be able to harm that candidate by expressing another preference for
  another candidate later on the ballot.  STAR fails this; giving a higher vote to a
  less-preferred candidate might mean that your more-preferred candidate doesn't get
  elected.  The STAR voting team [wrote an essay on why they gave up on this criterion.](https://www.starvoting.org/pass_fail)
  The short version is: electoral systems that satisfy later-no-harm generally also
  exhibit
  [the spoiler effect,](https://en.wikipedia.org/wiki/Vote_splitting#%22Spoiler_effect%22)
  which is a worse property.  But achieving later-no-harm *and* avoiding the spoiler effect
  makes your electoral system even worse!




## starvote

This module, **starvote**, implements a simple STAR vote tabulator.
To use, `import starvote`, then instantiate a `starvote.Poll` object.
Feed in the ballots using `poll.add_ballot(ballot)`; ballots are `dict` objects,
mapping the candidate to the ballot's score for that candidate.
(By convention, STAR ballot scores are in the range from 0 to 5 inclusive.
You may change the maximum score with the `max_score` keyword-only parameter
to the `Poll` constructor.)

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

(These scenarios are unlikely with real-world data.)

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
in [`https://star.vote/`](https://star.vote/) format, tabulate, and print
the result.  For example, you can run this from the root of the
source-code repository:

```
% python3 -m starvote sample_polls/sample_poll_automatic_runoff_breakable_tie.csv
```

to see how **starvote** handles a tie during the automatic runoff round.

## Multiple-winner elections

**starvote** also implements several multi-winner electoral systems:

* [Bloc STAR](https://www.starvoting.org/multi_winner),
* [Proportional STAR](https://www.starvoting.org/star-pr)
  (aka "STAR-PR", aka [Allocated Score](https://electowiki.org/wiki/Allocated_Score)),
  a [proportional representation](https://en.wikipedia.org/wiki/Proportional_representation)
  electoral system,
* and [Reweighted Range Voting](https://rangevoting.org/RRV.html)
  (aka "RRV"),
  an alternative proportional electoral system.
  Not a STAR variant per se, but the ballot and voting mechanism
  is identical to a STAR ballot.

Simply
instantiate your `Poll` object passing in the enum constant
`starvote.Bloc_STAR`, `starvote.Proportional_STAR`,
or `starvote.Reweighted_Range`
for the `variant` parameter, and the number of seats in
the `seats` keyword-only parameter:

```Python
poll = starvote.Poll(variant=starvote.Bloc_STAR, seats=2)
```

This changes `poll.result` to return a list of winners instead
of a single winner.

You can experiment with these with the command-line version of the
module, too.  You can specify the variant with `-v`,
the number of seats with `-s`,
and the maximum score with `-m`:

```
% python3 -m starvote -v Reweighted_Range -s 3 -m 10 sample_polls/sample_poll_reweighted_range_3_seats.csv
```

### Warning

I haven't found a test corpus for either of the STAR multi-winner
voting methods.
I'm following the rules, as best I can, and the results I'm getting
make sense.  But, so far, my implementations of Bloc STAR
and Proportional STAR definitely could be wrong.

(I do have one sample vote for )

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

**1.5** - *2023/05/22*

* Added support for
  [Reweighted Range Voting](https://rangevoting.org/RRV.html),
  an attractive alternative to Proportional STAR.
  Like STAR-PR, RRV is a proportional representation electoral
  system.  But RRV is simpler to understand, simpler to
  implement, and it never throws away votes.
  Thanks to Tim Peters for pointing me in this direction.
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
