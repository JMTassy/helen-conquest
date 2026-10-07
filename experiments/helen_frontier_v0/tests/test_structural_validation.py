"""Property: structural validation. Proves structure only."""
from __future__ import annotations

import pytest

from _fixtures import DELETE, make_discrimination
from discrimination import SCHEMA_NAME, load_schema, validate_discrimination


def test_schema_is_closed_everywhere():
    schema = load_schema()
    assert schema["additionalProperties"] is False
    assert schema["properties"]["authority"] == {"const": False}
    for name in ("witness", "provenance"):
        assert schema["properties"][name]["additionalProperties"] is False
    assert schema["$defs"]["evidenceRef"]["additionalProperties"] is False
    assert schema["title"] == SCHEMA_NAME


def test_valid_fixture_passes():
    ok, errors = validate_discrimination(make_discrimination())
    assert ok, errors
    assert errors == []


@pytest.mark.parametrize("field", [
    "schema", "distinction_id", "h_plus", "h_minus", "x_star", "e_plus", "e_minus",
    "witness", "status", "scope", "provenance", "authority",
])
def test_every_required_field_is_required(field):
    ok, errors = validate_discrimination(make_discrimination(**{field: DELETE}))
    assert not ok
    assert any(field in e for e in errors), errors


@pytest.mark.parametrize("bad_authority", [True, "false", 0, None])
def test_authority_must_be_literal_false(bad_authority):
    ok, _ = validate_discrimination(make_discrimination(authority=bad_authority))
    assert not ok


def test_unknown_top_level_property_rejected():
    ok, errors = validate_discrimination(make_discrimination(admitted=True))
    assert not ok and any("admitted" in e for e in errors)


def test_unknown_nested_property_rejected():
    d = make_discrimination()
    d["provenance"]["verified_by_platform"] = True
    ok, errors = validate_discrimination(d)
    assert not ok and any("verified_by_platform" in e for e in errors)


@pytest.mark.parametrize("text_field", ["h_plus", "h_minus", "x_star", "scope"])
@pytest.mark.parametrize("bad", ["", "   ", 3, None, ["x"]])
def test_text_fields_must_be_nonblank_strings(text_field, bad):
    ok, _ = validate_discrimination(make_discrimination(**{text_field: bad}))
    assert not ok


def test_status_enum_closed():
    for good in ("OPEN", "RESOLVED_PLUS", "RESOLVED_MINUS", "WITHDRAWN"):
        assert validate_discrimination(make_discrimination(status=good))[0]
    for bad in ("ADMITTED", "SEALED", "open", ""):
        assert not validate_discrimination(make_discrimination(status=bad))[0]


def test_provenance_requires_at_least_one_source_ref():
    ok, _ = validate_discrimination(make_discrimination(provenance={"producer": "W1", "source_refs": []}))
    assert not ok


def test_witness_kind_closed():
    ok, _ = validate_discrimination(make_discrimination(witness={"kind": "oracle", "requirement": "x"}))
    assert not ok


def test_evidence_lists_may_be_empty_but_items_are_typed():
    assert validate_discrimination(make_discrimination(e_plus=[], e_minus=[]))[0]
    assert not validate_discrimination(make_discrimination(e_plus=["loose string"]))[0]
    assert not validate_discrimination(make_discrimination(e_plus=[{"ref": "a"}]))[0]


@pytest.mark.parametrize("not_a_mapping", [None, 42, "D-x", ["D-x"], (), set()])
def test_non_mapping_input_refused(not_a_mapping):
    ok, errors = validate_discrimination(not_a_mapping)
    assert not ok and errors


def test_distinction_id_pattern():
    assert validate_discrimination(make_discrimination(distinction_id="D-abc.1_x-y"))[0]
    for bad in ("abc", "D-", "D-AB", "D-a b", "D-" + "x" * 70):
        assert not validate_discrimination(make_discrimination(distinction_id=bad))[0], bad
