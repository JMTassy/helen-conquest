#!/usr/bin/env python3
"""
Schema validator for HAL_VERDICT_V1 contract in turn events.
Enforces: verdict ∈ {PASS, WARN, BLOCK}, sorted reason codes, sorted required_fixes,
refs completeness, and mutation rule.
"""
import sys
import json
import re

def is_sorted(xs):
    """Check if array is sorted (lexicographically for strings)."""
    if not xs:
        return True
    return xs == sorted(xs)

def validate_reason_codes(codes):
    """
    Validate reason codes: must be sorted, match regex ^[A-Z0-9_]{3,64}$.
    """
    if not isinstance(codes, list):
        return False, "reasons_codes is not a list"
    
    if not is_sorted(codes):
        return False, f"reasons_codes not sorted: {codes}"
    
    pattern = re.compile(r"^[A-Z0-9_]{3,64}$")
    for code in codes:
        if not isinstance(code, str):
            return False, f"reason code {code} is not a string"
        if not pattern.match(code):
            return False, f"reason code {code} does not match ^[A-Z0-9_]{{3,64}}$"
    
    return True, None

def validate_required_fixes(fixes):
    """
    Validate required_fixes: must be sorted, all strings.
    """
    if not isinstance(fixes, list):
        return False, "required_fixes is not a list"
    
    if not is_sorted(fixes):
        return False, f"required_fixes not sorted: {fixes}"
    
    for fix in fixes:
        if not isinstance(fix, str):
            return False, f"required_fix {fix} is not a string"
    
    return True, None

def main(ledger_path):
    """Validate turn event schema in NDJSON ledger."""
    try:
        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[FAIL] File not found: {ledger_path}", file=sys.stderr)
        sys.exit(1)

    if not lines:
        print("[PASS] turn schema verified (no events)", file=sys.stderr)
        return

    turn_count = 0

    for line_num, line in enumerate(lines, start=1):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"[FAIL] Line {line_num}: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

        # Skip non-turn events
        if obj.get("type") != "turn":
            continue

        turn_count += 1
        payload = obj.get("payload", {})

        # Extract HAL verdict
        hal = payload.get("hal", {})
        if not isinstance(hal, dict):
            print(f"[FAIL] Line {line_num}: hal is not a dict", file=sys.stderr)
            sys.exit(1)

        # Validate verdict field
        verdict = hal.get("verdict")
        if verdict not in {"PASS", "WARN", "BLOCK"}:
            print(f"[FAIL] Line {line_num}: verdict {verdict} not in {{PASS, WARN, BLOCK}}", file=sys.stderr)
            sys.exit(1)

        # Validate reason codes
        codes = hal.get("reasons_codes", [])
        ok, err = validate_reason_codes(codes)
        if not ok:
            print(f"[FAIL] Line {line_num}: {err}", file=sys.stderr)
            sys.exit(1)

        # Validate required fixes
        fixes = hal.get("required_fixes", [])
        ok, err = validate_required_fixes(fixes)
        if not ok:
            print(f"[FAIL] Line {line_num}: {err}", file=sys.stderr)
            sys.exit(1)

        # Validate mutations
        mutations = hal.get("mutations", [])
        if not isinstance(mutations, list):
            print(f"[FAIL] Line {line_num}: mutations is not a list", file=sys.stderr)
            sys.exit(1)

        # Mutation rule: if mutations present, verdict must not be PASS
        if len(mutations) > 0 and verdict == "PASS":
            print(f"[FAIL] Line {line_num}: verdict is PASS but mutations present", file=sys.stderr)
            sys.exit(1)

        # Validate refs (must have certain fields)
        refs = hal.get("refs", {})
        if not isinstance(refs, dict):
            print(f"[FAIL] Line {line_num}: refs is not a dict", file=sys.stderr)
            sys.exit(1)

        required_refs = ["run_id", "kernel_hash", "policy_hash", "ledger_cum_hash", "identity_hash"]
        for ref_key in required_refs:
            if ref_key not in refs:
                print(f"[FAIL] Line {line_num}: refs missing {ref_key}", file=sys.stderr)
                sys.exit(1)

    print(f"[PASS] turn schema verified ({turn_count} turn events)", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_turn_schema.py <ledger.ndjson>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1])
