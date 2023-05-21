#!/usr/bin/env python3

__doc__ = "A simple STAR vote tabulator"

__version__ = "1.2"

__all__ = ['Poll', 'UnbreakableTieError', 'PollVariant', 'STAR', 'BLOC_STAR']

import enum
import math

try:
    from enum import global_enum
except ImportError:
    def global_enum(fn):
        return fn

class UnbreakableTieError(ValueError):
    def __init__(self, description, *candidates):
        super().__init__(description)
        self.candidates = tuple(candidates)


@global_enum
class PollVariant(enum.Enum):
    STAR = 1
    BLOC_STAR = 2
    # Proportional_STAR = 3

STAR = PollVariant.STAR
BLOC_STAR = PollVariant.BLOC_STAR
# Proportional_STAR = PollVariant.Proportional_STAR


class Poll:
    def __init__(self, variant=STAR, *, winners=1):
        self.variant = variant
        self.winners = winners

        self.candidates = {}
        self.ballots = []

        if variant == STAR:
            if winners != 1:
                raise ValueError("winners must be 1 when using variant STAR")
        else:
            if winners == 1:
                raise ValueError("winners must be > 1 when using variant " + str(variant).rpartition(".")[2])

    def add_candidate(self, name):
        self.candidates[name] = 0

    def add_ballot(self, ballot):
        for candidate, score in ballot.items():
            assert isinstance(score, int)
            assert 0 <= score <= 5
            if candidate not in self.candidates:
                self.add_candidate(candidate)
            self.candidates[candidate] += score
        self.ballots.append(ballot)

    @staticmethod
    def compute_widths(ballots, scores):
        # scores should be an array of [score, candidate] iterables.
        candidate_width = -1
        largest_score = -1
        largest_average = -1
        ballots_count = len(ballots)
        for score, candidate in scores:
            candidate_width = max(candidate_width, len(candidate))
            largest_score = max(largest_score, score)
            average = score / ballots_count
            largest_average = max(largest_average, average)
        score_width = math.floor(math.log10(largest_score)) + 1
        average_width = math.floor(math.log10(largest_average)) + 1  # .xx
        return candidate_width, score_width, average_width

    # of these 2 candidates, which is preferred?
    # used for the automatic runoff, and to resolve
    # two-way ties in the score round.
    @staticmethod
    def preference(ballots, candidate0, candidate1, *, when=None, print=None):
        scores = [ [0, candidate0], [0, candidate1] ]
        for ballot in ballots:
            score0 = ballot.get(candidate0, 0)
            score1 = ballot.get(candidate1, 0)
            if score0 > score1:
                scores[0][0] += 1
            elif score1 > score0:
                scores[1][0] += 1
        scores.sort()

        no_preference = len(ballots) - (scores[0][0] + scores[1][0])
        scores.insert(0, [no_preference, "No preference"])

        if print:
            candidate_width, score_width, average_width = Poll.compute_widths(ballots, scores)
            for score, candidate in reversed(scores):
                print(f"  {candidate:<{candidate_width}} -- {score:>{score_width}}")

        if scores[1][0] == scores[2][0]:
            raise UnbreakableTieError(f"two-way tie during {when} between {candidate0} and {candidate1}", candidate0, candidate1)
        winner = scores[2][1]

        return winner

    def result(self, *, print=None):
        winners = []
        candidates = self.candidates
        ballots = self.ballots

        if not candidates:
            raise ValueError("no candidates")

        if self.variant == STAR:
            if len(candidates) == 1:
                winners = list(candidates)
                winner = winners[0]
                print("Only one candidate, returning winner " + winner)
                return winner
            round_text_format = ""
        else:
            if len(candidates) <= self.winners:
                raise ValueError(f"not enough candidates, need {self.winners}, have {len(candidates)}")
            if len(candidates) == self.winners:
                winners = list(candidates)
                print(f"Only {self.winners} candidates, returning all candidates as winners")
                return winners
            # we're gonna modify ballots, so, make copies
            ballots = [dict(b) for b in ballots]
            candidates = dict(candidates)
            round_text_format = " {polling_round}"

        for polling_round in range(1, self.winners+1):
            candidates_count = len(candidates)
            ballots_count = len(ballots)
            assert candidates_count

            round_text = round_text_format.format(polling_round=polling_round)

            if print:
                print(f"[Score round{round_text}]")

            # score round
            rankings = [(score, candidate) for candidate, score in candidates.items()]
            rankings.sort()

            def print_rankings(rankings):
                candidate_width, score_width, average_width = self.compute_widths(ballots, rankings)
                total_average_width = average_width + 3

                for score, candidate in reversed(rankings):
                    average = score / ballots_count
                    average = f"{average:>1.2f}"
                    print(f"  {candidate:<{candidate_width}} -- {score:>{score_width}} (average {average:>{total_average_width}})")

            if print:
                print_rankings(rankings)

            top_two = rankings[-2:]
            if candidates_count > 2:
                if (rankings[-3][0] == rankings[-2][0]):
                    if rankings[-2][0] == rankings[-1][0]:
                        candidates = [r[1] for r in rankings[-3:]]
                        description = ", ".join(candidates)
                        first_two, comma, last_one = description.rpartition(",")
                        description = f"{first_two}{comma} and{last_one}"
                        raise UnbreakableTieError(f"unbreakable three-way tie for first in score round{round_text} between " + description, *candidates)
                    if (candidates_count > 3) and (rankings[-4][0] == rankings[-3][0]):
                        candidates = ([r[1] for r in rankings[-4:-1]])
                        description = ", ".join(candidates)
                        first_two, comma, last_one = description.rpartition(",")
                        description = f"{first_two}{comma} and{last_one}"
                        raise UnbreakableTieError(f"unbreakable three-way tie for second in score round{round_text} between " + description, *candidates)
                    if print:
                        print(f"[Resolving two-way tie between second and third in score round{round_text}]")
                    preferred = self.preference(ballots, rankings[-3][1], rankings[-2][1], print=print, when="preference runoff between second and third in score round")
                    if top_two[0][1] != preferred:
                        top_two[0] = rankings[-3]
            if print:
                print(f"[Automatic runoff round{round_text}]")

            try:
                winner = self.preference(ballots, top_two[0][1], top_two[1][1], print=print, when=f"automatic runoff round{round_text}")
            except UnbreakableTieError:
                if print:
                    print(f"[Resolving two-way tie in automatic runoff round{round_text}]")
                    print_rankings(top_two)

                if top_two[0][0] > top_two[1][0]:
                    winner= top_two[0][1]
                elif top_two[1][0] > top_two[0][0]:
                    winner = top_two[1][1]
                else:
                    raise UnbreakableTieError(f"unbreakable tie between {top_two[0][1]} and {top_two[1][1]} in automatic runoff round{round_text}", top_two[0][1], top_two[1][1])
            if print:
                print(f"[Winner round{round_text}]")
                print(f"  {winner}")
            winners.append(winner)

            if self.winners > 1:
                for b in ballots:
                    if winner in b:
                        del b[winner]
                assert winner in candidates
                del candidates[winner]

        if self.variant == STAR:
            assert len(winners) == 1
            return winner

        assert len(winners) == self.winners
        return winners

