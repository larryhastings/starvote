#!/usr/bin/env python3

# Test harness setup.
# starvote should already be imported by now.

import starvote

_add_tiebreaker = starvote._add_tiebreaker


@_add_tiebreaker
def _just_raise_tiebreaker(options, tie, desired, exception):
    """
    Just raise tiebreaker

    Raises the exception immediately.

    """
    raise exception

@_add_tiebreaker
def _only_heading_tiebreaker(options, tie, desired, exception): # pragma: nocover
    """
    This tiebreaker only has a heading, no description.


    """
    raise exception

@_add_tiebreaker
def _no_description_tiebreaker(options, tie, desired, exception):
    raise exception
