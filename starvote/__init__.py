#!/usr/bin/env python3

__doc__ = "A simple STAR vote tabulator"

__version__ = "1.3"

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
    Proportional_STAR = 3

STAR = PollVariant.STAR
BLOC_STAR = PollVariant.BLOC_STAR
Proportional_STAR = PollVariant.Proportional_STAR


class Poll:
    def __init__(self, variant=STAR, *, seats=1):
        self.variant = variant
        self.seats = seats

        self.candidates = {}
        self.ballots = []

        if variant == STAR:
            if seats != 1:
                raise ValueError("seats must be 1 when using variant STAR")
        else:
            if seats == 1:
                raise ValueError("seats must be > 1 when using variant " + str(variant).rpartition(".")[2])

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


    def print_rankings(self, ballots, rankings, print):
        candidate_width, score_width, average_width = self.compute_widths(ballots, rankings)
        total_average_width = average_width + 3
        ballots_count = len(ballots)

        # are the scores all ints?
        for score, candidate in rankings:
            int_score = int(score)
            if int_score != score:
                score_format = f"{score_width}.3f"
                total_score_width = score_width + 4
                break
        else:
            score_format = score_width
            total_score_width = score_width


        for score, candidate in reversed(rankings):
            average = score / ballots_count
            average = f"{average:>1.2f}"
            score = f"{score:>{score_format}}"
            print(f"  {candidate:<{candidate_width}} -- {score:>{total_score_width}} (average {average:>{total_average_width}})")


    def _proportional_result(self, ballots, candidates, *, print=None):
        winners = []

        # Floordiv so hare_quota is an integer.
        # If there would have been a fraction,
        # it just means the last round's hare quota
        # would be one more.
        #   e.g. 100 voters, 3 seats, you'd use 33, 33, and 34.
        # But we don't need to bother with the Hare quota
        # during the last round.
        # So we can just ignore the fraction completely.
        hare_quota = len(ballots) // self.seats

        if print:
            print(f"  Hare quota is {hare_quota}.")

        for polling_round in range(1, self.seats+1):
            rankings = [(score, candidate) for candidate, score in candidates.items()]
            rankings.sort()
            if print:
                print(f"[Score round {polling_round}]")
                remaining = " remaining" if polling_round > 1 else ""
                print(f"  {len(ballots)}{remaining} ballots.")
                self.print_rankings(ballots, rankings, print)

            round_winners = [t[1] for t in rankings if t[0] == rankings[-1][0]]
            if len(round_winners) > 2:
                raise UnbreakableTieError(f"{len(round_winners)}-way tie in round {polling_round}", *round_winners)
            if len(round_winners) == 2:
                winner = self.preference(ballots, *round_winners, when="proportional score round {polling_round}")
            else:
                assert len(round_winners) == 1
                winner = round_winners.pop()

            # we need to allocate voters to the winner,
            # do the hare quota thing, etc.
            # for simplicity of implementation, we're only going to handle
            # one winner here.  if we reached here and there were multiple
            # tied winners, we'll process the other winners in future
            # iterations of the loop.  doing them one at a time won't
            # affect the outcome.

            winners.append(winner)
            if print:
                print(f"[Winner round {polling_round}]")
                print(f"  {winner}")
            if len(winners) == self.seats:
                return winners

            del candidates[winner]

            # gonna iterate.
            # remove hare quota voters, possibly fractionally.
            if print:
                print(f"[Allocating voters round {polling_round}]")

            quota = hare_quota
            all_supporters = [ballot for ballot in ballots if ballot.get(winner, 0)]
            all_supporters.sort(key=lambda ballot: ballot[winner])

            while all_supporters:
                # find highest score.
                # note that this might not be an integer!
                # after the first scoring round, it's likely there will be non-integer votes.
                score = all_supporters[-1][winner]

                tranche = [ballot for ballot in all_supporters if ballot[winner] == score]
                tranche_count = len(tranche)

                assert all_supporters[-tranche_count][winner] == score
                assert (len(all_supporters) == tranche_count) or (all_supporters[-(tranche_count + 1)][winner] != score)
                del all_supporters[-tranche_count:]

                unallocated_ballots = [ballot for ballot in ballots if ballot.get(winner, 0) != score]

                if print:
                    print(f"  Quota remaining {quota}.")
                    print(f"    Allocating {tranche_count} voters at score {score}.")
                if tranche_count <= quota:
                    quota -= tranche_count
                    ballots = unallocated_ballots
                    if not quota:
                        break
                    continue

                # this tranche has more supporters than we need to fill the quota.
                # reduce every supporter's vote by the surplus, then keep them in play.
                weight_reduction_ratio = 1 - (quota / tranche_count)
                if print:
                    print(f"    This would take us over quota, so handling fractional surplus.")
                    print(f"    Allocating {(1 - weight_reduction_ratio) * 100:2.2f}% of these ballots.")
                    print(f"    Multiplying these ballot's scores by {weight_reduction_ratio:2.6f}, then keeping them unallocated.")
                for ballot in tranche:
                    del ballot[winner]
                    for candidate, vote in ballot.items():
                        adjusted_vote = vote * weight_reduction_ratio
                        candidates[candidate] += (adjusted_vote - vote)
                        ballot[candidate] = adjusted_vote

                unallocated_ballots.extend(tranche)

                ballots = unallocated_ballots
                break

            for ballot in ballots:
                if winner in ballot:
                    del ballot[winner]


        raise RuntimeError("shouldn't reach here")



    def result(self, *, print=None):
        winners = []
        candidates = self.candidates
        ballots = self.ballots

        if not candidates:
            raise ValueError("no candidates")

        if self.variant == STAR:
            if print:
                print("[STAR]")
            if len(candidates) == 1:
                winners = list(candidates)
                winner = winners[0]
                if print:
                    print("  Only one candidate, returning winner {winner}!")
                return winner
            round_text_format = ""
        else:
            if print:
                if self.variant == BLOC_STAR:
                    print("[BLOC STAR]")
                else:
                    print("[Proportional STAR]")
                print(f"  {self.seats} seats.")
            if len(candidates) <= self.seats:
                raise ValueError(f"not enough candidates, need {self.seats}, have {len(candidates)}")
            if len(candidates) == self.seats:
                print(f"  Have exactly {self.seats} candidates, all candidates are winners!")
                return list(candidates)
            # we're gonna modify ballots, so, make copies
            ballots = [dict(b) for b in ballots]
            candidates = dict(candidates)
            round_text_format = " {polling_round}"

        if self.variant == Proportional_STAR:
            return self._proportional_result(ballots, candidates, print=print)

        for polling_round in range(1, self.seats+1):
            candidates_count = len(candidates)
            ballots_count = len(ballots)
            assert candidates_count

            round_text = round_text_format.format(polling_round=polling_round)

            if print:
                print(f"[Score round{round_text}]")

            # score round
            rankings = [(score, candidate) for candidate, score in candidates.items()]
            rankings.sort()

            if print:
                self.print_rankings(ballots, rankings, print)

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
                    self.print_rankings(ballots, top_two, print)

                if top_two[0][0] > top_two[1][0]:
                    winner= top_two[0][1]
                elif top_two[1][0] > top_two[0][0]:
                    winner = top_two[1][1]
                else:
                    raise UnbreakableTieError(f"unbreakable tie between {top_two[0][1]} and {top_two[1][1]} in automatic runoff round{round_text}", top_two[0][1], top_two[1][1])
            if (self.seats != 1) and print:
                print(f"[Winner round{round_text}]")
                print(f"  {winner}")
            winners.append(winner)

            if self.seats > 1:
                for b in ballots:
                    if winner in b:
                        del b[winner]
                assert winner in candidates
                del candidates[winner]

        if self.variant == STAR:
            assert len(winners) == 1
            return winner

        assert len(winners) == self.seats
        return winners

