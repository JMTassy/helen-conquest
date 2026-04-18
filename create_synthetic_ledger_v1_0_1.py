#!/usr/bin/env python3
"""
Create Synthetic CWL v1.0.1 Compliant Ledger

Generates test ledger events using the exact v1.0.1 formula:
cum_hash_i = SHA256(PREFIX_LEDGER || prev_cum_hash || payload_hash_i)

Used for validator testing and proof of correctness.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime

# Constants from CWL_V1_0_1_ARCHITECTURE.md §3
PREFIX_LEDGER = b"HELEN_CUM_V1"
ZERO_HASH = "0" * 64

def compute_payload_hash(payload: dict) -> str:
    """Compute canonical payload hash: SHA256(canon(payload))"""
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload_json.encode()).hexdigest()

def compute_cum_hash(prev_cum_hash: str, payload_hash: str) -> str:
    """Compute cumulative hash per v1.0.1 formula"""
    prev_bytes = bytes.fromhex(prev_cum_hash)
    payload_bytes = bytes.fromhex(payload_hash)
    combined = PREFIX_LEDGER + prev_bytes + payload_bytes
    return hashlib.sha256(combined).hexdigest()

def create_event(seq: int, prev_cum: str, payload: dict, event_type: str = "event_v1") -> dict:
    """Create a single ledger event with correct v1.0.1 hashing"""
    payload_hash = compute_payload_hash(payload)
    cum_hash = compute_cum_hash(prev_cum, payload_hash)

    return {
        "type": event_type,
        "seq": seq,
        "payload": payload,
        "payload_hash": payload_hash,
        "prev_cum_hash": prev_cum,
        "cum_hash": cum_hash,
        "hash_law": "CWL_CUM_V1",  # ← CRITICAL: Semantic versioning for hash formula
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "generated_for": "test_validation"
        }
    }

def create_synthetic_ledger() -> list:
    """
    Generate 5 test events following CWL v1.0.1 specification.

    Returns: List of event dicts
    """
    events = []

    # Event 0: Genesis
    genesis_payload = {
        "schema": "GENESIS_V1",
        "cwl_version": "v1.0.1",
        "description": "Bootstrap ledger for CWL v1.0.1",
        "timestamp": "2026-02-27T00:00:00Z"
    }
    event0 = create_event(0, ZERO_HASH, genesis_payload, "genesis")
    events.append(event0)

    # Event 1: Receipt (SHIP decision)
    receipt_payload = {
        "schema": "RECEIPT_V1",
        "rid": "R-001",
        "type": "receipt_v1",
        "issuer": "MAYOR",
        "outcome": "SHIP",
        "payload_hash": "abc123def456"
    }
    event1 = create_event(1, event0["cum_hash"], receipt_payload, "receipt")
    events.append(event1)

    # Event 2: Attestation (proposal)
    attestation_payload = {
        "schema": "ATTESTATION_V1",
        "aid": "A-002",
        "type": "attestation_v1",
        "actor": "L0_agent",
        "authority": False,
        "payload": {"claim": "system operational"}
    }
    event2 = create_event(2, event1["cum_hash"], attestation_payload, "attestation")
    events.append(event2)

    # Event 3: Trace (non-sovereign telemetry)
    trace_payload = {
        "schema": "TRACE_EVENT_V1",
        "type": "trace_event",
        "actor": "system",
        "authority": False,
        "event": "boot_success",
        "details": "System boots with seal_v2 valid"
    }
    event3 = create_event(3, event2["cum_hash"], trace_payload, "trace_event")
    events.append(event3)

    # Event 4: Seal (identity closure)
    # The seal references the cumulative hash UP TO (but not including) the seal itself
    # So it references event3's cum_hash
    seal_payload = {
        "schema": "SEAL_V1",
        "type": "seal_v2",
        "refs": {
            "final_ledger_cum_hash": event3["cum_hash"],  # ← Previous event's hash
            "final_trace_hash": "0000000000000000000000000000000000000000000000000000000000000000",
            "env_hash": "1111111111111111111111111111111111111111111111111111111111111111",
            "kernel_hash": "2222222222222222222222222222222222222222222222222222222222222222"
        },
        "outcome": "SEALED"
    }
    event4 = create_event(4, event3["cum_hash"], seal_payload, "seal")
    events.append(event4)

    return events

def write_ledger(events: list, output_path: Path) -> None:
    """Write events to NDJSON ledger file"""
    with open(output_path, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    print(f"✓ Ledger written to {output_path}")

def print_ledger_summary(events: list) -> None:
    """Print readable summary of generated ledger"""
    print("\n" + "=" * 80)
    print("SYNTHETIC LEDGER v1.0.1 GENERATED")
    print("=" * 80)
    print(f"\nTotal events: {len(events)}")
    print(f"\nHash chain verification:")

    for event in events:
        event_type = event.get("type", "unknown")
        seq = event.get("seq", "?")
        cum_hash = event.get("cum_hash", "")[:16]
        payload_type = event.get("payload", {}).get("schema", "")

        print(f"  Seq {seq}: {event_type:15} | {payload_type:20} | hash: {cum_hash}...")

    print(f"\nFinal ledger cum_hash: {events[-1]['cum_hash']}")
    print(f"\nBoot validator should:")
    print(f"  ✓ Load all {len(events)} events")
    print(f"  ✓ Verify hash chain (each matches recomputed)")
    print(f"  ✓ Match final hash against seal")
    print(f"  ✓ Return SUCCESS ✅")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print("Creating synthetic CWL v1.0.1 ledger...")

    events = create_synthetic_ledger()
    output_file = Path("synthetic_ledger_v1_0_1.ndjson")

    write_ledger(events, output_file)
    print_ledger_summary(events)

    print(f"\nNext step: Validate with boot validator")
    print(f"  python3 cwl_boot_validator.py")
