# 🔗 WUL ↔ ORACLE TOWN Integration

**Date:** January 21, 2026
**Status:** Specification Complete
**Implementation:** Phase 1 - WUL Primitives Ready

---

## 🎯 Executive Summary

**WUL (Wordless Universal Language)** is now integrated as the **formal governance language** of ORACLE TOWN's kernel.

**Key Principle:**
```
Nothing may execute unless it was explicitly allowed;
once prevented, that specific attempt stays prevented forever.
```

This provides:
- ✅ Deterministic, replay-safe decisions
- ✅ Audit-grade proof trails
- ✅ Mechanical enforcement (no trust required)
- ✅ Irreversible kill-switches

---

## 📊 ORACLE ↔ WUL Mapping Table

| ORACLE Component | Current (V2) | WUL Token | Meaning |
|-----------------|-------------|-----------|---------|
| **User Claim** | Natural language text | `E01(ref="PROP_{hash}")` | Proposition reference (no free text in WUL) |
| **Briefcase** | JSON with obligations | `R15(objective, claim)` | Root governance anchor |
| **Obligation** | `{name, severity, type}` | `R10(event, intent)` | Intent to execute event |
| **Attestation (satisfied)** | `policy_match=1` | `R25(event)` | ALLOW - permission granted |
| **Factory.verify() starts** | Test execution begins | `R28(event)` | INITIATE - execution starts |
| **Factory.verify() completes** | Test passes (exit 0) | `R29(event)` | TERMINATE - execution completes |
| **Kill-Switch Trigger** | `kill_switch_triggered=true` | `R21(event)` | PREVENT - event burned forever |
| **DecisionRecord** | JSON file | `sha256(canonical_wul_trace)` | Hash of complete WUL trace |

---

## 🏗️ Architecture Before/After

### Before WUL (ORACLE V2 - Current)

```
INPUT (natural language)
    ↓
CLAIM COMPILER (pattern matching)
    ↓
BRIEFCASE (JSON - schema validated)
    ↓
FACTORY (executes tests)
    ↓
ATTESTATIONS (policy_match ∈ {0,1})
    ↓
MAYOR (predicate over attestations)
    ↓
DECISION_RECORD.JSON
```

**Problem:** Briefcase is JSON with schema, but not formally provable or replay-deterministic.

---

### After WUL (ORACLE V3 - Target)

```
INPUT (natural language)
    ↓
CLAIM COMPILER (derives hash)
    ↓
WUL TREE (R15-rooted, strict tokens)
    ↓
WUL VALIDATOR (fail-closed, reason codes)
    ↓
    ├─ Valid → Continue
    └─ Invalid → NO_SHIP with WUL_REASON_CODE
    ↓
FACTORY (produces WUL trace: ALLOW → INITIATE → TERMINATE)
    ↓
WUL TRACE VALIDATOR
    ↓
    ├─ Missing ALLOW → INVALID (cannot INITIATE)
    ├─ PREVENT exists → BURNED (cannot retry)
    └─ Valid chain → Continue
    ↓
MAYOR (pure predicate over WUL trace)
    ↓
DECISION_RECORD = sha256(canonical_wul_trace)
```

**Benefit:** Every decision is now a **cryptographic hash** of a **mechanically validated** proof trace.

---

## 🔧 WUL Primitives (Minimal Kernel)

### Token Definitions

```python
WUL_PRIMITIVES = {
    # Root
    "R15": (arity=2) "Objective Return - governance anchor"

    # Claim structure
    "D01": (arity=1) "Claim - contains proposition"
    "E01": (arity=0) "Proposition - leaf with ref"
    "E03": (arity=0) "Objective - leaf with ref"

    # Event lifecycle (ORACLE obligations)
    "R10": (arity=2) "Intent - obligation declaration"
    "R25": (arity=1) "ALLOW - permission granted"
    "R28": (arity=1) "INITIATE - execution starts"
    "R29": (arity=1) "TERMINATE - execution completes"

    # Safety override
    "R21": (arity=1) "PREVENT - permanently forbid"

    # Event reference
    "E_EVENT": (arity=0) "Event ID - leaf"
}
```

### Validation Rules

1. **Root must be R15**
   ```
   If tree.id != "R15" → WUL_R15_MISSING
   ```

2. **Arity must match**
   ```
   If len(args) != primitive.arity → WUL_BAD_ARITY
   ```

3. **No unknown symbols**
   ```
   If token.id not in PRIMITIVES → WUL_UNKNOWN_SYMBOL
   ```

4. **Ref pattern strict**
   ```
   If ref exists and !match(^[A-Z][A-Z0-9_]{0,63}$) → WUL_INVALID_REF
   ```

5. **Bounds enforced**
   ```
   If depth > max_depth or nodes > max_nodes → WUL_BOUNDS_VIOLATION
   ```

**Constitutional Rule:** Fail-closed - any violation → deterministic rejection.

---

## 📝 Example: ORACLE Shipping Run in WUL

### Scenario
User submits claim: "Refactor Mayor to remove confidence scoring"

### WUL Trace (Complete)

#### 1. Claim Registration
```json
{
  "id": "R15",
  "args": [
    {"id": "E03", "ref": "OBJECTIVE_MAIN"},
    {"id": "D01", "args": [
      {"id": "E01", "ref": "PROP_A7F3C2E9D8B1..."}
    ]}
  ]
}
```

**Meaning:** Claim is anchored to governance root R15 with proposition hash.

---

#### 2. Obligation Intents (ENGINEERING District)
```json
[
  {"id": "R10", "args": [
    {"id": "E_EVENT", "ref": "EVENT_PYPROJECT_INSTALLABLE"},
    {"id": "E01", "ref": "PYPROJECT_INSTALLABLE"}
  ]},
  {"id": "R10", "args": [
    {"id": "E_EVENT", "ref": "EVENT_UNIT_TESTS_GREEN"},
    {"id": "E01", "ref": "UNIT_TESTS_GREEN"}
  ]},
  {"id": "R10", "args": [
    {"id": "E_EVENT", "ref": "EVENT_IMPORTS_CLEAN_ORACLE_TOWN"},
    {"id": "E01", "ref": "IMPORTS_CLEAN_ORACLE_TOWN"}
  ]}
]
```

**Meaning:** Three obligations declared (intents).

---

#### 3. Factory Execution (For event: `EVENT_UNIT_TESTS_GREEN`)

**ALLOW (attestation exists):**
```json
{"id": "R25", "args": [
  {"id": "E_EVENT", "ref": "EVENT_UNIT_TESTS_GREEN"}
]}
```

**INITIATE (Factory runs pytest):**
```json
{"id": "R28", "args": [
  {"id": "E_EVENT", "ref": "EVENT_UNIT_TESTS_GREEN"}
]}
```

**TERMINATE (pytest exits 0):**
```json
{"id": "R29", "args": [
  {"id": "E_EVENT", "ref": "EVENT_UNIT_TESTS_GREEN"}
]}
```

**Validation:**
```
✅ R25 exists → ALLOW granted
✅ R28 after R25 → Valid INITIATE
✅ R29 after R28 → Valid TERMINATE
→ Obligation satisfied
```

---

#### 4. Mayor Decision (Pure Predicate)

**Input:** WUL trace with all events having valid `R25 → R28 → R29` chains

**Predicate:**
```python
def decide_wul(trace):
    if not validate_wul(trace):
        return "NO_SHIP", trace.reason_code

    if any_prevent_tokens(trace):
        return "NO_SHIP", "WUL_PREVENT_TRIGGERED"

    required_events = extract_intents(trace)
    for event in required_events:
        if not has_valid_chain(event, trace):  # R25 → R28 → R29
            return "NO_SHIP", "WUL_MISSING_ALLOW"

    return "SHIP", "WUL_VALID"
```

**Output:**
```json
{
  "decision": "SHIP",
  "reason": "WUL_VALID",
  "trace_hash": "sha256(canonical_wul_trace)",
  "events_verified": 3
}
```

---

### Counter-Example: Kill-Switch Scenario

**LEGAL team triggers kill-switch for `EVENT_UNIT_TESTS_GREEN`:**

```json
{"id": "R21", "args": [
  {"id": "E_EVENT", "ref": "EVENT_UNIT_TESTS_GREEN"}
]}
```

**Effect:**
- Event `EVENT_UNIT_TESTS_GREEN` is **burned**
- Cannot be initiated (even if R25 exists)
- To retry, must create new event ID: `EVENT_UNIT_TESTS_GREEN_V2`

**Mayor Decision:**
```json
{
  "decision": "NO_SHIP",
  "reason": "WUL_PREVENT_TRIGGERED",
  "prevented_events": ["EVENT_UNIT_TESTS_GREEN"]
}
```

**Constitutional Guarantee:** Monotone safety - system cannot silently revert a safety denial.

---

## 🔒 How WUL Strengthens ORACLE

### 1. Satisfaction Relation (Deterministic)

**Before (V2):**
```python
satisfied = any(
    a.obligation_name == o.name and a.policy_match == 1
    for a in attestations
)
```
**Problem:** Relies on attestation format, vulnerable to schema drift.

**After (WUL):**
```python
satisfied = wul_trace_contains_valid_chain(
    event_id=obligation_to_event(o.name),
    chain=[R25, R28, R29]
)
```
**Benefit:** Formally provable, replay-deterministic.

---

### 2. Fail-Closed Policy (Mechanical)

**Before:**
- Schema validation via JSON Schema (good)
- But still accepts "unexpected" fields in JSON

**After:**
- WUL validator rejects **any** unknown token
- Arity mismatch → immediate rejection
- No escape hatches

**Example:**
```python
# Attacker tries to add confidence field
bad_tree = {"id": "R15", "args": [...], "confidence": 0.99}

validator.validate(bad_tree)
→ False, WUL_INVALID, "Unknown field: confidence"
```

---

### 3. Kill-Switch Semantics (Irreversible)

**Before:**
```python
if kill_switch_triggered:
    return "NO_SHIP"
```
**Problem:** Not clear if this is temporary or permanent.

**After:**
```python
if R21_token_exists_for_event(event_id):
    return "NO_SHIP", "EVENT_BURNED"
    # Cannot retry with same event_id
```
**Benefit:** Explicit monotone safety - once prevented, cannot be undone.

---

### 4. Invariants (Compiled, Not Documented)

**Before:**
- Constitution documents invariants in markdown
- Humans must enforce compliance

**After:**
- WUL validator **is** the constitution
- Invariants are code (frozen primitives table)
- Violations produce reason codes (mechanically)

**Example:**
```python
# Invariant: "Root must be R15"
# Before: documented in KERNEL_CONSTITUTION.md
# After: enforced in validator.validate()

if tree.id != "R15":
    return WUL_R15_MISSING  # Machine-readable reason
```

---

### 5. Threat Model (Attack Prevention)

| Attack | V2 Defense | WUL Defense |
|--------|-----------|-------------|
| **Hallucinated approval** | Schema validation | No ALLOW token → INITIATE invalid |
| **Silent override** | Append-only ledger | PREVENT burns event ID forever |
| **Log tampering** | File integrity | Hash mismatch on canonical WUL trace |
| **Agent persuasion** | Separation of layers | Agents can't emit WUL tokens |
| **Receipt spam** | Mayor checks attestations | Unused tokens ignored (arity enforced) |
| **Free text injection** | JSON schema | Ref pattern `^[A-Z][A-Z0-9_]{0,63}$` blocks text |

---

## 🚀 Integration Plan (3 Phases)

### Phase 1: WUL Primitives (✅ COMPLETE)

**Status:** Implementation complete
**Artifact:** `oracle_town/core/wul_primitives.py`

**Capabilities:**
- ✅ WUL token definitions (R15, D01, E01, R25, R28, R29, R21, E_EVENT)
- ✅ WUL validator (arity, bounds, ref pattern)
- ✅ Reason codes (WUL_R15_MISSING, WUL_BAD_ARITY, etc.)
- ✅ ORACLE ↔ WUL mapping functions

---

### Phase 2: Factory WUL Trace Generation (NEXT)

**Goal:** Make Factory emit WUL trace instead of plain attestations

**Changes Required:**

**2.1 Update Factory to produce WUL tokens:**

```python
# OLD (V2)
attestation = Attestation(
    obligation_name="unit_tests_green",
    policy_match=1,
    ...
)

# NEW (V3)
event_id = obligation_to_wul_event("unit_tests_green")

wul_trace = [
    create_wul_allow(event_id),      # R25
    create_wul_initiate(event_id),   # R28
    # Run test
    create_wul_terminate(event_id),  # R29 if pass
    # OR create_wul_prevent(event_id) if kill-switch
]
```

**2.2 Write WUL trace to append-only ledger:**

```python
# wul_trace_ledger.jsonl (one token per line)
{"id": "R25", "args": [...], "event": "EVENT_UNIT_TESTS_GREEN", "timestamp": "..."}
{"id": "R28", "args": [...], "event": "EVENT_UNIT_TESTS_GREEN", "timestamp": "..."}
{"id": "R29", "args": [...], "event": "EVENT_UNIT_TESTS_GREEN", "timestamp": "..."}
```

---

### Phase 3: Mayor WUL Predicate (FINAL)

**Goal:** Make Mayor decide based on WUL trace validation, not attestation lookup

**Changes Required:**

**3.1 Replace Mayor V2 logic:**

```python
# OLD (V2)
def decide(briefcase, attestations):
    hard_names = {o.name for o in hard_obligations}
    satisfied = {a.obligation_name for a in attestations if a.policy_match == 1}
    unsatisfied = hard_names - satisfied

    if unsatisfied:
        return "NO_SHIP"
    return "SHIP"

# NEW (V3)
def decide(wul_tree, wul_trace):
    # Step 1: Validate WUL structure
    valid, code, msg = wul_validator.validate(wul_tree)
    if not valid:
        return "NO_SHIP", code

    # Step 2: Check for PREVENT tokens
    if any_prevent_in_trace(wul_trace):
        return "NO_SHIP", "WUL_PREVENT_TRIGGERED"

    # Step 3: Verify all intents have valid chains
    required_events = extract_intents_from_tree(wul_tree)
    for event_id in required_events:
        if not has_valid_chain(event_id, wul_trace):  # R25 → R28 → R29
            return "NO_SHIP", "WUL_MISSING_ALLOW"

    # Step 4: All checks pass
    return "SHIP", "WUL_VALID"
```

**3.2 DecisionRecord becomes hash:**

```python
# OLD
decision_record = {
    "decision": "SHIP",
    "blocking_obligations": [],
    ...
}

# NEW
decision_record = {
    "decision": "SHIP",
    "wul_trace_hash": sha256(canonical_wul_trace),
    "wul_reason": "WUL_VALID",
    "events_verified": 3
}
```

---

## 📊 Benefits Summary

| Capability | Before WUL | After WUL |
|-----------|-----------|-----------|
| **Determinism** | Schema-validated JSON | Cryptographic hash of token tree |
| **Replay** | Re-run with same inputs | Hash comparison (instant) |
| **Audit** | Read attestation ledger | Verify WUL trace mechanically |
| **Kill-Switch** | Flag in decision record | Event ID burned (permanent) |
| **Proof** | "These attestations exist" | "Here's the canonical trace hash" |
| **Attack Surface** | Schema drift, free text | Frozen primitives, no text |
| **Error Messages** | "Missing attestation" | "WUL_MISSING_ALLOW for event X" |
| **Compliance** | JSON Schema validation | Formal language validation |

---

## 🎓 One-Sentence Summary

**WUL transforms ORACLE from a schema-validated decision system into a formally provable, replay-deterministic governance kernel where every decision is a cryptographic hash of a mechanically validated proof trace.**

---

## 📁 Files Created

```
oracle_town/core/
├── wul_primitives.py          # ✅ NEW: WUL token definitions & validator
├── factory.py                  # TODO: Update to emit WUL trace
└── mayor_v2.py                 # TODO: Update to validate WUL trace

WUL_ORACLE_INTEGRATION.md       # ✅ NEW: This document
KERNEL_CONSTITUTION.md          # Updated to reference WUL
```

---

## 🚀 Next Step

**Choose one:**

1. **"implement phase 2"** - Update Factory to emit WUL trace
2. **"implement phase 3"** - Update Mayor to validate WUL trace
3. **"show example"** - Full ORACLE shipping run in WUL (concrete JSON)
4. **"show attack"** - How ORACLE fails without WUL (exploit scenario)

Ready when you are! 🏛️
