"""
conquest/resource_flow — RESOURCE_FLOW_V1 extractor layer.

Constitutional Freeze: RESOURCE_FLOW_LAW_V1.md

Inscription Path 1: DEFINE THE EXTRACTORS
    - FARM  → ESSENCE (agricultural; PLAIN + COAST terrain)
    - MINE  → MATTER  (mineral; HILL + MOUNTAIN terrain)
    - VITALITY vocabulary reserved for Path 3 (water / movement)

Constitutional invariants:
    - I-1: No lot without a SEALED receipt.
    - I-2: Quantity conservation — one lot per receipt, quantity = total_yield (MVP).
    - All receipt_ids and lot_ids are deterministic (SHA256 of canonical inputs).
    - ExtractionReceiptV1 and ResourceLotV1 are frozen (immutable once minted).
"""
from __future__ import annotations

from conquest.resource_flow.resource_kinds import (
    ADJACENCY_BONUS_V1,
    EXTRACTOR_KIND_V1,
    EXTRACTOR_OUTPUT_KIND,
    EXTRACTOR_TERRAIN_V1,
    EXTRACTOR_YIELD_V1,
    LOT_STATUS_V1,
    RECEIPT_STATUS_V1,
    RESOURCE_KIND_V1,
)
from conquest.resource_flow.resource_lot import (
    ResourceLotV1,
    mint_lot_id,
)
from conquest.resource_flow.extraction_receipt import (
    RECEIPT_SCHEMA_VERSION,
    ExtractionError,
    ExtractionReceiptV1,
    extract,
)

__all__ = [
    # Vocabulary
    "RESOURCE_KIND_V1",
    "EXTRACTOR_KIND_V1",
    "EXTRACTOR_OUTPUT_KIND",
    "EXTRACTOR_TERRAIN_V1",
    "EXTRACTOR_YIELD_V1",
    "LOT_STATUS_V1",
    "RECEIPT_STATUS_V1",
    "ADJACENCY_BONUS_V1",
    "RECEIPT_SCHEMA_VERSION",
    # Data objects
    "ResourceLotV1",
    "ExtractionReceiptV1",
    # Functions
    "mint_lot_id",
    "extract",
    # Errors
    "ExtractionError",
]
