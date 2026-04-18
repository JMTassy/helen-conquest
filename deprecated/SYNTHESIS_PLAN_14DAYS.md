# ORACLE TOWN v1 — 14-Day Synthesis Plan

**Objective:** Unify mathematical foundations, governance kernel, swarm intelligence, consensus protocols, and game layer into a single, deterministic, production-grade system.

**Timeline:** Days 1–14 (autonomous execution)

---

## Phase 1: Kernel Hardening (Days 1–3)

### Goal
Finalize the deterministic governance kernel with full Merkle event root infrastructure and replay capability.

### Deliverables

**Day 1: DFA Validator & Canonical Schemas**
- [ ] Define canonical JSON schemas for: Event, Claim, Verdict, Amendment
- [ ] Implement strict validation rules (no optional fields, deterministic ordering)
- [ ] Build event enum (ALLOW, PREVENT, INITIATE, TERMINATE)
- [ ] Write 10+ validation tests

**Day 2: Merkle Root Infrastructure**
- [ ] Implement Merkle tree hashing for all events in an epoch
- [ ] Add `pre_root` and `post_root` to each ledger entry
- [ ] Build deterministic epoch boundary detection
- [ ] Test: same events → same root (K5 determinism)

**Day 3: Deterministic Replay Suite**
- [ ] Build complete replay engine: genesis → current state
- [ ] Compare replayed state to stored state (must match byte-for-byte)
- [ ] Add performance benchmark (must replay 1000 events in <1 sec)
- [ ] Document test vectors for CI

**Output:** `oracle_kernel_v1.py` (single binary, deterministic, testable)

---

## Phase 2: Internal Swarm (Days 4–6)

### Goal
Transform single-decision-maker ORACLE into a micro-polity with 3 competing internal agents.

### Design

**Agent Interface:**
```python
class Agent:
    def propose(state: WorldState) -> Proposal
    def critique(proposal: Proposal) -> Verdict
```

**Agents:**
1. **WardenAgent** — Risk-averse, rejects proposals with high uncertainty
2. **StewardAgent** — Action-biased, favors expansion and growth
3. **ArchivistAgent** — Consistency-biased, rejects contradictions with past

### Execution

**Day 4: Agent Protocol**
- [ ] Define `Proposal` and `Verdict` types
- [ ] Implement agent trait/interface
- [ ] Write base implementation for each agent

**Day 5: Debate Cycle**
- [ ] Route all proposals through: **Warden → Steward → Archivist**
- [ ] Each agent votes (accept/reject/modify)
- [ ] Governor (external function) breaks ties deterministically
- [ ] Log full debate trace to ledger

**Day 6: Emergence Testing**
- [ ] Run 50-round simulation with random proposals
- [ ] Measure: decision quality improvement vs. single agent
- [ ] Check: do conflicting agents produce better outcomes?
- [ ] Document emergent patterns

**Output:** `oracle_swarm_v1.py` (single ORACLE with 3 agents, deterministic debate)

---

## Phase 3: Federation Layer (Days 7–9)

### Goal
Enable 3 independent ORACLE instances to coordinate without central authority.

### Protocol

**Gossip Model:**
- Each town maintains local ledger
- Periodically broadcasts receipts to peers
- Validation: does peer agree on the same decision?
- Disagreement → explicitly logged as contested claim

### Execution

**Day 7: Gossip Protocol**
- [ ] Implement request/response over TCP (deterministic ordering)
- [ ] Define message format: `{ ledger_epoch, claim_id, receipt_hash }`
- [ ] Add peer registry (fixed 3 nodes)

**Day 8: Cross-Validation**
- [ ] When receiving peer receipt: re-validate against local gates
- [ ] If match: append to local ledger with peer_validated flag
- [ ] If mismatch: create contested entry (reason logged)
- [ ] Count agreement rate per epoch

**Day 9: Consensus Report**
- [ ] Compute: voting matrix (who agrees with whom)
- [ ] Generate: consensus report showing agreement clusters
- [ ] Detect: Byzantine behavior (if any)
- [ ] Output: deterministic consensus file per epoch

**Output:** `oracle_federation_sim_v1.py` (3 ORACLE instances, gossip protocol)

---

## Phase 4: Game Integration (Days 10–12)

### Goal
Remove all hidden state from CONQUESTmon-Gotchi. Make all game logic derive from governance ledger.

### Mapping

| Game State | Governance Correlate | Event Type |
|---|---|---|
| Territory | Resource claim & approval | ALLOW/PREVENT |
| Stability | Governance health score | VERDICT rating |
| Entropy | Conflict density | INITIATE count |
| Cohesion | Agreement rate | acceptance_percentage |
| Knowledge | Validated claims count | ALLOW count |

### Execution

**Day 10: Event Emission**
- [ ] Modify CONQUESTmon-Gotchi to emit events on each action
- [ ] EXPAND → emit RESOURCE_CLAIM event
- [ ] FORTIFY → emit INFRASTRUCTURE_AMENDMENT
- [ ] Each event routed through governance kernel

**Day 11: State Derivation**
- [ ] Remove all hidden game state
- [ ] Derive all game metrics from ledger replay:
  - Territory = count of ALLOW'd territory claims
  - Stability = average VERDICT quality (5 rounds)
  - Entropy = count of conflicting claims
  - Cohesion = accepted / total proposals ratio
  - Knowledge = count of ALLOW'd knowledge claims

**Day 12: Ledger-Only Rendering**
- [ ] Game reads: ledger only
- [ ] Game renders: visual state from derived metrics only
- [ ] Test: replay ledger → identical game state
- [ ] Verify: no divergence between replay and live play

**Output:** `conquest_governance_v1.py` (CONQUEST fully integrated with ledger)

---

## Phase 5: Consolidation (Days 13–14)

### Goal
Package, document, test, and deliver production-ready system.

### Day 13: Integration Testing

- [ ] Run full 5-layer stack: kernel → swarm → federation → game → ledger
- [ ] Test: 10-round game with 3 towns gossiping
- [ ] Measure: determinism (same seed → identical outcome)
- [ ] Check: all state derivable from ledger
- [ ] Benchmark: performance (should handle 1000 events/sec)

### Day 14: Documentation & Delivery

**Deliverables:**

1. **Architecture Diagram** — All 5 layers with data flow
2. **Formal Invariants** — K1–K24 enforced at each layer
3. **Threat Model** — Federation attack scenarios + mitigations
4. **Demo Scripts:**
   - `demo_single_town.py` — Single ORACLE with swarm
   - `demo_federation.py` — 3 towns consensus
   - `demo_conquest_integration.py` — Game + governance

5. **Test Suite** — 50+ tests covering:
   - Determinism (K5)
   - Ledger immutability (K22)
   - Replay fidelity
   - Agent emergence
   - Federation consensus

6. **Operations Manual** — How to deploy and run all components

---

## Invariant Enforcement Map

| Layer | Critical Invariants | Test |
|---|---|---|
| **Kernel** | K5 (determinism), K22 (append-only), K21 (policy immutability) | Replay suite, byte-for-byte comparison |
| **Swarm** | Agents deterministic, votes logged, tie-breaking consistent | Same proposal → same verdict |
| **Federation** | Gossip ordering deterministic, validation consistent | Peer disagreement logged |
| **Game** | State only from ledger, no hidden vars | Replay ledger → identical state |
| **Ledger** | All events immutable, hashes correct, chain integrity | Merkle root matches |

---

## Success Criteria

✅ **Phase 1:** Single kernel boots, processes claim → receipt, replays identically
✅ **Phase 2:** 3 agents debate; conflict improves decision quality
✅ **Phase 3:** 3 towns agree on 80%+ of decisions; disagreements logged
✅ **Phase 4:** Game state fully derives from ledger; no hidden state
✅ **Phase 5:** Full stack runs 50+ rounds deterministically; all tests pass

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Swarm becomes nondeterministic | All agents seeded from root; tie-breaking deterministic |
| Federation consensus stalls | Majority (2/3) consensus; disagreement is valid outcome |
| Game-ledger divergence | Continuous state validation; failing test halts sync |
| Performance degradation | Benchmark each layer; optimize hot paths |

---

## File Structure (Output)

```
oracle_town/
├── kernel/
│   ├── oracle_kernel_v1.py       (Phase 1)
│   ├── test_kernel_determinism.py
│   └── schemas.json
├── swarm/
│   ├── oracle_swarm_v1.py        (Phase 2)
│   ├── agents/
│   │   ├── warden_agent.py
│   │   ├── steward_agent.py
│   │   └── archivist_agent.py
│   └── test_swarm_emergence.py
├── federation/
│   ├── oracle_federation_sim_v1.py (Phase 3)
│   ├── gossip_protocol.py
│   └── test_consensus.py
├── game/
│   ├── conquest_governance_v1.py  (Phase 4)
│   └── test_ledger_derivation.py
└── demos/
    ├── demo_single_town.py        (Phase 5)
    ├── demo_federation.py
    └── demo_conquest_integration.py
```

---

## Status Tracking

- [x] Plan created
- [ ] Phase 1: Kernel hardening
- [ ] Phase 2: Internal swarm
- [ ] Phase 3: Federation
- [ ] Phase 4: Game integration
- [ ] Phase 5: Consolidation
- [ ] **DELIVERY:** Autonomous execution complete

---

**Start Date:** 2026-02-17
**Target Completion:** 2026-03-02
**Execution Model:** Autonomous (no daily check-ins required)
