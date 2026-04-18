# GOVERNANCE_LAW_V1

**Version:** 1.0.0
**Status:** FROZEN
**Date:** 2026-03-07

---

## §7.0 Constitutional Basis

The governance law of HELEN OS rests on four non-negotiable soul rules and three canonical laws. These cannot be overridden by simulation output, narrative, user directives, or any non-receipted claim.

---

## §7.1 The Four Soul Rules

```
S1 — DRAFTS ONLY
    No world effect unless a human seals it.
    HELEN can propose, never decide.

S2 — NO RECEIPT = NO CLAIM
    Logs and certificates outrank narration.
    Unverified claims are drafts only.

S3 — APPEND-ONLY
    Memory is additive; deprecate, never erase.
    History is inviolable.

S4 — AUTHORITY SEPARATION
    Governance reads receipts; it does not invent truth.
    Authority flows through verified decisions only.
```

---

## §7.2 The Three Canonical Laws

### `CANYON_NONINTERFERENCE_V1`
**Statement:** Same admissible evidence (E_adm) → same sovereign output (verdict_hash_hex). Narrative variation cannot alter the verdict.

**Enforcement:** `GovernanceVM._check_canyon()` before every `propose()` call.

**Implication:** Two different narratives about the same evidence must produce the same governance verdict. Interpretation is separate from truth-recording.

### `HELEN_PROPOSAL_USE_RECEIPT_GATE_V1`
**Statement:** `helen_proposal_used=True` in any `ReducedConclusion` iff an `AUTHZ_RECEIPT_V1` binds to exact `(verdict_id, verdict_hash_hex)`.

**Enforcement:** `validate_authz_binding()` — raises `AuthzBindingError` if refs don't match.

**Implication:** HELEN's proposals are credited only when receipted. A proposal without a binding receipt is still a draft, regardless of how many times it was cited.

### `LAW_HELEN_BOUNDED_EMERGENCE_V1`
**Statement:** HELEN operates in CORE mode by default. SHIP mode requires: MayorCheck + AuthorityScan + SchemaValidation + receipt. HELEN cannot self-authorize. She can only make shipping undeniable.

**Hash:** `5594d400c2c21f0f25d008a171c925e497b8a4c4b9582531a0cfeab5170ffdc2`

**Enforcement:** `authority_bleed_scan()` blocks forbidden tokens before any gate. SHIP mutations require all three gates to pass.

---

## §7.3 The CORE/SHIP Split

HELEN operates in two modes. Mode must be tracked on every output.

| Mode | Character | May persist ledger mutations? | Required gates |
|---|---|---|---|
| **CORE** | Generative, exploratory, non-authoritative. Freely hypothesizes, patterns, proposes. | ❌ No | None |
| **SHIP** | Authoritative. Produces outputs that affect state. | ✅ Yes (only after gates pass) | MayorCheck + AuthorityScan + SchemaValidation |

**Forbidden tokens in CORE output:** `SHIP`, `SEALED`, `APPROVED`, `FINAL`
**Enforced by:** `authority_bleed_scan()` — any CORE output containing these tokens is auto-escalated to WARN or BLOCK.

**Invariant:** No state mutation without a gate + receipt. HELEN cannot self-authorize. She can only make it structurally undeniable that something should ship.

---

## §7.4 Hashing Standard

All artifact hashes, bundle hashes, receipt hashes, and verdict hashes in HELEN OS use:

**Canonical serialization:** RFC 8785 (JSON Canonicalization Scheme)
- Keys sorted lexicographically at every nesting level
- No extra whitespace
- Unicode normalized
- Deterministic: same object → same bytes → same hash

**Hash algorithm:** SHA-256
- 256-bit output
- 64-character hex digest
- No truncation for sovereign artifacts

**Application:**
```
payload_hash    = SHA256(RFC8785_canonical(payload))
cum_hash        = SHA256(bytes.fromhex(prev_cum_hash) || bytes.fromhex(payload_hash))
bundle_hash     = SHA256(RFC8785_canonical(artifact_fields))
verdict_hash    = SHA256(RFC8785_canonical({quest_id, quest_type, gates, next_quest_seed}))
theta_hash      = SHA256(RFC8785_canonical(theta_v1_config))
```

**Domain prefix** (ledger cumulative hashes only): `HELEN_CUM_V1::`

**Rule:** No two hash computations in HELEN OS may use different serialization methods. RFC 8785 + SHA-256 is the one canonical hashing law.

---

## §7.5 Ledger Invariants

The sovereign ledger (`helen_os_scaffold/storage/ledger.ndjson`) obeys:

1. **Append-only:** Entries are added only. No editing. No deletion.
2. **Hash-chained:** Every entry carries `payload_hash` and `cum_hash` linking it to the previous entry.
3. **Fail-closed:** If chain validation fails on GovernanceVM init, the system aborts and refuses new proposals.
4. **Deterministic replay:** A fresh GovernanceVM replaying the ledger from entry 0 must arrive at the same state as the current GovernanceVM.
5. **Idempotent:** Duplicate event IDs are rejected by `IdempotenceManager` before ledger append.

**Recovery:** If the ledger is corrupted, restore via `git checkout` on `ledger.ndjson`. No in-place repair.

---

## §7.6 Gate Requirements

Five gates exist. SHIP-mode outputs require all three marked ✅:

| Gate | Code | Required for SHIP? | What it checks |
|---|---|---|---|
| MayorCheck | `MAYOR_CHECK` | ✅ Yes | MAYOR has evaluated and issued a verdict |
| AuthorityScan | `AUTHORITY_SCAN` | ✅ Yes | No forbidden tokens in the output |
| SchemaValidation | `SCHEMA_VALID` | ✅ Yes | Output matches registered schema (Draft 2020-12) |
| ReceiptVerification | `RECEIPT_VERIFY` | Conditional | Receipt hash matches payload |
| KernelIsolation | `KERNEL_ISOLATION` | Metadata only | eval/meta modules don't import GovernanceVM |

**Gate failure behavior:**
- A single FAIL → verdict is FAIL (no partial pass)
- A DEFER → gather more evidence and resubmit
- A BLOCK from HAL → rewrite required before resubmission

---

## §7.7 Dialogue Laundering (Forbidden)

**Definition:** Dialogue laundering is the act of citing `dialog.ndjson` directly as SHIP-authority in a ledger mutation.

**Why it is forbidden:** Dialogue is always CORE-mode evidence. It is unverified, unredacted, and may contain injection attempts. Using dialogue as a direct path into the sovereign ledger bypasses all gates.

**The legal path for dialogue:**
```
dialog.ndjson
    → EPOCH4 CLAIM_GRAPH_V1 pipeline (ingest → validate → compute sets)
    → GovernanceVM.propose() (with anti-laundering check)
    → Gate evaluation
    → Sovereign ledger entry
```

**Enforcement:** `GovernanceVM.propose()` calls `_check_dialogue_laundering()` before any ledger append. This check cannot be bypassed by CLI or UI wrappers.

**Rule:** SHIP mutations may only cite: CLAIM_GRAPH_V1 artifact hashes, evaluation receipts, gate receipts, or law inscription receipts — never raw dialogue.

---

## §7.8 SCF (Structured Conversation Format) Invariant

SCF cannot silently disable. If the SCF model or config is missing:
- **Required behavior:** Emit a WARN turn with code `SCF_DISABLED`
- **Forbidden behavior:** Silent fallback (`scf_enabled=False` with no logging)

This invariant prevents sensemaking sessions from quietly losing their annotation structure.

---

## §7.9 HER/HAL Dyad Invariants

| Invariant | Code | Description |
|---|---|---|
| I-BLOCK | `I-BLOCK` | `HALVerdict.verdict=BLOCK` iff `required_fixes` non-empty (both directions) |
| I-BLEED | `I-BLEED` | HER output containing authority words → auto-escalated to WARN or BLOCK |
| I-VOCAB | `I-VOCAB` | HER `output_type` must be one of 5 permitted types |
| I-IDENTITY | `I-IDENTITY` | Identity = only the `identity_hash`. No prose. No "I am". Only the receipt. |
| I-NOWRITE | `I-NOWRITE` | HER cannot set constitutional state. HAL cannot write narrative. |

**Two-block wire format invariants (T-TWO-1 through T-TWO-5):**
- T-TWO-1: `[HER]` must precede `[HAL]` in output
- T-TWO-2: `kind` must be a valid `HEROutputType`
- T-TWO-3: `[HAL]` block must be valid JSON matching `HALVerdict` schema
- T-TWO-4: `certificates.her_block_hash_hex` must match `SHA256(canonical HER block)` if not `"COMPUTE_ME"`
- T-TWO-5: `verdict=block` requires non-empty `required_fixes` (I-BLOCK re-enforced at parse time)

---

## §7.10 Identity Binding

Session identity is the cryptographic binding of ledger state + kernel + policy:

```
identity_hash = SHA256(
    bytes.fromhex(ledger_cum_hash) ||
    bytes.fromhex(kernel_hash) ||
    bytes.fromhex(policy_hash)
)
```

**Byte-level concatenation. No separator. No padding.**

HELEN's identity is not a name. It is this hash. "I am HELEN" is never valid output. "My identity is the receipt" is the only valid identity claim.

---

## §7.11 Proof Pack Format

Every accepted governance decision must produce a proof pack. This is the minimum verifiable record of the decision process.

```json
{
  "proof_pack_version": "v1",
  "inputs": {
    "artifact_refs": ["<evidence_bundle_id>", "<issue_list_id>", "<task_list_id>"],
    "gate_report_ref": "<gate_report_id>",
    "router_receipt": "<routing_receipt_hash>",
    "helen_packet": "<mayor_packet_id>"
  },
  "decision": {
    "gate_evaluated_ref": "<verdict_id>",
    "verdict_hash_hex": "<64-char-hex>",
    "mayor_signature": "<receipt_hash>"
  },
  "kernel_commit": {
    "ledger_entry_hash": "<payload_hash>",
    "cum_hash": "<cum_hash_at_entry>"
  },
  "config": {
    "theta_hash": "<sha256-of-theta_v1.json>",
    "schema_manifest_hash": "<sha256-of-schema_manifest_v1.json>",
    "code_hash": "<sha256-of-engine-at-runtime>",
    "env_hash": "<env-hash-from-SEAL_V2>"
  }
}
```

A proof pack without all four `config` hashes is an incomplete proof pack and may not be cited as verification.

---

## §7.12 Phase Harness Separation

The runner layer enforces strict separation between observation and execution:

| Phase | What it may do | What it may NOT do |
|---|---|---|
| Phase 1 (Observation) | Collect evidence, produce proposals, assemble candidate action lists | Call action executors, append to ledger, emit receipts |
| Phase 2 (Execution) | Execute actions, append to ledger, emit receipts | Produce new proposals (Phase 1 only) |

**Invariant:** Phase 1 produces proposals. Phase 2 executes after gates pass. This separation cannot be collapsed.

---

**Frozen:** 2026-03-07
