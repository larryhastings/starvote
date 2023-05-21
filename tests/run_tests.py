#!/usr/bin/env python3

import builtins
import glob
import os.path
import re
import sys

def preload_local_starvote():
    """
    Pre-load the local "starvote" module, to preclude finding
    an already-installed one on the path.
    """
    from os.path import abspath, dirname, isfile, join, normpath
    import sys
    starvote_dir = abspath(dirname(sys.argv[0]))
    while True:
        starvote_init = join(starvote_dir, "starvote/__init__.py")
        if isfile(starvote_init):
            break
        starvote_dir = normpath(join(starvote_dir, ".."))
    sys.path.insert(1, starvote_dir)
    import starvote
    return starvote_dir

starvote_dir = preload_local_starvote()
import starvote

os.chdir(starvote_dir)

text = []
def print(*a, sep=" "):
    text.append(sep.join(str(o) for o in a))
def get_text():
    output = "\n".join(text)
    text.clear()
    return output
def flush_text():
    builtins.print(get_text())


seats_re = re.compile("_(\d+)_seats_")

tests_run = 0
for csv in sorted(glob.glob("sample_polls/*.csv")):
    expected_file = csv.replace(".csv", ".result.txt")
    if not os.path.isfile(expected_file):
        builtins.print("skipping", csv)
        continue
    text.clear()
    args = []
    if "_proportional_star_" in csv:
        match = seats_re.search(csv)
        assert match
        seats = match.group(1)
        args.extend(("-v", "Proportional_STAR", "-s", seats))
    args.append(csv)
    starvote.main(args, print=print)
    got = get_text().strip().split("\n")
    with open(expected_file, "rt") as f:
        expected = f.read().strip().split('\n')
    if expected != got:
        print(f"Test failed: {csv}")
        print(expected)
        print()
        print(got)
        import difflib
        text.extend(difflib.context_diff(expected, got, fromfile='expected', tofile='got', lineterm='\n'))
        print()
        flush_text()
        sys.exit(-1)

    tests_run += 1


print(f"{tests_run} tests passed.")

flush_text()
