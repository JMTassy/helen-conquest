# EDGE_LEGALITY_MATRIX_V1

---

## A. Scope

This document defines semantic legality for edges in CLAIM_GRAPH_V1.

It governs:

- which `(source_kind, edge_type, target_kind)` triples are allowed,
- which are forbidden,
- special restrictions on `wild_text`,
- the role of `policy`,
- the role of `receipt`,
- cycle law by subgraph.

This document is a semantic law document. It is not a JSON Schema.

**Law: schema shape does not determine graph legality.**

---

## B. Frozen Decisions on the Five Semantic Gaps

### B.1 Can `wild_text` support anything?

Yes, but only as contextual provenance, never as admissibility-bearing support.

Therefore:

- `wild_text -> claim` via `SUPPORTS` is allowed only as weak contextual support.
- A claim supported **only** by `wild_text` cannot become admissible.
- `wild_text` may never route to Mayor.
- `wild_text` is always `QUARANTINED`.

### B.2 Is `ROUTES` really a graph edge?

Yes, but only as a record of attempted or authorized routing state inside the graph model.

Therefore:

- `ROUTES` edges are allowed only from admissible `claim` nodes.
- `ROUTES` edges from `QUARANTINED` nodes are forbidden.
- `ROUTES` edges from `wild_text` are forbidden.
- `ROUTES` does not itself confer admissibility; it records graph-level routing relation.

### B.3 Can `policy` support or only gate?

`policy` may gate, not support.

Therefore:

- `policy -> claim` via `GATES` allowed.
- `policy -> artifact` via `GATES` allowed.
- `policy -> receipt` via `GATES` allowed.
- `policy -> *` via `SUPPORTS` forbidden.

### B.4 Can `receipt` refute?

Yes, if the receipt records a machine-checkable negative outcome.

Therefore:

- `receipt -> claim` via `REFUTES` allowed.
- `receipt -> artifact` via `REFUTES` forbidden unless a future spec explicitly introduces artifact-invalidating receipts.

### B.5 Are cycles allowed in any subgraph?

No cycles are allowed in the operational dependency structure.

Therefore:

- the subgraph induced by `DEPENDS_ON` must be acyclic,
- the subgraph induced by `SUPPORTS` must be acyclic,
- the combined subgraph on edges `{DEPENDS_ON, SUPPORTS, REFUTES, GATES, QUARANTINES, ROUTES}` must also be acyclic unless a future spec explicitly carves out an exception.

**Current law: the whole claim graph is treated as a DAG for validation purposes.**

---

## C. Node Kinds

The following node kinds are recognized:

- `claim`
- `evidence_handle`
- `artifact`
- `receipt`
- `witness`
- `policy`
- `definition`
- `wild_text`

---

## D. Edge Types

The following edge types are recognized:

- `SUPPORTS`
- `REFUTES`
- `DEPENDS_ON`
- `PRODUCES`
- `BINDS`
- `WITNESSES`
- `GATES`
- `QUARANTINES`
- `ROUTES`

---

## E. Allowed Edge Matrix

Below, each edge type lists all allowed triples.

### E.1 SUPPORTS

**Allowed:**

- `claim -> claim`
- `evidence_handle -> claim`
- `artifact -> claim`
- `receipt -> claim`
- `definition -> claim`
- `wild_text -> claim`

**Restrictions:**

- `wild_text -> claim` is contextual only and cannot be sole support for admissibility.
- `policy -> claim` via `SUPPORTS` forbidden.

All other `SUPPORTS` triples are forbidden.

---

### E.2 REFUTES

**Allowed:**

- `claim -> claim`
- `artifact -> claim`
- `receipt -> claim`
- `evidence_handle -> claim`

**Restrictions:**

- `wild_text -> claim` via `REFUTES` forbidden.
- `policy -> claim` via `REFUTES` forbidden.
- `receipt -> artifact` via `REFUTES` forbidden in V1.

All other `REFUTES` triples are forbidden.

---

### E.3 DEPENDS_ON

**Allowed:**

- `claim -> claim`
- `claim -> definition`
- `claim -> policy`

**Restrictions:**

- no `wild_text` participation in `DEPENDS_ON`
- no `artifact -> *` via `DEPENDS_ON`
- no `receipt -> *` via `DEPENDS_ON`

All other `DEPENDS_ON` triples are forbidden.

---

### E.4 PRODUCES

**Allowed:**

- `claim -> artifact`
- `witness -> receipt`

**Restrictions:**

- `wild_text` may not produce anything
- `policy` may not produce anything
- `receipt` may not produce anything

All other `PRODUCES` triples are forbidden.

---

### E.5 BINDS

**Allowed:**

- `evidence_handle -> artifact`
- `receipt -> artifact`
- `receipt -> claim`

**Restrictions:**

- `wild_text` may not bind
- `policy` may not bind

All other `BINDS` triples are forbidden.

---

### E.6 WITNESSES

**Allowed:**

- `witness -> receipt`
- `witness -> artifact`
- `witness -> claim`

**Restrictions:**

- `wild_text` may not witness
- `policy` may not witness

All other `WITNESSES` triples are forbidden.

---

### E.7 GATES

**Allowed:**

- `policy -> claim`
- `policy -> artifact`
- `policy -> receipt`

**Restrictions:**

- `claim -> *` via `GATES` forbidden
- `wild_text -> *` via `GATES` forbidden

All other `GATES` triples are forbidden.

---

### E.8 QUARANTINES

**Allowed:**

- `policy -> claim`
- `policy -> wild_text`

**Restrictions:**

- quarantine authority belongs to `policy` in V1
- `claim -> claim` via `QUARANTINES` forbidden
- `receipt -> claim` via `QUARANTINES` forbidden

All other `QUARANTINES` triples are forbidden.

---

### E.9 ROUTES

**Allowed:**

- `claim -> policy`

**Restrictions:**

- source `claim` must be `ADMISSIBLE`
- source `claim` must not be Tier III
- source `claim` must not be `QUARANTINED`
- `wild_text -> *` via `ROUTES` forbidden
- `policy -> *` via `ROUTES` forbidden
- `receipt -> *` via `ROUTES` forbidden

All other `ROUTES` triples are forbidden.

**Interpretation:** in V1, `ROUTES` records that an admissible claim is being routed under policy governance.

---

## F. Forbidden-by-Default Rule

Any `(source_kind, edge_type, target_kind)` triple not explicitly listed as allowed in Section E is forbidden.

**This rule is total.**

---

## G. Special Semantic Restrictions

### G.1 `wild_text`

- always `QUARANTINED`
- `route_to_mayor` must be `false`
- may appear in graph for provenance/context
- may not be sole support for admissibility
- may not participate in `DEPENDS_ON`
- may not originate `ROUTES`, `GATES`, `QUARANTINES`, `WITNESSES`, `BINDS`, or `PRODUCES`

### G.2 `policy`

- gates and quarantines
- does not support
- does not refute
- does not witness
- does not produce

### G.3 `receipt`

- may support a claim
- may refute a claim if it records a machine-checkable negative result
- may bind to artifact or claim
- may not itself route

### G.4 `evidence_handle`

- may support or refute claims
- may bind to artifacts
- does not gate
- does not route

---

## H. Cycle Law

### H.1 Global law

The graph must be acyclic.

### H.2 Operational interpretation

Cycle detection applies to the entire directed graph in V1.

### H.3 Consequence

Any directed cycle is invalid, regardless of edge type.

This is stricter than necessary in some future models, but is intentionally conservative for V1.

---

## I. Admissibility Consequences

The matrix alone does not confer admissibility. It only determines whether an edge is semantically legal.

In addition:

- a claim supported only by `wild_text` cannot become admissible,
- a Tier III claim cannot be routed,
- a quarantined node cannot originate a `ROUTES` edge,
- a syntactically legal graph may still fail other semantic validators.

---

## J. Validator Obligations

A semantic graph validator implementing this document must check:

1. every edge endpoint exists,
2. every edge triple is allowed by Section E,
3. all forbidden-by-default triples are rejected,
4. all Section G restrictions are enforced,
5. the graph is acyclic,
6. no quarantined node originates a `ROUTES` edge,
7. no Tier III claim originates a `ROUTES` edge,
8. no claim with only `wild_text` support is promoted to admissible.

---

## K. Suggested Stable Error Codes

These codes align with the current validator direction:

- `UNKNOWN_EDGE_ENDPOINT`
- `ILLEGAL_EDGE_TYPE`
- `ILLEGAL_DEPENDENCY_CYCLE`
- `WILD_ROUTING_VIOLATION`
- `TIER_PROMOTION_VIOLATION`
- `POLICY_QUARANTINE_ACTIVE`
- `MISSING_REQUIRED_SUPPORT`

If needed, add:

- `SOLE_WILD_SUPPORT_VIOLATION`
- `NON_ADMISSIBLE_ROUTE_VIOLATION`

---

## L. Non-Claims

This document does not define:

- JSON Schema shape,
- canonical hashing,
- artifact references by hash,
- scoring,
- routing thresholds,
- reducer decisions.

Those are governed elsewhere.

---

## M. One-line Operational Summary

**Generate freely upstream; admit only legal edges downstream.**

---

**Document Version**: EDGE_LEGALITY_MATRIX_V1
**Status**: FROZEN
