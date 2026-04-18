"""
tests/test_claim_graph_cg2_dr2.py — CG2: DR2 Decision Rule

Tests:
  CG2.1 — INCLUDE when undefeated_grounds >= 2 and unanswered_rebuttals == 0
  CG2.2 — DEFER when unanswered rebuttals exist
  CG2.3 — DEFER when undefeated_grounds < min_undefeated_grounds
  CG2.4 — BLOCKED when no grounds in graph
  CG2.5 — DR2.evaluate() emits a receipt (decision_receipt_id is set, cum_hash non-zero)
  CG2.6 — DR2 verdict is deterministic across 3 re-runs (same graph → same verdict)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.kernel import GovernanceVM
from helen_os.claim_graph import ClaimGraph, DR2DecisionRule, DR2Verdict


def make_kernel():
    return GovernanceVM(ledger_path=":memory:")


def make_graph_with(num_grounds: int, num_rebuttals: int, answer_all: bool = True) -> ClaimGraph:
    """Helper: build a graph with n grounds, m rebuttals, optionally answer all."""
    g = ClaimGraph(decision_topic="Test decision")
    for i in range(num_grounds):
        g.add_ground(f"Ground {i + 1}")
    for i in range(num_rebuttals):
        parent = f"G{(i % num_grounds) + 1}"
        g.add_rebuttal(f"Rebuttal {i + 1}", parent_id=parent)
        if answer_all:
            g.add_counter_rebuttal(f"Counter {i + 1}", parent_id=f"R{i + 1}")
    return g


def test_cg2_1_include_verdict():
    """CG2.1 — INCLUDE when >= 2 undefeated grounds and 0 unanswered rebuttals."""
    km  = make_kernel()
    g   = make_graph_with(num_grounds=3, num_rebuttals=1, answer_all=True)
    dr2 = DR2DecisionRule(min_undefeated_grounds=2)
    result = dr2.evaluate(g, km)

    assert result.verdict                    == DR2Verdict.INCLUDE
    assert result.unanswered_rebuttals_count == 0
    assert result.undefeated_grounds_count   >= 2


def test_cg2_2_defer_unanswered_rebuttals():
    """CG2.2 — DEFER when rebuttals exist with no counter-rebuttals."""
    km  = make_kernel()
    g   = make_graph_with(num_grounds=3, num_rebuttals=2, answer_all=False)
    dr2 = DR2DecisionRule(min_undefeated_grounds=2)
    result = dr2.evaluate(g, km)

    assert result.verdict                    == DR2Verdict.DEFER
    assert result.unanswered_rebuttals_count  > 0
    assert "DEFER" in result.reason


def test_cg2_3_defer_insufficient_grounds():
    """CG2.3 — DEFER when undefeated_grounds < min_undefeated_grounds."""
    km  = make_kernel()
    g   = make_graph_with(num_grounds=1, num_rebuttals=0)  # only 1 ground, min=2
    dr2 = DR2DecisionRule(min_undefeated_grounds=2)
    result = dr2.evaluate(g, km)

    assert result.verdict                  == DR2Verdict.DEFER
    assert result.undefeated_grounds_count  < dr2.min_undefeated_grounds
    assert "DEFER" in result.reason


def test_cg2_4_blocked_no_grounds():
    """CG2.4 — BLOCKED when no grounds in graph."""
    km  = make_kernel()
    g   = ClaimGraph(decision_topic="Empty decision")   # no grounds added
    dr2 = DR2DecisionRule(min_undefeated_grounds=2)
    result = dr2.evaluate(g, km)

    assert result.verdict == DR2Verdict.BLOCKED
    assert "BLOCKED" in result.reason


def test_cg2_5_receipt_emitted():
    """CG2.5 — DR2.evaluate() emits a receipt (non-None ID, 64-char cum_hash)."""
    km  = make_kernel()
    g   = make_graph_with(num_grounds=2, num_rebuttals=0)
    dr2 = DR2DecisionRule(min_undefeated_grounds=2)
    result = dr2.evaluate(g, km)

    assert result.decision_receipt_id is not None
    assert result.decision_receipt_id.startswith("R-"), (
        f"Receipt ID should start with 'R-'. Got: {result.decision_receipt_id!r}"
    )
    assert len(km.cum_hash) == 64
    assert km.cum_hash != "0" * 64, "Kernel must have processed at least one receipt"


def test_cg2_6_deterministic():
    """CG2.6 — Same graph structure → same DR2 verdict (deterministic across 3 runs)."""
    verdicts = []
    for _ in range(3):
        km  = make_kernel()
        g   = make_graph_with(num_grounds=3, num_rebuttals=2, answer_all=True)
        dr2 = DR2DecisionRule(min_undefeated_grounds=2)
        r   = dr2.evaluate(g, km)
        verdicts.append(r.verdict)

    assert all(v == verdicts[0] for v in verdicts), (
        f"DR2 should be deterministic. Got: {[v.value for v in verdicts]}"
    )
    assert verdicts[0] == DR2Verdict.INCLUDE
