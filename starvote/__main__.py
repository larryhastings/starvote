#!/usr/bin/env python3

import csv
import os.path
import sys
from . import Poll, UnbreakableTieError, STAR, BLOC_STAR, Proportional_STAR

def usage(s=None):
    if s:
        print(s)
        print()
    print("usage: starvote.py [-v|--variant variant] [-s|--seats seats] ballot.csv")
    print()
    print("-v|--variant specifies STAR variant.  supported variants are STAR (default) and BLOC_STAR.")
    print("-s|--seats specifies number of seats, default 1.")
    print()
    print("ballot is assumed to be in https://start.vote CSV format.")
    print()
    sys.exit(-1)

if len(sys.argv) == 1:
    usage()

consume_variant = False
variant = None

consume_seats = False
seats = None

csv_file = None

extraneous_args = []

for arg in sys.argv[1:]:
    if consume_variant:
        variant = arg
        consume_variant = False
        continue
    if arg.startswith("-v=") or arg.startswith("--variant="):
        if variant is not None:
            usage("variant specified twice")
        variant = arg.partition('=')[2]
        continue
    if arg in ("-v", "--variant"):
        if variant is not None:
            usage("variant specified twice")
        consume_variant = True
        continue

    if consume_seats:
        seats = int(arg)
        consume_seats = False
        continue
    if arg.startswith("-s=") or arg.startswith("--seats="):
        if seats is not None:
            usage("seats specified twice")
        seats = int(arg.partition('='))
        continue
    if arg in ("-s", "--seats"):
        if seats is not None:
            usage("seats specified twice")
        consume_seats = True
        continue

    if csv_file is None:
        csv_file = arg
        continue
    extraneous_args.append(arg)

if extraneous_args:
    usage("too many arguments: " + " ".join(extraneous_args))

if variant in ("STAR", None):
    variant = STAR
elif variant == "BLOC_STAR":
    variant = BLOC_STAR
elif variant == "Proportional_STAR":
    variant = Proportional_STAR
else:
    usage("unknown variant " + variant)

if seats == None:
    seats = 1

if csv_file is None:
    usage("no CSV file specified.")
if not os.path.isfile(csv_file):
    usage("invalid CSV file specified.")

poll = Poll(variant=variant, seats=seats)
with open(csv_file, "rt") as f:
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
    if len(e.candidates) == 2:
        winner = f"Tie between {e.candidates[0]} and {e.candidates[1]}"
    else:
        candidates = list(e.candidates)
        last_candidate = candidates.pop()
        winner = f"Tie between {', '.join(candidates)}, and {last_candidate}"

    s = str(e)
    s = s[0].title() + s[1:]
    myprint(f"\n{s}!")
    myprint("")
if seats == 1:
    myprint("[Winner]")
    myprint(f"  {winner}")
else:
    myprint("[Winners]")
    for w in winner:
        myprint(f"  {w}")

t = "\n".join(text)
print(t)
