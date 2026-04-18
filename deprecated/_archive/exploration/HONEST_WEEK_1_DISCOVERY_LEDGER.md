# Week 1 Discovery Ledger (Corrected, Tier-I Grade)

**Format:** FALSIFIABLE CLAIM | REQUIRED RECEIPTS | CURRENT STATUS | FALSIFIER

**Date:** 2026-01-29
**Ledger Version:** 2.0 (Corrected after input-identity audit)

---

## E1 — Governance Determinism (K5)

**Falsifiable Claim:**
For fixed (claim_id, policy_hash, ledger_digest, briefcase_digest, attestations_canonical), decision_digest is invariant across N ≥ 30 replays of the same input.

**Required Receipts:**
1. replay_manifest.json
   - claim_sha256
   - policy_sha256
   - ledger_sha256
   - briefcase_sha256
   - attestations_merkle (canonical)
   - environment_fingerprint (must be empty/pinned)

2. decision_digest_list.txt (30 lines, one per replay)

3. Proof: all 30 hashes identical OR any hash differs

**Current Status in Repo:**
- ❌ UNPROVEN (not falsified; test data incomplete)
- 3 decision records exist (runA, runB, runC) but they use DIFFERENT inputs:
  - claim_id differs (CLM-001, CLM-002, CLM-003)
  - policy_hash differs (f5d4c1f..., 9e06f4a..., 60268ce...)
  - ledger_digest differs (fc24ab1..., 0869951..., 80810ee...)
  - briefcase_digest differs (853d207..., 2d576b1..., fc01f4c...)
- These are not replays; these are three different governance decisions
- Cannot falsify determinism without identical inputs

**Falsifier:**
Same pinned inputs, but any two digests differ.

**Action to Resolve:**
Write replay_manifest.json + test_k5_determinism.py that:
- Pins one claim's inputs
- Runs mayor 30 times
- Emits digest_list.txt
- CI gate: all 30 match ✓ or fail

---

## E2 — Fail-Closed Default (K1)

**Falsifiable Claim:**
If a required receipt class is missing OR an attestor key is revoked, decision = NO_SHIP.

**Required Receipts:**
decision_record.json with fields:
- blocking_reasons (explicit enum: "missing class X", "revoked key Y", "invalid signature", etc.)
- decision (enum: "NO_SHIP" or "SHIP")

**Current Status in Repo:**
✅ **SUPPORTED by two independent test cases**

Evidence:
1. **Run A (Missing Receipt):**
   - blocking_reasons: ["Quorum not met for 'gdpr_consent_banner': missing classes ['LEGAL']"]
   - decision: NO_SHIP ✓

2. **Run B (Revoked Key):**
   - blocking_reasons: ['Revoked key: key-2025-12-legal-old (obligation: gdpr_consent_banner)']
   - decision: NO_SHIP ✓

Both explicitly demonstrate K1 enforcement (fail-closed default).

**Falsifier:**
Any claim with missing receipt OR revoked key produces decision = SHIP.

**Confidence:** HIGH (2/2 cases match expectation)

---

## E3 — Knowledge Intake (Mechanical, No Interpretation)

**Falsifiable Claim:**
Intake pipeline processes heterogeneous artifacts (LaTeX, Python, Markdown, JSON, etc.) through a uniform mechanical protocol (hash + manifest + metadata) without semantic interpretation or content-dependent branches.

**Required Receipts:**
bibliotheque_intake_manifest.json with schema:
```json
{
  "items": [
    {
      "path": string,
      "size_bytes": integer,
      "sha256": string,
      "mtime_epoch": integer (or null/excluded if not part of decision)
    }
  ]
}
```

**Current Status in Repo:**
✅ **SUPPORTED by manifest.json**

Evidence:
- 4 items processed: .tex, .py, .md, .md
- All 4 use identical schema: (path, size_bytes, sha256, mtime_epoch)
- No type-specific parsing observed
- manifest_sha256: `132f434c480dd811ed1a2555d04bac4a5b3fe4b39bf965bf16e60521e363a4cc`

Items:
1. REQ_001: `1f334917...` (22,043 bytes) ← LaTeX
2. REQ_002: `343bc6a4...` (10,791 bytes) ← Python
3. REQ_003: `92c56c9b...` (13,817 bytes) ← Markdown
4. REQ_004: `ef57ad8e...` (15,002 bytes) ← Markdown

**Falsifier:**
Intake requires type-specific parsing OR breaks on unsupported content type.

**Confidence:** HIGH (uniform treatment across 4 diverse types observed)

**Caveat:** mtime_epoch is present but should be excluded from decision gate (metadata only, not part of acceptance logic).

---

## E4 — Revocation Cascade (K4 + K3 + K1 Combination)

**Falsifiable Claim:**
When attestor key K is revoked:
1. K can no longer sign claims
2. Class C (which K belongs to) becomes missing from quorum
3. All pending decisions with C required default to NO_SHIP
4. This propagates until C is restored

**Required Receipts:**
1. key_registry.json (snapshots before/after revocation)
2. 5+ decision_records showing "missing class C → NO_SHIP" pattern
3. Incident-to-decision linkage (REQ_004 incidents pinned to specific decision_record.json files)

**Current Status in Repo:**
🟡 **PARTIALLY SUPPORTED (1 case, not full cascade)**

Evidence:
- Run B shows: Revoked key `key-2025-12-legal-old` → decision = NO_SHIP
- blocking_reasons: `['Revoked key: key-2025-12-legal-old (obligation: gdpr_consent_banner)']`

Gap:
- Only 1 decision shown with revocation
- No evidence of "cascade" (all pending decisions affected)
- REQ_004 incident log exists but not linked to decision records

**Falsifier:**
Revoked key still permits SHIP.

**Action to Resolve:**
1. Link REQ_004 incidents to decision_records
2. Show 3+ independent decisions all blocked by same revocation
3. Demonstrate "cascade" across multiple claims

---

## E5 — Constitutional Self-Reinforcement (Cross-Domain Coherence)

**Falsifiable Claim (Weak Form):**
Across multiple knowledge domains (math, code, research, incidents), governance decisions cite and enforce the same K-rules (K0–K9) consistently. New domains do not require exceptions.

**Required Receipts:**
1. decision_records corpus (10+ from 3+ domains)
2. rule_citation_matrix.json
   ```json
   {
     "domain": {
       "K0": count,
       "K1": count,
       ...
     }
   }
   ```
3. Entropy or coherence metric proving low variance across domains

**Current Status in Repo:**
🔴 **NOT FALSIFIABLE (no corpus analysis)**

Evidence available:
- 4 knowledge submissions (REQ_001-004) representing math, code, research, incidents
- 3 decision records (runA, runB, runC)
- Both use K0, K1, K3 rules

Missing:
- No corpus analysis
- No rule_citation_matrix
- No classifier script
- No explicit domain mapping

**Falsifier:**
New domain requires ad-hoc exception (e.g., "this rule doesn't apply in domain X").

**Action to Resolve:**
1. Create rule_citations field in decision_record.json
2. Write scripts/rule_citation_report.py
3. Input: decision_records/*
4. Output: rule_citation_matrix.json + entropy analysis
5. Gate: entropy(rule_distribution) < threshold for E5_supported

---

## Summary Table

| E | Claim | Status | Receipts | Action |
|---|-------|--------|----------|--------|
| **E1** | Determinism (K5) | 🔴 UNPROVEN | 3 different inputs | Create replay_manifest.json + test_k5_determinism.py |
| **E2** | Fail-Closed (K1) | ✅ SUPPORTED | 2 decision records | Maintain; no action needed |
| **E3** | Mechanical Intake | ✅ SUPPORTED | bibliotheque_manifest.json | Maintain; exclude mtime from gates |
| **E4** | Revocation Cascade | 🟡 PARTIAL | 1 revocation case | Link REQ_004 to decision_records; show 3+ cascade cases |
| **E5** | Self-Reinforcement | 🔴 NOT FALSIFIABLE | 4 submissions, no corpus | Create rule_citation_report.py + matrix |

---

## Constitutional Hygiene Fixes Applied

### Fix 1: Ban Soft Self-Attestation
**Before:** "E1 FALSIFIED by evidence shown"
**After:** "E1 UNPROVEN — requires replay_manifest input identity proof"

Replace all instances of "verified," "proved," "demonstrated" with:
- RECEIPTS: (specific file hash)
- STATUS: PASSED | FAILED
- INPUTS: (hashes of inputs)

### Fix 2: Input Identity Must Be Pinned Before Falsification
- Never claim falsification without proving input identity
- Always include comparative table of inputs when claiming same behavior across runs
- If inputs differ, conclusion status = "expected behavior" not "falsified"

### Fix 3: Corpus Before Inference
- No claims about patterns from N=1 or N=2 cases
- E5 requires N≥10 with classifier
- E4 requires N≥3 with incident linkage

---

## Corrected Status Assessment

**Tier I (Proven by Receipt):**
- ✅ E2: Fail-Closed behavior
- ✅ E3: Mechanical intake (with caveat: mtime handling)

**Tier II (Partially Proven, Need More Cases):**
- 🟡 E4: Revocation cascade (1 case; need 3+ with explicit cascade evidence)

**Tier III (Narrative Only, Not Falsifiable):**
- 🔴 E1: Determinism (requires replay_manifest + 30-iteration test)
- 🔴 E5: Self-Reinforcement (requires corpus + classifier)

---

## Lessons From This Audit

1. **Input identity is the foundation of falsification logic**
   - Never compare outputs without first proving inputs identical
   - Create replay_manifest.json early

2. **Narrative bias is real**
   - I claimed "Week 1 discovered determinism" then found evidence I thought supported it
   - Actual evidence was from different test cases (confusing variability with falsification)
   - Constitutional governance requires separating narrative from receipts

3. **Corpus analysis before pattern claims**
   - E5 ("self-reinforcement") is tempting as narrative but falsifiable only with corpus + classifier
   - Don't accept "4 domains agree" as proof without analyzing decision records from those domains

4. **Constitutional operations require receipts first**
   - "I found X" → provide receipt pointer
   - "X is stable" → provide metric timeline
   - "Culture emerged" → provide instrumentation

---

**This ledger is now PR-ready. It separates:**
- ✅ Tier I facts (E2, E3)
- 🟡 Tier II partial evidence (E4)
- 🔴 Tier III untested hypotheses (E1, E5)

Next phase: Build receipts for E1, E4, E5 rather than claiming them narrative.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
