# SECOND_WITNESS_RECEIPT_V1

---

## A. Scope

This document defines the receipt schema for second-witness attestation as required by `TEMPLE_SANDBOX_POLICY_V1`.

A `SECOND_WITNESS_RECEIPT_V1` is the only mechanism by which a Temple Sandbox artifact that has triggered the second witness mandate may receive authorization for controlled external reference.

**Law: without a valid `SECOND_WITNESS_RECEIPT_V1`, no transcendence-sensitive Temple artifact may exit the Sandbox.**

This document governs:

- required fields and their constraints,
- validity rules,
- the machine-checkable authorization test,
- integration with `CLAIM_GRAPH_V1`,
- the JSON schema.

This document does not govern what makes an artifact true, whether an artifact becomes admissible, or Mayor scoring.

---

## B. Purpose

The Second Witness Mandate addresses the deepest leakage risk in the system: narrative beauty being mistaken for sovereign truth.

The receipt is not an aesthetic judgment. It is a machine-checkable authorization record binding a specific human-role verdict to a specific artifact hash.

---

## C. Required Fields

All fields listed below are required. No optional fields except `notes` and `witness_timestamp_basis`.

### C.1 `receipt_id`

- Pattern: `^RCPT-SW-[A-Z0-9_-]{6,}$`
- Must be unique across all receipts in the system
- Purpose: stable identifier for this specific attestation event

### C.2 `artifact_id`

- Type: string, non-empty
- Must resolve to an existing node within the claim graph
- Purpose: local handle identifying the artifact being witnessed

### C.3 `artifact_hash`

- Format: `sha256:<64 lowercase hex>` (per `CANONICALIZATION_V1`)
- Must equal `canonical_sha256` of the referenced artifact
- Purpose: canonical identity binding; raw hash is not authoritative

### C.4 `witness_role`

- Enum: `MAYOR | SENATE_MEMBER`
- `MAYOR`: the adjudicator / governance authority
- `SENATE_MEMBER`: a designated human senate member with witness authority
- Machine-only roles are not valid witness roles
- If `witness_role = SENATE_MEMBER`, the `senate_id` field is required

### C.4.5 `senate_id`

- Type: string, non-empty (required iff `witness_role = SENATE_MEMBER`)
- Purpose: identifies which designated senate member is witnessing
- Format: free text, human-assigned (e.g., "senate_member_jmt_001" or "sr_governance_001")
- If `witness_role = MAYOR`, this field must be omitted or null

### C.5 `witness_identity`

- Type: string, non-empty
- Purpose: specific identifier of the witness (human-assigned, not machine-generated)
- This field is informational; it does not substitute for cryptographic signing if signing is required by policy

### C.6 `verdict`

- Enum: `AUTHORIZED | REJECTED | DEFERRED`
- `AUTHORIZED`: the witness approves the declared scope of reference
- `REJECTED`: the witness denies external reference entirely
- `DEFERRED`: the witness requires more information before deciding; artifact remains in Temple

### C.7 `scope_of_reference`

- Type: string, non-empty
- Purpose: declares exactly what external use is authorized
- Must be narrow and specific

**Valid example:**
```
"allowed as wild_text node in CLAIM_GRAPH_V1 with no routing rights and no admissibility"
```

**Invalid example:**
```
"generally approved"
```

General authorizations are rejected. The scope must be machine-interpretable by the routing validator.

### C.8 `export_permission`

- Type: boolean
- Must be `true` if and only if `verdict = AUTHORIZED`
- Must be `false` if `verdict = REJECTED` or `verdict = DEFERRED`
- Enforced by schema `allOf` conditional

### C.9 `related_policy_id`

- Const: `TEMPLE_SANDBOX_POLICY_V1`
- Purpose: binds this receipt to its governing policy

### C.10 `notes` (optional)

- Type: string
- Purpose: human-readable narrative from the witness
- Narrative in `notes` does not grant permissions beyond what `verdict` and `scope_of_reference` specify
- Machine validators must ignore `notes` for authorization decisions

### C.11 `witness_timestamp_basis` (optional)

- Type: string or null
- Purpose: deterministic basis for timing if required (ledger entry number, block height, or other deterministic anchor)
- Wall-clock timestamps are not authoritative. If used for record-keeping, they must be supplementary only
- For byte-identical CI snapshots, `null` or omission is preferred

---

## D. JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SECOND_WITNESS_RECEIPT_V1",
  "type": "object",
  "required": [
    "receipt_id",
    "artifact_id",
    "artifact_hash",
    "witness_role",
    "witness_identity",
    "verdict",
    "scope_of_reference",
    "export_permission",
    "related_policy_id"
  ],
  "additionalProperties": false,
  "properties": {
    "receipt_id": {
      "type": "string",
      "pattern": "^RCPT-SW-[A-Z0-9_-]{6,}$"
    },
    "artifact_id": {
      "type": "string",
      "minLength": 1
    },
    "artifact_hash": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "witness_role": {
      "type": "string",
      "enum": ["MAYOR", "SENATE_MEMBER"]
    },
    "senate_id": {
      "type": ["string", "null"],
      "minLength": 1
    },
    "witness_identity": {
      "type": "string",
      "minLength": 1
    },
    "verdict": {
      "type": "string",
      "enum": ["AUTHORIZED", "REJECTED", "DEFERRED"]
    },
    "scope_of_reference": {
      "type": "string",
      "minLength": 1
    },
    "export_permission": {
      "type": "boolean"
    },
    "related_policy_id": {
      "type": "string",
      "const": "TEMPLE_SANDBOX_POLICY_V1"
    },
    "notes": {
      "type": "string"
    },
    "witness_timestamp_basis": {
      "type": ["string", "null"]
    }
  },
  "allOf": [
    {
      "if": {
        "properties": { "verdict": { "const": "AUTHORIZED" } },
        "required": ["verdict"]
      },
      "then": {
        "properties": { "export_permission": { "const": true } }
      }
    },
    {
      "if": {
        "properties": {
          "verdict": { "enum": ["REJECTED", "DEFERRED"] }
        },
        "required": ["verdict"]
      },
      "then": {
        "properties": { "export_permission": { "const": false } }
      }
    },
    {
      "if": {
        "properties": { "witness_role": { "const": "SENATE_MEMBER" } },
        "required": ["witness_role"]
      },
      "then": {
        "required": ["senate_id"],
        "properties": { "senate_id": { "type": "string", "minLength": 1 } }
      }
    },
    {
      "if": {
        "properties": { "witness_role": { "const": "MAYOR" } },
        "required": ["witness_role"]
      },
      "then": {
        "properties": { "senate_id": { "type": "null" } }
      }
    }
  ]
}
```

---

## E. Validity Rules

A receipt is valid if and only if all of the following hold:

1. `receipt_id` matches pattern `^RCPT-SW-[A-Z0-9_-]{6,}$`
2. `receipt_id` is unique across all receipts in the submitted bundle
3. `artifact_id` resolves to an existing node in the referenced claim graph
4. `artifact_hash` equals `canonical_sha256` of the referenced artifact (per `CANONICALIZATION_V1`)
5. `witness_role` is `MAYOR` or `SENATE_MEMBER`
6. If `witness_role = SENATE_MEMBER`, `senate_id` is non-empty; if `witness_role = MAYOR`, `senate_id` is null or omitted (enforced by schema `allOf`)
7. `export_permission` is `true` iff `verdict = AUTHORIZED` (enforced by schema `allOf`)
8. `scope_of_reference` is specific and non-empty
9. `related_policy_id` equals `TEMPLE_SANDBOX_POLICY_V1`
10. Schema validation passes

Any single failure invalidates the receipt.

---

## F. Machine-Checkable Authorization Test

An artifact is authorized for controlled external reference if and only if:

```
∃ receipt: SECOND_WITNESS_RECEIPT_V1 such that:
  receipt.artifact_hash == canonical_sha256(artifact)
  AND receipt.verdict == "AUTHORIZED"
  AND receipt.export_permission == true
  AND receipt.related_policy_id == "TEMPLE_SANDBOX_POLICY_V1"
  AND receipt validates against SECOND_WITNESS_RECEIPT_V1 schema
  AND receipt.artifact_id resolves within the referenced graph
```

If any condition fails: artifact remains in the Temple. Export is denied.

---

## G. What Authorization Grants

A valid `SECOND_WITNESS_RECEIPT_V1` with `verdict = AUTHORIZED` grants:

- External reference **strictly within** the declared `scope_of_reference`
- Nothing beyond what `scope_of_reference` specifies

It does **not** grant:

- Admissibility (the artifact remains `QUARANTINED` in `CLAIM_GRAPH_V1`)
- Routing to Mayor
- Tier promotion
- Sovereign truth

The artifact with a valid receipt may be referenced in another claim graph as a `wild_text` node under its declared scope. Its governance classification does not change.

---

## H. Integration with CLAIM_GRAPH_V1

In a claim graph, a `SECOND_WITNESS_RECEIPT_V1` is represented as:

```
Node:
  id:         RCPT-SW-<id>
  kind:       receipt
  admissibility: ADMISSIBLE   (the receipt itself is admissible)

Edges from this receipt node:
  WITNESSES → wild_text artifact node
  BINDS     → wild_text artifact node
```

The `wild_text` artifact node retains:
```
admissibility:  QUARANTINED
route_to_mayor: false
```

The receipt does not promote the artifact. It records the attestation.

---

## I. Non-Claims

This document does not define:

- Whether the witnessed artifact is true in any domain
- Whether the artifact becomes admissible or may route to Mayor (it cannot)
- Canonical hashing rules (governed by `CANONICALIZATION_V1`)
- Edge legality (governed by `EDGE_LEGALITY_MATRIX_V1`)
- Mayor scoring dimensions
- Reducer decision logic

---

**Document Version**: SECOND_WITNESS_RECEIPT_V1
**Status**: FROZEN
**Depends on**: CANONICALIZATION_V1, TEMPLE_SANDBOX_POLICY_V1, CLAIM_GRAPH_V1 schema
