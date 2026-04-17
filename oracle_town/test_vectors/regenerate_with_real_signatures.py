#!/usr/bin/env python3
"""
Regenerate Test Vector Ledgers with Real Ed25519 Signatures

This script signs all attestations in the test vectors using the
actual private keys, making the signatures cryptographically valid.

Usage:
    python oracle_town/test_vectors/regenerate_with_real_signatures.py
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from oracle_town.core.crypto import (
    sign_ed25519,
    canonical_json_bytes,
    build_canonical_message
)

VECTORS_DIR = Path(__file__).parent
KEYS_DIR = VECTORS_DIR.parent / "keys"


def load_private_keys() -> dict:
    """Load private keys for signing"""
    path = KEYS_DIR / "private_keys_TEST_ONLY.json"
    with open(path, 'r') as f:
        return json.load(f)


def load_public_keys() -> dict:
    """Load public key registry"""
    path = KEYS_DIR / "public_keys.json"
    with open(path, 'r') as f:
        data = json.load(f)
    # Build dict by signing_key_id
    return {k["signing_key_id"]: k for k in data["keys"]}


def compute_registry_hash() -> str:
    """Compute registry hash for signatures"""
    path = KEYS_DIR / "public_keys.json"
    with open(path, 'r') as f:
        data = json.load(f)
    canonical = canonical_json_bytes(data)
    import hashlib
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def sign_attestation(att: dict, private_key_b64: str, registry_hash: str) -> str:
    """Sign an attestation using the canonical message format"""
    # Build canonical message including registry hash
    canonical_msg = build_canonical_message(
        run_id=att["run_id"],
        claim_id=att["claim_id"],
        obligation_name=att["obligation_name"],
        attestor_id=att["attestor_id"],
        attestor_class=att["attestor_class"],
        policy_hash=att["policy_hash"],
        evidence_digest=att["evidence_digest"],
        policy_match=att["policy_match"],
        key_registry_hash=registry_hash
    )
    msg_bytes = canonical_json_bytes(canonical_msg)

    # Sign
    sig_b64 = sign_ed25519(private_key_b64, msg_bytes)
    return f"ed25519:{sig_b64}"


def regenerate_ledger(ledger_path: Path, private_keys: dict, registry_hash: str) -> dict:
    """Regenerate a ledger file with real signatures"""
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)

    print(f"\nProcessing: {ledger_path.name}")
    print(f"  Run ID: {ledger['run_id']}")

    for att in ledger.get("attestations", []):
        key_id = att["signing_key_id"]

        if key_id not in private_keys:
            print(f"  ⚠ Key {key_id} not in private keys (expected for revoked keys)")
            # For revoked keys, we still need a signature but it should fail validation
            # We'll sign with the revoked key's private key if available
            continue

        old_sig = att["signature"][:40] + "..."
        att["signature"] = sign_attestation(att, private_keys[key_id], registry_hash)
        new_sig = att["signature"][:40] + "..."

        print(f"  ✓ Signed attestation {att['attestation_id']} with {key_id}")
        print(f"    Old: {old_sig}")
        print(f"    New: {new_sig}")

    return ledger


def main():
    print("=" * 70)
    print("REGENERATING TEST VECTORS WITH REAL SIGNATURES")
    print("=" * 70)

    # Load keys
    private_keys = load_private_keys()
    public_keys = load_public_keys()
    registry_hash = compute_registry_hash()

    print(f"\nLoaded {len(private_keys)} private keys")
    print(f"Loaded {len(public_keys)} public keys")
    print(f"Registry hash: {registry_hash[:50]}...")

    # Find all ledger files
    ledger_files = list(VECTORS_DIR.glob("ledger_*.json"))

    print(f"\nFound {len(ledger_files)} ledger files to process")

    for ledger_path in sorted(ledger_files):
        ledger = regenerate_ledger(ledger_path, private_keys, registry_hash)

        # Write back
        with open(ledger_path, 'w') as f:
            json.dump(ledger, f, indent=2)

        print(f"  → Saved: {ledger_path.name}")

    # Update policy with actual registry hash
    policy_path = VECTORS_DIR / "policy_POL-TEST-1.json"
    with open(policy_path, 'r') as f:
        policy = json.load(f)

    policy["key_registry_hash"] = registry_hash

    with open(policy_path, 'w') as f:
        json.dump(policy, f, indent=2)

    print(f"\n  → Updated policy with registry hash")

    print("\n" + "=" * 70)
    print("REGENERATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run: python -m pytest oracle_town/tests/test_phase2_crypto.py -v")
    print("  2. Run: python -m pytest oracle_town/tests/test_runs_ABC_phase2.py -v")


if __name__ == "__main__":
    main()
