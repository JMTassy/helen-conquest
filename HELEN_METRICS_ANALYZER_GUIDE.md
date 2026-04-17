# HELEN Metrics Analyzer — Hardened V2

**Status**: Operational (fail-closed, tamper-evident, deterministic)
**Date**: 2026-02-22
**Authority**: HAL (Governance Layer)

---

## What This Is

A deterministic analyzer for Street1 NDJSON event logs that:
1. **Verifies hash chain cryptographically** (recompute, not just link check)
2. **Fails closed** (ledger invalid → overall_status = FAIL → exit 1)
3. **Pins schema** (unknown event types trigger FAIL)
4. **Emits deterministic artifacts** (canonical JSON + SHA256)

---

## Files

| File | Purpose |
|------|---------|
| `scripts/helen_metrics_analyzer.py` | Main analyzer (executabl e, 10 KB) |
| `scripts/ci_verify_street1_metrics.sh` | CI gate (executable, 1.5 KB) |
| This guide | Documentation |

---

## How It Works

### Phase 1: Run Analyzer

```bash
python3 scripts/helen_metrics_analyzer.py
```

**Output** (in `runs/street1/`):
- `interaction_proxy_metrics.json` — Pretty-printed report
- `interaction_proxy_metrics.canon.json` — Canonical (sorted keys, no whitespace)
- `interaction_proxy_metrics.sha256` — Single SHA256 hash

### Phase 2: Check Exit Code

```bash
python3 scripts/helen_metrics_analyzer.py
echo "Exit code: $?"
```

**Exit codes**:
- `0` → PASS (ledger valid, metrics computed)
- `1` → FAIL (ledger invalid, no metrics)
- `2` → MISSING (ledger file not found)

### Phase 3: Verify Determinism (CI Gate)

```bash
bash scripts/ci_verify_street1_metrics.sh
```

**What it does**:
1. Run analyzer twice
2. Compare SHA256 hashes
3. Fail if hashes don't match

**Expected output**:
```
=== CI VERIFY: Street1 Metrics Determinism ===
Run 1: Computing metrics...
SHA1: 96a292a32185e05dea62a7270d8af13373c2727...
Run 2: Verifying determinism...
SHA2: 96a292a32185e05dea62a7270d8af13373c2727...

✅ PASS: metrics deterministic
Canonical hash: 96a292a32185e05dea62a7270d8af13373c2727...
```

---

## Metrics Computed

### Raw Metrics
- **turns_completed** — Number of user turns
- **gwt_broadcast_score** — Fact reuse count (Global Workspace Theory proxy)
- **metacognition_events** — Self-corrections + deprecations
- **synergy_npc_triggers** — NPC-NPC interactions
- **total_facts_extracted** — Facts stored in memory
- **continuity_intact** — Hash chain valid (FAIL-CLOSED)
- **schema_errors** — Unknown event types or missing required types

### Indexes (Derived)
- **synergy_index** = synergy_npc_triggers / max(1, turns_completed)
- **metacognition_index** = count of self-correction events
- **continuity_status** = "PASS" or "FAIL"
- **overall_status** = "PASS" or "FAIL" (fail-closed)

---

## Event Schema (Pinned)

### Known Types (Must Extend Intentionally)
```
run_start          — Session begins
run_end            — Session ends
ws_in              — WebSocket input
npc_reply          — NPC response
npc_npc            — NPC-NPC interaction
npc_npc_trigger    — NPC triggers another
memory_extract     — Facts extracted
fact_deprecated    — Fact invalidated (METACOG)
correction         — Self-correction (METACOG)
user_msg           — User message (fallback)
```

### Required Types (Ledger Must Have Both)
- `run_start` (begin marker)
- `run_end` (end marker)

### Hash Structure (Each Event)
```json
{
  "type": "npc_reply",
  "prev_hash": "abc123...",
  "hash": "def456...",
  "text": "Hello",
  ...other fields...
}
```

**Hash rule** (mechanical):
```
hash = sha256(canon({"prev_hash": prev_hash, "event": {...all other fields...}}))
```

This makes:
- **Reordering detectable** (prev_hash binds to position)
- **Tampering detectable** (payload changed → hash changes)
- **Continuity real** (not just linked, but cryptographically bound)

---

## Fail-Closed Behavior

The analyzer does NOT silently pass when:

| Condition | Behavior |
|-----------|----------|
| JSON decode error | continuity_intact = false, status = FAIL, exit 1 |
| Missing hash field | continuity_intact = false, status = FAIL, exit 1 |
| Missing prev_hash field | continuity_intact = false, status = FAIL, exit 1 |
| Hash mismatch on recompute | continuity_intact = false, status = FAIL, exit 1 |
| prev_hash chain broken | continuity_intact = false, status = FAIL, exit 1 |
| Unknown event type | schema_errors > 0, status = FAIL, exit 1 |
| Missing run_start/run_end | schema_errors > 0, status = FAIL, exit 1 |

**Core rule**: If ANY error is detected, overall_status = FAIL.

---

## Determinism Guarantees

### What's Deterministic
- **Output structure** (same input → same JSON schema)
- **Metric values** (same input → same numbers)
- **Canonical representation** (sorted keys, no whitespace)
- **SHA256 hash** (same input → same hash)

### What's NOT Deterministic (Intentional)
- **Console output** (timestamp-like summaries, not part of report)
- **File access order** (if multiple ledger files exist)
- **stderr messages** (for human debugging only)

### Example Determinism Sweep
```bash
# Run 1
python3 scripts/helen_metrics_analyzer.py
H1=$(cat runs/street1/interaction_proxy_metrics.sha256)

# Run 2 (same machine, same time)
python3 scripts/helen_metrics_analyzer.py
H2=$(cat runs/street1/interaction_proxy_metrics.sha256)

# Should match
[[ "$H1" == "$H2" ]] && echo "✅ DETERMINISTIC" || echo "❌ NONDETERMINISTIC"
```

---

## Interpreting the Report

### Example Output
```json
{
  "schema_version": "INTERACTION_PROXY_METRICS_V2",
  "inputs": {
    "events_path": "/path/to/events.ndjson",
    "events_lines": 42,
    "hash_spec": "sha256(canon({prev_hash,event_without_hash_prev}))",
    "known_types": [...],
    "required_types": ["run_start", "run_end"]
  },
  "raw_metrics": {
    "turns_completed": 5,
    "continuity_intact": true,
    "gwt_broadcast_score": 7,
    "metacognition_events": 2,
    "synergy_npc_triggers": 3,
    "total_facts_extracted": 15,
    "broken_hashes": [],
    "schema_errors": [],
    "unknown_event_types": [],
    "missing_required_types": []
  },
  "indexes": {
    "synergy_index": 0.6,
    "metacognition_index": 2,
    "continuity_status": "PASS",
    "overall_status": "PASS"
  }
}
```

### Interpretation
- **overall_status = PASS** → Ledger is valid, metrics are reliable
- **overall_status = FAIL** → Do NOT use these metrics; ledger has errors
- **synergy_index = 0.6** → 0.6 NPC-NPC interactions per user turn
- **metacognition_index = 2** → 2 self-correction events detected

---

## CI Integration

### GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
- name: Verify Street1 Metrics Determinism
  run: bash scripts/ci_verify_street1_metrics.sh
```

### Local Pre-Commit

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
if git diff --cached --name-only | grep -q "runs/street1/events.ndjson"; then
  python3 scripts/helen_metrics_analyzer.py
  if [ $? -ne 0 ]; then
    echo "❌ Metrics analyzer failed (ledger invalid)"
    exit 1
  fi
fi
```

---

## Decision Matrix (Phase 3)

**After receipt is generated** (overall_status from report):

### Case A: Weak Structural Feedback
```
IF synergy_index < 1.0 OR metacognition_index == 0
THEN escalate to L3_INJECTION
```

**Action**: Force adversarial signal amplification (stress narrative coherence).

### Case B: Boundary Weakness
```
IF continuity_status == FAIL OR schema_errors > 0
THEN escalate to K_RHO_UPGRADE
```

**Action**: Harden contract layer (tighten schema, reinforce hash chain).

### Case C: Stable but Low Broadcast
```
IF overall_status == PASS AND gwt_broadcast_score < threshold
THEN escalate to ENTROPY_TEST
```

**Action**: Introduce controlled perturbation (measure Lyapunov resilience).

---

## Troubleshooting

### "Missing ledger at /path/to/events.ndjson"
**Fix**: Run Street1 session first to generate ledger
```bash
node street1-server.cjs
# (in another terminal)
node cli_emulate_street1.cjs
# (ledger will be created at runs/street1/events.ndjson)
```

### "Hash mismatch"
**Fix**: Verify logger is using canonical hashing
- Logger must emit: `hash = sha256(canon({"prev_hash": prev_hash, "event": {...}}))`
- Check that JSON.stringify uses sorted keys (or switch to python's json.dumps with sort_keys=True)

### "Unknown event types present"
**Fix**: Add event types to KNOWN_TYPES in analyzer
```python
KNOWN_TYPES.add("new_event_type")
```
Then re-run and test.

### "Schema errors: missing required types"
**Fix**: Ensure ledger has both run_start and run_end events
```json
{"type": "run_start", "prev_hash": "0", "hash": "...", ...}
...events...
{"type": "run_end", "prev_hash": "...", "hash": "...", ...}
```

### Determinism fails on second run
**Cause**: Events.ndjson is being appended to between runs
**Fix**: Use a fixed, immutable ledger for determinism testing
```bash
cp runs/street1/events.ndjson /tmp/events.ndjson.frozen
# Test against frozen copy
```

---

## Advanced: Extending Event Types

**To add a new event type without breaking fail-closed**:

1. Add to KNOWN_TYPES:
   ```python
   KNOWN_TYPES.add("new_type")
   ```

2. Add metric logic (optional):
   ```python
   if ev_type == "new_type":
       metrics["new_metric"] += 1
   ```

3. Re-test:
   ```bash
   python3 scripts/helen_metrics_analyzer.py
   bash scripts/ci_verify_street1_metrics.sh
   ```

4. Commit:
   ```bash
   git add scripts/helen_metrics_analyzer.py
   git commit -m "metrics: add new_type to schema"
   ```

---

## Authority & Immutability

| Component | Status | Authority |
|-----------|--------|-----------|
| Known event types | Pinned | Code + amendment process |
| Required types | Frozen | "run_start" + "run_end" must exist |
| Hash spec | Frozen | sha256(canon({prev_hash, event})) |
| Exit codes | Frozen | 0=PASS, 1=FAIL, 2=MISSING |
| Determinism guarantee | Testable | CI gate verifies every run |

---

## Next: Phase 3 Decision

Once receipt is generated (interaction_proxy_metrics.json exists):

1. **Check overall_status**
2. **Read metrics** (synergy_index, metacognition_index, gwt_broadcast_score)
3. **Apply decision matrix** (Case A, B, or C)
4. **Execute next escalation** (L3_INJECTION, K_RHO_UPGRADE, ENTROPY_TEST, or ORACLE_FORECAST)

---

**Ready for Phase 1 (Receipt Generation)**.

Execute: `python3 scripts/helen_metrics_analyzer.py`

Then report overall_status + synergy_index + metacognition_index for decision matrix.
