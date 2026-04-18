# OpenClaw ↔ Oracle Town Integration Specification

**Status:** Normative integration architecture  
**Date:** 2026-02-04  
**Scope:** Full absorption of OpenClaw patterns into Oracle Town governance

---

## Executive Summary

OpenClaw provides five operational patterns that Oracle Town can safely absorb as **NPCs** (non-authority agents) and **job infrastructure**, without compromising governance:

| OpenClaw Pattern | Oracle Town Equivalent | Authority | Role |
|---|---|---|---|
| Agents | NPCs | None | Proposers, observers |
| Memory System | Memory Linker | Managed | Read-only search, append-only ledger |
| Heartbeats | Schedulers | None | Trigger observations |
| Jobs/Cron | Job Registry | None | Task graph execution |
| Skills Execution | Street Claims | None | Propose actions (K15: needs receipt) |

**Key Constraint:** OpenClaw never executes without an Oracle Town receipt.

---

## 1. The Five OpenClaw Patterns (Mapped)

### Pattern 1: Agents (→ NPCs in Oracle Town)

**What OpenClaw Has:**
```
Agent = {role, memory, tools, autonomy}
```

**What Oracle Town Needs:**
```
NPC = {role, memory (read-only), claims (proposals), no authority}
```

**Integration Rule:**
- OpenClaw agents become NPCs
- They can *propose* claims
- They cannot *decide* claims
- Claim type: "agent_observation" or "agent_proposal"

**Example OpenClaw Agent:**
```python
class EmailAnalyzer(Agent):
    role = "email_processor"
    async def process(self, email):
        if score(email) > threshold:
            return Decision(action="flag", reason=...)
```

**Becomes Oracle Town NPC:**
```python
class EmailAnalyzerNPC:
    role = "email_processor"
    def observe(self, email):
        claim = {
            "type": "agent_observation",
            "role": self.role,
            "statement": f"Email flagged by {self.role}: {reason}",
            "confidence": score,
            "proposed_action": "flag"  # ← not a decision
        }
        return claim  # → goes to TRI gate for verdict
```

### Pattern 2: Memory System (→ Memory Linker)

**What OpenClaw Has:**
```
Memory = {facts, beliefs, entities, links}
Mutable = facts can be updated
Searchable = LLM-based semantic search
Persistent = across sessions
```

**What Oracle Town Needs:**
```
Memory Ledger = {observations, decisions, entities, links}
Read-Only = can search
Append-Only = can add
Linked = back to claims/receipts
```

**Integration Rule:**
- OpenClaw memory becomes Oracle Town's Memory Linker
- Reads are unrestricted
- Writes are append-only, linked to ledger entries
- Searches trigger via NPCs ("What do we know about vendor X?")

**Schema:**
```yaml
oracle_town/memory/
├── index.json              # canonical entity map
├── entities/
│   ├── person_*.json       # people, roles
│   ├── vendor_*.json       # vendors, suppliers
│   ├── project_*.json      # projects, initiatives
│   └── outcome_*.json      # results, learnings
├── relationships.jsonl     # edge list (append-only)
└── search.py               # semantic search (read-only)
```

### Pattern 3: Heartbeats (→ Schedulers + Observation Triggers)

**What OpenClaw Has:**
```
Heartbeat = {schedule, action, error_handler}
"Every 6 hours, check status endpoint"
```

**What Oracle Town Needs:**
```
Scheduler = {cron, observer_role, trigger, claim_type}
"Every 6 hours, OBS district generates observation claim"
```

**Integration Rule:**
- Heartbeat fires on schedule
- Calls an NPC observer (does not execute directly)
- Observer generates claim
- Claim goes through gates

**Example:**
```yaml
# OpenClaw heartbeat
heartbeats:
  - name: "check_vendor_status"
    interval: "6h"
    action: "fetch(https://vendor.api/status)"

# Becomes Oracle Town scheduler
schedulers:
  vendor_status_observer:
    interval: "6h"
    trigger: "OBS.vendor_check"
    claim_type: "observation"
    observer: "VendorStatusNPC"
    action: |
      data = fetch(url)  # fetch before submission
      return Claim(
        type="observation",
        statement=f"Vendor status: {data.status}",
        evidence=data
      )
```

### Pattern 4: Jobs / Cron (→ Job Registry + Deterministic Graph)

**What OpenClaw Has:**
```
Job = {name, inputs, outputs, error_handling}
Cron = {schedule, retry, dependencies}
```

**What Oracle Town Needs:**
```
JobSpec = {id, inputs, outputs, dependencies, determinism_flag}
Registry = {DAG, execution order, ledger entries}
```

**Integration Rule:**
- OpenClaw jobs become Oracle Town job specs
- Execution order is deterministic (topological sort + tie-breaker)
- Each job execution is logged with receipt requirement
- No job executes without (1) receipt or (2) being deterministic/safe

**Schema:**
```yaml
oracle_town/jobs/
├── registry.json           # job definitions + DAG
├── specs/
│   └── job_*.json         # individual job specs
├── log/
│   └── execution.jsonl    # every job run logged
└── runner.py              # deterministic executor
```

### Pattern 5: Skills Execution (→ Street Claims + K15)

**What OpenClaw Has:**
```
Skill = {code, inputs, outputs, error_handler}
Execute = run(skill, args) immediately
```

**What Oracle Town Needs:**
```
SkillClaim = {skill_id, inputs, intended_output, evidence}
K15 Enforcement = receipt required before execution
```

**Integration Rule:**
- OpenClaw wants to execute a skill
- First: submit as claim (with evidence if possible)
- Wait: get receipt from Oracle Town (ACCEPT/REJECT)
- Then: execute only if receipt says ACCEPT

**K15 Enforcement:**
```python
# OpenClaw wants to run a skill
skill_claim = SkillClaim(
    skill_id="email_send",
    inputs={"to": "user@example.com", "body": "..."},
    evidence="pre-checked against policy"
)

# Step 1: Submit to Oracle Town
receipt = submit_claim(skill_claim)

# Step 2: Check receipt (K15: no receipt = no execute)
if not receipt or receipt["decision"] != "ACCEPT":
    log(f"Skill execution blocked: {receipt}")
    return False

# Step 3: Only execute if receipt permits
execute_skill(skill)
return True
```

---

## 2. Integration Architecture (Clean Layering)

```
┌─────────────────────────────────────────────────┐
│         OpenClaw (World Actor)                  │
│  ├─ Agents (→ NPCs)                             │
│  ├─ Skills (→ Claims)                           │
│  └─ Memory (→ Linked Ledger)                    │
└──────────────────┬──────────────────────────────┘
                   │
         [submit_claim() + fetch_evidence()]
                   │
┌──────────────────▼──────────────────────────────┐
│    Oracle Town (Authority Layer)                │
│  ├─ Intake Validation (schema, lineage)         │
│  ├─ Doctrine Enforcer (class check)             │
│  ├─ TRI Gate (K0–K7, K15)                       │
│  ├─ Mayor (SHIP/NO_SHIP)                        │
│  └─ Ledger (immutable receipt)                  │
└──────────────────┬──────────────────────────────┘
                   │
         [return receipt with decision]
                   │
┌──────────────────▼──────────────────────────────┐
│     OpenClaw (Execution Layer)                  │
│  ├─ Check receipt (K15)                         │
│  ├─ If ACCEPT → execute                         │
│  ├─ If REJECT → abort silently                  │
│  └─ Log to audit trail                          │
└─────────────────────────────────────────────────┘
```

---

## 3. Five Concrete Integration Points

### Integration Point 1: NPC Agent Submission

**OpenClaw Agent → Oracle Town NPC**

File: `oracle_town/npc/agent_bridge.py`

```python
class OpenClawAgentBridge:
    """
    Wraps an OpenClaw Agent as an Oracle Town NPC.

    NPC can generate claims.
    NPC cannot make decisions.
    """

    def __init__(self, openclaw_agent):
        self.agent = openclaw_agent
        self.role = openclaw_agent.role
        self.memory = openclaw_agent.memory  # read-only binding

    def observe(self, stimulus):
        """
        Agent observes something → generates claim.
        Returns Claim, not Decision.
        """
        result = self.agent.process(stimulus)
        claim = ClaimBuilder.from_agent_result(
            agent_id=self.role,
            stimulus=stimulus,
            result=result,
            confidence=getattr(result, 'confidence', 0.5)
        )
        return claim  # → to TRI gate

    def read_memory(self, query):
        """
        Agent can read memory (no restrictions).
        """
        return self.agent.memory.search(query)
```

### Integration Point 2: Memory Linking

**OpenClaw Memory → Oracle Town Memory Ledger**

File: `oracle_town/memory/ledger_linker.py`

```python
class MemoryLedgerLinker:
    """
    OpenClaw memory facts become Oracle Town ledger entries.

    - All writes are append-only
    - All writes link to original claim/receipt
    - All reads are unrestricted
    """

    def link_fact(self, fact, source_receipt_id):
        """
        Add a fact to memory, linked to the receipt that created it.
        """
        entry = {
            "fact_id": f"mem_{uuid.uuid4()}",
            "fact": fact,
            "source_receipt": source_receipt_id,
            "timestamp": date.today().isoformat(),
            "type": "memory_fact"
        }
        self.ledger.append(entry)  # append-only
        return entry

    def search_facts(self, query):
        """
        Unrestricted semantic search over all facts.
        """
        return self.agent.memory.search(query)  # OpenClaw's search

    def get_fact_lineage(self, fact_id):
        """
        Trace a fact back to the receipt that created it.
        """
        return self.ledger.find_by_id(fact_id)
```

### Integration Point 3: Heartbeat as Observation Trigger

**OpenClaw Heartbeat → Oracle Town Scheduler**

File: `oracle_town/scheduler/heartbeat_supervisor.py`

```python
class HeartbeatSupervisor:
    """
    OpenClaw heartbeats become Oracle Town observation triggers.

    Each heartbeat fires an NPC observer, which generates a claim.
    """

    def register_heartbeat(self, hb: Heartbeat):
        """
        Convert OpenClaw heartbeat to Oracle Town scheduler entry.
        """
        scheduler_entry = {
            "id": f"hb_{hb.name}",
            "interval": hb.interval,
            "observer_role": f"OBS.{hb.name}",
            "trigger": self._make_trigger(hb),
            "claim_type": "observation"
        }
        return self.registry.add(scheduler_entry)

    def _make_trigger(self, hb: Heartbeat):
        """
        Convert heartbeat action to claim generation.
        """
        def trigger():
            # OpenClaw's action runs (e.g., fetch)
            result = hb.action()

            # But instead of acting, generate claim
            claim = Claim(
                type="observation",
                statement=f"{hb.name}: {result}",
                evidence=result,
                source_npc=hb.name
            )
            return claim  # → to TRI gate

        return trigger

    def run_loop(self):
        """
        Scheduler loop: check heartbeats, fire triggers, generate claims.
        """
        for entry in self.registry.entries():
            if entry.is_due():
                claim = entry.trigger()
                receipt = submit_claim(claim)
                self.log_claim(entry.id, claim, receipt)
```

### Integration Point 4: Job Registry (Deterministic Graph)

**OpenClaw Jobs → Oracle Town Job Registry**

File: `oracle_town/jobs/registry.py`

```python
class JobRegistry:
    """
    OpenClaw jobs become deterministic Oracle Town job specs.

    Execution order is fixed. No randomness. All logged.
    """

    def register_job(self, job: Job):
        """
        Add job to registry with dependencies resolved.
        """
        spec = {
            "id": job.id,
            "inputs": job.inputs,
            "outputs": job.outputs,
            "dependencies": job.depends_on or [],
            "deterministic": job.has_no_side_effects(),
            "claim_type": "job_execution"
        }
        self.registry.add(spec)

    def execute_dag(self):
        """
        Execute job DAG in deterministic order.
        """
        dag = TopologicalSort(self.registry.entries())

        for job_id in dag.order():  # stable order
            job = self.registry.get(job_id)

            # Submit as claim (not direct execution)
            claim = Claim(
                type="job_execution",
                statement=f"Execute job: {job_id}",
                evidence={"inputs": job.inputs},
                job_id=job_id
            )

            # Get receipt
            receipt = submit_claim(claim)

            # If deterministic and SHIP, execute
            if receipt["decision"] == "SHIP":
                result = job.execute()
                self.log_execution(job_id, result, receipt)
            else:
                self.log_execution(job_id, None, receipt)
```

### Integration Point 5: K15 Enforcement (No Receipt = No Execute)

**OpenClaw Execution → K15 Gate**

File: `oracle_town/gates/k15_enforcement.py`

```python
class K15Enforcer:
    """
    K15: No receipt = no execution.

    OpenClaw skills cannot run without an Oracle Town receipt.
    """

    def execute_skill(self, skill_claim: Claim):
        """
        (1) Submit claim
        (2) Get receipt
        (3) Only execute if receipt permits
        """
        # Step 1: Submit
        receipt = submit_claim(skill_claim)

        # Step 2: Enforce K15
        if not receipt:
            # Oracle Town offline → fail-closed
            log("K15: No receipt provided (Oracle Town offline)")
            return ExecutionBlocked("No receipt from Oracle Town")

        if receipt["decision"] != "SHIP":
            log(f"K15: Oracle Town rejected: {receipt['reason']}")
            return ExecutionBlocked(f"Authority decision: {receipt['decision']}")

        # Step 3: Execute only if receipt permits
        try:
            result = skill_claim.execute()
            audit_trail(skill_claim.id, receipt, result)
            return result
        except Exception as e:
            log(f"Skill execution failed: {e}")
            raise

    def audit_trail(self, skill_id, receipt, result):
        """
        Log every skill execution with its receipt.
        """
        entry = {
            "skill_id": skill_id,
            "receipt_id": receipt["id"],
            "decision": receipt["decision"],
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.execution_log.append(entry)
```

---

## 4. File Structure (What to Create)

```
oracle_town/
├── npc/
│   ├── __init__.py
│   ├── agent_bridge.py        # OpenClaw Agent → NPC
│   ├── registry.py            # NPC registry
│   └── claims.py              # NPC claim types
│
├── memory/
│   ├── ledger_linker.py       # Memory ↔ Ledger linking
│   ├── fact_store.jsonl       # append-only facts
│   └── search.py              # semantic search
│
├── scheduler/
│   ├── heartbeat_supervisor.py  # Heartbeat → Observation Trigger
│   ├── registry.yaml            # scheduled tasks
│   └── runner.py                # execution loop
│
├── jobs/
│   ├── registry.py            # Job DAG
│   ├── specs.json             # job definitions
│   └── execution.jsonl        # job execution log
│
├── gates/
│   ├── k15_enforcement.py     # K15: No receipt = no execute
│   └── skill_validator.py     # Pre-submission validation
│
└── integration/
    ├── openclaw_config.yaml   # OpenClaw → Oracle Town config
    └── test_integration.py    # test harness
```

---

## 5. Configuration File

**File:** `oracle_town/integration/openclaw_config.yaml`

```yaml
openclaw_integration:
  enabled: true

  agents:
    # Map OpenClaw agents to NPCs
    bridge_mode: "claim_generator"  # agents propose, don't decide
    observation_prefix: "OBS."

  memory:
    # Link OpenClaw memory to Oracle Town ledger
    enabled: true
    sync_interval: "1h"
    ledger_path: "oracle_town/memory/ledger.jsonl"
    fact_store: "oracle_town/memory/facts.jsonl"

  heartbeats:
    # Convert heartbeats to observation triggers
    enabled: true
    registry_file: "oracle_town/scheduler/registry.yaml"
    fail_closed: true  # if trigger fails, log but don't execute

  jobs:
    # Manage OpenClaw job execution
    enabled: true
    dag_file: "oracle_town/jobs/registry.json"
    execution_log: "oracle_town/jobs/execution.jsonl"
    determinism_check: true  # verify no side effects

  execution:
    # K15 enforcement
    require_receipt: true
    fail_closed: true
    audit_trail: "oracle_town/execution.jsonl"

  policy:
    version: "1.0"
    doctrine_hash: "sha256:..."
```

---

## 6. Testing Strategy

### Test 1: NPC Claims Generation

```bash
python3 -m oracle_town.npc.test_agent_bridge
# Output:
# ✓ OpenClaw agent wrapped as NPC
# ✓ NPC generates claim (not decision)
# ✓ Claim linked to agent role
```

### Test 2: Memory Ledger Linking

```bash
python3 -m oracle_town.memory.test_ledger_linker
# Output:
# ✓ Fact added to ledger
# ✓ Fact linked to source receipt
# ✓ Semantic search works over facts
```

### Test 3: Heartbeat → Observation

```bash
python3 -m oracle_town.scheduler.test_heartbeat_supervisor
# Output:
# ✓ Heartbeat converted to scheduler entry
# ✓ Trigger fires on schedule
# ✓ Claim generated
# ✓ Claim sent to TRI gate
```

### Test 4: Job DAG Execution

```bash
python3 -m oracle_town.jobs.test_registry
# Output:
# ✓ Jobs registered with dependencies
# ✓ DAG sorted deterministically
# ✓ Each job generates claim
# ✓ Execution logged
```

### Test 5: K15 Enforcement

```bash
python3 -m oracle_town.gates.test_k15_enforcement
# Output:
# ✓ Skill claim submitted
# ✓ Receipt checked before execution
# ✓ No receipt → execution blocked
# ✓ REJECT receipt → execution blocked
# ✓ ACCEPT receipt → execution allowed
```

---

## 7. Deployment Path

### Phase 1: Wire Integration Points (Week 1)

- [ ] Create NPC agent bridge
- [ ] Create memory ledger linker
- [ ] Create heartbeat supervisor

### Phase 2: Build Infrastructure (Week 2)

- [ ] Build job registry
- [ ] Implement K15 enforcer
- [ ] Create configuration system

### Phase 3: Test & Validate (Week 3)

- [ ] Run 5-test harness
- [ ] Test with dummy OpenClaw agents
- [ ] Verify determinism

### Phase 4: Deploy to Oracle Town (Week 4)

- [ ] Merge into main
- [ ] Update CLAUDE.md
- [ ] Document for users

---

## 8. Guarantees

✅ **OpenClaw retains autonomy** — Agents observe, propose, learn  
✅ **Oracle Town retains authority** — Only kernel decides  
✅ **No authority leakage** — K15 enforces receipt requirement  
✅ **Determinism maintained** — Job order fixed, decisions logged  
✅ **Auditability complete** — Every action traced to receipt  
✅ **Fail-closed by default** — Missing receipt = no execution

---

## 9. Next Immediate Actions

1. **Create NPC agent bridge** (`oracle_town/npc/agent_bridge.py`)
2. **Create memory ledger linker** (`oracle_town/memory/ledger_linker.py`)
3. **Create heartbeat supervisor** (`oracle_town/scheduler/heartbeat_supervisor.py`)
4. **Write integration test suite**
5. **Document for OpenClaw users**

---

**Status:** Ready to implement  
**Maintainer:** Oracle Town governance  
**Review:** Weekly until Phase 4 complete
