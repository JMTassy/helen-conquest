#!/usr/bin/env python3
# Validate federation artifacts against schemas + minimal invariants.

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema missing. pip install jsonschema", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "oracle_town" / "federation" / "schemas"

SCHEMAS = {
    "FED_TREATY_V1": SCHEMA_DIR / "federation_treaty_v1.schema.json",
    "FED_LINK_V1": SCHEMA_DIR / "federation_link_v1.schema.json",
    "FED_RECEIPT_V1": SCHEMA_DIR / "federation_receipt_v1.schema.json",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(doc: dict) -> list:
    errors = []
    sv = doc.get("schema_version")
    if sv not in SCHEMAS:
        return [f"unknown schema_version: {sv}"]
    schema = load_json(SCHEMAS[sv])
    validator = jsonschema.Draft202012Validator(schema)
    for e in validator.iter_errors(doc):
        errors.append(e.message)
    # Minimal invariant: treaty towns must be unique by town_id
    if sv == "FED_TREATY_V1":
        towns = doc.get("towns", [])
        ids = [t.get("town_id") for t in towns]
        if len(ids) != len(set(ids)):
            errors.append("towns must be unique by town_id")
    # Minimal invariant: link from_town != to_town
    if sv == "FED_LINK_V1":
        if doc.get("from_town") == doc.get("to_town"):
            errors.append("from_town must differ from to_town")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_federation.py <path.json>")
        return 2
    path = Path(sys.argv[1])
    doc = load_json(path)
    errors = validate(doc)
    if errors:
        print("FEDERATION_VALIDATE: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("FEDERATION_VALIDATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
