# AUTORESEARCH E11/E12 — Reconciliation Hypothesis (Proposal)

NO CLAIM — NO SHIP — PROPOSAL ONLY — CANDIDATE_HYPOTHESIS

```
artifact_type:         PROPOSAL_RECONCILIATION_HYPOTHESIS
proposal_id:           AUTORESEARCH_E11_E12_RECONCILIATION
authority:             NON_SOVEREIGN
canon:                 NO_SHIP
lifecycle:             PROPOSAL
implementation_status: NOT_IMPLEMENTED
memory_class:          CANDIDATE_HYPOTHESIS
captured_on:           2026-04-27
captured_by:           operator (jeanmarie.tassy@uzik.com)
proposer_session:      claude-opus-4-7 (main, this session)
parent_state:          AUTORESEARCH halted at E12;
                       AUTORESEARCH_CONTRACT_V1.json sealed 2026-04-17;
                       E13 blocked per bounded-tranche discipline.
related_memory:        project_autoresearch_e12_halt.md
                       feedback_ralph_violations.md
                       feedback_single_sot.md
related_artifacts:     AUTORESEARCH_CONTRACT_V1.json
                       AUTORESEARCH_TRANCHE_E13_E18.json
                       GOVERNANCE/TRANCHE_RECEIPTS/E12-legoracle-replay-gate-V1.json
```

> **PULL-mode discipline (preserved)**
> One hypothesis per epoch. Observable signals only. Bounded tranche.
> 7-field receipt per epoch. Halt before next opens.
> Proposer ≠ Validator. KEEP/REJECT is MAYOR's call, never the proposer's.

---

## §0. Stop-rule

This is a **reconciliation hypothesis**, not a reconciliation. It does
not write to the kernel, governance, schemas, ledger, mayor registry, or
any tranche receipt. It does not open E13. It does not amend any sealed
contract. It does not delete or merge worktrees.

What it proposes: a **read-only diagnostic experiment** whose output is a
written REPORT (non-receipt) for MAYOR to rule on. MAYOR's verdict
(ACCEPT / AMEND / REVOKE) is what unblocks (or re-blocks) E13. This file
is upstream of that verdict.

---

## §1. Observable divergence evidence (from SOT investigation)

These are the **concrete signals** of "two parallel sessions diverged"
referenced in the halt memory. Source: read-only repo investigation
2026-04-27 (artifact paths, SHAs, commit hashes verified).

| # | Signal | Source |
|---|---|---|
| 1 | Contract hash mismatch: recorded `bc5d9226c5e7…`, actual `21ee5f6a3caf…` | `AUTORESEARCH_CONTRACT_V1.json` |
| 2 | E13-E18 tranche hash mismatch: recorded `d285cf24f6e9…`, actual `fff5f5c41798…` | `AUTORESEARCH_TRANCHE_E13_E18.json` |
| 3 | E12 CI test file SHA mismatch: expected `0872aa46…`, actual `da8f976a…` | `GOVERNANCE/TRANCHE_RECEIPTS/E12-legoracle-replay-gate-V1.json` C1 |
| 4 | Fixture directory path mismatch: receipt expects `legoracle_gate/`, code uses `legoracle/` | E12 receipt C2-C3 |
| 5 | E15 explicit cross-session divergence: "48→0 on operator side, 19 remaining here" | `AUTORESEARCH_TRANCHE_E13_E18.json` E15 note |
| 6 | E11 receipt **missing**: contract claims E11-E12 shipped; only E12 receipt exists in `GOVERNANCE/TRANCHE_RECEIPTS/` | `GOVERNANCE/TRANCHE_RECEIPTS/` (no `*E11*` file) |
| 7 | Three active parked worktrees branched at common base `b241ce2`, never reintegrated (`admiring-fermi-af4d54`, `elated-mirzakhani-ee1c46`, `modest-noether-0e644e`) | `.claude/worktrees/` |
| 8 | Contract invariant violated: line 117 claims "No multi-branch exploration" — contradicted by active multi-branch state | `AUTORESEARCH_CONTRACT_V1.json` vs worktree state |
| 9 | Two cum_hash basis: E12 receipt cites Desktop session `b3415eb3edfb` ("8 tests + 12 tests = 20 tests"); main session has narrower 4-test gate | `E12-legoracle-replay-gate-V1.json` line 91 |

These are facts, not interpretations. Any reconciliation must address
each numbered signal explicitly.

---

## §2. The single bounded hypothesis (PULL-mode)

> **H₁ — Receipt Drift, Not Structural Drift.**
> The E11/E12 divergence is bounded to **artifact-level** drift between
> the Desktop/Releve 24 session and the SOT main branch — fixture path
> renames, test file refactors, post-seal contract edits — and **does
> not** reflect a structural change to the LEGORACLE gate logic, the
> replay determinism boundary, or the K8 / K-tau gate semantics.

**If H₁ holds**: receipts can be reconciled by re-hashing the current
SOT artifacts and emitting a `SUPERSEDES_V0` annotation in a fresh
non-sovereign report. MAYOR rules whether to accept the annotation,
issue a one-line ledger correction, or revoke.

**If H₁ is falsified** (any signal traces to structural change):
receipts E11 / E12 must be marked **SUPERSEDED** (not amended). E13
remains blocked. A new bounded tranche `T11_T12_RERUN` is proposed in a
separate file. AUTORESEARCH does not silently roll forward.

---

## §3. Experiment design (read-only, deterministic)

### §3.1 Inputs

- `AUTORESEARCH_CONTRACT_V1.json` (current SOT state)
- `AUTORESEARCH_TRANCHE_E13_E18.json`
- `GOVERNANCE/TRANCHE_RECEIPTS/E12-legoracle-replay-gate-V1.json`
- All artifacts listed in those receipts' `artifacts_produced` fields
- `helen_os/governance/legoracle_gate_poc.py`
- `helen_os/tests/ci_replay_test_legoracle_gate.py`
- `legoracle_v13rc.py` (root)
- `git log --all --since='2026-04-15'` for E11/E12-touching commits

### §3.2 Procedure

For each artifact referenced in any of the receipts:

1. Compute current SHA-256 (`sha256sum <path>`)
2. Diff against the expected SHA recorded in the receipt
3. If mismatch, classify into exactly one of:
   - `PATH_RENAME` — file moved/renamed; content semantics preserved
   - `TEST_REFACTOR` — test code restyled; assertions equivalent
   - `FIXTURE_REGEN` — deterministically regenerable from inputs
   - `STRUCTURAL_CHANGE` — logic or semantics altered
4. For `STRUCTURAL_CHANGE`, record the commit hash and diff hunks
5. Tally: `mismatches_by_class`, `structural_change_count`
6. Compile findings into `docs/reports/AUTORESEARCH_E11_E12_RECONCILIATION_REPORT_V0.md`
   (a **report**, not a receipt; non-sovereign path; no spine write)

### §3.3 Forbidden during the experiment

- writing to `town/ledger_v1.ndjson` (sovereign firewall)
- writing to `helen_os/governance/`, `helen_os/schemas/`, `mayor_*.json`,
  `GOVERNANCE/CLOSURES/`, `GOVERNANCE/TRANCHE_RECEIPTS/`
- editing any of the receipts being audited
- merging or deleting worktrees
- amending the AUTORESEARCH contract
- opening E13 or any new tranche
- self-deciding KEEP / REJECT (per `feedback_ralph_violations.md`)

### §3.4 Expected output

A single read-only report at `docs/reports/AUTORESEARCH_E11_E12_RECONCILIATION_REPORT_V0.md`
with the following structure:

- §A. Per-artifact SHA diff table (expected vs actual vs class)
- §B. Tally by class
- §C. Per `STRUCTURAL_CHANGE` row: commit hash + hunk excerpt
- §D. Worktree audit (which worktrees touched E11/E12 paths post-base)
- §E. E11 receipt-absence diagnosis (was E11 ever written? was it lost?
  was it merged into E12 receipt? — read-only evidence)
- §F. Verdict candidates for MAYOR: ACCEPT_RE_HASH / AMEND_WITH_SUPERSEDES /
  REVOKE_AND_RERUN

The report is **input** to MAYOR, not a verdict.

---

## §4. The 7-field receipt template (when the experiment runs)

Per PULL-mode constitutional requirement, when this hypothesis is
executed it must emit a 7-field receipt for MAYOR:

```yaml
1. carry_forward_state:
     # SOT git HEAD, working-tree status, ledger cum_hash at experiment start
2. hypothesis:
     # H₁ exactly as written in §2 of this proposal
3. experiment:
     # §3 procedure, executed, with per-artifact SHA diff log
4. metric:
     # mismatches_by_class: {PATH_RENAME: N, TEST_REFACTOR: N,
     #                       FIXTURE_REGEN: N, STRUCTURAL_CHANGE: N}
     # structural_change_count
     # h1_falsified: bool (true iff structural_change_count > 0)
5. failure_mode:
     # observed structural changes, if any, with commit hashes
6. keep_reject_rule:
     # NOT decided by experiment runner.
     # MAYOR rules: KEEP if structural_change_count == 0 and operator
     #              countersigns; REJECT otherwise. Reducer applies
     #              MAYOR's verdict. Proposer ≠ Validator (Rule 3).
7. upgrade_path:
     # if KEEP:   emit non-sovereign SUPERSEDES_V0 annotation; E13
     #            unblocks pending HAL gate + MAYOR re-rank
     # if REJECT: receipts E11/E12 marked SUPERSEDED; new bounded
     #            tranche T11_T12_RERUN proposed in separate file;
     #            E13 remains blocked
```

The receipt must be emitted via the canonical writer
(`tools/helen_say.py`) once MAYOR rules — not by this proposal, not by
the report writer, not by Claude Code.

---

## §5. Why this is NON_SOVEREIGN

This proposal touches **none** of the sovereign-firewall paths:

- ✗ does not write to `oracle_town/kernel/`
- ✗ does not write to `helen_os/governance/`
- ✗ does not write to `helen_os/schemas/`
- ✗ does not write to `town/ledger_v1.ndjson`
- ✗ does not write to `mayor_*.json`
- ✗ does not write to `GOVERNANCE/CLOSURES/` or `GOVERNANCE/TRANCHE_RECEIPTS/`

What it does write (only when authorized):
- **this file** (`docs/proposals/AUTORESEARCH_E11_E12_RECONCILIATION.md`) — non-sovereign
- (when run) the report at `docs/reports/AUTORESEARCH_E11_E12_RECONCILIATION_REPORT_V0.md` — non-sovereign

The verdict belongs to MAYOR, not to this proposal.

---

## §6. Proposer / Validator separation

- **Proposer**: claude-opus-4-7 main session, this Claude Code instance
- **Required validator** before MAYOR reads the report:
  - a fresh-context **peer-review** sub-agent (Rule 3: Proposer ≠ Validator)
  - validator re-runs §3 procedure independently and confirms the SHA
    diff table byte-for-byte
- **Verdict authority**: MAYOR (after operator countersignature on the report)
- **Reducer applies MAYOR's verdict** to the spine

The peer-review surface already exists at `oracle_town/skills/feynman/`
(per CLAUDE.md §"Layer 4"). Use it.

---

## §7. Out of scope for this proposal

This file does **not**:

- run the experiment
- write the report
- compute any SHA
- amend any receipt
- merge or delete any worktree
- open E13
- propose what AUTORESEARCH does after reconciliation completes
  (a follow-on proposal handles E13+ planning, gated on MAYOR's verdict)
- self-decide KEEP / REJECT (forbidden by `feedback_ralph_violations.md`)
- run a Ralph / W loop or any other automated decider
- promote any candidate to canon
- commit any change to git (until operator authorizes)
- push any change to a remote (until operator authorizes)

---

## §8. Promotion path

1. Operator review of this proposal
2. If accepted: operator authorizes execution of §3 procedure (read-only)
3. Experiment runs; report written to `docs/reports/`
4. Peer-review sub-agent (fresh context) re-validates the report
5. Operator countersigns the report
6. Report routed to MAYOR via `tools/helen_say.py "<report-summary>" --op dialog`
7. MAYOR rules: ACCEPT_RE_HASH / AMEND_WITH_SUPERSEDES / REVOKE_AND_RERUN
8. Reducer applies MAYOR's verdict via the canonical writer
9. **Only then** is E13 unblocked (or a re-run tranche proposed)

No step skipped. No step automated. No step decided by the proposer.

---

## §9. Final Receipt

```
authority:             NON_SOVEREIGN
canon:                 NO_SHIP
lifecycle:             PROPOSAL
implementation_scope:  RECONCILIATION_HYPOTHESIS_ONLY
implementation_status: NOT_IMPLEMENTED
commit_status:         NO_COMMIT (pending operator authorization)
push_status:           NO_PUSH  (pending operator authorization)
validator_required:    fresh-context peer-review (Rule 3)
verdict_authority:     MAYOR (after operator countersignature)
next_verb:             review reconciliation hypothesis
```
