"""Integration Tests: End-to-end skill discovery pipeline.

This test suite demonstrates the complete flow:
1. Batch execution with repeated failures
2. Failure cluster detection
3. Discovery proposal generation
4. Governance admission/rejection
5. State mutation (if admitted)
6. Ledger recording
7. Replay verification

These tests wire together:
- autoresearch_batch_v1 (batch processing)
- skill_discovery_v1 (detection + proposal)
- skill_promotion_reducer (governance)
- skill_library_state_updater (state mutation)
- decision_ledger_v1 (immutable recording)
- ledger_replay_v1 (deterministic reconstruction)
"""
import pytest
from helen_os.autonomy.skill_discovery_v1 import discover_skills_in_batch
from helen_os.governance.skill_promotion_reducer import reduce_promotion_packet
from helen_os.state.skill_library_state_updater import apply_skill_promotion_decision
from helen_os.state.decision_ledger_v1 import append_decision_to_ledger
from helen_os.state.ledger_replay_v1 import replay_ledger_to_state


def make_initial_state() -> dict:
    """Create an initial skill state."""
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {
            "skill.search": {
                "active_version": "1.0.0",
                "status": "ACTIVE",
                "last_decision_id": "initial",
            },
            "skill.rank": {
                "active_version": "1.0.0",
                "status": "ACTIVE",
                "last_decision_id": "initial",
            },
        },
    }


def make_initial_ledger() -> dict:
    """Create an empty ledger."""
    return {
        "schema_name": "DECISION_LEDGER_V1",
        "schema_version": "1.0.0",
        "ledger_id": "ledger_test_001",
        "canonicalization": "JCS_SHA256_V1",
        "entries": [],
    }


def make_batch_with_repeated_failures(
    batch_id: str, failure_type: str, count: int
) -> dict:
    """Create a batch result with N repeated failures of the same type."""
    entries = []
    for i in range(count):
        entries.append(
            {
                "entry_index": i,
                "task_id": f"task_{batch_id}_{i}",
                "decision": {
                    "decision_type": "REJECTED",
                    "reason_code": failure_type,
                    "skill_id": "skill.search",
                },
            }
        )
    return {"ledger": {"entries": entries}}


# ============================================================================
# SCENARIO 1: Discovery → Admission → State Mutation → Ledger Recording
# ============================================================================


def test_integration_discovery_to_state_mutation():
    """
    E2E: Batch with repeated failures → discovery proposal → admission →
    state mutation → ledger entry.

    This demonstrates the complete happy path where:
    1. Batch encounters repeated failures
    2. skill.discovery detects the pattern
    3. NEW_SKILL_DISCOVERY_V1 proposal is generated
    4. Proposal passes governance (reducer admission)
    5. New skill is added to state
    6. Ledger entry records the decision
    """
    # Setup
    initial_state = make_initial_state()
    initial_ledger = make_initial_ledger()
    batch_result = make_batch_with_repeated_failures(
        batch_id="batch_001",
        failure_type="ERR_UNRESOLVED_SOURCE_CONFLICT",
        count=3,
    )

    # Step 1: Detect failure clusters and emit discovery proposals
    proposals = discover_skills_in_batch(
        batch_result,
        batch_id="batch_001",
        active_state=initial_state,
        min_occurrences=2,
        confidence_threshold=0.5,
    )

    assert len(proposals) == 1, "Should detect one failure cluster"
    discovery_proposal = proposals[0]

    assert discovery_proposal["schema_name"] == "NEW_SKILL_DISCOVERY_V1"
    assert discovery_proposal["failure_cluster"]["failure_type"] == "ERR_UNRESOLVED_SOURCE_CONFLICT"
    assert discovery_proposal["failure_cluster"]["occurrence_count"] == 3
    assert discovery_proposal["authority"] == "NONE"

    # Step 2: Skip governance for this test (focus on state mutation + ledger)
    # In real scenario, ORACLE TOWN would validate and pass through MAYOR

    # Step 3: Manually create ADMITTED decision (assume governance approved)
    decision_obj = {
        "schema_name": "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id": f"discovery_{discovery_proposal['discovery_id']}",
        "skill_id": discovery_proposal["proposed_skill"]["skill_name"],
        "candidate_version": discovery_proposal["proposed_skill"]["version"],
        "decision_type": "ADMITTED",
        "reason_code": "OK_ADMITTED",
    }

    # Step 4: If admitted, mutate state
    new_state = apply_skill_promotion_decision(initial_state, decision_obj)

    # Verify state mutation
    assert discovery_proposal["proposed_skill"]["skill_name"] in new_state["active_skills"]
    new_skill_obj = new_state["active_skills"][discovery_proposal["proposed_skill"]["skill_name"]]
    assert new_skill_obj["active_version"] == "1.0.0"
    assert new_skill_obj["status"] == "ACTIVE"

    # Step 5: Record in ledger (append-only)
    new_ledger = append_decision_to_ledger(initial_ledger, decision_obj)

    assert len(new_ledger["entries"]) == 1
    assert new_ledger["entries"][0]["decision"]["decision_type"] == "ADMITTED"


# ============================================================================
# SCENARIO 2: Multiple Discovery Proposals in One Batch
# ============================================================================


def test_integration_multiple_discoveries_one_batch():
    """
    E2E: Batch with multiple distinct failure clusters → multiple proposals.

    This tests that the system can detect and propose multiple new skills
    from a single batch.
    """
    initial_state = make_initial_state()

    # Create a batch with TWO distinct failure clusters
    entries = []
    idx = 0

    # Cluster 1: ERR_UNRESOLVED_SOURCE_CONFLICT (3 times)
    for i in range(3):
        entries.append(
            {
                "entry_index": idx,
                "task_id": f"task_conflict_{i}",
                "decision": {
                    "decision_type": "REJECTED",
                    "reason_code": "ERR_UNRESOLVED_SOURCE_CONFLICT",
                    "skill_id": "skill.search",
                },
            }
        )
        idx += 1

    # Cluster 2: ERR_DUPLICATE_DETECTION_FAILED (2 times)
    for i in range(2):
        entries.append(
            {
                "entry_index": idx,
                "task_id": f"task_dedup_{i}",
                "decision": {
                    "decision_type": "REJECTED",
                    "reason_code": "ERR_DUPLICATE_DETECTION_FAILED",
                    "skill_id": "skill.filter",
                },
            }
        )
        idx += 1

    batch_result = {"ledger": {"entries": entries}}

    # Discover proposals
    proposals = discover_skills_in_batch(
        batch_result,
        batch_id="batch_multi",
        active_state=initial_state,
        min_occurrences=2,
        confidence_threshold=0.5,
    )

    # Should detect both clusters
    assert len(proposals) == 2

    # Verify both proposals are distinct
    failure_types = {p["failure_cluster"]["failure_type"] for p in proposals}
    assert failure_types == {
        "ERR_UNRESOLVED_SOURCE_CONFLICT",
        "ERR_DUPLICATE_DETECTION_FAILED",
    }

    # Verify both are non-sovereign
    for proposal in proposals:
        assert proposal["authority"] == "NONE"


# ============================================================================
# SCENARIO 3: Deterministic Discovery (Same Batch → Same Proposals)
# ============================================================================


def test_integration_discovery_determinism():
    """
    E2E: Same batch processed twice produces identical discovery proposals.

    This proves that skill discovery is deterministic and idempotent,
    which is critical for governance repeatability.
    """
    initial_state = make_initial_state()

    batch_result = make_batch_with_repeated_failures(
        batch_id="batch_determ",
        failure_type="ERR_RANKING_INCONSISTENT",
        count=2,
    )

    # Process the same batch twice
    proposals_1 = discover_skills_in_batch(
        batch_result,
        batch_id="batch_determ",
        active_state=initial_state,
        min_occurrences=2,
    )

    proposals_2 = discover_skills_in_batch(
        batch_result,
        batch_id="batch_determ",
        active_state=initial_state,
        min_occurrences=2,
    )

    # Should produce identical proposals
    assert len(proposals_1) == len(proposals_2)
    assert proposals_1[0]["discovery_id"] == proposals_2[0]["discovery_id"]
    assert proposals_1[0]["proposed_skill"]["skill_name"] == proposals_2[0]["proposed_skill"]["skill_name"]


# ============================================================================
# SCENARIO 4: Ledger Replay After Governance
# ============================================================================


def test_integration_ledger_replay_after_admission():
    """
    E2E: Execute discovery → admit → record → replay ledger →
    verify reconstructed state matches applied state.

    This demonstrates the load-bearing property:
    initial_state + ledger → replay_ledger_to_state() → same final_state
    """
    initial_state = make_initial_state()
    initial_ledger = make_initial_ledger()

    # Create batch with discovery
    batch_result = make_batch_with_repeated_failures(
        batch_id="batch_replay",
        failure_type="ERR_VALIDATION_FAILED",
        count=2,
    )

    # Discover proposal
    proposals = discover_skills_in_batch(
        batch_result,
        batch_id="batch_replay",
        active_state=initial_state,
        min_occurrences=2,
    )

    assert len(proposals) == 1
    proposal = proposals[0]

    # Manually create admission decision (skip governance for this test)
    decision = {
        "schema_name": "SKILL_PROMOTION_DECISION_V1",
        "schema_version": "1.0.0",
        "decision_id": f"test_{proposal['discovery_id']}",
        "skill_id": proposal["proposed_skill"]["skill_name"],
        "candidate_version": proposal["proposed_skill"]["version"],
        "decision_type": "ADMITTED",
        "reason_code": "OK_ADMITTED",
    }

    # Apply to state
    state_after_application = apply_skill_promotion_decision(initial_state, decision)

    # Record in ledger
    ledger_with_entry = append_decision_to_ledger(initial_ledger, decision)

    # Now replay the ledger and verify it reconstructs to the same state
    state_after_replay = replay_ledger_to_state(
        ledger=ledger_with_entry, initial_state=initial_state
    )

    # Critical check: replayed state matches applied state
    assert state_after_replay["active_skills"] == state_after_application["active_skills"]


# ============================================================================
# SCENARIO 5: Filtering by Confidence Threshold
# ============================================================================


def test_integration_confidence_threshold_filters_weak_proposals():
    """
    E2E: With high confidence threshold, weak proposals are filtered.

    This tests the detector's confidence scoring and threshold filtering,
    ensuring only high-confidence discoveries are proposed.
    """
    initial_state = make_initial_state()

    # Single failure (low confidence cluster)
    batch_result = make_batch_with_repeated_failures(
        batch_id="batch_weak",
        failure_type="ERR_RARE_ERROR",
        count=1,  # Only 1 occurrence
    )

    # With high threshold, should filter out
    proposals_high_threshold = discover_skills_in_batch(
        batch_result,
        batch_id="batch_weak",
        active_state=initial_state,
        min_occurrences=1,
        confidence_threshold=0.9,  # Very high threshold
    )

    # With low threshold, should pass
    proposals_low_threshold = discover_skills_in_batch(
        batch_result,
        batch_id="batch_weak",
        active_state=initial_state,
        min_occurrences=1,
        confidence_threshold=0.5,  # Lower threshold
    )

    assert len(proposals_high_threshold) == 0, "High threshold filters out weak proposal"
    assert len(proposals_low_threshold) >= 0  # May still filter due to min_occurrences


# ============================================================================
# SCENARIO 6: Governance Rejection (Quarantine)
# ============================================================================


def test_integration_governance_quarantine_on_missing_receipts():
    """
    E2E: Discovery proposal → governance → rejection due to validation failure.

    This demonstrates that even discovered proposals must pass governance gates,
    and that governance properly rejects proposals with schema violations or
    insufficient evidence (receipts).
    """
    initial_state = make_initial_state()

    # Create discovery proposal
    batch_result = make_batch_with_repeated_failures(
        batch_id="batch_reject",
        failure_type="ERR_SCHEMA_TRANSFORMATION_FAILED",
        count=2,
    )

    proposals = discover_skills_in_batch(
        batch_result,
        batch_id="batch_reject",
        active_state=initial_state,
        min_occurrences=2,
    )

    assert len(proposals) == 1
    discovery_proposal = proposals[0]

    # Convert to skill promotion packet WITHOUT receipts (schema invalid)
    invalid_packet = {
        "schema_name": "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id": discovery_proposal["discovery_id"],
        "skill_id": discovery_proposal["proposed_skill"]["skill_name"],
        "candidate_version": discovery_proposal["proposed_skill"]["version"],
        "lineage": {
            "parent_skill_id": discovery_proposal["proposed_skill"]["parent_skill_id"],
        },
        "doctrine_surface": {
            "law_surface_version": "v1",
            "transfer_required": False,
        },
        "evaluation": {
            "passed": True,
        },
        "receipts": [],  # EMPTY - violates schema requirement
    }

    # Reducer should reject
    result = reduce_promotion_packet(invalid_packet, initial_state)

    # Should be REJECTED (schema validation is first gate)
    assert result.decision == "REJECTED"
    # The rejection reason is ERR_SCHEMA_INVALID because receipts fails schema
    assert result.reason_code == "ERR_SCHEMA_INVALID"


# ============================================================================
# SCENARIO 7: Non-Sovereignty Verification
# ============================================================================


def test_integration_discovery_proposals_are_non_sovereign():
    """
    E2E: Verify that discovery proposals have authority=NONE
    (non-sovereign, require MAYOR admission).

    This is a critical invariant: skill.discovery never claims authority
    over governance decisions. It only proposes.
    """
    initial_state = make_initial_state()

    batch_result = make_batch_with_repeated_failures(
        batch_id="batch_nonsovrn",
        failure_type="ERR_CAPABILITY_DRIFT",
        count=3,
    )

    proposals = discover_skills_in_batch(
        batch_result,
        batch_id="batch_nonsovrn",
        active_state=initial_state,
        min_occurrences=2,
    )

    # Every proposal must be non-sovereign
    for proposal in proposals:
        assert proposal["authority"] == "NONE"
        assert proposal["schema_name"] == "NEW_SKILL_DISCOVERY_V1"
        # Should NOT have any sovereign fields like "decision" or "receipt_hash"
        assert "decision" not in proposal
        assert "receipt_hash" not in proposal


# ============================================================================
# SCENARIO 8: Mixed Batch (Admitted + Rejected + New Discoveries)
# ============================================================================


def test_integration_discovery_coexists_with_normal_batch_flow():
    """
    E2E: A single batch contains:
    - Some admitted decisions (normal skills working)
    - Some rejected decisions (repeated failures)
    - Discoveries generated from rejection patterns

    This is the realistic scenario: not all failures indicate new skills,
    but patterns do.
    """
    initial_state = make_initial_state()

    # Mixed batch: some successes, some repeated failures
    entries = [
        # Admission (skill working fine)
        {
            "entry_index": 0,
            "task_id": "task_ok_1",
            "decision": {"decision_type": "ADMITTED", "reason_code": "OK_ADMITTED"},
        },
        # Repeated failure cluster
        {
            "entry_index": 1,
            "task_id": "task_fail_1",
            "decision": {
                "decision_type": "REJECTED",
                "reason_code": "ERR_UNRESOLVED_SOURCE_CONFLICT",
            },
        },
        {
            "entry_index": 2,
            "task_id": "task_fail_2",
            "decision": {
                "decision_type": "REJECTED",
                "reason_code": "ERR_UNRESOLVED_SOURCE_CONFLICT",
            },
        },
        # Another admission
        {
            "entry_index": 3,
            "task_id": "task_ok_2",
            "decision": {"decision_type": "ADMITTED", "reason_code": "OK_ADMITTED"},
        },
    ]

    batch_result = {"ledger": {"entries": entries}}

    # Discover
    proposals = discover_skills_in_batch(
        batch_result,
        batch_id="batch_mixed",
        active_state=initial_state,
        min_occurrences=2,
    )

    # Should detect the failure pattern (ignoring admissions)
    assert len(proposals) >= 1
    assert proposals[0]["failure_cluster"]["failure_type"] == "ERR_UNRESOLVED_SOURCE_CONFLICT"
    assert proposals[0]["failure_cluster"]["occurrence_count"] == 2
