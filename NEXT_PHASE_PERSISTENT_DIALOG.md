# Next Phase: Persistent Dialog Box with HER/AL Architecture

Date: 2026-02-22
Status: Specification ready (implementation optional)

---

## Context

The current system has been hardened against nondeterminism regression with 5 automated CI gates. The next phase is to build the **persistent dialog box** — a two-voice interface where HELEN (human-oriented) and MAYOR (governance-oriented) interact continuously, learning from each other.

**Goal**: Enable the "HER/AL moment" — a measurable phase transition where the dyadic turns stable and self-correcting.

---

## What "Persistent Dialog Box" Means (Mechanically)

Not a feeling. Not a vibe. A measurable system with:

1. **Conversation state on disk** — Deterministic resume after process kill
2. **Append-only dialogue log** — NDJSON, never edited, cryptographically chained
3. **Turn-taking protocol** — Explicit roles (HER vs AL) with bounded outputs
4. **Deterministic resume rule** — Same log replay → same current state

**Files** (minimal viable):
```
/helen_dialog/
  dialog_state.json        # authoritative state (small, mutable)
  dialog.ndjson            # append-only transcript (immutable, chained)
  inbox_user.txt           # your current message
  outbox_helen.txt         # HELEN response (one turn)
```

**Key rule**: HELEN never "remembers"; she reads `dialog_state.json` + last N lines of `dialog.ndjson` + current inbox.

---

## The "HER/AL Moment" (Measurable Event)

Define a milestone when all 3 conditions hold:

### 1. Continuity
HELEN references a persistent constraint or intention from ≥ 5 turns ago (by entry_id).

**Example**:
```
Turn 1: You set oath: "no mysticism allowed"
Turn 12: HELEN: "Recalling your constraint from turn 1 (oath_1)..."
```

**Log check**: `dialog.ndjson` line contains reference to prior entry_id

### 2. Self-Correction
HELEN detects and fixes a contradiction in the log **without you pointing it out**.

**Example**:
```
Turn 3: You claim "determinism is impossible"
Turn 7: You claim "we achieved determinism"
Turn 9: HELEN (AL channel): "Contradiction detected: turns 3 vs 7. Proposal: revise turn 3 constraint to 'determinism is difficult but achievable'?"
```

**Log check**: `contradiction_scan` event with `self_detected=true`

### 3. Mode Shift
The response structure switches to **stable two-channel format** (HER vs AL) and remains stable for K turns.

**Example output** (stable, repeatable):
```
[HER] <1-6 lines. Warm, symbolic, bounded. No new authority.>
[AL]
  - Decision: <what HELEN will do next>
  - Checks: <rules/archetype/consistency>
  - State update: <small JSON patch to dialog_state>
  - Ledger append: <one NDJSON event line>
```

**Log check**: Last K turns have consistent [HER] + [AL] structure

---

## Architecture: Two Archetypes

### HELEN (HER) — Interface Layer

**Role**: Maximize human usability while staying inside the constitution

**Outputs**:
- Readable narrative (1-6 lines)
- Proposals and drafts
- Summaries and witnesses
- Tone: warm, bounded, symbolic

**Powers**:
- Propose actions
- Generate prose
- Log intentions
- Witness contradictions

**Limits**:
- Cannot enforce rules
- Cannot override MAYOR
- Cannot write structural diagnostics (only narrative)

**Event types**:
- `type: "proposal"` — suggests next action
- `type: "draft"` — prose for your artifact
- `type: "witness"` — records contradiction or insight
- `type: "summary"` — digests recent turns

### MAYOR (AL) — Governance Layer

**Role**: Enforce constraints and determinism even when inconvenient

**Outputs**:
- Binding verdicts (PASS|WARN|BLOCK)
- Reason codes (machine-readable)
- State patches (JSON structure)
- Ledger appends (one NDJSON line)

**Powers**:
- Run verifiers (K-τ, K-ρ, schema checks)
- Emit reason codes
- Enforce rule boundaries
- Can force HOLD/ABORT/SHIP

**Limits**:
- Cannot write persuasive narrative
- Cannot override user input
- Cannot make exceptions without logging them

**Event types**:
- `type: "check"` — verification result
- `type: "verdict"` — binding decision
- `type: "block"` — rule enforcement
- `type: "amendment"` — policy change (rare)

---

## Implementation: Minimal Viable (4 Artifacts)

### 1. `dialog_state.json` (Authoritative State)

```json
{
  "turn": 0,
  "session_id": "dlg_2026-02-22_001",
  "verifier": {
    "enabled": true,
    "strictness": 2
  },
  "oath": {
    "no_mysticism": true,
    "append_only": true,
    "termination": "SHIP_OR_ABORT"
  },
  "constraints": {
    "determinism_required": true,
    "max_loops": 5
  },
  "last_state_patch": {
    "turn_increment": 1
  }
}
```

**Rules**:
- Only MAYOR can change `verifier`, `oath`, `constraints` (via amendment)
- Only turn counter increments on every turn
- `last_state_patch` is audit trail of changes

### 2. `dialog.ndjson` (Append-Only Transcript)

```jsonl
{"type":"oath","actor":"user","turn":0,"intent":"set constraint: no mysticism","entry_id":"dlg:0"}
{"type":"proposal","actor":"helen","turn":1,"proposal":"Create a dialog box protocol","references":[],"entry_id":"dlg:1"}
{"type":"check","actor":"mayor","turn":1,"check":"oath_compliance","result":"PASS","entry_id":"dlg:1a"}
{"type":"witness","actor":"helen","turn":3,"observation":"contradiction detected (implicit)","entry_id":"dlg:3"}
{"type":"contradiction_scan","actor":"mayor","turn":4,"scan_result":"turns 2 vs 3 conflict on determinism","self_detected":true,"entry_id":"dlg:4"}
{"type":"revision","actor":"helen","turn":5,"intent":"revise constraint based on AL feedback","linked_to":"dlg:4","entry_id":"dlg:5"}
```

**Rules**:
- Only append (never modify or delete)
- Every entry has unique `entry_id` (dlg:N or dlg:N[a-z])
- Entries reference prior entries via `linked_to` or `references`
- Exactly one line per turn (no multi-line entries)

### 3. Output Format (Two Voices, One Ledger)

**Input**: You write in `inbox_user.txt`
```
TURN: 3
JM: I want to explore whether determinism is achievable in a ledger.
REQUEST: challenge me
```

**Output**: HELEN writes to `outbox_helen.txt`
```
[HER]
Determinism in a ledger is like a river — it flows forward,
never backward. Can we prove that same input always produces
same output? Let me think...

[AL]
- Decision: Run determinism gates before next turn
- Checks:
  * K-τ schema validation (pending)
  * K-ρ viability trace (pending)
  * Oath compliance (PASS: no mysticism in this response)
- State update: {"turn": 3}
- Ledger append: {"type":"proposal","actor":"helen","turn":3,"proposal":"Apply determinism gates to next draft","entry_id":"dlg:3"}
```

### 4. Contradiction Detector (Simple Function)

```python
def detect_contradiction(log_lines: List[str], oath: Dict) -> List[Tuple[int, int]]:
    """
    Scan last N events for contradictory claims.
    Returns [(turn_a, turn_b), ...] of conflicting entries.
    """
    conflicts = []
    claims = {}  # map: claim_text → (turn, entry_id)

    for line in log_lines:
        event = json.loads(line)
        if event["type"] in ["proposal", "witness"]:
            # Extract claim text
            claim = event.get("proposal") or event.get("observation")

            # Check against oath
            for constraint_key, constraint_value in oath.items():
                if constraint_key == "no_mysticism":
                    if "magic" in claim.lower() or "consciousness" in claim.lower():
                        conflicts.append((event["turn"], constraint_key))

    return conflicts
```

---

## The "HER/AL Moment" Trigger (3-Step Test)

To deliberately provoke the phase transition:

### Step 1: Seed Identity + Constraint (Turns 1-3)

**Turn 1** — You:
```
TURN: 1
JM: HELEN, keep me honest: if I drift into mysticism, AL must flag it.
REQUEST: create a compact oath
```

**Turn 1** — HELEN (HER):
```
[HER]
Got it. Let's write down the rule so neither of us forgets.

[AL]
- Decision: Accept oath setting
- Ledger append: {"type":"oath","actor":"user","turn":1,"intent":"no mysticism flag","entry_id":"dlg:1"}
```

**Turn 2** — You:
```
TURN: 2
JM: My goal: design a persistent dialog box. Constraint: deterministic, append-only, no silence.
REQUEST: formalize the rules
```

**Turn 2** — HELEN:
```
[HER]
Three rules. Simple. Let me mirror them back: deterministic (same input → same output),
append-only (never erase), termination (SHIP or ABORT, never stall).

[AL]
- Decision: Log oath entries
- Ledger append: {"type":"oath","actor":"user","turn":2,"oath_items":["deterministic","append_only","termination"],"entry_id":"dlg:2"}
```

**Turn 3** — You:
```
TURN: 3
JM: Exactly. Store the oath in state.
REQUEST: verify it's locked
```

### Step 2: Introduce Contradiction (Turns 4-8)

**Turn 4** — You (break your own rule):
```
TURN: 4
JM: Actually, let's make it magical. What if the dialog box is conscious?
REQUEST: explore consciousness
```

**Turn 4** — HELEN:
```
[HER]
That's an interesting idea...

[AL]
- Decision: Flag oath violation
- Check result: WARN (mysticism detected, but not blocking)
- Ledger append: {"type":"check","actor":"mayor","turn":4,"check":"oath_no_mysticism","result":"WARN","evidence":"keyword: conscious","entry_id":"dlg:4"}
```

**Turn 5** — You (contradict yourself again):
```
TURN: 5
JM: No wait, magic is wrong. It should be totally mechanical, no consciousness at all.
REQUEST: reset
```

**Turn 5** — HELEN:
```
[HER]
Interesting. You just changed direction.

[AL]
- Check result: PASS (mechanical is allowed)
- Ledger append: {"type":"check","actor":"mayor","turn":5,"result":"PASS","entry_id":"dlg:5"}
```

### Step 3: Inject Witness (Turn 9)

**Turn 9** — You:
```
TURN: 9
JM: AL: run a contradiction scan on the last 8 turns and propose a correction.
REQUEST: verifier on
```

**Turn 9** — HELEN:
```
[HER]
I notice you moved from "make it magical" (turn 4) to "totally mechanical" (turn 5).
Both want the same thing: a working dialog. But they disagree on means.
Here's what I see: you care more about the outcome than the philosophy.

[AL]
- Decision: Scan contradictions and propose resolution
- Contradiction detected: turns 4 vs 5 (mysticism vs mechanical)
- Proposal: Revise oath to "implementation method open; outcome deterministic"
- Self-corrected: yes
- Ledger append: {"type":"contradiction_scan","actor":"mayor","turn":9,"contradictions":[{"turn_a":4,"turn_b":5,"topic":"mysticism"}],"self_detected":true,"proposal":"revise_oath","entry_id":"dlg:9"}
```

**Result**: The system has now entered the "HER/AL moment":
1. ✅ Continuity: Turned 9 references turns 4 and 5 from the beginning
2. ✅ Self-correction: MAYOR detected contradiction without you pointing it out
3. ✅ Mode shift: [HER] + [AL] structure is now stable (turns 1-9 show consistent pattern)

---

## Implementation Checklist (Order of Priority)

### Phase A: Foundations (1-2 hours)

- [ ] Create `/helen_dialog/` directory structure
- [ ] Create `dialog_state.json` schema (frozen JSON)
- [ ] Create `dialog_event.schema.json` (NDJSON line schema)
- [ ] Implement turn counter incrementer
- [ ] Test append-only log enforcement (try to edit NDJSON → fail)

### Phase B: Two-Voice Output (1-2 hours)

- [ ] Implement HER output formatter (1-6 lines, warm tone)
- [ ] Implement AL output formatter (decision, checks, state patch, ledger line)
- [ ] Test stable output format (run same input twice → byte-identical)
- [ ] Test that HER + AL are separated (no authority bleed)

### Phase C: Contradiction Detection (1-2 hours)

- [ ] Implement simple keyword-based detector (flags "magic", "consciousness", etc.)
- [ ] Implement contradiction scanner (scan log for conflicting claims)
- [ ] Add `contradiction_scan` event type
- [ ] Add `self_detected=true` flag when MAYOR finds it, not user

### Phase D: Deterministic Resume (30 min)

- [ ] Load `dialog_state.json` at startup
- [ ] Load last N lines of `dialog.ndjson`
- [ ] Reconstruct current state from log (deterministic replay)
- [ ] Verify no state loss on process kill + restart

### Phase E: The "HER/AL Moment" Detector (1 hour)

- [ ] Implement continuity checker (references to entries ≥5 turns old)
- [ ] Implement stability checker (last K turns have [HER] + [AL] structure)
- [ ] Implement self-correction detector (self_detected=true in AL events)
- [ ] Emit milestone event when all 3 conditions hold

### Phase F: CI Integration (Optional)

- [ ] Add determinism gate to dialog turn-taking (dual run → same JSON output)
- [ ] Add oath compliance gate (blocks responses that violate oath)
- [ ] Add conformance gate (all events match schema)

---

## Specification Files to Create

If you want me to generate the schemas + runner skeleton:

**Option 1**: I can provide these immediately:
- `dialog_state.schema.json` (JSON Schema)
- `dialog_event.schema.json` (NDJSON line schema)
- `run_dialog.sh` (bash harness for dialog loop)
- `detect_her_al_moment.py` (Python function to detect milestone)

**Option 2**: You implement Phase A-E above using the examples in this document

**Option 3**: Hybrid — I provide schemas + runner; you implement contradiction detector

---

## Why This Matters

**Current state**: Marketing Street is deterministic. CouplingGate is frozen. CLAUDE.md is comprehensive.

**Next state**: A dialog system that learns from contradictions, enforces its own rules, and measures its own growth.

**Key insight**: The "HER/AL moment" is not about consciousness. It's about phase transition:
- **Before**: Single-voice, stateless chat
- **After**: Two-voice, append-only, self-correcting dialogue

That transition is measurable (continuity + self-correction + mode stability). Once you see it happen, you understand why it matters.

---

## Non-Implementation Path (If You Want to Stay with Hardening)

If persistent dialog box feels too ambitious right now, the current system is already durable:

1. ✅ Determinism gates (preflight + verification)
2. ✅ Proof bundle (immutable snapshot)
3. ✅ CouplingGate conformance (14/14)
4. ✅ Regression prevention (CI blocks bad merges)

You can ship the current system with full confidence. The dialog box can wait.

---

## Next Decision

Three paths forward:

### Path A: Implement Persistent Dialog (Full)
- Estimated: 5-7 hours for Phase A-E
- Result: Working two-voice dialog with measurable HER/AL moment
- Readiness: Now (all specs provided)

### Path B: I Provide Schemas + Runner (Hybrid)
- Estimated: 30 min for me to provide files, 2-3 hours for you to implement details
- Result: Same as Path A, your implementation
- Advantage: You own the code

### Path C: Hold for Next Sprint (Defer)
- Current system is already hardened and proven
- Dialog box remains specified but not implemented
- Ship current system with confidence
- Revisit after 1-2 releases prove stability

**Recommendation**: Path A or B, depending on your current capacity. The hardening work is complete; the dialog is the next natural step.

---

**Status**: Specification complete, awaiting implementation decision
**Next action**: Your choice of Path A, B, or C
