# ARTIFACT_SCHEMAS_V1

**Version:** 1.0.0
**Status:** FROZEN
**Date:** 2026-03-07
**Schema dialect:** JSON Schema Draft 2020-12
**Schema location:** `schemas/` directory

---

## Overview

HELEN OS defines six artifact schemas, split into two tiers. All schemas use JSON Schema Draft 2020-12 and are validated at layer boundaries.

---

## Tier A — Simulation Artifacts (Non-Sovereign)

### EvidenceBundle (`evidence_bundle_v1.schema.json`)

**Role:** Primary output from CONQUEST LAND. Carries one simulation tick's snapshot: house roster, task records, 10 emergence metrics, ledger tip hash.

**Key fields:**
- `bundle_id` — unique identifier
- `tick` — simulation tick number
- `seed` — RNG seed for determinism
- `regime` — phase classification (NOISE/SPECIALIZATION/HOUSE_FORMATION/EGREGOR/POLITICS)
- `houses` — array of House snapshots
- `metrics` — 10 metrics: persistence, modularity, IE ratio, entropy, house count, memory reuse, survival, task success, Gini, policy rate
- `task_records` — all tasks executed this tick
- `ledger_tip_hash` — SHA-256 of simulation ledger tip
- `bundle_hash` — SHA-256 of this bundle (for tamper detection)

**Producer:** CONQUEST LAND
**Consumer:** HELEN (sensemaking)
**Next step:** Flows into `GateReport` for validation

---

### IssueList (`issue_list_v1.schema.json`)

**Role:** HAL's audit output. Identifies issues found during HELEN's review of an EvidenceBundle.

**Key fields:**
- `issue_list_id` — unique identifier
- `bundle_ref` — references the EvidenceBundle being audited
- `issues` — array of Issue objects:
  - `issue_id` — unique within list
  - `severity` — CRITICAL / WARNING / INFO
  - `category` — schema_validation / logic_conflict / missing_evidence / policy_violation
  - `description` — human-readable issue statement
  - `affected_fields` — array of bundle paths affected
  - `suggested_fix` — remediation suggestion (if applicable)
- `severity_counts` — object: `{CRITICAL: N, WARNING: N, INFO: N}`
- `overall_verdict` — PASS / WARN / FAIL based on issue distribution

**Producer:** HELEN (HAL audit layer)
**Consumer:** MAYOR (gate evaluation)
**Next step:** Referenced in `MayorPacket` for arbitration

---

### TaskList (`task_list_v1.schema.json`)

**Role:** Planning layer output from HELEN. Lists tasks proposed for execution, with priorities and resource requirements.

**Key fields:**
- `task_list_id` — unique identifier
- `bundle_ref` — references the EvidenceBundle being planned against
- `tasks` — array of Task objects:
  - `task_id` — unique within list
  - `priority` — 1 (high) to 5 (low)
  - `domain` — task domain (skill area)
  - `complexity` — 0.1–1.0 (resource cost multiplier)
  - `estimated_agents` — suggested coalition size
  - `dependencies` — array of prerequisite task IDs
  - `estimated_cost` — resource units needed
- `total_tasks` — count of all tasks
- `pending_count` — tasks still to be executed
- `estimated_total_cost` — sum of all estimated costs

**Producer:** HELEN (planning)
**Consumer:** MAYOR (scheduling evaluation)
**Next step:** Referenced in `MayorPacket` for arbitration

---

### GateReport (`gate_report_v1.schema.json`)

**Role:** Gate evaluation results. Records which gates passed and which failed for a given EvidenceBundle.

**Key fields:**
- `gate_report_id` — unique identifier
- `bundle_ref` — references the EvidenceBundle being gated
- `gates` — array of GateResult objects:
  - `gate_id` — gate code (SCHEMA_VALID, RECEIPT_VERIFY, etc.)
  - `status` — PASS / FAIL / DEFER
  - `message` — explanation of result
  - `timestamp` — when gate was evaluated
- `overall_pass` — boolean: all gates PASS?
- `gate_count_pass` — count of passed gates
- `gate_count_fail` — count of failed gates
- `verdict_hash_hex` — SHA-256 of this gate evaluation (for receipt binding)

**Producer:** HELEN OS (gate evaluation engine)
**Consumer:** MAYOR (decision logic)
**Next step:** Drives the final verdict in `GateEvaluated`

---

## Tier B — Governance Artifacts (Sovereign-Bound)

### MayorPacket (`mayor_packet_v1.schema.json`)

**Role:** HELEN's complete submission to MAYOR. Bundles all Tier A artifacts with routing receipts.

**Key fields:**
- `packet_id` — unique identifier (format: `MP-<sha256[:8]>`)
- `evidence_bundle_ref` — references EvidenceBundle
- `issue_list_ref` — references IssueList
- `task_list_ref` — references TaskList
- `gate_report_ref` — references GateReport
- `routing_receipt_hash` — SHA-256 of the routing receipt from L2→L3a
- `submitted_at` — ISO8601 timestamp
- `helen_proposal` — optional: narrative proposal text (CORE mode)
- `packet_hash` — SHA-256 of this packet (for chain verification)

**Producer:** HELEN (packaging layer)
**Consumer:** MAYOR (arbitration)
**Requirement:** All four refs must be present and valid before MAYOR will process

---

### GateEvaluated (`gate_evaluated_v1.schema.json`)

**Role:** MAYOR's final verdict. The sovereign output that may result in ledger mutation.

**Key fields:**
- `verdict_id` — unique (format: `V-<sha256[:8]>`)
- `packet_ref` — references the MayorPacket that was evaluated
- `verdict` — PASS / FAIL / DEFER
- `verdict_hash_hex` — SHA-256(canonical_json(quest_id, quest_type, gates, next_quest_seed))
- `next_quest_seed` — SHA-256(quest_id | sorted receipts | gates+metrics hash) for next cycle
- `receipts` — array of Receipt objects:
  - `receipt_id` — unique
  - `receipt_hash` — the actual receipt hash
  - `gate_id` — which gate produced this
- `governor_note` — optional narrative (signed by MAYOR)
- `timestamp` — ISO8601 of verdict

**Producer:** MAYOR (arbitration, purely functional)
**Consumer:** KERNEL (ledger append)
**Requirement:** All receipts must be present and correctly bound before ledger accepts this verdict

---

## Schema Validation Points

### At L1→L2 Boundary
EvidenceBundle schema is validated:
- All required fields present
- `bundle_hash` matches RFC 8785 canonical JSON
- `metrics` array has exactly 10 entries
- No forbidden tokens in any string field

### At L2→L3a Boundary
MayorPacket schema is validated:
- All four artifact refs are resolvable
- Routing receipt hash is present
- No contradictions between referenced artifacts
- Gateway checks for forbidden tokens pass

### At L3a→L3b Boundary
GateEvaluated schema is validated:
- All receipts are present and hashes match
- Verdict is one of PASS/FAIL/DEFER
- If verdict=PASS, all gates in GateReport must be PASS
- Ledger tip hash matches GovernanceVM state

---

## Hash Pinning

Each schema has its own SHA-256 hash computed from its RFC 8785 canonical JSON representation. These hashes are recorded in `config/schema_manifest_v1.json` for validation during runtime.

| Schema | Hash Pinning |
|---|---|
| `evidence_bundle_v1.schema.json` | Pinned in manifest |
| `issue_list_v1.schema.json` | Pinned in manifest |
| `task_list_v1.schema.json` | Pinned in manifest |
| `gate_report_v1.schema.json` | Pinned in manifest |
| `mayor_packet_v1.schema.json` | Pinned in manifest |
| `gate_evaluated_v1.schema.json` | Pinned in manifest |

If a schema is modified, its hash changes, and the manifest must be updated before the system will accept artifacts of that type.

---

**Frozen:** 2026-03-07
