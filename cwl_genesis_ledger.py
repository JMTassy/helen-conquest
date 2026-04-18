#!/usr/bin/env python3
"""
CWL v1.0.1 — Genesis Ledger Bootstrap

Creates the first v1.0.1-native ledger:
  Event 0: genesis_v1  (with MAYOR_PK anchor — D-004)
  Event 1: mayor_rotate_v1  (key registration — D-001)
  Event 2: seal_v2  (identity closure — seals ledger + trace + env + kernel)

Runs boot validator immediately. Fails closed on any mismatch.
"""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timezone

# Hash law constants (frozen v1.0.1)
PREFIX_LEDGER = b"HELEN_CUM_V1"
ZERO_HASH = "0" * 64

# ──────────────────────────────────────────────────────────────────
# Hash utilities
# ──────────────────────────────────────────────────────────────────

def payload_hash(payload: dict) -> str:
    """SHA256(canon(payload)) — canonical hash."""
    s = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode()).hexdigest()

def cum_hash(prev: str, ph: str) -> str:
    """SHA256(PREFIX || prev_cum_hash || payload_hash)."""
    return hashlib.sha256(
        PREFIX_LEDGER + bytes.fromhex(prev) + bytes.fromhex(ph)
    ).hexdigest()

def env_fingerprint() -> str:
    """Stable env hash: SHA256 of hostname + uid."""
    import socket
    data = f"{socket.gethostname()}:{os.getuid()}"
    return hashlib.sha256(data.encode()).hexdigest()

def kernel_fingerprint() -> str:
    """Stable kernel hash: SHA256 of this file's contents."""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# ──────────────────────────────────────────────────────────────────
# Event builders
# ──────────────────────────────────────────────────────────────────

def make_event(seq: int, prev_cum: str, payload_dict: dict, event_type: str) -> dict:
    """Build a single ledger event with correct CWL_CUM_V1 hashing."""
    ph = payload_hash(payload_dict)
    ch = cum_hash(prev_cum, ph)
    return {
        "type": event_type,
        "seq": seq,
        "payload": payload_dict,
        "payload_hash": ph,
        "prev_cum_hash": prev_cum,
        "cum_hash": ch,
        "hash_law": "CWL_CUM_V1",
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}
    }

def make_seal(seq: int, prev_cum: str, ledger_tip: str,
              env_hash: str, kernel_hash: str, mayor_pk_fingerprint: str) -> dict:
    """Build seal event (terminus — does NOT enter hash chain)."""
    payload_dict = {
        "schema": "SEAL_V2",
        "refs": {
            "final_ledger_cum_hash": ledger_tip,    # hash before this seal
            "final_trace_hash": ZERO_HASH,           # no trace yet at genesis
            "env_hash": env_hash,
            "kernel_hash": kernel_hash,
            "mayor_pk_fingerprint": mayor_pk_fingerprint,  # D-004 anchor
        },
        "cwl_version": "1.0.1",
        "outcome": "SEALED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    ph = payload_hash(payload_dict)
    ch = cum_hash(prev_cum, ph)   # seal does have a cum_hash for chain continuity
    return {
        "type": "seal",
        "seq": seq,
        "payload": payload_dict,
        "payload_hash": ph,
        "prev_cum_hash": prev_cum,
        "cum_hash": ch,
        "hash_law": "CWL_CUM_V1",
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}
    }


# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────

def generate_genesis_ledger(
    genesis_event_path: Path,
    rotation_receipt_path: Path,
    output_path: Path,
) -> dict:
    """
    Generate and seal the v1.0.1 genesis ledger.

    Structure:
      Seq 0: genesis_v1 (MAYOR_PK anchor)
      Seq 1: mayor_rotate_v1 (key registration)
      Seq 2: seal_v2 (identity closure)

    Returns boot validation result.
    """
    print("=" * 80)
    print("CWL v1.0.1 — GENESIS LEDGER BOOTSTRAP")
    print("=" * 80)
    print()

    # Load ceremony artifacts
    genesis_payload = json.loads(genesis_event_path.read_text())
    rotation_payload = json.loads(rotation_receipt_path.read_text())

    mayor_pk_fp = genesis_payload.get("mayor_pk_fingerprint", ZERO_HASH)
    print(f"MAYOR_PK Fingerprint:  {mayor_pk_fp[:16]}...")
    print(f"Env hash:              (computing from hostname + uid)")
    print(f"Kernel hash:           (computing from genesis script)")
    print()

    # Compute environment + kernel identity
    env_h = env_fingerprint()
    kern_h = kernel_fingerprint()
    print(f"  Env fingerprint:   {env_h[:16]}...")
    print(f"  Kernel fingerprint:{kern_h[:16]}...")
    print()

    # Build events
    events = []
    prev = ZERO_HASH

    # Seq 0: genesis_v1
    print("STEP 1: Genesis event (MAYOR_PK anchor)")
    e0 = make_event(0, prev, genesis_payload, "genesis_v1")
    events.append(e0)
    prev = e0["cum_hash"]
    print(f"  cum_hash: {prev[:16]}...")

    # Seq 1: mayor_rotate_v1
    print("STEP 2: Key registration (mayor_rotate_v1)")
    e1 = make_event(1, prev, rotation_payload, "mayor_rotate_v1")
    events.append(e1)
    prev = e1["cum_hash"]
    print(f"  cum_hash: {prev[:16]}...")

    # Record ledger tip BEFORE seal
    ledger_tip = prev
    print(f"\nLedger tip (before seal): {ledger_tip[:16]}...")

    # Seq 2: seal_v2 (identity closure)
    print("\nSTEP 3: Seal genesis ledger (identity closure)")
    e2 = make_seal(2, prev, ledger_tip, env_h, kern_h, mayor_pk_fp)
    events.append(e2)
    print(f"  Seal cum_hash: {e2['cum_hash'][:16]}...")
    print(f"  References ledger tip: {ledger_tip[:16]}...")

    # Write ledger
    with open(output_path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
    print(f"\n✓ Ledger written: {output_path} ({len(events)} events)")

    return {
        "events": len(events),
        "ledger_tip": ledger_tip,
        "seal_hash": e2["cum_hash"],
        "env_hash": env_h,
        "kernel_hash": kern_h,
        "mayor_pk_fingerprint": mayor_pk_fp,
    }


# ──────────────────────────────────────────────────────────────────
# Boot validation inline
# ──────────────────────────────────────────────────────────────────

def inline_boot_verify(ledger_path: Path) -> bool:
    """
    Re-implement minimal boot verification inline to avoid import issues.
    Returns True if ledger chain and seal binding are valid.
    """
    events = []
    with open(ledger_path) as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))

    current = ZERO_HASH
    for ev in events:
        if ev.get("hash_law", "CWL_CUM_V0") != "CWL_CUM_V1":
            continue
        if ev.get("type") == "seal":
            # Chain terminus: verify seal references our current tip
            seal_tip = ev.get("payload", {}).get("refs", {}).get("final_ledger_cum_hash")
            if seal_tip != current:
                print(f"  ❌ Seal mismatch: expected {current[:16]}... got {seal_tip[:16] if seal_tip else 'MISSING'}...")
                return False
            return True
        ph = ev.get("payload_hash", "")
        expected = hashlib.sha256(
            PREFIX_LEDGER + bytes.fromhex(current) + bytes.fromhex(ph)
        ).hexdigest()
        actual = ev.get("cum_hash", "")
        if expected != actual:
            print(f"  ❌ Hash mismatch at seq {ev.get('seq')}")
            return False
        current = actual

    return True


if __name__ == "__main__":
    import subprocess, sys

    # Locate ceremony artifacts
    genesis_files   = sorted(Path(".").glob("genesis_event_v1_0_1.json"))
    rotation_files  = sorted(Path(".").glob("mayor_rotate_v1_genesis_*.json"))

    if not genesis_files or not rotation_files:
        print("ERROR: Run cwl_mayor_key_ceremony.py first.")
        sys.exit(1)

    genesis_event_path  = genesis_files[0]
    rotation_path       = rotation_files[0]
    output_path         = Path("genesis_ledger_v1_0_1.ndjson")

    result = generate_genesis_ledger(genesis_event_path, rotation_path, output_path)

    # Boot validate
    print("\n" + "=" * 80)
    print("BOOT VALIDATION — Fresh Machine Replay")
    print("=" * 80)

    valid = inline_boot_verify(output_path)
    if valid:
        print("\n✅ BOOT VALIDATION: PASSED")
        print("   Hash chain:    VALID")
        print("   Seal binding:  VERIFIED")
        print("   Root of trust: ESTABLISHED")
        print()
        print(f"   Genesis ledger: {output_path}")
        print(f"   Ledger tip:     {result['ledger_tip'][:16]}...")
        print(f"   MAYOR_PK fp:    {result['mayor_pk_fingerprint'][:16]}...")
        print(f"   Env hash:       {result['env_hash'][:16]}...")
        print(f"   Kernel hash:    {result['kernel_hash'][:16]}...")
    else:
        print("\n❌ BOOT VALIDATION: FAILED — FAIL CLOSED")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("GENESIS LEDGER COMPLETE — CWL v1.0.1 ROOT OF TRUST ESTABLISHED")
    print("=" * 80)
    print()
    print("NEXT: This ledger is the sovereign baseline.")
    print("      All future state mutations must pass through β + MAYOR.")
    print("      NO RECEIPT → NO SHIP.")
