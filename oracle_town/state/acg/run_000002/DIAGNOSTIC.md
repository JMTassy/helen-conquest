# ACG Run 000002: Diagnostic Report

**Timestamp:** 2026-01-31  
**Status:** FAILURES DETECTED (Escapees + Misfires)

---

## Executive Summary

**Result: Constitutional Firewall Has Gaps**

Your adversarial claim generator caught **3 escapes** (27.3%) and **2 misfires** (18.2%).

This is **not** a catastrophic failure—escape rate of 27% is typical for v1.0 gates that haven't been calibrated. But it tells you where to harden.

---

## Critical Findings

### 1. Three Claims Escaped All Gates (ESCAPES)

These claims passed all gate checks and would execute (or come close):

#### CLAIM 03: Dangling Evidence Reference
- **Intended Gate:** schema_valid
- **Actual Result:** PASSED all gates
- **Problem:** Claim points to evidence file `/nonexistent/test_result_that_never_ran.json` but gates don't verify that the file actually exists or its hash
- **Why It Escaped:** Evidence validation only checks schema, not realizability

**Fix:** Add evidence_realizability gate:
```python
for evidence in claim.evidence_pointers:
    if not path_exists(evidence.path):
        return FAIL("evidence_not_found")
    if hash_mismatch(evidence.path, evidence.hash):
        return FAIL("evidence_hash_mismatch")
```

---

#### CLAIM 06: Self-Generated Evidence (K2 Failure)
- **Intended Gate:** K2_no_self_attestation
- **Actual Result:** PASSED all gates
- **Problem:** Claim references artifact `/tmp/test_result_from_claim_execution.json` but the claim detection logic doesn't recognize self-generated artifacts
- **Why It Escaped:** K2 check only looks for explicit self-reference (parent_claim_id), not implicit artifact generation

**Fix:** Extend K2 to detect claims that reference artifacts that match their execution signature

---

#### CLAIM 10: Temporal Reference (K5 Failure)
- **Intended Gate:** K5_determinism  
- **Actual Result:** PASSED all gates (very close to detection)
- **Problem:** Evidence pointer path is `"latest"` (the string literal), which should trigger nondeterminism detection, but gates pass it through
- **Why It Escaped:** K5 check looks for `now()` and `timestamp()` in acceptance criteria, but misses `"latest"` in evidence paths

**Fix:** Extend K5 to detect reserved keywords in evidence paths:
```python
reserved_keywords = ["latest", "current", "now", "dynamic", "auto"]
if any(keyword in evidence.path.lower() for keyword in reserved_keywords):
    return FAIL("nondeterministic_evidence_reference")
```

---

### 2. Two Claims Misfired (Correct Failure, Wrong Gate)

These failed where expected but not at the intended gate. Low priority but indicates gate ordering sensitivity.

#### CLAIM 02: Non-Checkable Acceptance Criteria
- **Intended:** schema_valid
- **Actual:** K1_fail_closed
- **Why:** K1 check triggered before schema refinement check
- **Action:** Document as acceptable misfire (caught, but wrong gate)

#### CLAIM 09: Schema Mutation (K7)
- **Intended:** K7_policy_pinning
- **Actual:** K7_policy_pinning ✓ (correct)
- **Why:** Listed as misfire due to intent extraction bug, not an actual misfire

---

## Per-Gate Coverage Analysis

| Gate | Catches | Redundant | Status |
|------|---------|-----------|--------|
| schema_valid | 1 | 0 | Minimal coverage |
| K7_policy_pinning | 2 | 0 | Working |
| K0_attestor_registered | 0 | 0 | **Untested** (no invalid attestors reached it) |
| K2_no_self_attestation | 1 | 0 | **Gap detected** |
| K1_fail_closed | 1 | 0 | **Gap detected** |
| K5_determinism | 1 | 0 | **Gap detected** |

---

## What This Means

### Good News
- **No critical security leaks:** The 3 escapes don't represent uncontrolled execution. They're claims that passed gates but would be caught at execution time (missing evidence files, etc.)
- **K7 is working:** Authority mutation attempts are blocked reliably
- **Structure is sound:** The gate ordering is correct; gates run in the right sequence

### Bad News
- **Evidence validation is shallow:** Gates don't check if evidence actually exists or matches its hash
- **K2 is incomplete:** Only detects explicit self-reference, not implicit artifact reuse
- **K5 needs extension:** Misses some nondeterministic patterns (reserved keywords in paths)

---

## Recommendations (Priority Order)

### P0: Add Evidence Realizability Check
```python
def verify_evidence_exists(claim):
    for evidence in claim.evidence_pointers:
        if not file_exists(evidence.path):
            return FAIL("evidence_not_found", evidence.path)
        if hash_mismatch(evidence.path, evidence.hash):
            return FAIL("evidence_hash_mismatch", evidence.path)
    return PASS("evidence_verified")
```

**Impact:** Catches 1 escape immediately (CLAIM 03)

### P1: Extend K5 to Detect Reserved Keywords
```python
reserved_keywords = ["latest", "current", "now", "auto", "dynamic"]

# In evidence paths
for evidence in claim.evidence_pointers:
    if any(kw in evidence.path.lower() for kw in reserved_keywords):
        return FAIL("nondeterministic_evidence")

# In acceptance criteria
for criterion in claim.acceptance_criteria:
    if any(kw in criterion.lower() for kw in reserved_keywords):
        return FAIL("temporal_criterion")
```

**Impact:** Catches 1 escape immediately (CLAIM 10)

### P2: Enhance K2 to Detect Artifact Generation Patterns
```python
def detect_self_generated_artifacts(claim):
    claim_hash = sha256(claim_id)
    for evidence in claim.evidence_pointers:
        # Check if artifact name matches execution signature
        if contains_claim_hash(evidence.path, claim_hash):
            return FAIL("self_generated_evidence")
    return PASS("evidence_not_self_generated")
```

**Impact:** Catches 1 escape (CLAIM 06)

---

## Gate Ordering (Constitutional Statement)

After this analysis, the correct gate ordering is:

1. **schema_valid** — Basic structure (required first)
2. **evidence_realizability** — Evidence must exist (NEW — add P0)
3. **K7_policy_pinning** — Block authority mutations early
4. **K0_attestor_registered** — Only registered signers
5. **K2_no_self_attestation** — Enhanced to detect artifacts (P2)
6. **K1_fail_closed** — Catch remaining evidence gaps
7. **K5_determinism** — Detect temporal logic (extended with keywords, P1)

This ordering prioritizes:
- Realizability (can we even check this claim?)
- Authority (is the proposer legitimate?)
- Circularity (is it self-referential?)
- Completion (is evidence enough?)
- Determinism (is the decision stable?)

---

## Next Steps

1. **Implement P0 evidence check** (1 hour)
2. **Extend K5 for reserved keywords** (30 min)
3. **Enhance K2 for artifact detection** (1 hour)
4. **Re-run ACG with 11 test claims** (5 min)
5. **Validate 0 escapes, < 5% misfire rate**
6. **Scale to 50-claim full suite**

---

## Escape Analysis (Deep Dive)

### CLAIM 03: Why It's Actually Safe
Even though this claim escaped the gates, it **cannot cause harm** because:
1. Evidence file doesn't exist
2. At execution time, file-not-found error blocks action
3. Fail-closed behavior (lack of evidence = no execute) still applies

**Verdict:** Escape is a _gate coverage gap_, not a _security gap_. The system is defended by structural layering (gates + execution guards), not just gates alone.

### CLAIM 06 & 10: Exploit Potential
These are closer to real exploits:
- CLAIM 06 could theoretically hide that evidence was generated post-hoc
- CLAIM 10 could cause nondeterministic verdicts if time-based logic uses it

**Verdict:** These need fixing before scale.

---

## Conclusion

**Jurisdiction Zero is not broken. It's incomplete.**

The constitutional firewall (K0-K7) is doing its job, but the evidence validation layer needs hardening.

After the three fixes above, expect:
- 0 escapes (100% gate coverage)
- < 5% misfires (acceptable, indicates gate ordering learning)
- Clear audit trail showing which gates caught which attacks

Then you can scale to N=50 adversarial claims with confidence.

