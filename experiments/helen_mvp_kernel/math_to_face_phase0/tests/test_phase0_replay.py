"""Phase 0 replay invariant test (stdlib only).

Asserts: same input + same seed -> same hashes across N runs.

The non-negotiable invariant from the operator's HAL verdict:
    same input + same seed -> same spectrum hash + same SDE trace hash
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parents[1]  # experiments/helen_mvp_kernel/
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from math_to_face_phase0.phase0_runner import run_one  # noqa: E402

FIXTURE = PKG_ROOT / "math_to_face_phase0" / "fixtures" / "phase0_prime7.json"


def _run_three():
    return [run_one(FIXTURE, emit=False) for _ in range(3)]


def test_operator_hash_replay_consistent():
    runs = _run_three()
    h0 = runs[0]["operator_hash"]
    for i, r in enumerate(runs):
        assert r["operator_hash"] == h0, f"run {i} drifted: {r['operator_hash']} != {h0}"


def test_eigenvalues_hash_replay_consistent():
    runs = _run_three()
    h0 = runs[0]["eigenvalues_hash"]
    for i, r in enumerate(runs):
        assert r["eigenvalues_hash"] == h0, f"run {i} drifted on eigenvalues_hash"


def test_trace_hash_replay_consistent():
    runs = _run_three()
    h0 = runs[0]["trace_hash"]
    for i, r in enumerate(runs):
        assert r["trace_hash"] == h0, f"run {i} drifted on trace_hash"


def test_z_T_hash_replay_consistent():
    runs = _run_three()
    h0 = runs[0]["z_T_hash"]
    for i, r in enumerate(runs):
        assert r["z_T_hash"] == h0, f"run {i} drifted on z_T_hash"


def test_spectral_receipt_hash_replay_consistent():
    runs = _run_three()
    h0 = runs[0]["spectral_receipt_hash"]
    for i, r in enumerate(runs):
        assert r["spectral_receipt_hash"] == h0


def test_sde_receipt_hash_replay_consistent():
    runs = _run_three()
    h0 = runs[0]["sde_receipt_hash"]
    for i, r in enumerate(runs):
        assert r["sde_receipt_hash"] == h0


def test_constitutional_locks_present():
    runs = _run_three()
    for r in runs:
        spec = r["spectral_receipt"]
        sde = r["sde_receipt"]
        assert spec["scope"] == "RESEARCH_SUBSANDBOX"
        assert sde["scope"] == "RESEARCH_SUBSANDBOX"
        assert spec["sovereign_admitted"] is False
        assert sde["sovereign_admitted"] is False
        assert spec["decimal_precision"] == 12
        assert sde["decimal_precision"] == 12


def test_phi_sde_zero_projection_drives_contraction():
    """With Pi_QAM=zero and ZERO_NOISE, z_T must have norm < |z_0|."""
    runs = _run_three()
    sde = runs[0]["sde_receipt"]
    z_T_norm = float(sde["z_T_summary"]["norm"])
    # z_0 is H(2), 512-dim sin/cos values; bounded |x|<=1, so |z_0| <= sqrt(512)
    # Contraction must drive norm strictly below initial.
    # With dt=0.1, T=5, the product of (1 - dt*phi^{-t}) over 50 steps
    # contracts by orders of magnitude. Sanity check: z_T_norm < 0.5 * sqrt(512).
    import math as _m
    upper = 0.5 * _m.sqrt(512)
    assert z_T_norm < upper, f"contraction failed: z_T_norm={z_T_norm} >= {upper}"


if __name__ == "__main__":
    # Allow stdlib-only execution without pytest
    tests = [
        test_operator_hash_replay_consistent,
        test_eigenvalues_hash_replay_consistent,
        test_trace_hash_replay_consistent,
        test_z_T_hash_replay_consistent,
        test_spectral_receipt_hash_replay_consistent,
        test_sde_receipt_hash_replay_consistent,
        test_constitutional_locks_present,
        test_phi_sde_zero_projection_drives_contraction,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e!r}")
            failed += 1
    print()
    print(f"REPLAY: {len(tests) - failed}/{len(tests)} passed")
    sys.exit(0 if failed == 0 else 1)
