# Clarifying STAR Voting

Although the STAR Voting procedure is very clear and straightforward
when there are no ties, things start to get muddy when ties rear their
ugly heads.  This document describes some scenarios that I think the
STAR Voting documentation doesn't make clear how to resolve,
along with my decisions on how to resolve them.

Official STAR Voting folks: if I goofed this up, let me know and I'll
fix it!


## Rationalizing Three Tiebreaker Protocols

The STAR Voting web site publishes *three* different tiebreaker protocols:

1. The first is named the "Simple Tie-breaker Protocol", or "Simple" for short.
2. The second is named the "Official Tiebreaker Protocol", or "Official" for short.
3. The third is part of the
   ["STAR Voting Technical Specifications",](https://www.starvoting.org/technical_specifications)
   or "Technical" for short.

The bad news is: they don't all match.  To be fair, one is intentionally
"simple", and it's intentionally simpler than the other two.  But the other
two seem like they should be the same... and they aren't.

The first two, the "Simple Tie-breaker Protocol" and the "Official Tiebreaker
Protocol", are both on the
[Q: How are ties in STAR Voting broken?](https://www.starvoting.org/ties)
page, part of
[the official STAR Voting FAQ.](https://www.starvoting.org/faq)
They're intended for different uses--you wouldn't use both on the same
election.  And the page describes when you might use one or the other,
as follows:

> In the event that an election has already been conducted but no protocol
> was specified, and an election tool that handles ties automatically
> wasn't used, the Simple Tiebreaker Protocol below should be used. We also
> recommend the Simple Tiebreaker Protocol for hand counted elections hosted
> by volunteers or lay people because of its simplicity and transparency.
>
> Otherwise, we recommend the Official STAR Voting Ties Protocol, which is
> the stock implementation included on all STAR Elections voting platforms.
> The official protocol is a bit more complex, but is exceptionally good at
> breaking ties wherever possible, even in small elections with only a
> few voters.

The third is part of a large technical document describing in exact language
every detail of STAR Voting.  (Including, by the way, the fact that it should
be spelled "STAR Voting", with capital S-T-A-R and V.)

Let's examine the three different protocols, then I'm going to draw some
conclusions.


## Simple Tiebreaker Protocol

This is the "Simple Tiebreaker Protocol" defined on the
[Q: How are ties in STAR Voting broken?](https://www.starvoting.org/ties)
page.  The text in the "Step" sections below is verbatim from that page.

Note: The page spells this "Simple Tie-breaker Protocol" in the heading,
but spells it "Simple Tiebreaker Protocol" everywhere else.  I've
elected for the latter spelling, as "tiebreaker" is generally regarded
as properly being one word.

### Step 1

If two candidates receive the same total score in the scoring round,
the tie should be broken in favor of the candidate who was preferred
(scored higher) by more voters, if possible.

### Step 2

Ties in the Runoff Round should be broken in favor of the candidate
who was scored higher if possible.

### Step 3

In the event that a tie can not be resolved as above,
the tie will be broken randomly with a method such as a coin toss
or by drawing a name out of a hat.


## Official Tiebreaker Protocol

This is the "Official Tiebreaker Protocol" defined on the
[Q: How are ties in STAR Voting broken?](https://www.starvoting.org/ties)
page.  The "Step" sections below are verbatim from that page.


### Step 1

Ties in the scoring round should be determined in favor of the candidate
who was preferred (scored higher) by more voters.  If there are only two
candidates this will be the majority preferred candidate.  If there are
multiple candidates who are scored equally, ties are broken by comparing
the tied candidates head to head and eliminating the candidate(s) who
lost the most match-ups. This can be repeated with the remaining tied
candidates as needed until two candidates can advance to the runoff.

### Step 2

Ties in the Runoff Round should be broken in favor of the candidate
who was scored higher if possible.

### Step 3

In the event that a tie can not be resolved as above, break the tie in
favor of the tied candidate who received the most five star ratings.
If this does not fully resolve the tie, eliminate the candidate(s) with
the least five star ratings.

### Step 4

In the event that a tie can not be resolved as above,
the tie will be broken randomly with a method such as a coin toss
or by drawing a name out of a hat.  If needed, repeat the tiebreaker
protocol from the top with remaining tied candidates until the
election is complete.


## STAR Voting Technical Specifications

This was copied out of the
[STAR Voting Technical Specifications](https://www.starvoting.org/technical_specifications)
document.
The text below is section **2.b** from that page, copied verbatim.

### 2.b.

Ties will be broken as follows:

### 2.b.1.

Ties in the scoring round should be determined in favor of the
candidate who was preferred (scored higher) by more voters.  If
there are only two candidates this will be the majority preferred
candidate, if there are multiple tied candidates this will be the
candidate(s) preferred over all other candidates.

### 2.b.2.

Ties in the Runoff Round should be broken in favor of the
candidate who was scored higher if possible.

### 2.b.3

In the event that a tie can not be resolved as above, the election
will be called as a tie and broken randomly, unless a further tie
breaking procedure was adopted in advance of the election and was
publicly disclosed.


## My analyis

I'm trying to do the right thing here.

Obviously STAR Voting naming something the *"Official* Tiebreaker
Protocol" is a strong indication that they want you to use it.
Right off the bat, we can dispense with "Simple".  Clearly we
should use a more sophisticated protocol.

Why don't the other two approaches match?  My guess is,
the "Technical" protocol is an early version of what became
the "Official" protocol.  Much of the wording is exactly the
same.  However, "Official" contains some new steps:

* "the most five-star votes", and
* "eliminating the candidate(s) who lost the most match-ups".

So I'm assuming "Official" is the latest, most-correct
version, and I'm basing my approach on that.

### My clarification for the Scoring Round

Now let's examine the Scoring Round and how to break ties in it.
First, here's the text from "Technical" describing how to
execute the Scoring Round:

> *Scoring Round:* For each position for which a candidate
> appears on the ballot, the vote tally system will calculate
> the sum total of the scores received by each candidate and
> then determine the two finalists who received the greatest
> total scores.

And here's the section from "Official" describing how to break
ties.

> Ties in the scoring round should be determined in favor of the candidate
> who was preferred (scored higher) by more voters.  If there are only two
> candidates this will be the majority preferred candidate.  If there are
> multiple candidates who are scored equally, ties are broken by comparing
> the tied candidates head to head and eliminating the candidate(s) who
> lost the most match-ups. This can be repeated with the remaining tied
> candidates as needed until two candidates can advance to the runoff.

I think it's strange how the tiebreaking section talks about
*"the candidate".*  The Scoring Round advances *two* candidates
to the next round.  So you're actually looking for two candidates,
not one.

Also, here are two edge cases which I think the documents leave
ambiguous, and describe how I chose to resolve the them.

First: if exactly two candidates tie for first in the score
round, that's "a tie".  Should they both advance to the
automatic runoff round?  I think obviously yes, although I
feel like the instructions are a little unclear.

Second: if there's a three-way tie for first in the score
round, you proceed to the tiebreakers.  If you're still
looking for two candidates, and you run a tiebreaker, and
exactly two candidates tie for first, should they both
advance to the automatic runoff round?  Again, I think the
answer is obviously yes.  But both the "Official" and
"Technical" tiebreaker protocols make no mention of it.

## My implementation of STAR Voting and BLOC Star Voting

Here's a text description of *my* implementation of STAR Voting.
As far as I know, I'm implementing STAR Voting correctly,
obeying the rules as laid down in the "Technical" document,
though amending that with the "Official" tiebreaker protocol.
This description also integrates my resolutions for what I
consider to be the ambiguous scenarios as described above.


### Scoring Round

This starts with an arbitrary number of candidates.
Its goal is to "advance" two candidates to the
Automatic Runoff Round.

First, handle elections with small numbers
of candidates.

* If you have zero candidates, it's an error--
  you can't run an election without candidates.
* If you have only one candidate, that candidate
  automatically wins the election.
* If you have only two candidates, they both
  automatically win the Scoring Round, and advance.
  Proceed to the Automatic Runoff Round.

If you start with three or more candidates, you start
with the Scoring Round, and you "need two winners".
The two winners of the Scoring Round will advance
to the Automatic Runoff Round.
Iterate through the "steps" described below.  For
each "step":

* Each step computes a "score" for every candidate.
  Sort these scores with highest scores first.  The
  highest scoring candidate(s) are in first place.
  Candidates that have the same score are tied for
  that place.
* If you "need two winners", and two candidates tie for
  first, both those candidates advance.  You discard
  all other candidates and proceed to the Automatic
  Runoff Round.
* If you "need two winners", and there's one candidate
  in first place and one candidate in second place,
  both those candidates advance.  You discard all other
  candidates and proceed to the Automatic Runoff Round.
* If you "need two winners", and there's one candidate
  in first place and a tie for second place, the
  candidate in first place advances and is no longer
  considered "in the running" in the Scoring Round.
  (When you "discard all other candidates", that doesn't
  include this candidate.)
  You now only "need one winner".  The candidates tied
  for second stay in the running.  Discard all
  candidates who placed third or lower and proceed to
  the next step.
* If you "need one winner", and there's exactly
  one candidate in first place, that candidate advances.
  Discard all other candidates and proceed to the
  Automatic Runoff Round.
* If you "need one winner", and there's a tie for
  first, all candidates tied for first stay in the
  running.  Discard all other candidates and
  proceed to the next step.

#### Scoring Round, Step 1

At the start of the Scoring round, you "need two winners".

Sum the scores of all candidates.  Each candidate's
score for this round is the sum of their scores.

#### Scoring Round, Step 2

For every ballot, perform a "head-to-head" matchup between
every pair of candidates.  A candidate "wins" this matchup
if their score is higher than the other candidate's.  Each
candidate's score from this round is the count of matchups
they won.

### Scoring Round, Step 3

Count the number of five-star scores received by each
candidate.  Each candidate's score from this round is the
count of five-star scores they received.

### Scoring Round, Step 4

Randomly select the number of candidates you need from
the remaining candidates.


## Automatic Runoff Round

If you reach the Automatic Runoff Round, by definition
you have exactly two candidates still in the running.
In this round you only need one winner.

* Each step computes a "score" for both candidates.
  Sort these scores, highest scores first.
* If the two candidates have different scores,
  the candidate with the higher score wins the election.
* If both candidates have the same score, they're tied.
  They both stay in the running and you proceed to the
  next step.

### Automatic Runoff Round, Step 1

For every ballot, perform a "head-to-head" matchup between
the two candidates.  A candidate "wins" this matchup
if their score is higher than the other candidate's.
Each candidate's score from this round is the count of
matchups they won.

### Automatic Runoff Round, Step 1

Sum the scores of the two candidates.  Each candidate's
score for this round is the sum of their scores.

### Automatic Runoff Round, Step 3

Count the number of five-star scores received by each
candidate.  Each candidates' score from this round is the
count of five-star scores they received.

### Automatic Runoff Round, Step 4

Randomly select one of the two candidates to be a winner.


## Bloc STAR Voting

My implementation of Bloc STAR Voting is literally
**N** iterations of STAR Voting, where **N** is
the number of seats I need to fill.

### Electowiki's shortcut for Bloc STAR

Electowiki has a page about STAR Voting, and it also
discusses Bloc STAR.  On that page in
[the *Complete ranking* section](https://electowiki.org/wiki/STAR_voting#Complete_ranking)
it says:

> A STAR voting ranking of candidates can be done by using the
> Bloc STAR voting procedure: find the STAR winner, put them in
> 1st place, then remove them from the election, and repeat,
> putting each consecutive STAR winner in a lower rank than all
> previous STAR winners. Optionally, if two candidates tie in the
> automatic runoff during this procedure, they can both be put as
> tied for the same rank, and then both are removed from the
> election. Note that while STAR voting can never put someone
> ranked 3rd or worse by Score voting as 1st i.e. its winner
> (when run on the same ballots; this is because only the two
> candidates ranked highest by Score voting can enter the STAR
> automatic runoff and thus even be eligible to win), it can put
> the candidate Score ranked 1st (i.e. the Score winner) as its
> last place candidate using this procedure, since the Score
> winner may be a Condorcet loser i.e. a candidate who would
> lose an automatic runoff against any other candidate.

Let me draw your attention to the second sentence:

> Optionally, if two candidates tie in the automatic runoff
> during this procedure, they can both be put as tied for the
> same rank, and then both are removed from the election.

I don't follow the rest of that paragraph, but I assume it's
basically telling you this isn't a good idea.  Basically,
one of the first two winners could be a
[Condorcet loser](https://en.wikipedia.org/wiki/Condorcet_loser_criterion)--they
would loser in a head-to-head runoff against any
other candidate.

I realize that, if two candidates tie all the way until the
end of the Automatic Runoff Round, they really are *tied,*
and arguably either one could be the winner.  And in real-world
elections, if two candidates tie like this, it's virtually
guaranteed that they'll both eventually get a seat.

But the rules of STAR Voting are clear and specific: if two
candidates exhaust the tiebreaker steps of the Automatic Runoff
Round, you should randomly choose *one.*  And if the one you
didn't choose is a "Condorcet loser", then they're not getting
a seat.  Giving a seat to both candidates is arguably more
consistent, which is appealing, but my goal is to implement
the letter of the law whenever possible.

I have a test election that demonstrates this, in
`test_elections/test_election_bloc_star_and_electowiki.starvote`.
