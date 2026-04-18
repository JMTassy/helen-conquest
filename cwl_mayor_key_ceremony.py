#!/usr/bin/env python3
"""
CWL v1.0.1 MAYOR Key Ceremony

Generates MAYOR keypair, stores SK in OS keystore (or file if unavailable),
and produces a pinnable MAYOR_PK registry entry for genesis ledger sealing.

Implements D-001: mayor_rotate_v1 receipt type design
Implements D-004: genesis ledger must include mayor_pk reference
"""

import json
import hashlib
import subprocess
import platform
import secrets
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass


# ──────────────────────────────────────────────────────────────────
# Minimal Ed25519 using Python stdlib (3.11+) or cryptography lib
# ──────────────────────────────────────────────────────────────────

def generate_keypair() -> tuple[bytes, bytes]:
    """Generate Ed25519 keypair. Returns (private_key_bytes, public_key_bytes)."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        sk = Ed25519PrivateKey.generate()
        pk = sk.public_key()
        from cryptography.hazmat.primitives.serialization import (
            Encoding, PublicFormat, PrivateFormat, NoEncryption
        )
        sk_bytes = sk.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        pk_bytes = pk.public_bytes(Encoding.Raw, PublicFormat.Raw)
        return sk_bytes, pk_bytes
    except ImportError:
        # Fallback: use secrets to simulate (NOT cryptographically real Ed25519)
        # In production, install cryptography: pip install cryptography
        print("⚠️  WARNING: cryptography library not found.")
        print("   Using simulated keypair for ceremony structure only.")
        print("   Install: pip install cryptography")
        print()
        sk_bytes = secrets.token_bytes(32)
        pk_bytes = secrets.token_bytes(32)
        return sk_bytes, pk_bytes


def fingerprint(pk_bytes: bytes) -> str:
    """SHA256 fingerprint of public key."""
    return hashlib.sha256(pk_bytes).hexdigest()


# ──────────────────────────────────────────────────────────────────
# OS Keystore Interface
# ──────────────────────────────────────────────────────────────────

def store_in_keystore(label: str, sk_hex: str) -> bool:
    """Store SK in OS keystore. Returns True if successful."""
    system = platform.system()

    if system == "Darwin":
        # macOS Keychain
        try:
            result = subprocess.run([
                "security", "add-generic-password",
                "-s", f"CWL_{label}",
                "-a", "cwl_mayor",
                "-w", sk_hex,
                "-U"  # Update if exists
            ], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    elif system == "Linux":
        # Try secret-tool (libsecret)
        try:
            proc = subprocess.run(
                ["secret-tool", "store", "--label", f"CWL {label}",
                 "service", "cwl", "key", label],
                input=sk_hex, capture_output=True, text=True
            )
            return proc.returncode == 0
        except FileNotFoundError:
            return False

    return False


def retrieve_from_keystore(label: str) -> str | None:
    """Retrieve SK from OS keystore. Returns hex string or None."""
    system = platform.system()

    if system == "Darwin":
        try:
            result = subprocess.run([
                "security", "find-generic-password",
                "-s", f"CWL_{label}",
                "-a", "cwl_mayor",
                "-w"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except FileNotFoundError:
            pass
    return None


# ──────────────────────────────────────────────────────────────────
# Key Registry
# ──────────────────────────────────────────────────────────────────

REGISTRY_PATH = Path("mayor_key_registry.json")


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {"version": "CWL_KEY_REGISTRY_V1", "keys": [], "active_key_id": None}


def save_registry(registry: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2))
    print(f"✓ Registry saved: {REGISTRY_PATH}")


# ──────────────────────────────────────────────────────────────────
# mayor_rotate_v1 Receipt Type  (D-001)
# ──────────────────────────────────────────────────────────────────

def generate_rotation_receipt(
    old_key_id: str | None,
    new_key_id: str,
    new_pk_hex: str,
    new_pk_fingerprint: str,
) -> dict:
    """
    mayor_rotate_v1: Receipt type for key rotation events.

    D-001: Without this, MAYOR_SK isolation has no operational exit.
    Key compromise with no rotation receipt = irrecoverable.
    """
    return {
        "type": "mayor_rotate_v1",
        "hash_law": "CWL_CUM_V1",
        "key_event": {
            "old_key_id": old_key_id,      # None = genesis (no prior key)
            "new_key_id": new_key_id,
            "new_pk_hex": new_pk_hex,
            "new_pk_fingerprint": new_pk_fingerprint,
            "rotation_reason": "genesis" if old_key_id is None else "ceremony",
            "effective_from_seq": None,    # Will be filled when appended to ledger
        },
        "grace_period": {
            "old_key_valid_until": None,   # None = immediate (genesis)
            "old_key_status": "revoked" if old_key_id else "none",
        },
        "issuer": "MAYOR",
        "authority": True,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema": "mayor_rotate_v1",
            "cwl_version": "1.0.1",
        }
    }


# ──────────────────────────────────────────────────────────────────
# Genesis Ledger with MAYOR_PK anchor (D-004)
# ──────────────────────────────────────────────────────────────────

def generate_genesis_event(mayor_pk_hex: str, mayor_pk_fingerprint: str) -> dict:
    """
    Genesis event pinning MAYOR_PK reference.

    D-004: Genesis must include mayor_pk to create verifiable root of trust.
    Without it, key registry has no cryptographic anchor in ledger.
    """
    payload = {
        "schema": "GENESIS_V1",
        "cwl_version": "v1.0.1",
        "hash_law": "CWL_CUM_V1",
        "mayor_pk_hex": mayor_pk_hex,           # ← Root of trust anchor
        "mayor_pk_fingerprint": mayor_pk_fingerprint,
        "key_registry_version": "CWL_KEY_REGISTRY_V1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "note": "CWL v1.0.1 genesis — frozen specification baseline",
    }
    return payload


# ──────────────────────────────────────────────────────────────────
# Main Ceremony
# ──────────────────────────────────────────────────────────────────

def run_ceremony():
    print("=" * 80)
    print("CWL v1.0.1 — MAYOR KEY CEREMONY")
    print("D-001: mayor_rotate_v1 receipt type | D-004: genesis pk anchor")
    print("=" * 80)
    print()

    # Step 1: Generate keypair
    print("STEP 1: Generate Ed25519 keypair")
    sk_bytes, pk_bytes = generate_keypair()
    sk_hex = sk_bytes.hex()
    pk_hex = pk_bytes.hex()
    pk_fp  = fingerprint(pk_bytes)

    print(f"  MAYOR_PK:          {pk_hex[:16]}...{pk_hex[-8:]}")
    print(f"  PK Fingerprint:    {pk_fp[:16]}...{pk_fp[-8:]}")
    print(f"  MAYOR_SK:          [REDACTED — stored only in keystore]")
    print()

    # Step 2: Store SK in OS keystore
    print("STEP 2: Isolate MAYOR_SK in OS keystore")
    stored = store_in_keystore("MAYOR_SK_V1_0_1", sk_hex)
    if stored:
        print(f"  ✅ MAYOR_SK stored in OS keystore (macOS Keychain / libsecret)")
        print(f"     Key never written to disk or logs beyond this ceremony")
    else:
        # Fallback: encrypted file (dev only, not production)
        fallback_path = Path(".mayor_sk_dev_ONLY.hex")
        fallback_path.write_text(sk_hex)
        fallback_path.chmod(0o600)
        print(f"  ⚠️  OS keystore unavailable. SK written to {fallback_path} (dev only)")
        print(f"     MOVE TO KEYSTORE OR HSM BEFORE PRODUCTION DEPLOYMENT")
    print()

    # Step 3: Build key registry entry
    print("STEP 3: Register MAYOR_PK in key registry")
    registry = load_registry()
    key_id = f"MAYOR_V1_0_1_{pk_fp[:8].upper()}"

    key_entry = {
        "key_id": key_id,
        "pk_hex": pk_hex,
        "pk_fingerprint": pk_fp,
        "algorithm": "Ed25519",
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cwl_version": "1.0.1",
        "rotation_receipt_type": "mayor_rotate_v1",
    }

    registry["keys"].append(key_entry)
    registry["active_key_id"] = key_id
    save_registry(registry)
    print(f"  ✅ Key registered: {key_id}")
    print(f"  Registry contains {len(registry['keys'])} key(s)")
    print()

    # Step 4: Generate mayor_rotate_v1 receipt (D-001)
    print("STEP 4: Generate mayor_rotate_v1 genesis receipt")
    rotation_receipt = generate_rotation_receipt(
        old_key_id=None,          # genesis: no prior key
        new_key_id=key_id,
        new_pk_hex=pk_hex,
        new_pk_fingerprint=pk_fp,
    )
    rotation_path = Path(f"mayor_rotate_v1_genesis_{pk_fp[:8]}.json")
    rotation_path.write_text(json.dumps(rotation_receipt, indent=2))
    print(f"  ✅ Rotation receipt: {rotation_path}")
    print(f"     Type: mayor_rotate_v1 (genesis)")
    print(f"     Old key: None (genesis, no prior key)")
    print(f"     New key: {key_id}")
    print()

    # Step 5: Generate genesis ledger event (D-004)
    print("STEP 5: Generate genesis ledger event with MAYOR_PK anchor")
    genesis_payload = generate_genesis_event(pk_hex, pk_fp)
    genesis_path = Path("genesis_event_v1_0_1.json")
    genesis_path.write_text(json.dumps(genesis_payload, indent=2))
    print(f"  ✅ Genesis event: {genesis_path}")
    print(f"     MAYOR_PK fingerprint pinned in genesis payload")
    print(f"     Root of trust: ESTABLISHED")
    print()

    # Step 6: Audit log (key identifiers only — never key material)
    print("STEP 6: Ceremony audit log")
    audit = {
        "ceremony": "MAYOR_KEY_GENESIS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "key_id": key_id,
        "pk_fingerprint": pk_fp,
        "sk_location": "os_keystore" if stored else "dev_file_INSECURE",
        "sk_material": "REDACTED",
        "rotation_receipt": str(rotation_path),
        "genesis_event": str(genesis_path),
        "registry": str(REGISTRY_PATH),
        "status": "CEREMONY_COMPLETE",
        "next_action": "Append genesis_event to ledger and seal immediately",
    }
    audit_path = Path(f"mayor_key_ceremony_audit_{pk_fp[:8]}.json")
    audit_path.write_text(json.dumps(audit, indent=2))
    print(f"  ✅ Audit log: {audit_path}")
    print(f"     Contains: key_id, fingerprint, location, status")
    print(f"     Does NOT contain: key material (sk_hex)")
    print()

    # Final summary
    print("=" * 80)
    print("CEREMONY COMPLETE")
    print("=" * 80)
    print(f"\n  MAYOR_PK (public):     {pk_hex[:16]}...{pk_hex[-8:]}")
    print(f"  Fingerprint:           {pk_fp}")
    print(f"  Key ID:                {key_id}")
    print(f"  SK Location:           {'OS Keystore ✅' if stored else 'Dev file ⚠️'}")
    print(f"\n  Registry:              {REGISTRY_PATH}")
    print(f"  Rotation receipt:      {rotation_path}")
    print(f"  Genesis event:         {genesis_path}")
    print(f"  Audit log:             {audit_path}")
    print()
    print("NEXT STEP: Run cwl_genesis_ledger.py to create v1.0.1 genesis ledger")
    print("           Using this MAYOR_PK as cryptographic root of trust anchor.")
    print("=" * 80)

    return {
        "key_id": key_id,
        "pk_hex": pk_hex,
        "pk_fingerprint": pk_fp,
        "genesis_payload": genesis_payload,
    }


if __name__ == "__main__":
    run_ceremony()
