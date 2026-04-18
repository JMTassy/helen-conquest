# Oracle Town Memory Integration Guide

How to wire the self-observing memory system into governance decisions.

## Quick Integration Examples

### Example 1: Mayor Checking Quorum Strategy

```python
# In oracle_town/core/mayor_rsm.py or your mayor logic

from oracle_town.memory.tools import MemoryLookup

def mayor_decide(briefcase, policy, ledger):
    """
    Make a SHIP/NO_SHIP decision.
    Reference memory for advisory context.
    """
    lookup = MemoryLookup()
    advisory = lookup.get_advisory_context()

    # Parse heuristics to understand what quorum strategy worked
    heuristics = advisory["heuristics"]

    # Example: Check if K3 (quorum-by-class) has been effective
    if "Quorum-by-class with N=2" in heuristics or \
       any(fact["fact"].startswith("Quorum-by-class") for fact in advisory["recent_decisions"]):
        # Advisory: quorum-by-class has worked in past
        # But still apply K3 logic deterministically
        pass

    # Apply policy deterministically (memory never overrides)
    if policy.apply_quorum_rule(ledger.attestations):
        return "SHIP"
    else:
        return "NO_SHIP"
```

### Example 2: Supervisor Detecting Authority Language (K0-L1)

```python
# In oracle_town/core/intake_guard.py

from oracle_town.memory.tools import MemoryLookup

def validate_proposal(proposal_text):
    """
    Validate proposal before sending to districts.
    Use memory to understand recent K-violations.
    """
    lookup = MemoryLookup()
    violations = lookup.get_invariant_violations()

    # If we've seen K0 (authority) violations recently, be extra strict
    k0_violations = [v for v in violations if "K0" in v.get("fact", "")]
    if k0_violations:
        print(f"Advisory: K0 violations detected recently. Extra strict K0-L1 scan.")
        # Apply K0-L1 scanner with higher sensitivity

    # Validate proposal (this is mandatory, not advisory)
    if contains_authority_language(proposal_text):
        return False  # Reject
    else:
        return True  # Accept
```

### Example 3: Orchestrator Choosing Lane Configuration

```python
# In oracle_town/core/orchestrator.py

from oracle_town.memory.tools import MemoryLookup

def orchestrate_cycle(claim, policy):
    """
    Run a governance cycle.
    Use memory to inform lane selection (advisory only).
    """
    lookup = MemoryLookup()
    lane_perf = lookup.get_lane_performance()
    emergence = lookup.get_emergence_signals()

    # Check if convergence was detected recently
    recent_convergence = [e for e in emergence if "convergence" in e.get("fact", "").lower()]

    if recent_convergence:
        print("Advisory: Convergence detected recently. Enabling Creativity lane.")
        # Enable Creativity lane (advisory, affects LLM context only)
        lanes_enabled = ["stability", "velocity", "democracy", "evidence", "creativity", "integrity", "learning"]
    else:
        print("Advisory: No recent convergence. Standard lane config.")
        lanes_enabled = ["stability", "velocity", "democracy", "evidence", "creativity", "integrity", "learning"]

    # Run districts (mandatory process)
    for district in self.districts:
        result = district.analyze(claim, policy)

    # Town hall (mandatory process)
    town_hall_result = self.town_hall.evaluate(claim, policy, district_results)

    # Mayor decides (deterministic, K-Invariant compliant)
    decision = self.mayor.decide(town_hall_result, policy)

    # Log decision for next memory cycle
    return decision
```

### Example 4: Day 2+ Mayor Using Learned Heuristics

```python
# In a future Day 2+ scenario

from oracle_town.memory.tools import MemoryLookup

def day_2_mayor_decide(briefcase, policy, ledger):
    """
    Day 2 mayor can access memory from Day 1.
    Use heuristics to inform (not determine) decisions.
    """
    lookup = MemoryLookup()
    rules = lookup.get_rules_of_thumb()
    heuristics = lookup.get_heuristics()

    # Example: Check if proposal count suggests certain quorum
    proposal_count = len(briefcase.proposals)

    # Advisory: use rules_of_thumb to guide decision
    # "IF proposal_count > 5: USE quorum_by_class N=3"
    if proposal_count > 5:
        suggested_quorum = 3
        print(f"Advisory from heuristics: Use quorum N={suggested_quorum} for {proposal_count} proposals")
    else:
        suggested_quorum = 2
        print(f"Advisory from heuristics: Use quorum N={suggested_quorum} for {proposal_count} proposals")

    # But apply policy deterministically (never use suggestion as override)
    if policy.apply_quorum_rule(ledger.attestations, quorum=policy.default_quorum):
        return "SHIP"
    else:
        return "NO_SHIP"
```

### Example 5: CT_COMBINER Using Convergence Signals

```python
# In LATERAL_THINKER_OFFICE integration

from oracle_town.memory.tools import MemoryLookup

def ct_combiner_decide(primary_proposal, lateral_suggestions, intern_ideas):
    """
    Decide whether to incorporate lateral/intern ideas into final proposal.
    Use memory to detect convergence patterns.
    """
    lookup = MemoryLookup()
    emergence = lookup.get_emergence_signals()

    # Check if convergence was detected
    convergence_detected = any("convergence" in e.get("fact", "").lower() for e in emergence)

    if convergence_detected:
        # Advisory: proposals are converging, maybe explore lateral alternatives
        print("Advisory: Convergence detected. Consider lateral ideas.")
        # Heuristic: if proposals converging, maybe stay with primary
        # OR if all proposals same, definitely use primary
        if all_proposals_same(primary_proposal, lateral_suggestions):
            return primary_proposal  # No diversity to explore
        else:
            # Diversity exists, maybe add one lateral suggestion
            return incorporate_one_lateral(primary_proposal, lateral_suggestions)
    else:
        # No convergence: use primary proposal as-is
        return primary_proposal
```

---

## Integration Points

### Where to Add Memory Lookups

| Component | Location | What to Check | Why |
|-----------|----------|---------------|-----|
| Intake Guard | `oracle_town/core/intake_guard.py` | Recent K-violations | Detect patterns of attacks |
| Supervisor | `oracle_town/core/supervisor.py` | Authority language violations | Inform K0-L1 strictness |
| Town Hall | `oracle_town/core/town_hall.py` | Lane performance | Select effective lanes |
| Orchestrator | `oracle_town/core/orchestrator.py` | Emergence signals | Detect convergence/divergence |
| Mayor RSM | `oracle_town/core/mayor_rsm.py` | Decision history | Log for synthesis |
| CT_Combiner | `oracle_town/runner/innerloop.py` | Convergence patterns | Decide idea incorporation |

### Code Pattern

```python
# Standard pattern for safe memory integration

from oracle_town.memory.tools import MemoryLookup

def my_function(inputs):
    # 1. Get memory lookup
    lookup = MemoryLookup()

    # 2. Fetch advisory data (never mandatory)
    advisory_heuristics = lookup.get_heuristics()

    # 3. Use advisory to INFORM logic (optional)
    if "pattern_X_succeeded" in advisory_heuristics:
        print(f"Advisory: Pattern X has worked. Considering...")

    # 4. Apply MANDATORY logic (K-Invariants, policy, etc.)
    if policy.check_mandatory_rule(inputs):
        return RESULT_A
    else:
        return RESULT_B

    # NOTE: Memory never overrides MANDATORY logic
```

---

## Memory Safety in Integration

### ✅ SAFE Ways to Use Memory

```python
# Check heuristics for context
if "Fast-track failed" in heuristics:
    print("Advisory: Fast-track has high failure rate.")
    # But you can still choose fast-track

# Reference recent decisions
recent = lookup.get_decision_history()
print(f"Last 5 decisions: {[d['decision'] for d in recent]}")

# Check lane performance
lanes = lookup.get_lane_performance()
print(f"Most active lanes: {list(lanes.keys())}")

# Monitor emergence signals
signals = lookup.get_emergence_signals()
convergence_detected = any("convergence" in s.get("fact", "") for s in signals)
```

### ⛔ FORBIDDEN Ways to Use Memory

```python
# DO NOT: Use memory to approve NO_SHIP unilaterally
if memory_says_ok:
    return "SHIP"  # FORBIDDEN — memory is advisory only

# DO NOT: Assume memory is complete
if "not in memory" implies "never happened":  # WRONG
    skip_check()  # FORBIDDEN

# DO NOT: Use confidence scores as tiebreakers
if memory_fact.confidence > 0.8:
    approve()  # FORBIDDEN — confidence is informational

# DO NOT: Override K-Invariants based on memory
if memory_says_quorum_not_needed:
    skip_k3_check()  # FORBIDDEN — K3 always applies
```

---

## Example: Full Cycle with Memory Integration

Here's a complete example showing memory integration in a governance cycle:

```python
from oracle_town.core.orchestrator import Orchestrator
from oracle_town.memory.tools import MemoryLookup

class MemoryAwareOrchestrator(Orchestrator):
    """Orchestrator that uses memory for advisory context."""

    def run_cycle(self, claim, policy):
        # Get memory before cycle starts
        lookup = MemoryLookup()
        context = lookup.get_advisory_context()

        print("=" * 60)
        print(f"CYCLE STARTING")
        print(f"Advisory: Recent decisions show {len(context['recent_decisions'])} outcomes")
        print(f"Advisory: {len(context['invariant_violations'])} K-violations detected")
        print("=" * 60)

        # Run intake guard (with advisory context available)
        intake_result = self.intake_guard.validate(claim)
        if not intake_result.valid:
            print(f"Rejected: {intake_result.reason}")
            return {"decision": "NO_SHIP", "reason": intake_result.reason}

        # Run districts (with memory context available to LLMs)
        print("\nRunning districts (with memory context)...")
        district_results = self.run_districts(claim, policy, advisory_context=context)

        # Run town hall
        print("\nTown hall evaluation...")
        town_hall_result = self.town_hall.evaluate(claim, policy, district_results)

        # Mayor decides (deterministically, K-Invariants always apply)
        print("\nMayor deciding...")
        decision = self.mayor.decide(briefcase=town_hall_result.briefcase,
                                     policy=policy,
                                     ledger=town_hall_result.ledger)

        # Log decision for memory
        print(f"\nDecision: {decision}")

        # Trigger extraction (optional, normally runs on cron)
        # extract_facts(cycle_num=self.cycle_count, decision=decision)

        return {"decision": decision}

# Usage
orchestrator = MemoryAwareOrchestrator()
result = orchestrator.run_cycle(claim, policy)
```

---

## Monitoring and Debugging

### Check Memory State

```bash
# See what facts were extracted
python3 oracle_town/memory/tools/memory_lookup.py --demo

# Check extraction logs
tail -f oracle_town/memory/meta/extraction.log

# Check synthesis logs
tail -f oracle_town/memory/meta/synthesis.log

# Inspect raw facts
cat oracle_town/memory/entities/decisions/*/items.json | jq .
```

### Test Memory in Python

```python
from oracle_town.memory.tools import MemoryLookup

lookup = MemoryLookup()

# Get everything
context = lookup.get_advisory_context()
print(json.dumps(context, indent=2, default=str))

# Get specific slices
heuristics = lookup.get_heuristics()
rules = lookup.get_rules_of_thumb()
recent_decisions = lookup.get_decision_history(limit=10)
violations = lookup.get_invariant_violations()

print("Recent decisions:")
for d in recent_decisions:
    print(f"  - {d['fact']}")
```

---

## Cost Considerations

Adding memory lookups to governance:

| Operation | Cost | When to Use |
|-----------|------|------------|
| `get_heuristics()` | Free (file read) | Advisor prompt context |
| `get_rules_of_thumb()` | Free (file read) | Decision guidance |
| `get_decision_history()` | Free (file read) | Pattern analysis |
| `get_advisory_context()` | Free (all file reads) | Comprehensive context |

**No LLM calls** — memory lookups are pure file I/O, so they're essentially free.

---

## Best Practices

1. **Always fetch advisory BEFORE mandatory checks**
   ```python
   context = lookup.get_advisory_context()  # Advisory
   if policy.check(briefcase):  # Mandatory
       return SHIP
   ```

2. **Never assume memory is complete**
   ```python
   # WRONG:
   if not in_memory(claim):
       skip_security_check()  # FORBIDDEN

   # RIGHT:
   if claim in memory:
       print("Advisory: seen similar before")
   # Always check regardless
   validate_claim(claim)
   ```

3. **Log ALL decisions for next synthesis**
   ```python
   decision = mayor.decide(...)
   log_for_memory(decision)  # So memory can learn
   return decision
   ```

4. **Memory informs, never determines**
   ```python
   # WRONG:
   if memory.says.ok:
       return SHIP  # Forbidden

   # RIGHT:
   if memory.says.ok:
       print("Advisory: pattern suggests OK")
   return policy.decide(briefcase)  # Policy decides
   ```

---

## Troubleshooting Integration

### Memory lookup returns empty

Check if facts were extracted:
```bash
python3 oracle_town/memory/tools/cycle_observer.py --scan-runs
ls -la oracle_town/memory/entities/*/*/items.json
```

### Memory affects decisions (should not)

Check if memory override is happening:
```python
# AUDIT: Are we using memory to override K-Invariants?
grep -r "memory\." oracle_town/core/mayor_rsm.py
# Should find only READS, not decision logic changes
```

### Memory growing too large

This is normal. Files are text-based:
- `items.json` appends only (never rewrites)
- `summary.md` regenerated weekly (replaces old)
- Check disk usage: `du -sh oracle_town/memory/`

---

## References

- **Memory system README:** `oracle_town/memory/README.md`
- **Memory setup guide:** `oracle_town/memory/SETUP.md`
- **Memory lookup API:** `oracle_town/memory/tools/memory_lookup.py`
- **K-Invariants:** `oracle_town/core/mayor_rsm.py`

---

## Next: Wire Up Your Components

Choose one component to integrate first:
1. **Intake Guard** — Check recent K-violations
2. **Town Hall** — Select lanes based on performance
3. **Mayor** — Log decisions for synthesis
4. **CT_Combiner** — Detect convergence patterns

Then test with:
```bash
python3 oracle_town/memory/tools/memory_lookup.py --demo
```

Ready to integrate? Pick a component and start coding!
