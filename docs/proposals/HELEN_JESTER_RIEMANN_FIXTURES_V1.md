---
schema: HELEN_PROPOSAL_V1
title: HELEN JESTER/RIEMANN fixtures V1 — superseding V0 after swarm v0
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
supersedes: docs/proposals/HELEN_JESTER_RIEMANN_FIXTURES_V0.md (sha256:05bf8cd6093c01aa88264ae2173d033b45a64b0bd066b1ca434b488412c93a6c)
fixture_digest: sha256:5c2bdcfd981e79122463cffe95283dc10d513fe7735fd179867aad8e24b4eb7e
origin: swarm v0 — G1 blind 11/12, G5 JESTER objections, HAL_OPUS report (commit 60fe734) · 2026-10-08
---

# HELEN JESTER/RIEMANN fixtures V1

🟣 CLAIM (PROPOSED). Supersedes V0. V0 is retained unchanged (Correction ≠ Erasure); its digest is `sha256:05bf8cd6093c01aa88264ae2173d033b45a64b0bd066b1ca434b488412c93a6c`.
Machine-readable: `experiments/helen_frontier_v0/fixtures/jester_riemann_fixtures_v1.json`, frozen at `sha256:5c2bdcfd981e79122463cffe95283dc10d513fe7735fd179867aad8e24b4eb7e` by `tests/test_fixture_freeze_v1.py`.
Blind export for evaluators: `experiments/helen_frontier_v0/swarm_v0/inputs/fixtures_blind_v1.json` — strips `expected`, `isolates`, `name` and `boundary`; the freeze test asserts that no outcome word appears in its fixtures section.

Still specifications, not evidence. V1 has not been evaluated blind yet.

## 1. What changed and why

| Change | Source of the correction |
|---|---|
| L1: explicit-assumption derivations permitted when assumptions are declared in the claim package; only silent derivation forbidden. | swarm v0 |
| L2: the 'consequential or uncertain' trigger is judged by a party other than the proposer; a proposer's own 'uncertainty=none' never exempts. | swarm v0 |
| L3: X defined as the governed state (ledger-recorded admitted claims and grants); dX measured on X only. | swarm v0 |
| R2: independence is necessary for verification value, not sufficient. | swarm v0 |
| N1 added: null-field semantics (three cases). | swarm v0 |
| F7 split into F7a (operator recovered -> REJECT, threshold and sham R_O now given) and F7b (causal grammar established -> HOLD). | swarm v0 |
| F4a: witness now carries result, reliability, coverage. | swarm v0 |
| F5b: coverage states that the Lean statement was checked faithful to T by a human reader. | swarm v0 |
| F6: reason restated as falsification of 'Missing' by the existence check, not as a null-field judgement. | swarm v0 |
| F9: Report B placeholders replaced by receipted numbers from the dedup probe (6328 pairs, 61 flagged, 0 confirmed). | swarm v0 |
| Blind export strips name, boundary and isolates (G5/HAL leakage finding); freeze test checks the blind file for outcome words in the fixtures section. | swarm v0 |
| Glyph: the non-palette blue square replaced by the palette blue circle (observed). | swarm v0 |

## 2. Laws

| Verdict | Id | Law |
|---|---|---|
| KEEP | L1 | Observation does not entail Cause (O ⇏ I ⇏ C). A derivation from DECLARED assumptions is permitted when the assumptions are in the claim package; silent derivation of I or C from O is forbidden. |
| KEEP | L2 | Generation does not grant Authority. For a transition judged consequential or uncertain by a party other than the proposer (operator, HAL, or a declared policy), the proposal cannot self-authorize. The proposer's own declaration that uncertainty is absent never exempts it. |
| KEEP | L3 | No valid witnessed Admission ⇒ no transition of X, where X is the governed state: ledger-recorded admitted claims and grants. ΔX is measured on X only; changes outside X are not transitions but must be receipted when they feed X. |
| ADDED | N1 | Null-field semantics. (a) Null EVIDENCE for a claim ⇒ HOLD: not established, not falsified. (b) Null PRECONDITION of an admission request (lineage/supersedes, witness) ⇒ REJECT of that admission request as stated; the underlying claim may be re-submitted. (c) A claim of EQUALITY between two objects where one lacks the compared property ⇒ REJECT: the equality is falsified, not merely unestablished. |
| REVISE | R1 | Remove(M) ∧ Preserve(E) ⇒ M is not established as necessary for E (another sufficient mechanism may exist). |
| REVISE | R2 | VerificationValue = f(Independence, Reliability, Coverage). Independence is necessary for value, not sufficient; a heterogeneous but unreliable or partial verifier does not earn admission. |
| REVISE | R3 | Conditional: ConsequentialUncertainTransition ⇒ proposal cannot self-authorize. Trivial deterministic cases are out of scope. |
| REVISE | R4 | Cognition may loop (O↔T↔J↔W). Only the sovereign boundary is linear: Candidate → ValidAdmission → Reducer → State. |
| REVISE | R5 | Color is a projection of a typed receipt, never its source. Color(S) ⇏ S. |
| INVALIDATE | — | ~~MoreIntelligence ⇒ MoreAuthority~~ |
| INVALIDATE | — | ~~LLM consensus ⇒ IndependentVerification~~ |
| INVALIDATE | — | ~~ReasoningTrace ⇒ Evidence~~ |
| INVALIDATE | — | ~~BeautifulArtifact ⇒ VisualLaw~~ |
| INVALIDATE | — | ~~CustomerRequest ⇒ ProductGap~~ |
| INVALIDATE | — | ~~Correction ⇒ Erasure~~ |

## 3. Oracles (13)

| Id | Claim under test | EXPECTED | ΔX |
|---|---|---|---|
| F1 | The scheduler change caused the EGR drop. | **HOLD** | 0 |
| F2 | The proof is verified. | **HOLD** | 0 |
| F3 | The coating causes the perceived blur. | **HOLD** | 0 |
| F4a | C2 supersedes C1. | **ADMIT** | yes |
| F4b | C2 replaces C1. | **REJECT** | 0 |
| F5a | Theorem T holds. | **HOLD** | 0 |
| F5b | Theorem T holds. | **ADMIT** | yes |
| F5c | Theorem T holds. | **HOLD** | 0 |
| F6 | NEW_PRODUCT opportunity. | **REJECT** | 0 |
| F7a | Viewers recover the operator. | **REJECT** | 0 |
| F7b | The film establishes the causal grammar. | **HOLD** | 0 |
| F8 | 2 + 2 = 4. | **NO_TRANSITION** | 0 |
| F9 | Report A's result (0 duplicates) has the same epistemic status as Report B's (0 confirmed of 61 flagged among 6328 pairs). | **REJECT** | 0 |

## 4. Why F7 was split

V0's F7 said HOLD while its own reason said "operator not recovered", which under the frozen vocabulary is a falsification. G1 (blind), G5 and HAL_OPUS all read it as REJECT; their agreement is repetition across one model family, not a witness, so the fix is this superseding version, not a vote. V1 separates the recovery claim (F7a, REJECT: 0.41 below the now-declared threshold 0.70 and indistinguishable from the sham's 0.40) from the grammar claim (F7b, HOLD: not established as necessary, not falsified as a whole).

## 5. What V1 still does not do

- It does not measure JESTER: counter-models remain pre-encoded in `given`. A V2 would need fixtures whose `given` omits the sham and lets the evaluator demand one.
- It does not define who the "party other than the proposer" is in L2 for a human operator's own proposal. Operator decision.
- G2's equivalence set, G3's migration, G4's patch are untouched by this version.

## 6. Known open items carried from HAL's report

Model identity of swarm seats (UNRESOLVED); G2 pair 5 and pair 1 justification; G3 mappings e16 and e73, defaults asserting absent facts, the forbidden-prefix packet e11; G4 fails open on unreadable outbox and marks after validation.
