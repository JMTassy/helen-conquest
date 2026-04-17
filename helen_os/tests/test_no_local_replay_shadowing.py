"""Test: Validator and batch use SINGLE replay primitive, never local implementations.

Anti-regression: prevents re-introducing replay_entries_to_state or similar
in governance/autonomy modules, which would create divergent state mutation logic.

Constitutional law: There shall be ONE source of truth for replay.
"""
import inspect
from helen_os.governance import ledger_validator_v1
from helen_os.autonomy import autoresearch_batch_v1


def test_validator_imports_single_replay_primitive():
    """Validator must import replay_ledger_to_state, never define local replay."""
    src = inspect.getsource(ledger_validator_v1)

    # Must import the primitive
    assert "from helen_os.state.ledger_replay_v1 import replay_ledger_to_state" in src

    # Must not define a local replay function (would shadow the primitive)
    assert "def replay_entries_to_state" not in src
    assert "def replay_ledger_to_state" not in src


def test_batch_imports_single_replay_primitive():
    """Batch must import replay_ledger_to_state, never define local replay."""
    src = inspect.getsource(autoresearch_batch_v1)

    # Must import the primitive
    assert "from helen_os.state.ledger_replay_v1 import replay_ledger_to_state" in src

    # Must not define a local replay function
    assert "def replay_entries_to_state" not in src
    assert "def replay_ledger_to_state" not in src


def test_validator_uses_replay_primitive_for_rollback():
    """Validator ROLLED_BACK proof must call replay_ledger_to_state, not local logic."""
    src = inspect.getsource(ledger_validator_v1)

    # ROLLED_BACK semantic proof must use the primitive
    assert "replay_ledger_to_state(" in src
    assert "make_ledger_prefix" in src  # helper to construct prefix ledger


def test_batch_uses_replay_primitive_for_state_application():
    """Batch governed application must call replay_ledger_to_state, not local logic."""
    src = inspect.getsource(autoresearch_batch_v1)

    # apply_ledger_governed must use the primitive
    assert "replay_ledger_to_state(" in src
    assert "make_ledger_prefix" in src  # helper to construct prefix ledger
