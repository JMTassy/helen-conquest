# Constitutional Governance Dashboard
## Oracle Town — Real-Time Evidence Status

**Last Updated:** 2026-01-29 19:45 UTC
**Format:** CLAIM | RECEIPT | STATUS | FALSIFIER | ACTION GATE

---

## TIER I: PROVEN (Receipts + Tests Pass)

### ✅ K1 Fail-Closed Default

| Component | Receipt | Status |
|-----------|---------|--------|
| **Claim** | If receipt missing OR attestor invalid → decision = NO_SHIP |
| **Receipt Location** | `oracle_town/runs/runA_no_ship_missing_receipts/decision_record.json` |
| **Evidence** | blocking_reasons: `["Quorum not met for 'gdpr_consent_banner': missing classes ['LEGAL']"]` → decision: `NO_SHIP` ✓ |
| **Receipt Location** | `oracle_town/runs/runB_no_ship_fake_attestor/decision_record.json` |
| **Evidence** | blocking_reasons: `['Revoked key: key-2025-12-legal-old (obligation: gdpr_consent_banner)']` → decision: `NO_SHIP` ✓ |
| **Test Cases** | 2/2 passing |
| **Falsifier** | Any missing receipt case → SHIP |
| **Status** | ✅ PROVEN |
| **Action Gate** | MAINTAIN (no further action needed) |

---

### ✅ E3: Mechanical Knowledge Intake (No Interpretation)

| Component | Receipt | Status |
|-----------|---------|--------|
| **Claim** | Intake processes heterogeneous types (.tex, .py, .md, .md) through uniform mechanical schema (hash+manifest) without semantic interpretation |
| **Receipt Location** | `receipts/bibliotheque_intake_manifest.json` |
| **Manifest Hash** | `132f434c480dd811ed1a2555d04bac4a5b3fe4b39bf965bf16e60521e363a4cc` |
| **Items Processed** | 4 (math/code/research/incidents) |
| **Schema** | Identical for all: (path, size_bytes, sha256, mtime_epoch) |
| **REQ_001** | 22,043 bytes, `1f334917...` ← LaTeX |
| **REQ_002** | 10,791 bytes, `343bc6a4...` ← Python |
| **REQ_003** | 13,817 bytes, `92c56c9b...` ← Markdown |
| **REQ_004** | 15,002 bytes, `ef57ad8e...` ← Markdown |
| **Falsifier** | Type-specific parsing required OR break on unsupported type |
| **Status** | ✅ PROVEN |
| **Action Gate** | MAINTAIN (caveat: exclude mtime_epoch from decision gates) |

---

## TIER II: PARTIAL (Some Evidence, Need More Cases)

### 🟡 E4: Revocation Cascade (K4 + K3 + K1)

| Component | Receipt | Status |
|-----------|---------|--------|
| **Claim** | When attestor key revoked → class missing from quorum → ALL pending decisions default to NO_SHIP (cascade effect) |
| **Evidence Count** | 1/3 required |
| **Receipt Location** | `oracle_town/runs/runB_no_ship_fake_attestor/decision_record.json` |
| **Case 1** | Revoked key `key-2025-12-legal-old` → decision: `NO_SHIP` ✓ |
| **Gap** | Does NOT show cascade to multiple pending decisions; only shows 1 decision blocked |
| **Required** | 3+ independent decisions all blocked by same revocation, with timestamps showing "pending at time of revocation" |
| **Falsifier** | Revoked key still permits SHIP in any subsequent decision |
| **Status** | 🟡 PARTIAL (1 case, need cascade evidence) |
| **Action Gate** | Link REQ_004 incidents to decision_records; show 3+ cascade cases |

---

## TIER III: NARRATIVE ONLY (Not Yet Falsifiable)

### 🔴 K5: Determinism (Governance Convergence)

| Component | Receipt | Status |
|-----------|---------|--------|
| **Claim** | For fixed (claim_id, policy_hash, ledger_digest, briefcase_digest, attestations_canonical), decision_digest invariant across 30+ replays |
| **Current Data** | 3 decision records exist (runA, runB, runC) BUT inputs all different |
| **Run A** | claim_id: CLM-001, policy: f5d4c1f..., digest: c6f45ad4... |
| **Run B** | claim_id: CLM-002, policy: 9e06f4a..., digest: 0dacdcad... |
| **Run C** | claim_id: CLM-003, policy: 60268ce..., digest: 91cc5f08... |
| **Problem** | Different inputs → different outputs (expected); does NOT test determinism |
| **Required** | replay_manifest.json pinning identical inputs + 30-iteration test |
| **Falsifier** | Same pinned inputs, any two digests differ |
| **Status** | 🔴 UNPROVEN (not falsified; test invalid) |
| **Action Gate** | BLOCK: Create test_k5_determinism.py with replay_manifest.json before proceeding |

**Required Artifact:**
```json
{
  "replay_manifest": {
    "claim_id": "CLM-REPLAY-001",
    "claim_sha256": "...",
    "policy_sha256": "...",
    "ledger_sha256": "...",
    "briefcase_sha256": "...",
    "attestations_merkle": "...",
    "environment_fingerprint": ""
  },
  "iterations": 30,
  "decision_digests": [
    "sha256:...", (30 lines, all should be identical)
  ]
}
```

---

### 🔴 E5: Constitutional Self-Reinforcement (Cross-Domain Coherence)

| Component | Receipt | Status |
|-----------|---------|--------|
| **Claim** | Across domains (math, code, research, incidents), decisions cite same K-rules consistently; new domains don't require exceptions |
| **Available** | 4 knowledge submissions + 3 decision records |
| **Missing** | Decision corpus + rule_citation_matrix classifier |
| **Required** | 10+ decisions from 3+ domains with rule_citations field |
| **Example Output** | rule_citation_matrix.json: {domain: {K0: count, K1: count, ...}} |
| **Falsifier** | New domain requires exception (e.g., "K3 doesn't apply here") |
| **Status** | 🔴 NOT FALSIFIABLE (no corpus) |
| **Action Gate** | BLOCK: Create scripts/rule_citation_report.py + analyze decision corpus before claiming E5 |

---

### 🔴 Culture Pillars (Week 2) — All Unmetric

| Pillar | Metric | Current | Status |
|--------|--------|---------|--------|
| **Transparency** | % submissions with complete receipts on first attempt | NOT MEASURED | 🔴 UNMETRIC |
| **Rigor** | (evidence_completeness_score × time_to_ship) vs (rush_attempts × overrides) | NOT MEASURED | 🔴 UNMETRIC |
| **Epistemic Humility** | (explicit_uncertainty_markers + referenced_receipts) / total_claims | NOT MEASURED | 🔴 UNMETRIC |
| **Rule Naturalization** | validator_pass_rate + governance_reminders_needed | NOT MEASURED | 🔴 UNMETRIC |

**Action Gate for Week 2 Claims:** BLOCK all culture claims until metrics.jsonl established with:
- missing_receipts_count
- validator_pass_rate
- % narrative tokens
- time_to_receipt_complete
- veto_latency

---

## GOVERNANCE GATES (Constitutional Blockers)

### Gate 1: Before Any "Proved" Claim
- [ ] Receipt location provided (file path + hash)
- [ ] Falsifier explicitly stated
- [ ] Test case that would fail the claim

### Gate 2: Before Any "Stable" Claim
- [ ] N ≥ 3 independent test cases
- [ ] Corpus analysis or classifier output
- [ ] Variance metric (entropy, std dev, or threshold)

### Gate 3: Before Any "Culture" Claim
- [ ] Metrics.jsonl with 4+ measurements per observation
- [ ] Baseline (Week 1) vs. current (Week N) comparison
- [ ] Statistical test (t-test, chi-square, or domain-specific)

### Gate 4: Before Any "Falsification" Claim
- [ ] Input identity pinning (all variables controlled)
- [ ] Comparative table showing which inputs differ
- [ ] Logical proof: "inputs identical AND outputs differ → claim falsified"

---

## CI/CD Receipts (Committed to Git)

| Artifact | Hash / Commit | Status |
|----------|---------------|--------|
| WEEK_1_RECEIPTS_TIER_I.md | Commit 5831f54 | ✓ Corrected |
| HONEST_WEEK_1_DISCOVERY_LEDGER.md | Commit 3439844 | ✓ Constitutional format |
| bibliotheque_intake_manifest.json | `132f434c48...` | ✓ Verified |
| runA decision_record.json | decision_digest: `c6f45ad4...` | ✓ Exists |
| runB decision_record.json | decision_digest: `0dacdcad...` | ✓ Exists |
| runC decision_record.json | decision_digest: `91cc5f08...` | ✓ Exists |

---

## Action Items (Ranked by Constitutional Urgency)

### CRITICAL (Blocks Tier III Claims)
1. **CREATE:** `replay_manifest.json` pinning identical inputs for K5 test
2. **CREATE:** `test_k5_determinism.py` (30-iteration determinism gate)
3. **CREATE:** `scripts/rule_citation_report.py` for E5 corpus analysis
4. **CREATE:** `metrics.jsonl` baseline (Week 1 culture measurements)

### HIGH (Upgrades Tier II → Tier I)
5. **LINK:** REQ_004 incidents to decision_records with timestamps
6. **SHOW:** 3+ independent decisions blocked by same revocation (cascade proof)

### MEDIUM (Documentation)
7. **DOCUMENT:** Which decisions cite which K-rules (for rule_citation_matrix)
8. **EXCLUDE:** mtime_epoch from decision gates (metadata only)

---

## Next Session: Tier III Proof Targets

**Recommended Order:**
1. K5 determinism (1 day) — build replay_manifest + test
2. E5 corpus analysis (2-3 days) — collect decision records, classify rules
3. Culture metrics (1 day) — establish baseline

**Estimated Result:** E1, E4, E5 can move from Tier III → Tier II/I within 1 week.

---

## Constitutional Status

✅ **Tier I established:** K1, E3 proven
🟡 **Tier II identified:** E4 needs 2 more cases
🔴 **Tier III tracked:** K5, E5, Culture all mapped to specific artifacts

**Governance Posture:** Fail-closed on unproven claims; receipts-first on new discoveries.

---

**Dashboard Next Update:** After replay_manifest.json + test_k5_determinism.py completed

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
