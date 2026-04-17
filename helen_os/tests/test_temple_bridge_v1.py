"""Test: temple_bridge_v1 requires Mayor path and preserves provenance.

Proves:
- Bridge never emits a mutation directly
- All output is PENDING_MAYOR_REVIEW (pre-institutional)
- Provenance hash links output to source
- Artifacts with sovereign fields are rejected
- Bridge is deterministic for same input
- authority is always "NONE"
"""
import pytest
from helen_os.temple.temple_v1 import run_temple_exploration
from helen_os.temple.temple_bridge_v1 import bridge_temple_to_proposal, BridgeRejectionError
from helen_os.governance.canonical import sha256_prefixed


# ─── helpers ──────────────────────────────────────────────────────────────────

def minimal_artifact(session_id="bridge_test_001", theme="Test theme"):
    return run_temple_exploration(
        session_id=session_id,
        theme=theme,
        her_threads=[],
        hal_frictions=[],
        tension_map=[],
        center_sketches=[],
        export_candidates=[],
    )


def artifact_with_skill_idea():
    return run_temple_exploration(
        session_id="bridge_test_skill",
        theme="Skill idea proposal",
        her_threads=[{"thread_id": "t1", "content": "We need a reconciliation skill"}],
        hal_frictions=[{"friction_id": "f1", "content": "What evidence?"}],
        tension_map=[{"tension_id": "tn1", "pole_a": "Create", "pole_b": "Verify",
                      "description": "Classic tension"}],
        center_sketches=[{"sketch_id": "s1", "content": "The skill"}],
        export_candidates=[
            {"candidate_id": "e1", "candidate_type": "SKILL_IDEA",
             "content": "skill.reconcile_conflicts"},
        ],
    )


# ─── LAW 1: Bridge may reformat, never admit ──────────────────────────────────

def test_bridge_output_is_pending_mayor_review():
    """Bridge output is always PENDING_MAYOR_REVIEW — never admitted."""
    artifact = minimal_artifact()
    request = bridge_temple_to_proposal(artifact)

    assert request["bridge_status"] == "PENDING_MAYOR_REVIEW"


def test_bridge_output_has_no_decision_field():
    """Bridge never emits a decision."""
    artifact = minimal_artifact()
    request = bridge_temple_to_proposal(artifact)

    assert "decision" not in request


def test_bridge_output_has_no_verdict_field():
    """Bridge never emits a verdict."""
    artifact = artifact_with_skill_idea()
    request = bridge_temple_to_proposal(artifact)

    assert "verdict" not in request
    assert "approved" not in request
    assert "rejected" not in request


# ─── LAW 2: Bridge may compress, never verdict ────────────────────────────────

def test_bridge_compresses_tensions_to_summary():
    """Bridge compresses tensions into summary (not full content)."""
    artifact = run_temple_exploration(
        session_id="compress_test",
        theme="Compression",
        her_threads=[],
        hal_frictions=[],
        tension_map=[
            {"tension_id": "tn1", "pole_a": "A", "pole_b": "B", "description": "long description"},
        ],
        center_sketches=[],
        export_candidates=[],
    )
    request = bridge_temple_to_proposal(artifact)

    # Compressed: only tension_id, pole_a, pole_b (not description)
    assert len(request["tension_summary"]) == 1
    assert "description" not in request["tension_summary"][0]
    assert request["tension_summary"][0]["tension_id"] == "tn1"


# ─── LAW 3: Bridge extracts candidate claims, never asserts truth ─────────────

def test_bridge_extracts_candidate_claims_as_pre_institutional():
    """Extracted claims are always PRE_INSTITUTIONAL."""
    artifact = artifact_with_skill_idea()
    request = bridge_temple_to_proposal(artifact)

    assert len(request["candidate_claims"]) == 1
    claim = request["candidate_claims"][0]
    assert claim["status"] == "PRE_INSTITUTIONAL"
    assert claim["content"] == "skill.reconcile_conflicts"


def test_bridge_empty_candidates_yields_archival():
    """No export candidates → archival proposal_kind."""
    artifact = minimal_artifact()
    request = bridge_temple_to_proposal(artifact)

    assert request["proposal_kind"] == "archival"
    assert request["candidate_claims"] == []


# ─── LAW 4: Provenance must be preserved ──────────────────────────────────────

def test_bridge_preserves_source_artifact_id():
    """source_artifact_id matches original session_id."""
    artifact = minimal_artifact(session_id="provenance_test_001")
    request = bridge_temple_to_proposal(artifact)

    assert request["source_artifact_id"] == "provenance_test_001"


def test_bridge_preserves_source_payload_hash():
    """source_payload_hash is a valid sha256 of the original artifact."""
    artifact = minimal_artifact()
    expected_hash = sha256_prefixed(artifact)
    request = bridge_temple_to_proposal(artifact)

    assert request["source_payload_hash"] == expected_hash
    assert request["source_payload_hash"].startswith("sha256:")


def test_bridge_source_schema_preserved():
    """source_schema names the Temple artifact schema."""
    artifact = minimal_artifact()
    request = bridge_temple_to_proposal(artifact)

    assert request["source_schema"] == "TEMPLE_EXPLORATION_V1"


# ─── LAW 5: Missing provenance = rejection ────────────────────────────────────

def test_bridge_rejects_wrong_schema_name():
    """Bridge rejects artifacts that are not TEMPLE_EXPLORATION_V1."""
    bad_artifact = {
        "schema_name": "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "authority": "NONE",
    }
    with pytest.raises(BridgeRejectionError, match="TEMPLE_EXPLORATION_V1"):
        bridge_temple_to_proposal(bad_artifact)


def test_bridge_rejects_missing_schema_name():
    """Bridge rejects artifacts with missing schema_name."""
    bad_artifact = {"theme": "test", "authority": "NONE"}
    with pytest.raises(BridgeRejectionError, match="TEMPLE_EXPLORATION_V1"):
        bridge_temple_to_proposal(bad_artifact)


def test_bridge_rejects_authority_not_none():
    """Bridge rejects artifacts claiming authority != NONE."""
    bad_artifact = {
        "schema_name": "TEMPLE_EXPLORATION_V1",
        "authority": "MAYOR",  # Attempting to claim authority
    }
    with pytest.raises(BridgeRejectionError, match="authority"):
        bridge_temple_to_proposal(bad_artifact)


# ─── LAW 6: Sovereign fields = rejection ──────────────────────────────────────

def test_bridge_rejects_artifact_with_verdict():
    """Bridge rejects any artifact containing sovereign field 'verdict'."""
    artifact = minimal_artifact()
    artifact["verdict"] = "ADMITTED"  # Injecting sovereign field

    with pytest.raises(BridgeRejectionError, match="sovereign"):
        bridge_temple_to_proposal(artifact)


def test_bridge_rejects_artifact_with_decision():
    """Bridge rejects any artifact containing sovereign field 'decision'."""
    artifact = minimal_artifact()
    artifact["decision"] = "APPROVED"

    with pytest.raises(BridgeRejectionError, match="sovereign"):
        bridge_temple_to_proposal(artifact)


def test_bridge_rejects_artifact_with_ship():
    """Bridge rejects artifact containing 'ship' field."""
    artifact = minimal_artifact()
    artifact["ship"] = True

    with pytest.raises(BridgeRejectionError, match="sovereign"):
        bridge_temple_to_proposal(artifact)


# ─── DETERMINISM ──────────────────────────────────────────────────────────────

def test_bridge_is_deterministic():
    """Same Temple artifact → same transmutation request."""
    artifact = artifact_with_skill_idea()

    request1 = bridge_temple_to_proposal(artifact)
    request2 = bridge_temple_to_proposal(artifact)

    assert sha256_prefixed(request1) == sha256_prefixed(request2)


def test_bridge_output_authority_is_none():
    """Bridge output always has authority='NONE'."""
    artifact = artifact_with_skill_idea()
    request = bridge_temple_to_proposal(artifact)

    assert request["authority"] == "NONE"


# ─── SECOND WITNESS ───────────────────────────────────────────────────────────

def test_bridge_requires_second_witness_for_skill_idea():
    """Skill proposals require second witness before MAYOR routing."""
    artifact = artifact_with_skill_idea()
    request = bridge_temple_to_proposal(artifact)

    assert request["requires_second_witness"] is True


def test_bridge_no_second_witness_for_archival():
    """Pure archival (no candidates, no risks, no tensions) needs no second witness."""
    artifact = minimal_artifact()
    request = bridge_temple_to_proposal(artifact)

    assert request["requires_second_witness"] is False


def test_bridge_requires_second_witness_when_open_risks():
    """Any open HAL friction triggers second witness requirement."""
    artifact = run_temple_exploration(
        session_id="risk_test",
        theme="Risk",
        her_threads=[],
        hal_frictions=[{"friction_id": "f1", "content": "Unresolved question"}],
        tension_map=[],
        center_sketches=[],
        export_candidates=[],
    )
    request = bridge_temple_to_proposal(artifact)

    assert request["requires_second_witness"] is True
    assert len(request["open_risks"]) == 1
