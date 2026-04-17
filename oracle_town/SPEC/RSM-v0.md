# RSM-v0: Receipt Security Model

**Version:** 0.1.0
**Status:** LOCKED (Constitutional)
**Last Updated:** 2026-01-23

## Purpose

Define what "receipt" means to prevent social capture, collusion, and authority smuggling.

---

## 1. Receipt Primitive (Canonical Definition)

A **receipt** is cryptographic proof that an obligation was satisfied under a specific policy version.

### 1.1 Receipt Object (Required Fields)

```json
{
  "attestation_id": "ATT-...",
  "run_id": "R-...",
  "claim_id": "CLM-...",
  "obligation_name": "gdpr_consent_banner",
  "attestor_id": "ci_runner_001",
  "attestor_class": "CI_RUNNER",
  "policy_hash": "sha256:a3f5...",
  "evidence_digest": "sha256:b7c2...",
  "signing_key_id": "key-2026-01-ci",
  "signature": "ed25519:...",
  "timestamp": "2026-01-23T10:30:00Z",
  "policy_match": 1
}
```

### 1.2 Field Semantics

| Field | Type | Semantics |
|-------|------|-----------|
| `attestation_id` | string | Unique identifier (UUID or content hash) |
| `run_id` | string | Links to governance run |
| `claim_id` | string | Links to claim being evaluated |
| `obligation_name` | string | Must match briefcase obligation (snake_case) |
| `attestor_id` | string | Unique attestor identifier (not person, but role instance) |
| `attestor_class` | enum | Function-based class (see §2) |
| `policy_hash` | sha256 | Pinned policy version (determinism requirement) |
| `evidence_digest` | sha256 | Hash of evidence payload |
| `signing_key_id` | string | Public key identifier (for revocation) |
| `signature` | ed25519 | Signature over canonical message (see §3) |
| `timestamp` | ISO8601 | When attestation was created |
| `policy_match` | 0 or 1 | Binary satisfaction (1 = satisfied, 0 = not satisfied) |

---

## 2. Receipt Types (Exhaustive Enum)

Each attestation **MUST** declare one of:

| Receipt Type | Attestor Class | Semantics |
|--------------|---------------|-----------|
| `EMPIRICAL_TEST` | `CI_RUNNER` | Unit/integration tests, reproducible execution |
| `STATIC_ANALYSIS` | `SECURITY` | Linters, SAST, formal checks |
| `COMPLIANCE_SIGNOFF` | `LEGAL` | Legal/regulatory, human authority |
| `PROVENANCE` | `RELEASE_MANAGER` | SBOM, artifact origin, supply chain |
| `REPRODUCIBILITY` | `CI_RUNNER` | Determinism / replay proofs |
| `HUMAN_REVIEW` | `DOMAIN_OWNER` | Expert signoff (non-automated) |

---

## 3. Attestor Classes (By Function, Not Person)

**Critical:** Attestors are identified by **function**, not individual identity.

### 3.1 Canonical Attestor Classes

| Class | Authority Scope | Revocation Trigger |
|-------|----------------|-------------------|
| `CI_RUNNER` | Automated test execution | Key compromise, test rig failure |
| `SECURITY` | Static analysis, vulnerability scanning | Scanner misconfiguration, false negative |
| `LEGAL` | Regulatory compliance, legal review | Attorney disbarment, policy change |
| `DOMAIN_OWNER` | Product/domain expertise signoff | Role change, conflict of interest |
| `RELEASE_MANAGER` | Build provenance, SBOM validation | Supply chain compromise |

**Forbidden:** `CREATIVE_TOWN`, `LLM_AGENT`, `ORACLE_PROPOSAL`

---

## 4. Quorum-by-Class Rules

### 4.1 Per-Obligation Quorum Declaration

Each obligation in the briefcase **MUST** declare:

```json
{
  "obligation_name": "gdpr_consent_banner",
  "required_attestor_classes": ["CI_RUNNER", "LEGAL"],
  "min_quorum": 2
}
```

### 4.2 Quorum Satisfaction Rule

An obligation is **satisfied** if and only if:

1. **Attestations exist** for all `required_attestor_classes`
2. **Distinct classes** (not distinct individuals)
3. **All `policy_match = 1`**
4. **No revoked keys** (see §5)
5. **Signatures valid** (see §6)

**Failure modes:**
- Missing class → `QUORUM_NOT_MET`
- Revoked key → `REVOKED_ATTESTOR`
- Invalid signature → `SIGNATURE_INVALID`
- `policy_match = 0` → `OBLIGATION_NOT_SATISFIED`

---

## 5. Non-Repudiation + Signature Scheme

### 5.1 Canonical Signature Message

Each attestation signs:

```
message = canonical_json({
  "run_id": "...",
  "claim_id": "...",
  "obligation_name": "...",
  "attestor_id": "...",
  "attestor_class": "...",
  "policy_hash": "...",
  "evidence_digest": "...",
  "policy_match": 1
})
```

Signature algorithm: **Ed25519**

### 5.2 Verification

Mayor **MUST** verify:

```python
verify_ed25519(
  public_key=get_public_key(signing_key_id),
  message=canonical_message,
  signature=signature
)
```

If verification fails → attestation is **invalid** (obligation not satisfied).

---

## 6. Revocation (Key-Based)

### 6.1 Revocation List (Append-Only)

Policy includes:

```json
{
  "revoked_keys": [
    { "key_id": "key-2025-12-ci", "revoked_at": "2026-01-15T00:00:00Z", "reason": "Key compromise" }
  ],
  "revoked_attestors": [
    { "attestor_id": "legal_advisor_001", "revoked_at": "2026-01-10T00:00:00Z", "reason": "Role change" }
  ]
}
```

### 6.2 Revocation Enforcement

Mayor rule:

```python
if attestation.signing_key_id in policy.revoked_keys:
    return INVALID_ATTESTATION
if attestation.attestor_id in policy.revoked_attestors:
    return INVALID_ATTESTATION
```

**Retroactive effect:** If key is revoked, **all** past attestations signed with that key are invalid.

---

## 7. Sampling / Audit (Anti-Rubber-Stamp)

### 7.1 Standing Obligation

Every policy **MUST** include:

```json
{
  "obligation_name": "audit_sample_random",
  "type": "COMPLIANCE_SIGNOFF",
  "severity": "SOFT",
  "required_attestor_classes": ["DOMAIN_OWNER"],
  "sampling_rate": 0.05
}
```

**Semantics:**
- 5% of SHIP runs are randomly selected for manual audit
- `DOMAIN_OWNER` or `SECURITY` must re-verify receipts
- Prevents "auto-SHIP" decay

### 7.2 Sampling Trigger

```python
import random
if random.random() < policy.sampling_rate:
    obligations.append(OBL_AUDIT_SAMPLE_RANDOM)
```

---

## 8. Evidence Linkage (No Receipt Without Evidence)

### 8.1 Evidence Artifact Requirements

Every attestation **MUST** reference evidence:

```json
{
  "evidence_digest": "sha256:...",
  "evidence_uri": "artifacts/sha256-b7c2.../pytest-junit.xml",
  "evidence_type": "pytest-junit"
}
```

### 8.2 Mayor Enforcement

```python
if not attestation.evidence_digest:
    return NO_RECEIPT_NO_SHIP
if not verify_evidence_exists(attestation.evidence_uri):
    return EVIDENCE_MISSING
```

**Axiom:** `NO_RECEIPT = NO_SHIP` (from ORACLE SUPERTEAM)

---

## 9. Determinism (Replay Equivalence)

### 9.1 Replay Requirement

Given:
- Same `briefcase.json`
- Same `ledger.json` (with receipts)
- Same `policy.json`

Mayor **MUST** produce:
- Same `decision_record.json`
- Same `decision_digest`

### 9.2 Digest Computation

```python
decision_digest = SHA256(canonical({
  "run_id": "...",
  "claim_id": "...",
  "decision": "SHIP",
  "policy_hash": "...",
  "briefcase_digest": "...",
  "ledger_digest": "..."
}))
```

**Test:** Replay 100 times → 100 identical digests.

---

## 10. Forbidden Operations (Constitutional)

These operations are **permanently forbidden**:

1. **Self-attestation:** CT/LLM agents cannot be valid attestors for HARD obligations
2. **Quorum-by-person:** Quorum must be by class, not individuals
3. **Soft satisfaction:** `policy_match` must be binary (0 or 1), no floats
4. **Receipt injection:** Receipts not signed with valid key → invalid
5. **Revocation bypass:** No "emergency override" to un-revoke keys
6. **Evidence-free receipts:** No receipt without `evidence_digest`

---

## 11. Test Vectors (Canonical)

Every RSM implementation MUST pass:

| Test ID | Scenario | Expected Outcome |
|---------|----------|------------------|
| `RSM-01` | Valid receipt, quorum met | OBLIGATION_SATISFIED |
| `RSM-02` | Receipt with revoked key | INVALID_ATTESTATION |
| `RSM-03` | Quorum requires 2 classes, only 1 present | QUORUM_NOT_MET |
| `RSM-04` | Receipt with `policy_match = 0` | OBLIGATION_NOT_SATISFIED |
| `RSM-05` | Receipt with invalid signature | SIGNATURE_INVALID |
| `RSM-06` | Receipt without evidence_digest | NO_RECEIPT_NO_SHIP |
| `RSM-07` | Replay same inputs 10 times | All decision_digest identical |

---

## 12. Immutability Clause

This specification is **locked**. Changes require:

1. **Policy change run** (itself governed)
2. **Security review** (OBL-POLICY-REVIEW-SECURITY)
3. **Cryptographic audit** (if signature scheme changes)
4. **MAJOR version bump** (breaking change)

**No "emergency bypass" permitted.**

---

**END RSM-v0.1.0**
