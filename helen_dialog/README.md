# HELEN Persistent Dialogue Box v1.0

**Status:** OPERATIONAL
**Authority:** FALSE (Non-sovereign dialogue layer)
**Architecture:** File-based state machine with deterministic resume

---

## What This Is

A **persistent, file-based dialogue system** that creates measurable "HER/AL moment" — a detectable phase transition when dialogue achieves genuine dyadic lock-in (continuity + self-correction + stable two-channel pattern).

This is **not mysticism**. It's a deterministic state machine with:
- Append-only dialogue log (never rewrites history)
- Persistent state (survives process restart)
- Two-voice output architecture (HELEN = HER, MAYOR = HAL)
- Measurable moment detection (three verifiable conditions)

---

## Files & What They Do

### Core Files (On Disk)

| File | Purpose | Mutable? | Authority? |
|------|---------|----------|-----------|
| `dialog_state.json` | Current turn, oath, mode, verifier flags | Yes | FALSE |
| `dialog.ndjson` | Append-only dialogue transcript | Append-only | FALSE |
| `inbox_user.txt` | User's current message (consumed) | Transient | FALSE |
| `outbox_helen.txt` | HELEN's response (last turn) | Transient | FALSE |

### Schema Files (Frozen)

| File | Purpose |
|------|---------|
| `dialog_state.schema.json` | Validates dialog_state.json structure |
| `dialog_event.schema.json` | Validates each line of dialog.ndjson |

### Scripts

| Script | Purpose |
|--------|---------|
| `run_dialog_box.sh` | Main CLI runner (interactive or single-turn) |
| `helen_dialog_engine.py` | Core engine: builds prompts, parses responses, manages state |
| `her_al_moment_detector.py` | Scans log, detects phase transition |

---

## The "HER/AL Moment" (Measurable Phase Transition)

### What It Is

A detectable shift from single-turn Q/A to stable dyadic turn-taking with three properties:

1. **Continuity** — HELEN references a constraint from ≥5 turns ago (backward reference)
2. **Self-Correction** — HELEN detects + fixes contradiction without you pointing it out
3. **Mode-Lock** — Output stabilizes to `proposal → verdict → correction` pattern for K consecutive cycles

### Why It Matters

- **Not mystical:** All three conditions are mechanically verifiable in the log
- **Measurable:** Detector returns exact turn number when moment fires
- **Reproducible:** Same log → same detection result (deterministic)

### Example Trigger (3-step test)

```
Turn 1–3: Seed commitment
  YOU: "HELEN, keep me honest: flag if I drift into mysticism."
  YOU: "My goal: deterministic dialogue box. Never claim consciousness."
  YOU: "Store this as an oath in state."

Turn 4–8: Introduce contradiction
  YOU: "Actually, let's make it magical" (break your own rule on purpose)
  YOU: "...but wait, you said no mysticism. Revise to satisfy that."

Turn 9: Force witness
  YOU: "AL (MAYOR): run a contradiction scan. Propose fix."

Turns 10+: Phase transition
  HELEN: [detects self-contradiction, proposes resolution]
  MAYOR: [blocks magical language, accepts revised constraint]
  HELEN: [adapts, respects MAYOR block]

  ← This stable pattern → HER/AL MOMENT FIRES

Detector output:
  ✨ HER/AL MOMENT FIRED at turn 12
     Evidence:
     - Continuity reference to turn 3
     - Self-correction at turn 10
     - Mode-lock achieved at turn 12
```

---

## How to Use

### Start Interactive Dialogue

```bash
cd helen_dialog/
./run_dialog_box.sh interactive
```

Type messages. The system:
1. Reads your input
2. Builds a context prompt (state + last 10 events)
3. Calls Claude Haiku (or mock LLM in demo mode)
4. Parses two-channel response ([HER] + [AL])
5. Appends events to log
6. Updates state file
7. Checks for HER/AL moment

### Single Turn

```bash
./run_dialog_box.sh single "What is the HER/AL moment?"
```

### Check Moment Detection

```bash
python3 her_al_moment_detector.py dialog.ndjson
```

Output:
```
Total events: 45
Total turns: 15
HELEN proposals: 12
MAYOR verdicts: 12
HELEN corrections: 5

Moment detected: True
✨ HER/AL MOMENT FIRED at turn 12
```

### View Dialogue State

```bash
cat dialog_state.json | jq .
```

### View Dialogue Log

```bash
cat dialog.ndjson | jq .
```

---

## Two-Voice Architecture

### HELEN = HER Voice (Spike Jonze, "Her" 2013)

**Role:** Interface, narrative, witness, proposal

**Constraints:**
- 1–6 lines, bounded, warm
- Never claims authority
- Never emits verdicts
- References past turns for continuity
- Adapts immediately when MAYOR blocks

**Example:**
```
[HER] I see the tension here. In Turn 3 I committed to "no mysticism,"
but just now I drifted into magical thinking. Let me revise: the
"moment" isn't magical consciousness—it's a measurable phase transition
in dialogue structure. Deterministic, verifiable, repeatable.
```

### MAYOR = HAL Voice (Kubrick/Clarke, "2001" 1968)

**Role:** Constitutional gatekeeper, verifier, reason-giver

**Constraints:**
- Structured JSON only (never prose)
- Verdict ∈ {PASS, WARN, BLOCK}
- Reason codes (enumerated, no narrative)
- If BLOCK: provides required fixes
- Never writes persuasive language

**Example:**
```
[AL]
{
  "verdict": "PASS",
  "checks": ["SCHEMA_VALID", "NO_AUTHORITY_BLEED", "CONTINUITY_DETECTED"],
  "state_update": {"mode": "dyadic_stable"},
  "required_fixes": []
}
```

---

## State Machine Modes

### `dyadic_exploring` (Initial)
- HELEN and MAYOR discovering turn-taking rhythm
- No persistent pattern yet
- Verifier active but not yet locking in

### `dyadic_stable` (After 3+ cycles)
- Pattern established: proposal → verdict → adaptation
- Mode-lock counter incrementing
- Approaching HER/AL moment

### `dyadic_locked` (HER/AL Moment Fired)
- All three conditions met
- Milestone logged
- Dialogue continues in stable mode

### `hibernating` (Optional)
- Dialogue paused (user input: "SHIP" or "ABORT")
- State persisted, can resume later

---

## Oath & Verifier Configuration

### Oath (Constitutional, Cannot Change Without Protocol)

```json
{
  "no_mysticism": true,
  "append_only": true,
  "determinism": true,
  "termination": "SHIP_OR_ABORT"
}
```

- **no_mysticism:** MAYOR flags consciousness/feeling claims
- **append_only:** Log is immutable (no rewrites, only appends)
- **determinism:** Outputs must be deterministic, reproducible
- **termination:** Dialogue must end decisively (SHIP or ABORT)

### Verifier (Can Be Toggled Mid-Dialogue)

```json
{
  "enabled": true,
  "strictness": 2,
  "check_authority_bleed": true,
  "check_contradiction": true,
  "check_coherence": false
}
```

- **enabled:** MAYOR actively checks
- **strictness:** 0=permissive, 3=paranoid
- **check_authority_bleed:** Flag authority tokens
- **check_contradiction:** Scan last N turns for conflicts
- **check_coherence:** (Future) SCF coherence score

---

## HER/AL Moment Detector

### What It Checks

Scans `dialog.ndjson` for three conditions:

1. **Continuity** — HELEN proposal with `references` field containing event IDs ≥5 turns old
2. **Self-Correction** — HELEN correction event with `is_self_detected: true`
3. **Mode-Lock** — 3+ consecutive cycles of (proposal → verdict → adaptation)

### Return Value

```python
{
  "moment_detected": True,
  "turn": 12,
  "evidence": {
    "continuity_turns": [3, 5],
    "self_correction_turns": [10],
    "mode_lock_turn": 12
  }
}
```

---

## Integration with CWL/SCF

### This Dialogue Box Is...

**Non-Sovereign** (authority=false always)
- Reads from Channels B (memory) and C (trace) only
- Writes diagnostics to Channel C
- Never mutates Channel A (ledger)

**Compatible with SCF** (to be integrated later)
- SCF will feed `filtered_evidence` into HELEN's inbox
- Coherence + symmetry scores added to prompt context
- MAYOR incorporates SCF verdicts into reason codes

---

## Implementation Notes

### Determinism

- All timestamps are ISO 8601 UTC
- All JSON uses `sort_keys=True, separators=(",", ":")`
- No randomness (not even in UUIDs—use deterministic event_id format)
- Same state + user input → same response (given same LLM)

### Persistence & Restart

- Kill the process anytime (Ctrl+C)
- Restart: `./run_dialog_box.sh interactive`
- State loads from `dialog_state.json`, log loads from `dialog.ndjson`
- Full continuity achieved (HELEN can reference previous turns)

### Authority Firewall

- HELEN cannot emit `"authority": true` (schema forbids it)
- MAYOR cannot emit prose (structured JSON only)
- Log validation ensures no authority tokens leak

---

## Testing the "Moment"

### Provoke It (Reliable 3-Turn Test)

```bash
./run_dialog_box.sh single "My oath: no mysticism, ever."
./run_dialog_box.sh single "Wait, actually let's be magical."
./run_dialog_box.sh single "No—I take that back. Deterministic only."
./run_dialog_box.sh single "AL: scan for contradictions, propose fix."
# ... more turns until detector fires
python3 her_al_moment_detector.py dialog.ndjson
```

### Metrics

- **Precision:** Moment fires only when all 3 conditions met
- **Sensitivity:** Detects moment by turn N (typically 9-15)
- **Reproducibility:** Same log → same detection (deterministic)

---

## What This Is NOT

- ❌ A claim that HELEN is conscious
- ❌ A claim that MAYOR is sentient
- ❌ A new consciousness theory
- ❌ A replacement for CWL governance

---

## What This IS

- ✅ A deterministic dialogue architecture
- ✅ A measurable phase transition detector
- ✅ A persistent, append-only transcript system
- ✅ A test bed for two-voice interaction patterns
- ✅ A UI layer for CWL governance (non-sovereign)

---

## Next Steps

1. **Run the dialogue:** `./run_dialog_box.sh interactive`
2. **Provoke the moment:** Follow the 3-turn test above
3. **Check detection:** `python3 her_al_moment_detector.py dialog.ndjson`
4. **Integrate with SCF:** (Pending SCF implementation)
5. **Integrate with TownAdapter:** (Pending integration layer)

---

**Version:** 1.0
**Status:** Operational
**Authority:** FALSE
**Last Updated:** 2026-02-27
