"""
test_mayor_no_ship_invariant.py

PURPOSE
-------
Enforce the critical Mayor invariant: NO_SHIP decision MUST include at least one
typed reason code in the blocking array.

Schema-level enforcement is PRIMARY (via JSON Schema allOf conditions).
This test provides runtime validation and detailed error messages.

INVARIANTS TESTED (Schema-Enforced)
------------------------------------
1. NO_SHIP ⇒ blocking.length >= 1 (schema: minItems)
2. SHIP ⇒ blocking.length == 0 (schema: maxItems)
3. SHIP ⇒ receipt_gap == 0 (schema: const)
4. SHIP ⇒ kill_switches_pass == true (schema: const)

WHAT THIS TEST ADDS BEYOND SCHEMA
----------------------------------
- Human-readable error messages for each violation type
- Verification that schema validation catches all violations
- Reason code format validation (delegated to test_reason_codes_allowlist.py for allowlist)
- Evidence path validation

INTEGRATION
-----------
- decision_record.json is receipt-hashed payload (deterministic)
- decision_record.meta.json holds timestamps (non-hashed)
- Schema is decision_record.schema.json (2020-12, additionalProperties:false)

FALSIFICATION
-------------
To verify enforcement, temporarily break fixtures:
- decision="NO_SHIP", blocking=[] → Schema MUST reject (minItems violation)
- decision="SHIP", blocking=[{code:"FOO"}] → Schema MUST reject (maxItems violation)
- decision="SHIP", receipt_gap=1 → Schema MUST reject (const violation)
- decision="SHIP", kill_switches_pass=false → Schema MUST reject (const violation)
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

try:
    import jsonschema
except ImportError:
    raise ImportError(
        "jsonschema package required. Install: pip install jsonschema"
    )


# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


# -----------------------------------------------------------------------------
# Loading Utilities
# -----------------------------------------------------------------------------

def load_json_fixture(filename: str) -> Dict[str, Any]:
    """Load JSON fixture with detailed error message."""
    path = FIXTURES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Fixture not found: {path}\n"
            f"Create: tests/fixtures/{filename}"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load JSON schema."""
    path = SCHEMAS_DIR / schema_name
    if not path.exists():
        raise FileNotFoundError(
            f"Schema not found: {path}\n"
            f"Expected: schemas/{schema_name}"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# Schema Validation
# -----------------------------------------------------------------------------

def validate_decision_record(decision_record: Dict[str, Any]) -> None:
    """
    Validate decision_record against decision_record.schema.json.

    Schema enforces:
    - Draft 2020-12
    - additionalProperties: false
    - NO_SHIP ⇒ blocking.minItems >= 1
    - SHIP ⇒ blocking.maxItems == 0, receipt_gap == 0, kill_switches_pass == true

    Raises:
        jsonschema.ValidationError: If validation fails
    """
    schema = load_schema("decision_record.schema.json")
    jsonschema.validate(instance=decision_record, schema=schema)


# -----------------------------------------------------------------------------
# Core Tests: Schema Enforcement Verification
# -----------------------------------------------------------------------------

def test_no_ship_fixture_validates():
    """
    NO_SHIP fixture must pass schema validation.

    Schema enforces: decision=="NO_SHIP" ⇒ blocking.minItems >= 1
    """
    decision_record = load_json_fixture("decision_record_no_ship.json")

    # Schema validation (will raise if invalid)
    validate_decision_record(decision_record)

    # Verify fixture structure
    decision = decision_record["decision"]
    blocking = decision_record["blocking"]

    assert decision == "NO_SHIP", f"Expected NO_SHIP, got {decision}"
    assert len(blocking) >= 1, \
        f"NO_SHIP fixture must have non-empty blocking array (schema should enforce this)"

    print(f"✓ NO_SHIP fixture valid with {len(blocking)} blocking reason(s)")
    for entry in blocking:
        code = entry["code"]
        detail = entry.get("detail", "(no detail)")
        print(f"  - {code}: {detail}")


def test_ship_fixture_validates():
    """
    SHIP fixture must pass schema validation.

    Schema enforces:
    - decision=="SHIP" ⇒ blocking.maxItems == 0
    - decision=="SHIP" ⇒ receipt_gap == 0
    - decision=="SHIP" ⇒ kill_switches_pass == true
    """
    decision_record = load_json_fixture("decision_record_ship.json")

    # Schema validation (will raise if invalid)
    validate_decision_record(decision_record)

    # Verify fixture structure
    decision = decision_record["decision"]
    blocking = decision_record["blocking"]
    receipt_gap = decision_record["receipt_gap"]
    kill_switches_pass = decision_record["kill_switches_pass"]

    assert decision == "SHIP", f"Expected SHIP, got {decision}"
    assert len(blocking) == 0, \
        f"SHIP fixture must have empty blocking array (schema should enforce this)"
    assert receipt_gap == 0, \
        f"SHIP fixture must have receipt_gap==0 (schema should enforce this)"
    assert kill_switches_pass is True, \
        f"SHIP fixture must have kill_switches_pass==true (schema should enforce this)"

    print("✓ SHIP fixture valid")
    print(f"  - receipt_gap: {receipt_gap}")
    print(f"  - kill_switches_pass: {kill_switches_pass}")
    print(f"  - blocking: [] (empty)")


# -----------------------------------------------------------------------------
# Falsification Tests: Schema MUST Reject Invalid Documents
# -----------------------------------------------------------------------------

def test_schema_rejects_no_ship_without_blocking():
    """
    FALSIFICATION: Schema MUST reject NO_SHIP with empty blocking array.

    This verifies the schema-level invariant enforcement is working.
    """
    invalid_doc = {
        "decision": "NO_SHIP",
        "kill_switches_pass": True,
        "receipt_gap": 3,
        "blocking": [],  # VIOLATION: empty blocking for NO_SHIP
        "metadata": {
            "mayor_version": "v0.1",
            "tribunal_bundle_hash": "a" * 64,
            "policies_hash": "b" * 64,
            "receipt_root_hash": "c" * 64
        }
    }

    schema = load_schema("decision_record.schema.json")

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=invalid_doc, schema=schema)

    error_msg = str(exc_info.value)
    print(f"✓ Schema correctly rejected NO_SHIP with empty blocking")
    print(f"  Error: {error_msg}")


def test_schema_rejects_ship_with_blocking():
    """
    FALSIFICATION: Schema MUST reject SHIP with non-empty blocking array.
    """
    invalid_doc = {
        "decision": "SHIP",
        "kill_switches_pass": True,
        "receipt_gap": 0,
        "blocking": [{"code": "FAKE_CODE"}],  # VIOLATION: blocking present for SHIP
        "metadata": {
            "mayor_version": "v0.1",
            "tribunal_bundle_hash": "a" * 64,
            "policies_hash": "b" * 64,
            "receipt_root_hash": "c" * 64
        }
    }

    schema = load_schema("decision_record.schema.json")

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=invalid_doc, schema=schema)

    error_msg = str(exc_info.value)
    print(f"✓ Schema correctly rejected SHIP with non-empty blocking")
    print(f"  Error: {error_msg}")


def test_schema_rejects_ship_with_nonzero_receipt_gap():
    """
    FALSIFICATION: Schema MUST reject SHIP with receipt_gap > 0.
    """
    invalid_doc = {
        "decision": "SHIP",
        "kill_switches_pass": True,
        "receipt_gap": 1,  # VIOLATION: non-zero receipt_gap for SHIP
        "blocking": [],
        "metadata": {
            "mayor_version": "v0.1",
            "tribunal_bundle_hash": "a" * 64,
            "policies_hash": "b" * 64,
            "receipt_root_hash": "c" * 64
        }
    }

    schema = load_schema("decision_record.schema.json")

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=invalid_doc, schema=schema)

    error_msg = str(exc_info.value)
    print(f"✓ Schema correctly rejected SHIP with receipt_gap > 0")
    print(f"  Error: {error_msg}")


def test_schema_rejects_ship_with_kill_switch_failure():
    """
    FALSIFICATION: Schema MUST reject SHIP with kill_switches_pass == false.
    """
    invalid_doc = {
        "decision": "SHIP",
        "kill_switches_pass": False,  # VIOLATION: kill switches failed
        "receipt_gap": 0,
        "blocking": [],
        "metadata": {
            "mayor_version": "v0.1",
            "tribunal_bundle_hash": "a" * 64,
            "policies_hash": "b" * 64,
            "receipt_root_hash": "c" * 64
        }
    }

    schema = load_schema("decision_record.schema.json")

    with pytest.raises(jsonschema.ValidationError) as exc_info:
        jsonschema.validate(instance=invalid_doc, schema=schema)

    error_msg = str(exc_info.value)
    print(f"✓ Schema correctly rejected SHIP with kill_switches_pass == false")
    print(f"  Error: {error_msg}")


# -----------------------------------------------------------------------------
# Additional Validation: Evidence Paths
# -----------------------------------------------------------------------------

def test_evidence_paths_are_relative():
    """
    Verify all evidence_paths in blocking entries are relative paths.

    Schema enforces RelPath pattern, but this test provides human-readable errors.
    """
    decision_record = load_json_fixture("decision_record_no_ship.json")
    blocking = decision_record.get("blocking", [])

    for i, entry in enumerate(blocking):
        evidence_paths = entry.get("evidence_paths", [])

        for j, path in enumerate(evidence_paths):
            # Check: not absolute
            if path.startswith("/"):
                raise AssertionError(
                    f"blocking[{i}].evidence_paths[{j}] is absolute path: {path}\n"
                    f"Evidence paths must be relative (schema should reject this)"
                )

            # Check: no parent traversal
            if ".." in path:
                raise AssertionError(
                    f"blocking[{i}].evidence_paths[{j}] contains parent traversal: {path}\n"
                    f"Evidence paths must not escape artifact directory (schema should reject this)"
                )

    print(f"✓ All evidence paths are valid relative paths")


# -----------------------------------------------------------------------------
# Run Tests
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
