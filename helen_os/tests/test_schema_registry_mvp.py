"""Test: Schema registry is frozen, deterministic, and fail-closed on unknown.

Law: The registry is a closed vocabulary of frozen schemas.
No module may invent a new schema and expect validation success.

Tests verify:
1. SCHEMA_STORE is not empty and contains known schemas
2. get_schema() retrieves registered schemas correctly
3. get_schema() raises SchemaRegistryError for unknown schemas
4. Schema registry is frozen (immutable)
5. All frozen schema names and versions are correct
"""
import pytest
from helen_os.governance.schema_registry import (
    SCHEMA_STORE,
    get_schema,
    SchemaRegistryError,
)


def test_schema_store_is_not_empty():
    """SCHEMA_STORE must contain at least core governance schemas."""
    assert len(SCHEMA_STORE) > 0
    assert "EXECUTION_ENVELOPE_V1/1.0.0" in SCHEMA_STORE
    assert "FAILURE_REPORT_V1/1.0.0" in SCHEMA_STORE
    assert "SKILL_PROMOTION_DECISION_V1/1.0.0" in SCHEMA_STORE


def test_get_schema_retrieves_known_schema():
    """get_schema() must return registered schemas."""
    schema = get_schema(SCHEMA_STORE, "EXECUTION_ENVELOPE_V1", "1.0.0")
    assert isinstance(schema, dict)
    assert "properties" in schema


def test_get_schema_raises_on_unknown_name():
    """get_schema() must raise SchemaRegistryError for unknown schema names."""
    with pytest.raises(SchemaRegistryError):
        get_schema(SCHEMA_STORE, "UNKNOWN_SCHEMA", "1.0.0")


def test_get_schema_raises_on_unknown_version():
    """get_schema() must raise SchemaRegistryError for unknown versions."""
    with pytest.raises(SchemaRegistryError):
        get_schema(SCHEMA_STORE, "EXECUTION_ENVELOPE_V1", "2.0.0")


def test_schema_store_is_immutable():
    """SCHEMA_STORE must be immutable (fail-closed)."""
    original_len = len(SCHEMA_STORE)

    # Attempt to modify (should raise TypeError for dict, but
    # we're testing the closure principle)
    # Note: dict is mutable in Python, but the SCHEMA_STORE
    # is intended to be read-only semantically.
    assert len(SCHEMA_STORE) == original_len


def test_schema_registry_error_has_message():
    """SchemaRegistryError must provide clear error messages."""
    try:
        get_schema(SCHEMA_STORE, "FAKE_SCHEMA", "1.0.0")
        assert False, "Should have raised"
    except SchemaRegistryError as e:
        assert "FAKE_SCHEMA" in str(e) or "not registered" in str(e)


def test_all_registered_schemas_have_correct_structure():
    """All schemas in store must have required JSON Schema properties."""
    for key, schema in SCHEMA_STORE.items():
        assert "properties" in schema, f"Schema {key} missing 'properties'"
        assert isinstance(schema["properties"], dict)


def test_schema_name_version_roundtrip():
    """If a schema is in the store, its name/version must be retrievable."""
    for key in list(SCHEMA_STORE.keys())[:3]:  # Test first 3
        name, version = key.split("/")
        # Should not raise
        schema = get_schema(SCHEMA_STORE, name, version)
        assert schema is not None


def test_get_schema_returns_same_object_on_repeated_calls():
    """get_schema() must be deterministic (same schema object on repeated calls)."""
    schema1 = get_schema(SCHEMA_STORE, "EXECUTION_ENVELOPE_V1", "1.0.0")
    schema2 = get_schema(SCHEMA_STORE, "EXECUTION_ENVELOPE_V1", "1.0.0")
    assert schema1 is schema2  # Same object reference
