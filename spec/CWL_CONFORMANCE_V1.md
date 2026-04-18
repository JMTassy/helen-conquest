# CWL Conformance v1 (Epoch3)

**Version:** CWL v1.0.1
**Status:** NORMATIVE — FROZEN
**Date:** 2026-02-27
**Spec Locks Applied:** S1, S2, S3, S4, S5

Keywords **MUST**, **MUST NOT**, **SHOULD**, **MAY** are interpreted as in RFC 2119.

---

## 0. Scope

This document defines normative conformance requirements for CWL v1.0.1 as an interoperability standard.

Covers:
- Canonical JSON encoding (CANON_JSON_V1)
- Sovereign Ledger hash chaining — Channel A (HELEN_CUM_V1)
- Non-sovereign Run Trace hash chaining — Channel C (CWL_TRACE_V1)
- Seal identity closure (binds ledger tip + trace tip + env + kernel)
- Anti-replay semantics as ledger-derivable (RID(L))
- Merkle commitment semantics for light verification (Level D, optional)
- `env_hash` and `kernel_hash` precision definitions (S5)

Out of scope: consensus, staking, semantic correctness of receipts, transport security.

---

## 1. Canonical JSON (CANON_JSON_V1)

### 1.1 Canonical encoding

Implementations MUST define canonical JSON bytes for any object `obj` as:

- UTF-8 encoding
- Object keys sorted lexicographically by Unicode code point
- Separators exactly `(",", ":")` — comma with no space, colon with no space
- `ensure_ascii = false`

**Python reference implementation:**

```python
json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

Implementations in other languages MUST produce byte-identical output for any given object.

### 1.2 Numeric restrictions

Sovereign events (Channel A) MUST NOT contain JSON floating-point numbers.
Integers MUST be represented as JSON integers (`"k": 42`, not `"k": 42.0`).

Non-sovereign channels (B, C) MAY contain floats, but those floats MUST NOT be committed into any sovereign hash (Channel A payload_hash or cum_hash).

### 1.3 String encoding

Strings MUST be valid UTF-8. Unicode characters above U+007F MUST be encoded as raw UTF-8 bytes (not `\uXXXX` escapes), given `ensure_ascii=false`.

---

## 2. Channels and Authority

### 2.1 Channel definitions

| Channel | Name | Sovereign | Description |
|---------|------|-----------|-------------|
| A | Sovereign Ledger | YES | Append-only, authority-bearing, HELEN_CUM_V1 |
| B | MemoryKernel | NO | Non-sovereign facts, conflict-aware |
| C | Run Trace | NO | Non-sovereign telemetry, CWL_TRACE_V1 |

### 2.2 Constitutional firewall

The only legal world-changing morphism is:

```
Dialogue (D) → Attestation (E) → Ledger append via β (L) → World mutation
```

Dialogue MUST NOT directly mutate Channel A.
Non-sovereign channels (B, C) MUST NOT influence the MAYOR decision predicate β.

### 2.3 Single write-gate per channel

- Only `TownAdapter` / `GovernanceVM` MAY append to Channel A.
- Only `TraceLogger` (or equivalent) is the designated writer of Channel C.
- Only `MemoryKernel` is the designated writer of Channel B.

Implementations MUST NOT allow any other code path to append to Channel A.

---

## 3. RunTrace (Channel C) — Spec Lock S1

### 3.1 Determinism (S1)

The trace chain commits MUST include ONLY deterministic fields in the hash core:

```
hash_core = {
  "authority": false,
  "event_type": <str>,
  "metadata": <dict>,
  "payload": <dict>,
  "run_id": <str>,
  "schema_version": "TRACE_EVENT_V1",
  "seq": <int>,
  "tick": <int>
}
```

**S1 rules (normative):**

- `tick` MUST be provided by a deterministic orchestrator (e.g., engine step counter). Wall-clock time MUST NOT be used as `tick`.
- `seq` MUST be a monotone integer starting at 0, incremented by 1 per appended event.
- `authority` MUST be `false` (boolean) for all trace events. Implementations MUST raise an error if `authority: true` is ever supplied.
- Wall-time MUST NOT be included in any committed bytes. If a wall-time audit timestamp is desired, it MAY appear in a `meta.timestamp` field outside the hash core.

### 3.2 Trace hashing (CANON + chain formula)

Let:

```
payload_bytes    = CANON_JSON_V1(hash_core)
payload_hash_i   = SHA256(payload_bytes)
trace_hash_i     = SHA256(b"HELEN_TRACE_V1" || prev_trace_hash_bytes || payload_hash_bytes)
```

- `prev_trace_hash` for the first event (`seq=0`) is 32 zero bytes.
- `||` denotes raw byte concatenation (no delimiters).
- The prefix `b"HELEN_TRACE_V1"` is 14 bytes (ASCII).

### 3.3 Monotone sequence

Implementations MUST verify that `seq` is strictly monotone increasing (0, 1, 2, …) when reading a trace file.
An implementation MAY bootstrap `seq` from the last event in the file on init.

---

## 4. Sovereign Ledger Hash Chain (Channel A) — HELEN_CUM_V1

### 4.1 Payload hash definition

Sovereign ledger events MUST commit to their payload via:

```
payload_hash = SHA256(CANON_JSON_V1(payload))
```

`payload` is the event payload object. Only payload fields are hashed, not the ledger envelope fields (`seq`, `cum_hash`, `meta`, etc.).

### 4.2 Cumulative hash definition

```
cum_hash_i = SHA256(b"HELEN_CUM_V1" || prev_cum_hash_bytes || payload_hash_bytes)
```

- `b"HELEN_CUM_V1"` is 12 bytes (ASCII prefix).
- `prev_cum_hash` for `seq=0` (genesis) is 32 zero bytes.
- `||` denotes raw byte concatenation (no delimiters between components).

### 4.3 Hash law field

Every Channel A event MUST include `"hash_law": "CWL_CUM_V1"` to enable version detection.

Validators MUST detect `hash_law` at the first event:
- `"CWL_CUM_V0"` → legacy ledger accepted without cryptographic verification (historical archive)
- `"CWL_CUM_V1"` → strict verification per this spec

---

## 5. Seal v2 (Identity Closure) — Spec Lock S2

### 5.1 Seal payload definition

`seal_v2` MUST bind:

| Field | Content |
|-------|---------|
| `final_cum_hash` | Channel A ledger tip (cum_hash of the last non-seal event) |
| `final_trace_hash` | Channel C trace tip (cum_hash of the last trace event) |
| `env_hash` | Environment identity hash (see §9.2) |
| `kernel_hash` | TCB (Trusted Computing Base) hash (see §9.1) |

**S2 rule (normative):** Seal payload MUST NOT include machine-local fields such as file system paths, process IDs, hostname, or UID.

Minimal conforming seal payload:

```json
{
  "cwl_version": "1.0.1",
  "env_hash": "HEX64",
  "final_cum_hash": "HEX64",
  "final_trace_hash": "HEX64",
  "kernel_hash": "HEX64",
  "outcome": "SEALED",
  "schema": "SEAL_V2",
  "timestamp": "ISO8601"
}
```

### 5.2 Seal terminus semantics

The seal event DOES NOT participate in its own hash chain. It references the cumulative hash of all events BEFORE the seal.

```
ledger_tip = cum_hash of last non-seal event
seal.final_cum_hash MUST == ledger_tip
```

Validators MUST stop hash chain computation when encountering a seal event and return the accumulated tip at that point.

### 5.3 Boot verification (fail-closed)

On boot, implementations MUST verify:

1. Last seal exists (or explicitly enter `UNSEALED_RECOVERY_MODE`)
2. `seal.final_cum_hash == computed_ledger_tip`
3. `seal.final_trace_hash == computed_trace_tip`
4. `seal.env_hash == compute_env_hash()` (if S5 env pinning is active)
5. `seal.kernel_hash == expected_kernel_hash` (if S5 kernel pinning is active)
6. Ledger hash chain verifies (no gaps, no mutations)
7. Trace hash chain verifies (no gaps, no mutations)

Failure MUST halt the system (fail-closed). No silent drift is permitted.

---

## 6. Anti-Replay — Spec Lock S3

### 6.1 Ledger-derivable RID set

Anti-replay MUST be derived from the sovereign ledger prefix:

```
RID(L) := { e.rid | e ∈ L and e has field "rid" }
```

A receipt `r` with field `rid` is admissible if and only if:

```
r.rid ∉ RID(L_current)
```

**S3 rule (normative):** No mutable external database, index, or cache is required for correctness of anti-replay. `RID(L)` is derivable purely from the sealed ledger prefix via replay.

Implementations MAY maintain a derived in-memory cache of `RID(L)` for performance, but it MUST be reconstructible from the ledger alone.

---

## 7. Merkle Commitments — Spec Lock S4 (Optional, Level D)

Merkle import proofs are a verification surface minimizer (enabling light clients). They MUST NOT create a new authority plane.

### 7.1 Domain-separated leaf hashes

```
leaf_s = SHA256(b"CWL_LEDGER_LEAF_V1" || payload_hash_s_bytes)
```

Where `payload_hash_s` is the `payload_hash` of the event at index `s` in the ledger.
`b"CWL_LEDGER_LEAF_V1"` is 18 bytes (ASCII prefix).

### 7.2 Internal node hashes

```
node = SHA256(b"CWL_MERKLE_NODE_V1" || left_bytes || right_bytes)
```

`b"CWL_MERKLE_NODE_V1"` is 18 bytes (ASCII prefix). `||` is raw byte concatenation.

### 7.3 Padding rule (duplicate-last)

If a level has an odd number of nodes, the last node MUST be duplicated to form a pair:

```
if len(nodes) % 2 == 1:
    nodes.append(nodes[-1])
```

This rule propagates up all levels until a single root is produced.

### 7.4 Inclusion proof verification

Proof steps MUST include sibling side (`"L"` or `"R"`). Verification is:

```python
current = leaf
for step in proof:
    if step["side"] == "R":
        current = merkle_node(current, step["hash"])
    else:  # "L"
        current = merkle_node(step["hash"], current)
assert current == root
```

Verification MUST be deterministic.

### 7.5 Root anchoring

If Merkle roots are used for cross-town import proofs, the root MUST be anchored in a valid `seal_v2` (or a future `seal_v3` extension). Unanchored roots are inadmissible.

---

## 8. Conformance Levels

| Level | Requirements |
|-------|-------------|
| **A** | CANON_JSON_V1 + Ledger hash chain (HELEN_CUM_V1) |
| **B** | Level A + RunTrace determinism (S1) + Seal v2 binds both ledger tip and trace tip |
| **C** | Level B + Ledger-derived anti-replay for receipts (S3) |
| **D** | Level C + Merkle leaf/node semantics (S4) + inclusion proofs + anchored root |

A system is CWL-conformant at level X if and only if it passes all checks for level X and all lower levels.

---

## 9. Environment and Kernel Identity — Spec Lock S5

### 9.1 kernel_hash (TCB hash)

`kernel_hash` MUST be computed as:

```
kernel_hash = SHA256( deterministic_tarball_bytes(TCB_FILESET) )
```

Where:

- `TCB_FILESET` is an **explicit, versioned list of file paths** committed to the spec or config
- Tarball file ordering MUST be **lexicographic** by file path
- File bytes MUST be **raw bytes** (no newline normalization, no platform adjustments)
- Empty files MUST produce deterministic content (empty bytes)

The TCB_FILESET MUST be explicitly enumerated and version-pinned. Implicit glob patterns are NOT conforming.

### 9.2 env_hash (environment identity)

`env_hash` MUST be computed as:

```
env_hash = SHA256( CANON_JSON_V1(env_descriptor) )
```

Where `env_descriptor` MUST include at minimum:

| Field | Example |
|-------|---------|
| Language + runtime version | `"python": "3.11.8"` |
| Dependency lockfile digest | `"lockfile_sha256": "abc..."` |
| Platform tag (if determinism is platform-dependent) | `"platform": "linux-x86_64"` |

If cross-platform deterministic replay is claimed, `env_descriptor` MUST include a statement of supported platforms and the deterministic math backends in use.

---

## 10. Non-Claims

CWL v1.0.1 does NOT guarantee:

- Semantic honesty of a remote town's receipts
- Global consensus across towns
- Liveness under network partitions
- Correctness of evidence beyond schema validation rules
- Resistance to an honest-but-equivocating MAYOR

CWL v1.0.1 DOES guarantee:

- **Append-only sovereign history** — ledger is cryptographically append-only
- **Deterministic replay** — identical attestation sequence → identical final ledger
- **Cryptographic identity closure** — ledger + trace + env + kernel all bound in seal
- **Fail-closed boot verification** — any mismatch halts system
- **Mechanical conformance** — all claims testable against frozen test vectors

---

## 11. Test Vectors

Normative test vectors are defined in `CWL_TEST_VECTORS_V1.json` (same directory).

All expected hash values therein are computed using this specification and are frozen at Epoch3. Any implementation MUST produce identical output for the fixtures defined therein.

---

## 12. Amendment Process

Per §11 of `CWL_V1_0_1_ARCHITECTURE.md`:

- No change to any hash formula, prefix, or structural rule is permitted without a version increment
- Changing any rule in this document requires: (a) evidence, (b) new version tag, (c) new test vectors
- Hash formulas are part of system identity: any formula change → new kernel_hash → existing seals invalid

**This document is frozen at CWL v1.0.1. No silent evolution.**

---

*Generated: 2026-02-27*
*Epoch: EPOCH3 Standard Artifacts*
*Spec Locks Applied: S1 (RunTrace Determinism), S2 (Seal Path Safety), S3 (Anti-Replay), S4 (Merkle), S5 (env/kernel hash)*
