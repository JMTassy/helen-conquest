# MEM District Charter

**Module:** Memory & Precedent Linking

## Purpose

Build and maintain a persistent, diffable knowledge graph linking observations, insights, and decisions across runs. MEM is the historian—it learns from the past and surfaces precedents for future decisions.

## Inputs

**Required (read-only):**
- `oracle_town/ledger/observations.jsonl` (all observations ever)
- `oracle_town/ledger/decisions.jsonl` (all decisions ever)
- `oracle_town/memory/index.json` (current entity index)
- Current run's artifacts (insights, brief, decision)

**No direct state mutations except memory writes.**

## Outputs

**Artifacts produced:**
- `memory/index.json` (updated entity + relationship index)
- `memory/entities/*.json` (individual entity files, append-only)
- `precedents.json` — Similar past decisions for this run's topic
- `mem_receipt.json` — Cryptographic proof

**State mutations:**
- Writes to `city_current.json`: `modules.MEM.progress`, `modules.MEM.status`, `modules.MEM.desc`
- Appends to `oracle_town/memory/entities/` (immutable entity history)

## Memory Index Schema

```json
{
  "entities": {
    "entity_id_001": {
      "type": "person|project|topic|decision",
      "name": "string",
      "status": "active|deprecated|archived",
      "tags": ["tag1", "tag2"],
      "created_run": 150,
      "last_seen_run": 173,
      "links_count": 5
    }
  },
  "relationships": [
    {
      "source": "entity_001",
      "relation": "observed_in|involved_in|blocked_by|enabled_by|similar_to",
      "target": "entity_002",
      "first_run": 150,
      "last_run": 173,
      "strength": 0.8
    }
  ]
}
```

## Entity File Schema

```json
{
  "id": "entity_001",
  "type": "decision",
  "name": "Launch marketing campaign v2",
  "created_run": 150,
  "events": [
    {
      "run": 150,
      "action": "created",
      "brief": "..."
    },
    {
      "run": 152,
      "action": "linked_from",
      "source_id": "obs_xxx"
    }
  ]
}
```

## Precedent Schema

```json
{
  "current_run": 173,
  "current_topic": "...brief summary...",
  "precedents": [
    {
      "past_run": 160,
      "similarity": 0.92,
      "brief": "...",
      "decision": "SHIP|NO_SHIP",
      "outcomes": "...",
      "relevance": "exact match|similar pattern|related"
    }
  ]
}
```

## Gates (Enforced by EVO)

**MEM cannot proceed unless:**
1. Current run's observations linked to entity graph
2. Decision record added to entity history
3. `memory/index.json` valid JSON with sorted keys
4. All entity files append-only (no modifications to past entries)
5. `mem_receipt.json` signed by mem_attestor_001

**Failure mode:** MEM stays WRN; memory becomes stale but doesn't block.

## Determinism Contract

**MEM must guarantee:**
- Same ledger + same entity index → identical precedent list
- Entity linking deterministic (match on name hash, not heuristics)
- No timestamps (only run IDs for versioning)
- Stable sorting: relationships sorted by (source, relation, target)

**Test:** Run MEM twice on same ledger; precedent list hash must match.

## Forbidden Actions

- MEM may NOT modify past decision records
- MEM may NOT delete entities (only deprecate)
- MEM may NOT rewrite relationship history (append-only)
- MEM may NOT add external entities (only from current run's artifacts)

## State Writes Allowed

```json
{
  "modules": {
    "MEM": {
      "status": "OFF|BLD|OK|WRN|FLR",
      "progress": 0-8,
      "desc": "string (max 50 chars)"
    }
  }
}
```

## Receipts Required

```json
{
  "mem_receipt": {
    "timestamp_unix": 1706601600,
    "entities_count": 42,
    "relationships_count": 87,
    "precedents_found": 3,
    "index_hash": "sha256:stu901...",
    "run_id": 173,
    "attestor_id": "mem_attestor_001",
    "signature": "ed25519:mno234..."
  }
}
```

**K0 enforcement:** Only mem_attestor_001 can sign MEM receipts.

## Relationship Types

- **observed_in** — Entity appears in observations
- **involved_in** — Entity mentioned in brief or insights
- **blocked_by** — Entity prevented decision (anomaly)
- **enabled_by** — Entity supported decision (precedent)
- **similar_to** — Entity similar to past decision (precedent candidate)

## Memory Continuity

**Critical invariant:** Memory is immutable and cumulative.

- Never rewrite past entries
- Never delete entities (deprecate instead)
- All new information appended as new events
- Git history shows memory growth over time

This prevents "memory drift" and enables audit trails.

## Integration with Daily OS

**Workflow step:**
```bash
python3 oracle_town/jobs/mem_link.py \
  --observations oracle_town/ledger/observations.jsonl \
  --decisions oracle_town/ledger/decisions.jsonl \
  --current-run-brief artifacts/brief.md \
  --index oracle_town/memory/index.json \
  --output artifacts/precedents.json \
  --receipt artifacts/mem_receipt.json
```

**Parallelizable:** MEM can run alongside PUB (both read-only on decision).

---

**Status:** Charter Active
**Last Updated:** 2026-01-30
