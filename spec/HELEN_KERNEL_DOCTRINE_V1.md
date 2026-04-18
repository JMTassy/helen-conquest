# HELEN_KERNEL_DOCTRINE_V1

**Status:** DRAFT_FREEZE_CANDIDATE
**Scope:** Kernel plane only
**Authority:** Constitutional kernel
**Version:** 1.0.0
**Date:** 2026-03-11

---

## 0. Purpose

This doctrine defines the minimal lawful core of HELEN OS.

Its purpose is to guarantee that externally meaningful state transitions are:
- admitted through typed manifests,
- evaluated under frozen doctrine,
- reduced by deterministic kernel logic,
- receipted canonically,
- appended to an immutable ledger,
- replayable exactly.

The kernel is not a conversational agent, not a UI, and not a simulation layer. It is the constitutional machine by which admissibility becomes state.

---

## 1. Core Laws

### Law 1.1 — Replay Law

**Same manifest in → same bytes out.**

For a fixed:
- doctrine version,
- doctrine hash,
- schema version,
- environment hash,
- admitted manifest,
- sealed ledger prefix,

the kernel MUST produce identical output bytes.

No wall clock, host path, temp path, locale, random seed, or process ordering may alter kernel output.

### Law 1.2 — Mutation Law

Kernel state changes only through admitted, receipted transitions.

No other subsystem may mutate kernel state.

### Law 1.3 — Receipt Law

**No receipt → no ship.**

No artifact may acquire admissible effect unless accompanied by a valid canonical receipt.

### Law 1.4 — Sovereignty Law

Only the kernel reducer may emit sovereign decision state.

HER, superteams, UI, simulation, Temple, or external agents may propose or explain, but may not decide.

### Law 1.5 — Doctrine Law

Kernel doctrine may not drift silently.

Any doctrine change MUST be:
- explicitly proposed,
- version-bumped,
- ledger-cited,
- replay-tested,
- admitted as a constitutional update event.

---

## 2. Kernel Boundary

### 2.1 Kernel Responsibilities

The kernel is allowed to perform only these functions:
1. ingest typed manifests,
2. validate schema and doctrine constraints,
3. reduce admitted inputs into deterministic decision state,
4. emit canonical receipts and artifact bundles,
5. append lawful transactions to the ledger.

### 2.2 Non-Kernel Responsibilities

The following are outside the kernel:
- HER narrative generation,
- UI rendering,
- office zones and sprites,
- speculative agents,
- unconstrained reasoning,
- world simulation,
- symbolic ritual layers,
- surface analytics.

These may observe, propose, or derive views. They MUST NOT mutate kernel state.

---

## 3. Kernel Planes

The system is split into three planes.

### Plane 1 — Kernel Plane
- deterministic
- receipt-bearing
- replayable
- sovereign

### Plane 2 — HER Plane
- interpretive
- explanatory
- contextual
- non-sovereign

### Plane 3 — Surface Plane
- UI
- dashboards
- graph views
- status projections
- observational only

**Plane Axiom:** Kernel decides. HER explains. UI renders.

---

## 4. Kernel State

The kernel state MUST remain minimal.

```json
{
  "doctrine_hash": "string",
  "schema_version": "string",
  "env_hash": "string",
  "ledger_head": "string",
  "open_obligations_index": {},
  "artifact_index": {},
  "replay_index": {}
}
```

### State Exclusions

The following MUST NOT exist in kernel state:
- HER narrative memory,
- UI coordinates,
- sprite state,
- office zone status,
- symbolic overlays,
- non-admitted simulation summaries.

These may exist only in derived projections.

---

## 5. Admission Model

### 5.1 Manifest Gate

The manifest gate is the sole input admission boundary.

Every candidate manifest MUST include:
- canonical JSON payload,
- schema version,
- doctrine hash,
- environment hash,
- explicit seed where applicable.

### 5.2 Manifest Gate Outcomes

The manifest gate may emit only:
- `ADMITTED`
- `REJECTED_SCHEMA`
- `REJECTED_DOCTRINE`
- `REJECTED_ENV`

No soft acceptance exists.

### 5.3 Admission Axiom

No hidden state may enter the kernel through omitted, inferred, ambient, or runtime-only values.

---

## 6. Reducer

Let:
- `s_t` = kernel state at time t
- `m_t` = admitted manifest

The kernel reducer is a pure function:

```
s_{t+1} = K(s_t, m_t)
```

The reducer MUST be:
- deterministic,
- side-effect free except through lawful output bundles,
- independent of non-frozen environmental entropy.

### Reducer Prohibitions

The reducer MUST NOT depend on:
- current time,
- hostname,
- temp path,
- unordered iteration,
- implicit filesystem discovery,
- external mutable state not cited in the manifest.

---

## 7. Invariant Engine

Every admitted transition MUST be checked against frozen invariants.

### 7.1 Minimum Invariants

1. `NO_RECEIPT = NO_SHIP`
2. Blocking obligations force `NO_SHIP`
3. Superteams cannot emit sovereign verdicts
4. HER cannot mutate kernel state
5. Receipt hash recomputes exactly
6. Same manifest yields same output bytes
7. Ledger is append-only
8. Rule update requires ledger-cited evidence

### 7.2 Invariant Failure Contract

Invariant failures MUST be emitted as structured objects, never prose.

Minimum failure structure:

```json
{
  "failure_type": "INVARIANT_FAILURE",
  "invariant_code": "string",
  "artifact_ref": "string",
  "message": "string"
}
```

---

## 8. Receipt Engine

All accepted outputs MUST be receipted canonically.

### 8.1 Canonical Receipt Rule

```
receipt_sha256 = sha256_jcs(artifact_without_receipt)
```

Where `artifact_without_receipt` means the artifact object with the `receipt_sha256` field **omitted** (not null, not empty string — omitted).

### 8.2 Receipt Constraints
- One canonical receipt path only.
- No approximate receipt matching.
- No human-readable-only receipts.
- No alternate serializers.

### 8.3 Canonicalization Regime

All hashing uses `JCS_SHA256_V1`:
- `payload_sha256 = sha256(JCS(payload))`
- `receipt_sha256 = sha256(JCS(artifact_with_receipt_sha256_omitted))`

### 8.4 Receipt Scope

The receipt engine MUST be reusable across:
- symbolic VM,
- mission VM,
- sensor VM,
- replay harness.

Receipt semantics remain kernel-defined.

---

## 9. Ledger Writer

The ledger writer is the only append path into sovereign storage.

### 9.1 Atomic Transaction

A lawful ledger append consists only of:
- admitted manifest,
- reducer output,
- verified receipt,
- invariant report.

These are appended as one constitutional transaction.

### 9.2 Ledger Laws
- Append-only.
- Sealed prefix immutable.
- No retroactive edits.
- No side-channel mutation path.

---

## 10. Unified Artifact Contract

Every kernel artifact MUST implement this contract.

```json
{
  "artifact_type": "string",
  "schema_version": "string",
  "doctrine_hash": "string",
  "canonicalization": "JCS_SHA256_V1",
  "payload": {},
  "payload_sha256": "string",
  "receipt_sha256": "string",
  "ledger_pointer": "string"
}
```

### Constitutive Fields

`artifact_type`, `schema_version`, `doctrine_hash`, `canonicalization`, and `payload` are **constitutive fields** — they determine artifact identity.

`ledger_pointer` is constitutive only in sealed form.

`artifact_meta.created_at` is observational only — excluded from receipt hash computation.

### Required Properties
- `artifact_type` must be explicit.
- `schema_version` must be frozen.
- `doctrine_hash` must match active doctrine.
- `payload_sha256` must recompute exactly.
- `receipt_sha256` must recompute exactly.
- `ledger_pointer` must identify the sealing location (sealed form only).

No ad hoc artifact formats are allowed inside the kernel.

### Draft vs. Sealed Split

Use two separate schemas — not a state enum — to prevent illegal intermediate states:

**Draft:** `ledger_pointer` FORBIDDEN
**Sealed:** `ledger_pointer` REQUIRED

---

## 11. Claim Graph Position

`CLAIM_GRAPH_V1` is a derived validator, not the kernel.

Its function is limited to:
- claim segmentation,
- support/refutation structure,
- grounding analysis,
- admissibility preparation.

It feeds the kernel. It does not replace the reducer.

### Required Ordering

```
manifest
  → claim graph validation
  → invariant engine
  → reducer
  → receipt engine
  → ledger
```

---

## 12. Event Vocabulary

The kernel transition vocabulary is frozen to the following minimum set:

- `MANIFEST_ADMITTED`
- `MANIFEST_REJECTED`
- `CLAIM_GRAPH_BUILT`
- `OBLIGATION_EMITTED`
- `RECEIPT_VERIFIED`
- `RECEIPT_FAILED`
- `DECISION_SHIP`
- `DECISION_NO_SHIP`
- `LEDGER_APPENDED`
- `DOCTRINE_UPDATE_PROPOSED`
- `DOCTRINE_UPDATE_ACCEPTED`
- `DOCTRINE_UPDATE_REJECTED`
- `STABILIZATION_MODE_ENTERED`

No new sovereign event type may be introduced without doctrine update.

---

## 13. Constitutional Inertia

Doctrine is slow state.

- No live mutation of doctrine is permitted.
- No hidden policy tweak is permitted.
- No kernel prompt drift is permitted.

Every doctrine update MUST be:
1. Proposed as an artifact,
2. Justified by ledger-cited evidence,
3. Replay-tested,
4. Version-bumped,
5. Explicitly accepted.

Formally, doctrine evolves as slow state:

```
θ_{t+1} = (1 − ρ)θ_t + ρ U(θ_t, K_t),  ρ ≪ 1
```

This gives the kernel constitutional inertia against rule thrashing.

---

## 14. Stability Monitor

The kernel MUST compute a stability monitor:

```
V_t = α C_t + β O_t + γ D_t + δ R_t
```

Where:
- `C_t` = contradiction density
- `O_t` = open obligation count
- `D_t` = replay drift count
- `R_t` = receipt failure count

**Desired condition:** `V_{t+1} − V_t ≤ 0`

### Stabilization Trigger

If violated, the kernel enters stabilization mode and MUST:
- Freeze doctrine updates,
- Reduce admission throughput,
- Elevate rejection strictness,
- Emit a `STABILIZATION_MODE_ENTERED` constitutional stress event.

---

## 15. Prohibitions

The following are forbidden during this phase:
- Adding more narrative power to HER.
- Making UI stateful in sovereign ways.
- Allowing UI semantics to affect doctrine.
- Adding adaptive kernel behavior without replay law.
- Merging simulation logic with governance logic.
- Allowing non-kernel systems to emit verdict-like state.

---

## 16. Minimal Doctrine Summary

The shortest faithful doctrine:

1. Kernel state changes only through admitted, receipted transitions.
2. Every decision must be replayable from a complete manifest.
3. Every output must be byte-stable under the frozen doctrine.
4. HER may interpret but never mutate.
5. No receipt, no ship.
6. No doctrine drift without explicit versioned constitutional update.

---

## 17. Companion Artifacts

This doctrine requires three implementation companions:

**17.1 `HELEN_ARTIFACT_SCHEMA_V1.json`** — unified artifact contract
**17.2 `UNIFIED_CI_REPLAY_HARNESS_V1`** — replay test suite
**17.3 `HELEN_KERNEL_STATE_SCHEMA_V1.json`** — minimal lawful kernel state

---

## 18. Upgrade Path

### Phase 1 — Freeze kernel law
- Manifest contract
- Artifact contract
- Invariant set
- Event vocabulary

### Phase 2 — Unify replay constitution
- Cross-VM CI harness
- Zero-drift tests
- Hidden-state tests
- Doctrine-hash enforcement

### Phase 3 — Add stability monitor
- Contradiction density
- Obligation density
- Replay drift
- Receipt failures

### Phase 4 — Expose derived surfaces
- HER context panel
- Receipt gap
- Pipeline state
- Claim graph viewer
- Office UI zones

---

*This is a CORE-mode draft. No sovereign ledger mutation. No SHIP gate passed.*
*S2 — NO RECEIPT = NO CLAIM. This document is a draft for HELEN OS v1.1.*
