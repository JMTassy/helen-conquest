# MAYOR_SCORE_VECTOR_V1

## Making the Mayor Operational Instead of Interpretive

**Purpose:** Define the scoring dimensions, constraints, and output rules for MAYOR_V1 (the governed prioritization oracle). Mayor does not adjudicate truth. Mayor ranks candidates within constitutional bounds and emits receipted verdicts, not beliefs.

**Core Law:**
```
Mayor scores candidate patches, research imports, policy parameters.
Mayor emits rankings, obligations, and receipt requirements.
Mayor does not believe, decide, or seal.
Mayor's output is advice constrained by three contraction axes.
```

---

## 1. Operational Philosophy

**What Mayor Does:**
- Ingests RESEARCH_CLAIM_V1 packets
- Computes normalized score vector Q across 7 dimensions
- Ranks candidates by Lyapunov-style objective ℒ
- Routes candidates to T0–T5 federation review
- Emits MAYOR_VERDICT_V1 (non-sovereign)

**What Mayor Does NOT Do:**
- Emit law
- Claim truth
- Seal artifacts
- Bypass T0–T5 gates
- Create new authority

---

## 2. Score Dimensions

The Mayor score vector is:

```
Q = (Q_det, Q_pol, Q_rep, Q_gnd, Q_sec, Q_opr, Q_fed, Q_cost)

where:
  Q_det  = determinism / replay quality
  Q_pol  = policy integrity / constitutional fit
  Q_rep  = replayability
  Q_gnd  = grounding completeness
  Q_sec  = security relevance
  Q_opr  = operational value
  Q_fed  = federation compatibility
  Q_cost = performance budget cost (enters negatively)
```

---

## 2.1 Q_det (Determinism)

**Definition:**
```
Q_det = (replay_artifact_hash_matches) / (total_replays)
```

**Measurement:**
- Tally: Number of bit-identical replays at governance layer (ℓ=0)
- Normalize: Count / max_count (capped at 1.0)
- Scale: [0, 1]

**Interpretation:**
- 1.0 = All replays identical (perfect determinism)
- 0.8 = 4/5 replays match (minor variance)
- 0.0 = No deterministic behavior

**Required For:**
- Tier II+ claims
- Any claim with `replayability_status == PARTIAL|FULL`

**Non-Required For:**
- Tier III claims (pure heuristic)
- Claims with `claim_kind == heuristic`

---

## 2.2 Q_pol (Policy Integrity)

**Definition:**
```
Q_pol = Σ (axis_contraction_on_axis_i) / n_axes
```

where `axis_contraction_on_axis_i` is measured via GOVERNANCE_TASP_V1.

**Measurement:**

Three independent contraction axes (A, B, C):
- **A:** Replay identity / determinism preserved or improved
- **B:** Authority separation: No leakage of non-sovereign claims into kernel
- **C:** Grounding + schema + receipt completeness maintained

**Scale:**
- 1.0 = All three axes provably contract (improve)
- 0.7 = Two axes contract, one stable
- 0.5 = Two axes stable, one contract
- 0.0 = Any axis expands (worsens)

**Required For:**
- Any claim proposed as policy change
- Any claim that affects governance layer

---

## 2.3 Q_rep (Replayability)

**Definition:**
```
Q_rep = (replayability_status_rank) / 3

where:
  NONE   -> rank 0, Q_rep = 0.0
  PARTIAL -> rank 2, Q_rep = 0.67
  FULL    -> rank 3, Q_rep = 1.0
```

**Measurement:**
- Direct mapping from claim's `replayability_status` field
- No further computation

**Scale:** [0, 1]

**Required For:**
- Tier II+ claims
- All candidates for federation review

---

## 2.4 Q_gnd (Grounding Completeness)

**Definition:**
```
Q_gnd = (receipt_refs_count + evidence_refs_count) / (required_refs_count)

capped at 1.0
```

**Measurement:**
1. Count explicit receipt references (`receipt_refs` field)
2. Count evidence references (`evidence_refs` field)
3. Divide by minimum required (depends on tier and claim_kind)

**Required Count By Tier:**
- Tier I: min 3 receipts + 2 evidence refs
- Tier II: min 1 receipt + 1 evidence ref
- Tier III: 0 required (but 0.0 score)

**Scale:** [0, 1]

**Interpretation:**
- 1.0 = Fully grounded in receipts and evidence
- 0.5 = Partially grounded
- 0.0 = No grounding (pure narrative)

---

## 2.5 Q_sec (Security Relevance)

**Definition:**
```
Q_sec = (threat_model_coverage) / (total_threats)

where threat_model_coverage counts:
  - explicit security analysis present
  - attack vectors identified
  - mitigations proposed or tested
```

**Measurement:**
1. Does the claim have explicit `safety_implications` field? (Yes = 0.5)
2. Are attack vectors listed in dependencies? (Yes = +0.3)
3. Are mitigations documented? (Yes = +0.2)

**Scale:** [0, 1]

**Interpretation:**
- 1.0 = Complete security analysis
- 0.5 = Some safety consideration
- 0.0 = No security thought

**Required For:**
- Cryptographic claims
- Governance claims
- Infrastructure claims

**Not Required For:**
- Pure heuristics (can be 0.0)
- Exploratory conjectures

---

## 2.6 Q_opr (Operational Value)

**Definition:**
```
Q_opr = (operational_value_rank) / 4

where operational_value field maps:
  unknown    -> rank 0, Q_opr = 0.0
  low        -> rank 1, Q_opr = 0.25
  medium     -> rank 2, Q_opr = 0.5
  high       -> rank 3, Q_opr = 0.75
  critical   -> rank 4, Q_opr = 1.0
```

**Measurement:**
- Direct mapping from claim's `operational_value` field
- No further computation

**Scale:** [0, 1]

**Interpretation:**
- 1.0 = Critical operational impact
- 0.5 = Medium operational usefulness
- 0.0 = Unknown or low value

---

## 2.7 Q_fed (Federation Compatibility)

**Definition:**
```
Q_fed = (T_i_compatible_count) / 7

where T_i in {T0, T1, T2, T3, T4, T5, Reducer}
```

**Measurement:**
1. Does claim respect T0 (integrity)? Yes/No
2. Does claim respect T1 (policy)? Yes/No
3. Does claim respect T2 (adapter)? Yes/No
4. Does claim respect T3 (perf)? Yes/No
5. Does claim respect T4 (ux)? Yes/No
6. Does claim respect T5 (adversary)? Yes/No
7. Is claim reducible to determinist verdict? Yes/No

**Scale:** [0, 1]

**Interpretation:**
- 1.0 = Compatible with all servitors
- 0.71 = 5/7 compatible (may need obligations)
- 0.5 = 3-4/7 compatible (significant rework needed)
- 0.0 = Incompatible or untestable

**Computed By:**
- Pre-review: Self-assessment by claim author
- Final: Actual T0–T5 feedback (post-review)

---

## 2.8 Q_cost (Performance Budget)

**Definition:**
```
Q_cost = 1 - (compute_cost / budget)

where compute_cost is measured in:
  - CPU ticks
  - memory footprint
  - network round-trips
  - verification steps
```

**Measurement:**
1. Estimate computational cost to operationalize claim
2. Compare to budget (e.g., 10% of total ledger ops per claim)
3. Normalize: cost / budget
4. Invert: 1 - normalized_cost

**Scale:** [0, 1]

**Interpretation:**
- 1.0 = Negligible cost (free or near-free)
- 0.5 = Moderate cost (moderate budget impact)
- 0.0 = Prohibitive cost (exceeds budget)

**Constraint:**
- If Q_cost < 0.2, claim is automatically flagged for efficiency review
- If Q_cost < 0.0 (exceeds budget), claim cannot be admitted

---

## 3. Lyapunov-Style Objective

The Mayor ranking function is:

```
ℒ(candidate) = w₁Q_det + w₂Q_pol + w₃Q_gnd + w₄Q_rep
              - w₅Q_cost - w₆Q_attack

subject to:
  Q_pol ≥ 0.7 (mandatory minimum on contraction axes)
  Q_cost ≥ 0.0 (cannot exceed budget)
  no claim with auth_mode=WILD enters Tier I (hard constraint)
  all admits must pass T0–T5 (not optional)
```

**Weights (Default):**

| Weight | Value | Dimension | Rationale |
|---|---|---|---|
| w₁ | 0.25 | Q_det | Determinism is foundational |
| w₂ | 0.30 | Q_pol | Policy integrity is critical |
| w₃ | 0.20 | Q_gnd | Grounding is required for shipping |
| w₄ | 0.10 | Q_rep | Replayability enables verification |
| w₅ | 0.10 | Q_cost | Performance matters but secondary |
| w₆ | 0.05 | Q_attack | Security cannot go negative |

**Sum:** w₁ + w₂ + w₃ + w₄ = 0.85 (positive terms)
**Subtract:** w₅ + w₆ = 0.15 (negative terms)

**Constraint Enforcement:**

```python
def mayor_rank(candidate: RESEARCH_CLAIM_V1, weights: dict) -> MAYOR_VERDICT_V1:
    # Compute dimensions
    q_vec = compute_q_vector(candidate)

    # Hard constraints (kill-switches)
    if q_vec.Q_pol < 0.7:
        return MAYOR_VERDICT_V1(
            verdict="QUARANTINE",
            reason="Policy integrity below threshold",
            obligations=["Fix policy violations before re-review"]
        )

    if q_vec.Q_cost < 0.0:
        return MAYOR_VERDICT_V1(
            verdict="REJECT",
            reason="Cost exceeds budget",
            obligations=[]
        )

    if candidate.author_mode == WILD and candidate.tier < II:
        return MAYOR_VERDICT_V1(
            verdict="HOLD",
            reason="WILD claims must reach Tier II before advancement",
            obligations=["Reclassify to Tier II; provide explicit dependencies"]
        )

    # Compute objective
    l_score = (
        weights['w1'] * q_vec.Q_det +
        weights['w2'] * q_vec.Q_pol +
        weights['w3'] * q_vec.Q_gnd +
        weights['w4'] * q_vec.Q_rep -
        weights['w5'] * q_vec.Q_cost -
        weights['w6'] * q_vec.Q_attack
    )

    # Rank and route
    if l_score >= 0.75:
        return MAYOR_VERDICT_V1(verdict="ADVANCE_TO_REVIEW", score=l_score)
    elif l_score >= 0.50:
        return MAYOR_VERDICT_V1(verdict="HOLD_FOR_REWORK", score=l_score,
                                obligations=[...])
    else:
        return MAYOR_VERDICT_V1(verdict="RETURN_TO_RESEARCH", score=l_score)
```

---

## 4. What Mayor May Emit

**Permitted Outputs:**

| Verdict | Meaning | Downstream Action |
|---|---|---|
| ADVANCE_TO_REVIEW | Score ≥ 0.75; ready for T0–T5 | Send to federation |
| HOLD_FOR_REWORK | Score 0.50–0.75; fixable | Return with obligations |
| RETURN_TO_RESEARCH | Score < 0.50; needs rethinking | Archive in RESEARCH_SANDBOX_V1 |
| QUARANTINE | Fails hard constraint | Locked in IDEA_SANDBOX_V1 |
| REJECT | Exceeds budget or contradicts law | Permanent NO_SHIP |

**Output Format (MAYOR_VERDICT_V1):**

```json
{
  "type": "MAYOR_VERDICT_V1",
  "verdict_id": "MV-<claim_id>-<timestamp_hash>",
  "target_claim_id": "rc_...",
  "verdict": "ENUM[ADVANCE_TO_REVIEW, HOLD_FOR_REWORK, RETURN_TO_RESEARCH, QUARANTINE, REJECT]",
  "score_vector": {
    "Q_det": 0.8,
    "Q_pol": 0.85,
    "Q_rep": 0.67,
    "Q_gnd": 0.9,
    "Q_sec": 0.5,
    "Q_opr": 0.75,
    "Q_fed": 0.71,
    "Q_cost": 0.6
  },
  "objective_score": 0.76,
  "reasoning": "Brief explanation of verdict",
  "obligations": ["Fix X", "Provide Y", "..."],
  "required_receipt_types": ["RCP-FEDREVIEW-T0-T5"],
  "next_gate": "T0_INTEGRITY_CHECK",
  "timestamp": "2026-03-08T...",
  "mayor_signature": "ed25519_signature"
}
```

---

## 5. What Mayor Is Forbidden to Emit

**FORBIDDEN:**

1. ❌ **Belief statements**
   - ❌ "This is true because..."
   - ❌ "The universe suggests..."
   - ✅ "Score is 0.8 on policy integrity axis"

2. ❌ **Law or doctrine**
   - ❌ "We should enact this as a constitutional rule"
   - ✅ "Routing to T0–T5 for policy compatibility review"

3. ❌ **Assertions without scoring**
   - ❌ "This is the right choice"
   - ✅ "ℒ-score is 0.72; routed to HOLD_FOR_REWORK"

4. ❌ **Authority claims**
   - ❌ "I have decided this is admissible"
   - ✅ "Score meets threshold for federation review"

5. ❌ **Bypassing gates**
   - ❌ Direct routing to ledger or kernel
   - ✅ Always routes to T0–T5 first

6. ❌ **Confidence claims**
   - ❌ "Very high confidence in this path"
   - ✅ "Q_fed = 0.85 (5/7 servitors compatible)"

---

## 6. Monotone-Safety Constraints

Mayor's ranking must preserve **three independent contraction axes** (from GOVERNANCE_TASP_V1):

### 6.1 Axis A: Replay Identity

**Contraction Requirement:**
```
If candidate is promoted:
  then replay_fidelity_post >= replay_fidelity_pre

i.e., determinism cannot degrade
```

**Enforcement:**
```python
if Q_det_new < Q_det_baseline:
    return MAYOR_VERDICT_V1(
        verdict="QUARANTINE",
        reason="Determinism degradation detected"
    )
```

---

### 6.2 Axis B: Authority Separation

**Contraction Requirement:**
```
If candidate is promoted:
  then authority_leakage_post <= authority_leakage_pre

i.e., non-sovereign claims cannot enter kernel decisions
```

**Enforcement:**
```python
if "kernel_decision" in candidate.proposed_operational_use:
    if candidate.receipt_status < FULL:
        return MAYOR_VERDICT_V1(
            verdict="QUARANTINE",
            reason="Cannot use unreceipted claims for kernel decisions"
        )
```

---

### 6.3 Axis C: Grounding & Receipts

**Contraction Requirement:**
```
If candidate is promoted:
  then grounding_completeness_post >= grounding_completeness_pre

i.e., evidence quality cannot decrease
```

**Enforcement:**
```python
if Q_gnd_new < Q_gnd_baseline:
    return MAYOR_VERDICT_V1(
        verdict="RETURN_TO_RESEARCH",
        reason="Grounding must improve or stay same; cannot degrade"
    )
```

---

## 7. Federation Review Gate

After Mayor scores a candidate as ADVANCE_TO_REVIEW, the claim enters T0–T5 federation review:

```
Mayor: ADVANCE_TO_REVIEW → T0 Integrity Check
                          → T1 Policy Compatibility
                          → T2 Adapter Integration
                          → T3 Performance Budget
                          → T4 UX/Operability
                          → T5 Adversary Robustness
```

**Mayor's Role:**
- Submits: `MAYOR_CANDIDATE_PACKET_V1` with score_vector
- Receives: `RESEARCH_EVAL_RECEIPT_V1` per servitor
- Does not participate in T0–T5 deliberation

**Result:**
- If all T_i pass: Reducer considers claim for ℒ-admission
- If any T_i fails: Claim returns to Mayor or research sandbox

---

## 8. Obligation Assignment

When Mayor emits HOLD_FOR_REWORK, it assigns specific obligations:

```json
{
  "obligations": [
    {
      "obligation_id": "OBL-001",
      "description": "Provide explicit replay command with expected output hash",
      "target_field": "replay_command, replay_artifact_hash",
      "severity": "critical"
    },
    {
      "obligation_id": "OBL-002",
      "description": "Resolve circular dependency between rc_A and rc_B",
      "target_field": "dependency_claim_ids",
      "severity": "critical"
    },
    {
      "obligation_id": "OBL-003",
      "description": "Add security analysis for cryptographic primitives",
      "target_field": "safety_implications",
      "severity": "high"
    }
  ],
  "rework_deadline": "2026-03-15T23:59:59Z"
}
```

**Obligation Types:**

| Type | Impact | Example |
|---|---|---|
| critical | Blocks advancement; must fix | Provide replay command |
| high | Strongly recommended | Add security analysis |
| medium | Improves score | Clarify dependencies |
| low | Optional enhancement | Better wording |

---

## 9. Score Transparency

Mayor must emit all scores explicitly (no hidden computation):

```json
{
  "score_vector": {
    "Q_det": 0.8,
    "Q_pol": 0.85,
    "Q_rep": 0.67,
    "Q_gnd": 0.9,
    "Q_sec": 0.5,
    "Q_opr": 0.75,
    "Q_fed": 0.71,
    "Q_cost": 0.6
  },
  "score_computation": {
    "Q_det_rationale": "4/5 replays matched; one outlier in ticks 42-50",
    "Q_pol_rationale": "All three TASP axes contract; no authority leakage detected",
    "Q_rep_rationale": "replayability_status=PARTIAL maps to 0.67",
    "Q_gnd_rationale": "2 receipts + 3 evidence refs; Tier II requires 1+1, so 5/2=2.5 capped at 1.0",
    "Q_sec_rationale": "Safety implications present (0.5) + no attack vectors listed (-0.0)",
    "Q_opr_rationale": "operational_value=high maps to 0.75",
    "Q_fed_rationale": "T0,T1,T2,T3,T4 compatible; T5 pending = 5/7 = 0.71",
    "Q_cost_rationale": "Est. cost = 60% of budget; 1 - 0.6 = 0.4 (minor issue)"
  },
  "objective_score_computation": "ℒ = 0.25*0.8 + 0.30*0.85 + 0.20*0.9 + 0.10*0.67 - 0.10*0.4 - 0.05*0.5 = 0.76"
}
```

---

## 10. Non-Negotiable Laws (Carved Into Score)

```
law_no_receipt_no_claim:
  if receipt_status == NONE:
    then Q_gnd = 0.0 (failing score)

law_no_replay_no_admission:
  if replayability_status == NONE AND tier < III:
    then Q_rep = 0.0 (must promote to Tier III or provide replay)

law_no_tier_no_processing:
  if tier not assigned:
    then verdict = QUARANTINE (cannot score untiered claims)

law_no_authority_separation_no_ship:
  if author_mode == WILD AND tier < II:
    then verdict = HOLD (must reach Tier II first)

law_mayor_never_seals:
  verdict in [ADVANCE_TO_REVIEW, HOLD_FOR_REWORK, RETURN_TO_RESEARCH, QUARANTINE, REJECT]
  verdict NOT in [SEAL, LAW_INSCRIPTION, FINAL_DECISION, APPROVED]
```

---

## 11. Example: Scoring a Tier II Crypto Claim

**Input Claim:**
```json
{
  "claim_id": "rc_cryptography_hash_001_f2e4d9c",
  "tier": "II",
  "claim_kind": "protocol",
  "statement": "SHA-256 variant with added whitening layer reduces collision probability in 128-bit output",
  "evidence_status": "PARTIAL",
  "replayability_status": "FULL",
  "receipt_status": "PARTIAL",
  "author_mode": "FORMAL",
  "proposed_operational_use": "crypto_primitive",
  "operational_value": "high",
  "dependency_claim_ids": ["rc_cryptography_sha256_001", "rc_randomness_whitening"],
  "safety_implications": "Variant untested against modern attacks; requires NIST-style analysis"
}
```

**Mayor Scoring:**

| Dimension | Computation | Result |
|---|---|---|
| Q_det | 1/1 replays matched | 1.0 |
| Q_pol | TASP: A=stable, B=contract, C=contract (2/3) | 0.67 |
| Q_rep | FULL maps to rank 3/3 | 1.0 |
| Q_gnd | 1 receipt + 2 evidence refs; Tier II requires 1+1; 3/2=1.5 capped | 1.0 |
| Q_sec | safety_implications present (0.5) + attack vectors needed (+0.0) | 0.5 |
| Q_opr | high → rank 3/4 | 0.75 |
| Q_fed | T0,T1,T3,T4 estimated compat; T2,T5 unknown (4/7) | 0.57 |
| Q_cost | Estimated low cost (0.9) | 0.9 |

**Objective:**
```
ℒ = 0.25*1.0 + 0.30*0.67 + 0.20*1.0 + 0.10*1.0
  - 0.10*0.1 - 0.05*0.5
  = 0.25 + 0.20 + 0.20 + 0.10 - 0.01 - 0.025
  = 0.724
```

**Verdict:**
```json
{
  "verdict": "HOLD_FOR_REWORK",
  "objective_score": 0.724,
  "reasoning": "Score near decision boundary; Q_pol below 0.7 due to TASP Axis C incomplete. Q_sec needs cryptographic threat analysis.",
  "obligations": [
    {
      "obligation_id": "OBL-CRYPTO-001",
      "description": "Provide formal collision-probability analysis against modern attacks",
      "severity": "critical"
    },
    {
      "obligation_id": "OBL-CRYPTO-002",
      "description": "Clarify whitening layer design; current description too abstract",
      "severity": "high"
    }
  ]
}
```

---

## 12. Summary: Mayor as Operational Oracle

**MAYOR_SCORE_VECTOR_V1 guarantees:**

1. ✅ All scores are transparent and reproducible
2. ✅ Mayor never believes, claims authority, or seals
3. ✅ Mayor ranks candidates by multi-dimensional safety
4. ✅ Hard constraints (Q_pol ≥ 0.7, Q_cost ≥ 0.0) are enforced
5. ✅ Obligations are explicit and actionable
6. ✅ All admitted claims pass T0–T5 before reducer
7. ✅ Three contraction axes are preserved monotonically

**Result:** Mayor becomes a deterministic scoring function, not a philosopher.

---

**Document Version:** MAYOR_SCORE_VECTOR_V1
**Status:** Canonical Law
**Next:** GOVERNANCE_TASP_V1.md

