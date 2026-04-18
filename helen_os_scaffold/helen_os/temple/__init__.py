"""
helen_os/temple/ — TEMPLE OS: Quarantined cognitive workspace

Three-layer architecture (from TEMPLE_MODE_POLICY_V1):

1. WILD LAYER — Generate, combine, provoke, reframe
   Outputs: TEMPLE_SESSION_V1, ORACLE_SPREAD_V1, WILD_SYNTHESIS_NOTE_V1

2. REVIEW LAYER — Classify, quarantine, score, extract candidates
   Outputs: WILD_INGESTION_V1, RISK_CLASSIFICATION_V1, TEMPLE_REVIEW_PACKET_V1

3. TRANSMUTATION LAYER — Strip mystification, convert to typed claims
   Outputs: TRANSMUTE_FOR_SHIP_V1, CLAIM_GRAPH_V1, RESEARCH_CLAIM_V1

Invariant: Nothing leaves TEMPLE without transmutation.
Authority: Zero default kernel authority. Everything is WILD until proven.
"""

from helen_os.temple.wild_ingestion import (
    MaterialType,
    QuarantineLevel,
    UILabel,
    WildIngestRecord,
    WildIngestionClassifier,
    classify_material,
)

__all__ = [
    "MaterialType",
    "QuarantineLevel",
    "UILabel",
    "WildIngestRecord",
    "WildIngestionClassifier",
    "classify_material",
]
