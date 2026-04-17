# GOVERNANCE INDEX — Constitutional Law Layer

This directory is the canonical source of frozen governance law for HELEN's kernel boundary.

---

## Directory Structure

```
GOVERNANCE/
├── CONSTITUTION/           (Frozen architectural laws)
├── REGISTRIES/             (Reference enumeration registries)
├── RUNTIME/                (Operational governance & policy)
├── STEP_4_CONFORMANCE/     (Active conformance audit work)
└── INDEX.md                (This file)
```

---

## CONSTITUTION/ — Frozen Architectural Laws

The three constitutional surfaces that lock the kernel boundary. These documents are immutable unless major version bumped.

| Document | Version | Status | Purpose | Tests |
|----------|---------|--------|---------|-------|
| **API_CONTRACT_DO_NEXT_V1.md** | 1.0.0 | FROZEN | Request/response schema for /do_next endpoint | 45 |
| **SESSION_PERSISTENCE_SEMANTICS_V1.md** | 1.0.0 | FROZEN | Session state, resumption, continuity, epoch | 48 |
| **LIFECYCLE_INVARIANTS_V1.md** | 1.0.0 | FROZEN | 7-phase execution order, receipt lineage, laws | 63 |
| **BOUNDARY_FREEZE_V1.md** | 1.0.0 | FROZEN | Ratification summary of boundary triad | — |

**Total freeze-test coverage: 156 tests**

### Dependency Graph
```
API_CONTRACT_DO_NEXT_V1
  ← DISPATCH_DECISION_TABLE_V1 (routing)
  ← SESSION_PERSISTENCE_SEMANTICS_V1 (session_id format)

SESSION_PERSISTENCE_SEMANTICS_V1
  ← API_CONTRACT_DO_NEXT_V1 (session_id format)
  ← INFERENCE_POLICY_FROZEN_V1 (determinism)

LIFECYCLE_INVARIANTS_V1
  ← API_CONTRACT_DO_NEXT_V1 (phases 1, 7)
  ← SESSION_PERSISTENCE_SEMANTICS_V1 (phase 2)
  ← AUDIT_FINDING_REGISTRY_V1 (phase 3)
  ← DISPATCH_DECISION_TABLE_V1 (phase 4)
  ← RECEIPT_SCHEMA_REGISTRY_V1 (receipt lineage)
```

---

## REGISTRIES/ — Reference Enumerations

Reference constitutional surfaces that define enumerated types and registries. Frozen but serve as lookup tables for the architecture.

| Registry | Version | Status | Purpose |
|----------|---------|--------|---------|
| AUDIT_FINDING_REGISTRY_V1.md | 1.0.0 | FROZEN_CANDIDATE | 13 finding codes (UNSUPPORTED_CLAIM, MISSING_PROVENANCE, etc.) |
| RECEIPT_SCHEMA_REGISTRY_V1.md | 1.0.0 | FROZEN_CANDIDATE | 8 receipt types (KNOWLEDGE_AUDIT, DISPATCH_DECISION, etc.) |
| DISPATCH_DECISION_TABLE_V1.md | 1.0.0 | FROZEN | Routing decisions (KERNEL, DEFER, REJECT) |

---

## RUNTIME/ — Operational Governance

Operational documents that guide implementation and interpretation. Mutable (no version bumps required, just date notes).

| Document | Status | Purpose |
|----------|--------|---------|
| HELEN_GOVERNANCE_FREEZE_V1.md | UPDATED | Governance freeze status, Step 4 completion, next phase |

---

## STEP_4_CONFORMANCE/ — Active Audit Work

Working directory for Step 4A (Implementation Conformance Check). Temporary artifacts; not constitutional source.

| Subdirectory | Purpose |
|--------------|---------|
| plans/ | Conformance audit plans |
| checklists/ | Verification checklists |
| conformance_reports/ | Results of conformance checks |
| drift_reports/ | Constitutional violations found in code |
| test_matrices/ | Freeze-test specifications |

---

## Authority & Precedence Rules

### 1. Constitutional Law Precedence (Highest)

Documents in CONSTITUTION/ are the source of truth for architecture.

- **Change process:** Requires major version bump (2.0.0) and explicit ratification
- **Enforcement:** Code must conform to law; if divergent, code is wrong
- **Scope:** Defines what may enter/leave kernel, what survives restart, what order execution takes

**Example:** If code does not execute phases 1→2→3→4→5→6→7 in strict order, code violates LIFECYCLE_INVARIANTS_V1 (constitutional violation).

### 2. Registry Precedence (Medium-High)

Documents in REGISTRIES/ enumerate valid codes and types referenced by architecture.

- **Change process:** Requires version bump (new codes require minor bump)
- **Enforcement:** Finding codes must be in AUDIT_FINDING_REGISTRY_V1, receipt types must be in RECEIPT_SCHEMA_REGISTRY_V1
- **Scope:** Reference tables for architecture

**Example:** If audit emits a finding with code "INVALID_FINDING", it's a violation because code is not in AUDIT_FINDING_REGISTRY_V1.

### 3. Operational Governance (Medium)

Documents in RUNTIME/ provide policy, doctrine, and guidance. Normative but mutable.

- **Change process:** Update + date note (no version bump)
- **Enforcement:** Guides implementation but subordinate to constitutional law
- **Scope:** Interpretation and policy

**Example:** HELEN_GOVERNANCE_FREEZE_V1.md can be updated to note that Step 4A passed; this does not require version bump.

### 4. Audit Work (Lowest)

Documents in STEP_4_CONFORMANCE/ are diagnostic and temporary. Not authoritative.

- **Change process:** Mutable without restriction
- **Enforcement:** Documents what must be fixed to reach zero violations
- **Scope:** Working space for conformance verification

**Example:** Conformance reports can be updated, retried, archived; they do not affect constitutional law.

---

## Version Precedence (When Multiple Versions Exist)

If multiple versions of a constitutional document exist:

1. **FROZEN version in GOVERNANCE/CONSTITUTION/ is canonical**
2. Any _PATCHED, _FINAL, _DRAFT variants in root are deprecated (move to GOVERNANCE/ or delete)
3. No parallel authorities; one filename = one source of truth

---

## Reading Order for Understanding the Boundary

**Start here:**
1. BOUNDARY_FREEZE_V1.md — Overview of boundary triad and drift vectors

**Then deep-dive by layer:**
2. CONSTITUTION/API_CONTRACT_DO_NEXT_V1.md — What enters and leaves
3. CONSTITUTION/SESSION_PERSISTENCE_SEMANTICS_V1.md — What survives restart
4. CONSTITUTION/LIFECYCLE_INVARIANTS_V1.md — How execution flows

**For reference:**
5. REGISTRIES/DISPATCH_DECISION_TABLE_V1.md — Routing decisions
6. REGISTRIES/AUDIT_FINDING_REGISTRY_V1.md — Finding codes
7. REGISTRIES/RECEIPT_SCHEMA_REGISTRY_V1.md — Receipt types

**For policy context:**
8. RUNTIME/HELEN_GOVERNANCE_FREEZE_V1.md — Governance status and next steps

---

## Step 4A: Implementation Conformance Check

**Current Status:** Constitutional boundary is FROZEN and RATIFIED.

**Next Phase:** Verify live code conforms to frozen law (zero violations required).

**Location:** GOVERNANCE/STEP_4_CONFORMANCE/

**Six Required Conformance Checks:**
1. Phase-order conformance (1→2→3→4→5→6→7)
2. Receipt-lineage conformance (parent_receipt_id integrity)
3. Epoch conformance (single increment per call)
4. Reject-path conformance (blocked paths obey law)
5. Replay conformance (identical state + request = identical outcome)
6. Persistence atomicity (commit full or fail full)

**Go/No-Go Gate:** Knowledge Compiler V2 proceeds only if **ZERO constitutional violations** found.

---

## Key Principles

✅ **One filename = one source of truth** — No split authority, no parallel versions
✅ **Constitutional documents are law** — Implementation must conform, not reinterpret
✅ **Registries are enumerations** — Valid codes/types frozen, new ones require version bump
✅ **Operational docs add context** — But do not override or weaken constitutional law
✅ **Audit work is temporary** — Archived once conformance passes
✅ **Replay determinism** — Same frozen state + request = same outcome

---

**Last Updated:** 2026-04-05
**Structure:** GOVERNANCE/ as canonical law layer
**Status:** Boundary FROZEN and RATIFIED; ready for Step 4A conformance audit
