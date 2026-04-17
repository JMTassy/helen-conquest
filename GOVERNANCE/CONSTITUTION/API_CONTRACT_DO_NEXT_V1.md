# API_CONTRACT_DO_NEXT_V1 — CONSTITUTIONAL LAW

**Status:** FROZEN
**Version:** 1.0.0
**Date Frozen:** 2026-04-05
**Scope:** /do_next endpoint request and response schema

---

## 0. Dependencies

This constitution depends on:

- **DISPATCH_DECISION_TABLE_V1** (routing decisions; status codes map to routing outcomes)
- **SESSION_PERSISTENCE_SEMANTICS_V1** (session_id format and semantics)

This contract is consumed by:

- All clients calling /do_next endpoint
- HELEN kernel (as input/output boundary)
- Session management (session_id handling)
- Audit and dispatch layers (response field validation)

---

## 1. Purpose

API_CONTRACT_DO_NEXT_V1 freezes the request and response schema for the /do_next endpoint. It is the constitutional contract for what may enter and leave the HELEN kernel at the step-4 boundary.

**Principle:** The API contract is the gateway. Everything crossing it must conform to frozen shape, frozen semantics, and frozen status code meaning.

This contract freezes:
- Request schema (11 fields, exact types, constraints)
- Response schema (9 fields, exact types, constraints)
- Status codes and their meanings (200, 400, 401, 500 only)
- Error response model
- Forbidden patterns (unknown fields, type violations, invalid enums)
- Versioning rules for schema changes
- Required freeze-tests

---

## 2. Formal Contract Model

```
APIContract = (
  request_schema: DoNextRequest,
  response_schema: DoNextResponse,
  status_codes: StatusCodeMapping,
  error_model: ErrorResponse,
  idempotence_property: CallIdempotence,
  forbidden_patterns: ProhibitedRequests,
  versioning: VersioningRules
)
```

---

## 3. Request Schema (DoNextRequest) (Frozen)

```json
DoNextRequest = {
  "session_id": string (required, alphanumeric + underscore, max 256 chars),
  "user_input": string (required, non-empty, max 10000 chars),
  "mode": enum (required, "deterministic" | "bounded" | "open"),
  "model": string (required, valid model identifier),
  "project": string (optional, max 256 chars),
  "max_context_messages": int (optional, >= 1, <= 100),
  "include_reasoning": bool (optional, default false),
  "temperature": float (optional, range [0.0, 2.0], default 0.7),
  "top_p": float (optional, range [0.0, 1.0], default 0.95),
  "seed": int (optional, >= 0)
}
```

### 3.1 Field Semantics (Frozen)

- **session_id:** Unique session identifier. Immutable once set. Alphanumeric and underscore only. If session does not exist, creates new session. If exists, resumes session (per SESSION_PERSISTENCE_SEMANTICS_V1).
- **user_input:** The user's prompt or query. Required and non-empty. Max 10,000 characters.
- **mode:** Execution mode. Three allowed values only: "deterministic" (frozen behavior), "bounded" (limited exploration), "open" (full exploration). Other values are invalid.
- **model:** LLM model identifier. Must be a valid model from INFERENCE_POLICY_FROZEN_V1. Frozen at request time.
- **project:** Optional project identifier for multitenancy. Used for logging and audit scope.
- **max_context_messages:** Maximum number of prior messages to include in context. Must be >= 1 if provided. Capped at 100.
- **include_reasoning:** Whether to include reasoning trace in response (if model supports it). Boolean only.
- **temperature:** Sampling temperature. Range 0.0–2.0. Frozen at request time.
- **top_p:** Nucleus sampling parameter. Range 0.0–1.0. Frozen at request time.
- **seed:** Random seed for deterministic inference. Integer >= 0. Optional; if omitted, provider default used.

### 3.2 Validation Rules (Frozen)

Every /do_next request must satisfy:

1. ✅ All required fields present (session_id, user_input, mode, model)
2. ✅ All fields have correct types (string, enum, int, float, bool)
3. ✅ session_id format matches (alphanumeric + underscore, max 256)
4. ✅ user_input is non-empty and <= 10000 chars
5. ✅ mode is exactly one of three values
6. ✅ model is a valid identifier
7. ✅ max_context_messages >= 1 if provided
8. ✅ temperature is 0.0–2.0 if provided
9. ✅ top_p is 0.0–1.0 if provided
10. ✅ seed is >= 0 if provided
11. ✅ No unknown fields in request

**Violation:** Any validation failure returns 400 (Bad Request).

---

## 4. Response Schema (DoNextResponse) (Frozen)

```json
DoNextResponse = {
  "session_id": string (required, echo of request),
  "mode": string (required, echo of request mode),
  "model": string (required, echo of request model),
  "reply": string (required if 200, null if 400/401/500),
  "receipt_id": string (required if 200, uuid4; null if 400/401/500),
  "run_id": int (required if 200, >= 0; null if 400/401/500),
  "context_items_used": array[string] (required if 200, may be empty; null if 400/401/500),
  "epoch": int (required if 200, >= 0; null if 400/401/500),
  "continuity": float (required if 200, range [0.0, 1.0]; null if 400/401/500)
}
```

### 4.1 Field Semantics (Frozen)

- **session_id:** Echo of request session_id. Identifies which session this response belongs to.
- **mode:** Echo of request mode. Confirms which mode was executed.
- **model:** Echo of request model. Confirms which model was used.
- **reply:** The LLM's reply text (if execution succeeded). Null on error.
- **receipt_id:** UUID identifying the CONCLUSION receipt for this call. Null on error. Used for audit traceability.
- **run_id:** Total number of /do_next calls in this session (monotonically increasing). Null on error. Same as session.run_count.
- **context_items_used:** Array of identifiers of context items (prior messages, facts, etc.) that were included in the LLM context. May be empty if no context was used. Null on error.
- **epoch:** Global monotonic counter (per EPOCH_LAW_V1). Identifies causality order across all sessions. Null on error.
- **continuity:** Session maturity score (0.0–1.0, per SESSION_PERSISTENCE_SEMANTICS_V1 §4). Null on error.

---

## 5. Status Codes (Frozen)

Only four HTTP status codes are permitted:

| Code | Meaning | When Used | Response Body |
|------|---------|-----------|----------------|
| 200 | Success | Request accepted, kernel executed or deferred | Full DoNextResponse with all fields |
| 400 | Bad Request / Audit Block | Request validation failed OR audit blocked (REJECT) | ErrorResponse object |
| 401 | Unauthorized | Session authentication failed | ErrorResponse object |
| 500 | Server Error | Infrastructure failure (persistence, inference provider, etc.) | ErrorResponse object |

**Forbidden:** 201, 202, 204, 301, 302, 304, 400 (with success body), 403, 404, 429, any 3xx redirection.

---

## 6. Error Response Model (Frozen)

```json
ErrorResponse = {
  "detail": string (required, human-readable error message, max 1000 chars)
}
```

**Semantics:**
- **detail:** Explanation of the error. Must be deterministic (same error condition = same message).
- No other fields in error response.
- No nested objects.
- No error codes beyond "detail" field.

**Examples:**
- `{"detail": "VALIDATION_ERROR: session_id format invalid"}`
- `{"detail": "AUDIT_BLOCK: finding code UNSUPPORTED_CLAIM prevents execution"}`
- `{"detail": "PERSISTENCE_FAILURE: session state could not be written"}`

---

## 7. Idempotence Properties (Frozen)

The /do_next endpoint is **not idempotent in the strong sense**.

**Definition:**
- Same request → different run_id (each call increments run_count)
- Same request → different receipt_id (each call generates new receipts)
- Same request → same canonical reply content (assuming deterministic inference policy)

**Implication:**
- Retry with identical request is safe (idempotent at the semantic level)
- But run_id and receipt_id will differ on retry
- Session state will reflect the additional call (run_count incremented)

**Use for fault tolerance:**
- Safe to retry on network failure (before response received)
- Not safe to retry after response received (will double-count the call)

---

## 8. Forbidden Patterns (Frozen)

These request patterns are absolutely prohibited and must return 400:

1. ❌ **Unknown field in request:** Request contains field not in schema → 400
2. ❌ **Missing required field:** session_id, user_input, mode, or model absent → 400
3. ❌ **Invalid enum value:** mode not in ["deterministic", "bounded", "open"] → 400
4. ❌ **Type violation:** session_id as integer, temperature as string, etc. → 400
5. ❌ **Constraint violation:** user_input empty, temperature > 2.0, max_context_messages = 0 → 400
6. ❌ **Null in required field:** session_id = null, user_input = null, mode = null → 400
7. ❌ **Invalid model identifier:** model not in INFERENCE_POLICY_FROZEN_V1 → 400
8. ❌ **Oversized field:** user_input > 10000 chars, project > 256 chars → 400
9. ❌ **Invalid type for optional:** temperature as string, seed as float → 400
10. ❌ **Array instead of string:** session_id = ["id1", "id2"] → 400

---

## 9. Versioning Rules (Frozen)

Changes to request or response schema require version bumps:

| Change Type | Bump Required | Criterion |
|---|---|---|
| Adding optional request field | Patch (1.0.1) | Clients sending old schema still work |
| Removing optional request field | Minor (1.1.0) | Clients may still send it (ignored) |
| Adding required request field | Major (2.0.0) | Old clients will fail validation |
| Removing required request field | Minor (1.1.0) | Clients sending it still works (extra field ignored) |
| Adding optional response field | Patch (1.0.1) | Clients expecting old schema still work |
| Removing optional response field | Minor (1.1.0) | Clients may break if they depend on it |
| Adding required response field | Major (2.0.0) | Clients expecting old schema break |
| Changing field type (string → int) | Major (2.0.0) | Client parsing breaks |
| Expanding enum (mode: add "hybrid") | Patch (1.0.1) | Old clients unaffected |
| Changing status code meaning | Major (2.0.0) | Client error handling breaks |

---

## 10. Required Test Set (Freeze-tests)

Every aspect of the API contract must have tests:

| Category | Test Count | Coverage |
|---|---|---|
| Request validation | 11 | All 11 validation rules |
| Response structure | 8 | All response fields present, correct types, correct values |
| Status codes | 4 | 200, 400, 401, 500 only; no other codes |
| Error response | 3 | Error message format, determinism, max length |
| Forbidden patterns | 10 | All 10 forbidden patterns return 400 |
| Session echo | 2 | Response echoes session_id, mode, model correctly |
| Idempotence | 2 | Same request → same reply, different run_id, different receipt_id |
| Type enforcement | 3 | Type violations rejected, coercion not allowed |
| Enum constraints | 2 | Mode enum, model validity |
| **Total** | **45** | Complete API contract coverage |

---

## 11. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-05 | FROZEN. DoNextRequest schema locked (11 fields, exact types, constraints), DoNextResponse schema locked (9 fields), status codes frozen to {200, 400, 401, 500} only, error response model fixed to {"detail": string}, idempotence properties defined (semantic idempotence but different run_id/receipt_id), 10 forbidden patterns enumerated, versioning rules tied to client compatibility and parsing robustness. |

---

## 12. Constitutional Compression

This contract freezes what may cross the kernel boundary. It ensures:

- Request is validated before reaching kernel
- Response is structured for client consumption
- Status codes are unambiguous and deterministic
- Error messages are consistent and helpful
- Schema changes are governed by explicit rules
- No unknown fields or types are accepted
- No status codes creep beyond the frozen set

No request field may be added, removed, or reinterpreted without version governance.

No response field may change type without major version bump.

No status code may be added or removed without major version bump.

**Principle:** The boundary shape is immutable unless you increment version and notify all clients.
