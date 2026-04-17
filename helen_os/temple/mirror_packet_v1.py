"""TEMPLE_MIRROR_PACKET_V1 — Minimal archivable mirror reading.

Constitution:
- One motif. One tension. One sketch. One limit.
- Full provenance (source_session_id, source_hash, protocol_version).
- Non-sovereign: authority=NONE, mirror_derived=True, export=NONE.
- Three HAL tests explicitly applied before archiving.

Law:
- The Mirror may reveal. It may not decide.
- Le Miroir n'est utile que si la coupe reste possible devant lui.
"""
from __future__ import annotations
from typing import Literal
from helen_os.governance.canonical import sha256_prefixed


EvidenceStrength = Literal["weak", "moderate", "strong"]
TestResult = Literal["pass", "fail", "weak"]
MythRisk = Literal["low", "medium", "high"]


def create_mirror_packet(
    *,
    packet_id: str,
    source_session_id: str,
    source_artifact: dict,
    motif_label: str,
    evidence_strength: EvidenceStrength,
    tension_pole_a: str,
    tension_pole_b: str,
    tension_description: str,
    center_sketch: str,
    limit: str,
    mythologization_risk: MythRisk,
    test_recurrence: TestResult,
    test_compression: TestResult,
    test_resistance: TestResult,
    notes: str | None = None,
) -> dict:
    """
    Assemble a TEMPLE_MIRROR_PACKET_V1.

    Cardinality caps enforced by schema:
      max_motifs: 1 | max_tensions: 1 | max_sketches: 1 | max_limits: 1

    Provenance:
      source_hash = sha256_prefixed(source_artifact) — computed here, not supplied.

    Returns dict with authority=NONE, mirror_derived=True, export=NONE.
    Does NOT call reducer, bridge, ledger, or state updater.
    """
    source_hash = sha256_prefixed(source_artifact)

    packet = {
        "schema_name": "TEMPLE_MIRROR_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id": packet_id,
        "source_session_id": source_session_id,
        "source_hash": source_hash,
        "protocol_version": "TEMPLE_MIRROR_PROTOCOL_V1",
        "authority": "NONE",
        "mirror_derived": True,
        "motif": {
            "label": motif_label,
            "evidence_strength": evidence_strength,
        },
        "tension": {
            "pole_a": tension_pole_a,
            "pole_b": tension_pole_b,
            "description": tension_description,
        },
        "center_sketch": center_sketch,
        "limit": limit,
        "mythologization_risk": mythologization_risk,
        "three_tests_applied": {
            "recurrence": test_recurrence,
            "compression": test_compression,
            "resistance": test_resistance,
        },
        "export": "NONE",
        "bridge_status": "NOT_SUBMITTED",
    }

    if notes:
        packet["notes"] = notes

    return packet
