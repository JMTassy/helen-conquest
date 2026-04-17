"""Frozen schema registry.

Law:
- Exactly one schema store exists.
- All governance-critical schemas must be registered here.
- No module may invent an unknown schema and expect validation.
- Schemas are loaded once at module import and never modified.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Final


class SchemaRegistryError(Exception):
    """Raised when a schema cannot be found or loaded."""

    pass


def load_schema_store(schema_dir: Path) -> dict[str, Mapping[str, Any]]:
    """
    Load all schemas from directory into registry.

    For each *.json file, extract schema_name and schema_version constants,
    then store as key: f"{name}/{version}".

    Rules:
    - Only .json files in schema_dir are loaded.
    - Malformed files are silently skipped.
    - Schema must have properties.schema_name.const and properties.schema_version.const.

    Returns:
        dict mapping "SCHEMA_NAME/1.0.0" → schema object (JSON Schema)

    Raises:
        (none — silently skips malformed files)
    """
    store: dict[str, Mapping[str, Any]] = {}
    for p in schema_dir.glob("*.json"):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            # Extract const values from properties
            name = obj.get("properties", {}).get("schema_name", {}).get("const")
            version = obj.get("properties", {}).get("schema_version", {}).get("const")
            if name and version:
                key = f"{name}/{version}"
                store[key] = obj
        except (json.JSONDecodeError, KeyError, IOError):
            pass  # Skip malformed or inaccessible files
    return store


def get_schema(store: dict[str, Mapping[str, Any]], name: str, version: str) -> Mapping[str, Any]:
    """
    Retrieve a schema from the store by name and version.

    Args:
        store: Schema store dict (typically SCHEMA_STORE)
        name: Schema name (e.g., "EXECUTION_ENVELOPE_V1")
        version: Schema version (e.g., "1.0.0")

    Returns:
        Schema object (JSON Schema dict)

    Raises:
        SchemaRegistryError: if schema not found
    """
    key = f"{name}/{version}"
    if key not in store:
        raise SchemaRegistryError(f"Schema not registered: {key}")
    return store[key]


# Lazy load at module import (one-time)
_SCHEMA_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "schemas"
SCHEMA_STORE: Final[dict[str, Mapping[str, Any]]] = load_schema_store(_SCHEMA_DIR)
