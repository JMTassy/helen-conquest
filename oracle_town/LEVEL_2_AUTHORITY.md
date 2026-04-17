# ORACLE TOWN — Level 2: Authority Model

**Status:** Constitutional specification (before implementation)

This document freezes the authority model. No component that generates a claim is allowed to ratify it. Ratification requires TRI verdict + Mayor signature + ledger commit.

---

## Architecture (Flipped)

```
Labor Layer (OBS, INS, BRF, PUB, MEM, EVO)
  ↓ produce Claim Bundles
Authority Layer (TRI, Mayor, Ledger)
  ↓ verify + sign + commit
World Mutation (file changes, state updates)
```

Labor can be massively parallel, cheap, adversarial, wrong.
Authority must be minimal, deterministic, auditable.

---

## Non-Negotiable Rules

### 1. No Direct Ledger Writes

PUB/MEM/EVO cannot write to ledger directly.

They produce Claim Bundles (artifacts + proposed diffs + evidence pointers).

**Ledger commits require Mayor signature.**

TRI may recommend SHIP, but it does not mutate state.

### 2. Every State Change Requires a Signed Receipt

No exceptions.
- Code merge
- Skill update
- Manifest update
- Policy update
- Key registry update

If it changes the system, it needs a receipt.

### 3. Skills Cannot Self-Edit Their Own Manifest

A skill can propose manifest changes as a claim.
It cannot modify the manifest in-place.

**Reason:** Manifest = capability routing + policy loading. Self-edit = root access.

### 4. Daemon Has Zero Merge Authority

Daemon may:
- Observe
- Detect violations
- Propose patches (claims)
- Trigger gates
- Escalate / block

Daemon may not:
- Modify policy
- Modify manifests
- Sign receipts
- Commit ledger entries

Daemon is enforcement and alerting, not legislature.

### 5. Oracle Town's Job Is Not "Find the Right Answer"

**It is:** Enforce that anything entering reality is justified + logged under pinned policy.

If a correct answer cannot be evidenced, it doesn't ship.

---

## TRI: Constitutional Gate (Not an Agent)

TRI is a **deterministic gate function**, not an agent.

### Inputs

- **Claim bundle** (diffs, artifacts, declared intent)
- **Evidence bundle** (tests, logs, hashes)
- **Pinned policy pack hash** (K7: policy immutable for this run)
- **Key registry snapshot** (K0: authority separation)

### Outputs

- **VERDICT** ∈ {ACCEPT, REJECT, DEFER}
- **Reasons** (machine-readable codes)
- **Required remediations** (optional)
- **Verdict receipt** (unsigned)

### What TRI Does NOT Do

- Change files
- Rewrite policy
- Negotiate
- Improve itself mid-run
- Sign receipts
- Commit to ledger

---

## Mayor: The Only Signer

Mayor takes TRI's verdict receipt and either:

1. **Signs and commits** (if ACCEPT) → Ledger entry + world mutation allowed
2. **Signs and rejects** (if REJECT) → Rejection receipt logged, claim denied
3. **Signs and defers** (if DEFER) → Deferral receipt logged, claim held

**Mayor signature is what makes a receipt legally binding in Oracle Town.**

That signature can be automated later (rule-based or human), but the role must exist as a distinct authority boundary.

No component may skip this step.

---

## Policy Evolution Model

### Per Run (Within a Run)

- Policy is **pinned** (hash fixed at run start)
- Nothing about K-gates changes mid-execution
- All K-gate decisions are based on immutable policy pack

### Between Runs (Cross-Run Evolution)

- Policy can evolve **only via**: Claim → TRI → Mayor → Ledger
- New policy pack → new hash → new run uses new rules
- Old run's decisions remain immutable under old policy

**K-gates are:**
- Immutable within a run (K7 enforcement)
- Upgradeable across runs via governed patches
- Versioned in ledger (full audit trail)

---

## Minimal Level 2 Implementation (Three Components)

### A. claim.json Schema

```json
{
  "claim": {
    "id": "claim_20260130_<uuid>",
    "timestamp": "2026-01-30T19:42:00Z",
    "target": "oracle_town/jobs/obs_scan.py",
    "claim_type": "code_change|skill_update|policy_patch|manifest_update",
    "proposed_diffs": [
      {
        "path": "oracle_town/jobs/obs_scan.py",
        "operation": "modify",
        "hash_before": "sha256:...",
        "hash_after": "sha256:...",
        "diff_url": "artifacts/claim_001_obs_scan.patch"
      }
    ],
    "evidence_pointers": [
      {
        "type": "test_result",
        "path": "artifacts/claim_001_tests.json",
        "hash": "sha256:..."
      },
      {
        "type": "determinism_check",
        "path": "artifacts/claim_001_replay.json",
        "hash": "sha256:..."
      }
    ],
    "expected_outcomes": [
      "all_tests_pass",
      "determinism_verified",
      "no_invariant_violations"
    ],
    "policy_pack_hash": "sha256:...",
    "generated_by": "obs_attestor_001",
    "intent": "Update observation loading to support additional file formats"
  }
}
```

### B. tri_gate.py

A pure validator function that:

1. **Load pinned policy pack** (K7)
2. **Validate claim schema** (required fields present, types correct)
3. **Verify evidence hashes** (all artifacts exist and match claimed hashes)
4. **Run required checks:**
   - Tests pass
   - Determinism verified (K5)
   - No invariant violations (I1-I8)
   - Policy conformance (K0-K7)
5. **Emit tri_verdict.json** (unsigned)

```json
{
  "verdict": {
    "claim_id": "claim_20260130_<uuid>",
    "decision": "ACCEPT|REJECT|DEFER",
    "checked_against_policy": "sha256:...",
    "checks_performed": [
      {
        "check": "K0_authority_separation",
        "result": "PASS",
        "details": "Attestor found in active key registry"
      },
      {
        "check": "K1_fail_closed",
        "result": "PASS",
        "details": "All required receipts present"
      },
      {
        "check": "K5_determinism",
        "result": "PASS",
        "details": "Run 1 hash == Run 2 hash"
      }
    ],
    "required_remediations": [],
    "timestamp": "2026-01-30T19:42:30Z"
  }
}
```

### C. mayor_sign.py + ledger/

1. **Mayor reads tri_verdict.json**
2. **Signs it** (Ed25519 or equivalent)
3. **Creates signed receipt**
4. **Appends to ledger** in canonical structure

**Ledger structure:**
```
oracle_town/ledger/
├── YYYY/
│   └── MM/
│       └── claim_id/
│           ├── claim.json (original claim)
│           ├── tri_verdict.json (unsigned)
│           ├── mayor_receipt.json (signed)
│           └── artifacts/ (all evidence)
```

**Mayor receipt schema:**
```json
{
  "receipt": {
    "claim_id": "claim_20260130_<uuid>",
    "verdict": "ACCEPT|REJECT|DEFER",
    "mayor_signature": "ed25519:...",
    "timestamp_signed": "2026-01-30T19:42:45Z",
    "policy_pack_hash": "sha256:...",
    "legal_binding": true,
    "world_mutation_allowed": true
  }
}
```

**Ledger Invariant:**
- Append-only (no modifications, no deletions)
- Every entry references claim + tri_verdict + mayor_signature
- No entry without all three = ledger is corrupted
- Git history shows cumulative growth (audit trail)

---

## What Happens After Mayor Signs

1. **If ACCEPT:** World mutation is allowed (merge code, update skill, apply policy patch)
2. **If REJECT:** Claim is logged as rejected; no mutation
3. **If DEFER:** Claim is held; can be resubmitted with additional evidence

All outcomes are logged in the ledger under the same receipt.

---

## Labor (OBS → INS → BRF → PUB → MEM → EVO)

Each labor component:
1. **Produces artifacts** (observations, insights, brief, etc.)
2. **Generates claims** (proposed changes to system state)
3. **Waits for TRI verdict** (does not mutate anything directly)
4. **Waits for Mayor signature** (does not assume approval)

Labor can:
- Run in parallel (thousands of cheap workers)
- Fail without consequence (rejected claims don't propagate)
- Be adversarial (try to break policy)
- Be improved independently (labor quality issues don't threaten authority)

Labor cannot:
- Write to ledger
- Sign receipts
- Mutate shared state
- Bypass TRI + Mayor

---

## The One Critical Rule

**No component that generates a claim is allowed to ratify it.**

Ratification requires:
1. TRI verdict (deterministic verification)
2. Mayor signature (authority binding)
3. Ledger commit (immutable recording)

This rule protects Oracle Town from:
- Self-justifying corruption
- Silent drift in policy
- Daemon mutating itself
- Skills evolving unsupervised
- Labor force bypassing gates for convenience

---

## Status

This is the **constitutional foundation** for Level 2.

Before implementing tri_gate.py, we freeze:
1. Claim schema (what can be proposed)
2. TRI checks (what makes a claim valid)
3. Mayor role (who signs, and what signatures mean)
4. Ledger structure (how truth is recorded)

Once these are written in code, Oracle Town becomes a jurisdiction, not a pipeline.

---

**Next:** Implement claim.json, tri_gate.py, mayor_sign.py in that order.

No exceptions to the authority model.

No "just this once" bypasses.

Hold the line.

