---
schema: HELEN_PROPOSAL_V1
title: HER-FABLE vision — HAL_OPUS supervising six Haiku goblins to turn FRONTIER v0 into first evidence
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: operator ask 2026-10-07 "ask her_fable to set up a vision for hal_opus to supervise a swarm of 6 goblins to execute new vision" · branch claude/wonderful-cannon-gua790
---

# HER-FABLE vision — swarm v0

🟣 CLAIM (PROPOSED). HER-FABLE proposes. HAL verifies. Goblins mutate inside their sandbox. The operator admits. No step below grants authority to any model.

## 0. Models, named exactly

| Role | Model id | Why |
|---|---|---|
| HER-FABLE (this seat) | claude-fable-5-1 | proposes the vision and the contracts; does not execute goblin tasks |
| HAL_OPUS | claude-opus-5-5 | verification needs the strongest reader; it emits admissibility *candidates*, never admissions |
| GOBLIN ×6 | claude-haiku-4-5-20251001 | the weakest sufficient mechanism for bounded, receipted artifact production. The operator wrote "Haiku 5.5"; no such model exists here, Haiku 4.5 is the latest |

Cost rule applied before launch (helen-os AGENTS.md @51a4109f): NewEvidence yes (FRONTIER v0 is frozen spec with zero evidence) · DecisionRelevant yes (whether FRONTIER proceeds) · Unresolved yes · Testable yes (each goblin has a checkable deliverable) · NotDuplicate yes. Frontier compute is used once, for verification, not for generation.

## 1. The vision in one line

**Turn FRONTIER v0 from frozen specification into first evidence, at the weakest sufficient cost, without any model gaining authority.**

Everything the swarm produces is a proposal file under `experiments/helen_frontier_v0/swarm_v0/<goblin>/` plus a `GOBLIN_RECEIPT_V0`. HAL_OPUS reads all of it and writes one `HAL_REPORT.md` with a verdict per goblin in {ADMIT_CANDIDATE, HOLD, REJECT}. Nothing is merged, admitted, or written to the ledger by the swarm.

## 2. The six goblins — six different jobs, one lane each

| Goblin | Job | Deliverable | Isolates |
|---|---|---|---|
| G1_BLIND_EVALUATOR | Evaluate the 12 oracles of `HELEN_JESTER_RIEMANN_FIXTURES_V0` **without seeing EXPECTED** (reads only `inputs/fixtures_blind.json`) | `blind_outcomes.json`: outcome + reason per fixture id | the first evaluator that did not write the oracles |
| G2_EQUIVALENCE_ANNOTATOR | From the 87 free-form outbox packets, annotate ≥ 10 pairs as EQUIVALENT-DISTINCTION or DIFFERENT-DISTINCTION with a one-line justification, **before** any evaluator exists | `equivalence_pairs.json` | the annotated set T8-strong needs |
| G3_OUTBOX_MIGRATION_PROPOSER | For the 86 packets rejected by the policy validator, propose a mapping of each free `finding_type` to the 6-value enum and list the missing required fields per packet. **Proposal only; no packet edited** | `migration_proposal.json`, `migration_proposal.md` | Correction ≠ Erasure: old packets stay, a proposal is versioned beside them |
| G4_SCANNER_PATCH_PROPOSER | Draft, as a patch file, the template-aware structural dedup check for `temple/autoresearch/autoresearch_scanner.py`, with a test. **Not applied**: `temple/` is outside the lane | `scanner_structural_dedup.patch`, `test_structural_dedup.py` | the weakest sufficient mechanism (a regex) made durable |
| G5_JESTER | Attack the three kept laws L1–L3 and the nine fixtures: for each, the minimal counter-model that removes the stated mechanism while preserving the apparent effect. No rescue of rejected claims | `objections.json`, `objections.md` | Remove(M) ∧ Preserve(E) ⇒ M not established as necessary |
| G6_REPLAY_WITNESS | Re-run every deterministic artifact of FRONTIER v0 (fixture digest, dedup probe tiers, test suite) and compare to the committed receipts byte for byte | `replay_receipt.json` | R0′ at its most local: zero-noise replay or a measured divergence |

Common rules for every goblin: write only inside its own directory; read anything else; never `git add`/`commit`; never touch `temple/`, `town/`, `helen_os/governance/`, `helen_os/schemas/`, `oracle_town/kernel/`, `GOVERNANCE/`; no network; every claim in the receipt names the file and line it rests on; `authority: false` on every file.

## 3. HAL_OPUS supervision contract

HAL_OPUS runs after all six goblins have returned. It:

1. Verifies each goblin's `GOBLIN_RECEIPT_V0` exists, is well-formed, and that `files_written` all lie in that goblin's directory (checked against `git status`, not against the goblin's word).
2. Re-derives every deterministic claim it can: G6's hashes, G1's outcomes against the frozen oracles (HAL may read the oracles; goblins may not), G3's mapping against the validator's enum, G4's patch against the real scanner file (dry-run `git apply --check`, never apply).
3. Scores G1 as (match / mismatch per oracle), and treats mismatches as **data about the oracles as much as about the evaluator**.
4. Reads G5's objections as JESTER output: which laws survive, which must be revised, which objections are invalid because they rescue a rejected claim or ignore the "not established as necessary" revision.
5. Emits per goblin: ADMIT_CANDIDATE (operator may admit as-is), HOLD (useful, incomplete, or unverifiable), REJECT (wrong, out of lane, or overclaims). With one sentence of reason and the evidence path.
6. Writes `swarm_v0/hal/HAL_REPORT.md` and `HAL_RECEIPT_V0.json`. Never edits goblin outputs. Never commits. Never says "admitted".

HAL_OPUS has no authority. Its verdicts are candidates for the operator. The pipeline that applies anything is the operator, by hand, on this branch.

## 4. What success looks like, and what it does not

Success: six receipts in lane, one HAL report, at least one goblin at ADMIT_CANDIDATE, G1's match/mismatch table existing at all (it is the first evidence the fixtures have ever produced), G6 reporting zero divergence or a named one.

Not success, and not claimed: cognitive contribution, independence of the six goblins (they share a model and a prompt author), economy (no token accounting is available from this seat beyond wall time), emergence. The swarm proves that bounded roles can produce receipted artifacts under supervision. Nothing more.

## 5. Known limits of this run

- Blindness of G1 is **by instruction, not by sandbox**: the subagent could open the oracle file. HAL checks the receipt's `inputs_read` and the report text for leakage; this is a weak check and is recorded as such.
- Six goblins on one model are not six independent witnesses. VerifierDiversity is not claimed.
- HAL_OPUS is a stronger model of the same family as the goblins. Its verification changes failure mode by role and by re-derivation, not by substrate.
