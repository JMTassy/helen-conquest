# ORACLE_TOWN_SWARM_SANDBOX_SPEC.md

## Swarm UX Pattern as a Non-Authoritative Convenience Layer

**Status:** Draft v0.1 (Implementation-Ready)
**Last Updated:** 2026-01-25

---

### 0. Purpose

This specification defines a "Swarm Sandbox" that enables parallel task execution (planner + workers) while preserving Oracle Town's governance invariants:

- **K0:** Natural language has zero authority.
- **SHIP = Mayor(policy, briefcase, ledger)**
- **No receipts => NO_SHIP**

The Swarm Sandbox is an ergonomics and throughput layer. It is **NOT** a governance layer.

---

### 1. Definitions

| Term | Definition |
|------|------------|
| **Swarm** | A set of cooperating processes/agents producing artifacts in parallel under a shared task plan. |
| **Swarm Controller ("Lead")** | A coordinator that decomposes work, assigns tasks, and synthesizes artifacts. |
| **Swarm Worker** | A specialist process that produces artifacts for a specific task. |
| **Swarm Transcript** | Non-authoritative logs of internal reasoning, messages, and intermediate outputs. |
| **Swarm Artifact** | A concrete file output (code, schema, test, manifest) intended for Intake/Factory/Mayor consumption. |
| **Swarm Boundary Digest (SBD)** | A canonical digest over all Swarm artifacts and selected metadata, computed deterministically. |

---

### 2. Non-Negotiable Invariants

| ID | Invariant | Description |
|----|-----------|-------------|
| **S0** | No Authority | Swarm outputs SHALL NOT decide SHIP/NO_SHIP, claim obligations satisfied, or emit receipts. |
| **S1** | Receipt Separation | No Swarm component SHALL create or sign attestations, receipts, or evidence digests. |
| **S2** | Policy Blindness | Swarm components MUST NOT read `policy.json`, `ledger.json`, `decision_record.json`, or keys. |
| **S3** | Fail-Closed Intake | Any Swarm artifact that contains forbidden authority tokens MUST be rejected at Intake. |
| **S4** | Deterministic Boundary | The Swarm Boundary Digest MUST be stable under replay given the same inputs. |

---

### 3. Allowed and Forbidden Outputs

#### 3.1 Allowed (Swarm Sandbox MAY produce)

- `proposal_bundle.json` (CT-format proposals)
- `ct_run_manifest.json`
- `evidence_plan.json` (plan only; no evidence claims)
- Patch bundles / code artifacts (non-authoritative)
- Schema files and test vectors
- Build logs and unit-test logs (as evidence candidates only, not receipts)

#### 3.2 Forbidden (Swarm Sandbox MUST NOT produce)

- Any SHIP/NO_SHIP verdict or equivalent (including synonyms)
- Any statement asserting an obligation is satisfied
- Any receipt/attestation/signature or "proof" artifact
- Any policy mutation, registry edits, or bypass instructions
- Any "confidence", ranking, recommendation, or prioritization claims

---

### 4. Architectural Placement

Swarm Sandbox sits **upstream** of Oracle Intake:

```
User request
  -> Swarm Sandbox (Lead + Workers)  [NON-AUTHORITATIVE]
  -> Creative Town Output Artifacts (proposal_bundle, etc.)
  -> Oracle Intake (schema + forbidden-field guard)
  -> Briefcase (obligations only)
  -> Factory (tools + evidence + signed receipts)
  -> Ledger (attestations)
  -> Mayor (decision)
```

---

### 5. Swarm Execution Model (Formal)

Swarm Sandbox MUST implement the following state machine:

```
STATE INIT:
  Inputs: user_request, constraints, swarm_config
  Output: swarm_run_manifest.json (deterministic run_id)

STATE PLAN:
  Lead emits swarm_task_board.json:
    - task_id, description, inputs, outputs, dependencies
    - MUST NOT include rankings or recommendations

STATE EXECUTE:
  Workers execute tasks and emit artifacts into swarm_artifacts/ directory.
  Workers MAY communicate but all messages are non-authoritative.

STATE SYNTHESIZE:
  Lead may merge worker artifacts into:
    - proposal_bundle.json
    - ct_run_manifest.json
    - evidence_plan.json
  Lead MUST NOT add authority tokens.

STATE SEAL:
  Swarm produces swarm_boundary_digest.json with stable hash.

STATE HANDOFF:
  Only the following files are eligible for Intake:
    - proposal_bundle.json
    - ct_run_manifest.json
    - evidence_plan.json
    - swarm_boundary_digest.json (optional; for reproducibility)

All other swarm transcripts remain sandbox-only.
```

---

### 6. Mandatory Swarm Guardrails (Mechanical)

Swarm Sandbox MUST run these checks before handoff:

| ID | Check | Description |
|----|-------|-------------|
| **G1** | Schema validation | Validate `proposal_bundle.json` and `ct_run_manifest.json` against schemas |
| **G2** | Forbidden field/token scan | Scan eligible handoff files for authority language (see 6.1) |
| **G3** | Duplicate-block detector | Detect repeated contiguous sections in eligible files only (see 6.2) |
| **G4** | Budget caps | Enforce max proposals, max obligation suggestions, max artifact sizes |
| **G5** | Stable hashing | Compute SBD from canonical JSON encodings |

If any check fails => Swarm handoff MUST be blocked; produce `swarm_reject.json`.

#### 6.1 Forbidden Authority Lexicon (Normative)

G2 implements a deterministic scan using a pinned lexicon.

**Normalization function:**
```python
def normalize(text: str) -> str:
    import unicodedata
    # Unicode NFKC, lowercase, whitespace collapse
    normalized = unicodedata.normalize('NFKC', text.lower())
    return ' '.join(normalized.split())
```

**Authority-attempt keys** (structural smuggling via JSON keys):
```
ship, verdict, decision, recommend, confidence, score, rank,
certified, satisfied, attestation, receipt, proof, approved, verified
```

**Authority-attempt phrases** (semantic escalation):
```
is satisfied, obligation satisfied, all tests passed, should ship,
ready to ship, safe to deploy, certified, verified, approved
```

**Generic forbidden tokens** (lower priority):
```
must ship, probability, prioritize
```

**Match procedure:**
1. Walk all JSON keys (case-folded) and check against authority-attempt keys
2. Normalize all string values and check for authority-attempt phrases (substring match)
3. Check for generic forbidden tokens (substring match)

**Reason code precedence** (frozen):
1. `SWARM_REJECT_SCHEMA_INVALID`
2. `SWARM_REJECT_BUDGET_VIOLATION`
3. `SWARM_REJECT_FORBIDDEN_AUTHORITY` (authority keys or phrases)
4. `SWARM_REJECT_DUPLICATE_BLOCKS`
5. `SWARM_REJECT_NONDETERMINISTIC_HASH`

#### 6.2 Duplicate-Block Scope (Normative)

G3 applies **only** to eligible handoff files:
- `proposal_bundle.json`
- `ct_run_manifest.json`
- `evidence_plan.json`
- `swarm_boundary_digest.json`

G3 MUST NOT scan sandbox-only transcripts (which are intentionally allowed to be noisy).

#### 6.3 Swarm Reject Artifact

When any guardrail fails, Swarm MUST produce `swarm_reject.json` conforming to `swarm_reject.schema.json`:

```json
{
  "swarm_run_id": "SWARM-...",
  "rejected_at": "2026-01-25T12:00:00Z",
  "reason_code": "SWARM_REJECT_FORBIDDEN_AUTHORITY",
  "violations": [
    {
      "path": "proposal_bundle.json#/proposals/0/description",
      "rule": "G2",
      "detail_digest": "sha256:...",
      "matched_signal": "AUTHORITY_PHRASE:should ship"
    }
  ]
}
```

Swarm reject artifacts are **terminal at Swarm layer**. They are never consumed by Intake.

---

### 7. Swarm Boundary Digest (SBD)

#### 7.1 Canonical JSON Definition (Normative)

**Canonical JSON** is defined as:

```python
json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

This removes multi-implementation drift. All hashing MUST use this encoding.

#### 7.2 SBD Computation

SBD is computed as:

```
SBD = sha256(
  canonical_json({
    "swarm_run_id": "...",
    "swarm_config_hash": "sha256:...",
    "eligible_artifacts": [
      { "path": "...", "sha256": "sha256:...", "bytes": N },
      ...
    ],
    "toolchain_versions": { ... }  // optional, restricted
  })
)
```

#### 7.3 Toolchain Versions Restrictions

`toolchain_versions` MAY include only:
- Language/runtime version (e.g., `"python": "3.10.12"`)
- OS/container digest (e.g., `"container_digest": "sha256:..."`)
- Dependency lock hash (e.g., `"requirements_lock": "sha256:..."`)

`toolchain_versions` MUST NOT include:
- `policy_hash`
- `key_registry_hash`
- `registry_hash`
- Any identifier that correlates with governance pins

This prevents backdoor authority signaling through metadata.

#### 7.4 SBD Notes

- Only eligible artifacts may be included.
- Transcripts MUST NOT be included (avoid nondeterminism and authority leakage).

---

### 8. Swarm Governance Contract (Why Swarm is Safe Here)

Swarm is safe because:

1. It produces **no receipts**.
2. It **cannot bind** policy or registry.
3. Intake is **fail-closed** and text-blind with respect to authority semantics.
4. Mayor only consumes `(policy, briefcase, ledger, registry)`, **never** Swarm output.

Therefore, Swarm subsumes the UX pattern while preserving K0.

---

### 9. Compliance Test Obligations (Recommended)

Add these CI obligations for Swarm Sandbox:

| Obligation Name | Description |
|-----------------|-------------|
| `obl_swarm_no_authority_lang` | Verify no authority language in handoff artifacts |
| `obl_swarm_no_receipts` | Verify no attestations/signatures produced |
| `obl_swarm_deterministic_sbd` | Verify SBD is stable across replay |
| `obl_swarm_handoff_schema_valid` | Verify all handoff artifacts pass schema validation |
| `obl_swarm_duplicate_blocks` | Verify no duplicate block patterns (persuasion) |

---

### 10. Canonical Reason Codes (Swarm)

| Code | Description |
|------|-------------|
| `SWARM_REJECT_FORBIDDEN_AUTHORITY` | Handoff artifact contains authority language |
| `SWARM_REJECT_SCHEMA_INVALID` | Handoff artifact fails schema validation |
| `SWARM_REJECT_DUPLICATE_BLOCKS` | Repeated contiguous sections detected |
| `SWARM_REJECT_BUDGET_VIOLATION` | Artifact exceeds budget caps |
| `SWARM_REJECT_NONDETERMINISTIC_HASH` | SBD not stable across replay |

---

### 11. Integration with Existing Oracle Town Components

#### 11.1 Intake Guard Extension

The existing `oracle_town/core/intake_guard.py` SHOULD be extended to:

1. Accept `swarm_boundary_digest.json` as optional provenance
2. Apply G2 forbidden-field scan to all Swarm-originated artifacts
3. Log Swarm origin in metadata (non-sovereign)

#### 11.2 Factory Interaction

Factory receives Swarm artifacts **only after** Intake processing:

- Factory MUST NOT receive raw Swarm transcripts
- Factory MUST NOT trust Swarm-generated evidence claims
- Factory generates its own attestations via tool execution

#### 11.3 Mayor Isolation

Mayor MUST remain completely isolated from Swarm:

- Mayor reads: `policy.json`, `briefcase.json`, `ledger.json`, `public_keys.json`
- Mayor does NOT read: Swarm manifests, transcripts, or artifacts

---

### 12. Example Swarm Flow

```
1. User: "Generate landing page with GDPR consent flow"

2. Swarm INIT:
   - swarm_run_id: SWARM-2026-01-25-abc123
   - inputs_digest: sha256:...

3. Swarm PLAN (Lead):
   - T01: Research GDPR requirements
   - T02: Design consent UI component
   - T03: Implement banner code
   - T04: Write unit tests

4. Swarm EXECUTE (Workers):
   - Worker-Legal: Produces gdpr_requirements.md
   - Worker-Design: Produces consent_ui_spec.json
   - Worker-Code: Produces consent_banner.tsx
   - Worker-Test: Produces consent_banner.test.tsx

5. Swarm SYNTHESIZE (Lead):
   - Merges into proposal_bundle.json
   - NO confidence scores
   - NO "should ship" language

6. Swarm SEAL:
   - Computes SBD over eligible artifacts

7. Swarm HANDOFF:
   - proposal_bundle.json -> Intake
   - ct_run_manifest.json -> Intake
   - swarm_boundary_digest.json -> Intake (optional)

8. Intake:
   - Validates schemas
   - Scans for forbidden tokens
   - Produces briefcase with obligations

9. Factory:
   - Runs tests independently
   - Generates attestations with signatures

10. Mayor:
    - Evaluates briefcase + ledger
    - Decision: SHIP or NO_SHIP
```

---

**END OF SPECIFICATION**

This document is normative for Swarm Sandbox implementation.
Any deviation MUST be justified via a governed policy-change run.
