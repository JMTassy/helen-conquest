# PHASE 2: EXECUTION GUIDE

**Status:** ✅ Infrastructure Complete and Ready
**Date:** 2026-01-26
**Next Action:** Obtain Claude API key and execute

---

## What's Happened So Far

### Phase 1 (Completed ✅)
- ✅ Built kernel infrastructure (Steps 0-4)
- ✅ Implemented deterministic simulation CT
- ✅ Ran 39 cycles with mock proposals
- ✅ Proved system is mechanically sound

**Key Finding:** QUORUM_MISSING dominates (48.7%) — policy working correctly.

### Phase 2 (Implemented ✅, Ready to Execute)
- ✅ Created `ct_gateway_claude.py` — Real Claude API wrapper
- ✅ Created `phase2_harness.py` — Phase 2 execution harness
- ✅ Implemented `Phase2Logger` — Enhanced cycle logging
- ✅ Designed K0-safe context feeding (facts only)
- ✅ Built output schema and error handling
- ✅ Verified all imports and dependencies

---

## How to Execute Phase 2

### Step 1: Obtain Claude API Key

1. Go to [Anthropic Dashboard](https://console.anthropic.com)
2. Navigate to API Keys section
3. Create a new API key
4. Copy it (format: `sk-...`)

### Step 2: Set Environment Variable

```bash
export ANTHROPIC_API_KEY="sk-your-key-here"
```

### Step 3: Run Phase 2

**Quick Test (5 cycles):**
```bash
cd "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
python3 oracle_town/runner/phase2_harness.py --max-cycles 5
```

**Production Run (50 cycles):**
```bash
python3 oracle_town/runner/phase2_harness.py --max-cycles 50
```

**Extended Run (100 cycles):**
```bash
python3 oracle_town/runner/phase2_harness.py --max-cycles 100
```

---

## What Phase 2 Tests

- **Does Claude adapt to feedback?** (blocking_reasons signals)
- **Does K0 enforcement work?** (Supervisor rejection rate)
- **Is SHIP reachable?** (with min_quorum=1)
- **How fast does it converge?** (cycles to first SHIP)
- **Does creativity survive constraint?** (proposal diversity)

---

## Expected Output

After execution, check `oracle_town/runner/phase2_logs/PHASE2_SUMMARY.json`:

```json
{
  "convergence_metrics": {
    "ship_count": 34,
    "no_ship_count": 16,
    "ship_rate": 0.68,
    "first_ship_cycle": 3
  },
  "blocking_reasons_frequency": {
    "NO_RECEIPTS": 16
  }
}
```

---

## Success Criteria

✅ SHIP occurs (at least once)
✅ Claude adapts (proposal diversity)
✅ K0 holds (Supervisor catches authority language)
✅ System is deterministic (replay verification)

---

## Files Status

```
oracle_town/runner/
├── ct_gateway_claude.py          ✅ Ready
├── phase2_harness.py             ✅ Ready
└── phase2_logs/                  (will be created on execution)
```

---

**Ready to execute. Await Claude API key.**
