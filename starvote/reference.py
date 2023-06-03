##
## The next 55 lines of code are the reference implementation of
## Allocated Score Voting, as found on the official STAR Voting site:
##   https://www.starvoting.org/technical_specifications
##
## Also published at:
##   https://electowiki.org/wiki/Allocated_Score
##
## Some notes:
##
## The reference implementation doesn't attempt to break ties,
## or even notice when they happen.  If there's a tie in the
## score round, this implementation blithely picks the first
## candidate in the array tied for first
## (via 'weighted_scores.sum().idxmax()').
##
## Also, it uses floats all over the place.  In practice this
## is fine, but makes it hard to compare things with precision.
## (You couldn't necessarily compute that the votes you
## allocated + the votes remaining *exactly equals* the original
## total votes.)
##
## However, note that their Hare quota is a float, which
## is proper, as long as you're using floats.  (Droop quota
## mandataes an integer, but Hare quota does *not*.)
##
## --------------------------------------------------------

import pandas as pd
import numpy as np

def Allocated_Score(K, W, S): # pragma: no cover

    #Normalize score matrix
    ballots = pd.DataFrame(S.values/K, columns=S.columns)

    #Find number of voters and quota size
    V = ballots.shape[0]
    quota = V/W
    ballot_weight = pd.Series(np.ones(V),name='weights')

    #Populate winners in a loop
    winner_list = []
    while len(winner_list) < W:

        weighted_scores = ballots.multiply(ballot_weight, axis="index")

        #Select winner
        w = weighted_scores.sum().idxmax()

        #Add winner to list
        winner_list.append(w)

        #remove winner from ballot
        ballots.drop(w, axis=1, inplace=True)

        #Create lists for manipulation
        cand_df = pd.concat([ballot_weight,weighted_scores[w]], axis=1).copy()
        cand_df_sort = cand_df.sort_values(by=[w], ascending=False).copy()

        #find the score where a quota is filled
        split_point = cand_df_sort[cand_df_sort['weights'].cumsum() < quota][w].min()

        #Amount of ballot for voters who voted more than the split point
        spent_above = cand_df[cand_df[w] > split_point]['weights'].sum()

        #Allocate all ballots above split point
        if spent_above>0:
            cand_df.loc[cand_df[w] > split_point, 'weights'] = 0.0

        #Amount of ballot for voters who gave a score on the split point
        weight_on_split = cand_df[cand_df[w] == split_point]['weights'].sum()

        #Fraction of ballot on split needed to be spent
        if weight_on_split>0:
            spent_value = (quota - spent_above)/weight_on_split

            #Take the spent value from the voters on the threshold evenly
            cand_df.loc[cand_df[w] == split_point, 'weights'] = cand_df.loc[cand_df[w] == split_point, 'weights'] * (1 - spent_value)

        ballot_weight = cand_df['weights'].clip(0.0,1.0)

    return winner_list

## --------------------------------------------------------



##
## Implement a standard scorevote functional interface on top of
## the Allocated Score Voting (reference) implementation.
##
## To make Allocated Score Voting (reference) available in starvote:
##
##     import starvote.starvoting
##     starvote.starvoting.monkey_patch()
##

import starvote

def allocated_score_voting_reference(ballots, *,
    maximum_score=starvote._DEFAULT_MAXIMUM_SCORE,
    print=starvote._DEFAULT_PRINT,
    seats,
    tiebreaker=None,
    verbosity=starvote._DEFAULT_VERBOSITY,
    ):
    """
    Tabulates an election using the reference implementation
    of Allocated Score Voting from the STAR voting website.
        https://www.starvoting.org/technical_specifications

    Returns a list of results.

    Takes one required positional parameter:
    * "ballots" should be an iterable of ballot dicts.

    Also accepts five optional keyword-only parameters:
    * "maximum_score" specifies the maximum score allowed
      per vote, default 5.
    * "print" is a function called to print output.
    * "seats" specifies the number of seats, must be > 1.
    * "tiebreaker" specifies how to break ties.
      Currently must be None.
    * "verbosity" is an int specifying how much output
      you want; 0 indicates no output, 1 prints results.
    """

    if tiebreaker is not None: # pragma: no cover
        raise ValueError("tiebreaker not supported")

    candidates = starvote._candidates(ballots)
    ballots_array = [[ballot.get(candidate, 0) for candidate in candidates] for ballot in ballots]

    K = maximum_score
    W = seats
    S = pd.DataFrame(ballots_array, index=candidates)

    winners = Allocated_Score(K, W, S)
    winners = [candidates[winner] for winner in winners]
    starvote._attempt_to_sort(winners)

    if verbosity: # pragma: no cover
        plural = "" if len(winners) == 1 else "s"
        print(f"[Winner{plural}]")
        for winner in winner_names:
            print(f"  {winners}")

    return winners


Allocated_Score_Voting_reference = allocated_r = starvote.Method("Allocated Score Voting (reference)", allocated_score_voting_reference, True)
methods = {
    'Allocated Score Voting (reference)': Allocated_Score_Voting_reference,
    'allocated_r': Allocated_Score_Voting_reference,
    }

__all__ = [
    "Allocated_Score_Voting_reference", # Method
    "allocated_r", # Method (nickname)
    "allocated_score_voting_reference", # function
    ]

def monkey_patch():
    """
    Adds the reference implementation of Proportional STAR from the STAR voting website
    to the available electoral systems provided by starvote, under the name
    'Reference Proportional STAR'.
    """
    starvote.methods.update(methods)

    g = globals()

    for name in __all__:
        symbol = g[name]
        setattr(starvote, name, symbol)
        starvote.__all__.append(name)
