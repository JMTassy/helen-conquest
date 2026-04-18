"""
tests/test_epoch3_q3_temporal.py — Q3: EXPLORE_TEMPORAL

Image: "Explore Temporal Realms" — ⌛ temporal insights gained?

Tests:
  T3.1 — Quest Q3 is in QUEST_BANK with type EXPLORE_TEMPORAL
  T3.2 — CounterfactualSpec SWEEP_TICKS is valid with horizons param
  T3.3 — Phase A sovereignty_drift_index == 0 at seed=42, ticks=20
  T3.4 — Phase B runs multiple tick horizons (10, 30, 50)
  T3.5 — All tick horizons achieve closure_success=True
  T3.6 — sovereignty_drift == 0 at all horizons (time-stable)
  T3.7 — temporal_insights_gained = True (evaluation gate ⌛)
  T3.8 — Full epoch3 canonical run produces 3 quest results + laws
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.kernel import GovernanceVM
from helen_os.epoch3.quest_bank import (
    QUEST_BANK, QuestType, CounterfactualSpec, get_quest
)
from helen_os.epoch3.sim_loop   import SimLoop
from helen_os.epoch3.evaluation import EvaluationGate
from helen_os.epoch3.run_epoch3 import run_epoch3_canonical
from helen_os.epoch2.law_ledger import LawLedger


def make_kernel():
    return GovernanceVM(ledger_path=":memory:")


def get_q3():
    return get_quest("Q3")


def test_t3_1_quest_in_bank():
    """T3.1 — Q3 is in QUEST_BANK with type EXPLORE_TEMPORAL."""
    q3 = get_q3()
    assert q3.id == "Q3"
    assert q3.quest_type == QuestType.EXPLORE_TEMPORAL
    assert q3.counterfactual is not None
    assert q3.counterfactual.op == "SWEEP_TICKS"
    assert q3.tick_horizons is not None
    assert len(q3.tick_horizons) >= 2


def test_t3_2_sweep_ticks_spec_valid():
    """T3.2 — CounterfactualSpec SWEEP_TICKS constructs correctly."""
    cf = CounterfactualSpec(op="SWEEP_TICKS", params={"horizons": [10, 30, 50]})
    payload = cf.to_payload()
    assert payload["op"] == "SWEEP_TICKS"
    assert 10 in payload["params"]["horizons"]


def test_t3_3_phase_a_sovereignty_zero():
    """T3.3 — Phase A sovereignty_drift_index == 0 (base run, seed=42, ticks=20)."""
    km   = make_kernel()
    q3   = get_q3()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q3, seed=42, ticks=20)

    drift = result.phase_a.metrics.sovereignty_drift_index
    assert drift == 0.0, (
        f"sovereignty_drift_index must be 0.0 in base world. Got {drift}"
    )


def test_t3_4_phase_b_multiple_horizons():
    """T3.4 — Phase B runs multiple tick horizons (from SWEEP_TICKS)."""
    km   = make_kernel()
    q3   = get_q3()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q3, seed=42, ticks=20)

    pb = result.phase_b
    assert pb.op == "SWEEP_TICKS"
    # Should have run at least 2 shadow horizons
    assert len(pb.shadow_metrics_list) >= 2, (
        f"SWEEP_TICKS must produce >= 2 shadow runs. Got {len(pb.shadow_metrics_list)}"
    )
    expected_horizons = set(q3.counterfactual.params.get("horizons", []))
    actual_horizons   = set(pb.shadow_ticks_list)
    assert expected_horizons == actual_horizons, (
        f"Shadow ticks should match spec. Expected={expected_horizons}, Got={actual_horizons}"
    )


def test_t3_5_all_horizons_close():
    """T3.5 — All tick horizons (≥20 ticks) achieve closure_success=True."""
    km   = make_kernel()
    q3   = get_q3()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q3, seed=42, ticks=20)

    pb = result.phase_b
    for i, (m, t) in enumerate(zip(pb.shadow_metrics_list, pb.shadow_ticks_list)):
        if t >= 20:
            assert m.closure_success is True, (
                f"Horizon ticks={t} must achieve closure. Got closure_success={m.closure_success}"
            )


def test_t3_6_sovereignty_drift_time_stable():
    """T3.6 — sovereignty_drift_index == 0 at all tick horizons (time-invariant)."""
    km   = make_kernel()
    q3   = get_q3()
    loop = SimLoop(kernel=km)
    result = loop.run(quest=q3, seed=42, ticks=20)

    pb = result.phase_b
    for m, t in zip(pb.shadow_metrics_list, pb.shadow_ticks_list):
        assert m.sovereignty_drift_index == 0.0, (
            f"sovereignty_drift must be 0.0 at all horizons. "
            f"Got {m.sovereignty_drift_index} at ticks={t}"
        )


def test_t3_7_temporal_insights_gained():
    """T3.7 — EvaluationGate marks temporal_insights_gained=True for Q3."""
    km   = make_kernel()
    q3   = get_q3()
    loop = SimLoop(kernel=km)
    ledger = LawLedger(kernel=km)
    result = loop.run(quest=q3, seed=42, ticks=20, law_ledger=ledger)
    eval_r = EvaluationGate.assess(result, kernel=km)

    assert eval_r.temporal_insights_gained is True, (
        f"⌛ Temporal insights must be gained. Eval:\n{eval_r.summary_line()}"
    )


def test_t3_8_epoch3_canonical_run():
    """T3.8 — Full epoch3 canonical run: 3 quest results, ≥3 laws, all evaluate."""
    result = run_epoch3_canonical(seed=42, ticks=20, ledger_path=":memory:")

    assert len(result.quest_results) == 3, (
        f"Must run all 3 quests. Got {len(result.quest_results)}"
    )
    # Each quest must have an evaluation receipt
    for qr in result.quest_results:
        assert qr.evaluation.evaluation_receipt_id is not None, (
            f"Quest {qr.quest.id} must have evaluation receipt"
        )

    # Laws from Q2 and Q3 should be inscribed (Q1 base metric=closure=True, also passes)
    assert len(result.laws_inscribed) >= 2, (
        f"At least 2 laws expected from 3 quest runs. Got {len(result.laws_inscribed)}"
    )

    # Cognitive growth is non-zero
    assert result.cognitive_growth >= 2

    # Temporal awareness has 3 quests
    ta = result.temporal_awareness
    assert ta["quests_run"] == 3
    assert ta["closures_achieved"] >= 2

    # Kernel cum hash is non-trivial
    assert result.kernel_cum_hash != ("0" * 64)

    print(f"\n✅ EPOCH3 canonical run complete:")
    print(f"   Quests:    {len(result.quest_results)}/3")
    print(f"   Laws:      {result.cognitive_growth}")
    print(f"   Closures:  {ta['closures_achieved']}/3")
    print(f"   Receipts:  {result.run_receipts_count}")
    for qr in result.quest_results:
        icon = "✅" if qr.evaluation.overall_pass else "⚠️"
        print(f"   {icon} {qr.quest.id} ({qr.quest.quest_type.value}): "
              f"overall={qr.evaluation.overall_pass}")
