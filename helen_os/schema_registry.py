"""
schema_registry.py - Schema loading and artifact validation.

Constitutional rule: Every artifact must be schema-valid before entering kernel.
"""

import json
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    from jsonschema import Draft202012Validator, ValidationError
except ImportError:
    raise ImportError(
        "jsonschema required. Install with: pip install jsonschema"
    )


class SchemaRegistry:
    """
    Thread-safe schema registry for HELEN artifacts.

    Loads schemas once, caches them, validates artifacts against them.
    """

    def __init__(self, schema_dir: Path = None):
        """
        Initialize registry with schema directory.

        Args:
            schema_dir: Path to schemas/ directory.
                        Defaults to helen_os/schemas/ (constitutional tree).
                        GOVERNANCE_DECISION_V1 SCHEMA-AUTHORITY-2026-04-16:
                        Registry A (governance/) is canonical. This default
                        was redirected from root schemas/ to helen_os/schemas/
                        per Action 1. Parameter retained for transition;
                        Action 2 will remove it.
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent / "schemas"

        self.schema_dir = schema_dir
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._validators: Dict[str, Draft202012Validator] = {}

    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Load schema by name (canonical MVP naming: lowercase_v1.json).

        Examples:
            load_schema("EXECUTION_ENVELOPE_V1")
            load_schema("SKILL_PROMOTION_PACKET_V1")

        Returns cached schema if already loaded.
        """
        if schema_name in self._schemas:
            return self._schemas[schema_name]

        # Load with canonical naming: lowercase.json
        schema_file = self.schema_dir / f"{schema_name.lower()}.json"

        if not schema_file.exists():
            raise FileNotFoundError(
                f"Schema not found: {schema_name} "
                f"(looked for {schema_file})"
            )

        with open(schema_file, "r") as f:
            schema = json.load(f)

        self._schemas[schema_name] = schema
        return schema

    def get_validator(self, schema_name: str) -> Draft202012Validator:
        """
        Get or create validator for schema.

        Caches validators to avoid repeated schema parsing.
        """
        if schema_name not in self._validators:
            schema = self.load_schema(schema_name)
            self._validators[schema_name] = Draft202012Validator(schema)

        return self._validators[schema_name]

    def validate_artifact(
        self, artifact: Any, schema_name: str
    ) -> Tuple[bool, list]:
        """
        Validate artifact against schema.

        Returns (is_valid, error_messages)
        """
        try:
            validator = self.get_validator(schema_name)
            errors = list(validator.iter_errors(artifact))

            if not errors:
                return (True, [])

            error_messages = [
                f"{'.'.join(str(p) for p in e.path)}: {e.message}"
                for e in errors
            ]
            return (False, error_messages)

        except Exception as e:
            return (False, [f"Validation error: {str(e)}"])

    def validate_or_reject(self, artifact: Any, schema_name: str) -> None:
        """
        Validate artifact. Raise ValueError if invalid.

        This is the strict path: no validation → exception.
        """
        is_valid, errors = self.validate_artifact(artifact, schema_name)

        if not is_valid:
            error_text = "\n  ".join(errors)
            raise ValueError(
                f"Artifact validation failed for {schema_name}:\n  {error_text}"
            )


# Global singleton registry
_global_registry: SchemaRegistry = None


def get_registry() -> SchemaRegistry:
    """Get or create global schema registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = SchemaRegistry()
    return _global_registry


def validate_artifact(artifact: Any, schema_name: str) -> Tuple[bool, list]:
    """
    Convenience function: validate artifact using global registry.

    Returns (is_valid, error_messages)
    """
    return get_registry().validate_artifact(artifact, schema_name)


def validate_or_reject(artifact: Any, schema_name: str) -> None:
    """
    Convenience function: validate or raise ValueError.
    """
    get_registry().validate_or_reject(artifact, schema_name)


__all__ = [
    "SchemaRegistry",
    "get_registry",
    "validate_artifact",
    "validate_or_reject",
]
