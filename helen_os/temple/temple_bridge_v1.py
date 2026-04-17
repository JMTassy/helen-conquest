"""TEMPLE_BRIDGE_V1: Transmutation surface from TEMPLE exploration to Mayor gateway.

Single responsibility:
- Accept TEMPLE_EXPLORATION_V1 artifact
- Validate provenance (source must have authority=NONE, no sovereign fields)
- Extract typed proposal packet from export_candidates
- Hash source artifact for chain integrity
- Emit TEMPLE_TRANSMUTATION_REQUEST_V1 (authority=NONE)

Bridge Laws (frozen):
1. Bridge may reformat, never admit
2. Bridge may compress, never verdict
3. Bridge may extract candidate claims, never assert truth
4. Every output retains exact provenance to the Temple artifact
5. Missing provenance = rejection
6. Anything claiming authority in source = rejection
"""
from __future__ import annotations

from typing import Any

from helen_os.governance.canonical import sha256_prefixed

# Frozen set of sovereign fields that must never appear in a TEMPLE artifact
_SOVEREIGN_FIELDS = frozenset({
    "verdict",
    "state_mutation",
    "ship",
    "no_ship",
    "decision",
    "receipt_claimed",
    "authorized_by",
    "ledger_pointer",
    "receipt_sha256",
    "entry_hash",
    "prev_entry_hash",
})

# Map from export_candidate type to bridge proposal_kind
_PROPOSAL_KIND_MAP = {
    "SKILL_IDEA": "skill_proposal",
    "CLAIM_CANDIDATE": "claim_submission",
    "ARTIFACT_SKETCH": "artifact_proposal",
    "NOTE": "informational",
    "TRACE": "archival",
}

# Proposal kinds that require a second witness (non-trivial claims)
_HIGH_STAKES_KINDS = frozenset({"skill_proposal", "claim_submission", "artifact_proposal"})


class BridgeRejectionError(ValueError):
    """Raised when the bridge cannot process an artifact due to provenance failure."""
    pass


def _validate_temple_artifact(artifact: dict[str, Any]) -> None:
    """
    Validate that the artifact is a legitimate TEMPLE_EXPLORATION_V1.

    Raises BridgeRejectionError on any violation:
    - Wrong schema_name
    - authority != "NONE"
    - Presence of any sovereign field
    """
    if artifact.get("schema_name") != "TEMPLE_EXPLORATION_V1":
        raise BridgeRejectionError(
            f"Bridge only accepts TEMPLE_EXPLORATION_V1. "
            f"Got: {artifact.get('schema_name', 'MISSING')}"
        )

    if artifact.get("authority") != "NONE":
        raise BridgeRejectionError(
            f"Bridge rejects artifacts claiming authority != NONE. "
            f"Got: {artifact.get('authority', 'MISSING')}"
        )

    found_sovereign = _SOVEREIGN_FIELDS & set(artifact.keys())
    if found_sovereign:
        raise BridgeRejectionError(
            f"Bridge rejects artifact with sovereign fields: {sorted(found_sovereign)}"
        )


def _extract_candidate_claims(export_candidates: list[dict]) -> list[dict]:
    """
    Extract candidate claims from export_candidates.

    Preserves content; never asserts truth. Labels each claim as pre-institutional.
    """
    claims = []
    for candidate in export_candidates:
        claims.append({
            "claim_id": candidate["candidate_id"],
            "claim_type": candidate["candidate_type"],
            "content": candidate["content"],
            "status": "PRE_INSTITUTIONAL",  # Never admitted, only proposed
            "proposal_kind": _PROPOSAL_KIND_MAP.get(candidate["candidate_type"], "archival"),
        })
    return claims


def _extract_open_risks(hal_frictions: list[dict]) -> list[dict]:
    """Extract open risks from HAL frictions."""
    return [
        {
            "risk_id": friction["friction_id"],
            "description": friction["content"],
            "targets": friction.get("targets", []),
            "status": "UNRESOLVED",
        }
        for friction in hal_frictions
    ]


def _classify_proposal_kind(candidate_claims: list[dict]) -> str:
    """
    Classify the overall proposal kind from extracted claims.

    Priority: skill_proposal > claim_submission > artifact_proposal > informational > archival
    """
    priority = ["skill_proposal", "claim_submission", "artifact_proposal", "informational", "archival"]
    kinds_present = {c["proposal_kind"] for c in candidate_claims}

    for kind in priority:
        if kind in kinds_present:
            return kind

    return "archival"  # Default: no export candidates


def _requires_second_witness(
    proposal_kind: str,
    open_risks: list[dict],
    tension_map: list[dict],
) -> bool:
    """
    Determine if this transmutation requires a second witness before MAYOR routing.

    True when:
    - Proposal kind is high-stakes (skill_proposal, claim_submission, artifact_proposal)
    - OR there are unresolved open risks
    - OR there are unresolved tensions
    """
    if proposal_kind in _HIGH_STAKES_KINDS:
        return True
    if open_risks:
        return True
    if tension_map:
        return True
    return False


def bridge_temple_to_proposal(
    temple_artifact: dict[str, Any],
) -> dict[str, Any]:
    """
    Transform TEMPLE_EXPLORATION_V1 into TEMPLE_TRANSMUTATION_REQUEST_V1.

    This is the only lawful path from TEMPLE exploration to MAYOR-routable proposal.

    Bridge Laws enforced here:
    - Validates provenance (rejects on failure)
    - Hashes source artifact (chain integrity)
    - Extracts candidate claims (never asserts truth)
    - Preserves open risks (HAL frictions)
    - Never emits verdict, decision, or admission
    - Returns authority="NONE" always

    Args:
        temple_artifact: A validated TEMPLE_EXPLORATION_V1 artifact

    Returns:
        TEMPLE_TRANSMUTATION_REQUEST_V1 dict

    Raises:
        BridgeRejectionError: If artifact fails provenance validation
    """
    # Law 5: Validate provenance first — reject on failure
    _validate_temple_artifact(temple_artifact)

    # Law 4: Hash source for immutable provenance chain
    source_payload_hash = sha256_prefixed(temple_artifact)
    source_artifact_id = temple_artifact["session_id"]

    # Extract candidate claims from export_candidates
    candidate_claims = _extract_candidate_claims(
        temple_artifact.get("export_candidates", [])
    )

    # Extract open risks from HAL frictions
    open_risks = _extract_open_risks(
        temple_artifact.get("hal_frictions", [])
    )

    # Classify proposal kind from claims
    proposal_kind = _classify_proposal_kind(candidate_claims)

    # Determine if second witness required
    requires_second_witness = _requires_second_witness(
        proposal_kind,
        open_risks,
        temple_artifact.get("tension_map", []),
    )

    # Build transmutation request (Law 1: reformat only, never admit)
    return {
        "schema_name": "TEMPLE_TRANSMUTATION_REQUEST_V1",
        "schema_version": "1.0.0",
        "source_artifact_id": source_artifact_id,
        "source_schema": "TEMPLE_EXPLORATION_V1",
        "source_payload_hash": source_payload_hash,
        "bridge_version": "1.0.0",
        "theme": temple_artifact["theme"],
        "proposal_kind": proposal_kind,
        "candidate_claims": candidate_claims,
        "open_risks": open_risks,
        "tension_summary": [
            {
                "tension_id": t["tension_id"],
                "pole_a": t["pole_a"],
                "pole_b": t["pole_b"],
            }
            for t in temple_artifact.get("tension_map", [])
        ],
        "requires_second_witness": requires_second_witness,
        # Law 1-3: Never verdict, never admit — bridge output is always pre-institutional
        "authority": "NONE",
        "bridge_status": "PENDING_MAYOR_REVIEW",
    }
