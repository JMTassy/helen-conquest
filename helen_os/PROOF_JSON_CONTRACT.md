# proof.json Contract — EXECUTION_REPLAY_PROOF_V1

**Status:** Frozen specification (non-schema)

**Purpose:** Cryptographic proof that a batch execution is deterministic across multiple runs.

---

## Structure

```json
{
  "schema_name": "EXECUTION_REPLAY_PROOF_V1",
  "proof_id": "proof_batch_abc123def456",
  "run_id": "run_2026-03-13T14:23:45Z",
  "timestamp": "2026-03-13T14:23:45Z",
  "environment_manifest": {
    "reducer_version": "v1",
    "law_surface_hash": "sha256:...",
    "canonicalization": "JCS_SHA256_V1"
  },
  "determinism_certificate": {
    "runs": 20,
    "all_decisions_identical": true,
    "all_states_identical": true,
    "decision_hashes": [
      "sha256:...",
      "sha256:...",
      "..."
    ],
    "state_hashes": [
      "sha256:...",
      "sha256:...",
      "..."
    ]
  },
  "ledger_replay_proof": {
    "from_initial_state_hash": "sha256:...",
    "via_ledger_entries": 10,
    "yields_final_state_hash": "sha256:...",
    "corruption_check": "PASS"
  }
}
```

---

## Fields

### Root Level

| Field | Type | Meaning |
|-------|------|---------|
| `schema_name` | string | Always `"EXECUTION_REPLAY_PROOF_V1"` |
| `proof_id` | string | Unique identifier for this proof (deterministic based on batch_id) |
| `run_id` | string | The run this proof certifies |
| `timestamp` | ISO 8601 | When this proof was generated |

### environment_manifest

Describes the governance context. If this changes between proof generations, the proof becomes invalid.

| Field | Type | Meaning |
|-------|------|---------|
| `reducer_version` | string | Reducer implementation version (e.g., "v1") |
| `law_surface_hash` | sha256 hash | Hash of the frozen constitutional laws |
| `canonicalization` | string | JSON canonicalization method (always `"JCS_SHA256_V1"`) |

**Invariant:** If `law_surface_hash` changes, the proof is void.

### determinism_certificate

Proof that the batch produced identical results across N runs.

| Field | Type | Meaning |
|-------|------|---------|
| `runs` | integer | Number of times batch was re-executed |
| `all_decisions_identical` | boolean | True if all decision hashes are byte-identical |
| `all_states_identical` | boolean | True if all final state hashes are identical |
| `decision_hashes` | array of sha256 | Array of length N, each entry the decision hash from one run |
| `state_hashes` | array of sha256 | Array of length N, each entry the final state hash from one run |

**Invariant:**
- If `all_decisions_identical` is true, `len(set(decision_hashes)) == 1`
- If `all_states_identical` is true, `len(set(state_hashes)) == 1`
- If either is false, batch is non-deterministic (failure case)

### ledger_replay_proof

Proof that the final state can be reconstructed by replaying the ledger.

| Field | Type | Meaning |
|-------|------|---------|
| `from_initial_state_hash` | sha256 | Hash of the starting state |
| `via_ledger_entries` | integer | Number of decision entries in ledger |
| `yields_final_state_hash` | sha256 | Hash reached by replay |
| `corruption_check` | enum | `"PASS"` if ledger is valid, `"FAIL"` if corrupt |

**Invariant:** `yields_final_state_hash` must match the final state hash from `determinism_certificate.state_hashes[0]` (or any entry, since all are identical if deterministic).

---

## Interpretation

### Proof is VALID if:

1. `all_decisions_identical == true`
2. `all_states_identical == true`
3. `corruption_check == "PASS"`
4. `environment_manifest.law_surface_hash` hasn't changed since batch execution

### Proof is INVALID if:

- Any determinism certificate field is false
- Ledger corruption is detected
- Environment manifest diverges from batch context

---

## Usage

```bash
# Generate proof during batch execution
helen autoresearch run \
  --env env.json \
  --state state.json \
  --decisions decisions.json \
  --out ./output \
  --proof-runs 20

# Check existing ledger determinism
helen replay proof \
  --env env.json \
  --state state.json \
  --ledger ledger.json \
  --runs 20 \
  --out proof.json
```

---

## Relationship to Other Artifacts

| Artifact | Contains | Purpose |
|----------|----------|---------|
| `BATCH_RECEIPT_PACKET_V1` | Initial + final state hashes, ledger hash | Governance facts |
| `ORACLE_TOWN_BATCH_ARTIFACT_V1` | Full ledger + state | Institutional archive |
| `EXECUTION_REPLAY_PROOF_V1` | Determinism certification | Verification of reproducibility |

**Order:** Generate receipt → write artifact → generate proof

---

## Invariant

**Every governance decision must be backed by:**

1. A receipt (proof object)
2. A ledger entry (immutable record)
3. A replay proof (determinism verification)

If any is missing or invalid, the decision is not admitted.
