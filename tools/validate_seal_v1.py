#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_seal_v1.py v1.0.0
SEAL event validator for HELEN OS ledgers.

Validates the SEAL event (at most one per ledger, MAYOR-only):
  1. At most one SEAL event exists in the ledger
  2. SEAL is the last event (highest seq number)
  3. payload.schema == "SEAL_V1"
  4. environment_hash_hex == SHA256(Canon(registries/environment.v1.json))
  5. final_ledger_length == total event count
  6. final_ledger_cum_hash_hex == prev_cum_hash field of the SEAL event
  7. identity_hash_hex == SHA256(bytes(final_ledger_cum_hash) || bytes(env_hash))
  8. mayor_key_id matches environment.v1.json mayor_key.key_id
  9. sealed_at_seq == seq of SEAL event (if present in payload)
  10. mayor_signature: Ed25519 verify if 'cryptography' available; WARN if not

If NO SEAL event is found: passes silently (runs may be ongoing).

Design: core logic raises ValueError; CLI wrapper exits 1.
"""

import sys
import os as _os
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
import json
import hashlib
import os
from kernel.canonical_json import canon_json_bytes

# ──────────────────────────────────────────────────────────────────────────────
# Default environment.v1.json path (relative to repo root)
# ──────────────────────────────────────────────────────────────────────────────
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TOOLS_DIR)
DEFAULT_ENV_PATH = os.path.join(_REPO_ROOT, "registries", "environment.v1.json")


# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load_json_file(path: str, label: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"{label} not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"{label} is invalid JSON: {e}")


def _load_ledger(ledger_path: str) -> list:
    """Load NDJSON ledger. Returns list of (line_num, obj) tuples."""
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            raw_lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise ValueError(f"Ledger file not found: {ledger_path}")

    events = []
    for i, line in enumerate(raw_lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"Line {i}: Invalid JSON: {e}")
        events.append((i, obj))
    return events


# ──────────────────────────────────────────────────────────────────────────────
# Signature verification (Ed25519 — optional, graceful degradation)
# ──────────────────────────────────────────────────────────────────────────────

def _verify_mayor_signature(
    seal_payload: dict,
    identity_hash_hex: str,
    public_key_b64: str,
) -> str:
    """
    Attempt Ed25519 signature verification.
    Returns:
      "VERIFIED"  — signature is valid
      "WARN_SKIP" — public key is placeholder or library missing
    Raises ValueError if signature is present and verification fails.
    """
    mayor_sig = seal_payload.get("mayor_signature", "")
    if not mayor_sig:
        raise ValueError("SEAL payload.mayor_signature is missing or empty")

    if "PLACEHOLDER" in public_key_b64.upper():
        return "WARN_SKIP"

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
        import base64

        # Public key is raw 32-byte Ed25519 key encoded as base64
        pub_bytes = base64.b64decode(public_key_b64)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)

        # Signature is base64url-encoded; pad to multiple of 4
        padding = "=" * (-len(mayor_sig) % 4)
        sig_bytes = base64.urlsafe_b64decode(mayor_sig + padding)

        # Message = raw bytes of identity_hash_hex (the hex string decoded to 32B)
        message = bytes.fromhex(identity_hash_hex)
        pub_key.verify(sig_bytes, message)
        return "VERIFIED"

    except ImportError:
        return "WARN_SKIP"
    except InvalidSignature:
        raise ValueError(
            "SEAL mayor_signature Ed25519 verification FAILED: "
            "signature does not verify under mayor_key.public_key_b64"
        )
    except Exception as exc:
        raise ValueError(
            f"SEAL mayor_signature verification error: {exc}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Core validation (raises ValueError — no sys.exit)
# ──────────────────────────────────────────────────────────────────────────────

def validate_seal_event(ledger_path: str, env_path: str = None) -> str:
    """
    Validate the SEAL event in the ledger.

    Returns a status string: "PASS", "PASS_NO_SEAL", or "PASS_WARN_SIG".
    Raises ValueError on any violation.

    If no SEAL event is present: returns "PASS_NO_SEAL" (run may be ongoing).
    """
    if env_path is None:
        env_path = DEFAULT_ENV_PATH

    events = _load_ledger(ledger_path)
    if not events:
        return "PASS_NO_SEAL"

    # ── Find SEAL events ─────────────────────────────────────────────────────
    seal_events = [
        (lnum, obj)
        for lnum, obj in events
        if obj.get("type", "").upper() == "SEAL"
    ]

    if not seal_events:
        return "PASS_NO_SEAL"

    if len(seal_events) > 1:
        seqs = [obj.get("seq") for _, obj in seal_events]
        raise ValueError(
            f"Multiple SEAL events found (seqs={seqs}). "
            "At most one SEAL is allowed per ledger."
        )

    seal_line_num, seal_obj = seal_events[0]
    seal_seq = seal_obj.get("seq")
    total_events = len(events)

    # ── SEAL must be the last event ──────────────────────────────────────────
    last_line_num, last_obj = events[-1]
    last_seq = last_obj.get("seq")
    if seal_seq != last_seq:
        raise ValueError(
            f"SEAL event (seq={seal_seq}) is not the last event "
            f"(last seq={last_seq}). SEAL must be the terminal event."
        )

    seal_payload = seal_obj.get("payload", {})

    # ── schema discriminator ─────────────────────────────────────────────────
    schema = seal_payload.get("schema")
    if schema != "SEAL_V1":
        raise ValueError(
            f"SEAL payload.schema must be 'SEAL_V1', got '{schema}'"
        )

    # ── environment_hash_hex ─────────────────────────────────────────────────
    env_obj = _load_json_file(env_path, "registries/environment.v1.json")
    computed_env_hash = sha256_hex(canon_json_bytes(env_obj))
    declared_env_hash = seal_payload.get("environment_hash_hex", "")
    if declared_env_hash != computed_env_hash:
        raise ValueError(
            f"SEAL environment_hash_hex mismatch: "
            f"declared='{declared_env_hash}', "
            f"computed SHA256(Canon(environment.v1.json))='{computed_env_hash}'"
        )

    # ── final_ledger_length ──────────────────────────────────────────────────
    declared_length = seal_payload.get("final_ledger_length")
    if not isinstance(declared_length, int):
        raise ValueError("SEAL payload.final_ledger_length is missing or not an integer")
    if declared_length != total_events:
        raise ValueError(
            f"SEAL final_ledger_length mismatch: "
            f"declared={declared_length}, actual event count={total_events}"
        )

    # ── final_ledger_cum_hash_hex == prev_cum_hash of SEAL event ─────────────
    seal_prev_cum = seal_obj.get("prev_cum_hash", "")
    declared_final_cum = seal_payload.get("final_ledger_cum_hash_hex", "")
    if not declared_final_cum:
        raise ValueError("SEAL payload.final_ledger_cum_hash_hex is missing")
    if declared_final_cum != seal_prev_cum:
        raise ValueError(
            f"SEAL final_ledger_cum_hash_hex='{declared_final_cum}' "
            f"!= SEAL event prev_cum_hash='{seal_prev_cum}'"
        )

    # ── identity_hash_hex = SHA256(bytes(final_cum) || bytes(env_hash)) ──────
    declared_identity = seal_payload.get("identity_hash_hex", "")
    if not declared_identity:
        raise ValueError("SEAL payload.identity_hash_hex is missing")
    computed_identity = sha256_hex(
        bytes.fromhex(declared_final_cum) + bytes.fromhex(computed_env_hash)
    )
    if declared_identity != computed_identity:
        raise ValueError(
            f"SEAL identity_hash_hex mismatch: "
            f"declared='{declared_identity}', "
            f"computed=SHA256(final_cum||env_hash)='{computed_identity}'"
        )

    # ── mayor_key_id must match environment ──────────────────────────────────
    declared_key_id = seal_payload.get("mayor_key_id", "")
    env_key_id = env_obj.get("mayor_key", {}).get("key_id", "")
    if not env_key_id:
        raise ValueError(
            "registries/environment.v1.json missing mayor_key.key_id"
        )
    if declared_key_id != env_key_id:
        raise ValueError(
            f"SEAL mayor_key_id='{declared_key_id}' "
            f"!= environment.v1.json mayor_key.key_id='{env_key_id}'"
        )

    # ── sealed_at_seq consistency (optional field) ────────────────────────────
    sealed_at = seal_payload.get("sealed_at_seq")
    if sealed_at is not None:
        if not isinstance(sealed_at, int) or sealed_at != seal_seq:
            raise ValueError(
                f"SEAL sealed_at_seq={sealed_at} != SEAL event seq={seal_seq}"
            )

    # ── mayor_signature ───────────────────────────────────────────────────────
    public_key_b64 = env_obj.get("mayor_key", {}).get("public_key_b64", "")
    sig_result = _verify_mayor_signature(seal_payload, declared_identity, public_key_b64)

    if sig_result == "WARN_SKIP":
        return "PASS_WARN_SIG"
    return "PASS"


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry-point
# ──────────────────────────────────────────────────────────────────────────────

def main(ledger_path: str, env_path: str = None) -> None:
    """CLI wrapper. Validates SEAL, prints result, exits 1 on failure."""
    try:
        result = validate_seal_event(ledger_path, env_path)
    except ValueError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    if result == "PASS_NO_SEAL":
        print("[PASS] seal_v1: no SEAL event present (run ongoing)", file=sys.stderr)
    elif result == "PASS_WARN_SIG":
        print(
            "[PASS] seal_v1 validated (structural checks OK; "
            "Ed25519 signature skipped — placeholder key or 'cryptography' not installed)",
            file=sys.stderr,
        )
    else:
        print("[PASS] seal_v1 validated (all checks including Ed25519 signature)", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python3 validate_seal_v1.py <ledger.ndjson> [registries/environment.v1.json]",
            file=sys.stderr,
        )
        sys.exit(2)
    env_arg = sys.argv[2] if len(sys.argv) > 2 else None
    main(sys.argv[1], env_arg)
