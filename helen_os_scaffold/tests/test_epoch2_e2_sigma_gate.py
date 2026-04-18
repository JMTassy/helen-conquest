"""
tests/test_epoch2_e2_sigma_gate.py

E2 — SigmaGate: multi-seed invariant validation.

Tests:
  E2.1 — SigmaGate.run() returns SigmaResult with correct structure
  E2.2 — H2 (closure_success across seeds) passes sigma gate
  E2.3 — A false hypothesis (admissibility_rate > 0.9999) FAILS sigma gate
  E2.4 — evidence_receipt_ids is non-empty (runs were receipted)
  E2.5 — SigmaResult.to_receipt_payload() has all required fields
  E2.6 — H1 (admissibility_rate >= 0.80) passes sigma gate
  E2.7 — H3 (sovereignty_drift == 0) passes sigma gate
"""

import pytest
from helen_os.kernel import GovernanceVM
from helen_os.epoch2.sigma_gate import SigmaGate, SigmaResult
from helen_os.epoch2.metrics import Metrics


def make_kernel():
    return GovernanceVM(ledger_path=":memory:")


# ── E2.1 — Structure ──────────────────────────────────────────────────────────

def test_e2_sigma_result_structure():
    """E2.1 — SigmaGate.run() returns SigmaResult with all required attributes."""
    km = make_kernel()
    result = SigmaGate.run(
        hypothesis="admissibility_rate >= 0.80 (structure test)",
        metric_fn=lambda m: m.admissibility_rate,
        metric_name="admissibility_rate",
        threshold=0.80,
        kernel=km,
    )

    assert isinstance(result, SigmaResult)
    assert isinstance(result.passed, bool)
    assert isinstance(result.hypothesis, str)
    assert isinstance(result.seed_set, list)
    assert isinstance(result.metric_values, dict)
    assert isinstance(result.evidence_receipt_ids, list)
    assert len(result.seed_set) == len(SigmaGate.DEFAULT_SEEDS)
    assert result.metric_name == "admissibility_rate"
    assert result.threshold == 0.80
    print(f"✅ E2.1: SigmaResult structure correct, passed={result.passed}")


# ── E2.2 — H2 passes (structural invariant) ──────────────────────────────────

def test_e2_h2_closure_passes():
    """E2.2 — closure_success=True for all standard seeds (H2 hypothesis)."""
    km = make_kernel()
    result = SigmaGate.run(
        hypothesis=(
            "closure_success == True in 20-tick runs: "
            "expedition reaches Vault when F3 escorts on siege_critical"
        ),
        metric_fn=lambda m: float(m.closure_success),
        metric_name="closure_success",
        threshold=1.0,
        kernel=km,
        ticks=20,
    )

    assert result.passed, (
        f"H2 should pass — closure_success should be True for all seeds. "
        f"metric_values={result.metric_values}. reason={result.reason}"
    )
    # All seeds should show closure_success=True (1.0)
    for seed, val in result.metric_values.items():
        assert val == 1.0, f"seed={seed}: closure_success={val} (expected 1.0)"

    print(f"✅ E2.2: H2 passes — closure_success=True for {result.seed_set}")
    print(f"   metric_values={result.metric_values}")


# ── E2.3 — False hypothesis fails ────────────────────────────────────────────

def test_e2_false_hypothesis_fails():
    """E2.3 — A hypothesis with an impossible threshold fails the sigma gate."""
    km = make_kernel()

    # Impossible: closure_success=False (expedition always reaches Vault in 20t)
    # metric_fn returns 0.0 when closure is True → fails threshold=1.0
    result_impossible = SigmaGate.run(
        hypothesis="closure_success == False (impossible in 20-tick runs)",
        metric_fn=lambda m: 0.0 if m.closure_success else 1.0,
        metric_name="no_closure",
        threshold=1.0,
        kernel=km,
        seed_set=[42],
    )

    assert not result_impossible.passed, (
        "A hypothesis requiring closure_success=False should fail "
        "(expedition always reaches Vault in 20-tick runs with F3 fix)"
    )
    print(f"✅ E2.3: False hypothesis correctly fails. reason={result_impossible.reason[:80]}")


# ── E2.4 — Evidence receipts emitted ────────────────────────────────────────

def test_e2_evidence_receipts_non_empty():
    """E2.4 — evidence_receipt_ids is non-empty (sigma runs were receipted)."""
    km = make_kernel()
    result = SigmaGate.run(
        hypothesis="closure_success == True (evidence test)",
        metric_fn=lambda m: float(m.closure_success),
        metric_name="closure_success",
        threshold=1.0,
        kernel=km,
        seed_set=[42],  # single seed for speed
    )

    assert len(result.evidence_receipt_ids) >= 1
    for rid in result.evidence_receipt_ids:
        assert rid.startswith("R-"), f"Malformed receipt id: {rid}"
    print(f"✅ E2.4: {len(result.evidence_receipt_ids)} evidence receipt(s) — {result.evidence_receipt_ids}")


# ── E2.5 — to_receipt_payload() structure ────────────────────────────────────

def test_e2_receipt_payload_structure():
    """E2.5 — SigmaResult.to_receipt_payload() has all required fields."""
    km = make_kernel()
    result = SigmaGate.run(
        hypothesis="test payload structure",
        metric_fn=lambda m: m.admissibility_rate,
        metric_name="admissibility_rate",
        threshold=0.5,
        kernel=km,
        seed_set=[42],
    )

    payload = result.to_receipt_payload()
    required_fields = [
        "type", "hypothesis", "verdict", "seed_set",
        "metric_name", "metric_values", "threshold",
        "evidence_receipt_ids", "reason",
    ]
    for f in required_fields:
        assert f in payload, f"Missing field in to_receipt_payload(): {f!r}"
    assert payload["type"] == "SIGMA_GATE_V1"
    print(f"✅ E2.5: to_receipt_payload() has all required fields")


# ── E2.6 — H1 passes ─────────────────────────────────────────────────────────

def test_e2_h1_admissibility_passes():
    """E2.6 — H1: admissibility_rate >= 0.80 passes for all standard seeds."""
    km = make_kernel()
    result = SigmaGate.run(
        hypothesis=(
            "admissibility_rate >= 0.80 across seed set [42,7,99]: "
            "anti-replay scheme does not over-block"
        ),
        metric_fn=lambda m: m.admissibility_rate,
        metric_name="admissibility_rate",
        threshold=0.80,
        kernel=km,
    )

    assert result.passed, (
        f"H1 should pass. metric_values={result.metric_values}. reason={result.reason}"
    )
    print(f"✅ E2.6: H1 passes — admissibility_rate≥0.80 for {result.seed_set}")


# ── E2.7 — H3 passes ─────────────────────────────────────────────────────────

def test_e2_h3_sovereignty_passes():
    """E2.7 — H3: sovereignty_drift_index == 0 passes for all standard seeds."""
    km = make_kernel()
    result = SigmaGate.run(
        hypothesis=(
            "sovereignty_drift_index == 0.0 across seed set [42,7,99]: "
            "all governance receipts issued by home-town factions only"
        ),
        metric_fn=lambda m: 1.0 - m.sovereignty_drift_index,
        metric_name="sovereignty_integrity",
        threshold=1.0,
        kernel=km,
    )

    assert result.passed, (
        f"H3 should pass. metric_values={result.metric_values}. reason={result.reason}"
    )
    print(f"✅ E2.7: H3 passes — sovereignty_drift=0 for {result.seed_set}")
