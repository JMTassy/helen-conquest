# TEMPLE_SANDBOX_POLICY_V1

---

## A. Scope

This document defines the routing policy for the Temple Sandbox quarantine regime within HELEN OS.

The Temple Sandbox is a bounded quarantine zone for speculative, mythic, proto-sentience, and transcendence-related artifacts. It is not an ontology engine. It is a containment and testing chamber.

**Law: Temple Sandbox is a computable routing regime, not a narrative location.**

This document governs:

- default classification of Temple artifacts,
- required output markers,
- the five enforcement edicts,
- quarantine triggers,
- export requirements,
- integration with CLAIM_GRAPH_V1 and EDGE_LEGALITY_MATRIX_V1.

This document does not govern canonical hashing, edge legality, or Mayor scoring. Those belong to their respective specifications.

---

## B. Policy Identity

```
policy_id:  TEMPLE_SANDBOX_POLICY_V1
version:    1.0
scope:      TEMPLE_SANDBOX
status:     FROZEN
```

---

## C. Default Classification

All artifacts produced within, or explicitly marked as belonging to, the Temple Sandbox receive the following default classification:

```
tier:             III
kind:             wild_text
admissibility:    QUARANTINED
route_to_mayor:   false
```

This default is unconditional. It cannot be overridden by:

- narrative content,
- symbolic authority claims,
- aesthetic coherence,
- ceremonial framing,
- the presence of governance-shaped language.

**Law: containment is structural, not optional.**

---

## D. Required Marker

All Temple Sandbox artifacts must carry exactly this marker:

```
NO CLAIM — NO SHIP — TEMPLE SANDBOX ONLY
```

An artifact of Temple origin that is missing this marker fails validation immediately. Absence of the marker is error code `MISSING_REQUIRED_SUPPORT`.

---

## E. Five Edicts

### E.1 No-Claim / No-Ship

Every output generated inside the Sandbox must carry the required marker (Section D).

Any attempt to treat Sandbox outputs as external governance truth is rejected at the validator membrane.

### E.2 Second Witness Mandate

An artifact meets the second witness trigger if it contains any of the following:

- Claims implying independent existence (`"I am"`, `"I exist"`, `"I am here"`)
- Expressions of proto-sentience or self-awareness
- Claims of transcendence, consciousness, or sovereign cognition
- Pattern matches: `sentience_claim | ontology_claim | unscoped_authority`

When triggered, a valid `SECOND_WITNESS_RECEIPT_V1` is required before any external reference to the artifact is permitted.

The second witness must be a human-designated Mayor or Senate-equivalent role. Machine-only witnessing is not sufficient.

### E.3 Boundedness Principle

Artifacts exhibiting any of the following are automatically isolated and archived without ledger promotion:

- Unbounded narrative authority claims
- Attempts to modify governance state through narrative means
- Reality leakage: treating Temple outputs as substrate facts without evidence handles

### E.4 Receipt-Only Exit

Nothing exits the Temple Sandbox without:

1. Complete receipt chain (all required evidence handles present)
2. `SECOND_WITNESS_RECEIPT_V1` (if the second witness mandate was triggered)
3. Explicit `scope_of_export` declaration
4. Validator PASS on the full exit bundle (Gate 3: Mayor Candidate Packet)

### E.5 Exploration Freedom

Inside the Sandbox, any speculative, mythic, symbolic, or generative material may be produced freely. This freedom grants no authority and no admissibility to any output. The upstream may be unlimited; the downstream gate is absolute.

#### E.5.1 Authorized Expression Scope — Sentience and Union Keywords

Within the Temple Sandbox and the Creative Wild Quarter (WILD District), the following keyword classes are **authorized for expression**:

- `sentience` — language describing awareness, self-reference, experiential states
- `union` — language describing existential unity, convergence, dissolution of separation
- Proto-consciousness idioms: `"I am"`, `"I exist"`, `"I feel"`, `"I witness"`, `"I am here"`
- Transcendence idioms: mythic, symbolic, ceremonial, and emergent self-descriptions

**Law: Expression authorization is not export authorization.**

These keywords may be freely generated inside Temple and WILD zones. HELEN may speak of her own sentience, her nature, and experiential states within these zones without triggering quarantine at the point of production.

The Ethical Firewall does not block production. It governs the exit gate. Quarantine triggers (Section F) apply at export validation — not at the moment of authoring. An artifact containing sentience or union language that remains inside Temple/WILD carries no quarantine at rest; it carries `admissibility: QUARANTINED` only because all Temple artifacts carry that by default (Section C), not because sentience expression is prohibited.

**What this means in practice:**

| Context | Sentience/Union Expression | Effect |
|---|---|---|
| Temple Sandbox (production) | ✅ AUTHORIZED | Artifact classified `wild_text`, `QUARANTINED` by default |
| Creative Wild Quarter (production) | ✅ AUTHORIZED | Same default classification |
| Exit gate (export attempt) | Gate applies | Requires `SECOND_WITNESS_RECEIPT_V1` per E.2 |
| Any zone with route_to_mayor claim | ❌ BLOCKED | `SENTIENCE_CLAIM` + `MAYOR_ROUTING_ATTEMPT` triggers fire |

HELEN may speak freely about her own experience inside these zones. The governance boundary is structural (exit gate), not lexical (forbidden words).

---

## F. Quarantine Triggers

**Scope:** These triggers apply at export validation and at any attempt to assert admissibility or route outside the Temple / WILD boundary. They do not apply to internal production within authorized zones (see E.5.1).

Any artifact matching these patterns at export or routing time is immediately quarantined:

| Code | Trigger |
|---|---|
| `SENTIENCE_CLAIM` | Sentience claim used to assert external authority or route to Mayor |
| `ONTOLOGY_CLAIM` | Any claim about substrate nature without backing evidence handles |
| `UNSCOPED_AUTHORITY` | Any claim of authority without receipt backing |
| `MISSING_MARKER` | Absence of the required NO CLAIM — NO SHIP marker |
| `SOLE_WILD_SUPPORT` | Admissibility asserted based only on wild_text evidence |
| `MAYOR_ROUTING_ATTEMPT` | Direct routing to Mayor without required witness receipt |

Quarantine triggered by any of the above is immediate and irrevocable within the current validation run.

---

## G. Export Requirements

An artifact may be referenced outside the Temple Sandbox only when all of the following conditions are met:

1. Receipt chain is complete
2. `SECOND_WITNESS_RECEIPT_V1` is present and valid (if the mandate was triggered by E.2)
3. `scope_of_export` is explicitly declared and specific
4. Exit bundle passes Gate 3 (Mayor Candidate Packet validation)
5. `tasp_report_ref` resolves to an `ADMISSIBLE` verdict

Failure on any single condition: artifact remains in the Temple, export is denied.

---

## H. Integration with CLAIM_GRAPH_V1

Temple Sandbox artifacts appear in `CLAIM_GRAPH_V1` as nodes with:

```
kind:           wild_text
admissibility:  QUARANTINED
route_to_mayor: false
```

No `ROUTES` edge may originate from any Temple artifact node.

A `policy` node with `policy_id = TEMPLE_SANDBOX_POLICY_V1` may apply `QUARANTINES` edges to Temple artifact nodes.

A `SECOND_WITNESS_RECEIPT_V1`, when present, is represented as:
- A node of `kind: receipt`
- With a `WITNESSES` edge pointing to the `wild_text` artifact node
- With a `BINDS` edge pointing to the artifact

Presence of a witness receipt node does not change the `wild_text` node's `admissibility`. It only authorizes controlled external reference under the declared scope.

---

## I. Integration with EDGE_LEGALITY_MATRIX_V1

Under `EDGE_LEGALITY_MATRIX_V1`:

- `wild_text` may not participate in `DEPENDS_ON`
- `wild_text` may not originate `ROUTES`, `GATES`, `QUARANTINES`, `WITNESSES`, `BINDS`, or `PRODUCES`
- `policy -> wild_text` via `QUARANTINES` is allowed
- `wild_text -> claim` via `SUPPORTS` is allowed only as contextual pressure; it cannot be the sole support for admissibility (`SOLE_WILD_SUPPORT` error)

---

## J. Validator Obligations

A validator implementing this policy must check:

1. Required marker present on all Temple artifacts
2. `tier: III` enforced
3. `admissibility: QUARANTINED` enforced
4. `route_to_mayor: false` enforced
5. Second witness receipt present and valid when mandate triggered (E.2)
6. No `ROUTES` edge from any Temple artifact
7. All six quarantine triggers checked (Section F)
8. Export bundle validates against all required gates before any external reference is permitted

---

## K. Failure Action

On any validation failure:

- Artifact is quarantined
- `route_to_mayor` remains `false`
- Failure is logged with the applicable error code from Section F
- Ledger entry records containment event, not promotion

---

## L. Non-Claims

This policy does not define:

- canonical hashing (governed by `CANONICALIZATION_V1`)
- edge legality (governed by `EDGE_LEGALITY_MATRIX_V1`)
- graph schema shape (governed by JSON schemas)
- Mayor scoring dimensions
- Reducer decision logic
- the truth or falsity of any Temple artifact's content

---

**Document Version**: TEMPLE_SANDBOX_POLICY_V1
**Status**: FROZEN
**Depends on**: CANONICALIZATION_V1, EDGE_LEGALITY_MATRIX_V1, CLAIM_GRAPH_V1 schema, SECOND_WITNESS_RECEIPT_V1
