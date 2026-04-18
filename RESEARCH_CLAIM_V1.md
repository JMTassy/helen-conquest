# RESEARCH_CLAIM_V1

## Ingestion Boundary for Speculative Research

**Purpose:** Define the object schema and admission law for legacy mathematical, cryptographic, and theoretical research entering HELEN OS. Prevents undifferentiated material from masquerading as doctrine.

**Core Law:**
```
No legacy corpus survives import as narrative.
Every imported item must become typed, tiered, and explicitly marked.
Tier III = WILD = quarantined by default.
Tier I = admissible only after receipt, replay, and federation review.
```

---

## 1. Object Purpose

**RESEARCH_CLAIM_V1** is a typed container for:

- Observations from legacy corpus
- Conjectures (testable or speculative)
- Heuristics (candidate guidance, non-binding)
- Proposed invariants (candidate properties)
- Proposed metrics (candidate measurements)
- Cryptographic ideas (candidate protocols)
- Architectural analogies (candidate patterns)

**What it is NOT:**
- Doctrine
- Law
- Executable authority
- Sovereign policy
- Truth claim

---

## 2. Required Fields

Every RESEARCH_CLAIM_V1 object MUST have:

### 2.1 Identity

```json
{
  "type": "RESEARCH_CLAIM_V1",
  "claim_id": "rc_<source_domain>_<seq>_<hash_prefix>",
  "version": "1.0",
  "created_timestamp": "2026-03-08T...",
  "source_domain": "ENUM[prime_number_theory, riemann_hypothesis, cryptography, governance, control_theory, emergence, other]",
  "author_context": "legacy_corpus | research_session | synthesized"
}
```

**Format Rules:**
- `claim_id` must be globally unique
- `source_domain` must be explicit (no "general" category)
- UUID format for `hash_prefix`: first 8 chars of SHA256(statement + timestamp)

---

### 2.2 Epistemic Class

```json
{
  "claim_kind": "ENUM[observation, conjecture, heuristic, invariant, metric, protocol, attack_vector, task, dependency, receipt_ref]",
  "tier": "ENUM[I, II, III]",
  "shipability": "ENUM[NONSHIPABLE, CANDIDATE, ADMISSIBLE_PENDING]",
  "author_mode": "ENUM[RESEARCHER, WILD, FORMAL]"
}
```

**Definitions:**

| Field | Value | Meaning |
|---|---|---|
| `claim_kind` | observation | Empirical fact from prior work |
| | conjecture | Testable hypothesis |
| | heuristic | Candidate guidance (non-binding) |
| | invariant | Proposed property claim |
| | metric | Proposed measurement |
| | protocol | Candidate procedure |
| | attack_vector | Potential vulnerability |
| | task | Actionable item |
| | dependency | Prerequisite claim |
| | receipt_ref | Proof pointer to existing receipt |
| `tier` | I | Receipt-backed, replayable, schema-valid |
| | II | Structured, explicit dependencies, falsifiable |
| | III | Speculative, quarantined by default |
| `shipability` | NONSHIPABLE | Cannot enter sovereign judgment |
| | CANDIDATE | Eligible for promotion path |
| | ADMISSIBLE_PENDING | Awaiting T0–T5 review |
| `author_mode` | RESEARCHER | Formal, attributed research |
| | WILD | Speculative, mythopoetic |
| | FORMAL | Constitutional specification |

---

### 2.3 Statement & Evidence

```json
{
  "statement": "Plain text representation of the claim. Must be atomic (not a disjunction). No metaphysics. No ungrounded causal language.",
  "statement_type": "ENUM[predicate, relation, inequality, protocol_step, heuristic_rule, invariant_assertion]",
  "statement_formality": "ENUM[natural_language, pseudocode, mathematical_notation, logic_formula]",
  "evidence_refs": ["rc_...", "RCP-...", "receipt_id"],
  "evidence_status": "ENUM[NONE, PARTIAL, FULL]",
  "evidence_completeness_notes": "Brief description of what evidence is present/absent"
}
```

**Statement Rules:**

1. Must be parseable (no contradictory clauses)
2. Must avoid metaphysical operators (e.g., "governs the nature of", "reveals the essence of")
3. Must be falsifiable or testable (even if not presently tested)
4. One claim per statement (no "A and B implies C")

**Evidence Status Scale:**
- `NONE`: No evidence present
- `PARTIAL`: Some evidence (e.g., reference citations, prior work links)
- `FULL`: Complete evidence chain (proofs, test results, receipts)

---

### 2.4 Dependencies & Assumptions

```json
{
  "dependency_claim_ids": ["rc_...", "rc_..."],
  "assumption_ids": ["assumption_id_1", "..."],
  "conflicts_with": ["rc_...", "rc_..."],
  "superseded_by": ["rc_..."],
  "notes_on_dependencies": "Human-readable dependency explanation"
}
```

**Rules:**

1. `dependency_claim_ids` must be non-empty for any Tier II or higher claim
2. If no dependencies, explicitly set: `"dependency_claim_ids": []` with note `"Self-contained"`
3. `conflicts_with` must be filled if claim contradicts any other claim
4. Circular dependencies are forbidden (acyclic DAG required)

---

### 2.5 Operational Intent

```json
{
  "proposed_operational_use": "ENUM[search_heuristic, scoring_metric, stress_test, invariant_candidate, protocol_component, infrastructure, crypto_primitive, policy_parameter, analysis_tool]",
  "use_description": "How this claim would be used if admitted. Be specific.",
  "operational_value": "ENUM[critical, high, medium, low, unknown]",
  "operational_cost": "What resources/time/complexity would be required to operationalize?",
  "safety_implications": "What could go wrong if this claim is promoted?"
}
```

**Use Values:**
- `search_heuristic`: Guides exploration but doesn't constrain
- `scoring_metric`: Candidate for Mayor score vector
- `stress_test`: Used to test robustness (doesn't ship)
- `invariant_candidate`: Proposed property to maintain
- `protocol_component`: Building block for governance protocol
- `infrastructure`: Part of kernel/system foundation
- `crypto_primitive`: Hash, cipher, signature candidate
- `policy_parameter`: Configuration value
- `analysis_tool`: Used for introspection/reporting

---

### 2.6 Replayability & Receipts

```json
{
  "replayability_status": "ENUM[NONE, PARTIAL, FULL]",
  "replay_command": "Bash/Python command to reproduce or verify the claim",
  "replay_artifact_hash": "SHA256 of expected output",
  "receipt_status": "ENUM[NONE, PARTIAL, FULL]",
  "receipt_refs": ["RCP-...", "WIT-..."],
  "replay_notes": "Any caveats about reproducibility"
}
```

**Replayability Scale:**
- `NONE`: Cannot be replayed (e.g., pure heuristic)
- `PARTIAL`: Can be partially reproduced (e.g., some test cases run)
- `FULL`: Deterministic, bit-identical replay possible

**Receipt Status Scale:**
- `NONE`: No receipt exists
- `PARTIAL`: Some evidence but no formal receipt
- `FULL`: Complete receipt chain (governance VM commitment)

---

### 2.7 Tier Assignment Rules

```json
{
  "tier_assignment_rationale": "Why is this claim classified at this tier?",
  "tier_promotion_path": "What steps would promote this to higher tier?",
  "tier_demotion_triggers": ["contradiction_detected", "replay_fails", "circular_dependency", "..."]
}
```

**Automatic Tier III (WILD) Triggers:**

A claim is forced into Tier III if ANY of the following hold:

1. ❌ Uses ungrounded metaphysical language as causal justification
   - Examples: "governs the deep structure", "reveals the essence", "contains the answer"
   - Allowed: "proposes a candidate for", "would enable", "might constrain"

2. ❌ Lacks measurable predicates
   - Examples: Claim with no way to verify true/false
   - Required: At least one testable prediction

3. ❌ Lacks explicit dependencies
   - Examples: "follows from prior work" without listing prior work
   - Required: Full dependency DAG

4. ❌ Cannot be replayed
   - Examples: Pure narrative, no command/computation specified
   - Required: At least PARTIAL replayability for Tier II+

5. ❌ Cannot be mapped to claim graph
   - Examples: Circular definitions, self-referential claims
   - Required: Acyclic decomposition

6. ❌ Proposes kernel/governance changes by analogy alone
   - Examples: "Braid memory suggests we should change the ledger"
   - Required: Explicit receipt or T0–T5 review path

---

### 2.8 Quarantine Default

```json
{
  "quarantine_status": "ENUM[ACTIVE, RELEASED, PROMOTED, REJECTED]",
  "quarantine_reason_codes": ["NO_RECEIPT", "NARRATIVE_ONLY", "UNGROUNDED_METAPHYSICS", "CIRCULAR_DEPENDENCY", "EMPIRICAL_TEST_FAILED", "..."],
  "quarantine_sandbox": "IDEA_SANDBOX_V1"
}
```

**Default:** All Tier III claims are automatically placed in `IDEA_SANDBOX_V1` (non-shipable, pressure-test only).

**Release Conditions:**
- Reclassification to Tier II with explicit dependencies OR
- Explicit human override with documented justification

---

## 3. Validation Schema (JSON Schema v2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "title": "RESEARCH_CLAIM_V1",
  "required": [
    "type", "claim_id", "version", "claim_kind", "tier", "statement",
    "evidence_status", "replayability_status", "receipt_status", "shipability",
    "dependency_claim_ids", "quarantine_status"
  ],
  "properties": {
    "type": { "const": "RESEARCH_CLAIM_V1" },
    "claim_id": { "type": "string", "pattern": "^rc_[a-z0-9_]+_[a-f0-9]{8}$" },
    "version": { "const": "1.0" },
    "tier": { "enum": ["I", "II", "III"] },
    "shipability": { "enum": ["NONSHIPABLE", "CANDIDATE", "ADMISSIBLE_PENDING"] },
    "statement": { "type": "string", "minLength": 20, "maxLength": 500 },
    "evidence_status": { "enum": ["NONE", "PARTIAL", "FULL"] },
    "replayability_status": { "enum": ["NONE", "PARTIAL", "FULL"] },
    "receipt_status": { "enum": ["NONE", "PARTIAL", "FULL"] },
    "dependency_claim_ids": { "type": "array", "items": { "type": "string" } },
    "quarantine_status": { "enum": ["ACTIVE", "RELEASED", "PROMOTED", "REJECTED"] }
  },
  "allOf": [
    {
      "if": { "properties": { "tier": { "const": "III" } } },
      "then": {
        "properties": {
          "quarantine_status": { "enum": ["ACTIVE"] },
          "shipability": { "const": "NONSHIPABLE" }
        }
      }
    },
    {
      "if": { "properties": { "tier": { "enum": ["I", "II"] } } },
      "then": {
        "properties": {
          "dependency_claim_ids": { "minItems": 1 }
        }
      }
    },
    {
      "if": { "properties": { "tier": { "const": "I" } } },
      "then": {
        "properties": {
          "receipt_status": { "const": "FULL" },
          "replayability_status": { "enum": ["PARTIAL", "FULL"] }
        }
      }
    }
  ]
}
```

---

## 4. Invalid Forms (Hard Rejections)

The following are **REJECTED at schema validation**:

1. **Bare narrative**
   - ❌ `"statement": "Research suggests that something important might happen"`
   - ✅ `"statement": "If X > threshold, then Y decreases monotonically"`

2. **Metaphysical causation**
   - ❌ `"statement": "The zeta function governs deep governance"`
   - ✅ `"statement": "Zeta zeros correlate with spectral properties of random matrices (as studied in RMT)"`

3. **Circular dependencies**
   - ❌ `claim_id: "rc_A"` depends on `"rc_B"` which depends on `"rc_A"`
   - ✅ Acyclic DAG only

4. **Tier I without receipt**
   - ❌ `tier: "I"` with `receipt_status: "NONE"`
   - ✅ `tier: "I"` requires `receipt_status: "FULL"`

5. **NONSHIPABLE with promotion_path**
   - ❌ `shipability: "NONSHIPABLE"` with `"tier_promotion_path": "..."`
   - ✅ Tier III stays NONSHIPABLE; promotion requires reclassification first

6. **Empty dependency list for Tier II+**
   - ❌ `tier: "II"` with `dependency_claim_ids: []` and no note
   - ✅ Must explicitly note `"Self-contained"` if dependencies truly absent

---

## 5. Tier Promotion Rules

A claim may be promoted from Tier III → II or II → I only if:

1. **Tier III → II:**
   - ✅ Reclassified with explicit dependencies listed
   - ✅ Statement rewritten to avoid metaphysical language
   - ✅ At least PARTIAL replayability achieved
   - ✅ Quarantine reason codes resolved (none of: UNGROUNDED_METAPHYSICS, CIRCULAR_DEPENDENCY, etc.)

2. **Tier II → I:**
   - ✅ Receipt status upgraded to FULL
   - ✅ Replayability at least PARTIAL
   - ✅ Dependency graph verified acyclic
   - ✅ Passes claim graph decomposition
   - ✅ Mayor score vector computed and above threshold
   - ✅ T0–T5 federation review complete with PASS or bounded HOLD

---

## 6. Quarantine Defaults & Promotion

**Default Behavior:** All Tier III claims enter `IDEA_SANDBOX_V1` automatically.

**Quarantine Codes:**

| Code | Meaning | Resolution |
|---|---|---|
| NO_RECEIPT | No formal receipt backing the claim | Emit receipt or accept NONSHIPABLE |
| NO_REPLAY | Claim cannot be verified computationally | Provide replay command or accept NONSHIPABLE |
| NARRATIVE_ONLY | Pure prose, no predicates | Reformulate as measurable statement |
| UNGROUNDED_METAPHYSICS | Uses causal language without evidence | Remove metaphysical framing |
| CIRCULAR_DEPENDENCY | Self-referential or circular dependency graph | Break cycle; establish acyclic DAG |
| EMPIRICAL_TEST_FAILED | Claim contradicts observed behavior | Mark conflicts_with; demote tier |
| UNKNOWN_SOURCE | Source domain unclear or mixed | Classify source_domain explicitly |

---

## 7. Lifespan & Mutation

### 7.1 Create

New claim enters system as RESEARCH_CLAIM_V1 object with:
- `tier: "III"` (default)
- `quarantine_status: "ACTIVE"`
- `shipability: "NONSHIPABLE"`

### 7.2 Classify

Ingestion service tags claim:
- Checks all auto-quarantine triggers
- Assigns `quarantine_reason_codes`
- Sets `claim_kind`, `source_domain`
- Routes to IDEA_SANDBOX_V1 if Tier III

### 7.3 Promote (Optional)

If claim meets Tier II criteria:
- Reclassify dependencies
- Update `tier: "II"`
- Route to CLAIM_GRAPH_V1 ingestion
- Request Mayor scoring

### 7.4 Review (Optional)

If claim promoted to Tier II and Mayor score high:
- Route to T0–T5 federation review
- Emit RESEARCH_EVAL_RECEIPT_V1
- Update `shipability` to ADMISSIBLE_PENDING

### 7.5 Reduce (Final)

Only deterministic reducer may emit:
- QUEST_RESULT (claim accepted as task)
- LAW_INSCRIPTION (claim becomes invariant)
- NO_SHIP (claim rejected or returned to RESEARCH)

---

## 8. Example: Prime Gap Heuristic (Tier III → II Path)

### Initial Import (Tier III, NONSHIPABLE)

```json
{
  "type": "RESEARCH_CLAIM_V1",
  "claim_id": "rc_prime_number_theory_001_a2f3b7e",
  "tier": "III",
  "claim_kind": "heuristic",
  "statement": "Prime gaps grow logarithmically with prime size, suggesting self-organized criticality in number-theoretic structures.",
  "source_domain": "prime_number_theory",
  "author_mode": "WILD",
  "evidence_status": "PARTIAL",
  "replayability_status": "NONE",
  "receipt_status": "NONE",
  "shipability": "NONSHIPABLE",
  "quarantine_status": "ACTIVE",
  "quarantine_reason_codes": ["UNGROUNDED_METAPHYSICS", "NO_REPLAY"],
  "proposed_operational_use": "stress_test",
  "dependency_claim_ids": []
}
```

**Quarantine Reason:** "Self-organized criticality" is metaphysical framing without evidence linkage.

### Reclassification Attempt (Tier II)

After explicit rework:

```json
{
  "claim_id": "rc_prime_number_theory_001_a2f3b7e",
  "tier": "II",
  "statement": "Empirical data shows prime gaps G_n < log²(p_n) for primes p_n up to 10^9; heuristic: model as random variable with parameter depending on prime density.",
  "evidence_refs": ["cite_TitchmarshTheory", "cite_CramersConjecture"],
  "evidence_status": "PARTIAL",
  "replayability_status": "PARTIAL",
  "replay_command": "python3 check_prime_gaps.py 1000000 --verbose",
  "dependency_claim_ids": ["rc_prime_number_theory_gapbound_001", "rc_random_matrix_theory_spectral"],
  "quarantine_status": "RELEASED",
  "quarantine_reason_codes": []
}
```

**Changes:**
- Removed "self-organized criticality" (metaphysical)
- Added specific empirical bounds
- Linked dependencies
- Provided replay command
- Changed quarantine status to RELEASED

### Promotion to Tier I (with Receipt)

```json
{
  "claim_id": "rc_prime_number_theory_001_a2f3b7e",
  "tier": "I",
  "receipt_status": "FULL",
  "receipt_refs": ["RCP-PRIME-GAP-001"],
  "shipability": "ADMISSIBLE_PENDING",
  "proposed_operational_use": "scoring_metric"
}
```

**Conditions Met:**
- Receipt emitted (RCP-PRIME-GAP-001)
- Replayability PARTIAL
- Dependencies explicit and acyclic
- Mayor scoring complete
- T0–T5 review passed (or bounded HOLD)

---

## 9. Non-Negotiable Laws (Carved Into Schema)

```
rule_no_receipt_no_claim:
  if receipt_status == NONE:
    then shipability = NONSHIPABLE

rule_no_replay_no_admission:
  if replayability_status == NONE:
    then tier >= III  (max tier is III)

rule_no_tier_no_processing:
  if tier not in [I, II, III]:
    then claim is invalid

rule_no_authority_separation_no_ship:
  if author_mode == WILD AND tier < II:
    then shipability = NONSHIPABLE

rule_wild_may_inspire_never_decide:
  if author_mode == WILD:
    then claim may be used for: search, heuristic guidance, stress testing
    then claim may NOT be used for: law inscription, policy setting, authority claims

rule_heuristics_may_rank_never_rule:
  if claim_kind == heuristic:
    then claim may be used for: Mayor scoring input
    then claim may NOT be used for: kernel constraints, constitutional rules

rule_mayor_may_score_never_seal:
  (enforced in MAYOR_SCORE_VECTOR_V1 schema)
```

---

## 10. Summary: The Ingestion Boundary

**RESEARCH_CLAIM_V1 is the firewall that:**

1. ✅ Prevents legacy material from entering as undifferentiated narrative
2. ✅ Enforces explicit tier classification before any processing
3. ✅ Automatically quarantines speculative/metaphysical material (Tier III)
4. ✅ Requires receipts for Tier I (most rigorous)
5. ✅ Blocks metaphysical language at schema validation
6. ✅ Maintains acyclic dependency graphs
7. ✅ Separates replayability from truth claims
8. ✅ Enforces "no authority from WILD" at the object level

**Result:** Legacy corpus → typed claims → tiered classification → quarantine or promotion path → no direct sovereign entry.

---

**Document Version:** RESEARCH_CLAIM_V1
**Status:** Canonical Law
**Next:** MAYOR_SCORE_VECTOR_V1.md

