# HELEN OS — Technical Reference Card

## System Schemas (Frozen & Immutable)

### EXECUTION_ENVELOPE_V1
Output from skill execution:
```json
{
  "exit_code": 0,
  "stdout": "results...",
  "stderr": null,
  "execution_time_ms": 1234
}
```

### FAILURE_REPORT_V1
Typed failure record:
```json
{
  "failure_type": "EMPTY_SEARCH_RESULTS",
  "schema_name": "FAILURE_REPORT_V1",
  "schema_version": "1",
  "context": "search_task_001",
  "timestamp": "2026-04-04T12:00:00Z"
}
```

Failure types (freeze-list):
- EMPTY_SEARCH_RESULTS
- POOR_RANKING
- DUPLICATES
- SLOW_QUERY
- LOW_RELEVANCE
- CAPABILITY_MISSING
- (extensible via schema versioning)

### SKILL_PROMOTION_PACKET_V1
Proposal for skill improvement:
```json
{
  "skill_id": "skill.search",
  "candidate_version": "1.2.0",
  "proposal": "add semantic fallback for empty results",
  "failure_source": "FAILURE_REPORT_V1",
  "receipt": {
    "receipt_id": "receipt_001",
    "payload": { "evidence": "..." },
    "sha256": "sha256:..."
  }
}
```

### SKILL_PROMOTION_DECISION_V1
Reducer output (frozen):
```json
{
  "decision": "ADMITTED",
  "reason_code": "OK_ADMITTED",
  "skill_id": "skill.search",
  "candidate_version": "1.2.0",
  "entry_hash": "sha256:...",
  "timestamp": "2026-04-04T12:00:01Z"
}
```

Decision values: ADMITTED | REJECTED
Reason codes (9 frozen):
- OK_ADMITTED
- OK_REJECTED_THRESHOLD
- ERR_SCHEMA_INVALID
- ERR_RECEIPT_MISSING
- ERR_RECEIPT_HASH_MISMATCH
- ERR_CAPABILITY_DRIFT
- ERR_DOCTRINE_CONFLICT
- ERR_THRESHOLD_NOT_MET
- (5 reserved)

### SKILL_LIBRARY_STATE_V1
Kernel state (extensible):
```json
{
  "version": "SKILL_LIBRARY_STATE_V1",
  "kernel_version": "HELEN_OS_v1.0",
  "initialized_at": "2026-04-04T12:00:00Z",
  "active_skills": {
    "skill.search": "1.3.0",
    "skill.rank": "1.1.0",
    "skill.filter": "1.0.0"
  },
  "decision_ledger": { ... }
}
```

### DECISION_LEDGER_V1
Immutable ledger structure:
```json
{
  "entries": [
    {
      "entry_index": 0,
      "prev_entry_hash": null,
      "decision": { ...SKILL_PROMOTION_DECISION_V1... },
      "entry_hash": "sha256:...",
      "timestamp": "2026-04-04T12:00:01Z"
    },
    ...
  ],
  "metadata": {
    "total_entries": 1,
    "chain_integrity": true
  }
}
```

## The 6 Reduction Gates (Constitutional Membrane)

```python
def reduce_promotion_packet(packet, state):
    # Gate 1: Schema Validity
    if not validate_schema(packet, "SKILL_PROMOTION_PACKET_V1"):
        return DECISION(REJECTED, ERR_SCHEMA_INVALID)

    # Gate 2: Receipt Presence
    if not packet.get("receipt"):
        return DECISION(REJECTED, ERR_RECEIPT_MISSING)

    # Gate 3: Receipt Hash Integrity
    computed_hash = canonical_hash(
        {"receipt_id": packet.receipt.receipt_id,
         "payload": packet.receipt.payload}
    )
    if computed_hash != packet.receipt.sha256:
        return DECISION(REJECTED, ERR_RECEIPT_HASH_MISMATCH)

    # Gate 4: Capability Lineage
    if not check_lineage(packet.skill_id, state.active_skills):
        return DECISION(REJECTED, ERR_CAPABILITY_DRIFT)

    # Gate 5: Doctrine Match
    if not check_doctrine(packet):
        return DECISION(REJECTED, ERR_DOCTRINE_CONFLICT)

    # Gate 6: Evaluation Threshold
    if not meets_threshold(packet.receipt):
        return DECISION(REJECTED, ERR_THRESHOLD_NOT_MET)

    # All gates pass
    return DECISION(ADMITTED, OK_ADMITTED)
```

## The 4 Constitutional Laws

**Law 1 (Membrane):** `state_updater(decision) → state_mutation IFF decision.verdict == ADMITTED`

**Law 2 (Ledger):** `ledger.append(decision) IFF decision.verdict == ADMITTED and decision verified by reducer`

**Law 3 (Autonomy):** `execute_task(task) → typed_failure → packet → reducer → (ADMITTED or REJECTED)`

**Law 4 (Replay):** `replay_ledger_to_state(ledger, initial) → final_state == state_reached_by_incremental_application`

## Determinism Certificate (REPLAY_PROOF_V1)

Cryptographic proof of identical behavior across multiple runs:

```python
result = replay_packet(
    packet=promotion_packet_json,
    state=state_json,
    runs=20
)

# Result structure:
{
    "packet_id": "packet_001",
    "runs": 20,
    "decision_hashes": [
        "sha256:abc123...",  # Run 1
        "sha256:abc123...",  # Run 2
        ...
        "sha256:abc123..."   # Run 20 (identical)
    ],
    "state_hashes": [
        "sha256:def456...",  # Run 1
        "sha256:def456...",  # Run 2
        ...
        "sha256:def456..."   # Run 20 (identical)
    ],
    "all_decisions_identical": true,
    "drift_detected": false
}
```

**Claim:** If `drift_detected=false`, then membrane is perfectly deterministic.

## Canonical Hashing (Determinism Primitive)

```python
from helen_os.governance.canonical import compute_hash

# Order-independent hashing
obj1 = {"b": 2, "a": 1}
obj2 = {"a": 1, "b": 2}

assert compute_hash(obj1) == compute_hash(obj2)  # True
# Both hash to: sha256({"a":1,"b":2})

# Receipt hash excludes sha256 field itself
receipt = {
    "receipt_id": "r1",
    "payload": {...},
    "sha256": "sha256:xyz"  # NOT hashed
}
computed = compute_hash({
    "receipt_id": receipt.receipt_id,
    "payload": receipt.payload
})  # Only hashes receipt_id + payload
```

## Module Import Map

```
helen_os/
├── governance/
│   ├── canonical.py                    (hashing)
│   ├── schema_registry.py              (schema loading)
│   ├── validators.py                   (validation)
│   ├── reason_codes.py                 (9 frozen codes)
│   ├── skill_promotion_reducer.py      (6-gate decision)
│   └── ledger_validator_v1.py          (chain integrity)
├── evolution/
│   └── failure_bridge.py               (failure routing)
├── executor/
│   └── helen_executor_v1.py            (execution + envelope)
├── state/
│   ├── skill_library_state_updater.py  (state mutation, Law 1)
│   ├── decision_ledger_v1.py           (ledger append, Law 2)
│   └── ledger_replay_v1.py             (replay, Law 4)
├── autonomy/
│   ├── autoresearch_step_v1.py         (single-step execution)
│   ├── autoresearch_batch_v1.py        (batch orchestration)
│   └── skill_discovery_v1.py           (discovery proposals)
├── temple/
│   ├── temple_v1.py                    (generation)
│   ├── temple_bridge_v1.py             (non-sovereign bridge)
│   └── eval/
│       └── autoresearch_eval_receipt_v1.py  (determinism cert)
└── cli/
    ├── helen_dialog.py                 (interactive shell)
    └── replay_proof_v1.py              (proof CLI)
```

## Failure Bridge Rules (Input Validation)

**Accepted:** Valid FAILURE_REPORT_V1 with schema_name + schema_version

**Rejected:**
- Untyped failures (missing schema_name/version)
- Malformed typed failures (schema validation fails)
- Leaked sovereign fields (contains "decision", "receipt_hash", etc.)

## State Update Algorithm

```python
def apply_skill_promotion_decision(state, decision):
    # Law 1: Only ADMITTED decisions mutate state
    if decision.verdict != "ADMITTED":
        return state  # No mutation

    # Extract target skill
    skill_id = decision.skill_id
    candidate_version = decision.candidate_version

    # Atomic state mutation
    new_state = copy.deepcopy(state)
    new_state.active_skills[skill_id] = candidate_version
    new_state.modified_at = now()

    return new_state
```

## Ledger Append Algorithm

```python
def append_to_ledger(ledger, decision):
    # Compute entry hash
    entry_body = {
        "entry_index": len(ledger.entries),
        "prev_entry_hash": (
            ledger.entries[-1].entry_hash
            if ledger.entries
            else None
        ),
        "decision": decision
    }
    entry_hash = compute_hash(entry_body)

    # Create entry
    entry = {
        **entry_body,
        "entry_hash": entry_hash,
        "timestamp": now()
    }

    # Append (Law 2: immutable)
    ledger.entries.append(entry)
    return ledger
```

## Ledger Replay Algorithm

```python
def replay_ledger_to_state(ledger, initial_state):
    # Start from initial state
    current_state = copy.deepcopy(initial_state)

    # Replay each entry in order
    for i, entry in enumerate(ledger.entries):
        # Validate entry index (corruption detection)
        if entry.entry_index != i:
            return initial_state  # Fail-closed

        # Validate entry hash
        if not verify_entry_hash(entry):
            return initial_state  # Fail-closed

        # Apply decision
        decision = entry.decision
        current_state = apply_skill_promotion_decision(
            current_state,
            decision
        )

    return current_state
```

## Batch Autonomy Flow

```
tasks = [task_1, task_2, ..., task_N]

for task in tasks:
    # Execute task
    execution_envelope = execute_skill(task.skill_id, task.params)

    # Type failure (if any)
    if execution_envelope.exit_code != 0:
        failure_report = type_failure(execution_envelope)
        packet = build_promotion_packet(failure_report)
    else:
        packet = None

    # Reduce (if packet exists)
    if packet:
        decision = reduce_promotion_packet(packet, current_state)

        # Apply decision
        if decision.verdict == ADMITTED:
            current_state = apply_skill_promotion_decision(
                current_state,
                decision
            )
            current_ledger = append_to_ledger(current_ledger, decision)

    # Record to journal
    journal.append({
        "task": task,
        "envelope": execution_envelope,
        "failure_report": failure_report or None,
        "decision": decision or None
    })

# Return final state + ledger + journal
return {
    "final_state": current_state,
    "final_ledger": current_ledger,
    "journal": journal
}
```

## CLI Interactive Commands

```
help              — Display commands
state             — Show kernel state (JSON)
memory            — Show institutional memory
ledger            — Show decision ledger (entries count)
skills            — List active skills
laws              — Display 4 constitutional laws
status            — System status (version, uptime, counts)
quit / exit       — Graceful shutdown (persists state)

<JSON packet>     — Submit SKILL_PROMOTION_PACKET_V1
```

## File Locations

```
helen_state.json              ← Persisted kernel state
                                (active_skills + decision_ledger)

helen_memory.json             ← Persisted institutional memory
                                (epochs, facts, doctrine)

helen_os/                     ← Source code
├── tests/                    ← 246 test cases
├── governance/               ← Constitutional layer
├── autonomy/                 ← Execution layer
├── state/                    ← State management
└── temple/                   ← Exploration layer
```

## Running Tests

```bash
# All tests (246/246)
pytest helen_os/tests -v

# By layer
pytest helen_os/tests -k "membrane" -v      # Layer 1 (28 tests)
pytest helen_os/tests -k "ledger" -v        # Layer 2 (4 tests)
pytest helen_os/tests -k "autoresearch" -v  # Layer 3 (6 tests)
pytest helen_os/tests -k "batch" -v         # Layer 3b (30+ tests)
pytest helen_os/tests -k "discovery" -v     # Layer 3c (20+ tests)
pytest helen_os/tests -k "replay" -v        # Layer 4 (4 tests)
pytest helen_os/tests -k "temple" -v        # Layer 5 (50+ tests)

# Determinism proof
python3 -m helen_os.replay_proof_v1 \
  --packet helen_os/cli/demo_packet.json \
  --state helen_os/cli/test_state.json \
  --runs 20
```

## Key Invariants (Mathematically Proven)

1. **Determinism:** `∀ runs N: reduce_promotion_packet(p, s) → identical ReductionResult`
2. **Immutability:** `∀ entries: entry[i] never modified, only appended`
3. **Chain Integrity:** `∀ entries[i]: entry[i].prev_entry_hash == entries[i-1].entry_hash`
4. **Replayability:** `replay_ledger_to_state(ledger, init) == final_state_reached_incrementally`
5. **Governed Autonomy:** `state mutation IFF decision.verdict == ADMITTED and decision from reducer`

---

**Reference Version:** HELEN OS v1.0
**Last Updated:** 2026-04-04
**Status:** FULLY OPERATIONAL (246/246 tests ✅)
