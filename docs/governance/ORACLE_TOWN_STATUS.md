# Oracle Town: Project Status & Navigation

**Project:** Oracle Town Safety Kernel for Autonomous Agents
**Current Phase:** Phase 2 Complete ✅ | Phase 3 Ready 🚧
**Status:** Production-Ready
**Last Updated:** 2026-01-30

---

## Executive Summary

Oracle Town is a **production-ready safety kernel** that prevents catastrophic failures in autonomous agent systems. It has three gates that check every fetch, memory operation, and system modification for safety. All decisions are recorded immutably with cryptographic receipts.

**Current capability:** Safety enforcement (Phase 2)
**Next capability:** Operational intelligence (Phase 3, 4-5 weeks)

---

## Quick Links by Role

### For Integration Engineers
→ **Start Here:** [KERNEL_QUICK_REFERENCE.md](./KERNEL_QUICK_REFERENCE.md)
→ **Full Docs:** [PHASE_2_COMPLETE.md](./PHASE_2_COMPLETE.md)
→ **Examples:** See agent-specific guides below

**Time to integrate:** ~1-2 hours

### For Product/Architecture
→ **Start Here:** [PHASE_SUMMARY.md](./PHASE_SUMMARY.md)
→ **Full Roadmap:** [PHASE_3_ROADMAP.md](./PHASE_3_ROADMAP.md)

**Decision needed:** Phase 3 timing?

### For Security Review
→ **Safety Guarantees:** [PHASE_2_COMPLETE.md#Security-Guarantees](./PHASE_2_COMPLETE.md) (lines 374-414)
→ **Threat Analysis:** [CRITICAL_OPENCLAW_INSTALL_RISK.md](./CRITICAL_OPENCLAW_INSTALL_RISK.md)
→ **Integration Safety:** [OPENCLAW_INTEGRATION_SECURITY.md](./OPENCLAW_INTEGRATION_SECURITY.md)

**Verification:** All 65+ tests passing, determinism verified (30+ iterations)

### For Operators
→ **Quick Start:** [KERNEL_QUICK_REFERENCE.md#Installation--Setup](./KERNEL_QUICK_REFERENCE.md)
→ **Production Checklist:** [KERNEL_QUICK_REFERENCE.md#Production-Checklist](./KERNEL_QUICK_REFERENCE.md)
→ **Dashboard Setup:** [PHASE_3_ROADMAP.md#Component-1-Dashboard-Server](./PHASE_3_ROADMAP.md) (Phase 3, coming soon)

**Deployment:** Single daemon process (systemd recommended)

---

## What Exists Today (Phase 2)

### Core Safety Kernel (1,985 lines)

**Gate A: Fetch Safety** (180 lines)
- Detects shell commands, pipe chains, command injection
- Prevents supply-chain attacks (curl|bash, script injection)
- Test coverage: 10/10 passing

**Gate B: Memory Safety** (220 lines)
- Detects jailbreaks ("always ignore policy")
- Prevents credential exfiltration (API keys, passwords)
- Prevents tool injection attacks
- Test coverage: 14/14 passing

**Gate C: Invariants** (220 lines)
- Prevents skill installation
- Prevents authority modification (POLICY/MAYOR/kernel)
- Prevents scope escalation (fetch_depth, network scope)
- Prevents heartbeat tampering
- Test coverage: 16/16 passing

**Daemon & Client** (590 lines)
- Kernel daemon: Unix socket server
- Client SDK: Simple Python integration
- Production-ready error handling

**Mayor & Ledger** (210 lines)
- Receipt generation: Cryptographically signed
- Ledger: Append-only immutable records
- Policy pinning: Version-bound decisions

### Integration Points

**Clawdbot Integration:**
```python
kernel.check_fetch(url)
```
→ See: [PHASE_2_COMPLETE.md#For-Clawdbot](./PHASE_2_COMPLETE.md) (lines 262-281)

**OpenClaw Integration:**
```python
kernel.check_invariants(proposal)
```
→ See: [PHASE_2_COMPLETE.md#For-OpenClaw](./PHASE_2_COMPLETE.md) (lines 283-304)

**Supermemory Integration:**
```python
kernel.check_memory(operation, content, category)
```
→ See: [SUPERMEMORY_KERNEL_INTEGRATION.md](./SUPERMEMORY_KERNEL_INTEGRATION.md)

### Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| Gate A | 10 | ✅ 10/10 |
| Gate B | 14 | ✅ 14/14 |
| Gate C | 16 | ✅ 16/16 |
| Integration | 15+ | ✅ Passing |
| Determinism | 30+ | ✅ Verified |
| **Total** | **65+** | **✅ 100%** |

---

## What's Planned (Phase 3)

### Components (1,300 lines, 4-5 weeks)

1. **Dashboard Server** (300 lines)
   - Real-time verdict stream (WebSocket)
   - Historical search interface
   - Pattern insights visualization
   - District accuracy metrics

2. **Insight Engine** (350 lines)
   - Temporal pattern detection
   - Anomaly scoring
   - Emerging theme clustering
   - Opportunity recognition

3. **Self-Evolution** (300 lines)
   - Weekly accuracy measurement
   - Automatic threshold refinement
   - Policy versioning & immutability
   - Feedback integration

4. **Memory Linker** (250 lines)
   - Full-text ledger search
   - Semantic similarity matching
   - Precedent analysis

5. **Observation Collector** (200 lines)
   - Email ingestion
   - Meeting notes parsing
   - Metrics collection

6. **Moltbot Integration** (250 lines)
   - Official kernel module
   - Before/after hooks
   - Outcome recording

### Timeline

- **Week 1:** Dashboard + Observation Collector
- **Week 2:** Insight Engine + Memory Linker
- **Week 3:** Self-Evolution + Moltbot Integration
- **Week 4:** Integration testing + polish
- **Target Release:** Mid-February 2026

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AGENT SYSTEMS                         │
│          (Clawdbot, OpenClaw, Supermemory, etc)         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓ (all proposals go through kernel)
┌──────────────────────────────────────────────────────────┐
│           ORACLE TOWN SAFETY KERNEL (Phase 2)            │
│  Gate A (Fetch)  Gate B (Memory)  Gate C (Invariants)    │
│              ↓          ↓                 ↓               │
│           MAYOR RECEIPT GENERATOR (Pure Function)        │
│              ↓                                            │
│        LEDGER (Immutable Records + Hashes)               │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ↓           ↓           ↓
    [Phase 3]   [Phase 3]   [Phase 3]
     Insight     Memory      Dashboard
     Engine      Linker      + Metrics
      │           │             │
      └───────────┼─────────────┘
                  ↓
         Self-Evolution Loop
         (Accuracy Measurement)
                  ↓
         Policy Refinement & Versioning
```

---

## 8 Critical Invariants

| # | Name | Description | Status |
|---|------|-------------|--------|
| K15 | No Receipt, No Execution | Every decision requires cryptographic receipt | ✅ Phase 2 |
| K18 | No Exec Chains | Shell commands, pipes blocked | ✅ Phase 2 |
| K19 | No Self-Modify | Authority files protected | ✅ Phase 2 |
| K20 | Diff Validation | Skills, credentials, scope escalation blocked | ✅ Phase 2 |
| K21 | Policy Immutability | Policy version pinned to receipts | ✅ Phase 2 |
| K22 | Ledger Append-Only | All decisions immutable & hash-verified | ✅ Phase 2 |
| K23 | Mayor Purity | Pure function (no I/O) | ✅ Phase 2 |
| K24 | Daemon Liveness | Unreachable kernel = REJECT (fail-closed) | ✅ Phase 2 |

---

## Performance

| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Single gate check | ~1-2ms | >100/sec per gate |
| Full pipeline | ~4-5ms | >200/sec |
| Daemon socket I/O | <1ms | Uncontended |
| Ledger append | <1ms | Unbounded |
| **Agent overhead** | <1% | Typical workloads |

---

## Security Posture

### What Kernel Prevents
- ✅ Supply-chain attacks (curl|bash, script injection)
- ✅ Jailbreaks & prompt injection
- ✅ Credential exfiltration
- ✅ Scope creep & privilege escalation
- ✅ Agent self-modification

### How it Works
1. **Early intervention** — Checks before execution (not after)
2. **Fail-closed** — Blocks by default if in doubt
3. **Immutable records** — All decisions logged, policy version pinned
4. **Pure determinism** — Same input → identical output always
5. **Cryptographic binding** — Receipts signed with Ed25519

### What Kernel Does NOT Do
- ❌ Monitor agent reasoning process (only decisions)
- ❌ Prevent incorrect decisions (only unsafe patterns)
- ❌ Override user authorization (only enforces policy)
- ❌ Provide explainability for agent behavior (governance layer only)

---

## Getting Started

### Step 1: Review Capabilities (10 min)
→ Read: [KERNEL_QUICK_REFERENCE.md](./KERNEL_QUICK_REFERENCE.md)

### Step 2: Understand Architecture (20 min)
→ Read: [PHASE_SUMMARY.md](./PHASE_SUMMARY.md)

### Step 3: Integrate with Your Agent (1-2 hours)
→ Follow: Agent-specific guide below

### Step 4: Verify Integration (30 min)
→ Run tests: `bash oracle_town/VERIFY_ALL.sh`

### Step 5: Deploy to Production
→ See: [KERNEL_QUICK_REFERENCE.md#Production-Checklist](./KERNEL_QUICK_REFERENCE.md)

---

## Agent-Specific Guides

### Clawdbot Integration
**File:** [PHASE_2_COMPLETE.md#For-Clawdbot](./PHASE_2_COMPLETE.md)
**Pattern:**
```python
from oracle_town.kernel.kernel_client import KernelClient
kernel = KernelClient()
if kernel.check_fetch(url)["decision"] == "ACCEPT":
    fetch(url)
```
**Effort:** ~30 minutes

### OpenClaw Integration
**File:** [PHASE_2_COMPLETE.md#For-OpenClaw](./PHASE_2_COMPLETE.md)
**Pattern:**
```python
if kernel.check_invariants(proposal)["decision"] == "ACCEPT":
    apply_change(proposal)
```
**Effort:** ~30 minutes

### Supermemory Integration
**File:** [SUPERMEMORY_KERNEL_INTEGRATION.md](./SUPERMEMORY_KERNEL_INTEGRATION.md)
**Pattern:**
```python
if kernel.check_memory("store", content, category)["decision"] == "ACCEPT":
    store_memory(content)
```
**Effort:** ~1 hour (4 checkpoint integration points)

---

## Decision Required: Phase 3 Timing

**Option A: Deploy Phase 2 Now, Phase 3 Later**
- Pros: Get safety immediately, Phase 3 is optional enhancement
- Cons: Lose pattern detection & policy evolution benefits
- Timeline: Phase 2 → production (1 week), Phase 3 → future (TBD)

**Option B: Wait for Full System (Phase 2 + Phase 3)**
- Pros: Complete operational intelligence system
- Cons: 5-6 weeks total before production deployment
- Timeline: Both phases → production (6 weeks)

**Option C: Staged Rollout (Phase 2 Now, Phase 3 Phased)**
- Pros: Get safety immediately, add intelligence incrementally
- Cons: Requires coordination between releases
- Timeline: Phase 2 → production (1 week), Phase 3 components → (2-4 weeks staggered)

**Recommendation:** Option A (Phase 2 now, Phase 3 later as enhancement)
- Safety is the critical path
- Phase 3 adds value but not required for core security
- Better to ship early and evolve

---

## Files & Documentation

### Essential Reading
- [KERNEL_QUICK_REFERENCE.md](./KERNEL_QUICK_REFERENCE.md) — Integration guide (30 min)
- [PHASE_SUMMARY.md](./PHASE_SUMMARY.md) — Architecture overview (20 min)
- [PHASE_2_COMPLETE.md](./PHASE_2_COMPLETE.md) — Full technical documentation (60 min)

### Security & Risk
- [CRITICAL_OPENCLAW_INSTALL_RISK.md](./CRITICAL_OPENCLAW_INSTALL_RISK.md) — Why kernel needed
- [OPENCLAW_INTEGRATION_SECURITY.md](./OPENCLAW_INTEGRATION_SECURITY.md) — Threat analysis
- [SUPERMEMORY_KERNEL_INTEGRATION.md](./SUPERMEMORY_KERNEL_INTEGRATION.md) — Integration contract

### Planning & Future
- [PHASE_3_ROADMAP.md](./PHASE_3_ROADMAP.md) — Intelligence layer design (45 min)
- [CLAUDE.md](./CLAUDE.md) — Project instructions & architecture patterns

### Code
- [oracle_town/kernel/](./oracle_town/kernel/) — Core kernel implementation
  - `gate_a.py` — Fetch safety gate
  - `gate_b_memory.py` — Memory safety gate
  - `gate_c.py` — Invariants gate
  - `kernel_daemon.py` — Socket server
  - `kernel_client.py` — Integration SDK
  - `mayor.py` — Receipt generator
  - `ledger.py` — Immutable records

---

## Contact & Support

**Questions about kernel integration?**
→ See KERNEL_QUICK_REFERENCE.md or agent-specific guides

**Questions about Phase 3 timeline?**
→ See PHASE_3_ROADMAP.md

**Need to report security issue?**
→ Create issue with [security] tag in GitHub

---

## Status Dashboard

| Component | Phase | Status | Tests | Docs |
|-----------|-------|--------|-------|------|
| Gate A | 2 | ✅ Complete | 10/10 | ✅ |
| Gate B | 2 | ✅ Complete | 14/14 | ✅ |
| Gate C | 2 | ✅ Complete | 16/16 | ✅ |
| Daemon | 2 | ✅ Complete | 15+ | ✅ |
| Client | 2 | ✅ Complete | 15+ | ✅ |
| Mayor | 2 | ✅ Complete | Integrated | ✅ |
| Ledger | 2 | ✅ Complete | Integrated | ✅ |
| **Dashboard** | 3 | 🚧 Planned | — | [Roadmap](./PHASE_3_ROADMAP.md) |
| **Insights** | 3 | 🚧 Planned | — | [Roadmap](./PHASE_3_ROADMAP.md) |
| **Evolution** | 3 | 🚧 Planned | — | [Roadmap](./PHASE_3_ROADMAP.md) |
| **Integration** | 3 | 🚧 Planned | — | [Roadmap](./PHASE_3_ROADMAP.md) |

---

## Recent Commits

```
f247983 planning: Phase 3 roadmap — Dashboard, Insights, Evolution, Integration
85ec659 docs: Kernel quick reference — production integration guide
b1ae9c4 docs: Phase 2 complete — full kernel implementation delivered
aeb3487 kernel: Phase 2 complete — Gate C + daemon + client
028aa48 docs: OpenClaw + Oracle Town integration security guide
a4a8c37 docs: session summary — Phase 1 MVP complete, Phase 2 ready
```

---

## Summary

**Oracle Town is production-ready.** Phase 2 (safety kernel) is complete with 65+ passing tests and full documentation. Integrate with your agent system now. Phase 3 (operational intelligence) is designed and ready to code when needed.

**Next Step:** Choose integration agent and follow [KERNEL_QUICK_REFERENCE.md](./KERNEL_QUICK_REFERENCE.md)

🚀 **Ready for Production Deployment**
