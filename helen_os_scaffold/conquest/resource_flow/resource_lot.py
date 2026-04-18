"""
conquest/resource_flow/resource_lot.py — RESOURCE_LOT_V1 token.

RESOURCE_FLOW_V1 — Constitutional Freeze (RESOURCE_FLOW_LAW_V1.md)

Every lot must trace back to exactly one ExtractionReceiptV1 (Invariant I-1).

Schema (RESOURCE_LOT_V1):
    lot_id             — deterministic; minted from source_receipt_id + index
    resource_kind      — ESSENCE | MATTER | VITALITY
    quantity           — positive integer (= total_yield for MVP one-lot receipts)
    owner_house_id     — non-optional string (house that owns this lot)
    current_hex_id     — hex where the lot currently resides
    source_receipt_id  — the ExtractionReceiptV1 that minted this lot
    source_hex_id      — hex where extraction occurred (immutable provenance)
    extraction_tick    — game tick at extraction time (immutable provenance)
    world_hash         — world snapshot hash at extraction time (provenance anchor)
    status             — ACTIVE | RESERVED | IN_TRANSIT | CONSUMED | EXHAUSTED | VOID

Invariants:
    - Frozen dataclass; immutable once minted.
    - resource_kind must be in RESOURCE_KIND_V1.
    - quantity > 0 always.
    - status must be in LOT_STATUS_V1.
    - lot_id is a deterministic SHA256 derivative of (source_receipt_id, index).
    - owner_house_id is a non-optional string (empty string not permitted).
    - source_hex_id is immutable provenance; equals hex at time of extraction.
    - extraction_tick is immutable provenance; equals tick at time of extraction.
    - world_hash is immutable provenance; equals world snapshot at time of extraction.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from conquest.resource_flow.resource_kinds import LOT_STATUS_V1, RESOURCE_KIND_V1

# ── Data class ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ResourceLotV1:
    """A single tokenized resource lot. Immutable once minted."""

    lot_id:            str
    resource_kind:     str   # ESSENCE | MATTER | VITALITY
    quantity:          int   # positive integer (= total_yield for MVP)
    owner_house_id:    str   # non-optional (was Optional[str] in Move 11)
    current_hex_id:    str
    source_receipt_id: str
    source_hex_id:     str   # immutable provenance: hex at extraction time
    extraction_tick:   int   # immutable provenance: tick at extraction time
    world_hash:        str   # immutable provenance: world snapshot hash
    status:            str = "ACTIVE"  # changed from "STORED" (Move 11)

    def __post_init__(self) -> None:
        if self.resource_kind not in RESOURCE_KIND_V1:
            raise ValueError(
                f"Unknown resource_kind {self.resource_kind!r}. "
                f"Valid: {sorted(RESOURCE_KIND_V1)}"
            )
        if self.quantity <= 0:
            raise ValueError(f"quantity must be > 0, got {self.quantity}")
        if not self.owner_house_id:
            raise ValueError("owner_house_id must be a non-empty string")
        if self.status not in LOT_STATUS_V1:
            raise ValueError(
                f"Unknown status {self.status!r}. Valid: {sorted(LOT_STATUS_V1)}"
            )

    def to_dict(self) -> dict:
        return {
            "lot_id":            self.lot_id,
            "resource_kind":     self.resource_kind,
            "quantity":          self.quantity,
            "owner_house_id":    self.owner_house_id,
            "current_hex_id":    self.current_hex_id,
            "source_receipt_id": self.source_receipt_id,
            "source_hex_id":     self.source_hex_id,
            "extraction_tick":   self.extraction_tick,
            "world_hash":        self.world_hash,
            "status":            self.status,
        }


# ── Lot-ID minting ──────────────────────────────────────────────────────────

def mint_lot_id(source_receipt_id: str, index: int) -> str:
    """
    Deterministic lot_id from (source_receipt_id, index).

    Format: LOT-<first 16 hex chars of sha256(source_receipt_id:index)>

    Invariant: same (source_receipt_id, index) → same lot_id, always.

    MVP: index is always 0 (one lot per receipt per RESOURCE_FLOW_LAW_V1 §V I-2).
    """
    digest = hashlib.sha256(
        f"{source_receipt_id}:{index:06d}".encode()
    ).hexdigest()[:16]
    return f"LOT-{digest}"
