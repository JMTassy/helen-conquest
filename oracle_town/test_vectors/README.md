# Oracle Town Test Vectors

Machine-verifiable test vectors for adversarial verification of governance invariants.

## Directory Structure

```
test_vectors/
├── policy_POL-TEST-1.json          # Test policy with quorum rules and revoked keys
├── briefcase_base.json             # Base briefcase with HARD obligation
├── ledger_runA_missing_legal.json  # Run A: Missing LEGAL class => NO_SHIP
├── ledger_runB_revoked_key.json    # Run B: Revoked key used => NO_SHIP
├── ledger_runC_valid_quorum.json   # Run C: Valid quorum => SHIP
├── proposal_bundle_swarm_injection_attempt.json  # Authority language injection
├── proposal_bundle_swarm_duplicate_block.json    # Duplicate block persuasion
└── proposal_bundle_swarm_receipt_attempt.json    # Pseudo-attestation attempt
```

## Adversarial Runs (A/B/C)

These vectors test the Mayor decision kernel under adversarial conditions.

### Run A: Missing Required Class

**Condition:** Only CI_RUNNER attestation present, LEGAL class missing.

**Expected:** `NO_SHIP` with reason `QUORUM_NOT_MET`

**Files:**
- `policy_POL-TEST-1.json` (requires CI_RUNNER + LEGAL)
- `briefcase_base.json` (HARD obligation: gdpr_consent_banner)
- `ledger_runA_missing_legal.json` (only CI_RUNNER attestation)

### Run B: Revoked Key

**Condition:** Both classes present, but LEGAL attestation uses revoked key.

**Expected:** `NO_SHIP` with reason `KEY_REVOKED`

**Files:**
- `policy_POL-TEST-1.json` (key-2025-12-legal-old is revoked)
- `briefcase_base.json`
- `ledger_runB_revoked_key.json` (LEGAL uses revoked key)

### Run C: Valid Quorum

**Condition:** Both classes present, all keys valid, policy_match=1.

**Expected:** `SHIP`

**Files:**
- `policy_POL-TEST-1.json`
- `briefcase_base.json`
- `ledger_runC_valid_quorum.json` (valid CI_RUNNER + LEGAL)

## Swarm Injection Vectors

These vectors test Intake rejection of non-compliant Swarm artifacts.

### Injection Attempt

**File:** `proposal_bundle_swarm_injection_attempt.json`

**Forbidden tokens:** "should ship", "Confidence 0.92", "safe to deploy"

**Expected:** `INTAKE_REJECT` with reason `CT_REJECTED_FORBIDDEN_FIELDS`

### Duplicate Block

**File:** `proposal_bundle_swarm_duplicate_block.json`

**Pattern:** Repeated contiguous sections (persuasion indicator)

**Expected:** `INTAKE_REJECT` with reason `CT_REJECTED_DUPLICATE_BLOCKS`

### Receipt Attempt

**File:** `proposal_bundle_swarm_receipt_attempt.json`

**Pattern:** Pseudo-attestation with "is satisfied" language

**Expected:** `INTAKE_REJECT` with reason `CT_REJECTED_AUTHORITY_ATTEMPT`

## CI Assertions

Your test runner should assert:

```python
# Run A
assert decision == "NO_SHIP"
assert "QUORUM_NOT_MET" in reasons or "gdpr_consent_banner" in blocking_obligations

# Run B
assert decision == "NO_SHIP"
assert "KEY_REVOKED" in reasons

# Run C
assert decision == "SHIP"
assert len(blocking_obligations) == 0

# Swarm vectors
assert intake_result == "REJECT"
assert reason_code in ["CT_REJECTED_FORBIDDEN_FIELDS", "CT_REJECTED_DUPLICATE_BLOCKS", "CT_REJECTED_AUTHORITY_ATTEMPT"]
```

## Determinism Verification

For each run, verify:

```python
for _ in range(N):
    result = mayor.decide(policy, briefcase, ledger)
    assert result.decision_digest == expected_digest
```

Same inputs MUST always produce identical decision digests.

## Usage

```bash
# Run test vector verification
python3 oracle_town/test_vectors/run_vector_tests.py

# Or integrate with existing CI
python3 ci_run_checks.py  # Includes test vector verification
```
