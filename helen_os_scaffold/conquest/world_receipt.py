"""
conquest/world_receipt.py — World receipt schemas (Phase C: CONQUEST_WFC_SPEC_V1)

Receipt types:
    WorldReceiptV1           — WORLD_GENERATION_RECEIPT_V1  (legacy; backward-compat)
    WorldPatchReceiptV1      — WORLD_PATCH_GEN_V1          (Phase C; typed patch witness)
    WorldContradictionReceiptV1 — WORLD_CONTRADICTION_V1   (Phase C; contradiction witness)

Constitutional invariants:
    - Purely functional: no I/O, no mutation, no sovereignty claims.
    - Canonical JSON (CANON_JSON_V1): sort_keys=True, separators=(",",":"), ensure_ascii=True
    - All hashes are SHA256 hex (no "sha256:" prefix in Phase C receipts;
      "sha256:" prefix retained for legacy WorldReceiptV1 backward compat).
    - canonical_payload_hash derivation: SHA256 of canonical JSON of hexes sorted by (q, r),
      tiles only (omitting generation_entropy from hash input per §6.1).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Optional


def _canon(obj: Any) -> str:
    """Legacy canonical JSON (ensure_ascii=False for WorldReceiptV1)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canon_v1(obj: Any) -> str:
    """Phase C canonical JSON (ensure_ascii=True per CONQUEST_WFC_SPEC_V1 §Appendix A)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(s: str) -> str:
    """Legacy: SHA256 with 'sha256:' prefix (for WorldReceiptV1 backward compat)."""
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha256_hex(s: str) -> str:
    """Phase C: SHA256 hex only (no prefix), lowercase 64 chars."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── Phase C helper functions ───────────────────────────────────────────────────

def compute_canonical_payload_hash(hexes: list[dict[str, Any]]) -> str:
    """
    Canonical payload hash for WORLD_PATCH_GEN_V1 (§6.1).

    Sorted by (q, r) ascending. Only {q, r, tile} included in hash —
    generation_entropy is informational and excluded.

    Returns 64-char lowercase SHA256 hex.
    """
    sorted_hexes = sorted(hexes, key=lambda h: (h["q"], h["r"]))
    payload = [{"q": h["q"], "r": h["r"], "tile": h["tile"]} for h in sorted_hexes]
    return _sha256_hex(_canon_v1(payload))


def compute_boundary_constraints_hash(border_cells: list[dict[str, Any]]) -> str:
    """
    Boundary constraints hash (§6.1).

    border_cells: list of {"q", "r", "required_tile"} or {"q", "r", "forbidden_tiles": [...]}
    Sorted by (q, r). Returns 64-char SHA256 hex.
    """
    sorted_bc = sorted(border_cells, key=lambda c: (c["q"], c["r"]))
    return _sha256_hex(_canon_v1(sorted_bc))


def compute_world_seed(tick_id: int, sov_hash: str) -> str:
    """
    World seed derivation per CONQUEST_WFC_SPEC_V1 §3.

    world_seed = sha256_hex("CONQUESTLAND" + str(tick_id) + str(sov_hash))
    Returns 64-char lowercase SHA256 hex.
    """
    seed_input = "CONQUESTLAND" + str(tick_id) + str(sov_hash)
    return _sha256_hex(seed_input)


def compute_retry_seed(world_seed: str, patch_id: str, retry_count: int) -> str:
    """
    Retry seed for contradiction recovery (§3).

    retry_seed = sha256_hex(world_seed + str(patch_id) + str(retry_count))
    """
    return _sha256_hex(world_seed + str(patch_id) + str(retry_count))


@dataclass
class WorldReceiptV1:
    """WORLD_GENERATION_RECEIPT_V1 fields."""
    artifact_type:     str = "WORLD_GENERATION_RECEIPT_V1"
    seed:              int = 0
    terrain_hash:      str = ""
    structure_hash:    str = ""
    region_hash:       str = ""
    world_hash:        str = ""
    generator_version: str = "CONQUEST_TILES_V0_1"
    repair_events:     list = None   # type: ignore[assignment]
    replay_command:    str = ""
    status:            str = "ok"

    def __post_init__(self):
        if self.repair_events is None:
            self.repair_events = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type":     self.artifact_type,
            "seed":              self.seed,
            "terrain_hash":      self.terrain_hash,
            "structure_hash":    self.structure_hash,
            "region_hash":       self.region_hash,
            "world_hash":        self.world_hash,
            "generator_version": self.generator_version,
            "repair_events":     self.repair_events,
            "replay_command":    self.replay_command,
            "status":            self.status,
        }


def emit_world_receipt(
    hexes:         list[dict[str, Any]],
    seed:          int,
    width:         int,
    height:        int,
    repair_events: list[dict[str, Any]] | None = None,
) -> WorldReceiptV1:
    """
    Compute WORLD_GENERATION_RECEIPT_V1 from serialized hex list.

    Args:
        hexes:         List of hex dicts sorted by hex_id.
        seed:          World generation seed.
        width, height: Grid dimensions.
        repair_events: WFC contradiction repair log.

    Returns:
        WorldReceiptV1 with deterministic hash fields.
    """
    sorted_hexes = sorted(hexes, key=lambda h: h["hex_id"])

    terrain_view = [
        {"hex_id": h["hex_id"], "terrain": h["terrain"],
         "generation_entropy": h.get("generation_entropy", 0.0)}
        for h in sorted_hexes
    ]
    structure_view = [
        {"hex_id": h["hex_id"], "structure": h.get("structure")}
        for h in sorted_hexes
    ]
    region_view = [
        {"hex_id": h["hex_id"], "region_id": h.get("region_id")}
        for h in sorted_hexes
    ]

    return WorldReceiptV1(
        artifact_type="WORLD_GENERATION_RECEIPT_V1",
        seed=seed,
        terrain_hash=_sha256(_canon(terrain_view)),
        structure_hash=_sha256(_canon(structure_view)),
        region_hash=_sha256(_canon(region_view)),
        world_hash=_sha256(_canon(sorted_hexes)),
        generator_version="CONQUEST_TILES_V0_1",
        repair_events=repair_events or [],
        replay_command=(
            f"python conquest_world_generator.py "
            f"--seed {seed} --width {width} --height {height}"
        ),
        status="ok",
    )


# ── Phase C: WORLD_PATCH_GEN_V1 ───────────────────────────────────────────────

@dataclass
class WorldPatchReceiptV1:
    """
    WORLD_PATCH_GEN_V1 — typed witness for a successfully solved terrain patch.

    Emitted by the orchestrator after WFC solver succeeds.
    The solver itself never emits this; it is always the caller's responsibility.

    canonical_payload_hash: SHA256 of canonical JSON of hexes sorted by (q, r),
    fields {q, r, tile} only (generation_entropy excluded from hash).
    """
    artifact_type:             str  = "WORLD_PATCH_GEN_V1"
    tile_spec_version:         str  = "CONQUEST_WFC_SPEC_V1"
    solver_version:            str  = "WFC_SOLVER_V1"
    patch_id:                  str  = ""
    tick_id:                   int  = 0
    world_seed:                str  = ""      # 64-char SHA256 hex
    boundary_constraints_hash: str  = ""      # 64-char SHA256 hex
    hexes:                     list = field(default_factory=list)
    repair_events:             list = field(default_factory=list)
    canonical_payload_hash:    str  = ""      # 64-char SHA256 hex
    status:                    str  = "ok"

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type":             self.artifact_type,
            "tile_spec_version":         self.tile_spec_version,
            "solver_version":            self.solver_version,
            "patch_id":                  self.patch_id,
            "tick_id":                   self.tick_id,
            "world_seed":                self.world_seed,
            "boundary_constraints_hash": self.boundary_constraints_hash,
            "hexes":                     self.hexes,
            "repair_events":             self.repair_events,
            "canonical_payload_hash":    self.canonical_payload_hash,
            "status":                    self.status,
        }


def emit_world_patch_receipt(
    patch_id:                  str,
    tick_id:                   int,
    world_seed:                str,
    hexes:                     list[dict[str, Any]],
    boundary_constraints:      Optional[list[dict[str, Any]]] = None,
    repair_events:             Optional[list[dict[str, Any]]] = None,
    solver_version:            str = "WFC_SOLVER_V1",
    tile_spec_version:         str = "CONQUEST_WFC_SPEC_V1",
) -> WorldPatchReceiptV1:
    """
    Emit a WORLD_PATCH_GEN_V1 receipt from solved WFC output.

    Args:
        patch_id:             Unique patch identifier (e.g. "patch_0x3y2").
        tick_id:              Game tick number.
        world_seed:           64-char SHA256 hex from compute_world_seed().
        hexes:                List of {"q", "r", "tile", "generation_entropy"} dicts.
        boundary_constraints: List of boundary constraint dicts (may be empty).
        repair_events:        WFC retry/repair log (may be empty).
        solver_version:       WFC solver version string.
        tile_spec_version:    Tile spec version string.

    Returns:
        WorldPatchReceiptV1 with canonical_payload_hash and boundary_constraints_hash computed.
    """
    bc = boundary_constraints or []
    bc_hash = compute_boundary_constraints_hash(bc)
    cph = compute_canonical_payload_hash(hexes)

    return WorldPatchReceiptV1(
        artifact_type="WORLD_PATCH_GEN_V1",
        tile_spec_version=tile_spec_version,
        solver_version=solver_version,
        patch_id=patch_id,
        tick_id=tick_id,
        world_seed=world_seed,
        boundary_constraints_hash=bc_hash,
        hexes=hexes,
        repair_events=repair_events or [],
        canonical_payload_hash=cph,
        status="ok",
    )


# ── Phase C: WORLD_CONTRADICTION_V1 ───────────────────────────────────────────

@dataclass
class WorldContradictionReceiptV1:
    """
    WORLD_CONTRADICTION_V1 — typed witness for an unresolved WFC contradiction.

    Emitted when all k retries are exhausted. Resolution is always
    "ARBITRATION_REQUIRED" — no implicit wildcard insertion.

    canonical_payload_hash: SHA256 of this receipt's canonical payload
    (all fields except canonical_payload_hash itself), sorted keys.
    """
    artifact_type:                        str  = "WORLD_CONTRADICTION_V1"
    tile_spec_version:                    str  = "CONQUEST_WFC_SPEC_V1"
    solver_version:                       str  = "WFC_SOLVER_V1"
    patch_id:                             str  = ""
    tick_id:                              int  = 0
    world_seed:                           str  = ""      # 64-char SHA256 hex
    boundary_constraints_hash:            str  = ""      # 64-char SHA256 hex
    contradiction_hex:                    dict = field(default_factory=dict)   # {"q": int, "r": int}
    retry_count:                          int  = 3       # always k=3 for MVP
    retry_seeds:                          list = field(default_factory=list)
    neighbor_terrains:                    list = field(default_factory=list)
    candidate_tiles_before_contradiction: list = field(default_factory=list)
    repair_attempts:                      list = field(default_factory=list)
    resolution:                           str  = "ARBITRATION_REQUIRED"
    canonical_payload_hash:               str  = ""      # 64-char SHA256 hex
    status:                               str  = "contradiction"

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type":                        self.artifact_type,
            "tile_spec_version":                    self.tile_spec_version,
            "solver_version":                       self.solver_version,
            "patch_id":                             self.patch_id,
            "tick_id":                              self.tick_id,
            "world_seed":                           self.world_seed,
            "boundary_constraints_hash":            self.boundary_constraints_hash,
            "contradiction_hex":                    self.contradiction_hex,
            "retry_count":                          self.retry_count,
            "retry_seeds":                          self.retry_seeds,
            "neighbor_terrains":                    self.neighbor_terrains,
            "candidate_tiles_before_contradiction": self.candidate_tiles_before_contradiction,
            "repair_attempts":                      self.repair_attempts,
            "resolution":                           self.resolution,
            "canonical_payload_hash":               self.canonical_payload_hash,
            "status":                               self.status,
        }


def _contradiction_canonical_payload_hash(receipt_dict: dict[str, Any]) -> str:
    """
    SHA256 of the contradiction receipt payload (all fields except the hash itself).
    """
    fields = {k: v for k, v in receipt_dict.items() if k != "canonical_payload_hash"}
    return _sha256_hex(_canon_v1(fields))


def emit_world_contradiction_receipt(
    patch_id:                             str,
    tick_id:                              int,
    world_seed:                           str,
    contradiction_hex:                    dict[str, int],
    retry_count:                          int = 3,
    boundary_constraints:                 Optional[list[dict[str, Any]]] = None,
    retry_seeds:                          Optional[list[str]] = None,
    neighbor_terrains:                    Optional[list[str]] = None,
    candidate_tiles_before_contradiction: Optional[list[str]] = None,
    repair_attempts:                      Optional[list[dict[str, Any]]] = None,
    solver_version:                       str = "WFC_SOLVER_V1",
    tile_spec_version:                    str = "CONQUEST_WFC_SPEC_V1",
) -> WorldContradictionReceiptV1:
    """
    Emit a WORLD_CONTRADICTION_V1 receipt when all k retries fail.

    Args:
        patch_id:                             Same patch_id as failed attempt.
        tick_id:                              Game tick number.
        world_seed:                           64-char SHA256 hex.
        contradiction_hex:                    {"q": int, "r": int} of cell that contradicted.
        retry_count:                          Number of retries exhausted (MVP = 3).
        boundary_constraints:                 Same boundary constraints as original attempt.
        retry_seeds:                          List of retry seed hex strings (one per attempt).
        neighbor_terrains:                    Terrain values of neighbors at contradiction cell.
        candidate_tiles_before_contradiction: Which tiles were candidates before failure.
        repair_attempts:                      Log of per-attempt outcomes.
        solver_version:                       WFC solver version string.
        tile_spec_version:                    Tile spec version string.

    Returns:
        WorldContradictionReceiptV1 with canonical_payload_hash computed.
    """
    bc = boundary_constraints or []
    bc_hash = compute_boundary_constraints_hash(bc)

    receipt = WorldContradictionReceiptV1(
        artifact_type="WORLD_CONTRADICTION_V1",
        tile_spec_version=tile_spec_version,
        solver_version=solver_version,
        patch_id=patch_id,
        tick_id=tick_id,
        world_seed=world_seed,
        boundary_constraints_hash=bc_hash,
        contradiction_hex=contradiction_hex,
        retry_count=retry_count,
        retry_seeds=retry_seeds or [],
        neighbor_terrains=neighbor_terrains or [],
        candidate_tiles_before_contradiction=candidate_tiles_before_contradiction or [],
        repair_attempts=repair_attempts or [],
        resolution="ARBITRATION_REQUIRED",
        canonical_payload_hash="",      # computed below
        status="contradiction",
    )

    # Compute canonical_payload_hash after all other fields are set
    d = receipt.to_dict()
    receipt.canonical_payload_hash = _contradiction_canonical_payload_hash(d)
    return receipt
