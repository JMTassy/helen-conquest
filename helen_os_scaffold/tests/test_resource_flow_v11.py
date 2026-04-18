"""
tests/test_resource_flow_v11.py — RESOURCE_FLOW_V1 Constitutional Freeze

Tests canonical RESOURCE_FLOW_LAW_V1.md invariants.

Key schema changes from Move 11 → V1 canonical:
    - FARM terrain: {PLAIN, COAST} only (FOREST removed; reserved for VITALITY)
    - FARM/COAST yield: 1 → 2
    - MINE/HILL yield:  2 → 3
    - LOT status vocabulary: {STORED,...} → {ACTIVE, RESERVED, IN_TRANSIT,
                                              CONSUMED, EXHAUSTED, VOID}
    - New lot fields: source_hex_id, extraction_tick, world_hash
    - owner_house_id: non-optional str
    - New receipt fields: receipt_type (was artifact_type), status,
                          terrain_kind (was terrain), adjacency_facts,
                          legality, yield_breakdown, input_refs, output_token_ids
    - Lot minting: N lots of quantity=1 → ONE lot of quantity=total_yield (I-2)
    - Adjacency bonus: FARM + river_adjacent → +1

Test Groups:
    RF01  RESOURCE_KIND_V1 has exactly 3 kinds
    RF02  EXTRACTOR_KIND_V1 has exactly 2 kinds (FARM, MINE)
    RF03  FARM legal terrain set is {PLAIN, COAST}
    RF04  MINE legal terrain set is {HILL, MOUNTAIN}
    RF05  FARM output kind is ESSENCE
    RF06  MINE output kind is MATTER
    RF07  FARM on PLAIN yields 3 (base)
    RF08  FARM on COAST yields 2 (base)
    RF09  MINE on HILL yields 3 (base)
    RF10  MINE on MOUNTAIN yields 4 (base)
    RF11  FARM on PLAIN + river_adjacent yields 4 (base + adjacency bonus)
    RF12  FARM on FOREST raises ExtractionError (FOREST no longer legal)
    RF13  FARM on MOUNTAIN raises ExtractionError (wrong terrain)
    RF14  MINE on PLAIN raises ExtractionError (wrong terrain)
    RF15  MINE on VOID raises ExtractionError (void terrain)
    RF16  Unknown extractor raises ExtractionError
    RF17  Receipt determinism: same inputs → same receipt_id + lot_ids
    RF18  Different tick → different receipt_id
    RF19  Different hex → different receipt_id
    RF20  Different river_adjacent → different receipt_id
    RF21  I-1: All lots reference their source receipt (SEALED)
    RF22  I-2: Exactly one lot per receipt, quantity = total_yield
    RF23  receipt.to_dict() has receipt_type == EXTRACTION_RECEIPT_V1
    RF24  receipt.to_dict() status == "SEALED"
    RF25  receipt.to_dict() has output_token_ids length == 1
    RF26  receipt.to_dict() has yield_breakdown with correct keys
    RF27  receipt.to_dict() has legality with all True for legal extraction
    RF28  receipt.to_dict() has adjacency_facts frozen correctly
    RF29  receipt.to_dict() has terrain_kind (not terrain)
    RF30  ResourceLotV1 rejects invalid resource_kind
    RF31  ResourceLotV1 rejects zero quantity
    RF32  ResourceLotV1 rejects negative quantity
    RF33  ResourceLotV1 is frozen (immutable)
    RF34  ResourceLotV1 rejects empty owner_house_id
    RF35  mint_lot_id is deterministic (same inputs → same id)
    RF36  mint_lot_id differs with different index
    RF37  lot.to_dict() has all required fields incl. source_hex_id, extraction_tick, world_hash
    RF38  lot default status is ACTIVE (not STORED)
    RF39  lot.resource_kind matches extractor output
    RF40  lot.quantity == receipt.quantity (I-2 verification)
    RF41  LOT_STATUS_V1 has 6 entries
    RF42  RECEIPT_STATUS_V1 has 3 entries
    RF43  VITALITY is in RESOURCE_KIND_V1 vocabulary (reserved)
    RF44  ADJACENCY_BONUS_V1 has (FARM, river_adjacent) → 1
    RF45  lot.source_hex_id equals the extraction hex
    RF46  lot.extraction_tick equals the extraction tick
    RF47  lot.world_hash equals the provided world_hash
    RF48  lot.owner_house_id matches the extracting house
    RF49  Different house → different receipt_id
    RF50  lot_ids are unique across receipts from different ticks
"""
from __future__ import annotations

import pytest
import os
import sys

# ── sys.path bootstrap ──────────────────────────────────────────────────────
_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_SCAFFOLD_ROOT))

from conquest.resource_flow import (
    RESOURCE_KIND_V1,
    EXTRACTOR_KIND_V1,
    EXTRACTOR_OUTPUT_KIND,
    EXTRACTOR_TERRAIN_V1,
    EXTRACTOR_YIELD_V1,
    LOT_STATUS_V1,
    RECEIPT_STATUS_V1,
    ADJACENCY_BONUS_V1,
    ResourceLotV1,
    ExtractionReceiptV1,
    ExtractionError,
    extract,
    mint_lot_id,
    RECEIPT_SCHEMA_VERSION,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _cell(terrain: str) -> dict:
    """Minimal hex cell with given terrain (uses 'terrain' key for compat)."""
    return {"terrain": terrain, "hex_id": "H0_0"}


_WORLD_HASH = "sha256:" + "a" * 64
_HOUSE      = "HOUSE_ALPHA"
_HEX        = "H3_2"
_TICK       = 42


def _do_extract(
    terrain: str,
    extractor: str,
    river_adjacent: bool = False,
    coast_adjacent: bool = False,
    **kwargs,
) -> ExtractionReceiptV1:
    return extract(
        cell=_cell(terrain),
        house_id=kwargs.get("house_id", _HOUSE),
        hex_id=kwargs.get("hex_id", _HEX),
        extractor_kind=extractor,
        tick=kwargs.get("tick", _TICK),
        world_hash=kwargs.get("world_hash", _WORLD_HASH),
        river_adjacent=river_adjacent,
        coast_adjacent=coast_adjacent,
    )


# ── RF01–RF06: Vocabulary invariants ────────────────────────────────────────

class TestVocabulary:
    def test_rf01_resource_kind_has_3_entries(self):
        assert len(RESOURCE_KIND_V1) == 3
        assert RESOURCE_KIND_V1 == {"ESSENCE", "MATTER", "VITALITY"}

    def test_rf02_extractor_kind_has_2_entries(self):
        assert len(EXTRACTOR_KIND_V1) == 2
        assert EXTRACTOR_KIND_V1 == {"FARM", "MINE"}

    def test_rf03_farm_legal_terrain(self):
        # FOREST removed — only PLAIN and COAST
        assert EXTRACTOR_TERRAIN_V1["FARM"] == frozenset({"PLAIN", "COAST"})
        assert "FOREST" not in EXTRACTOR_TERRAIN_V1["FARM"]

    def test_rf04_mine_legal_terrain(self):
        assert EXTRACTOR_TERRAIN_V1["MINE"] == frozenset({"HILL", "MOUNTAIN"})

    def test_rf05_farm_output_is_essence(self):
        assert EXTRACTOR_OUTPUT_KIND["FARM"] == "ESSENCE"

    def test_rf06_mine_output_is_matter(self):
        assert EXTRACTOR_OUTPUT_KIND["MINE"] == "MATTER"

    def test_rf41_lot_status_has_6_entries(self):
        assert len(LOT_STATUS_V1) == 6
        assert LOT_STATUS_V1 == {
            "ACTIVE", "RESERVED", "IN_TRANSIT", "CONSUMED", "EXHAUSTED", "VOID"
        }

    def test_rf42_receipt_status_has_3_entries(self):
        assert len(RECEIPT_STATUS_V1) == 3
        assert RECEIPT_STATUS_V1 == {"SEALED", "REJECTED", "VOID"}

    def test_rf43_vitality_in_vocabulary(self):
        assert "VITALITY" in RESOURCE_KIND_V1

    def test_rf44_adjacency_bonus_farm_river(self):
        assert ADJACENCY_BONUS_V1[("FARM", "river_adjacent")] == 1


# ── RF07–RF11: Yield counts ──────────────────────────────────────────────────

class TestYieldCounts:
    def test_rf07_farm_plain_yields_3(self):
        receipt = _do_extract("PLAIN", "FARM")
        assert receipt.quantity == 3
        assert receipt.yield_breakdown["base_yield"] == 3
        assert receipt.yield_breakdown["total_yield"] == 3

    def test_rf08_farm_coast_yields_2(self):
        # Changed: was 1 in Move 11, now 2 per canonical spec
        receipt = _do_extract("COAST", "FARM")
        assert receipt.quantity == 2
        assert receipt.yield_breakdown["base_yield"] == 2
        assert receipt.yield_breakdown["total_yield"] == 2

    def test_rf09_mine_hill_yields_3(self):
        # Changed: was 2 in Move 11, now 3 per canonical spec
        receipt = _do_extract("HILL", "MINE")
        assert receipt.quantity == 3
        assert receipt.yield_breakdown["base_yield"] == 3
        assert receipt.yield_breakdown["total_yield"] == 3

    def test_rf10_mine_mountain_yields_4(self):
        receipt = _do_extract("MOUNTAIN", "MINE")
        assert receipt.quantity == 4
        assert receipt.yield_breakdown["base_yield"] == 4
        assert receipt.yield_breakdown["total_yield"] == 4

    def test_rf11_farm_plain_river_adjacent_yields_4(self):
        # Adjacency bonus: FARM + river_adjacent → +1
        receipt = _do_extract("PLAIN", "FARM", river_adjacent=True)
        assert receipt.quantity == 4
        assert receipt.yield_breakdown["base_yield"] == 3
        assert receipt.yield_breakdown["adjacency_bonus"] == 1
        assert receipt.yield_breakdown["total_yield"] == 4

    def test_rf11_farm_coast_river_adjacent_yields_3(self):
        receipt = _do_extract("COAST", "FARM", river_adjacent=True)
        assert receipt.quantity == 3
        assert receipt.yield_breakdown["base_yield"] == 2
        assert receipt.yield_breakdown["adjacency_bonus"] == 1
        assert receipt.yield_breakdown["total_yield"] == 3

    def test_rf11_mine_river_adjacent_no_bonus(self):
        # MINE gets no river bonus per ADJACENCY_BONUS_V1
        receipt_base = _do_extract("HILL", "MINE", river_adjacent=False)
        receipt_river = _do_extract("HILL", "MINE", river_adjacent=True)
        assert receipt_river.quantity == receipt_base.quantity
        assert receipt_river.yield_breakdown["adjacency_bonus"] == 0

    def test_rf11_policy_bonus_is_zero_mvp(self):
        receipt = _do_extract("PLAIN", "FARM")
        assert receipt.yield_breakdown["policy_bonus"] == 0

    def test_rf11_mine_mountain_yields_more_than_hill(self):
        hill     = _do_extract("HILL", "MINE")
        mountain = _do_extract("MOUNTAIN", "MINE")
        assert mountain.quantity > hill.quantity


# ── RF12–RF16: Illegal extractions ──────────────────────────────────────────

class TestIllegalExtraction:
    def test_rf12_farm_on_forest_raises(self):
        # FOREST no longer legal for FARM (removed in canonical spec)
        with pytest.raises(ExtractionError, match="FARM"):
            _do_extract("FOREST", "FARM")

    def test_rf13_farm_on_mountain_raises(self):
        with pytest.raises(ExtractionError, match="FARM"):
            _do_extract("MOUNTAIN", "FARM")

    def test_rf14_mine_on_plain_raises(self):
        with pytest.raises(ExtractionError, match="MINE"):
            _do_extract("PLAIN", "MINE")

    def test_rf15_mine_on_void_raises(self):
        with pytest.raises(ExtractionError, match="MINE"):
            _do_extract("VOID", "MINE")

    def test_rf15_farm_on_sea_raises(self):
        with pytest.raises(ExtractionError, match="FARM"):
            _do_extract("SEA", "FARM")

    def test_rf15_farm_on_desert_raises(self):
        with pytest.raises(ExtractionError, match="FARM"):
            _do_extract("DESERT", "FARM")

    def test_rf16_unknown_extractor_raises(self):
        with pytest.raises(ExtractionError, match="CANNON"):
            _do_extract("PLAIN", "CANNON")

    def test_rf16_empty_extractor_raises(self):
        with pytest.raises(ExtractionError):
            _do_extract("PLAIN", "")

    def test_rf15_mine_on_coast_raises(self):
        with pytest.raises(ExtractionError, match="MINE"):
            _do_extract("COAST", "MINE")


# ── RF17–RF20: Determinism ───────────────────────────────────────────────────

class TestDeterminism:
    def test_rf17_same_inputs_same_receipt_id(self):
        r1 = _do_extract("PLAIN", "FARM")
        r2 = _do_extract("PLAIN", "FARM")
        assert r1.receipt_id == r2.receipt_id

    def test_rf17_same_inputs_same_lot_ids(self):
        r1 = _do_extract("PLAIN", "FARM")
        r2 = _do_extract("PLAIN", "FARM")
        assert r1.output_token_ids == r2.output_token_ids

    def test_rf18_different_tick_different_receipt(self):
        r1 = _do_extract("PLAIN", "FARM", tick=1)
        r2 = _do_extract("PLAIN", "FARM", tick=2)
        assert r1.receipt_id != r2.receipt_id

    def test_rf19_different_hex_different_receipt(self):
        r1 = _do_extract("PLAIN", "FARM", hex_id="H0_0")
        r2 = _do_extract("PLAIN", "FARM", hex_id="H1_1")
        assert r1.receipt_id != r2.receipt_id

    def test_rf20_different_river_adjacent_different_receipt(self):
        # Adjacency is included in receipt_id canonical hash
        r1 = _do_extract("PLAIN", "FARM", river_adjacent=False)
        r2 = _do_extract("PLAIN", "FARM", river_adjacent=True)
        assert r1.receipt_id != r2.receipt_id

    def test_rf49_different_house_different_receipt(self):
        r1 = _do_extract("PLAIN", "FARM", house_id="HOUSE_A")
        r2 = _do_extract("PLAIN", "FARM", house_id="HOUSE_B")
        assert r1.receipt_id != r2.receipt_id


# ── RF21–RF22: Constitutional Invariants I-1 and I-2 ────────────────────────

class TestConstitutionalInvariants:
    def test_rf21_i1_all_lots_reference_sealed_receipt(self):
        """I-1: No lot without a SEALED receipt."""
        receipt = _do_extract("PLAIN", "FARM")
        assert receipt.status == "SEALED"
        for lot in receipt.lots:
            assert lot.source_receipt_id == receipt.receipt_id

    def test_rf22_i2_exactly_one_lot_per_receipt(self):
        """I-2 MVP: exactly one lot per receipt."""
        receipt = _do_extract("MOUNTAIN", "MINE")
        assert len(receipt.lots) == 1
        assert len(receipt.output_token_ids) == 1

    def test_rf22_i2_lot_quantity_equals_receipt_quantity(self):
        """I-2: lot.quantity == receipt.quantity == total_yield."""
        receipt = _do_extract("PLAIN", "FARM")
        assert receipt.lots[0].quantity == receipt.quantity
        assert receipt.quantity == receipt.yield_breakdown["total_yield"]

    def test_rf22_i2_mine_mountain_one_lot_quantity_4(self):
        receipt = _do_extract("MOUNTAIN", "MINE")
        assert len(receipt.lots) == 1
        assert receipt.lots[0].quantity == 4
        assert receipt.quantity == 4

    def test_rf21_lots_reference_correct_hex(self):
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.current_hex_id == _HEX

    def test_rf21_lots_owner_matches_house(self):
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.owner_house_id == _HOUSE

    def test_rf50_lot_ids_unique_across_receipts(self):
        """Different receipt → different lot_ids (I-3 namespace uniqueness)."""
        r1 = _do_extract("PLAIN", "FARM", tick=1)
        r2 = _do_extract("PLAIN", "FARM", tick=2)
        ids_1 = {lot.lot_id for lot in r1.lots}
        ids_2 = {lot.lot_id for lot in r2.lots}
        assert ids_1.isdisjoint(ids_2), "lot_ids collide across receipts"


# ── RF23–RF29: Receipt schema (to_dict) ─────────────────────────────────────

class TestReceiptSchema:
    def test_rf23_receipt_type_correct(self):
        receipt = _do_extract("PLAIN", "FARM")
        d = receipt.to_dict()
        assert d["receipt_type"] == RECEIPT_SCHEMA_VERSION
        assert d["receipt_type"] == "EXTRACTION_RECEIPT_V1"

    def test_rf24_status_is_sealed(self):
        receipt = _do_extract("PLAIN", "FARM")
        assert receipt.status == "SEALED"
        assert receipt.to_dict()["status"] == "SEALED"

    def test_rf25_output_token_ids_length_is_1(self):
        """MVP: exactly one token per receipt (I-2)."""
        receipt = _do_extract("MOUNTAIN", "MINE")
        d = receipt.to_dict()
        assert len(d["output_token_ids"]) == 1

    def test_rf26_yield_breakdown_has_all_keys(self):
        receipt = _do_extract("PLAIN", "FARM")
        d = receipt.to_dict()
        assert "yield_breakdown" in d
        for key in ("base_yield", "adjacency_bonus", "policy_bonus", "total_yield"):
            assert key in d["yield_breakdown"], f"Missing yield_breakdown key: {key!r}"

    def test_rf27_legality_all_true_for_legal_extraction(self):
        receipt = _do_extract("PLAIN", "FARM")
        d = receipt.to_dict()
        assert "legality" in d
        assert d["legality"]["terrain_compatible"] is True
        assert d["legality"]["control_compatible"] is True
        assert d["legality"]["extractor_present"] is True

    def test_rf28_adjacency_facts_frozen_correctly(self):
        receipt = _do_extract("PLAIN", "FARM", river_adjacent=True)
        d = receipt.to_dict()
        assert "adjacency_facts" in d
        assert d["adjacency_facts"]["river_adjacent"] is True
        assert d["adjacency_facts"]["coast_adjacent"] is False

    def test_rf28_adjacency_facts_default_false(self):
        receipt = _do_extract("PLAIN", "FARM")
        d = receipt.to_dict()
        assert d["adjacency_facts"]["river_adjacent"] is False
        assert d["adjacency_facts"]["coast_adjacent"] is False

    def test_rf29_terrain_kind_in_receipt_not_terrain(self):
        """terrain_kind is the canonical field name (not 'terrain' as in Move 11)."""
        receipt = _do_extract("PLAIN", "FARM")
        d = receipt.to_dict()
        assert "terrain_kind" in d
        assert d["terrain_kind"] == "PLAIN"
        assert "terrain" not in d  # old field name must not be present

    def test_rf29_resource_kind_in_receipt_dict(self):
        receipt = _do_extract("HILL", "MINE")
        assert receipt.to_dict()["resource_kind"] == "MATTER"

    def test_receipt_schema_has_all_required_fields(self):
        required = {
            "receipt_type", "status", "receipt_id", "house_id", "hex_id",
            "extractor_kind", "resource_kind", "quantity", "tick",
            "terrain_kind", "adjacency_facts", "world_hash", "input_refs",
            "output_token_ids", "legality", "yield_breakdown",
        }
        receipt = _do_extract("PLAIN", "FARM")
        d = receipt.to_dict()
        for field in required:
            assert field in d, f"Missing receipt field: {field!r}"

    def test_input_refs_is_empty_for_raw_extraction(self):
        receipt = _do_extract("PLAIN", "FARM")
        assert receipt.to_dict()["input_refs"] == []

    def test_no_artifact_type_field(self):
        """artifact_type is gone; replaced by receipt_type."""
        d = _do_extract("PLAIN", "FARM").to_dict()
        assert "artifact_type" not in d


# ── RF30–RF40: ResourceLotV1 invariants ─────────────────────────────────────

class TestResourceLotInvariants:
    def _make_lot(self, **kwargs) -> ResourceLotV1:
        defaults = dict(
            lot_id="LOT-abc",
            resource_kind="ESSENCE",
            quantity=1,
            owner_house_id=_HOUSE,
            current_hex_id=_HEX,
            source_receipt_id="EX-abc",
            source_hex_id=_HEX,
            extraction_tick=_TICK,
            world_hash=_WORLD_HASH,
        )
        defaults.update(kwargs)
        return ResourceLotV1(**defaults)

    def test_rf30_invalid_resource_kind_raises(self):
        with pytest.raises(ValueError, match="resource_kind"):
            self._make_lot(resource_kind="GOLD")

    def test_rf31_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="quantity"):
            self._make_lot(quantity=0)

    def test_rf32_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="quantity"):
            self._make_lot(quantity=-5)

    def test_rf33_lot_is_frozen(self):
        receipt = _do_extract("PLAIN", "FARM")
        lot = receipt.lots[0]
        with pytest.raises((AttributeError, TypeError)):
            lot.quantity = 999  # type: ignore[misc]

    def test_rf34_empty_owner_house_id_raises(self):
        with pytest.raises(ValueError, match="owner_house_id"):
            self._make_lot(owner_house_id="")

    def test_rf35_mint_lot_id_deterministic(self):
        id1 = mint_lot_id("EX-deadbeef", 0)
        id2 = mint_lot_id("EX-deadbeef", 0)
        assert id1 == id2

    def test_rf36_mint_lot_id_differs_with_index(self):
        id0 = mint_lot_id("EX-deadbeef", 0)
        id1 = mint_lot_id("EX-deadbeef", 1)
        assert id0 != id1

    def test_rf37_lot_to_dict_has_all_required_fields(self):
        required = {
            "lot_id", "resource_kind", "quantity", "owner_house_id",
            "current_hex_id", "source_receipt_id", "source_hex_id",
            "extraction_tick", "world_hash", "status",
        }
        receipt = _do_extract("HILL", "MINE")
        for lot in receipt.lots:
            d = lot.to_dict()
            for field in required:
                assert field in d, f"lot.to_dict() missing {field!r}"

    def test_rf38_lot_default_status_is_active(self):
        """Status is now ACTIVE (was STORED in Move 11)."""
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.status == "ACTIVE"

    def test_rf38_status_stored_not_valid(self):
        """STORED is no longer in LOT_STATUS_V1."""
        assert "STORED" not in LOT_STATUS_V1

    def test_rf39_lot_resource_kind_matches_extractor_output(self):
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.resource_kind == "ESSENCE"

    def test_rf39_mine_lots_are_matter(self):
        receipt = _do_extract("HILL", "MINE")
        for lot in receipt.lots:
            assert lot.resource_kind == "MATTER"

    def test_rf40_lot_quantity_equals_receipt_quantity(self):
        """I-2: lot.quantity == receipt.quantity."""
        for terrain, extractor in [
            ("PLAIN", "FARM"), ("COAST", "FARM"),
            ("HILL", "MINE"), ("MOUNTAIN", "MINE"),
        ]:
            receipt = _do_extract(terrain, extractor)
            assert receipt.lots[0].quantity == receipt.quantity, (
                f"{extractor}/{terrain}: lot.quantity={receipt.lots[0].quantity} "
                f"!= receipt.quantity={receipt.quantity}"
            )


# ── RF45–RF48: Lot provenance fields ─────────────────────────────────────────

class TestLotProvenance:
    def test_rf45_lot_source_hex_id_equals_extraction_hex(self):
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.source_hex_id == _HEX

    def test_rf46_lot_extraction_tick_equals_extraction_tick(self):
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.extraction_tick == _TICK

    def test_rf47_lot_world_hash_equals_provided_world_hash(self):
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.world_hash == _WORLD_HASH

    def test_rf48_lot_owner_matches_house(self):
        receipt = _do_extract("PLAIN", "FARM")
        for lot in receipt.lots:
            assert lot.owner_house_id == _HOUSE

    def test_provenance_different_tick_preserved_in_lot(self):
        r1 = _do_extract("PLAIN", "FARM", tick=10)
        r2 = _do_extract("PLAIN", "FARM", tick=20)
        assert r1.lots[0].extraction_tick == 10
        assert r2.lots[0].extraction_tick == 20

    def test_provenance_different_hex_preserved_in_lot(self):
        r1 = _do_extract("PLAIN", "FARM", hex_id="H0_0")
        r2 = _do_extract("PLAIN", "FARM", hex_id="H9_9")
        assert r1.lots[0].source_hex_id == "H0_0"
        assert r2.lots[0].source_hex_id == "H9_9"

    def test_source_hex_id_and_current_hex_id_match_at_extraction(self):
        """At extraction time, source_hex_id == current_hex_id."""
        receipt = _do_extract("PLAIN", "FARM")
        lot = receipt.lots[0]
        assert lot.source_hex_id == lot.current_hex_id
