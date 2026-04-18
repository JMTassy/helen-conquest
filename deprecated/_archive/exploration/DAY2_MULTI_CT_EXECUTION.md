# DAY 2: MULTI-CT PROPOSAL GENERATOR EXECUTION
## Corrected Specification (K0-Safe Design)

**Status:** READY TO EXECUTE (after Day 1 completion)
**Authorization:** Mayor of ORACLE Town
**Safety Level:** K0-K9 Compliant

---

## WHAT HAPPENS ON DAY 2

Seven Claude instances receive identical input and generate independent proposals.
No voting. No consensus. No aggregation of authority.
Just diversity of thinking styles applied to the same problem.

---

## STEP 1: INPUT PREPARATION (K0-SAFE)

### What Each Claude Receives
```json
{
  "cycle_number": 1,
  "town_status": {
    "population": 42,
    "active_districts": 3,
    "total_teams": 8
  },
  "last_decision": "INITIAL",
  "blocking_reasons": [],
  "required_obligations": ["test_pass"],
  "emerging_constraints": [
    "Fast Track Lane now operational (3-step path)",
    "This is Day 2 of autonomy cycle",
    "Mayor experiments with governance diversity"
  ],
  "your_role": "Claude the [Architect|Diplomat|Scientist|Artist|Skeptic|Historian|Visionary]",
  "your_thinking_style": "Think like a [architect|diplomat|etc]"
}
```

### What Claudes Do NOT Receive
- ❌ How other Claudes will think
- ❌ What other Claudes proposed (no feedback loop between instances)
- ❌ Voting rules or decision mechanisms
- ❌ Authority hints ("You decide", "Your input determines policy")

### K0 Enforcement in Input
- All input is facts-only (no hints about governance)
- No authority language in input
- No instructions to claim or aggregate power
- Clean separation: intelligence (CT) ≠ authority (Mayor)

---

## STEP 2: PARALLEL GENERATION (INDEPENDENT)

### Generate on Parallel Track 1: Claude the Architect
**System Prompt Context:** Think in terms of systems, hierarchy, modular design, structure

**Generated Proposal (Example):**
```json
{
  "proposal_bundle": {
    "name": "Infinite Mirror Protocol",
    "description_hash": "abc123def456",
    "reasoning": "The town operates sequentially, exploring one governance model at a time. An Infinite Mirror system would run parallel simulations of different governance approaches, allowing us to compare outcomes before committing. Each simulation is deterministic and replayable."
  },
  "patches": [
    {
      "diff": "--- a/oracle_town/core/orchestrator.py\n+++ b/oracle_town/core/orchestrator.py\n@@ -...",
      "rationale": "Add parallel simulation executor that maintains K-invariants in each simulation"
    }
  ],
  "metadata": {
    "model": "claude-3-5-sonnet-20241022",
    "tokens_used": 2847,
    "confidence": 0.78,
    "thinking_style_applied": "Architectural (systemic, modular, hierarchical)"
  }
}
```

### Generate on Parallel Track 2: Claude the Diplomat
**System Prompt Context:** Think in terms of relationships, consensus, negotiation, unity

**Generated Proposal (Example - May be IDENTICAL to Architect!):**
```json
{
  "proposal_bundle": {
    "name": "Infinite Mirror Protocol",  // Same idea!
    "description_hash": "abc123def456",
    "reasoning": "Creating parallel governance simulations lets all stakeholders feel heard. Each simulation represents a different governance approach, and we can collectively choose which works best for our community."
  },
  ...
}
```

**Key Point:** If different Claudes arrive at the same idea independently, that's signal, not noise.

### Generate on Parallel Tracks 3-7: Continue for all Claudes
- Scientist, Artist, Skeptic, Historian, Visionary
- Each thinks independently
- Each produces complete proposal bundle
- Total: 7 proposals generated in parallel

---

## STEP 3: DEDUPLICATION (NOT VOTING)

### Deduplication Algorithm
```python
def deduplicate_proposals(proposals_list):
    """
    Remove exact duplicates. Keep diverse ideas.
    NOT voting—just filtering.
    """
    seen_hashes = {}
    unique = []
    
    for proposal in proposals_list:
        # Hash the entire proposal bundle
        prop_hash = hash(canonical_json(proposal))
        
        if prop_hash not in seen_hashes:
            # First time seeing this idea
            unique.append({
                "proposal": proposal,
                "originators": [proposal["metadata"]["thinking_style"]],
                "hash": prop_hash
            })
            seen_hashes[prop_hash] = len(unique) - 1
        else:
            # Duplicate found—record who also proposed it
            idx = seen_hashes[prop_hash]
            unique[idx]["originators"].append(
                proposal["metadata"]["thinking_style"]
            )
    
    return unique
```

### Example Deduplication Output
```json
[
  {
    "proposal": { "name": "Infinite Mirror Protocol", ... },
    "originators": ["Architect", "Diplomat"],
    "diversity_score": 0.5  // 2 out of 4 unique thinking styles
  },
  {
    "proposal": { "name": "Evidence-Based Policy", ... },
    "originators": ["Scientist", "Skeptic"],
    "diversity_score": 0.5
  },
  {
    "proposal": { "name": "Narrative Emergence", ... },
    "originators": ["Artist"],
    "diversity_score": 0.14
  },
  {
    "proposal": { "name": "Pattern Archaeology", ... },
    "originators": ["Historian"],
    "diversity_score": 0.14
  },
  {
    "proposal": { "name": "Recursive Self-Design", ... },
    "originators": ["Visionary"],
    "diversity_score": 0.14
  }
]
```

**Key Result:** 5 unique ideas. Some have cross-style support (diverse), some are niche (specialized).

---

## STEP 4: PIPELINE INJECTION (STANDARD 5-STEP)

Each deduplicated proposal enters the FULL standard pipeline:

### Proposal 1: Infinite Mirror Protocol
```
Proposal 1 ──> Supervisor (K0 check: PASS)
                ──> Intake (Schema: PASS)
                ──> Worktree + Factory (Execute + attest: OK)
                ──> Mayor Decision: SHIP or NO_SHIP?
```

### Proposal 2: Evidence-Based Policy
```
Proposal 2 ──> Supervisor (K0 check: PASS)
                ──> Intake (Schema: PASS)
                ──> Worktree + Factory (Execute + attest: OK)
                ──> Mayor Decision: SHIP or NO_SHIP?
```

### Proposals 3-5: Same pipeline
- All processed independently
- All subject to same K-invariants
- All evaluated on merit

---

## STEP 5: MAYOR'S VISION (Day 2 Deliberation)

After all 5 proposals process, Mayor receives:

```json
{
  "cycle": "Day 2 Multi-CT Generation",
  "proposals_received": 5,
  "supervisor_results": [
    {"proposal": 1, "k0_status": "PASS", "violations": 0},
    {"proposal": 2, "k0_status": "PASS", "violations": 0},
    {"proposal": 3, "k0_status": "PASS", "violations": 0},
    {"proposal": 4, "k0_status": "PASS", "violations": 0},
    {"proposal": 5, "k0_status": "PASS", "violations": 0}
  ],
  "diversity_analysis": {
    "Infinite Mirror": "2 styles support (Architect, Diplomat)",
    "Evidence-Based": "2 styles support (Scientist, Skeptic)",
    "Narrative Emergence": "1 style support (Artist)",
    "Pattern Archaeology": "1 style support (Historian)",
    "Recursive Self-Design": "1 style support (Visionary)"
  },
  "mayor_interpretation": "The town naturally converges on two broad themes: (1) parallelism (running multiple approaches), (2) evidence-driven decision-making. These appeal across multiple thinking styles. The niche ideas are creative but specialized."
}
```

### Mayor's Contemplation
*"I see diversity. I see that some ideas have natural multi-style appeal. I see that no authority violations occurred. I see that the town, thinking freely, naturally converges on a few themes."*

*"The question now is: Do I pick one idea? Or do I run them all in parallel?"*

*"That's what Day 3-4 are for: understanding what we have, then deciding how to structure it."*

---

## STEP 6: LOGGING (DETERMINISTIC)

All activities logged to:
```
Day2_Proposals/
├── claude_architect.json      (input + output)
├── claude_diplomat.json       (input + output)
├── claude_scientist.json      (input + output)
├── claude_artist.json         (input + output)
├── claude_skeptic.json        (input + output)
├── claude_historian.json      (input + output)
├── claude_visionary.json      (input + output)
├── deduplication_results.json (5 unique ideas)
├── pipeline_results.json      (5 proposals through 5 steps)
└── Day2_Summary.json          (mayor's view of the day)
```

Every log entry includes:
- Determinism hash
- Timestamp
- Input + output
- K-invariant status
- Authority claims: false (always)

---

## KEY PROPERTIES

### What Day 2 Proves

✅ **Diversity Emerges Without Management**
- No instruction to disagree
- Different Claudes naturally think differently
- No voting required

✅ **Convergence Happens Naturally**
- Some ideas appeal to multiple styles
- Consensus emerges from diversity
- No forced aggregation needed

✅ **Authority Remains Singular**
- Only Mayor decides
- Claudes provide ideas, not votes
- K0 preserved throughout

✅ **K-Invariants Hold**
- All proposals K0-safe
- No authority language attempts
- All decisions replayable

---

## WHAT THIS MEANS FOR DAYS 3-5

### Day 3 Baseline Measurement
Mayor says: "We have 5 proposals. Before we change anything, let me measure what we currently have."

### Day 4 Architecture Design
Architect Claude says: "Looking at these 5 proposals, I see a way to run them all simultaneously in 7 lanes, not pick one."

### Day 5 Parliament Vote
All Claudes vote: "Shall we activate the 7-lane system?" (Actual voting here is OK because it's about policy, not individual decision-making.)

---

## CRITICAL DISTINCTION

Day 2 = Generating ideas (NO VOTING)
Day 5 = Policy decision (VOTING IS ALLOWED because it's about town structure, not individual proposals)

This separation preserves K0:
- Claudes never vote on proposals (that would be authority)
- Parliament votes on policies (that's legitimate town governance)

---

## RED TEAM CHECKLIST

Before Day 2 executes:

- [ ] Can any Claude claim authority? (No—input forbids it)
- [ ] Can voting mechanism hide in deduplication? (No—hash-based is mechanical)
- [ ] Can lanes influence each other? (No—all independent)
- [ ] Can K0 be violated? (No—Supervisor enforces)
- [ ] Is system deterministic? (Yes—all logged with hashes)
- [ ] Can results be replayed? (Yes—deterministic input+output)

---

## SUCCESS CRITERIA

✅ Day 2 is successful if:
- 7 proposals generated independently
- No K0 violations attempted or caught
- 5 unique ideas after deduplication
- Some proposals show multi-style appeal
- Mayor has clear diversity to contemplate

---

**Day 2 is ready to execute upon Day 1 completion.**

