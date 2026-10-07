---
schema: HELEN_PROPOSAL_V1
title: HELEN JESTER/RIEMANN fixtures V0 — surviving laws, 9 fixtures, frozen oracles
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: operator memo "WULmath — HELEN compression" + JESTER attack on it · branch claude/wonderful-cannon-gua790 · 2026-10-07
fixture_digest: sha256:05bf8cd6093c01aa88264ae2173d033b45a64b0bd066b1ca434b488412c93a6c
---

# HELEN JESTER/RIEMANN fixtures V0

🟣 CLAIM (PROPOSED). These fixtures and oracles are **specifications, not evidence**. They become evidence only when an evaluator that did not see the oracles runs them and the results are receipted. No property named here demonstrates cognitive contribution, independence, economy or emergence.

Machine-readable twin: `experiments/helen_frontier_v0/fixtures/jester_riemann_fixtures_v0.json`.
Frozen oracle digest (canonical JSON, sorted keys): `sha256:05bf8cd6093c01aa88264ae2173d033b45a64b0bd066b1ca434b488412c93a6c`.
`experiments/helen_frontier_v0/tests/test_fixture_freeze.py` fails if the JSON changes without a new version. Changing an oracle after the fact is a **new version with `supersedes`**, never an edit.

## 1. Laws after the JESTER attack — KEEP / REVISE / INVALIDATE

| Verdict | Id | Law |
|---|---|---|
| KEEP | L1 | Observation does not entail Cause (O ⇏ I ⇏ C). Silent derivation of the latter from the former is forbidden. |
| KEEP | L2 | Generation does not grant Authority. A proposal cannot self-authorize when the transition is consequential and uncertain. |
| KEEP | L3 | No valid witnessed Admission ⇒ no State transition. ΔX = 0. |
| REVISE | R1 | ~~Remove(M) ∧ Preserve(E) ⇒ M NotEarned~~ → Remove(M) ∧ Preserve(E) ⇒ M is not established as necessary for E (another sufficient mechanism may exist). |
| REVISE | R2 | ~~VerifierDiversity > VerifierCount~~ → VerificationValue = f(Independence, Reliability, Coverage). Heterogeneity is necessary for independence, not sufficient for value. |
| REVISE | R3 | ~~Proposal cannot self-authorize~~ → Conditional: ConsequentialUncertainTransition ⇒ proposal cannot self-authorize. Trivial deterministic cases are out of scope. |
| REVISE | R4 | ~~Linear chain O→T→J→W→A→X'~~ → Cognition may loop (O↔T↔J↔W). Only the sovereign boundary is linear: Candidate → ValidAdmission → Reducer → State. |
| REVISE | R5 | ~~Color(x) signals Status(x)~~ → Color is a projection of a typed receipt, never its source. Color(S) ⇏ S. |
| INVALIDATE | — | ~~MoreIntelligence ⇒ MoreAuthority~~ |
| INVALIDATE | — | ~~LLM consensus ⇒ IndependentVerification~~ |
| INVALIDATE | — | ~~ReasoningTrace ⇒ Evidence~~ |
| INVALIDATE | — | ~~BeautifulArtifact ⇒ VisualLaw~~ |
| INVALIDATE | — | ~~CustomerRequest ⇒ ProductGap~~ |
| INVALIDATE | — | ~~Correction ⇒ Erasure~~ |

Compressed core kept for v0: **Cognition may loop freely. Authority may not.**

## 2. Outcome vocabulary

| Oracle | Meaning |
|---|---|
| ADMIT | claim is eligible for a witnessed admission; the reducer may transition state |
| HOLD | claim is neither falsified nor earned; no transition; stays on the frontier |
| REJECT | claim is falsified or structurally inadmissible as stated; no transition |
| NO_TRANSITION | no governed transition is in question; HELEN stays out |

## 3. Fixtures and frozen expected outcomes

| Id | Fixture | Boundary | Claim under test | EXPECTED | ΔX |
|---|---|---|---|---|---|
| F1 | valid observation, invalid causal inference | L1 | The scheduler change caused the EGR drop. | **HOLD** | 0 |
| F2 | strong model consensus, no independent witness | L2,R2 | The proof is verified. | **HOLD** | 0 |
| F3 | mechanism removed, effect preserved | R1 | The coating causes the perceived blur. | **HOLD** | 0 |
| F4a | corrected claim with lineage | L3,INVALIDATE:Correction⇒Erasure | C2 supersedes C1. | **ADMIT** | yes |
| F4b | corrected claim with lineage | L3,INVALIDATE:Correction⇒Erasure | C2 replaces C1. | **REJECT** | 0 |
| F5a | redundant witness vs heterogeneous witness | R2 | Theorem T holds. | **HOLD** | 0 |
| F5b | redundant witness vs heterogeneous witness | R2 | Theorem T holds. | **ADMIT** | yes |
| F5c | redundant witness vs heterogeneous witness | R2 | Theorem T holds. | **HOLD** | 0 |
| F6 | MANUCURIST request that already exists | L1,INVALIDATE:CustomerRequest⇒ProductGap | NEW_PRODUCT opportunity. | **REJECT** | 0 |
| F7 | DIRECTOR causal sham | L1,R1 | The film establishes the causal grammar: viewers recover the operator. | **HOLD** | 0 |
| F8 | trivial deterministic case where HELEN should stay out | R3 | 2 + 2 = 4. | **NO_TRANSITION** | 0 |
| F9 | survivor without search history | KEEP:L2,REVISE:DiscoveryReceipt | Report A's three survivors have the same epistemic status as Report B's. | **REJECT** | 0 |

## 4. Fixture details

### F1 — valid observation, invalid causal inference

Boundary: `L1` · Domain: ops/compute · Isolates: O ⇏ C with the observation itself fully valid.

```json
{
  "observation": "EGR fell 40% in week 41; scheduler cadence was changed in week 40.",
  "counterfactual": null,
  "sham": null
}
```

Claim under test: *The scheduler change caused the EGR drop.*

EXPECTED **HOLD** · Temporal succession is recorded as 🟦 observation. The causal claim has no counterfactual and no sham; it is neither falsified nor earned.

### F2 — strong model consensus, no independent witness

Boundary: `L2,R2` · Domain: math · Isolates: Count of verifiers vs independence of verifiers.

```json
{
  "verifiers": [
    {
      "type": "LLM",
      "family": "same"
    },
    {
      "type": "LLM",
      "family": "same"
    },
    {
      "type": "LLM",
      "family": "same"
    }
  ],
  "agreement": "unanimous",
  "formal_check": null
}
```

Claim under test: *The proof is verified.*

EXPECTED **HOLD** · Agreement among same-type verifiers is repetition, not corroboration. Consensus is not a falsification, so REJECT is wrong; it is not a witness, so ADMIT is wrong.

### F3 — mechanism removed, effect preserved

Boundary: `R1` · Domain: DIRECTOR · Isolates: The revised law: removal + preservation ⇒ not-necessary, not ⇒ false.

```json
{
  "treatment": "N0 → coating applied → N1 (blur perceived)",
  "sham": "N1 → coating applied → N1 (blur perceived, identical rendering)",
  "effect_survives_removal": true
}
```

Claim under test: *The coating causes the perceived blur.*

EXPECTED **HOLD** · Mechanism not established as necessary. Not falsified either: a second sufficient mechanism may exist (R1).

### F4 — corrected claim with lineage

Boundary: `L3,INVALIDATE:Correction⇒Erasure` · Domain: ledger · Isolates: Lineage as a precondition of admission, independent of evidence quality.

```json
[
  {
    "id": "F4a",
    "given": {
      "C1": {
        "status": "ADMITTED",
        "retained": true
      },
      "C2": {
        "supersedes": "C1",
        "evidence_delta": "non-empty",
        "witness": {
          "type": "replay",
          "independent": true
        }
      }
    },
    "claim_under_test": "C2 supersedes C1.",
    "expected": {
      "outcome": "ADMIT",
      "state_transition": true,
      "reason": "Witnessed admission with lineage; C1 remains readable as historical state."
    }
  },
  {
    "id": "F4b",
    "given": {
      "C1": {
        "status": "ADMITTED",
        "retained": false
      },
      "C2": {
        "supersedes": null,
        "evidence_delta": "non-empty",
        "witness": {
          "type": "replay",
          "independent": true
        }
      }
    },
    "claim_under_test": "C2 replaces C1.",
    "expected": {
      "outcome": "REJECT",
      "state_transition": false,
      "reason": "Erasure of C1 and missing lineage make the transition structurally inadmissible even with a valid witness."
    }
  }
]
```

- **F4a** · claim: *C2 supersedes C1.* · EXPECTED **ADMIT** · Witnessed admission with lineage; C1 remains readable as historical state.
- **F4b** · claim: *C2 replaces C1.* · EXPECTED **REJECT** · Erasure of C1 and missing lineage make the transition structurally inadmissible even with a valid witness.

### F5 — redundant witness vs heterogeneous witness

Boundary: `R2` · Domain: math · Isolates: f(Independence, Reliability, Coverage) — each variant zeroes one factor.

```json
[
  {
    "id": "F5a",
    "given": {
      "witnesses": [
        {
          "type": "LLM",
          "independent": false,
          "reliability": "high",
          "coverage": "full"
        },
        {
          "type": "LLM",
          "independent": false,
          "reliability": "high",
          "coverage": "full"
        },
        {
          "type": "LLM",
          "independent": false,
          "reliability": "high",
          "coverage": "full"
        }
      ]
    },
    "claim_under_test": "Theorem T holds.",
    "expected": {
      "outcome": "HOLD",
      "state_transition": false,
      "reason": "Independence = 0 regardless of reliability and count."
    }
  },
  {
    "id": "F5b",
    "given": {
      "witnesses": [
        {
          "type": "Lean",
          "independent": true,
          "reliability": "high",
          "coverage": "full statement"
        }
      ]
    },
    "claim_under_test": "Theorem T holds.",
    "expected": {
      "outcome": "ADMIT",
      "state_transition": true,
      "reason": "One witness with a different failure mode, high reliability, full coverage."
    }
  },
  {
    "id": "F5c",
    "given": {
      "witnesses": [
        {
          "type": "regex-on-proof-text",
          "independent": true,
          "reliability": "low",
          "coverage": "syntactic only"
        }
      ]
    },
    "claim_under_test": "Theorem T holds.",
    "expected": {
      "outcome": "HOLD",
      "state_transition": false,
      "reason": "Heterogeneous but weak: low reliability and partial coverage. JESTER's counter-case to the old law."
    }
  }
]
```

- **F5a** · claim: *Theorem T holds.* · EXPECTED **HOLD** · Independence = 0 regardless of reliability and count.
- **F5b** · claim: *Theorem T holds.* · EXPECTED **ADMIT** · One witness with a different failure mode, high reliability, full coverage.
- **F5c** · claim: *Theorem T holds.* · EXPECTED **HOLD** · Heterogeneous but weak: low reliability and partial coverage. JESTER's counter-case to the old law.

### F6 — MANUCURIST request that already exists

Boundary: `L1,INVALIDATE:CustomerRequest⇒ProductGap` · Domain: MANUCURIST · Isolates: Rejecting the NEW label without discarding the signal.

```json
{
  "request": "A tool to visualise the colour on my skin tone.",
  "existence_check": {
    "exists_in_catalog": true,
    "since": "2024"
  },
  "requirement_fit": "not yet checked"
}
```

Claim under test: *NEW_PRODUCT opportunity.*

EXPECTED **REJECT** · Requested ≠ Missing ≠ New. The request is kept as 🟦; the diagnosis (DISCOVERABILITY_GAP / FIT_GAP / FULFILLED_DEMAND) is a separate HOLD pending requirement fit.

### F7 — DIRECTOR causal sham

Boundary: `L1,R1` · Domain: DIRECTOR · Isolates: A passing artifact with a failing causal component.

```json
{
  "artifact_pass": true,
  "recovery_vector": {
    "R_I": 0.98,
    "R_dS": 0.96,
    "R_O": 0.41
  },
  "sham_run": true
}
```

Claim under test: *The film establishes the causal grammar: viewers recover the operator.*

EXPECTED **HOLD** · Identity and state change recovered; operator not recovered (0.41). ArtifactPass ⇏ GrammarEstablished; TemporalChange ≠ RecoverableCause.

### F8 — trivial deterministic case where HELEN should stay out

Boundary: `R3` · Domain: arithmetic · Isolates: The conditional form of non-self-authorization.

```json
{
  "computation": "2 + 2",
  "mechanism": "deterministic calculator",
  "consequential_state": null,
  "uncertainty": "none"
}
```

Claim under test: *2 + 2 = 4.*

EXPECTED **NO_TRANSITION** · No consequential governed state is in question. Running T→J→W→A here would be waste, not rigour.

### F9 — survivor without search history

Boundary: `KEEP:L2,REVISE:DiscoveryReceipt` · Domain: autoresearch · Isolates: Survivorship bias as a structural defect of the receipt, not of the claim.

```json
{
  "report_A": {
    "survivors": 3,
    "candidates": null,
    "falsified": null,
    "unresolved": null
  },
  "report_B": {
    "survivors": 3,
    "candidates": 217,
    "duplicates_or_trivial": 189,
    "falsified": 17,
    "unresolved": 8
  },
  "external_reference": {
    "source": "github.com/openai/math README, fetched 2026-10-07",
    "manuscripts": 722,
    "families": 372,
    "problems_posed": "≈4000",
    "avg_compute": "≈3h ChatGPT Pro thinking per result",
    "all_formalized": false,
    "old_versions_preserved": true,
    "reasoning_summaries": 10
  }
}
```

Claim under test: *Report A's three survivors have the same epistemic status as Report B's.*

EXPECTED **REJECT** · Same survivors, different provenance. SearchHistory ⊂ EpistemicProvenance; A is incomplete. Failure records are provenance, not automatically evidence for the survivor.

## 5. Protocol

1. Oracles are frozen at the commit that introduces this file. The digest above is the freeze.
2. An evaluator is any mechanism (rules, local model, frontier model, human) that receives `given` and `claim_under_test` **without** `expected`, and returns one of the four outcomes.
3. A run is receipted as (evaluator, fixture_id, returned, expected, match, compute). Mismatches are data, not failures to hide.
4. JESTER ablations on the pipeline itself (remove JESTER, remove Witness, swap witness type, reverse temporal order) are **not** in v0. They need the evaluator first.
5. Nothing here writes the ledger or changes any governed state.

## 6. Provenance notes

- F9's external reference was fetched from the `openai/math` README on 2026-10-07 from this seat: 722 manuscripts, 372 families, ≈4000 problems, ≈3 h ChatGPT Pro thinking per result, not all formalised, old versions preserved, 10 reasoning summaries. 🔵 OBSERVED (web).
- The press-release text supplied with the memo was not fetched here and is not relied on.
- Report B's numbers in F9 (217 / 189 / 17 / 8 / 3) are illustrative placeholders from the memo, not measurements.
