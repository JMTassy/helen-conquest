# Oracle Town Memory System — Complete Index

## Quick Navigation

### 📘 Documentation (Read These First)

| Document | Purpose | Audience |
|----------|---------|----------|
| **oracle_town/memory/README.md** | Complete architecture overview | Everyone |
| **oracle_town/memory/SETUP.md** | Cron job configuration | DevOps/Operators |
| **ORACLE_TOWN_MEMORY_SYSTEM_COMPLETE.md** | Implementation summary | Technical leads |
| **ORACLE_TOWN_MEMORY_INTEGRATION_GUIDE.md** | How to wire into governance | Developers |

### 🛠️ Tools (Use These)

| Tool | Location | Purpose | Usage |
|------|----------|---------|-------|
| **cycle_observer.py** | `oracle_town/memory/tools/cycle_observer.py` | Real-time extraction (every 30 min) | `python3 ... --scan-runs` |
| **weekly_synthesizer.py** | `oracle_town/memory/tools/weekly_synthesizer.py` | Weekly synthesis (Sundays 03:10) | `python3 oracle_town/memory/tools/weekly_synthesizer.py` |
| **memory_lookup.py** | `oracle_town/memory/tools/memory_lookup.py` | Advisory API for decisions | `from oracle_town.memory.tools import MemoryLookup` |

### 📊 Data Structures

| Structure | Location | Content | Access |
|-----------|----------|---------|--------|
| **Knowledge Graph** | `oracle_town/memory/entities/` | Facts (append-only) | File I/O |
| **Daily Logs** | `oracle_town/memory/daily/` | Cycle transcripts | File I/O |
| **Tacit Knowledge** | `oracle_town/memory/tacit/` | Heuristics & rules | File I/O |
| **Metadata** | `oracle_town/memory/meta/` | Schemas, checkpoints | File I/O |

---

## Getting Started (5 Minutes)

### 1. Verify Installation
```bash
ls -la oracle_town/memory/
# Should show: daily, entities, tacit, tools, meta, README.md, SETUP.md
```

### 2. Test Extraction
```bash
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs
# Output: Processed 3 runs, extracted facts
```

### 3. Test Synthesis
```bash
python3 oracle_town/memory/tools/weekly_synthesizer.py
# Output: Processed 3 entities, regenerated summaries
```

### 4. Test Advisory API
```bash
python3 oracle_town/memory/tools/memory_lookup.py --demo
# Output: Full advisory context with heuristics and decisions
```

### 5. Check What Was Learned
```bash
cat oracle_town/memory/tacit/heuristics.md
cat oracle_town/memory/tacit/rules_of_thumb.md
```

---

## Using Memory in Code (5 Minutes)

### Import the API
```python
from oracle_town.memory.tools import MemoryLookup
lookup = MemoryLookup()
```

### Get Advisory Context
```python
advisory = lookup.get_advisory_context()
# Returns: heuristics, rules, recent_decisions, lane_performance, etc.
```

### Use in Governance Logic
```python
# Check heuristics (advisory only)
heuristics = lookup.get_heuristics()
if "Quorum-by-class succeeded" in heuristics:
    print("Advisory: Use quorum-by-class")

# But always apply policy deterministically
if policy.apply_quorum_rule(attestations):
    return "SHIP"
else:
    return "NO_SHIP"
```

### Full Example
See: **ORACLE_TOWN_MEMORY_INTEGRATION_GUIDE.md** (Examples 1-5)

---

## Architecture at a Glance

```
ORACLE TOWN GOVERNANCE CYCLE
         ↓
    [Intake Guard]
         ↓
    [Districts] ← Get memory context (optional)
         ↓
    [Town Hall]
         ↓
    [Mayor RSM] ← Get memory context (optional)
         ↓
    [Ledger] ← Log decision
         ↓
    [Cycle Observer] ← Extract facts every 30 min
         ↓
    [Memory Entities] ← Append to items.json
         ↓
    [Weekly Synthesizer] ← Regenerate summaries (weekly)
         ↓
    [Heuristics.md] ← Updated with patterns
         ↓
    [Future Cycles] ← Use learned wisdom
```

---

## Three-Layer Memory

### Layer 1: Knowledge Graph (Entities)
**Files:** `oracle_town/memory/entities/{type}/{slug}/items.json`

Example fact:
```json
{
  "id": "quorum-abc123",
  "fact": "Quorum-by-class with N=2 succeeded",
  "timestamp": "2026-01-28T21:00:00",
  "status": "active",
  "category": "pattern_success",
  "confidence": 1.0
}
```

Key property: Never deleted, only superseded (transparent history)

### Layer 2: Daily Logs (Events)
**Files:** `oracle_town/memory/daily/cycle-{NNN}.json`

Example log:
```json
{
  "cycle_num": 1,
  "timestamp": "2026-01-28T21:00:00",
  "decision": "SHIP",
  "facts_extracted": 5
}
```

Key property: Raw transcript of what happened and when

### Layer 3: Tacit Knowledge (Wisdom)
**Files:** `oracle_town/memory/tacit/heuristics.md`, `rules_of_thumb.md`

Example:
```markdown
## K-Invariant Patterns
- K0: Authority Separation — Always enforced
- K3: Quorum-by-Class — Works with N=2+
- K5: Determinism — Never violated

## Lane Effectiveness
1. Stability (30%)
2. Velocity (20%)
3. Democracy (15%)
...
```

Key property: Learned from evidence, human-readable

---

## Common Tasks

### Task: Check Memory State
```bash
python3 oracle_town/memory/tools/memory_lookup.py --demo
```

### Task: Manually Extract Facts
```bash
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs
```

### Task: Manually Synthesize
```bash
python3 oracle_town/memory/tools/weekly_synthesizer.py
```

### Task: See What Memory Knows About Decisions
```bash
cat oracle_town/memory/entities/decisions/*/summary.md
```

### Task: See What Memory Knows About K-Violations
```bash
cat oracle_town/memory/entities/invariant_events/*/summary.md
```

### Task: Check Extraction Logs
```bash
tail -f oracle_town/memory/meta/extraction.log
```

### Task: Check Synthesis Logs
```bash
tail -f oracle_town/memory/meta/synthesis.log
```

---

## Safety Guarantees

✅ **K-Invariants never overridden** — Memory is advisory only
✅ **Complete auditability** — All facts timestamped, categorized, versioned
✅ **Self-correcting** — Newer facts supersede contradictions
✅ **Fail-safe** — Governance continues even if memory missing

---

## Cost Model

| Component | Cost | Frequency |
|-----------|------|-----------|
| Extraction | $0.02 | Every 30 min |
| Synthesis | $0.10 | Weekly |
| Lookup | Free | Per decision |
| **Total** | **<1% overhead** | Negligible |

---

## File Structure

```
oracle_town/memory/
├── README.md                              # Full guide
├── SETUP.md                               # Cron configuration
├── daily/                                 # Raw cycle logs
│   ├── cycle-001.json
│   ├── cycle-002.json
│   └── ...
├── entities/                              # Knowledge graph
│   ├── decisions/
│   │   ├── run-001-claim-001/
│   │   │   ├── items.json                # Facts
│   │   │   └── summary.md                # Summary
│   │   └── ...
│   ├── invariant_events/                 # K-violations
│   ├── lane_performance/                 # Lane metrics
│   ├── emergence_signals/                # Convergence
│   └── proposal_archetypes/              # (future)
├── tacit/                                 # Practical wisdom
│   ├── heuristics.md                     # Learned patterns
│   └── rules_of_thumb.md                 # Decision guidance
├── tools/                                 # Python modules
│   ├── __init__.py
│   ├── cycle_observer.py                 # Extraction
│   ├── weekly_synthesizer.py             # Synthesis
│   └── memory_lookup.py                  # Advisory API
└── meta/                                  # System files
    ├── fact_schema.json                  # Data schema
    ├── checkpoints.json                  # Extraction state
    ├── extraction.log                    # Extraction runs
    └── synthesis.log                     # Synthesis runs
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Memory lookup returns empty | Run `cycle_observer.py --scan-runs` to extract facts |
| Extraction doesn't run | Check cron: `crontab -l` and `tail -f oracle_town/memory/meta/extraction.log` |
| Synthesis failing | Run manually: `python3 oracle_town/memory/tools/weekly_synthesizer.py` |
| Memory growing too large | Normal — facts are text, check with `du -sh oracle_town/memory/` |
| Can't import MemoryLookup | Make sure you're in the right directory: `cd JMT\ CONSULTING\ -\ Releve\ 24` |

---

## References

| Document | Purpose |
|----------|---------|
| `oracle_town/memory/README.md` | Architecture and concepts |
| `oracle_town/memory/SETUP.md` | Cron job setup |
| `ORACLE_TOWN_MEMORY_SYSTEM_COMPLETE.md` | Implementation details |
| `ORACLE_TOWN_MEMORY_INTEGRATION_GUIDE.md` | Code integration examples |
| `oracle_town/schemas/decision_record.schema.json` | Decision format |
| `CLAUDE.md` | Project overview |

---

## One-Liner Commands

```bash
# Extract facts now
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs

# Synthesize now
python3 oracle_town/memory/tools/weekly_synthesizer.py

# See advisory context
python3 oracle_town/memory/tools/memory_lookup.py --demo

# Watch extraction logs
tail -f oracle_town/memory/meta/extraction.log

# Check memory size
du -sh oracle_town/memory/

# List all facts
find oracle_town/memory/entities -name items.json -exec cat {} \;

# See heuristics
cat oracle_town/memory/tacit/heuristics.md

# See rules of thumb
cat oracle_town/memory/tacit/rules_of_thumb.md
```

---

## Next Steps

1. **Read** `oracle_town/memory/README.md`
2. **Setup** cron jobs (see `oracle_town/memory/SETUP.md`)
3. **Test** extraction and synthesis (commands above)
4. **Integrate** with governance (see `ORACLE_TOWN_MEMORY_INTEGRATION_GUIDE.md`)
5. **Monitor** logs and memory growth

---

**Oracle Town is now learning from itself.**

For detailed information, see the full documentation in the files listed above.
