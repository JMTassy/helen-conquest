# POLICY-GOV: Policy Versioning + Change Control

**Version:** 1.0.0
**Status:** LOCKED (Constitutional)
**Last Updated:** 2026-01-23

## Purpose

Policies are the constitution. Policy changes must be governed with the same rigor as claims.

---

## 1. Core Principles

### 1.1 Policy is Immutable Per Run

Each run pins a **`policy_hash`**. Mayor evaluates **only** against that pinned hash.

**Invariant:**
```
decision(run_id) = f(policy_hash, briefcase, ledger)
```

Changing policy mid-run → **forbidden** (determinism violation).

### 1.2 Policy Change is Itself Governed

A policy update is **only accepted** if:

1. Proposed as a **`policy_change_bundle`**
2. Runs through the **same Factory/Mayor pipeline**
3. Satisfies dedicated obligation set (see §3)

**No "admin override" permitted.**

---

## 2. Policy Object Structure

### 2.1 Canonical Policy Schema

```json
{
  "policy_id": "POL-ORACLE-TOWN",
  "policy_version": "1.2.3",
  "policy_hash": "sha256:a3f5...",
  "effective_date": "2026-01-23T00:00:00Z",
  "parent_policy_hash": "sha256:b7c2...",
  "change_rationale": "Added OBL-GDPR-COOKIE-CONSENT",

  "obligations": [...],
  "attestor_registry": [...],
  "revoked_keys": [...],
  "revoked_attestors": [...],
  "quorum_rules": {...},
  "invariants": {...},
  "budget_caps": {...}
}
```

### 2.2 Semantic Versioning

`policy_version = MAJOR.MINOR.PATCH`

| Component | When to Increment | Examples |
|-----------|------------------|----------|
| **MAJOR** | Breaking schema/governance rule change | Remove obligation type, change quorum rules |
| **MINOR** | Adds obligations / attestors / tooling | Add new obligation, add attestor class |
| **PATCH** | Bugfixes, clarifications, no rule impact | Fix typo, clarify description |

**Version advancement is monotonic** (no downgrades).

---

## 3. Policy Change Obligations (Mandatory)

Every policy change **MUST** satisfy:

### 3.1 Required Obligations

```json
{
  "obligation_name": "policy_review_security",
  "type": "COMPLIANCE_SIGNOFF",
  "severity": "HARD",
  "required_attestor_classes": ["SECURITY"],
  "description": "Security review of policy changes for governance vulnerabilities"
}
```

```json
{
  "obligation_name": "policy_review_legal",
  "type": "COMPLIANCE_SIGNOFF",
  "severity": "HARD",
  "required_attestor_classes": ["LEGAL"],
  "description": "Legal review of policy changes (required if high-stakes domain)"
}
```

```json
{
  "obligation_name": "policy_determinism_check",
  "type": "EMPIRICAL_TEST",
  "severity": "HARD",
  "required_attestor_classes": ["CI_RUNNER"],
  "description": "Verify policy hash is stable under canonical serialization"
}
```

```json
{
  "obligation_name": "policy_compatibility_check",
  "type": "STATIC_ANALYSIS",
  "severity": "HARD",
  "required_attestor_classes": ["CI_RUNNER"],
  "description": "Schema compatibility check OR explicit breaking version bump"
}
```

### 3.2 Policy Change Flow

```
1. Human proposes policy change → policy_change_bundle.json
2. Oracle intake → briefcase (with policy change obligations)
3. Factory executes policy change tests
4. Mayor decides on policy change (SHIP or NO_SHIP)
5. If SHIP → new policy becomes active
6. If NO_SHIP → policy change rejected, old policy remains
```

---

## 4. Mayor Purity w.r.t. Policy

### 4.1 Pure Function Requirement

Mayor logic depends **only** on:

```python
def mayor_decide(policy: Policy, briefcase: Briefcase, ledger: Ledger) -> Decision:
    # NO environment reads
    # NO timestamps (except for logging)
    # NO model outputs
    # NO external state
    return decision
```

**Forbidden inputs:**
- Current time (except for audit logs)
- Network state
- LLM outputs
- User preferences (not in policy)
- Random numbers (except for sampling, with fixed seed)

### 4.2 Determinism Test

```python
# Same inputs → same output
d1 = mayor_decide(policy, briefcase, ledger)
d2 = mayor_decide(policy, briefcase, ledger)
assert d1.decision_digest == d2.decision_digest
```

---

## 5. Policy Pinning (Execution-Time)

### 5.1 Run-Time Policy Selection

Every run **MUST** declare policy at start:

```json
{
  "run_id": "R-20260123-001",
  "policy_id": "POL-ORACLE-TOWN",
  "policy_version": "1.2.3",
  "policy_hash": "sha256:a3f5..."
}
```

### 5.2 Policy Hash Verification

Before Mayor execution:

```python
loaded_policy = load_policy(policy_id, policy_version)
computed_hash = SHA256(canonical_json(loaded_policy))

if computed_hash != run_manifest.policy_hash:
    raise PolicyHashMismatch("Policy was tampered with")
```

**Fail-closed:** Mismatch → NO_SHIP (immediate halt).

---

## 6. Policy Lineage (Audit Trail)

### 6.1 Parent Policy Hash

Each policy **MUST** reference its parent:

```json
{
  "policy_version": "1.3.0",
  "policy_hash": "sha256:a3f5...",
  "parent_policy_hash": "sha256:b7c2...",
  "change_rationale": "Added OBL-GDPR-COOKIE-CONSENT per EU regulation 2024/XYZ"
}
```

### 6.2 Policy Change Log

Maintained as append-only ledger:

```json
{
  "policy_changes": [
    {
      "from_version": "1.2.3",
      "to_version": "1.3.0",
      "change_run_id": "R-POLICY-20260120-001",
      "change_decision": "SHIP",
      "change_digest": "sha256:...",
      "changed_by": "DOMAIN_OWNER",
      "timestamp": "2026-01-20T10:00:00Z"
    }
  ]
}
```

---

## 7. Backward Compatibility Rules

### 7.1 MINOR Version Compatibility

MINOR version bumps **MUST**:
- Preserve existing obligation names
- Preserve existing attestor classes
- Only **add** new obligations/attestors (never remove)

### 7.2 MAJOR Version Breaking Changes

MAJOR version bumps **MAY**:
- Remove obligations
- Change quorum rules
- Remove attestor classes
- Change signature schemes

**Requirement:** MAJOR bumps require **explicit migration plan**.

---

## 8. Policy Activation (Atomic Swap)

### 8.1 Activation Trigger

New policy becomes active **only after**:

1. Policy change run completes with `SHIP`
2. Decision record is written
3. Policy file is atomically swapped

```bash
# Atomic swap (filesystem-level)
mv policies/POL-1.3.0.json.tmp policies/POL-1.3.0.json
```

### 8.2 Rollback Plan

If new policy causes failures:

1. **Revert to parent policy** (using `parent_policy_hash`)
2. **Create emergency policy change run** (with new obligations to fix issue)
3. **Document failure mode** (add to policy change log)

**No manual override.**

---

## 9. Forbidden Policy Changes (Constitutional)

These changes are **permanently forbidden** (even in MAJOR versions):

### 9.1 Never Permitted

1. **Removing fail-closed semantics** (missing receipt → NO_SHIP)
2. **Adding "override buttons"** (human can bypass obligations)
3. **Non-deterministic scoring** (LLM-based verdicts)
4. **Removing kill-switch dominance** (authorized teams can always halt)
5. **Removing receipt requirements** (NO_RECEIPT = NO_SHIP axiom)
6. **Self-attestation for HARD obligations** (CT cannot satisfy its own proposals)
7. **Quorum-by-person** (must be quorum-by-class)

### 9.2 Rationale

These rules are **kernel invariants**. Violating them → not ORACLE TOWN anymore.

---

## 10. Policy Change Test Suite (Mandatory)

Every policy change **MUST** pass:

| Test ID | Test Description | Expected Outcome |
|---------|-----------------|------------------|
| `POL-01` | Policy hash is deterministic (serialize 10 times) | All hashes identical |
| `POL-02` | Schema validation passes | Valid JSON Schema |
| `POL-03` | MINOR version does not remove obligations | Compatibility check passes |
| `POL-04` | MAJOR version includes migration plan | Document exists |
| `POL-05` | Replay old runs with new policy → same decision | Determinism preserved |
| `POL-06` | New policy includes all kernel invariants | Invariants present |
| `POL-07` | Revoked keys remain revoked | Revocation list append-only |

---

## 11. Emergency Policy Changes (Restricted)

### 11.1 Definition

An **emergency policy change** is one triggered by:
- Critical security vulnerability
- Legal/regulatory compliance failure
- Production system failure

### 11.2 Emergency Change Process

Even in emergencies:

1. **Create policy change bundle** (no shortcuts)
2. **Expedited Factory run** (but still run tests)
3. **SECURITY + LEGAL signoff required** (quorum-by-class)
4. **Post-mortem obligation** (analyze why emergency happened)

**No "skip governance" flag.**

---

## 12. Policy Versioning Examples

### 12.1 PATCH Change (Non-Breaking)

```diff
# POL-1.2.3 → POL-1.2.4

{
  "obligation_name": "gdpr_consent_banner",
- "description": "Implement cookie consent banner"
+ "description": "Implement cookie consent banner (GDPR Art. 7)"
}
```

**Rationale:** Clarification only, no semantic change.

### 12.2 MINOR Change (Additive)

```diff
# POL-1.2.4 → POL-1.3.0

{
  "obligations": [
    { "obligation_name": "gdpr_consent_banner", ... },
+   { "obligation_name": "ccpa_do_not_sell", "type": "LEGAL_COMPLIANCE", ... }
  ]
}
```

**Rationale:** Added new obligation, did not remove old ones.

### 12.3 MAJOR Change (Breaking)

```diff
# POL-1.3.0 → POL-2.0.0

{
  "quorum_rules": {
-   "min_quorum": 2,
+   "min_quorum": 3,
-   "required_attestor_classes": ["CI_RUNNER", "LEGAL"],
+   "required_attestor_classes": ["CI_RUNNER", "LEGAL", "SECURITY"]
  }
}
```

**Rationale:** Changed quorum rules (breaking change, requires MAJOR bump).

---

## 13. Immutability Clause

This specification is **locked**. Changes require:

1. **Policy change run** (meta: policy-about-policy-changes)
2. **Security review** (OBL-POLICY-REVIEW-SECURITY)
3. **Legal review** (OBL-POLICY-REVIEW-LEGAL)
4. **Determinism verification** (OBL-POLICY-DETERMINISM)
5. **Community review** (if open-source)
6. **MAJOR version bump** (breaking change)

**No "emergency bypass" permitted.**

---

**END POLICY-GOV v1.0.0**
