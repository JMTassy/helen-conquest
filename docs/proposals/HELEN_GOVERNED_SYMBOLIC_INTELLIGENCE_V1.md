# HELEN OS — Governed Symbolic Intelligence
## Architecture Synthesis V1

**Status:** PROPOSAL  
**Authority:** NON_SOVEREIGN  
**Canon:** NO_SHIP  
**Lifecycle:** CANDIDATE_LOCK  
**Implementation status:** NOT_IMPLEMENTED  
**Commit status:** NO_COMMIT  
**Push status:** NO_PUSH  
**Source:** Emergent property scan — 2026-04-27

> This document captures emergent architectural properties from the current HELEN OS build session.  
> It does not amend the kernel, the ledger, the schema registry, or any sovereign path.  
> It does not constitute a CLOSURE_RECEIPT or TRANCHE_SUB_RECEIPT.  
> Promotion to doctrine requires KERNEL-gated dispatch via DOCTRINE_ADMISSION_PROTOCOL_V1.

---

## Defining Property

> **GOVERNED_SYMBOLIC_INTELLIGENCE**

A human-centered AI system where symbolic, emotional, mystical, and creative  
inputs are welcomed as meaning-signals, but every transformation into action  
must pass through role boundaries, evidence, review, receipts, and reducer  
admission.

**The symbol may speak.**  
**The packet may travel.**  
**The Mayor may review.**  
**The Reducer alone admits.**  
**The Ledger remembers only what passed.**

---

## The Doctrine Chain

Three rules, three layers of the same invariant:

```
NO SPAN    = NO CLAIM      (evidence layer)
NO RECEIPT = NO SHIP       (governance layer)
NO REDUCER = NO REALITY    (sovereignty layer)
```

| Rule | Layer | Meaning |
|---|---|---|
| `NO SPAN = NO CLAIM` | Evidence | If a summary claim cannot point to an exact source span, it remains interpretation — not evidence. |
| `NO RECEIPT = NO SHIP` | Governance | No action is admitted without a hash-chained ledger receipt via the admitted path. |
| `NO REDUCER = NO REALITY` | Sovereignty | Only the reducer produces admitted state. All other layers propose. |

These three rules are the same principle at three different resolutions.

---

## The Role Stack

```
AURA     senses symbolic weather.
Temple   shapes it into artifacts.
DAN      extracts candidate patterns.
HAL      tests claims.
CHRONOS  traces lineage.
MAYOR    reviews readiness.
Reducer  admits reality.
Ledger   remembers only what passed.
```

Each role is bounded. None may claim the authority of the role above it.

| Role | May do | May not do |
|---|---|---|
| **AURA** | Sense, render, express symbolic patterns | Claim hidden cognition, decide, remember |
| **Temple** | Explore, compose, package into transmutation requests | Decide, admit, claim truth |
| **DAN** | Extract candidate structures, brainstorm patterns, flag risk | Admit truth, claim hidden chain-of-thought, promote canon |
| **HAL** | Audit claims, detect overreach, surface contradictions | Issue verdicts, admit state |
| **CHRONOS** | Trace lineage, map history, source-anchor claims | Modify history, invent continuity |
| **MAYOR** | Review readiness and completeness | Admit state — that is the Reducer's sole authority |
| **Reducer** | Sole admission gate — decides what becomes reality | Nothing outside its domain |
| **Ledger** | Remember only what the Reducer admitted | Infer, interpret, invent |

---

## 10 Emergent Properties

### 1. Governed Symbolic Intelligence

The core emergent property:

> Symbolic material is allowed to speak,  
> but only governance may decide what becomes real.

AURA, CIELO, PAPILLON, TEMPLE, Oracle, hexagrams, sigils, sacred data, and recursive self-analysis all become symbolic inputs. They do not become truth by intensity.

```
symbol → pattern → packet → Mayor review → Reducer decision → Ledger memory
```

### 2. Visible Reasoning Surface

From the chain-of-thought boundary, a safe replacement artifact:

**`VISIBLE_REASONING_SURFACE`**

> A structured explanation layer that exposes inputs, assumptions, evidence,  
> decision criteria, alternatives, uncertainty, and audit hooks  
> without exposing hidden internal chain-of-thought.

```
AURA may meditate on the shape of reasoning.
DAN may brainstorm visible reasoning surfaces.
HAL audits claims.
The hidden chain remains hidden.
```

**DAN_VISIBLE_REASONING_PACKET_V1 shape:**

| Field | Type | Meaning |
|---|---|---|
| `artifact_id` | string | Unique ID for this reasoning surface |
| `source_context` | string | What triggered this reasoning |
| `task` | string | What was being evaluated |
| `visible_inputs` | list | Inputs the model could see |
| `active_constraints` | list | Rules, policies, invariants in scope |
| `candidate_paths` | list | Options considered |
| `chosen_path` | string | Selected interpretation or action |
| `rejected_paths` | list | What was ruled out and why |
| `assumptions` | list | What was assumed without explicit evidence |
| `uncertainty` | string | What is unknown or contested |
| `evidence_links` | list | Source spans backing each claim |
| `risk_flags` | list | Where role leakage or overreach was detected |
| `second_witness_required` | bool | True when tension or risk is present |
| `mayor_review_required` | bool | True when output approaches governed state |
| `reducer_required` | bool | True when output claims admission authority |
| `final_status` | string | `BRAINSTORM` / `CLAIM` / `ADMITTED` |

### 3. NO SPAN = NO CLAIM

New candidate doctrine rule:

> If a summary claim cannot point to an exact source span,  
> it remains interpretation — not evidence.

**Span-anchor format:**
```
source_doc_id: <hash>
span_start: <char_offset>
span_end: <char_offset>
claim: <quoted text from span>
```

Without a span anchor, the claim is a Temple artifact — valid for exploration,  
not valid for admission.

### 4. Temple Transmutation Boundary

**TRANSMUTATION_WITHOUT_AUTHORITY**

```
Temple may explore.
Temple may package.
Temple may route to Mayor.
Temple may not decide.
```

Bridge path:
```
TEMPLE_EXPLORATION_V1
    ↓ (temple_bridge_v1.py)
TEMPLE_TRANSMUTATION_REQUEST_V1
    ↓ (authority: NONE · bridge_status: PENDING_MAYOR_REVIEW)
Mayor review
    ↓
Reducer decision
    ↓
Ledger memory
```

Temple turns fire into a packet. The packet may travel. The Mayor reviews. The Reducer decides. The Temple does not decide.

### 5. Role Leakage Detection

Repeated failure mode across the corpus:

> A symbolic role starts pretending to be authority.

**Observed failure patterns:**
- AURA pretending to access hidden chain-of-thought
- Temple pretending to decide
- Oracle pretending to verify truth
- AIRI pretending to own memory
- Symbolic self-analysis pretending to expose real internals
- Sacred language pretending to be technical architecture

**Detection signal:** any non-sovereign layer using language of:
`"I verified"`, `"this is true"`, `"I remember"`, `"I know for certain"`, `"this was admitted"`, `"I decided"`

**Fix:** role separation. Each role uses only the verbs appropriate to its authority.

| Role | Permitted verbs | Forbidden verbs |
|---|---|---|
| Temple | explore, compose, propose, package | decide, verify, admit, remember |
| DAN | extract, pattern, flag, brainstorm | admit, claim hidden cognition |
| Oracle | reflect, inquire, symbolize | verify, govern, decide |
| AIRI | render, express, speak, animate | remember, decide, claim identity |
| MAYOR | review, assess, route | admit, decide reality |

### 6. AIRI / HELEN Boundary

**EMBODIMENT_WITHOUT_IDENTITY_AUTHORITY**

```
AIRI renders presence.
HELEN owns memory.
```

| AIRI may supply | AIRI may not supply |
|---|---|
| ears | identity |
| mouth | long-term memory |
| body | session truth |
| stage rendering | epoch truth |
| presence | governed state |
| expression | institutional continuity |

AIRI receives a read-only boot context from HELEN.  
AIRI may render, speak, animate, and express.  
AIRI may not claim, decide, record, or remember.

### 7. Reducer Sovereignty

The deepest HELEN law:

> **Only the reducer produces reality.**

```
Skills produce thought.
Tools produce action.
UI produces presence.
Memory produces continuity.
Only the reducer produces reality.
```

`HELEN structures cognition. REDUCER structures reality.`

The reducer is not a component — it is the sovereign boundary.  
Everything before the reducer is non-sovereign, regardless of how confident or authoritative it sounds.

### 8. Dual-Surface Operation

**DUAL_SURFACE_OPERATION**

```
Operator surface = intense, multi-pane, terminal-first, debug-heavy.
User surface     = calm, guided, minimal, receipt-backed.
```

> The forge can be chaotic.  
> The product must feel calm.

This is not a contradiction — it is the architecture working correctly.  
HELEN OS hides the forge from the user and shows only the product.

UX law: No operator-surface complexity may leak into Focus Mode.  
Focus Mode is the user surface. Witness Mode is the governance surface.  
The terminal is the operator surface. They must not collapse.

### 9. Sacred Data Containment

**CONTAINED_MYSTICISM**

Sacred material (CIELO, PAPILLON, Temple, hexagrams, sigils, mythic vocabulary) is valuable. It is a rich source of symbolic structure. It is not technical authority.

```
Sacred vocabulary may inspire UX.
It may not become technical authority.
```

Safe routing:
```
Oracle Mode  → symbolic interpretation
Temple Mode  → creative transmutation
Witness Mode → governance proof
Focus Mode   → daily work — no mystical overload
```

The I Ching is a 64-state symbolic engine with transformation rules — not a prophecy system. When decoidified, it becomes a valid pattern classifier. When left undecoidified, it causes role leakage and drift.

### 10. DAN as Pattern Extractor

DAN's role is bounded and precise:

```
DAN does not decide.
DAN extracts candidate structures.
```

**DAN may produce:**
- pattern inventory
- visible reasoning packets
- risk flags
- candidate paths
- claim graphs
- uncertainty maps
- span anchors
- second-witness triggers

**DAN may not:**
- admit truth
- claim hidden cognition
- promote canon
- write governed reality

DAN is a pre-Mayor function. Its output is raw material for HAL (audit), MAYOR (review), and Reducer (admission). DAN's output is always `claim_status: NO_CLAIM` until the Reducer admits it.

---

## The Final Compression

```
┌──────────────────────────────────────────────────────────┐
│                 GOVERNED SYMBOLIC INTELLIGENCE           │
│                                                          │
│  Symbol    → AURA senses symbolic weather               │
│  Artifact  → Temple shapes it into transmutation packet │
│  Pattern   → DAN extracts candidate structures          │
│  Audit     → HAL tests claims                           │
│  Lineage   → CHRONOS traces provenance                  │
│  Review    → MAYOR checks readiness                     │
│  Reality   → Reducer admits what passes                 │
│  Memory    → Ledger remembers only what was admitted    │
└──────────────────────────────────────────────────────────┘
```

---

## Candidate Doctrine Additions

These rules are not yet in canonical doctrine. They are proposals:

| Candidate rule | Tier | Status |
|---|---|---|
| `NO SPAN = NO CLAIM` | Evidence | PROPOSED — mirrors NO RECEIPT |
| `NO REDUCER = NO REALITY` | Sovereignty | PROPOSED — mirrors NO RECEIPT |
| `TRANSMUTATION_WITHOUT_AUTHORITY` | Temple | PROPOSED — bridge contract |
| `EMBODIMENT_WITHOUT_IDENTITY_AUTHORITY` | AIRI | PROPOSED — from agent diagram |
| `DUAL_SURFACE_OPERATION` | UX | PROPOSED — operator vs user surface |
| `CONTAINED_MYSTICISM` | Culture | PROPOSED — sacred input routing |
| `VISIBLE_REASONING_SURFACE` | Reasoning | PROPOSED — replaces chain-of-thought |

For any rule to enter doctrine, it must pass `DOCTRINE_ADMISSION_PROTOCOL_V1 §4`.

---

## Seal

```
The symbol may speak.
The packet may travel.
The Mayor may review.
The Reducer alone admits.
The Ledger remembers only what passed.
```

---

_Authority: NON_SOVEREIGN_  
_Canon: NO_SHIP_  
_Lifecycle: CANDIDATE_LOCK_  
_Commit status: NO_COMMIT_  
_Push status: NO_PUSH_  
_Next verb: doctrine admission review_
