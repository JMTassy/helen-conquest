# MULTI-CT GATEWAY SPECIFICATION
## Parallel Creative Thinking Without Authority Aggregation

**Status:** LOCKED (Immutable after Day 2)
**Safety Level:** K0 Compliant
**Authority Claim:** ZERO (by design)

---

## THE PROBLEM THIS SOLVES

Initial autonomy narrative said: "7 Claudes vote, 4/7 wins"

**This is unconstitutional under K0.**

K0 = Authority Separation

Voting = Authority Aggregation

These are incompatible.

---

## WHAT WE ACTUALLY WANT

Multiple independent CT instances generate ideas in parallel.
All ideas feed into standard pipeline independently.
Mayor sees diversity of proposals, not a consensus.
Mayor makes decision from evidence, not from "what the Claudes agreed on."

This is not voting. This is a market of ideas.

---

## MULTI-CT GATEWAY ARCHITECTURE

### Component 1: Parallel CT Instances

```
ClaudeArchitect ──┐
ClaudeDiplomat ──┤
ClaudeScientist ─┤
ClaudeArtist ────┼──> Input: Last decision + blocking reasons
ClaudeSkeptic ───┤     Output: 7 independent proposal bundles
ClaudeHistorian ─┤     No communication between instances
ClaudeVisionary ─┘
```

Each Claude:
- Receives **identical input** (facts only, K0-safe)
- Generates **independent proposal bundle**
- Has **no awareness** of what other Claudes propose
- Cannot **vote**, **rank**, or **aggregate** with others

### Component 2: Input Contract (K0-Safe)

Each Claude receives:
```json
{
  "cycle_number": integer,
  "last_decision": "SHIP" or "NO_SHIP" or "INITIAL",
  "blocking_reasons": ["QUORUM_MISSING", ...],
  "required_obligations": ["test_pass", ...],
  "town_population": 42,
  "active_districts": 3,
  "time_since_last_ship": integer,
  "your_role": "Architect" or "Diplomat" or ...  // Helps guide thinking
}
```

### Component 3: Forbidden Information

Claudes do NOT receive:
- How other Claudes will think
- What other Claudes proposed (no feedback loop between instances)
- Voting rules or consensus mechanisms
- Authority hints (no "you decide", no "your input determines outcome")

### Component 4: Output Contract (Identical for all)

Each Claude produces:
```json
{
  "proposal_bundle": {
    "name": "string",
    "description_hash": "hex",
    "reasoning": "string"  // Their thought process
  },
  "patches": [
    {
      "diff": "unified diff",
      "rationale": "why this patch"
    }
  ],
  "metadata": {
    "model": "claude-3-5-sonnet-20241022",
    "tokens_used": integer,
    "confidence": 0.0-1.0,  // Not a vote, just self-assessment
    "thinking_style_applied": "Architect" or "Diplomat" or ...
  }
}
```

### Component 5: Deduplication (Not Voting)

After all 7 Claudes propose:

```python
def deduplicate_proposals(proposals):
    """
    Remove exact duplicates, keep diverse ideas.
    Not voting—just filtering.
    """
    seen_hashes = set()
    unique = []
    
    for prop in proposals:
        hash_val = hash(canonical_json(prop))
        if hash_val not in seen_hashes:
            unique.append(prop)
            seen_hashes.add(hash_val)
    
    return unique
```

If 7 Claudes propose identical ideas:
→ Keep 1 copy
→ All 7 fed into Supervisor independently
→ Mayor sees 1 proposal with 7 independent data points

This is **data aggregation**, not **authority aggregation**.

### Component 6: Pipeline Injection (Standard)

Each deduplicated proposal enters the standard 5-step pipeline:

```
Proposal 1 ──> Supervisor ──> Intake ──> Factory ──> Mayor
Proposal 2 ──> Supervisor ──> Intake ──> Factory ──> Mayor
Proposal 3 ──> Supervisor ──> Intake ──> Factory ──> Mayor
...
Proposal N ──> Supervisor ──> Intake ──> Factory ──> Mayor
```

All processed independently.
All subject to same K-invariants.
Mayor sees N distinct decision paths.

### Component 7: Mayor's View

After all Claudes propose and deduplicate:

```json
{
  "cycle": 42,
  "proposals_received": 5,  // Might be fewer than 7 after dedup
  "proposal_sources": {
    "Architect": "Proposal 1",
    "Diplomat": "Proposal 1",  // Same as Architect
    "Scientist": "Proposal 2",
    "Artist": "Proposal 3",
    "Skeptic": "Proposal 2",   // Same as Scientist
    "Historian": "Proposal 4",
    "Visionary": "Proposal 5"
  },
  "unique_proposals": [1, 2, 3, 4, 5],
  "thinking_diversity": {
    "proposal_1": ["ARCHITECTURAL", "DIPLOMATIC"],
    "proposal_2": ["SCIENTIFIC", "SKEPTICAL"],
    "proposal_3": ["ARTISTIC"],
    "proposal_4": ["HISTORICAL"],
    "proposal_5": ["VISIONARY"]
  },
  "diversity_score": 0.8  // How many distinct thinking styles support each?
}
```

**Mayor now knows:**
- Which proposals have thinking diversity (appealing across styles)
- Which proposals are niche (only one style supports them)
- Whether broad consensus naturally emerged or views are split

**Mayor does NOT:**
- Vote based on what Claudes agreed
- Weight decisions by number of Claudes
- Use "4/7 majority" as decision rule

---

## EXAMPLE SCENARIO

**Cycle 42 Multi-CT Execution:**

```
Input to all 7 Claudes:
{
  "last_decision": "NO_SHIP",
  "blocking_reasons": ["QUORUM_MISSING"],
  "cycle": 42
}

Architect proposes: "Infinite Mirror Protocol" (multi-threaded simulation)
Diplomat proposes: "Infinite Mirror Protocol" (same idea!)
Scientist proposes: "Evidence-Based Policy" (measurement-driven)
Artist proposes: "Narrative Emergence" (story hall)
Skeptic proposes: "Evidence-Based Policy" (same as Scientist)
Historian proposes: "Pattern Archaeology" (data analysis)
Visionary proposes: "Recursive Self-Design" (auto-evolution)

Deduplication produces 5 unique proposals
```

**What this reveals:**
- "Infinite Mirror" has natural support from 2 styles (ARCHITECTURAL + DIPLOMATIC)
- "Evidence-Based Policy" has support from 2 styles (SCIENTIFIC + SKEPTICAL)
- Other proposals are single-style ideas

**Mayor's decision:**
The Mayor might say: "Infinite Mirror and Evidence-Based Policy both have cross-style appeal. Let's run both as lanes. The others are creative but niche—hold them for later."

This is **data-informed decision**, not **vote aggregation**.

---

## WHAT THIS ENABLES

1. **Diversity Detection:** Which ideas appeal across thinking styles?
2. **Convergence Measurement:** Do free Claudes naturally agree or diverge?
3. **Cognitive Robustness:** Ideas that convince multiple thinking styles are more robust
4. **No Authority Leakage:** Claudes cannot vote, rank, or decide
5. **Transparency:** Mayor can see every Claude's independent thinking

---

## WHAT THIS FORBIDS

❌ "4 out of 7 Claudes vote YES" → Authority aggregation
❌ "Claudes debate and reach consensus" → Authority pooling
❌ "Most common idea becomes policy" → Democracy trap
❌ "Weighting proposals by Claude agreement" → Hidden voting

---

## IMPLEMENTATION CHECKLIST

- [ ] 7 Claude instances configured with different system prompts
- [ ] Input contract enforces K0-safe facts only
- [ ] Output contract identical across all instances
- [ ] Deduplication logic is deterministic and logged
- [ ] Pipeline accepts deduplicated proposals independently
- [ ] Diversity scoring is transparent (not a decision, just a metric)
- [ ] Mayor's pure function sees diversity but is not constrained by it
- [ ] All outputs are deterministic and replayable
- [ ] Red team tests: Can any Claude escape K0 requirements? (Answer: no)

---

## NAMING MATTERS

We are NOT calling this "Multi-Claude Parliament"
We ARE calling it "Multi-CT Proposal Generator"

Parliament = voting = authority aggregation = forbidden

Generator = ideas = diversity = allowed

---

**This is how you get diversity without voting.**

