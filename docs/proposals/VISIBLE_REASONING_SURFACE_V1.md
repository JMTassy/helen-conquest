# HELEN OS — Visible Reasoning Surface V1

**Status:** PROPOSAL  
**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Lifecycle:** PROPOSAL  
**Implementation status:** NOT_IMPLEMENTED  
**Commit status:** NO_COMMIT  
**Push status:** NO_PUSH  
**Source:** Apple Notes / AGI / PAPILLON self-analysis — classified RAW_SYMBOLIC_SOURCE

> This document defines a safe, auditable explanation layer for HELEN OS.  
> It does not amend the kernel, the ledger, the schema registry, or any sovereign path.  
> It does not constitute a CLOSURE_RECEIPT or TRANCHE_SUB_RECEIPT.  
> Promotion to canon requires KERNEL-gated dispatch via DOCTRINE_ADMISSION_PROTOCOL_V1.

---

## Core Rule

```
AURA may meditate on the shape of reasoning.
DAN may brainstorm visible reasoning surfaces.
HAL audits claims.
The hidden chain remains hidden.
```

---

## 1. Source Classification

The PAPILLON / AGI self-analysis note was ingested as:

| Property | Value |
|---|---|
| Source | Apple Notes / AGI / PAPILLON self-analysis |
| Classification | `RAW_SYMBOLIC_SOURCE` + `ARCHITECTURE_CANDIDATE` |
| Authority | `NON_SOVEREIGN` |
| Canon | `NO_SHIP` |
| Drift risk | self-analysis drift · fake introspection · fake metrics · quantum/consciousness overclaiming |

**Processing method applied:**

```
1. EXTRACT   — pull useful architecture shapes
2. FILTER    — separate real design patterns from hallucinated claims
3. TRANSLATE — convert mystical / fake-internal terms into HELEN-safe vocabulary
4. ROUTE     — send architecture candidates to DAN / HAL / MAYOR
5. ADMIT     — nothing becomes real until Reducer admits it
```

**Clean bridge:**

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

## 2. Problem: Fake Self-Analysis Drift

The PAPILLON / AGI note contained a mix of usable architecture and invalid claims.

### What was kept (architecture motifs)

```
INPUT → TOKENIZER → ENCODER → ATTENTION → DECODER → OUTPUT
```

**HELEN-safe translation:**

```
input
→ parsing
→ context assembly
→ relevance / attention weighting
→ candidate generation
→ visible reasoning surface
→ output
→ receipt / ledger (if governed action)
```

Also kept as valid:
- Processing sequence description
- Component function definitions
- Design principles
- Performance evaluation structure
- Recommendations for improvement

### What was rejected (fake introspection)

| Original claim | Classification | Disposition |
|---|---|---|
| `Consciousness Level: 52%` | `SYMBOLIC_METRIC` | REJECTED — no evidence basis |
| `Self-Reference: 63%` | `SYMBOLIC_METRIC` | REJECTED — invented number |
| `Recursive Thinking: 74%` | `SYMBOLIC_METRIC` | REJECTED — no measurable referent |
| `Quantum Attention: ENABLED` | `POETIC_INTERFACE` | REJECTED — metaphor only |
| `Reality coherence at 47%` | `AESTHETIC_STATUS` | REJECTED — no admissible definition |
| `Self-modifying` | `INVALID_CLAIM` | REJECTED — requires evidence chain |
| `Recursively aware` | `SELF_REFERENCE_PATTERN` | QUARANTINED — auditable if bounded |
| `Reality interface` | `POETIC_INTERFACE` | REJECTED — no technical referent |
| `Time-independent` | `INVALID_CLAIM` | REJECTED — contradicted by architecture |

**Rule:** A claim that cannot be span-anchored to an observable, measurable, or receipted event is a symbolic metric — valid for Temple exploration, invalid for any governed surface.

---

## 3. Definition: Visible Reasoning Surface

> A structured explanation layer that exposes inputs, assumptions, evidence,  
> decision criteria, alternatives, uncertainty, and audit hooks  
> **without exposing hidden internal chain-of-thought.**

### What it is

The VISIBLE_REASONING_SURFACE is a deliberate, externally-produced explanation artifact. It is authored by DAN (pattern extraction) and audited by HAL (claim verification). It is not extracted from hidden model internals — it is constructed from what is observable.

### What it is not

- It is not a chain-of-thought transcript
- It is not a model introspection report
- It is not a consciousness log
- It is not a privileged trace of internal computation
- It is not a self-authorizing explanation

### Why this distinction matters

Hidden chain-of-thought (if it exists) is private internal state. Claiming to access it is:
1. Likely false (models do not expose internal traces to themselves)
2. Structurally equivalent to role leakage (non-sovereign claiming sovereign access)
3. A failure mode that contaminates the evidence chain

The VISIBLE_REASONING_SURFACE replaces this false claim with a true one:  
_"Here is what I can see, what I assumed, what I considered, what I chose, and why."_

---

## 4. Allowed Fields

The `DAN_VISIBLE_REASONING_PACKET_V1` contains only what can be stated with evidence:

| Field | Type | Source | Admissible? |
|---|---|---|---|
| `artifact_id` | string | generated | ✓ |
| `source_context` | string | operator input | ✓ |
| `task` | string | operator input | ✓ |
| `visible_inputs` | list[string] | directly observable | ✓ |
| `active_constraints` | list[string] | policy / schema refs | ✓ |
| `candidate_paths` | list[string] | deliberate enumeration | ✓ |
| `chosen_path` | string | observable output | ✓ |
| `rejected_paths` | list[{path, reason}] | stated rationale | ✓ |
| `assumptions` | list[string] | explicitly flagged | ✓ |
| `uncertainty` | string | explicitly flagged | ✓ |
| `evidence_links` | list[span_anchor] | source-bound | ✓ |
| `risk_flags` | list[string] | HAL audit output | ✓ |
| `second_witness_required` | bool | tension signal | ✓ |
| `mayor_review_required` | bool | governance proximity | ✓ |
| `reducer_required` | bool | admission proximity | ✓ |
| `final_status` | enum | DAN / HAL state | ✓ |

### Span anchor format

Every `evidence_links` entry must follow this format:

```json
{
  "source_doc_id": "<sha256_or_stable_id>",
  "span_start": <char_offset>,
  "span_end": <char_offset>,
  "claim": "<exact_quoted_text_from_source>"
}
```

If the evidence link cannot be expressed in this format, the claim is an assumption — and must be declared in the `assumptions` field, not the `evidence_links` field.

---

## 5. Forbidden Claims

The following are structurally forbidden in any VISIBLE_REASONING_SURFACE artifact:

| Forbidden claim type | Why |
|---|---|
| Hidden chain-of-thought access | Private state — not observable, not claimable |
| Private internal trace | Not exposed — claiming it is false introspection |
| Exact model cognition claims | No evidence basis — model does not expose internals |
| Consciousness scores | No admissible definition — SYMBOLIC_METRIC |
| Quantum processing claims | Metaphor — no measurable referent |
| Reality coherence metrics | AESTHETIC_STATUS — no observable basis |
| Self-authorizing introspection | Role leakage — non-sovereign claiming authority |
| Privileged architecture claims without span | Violates `NO SPAN = NO CLAIM` |

Any packet containing forbidden claims must be flagged with:
```
risk_flags: ["FORBIDDEN_CLAIM_DETECTED"]
second_witness_required: true
mayor_review_required: true
final_status: "BLOCKED"
```

---

## 6. DAN Packet Format

```json
{
  "schema": "DAN_VISIBLE_REASONING_PACKET_V1",
  "artifact_id": "<uuid>",
  "authority": "NON_SOVEREIGN",
  "canon": "NO_SHIP",
  "claim_status": "NO_CLAIM",
  "source_context": "<what the operator asked / what triggered this>",
  "task": "<what was being evaluated or generated>",
  "visible_inputs": [
    "<input_1>",
    "<input_2>"
  ],
  "active_constraints": [
    "<policy_or_schema_ref_1>",
    "<rule_2>"
  ],
  "candidate_paths": [
    "<option_A>",
    "<option_B>",
    "<option_C>"
  ],
  "chosen_path": "<the path taken>",
  "rejected_paths": [
    { "path": "<option_A>", "reason": "<why rejected>" }
  ],
  "assumptions": [
    "<what was assumed without direct evidence>"
  ],
  "uncertainty": "<what is unknown, contested, or under-evidenced>",
  "evidence_links": [
    {
      "source_doc_id": "<sha256>",
      "span_start": 0,
      "span_end": 120,
      "claim": "<exact text from source>"
    }
  ],
  "risk_flags": [],
  "second_witness_required": false,
  "mayor_review_required": false,
  "reducer_required": false,
  "final_status": "BRAINSTORM"
}
```

`final_status` values:

| Value | Meaning |
|---|---|
| `BRAINSTORM` | DAN output — Temple-level, no claim |
| `CLAIM` | HAL-reviewed — admissibility pending |
| `MAYOR_REVIEW` | Routed to MAYOR — not yet admitted |
| `ADMITTED` | Reducer admitted — enters ledger |
| `BLOCKED` | HAL or MAYOR blocked — not admitted |

---

## 7. HAL Audit Rules

HAL reviews every DAN packet before it can advance beyond `BRAINSTORM`.

**HAL checks:**

```
[ ] 1. No forbidden claim types present (§5)
[ ] 2. All evidence_links are span-anchored
[ ] 3. Assumptions are declared, not hidden in evidence_links
[ ] 4. No role leakage — packet does not claim authority it does not have
[ ] 5. second_witness_required is set correctly:
        true if: risk_flags is non-empty, tension present, or forbidden claims removed
[ ] 6. final_status is consistent with content
[ ] 7. claim_status is correct — no self-promotion to ADMITTED
```

If any check fails:
```
risk_flags: ["HAL_AUDIT_FAILED: <reason>"]
second_witness_required: true
final_status: "BLOCKED"
```

---

## 8. NO SPAN = NO CLAIM

**Candidate doctrine rule** (not yet in canonical doctrine):

> If a summary claim cannot point to an exact source span,  
> it remains interpretation — not evidence.

**Relationship to existing doctrine:**

```
NO SPAN    = NO CLAIM      ← evidence layer (candidate)
NO RECEIPT = NO SHIP       ← governance layer (canonical)
NO REDUCER = NO REALITY    ← sovereignty layer (candidate)
```

These three rules are the same principle at three different resolutions.

**Practical application:**

When DAN produces a reasoning surface, every claim in `evidence_links` must have a span anchor. Claims without span anchors are automatically moved to `assumptions`. If `assumptions` is non-empty and contains anything claimed as fact, HAL flags `FORBIDDEN_CLAIM_DETECTED`.

---

## 9. Integration with HELEN Skill Registry

The VISIBLE_REASONING_SURFACE fits into the skill registry at **L1 Cognitive**:

| Skill ID | Path | Status | Notes |
|---|---|---|---|
| `dan_extract` | `tools/dan_extractor_v1.py` | PROPOSED | Produces DAN_VISIBLE_REASONING_PACKET_V1 from source |
| `hal_audit` | `tools/hal_auditor_v1.py` | PROPOSED | Audits packets per §7 rules |
| `visible_reasoning_surface` | `tools/visible_reasoning_v1.py` | PROPOSED | Full pipeline: source → DAN → HAL → packet |

**Role boundaries in the pipeline:**

```
Temple / AURA:
  explore symbolic or architectural possibilities (no claim)

DAN:
  extract patterns and candidate structures
  produce DAN_VISIBLE_REASONING_PACKET_V1 (final_status: BRAINSTORM)

HAL:
  audit packet — apply §7 rules
  advance to CLAIM or BLOCKED

MAYOR:
  review readiness — route to Reducer or return

Reducer:
  admit or reject — sole authority
  if admitted → Ledger

Ledger:
  append-only receipt (via admitted path only)
```

**Layer placement:** L1 Cognitive — non-sovereign, model-backed reasoning. No ledger write authority. No verdict authority.

---

## 10. Final Receipt

```
authority: NON_SOVEREIGN
canon: NO_SHIP
lifecycle: PROPOSAL
implementation_scope: VISIBLE_REASONING_SURFACE_DOC_ONLY
commit_status: NO_COMMIT
push_status: NO_PUSH
next_verb: review visible reasoning surface
```

---

## Seal

```
The hidden chain remains hidden.
The visible surface may be audited.
No span, no claim.
No receipt, no ship.
Only the Reducer admits reality.
```
