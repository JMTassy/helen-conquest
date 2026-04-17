#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Meta Invariance Test

Checks:
1. No floats in payload (determinism regression)
2. reasons_codes are codes (not prose) + sorted
3. required_fixes are sorted

Catches 90% of regressions that would break determinism slowly.
"""

import json
import re
import sys

RE_CODE = re.compile(r"^[A-Z0-9_]{3,64}$")


def check_no_floats(payload: dict, path: str = "$") -> list:
    """Recursively check that payload contains no floats."""
    errors = []

    def walk(x, p):
        if isinstance(x, float):
            errors.append(f"FLOAT in payload at {p} (value={x})")
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{p}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{p}[{i}]")

    walk(payload, path)
    return errors


def check_reasons_codes(hal: dict) -> list:
    """Check reasons_codes: codes (not prose) + sorted."""
    errors = []
    codes = hal.get("reasons_codes", [])

    if not isinstance(codes, list):
        return errors

    # Check each code matches regex
    for code in codes:
        if not isinstance(code, str):
            errors.append(f"reasons_codes item not string: {code}")
        elif not RE_CODE.match(code):
            errors.append(f"reasons_codes regex fail: {code}")

    # Check sorted
    if codes != sorted(codes):
        errors.append(
            f"reasons_codes not sorted: {codes} vs {sorted(codes)}"
        )

    return errors


def check_required_fixes(hal: dict) -> list:
    """Check required_fixes: sorted."""
    errors = []
    fixes = hal.get("required_fixes", [])

    if not isinstance(fixes, list):
        return errors

    if fixes != sorted(fixes):
        errors.append(
            f"required_fixes not sorted: {fixes} vs {sorted(fixes)}"
        )

    return errors


def main(path: str):
    """Run all meta invariance checks."""
    errors = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            obj = json.loads(line)

            if obj["type"] != "turn":
                continue

            payload = obj.get("payload", {})

            # Check 1: No floats
            float_errors = check_no_floats(payload)
            if float_errors:
                errors.extend(
                    [f"Line {line_no}: {e}" for e in float_errors]
                )

            # Check 2 & 3: Reasons codes + sorting
            hal = payload.get("hal", {})
            codes_errors = check_reasons_codes(hal)
            if codes_errors:
                errors.extend(
                    [f"Line {line_no}: {e}" for e in codes_errors]
                )

            fixes_errors = check_required_fixes(hal)
            if fixes_errors:
                errors.extend(
                    [f"Line {line_no}: {e}" for e in fixes_errors]
                )

    if errors:
        print("[FAIL] Meta invariance violations:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    print("[PASS] Meta invariance verified (no floats, reasons sorted)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python3 tools/test_meta_invariance.py <ledger.ndjson>"
        )
    main(sys.argv[1])
