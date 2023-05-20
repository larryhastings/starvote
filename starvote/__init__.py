#!/usr/bin/env python3

__doc__ = "A simple STAR vote tabulator"

__version__ = "1.1"

import math

__all__ = ['Poll', 'UnbreakableTieError']

class UnbreakableTieError(ValueError):
    pass

class Poll:
    def __init__(self):
        self.candidates = {}
        self.ballots = []

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

    def compute_widths(self, scores):
        # scores should be an array of [score, candidate] iterables.
        candidate_width = -1
        largest_score = -1
        largest_average = -1
        ballots_count = len(self.ballots)
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
    def preference(self, candidate0, candidate1, *, when=None, print=None):
        scores = [ [0, candidate0], [0, candidate1] ]
        for ballot in self.ballots:
            score0 = ballot.get(candidate0, 0)
            score1 = ballot.get(candidate1, 0)
            if score0 > score1:
                scores[0][0] += 1
            elif score1 > score0:
                scores[1][0] += 1
        scores.sort()

        no_preference = len(self.ballots) - (scores[0][0] + scores[1][0])
        scores.insert(0, [no_preference, "No preference"])

        if print:
            candidate_width, score_width, average_width = self.compute_widths(scores)
            for score, candidate in reversed(scores):
                print(f"  {candidate:<{candidate_width}} -- {score:>{score_width}}")

        if scores[1][0] == scores[2][0]:
            raise UnbreakableTieError(f"two-way tie during {when} between {candidate0} and {candidate1}")
        winner = scores[2][1]

        return winner

    def result(self, *, print=None):
        candidates_count = len(self.candidates)
        ballots_count = len(self.ballots)
        if not candidates_count:
            raise ValueError("no candidates")
        if print:
            print("[Score round]")

        # score round
        rankings = [(score, candidate) for candidate, score in self.candidates.items()]
        rankings.sort()

        def print_rankings(rankings):
            candidate_width, score_width, average_width = self.compute_widths(rankings)
            total_average_width = average_width + 3

            for score, candidate in reversed(rankings):
                average = score / ballots_count
                average = f"{average:>1.2f}"
                print(f"  {candidate:<{candidate_width}} -- {score:>{score_width}} (average {average:>{total_average_width}})")

        if print:
            print_rankings(rankings)

        if candidates_count == 1:
            for winner in self.candidates:
                if print:
                    print(f"  Only one candidate, returning winner {winner!r}")
                return winner

        top_two = rankings[-2:]
        if candidates_count > 2:
            if (rankings[-3][0] == rankings[-2][0]):
                if rankings[-2][0] == rankings[-1][0]:
                    candidates = ", ".join(r[1] for r in rankings[-3:])
                    first_two, comma, last_one = candidates.rpartition(",")
                    candidates = f"{first_two}{comma} and{last_one}"
                    raise UnbreakableTieError("unbreakable three-way tie for first in score round between " + candidates)
                if (candidates_count > 3) and (rankings[-4][0] == rankings[-3][0]):
                    candidates = ", ".join(r[1] for r in rankings[-4:-1])
                    first_two, comma, last_one = candidates.rpartition(",")
                    candidates = f"{first_two}{comma} and{last_one}"
                    raise UnbreakableTieError("unbreakable three-way tie for second in score round between " + candidates)
                if print:
                    print("[Resolving two-way tie between second and third in score round]")
                preferred = self.preference(rankings[-3][1], rankings[-2][1], print=print, when="preference runoff between second and third in score round")
                if top_two[0][1] != preferred:
                    top_two[0] = rankings[-3]
        if print:
            print("[Automatic runoff round]")

        try:
            winner = self.preference(top_two[0][1], top_two[1][1], print=print, when="automatic runoff round")
        except UnbreakableTieError:
            if print:
                print("[Resolving two-way tie in automatic runoff round]")
                print_rankings(top_two)

            if top_two[0][0] > top_two[1][0]:
                winner = top_two[0][1]
            elif top_two[1][0] > top_two[0][0]:
                winner = top_two[1][1]
            else:
                raise UnbreakableTieError(f"unbreakable tie between {top_two[0][1]} and {top_two[1][1]} in automatic runoff round")

        return winner

