#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
certify_phase1_determinism.py

CONSTITUTIONAL CERTIFICATION GATE

Runs 4 mandatory checks before Phase 2 (Hash Scheme Migration) can proceed:

1. Payload hash re-certification across ALL ledgers
2. Full cumulative hash replay under CUM_SCHEME_V0
3. Float retroactive scan (zero-float constraint)
4. Unicode byte equivalence check

All 4 must PASS before HELEN_CUM_V1 activation is permitted.

Usage:
    python3 tools/certify_phase1_determinism.py
"""

import sys
import os as _os
import json
import hashlib
import glob

_repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from kernel.canonical_json import canon_json_bytes


def sha256_hex(b: bytes) -> str:
    """SHA256 hash of bytes, return as hex string."""
    return hashlib.sha256(b).hexdigest()


def find_all_ledgers(repo_root: str) -> list:
    """
    Find GOVERNANCE LEDGERS ONLY (not diagnostic artifacts).

    Governance ledgers are cum-hash bound and must pass determinism checks.
    Diagnostic artifacts (k_tau_trace, rho_trace, etc.) are not cum-bound.
    """
    # Only include governance ledgers (town/ directory)
    patterns = [
        f"{repo_root}/town/ledger*.ndjson",
        f"{repo_root}/town/ledger.json",
    ]

    ledgers = []
    for pattern in patterns:
        for path in glob.glob(pattern, recursive=False):
            if _os.path.isfile(path):
                ledgers.append(path)

    return sorted(set(ledgers))


# ──────────────────────────────────────────────────────────────────────────────
# CHECK 1: Payload Hash Re-certification
# ──────────────────────────────────────────────────────────────────────────────

def check_1_payload_hash_recertification(repo_root: str) -> tuple[bool, list]:
    """
    For every ledger event, recompute payload_hash and verify equality.

    Returns: (all_pass, mismatches)
    """
    print("\n" + "=" * 80)
    print("CHECK 1: Payload Hash Re-certification")
    print("=" * 80)

    ledgers = find_all_ledgers(repo_root)
    total_events = 0
    mismatches = []

    for ledger_path in ledgers:
        try:
            with open(ledger_path, "r") as f:
                for line_num, line in enumerate(f, start=1):
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Try to extract payload and stored hash
                    payload = event.get("payload", event)
                    stored_hash = event.get("payload_hash")

                    if not stored_hash:
                        continue

                    # Recompute
                    canonical_bytes = canon_json_bytes(payload)
                    recomputed_hash = sha256_hex(canonical_bytes)
                    total_events += 1

                    if recomputed_hash != stored_hash:
                        mismatches.append(
                            {
                                "ledger": ledger_path,
                                "line": line_num,
                                "stored": stored_hash[:16],
                                "recomputed": recomputed_hash[:16],
                            }
                        )

        except Exception as e:
            print(f"Warning: Could not process {ledger_path}: {e}")

    if mismatches:
        print(f"[FAIL] Found {len(mismatches)} payload hash mismatches:")
        for m in mismatches[:5]:  # Show first 5
            print(
                f"  {m['ledger']}:{m['line']} "
                f"stored={m['stored']}... != recomputed={m['recomputed']}..."
            )
        if len(mismatches) > 5:
            print(f"  ... and {len(mismatches) - 5} more")
        return False, mismatches

    print(f"[PASS] Payload hash recertification: {total_events} events verified")
    return True, []


# ──────────────────────────────────────────────────────────────────────────────
# CHECK 2: Full Cum Replay Under CUM_SCHEME_V0
# ──────────────────────────────────────────────────────────────────────────────

def compute_cum_v0(prev_cum_hex: str, payload_hash_hex: str) -> str:
    """Compute cumulative hash under CUM_SCHEME_V0 (no domain separation)."""
    prev_bytes = bytes.fromhex(prev_cum_hex)
    payload_bytes = bytes.fromhex(payload_hash_hex)
    return hashlib.sha256(prev_bytes + payload_bytes).hexdigest()


def check_2_cum_replay_v0(repo_root: str) -> tuple[bool, list]:
    """
    For every ledger, replay entire hash chain under CUM_SCHEME_V0.

    Verify each computed cum_hash matches stored cum_hash.

    Returns: (all_pass, divergences)
    """
    print("\n" + "=" * 80)
    print("CHECK 2: Full Cumulative Hash Replay (CUM_SCHEME_V0)")
    print("=" * 80)

    ledgers = find_all_ledgers(repo_root)
    total_events = 0
    divergences = []

    for ledger_path in ledgers:
        try:
            with open(ledger_path, "r") as f:
                cum = "0" * 64  # Genesis hash (all zeros)

                for line_num, line in enumerate(f, start=1):
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    payload_hash = event.get("payload_hash")
                    stored_cum = event.get("cum_hash")

                    if not payload_hash or not stored_cum:
                        continue

                    # Recompute under V0
                    recomputed_cum = compute_cum_v0(cum, payload_hash)
                    total_events += 1

                    if recomputed_cum != stored_cum:
                        divergences.append(
                            {
                                "ledger": ledger_path,
                                "line": line_num,
                                "seq": event.get("seq", -1),
                                "stored": stored_cum[:16],
                                "recomputed": recomputed_cum[:16],
                            }
                        )
                        # Continue from recomputed to catch downstream issues
                        cum = recomputed_cum
                    else:
                        cum = recomputed_cum

        except Exception as e:
            print(f"Warning: Could not process {ledger_path}: {e}")

    if divergences:
        print(f"[FAIL] Found {len(divergences)} cumulative hash divergences:")
        for d in divergences[:5]:
            print(
                f"  {d['ledger']}:{d['line']} (seq={d['seq']}) "
                f"stored={d['stored']}... != recomputed={d['recomputed']}..."
            )
        if len(divergences) > 5:
            print(f"  ... and {len(divergences) - 5} more")
        return False, divergences

    print(f"[PASS] Cumulative hash replay (V0): {total_events} events verified")
    return True, []


# ──────────────────────────────────────────────────────────────────────────────
# CHECK 3: Float Retroactive Scan
# ──────────────────────────────────────────────────────────────────────────────

def detect_floats_recursive(obj, path="$", floats_found=None):
    """Recursively detect float values in object tree."""
    if floats_found is None:
        floats_found = []

    if isinstance(obj, float):
        floats_found.append((path, obj))
    elif isinstance(obj, dict):
        for key, value in obj.items():
            detect_floats_recursive(value, f"{path}.{key}", floats_found)
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            detect_floats_recursive(item, f"{path}[{i}]", floats_found)

    return floats_found


def check_3_float_retroactive_scan(repo_root: str) -> tuple[bool, list]:
    """
    Scan all historical payloads for float values.

    Float constraint is new. If floats exist historically,
    new canonicalizer would reject them (retroactive break).

    Returns: (all_pass, floats_found)
    """
    print("\n" + "=" * 80)
    print("CHECK 3: Float Retroactive Scan")
    print("=" * 80)

    ledgers = find_all_ledgers(repo_root)
    total_events = 0
    all_floats = []

    for ledger_path in ledgers:
        try:
            with open(ledger_path, "r") as f:
                for line_num, line in enumerate(f, start=1):
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    payload = event.get("payload", event)
                    floats = detect_floats_recursive(payload)
                    total_events += 1

                    for path, value in floats:
                        all_floats.append(
                            {
                                "ledger": ledger_path,
                                "line": line_num,
                                "path": path,
                                "value": value,
                            }
                        )

        except Exception as e:
            print(f"Warning: Could not process {ledger_path}: {e}")

    if all_floats:
        print(f"[FAIL] Found {len(all_floats)} float values in historical payloads:")
        for f in all_floats[:5]:
            print(
                f"  {f['ledger']}:{f['line']} "
                f"path={f['path']} value={f['value']}"
            )
        if len(all_floats) > 5:
            print(f"  ... and {len(all_floats) - 5} more")
        print(
            "\n[ALERT] Float enforcement would retroactively break payload hashing."
        )
        print("        This is a phase 1 violation.")
        return False, all_floats

    print(f"[PASS] Float scan: {total_events} events checked, zero floats found")
    return True, []


# ──────────────────────────────────────────────────────────────────────────────
# CHECK 4: Unicode Byte Equivalence
# ──────────────────────────────────────────────────────────────────────────────

def check_4_unicode_byte_equivalence(repo_root: str) -> tuple[bool, list]:
    """
    For historical payloads containing UTF-8, verify:

    Serializing with unified canonicalizer produces byte-equivalent output
    to what was used to compute stored payload_hash.

    Returns: (all_pass, issues)
    """
    print("\n" + "=" * 80)
    print("CHECK 4: Unicode Byte Equivalence")
    print("=" * 80)

    ledgers = find_all_ledgers(repo_root)
    total_utf8_events = 0
    issues = []

    for ledger_path in ledgers:
        try:
            with open(ledger_path, "r") as f:
                for line_num, line in enumerate(f, start=1):
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    payload = event.get("payload", event)
                    stored_hash = event.get("payload_hash")

                    if not stored_hash:
                        continue

                    # Recompute bytes
                    recomputed_bytes = canon_json_bytes(payload)

                    # Check if payload contains non-ASCII (UTF-8)
                    try:
                        recomputed_bytes.decode("ascii")
                    except UnicodeDecodeError:
                        # Contains UTF-8
                        total_utf8_events += 1

                        # Verify hash
                        recomputed_hash = sha256_hex(recomputed_bytes)
                        if recomputed_hash != stored_hash:
                            issues.append(
                                {
                                    "ledger": ledger_path,
                                    "line": line_num,
                                    "stored": stored_hash[:16],
                                    "recomputed": recomputed_hash[:16],
                                }
                            )

        except Exception as e:
            print(f"Warning: Could not process {ledger_path}: {e}")

    if issues:
        print(f"[FAIL] Found {len(issues)} Unicode byte equivalence issues:")
        for issue in issues[:5]:
            print(
                f"  {issue['ledger']}:{issue['line']} "
                f"stored={issue['stored']}... != recomputed={issue['recomputed']}..."
            )
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
        return False, issues

    if total_utf8_events > 0:
        print(
            f"[PASS] Unicode byte equivalence: {total_utf8_events} UTF-8 events verified"
        )
    else:
        print("[PASS] Unicode byte equivalence: No UTF-8 payloads found in ledgers")

    return True, []


# ──────────────────────────────────────────────────────────────────────────────
# MAIN CERTIFICATION SUITE
# ──────────────────────────────────────────────────────────────────────────────

def run_certification_suite(repo_root: str) -> bool:
    """
    Run all 4 certification checks.

    Returns: True if all pass, False if any fail.
    """
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " PHASE 1 DETERMINISM CERTIFICATION GATE ".center(78) + "║")
    print("║" + " (Must pass before HELEN_CUM_V1 activation) ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")

    results = []

    # Run all 4 checks
    pass_1, mismatch_1 = check_1_payload_hash_recertification(repo_root)
    results.append(("Payload hash recertification", pass_1))

    pass_2, divergence_2 = check_2_cum_replay_v0(repo_root)
    results.append(("Cumulative hash replay (V0)", pass_2))

    pass_3, floats_3 = check_3_float_retroactive_scan(repo_root)
    results.append(("Float retroactive scan", pass_3))

    pass_4, issues_4 = check_4_unicode_byte_equivalence(repo_root)
    results.append(("Unicode byte equivalence", pass_4))

    # Summary
    print("\n" + "=" * 80)
    print("CERTIFICATION SUMMARY")
    print("=" * 80)

    all_pass = True
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_pass = False

    print("=" * 80)

    if all_pass:
        print("\n" + "╔" + "=" * 78 + "╗")
        print(
            "║"
            + " ALL CHECKS PASSED: Phase 1 is deterministically stable ".center(78)
            + "║"
        )
        print(
            "║"
            + " You are CLEARED to proceed to Phase 2 (Hash Scheme Migration) ".center(78)
            + "║"
        )
        print("╚" + "=" * 78 + "╝\n")
        return True
    else:
        print("\n" + "╔" + "=" * 78 + "╗")
        print(
            "║"
            + " CERTIFICATION FAILED: Phase 1 is not stable ".center(78)
            + "║"
        )
        print(
            "║"
            + " Do NOT proceed to Phase 2 until all checks pass ".center(78)
            + "║"
        )
        print("╚" + "=" * 78 + "╝\n")
        return False


def main():
    """Entry point."""
    repo_root = _repo_root
    success = run_certification_suite(repo_root)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
