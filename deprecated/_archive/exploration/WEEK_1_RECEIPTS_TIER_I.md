# Week 1 Discoveries: Tier I Receipts

**Date Generated:** 2026-01-29
**Status:** Falsifiable claims with hard evidence (receipts)
**Format:** Facts only; no narrative interpretation

---

## Discovery E1: Governance Convergence (Determinism)

### Falsifiable Claim
For fixed (claim_id, policy_hash, attestation_set), the decision_digest is invariant across independent runs.

### Receipts

**Run A (Missing Receipts - K1 Test)**
- Run directory: `oracle_town/runs/runA_no_ship_missing_receipts/`
- Decision record: `oracle_town/runs/runA_no_ship_missing_receipts/decision_record.json`
- decision_digest: `sha256:c6f45ad4ab4bc2a01988d7caddc181196e4b5ba4495aebfea6fff52e8a20fceb`
- decision: `NO_SHIP`
- policy_hash: `sha256:f5d4c1f28b132a1ff78fa32577a83399f2163bd901f17c13a41ced6a436e66a4`
- blocking_reasons: `["Quorum not met for 'gdpr_consent_banner': missing classes ['LEGAL']"]`

**Run B (Fake Attestor - K0 Test)**
- Run directory: `oracle_town/runs/runB_no_ship_fake_attestor/`
- decision_digest: `sha256:0dacdcade3eaca123f95f33bbab8c04a7fcfd6cb42c596ca401010fff9a2e755`
- decision: `NO_SHIP`
- blocking_reasons: `['Revoked key: key-2025-12-legal-old (obligation: gdpr_consent_banner)']`

**Run C (Valid Quorum - K3 Test)**
- Run directory: `oracle_town/runs/runC_ship_quorum_valid/`
- decision_digest: `sha256:91cc5f08bd7f9cbaa62e15acc9efbbd3059c2c390b26a9316222374ef90b7a98`
- decision: `SHIP`
- blocking_reasons: `[]`

### Input Pinning Analysis

**Run A inputs:**
- claim_id: `CLM-001`
- policy_hash: `sha256:f5d4c1f28b132a1ff78fa32577a83399f2163bd901f17c13a41ced6a436e66a4`
- ledger_digest: `sha256:fc24ab15d1657dbd9e43ac02cb2507c0a9d48d9e3c14672ecbec99d03a7da89c`
- briefcase_digest: `sha256:853d20754ef6cfbc6a28bad9a8e7034539afd7f77a6dfeda02daf15bcc43ae32`
- decision_digest: `sha256:c6f45ad4ab4bc2a01988d7caddc181196e4b5ba4495aebfea6fff52e8a20fceb`

**Run B inputs:**
- claim_id: `CLM-002` ← **DIFFERENT**
- policy_hash: `sha256:9e06f4a0aa09eb00d50c48c6a70817ac5cdfbd63df2831a55bda0a7569ceb6f6` ← **DIFFERENT**
- ledger_digest: `sha256:086995141bf8304f159a1c480fdbb0c370756e079bf6682e47edd7bae5e9318e` ← **DIFFERENT**
- briefcase_digest: `sha256:2d576b185d977a9219461f5f1e2c6de72da730d72e9d9c75de26830d060f5b0f` ← **DIFFERENT**
- decision_digest: `sha256:0dacdcade3eaca123f95f33bbab8c04a7fcfd6cb42c596ca401010fff9a2e755`

**Run C inputs:**
- claim_id: `CLM-003` ← **DIFFERENT**
- policy_hash: `sha256:60268ce4a55f936ab1b537f165e877ee0aaa68835c0dbc62c164a29b8b6d15dc` ← **DIFFERENT**
- ledger_digest: `sha256:80810ee8b5eba5a05be52b001eeac15cd1e84859e8d6d2ef5e4051578f3e459e` ← **DIFFERENT**
- briefcase_digest: `sha256:fc01f4cf6293dce9d4a5e8e3b1aa9ba9250d2ffb8b41256894913cabf54a70bb` ← **DIFFERENT**
- decision_digest: `sha256:91cc5f08bd7f9cbaa62e15acc9efbbd3059c2c390b26a9316222374ef90b7a98`

### Status of E1 Claim

**Observation:** All three runs use COMPLETELY DIFFERENT inputs (different claim_ids, policies, ledger states, and briefcase digests).

**Correct assessment:** 🔴 **FALSIFICATION INVALID** (logical error on my part)

**Why the previous conclusion was wrong:**
- I claimed: "3 runs show different digests → determinism falsified"
- This is only valid if inputs are identical
- These inputs are NOT identical; they're completely different test cases:
  - Run A tests K1 fail-closed (missing receipts)
  - Run B tests K0 authority (fake attestor)
  - Run C tests K3 quorum (valid case)
- Different inputs → different outputs = expected behavior, proves nothing about determinism

**Correct conclusion:** E1 is **UNPROVEN** (not falsified)
- Expected K5 test: Run claim X 30 times with identical (claim_id, policy_hash, ledger_digest, briefcase_digest)
- All 30 decision_digests should be identical
- Currently available data does NOT test this

**Required to prove/falsify E1:**
- Create replay_manifest.json pinning identical inputs
- Run mayor 30+ times with those inputs
- All digests identical → K5 verified ✅
- Any digest differs → K5 falsified ❌

---

## Discovery E2: Fail-Closed (K1)

### Falsifiable Claim
If any required receipt is missing or invalid, decision = NO_SHIP.

### Receipts

**Run A Evidence (Missing Receipts)**
- Claim: `gdpr_consent_banner`
- Missing class: `LEGAL`
- Decision: `NO_SHIP` ✅
- Blocking reason: `Quorum not met for 'gdpr_consent_banner': missing classes ['LEGAL']`

**Run B Evidence (Invalid/Revoked Attestor)**
- Claim: `gdpr_consent_banner`
- Invalid attestor: `key-2025-12-legal-old`
- Decision: `NO_SHIP` ✅
- Blocking reason: `Revoked key: key-2025-12-legal-old (obligation: gdpr_consent_banner)`

### Status of E2 Claim
✅ **SUPPORTED by evidence**

Both missing receipts (Run A) and invalid attestations (Run B) consistently produce NO_SHIP decisions. Fail-closed behavior verified.

---

## Discovery E3: Knowledge Without Understanding

### Falsifiable Claim
Intake pipeline processes heterogeneous artifacts using uniform mechanical protocol (hash+manifest) without interpretation.

### Receipts

**Manifest File:** `receipts/bibliotheque_intake_manifest.json`
- Manifest SHA256: `132f434c480dd811ed1a2555d04bac4a5b3fe4b39bf965bf16e60521e363a4cc`
- Generated at: `2026-01-29T17:34:53.266756+00:00Z`

**Item 1: Mathematics**
- Path: `REQ_001/pluginRIEMANN_V8.0_FINAL.tex`
- Size: `22,043 bytes`
- SHA256: `1f3349175249babc6e1c3b91b2d55ff22a549a25fe9c7bc1340436a246fbb9af`
- Type: `.tex` (LaTeX)

**Item 2: Code**
- Path: `REQ_002/legacy_quorum_v1_historical.py`
- Size: `10,791 bytes`
- SHA256: `343bc6a4ac7a24201c76122ca8f140ebc5f2f0ff41be2b5639f4c502442bab77`
- Type: `.py` (Python)

**Item 3: Research**
- Path: `REQ_003/byzantine_quorum_foundations.md`
- Size: `13,817 bytes`
- SHA256: `92c56c9b1cbdebf011145e39d93e5883e1d1162ab5bc98bf8db0cc9d79b260f2`
- Type: `.md` (Markdown)

**Item 4: Incidents**
- Path: `REQ_004/attestation_failures_incident_log.md`
- Size: `15,002 bytes`
- SHA256: `ef57ad8e90d67684a0b7cdce4718eae46b38fc555a3b3ff2321e66d3547649a1`
- Type: `.md` (Markdown)

**Total Knowledge:** 61,653 bytes across 4 heterogeneous types

### Status of E3 Claim
✅ **SUPPORTED by evidence**

All 4 items processed through identical manifest schema (sha256, size_bytes, path, mtime_epoch) regardless of content type. No type-specific parsing detected. Mechanical hashing only.

---

## Discovery E4: Revocation Cascade

### Falsifiable Claim
When attestor key is revoked, that class becomes missing from quorum → NO_SHIP propagates.

### Receipts

**Run B Evidence (Revocation Cascade)**
- Revoked key: `key-2025-12-legal-old`
- System response: Blocking reason = `Revoked key: key-2025-12-legal-old (obligation: gdpr_consent_banner)`
- Class affected: `LEGAL` (inferred from key name + blocking obligation)
- Decision: `NO_SHIP` ✅

### Status of E4 Claim
🟡 **PARTIALLY SUPPORTED**

Evidence shows revoked key blocks a decision. Does NOT yet show:
1. That this cascades to ALL pending decisions
2. That missing class causes quorum failure (Run B shows key revocation, not class quorum failure explicitly)
3. Pattern across multiple incidents

**Required to prove E4:**
- Show 3+ separate revocation incidents with consistent "missing class → NO_SHIP" pattern
- Requires REQ_004 incident data with decision records pinned to each incident

---

## Discovery E5: Constitutional Self-Reinforcement

### Falsifiable Claim (Weak Form)
Across multiple domains, decisions cite the same K-rules consistently.

### Status of E5 Claim
🔴 **NOT FALSIFIABLE from current evidence**

Current evidence shows:
- 4 knowledge submissions receipted (math, code, research, incidents)
- 3 decision records from runs (all cite K1, K3, K0, K7 rules)

But does NOT show:
- Cross-domain decision record corpus
- Rule citation frequency per domain
- Classifier output: "which K-rules invoked per domain"

**Required to prove E5:**
- Decision record corpus with 10+ decisions across 3+ domains
- Analysis: which K-rules cited per decision per domain
- Falsifier test: Does a new domain require new exceptions?

---

## Summary: Week 1 Evidence Status

| Discovery | Claim | Evidence | Status |
|-----------|-------|----------|--------|
| **E1** | Determinism (30/30 identical) | 3 runs with different inputs (CLM-001, CLM-002, CLM-003 + different policies) | 🔴 UNPROVEN (not falsified; test invalid) |
| **E2** | Fail-Closed (missing receipts → NO_SHIP) | Run A, Run B both NO_SHIP | ✅ SUPPORTED |
| **E3** | Mechanical intake (no interpretation) | 4-item manifest, identical schema | ✅ SUPPORTED |
| **E4** | Revocation cascade | 1 revocation instance | 🟡 PARTIAL |
| **E5** | Constitutional self-reinforcement | 4 submissions, no decision corpus | 🔴 NOT FALSIFIABLE |

---

## Critical Red Flag: E1 Audit Error (Self-Correction)

**The claim "E1 FALSIFIED"** in my initial audit was logically invalid. Here's what I did wrong:

1. I observed three different digests across three runs
2. I concluded: "Different digests = determinism falsified"
3. **This was wrong** because I didn't verify the inputs were identical

**Actual situation:**
- Run A (CLM-001 with policy `f5d4c1f...`): digest `c6f45ad4...`
- Run B (CLM-002 with policy `9e06f4a...`): digest `0dacdcad...`
- Run C (CLM-003 with policy `60268ce...`): digest `91cc5f0...`

These are THREE DIFFERENT claims with THREE DIFFERENT policies. Different outputs are expected.

**Honest correction:** E1 is **UNPROVEN**, not falsified. The test I performed was invalid for testing determinism. A valid determinism test requires identical inputs (claim, policy, ledger, attestations) replayed 30 times.

**What this reveals:** I was vulnerable to narrative bias—I had written that Week 1 "discovered determinism," so when I saw three different digests, I rationalized them as proof rather than asking "are the inputs actually identical?"

This is exactly the constitutional check you flagged: system-authored claims need receipts, not narrative confidence.

---

## What Would Make This Tier I

To prove E1:
- Provide a replay_manifest.json pinning inputs (claim_id, policy_hash, ledger_hash, briefcase_hash)
- Run claim 30 times
- Show all 30 decision_digests are identical
- Git commit the replay results

To prove E4 + E5:
- REQ_004 incident log with 5+ incident records
- Each pinned to a decision_record.json
- Corpus analysis showing rule citations per domain

---

**This is the honest ledger you asked for. The Week 1 narrative was strong, but receipts are partial.**

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
