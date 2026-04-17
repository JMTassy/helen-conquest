"""Test: Skill discovery detects failure clusters and proposes new skills.

Law of discovery:
- Non-sovereign observation and proposal
- Repeated typed failures → capability gap → governed new skill
- All proposals pass through MAYOR (admission required)
- Same batch input → deterministic discovery output

Tests verify:
1. Failure clustering from batch results
2. Capability gap analysis
3. Deterministic discovery_id generation
4. Proposal schema compliance
5. Empty result when no clusters found
6. Confidence scoring and threshold filtering
"""
import pytest
from helen_os.autonomy.skill_discovery_v1 import (
    detect_failure_clusters,
    compute_deterministic_discovery_id,
    analyze_capability_gap,
    emit_discovery_proposal,
    discover_skills_in_batch,
    FailureCluster,
)


def make_batch_result_with_failures(failures: list) -> dict:
    """Helper: Create a batch result with specified failures."""
    entries = []
    for i, (task_id, failure_type) in enumerate(failures):
        entries.append(
            {
                "entry_index": i,
                "task_id": task_id,
                "decision": {
                    "decision_type": "REJECTED",
                    "reason_code": failure_type,
                    "skill_id": "skill.search",
                },
            }
        )
    return {"ledger": {"entries": entries}}


def test_detect_failure_clusters_simple():
    """detect_failure_clusters must find repeated failures."""
    batch = make_batch_result_with_failures(
        [
            ("task1", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
            ("task2", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
            ("task3", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
        ]
    )

    clusters = detect_failure_clusters(batch, min_occurrences=2)

    assert len(clusters) == 1
    assert clusters[0].failure_type == "ERR_UNRESOLVED_SOURCE_CONFLICT"
    assert clusters[0].occurrence_count == 3
    assert set(clusters[0].affected_task_ids) == {"task1", "task2", "task3"}


def test_detect_failure_clusters_multiple():
    """detect_failure_clusters must handle multiple distinct failure types."""
    batch = make_batch_result_with_failures(
        [
            ("t1", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
            ("t2", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
            ("t3", "ERR_DUPLICATE_DETECTION_FAILED"),
            ("t4", "ERR_DUPLICATE_DETECTION_FAILED"),
            ("t5", "ERR_RANKING_INCONSISTENT"),  # Only once, below threshold
        ]
    )

    clusters = detect_failure_clusters(batch, min_occurrences=2)

    assert len(clusters) == 2
    types = {c.failure_type for c in clusters}
    assert types == {
        "ERR_UNRESOLVED_SOURCE_CONFLICT",
        "ERR_DUPLICATE_DETECTION_FAILED",
    }


def test_detect_failure_clusters_below_threshold():
    """detect_failure_clusters must filter out clusters below min_occurrences."""
    batch = make_batch_result_with_failures(
        [
            ("t1", "ERR_RARE_FAILURE"),
        ]
    )

    clusters = detect_failure_clusters(batch, min_occurrences=2)

    assert len(clusters) == 0


def test_detect_failure_clusters_ignores_admitted():
    """detect_failure_clusters must ignore ADMITTED decisions."""
    entries = [
        {
            "entry_index": 0,
            "task_id": "t1",
            "decision": {"decision_type": "ADMITTED", "reason_code": "OK_ADMITTED"},
        },
        {
            "entry_index": 1,
            "task_id": "t2",
            "decision": {
                "decision_type": "REJECTED",
                "reason_code": "ERR_UNRESOLVED_SOURCE_CONFLICT",
            },
        },
    ]
    batch = {"ledger": {"entries": entries}}

    clusters = detect_failure_clusters(batch, min_occurrences=1)

    # Should find 1 cluster from the REJECTED decision, ADMITTED is ignored
    assert len(clusters) == 1
    assert clusters[0].failure_type == "ERR_UNRESOLVED_SOURCE_CONFLICT"
    assert clusters[0].occurrence_count == 1


def test_compute_deterministic_discovery_id():
    """compute_deterministic_discovery_id must be idempotent."""
    id1 = compute_deterministic_discovery_id(
        "batch123", "ERR_UNRESOLVED_SOURCE_CONFLICT", ["t1", "t2", "t3"]
    )
    id2 = compute_deterministic_discovery_id(
        "batch123", "ERR_UNRESOLVED_SOURCE_CONFLICT", ["t1", "t2", "t3"]
    )

    assert id1 == id2
    assert id1.startswith("discovery_")


def test_compute_deterministic_discovery_id_order_independent():
    """compute_deterministic_discovery_id must not depend on task order."""
    id1 = compute_deterministic_discovery_id(
        "batch123", "ERR_UNRESOLVED_SOURCE_CONFLICT", ["t1", "t2", "t3"]
    )
    id2 = compute_deterministic_discovery_id(
        "batch123", "ERR_UNRESOLVED_SOURCE_CONFLICT", ["t3", "t1", "t2"]
    )

    assert id1 == id2


def test_compute_deterministic_discovery_id_changes_on_input_diff():
    """compute_deterministic_discovery_id must differ for different inputs."""
    id1 = compute_deterministic_discovery_id(
        "batch123", "ERR_UNRESOLVED_SOURCE_CONFLICT", ["t1", "t2"]
    )
    id2 = compute_deterministic_discovery_id(
        "batch123", "ERR_UNRESOLVED_SOURCE_CONFLICT", ["t1", "t3"]
    )

    assert id1 != id2


def test_analyze_capability_gap():
    """analyze_capability_gap must classify the gap correctly."""
    cluster = FailureCluster(
        failure_type="ERR_UNRESOLVED_SOURCE_CONFLICT",
        occurrence_count=3,
        affected_task_ids=["t1", "t2", "t3"],
        common_context={},
    )
    state = {
        "active_skills": {
            "skill.search": "1.0.0",
            "skill.rank": "1.0.0",
        }
    }

    gap = analyze_capability_gap(cluster, state)

    assert gap["class"] == "RECONCILE"
    assert "gap" in gap["description"].lower()


def test_emit_discovery_proposal_structure():
    """emit_discovery_proposal must return valid NEW_SKILL_DISCOVERY_V1."""
    cluster = FailureCluster(
        failure_type="ERR_UNRESOLVED_SOURCE_CONFLICT",
        occurrence_count=3,
        affected_task_ids=["t1", "t2", "t3"],
        common_context={"skill_id": "skill.search"},
    )
    state = {"active_skills": {"skill.search": "1.0.0"}}

    proposal = emit_discovery_proposal("batch123", cluster, state, confidence=0.8)

    assert proposal["schema_name"] == "NEW_SKILL_DISCOVERY_V1"
    assert proposal["schema_version"] == "1.0.0"
    assert "discovery_id" in proposal
    assert proposal["batch_id"] == "batch123"
    assert proposal["failure_cluster"]["failure_type"] == "ERR_UNRESOLVED_SOURCE_CONFLICT"
    assert proposal["failure_cluster"]["occurrence_count"] == 3
    assert proposal["capability_gap"]["class"] == "RECONCILE"
    assert "proposed_skill" in proposal
    assert proposal["authority"] == "NONE"
    assert proposal["confidence"] == 0.8


def test_emit_discovery_proposal_deterministic():
    """emit_discovery_proposal must be deterministic for same inputs."""
    cluster = FailureCluster(
        failure_type="ERR_UNRESOLVED_SOURCE_CONFLICT",
        occurrence_count=2,
        affected_task_ids=["t1", "t2"],
        common_context={},
    )
    state = {"active_skills": {}}

    proposal1 = emit_discovery_proposal("batch123", cluster, state)
    proposal2 = emit_discovery_proposal("batch123", cluster, state)

    assert proposal1["discovery_id"] == proposal2["discovery_id"]


def test_discover_skills_in_batch_empty():
    """discover_skills_in_batch must return empty list when no clusters found."""
    batch = make_batch_result_with_failures(
        [
            ("t1", "ERR_UNIQUE_FAILURE"),
        ]
    )
    state = {"active_skills": {}}

    proposals = discover_skills_in_batch(batch, "batch123", state, min_occurrences=2)

    assert proposals == []


def test_discover_skills_in_batch_single_cluster():
    """discover_skills_in_batch must emit proposal for significant cluster."""
    batch = make_batch_result_with_failures(
        [
            ("t1", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
            ("t2", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
            ("t3", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
        ]
    )
    state = {"active_skills": {"skill.search": "1.0.0"}}

    proposals = discover_skills_in_batch(
        batch, "batch123", state, min_occurrences=2, confidence_threshold=0.5
    )

    assert len(proposals) == 1
    assert proposals[0]["schema_name"] == "NEW_SKILL_DISCOVERY_V1"
    assert proposals[0]["failure_cluster"]["failure_type"] == "ERR_UNRESOLVED_SOURCE_CONFLICT"


def test_discover_skills_in_batch_confidence_filtering():
    """discover_skills_in_batch must filter by confidence threshold."""
    batch = make_batch_result_with_failures(
        [
            ("t1", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
            ("t2", "ERR_UNRESOLVED_SOURCE_CONFLICT"),
        ]
    )
    state = {"active_skills": {}}

    proposals_high_threshold = discover_skills_in_batch(
        batch, "batch123", state, min_occurrences=2, confidence_threshold=0.9
    )
    proposals_low_threshold = discover_skills_in_batch(
        batch, "batch123", state, min_occurrences=2, confidence_threshold=0.5
    )

    # With default confidence of 0.7, high threshold filters it out
    assert len(proposals_high_threshold) == 0
    assert len(proposals_low_threshold) == 1


def test_discover_skills_proposed_skill_has_name():
    """emit_discovery_proposal must generate a valid skill name."""
    cluster = FailureCluster(
        failure_type="ERR_UNRESOLVED_SOURCE_CONFLICT",
        occurrence_count=2,
        affected_task_ids=["t1", "t2"],
        common_context={},
    )
    state = {"active_skills": {}}

    proposal = emit_discovery_proposal("batch123", cluster, state)

    assert "skill_name" in proposal["proposed_skill"]
    assert proposal["proposed_skill"]["skill_name"].startswith("skill.")
    assert proposal["proposed_skill"]["version"] == "1.0.0"


def test_discover_skills_authority_is_none():
    """All discovery proposals must have authority=NONE (non-sovereign)."""
    batch = make_batch_result_with_failures(
        [
            ("t1", "ERR_DUPLICATE_DETECTION_FAILED"),
            ("t2", "ERR_DUPLICATE_DETECTION_FAILED"),
        ]
    )
    state = {"active_skills": {}}

    proposals = discover_skills_in_batch(batch, "batch123", state)

    for proposal in proposals:
        assert proposal["authority"] == "NONE"
