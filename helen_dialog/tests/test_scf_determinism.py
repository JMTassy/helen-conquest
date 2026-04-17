#!/usr/bin/env python3
"""
test_scf_determinism.py

T5: SCF Determinism

Verifies: SCF with frozen params produces identical output across independent runs.
- Same input (memory, trace, candidates) → identical filtered evidence + identical telemetry
- Params hash remains constant
- Eigenvalue computation is deterministic (fixed-point arithmetic)

Acceptance: sha256(telemetry_json) identical between runs.
"""

import sys
import os
import json
import hashlib
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from helen_os.spectral.engine import SpectralAnalyzer, SCFParams


def sha256_json(obj: dict) -> str:
    """SHA256 of canonical JSON."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_test_input():
    """Create deterministic test input (same across runs)."""
    memory_facts = [
        {
            "fact_id": "M1",
            "content": "HELEN observed user intent",
            "status": "OBSERVED",
            "turn": 1,
        },
        {
            "fact_id": "M2",
            "content": "Previous constraint about clarity",
            "status": "CONFIRMED",
            "turn": 2,
        },
        {
            "fact_id": "M3",
            "content": "Contradicts M2",
            "status": "DISPUTED",
            "severity_fp": 750000,
            "turn": 3,
        },
    ]

    trace_events = [
        {
            "event_id": "T1",
            "event_type": "anomaly_coherence_drop",
            "weight_fp": 500000,
            "turn": 2,
        },
        {
            "event_id": "T2",
            "event_type": "anomaly_symmetry_break",
            "weight_fp": 300000,
            "turn": 3,
        },
    ]

    candidates = [
        {
            "rid": "C1",
            "type": "proposal",
            "payload": "HELEN proposes course A",
            "references": ["M1", "M2"],
        },
        {
            "rid": "C2",
            "type": "proposal",
            "payload": "HELEN proposes course B",
            "references": ["M3"],
        },
        {
            "rid": "C3",
            "type": "correction",
            "payload": "Correction to C1",
            "references": ["C1"],
        },
    ]

    return candidates, memory_facts, trace_events


def run_scf_deterministic(num_runs: int = 3) -> list:
    """Run SCF multiple times with identical input. Return list of telemetry hashes."""
    params = SCFParams()
    scf = SpectralAnalyzer(params)

    candidates, memory_facts, trace_events = create_test_input()

    results = []
    for run_num in range(num_runs):
        filtered, telemetry = scf.process(candidates, memory_facts, trace_events, turn=1)

        # Record telemetry hash (excluding timestamp which changes each run)
        telemetry_copy = telemetry.copy()
        telemetry_copy.pop("timestamp", None)  # Remove timestamp for determinism check
        telemetry_hash = sha256_json(telemetry_copy)

        results.append({
            "run": run_num,
            "telemetry_hash": telemetry_hash,
            "evidence_in": telemetry["evidence_in_count"],
            "evidence_out": telemetry["evidence_out_count"],
            "params_hash": telemetry["params_hash"],
        })

    return results


def test_scf_determinism():
    """
    T5: SCF determinism across independent runs.

    Verifies:
    1. Same input → identical telemetry hash
    2. Params hash constant
    3. Filtered evidence count deterministic
    """
    print("\n" + "=" * 70)
    print("T5: SCF DETERMINISM")
    print("=" * 70)

    results = run_scf_deterministic(num_runs=5)

    print(f"\nRun results:")
    for result in results:
        print(f"  Run {result['run']}: {result['telemetry_hash'][:16]}... "
              f"(in={result['evidence_in']}, out={result['evidence_out']})")

    # Acceptance: All hashes identical
    hashes = [r["telemetry_hash"] for r in results]
    params_hashes = [r["params_hash"] for r in results]

    assert len(set(hashes)) == 1, f"Telemetry hashes differ: {set(hashes)}"
    assert len(set(params_hashes)) == 1, f"Params hashes differ: {set(params_hashes)}"

    # Verify evidence counts are consistent
    evidence_in = [r["evidence_in"] for r in results]
    evidence_out = [r["evidence_out"] for r in results]
    assert len(set(evidence_in)) == 1, f"Evidence IN counts differ: {set(evidence_in)}"
    assert len(set(evidence_out)) == 1, f"Evidence OUT counts differ: {set(evidence_out)}"

    print(f"\n✅ T5 PASSED: Determinism verified")
    print(f"   All {len(results)} runs produced identical telemetry hash")
    print(f"   Params hash constant: {results[0]['params_hash'][:16]}...")


if __name__ == "__main__":
    try:
        test_scf_determinism()
    except AssertionError as e:
        print(f"\n❌ T5 FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ T5 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
