import starvote

poll = starvote.Poll()
poll.add_ballot({'Amy': 1, 'Brian': 3, 'Chuck': 5})
poll.add_ballot({'Amy': 5, 'Brian': 2, 'Chuck': 3})
poll.add_ballot({'Amy': 4, 'Brian': 4, 'Chuck': 5})
winner = poll.result(print=print)
print()
print(f"[Winner]\n{winner}")
