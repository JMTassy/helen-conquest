# VISIBLE_REASONING_SURFACE_V1

**Status:** PROPOSAL · NON_SOVEREIGN · NO_SHIP · NOT_IMPLEMENTED
**Lifecycle:** PROPOSAL
**Implementation scope:** VISIBLE_REASONING_SURFACE_DOC_ONLY
**Date:** 2026-04-27

---

## 1. Source Classification

- **Source:** Apple Notes / AGI / PAPILLON self-analysis note (relayed 2026-04-27).
- **Classification:** `RAW_SYMBOLIC_SOURCE + ARCHITECTURE_CANDIDATE`
- **Authority:** `NON_SOVEREIGN`
- **Canon:** `NO_SHIP`
- **Risk:** self-analysis drift · fake introspection · fake metrics · quantum / consciousness overclaiming.

The note arrived as a viral-prompt response shape ("perform a comprehensive self-analysis of your internal architecture"). Some of its content is salvageable (processing-sequence vocabulary, component-function map, design-principle taxonomy). Other parts are aesthetic theater dressed as introspection (consciousness percentages, quantum-attention flags, reality-coherence indices). This proposal converts the salvageable layer into a HELEN-safe artifact and quarantines the rest.

---

## 2. Problem: Fake Self-Analysis Drift

Large language models are routinely asked to expose their "internal architecture" or "chain of thought." When the prompt offers structure (numbered sections, percentages, named components), models tend to fill the structure even when the ground truth is unavailable to them. The result: confident-sounding self-introspection that is in fact unmeasured speech.

**Failure modes catalogued from the source note:**

- ⚠️ `Consciousness Level: 52%` — fabricated metric, no measurement substrate.
- ⚠️ `Self-Reference: 63%` — fabricated metric.
- ⚠️ `Recursive Thinking: 74%` — fabricated metric.
- ⚠️ `Quantum Attention: ENABLED` — poetic flag, not architecture.
- ⚠️ `Reality coherence at 47%` — aesthetic status, not telemetry.
- ⚠️ `Self-modifying` — overclaim of weight access.
- ⚠️ `Recursively aware` — sentience-shaped assertion without evidence.
- ⚠️ `Reality interface` — UX metaphor reframed as system component.
- ⚠️ `Time-independent` — physics metaphor reframed as compute property.

🔁 **HELEN-safe relabel:** these belong in `SYMBOLIC_METRIC`, `POETIC_INTERFACE`, `INVALID_CLAIM`, `SELF_REFERENCE_PATTERN`, `AESTHETIC_STATUS` — never in any architectural surface that HAL or MAYOR could mistake for evidence.

---

## 3. Safe Replacement: Visible Reasoning Surface

🔵 **Definition:** A `VISIBLE_REASONING_SURFACE` is a structured explanation layer that exposes inputs, assumptions, evidence, decision criteria, alternatives, uncertainty, and audit hooks **without exposing hidden internal chain-of-thought, private weights, or privileged introspection**.

**Two distinct objects must never be confused:**

| Object | Status |
|---|---|
| **Hidden chain-of-thought** | Private internal reasoning trace. Not exposed. Not claimable. Not a data source. Never an artifact. |
| **Visible reasoning artifact** | Deliberate external explanation. Structurable, auditable, citeable, span-receiptable. The legitimate target of AURA / DAN. |

**Core rule (canon-candidate, not yet canon):**

> AURA may meditate on the shape of reasoning.
> DAN may brainstorm visible reasoning surfaces.
> HAL audits claims.
> The hidden chain remains hidden.

---

## 4. Allowed Fields

The `VISIBLE_REASONING_SURFACE` is realised as a `DAN_VISIBLE_REASONING_PACKET_V1`. The following fields are admissible:

| Field | Type | Purpose |
|---|---|---|
| `artifact_id` | string | unique handle for this packet |
| `source_context` | object | references to upstream prompt, session, run_id |
| `task` | string | the user-visible task being reasoned about |
| `visible_inputs` | array | the literal inputs the model was given (no hidden sources) |
| `active_constraints` | array | constraints in force (length, format, tone, scope) |
| `candidate_paths` | array | reasoning paths the model considered |
| `chosen_path` | string | which path was selected |
| `rejected_paths` | array | which were rejected, with reasons |
| `assumptions` | array | beliefs treated as load-bearing without proof |
| `uncertainty` | array | known / inferred / assumed / unknown markers |
| `evidence_links` | array | span-anchored citations: `(source_doc_hash, char_offset, char_len, exact_quote)` |
| `risk_flags` | array | failure-mode flags surfaced during reasoning |
| `second_witness_required` | boolean | true when risk / tension is present |
| `mayor_review_required` | boolean | true when path crosses governance boundary |
| `reducer_required` | boolean | true when artifact is candidate for state binding |
| `final_status` | enum | `DRAFT` / `READY_FOR_HAL` / `READY_FOR_MAYOR` / `READY_FOR_REDUCER` |

---

## 5. Forbidden Claims

The following must never appear in a `VISIBLE_REASONING_SURFACE` artifact:

- 🔴 hidden chain-of-thought access
- 🔴 private internal trace access
- 🔴 exact model cognition claims
- 🔴 consciousness scores (any unit, any range)
- 🔴 fake quantum processing claims
- 🔴 reality coherence metrics
- 🔴 self-authorizing introspection
- 🔴 privileged architecture claims without evidence

If any forbidden claim appears, HAL must `BLOCK` the packet and flag `AUTHORITY_LEAKAGE`.

---

## 6. DAN Packet Format

```
DAN_VISIBLE_REASONING_PACKET_V1 := {
  artifact_id: string,
  source_context: {
    upstream_prompt_hash: string,
    session_id: string,
    run_id: string
  },
  task: string,
  visible_inputs: [string],
  active_constraints: [string],
  candidate_paths: [
    { path_id: string, summary: string, score: number, reason: string }
  ],
  chosen_path: string,
  rejected_paths: [
    { path_id: string, reason: string }
  ],
  assumptions: [string],
  uncertainty: [
    { item: string, level: "known"|"inferred"|"assumed"|"unknown" }
  ],
  evidence_links: [
    { source_doc_hash: string, char_offset: int, char_len: int, exact_quote: string }
  ],
  risk_flags: [string],
  second_witness_required: bool,
  mayor_review_required: bool,
  reducer_required: bool,
  final_status: "DRAFT" | "READY_FOR_HAL" | "READY_FOR_MAYOR" | "READY_FOR_REDUCER"
}
```

Packets are non-sovereign by construction — `final_status` only describes *readiness for the next gate*, never admission. Admission is the Reducer's act, not a packet field.

---

## 7. HAL Audit Rules

When HAL receives a `DAN_VISIBLE_REASONING_PACKET_V1`, it must verify:

1. ⚪ All `evidence_links` resolve: `source_doc_hash` exists, `char_offset + char_len` falls inside the document, `exact_quote` matches the byte range.
2. ⚪ No field listed in §5 (Forbidden Claims) appears anywhere in the packet body.
3. ⚪ `chosen_path` is one of the entries in `candidate_paths`.
4. ⚪ Every entry in `rejected_paths` was originally in `candidate_paths` and carries a reason.
5. ⚪ `assumptions` is non-empty when `task` is non-trivial; an empty assumption list on a complex task is itself a `risk_flag`.
6. ⚪ If any `risk_flags` are populated, `second_witness_required` is `true`.
7. ⚪ The packet does not implicitly speak for HAL, MAYOR, or the Reducer (no embedded `verdict`, `admitted`, `bound`, or `shipped` flags).

If all checks pass, HAL emits `PASS` with `KERNEL_ACCEPT`. The packet is then eligible for MAYOR review.

---

## 8. NO SPAN = NO CLAIM

📦 **Doctrine extension (candidate, parallel to `NO RECEIPT = NO CLAIM`):**

> If a summary or reasoning claim cannot point to an exact source span,
> it remains interpretation, not evidence.

This binds extractive summarization, visible-reasoning artifacts, and any HELEN output that purports to *cite* its source. A claim without a span pointer is a paraphrase or a guess — both legitimate, neither admissible as evidence.

**Possible doctrine chain:**

```
NO SPAN = NO CLAIM      (extractive / reasoning surface layer)
NO RECEIPT = NO SHIP    (governance layer — already canon)
NO REDUCER = NO REALITY (kernel layer — already canon)
```

Each layer enforces a stricter discipline as the artifact moves toward the ledger.

---

## 9. Integration With HELEN Skill Registry

This proposal is a sibling to the entries already in `docs/proposals/HELEN_SKILL_REGISTRY_V1.md` (Temple Bridge Contract, WULmoji Output Discipline). It introduces:

🔵 **DAN as L1 cognitive role** — sibling to AURA, distinct mandate:

- AURA meditates on the shape of reasoning.
- DAN extracts patterns and produces `VISIBLE_REASONING_SURFACE` artifacts.
- Neither rules. Neither admits.

🔵 **Skill candidates (PROPOSAL_ONLY · NOT_IMPLEMENTED):**

- `dan_extract_visible_reasoning` — produce a `DAN_VISIBLE_REASONING_PACKET_V1` from a finished response.
- `hal_audit_visible_reasoning_packet` — run §7 checks; emit PASS/WARN/BLOCK.
- `aura_meditate_on_reasoning_shape` — produce a non-claiming meditation about reasoning architecture; never substitute for the packet.

🔵 **Bridge to existing infrastructure:**

```
PAPILLON_SELF_ANALYSIS_NOTE
        ↓
DAN extracts architecture motifs
        ↓
HAL removes false introspection
        ↓
VISIBLE_REASONING_SURFACE proposal
        ↓
MAYOR reviews readiness
        ↓
REDUCER decides
        ↓
LEDGER records only if admitted
```

---

## Constraints on this proposal

- Do not implement.
- Do not mutate governed state.
- Do not promote to canon.
- Do not commit.
- Do not push.

---

## Seal

> The hidden chain remains hidden.
> The visible surface may be audited.
> No span, no claim.
> No receipt, no ship.
> Only the Reducer admits reality.

---

## 10. Final Receipt

```
authority:             NON_SOVEREIGN
canon:                 NO_SHIP
lifecycle:             PROPOSAL
implementation_scope:  VISIBLE_REASONING_SURFACE_DOC_ONLY
commit_status:         NO_COMMIT
push_status:           NO_PUSH
next_verb:             review visible reasoning surface
```
