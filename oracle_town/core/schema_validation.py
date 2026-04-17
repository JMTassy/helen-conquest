"""
Schema Validation Module - Fail-Closed Enforcement

This module enforces mandatory JSON Schema validation at every boundary object.
Every boundary crossing (Proposal → WUL, WUL → Briefcase, Factory → Receipt)
must call validate_or_raise() before proceeding.

Fail-closed: Invalid payloads abort the run immediately.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise ImportError(
        "jsonschema is required for schema validation. "
        "Install with: pip install jsonschema"
    )


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


class SchemaValidationError(ValueError):
    """Raised when a boundary object fails schema validation"""
    pass


def _load_schema(schema_filename: str) -> dict[str, Any]:
    """Load JSON schema from schemas/ directory"""
    schema_path = SCHEMAS_DIR / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema not found: {schema_path}\n"
            f"Expected location: {SCHEMAS_DIR}/{schema_filename}"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_or_raise(payload: Any, schema_filename: str) -> None:
    """
    Validate payload against JSON schema. Fail-closed.

    Args:
        payload: Object to validate (must be JSON-serializable)
        schema_filename: Name of schema file in schemas/ directory

    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If schema file doesn't exist

    Usage:
        validate_or_raise(ui_stream, "ui_event_stream.schema.json")
        validate_or_raise(receipt_bundle, "ci_receipt_bundle.schema.json")
    """
    schema = _load_schema(schema_filename)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))

    if errors:
        error_details = "\n".join([
            f"  - {list(e.path) if e.path else 'root'}: {e.message}"
            for e in errors
        ])
        raise SchemaValidationError(
            f"Schema validation failed ({schema_filename}):\n{error_details}\n\n"
            f"Boundary objects must conform exactly to their schemas.\n"
            f"No permissive fallbacks. Fix the payload or update the schema."
        )
