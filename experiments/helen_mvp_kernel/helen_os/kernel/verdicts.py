"""Termination verdicts."""
from __future__ import annotations


class Verdicts:
    NO_SHIP = "NO_SHIP"
    ABORT = "ABORT"
    OPERATOR_SHIP = "OPERATOR_SHIP"  # only an operator may set this; not AI


VALID_TERMINATION_VERDICTS = frozenset({Verdicts.NO_SHIP, Verdicts.ABORT, Verdicts.OPERATOR_SHIP})
