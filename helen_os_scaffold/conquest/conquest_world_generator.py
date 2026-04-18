"""
conquest/conquest_world_generator.py — CONQUESTLAND_WORLDGEN_V0_1

Deterministic world generator for CONQUESTLAND.

Pipeline:
  seed
  → build hex lattice
  → terrain_wfc()
  → carve_rivers()
  → place_structures()
  → solve_roads()
  → assign_regions()
  → assign_resources()
  → init_ledger_overlays()
  → emit WORLD_GENERATION_RECEIPT_V1

Success condition: same seed → same world_hash

Invariants:
  L1  terrain_wfc knows nothing about claims, Houses, duels, or Senate.
  L2  ledger_init knows nothing about WFC contradiction recovery.
  L3  No ownership is assigned during generation.
  L4  CLAIMED / SEALED / FORTIFIED / RESOURCE_LOCKED / DUEL_PENDING
      require a receipt — never set during worldgen.
  L5  generation_entropy ≠ epistemic_fog  (solver uncertainty ≠ player knowledge)
  L6  Determinism: only seeded RNG; no external I/O during generation.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

# ── Load registry — prefer canonical modules, fall back to direct JSON ─────────

try:
    from conquest.tiles import (
        TERRAIN_REGISTRY,
        STRUCTURE_REGISTRY,
        OVERLAY_REGISTRY,
        VALID_TERRAINS,
        VALID_STRUCTURES,
        REGIONS,
        REGION_BIAS,
        HARD_INVARIANTS,
    )
    from conquest.adjacency import TERRAIN_ADJACENCY
except ImportError:
    # Standalone / sys.path includes conquest/ directly
    _HERE = Path(__file__).parent
    _TILES    = json.loads((_HERE / "conquest_tiles.json").read_text())
    _ADJACENCY = json.loads((_HERE / "conquest_adjacency_matrix.json").read_text())
    TERRAIN_REGISTRY   = _TILES["terrain_registry"]
    STRUCTURE_REGISTRY = _TILES["structure_registry"]
    OVERLAY_REGISTRY   = _TILES["overlay_registry"]
    TERRAIN_ADJACENCY  = _ADJACENCY["terrain_adjacency"]
    REGION_BIAS        = _TILES["region_bias"]
    HARD_INVARIANTS    = _TILES["hard_invariants"]
    VALID_TERRAINS   = list(TERRAIN_REGISTRY.keys())
    VALID_STRUCTURES = list(STRUCTURE_REGISTRY.keys())
    REGIONS          = _TILES["regions"]


# ── Canonical hex dataclass ───────────────────────────────────────────────────

@dataclass
class HexTile:
    """Canonical world cell — CONQUEST_HEX_V0_1."""
    hex_id: str
    q: int
    r: int
    terrain: str
    structure: Optional[str] = None
    overlay: list[str] = field(default_factory=lambda: ["UNCLAIMED"])
    region_id: Optional[str] = None
    owner_house_id: Optional[str] = None          # always null at generation time
    resource_profile: list[str] = field(default_factory=list)
    generation_entropy: float = 0.0               # WFC solver uncertainty
    epistemic_fog: bool = True                    # player knowledge state
    receipt_hash: Optional[str] = None            # null until ledger_init / receipt op

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WorldV1:
    """Complete CONQUESTLAND world."""
    seed: int
    width: int
    height: int
    hexes: list[HexTile] = field(default_factory=list)
    region_map: dict[str, str] = field(default_factory=dict)  # hex_id → region_id
    spec: str = "CONQUESTLAND_WORLDGEN_V0_1"

    def hex_by_id(self, hex_id: str) -> Optional[HexTile]:
        for h in self.hexes:
            if h.hex_id == hex_id:
                return h
        return None

    def neighbors(self, hex_id: str) -> list[HexTile]:
        """Return the 6 axial neighbors of a hex (flat-top cube coords)."""
        target = self.hex_by_id(hex_id)
        if target is None:
            return []
        q, r = target.q, target.r
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
        result = []
        for dq, dr in directions:
            nq, nr = q + dq, r + dr
            nid = _hex_id(nq, nr)
            neighbor = self.hex_by_id(nid)
            if neighbor:
                result.append(neighbor)
        return result


@dataclass
class WorldGenerationReceiptV1:
    """WORLD_GENERATION_RECEIPT_V1 — proof of deterministic generation."""
    seed: int
    terrain_hash: str
    structure_hash: str
    region_hash: str
    world_hash: str
    generator_version: str
    repair_events: list[str]
    replay_command: str
    status: str  # "ok" | "fail"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hex_id(q: int, r: int) -> str:
    return f"H{q}_{r}"


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(s: str) -> str:
    return "sha256:" + hashlib.sha256(s.encode()).hexdigest()


def _world_hash(world: WorldV1) -> str:
    payload = [h.to_dict() for h in sorted(world.hexes, key=lambda x: x.hex_id)]
    return _sha256(_canon(payload))


# ── Stage 1: Hex lattice ──────────────────────────────────────────────────────

def _build_hex_lattice(width: int, height: int) -> list[HexTile]:
    """
    Build an offset-to-axial hex grid.
    Uses even-q offset → axial conversion.
    """
    hexes: list[HexTile] = []
    for col in range(width):
        for row in range(height):
            q = col
            r = row - (col - (col & 1)) // 2
            hexes.append(HexTile(
                hex_id=_hex_id(q, r),
                q=q,
                r=r,
                terrain="PLAIN",   # default; overwritten by WFC
            ))
    return hexes


# ── Stage 2: Terrain WFC (simplified constraint solver) ───────────────────────

def _terrain_wfc(hexes: list[HexTile], rng: random.Random) -> list[HexTile]:
    """
    Simplified Wave Function Collapse for terrain.

    Real WFC: propagate constraints, collapse lowest-entropy cell.
    This implementation uses a seeded-random greedy collapse with
    neighbor-compatibility checking as a minimum viable first pass.

    Production upgrade: replace _choose_terrain() with full entropy propagation.
    """
    hex_map: dict[str, HexTile] = {h.hex_id: h for h in hexes}

    # Collapse order: random (seeded)
    ordered = list(hexes)
    rng.shuffle(ordered)

    for tile in ordered:
        neighbors = _get_neighbors(tile, hex_map)
        terrain = _choose_terrain(tile, neighbors, rng)
        tile.terrain = terrain
        tile.generation_entropy = rng.random()

    return list(hex_map.values())


def _get_neighbors(tile: HexTile, hex_map: dict[str, HexTile]) -> list[HexTile]:
    q, r = tile.q, tile.r
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
    result = []
    for dq, dr in directions:
        nid = _hex_id(q + dq, r + dr)
        if nid in hex_map:
            result.append(hex_map[nid])
    return result


def _choose_terrain(
    tile: HexTile,
    neighbors: list[HexTile],
    rng: random.Random,
) -> str:
    """
    Choose terrain compatible with neighbor constraints.
    Falls back to PLAIN on contradiction.
    """
    # Collect legal terrains from adjacency rules
    neighbor_terrains = [n.terrain for n in neighbors if n.terrain != "PLAIN" or n.generation_entropy > 0]
    if not neighbor_terrains:
        # No solved neighbors yet — weighted random from non-void non-sea terrains
        candidates = [t for t in VALID_TERRAINS if t not in ("VOID", "SEA", "RIVER", "BRIDGE")]
        return rng.choice(candidates)

    # Find terrains that are legal adjacent to ALL solved neighbors
    legal = set(VALID_TERRAINS)
    for nt in neighbor_terrains:
        allowed = set(TERRAIN_ADJACENCY.get(nt, VALID_TERRAINS))
        legal &= allowed

    # Remove VOID from generation (only used for map borders)
    legal.discard("VOID")
    if not legal:
        return "PLAIN"  # repair: neutral connector

    return rng.choice(sorted(legal))


# ── Stage 3: River carving ────────────────────────────────────────────────────

def _carve_rivers(world: WorldV1, rng: random.Random) -> WorldV1:
    """
    Carve 1–3 river corridors from high elevation to coast/lake.
    Modifies HILL/MOUNTAIN tiles along corridors to RIVER.
    """
    hill_tiles = [h for h in world.hexes if h.terrain in ("HILL", "MOUNTAIN")]
    if not hill_tiles:
        return world

    num_rivers = min(rng.randint(1, 3), len(hill_tiles))
    sources = rng.sample(hill_tiles, num_rivers)

    for source in sources:
        current = source
        max_steps = 20
        for _ in range(max_steps):
            current.terrain = "RIVER"
            neighbors = world.neighbors(current.hex_id)
            # Flow toward lowest elevation or water
            water_neighbors = [n for n in neighbors if n.terrain in ("COAST", "LAKE", "SEA")]
            if water_neighbors:
                break  # river reached the sea / lake
            lower = [n for n in neighbors if TERRAIN_REGISTRY[n.terrain]["elevation"] <= TERRAIN_REGISTRY[current.terrain]["elevation"]]
            if not lower:
                break
            current = rng.choice(lower)

    return world


# ── Stage 4: Structure placement ──────────────────────────────────────────────

def _place_structures(world: WorldV1, rng: random.Random) -> WorldV1:
    """
    Place structures on legal terrain tiles.
    Respects structure_registry.allowed_on.
    Does not set ownership. Does not set CLAIMED overlay.
    """
    # Build terrain → hex lookup
    terrain_hex: dict[str, list[HexTile]] = {}
    for tile in world.hexes:
        terrain_hex.setdefault(tile.terrain, []).append(tile)

    for struct_name, spec in STRUCTURE_REGISTRY.items():
        allowed_terrains = spec["allowed_on"]
        candidates = []
        for t in allowed_terrains:
            candidates.extend(terrain_hex.get(t, []))
        candidates = [c for c in candidates if c.structure is None]

        if not candidates:
            continue

        # Place 1–3 of each structure type (density target is rough)
        count = rng.randint(1, 3)
        placed = rng.sample(candidates, min(count, len(candidates)))
        for tile in placed:
            tile.structure = struct_name

    return world


# ── Stage 5: Road solver ──────────────────────────────────────────────────────

def _solve_roads(world: WorldV1, rng: random.Random) -> WorldV1:
    """
    Connect major settlements (TOWN, CITY, CASTLE) with ROAD corridors.
    Simplified: marks passable non-water tiles between pairs as ROAD.
    """
    anchors = [h for h in world.hexes if h.structure in ("TOWN", "CITY", "CASTLE")]
    if len(anchors) < 2:
        return world

    # Connect consecutive anchor pairs along a rough path
    rng.shuffle(anchors)
    for i in range(len(anchors) - 1):
        _road_between(world, anchors[i], anchors[i + 1])

    return world


def _road_between(world: WorldV1, src: HexTile, dst: HexTile) -> None:
    """Naively mark tiles between two hexes as ROAD (simplified BFS)."""
    visited: set[str] = set()
    queue = [src]
    visited.add(src.hex_id)
    while queue:
        current = queue.pop(0)
        if current.hex_id == dst.hex_id:
            break
        for neighbor in world.neighbors(current.hex_id):
            if neighbor.hex_id in visited:
                continue
            info = TERRAIN_REGISTRY.get(neighbor.terrain, {})
            if not info.get("passable", False):
                continue
            if neighbor.terrain not in ("ROAD", "COAST") and neighbor.structure is None:
                neighbor.terrain = "ROAD"
            visited.add(neighbor.hex_id)
            queue.append(neighbor)


# ── Stage 6: Region partition ─────────────────────────────────────────────────

def _assign_regions(world: WorldV1, rng: random.Random) -> WorldV1:
    """
    Assign each hex to one of the 6 canonical regions.
    Uses Voronoi-style seeded assignment from random centroids.
    """
    # Pick one centroid per region from eligible tiles
    eligible = [h for h in world.hexes if h.terrain not in ("VOID", "SEA")]
    if not eligible:
        return world

    centroids: dict[str, HexTile] = {}
    pool = list(eligible)
    rng.shuffle(pool)
    for region in REGIONS:
        if pool:
            centroids[region] = pool.pop()

    # Assign each hex to nearest centroid (Manhattan on axial coords)
    for tile in world.hexes:
        if not centroids:
            tile.region_id = REGIONS[0]
            continue
        nearest = min(
            centroids.items(),
            key=lambda kv: abs(tile.q - kv[1].q) + abs(tile.r - kv[1].r),
        )
        tile.region_id = nearest[0]

    world.region_map = {tile.hex_id: tile.region_id for tile in world.hexes if tile.region_id}
    return world


# ── Stage 7: Resource assignment ──────────────────────────────────────────────

def _assign_resources(world: WorldV1, rng: random.Random) -> WorldV1:
    """
    Assign resource profiles from terrain base_resources.
    Structure grants_resources are added on top.
    No ownership is granted here.
    """
    for tile in world.hexes:
        resources = list(TERRAIN_REGISTRY[tile.terrain]["base_resources"])
        if tile.structure and tile.structure in STRUCTURE_REGISTRY:
            resources += STRUCTURE_REGISTRY[tile.structure]["grants_resources"]
        tile.resource_profile = sorted(set(resources))  # deterministic sort

    return world


# ── Stage 8: Ledger overlay init ──────────────────────────────────────────────

def _init_ledger_overlays(world: WorldV1) -> WorldV1:
    """
    Initialize overlays to UNCLAIMED / CLAIMABLE per tile eligibility.

    Hard invariants (from HARD_INVARIANTS):
      - CLAIMED / FORTIFIED / SEALED / RESOURCE_LOCKED / DUEL_PENDING
        require receipts; never set here.
      - owner_house_id remains null.
      - receipt_hash remains null.
    """
    for tile in world.hexes:
        t_info = TERRAIN_REGISTRY[tile.terrain]
        if tile.terrain == "VOID":
            tile.overlay = []                      # VOID: no overlay
        elif not t_info["passable"] and not t_info["water"]:
            tile.overlay = ["UNCLAIMED"]           # impassable land: unclaimed
        elif tile.terrain == "SEA":
            tile.overlay = ["UNCLAIMED"]           # sea: unclaimed
        else:
            tile.overlay = ["CLAIMABLE"]           # passable tiles: claimable

        # Guard: never set receipt-requiring overlays
        forbidden = {"CLAIMED", "FORTIFIED", "SEALED", "RESOURCE_LOCKED", "DUEL_PENDING"}
        tile.overlay = [o for o in tile.overlay if o not in forbidden]

    return world


# ── Receipt emission ──────────────────────────────────────────────────────────

def world_generation_receipt(
    world: WorldV1,
    seed: int,
    repair_events: Optional[list[str]] = None,
) -> WorldGenerationReceiptV1:
    """
    Emit WORLD_GENERATION_RECEIPT_V1.

    terrain_hash covers only terrain fields.
    structure_hash covers structure fields.
    region_hash covers region assignments.
    world_hash covers the full serialized world.
    """
    terrain_payload = [
        {"hex_id": h.hex_id, "terrain": h.terrain}
        for h in sorted(world.hexes, key=lambda x: x.hex_id)
    ]
    structure_payload = [
        {"hex_id": h.hex_id, "structure": h.structure}
        for h in sorted(world.hexes, key=lambda x: x.hex_id)
    ]
    region_payload = [
        {"hex_id": h.hex_id, "region_id": h.region_id}
        for h in sorted(world.hexes, key=lambda x: x.hex_id)
    ]

    return WorldGenerationReceiptV1(
        seed=seed,
        terrain_hash=_sha256(_canon(terrain_payload)),
        structure_hash=_sha256(_canon(structure_payload)),
        region_hash=_sha256(_canon(region_payload)),
        world_hash=_world_hash(world),
        generator_version="CONQUEST_TILES_V0_1",
        repair_events=repair_events or [],
        replay_command=f"python conquest_world_generator.py --seed {seed}",
        status="ok",
    )


# ── Main entrypoint ───────────────────────────────────────────────────────────

def generate_world(seed: int, width: int = 32, height: int = 32) -> WorldV1:
    """
    Generate a deterministic CONQUESTLAND world.

    Args:
        seed:   Integer seed. Same seed → identical world_hash.
        width:  Hex grid columns.
        height: Hex grid rows.

    Returns:
        WorldV1 with fully solved terrain, structures, roads, regions,
        resources, and initial ledger overlays.
    """
    rng = random.Random(seed)

    world = WorldV1(seed=seed, width=width, height=height)

    # Layer A: terrain substrate (immutable after this stage)
    world.hexes = _build_hex_lattice(width, height)
    world.hexes = _terrain_wfc(world.hexes, rng)
    world = _carve_rivers(world, rng)

    # Layer B: human settlement + infrastructure (placed, not sovereign)
    world = _place_structures(world, rng)
    world = _solve_roads(world, rng)

    # Geography metadata
    world = _assign_regions(world, rng)
    world = _assign_resources(world, rng)

    # Layer C: ledger overlays (UNCLAIMED / CLAIMABLE only; no receipts)
    world = _init_ledger_overlays(world)

    return world


# ── CLI entry ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="CONQUESTLAND world generator")
    parser.add_argument("--seed",   type=int, default=912733, help="World seed")
    parser.add_argument("--width",  type=int, default=32,     help="Grid width")
    parser.add_argument("--height", type=int, default=32,     help="Grid height")
    parser.add_argument("--out",    type=str, default=None,   help="Output JSON path")
    args = parser.parse_args()

    world   = generate_world(args.seed, args.width, args.height)
    receipt = world_generation_receipt(world, args.seed)

    output = {
        "world":   {"spec": world.spec, "seed": world.seed,
                    "width": world.width, "height": world.height,
                    "hex_count": len(world.hexes)},
        "receipt": receipt.to_dict(),
    }

    if args.out:
        Path(args.out).write_text(json.dumps(output, indent=2))
        print(f"[CONQUESTLAND] World written to {args.out}", file=sys.stderr)
    else:
        print(json.dumps(output, indent=2))
