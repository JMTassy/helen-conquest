"""State observer — reads ledger, projects state, yields snapshots.

No new state engine. No mutation. Kernel is source of truth.
"""
from helen_os.runtime.state_observer import current_snapshot, tail
from helen_os.tests._helpers import make_session


def _run_session(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    s.propose_shell("pwd")
    s.terminate(verdict="OPERATOR_SHIP")
    return s.ledger_path


def test_current_snapshot_empty_ledger(tmp_path):
    empty = tmp_path / "empty.ndjson"
    snap = current_snapshot(empty)
    assert snap["state_hash"] is None
    assert snap["event_count"] == 0
    assert snap["terminated"] is False


def test_current_snapshot_after_session(tmp_path):
    ledger = _run_session(tmp_path)
    snap = current_snapshot(ledger)
    assert snap["state_hash"] is not None
    assert snap["last_receipt"] is not None
    assert snap["last_receipt"].startswith("sha256:") or len(snap["last_receipt"]) == 64
    assert snap["event_count"] >= 4
    assert snap["terminated"] is True
    assert snap["last_event_type"] == "COGNITION_TERMINATED"


def test_current_snapshot_is_deterministic(tmp_path):
    ledger = _run_session(tmp_path)
    s1 = current_snapshot(ledger)
    s2 = current_snapshot(ledger)
    assert s1["state_hash"] == s2["state_hash"]
    assert s1["last_receipt"] == s2["last_receipt"]
    assert s1["event_count"] == s2["event_count"]


def test_state_hash_changes_after_new_event(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    snap_before = current_snapshot(s.ledger_path)
    s.propose_shell("pwd")
    snap_after = current_snapshot(s.ledger_path)
    assert snap_before["state_hash"] != snap_after["state_hash"]
    assert snap_after["event_count"] > snap_before["event_count"]


def test_tail_yields_on_new_events(tmp_path):
    s = make_session(tmp_path)
    s.start_session()

    gen = tail(s.ledger_path, poll_interval=0.0)
    snap = next(gen)
    assert snap["event_count"] >= 1

    s.propose_shell("pwd")
    snap2 = next(gen)
    assert snap2["event_count"] > snap["event_count"]
    assert snap2["state_hash"] != snap["state_hash"]


def test_snapshot_keys_are_complete(tmp_path):
    ledger = _run_session(tmp_path)
    snap = current_snapshot(ledger)
    required = {"state_hash", "last_receipt", "event_count", "last_event_type",
                "terminated", "cognition_active"}
    assert required <= set(snap.keys())
