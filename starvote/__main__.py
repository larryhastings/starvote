#!/usr/bin/env python3

import csv
import sys
from . import Poll, UnbreakableTieError

if len(sys.argv) == 1:
    sys.exit("usage: starvote.py ballot.csv\nballot is assumed to be in https://start.vote CSV format.\n")

poll = Poll()
with open(sys.argv[1], "rt") as f:
    reader = csv.reader(f)
    candidates = None
    for row in reader:
        # clip off voterid, date, and pollid
        row = row[3:]
        if candidates == None:
            candidates = row
            # for candidate in candidates:
            #     poll.add_candidate(candidate)
            continue
        ballot = {candidate: int(vote) for candidate, vote in zip(candidates, row)}
        poll.add_ballot(ballot)

text = []
def myprint(*a, sep=" "):
    text.append(sep.join(str(o) for o in a))

winner = None
try:
    winner = poll.result(print=myprint)
except UnbreakableTieError as e:
    s = str(e)
    s = s[0].title() + s[1:]
    myprint(f"\n{s}!")
    myprint("")
myprint(f"[Winner]\n  {winner}")
t = "\n".join(text)
print(t)
