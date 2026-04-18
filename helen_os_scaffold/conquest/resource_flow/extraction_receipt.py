"""
conquest/resource_flow/extraction_receipt.py — EXTRACTION_RECEIPT_V1.

RESOURCE_FLOW_V1 — Constitutional Freeze (RESOURCE_FLOW_LAW_V1.md)

Proof-of-extraction artifact. No lot may exist without one (Invariant I-1).

Receipt pipeline:
    1. Validate extractor_kind in EXTRACTOR_KIND_V1.
    2. Validate terrain_kind is legal for this extractor (EXTRACTOR_TERRAIN_V1).
    3. Compute base yield (EXTRACTOR_YIELD_V1[extractor_kind][terrain_kind]).
    4. Compute adjacency bonus (ADJACENCY_BONUS_V1).
    5. Build legality dict (terrain_compatible, control_compatible, extractor_present).
    6. Compute deterministic receipt_id (SHA256 of canonical inputs incl. adjacency).
    7. Mint exactly ONE ResourceLotV1 with quantity = total_yield (MVP).
    8. Return ExtractionReceiptV1 (frozen, immutable, status="SEALED").

Invariants (per RESOURCE_FLOW_LAW_V1):
    - I-1: No lot without a SEALED receipt.
    - I-2: Exactly one lot per receipt; lot.quantity == receipt.quantity == total_yield.
    - Same canonical inputs → same receipt_id (deterministic).
    - receipt_id format: EX-<first 24 hex chars of sha256(canonical_json)>.
    - lot_id format: LOT-<first 16 hex chars of sha256(receipt_id:000000)>.
    - receipt_type is always "EXTRACTION_RECEIPT_V1" (schema version pin).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from conquest.resource_flow.resource_kinds import (
    ADJACENCY_BONUS_V1,
    EXTRACTOR_KIND_V1,
    EXTRACTOR_OUTPUT_KIND,
    EXTRACTOR_TERRAIN_V1,
    EXTRACTOR_YIELD_V1,
)
from conquest.resource_flow.resource_lot import ResourceLotV1, mint_lot_id

# ── Constants ────────────────────────────────────────────────────────────────

RECEIPT_SCHEMA_VERSION: str = "EXTRACTION_RECEIPT_V1"


# ── Error ────────────────────────────────────────────────────────────────────

class ExtractionError(ValueError):
    """Raised when extraction is illegal.

    Reasons:
        - Unknown extractor_kind
        - terrain_kind not in EXTRACTOR_TERRAIN_V1[extractor_kind]
        - Yield resolves to 0 (guard, should not occur with valid tables)
    """


# ── Receipt dataclass ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ExtractionReceiptV1:
    """
    Immutable proof-of-extraction artifact.

    Fields:
        receipt_type     — always "EXTRACTION_RECEIPT_V1" (was artifact_type)
        status           — "SEALED" | "REJECTED" | "VOID"
        receipt_id       — deterministic SHA256 derivative (incl. adjacency facts)
        house_id         — extracting house (player / faction)
        hex_id           — source hex
        extractor_kind   — FARM | MINE
        resource_kind    — ESSENCE | MATTER | VITALITY
        quantity         — total lots minted this tick (= total_yield; 1 lot for MVP)
        tick             — game tick at time of extraction
        terrain_kind     — terrain at extraction time (renamed from terrain)
        adjacency_facts  — {river_adjacent: bool, coast_adjacent: bool}
        world_hash       — world snapshot hash (provenance anchor)
        input_refs       — tuple of upstream receipt/event ids (empty for extraction)
        output_token_ids — tuple of lot_ids minted (renamed from output_lot_ids)
        legality         — {terrain_compatible, control_compatible, extractor_present}
        yield_breakdown  — {base_yield, adjacency_bonus, policy_bonus, total_yield}
        lots             — tuple of ResourceLotV1 (ONE for MVP)
    """
    receipt_type:     str    # "EXTRACTION_RECEIPT_V1"
    status:           str    # "SEALED"
    receipt_id:       str
    house_id:         str
    hex_id:           str
    extractor_kind:   str
    resource_kind:    str
    quantity:         int    # = total_yield
    tick:             int
    terrain_kind:     str    # renamed from 'terrain'
    adjacency_facts:  dict   # {river_adjacent: bool, coast_adjacent: bool}
    world_hash:       str
    input_refs:       tuple  # upstream receipt ids (empty for raw extraction)
    output_token_ids: tuple  # tuple of lot_id strings
    legality:         dict   # {terrain_compatible, control_compatible, extractor_present}
    yield_breakdown:  dict   # {base_yield, adjacency_bonus, policy_bonus, total_yield}
    lots:             tuple  # tuple[ResourceLotV1, ...] — ONE for MVP

    def to_dict(self) -> dict:
        return {
            "receipt_type":     self.receipt_type,
            "status":           self.status,
            "receipt_id":       self.receipt_id,
            "house_id":         self.house_id,
            "hex_id":           self.hex_id,
            "extractor_kind":   self.extractor_kind,
            "resource_kind":    self.resource_kind,
            "quantity":         self.quantity,
            "tick":             self.tick,
            "terrain_kind":     self.terrain_kind,
            "adjacency_facts":  self.adjacency_facts,
            "world_hash":       self.world_hash,
            "input_refs":       list(self.input_refs),
            "output_token_ids": list(self.output_token_ids),
            "legality":         self.legality,
            "yield_breakdown":  self.yield_breakdown,
        }


# ── Internal helpers ─────────────────────────────────────────────────────────

def _compute_receipt_id(
    house_id:       str,
    hex_id:         str,
    extractor_kind: str,
    tick:           int,
    terrain_kind:   str,
    river_adjacent: bool,
) -> str:
    """
    Deterministic receipt_id: EX-<24 hex chars of sha256(canonical_json)>.

    Includes adjacency flags in the canonical hash so that a river-adjacent
    extraction is distinguishable from the same hex without river adjacency.
    (Per RESOURCE_FLOW_LAW_V1 §VII.)
    """
    canon = json.dumps(
        {
            "extractor_kind": extractor_kind,
            "hex_id":         hex_id,
            "house_id":       house_id,
            "river_adjacent": river_adjacent,
            "terrain_kind":   terrain_kind,
            "tick":           tick,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return f"EX-{digest[:24]}"


def _compute_adjacency_bonus(extractor_kind: str, adjacency_facts: dict) -> int:
    """Sum all applicable adjacency bonuses for this extractor and hex."""
    bonus = 0
    for flag_name, flag_value in adjacency_facts.items():
        if flag_value:
            key = (extractor_kind, flag_name)
            bonus += ADJACENCY_BONUS_V1.get(key, 0)
    return bonus


# ── Public API ────────────────────────────────────────────────────────────────

def extract(
    cell:             dict,
    house_id:         str,
    hex_id:           str,
    extractor_kind:   str,
    tick:             int,
    world_hash:       str,
    river_adjacent:   bool = False,
    coast_adjacent:   bool = False,
) -> ExtractionReceiptV1:
    """
    Attempt resource extraction on a single hex cell.

    Args:
        cell:           Hex cell dict with at least {"terrain": str}.
        house_id:       ID of the extracting house / player.
        hex_id:         Hex identifier (e.g. "H0_0").
        extractor_kind: "FARM" or "MINE".
        tick:           Current game tick (int ≥ 0).
        world_hash:     SHA256 world snapshot hash (provenance anchor).
        river_adjacent: True if this hex is adjacent to a RIVER hex.
        coast_adjacent: True if this hex is adjacent to a COAST hex (bonus reserved).

    Returns:
        ExtractionReceiptV1 with status="SEALED" and exactly ONE minted ResourceLotV1.

    Raises:
        ExtractionError: if extractor_kind is unknown or terrain_kind is illegal.
    """
    # Guard 1: known extractor
    if extractor_kind not in EXTRACTOR_KIND_V1:
        raise ExtractionError(
            f"Unknown extractor_kind {extractor_kind!r}. "
            f"Valid: {sorted(EXTRACTOR_KIND_V1)}"
        )

    # Guard 2: legal terrain
    # Support both "terrain" and "terrain_kind" keys in cell dict
    terrain_kind = cell.get("terrain_kind") or cell.get("terrain", "VOID")
    legal_terrains = EXTRACTOR_TERRAIN_V1[extractor_kind]
    terrain_compatible = terrain_kind in legal_terrains
    if not terrain_compatible:
        raise ExtractionError(
            f"{extractor_kind} cannot operate on terrain {terrain_kind!r}. "
            f"Legal terrains: {sorted(legal_terrains)}"
        )

    # Legality dict (MVP: control_compatible and extractor_present always True)
    legality = {
        "terrain_compatible":  terrain_compatible,
        "control_compatible":  True,   # reserved: no control check in MVP
        "extractor_present":   True,   # reserved: no structure check in MVP
    }

    # Adjacency facts (frozen into receipt)
    adjacency_facts = {
        "river_adjacent": bool(river_adjacent),
        "coast_adjacent": bool(coast_adjacent),
    }

    # Yield computation (per RESOURCE_FLOW_LAW_V1 §III–IV)
    base_yield       = EXTRACTOR_YIELD_V1[extractor_kind].get(terrain_kind, 0)
    adjacency_bonus  = _compute_adjacency_bonus(extractor_kind, adjacency_facts)
    policy_bonus     = 0  # MVP: always 0
    total_yield      = base_yield + adjacency_bonus + policy_bonus

    # Guard 3: positive yield (should never trigger with valid tables + legal terrain)
    if total_yield <= 0:
        raise ExtractionError(
            f"{extractor_kind} on {terrain_kind!r} yields {total_yield} (expected > 0)"
        )

    yield_breakdown = {
        "base_yield":      base_yield,
        "adjacency_bonus": adjacency_bonus,
        "policy_bonus":    policy_bonus,
        "total_yield":     total_yield,
    }

    # Compute provenance
    resource_kind = EXTRACTOR_OUTPUT_KIND[extractor_kind]
    rid = _compute_receipt_id(
        house_id, hex_id, extractor_kind, tick, terrain_kind, river_adjacent
    )

    # Mint exactly ONE lot (Invariant I-2: quantity conservation, MVP)
    lot = ResourceLotV1(
        lot_id=mint_lot_id(rid, 0),
        resource_kind=resource_kind,
        quantity=total_yield,           # one lot carries full yield
        owner_house_id=house_id,
        current_hex_id=hex_id,
        source_receipt_id=rid,
        source_hex_id=hex_id,           # immutable provenance
        extraction_tick=tick,           # immutable provenance
        world_hash=world_hash,          # immutable provenance
        status="ACTIVE",                # renamed from "STORED"
    )
    lots = (lot,)

    return ExtractionReceiptV1(
        receipt_type=RECEIPT_SCHEMA_VERSION,
        status="SEALED",
        receipt_id=rid,
        house_id=house_id,
        hex_id=hex_id,
        extractor_kind=extractor_kind,
        resource_kind=resource_kind,
        quantity=total_yield,
        tick=tick,
        terrain_kind=terrain_kind,
        adjacency_facts=adjacency_facts,
        world_hash=world_hash,
        input_refs=(),
        output_token_ids=tuple(lot.lot_id for lot in lots),
        legality=legality,
        yield_breakdown=yield_breakdown,
        lots=lots,
    )
