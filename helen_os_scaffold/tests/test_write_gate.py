"""
tests/test_write_gate.py — Sovereignty enforcement for write_gate.py.

Tests:
  T01: Requires receipt_id
  T02: Blocks DIALOG_TURN_V1 ref type
  T03: Blocks dialogue path in string field
  T04: Allows valid receipted non-dialogue event
  T05: Chain — second append links to first cumulative_hash
"""
import json
from pathlib import Path

import pytest
from adapters.write_gate import (
    append_event,
    MissingReceiptError,
    DialogueLaunderingError,
)

STORAGE_ROOT = Path(__file__).resolve().parents[1] / "storage"


@pytest.fixture(autouse=True)
def clean_storage():
    targets = [
        STORAGE_ROOT / "town" / "ledger.ndjson",
        STORAGE_ROOT / "memory" / "memory.ndjson",
        STORAGE_ROOT / "trace" / "run_trace.ndjson",
    ]
    for t in targets:
        if t.exists():
            t.unlink()
    yield
    for t in targets:
        if t.exists():
            t.unlink()


def test_t01_requires_receipt_id():
    with pytest.raises(MissingReceiptError):
        append_event(channel="town", payload={"type": "TOWN_RECEIPT_V1"})


def test_t02_blocks_dialogue_ref_type():
    with pytest.raises(DialogueLaunderingError):
        append_event(channel="town", payload={
            "type": "TOWN_RECEIPT_V1",
            "receipt_id": "R-001",
            "refs": [{"type": "DIALOG_TURN_V1", "id": "t1"}],
        })


def test_t03_blocks_dialogue_path_in_string():
    with pytest.raises(DialogueLaunderingError):
        append_event(channel="town", payload={
            "type": "TOWN_RECEIPT_V1",
            "receipt_id": "R-002",
            "evidence": "see dialogue/dialog.ndjson line 20",
        })


def test_t04_allows_valid_event():
    r = append_event(channel="town", payload={
        "type": "TOWN_RECEIPT_V1",
        "receipt_id": "R-003",
        "refs": [{"type": "CLAIM_GRAPH_V1", "id": "CG-001"}],
        "payload": {"verdict": "PASS"},
    })
    path = Path(r.path)
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["payload"]["receipt_id"] == "R-003"
    assert record["cumulative_hash"]


def test_t05_chain_links_hashes():
    r1 = append_event(channel="trace", payload={
        "type": "TRACE_EVENT_V1",
        "receipt_id": "T-001",
        "refs": [{"type": "CLAIM_GRAPH_V1", "id": "CG-101"}],
    })
    r2 = append_event(channel="trace", payload={
        "type": "TRACE_EVENT_V1",
        "receipt_id": "T-002",
        "refs": [{"type": "CLAIM_GRAPH_V1", "id": "CG-102"}],
    })
    assert r2.previous_hash == r1.cumulative_hash
