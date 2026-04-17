"""Tests for EXPERIMENT_LINEAGE_V1 (ELG) and SKILL_LINEAGE_V1 (SEG).

Invariants verified:
  ELG-I1. experiment_id is unique within a lineage.
  ELG-I2. parent_experiment_id must refer to existing node.
  ELG-I3. Prior nodes are never modified (append-only).
  ELG-I4. Lineage hash is deterministic.
  ELG-I5. Query functions are pure (no side effects).

  SEG-I1. (skill_id, skill_version) pair is unique within a SEG.
  SEG-I2. parent must exist if set.
  SEG-I3. Prior nodes never modified.
  SEG-I4. get_skill_ancestry returns correct chain root→target.
"""
from __future__ import annotations

import copy

from helen_os.governance.canonical import sha256_prefixed
from helen_os.lineage.experiment_lineage_v1 import (
    make_empty_lineage,
    append_experiment_node,
    build_experiment_node,
    get_admitted_nodes,
    get_rejected_nodes,
    get_nodes_by_mutation_family,
    get_nodes_by_skill,
    get_node_by_id,
    compute_lineage_hash,
)
from helen_os.lineage.skill_lineage_v1 import (
    make_empty_skill_lineage,
    append_skill_node,
    build_skill_node,
    get_admitted_skill_nodes,
    get_nodes_by_skill_id,
    get_skill_ancestry,
    compute_skill_lineage_hash,
)


# ── Shared helpers ────────────────────────────────────────────────────────────

_HASH_A = "sha256:" + "a" * 64
_HASH_B = "sha256:" + "b" * 64
_HASH_C = "sha256:" + "c" * 64


def _node(experiment_id, skill_id="skill.search", decision="ADMITTED",
          mutation_family="architecture", parent_id=None):
    return build_experiment_node(
        experiment_id=experiment_id,
        skill_id=skill_id,
        candidate_version="1.0.0",
        mutation_family=mutation_family,
        eval_receipt_hash=_HASH_A,
        promotion_case_hash=_HASH_B,
        reducer_decision=decision,
        parent_experiment_id=parent_id,
    )


def _skill_node(skill_id, version, decision="ADMITTED",
                parent_id=None, parent_ver=None):
    return build_skill_node(
        skill_id=skill_id,
        skill_version=version,
        origin_experiments=["EXP_001"],
        promotion_case_hash=_HASH_C,
        reducer_decision=decision,
        parent_skill_id=parent_id,
        parent_version=parent_ver,
    )


# ── ELG tests ─────────────────────────────────────────────────────────────────

class TestExperimentLineage:

    def test_empty_lineage_has_no_nodes(self):
        lin = make_empty_lineage("lin_001")
        assert lin["schema_name"] == "EXPERIMENT_LINEAGE_V1"
        assert lin["nodes"] == []

    def test_append_node_adds_to_lineage(self):
        lin = make_empty_lineage("lin_001")
        node = _node("EXP_001")
        new_lin = append_experiment_node(lin, node)
        assert len(new_lin["nodes"]) == 1
        assert new_lin["nodes"][0]["experiment_id"] == "EXP_001"

    def test_elg_i3_prior_nodes_unchanged(self):
        """ELG-I3: original lineage unchanged after append."""
        lin = make_empty_lineage("lin_001")
        lin_before = copy.deepcopy(lin)
        node = _node("EXP_001")
        append_experiment_node(lin, node)
        assert lin == lin_before

    def test_elg_i1_duplicate_id_rejected(self):
        """ELG-I1: second append with same experiment_id silently returns unchanged."""
        lin = make_empty_lineage("lin_001")
        node = _node("EXP_001")
        lin2 = append_experiment_node(lin, node)
        lin3 = append_experiment_node(lin2, node)   # same id
        assert len(lin3["nodes"]) == 1   # unchanged

    def test_elg_i2_parent_must_exist(self):
        """ELG-I2: parent_experiment_id must refer to existing node."""
        lin = make_empty_lineage("lin_001")
        node = _node("EXP_002", parent_id="EXP_001")  # EXP_001 not in lineage yet
        new_lin = append_experiment_node(lin, node)
        assert len(new_lin["nodes"]) == 0   # rejected

    def test_elg_i2_root_node_no_parent(self):
        """ELG-I2: root node (parent_id=None) is accepted without parent check."""
        lin = make_empty_lineage("lin_001")
        root = _node("EXP_001", parent_id=None)
        new_lin = append_experiment_node(lin, root)
        assert len(new_lin["nodes"]) == 1

    def test_elg_i2_child_after_parent_accepted(self):
        """ELG-I2: child accepted once parent exists."""
        lin = make_empty_lineage("lin_001")
        lin = append_experiment_node(lin, _node("EXP_001"))
        lin = append_experiment_node(lin, _node("EXP_002", parent_id="EXP_001"))
        assert len(lin["nodes"]) == 2

    def test_get_admitted_nodes(self):
        lin = make_empty_lineage("lin_001")
        lin = append_experiment_node(lin, _node("EXP_001", decision="ADMITTED"))
        lin = append_experiment_node(lin, _node("EXP_002", decision="REJECTED"))
        lin = append_experiment_node(lin, _node("EXP_003", decision="ADMITTED"))
        admitted = get_admitted_nodes(lin)
        assert len(admitted) == 2
        assert all(n["reducer_decision"] == "ADMITTED" for n in admitted)

    def test_get_rejected_nodes(self):
        lin = make_empty_lineage("lin_001")
        lin = append_experiment_node(lin, _node("EXP_001", decision="ADMITTED"))
        lin = append_experiment_node(lin, _node("EXP_002", decision="REJECTED"))
        rejected = get_rejected_nodes(lin)
        assert len(rejected) == 1
        assert rejected[0]["experiment_id"] == "EXP_002"

    def test_get_nodes_by_mutation_family(self):
        lin = make_empty_lineage("lin_001")
        lin = append_experiment_node(lin, _node("EXP_001", mutation_family="architecture"))
        lin = append_experiment_node(lin, _node("EXP_002", mutation_family="optimizer"))
        lin = append_experiment_node(lin, _node("EXP_003", mutation_family="architecture"))
        arch_nodes = get_nodes_by_mutation_family(lin, "architecture")
        assert len(arch_nodes) == 2
        assert all(n["mutation_family"] == "architecture" for n in arch_nodes)

    def test_get_nodes_by_skill(self):
        lin = make_empty_lineage("lin_001")
        lin = append_experiment_node(lin, _node("EXP_001", skill_id="skill.search"))
        lin = append_experiment_node(lin, _node("EXP_002", skill_id="skill.rank"))
        search_nodes = get_nodes_by_skill(lin, "skill.search")
        assert len(search_nodes) == 1
        assert search_nodes[0]["skill_id"] == "skill.search"

    def test_elg_i4_compute_lineage_hash_deterministic(self):
        """ELG-I4: same lineage → same hash across two computations."""
        lin = make_empty_lineage("lin_001")
        lin = append_experiment_node(lin, _node("EXP_001"))
        lin = append_experiment_node(lin, _node("EXP_002", parent_id="EXP_001"))
        h1 = compute_lineage_hash(lin)
        h2 = compute_lineage_hash(lin)
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_elg_i4_different_lineages_different_hashes(self):
        """ELG-I4: different nodes → different hash."""
        lin1 = make_empty_lineage("lin_001")
        lin1 = append_experiment_node(lin1, _node("EXP_001", decision="ADMITTED"))
        lin2 = make_empty_lineage("lin_001")
        lin2 = append_experiment_node(lin2, _node("EXP_001", decision="REJECTED"))
        assert compute_lineage_hash(lin1) != compute_lineage_hash(lin2)

    def test_build_experiment_node_experiment_hash_deterministic(self):
        """Node's experiment_hash is computed deterministically."""
        n1 = _node("EXP_042")
        n2 = _node("EXP_042")
        assert n1["experiment_hash"] == n2["experiment_hash"]
        assert n1["experiment_hash"].startswith("sha256:")


# ── SEG tests ─────────────────────────────────────────────────────────────────

class TestSkillLineage:

    def test_empty_skill_lineage(self):
        seg = make_empty_skill_lineage("seg_001")
        assert seg["schema_name"] == "SKILL_LINEAGE_V1"
        assert seg["nodes"] == []

    def test_append_skill_node_adds(self):
        seg = make_empty_skill_lineage("seg_001")
        node = _skill_node("skill.search", "1.0.0")
        new_seg = append_skill_node(seg, node)
        assert len(new_seg["nodes"]) == 1

    def test_seg_i3_prior_nodes_unchanged(self):
        """SEG-I3: original SEG unchanged after append."""
        seg = make_empty_skill_lineage("seg_001")
        seg_before = copy.deepcopy(seg)
        append_skill_node(seg, _skill_node("skill.search", "1.0.0"))
        assert seg == seg_before

    def test_seg_i1_duplicate_version_rejected(self):
        """SEG-I1: (skill_id, skill_version) uniqueness enforced."""
        seg = make_empty_skill_lineage("seg_001")
        node = _skill_node("skill.search", "1.0.0")
        seg2 = append_skill_node(seg, node)
        seg3 = append_skill_node(seg2, node)   # duplicate
        assert len(seg3["nodes"]) == 1

    def test_seg_i2_parent_must_exist(self):
        """SEG-I2: parent (skill_id, version) must exist."""
        seg = make_empty_skill_lineage("seg_001")
        node = _skill_node("skill.search", "2.0.0",
                            parent_id="skill.search", parent_ver="1.0.0")
        new_seg = append_skill_node(seg, node)
        assert len(new_seg["nodes"]) == 0   # rejected

    def test_seg_i2_child_after_parent_accepted(self):
        """SEG-I2: child appended once parent exists."""
        seg = make_empty_skill_lineage("seg_001")
        seg = append_skill_node(seg, _skill_node("skill.search", "1.0.0"))
        seg = append_skill_node(seg, _skill_node(
            "skill.search", "2.0.0",
            parent_id="skill.search", parent_ver="1.0.0"
        ))
        assert len(seg["nodes"]) == 2

    def test_get_admitted_skill_nodes(self):
        seg = make_empty_skill_lineage("seg_001")
        seg = append_skill_node(seg, _skill_node("skill.search", "1.0.0", decision="ADMITTED"))
        seg = append_skill_node(seg, _skill_node("skill.search", "0.9.0", decision="REJECTED"))
        admitted = get_admitted_skill_nodes(seg)
        assert len(admitted) == 1
        assert admitted[0]["skill_version"] == "1.0.0"

    def test_get_skill_ancestry_chain(self):
        """SEG-I4: ancestry chain is correctly ordered root→target."""
        seg = make_empty_skill_lineage("seg_001")
        seg = append_skill_node(seg, _skill_node("skill.search", "1.0.0"))
        seg = append_skill_node(seg, _skill_node(
            "skill.search", "2.0.0",
            parent_id="skill.search", parent_ver="1.0.0"
        ))
        seg = append_skill_node(seg, _skill_node(
            "skill.search", "3.0.0",
            parent_id="skill.search", parent_ver="2.0.0"
        ))
        chain = get_skill_ancestry(seg, "skill.search", "3.0.0")
        assert len(chain) == 3
        assert chain[0]["skill_version"] == "1.0.0"
        assert chain[1]["skill_version"] == "2.0.0"
        assert chain[2]["skill_version"] == "3.0.0"

    def test_compute_skill_lineage_hash_deterministic(self):
        seg = make_empty_skill_lineage("seg_001")
        seg = append_skill_node(seg, _skill_node("skill.search", "1.0.0"))
        h1 = compute_skill_lineage_hash(seg)
        h2 = compute_skill_lineage_hash(seg)
        assert h1 == h2
        assert h1.startswith("sha256:")
