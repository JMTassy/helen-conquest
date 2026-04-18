"""
tests/test_epoch4_claim_graph_v1.py — EPOCH4: Real CLAIM_GRAPH_V1 artifact pipeline

Tests:
  E4.1 — ingest_dialogue(fixture) produces ClaimGraphV1 with correct node IDs
  E4.2 — at least one OBJECTS_TO edge exists in the ingested graph
  E4.3 — computed G-set matches declared G-set (H1, H2, H3, H4, PERF1, ARCH1, QA1–QA5)
  E4.4 — kernel.verify_ledger() returns True after kernel.propose(graph)
  E4.5 — canonical source_digest is stable across 3 runs (same fixture → same hash)
  E4.6 — DR2 exists in decision_rules with correct depends_on members
  E4.7 — T1–T4 tasks are present in the graph
  E4.8 — run_epoch4() produces Epoch4Result with LOG A–D all PASS
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from helen_os.kernel import GovernanceVM
from helen_os.claim_graph.dialogue_ingest import ingest_dialogue, IngestError
from helen_os.claim_graph.graph_ops import (
    validate_graph, compute_sets, validate_dr_dependencies,
)
from helen_os.claim_graph.canon import sha256_text
from helen_os.epoch4 import run_epoch4, Epoch4Result


# ── Fixture ──────────────────────────────────────────────────────────────────

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "decay_dialogue_v1.txt"

EXPECTED_G_SET = {
    "H1", "H2", "H3", "H4", "PERF1", "ARCH1",
    "QA1", "QA2", "QA3", "QA4", "QA5",
}
EXPECTED_R_SET_EMPTY = True   # A1/A2/A3 are counter-objected → R-set = []

DR_DEPENDS_ON_REQUIRED = {"PERF1", "QA1", "QA2", "QA3", "ARCH1"}


def load_fixture() -> str:
    if not FIXTURE_PATH.exists():
        pytest.skip(f"Fixture not found: {FIXTURE_PATH}")
    return FIXTURE_PATH.read_text(encoding="utf-8")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_e4_1_ingest_produces_graph_with_correct_nodes():
    """E4.1 — ingest_dialogue(fixture) produces ClaimGraphV1 with H1..QA5 + A1..A3."""
    text  = load_fixture()
    graph = ingest_dialogue(text)

    node_ids = {n.node_id for n in graph.nodes}
    assert "H1"    in node_ids, f"H1 missing. Got: {node_ids}"
    assert "H2"    in node_ids
    assert "H3"    in node_ids
    assert "H4"    in node_ids
    assert "PERF1" in node_ids
    assert "ARCH1" in node_ids
    assert "A1"    in node_ids, f"A1 missing. Got: {node_ids}"
    assert "A2"    in node_ids
    assert "A3"    in node_ids
    assert "QA1"   in node_ids
    assert "QA3"   in node_ids
    assert "QA5"   in node_ids

    # LOG A: minimum claim count
    assert len(graph.nodes) >= 10, (
        f"LOG A: expected >= 10 claims, got {len(graph.nodes)}"
    )


def test_e4_2_at_least_one_objects_to_edge():
    """E4.2 — At least one OBJECTS_TO edge exists in the graph."""
    text  = load_fixture()
    graph = ingest_dialogue(text)

    objects_to = [e for e in graph.edges if e.type == "OBJECTS_TO"]
    assert len(objects_to) >= 1, (
        f"LOG B: no OBJECTS_TO edges found. Edge types: "
        f"{[e.type for e in graph.edges]}"
    )
    # The canonical fixture has 5 OBJECTS_TO edges
    assert len(objects_to) >= 3, (
        f"LOG B: expected >= 3 OBJECTS_TO edges, got {len(objects_to)}"
    )


def test_e4_3_computed_gset_matches_declared():
    """E4.3 — computed G-set matches declared G-set from fixture."""
    text   = load_fixture()
    graph  = ingest_dialogue(text)

    # Declared G-set from fixture text
    declared_g = set(graph.g_set)
    assert declared_g == EXPECTED_G_SET, (
        f"Declared G-set mismatch.\n"
        f"  Expected: {sorted(EXPECTED_G_SET)}\n"
        f"  Got:      {sorted(declared_g)}"
    )

    # Computed G-set via compute_sets()
    # When g_set is already declared, compute_sets preserves it
    graph_computed = compute_sets(graph)
    computed_g     = set(graph_computed.g_set)
    assert computed_g == EXPECTED_G_SET, (
        f"Computed G-set mismatch.\n"
        f"  Expected: {sorted(EXPECTED_G_SET)}\n"
        f"  Got:      {sorted(computed_g)}"
    )

    # Verify R-set is empty (A1/A2/A3 are counter-objected)
    assert graph_computed.r_set == [], (
        f"Expected empty R-set, got: {graph_computed.r_set}"
    )


def test_e4_4_kernel_verify_ledger_passes():
    """E4.4 — kernel.verify_ledger() returns True after proposing the graph."""
    text   = load_fixture()
    graph  = ingest_dialogue(text)
    graph  = compute_sets(graph)

    km      = GovernanceVM(ledger_path=":memory:")
    receipt = km.propose(graph.to_receipt_payload())

    assert receipt.id.startswith("R-"), f"Expected R-xxx receipt ID, got: {receipt.id!r}"
    assert len(receipt.cum_hash) == 64
    assert receipt.cum_hash != "0" * 64

    # In-memory ledger verify
    assert km.verify_ledger() is True, "kernel.verify_ledger() must return True"


def test_e4_5_source_digest_stable():
    """E4.5 — source_digest = sha256(fixture text) is stable across 3 runs."""
    text = load_fixture()

    digests = []
    for _ in range(3):
        graph = ingest_dialogue(text)
        digests.append(graph.source_digest)

    assert len(set(digests)) == 1, (
        f"source_digest is not stable across runs: {digests}"
    )
    # source_digest must be the SHA256 of the raw text
    expected = sha256_text(text)
    assert digests[0] == expected, (
        f"source_digest mismatch.\n"
        f"  Expected: {expected}\n"
        f"  Got:      {digests[0]}"
    )


def test_e4_6_dr2_exists_with_correct_depends_on():
    """E4.6 — DR2 exists in decision_rules with depends_on PERF1, QA1, QA2, QA3, ARCH1."""
    text  = load_fixture()
    graph = ingest_dialogue(text)

    dr_ids = [dr.rule_id for dr in graph.decision_rules]
    assert "DR2" in dr_ids, (
        f"DR2 not found in decision_rules. Got: {dr_ids}"
    )

    dr2 = next(dr for dr in graph.decision_rules if dr.rule_id == "DR2")
    actual_deps = set(dr2.depends_on)
    assert DR_DEPENDS_ON_REQUIRED.issubset(actual_deps), (
        f"DR2 missing required depends_on members.\n"
        f"  Required: {sorted(DR_DEPENDS_ON_REQUIRED)}\n"
        f"  Got:      {sorted(actual_deps)}"
    )

    # DR depends_on must be CONSTRAINT or GATE kind
    validate_graph(graph)
    validate_dr_dependencies(graph)   # must not raise


def test_e4_7_tasks_present():
    """E4.7 — T1–T4 tasks are present in the graph."""
    text  = load_fixture()
    graph = ingest_dialogue(text)

    task_ids = {t.task_id for t in graph.tasks}
    assert "T1" in task_ids, f"T1 missing from tasks. Got: {task_ids}"
    assert "T2" in task_ids
    assert "T3" in task_ids
    assert "T4" in task_ids

    # Each task must have non-empty fields
    for t in graph.tasks:
        assert t.text,            f"Task {t.task_id}: empty text"
        assert t.hypothesis,      f"Task {t.task_id}: empty hypothesis"
        assert t.validation_gate, f"Task {t.task_id}: empty validation_gate"


def test_e4_8_run_epoch4_logs_all_pass():
    """E4.8 — run_epoch4() produces Epoch4Result with all LOG A–D PASS."""
    text   = load_fixture()
    result = run_epoch4(text, ledger_path=":memory:")

    assert isinstance(result, Epoch4Result)

    # LOG A: claims extracted
    assert result.log_a["status"]       == "PASS", f"LOG A: {result.log_a}"
    assert result.log_a["claims_count"] >= 10

    # LOG B: edges + sets
    assert result.log_b["status"]            == "PASS", f"LOG B: {result.log_b}"
    assert result.log_b["objects_to_edges"]  >= 3

    # LOG C: DR dependencies
    assert result.log_c["status"]  == "PASS", f"LOG C: {result.log_c}"
    assert "DR2" in result.log_c["dr_ids"]

    # LOG D: no authority tokens
    assert result.log_d["status"] == "PASS", f"LOG D: {result.log_d}"

    # Receipt chain
    assert result.receipt_id.startswith("R-")
    assert len(result.cum_hash) == 64
    assert result.cum_hash != "0" * 64
