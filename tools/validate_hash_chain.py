#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hash chain validator for NDJSON ledger files — HELEN_CUM_V1 (Environment-Sovereign)

Validates: seq monotonicity, payload_hash correctness, cum_hash correctness.

Hash scheme is ENVIRONMENT-DRIVEN — reads registries/environment.v1.json.
No auto-detection. No fallback guessing. Environment is sovereign.

Schemes supported:
  HELEN_CUM_V1 (default, active): SHA256(b"HELEN_CUM_V1" || prev_bytes || payload_bytes)
  CUM_SCHEME_V0 (historical): SHA256(prev_bytes || payload_bytes)

Historical V0 ledgers: use --scheme CUM_SCHEME_V0 override.
New V1 ledgers: validated using environment-declared HELEN_CUM_V1.

Reference:
  HELEN_CUM_V1 spec: registries/environment.v1.json → hash_scheme
  V0 rollback anchor: MIGRATION_V0_SNAPSHOT.md
  OCaml alignment: kernel/hash_util.ml — Hash_util.concat
"""
import sys
import os as _os

_repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import json
import hashlib

from kernel.canonical_json import canon_json_bytes

# ──────────────────────────────────────────────────────────────────────────────
# HELEN_CUM_V1 domain separator — HARDCODED BYTE LITERAL (never dynamic)
# OCaml: Bytes.of_string "HELEN_CUM_V1"  (kernel/hash_util.ml)
# 12 ASCII bytes. No trailing whitespace. No encoding variation.
# Must be byte-identical to OCaml helen_cum_v1_prefix.
# ──────────────────────────────────────────────────────────────────────────────
HELEN_CUM_V1_PREFIX: bytes = b"HELEN_CUM_V1"

_ENV_PATH = _os.path.join(_repo_root, "registries", "environment.v1.json")

KNOWN_SCHEMES = ("HELEN_CUM_V1", "CUM_SCHEME_V0")


def sha256_hex(b: bytes) -> str:
    """SHA256 hash of bytes, returned as hex string."""
    return hashlib.sha256(b).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Hash scheme implementations
# ──────────────────────────────────────────────────────────────────────────────

def chain_hash_v0(prev_hex: str, payload_hex: str) -> str:
    """
    CUM_SCHEME_V0 — no domain separation (historical ledgers only).

    cum_hash = SHA256( bytes(prev_hex) || bytes(payload_hex) )
    Input: 32 + 32 = 64 bytes.

    FROZEN: matches validate_hash_chain.py original + MIGRATION_V0_SNAPSHOT.md.
    Use this ONLY for validating historical V0 ledgers.
    """
    return sha256_hex(bytes.fromhex(prev_hex) + bytes.fromhex(payload_hex))


def chain_hash_v1(prev_hex: str, payload_hex: str) -> str:
    """
    HELEN_CUM_V1 — domain-separated (all new ledgers).

    cum_hash = SHA256( b"HELEN_CUM_V1" || bytes(prev_hex) || bytes(payload_hex) )
    Input: 12 + 32 + 32 = 76 bytes.

    PREFIX is HELEN_CUM_V1_PREFIX — hardcoded byte literal, never dynamic,
    never .encode() from variable, no whitespace variation.

    INVARIANT: Must produce byte-identical output to OCaml Hash_util.concat
    in kernel/hash_util.ml.
    """
    prev_b = bytes.fromhex(prev_hex)
    payl_b = bytes.fromhex(payload_hex)
    return sha256_hex(HELEN_CUM_V1_PREFIX + prev_b + payl_b)


def load_hash_scheme_from_env() -> str:
    """
    Load hash_scheme from registries/environment.v1.json.

    Environment is sovereign. Returns scheme string.
    Raises ValueError if field is missing or unrecognized.

    No auto-detection. No fallback guessing.
    """
    try:
        with open(_ENV_PATH, "r", encoding="utf-8") as f:
            env = json.load(f)
    except FileNotFoundError:
        raise ValueError(
            f"Environment file not found: {_ENV_PATH}\n"
            "Cannot validate without explicit hash scheme declaration.\n"
            "Environment is sovereign — it must declare the scheme."
        )

    scheme = env.get("hash_scheme")
    if not scheme:
        raise ValueError(
            f"hash_scheme field missing from {_ENV_PATH}\n"
            "Environment is sovereign — hash_scheme must be declared."
        )

    if scheme not in KNOWN_SCHEMES:
        raise ValueError(
            f"Unknown hash_scheme: {scheme!r} in {_ENV_PATH}\n"
            f"Expected one of: {KNOWN_SCHEMES}"
        )

    return scheme


def get_hash_fn(scheme: str):
    """Return the chain_hash function for the given scheme string."""
    if scheme == "HELEN_CUM_V1":
        return chain_hash_v1
    elif scheme == "CUM_SCHEME_V0":
        return chain_hash_v0
    else:
        raise ValueError(f"Unknown scheme: {scheme!r}. Expected one of {KNOWN_SCHEMES}")


# ──────────────────────────────────────────────────────────────────────────────
# Validation engine
# ──────────────────────────────────────────────────────────────────────────────

def main(ledger_path: str, scheme_override: str = None) -> None:
    """
    Validate hash chain integrity of NDJSON ledger.

    Hash scheme is read from registries/environment.v1.json unless
    scheme_override is provided on the command line.

    Environment is sovereign. No auto-detection. No fallback guessing.

    For historical V0 ledgers, pass: --scheme CUM_SCHEME_V0
    For new V1 ledgers, omit --scheme (environment declares HELEN_CUM_V1).
    """
    # Determine hash scheme — environment is sovereign
    if scheme_override:
        if scheme_override not in KNOWN_SCHEMES:
            print(
                f"[FAIL] Unknown scheme override: {scheme_override!r}. "
                f"Expected one of {KNOWN_SCHEMES}",
                file=sys.stderr,
            )
            sys.exit(2)
        scheme = scheme_override
        print(f"[INFO] Hash scheme (CLI override): {scheme}", file=sys.stderr)
    else:
        try:
            scheme = load_hash_scheme_from_env()
        except ValueError as e:
            print(f"[FAIL] Cannot determine hash scheme:\n{e}", file=sys.stderr)
            sys.exit(1)
        print(f"[INFO] Hash scheme (from environment): {scheme}", file=sys.stderr)

    hash_fn = get_hash_fn(scheme)

    # Load ledger
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[FAIL] File not found: {ledger_path}", file=sys.stderr)
        sys.exit(1)

    if not lines:
        print("[PASS] Empty ledger (no events to validate)", file=sys.stderr)
        return

    expected_seq = 0
    prev_cum_hash = "0" * 64  # Genesis hash

    for line_num, line in enumerate(lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[FAIL] Line {line_num}: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

        # Validate required fields
        required = {"seq", "payload", "prev_cum_hash", "cum_hash", "payload_hash"}
        if not required.issubset(obj.keys()):
            missing = required - set(obj.keys())
            print(
                f"[FAIL] Line {line_num}: Missing required field(s): {sorted(missing)}",
                file=sys.stderr,
            )
            sys.exit(1)

        seq = obj["seq"]
        payload = obj["payload"]
        event_prev_cum = obj["prev_cum_hash"]
        event_cum_hash = obj["cum_hash"]
        event_payload_hash = obj["payload_hash"]

        # seq monotonicity
        if seq != expected_seq:
            print(
                f"[FAIL] Line {line_num}: seq mismatch: got {seq}, expected {expected_seq}",
                file=sys.stderr,
            )
            sys.exit(1)

        # prev_cum_hash chain continuity
        if event_prev_cum != prev_cum_hash:
            print(
                f"[FAIL] Line {line_num}: prev_cum_hash mismatch:\n"
                f"  stored  : {event_prev_cum}\n"
                f"  expected: {prev_cum_hash}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Recompute payload_hash via canonical JSON
        recomputed_payload_hash = sha256_hex(canon_json_bytes(payload))
        if recomputed_payload_hash != event_payload_hash:
            print(
                f"[FAIL] Line {line_num}: payload_hash mismatch:\n"
                f"  stored  : {event_payload_hash}\n"
                f"  recomputed: {recomputed_payload_hash}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Recompute cum_hash using environment-declared scheme
        recomputed_cum_hash = hash_fn(prev_cum_hash, event_payload_hash)
        if recomputed_cum_hash != event_cum_hash:
            print(
                f"[FAIL] Line {line_num}: cum_hash mismatch (scheme={scheme}):\n"
                f"  stored  : {event_cum_hash}\n"
                f"  recomputed: {recomputed_cum_hash}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Advance state
        prev_cum_hash = event_cum_hash
        expected_seq += 1

    print(
        f"[PASS] hash chain verified ({len(lines)} events, scheme={scheme})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate NDJSON ledger hash chain (environment-sovereign)."
    )
    parser.add_argument("ledger", help="Path to NDJSON ledger file")
    parser.add_argument(
        "--scheme",
        choices=list(KNOWN_SCHEMES),
        default=None,
        help=(
            "Override hash scheme (default: read from registries/environment.v1.json). "
            "Use CUM_SCHEME_V0 for historical V0 ledgers."
        ),
    )

    args = parser.parse_args()
    main(args.ledger, scheme_override=args.scheme)
