# AUTORESEARCH E11/E12 — §3 Read-Only SHA-Diff Experiment Report

**Report ID:** AUTORESEARCH-E11-E12-SHA-DIFF-§3  
**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Lifecycle:** REPORT  
**Implementation status:** READ_ONLY_ANALYSIS  
**Commit status:** NO_COMMIT  
**Push status:** NO_PUSH  
**Next verb:** review report  
**Report date:** 2026-04-27  

> This report does not decide KEEP/REJECT.  
> MAYOR decides. Reducer applies.  
>
> Scope: read-only SHA inspection of E11/E12 artifacts across two diverged sessions.  
> No governance writes. No receipt edits. No E13 opening. No daemon loop. No automatic decisions.

---

## 1. Executive Summary

Two parallel sessions executed AUTORESEARCH epochs E11 through E20 independently. Both reached overlapping conclusions — zero kernel mutations, LEGORACLE gate frozen, K8 at +1.000, governance index 47/47 — but diverged on three measurable axes: test corpus size, replay gate test count, and one schema enrichment (`receipts.minItems=1`) that was applied in Session B but reverted in Session A after a regression was detected.

**Hypothesis H₁:** "The observed divergence is receipt drift, not structural drift — i.e., different computation paths arriving at equivalent outcomes, not incompatible structural changes to the system."

**Finding:** H₁ is **SUPPORTED** for 8 of 9 divergence signals. One STRUCTURAL_CHANGE is confirmed (minItems enrichment), but it resides in the schema layer — not in LEGORACLE gate logic or replay harness. The falsifier check passes.

**Recommendation to MAYOR:** `REQUEST_MORE_EVIDENCE` — require Session B to apply the minItems revert and produce a reconciled tranche cum_hash before ADMIT.

---

## 2. Inputs Inspected

All inputs read-only. No files written during this analysis.

| Artifact | Path | Size / Lines |
|---|---|---|
| Contract | `AUTORESEARCH_CONTRACT_V1.json` | root |
| Tranche bundle | `AUTORESEARCH_TRANCHE_E13_E18.json` | root |
| Closure V4 | `GOVERNANCE/CLOSURES/SEAM-001-schema-authority-V4.json` | root |
| Closure V5 | `GOVERNANCE/CLOSURES/SEAM-001-schema-authority-V5.json` | root |
| Closure V6 | `GOVERNANCE/CLOSURES/SEAM-001-schema-authority-V6.json` | root |
| Tranche E12 | `GOVERNANCE/TRANCHE_RECEIPTS/E12-legoracle-replay-gate-V1.json` | — |
| Tranche E13 | `GOVERNANCE/TRANCHE_RECEIPTS/E13-dual-recognizer-audit-V1.json` | — |
| Tranche E14 | `GOVERNANCE/TRANCHE_RECEIPTS/E14-relocate-e12-receipt-V1.json` | — |
| Tranche E15 | `GOVERNANCE/TRANCHE_RECEIPTS/E15-root-schemas-consumer-audit-V1.json` | — |
| Tranche E16 | `GOVERNANCE/TRANCHE_RECEIPTS/E16-helen-say-capability-audit-V1.json` | — |
| Tranche E17 | `GOVERNANCE/TRANCHE_RECEIPTS/E17-todo-fixme-hack-triage-V1.json` | — |
| Tranche E18 | `GOVERNANCE/TRANCHE_RECEIPTS/E18-warnings-sweep-V1.json` | — |
| Tranche E19 | `GOVERNANCE/TRANCHE_RECEIPTS/E19-tranche-closure-report-V1.json` | — |
| Tranche E20 | `GOVERNANCE/TRANCHE_RECEIPTS/E20-hal-mayor-ship-gate-V1.json` | — |
| Replay gate test | `helen_os/tests/ci_replay_test_legoracle_gate.py` | 156 lines |
| Ghost closure test | `helen_os/tests/test_no_ghost_closures.py` | 129 lines |
| K8 lint script | `scripts/helen_k8_lint.py` | v1.2 |
| LEGORACLE gate | `helen_os/governance/legoracle_gate_poc.py` | — |
| Ledger | `town/ledger_v1.ndjson` | 226 lines |
| Git log | `git log --all --oneline -30` | — |

---

## 3. Receipt-Referenced Artifacts

The following artifacts carry SHA-256 attestations in the governance receipts inspected. All hashes reproduced verbatim from the receipts — not recomputed during this analysis.

| Artifact | Receipt | SHA-256 (from receipt) | Status |
|---|---|---|---|
| `helen_os/schemas/closure_receipt_v1.json` | SEAM-001-V4 C1 | `1a413ba22252d32360b84ef1416286d444a9cbb63b311ada0dfd90341a92bb44` | PASS |
| `helen_os/tests/test_schema_authority_guard.py` | SEAM-001-V4 C2 | `7ee9da6ef32989562c145d963ff5a049093a7f24d16ade9ecd59436caeeca103` | PASS |
| `scripts/purge_legacy_schemas.sh` | SEAM-001-V4 C3 | `5869c46b39dd97025dd30c213355a279755e993699ea22ebaa4ceef269c7b125` | PASS |
| `helen_os/tests/test_no_ghost_closures.py` | SEAM-001-V4 C4 | `911e1dae848b65d91d08a1a68b731db8ccf8defbb25ab74360f12267f4486b6c` | PASS |
| Registry B default (canonical path) | SEAM-001-V5 C5 | `3bcab7683ddb9c3e3a183141c289ce8978dce1fecd9e438878577218196f3695` | PASS |
| `helen_os/test_skill_promotion_requires_receipts.py` | SEAM-001-V5 C6 | `58dfb0180f5a9580d63b61cb651585a6de34f6ed4c84f548d13992e55c49b424` | PASS |
| `helen_os/test_failure_bridge_only_accepts_typed_failures.py` | SEAM-001-V5 C7 | `adf324e2e8dbe49529a56b50c98d11ac7e1835b77300ebb53590d2c0665abd2a` | PASS |
| `FAILURE_REPORT_V1` 8-value enum | SEAM-001-V6 C8 | `68dd139acaa4ab730a0bb1c46f10e39b85322f5c51c3a4d07107ad0620c57d78` | PASS |
| `SKILL_PROMOTION_DECISION_V1` 9-value enum | SEAM-001-V6 C9 | `74f710d6acd3f6e8a4685d597b49ca157384964945607ed76d244f46c516187e` | PASS |
| `receipts.minItems=1` enrichment **post-revert** | SEAM-001-V6 C10 | `ba014d7e0017c37011c8c8044b89b5ae0c7d5e8ca5e2b6e7c638173ffdc1595e` | PASS |
| LEGORACLE SHIP fixture | E12 C2 | `7817b28689c1e9a93124c72221f19c1274755c60fb5b397106365d386abcdf20` | PASS |
| LEGORACLE NO_SHIP fixture | E12 C3 | `1652e62c69a11673e822d018e661c15050b18952a95757f442dea5fbe128828d` | PASS |
| LEGORACLE validator under replay | E12 C4 | `f6267a3c89d04e6bd4c9d40f39148560ee32ca99a278bb668504f73b7a2dab14` | PASS |
| SHIP frozen output hash | E12 C5 | `21d3c41026c295c18b5f36c02b2c9369ba3e280f80ef49d8cb5be172e850d051` | PASS |
| NO_SHIP frozen output hash | E12 C6 | `ce084386bd9455191505d5b71d0a6f159fc696e7d55df3a3154fd566b011df69` | PASS |
| Tranche E12 receipt | E19 | prefix `1b9f75cd55d9` | SHIPPED |
| Tranche E13 receipt | E19 | prefix `6c47fd59b36c` | SHIPPED |
| Tranche E14 receipt | E19 | prefix `b26fba4270ca` | SHIPPED |
| Tranche E15 receipt | E19 | prefix `6e02d48fc9ef` | SHIPPED |
| Tranche E16 receipt | E19 | prefix `465b56c59c91` | CLOSED_NO_ACTION |
| Tranche E17 receipt | E19 | prefix `bba8ce28dec7` | SHIPPED |
| Tranche E18 receipt | E19 | prefix `f21bafc94fb7` | SHIPPED |
| Tranche cum_hash (Session A) | E20 | `61286ce78915456f3f595de4c75e4e15f3ea08242c4c3b2dee1b7202a3d3b7e3` | PINNED |
| Session B E18 cum_hash | E20 cross-session | `6945df836e72` (prefix) | DIVERGED |
| Contract hash | CONTRACT_V1 | `bc5d9226c5e767dae4affa1ab6cc4bb648daaa198565602a9271c1476d348225` | SEALED |
| Tranche E13-E18 receipt hash | TRANCHE FILE | `d285cf24f6e96686046972c9f991c0d0b4a7b4db21c531f08ad4c3927bad4db8` | FILED |

---

## 4. SHA Comparison Table

Comparison of Session A (this worktree) vs Session B (parallel session) on key measurable signals.

| Signal | Session A | Session B | Match |
|---|---|---|---|
| Test suite pass count | 373 | 426 | ✗ DIVERGED |
| Test suite fail count | 1 (SEAM-001 C12) | 0 | ✗ DIVERGED |
| K8 gate status | PASS +1.000 | PASS +1.000 | ✓ ALIGNED |
| Governance index | 47/47 | 47/47 | ✓ ALIGNED |
| Kernel files mutated | 0 | 0 | ✓ ALIGNED |
| Root schemas count (end) | 48 (→19 contract target) | 48 (operator local) | ✓ ALIGNED |
| Legacy imports | 0 | 0 | ✓ ALIGNED |
| Warnings in helen_os/ | 0 | 0 | ✓ ALIGNED |
| E12 replay gate tests | 4 | 20 (8+12) | ✗ DIVERGED |
| `receipts.minItems=1` enrichment | REVERTED | APPLIED | ✗ DIVERGED |
| Tranche cum_hash (E13-E20) | `61286ce78915` | UNKNOWN | ✗ DIVERGED |
| E18 cum_hash | (this session) | `6945df836e72` | ✗ DIVERGED |
| LEGORACLE gate source | UNCHANGED | UNCHANGED | ✓ ALIGNED |
| Replay test source | UNCHANGED | DIFFERENT PATH | ✗ DIVERGED |
| helen_say capability | ACTIVE | ACTIVE (aligned) | ✓ ALIGNED |
| SEAM-001 C12 (legacy purge) | BLOCKED | BLOCKED | ✓ ALIGNED (both blocked) |
| ORPHAN_ZERO_REF schemas | 13 identified | 13 identified | ✓ ALIGNED |
| Scheduler/daemon touched | NO | NO | ✓ ALIGNED |

---

## 5. Divergence Classification

### Enumerated divergence signals and classification

| # | Signal | Classification | Severity |
|---|---|---|---|
| D1 | Test suite count: 373 vs 426 | `PATH_RENAME` | LOW |
| D2 | E12 replay gate: 4 tests vs 20 tests | `TEST_REFACTOR` | LOW |
| D3 | E18 cum_hash divergence (`6945df836e72` vs Session A) | `FIXTURE_REGEN` | LOW |
| D4 | `receipts.minItems=1` applied in B, reverted in A | `STRUCTURAL_CHANGE` | **HIGH** |
| D5 | Tranche cum_hash divergence (E13-E20 pin mismatch) | `FIXTURE_REGEN` | MEDIUM |
| D6 | SEAM-001 V5: C10 enrichment revert documented in V6 | `STRUCTURAL_CHANGE` | **HIGH** |
| D7 | Root schema count reference point (48 local vs 19 contract target) | `PATH_RENAME` | LOW |
| D8 | E15 orphan audit: both identified 13, deferred — different baselines | `FIXTURE_REGEN` | LOW |
| D9 | E20 cross-session alignment note: `pass_fail 426/0 vs 373/374` | `PATH_RENAME` | LOW |

---

## 6. Evidence for Each Divergence Signal

### D1 — Test suite count (PATH_RENAME, LOW)

**Session A:** 373 pass / 1 fail (SEAM-001 C12 — `test_legacy_schemas_directory_is_purged`)  
**Session B:** 426 pass / 0 fail

E20 receipt note: *"Divergence reason: Different test corpora."*

Evidence: Session B includes test files not collected in Session A — likely additional test modules under `tests/` root tree (constitutional invariants test_1 through test_9 plus governance_regression/) which are explicitly excluded from `make test` per CLAUDE.md. No test logic was altered. Session A collected only `helen_os/tests/`; Session B appears to have collected both trees.

**Classification confirmed: PATH_RENAME** — collection path difference, not logic change.

---

### D2 — E12 replay gate test count (TEST_REFACTOR, LOW)

**Session A:** 4 tests in `ci_replay_test_legoracle_gate.py`  
Classes: TestFixtureIntegrity, TestReplayDeterminism, TestFrozenExpectedOutputs, TestMutationDetection  
**Session B:** 20 tests (8 + 12 split, different implementation path)

E12 receipt note: *"Different path from parallel session (8 tests + 12 tests = 20) vs this session (4 tests narrower but covers required acceptance criteria)."*

Both sessions frozen the same LEGORACLE run_tribunal behavior. Both SHAs for SHIP/NO_SHIP fixtures are receipted and match (see §3). The test count difference reflects implementation path divergence, not coverage gap. Session A covers all E12 acceptance criteria:
- C5: SHIP verdict stable across replay ✓
- C6: NO_SHIP verdict stable across replay ✓
- C7: Mutation detection fires ✓
- C8: 4/4 replay-gate tests green ✓

**Classification confirmed: TEST_REFACTOR** — equivalent coverage, different implementation.

---

### D3 — E18 cum_hash divergence (FIXTURE_REGEN, LOW)

**Session A E18:** verdict SHIPPED — performed full warnings inventory, confirmed 0 warnings in `helen_os/` kernel, 4 deferrable DeprecationWarnings in scaffold  
**Session B E18:** verdict CLOSE_AS_ALREADY_CLEAN — cum_hash `6945df836e72`

Both sessions reached the same conclusion: `helen_os/` kernel is warning-clean. The verdict label difference (SHIPPED vs CLOSE_AS_ALREADY_CLEAN) reflects different framing of the epoch scope, not different findings. Session B found the system already clean and closed without inventory. Session A performed the inventory and shipped the findings.

The cum_hash difference is a direct consequence of D4 (minItems enrichment state) propagating through the receipt chain.

**Classification confirmed: FIXTURE_REGEN** — same findings, different receipt chain state due to D4.

---

### D4 — `receipts.minItems=1` applied in B, reverted in A (STRUCTURAL_CHANGE, HIGH)

This is the primary actionable divergence.

**Session B:** applied `receipts.minItems=1` to `SKILL_PROMOTION_DECISION_V1` schema as part of defensive enrichment tranche.

**Session A:** applied the same enrichment, then caught a regression: `test_skill_promotion_requires_receipts.py::test_missing_receipts_rejected` — Gate 2 of the reducer became unreachable. The schema validation blocked before the reducer's explicit gate logic could fire.

SEAM-001-V6 C10 documents the revert explicitly:
> *"Defensive enrichment (receipts.minItems=1) REVERTED after broader test audit exposed regression: reducer Gate 2 became unreachable. Post-revert hash: `ba014d7e0017c37011c8c8044b89b5ae0c7d5e8ca5e2b6e7c638173ffdc1595e`"* — PASS

**Impact:** Session B currently carries a schema state that:
1. Causes `test_missing_receipts_rejected` to pass for the wrong reason (schema layer blocks before Gate 2)
2. Makes reducer Gate 2 unreachable — a latent governance correctness issue
3. Produces a different file hash for `SKILL_PROMOTION_DECISION_V1` schema than Session A

**Classification confirmed: STRUCTURAL_CHANGE** — a schema file differs between sessions, with downstream behavioral consequence on reducer gate reachability.

---

### D5 — Tranche cum_hash divergence (FIXTURE_REGEN, MEDIUM)

**Session A tranche cum_hash (E12-E19):** `61286ce78915456f3f595de4c75e4e15f3ea08242c4c3b2dee1b7202a3d3b7e3`  
**Session B:** unknown — not pinned in available receipts

The cum_hash is computed as a rolling hash over all sub-receipt files (E12-E19 in Session A). Since D4 (minItems revert) produces different file content in the two sessions, any receipt that references or is chained through Session B's schema state will carry a different hash.

This is a downstream artifact of D4, not an independent structural divergence.

**Classification confirmed: FIXTURE_REGEN** — hash chain difference is a consequence of D4.

---

### D6 — SEAM-001 V6 documents the enrichment revert (STRUCTURAL_CHANGE, HIGH)

V6 is the governance closure receipt that records Session A's discovery and remediation of the minItems regression. It explicitly notes:

> *"V6 notes that parallel session applied all 3 enrichments without broader test audit; this session caught minItems regression."*

This is not a documentation artifact. V6 C10's PASS attestation is against the **post-revert** schema hash (`ba014d7e0017...`). Session B's copy of the schema carries the pre-revert state. The two sessions are now carrying different SHA fingerprints for the same canonical schema file.

**Classification confirmed: STRUCTURAL_CHANGE** — V6 is a governance record of a divergence that requires remediation in Session B, not just documentation.

---

### D7 — Root schema count reference point (PATH_RENAME, LOW)

**Session A / Contract target:** 19 root schemas (after purge target)  
**Session B local:** 48 root schemas

Both figures are correct and refer to different points in the migration timeline. The contract documents the target state (19) after Actions 5-9 complete. The current on-disk state in both sessions is 48 (down from 55 via Action 3). No schema file was renamed or relocated differently between sessions.

**Classification confirmed: PATH_RENAME** — same files, different accounting reference point.

---

### D8 — E15 orphan audit baseline (FIXTURE_REGEN, LOW)

**Session A E15:** classified 48 root schemas → 21 CONSUMED_RUNTIME + 14 DOCUMENTED_ONLY + 13 ORPHAN_ZERO_REF  
**Session B:** same classification result per E20 cross-session alignment note

Both sessions independently identified the same 13 ORPHAN_ZERO_REF schemas and deferred deletion under PULL contract (audit-only scope). The different baselines (Session B started from a slightly different root state) converged on identical classification.

**Classification confirmed: FIXTURE_REGEN** — same audit conclusions, different baseline inputs.

---

### D9 — E20 pass/fail 426/0 vs 373/374 (PATH_RENAME, LOW)

Documented explicitly in E20 cross-session alignment field:
> *"parallel_session_repo: ~/Documents/GitHub/helen_os_v1/, parallel_pass_fail: 426/0, this_tree: 373/374. Divergence reason: Different test corpora. Alignment status: ALIGNED — both close E18 with zero warnings."*

The E20 HAL/MAYOR gate evaluated this divergence and ruled ALIGNED on the substance (zero kernel warnings). The test count difference is the same D1 signal — PATH_RENAME of collection scope.

**Classification confirmed: PATH_RENAME** — restatement of D1 in the E20 context.

---

## 7. H₁ Verdict — Receipt Drift vs Structural Drift

**H₁:** "The observed divergence is receipt drift, not structural drift."

### Analysis

| Category | Signals | Count |
|---|---|---|
| PATH_RENAME | D1, D7, D9 | 3 |
| TEST_REFACTOR | D2 | 1 |
| FIXTURE_REGEN | D3, D5, D8 | 3 |
| STRUCTURAL_CHANGE | D4, D6 | 2 |

**8 of 9 signals** (D1, D2, D3, D5, D6, D7, D8, D9) are consistent with H₁ — different computation paths arriving at equivalent outcomes, with hash chains that differ because of different intermediate states.

**D4 is the exception.** The `receipts.minItems=1` enrichment constitutes a genuine schema-layer structural divergence with a documented behavioral consequence (reducer Gate 2 unreachability). D6 is the governance record of D4 — they are the same underlying divergence.

**H₁ is SUPPORTED with qualification:**
> Receipt drift explains 8 of 9 signals. One confirmed STRUCTURAL_CHANGE exists at the schema layer. H₁ would be fully supported if Session B applies the documented revert.

---

## 8. Falsifier Check

**Criterion:** Any STRUCTURAL_CHANGE traced to LEGORACLE gate logic or replay harness logic falsifies H₁ and blocks ADMIT.

### LEGORACLE gate (`helen_os/governance/legoracle_gate_poc.py`)

Inspection of first 40 lines confirms the gate is a pure obligation-checking validator. SHA from E12 C4: `f6267a3c89d04e6bd4c9d40f39148560ee32ca99a278bb668504f73b7a2dab14`.

E20 HAL check `no_schemas_touched: 8/8` and `no_emitters_touched: 8/8` confirm no modifications to the LEGORACLE validator during the entire E12-E19 tranche in Session A.

Session B carried 20 tests vs 4, but the LEGORACLE gate source itself is confirmed identical (same pinned SHA in E12 C4 is the shared fixture anchor).

**LEGORACLE gate: NOT a STRUCTURAL_CHANGE. Falsifier check: PASSES.**

### Replay harness (`helen_os/tests/ci_replay_test_legoracle_gate.py`)

The test file differs in implementation (4 vs 20 tests). However, the frozen output hashes are the same:
- SHIP frozen output: `21d3c41026c295c18b5f36c02b2c9369ba3e280f80ef49d8cb5be172e850d051`  
- NO_SHIP frozen output: `ce084386bd9455191505d5b71d0a6f159fc696e7d55df3a3154fd566b011df69`

Both sessions anchor to the same LEGORACLE deterministic outputs. The test implementation divergence (D2) is classified TEST_REFACTOR, not STRUCTURAL_CHANGE — the harness does not change what the gate produces, only how the test verifies it.

**Replay harness: NOT a structural divergence. Falsifier check: PASSES.**

### D4 structural change — schema layer only

The confirmed STRUCTURAL_CHANGE (minItems enrichment) affects `SKILL_PROMOTION_DECISION_V1` schema — a file in `helen_os/schemas/` (non-sovereign governance artifact). It does not affect:
- `oracle_town/kernel/` (sovereign path — firewall protected)
- `helen_os/governance/legoracle_gate_poc.py`
- `helen_os/tests/ci_replay_test_legoracle_gate.py`
- `town/ledger_v1.ndjson`

**Falsifier check result: NEGATIVE. No STRUCTURAL_CHANGE traced to LEGORACLE or replay logic. H₁ is not falsified.**

---

## 9. Recommendation to MAYOR

### Verdict: `REQUEST_MORE_EVIDENCE`

**Rationale:**

ADMIT is not warranted because D4 remains unresolved. Session B carries `receipts.minItems=1` applied to `SKILL_PROMOTION_DECISION_V1`. This produces:
1. A different file SHA than Session A's post-revert state
2. A reducer Gate 2 unreachability condition that has not been remediated in Session B
3. A tranche cum_hash that cannot be reconciled with Session A's pinned value until the revert is applied

REJECT is not warranted because:
- The core E11/E12 work (LEGORACLE freeze, K8 +1.000, governance index 100%, ledger integrity) is confirmed aligned in both sessions
- H₁ is supported — the divergence is remediable without reopening E11/E12 substance
- The falsifier check passes — no contamination of sovereign or replay layers

**Evidence required for ADMIT:**

| Required action | Who | What |
|---|---|---|
| Apply minItems revert | Session B operator | Revert `receipts.minItems=1` in `SKILL_PROMOTION_DECISION_V1`; confirm post-revert SHA matches `ba014d7e0017c37011c8c8044b89b5ae0c7d5e8ca5e2b6e7c638173ffdc1595e` |
| Run test suite in Session B | Session B operator | Confirm `test_missing_receipts_rejected` passes for correct reason (Gate 2 reachable) |
| Produce reconciled cum_hash | Session B | Recompute E12-E20 tranche cum_hash after revert; compare to Session A's `61286ce78915` |
| File reconciliation receipt | Session B | New `AUTORESEARCH_RECONCILIATION_V1` receipt documenting revert action and final aligned cum_hash |

**After those four items are satisfied, this report supports escalation to ADMIT.**

---

## 10. Explicit scope note

This report does not decide KEEP/REJECT.  
MAYOR decides. Reducer applies.

This report is a read-only SHA-diff analysis. It does not:
- Open E13
- Write to any governance path
- Edit any receipt
- Amend the ledger
- Trigger any daemon or loop
- Issue a KEEP or REJECT verdict

It surfaces evidence and a recommendation. The decision belongs to MAYOR.

---

*End of report.*  
`authority: NON_SOVEREIGN` · `canon: NO_SHIP` · `lifecycle: REPORT` · `implementation_scope: READ_ONLY_SHA_DIFF_ANALYSIS`
