# CONQUEST_WFC_SPEC_V1

**Status:** FROZEN
**Version:** 1.0.0
**File:** `conquest/CONQUEST_WFC_SPEC_V1.md`
**Governs:** `terrain_wfc.py`, `tiles.py`, `adjacency.py`, `world_receipt.py`
**Supersedes:** `CONQUEST_TILES_V0_1` (terrain layer only; overlay/structure layers unchanged)

---

## Constitutional Preamble

```
solver output  ≠  admitted topology  ≠  sealed territory
```

WFC is a non-sovereign constraint solver. It **proposes** terrain. The kernel **admits or rejects** via typed receipts. No WFC output is sovereign until a `WORLD_PATCH_GEN_V1` receipt is appended to the ledger. No contradiction is silently healed; every unresolved contradiction produces a `WORLD_CONTRADICTION_V1` receipt.

**Three invariants that cannot be violated:**

1. **Determinism invariant** — same `world_seed` + same `boundary_constraints_hash` → same `canonical_payload_hash`. Always. Guaranteed by seeded RNG + sorted collapse order.
2. **Contradiction invariant** — a contradiction is never silently resolved by inserting an unlisted tile. After `k=3` local retries, the patch halts and emits `WORLD_CONTRADICTION_V1`. Arbitration is required.
3. **Receipt invariant** — no hex cell in the admitted topology may carry a tile assignment that was not covered by a `WORLD_PATCH_GEN_V1` receipt. No receipt → not admitted.

---

## §1 — Tile Primitives

Eight canonical tiles for `CONQUEST_WFC_SPEC_V1`. All future tiles added to this set require a new spec version and a migration receipt.

| Tile ID     | Display Name | Category  | Passable | Water | Elevation Band |
|-------------|--------------|-----------|----------|-------|----------------|
| `OCEAN`     | Ocean        | terrain   | ✗        | ✓     | 0 (sea level)  |
| `COAST`     | Coast        | terrain   | ✓        | ✓     | 0 (shore)      |
| `GRASS`     | Grassland    | terrain   | ✓        | ✗     | 1 (low)        |
| `ROAD`      | Road         | terrain   | ✓        | ✗     | 1 (low)        |
| `RIVER`     | River        | terrain   | ✗        | ✓     | 1–3 (variable) |
| `FOREST`    | Forest       | terrain   | ✓        | ✗     | 1–2 (mid)      |
| `CITY`      | City         | terrain   | ✓        | ✗     | 1 (low)        |
| `MOUNTAIN`  | Mountain     | terrain   | ✗        | ✗     | 3 (high)       |

**Tile properties (frozen):**

```json
{
  "OCEAN":    { "passable": false, "water": true,  "elevation": 0, "base_resources": ["WATER", "SALT"] },
  "COAST":    { "passable": true,  "water": true,  "elevation": 0, "base_resources": ["WATER", "SALT", "FISH"] },
  "GRASS":    { "passable": true,  "water": false, "elevation": 1, "base_resources": ["FOOD", "WOOD"] },
  "ROAD":     { "passable": true,  "water": false, "elevation": 1, "base_resources": ["TRADE"] },
  "RIVER":    { "passable": false, "water": true,  "elevation": 1, "base_resources": ["WATER", "FISH"] },
  "FOREST":   { "passable": true,  "water": false, "elevation": 2, "base_resources": ["WOOD", "GAME"] },
  "CITY":     { "passable": true,  "water": false, "elevation": 1, "base_resources": ["TRADE", "CULTURE"] },
  "MOUNTAIN": { "passable": false, "water": false, "elevation": 3, "base_resources": ["STONE", "ORE"] }
}
```

**Sovereign overlays** (not assigned by WFC; only by receipt-bearing operations): `CLAIMED`, `FORTIFIED`, `SEALED`, `DUEL_PENDING`. WFC assigns terrain only.

---

## §2 — Edge Algebra (Adjacency Matrix)

Hexagonal cells have 6 undirected edges. Because hex edges are symmetric and uniform (no directional bias in the base solver), adjacency is a symmetric binary relation over the tile set.

**Notation:** `T_a ~ T_b` means tile `T_a` may appear in a hex cell that is adjacent to a hex cell containing `T_b`. The relation is symmetric: `T_a ~ T_b ↔ T_b ~ T_a`.

### Canonical Adjacency Table

`✓` = legally adjacent | `✗` = forbidden | adjacency is **forbidden by default** (whitelist only)

|            | OCEAN | COAST | GRASS | ROAD | RIVER | FOREST | CITY | MOUNTAIN |
|------------|:-----:|:-----:|:-----:|:----:|:-----:|:------:|:----:|:--------:|
| **OCEAN**  |   ✓   |   ✓   |   ✗   |  ✗   |   ✓   |   ✗    |  ✗   |    ✗     |
| **COAST**  |   ✓   |   ✓   |   ✓   |  ✓   |   ✓   |   ✓    |  ✓   |    ✗     |
| **GRASS**  |   ✗   |   ✓   |   ✓   |  ✓   |   ✓   |   ✓    |  ✓   |    ✓     |
| **ROAD**   |   ✗   |   ✓   |   ✓   |  ✓   |   ✗   |   ✓    |  ✓   |    ✗     |
| **RIVER**  |   ✓   |   ✓   |   ✓   |  ✗   |   ✓   |   ✓    |  ✗   |    ✓     |
| **FOREST** |   ✗   |   ✓   |   ✓   |  ✓   |   ✓   |   ✓    |  ✗   |    ✓     |
| **CITY**   |   ✗   |   ✓   |   ✓   |  ✓   |   ✗   |   ✗    |  ✓   |    ✗     |
| **MOUNTAIN**|  ✗   |   ✗   |   ✓   |  ✗   |   ✓   |   ✓    |  ✗   |    ✓     |

### Adjacency Rationale (non-normative, informational)

| Rule | Rationale |
|------|-----------|
| `OCEAN ✗ GRASS` | No land-cliffs; ocean must first transition through COAST |
| `OCEAN ✗ MOUNTAIN` | Mountain ranges do not meet the sea without a coastal transition |
| `COAST ✗ MOUNTAIN` | Mountains do not meet shore directly; GRASS or FOREST must intervene |
| `ROAD ✗ RIVER` | Roads cross rivers only via a BRIDGE tile (not in V1 tile set; add BRIDGE in V2) |
| `ROAD ✗ MOUNTAIN` | Roads cannot traverse mountains without engineering; MOUNTAIN is impassable |
| `CITY ✗ RIVER` | Cities do not directly border rivers (flood risk, no river-city adjacency in V1) |
| `CITY ✗ FOREST` | Urban expansion does not directly abut forest (deforestation rule deferred to V2) |
| `CITY ✗ MOUNTAIN` | Cities require flat, low-elevation terrain |

### Edge Type Encoding (for directed solvers)

Each tile exposes a single edge class on all 6 sides (non-directional solver):

| Tile     | Edge class |
|----------|------------|
| OCEAN    | `WATER`    |
| COAST    | `SHORE`    |
| GRASS    | `LAND`     |
| ROAD     | `LAND`     |
| RIVER    | `FLOW`     |
| FOREST   | `LAND`     |
| CITY     | `URBAN`    |
| MOUNTAIN | `HIGH`     |

**Edge compatibility rule:**
```
edge_class_a ~ edge_class_b  ↔  (tile_a, tile_b) ∈ adjacency_table
```

The edge class encoding is informational. The adjacency table (§2 above) is authoritative. Any conflict between edge class logic and the table → the table wins.

---

## §3 — Seed Rule (Determinism Anchor)

```
world_seed = sha256_hex("CONQUESTLAND" + str(tick_id) + str(sov_hash))
```

Where:
- `"CONQUESTLAND"` is the literal ASCII string prefix (frozen; no locale variation)
- `tick_id` is the decimal integer tick number (e.g. `"36"`, not `"036"`)
- `sov_hash` is the `manifest_hash` of the current sovereign ledger tail (64 hex chars)
- `sha256_hex(s)` = SHA256 of UTF-8 bytes of `s`, hex-encoded, lowercase

**Example (tick 36, sovereign tail = all-zeros genesis):**
```
world_seed = sha256_hex("CONQUESTLAND36" + "0" * 64)
           = sha256_hex("CONQUESTLAND36" + "000...000")
```

**Sub-seed for retries (see §5 Contradiction Rule):**
```
retry_seed = sha256_hex(world_seed + str(patch_id) + str(retry_count))
```

Sub-seeds prevent retry runs from producing the same contradiction.

**Solver RNG initialization:**
```python
import hashlib, random
rng = random.Random(int(world_seed[:16], 16))   # first 64 bits of seed as int
```

Using the first 64 bits of a SHA256 hex string yields a reproducible, uniform seed for `random.Random`. `PYTHONHASHSEED` must be set to `"0"` for the process running the solver.

---

## §4 — Solver Determinism Rule

The solver MUST be deterministic: **same `world_seed` + same `boundary_constraints_hash` → same `canonical_payload_hash`**.

Requirements:

1. **Seeded RNG** — all stochastic choices use `random.Random(seed)` initialized from `world_seed`. No `random.random()`, no `numpy.random`, no OS entropy.
2. **Sorted collapse order** — cells are processed in ascending `(q, r)` sort order (primary `q`, secondary `r`), not in hash-randomized order. The solver may optionally shuffle with the seeded RNG, but if it does, the shuffle must be the first RNG call.
3. **Deterministic candidate selection** — when multiple tiles are legal for a cell, the solver selects from `sorted(legal_tiles)`. No set-iteration order dependence.
4. **`PYTHONHASHSEED=0`** — must be set in the solver subprocess environment to neutralize Python dict/set hash randomization.
5. **No mutable global state** — solver is a pure function from `(hex_cells, world_seed, boundary_constraints)` to `(hex_cells_with_tiles, repair_events)`. No class attributes, no module-level counters.

**Violation of any requirement → `canonical_payload_hash` is non-reproducible → `WORLD_PATCH_GEN_V1` receipt is invalid → patch is not admissible.**

---

## §5 — Contradiction Rule

A **contradiction** occurs when a hex cell has no legal tile assignment given the already-placed neighbors (the intersection of all neighbor adjacency sets is empty).

### Resolution Protocol

```
for retry in range(k=3):
    attempt local patch solve with retry_seed(world_seed, patch_id, retry)
    if contradiction:
        continue
    else:
        emit WORLD_PATCH_GEN_V1 receipt (status="ok")
        return

# All k retries exhausted
emit WORLD_CONTRADICTION_V1 receipt (resolution="ARBITRATION_REQUIRED")
halt solver for this patch
```

### Hard Rules

- **k = 3** (frozen for MVP; increase requires new spec version)
- **No wildcard insertion** — the solver must never insert an unlisted tile (e.g., `VOID`, `PLAIN`, `WILDCARD`) to resolve a contradiction. The contradiction must be surfaced as `WORLD_CONTRADICTION_V1`.
- **No silent retry without receipt** — each retry attempt is recorded in `repair_events` of the eventual receipt. If all retries fail, the contradiction receipt carries the full retry log.
- **No cross-patch contamination** — a contradiction in patch `P` does not alter already-committed neighbor patches. Each patch is solved in isolation.

### Contradiction Arbitration Flow

```
WORLD_CONTRADICTION_V1 emitted
        ↓
Human or HELEN reviews neighboring constraints
        ↓
Relaxation authorized via CONSTRAINT_RELAXATION_RECEIPT_V1
        ↓
Solver re-runs patch from world_seed (not retry_seed)
with the new relaxed boundary_constraints_hash
        ↓
WORLD_PATCH_GEN_V1 emitted on success
```

A `CONSTRAINT_RELAXATION_RECEIPT_V1` is required before any re-solve after a contradiction. It is out of scope for this spec (V2 artifact).

---

## §6 — Receipt Schemas

### 6.1 — WORLD_PATCH_GEN_V1

Emitted when a patch is successfully solved.

```json
{
  "artifact_type":             "WORLD_PATCH_GEN_V1",
  "tile_spec_version":         "CONQUEST_WFC_SPEC_V1",
  "solver_version":            "WFC_SOLVER_V1",
  "patch_id":                  "<string — unique patch identifier, e.g. 'patch_0x3y2'>",
  "tick_id":                   "<integer>",
  "world_seed":                "<sha256 hex — 64 chars>",
  "boundary_constraints_hash": "<sha256 hex — 64 chars>",
  "hexes": [
    {
      "q":                   "<integer — axial coordinate>",
      "r":                   "<integer — axial coordinate>",
      "tile":                "<one of: OCEAN|COAST|GRASS|ROAD|RIVER|FOREST|CITY|MOUNTAIN>",
      "generation_entropy":  "<float 0.0–1.0 — RNG sample at collapse time>"
    }
  ],
  "repair_events": [
    {
      "hex_q":       "<integer>",
      "hex_r":       "<integer>",
      "attempt":     "<integer 1..k>",
      "reason":      "contradiction_retry",
      "resolved_to": "<tile>"
    }
  ],
  "canonical_payload_hash":    "<sha256 hex — SHA256 of canonical_payload>",
  "status":                    "ok"
}
```

**`canonical_payload_hash` derivation (must be exactly reproducible):**

```python
import json, hashlib

def canonical_payload(hexes):
    # Sorted by (q, r) ascending
    sorted_hexes = sorted(hexes, key=lambda h: (h["q"], h["r"]))
    # Omit generation_entropy from hash (informational only)
    payload = [{"q": h["q"], "r": h["r"], "tile": h["tile"]} for h in sorted_hexes]
    canon   = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
```

**`boundary_constraints_hash` derivation:**

```python
def boundary_constraints_hash(border_cells):
    # border_cells: list of {"q", "r", "required_tile"} or {"q", "r", "forbidden_tiles": [...]}
    sorted_bc = sorted(border_cells, key=lambda c: (c["q"], c["r"]))
    canon     = json.dumps(sorted_bc, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
```

**Required fields:** `artifact_type`, `tile_spec_version`, `solver_version`, `patch_id`, `tick_id`, `world_seed`, `boundary_constraints_hash`, `hexes`, `canonical_payload_hash`, `status`.
**Optional fields:** `repair_events` (may be `[]`).
**Forbidden:** any tile value not in the V1 tile set (OCEAN, COAST, GRASS, ROAD, RIVER, FOREST, CITY, MOUNTAIN).

---

### 6.2 — WORLD_CONTRADICTION_V1

Emitted when all `k` retries are exhausted without resolving the contradiction.

```json
{
  "artifact_type":             "WORLD_CONTRADICTION_V1",
  "tile_spec_version":         "CONQUEST_WFC_SPEC_V1",
  "solver_version":            "WFC_SOLVER_V1",
  "patch_id":                  "<string — same patch_id as the failed attempt>",
  "tick_id":                   "<integer>",
  "world_seed":                "<sha256 hex — 64 chars>",
  "boundary_constraints_hash": "<sha256 hex — 64 chars>",
  "contradiction_hex": {
    "q":               "<integer — axial coordinate of contradiction cell>",
    "r":               "<integer — axial coordinate of contradiction cell>"
  },
  "retry_count":               "<integer — always k=3 for MVP>",
  "retry_seeds":               ["<sha256 hex>", "<sha256 hex>", "<sha256 hex>"],
  "neighbor_terrains":         ["<tile>", ...],
  "candidate_tiles_before_contradiction": [],
  "repair_attempts": [
    {
      "attempt":          "<integer 1..k>",
      "retry_seed":       "<sha256 hex>",
      "resolved":         false,
      "contradiction_at": { "q": "<integer>", "r": "<integer>" }
    }
  ],
  "resolution":                "ARBITRATION_REQUIRED",
  "canonical_payload_hash":    "<sha256 hex — SHA256 of canonical_payload of this receipt>",
  "status":                    "contradiction"
}
```

**`canonical_payload_hash` for contradiction receipts:**

```python
def contradiction_canonical_payload(receipt_dict):
    # Hash of the contradiction fields (excluding canonical_payload_hash itself)
    fields = {k: v for k, v in receipt_dict.items() if k != "canonical_payload_hash"}
    canon  = json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
```

**Required fields:** all fields above.
**`resolution`:** always `"ARBITRATION_REQUIRED"` (no automatic resolution).
**`status`:** always `"contradiction"` (never `"ok"`).

---

## §7 — Replay Acceptance Test

**Specification (MUST pass for any conformant solver implementation):**

```
Given:
    world_seed               = sha256_hex("CONQUESTLAND36" + "0" * 64)
    boundary_constraints     = []   # no boundary constraints (open patch)
    patch_cells              = [(q, r) for (q, r) in [(0,0),(1,0),(0,1),(-1,1),(-1,0),(0,-1),(1,-1)]]
                               # 7-cell hex rosette

Assert:
    run_1 = solve(patch_cells, world_seed, boundary_constraints)
    run_2 = solve(patch_cells, world_seed, boundary_constraints)

    run_1.canonical_payload_hash == run_2.canonical_payload_hash   # MUST hold
    run_1.status == "ok"                                           # MUST hold
    all(h["tile"] in TILE_SET for h in run_1.hexes)                # MUST hold
    all(are_legal_neighbors(h1["tile"], h2["tile"])
        for (h1, h2) in adjacent_pairs(run_1.hexes))               # MUST hold
```

**Test harness invocation:**

```bash
PYTHONHASHSEED=0 python -m pytest conquest/tests/test_wfc_replay.py -v
# Expected: test_wfc_replay_determinism PASSED
#           test_wfc_no_illegal_adjacency PASSED
#           test_wfc_tile_set_conformance PASSED
```

**Replay test also covers contradiction path:**

```
Given:
    # Impossible constraint: force OCEAN surrounded by MOUNTAIN
    boundary_constraints = [
        {"q":  1, "r":  0, "required_tile": "MOUNTAIN"},
        {"q":  0, "r":  1, "required_tile": "MOUNTAIN"},
        {"q": -1, "r":  1, "required_tile": "MOUNTAIN"},
        {"q": -1, "r":  0, "required_tile": "MOUNTAIN"},
        {"q":  0, "r": -1, "required_tile": "MOUNTAIN"},
        {"q":  1, "r": -1, "required_tile": "MOUNTAIN"},
    ]
    forced_center = {"q": 0, "r": 0, "required_tile": "OCEAN"}

Assert:
    result.status == "contradiction"
    result.resolution == "ARBITRATION_REQUIRED"
    result.retry_count == 3
    result.canonical_payload_hash is not None   # contradiction receipt is still hashed
```

---

## §8 — Tile Set Governance

### Adding New Tiles

To add a new tile (e.g., `BRIDGE`, `DESERT`, `MARSH`):

1. Draft a `TILE_AMENDMENT_V1` proposal (proposal_id format: `PROP_TILE_<NAME>`)
2. Specify: tile properties, edge class, full row/column update to adjacency matrix
3. Receipt: `TILE_AMENDMENT_RECEIPT_V1` with `sha256` of new adjacency table
4. Bump spec version: `CONQUEST_WFC_SPEC_V2`
5. Migration receipt required for any already-admitted patches that may be affected

### Modifying Adjacency Rules

Changing `T_a ~ T_b` from `✓` to `✗` or vice versa:
- Requires new spec version
- Requires `ADJACENCY_MIGRATION_RECEIPT_V1` listing all affected patch IDs
- Already-admitted patches remain valid under the spec version under which they were admitted

### Frozen Fields

The following are frozen for `CONQUEST_WFC_SPEC_V1` and may not change without a version bump:
- `k = 3` (retry limit)
- Seed prefix `"CONQUESTLAND"` (string literal)
- `canonical_payload_hash` derivation algorithm (§6.1)
- `PYTHONHASHSEED=0` requirement
- Sorted collapse order by `(q, r)`
- All 8 tile IDs and their `artifact_type` identifiers

---

## §9 — Integration Boundary

**What WFC may do:**
- Read `(q, r, boundary_constraints)` input
- Assign a tile from the V1 tile set to each cell
- Log repair events (retries, contradiction recovery)
- Return `(hex_cells_with_tiles, repair_events)`

**What WFC must never do:**
- Append to the sovereign ledger
- Emit a receipt itself (the caller emits the receipt)
- Assign overlay state (`CLAIMED`, `SEALED`, etc.)
- Access player state, sovereignty records, or duel outcomes
- Insert a tile not in the V1 canonical set

**Module boundary (correct integration):**

```
conquest/terrain_wfc.py         ← solver (pure function)
conquest/tiles.py               ← tile registry (read-only)
conquest/adjacency.py           ← adjacency matrix (read-only)
conquest/world_receipt.py       ← receipt emitter (called by orchestrator)
integration/worldgen_bridge.py  ← orchestrator: calls solver + emits receipt
helen/receipt_authority/world_gen_validators.py  ← receipt validation
```

The orchestrator (`worldgen_bridge.py`) is the only module that:
1. Calls the solver
2. Calls `emit_world_patch_receipt(result)` → produces `WORLD_PATCH_GEN_V1`
3. Appends the receipt to the ledger (Phase 2 harness only)

---

## §10 — Relation to Existing CONQUEST_TILES_V0_1

`CONQUEST_TILES_V0_1` defines a richer tile set (13 terrain types, 11 structure types, 10 overlay types). `CONQUEST_WFC_SPEC_V1` does not replace it; it **narrows** the terrain set used by the WFC solver to 8 canonical types.

Mapping from V0_1 names to WFC V1 names:

| V0_1 Name  | WFC V1 Name | Notes                            |
|------------|-------------|----------------------------------|
| `SEA`      | `OCEAN`     | Renamed for clarity              |
| `COAST`    | `COAST`     | Identical                        |
| `PLAIN`    | `GRASS`     | Renamed; same semantics          |
| `ROAD`     | `ROAD`      | Identical                        |
| `RIVER`    | `RIVER`     | Identical                        |
| `FOREST`   | `FOREST`    | Identical                        |
| `MOUNTAIN` | `MOUNTAIN`  | Identical                        |
| `TOWN`/`CITY` structure on `PLAIN` | `CITY` | Collapsed to single terrain tile |
| `HILL`, `MARSH`, `DESERT`, `LAKE`, `BRIDGE`, `VOID` | — | Not in WFC V1 set; may be added via tile amendment |

The WFC solver uses V1 names internally. The receipt stores V1 names. The world validator maps V1 → V0_1 names for display if needed.

---

## Appendix A — Canonical JSON Rules (CANON_JSON_V1)

All hash computations in this spec use:
- `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
- Encoding: UTF-8
- Hash function: SHA256
- Output format: lowercase hex, 64 characters

No BOM. No trailing newline in hash input. Leading/trailing whitespace stripped before hashing.

---

## Appendix B — Spec Metadata

```yaml
spec_id:          CONQUEST_WFC_SPEC_V1
version:          1.0.0
status:           FROZEN
authors:          [HELEN OS kernel, HAL architectural review]
date_frozen:      2026-03-11
tile_count:       8
receipt_types:    [WORLD_PATCH_GEN_V1, WORLD_CONTRADICTION_V1]
retry_limit_k:    3
seed_prefix:      "CONQUESTLAND"
hash_algorithm:   SHA256
rng_class:        python_random_Random
pythonhashseed:   "0"
collapse_order:   sorted_by_q_then_r
governed_by:      LAW_HELEN_BOUNDED_EMERGENCE_V1
law_surface_version: LAW_SURFACE_V1
```

---

*End of CONQUEST_WFC_SPEC_V1. No additions or modifications without version bump.*
