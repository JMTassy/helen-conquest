"""
tests/test_claim_graph_cg1_nodes.py — CG1: Claim Nodes and Graph Operations

Tests:
  CG1.1 — ClaimNodeType has 4 types (DECISION/GROUND/REBUTTAL/COUNTER_REBUTTAL)
  CG1.2 — ClaimGraph g_set/r_set/cr_set filter correctly
  CG1.3 — REBUTTAL / COUNTER_REBUTTAL require parent_id (raises ValueError)
  CG1.4 — add_counter_rebuttal marks the parent rebuttal.defeated = True
  CG1.5 — unanswered_rebuttals returns only rebuttals without counter-rebuttals
  CG1.6 — ClaimGraph.to_payload() is JSON-roundtrip stable
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from helen_os.claim_graph import (
    ClaimNode, ClaimNodeType, ClaimSource, ClaimGraph,
)


def make_graph() -> ClaimGraph:
    return ClaimGraph(decision_topic="Include feature X?")


def test_cg1_1_claim_node_types():
    """CG1.1 — 4 ClaimNodeType values exist."""
    types = set(ClaimNodeType)
    assert ClaimNodeType.DECISION         in types
    assert ClaimNodeType.GROUND           in types
    assert ClaimNodeType.REBUTTAL         in types
    assert ClaimNodeType.COUNTER_REBUTTAL in types
    assert len(types) == 4


def test_cg1_2_graph_gset_rset_crset():
    """CG1.2 — g_set, r_set, cr_set filter correctly."""
    g = make_graph()
    g1  = g.add_ground("Ground 1")
    g2  = g.add_ground("Ground 2")
    r1  = g.add_rebuttal("Rebuttal 1", parent_id="G1")
    cr1 = g.add_counter_rebuttal("Counter 1", parent_id="R1")

    assert len(g.g_set)  == 2,  f"Expected 2 grounds, got {len(g.g_set)}"
    assert len(g.r_set)  == 1,  f"Expected 1 rebuttal, got {len(g.r_set)}"
    assert len(g.cr_set) == 1,  f"Expected 1 CR, got {len(g.cr_set)}"
    assert g1.node_id  == "G1"
    assert g2.node_id  == "G2"
    assert r1.node_id  == "R1"
    assert cr1.node_id == "CR1"


def test_cg1_3_rebuttal_requires_parent():
    """CG1.3 — REBUTTAL and COUNTER_REBUTTAL require parent_id (ValueError if absent)."""
    with pytest.raises(ValueError, match="parent_id"):
        ClaimNode(
            node_id   = "R1",
            node_type = ClaimNodeType.REBUTTAL,
            claim_text= "Bad rebuttal",
            source    = ClaimSource.HAL,
            parent_id = None,           # must raise
        )
    with pytest.raises(ValueError, match="parent_id"):
        ClaimNode(
            node_id   = "CR1",
            node_type = ClaimNodeType.COUNTER_REBUTTAL,
            claim_text= "Bad CR",
            source    = ClaimSource.HELEN,
            parent_id = None,           # must raise
        )


def test_cg1_4_counter_rebuttal_sets_defeated():
    """CG1.4 — add_counter_rebuttal marks the parent rebuttal.defeated = True."""
    g = make_graph()
    g.add_ground("G text")
    r = g.add_rebuttal("R text", parent_id="G1")
    assert r.defeated is False

    g.add_counter_rebuttal("CR text", parent_id="R1")
    assert r.defeated is True


def test_cg1_5_unanswered_rebuttals():
    """CG1.5 — unanswered_rebuttals returns rebuttals without counter-rebuttals."""
    g = make_graph()
    g.add_ground("G1 text")
    g.add_ground("G2 text")
    r1 = g.add_rebuttal("R1 text", parent_id="G1")
    r2 = g.add_rebuttal("R2 text", parent_id="G2")

    # Both unanswered initially
    assert len(g.unanswered_rebuttals) == 2

    # Answer R1 only
    g.add_counter_rebuttal("CR1 text", parent_id="R1")
    unanswered = g.unanswered_rebuttals
    assert len(unanswered) == 1
    assert unanswered[0].node_id == "R2"

    # Answer R2
    g.add_counter_rebuttal("CR2 text", parent_id="R2")
    assert len(g.unanswered_rebuttals) == 0


def test_cg1_6_payload_json_roundtrip():
    """CG1.6 — to_payload() is JSON-roundtrip stable."""
    g = make_graph()
    g.add_ground("Ground text")
    g.add_rebuttal("Rebuttal text", parent_id="G1")
    g.add_counter_rebuttal("CR text", parent_id="R1")

    payload  = g.to_payload()
    json_str = json.dumps(payload, sort_keys=True)
    recovered = json.loads(json_str)

    assert recovered["type"]                 == "CLAIM_GRAPH_V1"
    assert recovered["g_set_count"]          == 1
    assert recovered["r_set_count"]          == 1
    assert recovered["cr_set_count"]         == 1
    assert recovered["unanswered_rebuttals"] == 0
    assert recovered["undefeated_grounds"]   == 1
    assert len(recovered["nodes"])           == 4  # D0 + G1 + R1 + CR1
