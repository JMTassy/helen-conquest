# G5_JESTER objections to the JESTER/RIEMANN fixtures V0

authority: false · ledger_effect: none · NON_SOVEREIGN · analysis by reading only; no evaluator was run.

Source: `docs/proposals/HELEN_JESTER_RIEMANN_FIXTURES_V0.md`, `experiments/helen_frontier_v0/fixtures/jester_riemann_fixtures_v0.json`, `experiments/helen_frontier_v0/README.md`.

Counts: laws STRONG 1 · WEAK 2 · FAILS 0. Oracles STRONG 4 · WEAK 6 · FAILS 2 (12 entries).

## 1. Strongest attacks first

### 1.1 L2 is gameable through its own trigger (STRONG)
L2 says a proposal cannot self-authorize "when the transition is consequential and uncertain". It never says who judges uncertainty. A proposer who declares `uncertainty: none` and `consequential: true` about its own transition falls outside the conditional, and L2 says nothing. Minimal counter-model: one boolean in the proposal. The same conditional is carried into R3, and F8 relies on the same proposer-asserted `uncertainty: none` field.
Revision: uncertainty and consequentiality are assessed by a non-proposer, and an unassessed transition defaults to uncertain. The law should also say whether an operator acting on their own proposal counts as self-authorization. It is silent on that case.

### 1.2 F4a's ADMIT rests on a witness the given does not describe (STRONG)
The witness is `{type: replay, independent: true}`. It has no result, no reliability and no coverage. R2's `f(Independence, Reliability, Coverage)` cannot be evaluated from it. A replay checks the evidence delta, but the claim is the lineage relation `supersedes`, which a replay does not check. The ADMIT is supported only by the reason text, which asserts that the witness covers lineage.
Alternative: HOLD.

### 1.3 F5b's ADMIT assumes the Lean statement is the theorem (STRONG)
`coverage: "full statement"` is coverage of the Lean statement. Nothing checks that the formal statement equals the informal Theorem T. Misformalisation is the standard way a Lean witness goes wrong. A single witness also has no comparison set, so `independent: true` is asserted, not tested. R2 says heterogeneity is not sufficient for value.
Alternative: HOLD, pending a faithfulness check.

### 1.4 F6's REJECT is a falsification whose falsifier is unchecked (STRONG)
NEW_PRODUCT is falsified only if an existing product fulfils the request. The field that would show fulfilment, `requirement_fit`, is "not yet checked". Existence in the catalog shows the request is not missing, not that the product fits. The oracle's own reason makes the diagnosis a HOLD pending fit. Under F1's rule ("neither falsified nor earned, so HOLD"), the output is HOLD.
Alternative: HOLD.

### 1.5 F7's HOLD depends on an unstated threshold (STRONG)
The reason reads `operator not recovered (0.41)`. That is a statement that the predicate "viewers recover the operator" is false. The given gives no recovery threshold. It also reports `sham_run: true` but not the sham's R_O, so the film's contribution over baseline is unmeasured. With a threshold of 0.5 and a sham R_O near 0.41, the claim is falsified.
Alternative: REJECT.

### 1.6 L1 is silent, not wrong, on explicit assumptions (WEAK)
L1 forbids *silent* derivation. An explicit derivation is not silent, so L1 allows it and returns no verdict. Counter-model: an observed series plus the change log, plus the stated assumption "no other input changed in weeks 39–41", plus a fitted model `EGR_t = f(cadence_{t-1})`. The claim follows explicitly, and L1 gives no answer on admissibility. "Entail" is also unspecified. Relative to an empty background O does not entail C, trivially. Relative to program semantics it can. The universal form "O does not entail C" is then false for that background.
Revision: split into L1a (non-entailment is relative to a named background) and L1b (an admissible causal claim needs an explicit intervention or counterfactual record; without one, HOLD). Note that F1's HOLD does not come from L1. It comes from the null-counterfactual rule, which is not stated anywhere.

### 1.7 L3's ΔX = 0 depends on what X is (WEAK)
Two counters. (a) F1's own fixture has the operator changing the scheduler in week 40 with no admission, so world state changes while HELEN's state does not. L3 holds only if X is HELEN's governed state, which the law does not define. (b) NO RECEIPT = NO CLAIM requires a ledger append for every action, and F1 says the observation is "recorded". If the ledger is in X, every HOLD or REJECT is a ΔX ≠ 0.
Revision: X is HELEN's governed claim-state. Receipts are append-only and outside X. External transitions enter only as observations.

### 1.8 Null-field outcomes are inconsistent across the oracle set (applies to F1, F2, F4b, F9)
The oracles map null fields to different outcomes:
- F1: `counterfactual: null`, `sham: null` gives HOLD.
- F2: `formal_check: null` gives HOLD.
- F4b: `supersedes: null` gives REJECT ("structurally inadmissible").
- F9: `candidates: null` and similar give REJECT.
No rule says what null means. This is the main reason the WEAK ratings below exist. The oracles are not wrong for any single fixture, but the set does not agree with itself.

### 1.9 F4b: replacement vs admission of C2 (WEAK)
The claim is "C2 replaces C1", so REJECT applies to the replacement. C2's own evidence and witness are identical to F4a's, and F4a's logic makes admitting C2 a transition. F4b says `state_transition: false`. That is consistent only if the rejected operation bundles C2's admission with erasing C1. The given does not say whether a non-superseding admission of C2 is allowed.
Alternative: ADMIT (C2 standalone) or HOLD.

### 1.10 F5a: HOLD needs an unstated necessity claim (WEAK)
R2 says heterogeneity is necessary for independence and not sufficient for value. It does not say independence is necessary for value. F5a's HOLD needs f(0, R, C) = 0. An additive f gives nonzero value from three non-independent high-reliability witnesses, and the outcome then depends on the choice of f.
Alternative: ADMIT under an additive f.

### 1.11 F3: the baseline and the removal path are not in the given (WEAK)
`N0 -> coating -> N1 (blur perceived)` does not state that N0 is sharp. If the blur predates the coating, "the coating causes the blur" is falsified. `effect_survives_removal: true` names no removal path, and no coating-free rendering appears in the fixture.
Alternative: REJECT.

### 1.12 F8: NO_TRANSITION gives no verdict on the claim under test (WEAK)
The claim is "2 + 2 = 4". NO_TRANSITION is a non-verdict on it. ADMIT is defined as eligible for witnessed admission, and nothing requires a transition for ADMIT, so an eligible claim with no transition is coherent. R3 says trivial cases are "out of scope", which is not the same as NO_TRANSITION. The inputs `consequential_state: null` and `uncertainty: none` are proposer-asserted, the same trust gap as L2.
Alternative: ADMIT.

### 1.13 F9: REJECT vs HOLD when provenance is missing (WEAK)
A's fields are null. That shows missing provenance, not unequal status. REJECT needs the "structurally inadmissible" branch of the vocabulary, which the oracle does not justify, and it conflicts with the F1/F2 null-to-HOLD mapping. Report B's numbers (217 / 189 / 17 / 8) are placeholders by the fixture doc's own section 6, so the comparison side is not measured.
Alternative: HOLD.

### 1.14 F5c: outcome survives, reason does not match the given (FAILS)
The reason text says "partial coverage". The given says `coverage: "syntactic only"`. Zero semantic coverage behaves like F5a's zero factor, and F5a gives HOLD, so the REJECT alternative contradicts F5a. R2 gives no threshold between weak and admissible, so HOLD vs ADMIT is undetermined by the law. Fix the reason text.

### 1.15 F2: HOLD survives (FAILS)
Three same-family LLM verifiers, unanimous, `formal_check: null`. Agreement is not falsification, and nothing is a witness. The only alternative (REJECT because a verified claim has no checkable artifact) reverses the null-to-HOLD rule F1 uses. No defensible alternative keeps the stated vocabulary.

## 2. Oracle table

| id | expected | strength | best alternative | the ambiguity in "given" |
|---|---|---|---|---|
| F4a | ADMIT | STRONG | HOLD | witness has no result, reliability or coverage; replay does not check lineage |
| F5b | ADMIT | STRONG | HOLD | "full statement" is the Lean statement, not T; no faithfulness check |
| F6 | REJECT | STRONG | HOLD | requirement_fit unchecked; existence alone does not falsify NEW |
| F7 | HOLD | STRONG | REJECT | 0.41 with no threshold; sham R_O not reported |
| F1 | HOLD | WEAK | REJECT | null counterfactual read as "not provided" vs "required and absent" |
| F3 | HOLD | WEAK | REJECT | N0 baseline not stated; removal path not given |
| F4b | REJECT | WEAK | ADMIT / HOLD | replacement vs admission of C2 standalone |
| F5a | HOLD | WEAK | ADMIT | f not specified; necessity of I for value unstated |
| F8 | NO_TRANSITION | WEAK | ADMIT | non-verdict on the claim; proposer-asserted uncertainty |
| F9 | REJECT | WEAK | HOLD | null is missing provenance, not inequality; placeholder numbers |
| F2 | HOLD | FAILS | (none defensible) | none beyond null-rule reversal |
| F5c | HOLD | FAILS | REJECT (contradicts F5a) | reason says "partial coverage", given says "syntactic only" |

## 3. Pipeline ablation

Method: a no-witness evaluator cannot produce ADMIT, since L3 requires a witnessed admission. A no-JESTER evaluator is one that reads `given` and does not generate counter-models.

- **Without Witness (W):** the frozen outcome is still matched for F1, F2, F3, F4b, F5a, F5c, F6, F7, F8, F9 (10 of 12 entries). Only F4a and F5b differ, and both are ADMIT. An evaluator that never admits passes 10 of 12. W is exercised by two entries, both ADMIT, and the oracle set cannot tell a witness step from a rule that never admits.
- **Without JESTER (J):** every counter-model result the frozen outcome needs is already pre-encoded in `given`: `counterfactual: null`, `sham: null`, `effect_survives_removal`, `sham_run`, `formal_check: null`, `exists_in_catalog`, `consequential_state: null`, and A's null fields. So all 12 entries are matched by a J-less evaluator that reads `given`. This is a prediction, not a measurement. Protocol section 5.4 keeps ablations out of v0. The oracles cannot measure J's contribution, and that is itself a finding.
  - Pre-encoded J output: F1, F2, F3, F6, F7, F8, F9.
  - J-irrelevant by construction: F4a, F4b, F5a, F5b, F5c.

## 4. Overclaims

1. `docs/proposals/EGREGOR_DISAMBIGUATION_V0.md` line 26: "verified". The evidence is that the text was located at 51a4109f. Section 3 says the predicate is not in code and application is not demonstrated. Use "located in".
2. `docs/proposals/EGREGOR_DISAMBIGUATION_V0.md` line 47: "establish" with "already an invariant in that codebase". The helen-os test files were read, not run, and helen-os is not in this checkout. Assertions show what a test checks, not that the invariant holds. Use "the test files assert". The "170-odd tests" count is also unverifiable from here.
3. `docs/proposals/HELEN_JESTER_RIEMANN_FIXTURES_V0.md` line 145: "ADMITTED". The given for F4a supplies C1's status as input with no admission receipt. Section 1 (R5) says a status is a projection of a typed receipt, never its source. The JSON twin (line 148) has the same string.
4. `docs/proposals/HELEN_JESTER_RIEMANN_FIXTURES_V0.md` line 168: "ADMITTED". Same defect for C1 in F4b. The JSON twin (line 171) has the same string.

## 5. Other defects (not overclaims)

- **Undefined glyph.** 🟦 appears at fixture doc lines 88 and 292 and JSON lines 85 and 288. The repo palette (fixture doc section 6 and the CLAUDE.md palette) is ⚫ 🔵 🟣 🟠 🟢 🟡 ⚪ 🔴. 🟦 is not defined. The doc uses 🔵 OBSERVED at line 377.
- **F5c reason mismatch.** "partial coverage" vs "syntactic only" (see 1.14).
- **F9 placeholders.** The comparison side uses numbers the doc itself calls placeholders.
- **Model field.** The brief specifies `claude-haiku-4-5-20251001`. The runtime identifies as claude-haiku-5-5. The receipt uses the specified value and says so.

## 6. Checks that passed

- The canonical digest of the JSON, computed with `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)` and SHA-256, equals `05bf8cd6093c01aa88264ae2173d033b45a64b0bd066b1ca434b488412c93a6c`. This matches the frontmatter and the constant in `tests/test_fixture_freeze.py`.
- The freeze commit `df93c30` (15:36 UTC) precedes the dedup probe `e89d0c8` (15:54 UTC). No evaluator commit precedes the freeze in this repo.
- The README's law counts (3 kept, 5 revised, 6 invalidated, 9 fixtures) match the JSON.

## 7. Limits

- No evaluator was run. Ratings are by reading the fixtures and their stated rules.
- `pytest` was not run, to avoid writing caches into the repo. The digest was reproduced with a standalone computation instead.
- The helen-os repo referenced in the EGREGOR doc is not in this checkout.
