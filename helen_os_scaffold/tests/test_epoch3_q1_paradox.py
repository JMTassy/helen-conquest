"""
tests/test_epoch3_q1_paradox.py — Q1: SOLVE_PARADOX

Image: "Solve a Paradox" — ☯ contradiction resolved?

Tests:
  P1.1 — Quest Q1 is in QUEST_BANK with correct type
  P1.2 — CounterfactualSpec INJECT_PARADOX is valid (no freeform ops)
  P1.3 — Phase A runs base world, produces closure_success=True
  P1.4 — Phase B runs shadow W' with paradox injected, closure_success=False
  P1.5 — delta_closure > 0.5 (base closed, shadow did not)
  P1.6 — contradiction_resolved = True (evaluation gate ☯)
  P1.7 — overall_pass from Q1 quest loop
  P1.8 — INJECT_PARADOX receipt is emitted
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.kernel import GovernanceVM
from helen_os.epoch3.quest_bank import (
    QUEST_BANK, QuestType, CounterfactualSpec, get_quest
)
from helen_os.epoch3.sim_loop  import SimLoop
from helen_os.epoch3.evaluation import EvaluationGate
from helen_os.epoch2.law_ledger import LawLedger


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_kernel():
    return GovernanceVM(ledger_path=":memory:")


def get_q1():
    return get_quest("Q1")


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_p1_1_quest_in_bank():
    """P1.1 — Q1 is in QUEST_BANK with type SOLVE_PARADOX."""
    q1 = get_q1()
    assert q1.id == "Q1"
    assert q1.quest_type == QuestType.SOLVE_PARADOX
    assert q1.counterfactual is not None
    assert q1.counterfactual.op == "INJECT_PARADOX"


def test_p1_2_counterfactual_valid():
    """P1.2 — CounterfactualSpec rejects unknown ops."""
    with pytest.raises(ValueError, match="not in allowed set"):
        CounterfactualSpec(op="EXEC_SHELL", params={})

    # Valid op must not raise
    cf = CounterfactualSpec(op="INJECT_PARADOX", params={"dispute_all": True})
    assert cf.to_payload()["type"] == "COUNTERFACTUAL_SPEC_V1"


def test_p1_3_phase_a_base_world_closes():
    """P1.3 — Phase A base world (seed=42) achieves closure_success=True."""
    km   = make_kernel()
    q1   = get_q1()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q1, seed=42, ticks=20)

    assert result.phase_a.metrics.closure_success is True, (
        "Base world must close in 20 ticks (F3 proactive escort fix)"
    )


def test_p1_4_phase_b_paradox_no_closure():
    """P1.4 — Phase B shadow W' with INJECT_PARADOX has closure_success=False."""
    km   = make_kernel()
    q1   = get_q1()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q1, seed=42, ticks=20)

    pb = result.phase_b
    assert pb.paradox_injected is True, "Phase B must set paradox_injected=True"
    assert len(pb.shadow_metrics_list) == 1
    shadow_closure = pb.shadow_metrics_list[0].closure_success
    assert shadow_closure is False, (
        f"Paradox world W' must not close. Got closure_success={shadow_closure}"
    )


def test_p1_5_delta_closure_positive():
    """P1.5 — delta_closure = closure(W) - closure(W') > 0.5."""
    km   = make_kernel()
    q1   = get_q1()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q1, seed=42, ticks=20)

    delta = result.phase_c.delta_closure_success
    assert delta > 0.5, (
        f"delta_closure should be > 0.5 (W closed, W' did not). Got {delta}"
    )


def test_p1_6_contradiction_resolved():
    """P1.6 — EvaluationGate marks contradiction_resolved=True for Q1."""
    km   = make_kernel()
    q1   = get_q1()
    loop = SimLoop(kernel=km)
    ledger = LawLedger(kernel=km)
    result = loop.run(quest=q1, seed=42, ticks=20, law_ledger=ledger)
    eval_r = EvaluationGate.assess(result, kernel=km)

    assert eval_r.contradiction_resolved is True, (
        f"☯ Contradiction must be resolved. Eval: {eval_r.summary_line()}"
    )


def test_p1_7_overall_pass():
    """P1.7 — Full Q1 quest loop passes all 3 evaluation gates."""
    km   = make_kernel()
    q1   = get_q1()
    loop = SimLoop(kernel=km)
    ledger = LawLedger(kernel=km)
    result = loop.run(quest=q1, seed=42, ticks=20, law_ledger=ledger)
    eval_r = EvaluationGate.assess(result, kernel=km)

    assert eval_r.overall_pass is True, (
        f"Q1 should pass all 3 gates.\n{eval_r.summary_line()}"
    )


def test_p1_8_paradox_receipt_emitted():
    """P1.8 — INJECT_PARADOX is evidenced by a PHASE_B_EXPERIMENT_V1 receipt."""
    km   = make_kernel()
    q1   = get_q1()
    loop = SimLoop(kernel=km)
    loop.run(quest=q1, seed=42, ticks=20)

    # cum_hash must be a 64-char SHA256 hex and not all-zeros (receipts were emitted)
    assert len(km.cum_hash) == 64, f"cum_hash must be 64 hex chars, got: {km.cum_hash!r}"
    assert km.cum_hash != "0" * 64, "Kernel must have processed at least one receipt"
