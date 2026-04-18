# Decision Record Determinism Contract

## Purpose

This document defines the determinism contract for Mayor decision outputs, establishing which fields are receipt-hashed (deterministic) and which are audit-only metadata (non-deterministic).

---

## The Determinism Problem

**Problem:** Timestamps kill replay determinism.

If `decision_record.json` includes an ISO 8601 timestamp and is receipt-hashed, then:
- Two identical runs with same inputs produce different hashes (timestamp differs)
- Cross-runtime determinism tests fail
- Receipt gap reduction becomes impossible (hashes never match)

**Solution:** Split decision output into two files:

1. **`decision_record.json`** — Receipt-hashed payload (deterministic)
2. **`decision_record.meta.json`** — Audit metadata (non-hashed, includes timestamp)

---

## File 1: decision_record.json (Receipt-Hashed)

### Purpose
Deterministic Mayor decision that can be replayed, verified, and hashed for receipt binding.

### Schema
`schemas/decision_record.schema.json` (Draft 2020-12, `additionalProperties: false`)

### Required Fields
```json
{
  "decision": "SHIP" | "NO_SHIP",
  "kill_switches_pass": boolean,
  "receipt_gap": integer >= 0,
  "blocking": [
    {
      "code": "REASON_CODE",
      "detail": "optional human-readable",
      "evidence_paths": ["optional/relative/paths"]
    }
  ],
  "metadata": {
    "mayor_version": "v0.1",
    "tribunal_bundle_hash": "<sha256-hex>",
    "policies_hash": "<sha256-hex>",
    "receipt_root_hash": "<sha256-hex>"
  }
}
```

### Schema-Enforced Invariants

Using JSON Schema `allOf` conditions:

**Invariant 1: NO_SHIP ⇒ blocking non-empty**
```json
{
  "if": { "properties": { "decision": { "const": "NO_SHIP" } } },
  "then": { "properties": { "blocking": { "minItems": 1 } } }
}
```

**Invariant 2: SHIP ⇒ blocking empty, receipt_gap==0, kill_switches_pass==true**
```json
{
  "if": { "properties": { "decision": { "const": "SHIP" } } },
  "then": {
    "properties": {
      "blocking": { "maxItems": 0 },
      "receipt_gap": { "const": 0 },
      "kill_switches_pass": { "const": true }
    }
  }
}
```

### Determinism Properties

✅ **No timestamps** — Removed to enable replay-equivalence
✅ **No floats** — All numbers are integers or strings
✅ **Canonical JSON** — RFC 8785 for hashing
✅ **Schema-validated** — All fields typed and constrained
✅ **Reason code allowlist** — `blocking[].code` must be in `reason_codes.json`

### Hashing Recipe

```python
import json
import hashlib

def hash_decision_record(decision_record: dict) -> str:
    """
    Compute SHA-256 of decision_record.json using RFC 8785 canonical JSON.

    Returns:
        64-character lowercase hex string
    """
    canonical_json = canon8785(decision_record)  # RFC 8785 implementation
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
```

### Replay-Equivalence

Two Mayor runs are **replay-equivalent** if they produce identical `decision_record.json` when given:
- Same `tribunal_bundle_hash`
- Same `policies_hash`
- Same `receipt_root_hash`
- Same `mayor_version`

**Property:** Replay-equivalent runs MUST produce identical decision record hashes.

---

## File 2: decision_record.meta.json (Non-Hashed Audit Metadata)

### Purpose
Non-deterministic audit information about when/where the Mayor decision was executed.

### Schema
`schemas/decision_record.meta.schema.json` (if formalized)

### Required Fields
```json
{
  "decision_record_hash": "<sha256 of decision_record.json>",
  "timestamp": "2026-01-16T19:45:00Z",
  "audit_trail": {
    "run_id": "unique-run-identifier",
    "execution_duration_ms": 1234.5,
    "node_hostname": "mayor-node-01",
    "git_commit": "<40-char-git-sha>"
  }
}
```

### Determinism Properties

❌ **Contains timestamps** — ISO 8601 datetime of decision finalization
❌ **Contains floats** — Execution duration in milliseconds
❌ **Contains hostnames** — Node-specific information
✅ **Binds to hashed payload** — `decision_record_hash` links to deterministic file

### NOT Included in Receipt Hash

This file is **never hashed** for receipt purposes. It exists solely for:
- Human audit trails
- Performance profiling
- Debugging (which node produced decision)
- Incident response (timestamp correlation)

---

## Enforcement

### Test: test_mayor_no_ship_invariant.py

Validates:
1. Schema enforcement of NO_SHIP/SHIP invariants
2. Falsification tests proving schema rejects violations
3. Evidence path validation (no absolute paths, no parent traversal)

### Test: test_reason_codes_allowlist.py

Validates:
1. All `blocking[].code` values are in `reason_codes.json`
2. No typos or undocumented codes
3. Allowlist integrity (no duplicates, valid format, sorted)

### CI Requirements

1. **Schema validation:** All decision records MUST validate against schema
2. **Reason code sync:** `reason_codes.json` MUST match REASON_CODES.md
3. **Determinism check:** Replay-equivalent runs MUST produce identical hashes
4. **No timestamp in hashed payload:** CI MUST reject PRs adding timestamp to `decision_record.json`

---

## Migration Path

If existing code has `decision_record.json` with timestamps:

### Step 1: Split the file
```bash
# Extract hashed fields to decision_record.json
jq 'del(.timestamp, .audit_trail)' old_decision_record.json > decision_record.json

# Extract metadata to decision_record.meta.json
jq '{decision_record_hash: .hash, timestamp: .timestamp, audit_trail: .audit_trail}' \
   old_decision_record.json > decision_record.meta.json
```

### Step 2: Update Mayor to emit two files
```python
def emit_decision(decision_data):
    # Hashed payload
    decision_record = {
        "decision": decision_data["decision"],
        "kill_switches_pass": decision_data["kill_switches_pass"],
        "receipt_gap": decision_data["receipt_gap"],
        "blocking": decision_data["blocking"],
        "metadata": decision_data["metadata"]
    }

    # Compute hash
    record_hash = hash_decision_record(decision_record)

    # Non-hashed metadata
    meta = {
        "decision_record_hash": record_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "audit_trail": decision_data["audit_trail"]
    }

    # Write both files
    write_json("decision_record.json", decision_record)
    write_json("decision_record.meta.json", meta)
```

### Step 3: Update receipt binding
Receipts must reference `decision_record_hash` (from meta file), not timestamp.

---

## Summary

| Property | decision_record.json | decision_record.meta.json |
|----------|---------------------|---------------------------|
| Receipt-hashed | ✅ Yes | ❌ No |
| Contains timestamp | ❌ No | ✅ Yes |
| Deterministic | ✅ Yes | ❌ No |
| Schema-validated | ✅ Yes (strict) | Optional |
| Replay-equivalent | ✅ Yes | ❌ No |
| Audit trail | Partial (hashes) | ✅ Full |

**Key Principle:** If it affects the decision, it's in the hashed payload. If it's about when/where/how long, it's in metadata.

---

**END OF DECISION_RECORD_DETERMINISM.md**
