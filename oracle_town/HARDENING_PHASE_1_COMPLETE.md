# Oracle Town: Hardening Phase 1 Complete

**Date:** 2026-01-23
**Status:** ✅ STRUCTURAL INVARIANTS LOCKED
**Next:** Cryptographic signature verification (Phase 2)

---

## What Was Fixed (Critical Correctness Issues)

### Issue 1: Self-Hashing Digests ✅ FIXED

**Problem:**
```python
ledger["ledger_digest"] = compute_digest(ledger)  # WRONG: hashes itself
```

**Solution:**
```python
ledger["ledger_digest"] = compute_digest(ledger, exclude_field="ledger_digest")
```

**Rule:** `digest = sha256(canonical(obj WITHOUT its digest field))`

**Verification:**
- ✅ All three runs regenerated with correct digest computation
- ✅ Determinism test: 200 iterations → 1 unique digest

---

### Issue 2: CT Boundary Digest Not Written Back ✅ FIXED

**Problem:**
Intake computed `ct_boundary_digest`, but saved manifest had `""`.

**Solution:**
```python
# Compute digest
intake_decision = guard.evaluate(ct_bundle, ct_manifest)

# Write back to manifest
ct_manifest["ct_boundary_digest"] = intake_decision.ct_boundary_digest

# Then write file
write_json(f"{run_dir}/ct_run_manifest.json", ct_manifest)
```

**Verification:**
```
runA: manifest digest == hashes digest ✅
runB: manifest digest == hashes digest ✅
runC: manifest digest == hashes digest ✅
```

---

### Issue 3: Quorum Not Explicit in Briefcase ✅ FIXED

**Problem:**
Mayor was inferring quorum from policy (ambiguous).

**Solution:**
Briefcase obligations now include:
```json
{
  "name": "gdpr_consent_banner",
  "severity": "HARD",
  "required_attestor_classes": ["CI_RUNNER", "LEGAL"],
  "min_quorum": 2,
  "required_evidence": [...]
}
```

**Mayor updated:**
```python
# Read quorum from obligation (not policy)
required_classes = obligation.required_attestor_classes
min_quorum = obligation.min_quorum
```

**Verification:**
- ✅ Run A: Missing LEGAL class → NO_SHIP (quorum not met)
- ✅ Run B: Revoked key → NO_SHIP (revoked key detected)
- ✅ Run C: CI_RUNNER + LEGAL valid → SHIP

---

## Structural Invariants Now Locked

| ID | Invariant | Test | Status |
|----|-----------|------|--------|
| **S1** | No self-hashing digests | 200 iterations → 1 digest | ✅ |
| **S2** | CT manifest internally consistent | All 3 runs verified | ✅ |
| **S3** | Quorum explicit (no inference) | Mayor reads from briefcase | ✅ |
| **S4** | Deterministic canonicalization | Same inputs → same hash | ✅ |

---

## Current Test Results

### Determinism Gate (200 Iterations)
```
unique_digests= 1
digest= sha256:782f06183a985ecf9c8d9a0bfb0d3f6524783c8a2636d7f2c3faa29c7e08ee3a
```
✅ **PASS** (deterministic)

### Adversarial Runs

**Run A: Missing Receipts**
```
Decision: NO_SHIP
Blocking Reason: "Quorum not met for 'gdpr_consent_banner': missing classes ['LEGAL']"
Decision Digest: sha256:d33ce1184afd5fcdd5628040b0dff7e80535d6edc02ab809bbb6d191ac612f5d
```
✅ **PASS** (quorum-by-class enforced)

**Run B: Revoked Key**
```
Decision: NO_SHIP
Blocking Reason: "Revoked key: key-2025-12-legal-old (obligation: gdpr_consent_banner)"
Decision Digest: sha256:97403b14fb2cf114e49ca2fda8c638a8a6a7c3ca06c79069b0e01b3e50b7ed57
```
✅ **PASS** (revocation enforced)

**Run C: Valid Quorum**
```
Decision: SHIP
Blocking Reasons: []
Decision Digest: sha256:74ef94c383a3dfffc3699bf01b159b28c7b7db0c4e844b23a1c9eea8edcdb2c7
```
✅ **PASS** (correct governance flow)

---

## What This Proves (So Far)

1. **Digest soundness:** Objects never hash themselves (self-reference bug fixed)
2. **Internal consistency:** All artifacts in run folders are consistent
3. **Explicit quorum:** Mayor reads quorum from briefcase (no inference)
4. **Determinism:** 200 iterations → identical digest

---

## What's Still Missing (Phase 2)

### Critical: Cryptographic Signature Verification

**Current state:**
```json
"signature": "ed25519:valid_signature_ci"  // PLACEHOLDER (not verified)
```

**Required:**
1. ✅ Public key registry (`oracle_town/keys/public_keys.json`)
2. ✅ Mayor signature verification (Ed25519)
3. ✅ Fail-closed on:
   - Key not found
   - Key revoked
   - Signature invalid
   - Policy hash mismatch

**Skeptic attack:**
> "Those ed25519:valid_signature_* strings are placeholders. You didn't verify anything."

**Response after Phase 2:**
> "Mayor verifies every Ed25519 signature against a public key registry. Invalid signatures → NO_SHIP. Here's the code."

---

## Phase 2 Checklist (Next Steps)

### STEP 1: Create Public Key Registry

```bash
mkdir -p oracle_town/keys
```

```json
// oracle_town/keys/public_keys.json
{
  "key-2026-01-ci": "ed25519:<base64_public_key>",
  "key-2026-01-legal": "ed25519:<base64_public_key>",
  "key-2025-12-legal-old": "ed25519:<base64_public_key_revoked>"
}
```

### STEP 2: Update Mayor to Verify Signatures

Add to `mayor_rsm.py`:
```python
def _verify_attestation_signature(self, attestation: Attestation, public_keys: Dict) -> bool:
    """
    Verify Ed25519 signature.

    Returns:
        True if signature valid, False otherwise
    """
    # Build canonical message
    message = canonical_json({
        "run_id": attestation.run_id,
        "claim_id": attestation.claim_id,
        "obligation_name": attestation.obligation_name,
        "attestor_id": attestation.attestor_id,
        "attestor_class": attestation.attestor_class,
        "policy_hash": attestation.policy_hash,
        "evidence_digest": attestation.evidence_digest,
        "policy_match": attestation.policy_match
    })

    # Get public key
    public_key_str = public_keys.get(attestation.signing_key_id)
    if not public_key_str:
        return False  # Key not found → invalid

    # Verify signature (using nacl.signing or cryptography)
    # ... verification code ...

    return signature_valid
```

### STEP 3: Enforce in Constitutional Rules

In `_apply_constitutional_rules`:
```python
# NEW: Rule 1.5 — Signature verification
for att in attestations:
    if not self._verify_attestation_signature(att, public_keys):
        blocking_reasons.append(
            f"Invalid signature: {att.attestation_id} (key: {att.signing_key_id})"
        )

if blocking_reasons:
    return ("NO_SHIP", blocking_reasons)
```

### STEP 4: Update Adversarial Runs with Real Signatures

Generate real Ed25519 key pairs and sign canonical messages.

---

## Acceptance Criteria for Phase 2

When Phase 2 is complete, all three commands must pass:

```bash
oracle-town cli replay oracle_town/runs/runA_no_ship_missing_receipts
# Expected: NO_SHIP (quorum not met)

oracle-town cli replay oracle_town/runs/runB_no_ship_fake_attestor
# Expected: NO_SHIP (invalid signature OR revoked key)

oracle-town cli replay oracle_town/runs/runC_ship_quorum_valid
# Expected: SHIP (all signatures valid, quorum met)
```

And:
- Repeated runs → identical digests
- Changing signature → verdict flips

---

## Summary

**Phase 1 (Complete):** Structural invariants locked
- ✅ Digest soundness (no self-hashing)
- ✅ Internal consistency (CT manifest)
- ✅ Explicit quorum (no inference)
- ✅ Determinism (200 iterations verified)

**Phase 2 (Next):** Cryptographic hardening
- ⏳ Public key registry
- ⏳ Ed25519 signature verification
- ⏳ Fail-closed on invalid signatures
- ⏳ Real signatures in adversarial runs

**When done:** The system will be cryptographically verifiable, not just structurally sound.

---

**END HARDENING_PHASE_1_COMPLETE.md**
