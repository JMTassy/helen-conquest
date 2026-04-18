"""
conquest/castle_centered_generator.py — CASTLE_CENTERED_WORLDGEN_V0_1

Governing law:
    The castle is not placed into a finished world.
    The world is generated around the castle.

Castle fixed at (anchor_q, anchor_r) as the constitutional anchor.
World built outward in concentric rings via:

    Stage 1:  Build radial hex lattice (rings 0..radius)
    Stage 2:  Apply CASTLE_DOMAIN_TEMPLATE (rings 0–3 biased)
    Stage 3:  Castle-biased terrain WFC (inner-ring-first collapse)
    Stage 4:  Carve rivers from HILL/MOUNTAIN sources
    Stage 5:  Solve roads from castle outward
    Stage 6:  Assign resources (terrain + structure grants)
    Stage 7:  Place structures (castle pre-placed; skipped)
    Stage 8:  Partition regions
    Stage 9:  Initialize ledger overlays
    Stage 10: Survivability check (traversable exits, GRAIN, defense)

Sub-seed splitting:
    subseed = int(sha256(f"{world_seed}:{label}").hexdigest(), 16) & 0xFFFFFFFF

Determinism invariant:
    same world_seed → same world_hash (constitutional requirement)

Boundary invariants:
    - No sovereignty assigned during generation.
    - CLAIMED / FORTIFIED / SEALED / RESOURCE_LOCKED / DUEL_PENDING
      require a receipt — never set here.
    - generation_entropy ≠ epistemic_fog  (solver fog ≠ player fog)
"""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from conquest.adjacency import legal_neighbors
from conquest.hex_grid import axial_distance, axial_neighbors, hex_id, HEX_DIRECTIONS
from conquest.ledger_init import init_ledger_overlays
from conquest.region_partition import assign_regions
from conquest.resource_assignment import assign_resources
from conquest.river_carving import carve_rivers
from conquest.road_solver import solve_roads
from conquest.structure_placement import place_structures
from conquest.tiles import TERRAIN_REGISTRY, VALID_TERRAINS
from conquest.world_receipt import emit_world_receipt


# ── Sub-seed splitting ──────────────────────────────────────────────────────

def _sub_seed(world_seed: int, label: str) -> int:
    """
    Deterministic sub-seed from world_seed + label.
    sha256(f"{world_seed}:{label}")[:8] as little-endian int.
    """
    digest = hashlib.sha256(f"{world_seed}:{label}".encode()).hexdigest()
    return int(digest[:8], 16)


# ── Ring-based hex lattice ──────────────────────────────────────────────────

def hex_ring(center_q: int, center_r: int, radius: int) -> list[tuple[int, int]]:
    """
    Return all (q, r) coords at exactly `radius` axial distance from center.
    Uses the standard 6-side ring traversal starting from the east corner.
    """
    if radius == 0:
        return [(center_q, center_r)]

    # Six directions for traversing the ring clockwise
    # (starting east, going south-east, south-west, west, north-west, north-east)
    ring_dirs: list[tuple[int, int]] = [
        (-1,  1),  # south-west
        (-1,  0),  # west
        ( 0, -1),  # north-west
        ( 1, -1),  # north-east
        ( 1,  0),  # east
        ( 0,  1),  # south-east
    ]
    results: list[tuple[int, int]] = []
    q = center_q + radius
    r = center_r
    for dq, dr in ring_dirs:
        for _ in range(radius):
            results.append((q, r))
            q += dq
            r += dr
    return results


def build_radial_lattice(
    anchor_q: int,
    anchor_r: int,
    radius: int,
) -> dict[str, dict[str, Any]]:
    """
    Build hex lattice for all cells within `radius` rings of anchor.

    Each cell carries:
      - q, r, hex_id, ring               — spatial identity
      - epistemic_fog                    — player uncertainty (ring / radius)
      - terrain, structure, overlay, ... — initialized to null/empty
      - generation_entropy               — solver uncertainty (set by WFC)

    Invariant:
      generation_entropy ≠ epistemic_fog  (do not collapse these fields)
    """
    hex_map: dict[str, dict[str, Any]] = {}
    for ring_idx in range(radius + 1):
        for q, r in hex_ring(anchor_q, anchor_r, ring_idx):
            hid = hex_id(q, r)
            hex_map[hid] = {
                "hex_id":            hid,
                "q":                 q,
                "r":                 r,
                "ring":              ring_idx,
                "epistemic_fog":     float(ring_idx) / max(radius, 1),
                "terrain":           None,
                "structure":         None,
                "overlay":           [],
                "owner_house_id":    None,
                "receipt_hash":      None,
                "region_id":         None,
                "resource_profile":  [],
                "generation_entropy": 0.0,
            }
    return hex_map


# ── Castle Domain Template ──────────────────────────────────────────────────

# Ring-by-ring terrain prescription around the castle anchor.
# Ring 0: castle substrate — HILL (forced), CASTLE structure placed.
# Ring 1: close domain — preferred passable terrain; SEA/VOID forbidden.
# Ring 2: near domain — preferred highland/plain blend.
# Ring 3: domain edge — must include 1 ROAD + 2 PLAIN; rest from WFC.
CASTLE_DOMAIN_TEMPLATE: dict[int, dict[str, Any]] = {
    0: {
        "forced":     "HILL",
        "structure":  "CASTLE",
    },
    1: {
        "preferred":  ["PLAIN", "FOREST", "ROAD"],
        "forbidden":  {"SEA", "VOID"},
    },
    2: {
        "preferred":  ["PLAIN", "FOREST", "HILL"],
        "forbidden":  {"SEA", "VOID"},
    },
    3: {
        "must_include_at_least": {"ROAD": 1, "PLAIN": 2},
        "forbidden":  {"SEA", "VOID"},
    },
}


def _apply_castle_domain_template(
    hex_map: dict[str, dict[str, Any]],
    anchor_q: int,
    anchor_r: int,
    rng: random.Random,
) -> dict[str, dict[str, Any]]:
    """
    Pre-assign terrain for rings 0–3 according to CASTLE_DOMAIN_TEMPLATE.

    Ring 0:   HILL forced; CASTLE structure placed.
    Ring 1-2: All cells assigned to a random preferred terrain.
    Ring 3:   Quota cells (ROAD×1, PLAIN×2) assigned; rest left for WFC.

    Args:
        hex_map:    Mutable lattice.
        anchor_q/r: Castle anchor coordinates.
        rng:        Seeded RNG (template sub-seed).

    Returns:
        Updated hex_map with rings 0–3 partially or fully pre-assigned.
    """
    # ── Ring 0: forced substrate ───────────────────────────────────────────
    hid0 = hex_id(anchor_q, anchor_r)
    if hid0 in hex_map:
        rule0 = CASTLE_DOMAIN_TEMPLATE[0]
        hex_map[hid0]["terrain"]             = rule0["forced"]
        hex_map[hid0]["structure"]           = rule0["structure"]
        hex_map[hid0]["generation_entropy"]  = rng.random()

    # ── Rings 1–2: preferred pool assignment ──────────────────────────────
    for ring_idx in (1, 2):
        rule = CASTLE_DOMAIN_TEMPLATE[ring_idx]
        preferred = rule["preferred"]
        ring_hexes = [
            hid for hid, c in hex_map.items() if c["ring"] == ring_idx
        ]
        rng.shuffle(ring_hexes)
        for hid in ring_hexes:
            terrain = rng.choice(preferred)
            hex_map[hid]["terrain"]            = terrain
            hex_map[hid]["generation_entropy"] = rng.random()

    # ── Ring 3: quota assignment + remaining left for WFC ─────────────────
    rule3 = CASTLE_DOMAIN_TEMPLATE[3]
    ring3_hexes = [
        hid for hid, c in hex_map.items() if c["ring"] == 3
    ]
    rng.shuffle(ring3_hexes)
    cursor = 0
    for terrain, quota in rule3["must_include_at_least"].items():
        assigned = 0
        while assigned < quota and cursor < len(ring3_hexes):
            hid = ring3_hexes[cursor]
            hex_map[hid]["terrain"]            = terrain
            hex_map[hid]["generation_entropy"] = rng.random()
            cursor += 1
            assigned += 1

    return hex_map


# ── Castle-biased terrain WFC ───────────────────────────────────────────────

_PLACEABLE_TERRAINS = [t for t in VALID_TERRAINS if t != "VOID"]
_INTERIOR_TERRAINS  = [
    t for t in _PLACEABLE_TERRAINS
    if t not in ("SEA", "COAST", "RIVER", "BRIDGE")
]


def _castle_wfc(
    hex_map: dict[str, dict[str, Any]],
    seed: int,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """
    Run greedy WFC on all unresolved (terrain=None) cells.

    Collapse order: inner rings first, shuffled within each ring.
    Pre-assigned cells (terrain ≠ None) act as fixed constraints.
    Inner rings (≤ 8) prefer interior terrain; outer rings allow all.

    Args:
        hex_map: Mutable lattice (some cells pre-assigned from template).
        seed:    WFC sub-seed.

    Returns:
        (updated_hex_map, repair_events)
    """
    rng = random.Random(seed)
    repair_events: list[dict[str, Any]] = []

    # Group unresolved cells by ring
    ring_groups: dict[int, list[str]] = {}
    for hid, cell in hex_map.items():
        if cell.get("terrain") is None:
            ring = cell["ring"]
            ring_groups.setdefault(ring, []).append(hid)

    # Build collapse order: inner-ring-first, shuffled within ring
    collapse_order: list[str] = []
    for ring_idx in sorted(ring_groups.keys()):
        group = ring_groups[ring_idx]
        rng.shuffle(group)
        collapse_order.extend(group)

    for hid in collapse_order:
        cell  = hex_map[hid]
        q, r  = cell["q"], cell["r"]
        ring  = cell["ring"]

        # Collect already-resolved neighbor terrains
        solved_nbr: list[str] = []
        for nq, nr in axial_neighbors(q, r):
            nbr = hex_map.get(hex_id(nq, nr))
            if nbr and nbr.get("terrain") is not None:
                solved_nbr.append(nbr["terrain"])

        # Build legal terrain set
        if solved_nbr:
            legal: set[str] = set(_PLACEABLE_TERRAINS)
            for nt in solved_nbr:
                allowed = legal_neighbors(nt)
                if allowed:
                    legal &= allowed
            legal.discard("VOID")
            # Inner rings prefer interior (no sea/coast)
            if ring <= 8:
                inner = legal & set(_INTERIOR_TERRAINS)
                if inner:
                    legal = inner
        else:
            legal = set(_INTERIOR_TERRAINS)

        if not legal:
            terrain = "PLAIN"
            repair_events.append({
                "hex_id":      hid,
                "reason":      "contradiction_recovery",
                "resolved_to": terrain,
            })
        else:
            terrain = rng.choice(sorted(legal))

        cell["terrain"]            = terrain
        cell["generation_entropy"] = rng.random()

    return hex_map, repair_events


# ── Survivability Validator ─────────────────────────────────────────────────

_PASSABLE_TERRAINS    = frozenset({
    "PLAIN", "FOREST", "HILL", "MARSH", "DESERT",
    "ROAD", "COAST", "BRIDGE",
})
_DEFENSIVE_STRUCTURES = frozenset({"CASTLE", "FORT", "WATCHTOWER"})
_DEFENSIVE_TERRAINS   = frozenset({"HILL", "MOUNTAIN"})


def _traversable_exits(
    hex_map: dict[str, dict[str, Any]],
    castle_hid: str,
) -> int:
    """Count passable hexes directly adjacent to the castle."""
    cell = hex_map.get(castle_hid, {})
    q, r = cell.get("q", 0), cell.get("r", 0)
    return sum(
        1
        for nq, nr in axial_neighbors(q, r)
        if hex_map.get(hex_id(nq, nr), {}).get("terrain") in _PASSABLE_TERRAINS
    )


def _nearby_resource(
    hex_map: dict[str, dict[str, Any]],
    castle_hid: str,
    resource: str,
    radius: int,
) -> bool:
    """Return True if `resource` appears in any hex within `radius` of castle."""
    cell = hex_map.get(castle_hid, {})
    cq, cr = cell.get("q", 0), cell.get("r", 0)
    return any(
        resource in h.get("resource_profile", [])
        and axial_distance(cq, cr, h["q"], h["r"]) <= radius
        for h in hex_map.values()
    )


def _nearby_defense(
    hex_map: dict[str, dict[str, Any]],
    castle_hid: str,
    radius: int,
) -> bool:
    """Return True if a defensive structure or terrain exists within radius."""
    cell = hex_map.get(castle_hid, {})
    cq, cr = cell.get("q", 0), cell.get("r", 0)
    for hid, h in hex_map.items():
        if hid == castle_hid:
            continue
        if axial_distance(cq, cr, h["q"], h["r"]) <= radius:
            if h.get("structure") in _DEFENSIVE_STRUCTURES:
                return True
            if h.get("terrain") in _DEFENSIVE_TERRAINS:
                return True
    return False


def validate_castle_start(
    hex_map: dict[str, dict[str, Any]],
    castle_hid: str,
) -> dict[str, Any]:
    """
    Survivability validator for the castle start position.

    Checks:
      - traversable_exits >= 2  (castle must not be a dead-end)
      - GRAIN resource within radius 3
      - defensive structure or terrain within radius 2

    Returns:
        {"ok": bool, "violations": list[str]}
    """
    violations: list[str] = []

    exits = _traversable_exits(hex_map, castle_hid)
    if exits < 2:
        violations.append(f"traversable_exits={exits} (need >= 2)")

    if not _nearby_resource(hex_map, castle_hid, "GRAIN", radius=3):
        violations.append("no GRAIN resource within radius=3")

    if not _nearby_defense(hex_map, castle_hid, radius=2):
        violations.append("no defensive structure or terrain within radius=2")

    return {"ok": len(violations) == 0, "violations": violations}


# ── World Receipt ───────────────────────────────────────────────────────────

def emit_world_generation_receipt(
    world: dict[str, Any],
    world_seed: int,
    castle_id: str,
) -> dict[str, Any]:
    """
    Emit WORLD_GENERATION_RECEIPT_V1 for a castle-centered world.

    Args:
        world:      Output of generate_world_around_castle().
        world_seed: Integer seed used for generation.
        castle_id:  Logical castle ID (e.g. "CASTLE_HOUSEVAR_001").

    Returns:
        Receipt dict with deterministic hash fields + castle metadata.

    Constitutional rule:
        same world_seed → same world_hash (verifiable by replay).
    """
    hexes        = world["hexes"]
    sorted_hexes = sorted(hexes, key=lambda h: h["hex_id"])

    def _canon(obj: Any) -> str:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _sha256(s: str) -> str:
        return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()

    terrain_view = [
        {
            "hex_id":            h["hex_id"],
            "terrain":           h["terrain"],
            "generation_entropy": h.get("generation_entropy", 0.0),
        }
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

    return {
        "artifact_type":     "WORLD_GENERATION_RECEIPT_V1",
        "seed":              world_seed,
        "castle_id":         castle_id,
        "hex_count":         len(hexes),
        "radius":            world.get("radius", 0),
        "anchor":            world.get("anchor", {}),
        "terrain_hash":      _sha256(_canon(terrain_view)),
        "structure_hash":    _sha256(_canon(structure_view)),
        "region_hash":       _sha256(_canon(region_view)),
        "world_hash":        _sha256(_canon(sorted_hexes)),
        "generator_version": "CASTLE_CENTERED_WORLDGEN_V0_1",
        "repair_events":     world.get("repair_events", []),
        "survivability":     world.get("survivability", {}),
        "replay_command":    (
            f"python castle_centered_generator.py "
            f"--seed {world_seed} --castle_id {castle_id} "
            f"--radius {world.get('radius', 16)}"
        ),
        "status": "ok",
    }


# ── Main Entry Point ────────────────────────────────────────────────────────

def generate_world_around_castle(
    world_seed:  int,
    castle_id:   str,
    anchor_q:    int = 0,
    anchor_r:    int = 0,
    radius:      int = 16,
) -> dict[str, Any]:
    """
    Generate a CONQUESTLAND world centred on a fixed castle anchor.

    Constitutional rule:
        The castle is not placed into a finished world.
        The world is generated around the castle.

    Pipeline (12 stages):
        1.  Build radial hex lattice (rings 0..radius)
        2.  Apply CASTLE_DOMAIN_TEMPLATE (rings 0–3 pre-assigned)
        3.  Castle-biased terrain WFC (unresolved cells, ring-first order)
        4.  River carving from HILL/MOUNTAIN sources
        5.  Road solver anchored to castle
        6.  Resource assignment (terrain + structure grants)
        7.  Structure placement (castle already placed → skipped for ring 0)
        8.  Region partition (Voronoi from 6 centroids)
        9.  Ledger overlay initialization (UNCLAIMED / CLAIMABLE)
        10. Survivability validation

    Sub-seed splitting:
        Each stage uses _sub_seed(world_seed, label) for isolation.

    Determinism invariant:
        same world_seed → same world_hash  ← constitutional requirement

    Args:
        world_seed: Integer seed. Must be deterministic root.
        castle_id:  Logical castle identifier (player/faction scoped).
        anchor_q:   Castle q-coordinate (default 0 = world origin).
        anchor_r:   Castle r-coordinate (default 0 = world origin).
        radius:     World extent in hex rings (default 16).

    Returns:
        {
          "world_seed":    int,
          "castle_id":     str,
          "anchor":        {"q": int, "r": int, "hex_id": str},
          "radius":        int,
          "hexes":         list[dict],       # all hex cells
          "repair_events": list[dict],       # WFC contradiction log
          "survivability": {"ok": bool, "violations": list[str]},
        }
    """
    castle_hid = hex_id(anchor_q, anchor_r)

    # ── Stage 1: Build radial lattice ─────────────────────────────────────
    hex_map = build_radial_lattice(anchor_q, anchor_r, radius)

    # ── Stage 2: Castle domain template ───────────────────────────────────
    template_seed = _sub_seed(world_seed, "template")
    template_rng  = random.Random(template_seed)
    hex_map       = _apply_castle_domain_template(
        hex_map, anchor_q, anchor_r, template_rng
    )

    # ── Stage 3: Terrain WFC (unresolved cells only) ──────────────────────
    terrain_seed = _sub_seed(world_seed, "terrain")
    hex_map, repair_events = _castle_wfc(hex_map, terrain_seed)

    # ── Stage 4: River carving ─────────────────────────────────────────────
    river_seed = _sub_seed(world_seed, "rivers")
    hex_map    = carve_rivers(hex_map, river_seed)

    # ── Stage 5: Road solver (castle is a CASTLE anchor → always included) ─
    road_seed = _sub_seed(world_seed, "roads")
    hex_map   = solve_roads(hex_map, road_seed)

    # ── Stage 6: Resource assignment ──────────────────────────────────────
    hex_map = assign_resources(hex_map)

    # ── Stage 7: Structure placement (castle pre-placed, not overwritten) ──
    struct_seed = _sub_seed(world_seed, "structures")
    hex_map     = place_structures(hex_map, struct_seed)

    # ── Stage 8: Region partition ──────────────────────────────────────────
    region_seed = _sub_seed(world_seed, "regions")
    hex_map     = assign_regions(hex_map, region_seed)

    # ── Stage 9: Ledger overlay initialization ────────────────────────────
    hex_map = init_ledger_overlays(hex_map)

    # ── Stage 10: Survivability check ─────────────────────────────────────
    survivability = validate_castle_start(hex_map, castle_hid)

    return {
        "world_seed":    world_seed,
        "castle_id":     castle_id,
        "anchor":        {"q": anchor_q, "r": anchor_r, "hex_id": castle_hid},
        "radius":        radius,
        "hexes":         list(hex_map.values()),
        "repair_events": repair_events,
        "survivability": survivability,
    }
