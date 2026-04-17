# Oracle Town Skills

MCP skills for CONQUEST game system with K-gate enforcement.

## Available Skills

### Map Generator Skill

**Status:** ✅ MVP Complete

Procedural map generation for CONQUEST with K-gate enforcement:
- **K1 (Fail-Closed):** Missing parameters rejected
- **K2 (No Self-Validation):** Generates LP-### claim for Foreman approval
- **K5 (Determinism):** Same seed = identical map (cached)
- **K7 (Policy Pinning):** Map hash locked in JSONL ledger per game

**Files:**
- `map_generator_skill.py` — Main skill class (308 lines)
- `procedural_map.py` — Core generation algorithm (234 lines)
- `claim_workflow.py` — K2 claim curation workflow (250 lines)
- `ledger_reader.py` — K7 ledger reader + auditing (180 lines)

**Quick Start:**

```python
from oracle_town.skills.map_generator_skill import MapGeneratorSkill

skill = MapGeneratorSkill()
result = skill.generate_map(seed=111, game_id="game_001")

if result["status"] == "success":
    print(f"Generated {len(result['map_data']['territories'])} territories")
```

**Tests:** 47 passing tests in `tests/`
- `test_map_generator_skill.py` — K-gate validation (21 tests)
- `test_k2_k7_workflow.py` — Claim + ledger workflow (15 tests)
- `test_conquest_map_generator_integration.py` — CONQUEST integration (11 tests)

**Documentation:** See `docs/MAP_GENERATOR_SKILL_MVP.md` for complete guide

---

## Architecture

### K-Gate Enforcement Flow

```
User Request (seed, game_id)
  ↓
K1: Validate input (fail-closed)
  ↓
K5: Check cache (determinism)
  ├─ Cache hit → return cached map
  └─ Cache miss → generate new map
  ↓
K7: Compute hash + write ledger (policy pinning)
  ↓
K2: Generate LP-### claim (no self-validation)
  ↓
Response: {status, map_data, validation_results, claim, ledger_entry_id}
```

### Component Responsibilities

| Component | Responsibility |
|-----------|-----------------|
| `MapGeneratorSkill` | Orchestrates generation, enforces K-gates, produces claim |
| `ProceduralMapGenerator` | Core Voronoi-like partitioning + terrain/climate |
| `ClaimWorkflow` | K2 workflow: pending → accepted/rejected |
| `LedgerReader` | K7 ledger: read, audit, verify hash consistency |

---

## File Structure

```
oracle_town/skills/
├── __init__.py
├── README.md (this file)
├── map_generator_skill.py      # Main skill (K1, K2, K5, K7)
├── procedural_map.py           # Generation algorithm
├── claim_workflow.py           # K2 workflow manager
└── ledger_reader.py            # K7 ledger reader

tests/
├── test_map_generator_skill.py             # 21 tests (K1, K5, K7, K2)
├── test_k2_k7_workflow.py                  # 15 tests (workflow + ledger)
└── test_conquest_map_generator_integration.py  # 11 tests (CONQUEST)

kernel/ledger/
└── map_generation_records.jsonl  # K7 immutable ledger (JSONL)

artifacts/
└── map_cache/
    ├── map_seed_111.json
    ├── map_seed_222.json
    └── ...                      # K5 cache by seed

docs/
└── MAP_GENERATOR_SKILL_MVP.md  # Complete MVP documentation
```

---

## Testing

### Run All Tests

```bash
source .venv/bin/activate
python3 -m pytest tests/test_map_generator_skill.py \
                  tests/test_k2_k7_workflow.py \
                  tests/test_conquest_map_generator_integration.py \
                  -v
```

**Expected Output:** 47 passed

### Test Coverage by K-Gate

```bash
# K1 Fail-Closed (5 tests)
pytest tests/test_map_generator_skill.py::TestK1FailClosedValidation -v

# K5 Determinism (5 tests)
pytest tests/test_map_generator_skill.py::TestK5Determinism -v

# K7 Policy Pinning (5 tests)
pytest tests/test_map_generator_skill.py::TestK7PolicyPinning -v

# K2 No Self-Validation (3 tests)
pytest tests/test_map_generator_skill.py::TestK2NoSelfValidation -v

# K2+K7 Workflow (5 tests)
pytest tests/test_k2_k7_workflow.py::TestK2ClaimWorkflow -v

# Ledger Operations (8 tests)
pytest tests/test_k2_k7_workflow.py::TestK7LedgerReader -v

# CONQUEST Integration (11 tests)
pytest tests/test_conquest_map_generator_integration.py -v
```

---

## Usage Examples

### Basic Map Generation

```python
from oracle_town.skills.map_generator_skill import MapGeneratorSkill

skill = MapGeneratorSkill()
result = skill.generate_map(seed=111, game_id="game_001")

map_data = result["map_data"]
territories = map_data["territories"]
tiles = map_data["tile_map"]

print(f"Map size: {map_data['width']}×{map_data['height']}")
print(f"Territories: {len(territories)}")
```

### K5 Determinism Check

```python
# Same seed produces same output
result1 = skill.generate_map(seed=111, game_id="game_1")
result2 = skill.generate_map(seed=111, game_id="game_2")

assert result1["map_data"] == result2["map_data"]  # ✅
print("K5 Determinism: PASS")
```

### K7 Ledger Verification

```python
from oracle_town.skills.ledger_reader import LedgerReader

ledger = LedgerReader()
entries = ledger.read_all_entries()

for entry in entries:
    print(f"Game: {entry['game_id']}")
    print(f"Seed: {entry['seed']}")
    print(f"Hash: {entry['map_hash'][:16]}...")
```

### K2 Claim Workflow

```python
from oracle_town.skills.claim_workflow import ClaimWorkflow, Claim

workflow = ClaimWorkflow()

# Skill proposes claim
claim = Claim(
    claim_id="LP-MAP-game_001",
    type="map_generation",
    author="MapGeneratorSkill",
    statement="Map generated for game_001 with 6 territories"
)
workflow.propose_claim(claim)

# Foreman reviews
pending = workflow.get_pending_claims()
print(f"Pending claims: {len(pending)}")

# Foreman approves
workflow.accept_claim("LP-MAP-game_001", "Foreman", "Map approved")
accepted = workflow.get_accepted_claims()
print(f"Accepted: {len(accepted)}")
```

### CONQUEST Integration

```python
from oracle_town.skills.map_generator_skill import MapGeneratorSkill
from conquest_v2_hexacycle import HexaCycleGame

# Generate map
skill = MapGeneratorSkill()
result = skill.generate_map(seed=111, game_id="conquest_001")

# Initialize CONQUEST with same seed
game = HexaCycleGame(seed=111)
winner = game.run_simulation()

# K5: Deterministic outcome
print(f"Winner: {winner.name}")
print(f"Territory: {winner.territory_count()} tiles")
```

---

## K-Gate Details

### K1: Fail-Closed Default

**Rule:** Missing evidence → REJECT (never guess)

```python
result = skill.generate_map(seed=None, game_id="game_001")
assert result["status"] == "validation_failed"
assert "SEED_REQUIRED" in result["error"]
```

### K2: No Self-Edit

**Rule:** Proposer ≠ Validator

The skill generates the claim but cannot approve it. Foreman must approve.

```python
claim = result["claim"]
assert claim["status"] == "pending"  # Awaiting approval
assert claim["author"] == "MapGeneratorSkill"
```

### K5: Determinism

**Rule:** Same seed → identical output (all RNG seeded)

```python
# Uses numpy.random.RandomState(seed) for reproducibility
# Cached to artifacts/map_cache/map_seed_{seed}.json
# Second call returns cached version instantly
```

### K7: Policy Pinning

**Rule:** Map hash locked per game (immutable ledger)

```python
# SHA256(JSON(map_data)) stored in JSONL ledger
# kernel/ledger/map_generation_records.jsonl
# Prevents mid-game map modifications
```

---

## Configuration

### Custom Paths

```python
skill = MapGeneratorSkill(
    cache_dir="custom/cache",
    ledger_path="custom/ledger.jsonl"
)

workflow = ClaimWorkflow(
    pending_path="custom/pending.md",
    accepted_path="custom/accepted.md",
    rejected_path="custom/rejected.md"
)

ledger = LedgerReader("custom/ledger.jsonl")
```

### Dry Run (No Ledger Write)

```python
result = skill.generate_map(
    seed=111,
    game_id="test",
    validate_only=True
)
assert result["ledger_entry_id"] is None  # No ledger write
```

---

## Performance

- **Map Generation:** ~1ms (cached)
- **Cache Retrieval:** <0.1ms
- **Ledger Write:** ~0.5ms (JSONL append)
- **Hash Computation:** ~0.2ms (SHA256)

---

## Next Steps

1. **CONQUEST Integration:** Wire into game initialization
2. **UZIK Visualization:** Generate card layouts from map
3. **Foreman Workflow:** Full K2 approval enforcement
4. **Enhanced Generation:** Voronoi, rivers, biomes (post-MVP)

---

## Support

For questions or issues:
1. Check test files for examples
2. Review MAP_GENERATOR_SKILL_MVP.md
3. Consult KERNEL_V2.md for constitutional rules

---

**Last Updated:** 2026-04-16 (was 2026-02-20)
**Status:** MVP Ready to Use; Feynman/Voice/Video subtrees fused 2026-04-16
**Tests Passing:** 47/47 ✅ (MVP); fused subtrees untested (deferred F-09)

---

## Fused subtrees (added 2026-04-16, witness chain R-20260416-0002..0009)

```
oracle_town/skills/
├── feynman/
│   ├── peer_review/          K2/Rule 3 enforcer (reviewer ≠ proposer)
│   ├── intent_action_audit/  CONTRADICTION step — records gaps, never resolves
│   └── session_notes/        Narrative artifact — non-ledger, must cite ledger
├── voice/
│   └── gemini_tts/           Gemini 2.5 TTS — voice = transport, never editor
└── video/
    └── hyperframes/          HeyGen HyperFrames — no HELEN self-portraits
```

Each new skill ships `SKILL.md` + `.provenance.md`. Voice/video are gated by `scripts/helen_k8_lint.py` (K8 Non-Determinism Boundary, shipped R-20260416-0008).
