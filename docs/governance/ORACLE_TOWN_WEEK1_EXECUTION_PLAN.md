# Oracle Town Week 1 Real Execution Plan

**How to run Oracle Town's first actual governance cycle with real memory capture.**

---

## Overview

This plan describes how to execute Oracle Town's **actual Day 1 governance cycle** (not simulated, not test harness) and capture its decisions in the memory system.

**Key principle:** We run *your actual governance logic*, record the *real decisions*, and feed them into the memory system for learning.

---

## Prerequisites

✅ Oracle Town governance engine functional (mayor_rsm.py, districts, town_hall, ledger)
✅ Memory system deployed and tested (cycle_observer.py, weekly_synthesizer.py)
✅ Test harness verified (test_harness.py runs successfully)
✅ One governance cycle can be executed (can generate decision_record.json)

---

## Week 1 Execution Steps

### Step 0: Prepare Test Claims

Create a small set of test proposals to run through governance.

**File:** `oracle_town/test_claims.json`

```json
{
  "test_claims": [
    {
      "claim_id": "REAL_001",
      "title": "Launch marketing campaign with email collection",
      "description": "...",
      "source": "real_week1"
    },
    {
      "claim_id": "REAL_002",
      "title": "Update privacy policy for GDPR",
      "description": "...",
      "source": "real_week1"
    },
    {
      "claim_id": "REAL_003",
      "title": "Implement new data retention rules",
      "description": "...",
      "source": "real_week1"
    }
  ]
}
```

These claims will flow through your actual governance cycle.

### Step 1: Run Governance Cycle

Execute your actual Oracle Town governance:

```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24

# Option A: If you have a CLI entry point
python3 oracle_town/cli.py --input oracle_town/test_claims.json --output decisions/REAL_WEEK1.json

# Option B: If you run the orchestrator directly
python3 oracle_town/core/orchestrator.py --claims oracle_town/test_claims.json --output decisions/REAL_WEEK1.json

# Option C: Custom script (depends on your setup)
# python3 my_governance_runner.py
```

**Output:** `decisions/REAL_WEEK1.json` — a decision_record.json with real SHIP/NO_SHIP verdicts

**What gets logged:**
- Each proposal flows through: Intake → Districts → Town Hall → Mayor → Ledger
- Mayor produces binary SHIP/NO_SHIP for each
- Blocking reasons recorded (K-violations, missing evidence, etc.)
- Timestamps and signatures applied

### Step 2: Extract Memory from Real Cycle

Now feed the real governance decisions into the memory system:

```bash
python3 oracle_town/memory/tools/cycle_observer.py 1 decisions/REAL_WEEK1.json
```

Or if your decision file is in decisions/:

```bash
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs
```

**What happens:**
- cycle_observer.py reads decisions/REAL_WEEK1.json
- Extracts facts about decisions, K-violations, proposal archetypes
- Appends to `memory/entities/decisions/`, `memory/entities/invariant_events/`, etc.
- Creates `memory/daily/cycle-001.json` with raw transcript
- Updates `memory/meta/checkpoints.json`

**Verification:**
```bash
# Check that facts were extracted
ls -la oracle_town/memory/entities/decisions/
ls -la oracle_town/memory/daily/

# View extraction log
tail oracle_town/memory/meta/extraction.log
```

### Step 3: Review Memory State

Check what the memory system learned:

```bash
# See decision entities
cat oracle_town/memory/entities/decisions/REAL_WEEK1*/summary.md

# See any K-violations
cat oracle_town/memory/entities/invariant_events/*/summary.md

# See daily log
cat oracle_town/memory/daily/cycle-001.json
```

**What to look for:**
- How many proposals SHIPPED vs. NO_SHIPPED?
- Which K-violations occurred (if any)?
- Did certain lanes get used more than others?

### Step 4: Weekly Synthesis (Optional)

If you want to trigger synthesis now (normally runs on Sunday):

```bash
python3 oracle_town/memory/tools/weekly_synthesizer.py
```

**What happens:**
- Regenerates all `summary.md` files from active facts
- Detects contradictions (rarely happens on Week 1)
- Updates `heuristics.md` with initial observations
- Updates `rules_of_thumb.md` if patterns emerge

**View results:**
```bash
cat oracle_town/memory/tacit/heuristics.md
cat oracle_town/memory/tacit/rules_of_thumb.md
```

### Step 5: Validate Memory Data

Ensure memory capture was clean:

```bash
# Check no errors in extraction
cat oracle_town/memory/meta/extraction.log | grep ERROR

# Verify facts are well-formed
python3 -c "
import json
from pathlib import Path
for f in Path('oracle_town/memory/entities').rglob('items.json'):
    items = json.load(open(f))
    print(f'{f.parent.name}: {len(items)} facts')
"

# Check checkpoints updated
cat oracle_town/memory/meta/checkpoints.json | jq .
```

---

## Failure Modes & Recovery

### Problem: Governance cycle fails to run

**Cause:** Orchestrator or mayor logic error

**Recovery:**
1. Check orchestrator logs: `python3 oracle_town/core/orchestrator.py --verbose`
2. Verify test claims are well-formed: `python3 -c "import json; json.load(open('oracle_town/test_claims.json'))"`
3. Run a single claim at a time: `python3 oracle_town/cli.py "Test claim"`

### Problem: Decision record file malformed

**Cause:** Mayor didn't produce valid decision_record.json

**Recovery:**
1. Check decision file: `python3 -c "import json; json.load(open('decisions/REAL_WEEK1.json'))"`
2. Verify it matches schema: `cat oracle_town/schemas/decision_record.schema.json`
3. Manually fix if minor issues

### Problem: Memory extraction finds no facts

**Cause:** Extraction logic doesn't match decision structure

**Recovery:**
1. Check decision file contains `decision_record` field
2. Check `run_id` and `claim_id` are present
3. Run with verbose logging: `python3 oracle_town/memory/tools/cycle_observer.py --verbose`

---

## What Week 1 Real Execution Captures

After completing these steps, your memory system will contain:

✅ **Real decisions** — Actual SHIP/NO_SHIP verdicts from your governance
✅ **Real K-violations** — Actual constraint violations encountered
✅ **Real blockers** — Real reasons proposals were rejected
✅ **Real timestamps** — When decisions were made
✅ **Real audit trail** — Ledger entries with signatures

This is the ground truth for learning.

---

## What NOT to Do

❌ Don't manually edit memory files after extraction
❌ Don't mix test harness runs with real governance
❌ Don't skip cycle_observer.py (memory capture is automatic only if you run it)
❌ Don't assume synthesis updates heuristics (it does, but based on data)
❌ Don't modify decisions after they're logged

---

## Timeline for Weeks 2-9

Once Week 1 is captured and verified:

### Week 2 (Day 8)
```bash
# Run governance again with fresh claims
python3 oracle_town/cli.py --input oracle_town/test_claims_week2.json

# Extract memory
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs

# Optional: synthesize
python3 oracle_town/memory/tools/weekly_synthesizer.py
```

### Week 3-9
Same pattern: Run governance → Extract → Synthesize (weekly)

### After Week 9
Full 9-week memory record enables emergence analysis.

---

## Monitoring Convergence

As you run weeks 1-9, watch for:

### Lane Usage Patterns
```bash
# Are certain lanes being used more?
grep -r "lane" oracle_town/memory/entities/*/items.json | cut -d: -f3 | sort | uniq -c | sort -rn
```

### Proposal Success Rates
```bash
# SHIP vs NO_SHIP ratio over time
grep "pattern_success\|pattern_failure" oracle_town/memory/entities/decisions/*/items.json | cut -d: -f3 | sort | uniq -c
```

### Heuristic Evolution
```bash
# What changed in heuristics between synthesis runs?
diff <(git show HEAD:oracle_town/memory/tacit/heuristics.md) oracle_town/memory/tacit/heuristics.md
```

### K-Invariant Pressure
```bash
# Which K-violations are most common?
grep "blocker-" oracle_town/memory/entities/invariant_events/*/summary.md | cut -d: -f2 | sort | uniq -c | sort -rn
```

---

## Comparison: Test Harness vs. Real Execution

| Aspect | Test Harness | Real Execution |
|--------|--------------|---|
| Governance logic | Mock | Your actual logic |
| Decision source | Generated by me | Your mayor |
| Memory validity | Illustrative | Authoritative |
| Realism | 80% (plausible) | 100% (actual) |
| Usability | Debugging, learning | Foundation for learning |

**After Week 1 real execution**, your memory system contains actual Oracle Town governance history.

---

## Data Ownership & Privacy

- All memory data stays local in `oracle_town/memory/`
- No cloud upload, no external processing
- You own the governance record completely
- Backward-compatible with test harness data

---

## Success Criteria for Week 1

✅ Governance cycle completes without error
✅ Decision record is well-formed JSON
✅ cycle_observer.py extracts ≥3 facts
✅ Memory entities created in `memory/entities/`
✅ Checkpoints updated in `meta/checkpoints.json`
✅ At least one proposal SHIPPED, one NO_SHIPPED
✅ No errors in extraction logs

If all checks pass: Week 1 is captured. Ready for Week 2.

---

## Next Steps

1. **Gather test claims** — Create oracle_town/test_claims.json
2. **Run governance** — Execute your actual governance cycle
3. **Extract memory** — Run cycle_observer.py
4. **Verify** — Check that memory was populated
5. **Plan Week 2** — Prepare next set of claims

Then repeat for weeks 2-9, and analyze emergence patterns.

---

## Support

If something breaks:

1. **Check logs:** `tail -f oracle_town/memory/meta/extraction.log`
2. **Verify structure:** `python3 -c "import json; json.load(open('decisions/REAL_WEEK1.json'))"`
3. **Consult schemas:** `cat oracle_town/schemas/decision_record.schema.json`
4. **Test in isolation:** Run cycle_observer.py on a single claim

---

**You're ready to capture Oracle Town's real governance history.**

Start with Week 1 and we'll build from there.
