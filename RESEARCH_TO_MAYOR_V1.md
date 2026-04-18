# RESEARCH_TO_MAYOR_V1

## The Bridge: From Legacy Corpus to Governed Reduction

**Purpose:** Define the complete end-to-end path for speculative mathematical, cryptographic, and theoretical research entering HELEN OS as non-sovereign input and potentially exiting as governed contribution to kingdom decisions.

**Core Metaphor:**
```
Upstream: Exploratory creativity (WILD, RESEARCH)
→ Midstream: Constitutional filtration (TIER classification, QUARANTINE, MAYOR scoring)
→ Downstream: Deterministic reduction (T0–T5 review, reducer verdict)

Or more sharply:
Old corpus = input pressure
HELEN/TOWN = constitutional filtration
```

---

## 1. The Problem RESEARCH_TO_MAYOR_V1 Solves

**What could go wrong without this bridge:**

1. ❌ Legacy material enters as undifferentiated narrative
   - Risk: Heuristic masquerades as law
   - Mitigation: RESEARCH_CLAIM_V1 enforces typing + tiering

2. ❌ Speculative research bypasses governance gates
   - Risk: WILD claims influence kernel directly
   - Mitigation: T0–T5 federation review is mandatory

3. ❌ Mayor acts as philosopher instead of scorer
   - Risk: Verdicts are opaque beliefs, not reproducible scores
   - Mitigation: MAYOR_SCORE_VECTOR_V1 enforces transparency

4. ❌ Governance admits claims that degrade evidence or determinism
   - Risk: System becomes less trustworthy over time
   - Mitigation: GOVERNANCE_TASP_V1 enforces three-axis contraction

5. ❌ Non-sovereign layer authority leaks into kernel
   - Risk: Unreceipted claims become law
   - Mitigation: Authority separation is structurally enforced

**RESEARCH_TO_MAYOR_V1 as Solution:**
Formalize every step so no legacy material escapes classification, and no unvetted claim reaches the kernel.

---

## 2. The Canonical Flow

```
Legacy Corpus
    ↓
[INGESTION] Import as RESEARCH_CLAIM_V1
    ↓
[TIER CLASSIFICATION]
    ├─ Tier I: Receipt-backed, replayable, schema-valid
    ├─ Tier II: Structured, explicit dependencies, falsifiable
    └─ Tier III: Speculative, metaphysical → auto-QUARANTINE
    ↓
[TRIAGE]
    ├─ WILD mode → IDEA_SANDBOX_V1 (never ships)
    ├─ RESEARCH mode → claim-graph linkage + Mayor scoring
    └─ FORMAL mode → receipt validation + policy check
    ↓
[GOVERNANCE_TASP_V1 GATE] (three-axis contraction)
    ├─ All axes contract → ADVANCE
    └─ Any axis expands → QUARANTINE
    ↓
[MAYOR SCORING] (MAYOR_SCORE_VECTOR_V1)
    ├─ Score >= 0.75 → ADVANCE_TO_REVIEW
    ├─ Score 0.50–0.75 → HOLD_FOR_REWORK
    └─ Score < 0.50 → RETURN_TO_RESEARCH
    ↓
[T0–T5 FEDERATION REVIEW] (mandatory for Tier I/II)
    ├─ T0: Integrity check
    ├─ T1: Policy compatibility
    ├─ T2: Adapter integration
    ├─ T3: Performance budget
    ├─ T4: UX/Operability
    └─ T5: Adversary robustness
    ↓
[DETERMINISTIC REDUCER]
    ├─ All T0–T5 PASS → QUEST_RESULT (accepted)
    ├─ T0–T5 HOLD (bounded) → HOLD with obligations
    └─ Any T0–T5 FAIL → NO_SHIP
    ↓
[FINAL VERDICTS]
    ├─ QUEST_RESULT: Task accepted for execution
    ├─ LAW_INSCRIPTION: Invariant accepted for ledger
    └─ NO_SHIP: Claim rejected, returned to research

```

---

## 3. Tier Mapping at Ingestion

**Every claim must be classified immediately.**

| Tier | Requirements | Endpoint | Usage |
|---|---|---|---|
| **I** | Receipt-backed, replayable, schema-valid, receipt_status=FULL | Federation + Reducer | Can influence kernel (post-review) |
| **II** | Structured, dependencies explicit, falsifiable, receipt_status>=PARTIAL | Federation + Reducer | Can influence domain reasoning (post-review) |
| **III** | Speculative, ungrounded, metaphysical, quarantined by default | IDEA_SANDBOX_V1 (quarantine) | Pressure-test only (never ships) |

**Automatic Quarantine Triggers → Tier III:**
1. ❌ Ungrounded metaphysical language ("governs the nature of...")
2. ❌ No measurable predicates (unfalsifiable)
3. ❌ Circular dependencies
4. ❌ No replay command (Tier III only)
5. ❌ Proposes kernel changes by analogy alone

**Result:** 80%+ of legacy corpus typically enters Tier III automatically.

---

## 4. RESEARCH_CLAIM_V1 Ingestion

**Step 1: Classify the Incoming Material**

```bash
# Example: Legacy prime gap heuristic
claim_id = "rc_prime_number_001_a2f3b7e"
claim_kind = "heuristic"
tier = "III"  # Default: metaphysical framing
source_domain = "prime_number_theory"
author_mode = "WILD"

quarantine_reason_codes = ["UNGROUNDED_METAPHYSICS", "NO_REPLAY"]
quarantine_status = "ACTIVE"
shipability = "NONSHIPABLE"
```

**Step 2: Emit RESEARCH_CLAIM_V1 Object**

(See RESEARCH_CLAIM_V1.md for full schema)

**Step 3: Route**
- Tier III → IDEA_SANDBOX_V1 (quarantine)
- Tier II/I → GOVERNANCE_TASP_V1 gate → Mayor scoring

---

## 5. GOVERNANCE_TASP_V1 Gate (Three-Axis Contraction)

**Check 1: Does the claim preserve Axis A (Determinism)?**

```python
det_before = measure_governance_determinism()  # baseline
det_after = measure_with_claim_added()        # tentative

if det_after >= det_before:
    axis_a_status = "CONTRACTS"  ✅
else:
    axis_a_status = "EXPANDS"    ❌ → QUARANTINE
```

**Check 2: Does the claim preserve Axis B (Authority Separation)?**

```python
auth_leakage_before = count_unreceipted_in_kernel()
auth_leakage_after = count_with_claim_added()

if auth_leakage_after <= auth_leakage_before:
    axis_b_status = "CONTRACTS"  ✅
else:
    axis_b_status = "EXPANDS"    ❌ → QUARANTINE
```

**Check 3: Does the claim preserve Axis C (Grounding)?**

```python
gnd_before = measure_evidence_completeness()
gnd_after = measure_with_claim_added()

if gnd_after >= gnd_before:
    axis_c_status = "CONTRACTS"  ✅
else:
    axis_c_status = "EXPANDS"    ❌ → QUARANTINE
```

**TASP Verdict:**
```
if axis_a and axis_b and axis_c:
    verdict = "GOVERNANCE_CONSISTENT"  ✅ → ADVANCE
else:
    verdict = "GOVERNANCE_INCONSISTENT"  ❌ → QUARANTINE
```

---

## 6. Mayor Scoring (MAYOR_SCORE_VECTOR_V1)

**Input:** RESEARCH_CLAIM_V1 + claim-graph decomposition

**Output:** MAYOR_VERDICT_V1 with ranked recommendation

### 6.1 Score Dimensions

```
Q = (Q_det, Q_pol, Q_rep, Q_gnd, Q_sec, Q_opr, Q_fed, Q_cost)

ℒ = w₁Q_det + w₂Q_pol + w₃Q_gnd + w₄Q_rep - w₅Q_cost - w₆Q_attack
```

### 6.2 Verdict Routing

```
if Q_pol < 0.7:
    return QUARANTINE ("Policy integrity below threshold")

if Q_cost < 0.0:
    return REJECT ("Exceeds budget")

if author_mode == WILD and tier < II:
    return HOLD ("WILD claims must reach Tier II first")

if ℒ >= 0.75:
    return ADVANCE_TO_REVIEW (route to T0–T5)

elif ℒ >= 0.50:
    return HOLD_FOR_REWORK (return with obligations)

else:
    return RETURN_TO_RESEARCH (archive)
```

---

## 7. T0–T5 Federation Review

**Mandatory for all Tier II/I claims routed to ADVANCE_TO_REVIEW.**

### 7.1 Review Order

```
Claim → T0 Integrity Check
     → T1 Policy Compatibility
     → T2 Adapter Integration
     → T3 Performance Budget
     → T4 UX / Operability
     → T5 Adversary Robustness
     → Reducer (final verdict)
```

### 7.2 Servitor Outputs

Each T_i emits:

```json
{
  "type": "RESEARCH_EVAL_RECEIPT_V1",
  "servitor": "T0|T1|T2|T3|T4|T5",
  "target_claim_id": "rc_...",
  "verdict": "PASS|HOLD|FAIL",
  "findings": ["...", "..."],
  "obligations": ["If HOLD: what must be fixed"],
  "signature": "ed25519_signature"
}
```

### 7.3 Aggregation

```
if all(T_i verdict == PASS for T_i in [T0..T5]):
    reducer_status = "ALL_PASS"   → reducer may emit QUEST_RESULT

elif all(T_i verdict in [PASS, HOLD] for T_i in [T0..T5]):
    reducer_status = "BOUNDED_HOLD"   → reducer may emit HOLD with aggregated obligations

else:
    reducer_status = "FAIL"   → reducer emits NO_SHIP
```

---

## 8. Deterministic Reducer (Final Authority)

**Only source of truth: the reducer.**

### 8.1 Reducer Inputs

```json
{
  "claim_id": "rc_...",
  "claim_graph": {...},
  "mayor_score_vector": {...},
  "federation_receipts": [
    "RCP-FEDREVIEW-T0-...",
    "RCP-FEDREVIEW-T1-...",
    "...",
    "RCP-FEDREVIEW-T5-..."
  ],
  "replay_bundle": {
    "replay_command": "...",
    "replay_artifact_hash": "..."
  }
}
```

### 8.2 Reducer Logic

```python
def reduce_claim(claim_packet: MAYOR_CANDIDATE_PACKET_V1) -> REDUCER_VERDICT_V1:
    """
    Deterministic reduction: no randomness, no philosophy.
    """

    # Verify all receipts present and signed
    if not all_receipts_valid(claim_packet.federation_receipts):
        return REDUCER_VERDICT_V1(verdict="NO_SHIP", reason="Receipt validation failed")

    # Check TASP gate one more time
    if not governance_tasp_check(...):
        return REDUCER_VERDICT_V1(verdict="NO_SHIP", reason="TASP gate failed")

    # Extract federation outcomes
    federation_verdicts = [r.verdict for r in claim_packet.federation_receipts]

    if all(v == "PASS" for v in federation_verdicts):
        # All servitors passed
        return REDUCER_VERDICT_V1(
            verdict="QUEST_RESULT",
            result_type="ACCEPT_FOR_EXECUTION",
            receipt_id="RCP-REDUCER-QUEST-..."
        )

    elif all(v in ["PASS", "HOLD"] for v in federation_verdicts):
        # Some holds; extract obligations
        obligations = extract_obligations(claim_packet.federation_receipts)
        return REDUCER_VERDICT_V1(
            verdict="HOLD",
            result_type="ACCEPT_WITH_OBLIGATIONS",
            obligations=obligations,
            receipt_id="RCP-REDUCER-HOLD-..."
        )

    else:
        # Any fail → NO_SHIP
        return REDUCER_VERDICT_V1(
            verdict="NO_SHIP",
            reason="Federation review produced failures",
            receipt_id="RCP-REDUCER-NOSHIP-..."
        )
```

### 8.3 Reducer Outputs

| Verdict | Meaning | Action |
|---|---|---|
| QUEST_RESULT | Claim accepted; emit task | Write to ledger + mark for execution |
| LAW_INSCRIPTION | Claim accepted; emit invariant | Write to ledger + install as policy |
| HOLD | Claim accepted with obligations | Add to ledger + return to author with required fixes |
| NO_SHIP | Claim rejected | Return to research sandbox (no ledger write) |

---

## 9. Hard Prohibitions (Governing Laws)

These are enforced at every stage:

```
rule_1_no_receipt_no_claim:
  if receipt_status == NONE:
    then shipability = NONSHIPABLE (always)

rule_2_no_replay_no_admission:
  if replayability_status == NONE:
    then max_tier = III (unreceipted material cannot reach kernel)

rule_3_no_tier_no_processing:
  if tier not in [I, II, III]:
    then claim is invalid (rejected at schema)

rule_4_no_authority_separation_no_ship:
  if author_mode == WILD:
    then max_endpoints = [RESEARCH_SANDBOX, IDEA_SANDBOX] (never kernel)

rule_5_wild_may_inspire_never_decide:
  if author_mode == WILD:
    then may_use_for = [search, heuristic, stress_test]
    then cannot_use_for = [law, policy, authority]

rule_6_heuristics_may_rank_never_rule:
  if claim_kind == heuristic:
    then may_use_for = [Mayor_scoring_input]
    then cannot_use_for = [kernel_constraint, constitutional_rule]

rule_7_mayor_may_score_never_seal:
  if verdict_type in [ADVANCE, HOLD, RETURN, QUARANTINE, REJECT]:
    then verdict_type NOT in [SEAL, LAW, FINAL_DECISION, APPROVED]

rule_8_tasp_proves_admissibility_not_truth:
  (TASP_gate_pass) ≠> (claim_is_true_in_domain)
  (TASP_gate_pass) => (governance_consistent_with_model)

rule_9_t0t5_not_optional:
  if tier in [I, II]:
    then federation_review = mandatory
    then no_bypass = true

rule_10_reducer_is_final_authority:
  only_reducer_may_emit = [QUEST_RESULT, LAW_INSCRIPTION]
  only_reducer_may_write = [ledger]
  bypass_reducer = impossible
```

---

## 10. Lifecycle Example: Prime Gap Conjecture

### 10.1 Import (Legacy Corpus)

```
"Prime gaps grow logarithmically with prime size, suggesting
self-organized criticality in number-theoretic structures."
```

### 10.2 Ingestion → RESEARCH_CLAIM_V1

```json
{
  "claim_id": "rc_prime_001_a2f3b7e",
  "tier": "III",
  "statement": "Prime gaps G_n appear to exhibit log² scaling; candidate mechanism: self-organized criticality",
  "claim_kind": "heuristic",
  "author_mode": "WILD",
  "quarantine_status": "ACTIVE",
  "shipability": "NONSHIPABLE"
}
```

**Reason for Tier III:**
- "Self-organized criticality" is metaphysical framing (no causal evidence)
- No replay command
- No explicit measurement predicates

**Result:** Forced to IDEA_SANDBOX_V1 (quarantine).

### 10.3 Reclassification (Researcher Intervention)

Author rewrites to Tier II:

```json
{
  "claim_id": "rc_prime_001_a2f3b7e",
  "tier": "II",
  "statement": "Empirical data shows G_n < log²(p_n) for primes up to 10⁹; candidate model: random variable with density-dependent parameter",
  "evidence_refs": ["Cramer1936", "Titchmarsh1951", "TitchmarshBook"],
  "evidence_status": "PARTIAL",
  "replayability_status": "PARTIAL",
  "replay_command": "python3 gap_analysis.py 1000000 --heuristic_model",
  "dependency_claim_ids": ["rc_random_matrix_001", "rc_spectral_001"]
}
```

**Changes:**
- Removed metaphysical framing
- Added specific empirical bounds
- Provided replay command
- Linked dependencies

**Result:** RELEASED from quarantine; eligible for Mayor scoring.

### 10.4 GOVERNANCE_TASP_V1 Gate

```
Axis A (Determinism):
  Same data input → same heuristic output
  → CONTRACTS ✅

Axis B (Authority):
  Heuristic is non-sovereign; not used for kernel
  → CONTRACTS ✅

Axis C (Grounding):
  Receipts: 1 (from reclassification)
  Evidence: 3 citations
  → CONTRACTS ✅

Verdict: GOVERNANCE_CONSISTENT → ADVANCE to Mayor
```

### 10.5 Mayor Scoring

```
Q_det = 0.8  (deterministic heuristic)
Q_pol = 0.75 (policy compliant)
Q_rep = 0.67 (PARTIAL replayability)
Q_gnd = 0.75 (partial grounding)
Q_sec = 0.0  (not cryptographic)
Q_opr = 0.5  (medium value)
Q_fed = 0.57 (needs adapter work)
Q_cost = 0.9

ℒ = 0.25*0.8 + 0.30*0.75 + 0.20*0.75 + 0.10*0.67 - 0.10*0.1 - 0.05*0.5
  = 0.20 + 0.225 + 0.15 + 0.067 - 0.01 - 0.025
  = 0.607

Verdict: HOLD_FOR_REWORK (score 0.607 in 0.50–0.75 range)
```

**Obligations:**
1. Provide full replay command with expected output hash
2. Clarify random variable model: what is the parameter?
3. Add explicit dependency on Cramer's conjecture (if applicable)

### 10.6 Author Rework

Author provides:
- Full replay script with expected hash
- Formal specification of random model
- Clarified dependencies

→ Re-scores to 0.72 (now in HOLD range, closer to ADVANCE)

### 10.7 Federation Review (Optional)

If author refines further, claim might score >= 0.75 → ADVANCE_TO_REVIEW:

```
T0 Integrity: ✅ PASS (claim structure sound)
T1 Policy: ✅ PASS (compliant with governance law)
T2 Adapter: 🟡 HOLD (needs integration work)
T3 Performance: ✅ PASS (low computational cost)
T4 UX: ✅ PASS (clear description)
T5 Adversary: ✅ PASS (no security risk)
```

**Result:** Bounded holds on T2 only; resolver may emit HOLD with obligations.

### 10.8 Reducer Verdict

```json
{
  "verdict": "HOLD",
  "reason": "T2 Adapter requires integration work; all other servitors pass",
  "obligations": ["Implement adapter interface per T2 spec"],
  "receipt_id": "RCP-REDUCER-HOLD-rc_prime_001",
  "next_step": "Return to author for T2 work; re-route when complete"
}
```

**Result:** Claim is not shipped yet, but path is clear.

### 10.9 Final State

If author completes T2 work and re-submits:

```
All T0–T5 PASS → Reducer emits QUEST_RESULT

Output options:
  A) QUEST_RESULT: "Implement heuristic as search metric in CONQUEST games"
  B) LAW_INSCRIPTION: "Add heuristic as standard output metric in all future simulations"
```

**Result:** Claim enters ledger with receipt; no longer speculative.

---

## 11. The Three Non-Negotiable Outcomes

Every claim eventually reaches one of three fates:

### 11.1 NO_SHIP

**Claim is rejected and archived.**

```json
{
  "verdict": "NO_SHIP",
  "claim_id": "rc_...",
  "reasons": [
    "TASP gate failure: Axis B would leak authority",
    "Federation review: T5 (adversary) raised fatal security concerns"
  ],
  "archive_location": "RESEARCH_SANDBOX_V1",
  "receipt_id": "RCP-FINAL-NOSHIP-..."
}
```

- Claim never enters ledger
- Returned to research corpus for future work
- No authority claim asserted

### 11.2 HOLD

**Claim is accepted conditionally; must fix obligations.**

```json
{
  "verdict": "HOLD",
  "claim_id": "rc_...",
  "obligations": [
    {"id": "OBL-001", "description": "Fix T2 adapter integration", "deadline": "2026-03-20"}
  ],
  "receipt_id": "RCP-FINAL-HOLD-...",
  "next_action": "Return to author; re-submit when obligations complete"
}
```

- Claim enters ledger as PENDING
- Cannot influence kernel yet
- Author has clear path forward

### 11.3 QUEST_RESULT or LAW_INSCRIPTION

**Claim is accepted and shipped.**

```json
{
  "verdict": "QUEST_RESULT",
  "claim_id": "rc_...",
  "result_type": "ACCEPT_FOR_EXECUTION",
  "task_id": "QUEST-PRIME-GAP-HEURISTIC-001",
  "description": "Use prime gap heuristic as search guidance in CONQUEST domain",
  "receipt_id": "RCP-FINAL-QUEST-...",
  "ledger_entry_hash": "...",
  "effective_date": "2026-03-09T00:00:00Z"
}
```

- Claim written to ledger
- Becomes part of operational governance
- Falsifiable and monitored

---

## 12. The Bridge in One Diagram

```
LEGACY CORPUS (Narrative, Metaphysical, Untyped)
        |
        | Ingestion: RESEARCH_CLAIM_V1
        ↓
CLASSIFIED & TIERED (Explicit, Typed, Measurable)
        |
        ├─ Tier III → IDEA_SANDBOX_V1 [WILD pressure-test only]
        |
        ├─ Tier II, I → GOVERNANCE_TASP_V1 Gate
        |             [Axis A, B, C contraction check]
        ↓
GOVERNANCE-CONSISTENT (Determinism maintained, Authority sealed, Grounding strong)
        |
        | Mayor Scoring: MAYOR_SCORE_VECTOR_V1
        | [8-dimensional ranking]
        ↓
        ├─ Score < 0.50 → RETURN_TO_RESEARCH
        |
        ├─ Score 0.50–0.75 → HOLD_FOR_REWORK
        |
        └─ Score >= 0.75 → ADVANCE_TO_REVIEW
                            |
                            | Federation: T0–T5 Review
                            | [Integrity, Policy, Adapter, Perf, UX, Adversary]
                            ↓
                       DETERMINISTIC REDUCER
                            |
                            ├─ All PASS → QUEST_RESULT [SHIP]
                            ├─ Bounded HOLD → HOLD [with obligations]
                            └─ Any FAIL → NO_SHIP [archive]
```

---

## 13. Success Criteria

RESEARCH_TO_MAYOR_V1 is successful when:

1. ✅ **No legacy material enters kernel untyped**
   - Every claim classified by tier at ingestion
   - Automatic quarantine for WILD/metaphysical

2. ✅ **Speculation stays speculative**
   - Tier III = pressure-test only (IDEA_SANDBOX_V1)
   - No influence on kernel without promotion to Tier II+

3. ✅ **Mayor is transparent, not opaque**
   - All scores published with rationale
   - Deterministic routing (no subjective calls)

4. ✅ **TASP enforces constitutional law**
   - All three axes verified before admission
   - No claim degrades determinism, authority separation, or grounding

5. ✅ **Federation review is mandatory**
   - All Tier II/I claims pass T0–T5
   - No bypass to reducer possible

6. ✅ **Reducer is final and deterministic**
   - Only source of truth for QUEST_RESULT / LAW_INSCRIPTION
   - No override possible

---

## 14. Summary: The Firewall

**RESEARCH_TO_MAYOR_V1 is the firewall that:**

1. **Classifies** — RESEARCH_CLAIM_V1 enforces typing
2. **Filters** — GOVERNANCE_TASP_V1 enforces three-axis contraction
3. **Ranks** — MAYOR_SCORE_VECTOR_V1 enforces transparent scoring
4. **Reviews** — T0–T5 federation enforces multidimensional scrutiny
5. **Reduces** — Deterministic reducer enforces final authority

**Result:** Legacy corpus → creative input, never doctrine.

---

**Document Version:** RESEARCH_TO_MAYOR_V1
**Status:** Canonical Law — Bridge Complete
**Related Documents:**
- RESEARCH_CLAIM_V1.md (Ingestion boundary)
- MAYOR_SCORE_VECTOR_V1.md (Transparent scoring)
- GOVERNANCE_TASP_V1.md (Three-axis contraction)

