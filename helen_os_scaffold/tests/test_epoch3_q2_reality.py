"""
tests/test_epoch3_q2_reality.py — Q2: ALTER_REALITY

Image: "Alter Reality States" — ◉ reality transformed?

Tests:
  R2.1 — Quest Q2 is in QUEST_BANK with type ALTER_REALITY
  R2.2 — CounterfactualSpec SET_SEED is valid with shadow_seed param
  R2.3 — Phase A base world (seed=42) admissibility_rate >= 0.80
  R2.4 — Phase B shadow world (seed=7) also admissibility_rate >= 0.80
  R2.5 — Both seeds pass sigma gate threshold
  R2.6 — reality_transformed = True (evaluation gate ◉)
  R2.7 — delta_admissibility is near-zero (protocol stability)
  R2.8 — Law Q2 is inscribed (temporal_insights_gained = True)
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.kernel import GovernanceVM
from helen_os.epoch3.quest_bank import (
    QuestType, CounterfactualSpec, get_quest
)
from helen_os.epoch3.sim_loop   import SimLoop
from helen_os.epoch3.evaluation import EvaluationGate
from helen_os.epoch2.law_ledger import LawLedger


def make_kernel():
    return GovernanceVM(ledger_path=":memory:")


def get_q2():
    return get_quest("Q2")


def test_r2_1_quest_in_bank():
    """R2.1 — Q2 is in QUEST_BANK with type ALTER_REALITY."""
    q2 = get_q2()
    assert q2.id == "Q2"
    assert q2.quest_type == QuestType.ALTER_REALITY
    assert q2.counterfactual is not None
    assert q2.counterfactual.op == "SET_SEED"
    assert q2.counterfactual.params.get("shadow_seed") is not None


def test_r2_2_set_seed_spec_valid():
    """R2.2 — CounterfactualSpec SET_SEED constructs correctly."""
    cf = CounterfactualSpec(op="SET_SEED", params={"shadow_seed": 7})
    payload = cf.to_payload()
    assert payload["op"] == "SET_SEED"
    assert payload["params"]["shadow_seed"] == 7


def test_r2_3_phase_a_admissibility():
    """R2.3 — Phase A base world (seed=42) admissibility_rate >= 0.80."""
    km   = make_kernel()
    q2   = get_q2()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q2, seed=42, ticks=20)

    rate = result.phase_a.metrics.admissibility_rate
    assert rate >= 0.80, (
        f"Base world admissibility_rate must be >= 0.80, got {rate:.4f}"
    )


def test_r2_4_shadow_world_admissibility():
    """R2.4 — Phase B shadow world (seed=7) also admissibility_rate >= 0.80."""
    km   = make_kernel()
    q2   = get_q2()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q2, seed=42, ticks=20)

    pb = result.phase_b
    assert len(pb.shadow_metrics_list) >= 1
    shadow_rate = pb.shadow_metrics_list[0].admissibility_rate
    assert shadow_rate >= 0.80, (
        f"Shadow world (seed=7) admissibility_rate must be >= 0.80, got {shadow_rate:.4f}"
    )


def test_r2_5_sigma_passes():
    """R2.5 — Sigma gate passes for Q2 (admissibility_rate >= 0.80)."""
    km   = make_kernel()
    q2   = get_q2()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q2, seed=42, ticks=20)

    assert result.phase_c.sigma_passed is True, (
        f"Sigma gate must pass for Q2. Reason: {result.phase_c.sigma_reason}"
    )


def test_r2_6_reality_transformed():
    """R2.6 — EvaluationGate marks reality_transformed=True for Q2."""
    km   = make_kernel()
    q2   = get_q2()
    loop = SimLoop(kernel=km)
    ledger = LawLedger(kernel=km)
    result = loop.run(quest=q2, seed=42, ticks=20, law_ledger=ledger)
    eval_r = EvaluationGate.assess(result, kernel=km)

    assert eval_r.reality_transformed is True, (
        f"◉ Reality must be transformed. Eval:\n{eval_r.summary_line()}"
    )


def test_r2_7_delta_admissibility_small():
    """R2.7 — |delta_admissibility| < 0.20 (admissibility is seed-stable)."""
    km   = make_kernel()
    q2   = get_q2()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q2, seed=42, ticks=20)

    delta = abs(result.phase_c.delta_admissibility)
    assert delta < 0.20, (
        f"Admissibility should be seed-stable (delta < 0.20). Got delta={delta:.4f}"
    )


def test_r2_8_law_inscribed():
    """R2.8 — Q2 sigma pass → law inscribed → temporal_insights_gained=True."""
    km   = make_kernel()
    q2   = get_q2()
    loop = SimLoop(kernel=km)
    ledger = LawLedger(kernel=km)
    result = loop.run(quest=q2, seed=42, ticks=20, law_ledger=ledger)
    eval_r = EvaluationGate.assess(result, kernel=km)

    assert eval_r.temporal_insights_gained is True, (
        f"⌛ Temporal insights must be gained (law inscribed). Eval:\n{eval_r.summary_line()}"
    )
    assert eval_r.laws_count >= 1
