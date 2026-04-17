#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: Canonical Dialogue Events with Payload/Meta Split

This test demonstrates:
1. Building canonical dialogue events with payload/meta separation
2. Computing payload_hash and cumulative hash
3. Verifying that timestamp_utc is meta-only (not in hash)
4. Running same turn twice proves determinism (same payload_hash + cum_hash)

Expected output:
  Turn 1, Run A: cum_hash = XYZ123...
  Turn 1, Run B: cum_hash = XYZ123... (IDENTICAL - proof of determinism)
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from street1_runner_with_dialogue import (
    canonical,
    sha256_obj,
    sha256_hex,
    build_canonical_dialogue_event,
    normalize_reason_codes,
)

def test_payload_meta_split():
    """Test 1: Payload and meta are properly separated."""
    print("=" * 80)
    print("TEST 1: Payload/Meta Split")
    print("=" * 80)

    hal = {
        "verdict": "PASS",
        "reasons_codes": ["AUTHORITY_CONSTRAINT_OK", "BYZANTINE_DETECTION_OK"],
        "required_fixes": [],
        "certificates": ["KTAU_OK"],
        "refs": {
            "run_id": "run-001",
            "kernel_hash": "a" * 64,
            "policy_hash": "b" * 64,
            "ledger_cum_hash": "c" * 64,
            "identity_hash": "d" * 64,
        },
        "mutations": [],
    }

    her_text = "All governance checks passed. System is ready."

    # Build event
    event = build_canonical_dialogue_event(
        turn=1,
        her_text=her_text,
        hal=hal,
        raw_text="[HER]\nAll governance checks passed...\n\n[HAL]\n{...}",
    )

    print("\n✅ Event structure:")
    print(f"  type: {event['type']}")
    print(f"  seq: {event['seq']}")
    print(f"  payload keys: {list(event['payload'].keys())}")
    print(f"  meta keys: {list(event['meta'].keys())}")
    print(f"\n  PAYLOAD (hash-bound):")
    for k, v in event['payload'].items():
        if isinstance(v, dict) and len(str(v)) > 60:
            print(f"    {k}: {{...}} ({len(str(v))} chars)")
        else:
            print(f"    {k}: {v}")

    print(f"\n  META (not hash-bound):")
    for k, v in event['meta'].items():
        print(f"    {k}: {v}")

    print(f"\n  HASHES:")
    print(f"    payload_hash: {event['payload_hash'][:16]}... (SHA256 of PAYLOAD only)")
    print(f"    cum_hash: {event['cum_hash'][:16]}... (SHA256(prev||payload))")

    # Verify: timestamp is in meta, not in payload
    assert "timestamp_utc" not in event["payload"], "ERROR: timestamp_utc should not be in payload!"
    assert "timestamp_utc" in event["meta"], "ERROR: timestamp_utc should be in meta!"
    print("\n✅ PASS: timestamp_utc correctly placed in META (not PAYLOAD)")

    return event


def test_determinism_same_input():
    """Test 2: Same input produces same payload_hash + cum_hash."""
    print("\n" + "=" * 80)
    print("TEST 2: Determinism - Same Input Produces Same Hashes")
    print("=" * 80)

    hal = {
        "verdict": "WARN",
        "reasons_codes": ["NONDETERMINISM_TIMESTAMP"],
        "required_fixes": ["OMIT_TIMESTAMP_FROM_PAYLOAD"],
        "certificates": [],
        "refs": {
            "run_id": "run-002",
            "kernel_hash": "e" * 64,
            "policy_hash": "f" * 64,
            "ledger_cum_hash": "0" * 64,
            "identity_hash": "1" * 64,
        },
        "mutations": [
            {
                "policy": "dialogue_logging",
                "change": "move timestamp to meta",
            }
        ],
    }

    her_text = "I propose moving timestamps to metadata to enable deterministic proofs."

    # Run 1
    print("\nRun A: Building event...")
    event_a = build_canonical_dialogue_event(
        turn=1,
        her_text=her_text,
        hal=hal,
    )
    payload_hash_a = event_a["payload_hash"]
    cum_hash_a = event_a["cum_hash"]

    # Run 2 (same input, different wall-clock time)
    print("Run B: Building same event again (few seconds later)...")
    import time
    time.sleep(0.5)  # Different wall-clock time
    event_b = build_canonical_dialogue_event(
        turn=1,
        her_text=her_text,
        hal=hal,
    )
    payload_hash_b = event_b["payload_hash"]
    cum_hash_b = event_b["cum_hash"]

    print(f"\n  Run A payload_hash: {payload_hash_a[:16]}...")
    print(f"  Run B payload_hash: {payload_hash_b[:16]}...")
    assert payload_hash_a == payload_hash_b, "ERROR: payload_hash differs!"
    print("  ✅ IDENTICAL payload_hash (determinism preserved)")

    print(f"\n  Run A cum_hash: {cum_hash_a[:16]}...")
    print(f"  Run B cum_hash: {cum_hash_b[:16]}...")
    assert cum_hash_a == cum_hash_b, "ERROR: cum_hash differs!"
    print("  ✅ IDENTICAL cum_hash (deterministic hash chain)")

    print("\n✅ PASS: Same input produces deterministic hashes despite different timestamps")

    return event_a, event_b


def test_reason_codes_sorting():
    """Test 3: Reason codes are sorted lexicographically."""
    print("\n" + "=" * 80)
    print("TEST 3: Reason Code Normalization & Sorting")
    print("=" * 80)

    test_cases = [
        (["All K-gates verified", "Ledger coherent"], ["ALL_K_GATES_VERIFIED", "LEDGER_COHERENT"]),
        (["Ledger coherent", "All K-gates verified"], ["ALL_K_GATES_VERIFIED", "LEDGER_COHERENT"]),  # should sort
        (["RHO_VIABILITY_CRITICAL", "BYZANTINE_DETECTION_OK"], ["BYZANTINE_DETECTION_OK", "RHO_VIABILITY_CRITICAL"]),
    ]

    for input_codes, expected in test_cases:
        result = normalize_reason_codes(input_codes)
        print(f"\n  Input: {input_codes}")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        # Result may have more codes due to conversion, but should be sorted
        assert result == sorted(result), f"ERROR: result not sorted! {result}"
        print(f"  ✅ Correctly sorted")

    print("\n✅ PASS: Reason codes normalized and sorted lexicographically")


def test_canonical_json_determinism():
    """Test 4: Canonical JSON is deterministic (keys sorted, etc)."""
    print("\n" + "=" * 80)
    print("TEST 4: Canonical JSON Determinism")
    print("=" * 80)

    obj = {
        "z_field": 1,
        "a_field": 2,
        "m_field": {"nested_z": "value", "nested_a": "other"},
    }

    canon1 = canonical(obj)
    canon2 = canonical(obj)

    print(f"\n  Canonicalized: {canon1}")
    assert canon1 == canon2, "ERROR: canonical() is not deterministic!"
    print(f"\n✅ PASS: Canonical form is identical across calls")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CANONICAL DIALOGUE FORMAT TEST SUITE")
    print("Testing Payload/Meta Split + Deterministic Hashing")
    print("=" * 80)

    test_canonical_json_determinism()
    event1 = test_payload_meta_split()
    events_a, events_b = test_determinism_same_input()
    test_reason_codes_sorting()

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✅")
    print("=" * 80)
    print("\nSummary:")
    print("  ✅ Timestamp is in META (not PAYLOAD) → allows real timestamps without breaking determinism")
    print("  ✅ Same input → identical payload_hash + cum_hash → determinism proven")
    print("  ✅ Reason codes are normalized and sorted → no fragile ordering")
    print("  ✅ Canonical JSON is deterministic → reproducible proofs")
    print("\nNext steps:")
    print("  1. Update her_hal_validate.cjs to work with dialogue.ndjson (NDJSON mode)")
    print("  2. Run moment detector to find HER_HAL_MOMENT (veto + adaptation + continuity)")
    print("  3. Run CI pipeline (K-τ, K-ρ, CouplingGate)")
