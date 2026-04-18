# ORACLE 2: BUILDERS — Canonical Specification
**Version:** 2.0-FINAL
**Status:** LOCKED FOR SHIPPING

---

## SECTION 0: THE FRAME (NON-NEGOTIABLE)

### Core Principle

**ORACLE 1 = Judge. ORACLE 2 = Mechanic.**

ORACLE 2 (Builders) takes NO_SHIP verdicts and produces **strictly weaker, testable V2 proposals**.

**Builders never decides truth. It only prepares admissible artifacts.**

---

## SECTION 1: MVP WEDGE (ONE SENTENCE)

> **ORACLE 2 takes a NO_SHIP verdict and outputs a strictly weaker, testable V2 proposal.**

Everything else is implementation detail.

---

## SECTION 2: INPUT CONTRACT (LOCKED)

ORACLE 2 MUST ACCEPT ONLY THIS INPUT:

```typescript
{
  "original_claim": Claim,
  "verdict": {
    "decision": "NO_SHIP",
    "blocking": BlockingObligationV1[]
  }
}
```

**Hard Rule:** If `verdict.decision == "SHIP"` → ORACLE 2 does nothing.

This prevents:
- Overreach
- Builder-led acceptance
- Incentive corruption

---

## SECTION 3: OUTPUT CONTRACT (LOCKED)

ORACLE 2 OUTPUTS EXACTLY ONE THING:

```typescript
{
  "v2_proposal": {
    "tier_a": null,                    // ALWAYS null (no Tier I claims)
    "tier_b": TierBProposal | null,    // Measurable downgrade
    "tier_c": TierCProposal | null,    // Narrative downgrade
    "delta_log": DeltaEntry[],         // What changed from V1
    "acceptance_gates": Gate[],        // All must be false initially
    "ship_score": number,              // Remaining blockers count
    "disclaimer": string               // Required explicit disclaimer
  }
}
```

**Hard Rules:**
- `tier_a` is ALWAYS `null` (no Tier I/A claims allowed)
- `tier_b` = measurable, testable downgrade
- `tier_c` = narrative, qualitative downgrade
- Explicit disclaimer REQUIRED
- All `acceptance_gates` start with `pass_fail: false`

---

## SECTION 4: MONOTONIC WEAKENING LAW (CORE INVARIANT)

Every remediation MUST satisfy:

```
scope(V2) ⊂ scope(V1)
strength(V2) ≤ strength(V1)
tier(V2) ∈ {B, C}  // Never A/I
```

**If this fails → remediation is rejected.**

This single rule prevents:
- Claim laundering
- Rhetorical inflation
- Builder drift

---

## SECTION 5: BLOCKING OBLIGATION SCHEMA (LOCKED)

### 5.1 TypeScript Definition

```typescript
export type ObligationStatus = "OPEN" | "SATISFIED" | "WAIVED" | "INVALID";

export type ObligationType =
  | "BASELINE_REQUIRED"
  | "INSTRUMENTATION_INTEGRITY"
  | "ATTESTATION_REQUIRED"
  | "SECURITY_REVIEW"
  | "LEGAL_REVIEW"
  | "PRIVACY_REVIEW"
  | "REPRODUCIBILITY_REQUIRED"
  | "OTHER";

export type ObligationSeverity = "HARD" | "SOFT";

export type ExpectedAttestor =
  | "METRIC_SNAPSHOT"
  | "TOOL_RESULT"
  | "CODE_PROOF"
  | "AUDITOR_REPORT"
  | "LEGAL_DOC"
  | "PRIVACY_DOC"
  | "HUMAN_REVIEW"
  | "NONE";

export type ReasonCode =
  | "NO_RECEIPT"
  | "MISSING_BASELINE"
  | "MISSING_INSTRUMENTATION"
  | "MISSING_ATTESTATION"
  | "UNVERIFIABLE"
  | "OVERSCOPED"
  | "LEGAL_RISK"
  | "PRIVACY_RISK"
  | "SECURITY_RISK"
  | "NON_DETERMINISTIC";

export interface BlockingObligationV1 {
  // Determinism controls
  canon_version: "OBL_V1";

  // Identity
  id: string;     // stable e.g. "O-000311"
  name: string;   // stable snake_case label
  type: ObligationType;

  // Blocking semantics
  severity: ObligationSeverity;
  status: ObligationStatus;

  // Attestation binding
  expected_attestor: ExpectedAttestor;
  evidence_artifact: string | null;
  evidence_format: string | null;
  evidence_hash: string | null;

  // Governance metadata (replay-safe)
  domain: string;
  tier: "I" | "II" | "III";
  reason: string;
  reason_codes: ReasonCode[];

  // Telemetry-only (excluded from replay hash)
  created_at?: string;
}
```

### 5.2 JSON Schema

```json
{
  "$id": "legoracle.schemas/BlockingObligationV1.json",
  "type": "object",
  "required": [
    "canon_version",
    "id",
    "name",
    "type",
    "severity",
    "status",
    "expected_attestor",
    "evidence_artifact",
    "evidence_format",
    "evidence_hash",
    "domain",
    "tier",
    "reason",
    "reason_codes"
  ],
  "properties": {
    "canon_version": { "const": "OBL_V1" },
    "id": { "type": "string", "pattern": "^O-[0-9]{6}$" },
    "name": { "type": "string" },
    "type": {
      "enum": [
        "BASELINE_REQUIRED",
        "INSTRUMENTATION_INTEGRITY",
        "ATTESTATION_REQUIRED",
        "SECURITY_REVIEW",
        "LEGAL_REVIEW",
        "PRIVACY_REVIEW",
        "REPRODUCIBILITY_REQUIRED",
        "OTHER"
      ]
    },
    "severity": { "enum": ["HARD", "SOFT"] },
    "status": { "enum": ["OPEN", "SATISFIED", "WAIVED", "INVALID"] },
    "expected_attestor": {
      "enum": [
        "METRIC_SNAPSHOT",
        "TOOL_RESULT",
        "CODE_PROOF",
        "AUDITOR_REPORT",
        "LEGAL_DOC",
        "PRIVACY_DOC",
        "HUMAN_REVIEW",
        "NONE"
      ]
    },
    "evidence_artifact": { "type": ["string", "null"] },
    "evidence_format": { "type": ["string", "null"] },
    "evidence_hash": { "type": ["string", "null"] },
    "domain": { "type": "string" },
    "tier": { "enum": ["I", "II", "III"] },
    "reason": { "type": "string", "maxLength": 240 },
    "reason_codes": {
      "type": "array",
      "items": {
        "enum": [
          "NO_RECEIPT",
          "MISSING_BASELINE",
          "MISSING_INSTRUMENTATION",
          "MISSING_ATTESTATION",
          "UNVERIFIABLE",
          "OVERSCOPED",
          "LEGAL_RISK",
          "PRIVACY_RISK",
          "SECURITY_RISK",
          "NON_DETERMINISTIC"
        ]
      }
    },
    "created_at": { "type": "string" }
  },
  "additionalProperties": false
}
```

### 5.3 Invariants (Hard)

1. If `severity="HARD"` and `status="OPEN"` ⇒ blocks SHIP
2. If `status="SATISFIED"` ⇒ `evidence_hash` MUST be non-null
3. `created_at` MUST be excluded from replay hash
4. `reason_codes` must be sorted lexicographically

---

## SECTION 6: DETERMINISTIC CANONICALIZATION

### 6.1 Canonicalization Function

```python
def canon(obj):
    """
    Deterministic hash view:
    - UTF-8 JSON
    - Stable key ordering (lexicographic)
    - No whitespace
    - Exclude: *.created_at, timestamps, run IDs
    """
    return json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')
    ).encode('utf-8')
```

### 6.2 Sorting Key (Obligations List)

```python
def obligation_sort_key(obl):
    """
    Enforce this single ordering everywhere.
    """
    severity_rank = 0 if obl["severity"] == "HARD" else 1
    status_rank = {
        "OPEN": 0,
        "SATISFIED": 1,
        "WAIVED": 2,
        "INVALID": 3
    }[obl["status"]]

    return (
        severity_rank,
        status_rank,
        obl["expected_attestor"],
        obl["type"],
        obl["name"],
        obl["id"]
    )
```

### 6.3 Deterministic Ordering Inside Object

- `reason_codes`: sort lexicographically before hashing and display

---

## SECTION 7: REMEDIATION ENGINE (MINIMAL, DETERMINISTIC)

### 7.1 Algorithm

```python
def remediate(original_claim, blocking_obligations):
    """
    Simple, deterministic remediation.

    For each blocker:
    - If metric missing → propose Tier B metric
    - If scope too broad → shrink scope
    - If unverifiable → downgrade to narrative

    Emit:
    - delta_log
    - acceptance_gates (all false)
    - ship_score = count of remaining blockers
    """
    v2 = {
        "tier_a": None,  # ALWAYS null
        "tier_b": None,
        "tier_c": None,
        "delta_log": [],
        "acceptance_gates": [],
        "ship_score": 0,
        "disclaimer": ""
    }

    for obl in blocking_obligations:
        if obl["status"] != "OPEN":
            continue

        v2["ship_score"] += 1

        if obl["type"] == "BASELINE_REQUIRED":
            v2["tier_b"] = propose_tier_b_metric(obl)
            v2["delta_log"].append({
                "change": "Added baseline metric",
                "reason": obl["reason"]
            })
            v2["acceptance_gates"].append({
                "id": f"gate-{obl['id']}",
                "obligation_id": obl["id"],
                "pass_fail": False,
                "description": "Baseline metric verified"
            })

        elif obl["type"] == "INSTRUMENTATION_INTEGRITY":
            v2["tier_b"] = propose_tier_b_metric(obl)
            v2["delta_log"].append({
                "change": "Added instrumentation integrity check",
                "reason": obl["reason"]
            })
            v2["acceptance_gates"].append({
                "id": f"gate-{obl['id']}",
                "obligation_id": obl["id"],
                "pass_fail": False,
                "description": "Instrumentation verified via CODE_PROOF"
            })

        elif obl["type"] == "ATTESTATION_REQUIRED":
            v2["tier_c"] = downgrade_to_narrative(obl)
            v2["delta_log"].append({
                "change": "Downgraded to narrative (attestation pending)",
                "reason": obl["reason"]
            })
            v2["disclaimer"] += f"\n⚠️  Pending attestation: {obl['name']}"

        elif obl["type"] in ["LEGAL_REVIEW", "PRIVACY_REVIEW", "SECURITY_REVIEW"]:
            v2["tier_c"] = downgrade_to_narrative(obl)
            v2["delta_log"].append({
                "change": f"Downgraded to narrative ({obl['type']} pending)",
                "reason": obl["reason"]
            })
            v2["disclaimer"] += f"\n⚠️  Pending {obl['type']}: {obl['name']}"

        elif obl["type"] == "REPRODUCIBILITY_REQUIRED":
            v2["tier_b"] = propose_tier_b_with_artifacts(obl)
            v2["delta_log"].append({
                "change": "Added hashable artifacts requirement",
                "reason": obl["reason"]
            })
            v2["acceptance_gates"].append({
                "id": f"gate-{obl['id']}",
                "obligation_id": obl["id"],
                "pass_fail": False,
                "description": "Replay manifest verified"
            })

        else:  # OTHER
            v2["tier_c"] = downgrade_to_narrative(obl)
            v2["delta_log"].append({
                "change": "Downgraded to narrative (unverifiable)",
                "reason": obl["reason"]
            })

    # Ensure disclaimer is non-empty
    if not v2["disclaimer"]:
        v2["disclaimer"] = "⚠️  This is a V2 proposal. Original claim was blocked."

    return v2
```

### 7.2 Minimal Mapping Table

| `obligation.type` | Builders Default Response |
|-------------------|---------------------------|
| `BASELINE_REQUIRED` | Tier B metric + baseline declaration |
| `INSTRUMENTATION_INTEGRITY` | Tier B metric event schema + CODE_PROOF evidence plan |
| `ATTESTATION_REQUIRED` | Tier C downgrade + explicit disclaimer |
| `LEGAL/PRIVACY/SECURITY_REVIEW` | Tier C narrative + "pending review" disclaimer |
| `REPRODUCIBILITY_REQUIRED` | Tier B with hashable artifacts + replay manifest |

---

## SECTION 8: INTEGRATION WITH META-COGNITIVE BUILDER

### 8.1 The Bridge

The **Meta-Cognitive Builder** (v2.0-RLM) feeds ORACLE 2 BUILDERS:

```
CONSENSUS PACKET → Meta-Cognitive Builder → OBLIGATIONS → ORACLE 1 → NO_SHIP
                   (5-agent pipeline)                     (Verdict)

                                                            ↓
                                                      ORACLE 2 BUILDERS
                                                            ↓
                                                       V2 PROPOSAL
```

### 8.2 Flow

1. **Human** defines `ConsensusPacket` (wedge + constraints)
2. **Meta-Cognitive Builder** runs 5-agent pipeline:
   - DECOMPOSER → breaks into subtasks
   - EXPLORER → generates candidates
   - CRITIC → multi-angle verification + confidence scoring
   - BUILDER → converts to obligations
   - INTEGRATOR → synthesizes (STOP/CONTINUE)
3. **ORACLE 1** evaluates obligations:
   - If `blocking_obligations > 0` → NO_SHIP
4. **ORACLE 2 BUILDERS** remediates:
   - Takes NO_SHIP + `blocking_obligations`
   - Applies monotonic weakening
   - Outputs V2 proposal

### 8.3 Example

**Input (from Meta-Cognitive Builder):**

```json
{
  "original_claim": {
    "assertion": "Reduce API latency to < 100ms p99 without external dependencies"
  },
  "verdict": {
    "decision": "NO_SHIP",
    "blocking": [
      {
        "canon_version": "OBL_V1",
        "id": "O-000311",
        "name": "baseline_required",
        "type": "BASELINE_REQUIRED",
        "severity": "HARD",
        "status": "OPEN",
        "expected_attestor": "METRIC_SNAPSHOT",
        "evidence_artifact": null,
        "evidence_format": null,
        "evidence_hash": null,
        "domain": "engineering",
        "tier": "II",
        "reason": "No pre-change baseline for latency p99",
        "reason_codes": ["MISSING_BASELINE"]
      }
    ]
  }
}
```

**Output (from ORACLE 2 BUILDERS):**

```json
{
  "v2_proposal": {
    "tier_a": null,
    "tier_b": {
      "metric": "api_latency_p99_ms",
      "baseline": {
        "value": null,
        "measured_at": null,
        "requires_collection": true
      },
      "acceptance_gate": {
        "condition": "p99 < 100ms",
        "evidence_type": "METRIC_SNAPSHOT"
      }
    },
    "tier_c": null,
    "delta_log": [
      {
        "change": "Added baseline metric",
        "reason": "No pre-change baseline for latency p99"
      }
    ],
    "acceptance_gates": [
      {
        "id": "gate-O-000311",
        "obligation_id": "O-000311",
        "pass_fail": false,
        "description": "Baseline metric verified"
      }
    ],
    "ship_score": 1,
    "disclaimer": "⚠️  This is a V2 proposal. Original claim was blocked."
  }
}
```

---

## SECTION 9: CLI SURFACE (MVP ONLY)

### 9.1 Command 1: Run with Remediation

```bash
legoracle run --claim "X" --remediate
```

**Behavior:**
- `SHIP` → normal verdict (no remediation)
- `NO_SHIP` → verdict + V2 proposal

**Example Output:**

```
═══════════════════════════════════════════════════════════
ORACLE 1 — Verdict
═══════════════════════════════════════════════════════════
Decision: NO_SHIP
Blocking Obligations: 1

O-000311 | baseline_required | HARD | OPEN
  Reason: No pre-change baseline for latency p99

═══════════════════════════════════════════════════════════
ORACLE 2 — V2 Proposal
═══════════════════════════════════════════════════════════
Ship Score: 1 (lower is better)

Tier A: null
Tier B:
  Metric: api_latency_p99_ms
  Baseline: REQUIRES COLLECTION
  Gate: p99 < 100ms (pass_fail: false)

Disclaimer:
⚠️  This is a V2 proposal. Original claim was blocked.

Next Steps:
1. Collect baseline metric
2. Re-submit with evidence_hash
```

### 9.2 Command 2: Show Canonical Example

```bash
legoracle remediation-sample --domain engineering
```

**Output:**

```json
{
  "canon_version": "OBL_V1",
  "id": "O-000311",
  "name": "baseline_required",
  "type": "BASELINE_REQUIRED",
  "severity": "HARD",
  "status": "OPEN",
  "expected_attestor": "METRIC_SNAPSHOT",
  "evidence_artifact": null,
  "evidence_format": null,
  "evidence_hash": null,
  "domain": "engineering",
  "tier": "II",
  "reason": "No pre-change baseline for metric X",
  "reason_codes": ["MISSING_BASELINE"]
}
```

### 9.3 Command 3: Generate Blank Scaffold

```bash
legoracle remediation-template --domain marketing
```

**Output:**

```json
{
  "v2_proposal": {
    "tier_a": null,
    "tier_b": null,
    "tier_c": {
      "narrative": "[YOUR NARRATIVE HERE]"
    },
    "delta_log": [],
    "acceptance_gates": [],
    "ship_score": 0,
    "disclaimer": "⚠️  Template only. Replace with actual proposal."
  }
}
```

---

## SECTION 10: WHAT YOU DO NOT SHIP (CRITICAL)

ORACLE 2 does **NOT** ship:
- ❌ Auto-approval
- ❌ Confidence scoring that implies truth
- ❌ Iterative remediation loops (single-pass only)
- ❌ Builder voting
- ❌ "Improvement" language
- ❌ Tier A/I claims (always null)
- ❌ Override buttons

**ORACLE 2 does not optimize truth. It optimizes admissibility.**

---

## SECTION 11: MVP EXIT CRITERIA

You can ship ORACLE 2 MVP when:

1. ✅ Every NO_SHIP produces a valid V2
2. ✅ V2 never upgrades a claim (monotonic weakening)
3. ✅ Output is JSON-stable and replayable
4. ✅ ORACLE 1 remains untouched
5. ✅ All obligations conform to `BlockingObligationV1.json`
6. ✅ Schema gates pass in CI

If those hold, **the product is real**.

---

## SECTION 12: CI GATES (MINIMAL, DECISIVE)

### 12.1 Required CI Checks

1. **Schema Gate:** Each obligation validates against `BlockingObligationV1.json`
2. **Contract Gate:** If `status="SATISFIED"` then `evidence_hash != null`
3. **Replay Gate:** Re-hash `canon(obligation)` twice ⇒ identical SHA-256
4. **Ordering Gate:** Lists of obligations sorted by `obligation_sort_key`
5. **Reason Code Gate:** `reason_codes` must be sorted and unique

### 12.2 Implementation

```python
def ci_validate_obligations(obligations):
    """
    Run all CI gates. Fail fast on any violation.
    """
    for obl in obligations:
        # Gate 1: Schema
        validate_schema(obl, schema="BlockingObligationV1.json")

        # Gate 2: Contract
        if obl["status"] == "SATISFIED" and not obl["evidence_hash"]:
            raise ValueError(f"SATISFIED obligation {obl['id']} missing evidence_hash")

        # Gate 3: Replay
        hash1 = sha256(canon(obl))
        hash2 = sha256(canon(obl))
        assert hash1 == hash2, f"Non-deterministic hash for {obl['id']}"

        # Gate 5: Reason codes
        assert obl["reason_codes"] == sorted(set(obl["reason_codes"]))

    # Gate 4: Ordering
    sorted_obls = sorted(obligations, key=obligation_sort_key)
    assert obligations == sorted_obls, "Obligations not properly sorted"
```

---

## SECTION 13: GOLDEN FIXTURES

### 13.1 Baseline Required (OPEN)

```json
{
  "canon_version": "OBL_V1",
  "id": "O-000311",
  "name": "baseline_required",
  "type": "BASELINE_REQUIRED",
  "severity": "HARD",
  "status": "OPEN",
  "expected_attestor": "METRIC_SNAPSHOT",
  "evidence_artifact": null,
  "evidence_format": null,
  "evidence_hash": null,
  "domain": "engineering",
  "tier": "II",
  "reason": "No pre-change baseline for metric X",
  "reason_codes": ["MISSING_BASELINE"]
}
```

### 13.2 Attestation Required (OPEN)

```json
{
  "canon_version": "OBL_V1",
  "id": "O-000320",
  "name": "soc2_attestation_required",
  "type": "ATTESTATION_REQUIRED",
  "severity": "HARD",
  "status": "OPEN",
  "expected_attestor": "AUDITOR_REPORT",
  "evidence_artifact": null,
  "evidence_format": null,
  "evidence_hash": null,
  "domain": "security",
  "tier": "II",
  "reason": "No auditor report supplied",
  "reason_codes": ["MISSING_ATTESTATION"]
}
```

---

## SECTION 14: WHAT THIS UNLOCKS (WITHOUT PROMISING)

Once live, ORACLE 2 enables:
- ✅ Constructive NO_SHIP outcomes
- ✅ Claim compression over time
- ✅ Institutional adoption (legal, science, gov)
- ✅ CI/CD for assertions
- ✅ Explicit uncertainty flagging
- ✅ Evidence-first culture

**But only because it never violates sovereignty.**

---

## FINAL AXIOMS

1. **ORACLE 1 = Judge, ORACLE 2 = Mechanic**
2. **Monotonic weakening is non-negotiable**
3. **Tier A is always null in V2**
4. **All gates start with pass_fail = false**
5. **Disclaimers are mandatory**
6. **Schema validation is a CI gate**
7. **Replay determinism is enforced**
8. **No auto-approval ever**

---

**Document Hash:** `SHA-256: [to be computed]`
**Version:** 2.0-FINAL
**Status:** LOCKED FOR SHIPPING

This is not a conversation. This is an institution.
