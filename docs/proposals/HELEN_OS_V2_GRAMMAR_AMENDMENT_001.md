# HELEN OS v2 — Grammar Amendment 001 (Proposal)

NO CLAIM — NO SHIP — PROPOSAL ONLY — CANDIDATE_AMENDMENT

```
artifact_type:         PROPOSAL_GRAMMAR_AMENDMENT
proposal_id:           HELEN_OS_V2_GRAMMAR_AMENDMENT_001
authority:             NON_SOVEREIGN
canon:                 NO_SHIP
lifecycle:             PROPOSAL
implementation_status: NOT_IMPLEMENTED
memory_class:          CANDIDATE_AMENDMENT
captured_on:           2026-04-27
amends:                docs/proposals/HELEN_OS_V2_INTERACTION_GRAMMAR.md
                       (commit 37a3c18, locked earlier today)
parent_proposal:       docs/proposals/HELEN_OS_V2_USER_CENTRIC_UX.md
sibling_proposals:     docs/proposals/FOCUS_MODE_TERMINAL_SPEC.md
                       docs/proposals/HELEN_OS_V2_VISUAL_CANON_LOCK.md
related_memory:        project_helen_os_v2_product_model.md
                       feedback_helen_mvp_kernel_scope.md
trigger:               operator observation 2026-04-27 — "the cognition was
                       ready before the interface existed; the model's voice
                       and the ledger's record must never be visually equivalent"
```

> **Why this exists**
> The grammar lock shipped today (commit `37a3c18`) is correct but not
> tight. After binding `gemma3:1b` (Ollama, running since 15:00) to the
> Focus CLI surface, the operator observed that cognition output and
> ledger receipts can render as visually equivalent lines. They are
> not. One is non-authoritative cognition; one is an immutable
> constitutional record. This amendment locks the discipline that
> separates them.

> **Three corollaries** (in order of leverage)
> 1. Visual non-equivalence — typography is doctrine
> 2. Provider provenance — `NO_PROVENANCE = NO_TRUST`
> 3. Cognition-waits-for-governance — observe before legislating

---

## §1. Stop-rule

This amendment defines doctrine. It does **not** implement provenance
fields, modify the ledger schema, write a symbolic classifier, edit
the renderer, change the kernel, promote anything to canon, or
commit. It tightens the grammar lock in a way the focus_cli
implementation must catch up to in a follow-up commit, gated on
operator authorization.

---

## §2. The structural observation (provenance)

Today's session built the constitutional surface — Focus CLI, receipt
loop, gate states — atop cognition that was already running before
that surface existed. `gemma3:1b` had been loaded and warm in Ollama
since 15:00. The AMP health check responded in 1ms because the
cognitive layer was live before it had anything to propose to.

The architecture *implies*: governance precedes cognition. You build
the rules before you deploy the model. What actually happened is the
inversion: cognition ran for hours in isolation, then governance
arrived and bound to it.

**The binding inherits a structural risk.** Ollama reports to
nothing. The ledger reports to the kernel. They share a process now
but live under completely different authorities. The Focus CLI is
running two independent authority chains and presenting them as one
surface. `(ollama)` and `seq=225 APPENDED` look like two lines of the
same thing. They are not.

This amendment closes the gap.

---

## §3. Corollary 1 — Visual non-equivalence rule

> **Hard rule**
> A cognition line and a receipt line must never be substitutable.
> The renderer must guarantee that no operator can mistake a model
> utterance for a ledger fact, by typography alone, with the labels
> stripped.

Label discipline (already in the grammar lock §4) is necessary but
not sufficient. Labels can be stripped, paginated past, color-disabled
in narrow terminals, or lost in scrollback. The visual invariant must
hold below the label.

### §3.1 Enforcement candidates (compose all four)

| # | Mechanism | Closes the failure mode |
|---|---|---|
| 1 | **Glyph exclusivity** — `⏚` is reserved for receipts. Cognition lines may never begin with it. | typography stripped to single-glyph |
| 2 | **Hash-shape exclusivity** — any line ending in a 12-hex suffix (`· abc123def456`) carries an actual `event_hash`. Cognition lines, by construction, cannot. | scrollback pagination |
| 3 | **Column separation** — cognition is left-margin body text; receipts are own-pill, right-aligned or footer. Operator scans by column, not by line. | color disabled |
| 4 | **Renderer assertion** — at write time: `assert (line_has_hash_suffix) ⇔ (line_is_receipt)`. Drift triggers test failure. | renderer fork |

All four belong. Each closes a different failure mode. Removing any
one re-opens at least one drift path.

### §3.2 Color band tightening

`HELEN_OS_V2_VISUAL_CANON_LOCK.md` §2.2 already reserves warm amber
for receipts and ledger. This amendment tightens that to an
**iff**: a line in amber **is** a receipt; a line not in amber is
**not** a receipt. Cognition uses body color (graphite / restrained
violet) — never amber.

---

## §4. Corollary 2 — Provider provenance (`NO_PROVENANCE = NO_TRUST`)

The grammar lock contains the constitutional invariant `NO RECEIPT =
NO CLAIM`. This amendment adds a sibling:

> **Hard rule**
> `NO_PROVENANCE = NO_TRUST.`
> Every receipt that records a proposal or a confirmation **must**
> name the non-sovereign origin of the cognition that produced the
> proposal. A receipt without provenance carries no trust.

### §4.1 Receipt payload extension (proposed)

The current Focus CLI receipt payload encodes the operator's
decision but not who proposed the action. The proposed extension:

```
EFFECT_PROPOSED (focus_action_proposed):
  payload:
    effect_kind:       focus_action_proposed
    proposal_index:    1
    label:             "Inventory inputs"
    description:       "..."
    proposed_by:       "ollama·gemma3:1b"     # NEW — non-sovereign origin
    proposed_by_class: "LOCAL_LLM"            # NEW — provider category
    cognition_hash:    "<sha256 of model+prompt+seed>"  # NEW — reproducibility
```

```
OPERATOR_DECISION (focus_action_confirmed):
  payload:
    effect_kind:    focus_action_confirmed
    chosen_index:   2
    label:          "Draft the deliverable shape"
    confirmed_by:   "operator"                # explicit — closes the chain
    proposed_by:    "ollama·gemma3:1b"        # carry-forward from the proposal
```

The chain becomes auditable end-to-end:
**cognition proposed → operator decided → ledger recorded**, with each
hop named and traceable.

### §4.2 Provider class taxonomy (proposed, candidate)

| Class | Examples | Trust posture |
|---|---|---|
| `LOCAL_LLM` | Ollama / `gemma3:1b`, llama.cpp, mlx | non-sovereign; deterministic given seed; no network egress unless explicit |
| `CLOUD_LLM` | Gemini, Anthropic, OpenAI | non-sovereign; network-bound; subject to remote-provider drift |
| `STUB_PLANNER` | `focus_cli/stub_plan()` (commit `e053bd6`) | deterministic; non-AI; documentation-class |
| `OPERATOR` | the human operator declaring intent | sovereign within the discipline; receipts authored by `OPERATOR` |
| `KERNEL` | the gate, reducer, runtime | sovereign; constitutional |

`STUB_PLANNER` exists because today's Focus CLI MVP uses one. The
class taxonomy makes the stub-vs-LLM distinction explicit at the
ledger level. A receipt with `proposed_by_class: STUB_PLANNER` is
demonstrably not yet bound to a real cognition.

### §4.3 Visual surfacing in Focus

The provenance is **always recorded** in the ledger payload. In Focus
Mode, a single short suffix on the proposal line:

```
proposals:
  1  Inventory inputs                        (gemma3:1b)
  2  Draft the deliverable shape             (gemma3:1b)
  3  Identify the first concrete step        (stub)
```

In Witness Mode, the full payload is visible. The visual goal is:
the operator never confuses a `STUB_PLANNER` proposal with a
`LOCAL_LLM` proposal — the surface tells them.

---

## §5. Corollary 3 — Symbolic classifier as the bridge layer

The split between free cognition (Ollama) and governed record
(ledger) is not a defect to hide. It is the **doctrine seam** the
symbolic classifier formalizes.

### §5.1 The classifier is not a filter

The classifier reads raw intent and emits:

```
{
  mode:       FOCUS | WITNESS | ORACLE | TEMPLE
  confidence: 0.0 .. 1.0
  reason:     "<short rationale>"
  provider:   <recommended provider for this intent>
}
```

Its job is **routing**, not gating. It chooses both the constitutional
surface (which mode owns this intent) and the cognition provider
(which model proposes for this intent). A meditative / sacred-toned
intent routes to ORACLE / TEMPLE — different surface, possibly
different provider, never the spine ledger.

### §5.2 The classifier is the load-bearing bridge

The grammar lock §1 names five arrows. The classifier sits at
**arrow 0** — pre-arrow, before `click → propose`:

```
intent → [classifier] → mode + provider → click → propose → ...
```

This is what makes the inversion (cognition arrived first) safe: the
binding surface, not the cognition, decides which authority chain
this intent is allowed to enter.

### §5.3 Build-path implication

Per the build path locked in doctrine point 10
(`feedback_helen_amp.md` chain):

```
[DONE] terminal kernel
[DONE] Focus Mode CLI               experiments/helen_mvp_kernel/focus_cli/
[ ]    HELEN AMP terminal module
[ ]    symbolic classifier          ← elevated by this amendment
```

The symbolic classifier is **next**, and per this amendment it is
**not a filter** — it is the bridge layer that closes the cognition /
governance seam. AMP can come after; the classifier is more
load-bearing.

---

## §6. Corollary 3-bis — Cognition-waits-for-governance deployment

PULL-mode AUTORESEARCH discipline (parent CLAUDE.md §"PULL-Mode
Tranche Discipline") says: observable signals only, one hypothesis
per epoch, halt before next opens. This amendment proposes the same
discipline applies to deployment of the symbolic classifier:

> **Don't write the rules in advance.** `gemma3:1b` is already
> running. Observe what it proposes across 20–30 intents. Classify
> the patterns empirically. Then write the symbolic classifier rules
> from what you observe — not from first principles.

This protects against the dual failure mode:
- writing classifier rules that don't match how the model actually
  proposes (rules-too-tight)
- writing classifier rules that pretend the model is constrained when
  it isn't (rules-too-loose)

Both fail differently; both fail. Observation-first lets the
classifier inherit the model's actual behavior shape.

---

## §7. Implementation status of `focus_cli` (as of commit `e053bd6`)

| Discipline | Compliant in current `focus_cli`? | Gap |
|---|---|---|
| Visual non-equivalence (§3) | partial | proposals labelled `1/2/3`; receipts use `⏚` and short hash; same column, same color, no renderer assertion |
| Glyph exclusivity (§3.1.1) | partial | `⏚` used only on ledger pill, but no formal ban on cognition lines using it |
| Hash-shape exclusivity (§3.1.2) | yes | only receipt lines carry hash suffixes |
| Column separation (§3.1.3) | partial | ledger is footer, proposals are body; weak |
| Renderer assertion (§3.1.4) | no | no test enforces the iff |
| Provider provenance (§4) | no | uses stub planner; no `proposed_by` field |
| Provider class taxonomy (§4.2) | no | not yet defined |
| Symbolic classifier (§5) | no | not yet built |

The MVP is a working demonstration of the **loop**, not yet a
demonstration of the **loop with full provenance discipline**. The
amendment proposes the gap; closing it is the next implementation
step (and a separate authorized commit).

---

## §8. Implementation order (recommended, not authorized)

If MAYOR / operator countersigns this amendment, the implementation
order that produces the smallest blast radius:

1. **Add `proposed_by` / `proposed_by_class` / `cognition_hash`
   fields to focus_cli payloads** (~30-line change to
   `experiments/helen_mvp_kernel/focus_cli/focus_cli.py`,
   reducer-compatible since payload is opaque to the existing
   reducer)
2. **Add renderer assertion §3.1.4** (10-line change + 1 test)
3. **Define provider class taxonomy in code** (small new file,
   `experiments/helen_mvp_kernel/focus_cli/providers.py`)
4. **Bind a real LOCAL_LLM provider** (Ollama / `gemma3:1b`), still
   inside the scope sandbox per `feedback_helen_mvp_kernel_scope.md`
5. **Observe 20–30 intents** (manual, operator drives — PULL-mode
   discipline)
6. **Draft the symbolic classifier from observations** (separate
   proposal-class artifact + scope-internal code)

Steps 1–4 are intra-`focus_cli`. Step 5 is observational, no code.
Step 6 is a new proposal.

---

## §9. Non-Goals

This amendment does **not**:

- modify the ledger schema in `helen_os/schemas/` (sovereign firewall)
- edit the existing `EFFECT_PROPOSED` / `OPERATOR_DECISION` event
  types (they accept opaque payloads — no schema change required for
  §4.1)
- implement provenance fields, the renderer assertion, the provider
  class taxonomy, or the symbolic classifier
- bind any cloud LLM provider
- make any commit or push without explicit operator authorization
- amend the parent grammar lock in-place (this is a separate
  amendment artifact, citation-linked)
- replace the §3 visual non-equivalence rule with a single mechanism
  (all four §3.1 mechanisms compose)

---

## §10. Promotion path

1. Operator review of this amendment
2. Fresh-context peer-review (Rule 3, Proposer ≠ Validator)
3. Operator countersignature
4. Routing to MAYOR via `tools/helen_say.py "<amendment-summary>"
   --op dialog` (kernel daemon now booted as of session 18:44)
5. MAYOR ruling: ACCEPT (amendment locked into v2 grammar) / AMEND
   / REJECT
6. If ACCEPT: implementation order in §8 begins, each step its own
   authorized commit

Until step 5, this is candidate amendment. Conform to it in any new
artifact; cite it in any review.

---

## §11. Final Receipt

```
authority:             NON_SOVEREIGN
canon:                 NO_SHIP
lifecycle:             PROPOSAL
implementation_scope:  GRAMMAR_AMENDMENT_DOC_ONLY
implementation_status: NOT_IMPLEMENTED
amends:                HELEN_OS_V2_INTERACTION_GRAMMAR (commit 37a3c18)
peer_review_required:  YES (Rule 3, Proposer ≠ Validator)
verdict_authority:     MAYOR (after operator countersignature)
commit_status:         NO_COMMIT (pending operator authorization)
push_status:           NO_PUSH  (pending operator authorization)
trigger:               operator structural-risk observation 2026-04-27
next_verb:             review grammar amendment 001
```
