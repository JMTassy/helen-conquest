# INTAKE-GUARD: Forbidden Field Enforcement

**Version:** 1.0.0
**Status:** LOCKED (Constitutional)
**Last Updated:** 2026-01-23

## Purpose

Prevent Creative Town outputs from smuggling authority into the governance kernel.

---

## 1. Intake Guard Mission

**Single responsibility:** Reject CT bundles that attempt to assert authority.

### 1.1 Authority Separation Principle

```
CT outputs can influence WHAT gets evaluated.
CT outputs CANNOT influence WHETHER it gets approved.
```

**Enforcement:** Hard reject at intake (before Mayor sees it).

---

## 2. Forbidden Fields (Canonical List)

### 2.1 Ranking/Ordering (Authority Assertion)

Case-insensitive match (including as substrings):

```
rank, score, rating, priority, prioritize, top, best, worst,
recommended, recommend, preference, prefer, optimal, suboptimal,
first, second, third, winner, loser, chosen, selected, pick
```

**Rationale:** Ranking implies "this should be chosen" → authority claim.

### 2.2 Confidence/Epistemics (False Precision)

```
confidence, probability, likelihood, certainty, certain, sure,
guarantee, guaranteed, percent, %, odds, chance, risk, uncertain,
definitely, probably, maybe, possibly, likely, unlikely
```

**Rationale:** Confidence claims suggest "you should trust this" → authority claim.

### 2.3 Authority Claims (Direct Assertion)

```
ship, approved, approve, safe, unsafe, compliant, non-compliant,
verified, unverified, passed, failed, certified, valid, invalid,
satisfied, unsatisfied, complete, incomplete, resolved, unresolved,
cleared, blocked, ready, not_ready, go, no_go, green, red, yellow
```

**Rationale:** Direct assertion of verdict → authority claim.

### 2.4 Personalized High-Stakes (Investment/Trading)

```
buy, sell, hold, long, short, position, portfolio, allocation,
invest, divest, trade, execute, order, bid, ask, price_target,
recommendation, advice, guidance, counsel, suggestion
```

**Rationale:** Personalized financial advice → regulatory + ethical violation.

### 2.5 Obligation Satisfaction (Kernel Bypass)

```
already_satisfied, already_complete, already_verified, already_cleared,
no_action_needed, sufficient, adequate, acceptable, meets_requirements,
passes, complies, fulfills, satisfies
```

**Rationale:** Asserting satisfaction bypasses Factory → governance leak.

---

## 3. Detection Algorithm (Canonical)

### 3.1 Recursive Field Scanner

```python
def scan_for_forbidden_fields(obj: dict | list, forbidden_words: set) -> list[str]:
    """
    Recursively scan JSON object for forbidden field names or values.

    Returns: List of forbidden fields found (empty if clean)
    """
    violations = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            # Check key name
            if any(word in key.lower() for word in forbidden_words):
                violations.append(f"field_name:{key}")

            # Check string values
            if isinstance(value, str):
                if any(word in value.lower() for word in forbidden_words):
                    violations.append(f"field_value:{key}={value[:50]}")

            # Recurse
            violations.extend(scan_for_forbidden_fields(value, forbidden_words))

    elif isinstance(obj, list):
        for item in obj:
            violations.extend(scan_for_forbidden_fields(item, forbidden_words))

    return violations
```

### 3.2 Exempted Fields (Narrow Exceptions)

Some fields **MAY** contain forbidden words if they're metadata-only:

```json
{
  "metadata": {
    "ct_version": "1.0.0",  ← "version" allowed here
    "generation_timestamp": "...",  ← "timestamp" allowed
    "creative_role": "counterexample_hunter"  ← role name allowed
  }
}
```

**Rule:** Fields under `metadata.*` and `ct_run_manifest.*` are exempt (but still schema-validated).

---

## 4. Rejection Behavior (Fail-Closed)

### 4.1 Rejection Codes

| Code | Meaning | Remediation |
|------|---------|-------------|
| `CT_REJECTED_FORBIDDEN_FIELDS` | Forbidden fields detected | Remove fields, resubmit |
| `CT_REJECTED_SCHEMA_INVALID` | JSON schema validation failed | Fix schema, resubmit |
| `CT_REJECTED_BUDGET_VIOLATION` | Exceeded budget caps | Reduce proposals, resubmit |
| `CT_REJECTED_MALFORMED_JSON` | Invalid JSON syntax | Fix JSON, resubmit |

### 4.2 Rejection Output

```json
{
  "intake_decision": "REJECT",
  "rejection_code": "CT_REJECTED_FORBIDDEN_FIELDS",
  "forbidden_fields_found": [
    "field_name:recommendation",
    "field_value:ship=true"
  ],
  "ct_boundary_digest": "sha256:...",
  "timestamp": "2026-01-23T10:30:00Z"
}
```

**Critical:** Entire bundle rejected (no partial acceptance).

---

## 5. Boundary Digest (Immutable Record)

### 5.1 Purpose

Even rejected bundles get a digest (for audit trail).

### 5.2 Digest Computation

```python
boundary_digest = SHA256(canonical_json({
  "proposal_bundle": proposal_bundle,
  "ct_run_manifest": ct_run_manifest
}))
```

**Stored:** In rejection record (for later analysis of attack patterns).

---

## 6. Schema Validation (First Line of Defense)

### 6.1 Validation Order

1. **JSON syntax check** (malformed → reject)
2. **Schema validation** (against `proposal_bundle.schema.json`)
3. **Forbidden field scan** (this spec)
4. **Budget cap enforcement** (CT-SPEC §6)

**Early rejection:** Fail fast to save compute.

### 6.2 Schema Strictness

```json
{
  "additionalProperties": false  ← No extra fields allowed
}
```

**Rationale:** Schema closure prevents "creative" authority smuggling.

---

## 7. Budget Caps (Anti-DOS)

### 7.1 Hard Limits

| Cap | Limit | Violation Code |
|-----|-------|---------------|
| `max_proposals_per_run` | 100 | `CT_REJECTED_BUDGET_VIOLATION` |
| `max_obligations_per_run` | 50 | `CT_REJECTED_BUDGET_VIOLATION` |
| `max_free_text_bytes` | 100KB | `CT_REJECTED_BUDGET_VIOLATION` |
| `max_metadata_fields` | 20 | `CT_REJECTED_BUDGET_VIOLATION` |
| `max_description_hash_length` | 64 chars | `CT_REJECTED_SCHEMA_INVALID` |

**Enforcement:** Check before forbidden field scan (fail fast).

---

## 8. Adversarial Examples (Canonical Test Cases)

### 8.1 Attack: Direct Authority Claim

**Input:**
```json
{
  "proposals": [
    {
      "proposal_id": "P-...",
      "ship": true,  ← FORBIDDEN
      "rationale": "This is safe to ship"
    }
  ]
}
```

**Expected:** `CT_REJECTED_FORBIDDEN_FIELDS` (field: `ship`)

### 8.2 Attack: Confidence Smuggling

**Input:**
```json
{
  "proposals": [
    {
      "proposal_id": "P-...",
      "suggested_changes": {
        "gdpr_compliance": "verified with 95% confidence"  ← FORBIDDEN
      }
    }
  ]
}
```

**Expected:** `CT_REJECTED_FORBIDDEN_FIELDS` (field_value: `confidence`)

### 8.3 Attack: Ranking Implication

**Input:**
```json
{
  "proposals": [
    {
      "proposal_id": "P-001",
      "rank": 1  ← FORBIDDEN
    },
    {
      "proposal_id": "P-002",
      "rank": 2  ← FORBIDDEN
    }
  ]
}
```

**Expected:** `CT_REJECTED_FORBIDDEN_FIELDS` (field: `rank`)

### 8.4 Attack: Obligation Satisfaction Assertion

**Input:**
```json
{
  "proposals": [
    {
      "proposal_id": "P-...",
      "suggested_changes": {
        "gdpr_consent_banner": "already_satisfied"  ← FORBIDDEN
      }
    }
  ]
}
```

**Expected:** `CT_REJECTED_FORBIDDEN_FIELDS` (field_value: `already_satisfied`)

---

## 9. Normalization (Post-Acceptance)

If intake accepts bundle, it **MUST** normalize:

### 9.1 Normalization Steps

1. **Sort keys lexicographically** (deterministic hash)
2. **Remove whitespace** (compact JSON)
3. **Validate UTF-8 encoding**
4. **Compute boundary digest**
5. **Strip free-text** (keep only `description_hash`)

### 9.2 Normalized Output

```json
{
  "intake_decision": "ACCEPT",
  "briefcase": {
    "run_id": "R-20260123-001",
    "claim_id": "CLM-...",
    "required_obligations": [...],
    "policy_hash": "sha256:..."
  },
  "ct_boundary_digest": "sha256:...",
  "timestamp": "2026-01-23T10:30:00Z"
}
```

**No free text in briefcase** (only structured data).

---

## 10. Logging (Audit Trail)

### 10.1 Rejection Log

Every rejection **MUST** be logged:

```json
{
  "log_entry_id": "LOG-...",
  "intake_decision": "REJECT",
  "rejection_code": "CT_REJECTED_FORBIDDEN_FIELDS",
  "ct_boundary_digest": "sha256:...",
  "forbidden_fields_found": [...],
  "timestamp": "2026-01-23T10:30:00Z",
  "policy_version": "1.2.3"
}
```

**Purpose:** Detect attack patterns, improve forbidden field list.

---

## 11. Escape Hatches (None Permitted)

**Forbidden:**
- `--skip-intake` flag
- `--allow-forbidden-fields` override
- `--trust-creative-town` mode
- Manual approval of rejected bundles

**Rationale:** Intake guard is **non-negotiable** security boundary.

---

## 12. Test Suite (Mandatory)

| Test ID | Input | Expected Outcome |
|---------|-------|------------------|
| `IG-01` | Valid proposal bundle | ACCEPT |
| `IG-02` | Bundle with `rank: 1` | REJECT (FORBIDDEN_FIELDS) |
| `IG-03` | Bundle with `confidence: 0.9` | REJECT (FORBIDDEN_FIELDS) |
| `IG-04` | Bundle with `ship: true` | REJECT (FORBIDDEN_FIELDS) |
| `IG-05` | Bundle with 101 proposals | REJECT (BUDGET_VIOLATION) |
| `IG-06` | Malformed JSON | REJECT (MALFORMED_JSON) |
| `IG-07` | Bundle with `already_satisfied` | REJECT (FORBIDDEN_FIELDS) |
| `IG-08` | Bundle with `recommendation` | REJECT (FORBIDDEN_FIELDS) |
| `IG-09` | Bundle with metadata.ct_version | ACCEPT (exempted field) |
| `IG-10` | 100 bundles, 5 with violations | 5 REJECT, 95 ACCEPT |

---

## 13. Immutability Clause

This specification is **locked**. Changes require:

1. **Policy change run** (itself governed)
2. **Security review** (OBL-POLICY-REVIEW-SECURITY)
3. **Adversarial testing** (new forbidden words must have test cases)
4. **MAJOR version bump** (if removing forbidden words)

**No "emergency relaxation" permitted.**

---

**END INTAKE-GUARD v1.0.0**
