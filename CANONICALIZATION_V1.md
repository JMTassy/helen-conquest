# CANONICALIZATION_V1

---

## A. Scope

This document defines canonical identity for JSON artifacts used by HELEN OS validation and routing.

It governs:

- canonical serialization,
- hash format,
- artifact identity,
- bundle identity,
- cross-artifact reference resolution,
- deterministic ordering of validation outputs.

This document does not define schema validity. Schema validity concerns structural shape only. Artifact identity is defined here.

**Law: schema validity is not artifact identity.**

---

## B. Canonical Serialization Rule

All canonical hashes are computed from canonical bytes obtained by serializing a parsed JSON value under the following rules.

### B.1 Encoding

- UTF-8 only.

### B.2 Objects

- Keys sorted in strict lexicographic order by Unicode code point.
- No duplicate keys permitted. If duplicate keys are encountered in raw input, canonicalization fails.

### B.3 Arrays

- Array order is preserved exactly as semantically supplied.
- Arrays are not sorted unless the governing artifact specification explicitly requires sorted order for that field.
- If a field is declared "sorted unique" by spec, that property must be validated separately by semantic validators; canonicalization itself does not reorder arrays.

### B.4 Whitespace

- No insignificant whitespace.
- Canonical output uses the minimal JSON form with no added indentation or line breaks.

### B.5 Strings

- Valid JSON strings only.
- Escaping must follow standard JSON escaping.
- Canonical serializer must emit semantically equivalent strings deterministically.

### B.6 Numbers

- Must be valid JSON numbers.
- Canonical serializer must emit minimal JSON representation.
- No NaN, Infinity, or non-JSON numeric values permitted.

### B.7 Literals

- `true`, `false`, `null` in standard lowercase JSON form only.

### B.8 Raw vs canonical bytes

- **Raw bytes**: exact input bytes as received.
- **Canonical bytes**: deterministic serialization of the parsed JSON value under B.1–B.7.

If parsing fails, canonicalization fails.

---

## C. Hash Format

All authoritative artifact hashes must use exactly this format:

```
sha256:<64 lowercase hexadecimal characters>
```

Examples:

- **valid**: `sha256:7f83b1657ff1fc53b92dc18148a1d65dfa135014...`
- **invalid**: uppercase hex
- **invalid**: missing `sha256:` prefix
- **invalid**: whitespace around hash
- **invalid**: alternate algorithms

**Law: only `sha256:<64 lowercase hex>` is accepted.**

---

## D. Hash Domains

Two hash domains are recognized.

### D.1 Raw hash

```
raw_sha256 = sha256(raw bytes)
```

### D.2 Canonical hash

```
canonical_sha256 = sha256(canonical bytes)
```

### D.3 Authoritative identity

Cross-artifact references must resolve against canonical hashes, not raw hashes.

**Law: all `*_ref` fields bind to `canonical_sha256` unless an artifact spec explicitly states otherwise. No current spec states otherwise.**

---

## E. Bundle Identity

Validation operates on a **bundle**.

A bundle is the complete set of artifacts submitted together for a single validation run, plus any explicitly named validated registry artifacts available to that run.

### E.1 Default rule

- References resolve only within the submitted bundle.

### E.2 External registry rule

- An external artifact may be resolved only if the validator is configured with an explicit validated registry.
- External registry artifacts must themselves be identified by canonical hash.

### E.3 Bundle determinism

Given the same bundle contents and the same canonicalization rules, validation results must be byte-identical.

---

## F. Reference Resolution

### F.1 Local handles vs global identities

- Local ids such as `N-*`, `E-*`, `RC-*`, `PKT-*` are artifact-local handles.
- Canonical hashes are cross-artifact identities.

### F.2 Resolution rules

- `claim_graph_ref` must equal the canonical hash of a valid CLAIM_GRAPH_V1 artifact.
- `tasp_report_ref` must equal the canonical hash of a valid TASP report artifact.
- `primary_claim_id` must resolve within the graph referenced by `claim_graph_ref`.
- `primary_claim_id` must identify a node whose `kind` is `claim`.
- A syntactically valid id that does not resolve is invalid.
- A resolvable id of the wrong kind is invalid.

### F.3 No ambiguous resolution

If more than one artifact could satisfy a reference, validation fails. Resolution must be unique.

### F.4 No raw-hash resolution

References may not resolve against `raw_sha256`.

---

## G. Deterministic Output Ordering

All validator outputs must be deterministically ordered.

### G.1 Errors

Errors sorted lexicographically by the tuple:

```
(code, node_id, edge_id, ref, message)
```

Missing fields in the tuple are treated as empty strings.

### G.2 Warnings

Warnings use the same ordering rule.

### G.3 Summary object

Summary fields must be emitted in fixed order:

1. `nodes`
2. `edges`
3. `claims`
4. `wild_text_nodes`
5. `admissible_claims`
6. `quarantined_nodes`

Additional fields, if later introduced, must be appended and documented.

### G.4 Hash reporting

When hashes are reported, emit in fixed order:

1. `raw_sha256`
2. `canonical_sha256`

### G.5 Time fields

If timestamps are emitted, they must either:

- be omitted, or
- be deterministically derived from the validation environment.

For byte-identical CI snapshots, omission is preferred.

---

## H. Rejection Rules

Validation fails immediately if any of the following occur:

1. JSON parsing failure
2. duplicate object keys
3. canonicalization failure
4. invalid hash format
5. unresolved `*_ref`
6. ambiguous reference resolution
7. mismatch between reference field and referenced artifact canonical hash
8. `primary_claim_id` missing from referenced graph
9. `primary_claim_id` resolving to non-`claim` node
10. any attempt to use raw hash as authoritative cross-artifact identity

---

## I. Validation Logs Required

Each validated artifact should emit deterministic identity logs with:

- `artifact_type`
- `schema_version`
- `raw_sha256`
- `canonical_sha256`
- `canonicalization_version`

Recommended canonicalization version string:

```
CANONICALIZATION_V1
```

---

## J. Non-Claims

This document does not define:

- schema shape,
- graph acyclicity,
- edge legality,
- quarantine routing law,
- admissibility semantics,
- scoring,
- routing thresholds.

Those belong to semantic validators and policy specifications.

---

**Document Version**: CANONICALIZATION_V1
**Status**: FROZEN
