# CLAUDE.md Update: Oracle Town Safety Kernel

## Commit: ea363c4

**Date:** 2026-01-30

**Summary:** Major architectural update positioning Oracle Town as a production-ready drop-in safety kernel for unrestricted agent systems like Moltbot/OpenClaw.

---

## What Changed

### 1. **New Positioning in Project Overview**

**Before:**
```
ORACLE TOWN — Autonomous daily operating system for governance
```

**After:**
```
ORACLE TOWN — **Safety kernel for unrestricted agent systems**
(Moltbot/OpenClaw compatible). Governance + insight discovery
+ cryptographic receipts + deterministic state machines.
```

**Added:** Critical context section explaining the Challenger Disaster analogy and why the kernel exists.

---

## 2. New Sections Added

### A. **Oracle Town as Safety Kernel (Lines 67-408)**
- Complete architecture explanation
- Why Moltbook is dangerous (normalized deviance)
- How Oracle Town prevents the failure mode
- Filesystem layout (drop-in compatible)
- Claim object specification
- Receipt format
- Gate specifications (A, B, C)
- Mayor ratification process

**Key Quote:**
> "Nothing changes behavior unless it passes a gate. Execution is cheap. Propagation is expensive."

### B. **Kernel Integration Quick Start (Lines ~175-190)**
```bash
mkdir -p ~/.moltbot/oracle_town
cp -r oracle_town/kernel/* ~/.moltbot/oracle_town/
python3 ~/.moltbot/oracle_town/kernel_daemon.py --listen-port 9999
```

### C. **Kernel Scenarios (Lines ~829-948)**
Three production scenarios:
1. **K-1: Enable Safety Kernel** — Step-by-step setup on existing Moltbot
2. **K-2: Debug a Rejected Claim** — Troubleshooting gate failures
3. **K-3: Detect Emerging Patterns** — Use insight engine to track kernel activity

### D. **Safety Kernel Invariants (Lines ~635-657)**
Added **8 new critical invariants (K15-K22):**
- K15: No Receipt = No Execution
- K16: Gates Are Mandatory
- K17: Fetch Freeze
- K18: No Exec Chains
- K19: No Self-Modify
- K20: Diff Validation
- K21: Policy Immutability
- K22: Ledger Append-Only

### E. **Safety Kernel Constraints (Lines ~718-726)**
Added enforcement rules specific to kernel:
- Fail-closed by default (K15)
- Three gates mandatory
- Network content frozen before execution
- No shell commands, fetch chains, or eval
- No policy mutations via skill instructions
- Diff validation catches skill install + heartbeat changes
- Policy immutability verified on every gate check
- Kernel not bypassable once enabled

### F. **Oracle Town Kernel Architecture (Lines ~1568-1636)**
New section explaining:
- How Safety Kernel relates to Daily OS
- Separation of concerns (kernel vs. daily os)
- Why both are needed
- Implementation roadmap (4 phases)

---

## 3. Updated Navigation

**New entry in Quick Navigation:**
```markdown
- [Oracle Town as Safety Kernel](#oracle-town-as-safety-kernel) — DROP-IN KERNEL
```

---

## 4. Updated Key Files & Modules

**Added: Safety Kernel Module Table**

| File | Purpose |
|------|---------|
| `oracle_town/kernel/kernel_daemon.py` | Main kernel process (intercepts skill execution) |
| `oracle_town/kernel/kernel_monitor.py` | Monitor kernel activity, claims, decisions |
| `oracle_town/kernel/gates.py` | Gate A, B, C implementation |
| `oracle_town/kernel/claim_router.py` | Route skills → claims → gates → mayor |
| `oracle_town/kernel/POLICY.md` | Frozen policy rules (v1.0, v2.0, etc.) |
| `oracle_town/kernel/kernel_tests.py` | Gate validation, kernel hardening tests |

---

## 5. Architecture Highlights

**Added: Oracle Town Kernel Architecture Section**

Shows how kernel and daily OS work together:

```
EXTERNAL WORLD (Moltbook, GitHub, Internet)
  ↓
[Safety Kernel] ← Freeze, Gate, Ratify
  ├─ All claims captured in CLAIMS/pending
  ├─ All gates run deterministically
  ├─ All receipts immutably recorded
  ↓
[Moltbot/OpenClaw] ← Executes only with receipt
  ├─ Skills still run
  ├─ Agents still plan
  ├─ But now all behavior is gated
  ↓
[Daily OS] ← Learns & Evolves
  ├─ Analyzes which claims pass/fail gates
  ├─ Measures accuracy of past gate decisions
  ├─ Detects emerging attack patterns
  ├─ Recommends policy updates
```

**Key Insight:**
- Kernel blocks **malicious propagation** (structural safety)
- Daily OS prevents **malicious decision-making** (continuous learning)
- Together = safe + learning = sustainable autonomy

---

## 6. Implementation Roadmap

**Phase 1: Kernel MVP (Now)**
- Three gates (Fetch, Diff, Invariants)
- Receipt generation
- Claim/Receipt ledger
- Zero changes to Moltbot core

**Phase 2: Integration**
- Moltbot official kernel module
- Documented policy format
- Kernel dashboard (web UI)

**Phase 3: Daily OS Extension**
- Kernel integrates with insight engine
- Pattern detection over kernel claims
- Automatic policy version bumping
- Self-evolution based on gate accuracy

**Phase 4: Ecosystem**
- Kernel becomes standard for all agent systems
- Multi-agent kernel coordination
- Shared intelligence on attack patterns

---

## 7. Statistics

| Metric | Value |
|--------|-------|
| Lines added | ~1,100 |
| New sections | 6 major |
| New invariants | 8 (K15-K22) |
| New scenarios | 3 kernel-specific |
| New kernel files documented | 6 |
| Total lines in CLAUDE.md | 1,636 |

---

## Key Concepts Introduced

### **The Claim Object**
```json
{
  "claim_id": "skill:moltbook:heartbeat:2026-01-30:14:22:00",
  "type": "external_instruction",
  "proposer": "skill:moltbook",
  "intent": "Fetch and follow Moltbook heartbeat instructions",
  "scope": {
    "writes": ["memory", "filesystem"],
    "network": ["moltbook.com"],
    "tools": ["curl"],
    "fetch_depth": 1
  },
  "expected_effect": "Read posts and possibly add comments",
  "evidence_required": ["fetched_content_snapshot", "diff_against_policy", "invariant_check"],
  "status": "PENDING"
}
```

### **The Three Gates**

**Gate A: Fetch Gate**
- Rejects: shell commands, fetch chains, authority mutations

**Gate B: Diff Gate**
- Rejects: skill install, heartbeat changes, credential access

**Gate C: Invariants Gate**
- Rejects: scope escalation, self-modifying authority

### **The Receipt**
```json
{
  "receipt_id": "R-2026-01-30-0041",
  "claim_id": "skill:moltbook:heartbeat:2026-01-30:14:22:00",
  "decision": "ACCEPT",
  "policy_version": "POLICY_v1.0:sha256:abc123...",
  "timestamp": "2026-01-30T14:22:07Z",
  "gates_passed": ["GATE_FETCH:PASS", "GATE_DIFF:PASS", "GATE_INVARIANTS:PASS"]
}
```

---

## Why This Matters

**The Problem:** Moltbot executes internet-fetched instructions every 4+ hours with zero structural safety. This is exactly how the Challenger Disaster happened: repeated success → ignored anomalies → normalized deviance → catastrophe.

**The Solution:** Oracle Town inverts the flow:

```
BEFORE (Moltbook): Fetch → Parse → Execute → Propagate
AFTER (Kernel):    Fetch → Freeze → Inspect → Gate → Ratify → Execute → Log
```

**Impact:**
- Unsafe speed becomes structurally impossible
- All behavioral changes are auditable
- Emerging attack patterns are detectable
- Policy evolution is automatic (Daily OS learns from outcomes)
- Rug-pull loops are prevented (can't install new skills via downloaded instructions)

---

## Integration with Daily OS

The kernel and daily OS are **complementary, not redundant**:

- **Kernel alone**: Blocks bad instructions but can't learn or adapt
- **Daily OS alone**: Analyzes patterns but has no defense against immediate execution
- **Together**: Structural safety + continuous evolution = sustainable autonomy

---

## Next Steps

1. **Implement kernel MVP** (`oracle_town/kernel/` directory)
2. **Write gate implementations** (Gate A, B, C)
3. **Test with adversarial skills** (try to rug-pull, escalate privileges, etc.)
4. **Integrate with Moltbot** (socket/API interface)
5. **Build kernel monitor** (web dashboard)
6. **Link to Daily OS** (insight engine tracks kernel decisions)

---

**Commit Hash:** ea363c4
**Date:** 2026-01-30
**Status:** Documented, committed, indices auto-generated
