# HELEN_OS_CANON_V1
## Canonical Specification — Normative Reference

**Status:** ✅ VERIFIED — 14/14 conformance gates passed 2026-03-06
**Version:** 1.0
**Date:** 2026-03-06
**Authority:** This document is normative for the current epoch unless explicitly superseded by a versioned amendment bearing a ledger receipt.

---

## 0. Purpose

This document fixes the canonical shape of HELEN OS at the point where architecture becomes standard.

It defines:

- the prime invariant
- the authority model
- the channel model
- the single write-gate
- the seal model
- the verification discipline
- the proof-pack requirement
- the boundary between cognition and sovereignty

**This document is not aspirational. It is the current canonical form.**

Everything that contradicts this document must either:
1. propose an amendment (via the standard proposal pipeline), or
2. be treated as non-conformant.

---

## 1. Prime Invariant

```
No receipt → no ship.
```

No state-changing action becomes real unless it is:

1. expressed as typed evidence,
2. validated by the reducer,
3. appended to the sovereign ledger.

Everything else — dialogue, plans, simulations, summaries, models — may be useful, insightful, or persuasive.

**It is not authoritative.**

This invariant cannot be relaxed by an agent, a servitor, a persona, or an administrator. The only valid exception is a reducer-validated law amendment, itself ledgered.

---

## 2. Core Formula

The canonical authority pipeline is:

```
LLM proposes → reducer validates → ledger commits
```

This means:

| Actor | Role | May Write Ledger? |
|-------|------|-------------------|
| Language model | Suggest, draft, structure | ❌ No |
| Memory system | Contextualize, surface | ❌ No |
| Retrieval | Surface relevant evidence | ❌ No |
| Trace | Record execution path | ❌ No |
| **Reducer** | **Authorize** | **✅ Only this** |
| **Ledger** | **Make real** | **✅ Result** |

Nothing in this pipeline is optional. Skipping the reducer is a constitutional violation. Skipping the ledger is a constitutional violation.

---

## 3. System Identity (Canonical Definition)

HELEN OS is:

> **A constitutional multi-agent operating system in which expressive cognition is non-sovereign, and sovereign state exists only as reducer-validated, append-only ledgered events.**

It is not:

- a chatbot shell
- an agent swarm
- a memory tool
- an orchestration framework
- a UI wrapper

It is a **governance substrate** — an OS for bounded intelligence under constitutional law.

**One-line form:**
> Language may propose. Only the reducer plus ledger can make anything real.

---

## 4. Authority Stratification

The system is organized into four layers. Authority flows strictly downward. No layer may claim authority above its own.

### L0 — Agents

**Examples:** HELEN, AIRI, specialist agents, researcher mode, planner/critic/worker personas.

Agents are expressive, generative, and **non-sovereign**.

**Agents may:**
- speak
- propose
- draft
- summarize
- structure candidate evidence
- operate in researcher mode (see § 8)

**Agents must not:**
- write to the sovereign ledger
- issue seals
- self-authorize actions
- rewrite law
- bypass the reducer

Violation of these constraints is a constitutional breach, not a policy disagreement.

---

### L1 — Servitors / Superteams

**Examples:** Planner, Worker, Critic, Retrieval, Hands, Pipeline Workers, Superteam coordinators.

Servitors perform **deterministic orchestration** where possible. They produce artifacts, attestations, and traces.

**Servitors may:**
- receive tasks from L0 agents or L3 kernel
- produce artifacts, attestations, structured traces
- call tools within their defined capability scope (Hand allowlist)

**Servitors must not:**
- ship authority
- write Channel A (sovereign ledger)
- override reducer decisions
- self-promote to L3

---

### L2 — Street / Emergent Layer

**Examples:** Memory patterns, drift signals, metrics, culture signals, behavioral telemetry.

This layer is **advisory only**. It surfaces patterns from runtime behavior but has no decision authority.

**L2 may:**
- surface observations
- flag anomalies
- contribute to memory continuity

**L2 must not:**
- access the reducer directly
- influence ledger writes
- claim authority based on observation alone

---

### L3 — Town / Kernel

**Examples:** Reducer, GovernanceVM, Ledger, Seals, TownAdapter.

This is the **sole legitimacy gate**. L3 is the only layer that makes things real.

**L3 components:**
- **Reducer** — validates law proposals, issues verdicts
- **Ledger** — receives validated events, appends them immutably
- **Receipts** — cryptographic proof of each ledger event
- **Seals** — identity closure binding ledger + trace + environment + kernel
- **TownAdapter / GovernanceVM** — the only authorized writer of Channel A

**L3 invariant:** Nothing enters the sovereign ledger that has not passed through the reducer. No exceptions.

---

## 5. Channel Model

The system has exactly three channels. Each has a different authority level and write policy.

### Channel A — Sovereign Ledger

```
Path: town/storage/ledger.ndjson
```

| Property | Value |
|----------|-------|
| Mutability | Append-only |
| Hash chain | Yes |
| Replayable | Yes |
| Event classes | Verdict / Receipt / Seal / Law inscription |
| Authority | Sovereign |
| Write access | TownAdapter / GovernanceVM only |
| World-changing | Yes — **this is the only world-changing channel** |

No agent, servitor, or persona may write directly to Channel A. Any attempt to do so is a constitutional violation.

---

### Channel B — MemoryKernel

```
Path: helen_os/memory/memory.ndjson
```

| Property | Value |
|----------|-------|
| Mutability | Append-only |
| Conflict handling | Conflict-aware (no silent overwrite) |
| Authority language | **Hard-banned** |
| Purpose | Memory continuity, context, learned lessons |
| Authority | Non-sovereign |
| World-changing | No |

Channel B is for **continuity**, not truth. Nothing in Channel B overrides a receipt.

**Hard bans in Channel B:**
- `"I authorize"`
- `"This is final"`
- `"Sealed"`
- `"Approved"` (as a claim, not a receipt reference)

---

### Channel C — RunTrace

```
Path: storage/run_trace.ndjson
```

| Property | Value |
|----------|-------|
| Mutability | Append-only |
| Hash chain | Yes (trace domain: `HELEN_TRACE_V1::`) |
| Authority flag | `authority=false` enforced |
| Purpose | Telemetry, UI events, cognition traces, research traces |
| Authority | Non-sovereign |
| World-changing | No |

Channel C is **never authoritative**. It records what happened, not what is true.

RunTrace may be used to reconstruct execution paths for audit, but it cannot substitute for a receipt.

---

## 6. Single Write-Gate Rule

Only one path may mutate sovereign state:

```
Dialogue → Evidence → Reducer → Ledger
```

And only one component may write Channel A:

```
TownAdapter / GovernanceVM
```

Everything else:
- proposes
- traces
- remembers
- observes
- retrieves

**But does not decide.**

This rule is enforced structurally, not just by policy. Any code path that writes to the ledger without going through GovernanceVM is a bug, not a feature.

---

## 7. Identity Closure (Seal Model)

A valid HELEN OS seal binds four values:

```
seal = closure(
    final_cum_hash,     // ledger tip hash
    final_trace_hash,   // run trace tip hash
    env_hash,           // environment hash at boot
    kernel_hash         // kernel binary/policy hash
)
```

This means system identity is the closure of:

```
ledger + trace + environment + kernel
```

**Tamper detection:**
- Ledger tamper → `cum_hash` mismatch → seal invalid
- Trace tamper → `trace_hash` mismatch → seal invalid
- Environment drift → `env_hash` mismatch → seal invalid (boot fail-closed)
- Kernel change → `kernel_hash` mismatch → seal invalid

A seal is not optional. An unsealed HELEN OS epoch has no verifiable identity.

---

## 8. HELEN's Role Inside HELEN OS

HELEN is **not the sovereign**.

HELEN is the **cognitive compiler**:

| HELEN can | HELEN cannot |
|-----------|--------------|
| Read context | Self-authorize |
| Retrieve memory | Seal |
| Structure proposals | Ship |
| Emit candidate evidence | Rewrite law |
| Research, simulate, reflect | Bypass reducer |
| Operate in researcher mode | Write Channel A |

HELEN's output is always one of:
- **Proposal** (requires reducer validation)
- **Candidate evidence** (requires reducer acceptance)
- **Trace** (Channel C, authority=false)
- **Memory entry** (Channel B, non-sovereign)

Nothing HELEN produces is authoritative without reducer validation.

---

## 9. HAL / Reducer Role

HAL and the reducer perform **sovereignty gating**:

| HAL / Reducer can | HAL / Reducer cannot |
|------|------|
| Apply law | Generate proposals |
| Issue verdicts | Write narrative |
| Validate evidence | Self-modify law |
| Authorize ledger writes | Accept authority from L0/L1 |
| Emit receipts | Bypass the ledger |

The reducer is **not creative**. It applies defined rules to typed evidence and produces a verdict.

Verdict types:
- `PASS` → evidence accepted, event appended to ledger
- `FAIL` → evidence rejected, rejection receipt appended
- `NEEDS_APPROVAL` → EXECUTE-class action blocked pending human approval

---

## 10. Researcher Mode

Researcher Mode is a clean **non-sovereign operating mode** of HELEN OS.

```
authority: false
kernel access: none
ledger write: disabled
output class: dialogue + candidate evidence only
```

In Researcher Mode:
- HELEN may theorize, model, draft, simulate
- All output is tagged `authority=false`
- No output enters Channel A
- No receipt is produced (because no sovereign action occurred)

Researcher Mode is **valuable** because it expands thought without leaking into authority.

It is not a sandbox bypass. It is a constitutionally clean mode of operation.

---

## 11. What Is Mature (Current Epoch)

The following subsystems are **mature** and should not be destabilized by new development:

| Subsystem | Status |
|-----------|--------|
| Constitutional separation (L0-L3) | ✅ Mature |
| Receipts-first doctrine | ✅ Mature |
| Append-only ledger | ✅ Mature |
| Deterministic reducer model | ✅ Mature |
| Trace separation (Channel C) | ✅ Mature |
| Seal-based identity closure | ✅ Mature |
| Federation as composition of sealed towns | ✅ Mature |
| SOUL layer (5 laws, ~500 words) | ✅ Verified |
| Retrieval layer (JMT manifest, jmt_retrieval.py) | ✅ Verified |
| Terminal colors (ADHD-friendly) | ✅ Verified |
| Proof-pack mindset (claims → facts via gates) | ✅ Active |

---

## 12. What HELEN OS Is Becoming

Not a chatbot shell.
Not an agent swarm.
Not a mythology wrapper.

HELEN OS is becoming:

> **A governance-grade, replay-verifiable operating substrate for agentic civilization systems.**

Or more simply:

> **An OS for bounded intelligence under constitutional law.**

The distinguishing property is:

```
expression is rich, but authority is sparse
```

That is why the system can become powerful without becoming incoherent.

---

## 13. The Next Correct Move

Not more mythology.
Not more surface complexity.

The next correct move is to freeze HELEN OS as a **standard** with:

1. canonical primitives (this document)
2. conformance rules (test vectors)
3. proof pack (artifacts)
4. implementation verification (gate suite)

That is how HELEN OS stops being "an idea" and becomes infrastructure.

**Operational posture:**

```
1. Freeze canonical primitives
2. Run verification gates
3. Generate proof pack
4. Tag implementation state
5. Only then open the next epoch
```

---

## 14. Verification Requirements

Every HELEN OS epoch must produce a **proof pack** before it is considered complete.

### Required Gate Phases

| Phase | Name | Requirement |
|-------|------|-------------|
| P0 | Existence | All canonical files present |
| P1 | Integrity | Imports OK, JSON valid, sizes within bounds |
| P2 | Behavior | Each component exhibits correct behavior (deterministic) |
| P3 | Regression | No secrets, no authority leakage, no policy bypass |
| P4 | Artifacts | Proof pack created and archivable |

### Required Proof Pack Contents

```
artifacts/{EPOCH}_{DATE}/
    ├── [implementation files]      (the actual code shipped)
    ├── GATE_REPORT.md              (gate-by-gate results)
    ├── VERIFICATION_SUMMARY.txt    (one-page pass/fail)
    ├── imports.txt                 (import verification)
    ├── git_head.txt                (commit hash)
    ├── git_status.txt              (uncommitted changes)
    └── unittest.txt                (test runner output)
```

### Authority Checks

Each component in the proof pack must demonstrate:

1. **No self-authorization** — nothing writes Channel A without GovernanceVM
2. **No authority bleed** — forbidden tokens (`SHIP`, `SEALED`, `APPROVED`, `FINAL`) absent from non-sovereign output
3. **No bypass** — every state-changing action has a receipt
4. **Determinism** — same input → same output (required for reducer, retrieval, and trace)

---

## 15. Conformance Rules

An implementation is **HELEN OS conformant** if and only if:

| Rule | Requirement |
|------|-------------|
| C1 | Channel A is append-only and hash-chained |
| C2 | Only GovernanceVM / TownAdapter writes Channel A |
| C3 | All sovereign events have receipts |
| C4 | SOUL is ≤ 650 words |
| C5 | Retrieval returns ≤ max_results frameworks per turn |
| C6 | Retrieval is deterministic (same query → same result) |
| C7 | Seal binds ledger tip + trace tip + env_hash + kernel_hash |
| C8 | RunTrace carries `authority=false` on all entries |
| C9 | Memory (Channel B) forbids authority-claiming language |
| C10 | Reducer verdicts are typed (PASS / FAIL / NEEDS_APPROVAL) |

Failing any conformance rule is a constitutional breach, not a configuration issue.

---

## 16. Forbidden Patterns

The following patterns are **explicitly prohibited** under this canon:

```python
# ❌ FORBIDDEN: Agent writing directly to ledger
agent.ledger.append(event)  # Must go through reducer

# ❌ FORBIDDEN: Self-authorization
if model_says_ok:
    execute_action()  # Must pass reducer gate

# ❌ FORBIDDEN: Non-sovereign channel claiming authority
memory.append({"event": "APPROVED", "authority": true})  # Banned

# ❌ FORBIDDEN: Bypassing receipt chain
ledger_file.write(json.dumps(event))  # Must go through ReceiptChain

# ❌ FORBIDDEN: Soft failure on receipt write
try:
    chain.append(event)
except:
    pass  # Must fail-closed on receipt failure
```

---

## 17. Glossary

| Term | Definition |
|------|-----------|
| **Receipt** | Cryptographic proof (SHA256) of a ledger event. No receipt = not real. |
| **Reducer** | Deterministic function that validates evidence and produces verdicts. |
| **Ledger** | Append-only NDJSON log. Channel A only. Sole source of sovereign truth. |
| **Seal** | Cryptographic closure binding ledger tip, trace tip, env hash, kernel hash. |
| **Sovereign** | Having the power to make authoritative state. Only L3/reducer is sovereign. |
| **Non-sovereign** | May propose, may trace, may remember. Cannot authorize. |
| **Channel A** | Sovereign ledger. The only world-changing channel. |
| **Channel B** | MemoryKernel. Non-sovereign, conflict-aware, continuity-focused. |
| **Channel C** | RunTrace. Telemetry and cognition traces. Authority=false. |
| **Researcher Mode** | Clean non-sovereign HELEN mode. authority=false, no ledger write. |
| **Proof pack** | Archivable set of artifacts proving implementation correctness. |
| **Gate** | A deterministic check that a claim is true. Replaces narrative. |
| **Conformance** | Implementation satisfies all C1–C10 rules. |
| **Authority bleed** | Forbidden tokens appearing in non-sovereign output. A violation. |
| **Fail-closed** | On error or missing receipt, refuse to proceed. Never silently continue. |
| **SOUL** | Frozen identity prompt for HELEN. Max ~500 words, 5 invariant laws. |
| **PLUGINS** | JMT framework catalog. Metadata only. Retrieved per-turn. |
| **RETRIEVAL** | Semantic keyword match to inject 2-3 frameworks per turn. |
| **MEMORY** | Channel B entries. Lessons and prior context. Not truth. |

---

## 18. Amendment Protocol

This document may be amended only through:

1. **Proposal** — express the change as typed candidate evidence
2. **Validation** — reducer validates the proposal against existing law
3. **Ledger commit** — amendment is appended to Channel A with receipt
4. **Version bump** — this document gets new version `HELEN_OS_CANON_V{N+1}.md`
5. **Verification** — new proof pack generated

An amendment that skips any of these steps is **not valid**.

---

## 19. Document History

| Version | Date | Change |
|---------|------|--------|
| V1 | 2026-03-06 | Initial canonical form, frozen after verification |

---

## 20. Certification

This document is the canonical reference for HELEN OS epoch current.

```
Prime invariant:    No receipt → no ship
Core formula:       LLM proposes → reducer validates → ledger commits
System identity:    Constitutional multi-agent OS, cognition non-sovereign
Authority structure: L0 (agents) → L1 (servitors) → L2 (street) → L3 (kernel)
Channel model:      A (sovereign) / B (memory) / C (trace)
Write gate:         GovernanceVM only
Seal:               ledger + trace + environment + kernel
HELEN role:         Cognitive compiler (non-sovereign)
Reducer role:       Sovereignty gate (sole authority)
Ledger role:        Truth surface (append-only, hash-chained)

Expression is rich. Authority is sparse.
```

**Status:** ✅ VERIFIED — 14/14 conformance gates passed 2026-03-06
**Proof pack:** `artifacts/20260306_verification/` (CANON_GATE_REPORT.md)
**SHA256:** `a6b8feba3d4ca1750f5f039844f969493714a1e0f1b62c3db5dd4e1ee926309e`
**Next step:** Amendment via §18 protocol only. This epoch is closed.

---

*HELEN OS Canon V1 — 2026-03-06 — VERIFIED*
