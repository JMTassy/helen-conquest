"""Properties: declared deduplication · rename invariance.

These test the *declared* contract (shared distinction_id ⇒ one group). They do
not test recognition of three wordings of one distinction, nor independence of
contributions. Naming them otherwise would overclaim.
"""
from __future__ import annotations

import copy

import pytest

from _fixtures import make_discrimination
from discrimination import declared_groups, group_signature


def test_same_declared_distinction_under_three_producers_is_one_group():
    items = [make_discrimination(provenance={"producer": p, "source_refs": ["s"]}) for p in ("W1", "W2", "W3")]
    groups = declared_groups(items)
    assert len(groups) == 1
    assert groups["D-e58-goldset-window"] == ("W1", "W2", "W3")
    assert group_signature(groups) == ((3, 1),)


def test_same_producers_with_different_distinctions_are_distinct_groups():
    items = [
        make_discrimination(distinction_id=f"D-q{i:03d}", provenance={"producer": "W1", "source_refs": ["s"]})
        for i in range(3)
    ]
    groups = declared_groups(items)
    assert len(groups) == 3
    assert all(v == ("W1",) for v in groups.values())
    assert group_signature(groups) == ((1, 3),)


def test_different_wording_same_id_is_still_one_group_declaratively():
    """Same id, different H+ text ⇒ one group. This is declaration, not semantics."""
    a = make_discrimination(h_plus="Threshold sufficient.")
    b = make_discrimination(h_plus="The 0.003 safety margin suffices for expansion.",
                            provenance={"producer": "W2", "source_refs": ["s"]})
    assert len(declared_groups([a, b])) == 1


def test_rename_invariance_under_bijective_producer_renaming():
    base = [
        make_discrimination(distinction_id="D-alpha", provenance={"producer": "W1", "source_refs": ["s"]}),
        make_discrimination(distinction_id="D-alpha", provenance={"producer": "W2", "source_refs": ["s"]}),
        make_discrimination(distinction_id="D-beta", provenance={"producer": "W2", "source_refs": ["s"]}),
        make_discrimination(distinction_id="D-gamma", provenance={"producer": "W3", "source_refs": ["s"]}),
    ]
    rename = {"W1": "ARCHITECT", "W2": "JESTER", "W3": "HAL"}
    renamed = copy.deepcopy(base)
    for item in renamed:
        item["provenance"]["producer"] = rename[item["provenance"]["producer"]]

    g0, g1 = declared_groups(base), declared_groups(renamed)
    assert group_signature(g0) == group_signature(g1) == ((1, 2), (2, 1))
    # groups correspond exactly under the renaming
    assert {k: tuple(sorted(rename[p] for p in v)) for k, v in g0.items()} == g1


def test_rename_invariance_under_distinction_id_renaming():
    base = [
        make_discrimination(distinction_id="D-alpha", provenance={"producer": "W1", "source_refs": ["s"]}),
        make_discrimination(distinction_id="D-alpha", provenance={"producer": "W2", "source_refs": ["s"]}),
        make_discrimination(distinction_id="D-beta", provenance={"producer": "W3", "source_refs": ["s"]}),
    ]
    renamed = copy.deepcopy(base)
    for item in renamed:
        item["distinction_id"] = {"D-alpha": "D-zeta", "D-beta": "D-omega"}[item["distinction_id"]]
    assert group_signature(declared_groups(base)) == group_signature(declared_groups(renamed))


def test_order_invariance():
    items = [make_discrimination(provenance={"producer": p, "source_refs": ["s"]}) for p in ("W3", "W1", "W2")]
    assert declared_groups(items) == declared_groups(list(reversed(items)))


def test_batch_refused_if_any_item_invalid():
    good = make_discrimination()
    bad = make_discrimination(authority=True)
    with pytest.raises(ValueError, match=r"item\[1\] invalid"):
        declared_groups([good, bad])


def test_grouping_is_pure():
    items = [make_discrimination()]
    snapshot = copy.deepcopy(items)
    declared_groups(items)
    assert items == snapshot
