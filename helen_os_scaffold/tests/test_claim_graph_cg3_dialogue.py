"""
tests/test_claim_graph_cg3_dialogue.py — CG3: HELEN↔HAL Canonical Dialogue

Tests:
  CG3.1 — run_claim_graph_canonical() returns ClaimGraphRunResult
  CG3.2 — Delayed Decay decision is INCLUDE (4G, 2R defeated, 2 CR)
  CG3.3 — Receipt chain is non-trivial (cum_hash != zeros, receipts_count >= 14)
  CG3.4 — T1–T4 hypotheses are present in q4_hypotheses (ids T1/T2/T3/T4)
  CG3.5 — Canonical dialogue has exactly 8 turns (4G + 2R + 2CR)
  CG3.6 — HALDialogueResult.to_payload() round-trips to JSON cleanly
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.claim_graph import run_claim_graph_canonical, ClaimGraphRunResult
from helen_os.claim_graph.decision_rule import DR2Verdict


def test_cg3_1_returns_result():
    """CG3.1 — run_claim_graph_canonical() returns ClaimGraphRunResult."""
    result = run_claim_graph_canonical(ledger_path=":memory:")
    assert isinstance(result, ClaimGraphRunResult)


def test_cg3_2_delayed_decay_include():
    """CG3.2 — Canonical Delayed Decay verdict is INCLUDE."""
    result = run_claim_graph_canonical(ledger_path=":memory:")

    assert result.is_include is True, (
        f"Delayed Decay decision should be INCLUDE. Got: {result.verdict}"
    )
    assert result.verdict == "INCLUDE"
    assert result.dialogue_result.dr2_result.unanswered_rebuttals_count == 0
    assert result.dialogue_result.dr2_result.undefeated_grounds_count   == 4


def test_cg3_3_receipt_chain_nontrivial():
    """CG3.3 — Receipt chain is non-trivial (cum_hash != zeros, receipts_count == 14)."""
    result = run_claim_graph_canonical(ledger_path=":memory:")

    assert len(result.kernel_cum_hash) == 64
    assert result.kernel_cum_hash != "0" * 64, "Receipt chain must be non-trivial"
    # Canonical count: 1 start + 1 dlg_start + 8 turns + 1 dr2 + 1 dlg_result + 1 q4 + 1 summary = 14
    assert result.receipts_count == 14, (
        f"Expected 14 receipts in canonical run. Got {result.receipts_count}"
    )


def test_cg3_4_q4_hypotheses_present():
    """CG3.4 — T1–T4 hypotheses are all present in q4_hypotheses."""
    result = run_claim_graph_canonical(ledger_path=":memory:")

    ids = {h["id"] for h in result.q4_hypotheses}
    assert "T1" in ids, f"T1 missing from q4_hypotheses. Got: {ids}"
    assert "T2" in ids, f"T2 missing from q4_hypotheses. Got: {ids}"
    assert "T3" in ids, f"T3 missing from q4_hypotheses. Got: {ids}"
    assert "T4" in ids, f"T4 missing from q4_hypotheses. Got: {ids}"
    assert len(result.q4_hypotheses) >= 4


def test_cg3_5_dialogue_turns():
    """CG3.5 — Canonical dialogue has exactly 8 turns (4G + 2R + 2CR)."""
    result = run_claim_graph_canonical(ledger_path=":memory:")

    turns = result.dialogue_result.total_turns
    assert turns == 8, (
        f"Canonical scenario must have 8 turns (4G + 2R + 2CR). Got {turns}"
    )
    # Verify speaker pattern
    d = result.dialogue_result
    assert len(d.graph.g_set)  == 4, f"Expected 4 grounds, got {len(d.graph.g_set)}"
    assert len(d.graph.r_set)  == 2, f"Expected 2 rebuttals, got {len(d.graph.r_set)}"
    assert len(d.graph.cr_set) == 2, f"Expected 2 counter-rebuttals, got {len(d.graph.cr_set)}"


def test_cg3_6_payload_json_roundtrip():
    """CG3.6 — HALDialogueResult.to_payload() round-trips to JSON cleanly."""
    result  = run_claim_graph_canonical(ledger_path=":memory:")
    payload = result.dialogue_result.to_payload()

    # Must be JSON-serializable
    json_str  = json.dumps(payload, sort_keys=True)
    recovered = json.loads(json_str)

    assert recovered["type"]        == "HAL_DIALOGUE_RESULT_V1"
    assert recovered["verdict"]     == "INCLUDE"
    assert recovered["is_resolved"] is True
    assert recovered["total_turns"] == 8
    assert len(recovered["turns"])  == 8
    # All nodes accounted for
    assert recovered["g_set_count"]  == 4
    assert recovered["r_set_count"]  == 2
    assert recovered["cr_set_count"] == 2
