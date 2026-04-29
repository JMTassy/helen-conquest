"""Constitutional Reflexivity invariant.

No actor — developer, operator, CLI, script, or test — may mutate kernel
state without a receipt flowing through the reducer → ledger path.
"""
import pytest

from helen_os.kernel.state import State
from helen_os.kernel.reducer import fold
from helen_os.tests._helpers import make_session


def test_builder_cannot_bypass_receipt():
    """Even internal code cannot mutate state without receipt."""
    state = State()
    with pytest.raises(Exception) as exc_info:
        state._unsafe_mutation({"key": "value"})
    assert "receipt" in str(exc_info.value).lower()


def test_state_has_no_public_mutation_methods():
    """State exposes no public callable that bypasses the reducer."""
    public_methods = {
        n for n in dir(State)
        if not n.startswith("_") and callable(getattr(State, n))
    }
    allowed = {"to_dict"}
    mutation_leaks = public_methods - allowed
    assert not mutation_leaks, (
        f"State exposes public mutation surface: {mutation_leaks}. "
        "Only the reducer may produce new state."
    )


def test_state_only_changes_through_fold(tmp_path):
    """State is derived exclusively by replaying events through fold()."""
    s = make_session(tmp_path)
    s.start_session()
    s.propose_shell("pwd")
    s.terminate(verdict="OPERATOR_SHIP")

    from helen_os.ledger.event_log import read_events
    events = list(read_events(s.ledger_path))
    state = fold(events)

    assert state.terminated is True
    assert state.events_seen == len(events)
    assert state.proposed_count >= 1
