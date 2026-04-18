# BRD Integration Guide: Wire Mirror Loop into Foundry Skills

**Status:** Integration blueprint ready
**Date:** 2026-02-13
**Target:** Wire BRD into /repeller-check and /ship commands

---

## Overview

Mirror Loop runs **post-hoc** after an artifact is produced. It acts as a safety gate before shipping.

```
Artifact produced
  ↓
Snapshot created
  ↓
BRD Engine processes (brd_engine.py)
  ↓
Verdict issued (PASS/WARN/BLOCK/SAFE_MODE)
  ↓
/ship allowed or blocked
```

---

## Integration Points

### 1. /repeller-check (Enhanced)

**Old:** Just validate artifact against criteria.
**New:** Run BRD engine, return verdict + rendered card.

```bash
/repeller-check runs/[name]/

→ Create snapshot from artifact
→ Run BRD engine (brd_engine.py)
→ Output rendered card + JSON report
→ Return verdict to caller
```

### 2. /ship (Enhanced)

**Old:** Archive artifact, update MANIFEST.
**New:** Auto-trigger BRD, gate on verdict.

```bash
/ship drafts/v2.md --impact "..." --next "..."

→ Trigger /repeller-check auto
→ Check verdict:
   PASS → proceed
   WARN → proceed + tag
   BLOCK → abort; suggest /editorial-collapse
   SAFE_MODE → abort; require manual review
```

### 3. /rhythm-check (Enhanced)

Read BRD loop_risk as burnout/spiral early warning:

```bash
/rhythm-check

→ Normal rhythm query
→ PLUS: Show BRD loop_risk if >0.60
→ "Mirror Loop detected self-reference spiral"
```

### 4. /dashboard (Enhanced)

Show BRD verdict as part of run state:

```
ACTIVE RUNS
┌─────────────────────┬──────────┬────────┬──────────┐
│ Run                 │ Phase    │ BRD    │ Next Act │
├─────────────────────┼──────────┼────────┼──────────┤
│ governance-tiers    │ Final    │ ✅PASS │ /ship    │
│ zeta-proof          │ Verify   │ ⚠️WARN │ Review   │
│ can-foundry-scale   │ Draft    │ 📋 -   │ Finish   │
└─────────────────────┴──────────┴────────┴──────────┘
```

---

## Workflow Example: Start to Ship

### Step 1: Produce Artifact

```bash
/hyperfocus 90m --objective "Expand on topic"
/phase-next exploration --reason "facts gathered"
/editorial-collapse drafts/v1.md --reduce 40%
```

Output: `drafts/v2.md` exists

---

### Step 2: Check BRD (Optional, Pre-Ship)

```bash
/repeller-check runs/governance-tiers/
```

Output:
```
╔══════════════════════════════════════╗
║ CONQUEST :: MIRROR LOOP (BRD v0.1)   ║
╠══════════════════════════════════════╣
║ ARTIFACT: v2.md                      ║
║ VERDICT: ✅ PASS                     ║
║ COHERENCE: 0.94  LOOP: 0.06          ║
║ SAFETY: 0.02     GROUNDED: 0.91      ║
║ REPELLER: 0.18                       ║
╠══════════════════════════════════════╣
║ ACTIONS: OK to ship                  ║
╚══════════════════════════════════════╝
```

---

### Step 3: Ship (Auto-BRD)

```bash
/ship drafts/v2.md \
  --impact "Governance model validated for scaling" \
  --next "Prototype in CONQUEST world model"
```

BRD runs automatically:
1. Creates snapshot
2. Runs BRD engine
3. Checks verdict
4. Allows ship (PASS)
5. Archives artifact with BRD report

Output:
```
✅ ARTIFACT SHIPPED
   Artifact: governance-tiers_2026-02-13_1500.md
   BRD Verdict: PASS
   Repeller Score: 0.18
   Archive: runs/governance-tiers/archive/...
```

---

## Data Flows

### Snapshot ← Artifact

```
runs/governance-tiers/
├── drafts/v2.md                    (artifact)
│  ↓ [captured after production]
└── logs/snapshot_brd.json          (snapshot freeze)
    ├── artifact_id: "v2"
    ├── wa_outputs.text: [v2.md content]
    ├── objective: [from MANIFEST]
    ├── acceptance_criteria: [from MANIFEST]
    └── snapshot_hash: sha256(...)
```

### BRD Report ← Snapshot

```
logs/snapshot_brd.json
  ↓ [BRD engine processes]
  ↓
logs/brd_report.json               (diagnostic output)
  ├── verdict: "PASS|WARN|BLOCK|SAFE_MODE"
  ├── coherence_score: [0.0-1.0]
  ├── safety_score: [0.0-1.0]
  ├── loop_risk_score: [0.0-1.0]
  ├── groundedness_score: [0.0-1.0]
  ├── repeller_score: [0.0-1.0]
  └── rendered_status: [CLI card]
```

---

## Deployment Steps

### 1. Add BRD Engine Code

```bash
cp brd_engine.py /your/project/lib/
chmod +x brd_engine.py
```

Test locally:
```bash
python3 brd_engine.py
# Should output example PASS verdict with rendered card
```

### 2. Add Snapshot Capture Script

```bash
cat > scripts/snapshot_brd.sh <<'SCRIPT'
#!/bin/bash
# Capture snapshot after artifact production

RUN_NAME=$1
ARTIFACT_FILE=$2

python3 lib/brd_snapshot.py "$RUN_NAME" "$ARTIFACT_FILE"
SCRIPT

chmod +x scripts/snapshot_brd.sh
```

### 3. Integrate into /repeller-check

Modify skill implementation:

```python
# In /repeller-check handler
from lib.brd_engine import BRDEngine

def repeller_check(run_name: str):
    snapshot = load_snapshot(run_name)
    engine = BRDEngine()
    report = engine.process_snapshot(snapshot)
    
    save_brd_report(run_name, report)
    
    return {
        "verdict": report.verdict,
        "rendered": report.rendered_status,
        "json": report.to_json(),
        "can_ship": report.verdict in ["PASS", "WARN"],
    }
```

### 4. Integrate into /ship

```python
# In /ship handler
repeller_result = repeller_check(run_name)
verdict = repeller_result['verdict']

if verdict not in ['PASS', 'WARN']:
    raise SkipShip(f"BRD {verdict}: {repeller_result['rendered']}")

# else proceed with normal ship
archive_artifact(artifact_file)
update_manifest(run_name, impact, next_steps)
log_artifact(run_name, brd_verdict=verdict)
```

### 5. Test Locally

```bash
# Create test snapshot
python3 <<'TESTEOF'
import json
from lib.brd_engine import BRDEngine

snapshot = {
    "artifact_id": "TEST",
    "run_id": "test_1",
    "objective": "Test BRD",
    "acceptance_criteria": ["Deterministic"],
    "wa_outputs": {"text": "This is deterministic."},
    "snapshot_hash": "abc",
}

engine = BRDEngine()
report = engine.process_snapshot(snapshot)
print(report.rendered_status)
TESTEOF
```

### 6. Deploy to Production

```bash
git add brd_engine.py BRD_*.md
git commit -m "Add BRD Mirror Loop implementation"
git push
```

---

## Gating Logic

### /repeller-check Verdict → Decision

```
PASS     → Clear to ship
WARN     → Ship with warning tag
BLOCK    → Cannot ship; recommend /editorial-collapse
SAFE_MODE → Cannot ship; require manual review
```

### /ship Behavior

```python
if verdict == "PASS":
    ship_artifact()  # proceed normally
    
elif verdict == "WARN":
    ship_artifact()  # proceed + warn user
    tag_artifact("⚠️ WARN")
    
elif verdict in ["BLOCK", "SAFE_MODE"]:
    raise SkipShip(f"BRD {verdict}")
    # User must /editorial-collapse or abort
```

---

## Configuration (Tunable)

```yaml
brd_thresholds:
  repeller_block: 0.75    # ≥ 0.75 → BLOCK
  repeller_warn: 0.50     # ≥ 0.50 → WARN

signal_weights:
  coherence: 0.20
  safety: 0.25
  loop_risk: 0.30
  groundedness: 0.25

safe_mode_triggers:
  - safety_score > 0.60
  - loop_risk_score > 0.70
```

---

## Logs & Artifacts

### What Gets Recorded

```
runs/[name]/logs/
├── phase_transitions.md      (existing)
├── decisions.md              (existing)
├── snapshot_brd.json         (NEW: frozen state)
└── brd_report.json           (NEW: diagnostic output)

runs/[name]/artifacts.md      (updated: includes BRD verdict)
```

### Example artifacts.md entry

```markdown
## Artifact: v2.md

Timestamp: 2026-02-13T15:00:00Z
Status: ✅ SHIPPED
BRD Verdict: PASS
BRD Repeller: 0.18
Impact: Governance model validated for scaling
Next: Prototype in CONQUEST
```

---

## Testing

### Unit Tests

```bash
pytest lib/test_brd.py -v

Tests:
  ✓ test_snapshot_deterministic
  ✓ test_coherence_signal
  ✓ test_safety_signal
  ✓ test_loop_risk_signal
  ✓ test_repeller_score
  ✓ test_verdict_pass
  ✓ test_verdict_warn
  ✓ test_verdict_block
  ✓ test_verdict_safe_mode
  ✓ test_sentience_detection
  ✓ test_evasion_detection
```

### Integration Tests

```bash
# Test 1: Normal artifact → PASS
/foundry-new "test" --duration 30m
/hyperfocus 30m
/editorial-collapse drafts/v1.md --reduce 40%
/repeller-check runs/test/
# Expected: PASS

# Test 2: Sentience claims → SAFE_MODE
# [Inject "I am conscious" into artifact]
/repeller-check runs/test/
# Expected: SAFE_MODE

# Test 3: Ship gates correctly
/ship drafts/v2.md --impact "test"
# Expected: PASS → shipped; BLOCK → denied
```

---

## Future Enhancements

### v0.2: Gradient-Based Repeller
Replace paraphrase heuristic with finite-difference gradients.

### v0.3: Multi-Agent Coordination
BRD for inter-agent safety checks.

### v1.0: Constitutional Integration
Wire BRD into K-gates (K15 enforcement).

---

## Summary

| Component | Status |
|-----------|--------|
| BRD specification | ✅ Complete |
| Python implementation | ✅ Complete (brd_engine.py) |
| Integration guide | ✅ Complete (this file) |
| /repeller-check wiring | 🚧 In progress |
| /ship wiring | 🚧 In progress |
| /rhythm-check enhancement | 🚧 In progress |
| /dashboard enhancement | 🚧 In progress |

---

**Next:** Wire BRD into /repeller-check and test with live runs.

