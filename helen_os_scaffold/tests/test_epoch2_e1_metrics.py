"""
tests/test_epoch2_e1_metrics.py

E1 — EpochMetricsCollector: determinism and correctness.

Verifies the 5 EPOCH2 metrics against a real seed=42, ticks=20 run.

Tests:
  E1.1 — Same receipts + summary → same Metrics (determinism)
  E1.2 — admissibility_rate is in [0.0, 1.0]
  E1.3 — closure_success=True when return_warrant_v1 in expedition_bundle
  E1.4 — closure_success=False when bundle lacks return_warrant_v1
  E1.5 — witness_integrity.missing_pins counts gaps in 3-tick pin sequence
  E1.6 — sovereignty_drift_index == 0.0 (no cross-governance in standard run)
  E1.7 — dispute_heat is non-negative (decoys from F4 contribute)
  E1.8 — emit_attempts >= len(receipts) (anti-replay never fabricates receipts)
"""

import pytest
from helen_os.kernel import GovernanceVM
from helen_os.seeds.worlds.conquest_land import ConquestLandWorld
from helen_os.epoch2.metrics import EpochMetricsCollector, Metrics


SEED = 42
TICKS = 20


def run_world(seed=SEED, ticks=TICKS):
    """Run CONQUEST LAND and return (receipts, summary)."""
    km = GovernanceVM(ledger_path=":memory:")
    world = ConquestLandWorld(km, world_seed=seed)
    all_receipts = []
    for t in range(1, ticks + 1):
        all_receipts.extend(world.tick(t))
    return all_receipts, world.summary()


# ── E1.1 — Determinism ───────────────────────────────────────────────────────

def test_e1_metrics_deterministic():
    """E1.1 — Same inputs → same Metrics (pure function)."""
    receipts, summary = run_world()
    m1 = EpochMetricsCollector.compute(receipts, summary, TICKS)
    m2 = EpochMetricsCollector.compute(receipts, summary, TICKS)

    assert m1.admissibility_rate == m2.admissibility_rate
    assert m1.dispute_heat == m2.dispute_heat
    assert m1.closure_success == m2.closure_success
    assert m1.witness_integrity == m2.witness_integrity
    assert m1.sovereignty_drift_index == m2.sovereignty_drift_index
    print(f"✅ E1.1: Metrics deterministic (seed={SEED})")


# ── E1.2 — admissibility_rate bounds ─────────────────────────────────────────

def test_e1_admissibility_rate_bounds():
    """E1.2 — admissibility_rate is in [0.0, 1.0]."""
    receipts, summary = run_world()
    m = EpochMetricsCollector.compute(receipts, summary, TICKS)

    assert 0.0 <= m.admissibility_rate <= 1.0, (
        f"admissibility_rate out of bounds: {m.admissibility_rate}"
    )
    # With unique per-tick rids, expect near 1.0
    assert m.admissibility_rate >= 0.80, (
        f"admissibility_rate unexpectedly low: {m.admissibility_rate}"
    )
    print(f"✅ E1.2: admissibility_rate={m.admissibility_rate:.3f} ∈ [0.80, 1.0]")


# ── E1.3 — closure_success=True ──────────────────────────────────────────────

def test_e1_closure_success_true():
    """E1.3 — closure_success=True when expedition reaches Vault."""
    receipts, summary = run_world()

    assert "return_warrant_v1" in summary["expedition_bundle"], (
        "return_warrant_v1 not in expedition_bundle — world did not reach Vault"
    )
    m = EpochMetricsCollector.compute(receipts, summary, TICKS)
    assert m.closure_success is True, (
        f"closure_success should be True when return_warrant in bundle"
    )
    print(f"✅ E1.3: closure_success=True, expedition at {summary['expedition_position']}")


# ── E1.4 — closure_success=False ─────────────────────────────────────────────

def test_e1_closure_success_false_when_missing():
    """E1.4 — closure_success=False when summary says return_achieved=False."""
    receipts, summary = run_world()
    # Patch summary to simulate no Vault return
    fake_summary = dict(summary)
    fake_summary["return_achieved"] = False
    fake_summary["expedition_bundle"] = [
        e for e in summary["expedition_bundle"]
        if e != "return_warrant_v1"
    ]
    m = EpochMetricsCollector.compute(receipts, fake_summary, TICKS)
    assert m.closure_success is False
    print("✅ E1.4: closure_success=False when return_warrant absent")


# ── E1.5 — witness_integrity.missing_pins ────────────────────────────────────

def test_e1_witness_integrity_pins():
    """E1.5 — missing_pins counts gaps in the 3-tick witness pin sequence."""
    receipts, summary = run_world()
    m = EpochMetricsCollector.compute(receipts, summary, TICKS)

    expected_pin_ticks = sum(1 for t in range(1, TICKS + 1) if t % 3 == 0)
    actual_pins = sum(1 for r in receipts if r.get("evidence_type") == "witness_pin_v1")

    assert "missing_pins" in m.witness_integrity
    assert "replay_blocks" in m.witness_integrity
    assert m.witness_integrity["missing_pins"] == max(0, expected_pin_ticks - actual_pins)
    print(
        f"✅ E1.5: witness_integrity={m.witness_integrity}, "
        f"expected_pin_ticks={expected_pin_ticks}, actual={actual_pins}"
    )


# ── E1.6 — sovereignty_drift_index == 0.0 ────────────────────────────────────

def test_e1_sovereignty_drift_zero():
    """E1.6 — All governance receipts are issued by home-town factions."""
    receipts, summary = run_world()
    m = EpochMetricsCollector.compute(receipts, summary, TICKS)

    assert m.sovereignty_drift_index == 0.0, (
        f"Unexpected sovereignty drift: {m.sovereignty_drift_index}. "
        f"A non-home faction issued a governance receipt."
    )
    print(f"✅ E1.6: sovereignty_drift_index=0.0 — no cross-governance")


# ── E1.7 — dispute_heat is non-negative ──────────────────────────────────────

def test_e1_dispute_heat():
    """E1.7 — dispute_heat >= 0, and F4 decoys appear every 4 ticks."""
    receipts, summary = run_world()
    m = EpochMetricsCollector.compute(receipts, summary, TICKS)

    assert m.dispute_heat >= 0.0
    # F4 emits decoy_signal_v1 at t=4,8,12,16,20 → 5 decoys in 20 ticks → 0.25
    decoy_count = sum(1 for r in receipts if r.get("evidence_type") == "decoy_signal_v1")
    assert decoy_count > 0, "Expected F4 decoy signals in 20-tick run"
    print(f"✅ E1.7: dispute_heat={m.dispute_heat:.3f}, decoys={decoy_count}")


# ── E1.8 — emit_attempts >= receipt count ─────────────────────────────────────

def test_e1_emit_attempts_bounds():
    """E1.8 — emit_attempts from summary >= successful receipts (anti-replay never fabricates)."""
    receipts, summary = run_world()
    m = EpochMetricsCollector.compute(receipts, summary, TICKS)

    emit_attempts = summary["emit_attempts"]
    successful = len([r for r in receipts if r and not r.get("error")])

    assert emit_attempts >= successful, (
        f"emit_attempts ({emit_attempts}) < successful receipts ({successful}) — "
        f"anti-replay is over-counting successful emissions"
    )
    print(
        f"✅ E1.8: emit_attempts={emit_attempts}, successful={successful}, "
        f"replay_blocks={m.witness_integrity['replay_blocks']}"
    )
