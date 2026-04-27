import json

import pytest

from helen_os.kernel.reducer import fold
from helen_os.ledger.event_log import read_events
from helen_os.ledger.hash_chain import ChainBreak

from helen_os.tests._helpers import make_session


def _rewrite_ndjson(path, events):
    with open(path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def test_modifying_prev_event_hash_breaks_chain(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    s.propose_shell("ls")
    s.propose_shell("pwd")

    events = read_events(s.ledger_path)
    assert len(events) >= 3
    # Tamper with prev_event_hash on event index 2.
    events[2]["prev_event_hash"] = "0" * 64
    _rewrite_ndjson(s.ledger_path, events)

    with pytest.raises(ChainBreak):
        fold(read_events(s.ledger_path), forbidden_tokens=s.forbidden_tokens)


def test_modifying_payload_breaks_event_hash(tmp_path):
    s = make_session(tmp_path)
    s.start_session()
    s.propose_shell("pwd")
    events = read_events(s.ledger_path)
    # Tamper with payload of event 1 — event_hash will no longer match.
    events[1]["payload"]["command"] = "ls"
    _rewrite_ndjson(s.ledger_path, events)

    with pytest.raises(ChainBreak):
        fold(read_events(s.ledger_path), forbidden_tokens=s.forbidden_tokens)
