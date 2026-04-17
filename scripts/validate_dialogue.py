#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue Validators (Minimal, Executable)

Validates canonical dialogue events:
1. Hash chain integrity (payload_hash, cum_hash)
2. Schema validation (turn events, HAL contract)

Fails CI if validation fails.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import List, Tuple


def canon(obj) -> str:
    """Canonical JSON: sorted keys, compact."""
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def validate_hash_chain(path: str) -> Tuple[bool, List[str]]:
    """
    Validate cum_hash chain integrity.

    Returns: (passed, errors)
    """
    errors = []
    prev_cum_hash = "0" * 64  # genesis
    seq = 0

    content = Path(path).read_text(encoding="utf-8")
    lines = [l for l in content.split("\n") if l.strip()]

    for line_num, line in enumerate(lines):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"Line {line_num}: JSON parse error: {e}")
            continue

        # Check seq monotonicity
        if event.get("seq") != seq:
            errors.append(
                f"Line {line_num}: seq mismatch. Expected {seq}, got {event.get('seq')}"
            )

        # Check prev_cum_hash
        if event.get("prev_cum_hash") != prev_cum_hash:
            errors.append(f"Line {line_num}: prev_cum_hash mismatch")

        # Recompute payload_hash
        try:
            payload = event.get("payload", {})
            payload_str = canon(payload)
            expected_payload_hash = hashlib.sha256(
                payload_str.encode("utf-8")
            ).hexdigest()

            if event.get("payload_hash") != expected_payload_hash:
                errors.append(
                    f"Line {line_num}: payload_hash mismatch. "
                    f"Expected {expected_payload_hash[:16]}... "
                    f"Got {event.get('payload_hash', '')[:16]}..."
                )
        except Exception as e:
            errors.append(f"Line {line_num}: payload_hash computation failed: {e}")
            expected_payload_hash = event.get("payload_hash")

        # Recompute cum_hash
        try:
            prev_bytes = bytes.fromhex(prev_cum_hash)
            payload_bytes = bytes.fromhex(expected_payload_hash)
            expected_cum_hash = hashlib.sha256(prev_bytes + payload_bytes).hexdigest()

            if event.get("cum_hash") != expected_cum_hash:
                errors.append(
                    f"Line {line_num}: cum_hash mismatch. "
                    f"Expected {expected_cum_hash[:16]}... "
                    f"Got {event.get('cum_hash', '')[:16]}..."
                )
        except Exception as e:
            errors.append(f"Line {line_num}: cum_hash computation failed: {e}")

        seq += 1
        prev_cum_hash = event.get("cum_hash", prev_cum_hash)

    return (len(errors) == 0, errors)


def validate_turn_schema(payload: dict) -> Tuple[bool, List[str]]:
    """
    Validate turn event payload against HAL_VERDICT_V1 contract.

    Returns: (passed, errors)
    """
    errors = []

    # Basic fields
    if payload.get("turn") is None:
        errors.append("payload.turn: missing")
    if not isinstance(payload.get("turn"), int) or payload.get("turn") < 1:
        errors.append(f"payload.turn: invalid (must be int ≥ 1)")

    if payload.get("channel_contract") != "HER_HAL_V1":
        errors.append(
            f"payload.channel_contract: invalid (expected HER_HAL_V1, got {payload.get('channel_contract')})"
        )

    # HAL verdict
    hal = payload.get("hal", {})
    verdict = hal.get("verdict")

    if verdict not in ["PASS", "WARN", "BLOCK"]:
        errors.append(f"hal.verdict: invalid (got {verdict}, expected PASS/WARN/BLOCK)")

    # Check reasons_codes (sorted + regex)
    codes = hal.get("reasons_codes", [])
    if not isinstance(codes, list):
        errors.append(f"hal.reasons_codes: must be list")
    else:
        for code in codes:
            if not isinstance(code, str) or not code:
                errors.append(f"hal.reasons_codes: invalid code {code}")
            elif not __is_valid_code(code):
                errors.append(
                    f"hal.reasons_codes: invalid format {code} (must match ^[A-Z0-9_]{{3,64}}$)"
                )

        sorted_codes = sorted(codes)
        if codes != sorted_codes:
            errors.append(
                f"hal.reasons_codes: not sorted. Got {codes}, Expected {sorted_codes}"
            )

    # Check required_fixes (sorted)
    fixes = hal.get("required_fixes", [])
    if not isinstance(fixes, list):
        errors.append(f"hal.required_fixes: must be list")
    else:
        sorted_fixes = sorted(fixes)
        if fixes != sorted_fixes:
            errors.append(
                f"hal.required_fixes: not sorted. Got {fixes}, Expected {sorted_fixes}"
            )

    # Check mutation rule: mutations present → verdict must be WARN or BLOCK
    mutations = hal.get("mutations", [])
    if mutations and verdict == "PASS":
        errors.append(
            f"hal: mutations present but verdict is PASS (must be WARN or BLOCK)"
        )

    # Check refs (optional but recommended)
    refs = hal.get("refs", {})
    if refs:
        for field in ["run_id", "kernel_hash", "policy_hash", "ledger_cum_hash", "identity_hash"]:
            val = refs.get(field)
            if not val:
                errors.append(f"hal.refs.{field}: missing or empty")
            elif field.endswith("_hash"):
                if not isinstance(val, str) or len(val) != 64:
                    errors.append(
                        f"hal.refs.{field}: invalid (must be 64-char hex, got {len(val) if val else 0} chars)"
                    )

    return (len(errors) == 0, errors)


def __is_valid_code(code: str) -> bool:
    """Check if code matches ^[A-Z0-9_]{3,64}$"""
    return isinstance(code, str) and 3 <= len(code) <= 64 and code.replace("_", "").isalnum() and code.isupper()


def main():
    """Run all validators on dialogue.ndjson"""
    path = Path("./town/dialogue.ndjson")

    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    print(f"\n📋 Dialogue Validators\n")
    print(f"File: {path}")

    # Count events
    content = path.read_text(encoding="utf-8")
    lines = [l for l in content.split("\n") if l.strip()]
    print(f"Events: {len(lines)}\n")

    # Hash chain validation
    print("Validating hash chain...")
    passed, errors = validate_hash_chain(str(path))

    if not passed:
        print(f"❌ Hash chain validation FAILED ({len(errors)} errors):\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"✅ Hash chain valid (cum_hash proven across {len(lines)} events)\n")

    # Schema validation
    print("Validating turn event schemas...")
    schema_errors = []

    for line_num, line in enumerate(lines):
        event = json.loads(line)
        if event.get("type") != "turn":
            continue

        payload = event.get("payload", {})
        passed, errors = validate_turn_schema(payload)

        if not passed:
            schema_errors.append((line_num, errors))

    if schema_errors:
        print(f"❌ Schema validation FAILED ({len(schema_errors)} events):\n")
        for line_num, errors in schema_errors:
            print(f"  Event {line_num}:")
            for e in errors:
                print(f"    - {e}")
        sys.exit(1)

    print(f"✅ All event schemas valid\n")

    # Summary
    print("=" * 80)
    print("Summary:")
    print(f"  Events: {len(lines)}")
    print(f"  Hash chain: ✅ VALID")
    print(f"  Schemas: ✅ VALID")
    print(f"  Final cum_hash: {json.loads(lines[-1]).get('cum_hash', '')[:16]}...")
    print("=" * 80)
    print("\n✅ ALL VALIDATIONS PASSED")


if __name__ == "__main__":
    main()
