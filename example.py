import starvote

ballots = [
    {'Amy': 1, 'Brian': 3, 'Chuck': 5},
    {'Amy': 5, 'Brian': 2, 'Chuck': 3},
    {'Amy': 4, 'Brian': 4, 'Chuck': 5},
]

winners = starvote.election(starvote.star, ballots, verbosity=1)
