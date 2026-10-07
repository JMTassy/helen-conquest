"""Property: cost predicate with strict booleans. Proves declaration shape only."""
from __future__ import annotations

import copy

import pytest

from cost_gate import (
    CONJUNCTS,
    DECLARED_FAVORABLE,
    DECLARED_UNFAVORABLE,
    REFUSED_MALFORMED,
    evaluate_cost_gate,
)


def favorable() -> dict:
    return {name: {"value": True, "evidence": f"receipt://{name}"} for name in CONJUNCTS}


def test_conjuncts_mirror_policy_text():
    # NewEvidence AND DecisionRelevant AND Unresolved AND Testable AND NOT Duplicate
    assert CONJUNCTS == ("new_evidence", "decision_relevant", "unresolved", "testable", "not_duplicate")


def test_all_true_is_declared_favorable_only():
    r = evaluate_cost_gate(favorable())
    assert r.verdict == DECLARED_FAVORABLE and r.failing == () and r.errors == ()
    assert "not a permission" in r.meaning
    assert not hasattr(r, "allowed") and not hasattr(r, "permitted")


@pytest.mark.parametrize("name", CONJUNCTS)
def test_single_false_conjunct_is_unfavorable_and_named(name):
    d = favorable()
    d[name]["value"] = False
    r = evaluate_cost_gate(d)
    assert r.verdict == DECLARED_UNFAVORABLE
    assert r.failing == (name,)


@pytest.mark.parametrize("name", CONJUNCTS)
def test_missing_conjunct_refused(name):
    d = favorable()
    del d[name]
    r = evaluate_cost_gate(d)
    assert r.verdict == REFUSED_MALFORMED and any(f"{name}: missing" in e for e in r.errors)


@pytest.mark.parametrize("bad_value", ["true", "True", "yes", 1, 0, 1.0, None, [True], {"v": True}])
def test_non_strict_bool_refused(bad_value):
    d = favorable()
    d["testable"]["value"] = bad_value
    r = evaluate_cost_gate(d)
    assert r.verdict == REFUSED_MALFORMED
    assert any("testable.value" in e for e in r.errors)


@pytest.mark.parametrize("bad_evidence", ["", "   ", None, [], {}, 0, 7])
def test_empty_or_non_evidence_refused(bad_evidence):
    d = favorable()
    d["unresolved"]["evidence"] = bad_evidence
    r = evaluate_cost_gate(d)
    assert r.verdict == REFUSED_MALFORMED
    assert any("unresolved.evidence" in e for e in r.errors)


def test_missing_evidence_key_refused():
    d = favorable()
    del d["new_evidence"]["evidence"]
    assert evaluate_cost_gate(d).verdict == REFUSED_MALFORMED


def test_extra_top_level_key_refused():
    d = favorable()
    d["operator_override"] = {"value": True, "evidence": "x"}
    r = evaluate_cost_gate(d)
    assert r.verdict == REFUSED_MALFORMED and any("unexpected keys" in e for e in r.errors)


def test_extra_nested_key_refused():
    d = favorable()
    d["testable"]["validated"] = True
    assert evaluate_cost_gate(d).verdict == REFUSED_MALFORMED


def test_malformation_wins_over_favorable_values():
    """A malformed declaration is never DECLARED_FAVORABLE, even if every present value is True."""
    d = favorable()
    d["not_duplicate"]["evidence"] = ""
    assert evaluate_cost_gate(d).verdict == REFUSED_MALFORMED


def test_all_errors_reported_not_just_first():
    d = favorable()
    del d["testable"]
    d["unresolved"]["value"] = "true"
    d["new_evidence"]["evidence"] = ""
    r = evaluate_cost_gate(d)
    assert r.verdict == REFUSED_MALFORMED and len(r.errors) == 3


@pytest.mark.parametrize("not_mapping", [None, "all true", 5, [("new_evidence", True)]])
def test_non_mapping_refused(not_mapping):
    assert evaluate_cost_gate(not_mapping).verdict == REFUSED_MALFORMED


def test_evaluation_is_pure():
    d = favorable()
    snapshot = copy.deepcopy(d)
    evaluate_cost_gate(d)
    assert d == snapshot
