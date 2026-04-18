# KERNEL CONSTITUTION

**Version:** 2.0.0  
**Date:** 2026-01-21  
**Status:** IMMUTABLE

---

## Non-Negotiable Constitutional Rules

### 1. Mayor-Only Verdict Output
**Rule:** Only Mayor V2 may emit `decision_record.json` (and optional `remediation_plan.json`).

**Enforcement:**
- No other component may write files with "decision" or "verdict" semantics
- EV district verifies this obligation: `mayor_emits_single_decision_record`

**Violation:** System integrity failure → NO_SHIP

---

### 2. Factory Emits Attestations Only
**Rule:** Factory may only emit attestations to append-only ledger. No verdicts, no decisions.

**Enforcement:**
- Factory writes to `attestations_ledger.jsonl` only
- No SHIP/NO_SHIP logic in Factory
- Attestations are truth primitives: `(run_id, obligation_name, policy_match, payload_hash, attestor, timestamp)`

**Violation:** Architecture violation → NO_SHIP

---

### 3. Kernel is JSON-First and Schema-Closed
**Rule:** Governance kernel accepts only schema-valid JSON. Everything else is UX/debug telemetry.

**Enforcement:**
- Briefcase must conform to `briefcase.schema.json`
- Attestations must conform to `attestation.schema.json`
- Decision records must conform to `decision_record.schema.json`
- `additionalProperties: false` on all schemas (fail closed)

**Violation:** Schema failure → NO_SHIP (enforced by EV district)

---

### 4. NO RECEIPT = NO SHIP
**Rule:** Every HARD obligation requires a matching satisfied attestation. No exceptions.

**Mathematical Definition:**
```
Let O_HARD = {o ∈ O : o.severity = "HARD"}
Let A = attestations for this run
Let sat(o, A) ≡ ∃a ∈ A : (a.obligation_name = o.name) ∧ (a.policy_match = 1)

SHIP ⟺ (¬kill_switch_triggered) ∧ (∀o ∈ O_HARD : sat(o, A))
```

**Enforcement:**
- Mayor V2 applies this predicate deterministically
- No confidence, no scoring, no reasoning
- Pure lookup: attestations.contains(obligation) → satisfied

**Violation:** Missing attestations → NO_SHIP with blocking_obligations listed

---

### 5. Districts are Parallel Obligation Analysis
**Rule:** Districts propose obligations independently. Mayor reduces attestations to verdict.

**Enforcement:**
- Districts emit `BuilderPacket` objects (non-sovereign)
- Concierge aggregates into single `Briefcase`
- Mayor never reads district packets directly
- Districts scale horizontally without changing Mayor logic

**Violation:** District bypassing Concierge → architecture violation

---

## Kernel Boundary Separation

### Cognition Layer (Simulation UX)
**Allowed:**
- Confidence scores
- QI-INT scoring
- Narrative reports
- Agent conversations (Streets, Buildings)
- Rich telemetry

**Forbidden:**
- Emitting SHIP/NO_SHIP decisions
- Writing decision_record.json
- Influencing Mayor's predicate
- Bypassing attestation requirements

**Storage:** `telemetry.jsonl` (separate from ledger)

---

### Governance Kernel (Truth Layer)
**Allowed:**
- Reading Briefcase (schema-valid JSON only)
- Executing deterministic tests (Factory)
- Emitting attestations (append-only ledger)
- Applying constitutional rules (Mayor)
- Emitting decision_record.json (Mayor only)

**Forbidden:**
- Reading confidence/scores/narratives
- Probabilistic reasoning
- Narrative persuasion
- Accepting non-schema inputs

**Storage:** `attestations_ledger.jsonl`, `decisions/decision_*.json`

---

## Mayor V2 Decision Semantics

### Constitutional Rules (Applied in Order)

**Rule 1: Kill-Switch Check**
```
IF kill_switch_triggered → NO_SHIP (immediate)
```

**Rule 2: HARD Obligations Check**
```
IF any unsatisfied HARD obligations → NO_SHIP
   WITH blocking_obligations = [list of unsatisfied names]
```

**Rule 3: Default**
```
ELSE → SHIP
```

### Properties
- **Deterministic:** Same briefcase + same attestations → same decision
- **Monotonic:** Adding satisfied attestations can only change NO_SHIP → SHIP
- **Transparent:** blocking_obligations explicitly lists missing receipts
- **No Reasoning:** Mayor never "thinks" about truth, only checks attestations

---

## Claim Type Routing

### COMMENTARY / ANALYSIS
- **Obligations:** 0 (typically)
- **Expected Verdict:** SHIP (immediate)
- **Rationale:** Meta-commentary doesn't require receipts

### CHANGE_REQUEST / REFACTOR
- **Obligations:** ≥ 1 HARD obligation
- **Expected Verdict:** NO_SHIP until receipts exist
- **Rationale:** Code changes require verification

### Unknown Claim Types
- **Fallback:** Treat as CHANGE_REQUEST (fail safe)
- Districts use keyword heuristics for classification

---

## Mandatory Districts (Core Pair)

### ENGINEERING District
**Purpose:** Code quality verification  
**Attestor:** `CI_RUNNER`

**HARD Obligations:**
1. `pyproject_installable` → `pip install -e .` exit 0
2. `unit_tests_green` → `pytest` exit 0
3. `imports_clean_oracle_town` → `python -c "import oracle_town"` exit 0

**Triggers:** claim_type ∈ {refactor, feature, fix, change_request}

---

### EV District (Evidence & Validation)
**Purpose:** Kernel integrity verification  
**Attestor:** `TOOL_RESULT`

**HARD Obligations:**
1. `attestation_ledger_written` → ledger exists, has run_id, valid JSONL
2. `mayor_emits_single_decision_record` → decision exists, valid schema, Mayor-owned
3. `briefcase_schema_valid` → briefcase conforms to schema
4. `replay_determinism_hash_match` → same inputs → same decision_digest (SOFT for MVP)

**Triggers:** All non-commentary claims

**Rationale:** Meta-verification - EV checks the checkers

---

## Scalability Invariants

### Horizontal Scaling (Correct)
✅ Add new districts (LEGAL, SECURITY, BUSINESS...)  
✅ Add new obligations per district  
✅ Add new attestors (SECURITY_SCANNER, HUMAN_REVIEW...)  
✅ Increase test parallelism in Factory

### Vertical Complexity (Forbidden)
❌ Add new decision logic to Mayor  
❌ Add confidence/scoring to decision path  
❌ Allow districts to emit verdicts  
❌ Bypass attestation requirements  
❌ Add "soft consensus" or "partial shipping"

**Principle:** System scales by adding constraints (obligations), not by adding intelligence.

---

## Determinism & Replay

### Canonical Form Requirements
1. **Sort object keys** (stable JSON serialization)
2. **Sort arrays** where order is non-semantic:
   - `required_obligations` (by name)
   - `blocking_obligations` (by name)
   - `attestations_checked` (by attestation_id)
3. **Exclude volatile fields** from decision_digest:
   - `timestamp` (optional in DecisionRecord)
   - `run_id` (if digest is for cross-run comparison)

### Decision Digest Computation
```python
def compute_decision_digest(decision_record):
    canonical = {
        "claim_id": decision_record.claim_id,
        "decision": decision_record.decision,
        "blocking_obligations": sorted(decision_record.blocking_obligations),
        "kill_switch_triggered": decision_record.kill_switch_triggered,
    }
    return sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
```

### EV Determinism Check
**Obligation:** `replay_determinism_hash_match`

**Test:**
1. Run governance loop with seed briefcase → decision D1
2. Replay with identical briefcase → decision D2
3. Assert: `digest(D1) == digest(D2)`

**Severity:** SOFT for MVP, HARD for production

---

## Pass Conditions (File-Based Truth)

### Mode A: COMMENTARY → SHIP
**Required Artifacts:**
1. ✅ `attestations_ledger.jsonl` exists (≥ 1 line with run_id)
2. ✅ `decisions/decision_{run_id}.json` exists
3. ✅ Decision contains:
   - `"decision": "SHIP"`
   - `"blocking_obligations": []`
   - `"kill_switch_triggered": false`

**Failure:** Missing artifact → treat as NO_SHIP (kernel integrity failure)

---

### Mode B: CHANGE_REQUEST → NO_SHIP (until receipts)
**Required Artifacts:**
1. ✅ `attestations_ledger.jsonl` exists with attestation entries
2. ✅ `decisions/decision_{run_id}.json` exists
3. ✅ Decision contains:
   - `"decision": "NO_SHIP"` (when receipts missing)
   - `"blocking_obligations": [...]` (non-empty)
   - `"kill_switch_triggered": false`

**Then, after Factory emits receipts:**
4. ✅ Re-run produces `"decision": "SHIP"`
5. ✅ `"blocking_obligations": []`

**Failure:** SHIP without receipts → constitutional violation

---

### Kill-Switch Mode
**Required Artifacts:**
1. ✅ Decision contains:
   - `"decision": "NO_SHIP"`
   - `"kill_switch_triggered": true`
   - No attestation checks needed (immediate halt)

---

## Confidence Telemetry (Non-Sovereign)

### Where Confidence is Allowed
- ✅ Street agent reports (ChatDev simulation)
- ✅ Building aggregations (QI-INT scoring)
- ✅ District narratives (risk assessments)
- ✅ UI visualizations (town simulation)

### Where Confidence is Forbidden
- ❌ Briefcase schema (no confidence field)
- ❌ Attestation schema (no confidence field)
- ❌ Mayor input (only reads briefcase + attestations)
- ❌ Factory logic (only executes tests)

### Enforcement
**Schema Boundary:**
```json
{
  "briefcase.schema.json": {
    "additionalProperties": false,
    "required": ["run_id", "claim_id", "required_obligations", "requested_tests"]
    // NO "confidence", "score", or "recommendation" fields
  }
}
```

**Storage Separation:**
- Cognition telemetry → `telemetry.jsonl` (never read by kernel)
- Governance truth → `attestations_ledger.jsonl` (only source for Mayor)

---

## Violation Response Protocol

### Schema Violation
**Trigger:** Briefcase/Attestation/DecisionRecord fails schema validation

**Response:**
1. EV district fails obligation: `briefcase_schema_valid`
2. Mayor emits: `NO_SHIP` with blocking_obligations
3. Remediation: Fix schema, re-run

**No Fallback:** Schema violations are hard failures

---

### Missing Attestation
**Trigger:** HARD obligation has no matching satisfied attestation

**Response:**
1. Mayor emits: `NO_SHIP` with blocking_obligations listing missing names
2. Remediation plan suggests: specific tests to run, expected attestors

**No Override:** Human approval cannot bypass missing receipts

---

### Kill-Switch Trigger
**Trigger:** Enabled kill-switch policy evaluates to true

**Response:**
1. Mayor emits: `NO_SHIP` with `kill_switch_triggered: true`
2. No attestation checks performed (immediate halt)
3. Remediation: Resolve policy violation (LEGAL/SECURITY approval required)

**Authority:** LEGAL, SECURITY teams (deterministic rule evaluation only)

---

## Amendment Process

**This constitution is IMMUTABLE.**

Changes require:
1. New version number (semantic versioning)
2. Migration path from previous version
3. Proof that new version preserves constitutional invariants
4. EV district verification of migration

**Forbidden Amendments:**
- Removing "NO RECEIPT = NO SHIP"
- Adding confidence to decision path
- Allowing non-Mayor verdict emission
- Bypassing schema validation

---

## Appendix: Canonical Artifacts

### Minimal Briefcase (Mode A)
```json
{
  "run_id": "RUN_MODE_A_001",
  "claim_id": "CLM_COMMENTARY_001",
  "claim_type": "COMMENTARY",
  "required_obligations": [],
  "requested_tests": [],
  "kill_switch_policies": []
}
```

### Minimal Attestation
```json
{
  "run_id": "RUN_MODE_B_001",
  "claim_id": "CLM_REFACTOR_001",
  "obligation_name": "unit_tests_green",
  "attestor": "CI_RUNNER",
  "policy_match": 1,
  "payload_hash": "abc123...",
  "timestamp": "2026-01-21T22:00:00.000Z"
}
```

### Minimal Decision Record (SHIP)
```json
{
  "run_id": "RUN_MODE_A_001",
  "claim_id": "CLM_COMMENTARY_001",
  "decision": "SHIP",
  "blocking_obligations": [],
  "kill_switch_triggered": false,
  "attestations_checked": 0,
  "timestamp": "2026-01-21T22:00:00.000Z",
  "code_version": "oracle_town_v2.0.0"
}
```

### Minimal Decision Record (NO_SHIP)
```json
{
  "run_id": "RUN_MODE_B_001",
  "claim_id": "CLM_REFACTOR_001",
  "decision": "NO_SHIP",
  "blocking_obligations": ["unit_tests_green", "pyproject_installable"],
  "kill_switch_triggered": false,
  "attestations_checked": 0,
  "timestamp": "2026-01-21T22:00:00.000Z",
  "code_version": "oracle_town_v2.0.0"
}
```

---

**End of Constitution**

**Enforcement:** This document is the canonical specification. Any implementation drift from these rules is a kernel bug, not a feature request.

**Audit:** EV district continuously verifies compliance with all constitutional rules.

---

*Signed: ORACLE TOWN V2 Governance Kernel*  
*Date: January 21, 2026*
