"""
test_reason_codes_allowlist.py

PURPOSE
-------
Enforce that all blocking reason codes emitted by the Mayor are in the canonical
allowlist defined in reason_codes.json.

This closes the "reason code registry" loop: the schema enforces format (^[A-Z0-9_]{3,64}$),
but this test enforces that codes belong to the authoritative registry.

VIOLATIONS CAUGHT
-----------------
1. Emitting unknown/undocumented reason codes
2. Typos in reason codes (e.g., "RECEIT_GAP_NONZERO" instead of "RECEIPT_GAP_NONZERO")
3. Deprecated codes still in use
4. Ad-hoc codes added without updating registry

ENFORCEMENT SURFACE
-------------------
- All decision_record_*.json fixtures must only use allowlisted codes
- CI step ensures reason_codes.json is in sync with REASON_CODES.md
- Future: production Mayor output validation against allowlist

INTEGRATION WITH CI
-------------------
CI must include a step that:
1. Parses REASON_CODES.md section 3 (Canonical Reason Codes)
2. Extracts all code names (e.g., "#### RECEIPT_GAP_NONZERO")
3. Compares extracted list to reason_codes.json
4. Fails if diff detected (codes added/removed without updating JSON)

Example CI check:
    python scripts/sync_reason_codes.py --check

This ensures REASON_CODES.md remains the single source of truth while
reason_codes.json provides the machine-readable allowlist.
"""

import json
from pathlib import Path
from typing import Set

import pytest


# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
REASON_CODES_JSON = REPO_ROOT / "reason_codes.json"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# -----------------------------------------------------------------------------
# Allowlist Loading
# -----------------------------------------------------------------------------

def load_reason_codes_allowlist() -> Set[str]:
    """
    Load canonical reason code allowlist from reason_codes.json.

    Returns:
        Set of valid reason code strings

    Raises:
        FileNotFoundError: If reason_codes.json missing
        ValueError: If JSON structure invalid
    """
    if not REASON_CODES_JSON.exists():
        raise FileNotFoundError(
            f"Reason codes allowlist not found: {REASON_CODES_JSON}\n"
            f"Expected location: {REPO_ROOT}/reason_codes.json\n"
            f"This file must be generated from REASON_CODES.md"
        )

    with open(REASON_CODES_JSON) as f:
        data = json.load(f)

    if "codes" not in data:
        raise ValueError(
            f"Invalid reason_codes.json structure: missing 'codes' array.\n"
            f"Expected: {{\"codes\": [\"CODE1\", \"CODE2\", ...]}}"
        )

    codes = data["codes"]
    if not isinstance(codes, list):
        raise ValueError(
            f"Invalid reason_codes.json: 'codes' must be array, got {type(codes)}"
        )

    return set(codes)


# -----------------------------------------------------------------------------
# Fixture Discovery
# -----------------------------------------------------------------------------

def iter_decision_record_fixtures():
    """
    Yield all decision_record_*.json fixtures for testing.

    Yields:
        Path objects for each fixture
    """
    for path in FIXTURES_DIR.glob("decision_record_*.json"):
        yield path


# -----------------------------------------------------------------------------
# Core Test
# -----------------------------------------------------------------------------

def test_blocking_codes_in_allowlist():
    """
    CRITICAL ENFORCEMENT: All blocking codes must be in reason_codes.json allowlist.

    For each decision_record fixture:
    1. Load the decision record
    2. Extract all blocking[].code values
    3. Assert each code is in the canonical allowlist

    Failure modes:
    - Code not in allowlist → Typo or undocumented code
    - Empty allowlist → reason_codes.json corrupted
    - Fixture uses deprecated code → Update fixture
    """
    allowlist = load_reason_codes_allowlist()

    if not allowlist:
        raise AssertionError(
            "Reason codes allowlist is empty.\n"
            f"Check {REASON_CODES_JSON} for valid structure."
        )

    print(f"\n✓ Loaded {len(allowlist)} canonical reason codes from allowlist")

    fixtures_checked = 0
    codes_validated = 0

    for fixture_path in iter_decision_record_fixtures():
        fixtures_checked += 1
        print(f"\nChecking fixture: {fixture_path.name}")

        with open(fixture_path) as f:
            decision_record = json.load(f)

        blocking = decision_record.get("blocking", [])
        print(f"  Found {len(blocking)} blocking reason(s)")

        for i, entry in enumerate(blocking):
            code = entry.get("code")

            if not code:
                raise AssertionError(
                    f"{fixture_path.name}: blocking[{i}] missing 'code' field.\n"
                    f"Entry: {json.dumps(entry, indent=2)}"
                )

            if code not in allowlist:
                raise AssertionError(
                    f"REASON_CODE_NOT_IN_ALLOWLIST:\n"
                    f"Fixture: {fixture_path.name}\n"
                    f"Blocking entry: {i}\n"
                    f"Code: '{code}'\n"
                    f"Allowlist location: {REASON_CODES_JSON}\n"
                    f"Allowlist size: {len(allowlist)}\n"
                    f"\n"
                    f"This code is either:\n"
                    f"  1. A typo (check REASON_CODES.md for correct spelling)\n"
                    f"  2. Undocumented (add to REASON_CODES.md section 3, then regenerate reason_codes.json)\n"
                    f"  3. Deprecated (remove from fixture or use replacement code)\n"
                    f"\n"
                    f"To add a new code:\n"
                    f"  1. Add entry to REASON_CODES.md section 3\n"
                    f"  2. Run: python scripts/sync_reason_codes.py\n"
                    f"  3. Commit both files\n"
                )

            codes_validated += 1
            detail = entry.get("detail", "(no detail)")
            print(f"  ✓ {code}: {detail}")

    print(f"\n{'='*60}")
    print(f"✓ Allowlist enforcement passed")
    print(f"  Fixtures checked: {fixtures_checked}")
    print(f"  Codes validated: {codes_validated}")
    print(f"  Allowlist size: {len(allowlist)}")
    print(f"{'='*60}")


# -----------------------------------------------------------------------------
# Allowlist Integrity Tests
# -----------------------------------------------------------------------------

def test_allowlist_has_no_duplicates():
    """
    Verify reason_codes.json contains no duplicate codes.

    Duplicates indicate:
    - Manual editing error
    - Sync script bug
    - Merge conflict resolution mistake
    """
    with open(REASON_CODES_JSON) as f:
        data = json.load(f)

    codes = data.get("codes", [])
    unique_codes = set(codes)

    if len(codes) != len(unique_codes):
        duplicates = [code for code in codes if codes.count(code) > 1]
        raise AssertionError(
            f"Reason codes allowlist contains duplicates: {set(duplicates)}\n"
            f"Total codes: {len(codes)}, Unique codes: {len(unique_codes)}\n"
            f"File: {REASON_CODES_JSON}"
        )

    print(f"✓ Allowlist has {len(codes)} unique codes (no duplicates)")


def test_allowlist_format_valid():
    """
    Verify all codes in allowlist match the required format: ^[A-Z0-9_]{3,64}$

    This catches:
    - Lowercase codes
    - Codes with special characters
    - Codes too short/long
    - Whitespace issues
    """
    import re

    allowlist = load_reason_codes_allowlist()
    pattern = re.compile(r"^[A-Z0-9_]{3,64}$")

    invalid_codes = [code for code in allowlist if not pattern.match(code)]

    if invalid_codes:
        raise AssertionError(
            f"Allowlist contains codes with invalid format: {invalid_codes}\n"
            f"Required pattern: ^[A-Z0-9_]{{3,64}}$\n"
            f"File: {REASON_CODES_JSON}"
        )

    print(f"✓ All {len(allowlist)} codes match required format")


def test_allowlist_sorted():
    """
    Verify reason_codes.json is sorted alphabetically.

    Sorted allowlist makes diffs cleaner and merge conflicts easier to resolve.
    """
    with open(REASON_CODES_JSON) as f:
        data = json.load(f)

    codes = data.get("codes", [])
    sorted_codes = sorted(codes)

    if codes != sorted_codes:
        raise AssertionError(
            f"Reason codes allowlist is not sorted alphabetically.\n"
            f"File: {REASON_CODES_JSON}\n"
            f"Run: python scripts/sync_reason_codes.py --sort"
        )

    print(f"✓ Allowlist is sorted alphabetically")


# -----------------------------------------------------------------------------
# Run Tests
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
