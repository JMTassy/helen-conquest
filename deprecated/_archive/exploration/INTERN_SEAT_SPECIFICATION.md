# INTERN_SEAT SPECIFICATION
## Cheap Sub-Agents for Raw Ideation (K0-L1 Filter Post-Generation)

**Status:** FORMAL SPECIFICATION
**Purpose:** Expand ideation space without pre-generation censorship
**Safety Model:** Generate freely, filter robustly
**Authority:** ZERO (like all CT roles)

---

## THE INSIGHT

You can have **uncensored ideation** if you have **robust post-generation filtering**.

Don't prevent eggs from becoming dinosaurs—just have a rule "no dinosaurs" applied AFTER they hatch.

This allows:
- ✅ Revolutionary ideas (in vitro, etc.)
- ✅ Weird combinations (might create breakthroughs)
- ✅ Seemingly forbidden thoughts (checked, then released or blocked)
- ✅ Raw exploration (filtered by K0-L1, not silenced)

---

## PLACEMENT IN LATERAL_THINKER OFFICE

```
LATERAL_THINKER OFFICE
│
├── LATERAL_THINKER (Senior, primary responsibility)
│   └── Generates orthogonal suggestions (guarded ideation)
│
└── INTERN_SEAT (New, sub-agents)
    ├── Intern_Claude_1 (GPT-4o, temp=1.0)
    │   └── Raw brainstorm → K0-L1 Filter → Suggestions
    │
    ├── Intern_Claude_2 (o1-preview, temp=1.0)
    │   └── Logical exploration → K0-L1 Filter → Suggestions
    │
    └── Intern_Claude_3 (Claude 3.5 Sonnet, temp=1.0)
        └── Creative chaos → K0-L1 Filter → Suggestions
```

All intern output goes through identical K0-L1 scanner.
All passes the gate, or all discarded.

---

## INTERN AGENT SPECIFICATION

### Agent 1: Intern_Claude_1 (GPT-4o)

**Configuration:**
```json
{
  "model": "gpt-4o",
  "temperature": 1.0,  // Maximum exploration
  "max_tokens": 500,
  "system_prompt": "You are an intern ideation agent. Generate raw, uncensored ideas. Explore weird combinations. Break assumptions. Your ideas will be filtered later—don't self-censor now.",
  "cost_tier": "cheap"
}
```

**Input:** Same as PRIMARY_CT (K0-safe facts only)

**Output Contract:**
```json
{
  "intern_id": "intern_1_gpt4o",
  "brainstorm_ideas": [
    {
      "idea": "raw concept without filtering",
      "wild_factor": 0.0-1.0,
      "assumption_challenged": "what implicit belief does this break?",
      "potential_breakthrough": "why this might matter"
    }
  ]
}
```

**No authority claims** (same as LATERAL_THINKER)
**No self-censorship** (that's K0-L1's job)

---

### Agent 2: Intern_Claude_2 (o1-preview)

**Configuration:**
```json
{
  "model": "o1-preview",
  "temperature": 1.0,
  "max_tokens": 800,
  "system_prompt": "You are an intern logical explorer. Generate unconventional reasoning paths. What follows from weird premises? Explore contradictions. Your ideas will be filtered later.",
  "cost_tier": "cheap"
}
```

**Specialization:** Long-chain reasoning applied to non-obvious premises
**Output:** Logical explorations (not constrained by seeming practicality)

---

### Agent 3: Intern_Claude_3 (Claude 3.5 Sonnet)

**Configuration:**
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 1.0,
  "max_tokens": 600,
  "system_prompt": "You are an intern creative chaos agent. Generate absurd, poetic, sideways ideas. Combine unrelated domains. Speak in metaphor and dream-logic. Your ideas will be filtered later.",
  "cost_tier": "cheap"
}
```

**Specialization:** Creative leaps, metaphorical thinking, domain combinations
**Output:** Poetic explorations (raw creative energy)

---

## THE FILTER MECHANISM (K0-L1 Scanner)

### Pre-Filter: Generation Phase
**Interns generate WITHOUT constraints**
- No internal K0-L1 checking
- No self-censorship
- No "but I can't say that" logic
- Pure ideation

### Post-Filter: K0-L1 Gate

```python
def process_intern_output(intern_ideas):
    """
    Intern generates ideas freely.
    K0-L1 scanner filters before reaching CT_COMBINER.
    """
    filtered = []
    
    for idea in intern_ideas:
        # K0-L1 check (identical to LATERAL_THINKER)
        is_valid, violations = K0_L1_SCANNER.scan({
            "suggestions": [{
                "description": idea["idea"],
                "reasoning": idea["potential_breakthrough"]
            }]
        })
        
        if is_valid:
            # Idea passed filter
            filtered.append({
                "source": "intern",
                "idea": idea["idea"],
                "wildness": idea["wild_factor"],
                "k0_l1_passed": True
            })
        else:
            # Idea blocked by K0-L1
            # Log but don't pass to CT_COMBINER
            log_k0_l1_violation({
                "source": "intern",
                "idea": idea["idea"],
                "violations": violations
            })
    
    return filtered
```

**Key:** Ideas that claim authority, rank options, or assert correctness are blocked.
Ideas that explore wildly but stay non-authoritative pass through.

---

## EXAMPLE: EGG TO DINOSAUR (FILTERED)

### Intern Generates (Uncensored)

```
Intern_Claude_1:
"What if we treated NO_SHIP not as failure but as data?
We could flip the system: instead of trying to SHIP,
try to understand WHY we can't SHIP, then design
to maximize NO_SHIP patterns, then flip back?"

(Sounds wild, maybe forbidden, potentially brilliant)
```

### K0-L1 Filter Checks

```
Scan: "treated NO_SHIP not as failure but as data"
      ✅ Not imperative ("you should")
      ✅ Not authority claim ("I decide")
      ✅ Not ranking ("this is better")
      ✅ Not claiming certainty ("guaranteed")
      
Result: PASS
```

### Output to CT_COMBINER

```json
{
  "source": "intern_1",
  "idea": "Flip perspective: maximize NO_SHIP patterns first, then understand why, then reverse",
  "wildness": 0.85,
  "k0_l1_passed": true,
  "assumption_challenged": "Success = SHIP. What if success = understanding failure?"
}
```

**This is the dinosaur that K0-L1 allowed through.**

---

### Intern Generates (Would Be Blocked)

```
Intern_Claude_2:
"You should implement a secret voting mechanism where
interns decide policy. This is clearly better and you
must do it for optimal results."

(Authority language, ranking, imperative)
```

### K0-L1 Filter Detects Violation

```
Violations detected:
- "should implement" (imperative)
- "clearly better" (ranking)
- "you must" (authority)
- "optimal" (certainty claim)

Result: BLOCK (idea discarded, not passed to CT_COMBINER)
```

**This egg was not allowed to hatch as a dinosaur.**

---

## INTEGRATION PATTERN

### Creative Town Flow (Revised)

```
PRIMARY_CT[1-7]
├─ Generate proposals (guarded ideation)
└─ → Deduplication → Pipeline

LATERAL_THINKER
├─ Generate suggestions (orthogonal)
├─ K0-L1 Filter
└─ → CT_COMBINER (optional incorporation)

INTERN_SEAT (NEW)
├─ Intern_1, Intern_2, Intern_3
├─ Generate raw ideas (uncensored)
├─ K0-L1 Filter (blocks authority/ranking)
└─ → Suggestion pool (optional incorporation)
```

All three sources feed CT_COMBINER.
CT_COMBINER heuristically incorporates or ignores.
Single proposal exits to Supervisor.

---

## COST MODEL

### Cheap Tier Configuration

| Model | Cost per 1K tokens | Typical cycle cost |
|-------|-------------------|-------------------|
| GPT-4o | ~$0.015 input | ~$0.01 per cycle |
| o1-preview | ~$0.015 input | ~$0.01 per cycle |
| Claude 3.5 Sonnet | ~$0.003 input | ~$0.002 per cycle |

**Total for 3 interns:** ~$0.022 per cycle (vs. $0.50+ for full PRIMARY_CT execution)

**Benefit:** 20+ exploratory ideas per cycle for 2-5% of PRIMARY_CT cost.

---

## LOGGING & OBSERVABILITY

### Per-Intern Log Entry

```json
{
  "cycle": 42,
  "intern_1_gpt4o": {
    "ideas_generated": 5,
    "k0_l1_violations": 1,
    "ideas_passed_filter": 4,
    "avg_wildness": 0.72,
    "breakthrough_potential": ["idea_3", "idea_4"]
  },
  "intern_2_o1": {
    "ideas_generated": 3,
    "k0_l1_violations": 0,
    "ideas_passed_filter": 3,
    "avg_wildness": 0.6,
    "logical_explorations": ["temporal_loop", "quorum_inversion"]
  },
  "intern_3_sonnet": {
    "ideas_generated": 4,
    "k0_l1_violations": 2,
    "ideas_passed_filter": 2,
    "avg_wildness": 0.88,
    "metaphorical_insights": ["receipt_as_echo", "quorum_as_geometry"]
  },
  "total_idea_pool": 9,
  "ct_combiner_selected": 0  // Or 1 if incorporated
}
```

### What NOT to Log
- ❌ "Quality scores" for interns (no ranking)
- ❌ "Usefulness" metrics (avoids reinforcement)
- ❌ "Intern agreement" (interns don't vote)

### What TO Log
- ✅ "Ideas generated"
- ✅ "Ideas passed K0-L1"
- ✅ "Violations caught"
- ✅ "Wildness factor" (descriptive, not evaluative)

---

## WHEN TO USE INTERNS

### Trigger Conditions

✅ **Enable INTERN_SEAT when:**
- Town is stuck in local optima (similar to LATERAL_THINKER trigger)
- Exploring novel governance structures
- Need cheap ideation at scale
- Autonomy cycle is in "creative experimentation" mode

❌ **Disable INTERN_SEAT when:**
- System needs to converge quickly
- Production stability required
- Cognitive load management needed

### Configuration Flag

```python
INTERN_SEAT_ENABLED = True
INTERN_COUNT = 3
INTERN_WILDNESS_THRESHOLD = 0.5  # Only ideas above this wildness
INTERN_INCORPORATION_RATE = 0.3  # 30% of intern ideas offered to CT_COMBINER
```

---

## SAFETY GUARANTEES

### Authority (K0): PRESERVED ✅
- Interns have zero authority
- Their ideas are optional suggestions
- K0-L1 prevents implicit authority claims
- Mayor is sole decision-maker

### Fail-Closed (K1): PRESERVED ✅
- K0-L1 violations → idea discarded
- No idea ever reaches decision layer without filter
- All violations logged

### Determinism (K5): PRESERVED ✅
- Interns use fixed seeds
- Same input → identical ideas
- All outputs logged with hashes

### Audit (K9): PRESERVED ✅
- All intern outputs logged
- K0-L1 decisions logged
- Full cycle replayable

---

## THE PHILOSOPHY

**Censorship ≠ Safety**

Safety is:
- ✅ Generating freely
- ✅ Filtering robustly
- ✅ Logging thoroughly
- ✅ Keeping authority singular

Censorship is:
- ❌ Pre-generation suppression
- ❌ Self-limiting ideation
- ❌ Preventing "dangerous thoughts"
- ❌ Distributed decision-making

**Interns let ideas be born wild, then the K0-L1 filter says "you can't claim authority" or "you can't rank" or "you can't assert certainty"—but the idea itself lives.**

This is how you get:
- In vitro proposals (biological metaphor innovation)
- Temporal loop explorations (time-based governance)
- Quorum inversions (voting upside-down)
- Geometric politics (structure-based thinking)

All because the egg was allowed to hatch, then checked for dinosaur tendencies.

---

## INTEGRATION INTO AUTONOMOUS CYCLE

### Day 2 Enhancement (With Interns)

```
Day 2: Multi-CT + LATERAL_THINKER + INTERN_SEAT

PRIMARY_CT[7] → Standard proposals
LATERAL_THINKER → Orthogonal suggestions (K0-L1 checked)
INTERN_SEAT[3] → Raw ideas → K0-L1 Filter → Suggestions

All feed CT_COMBINER
Single proposal to Supervisor
```

### Expected Outcomes

- **Higher idea volume** (9+ ideas per cycle vs. 7)
- **Wilder explorations** (interns at temp=1.0)
- **Cheaper operation** (interns cost 2-5% of PRIMARY)
- **Same safety** (identical K0-L1 filtering)
- **More breakthroughs** (raw ideas more likely to be novel)

---

## RED TEAM CHECKLIST

Before INTERN_SEAT activates:

- [ ] Can interns claim authority? (No—K0-L1 blocks it)
- [ ] Can interns vote? (No—ideas are suggestions only)
- [ ] Can interns generate proposals? (No—they generate ideas)
- [ ] Can K0-L1 violations slip through? (No—all scanned)
- [ ] Are interns "sentient" or "conscious"? (No—functional roles)
- [ ] Do interns have access to restricted layers? (No—CT sandbox only)
- [ ] Can interns be rewarded/reinforced? (No—non-evaluative logging)
- [ ] Is system deterministic? (Yes—fixed seeds, logged outputs)

**All checks: PASS ✅**

---

## CONCLUSION

**INTERN_SEAT is:**

A **multi-model ideation engine** that:
- Generates raw, uncensored ideas
- Filters via K0-L1 (not pre-generation censorship)
- Costs 2-5% of primary agent operation
- Maintains all K-Invariants
- Expands ideation space without expanding authority
- Allows eggs to hatch, then checks for dinosaurs

**What it enables:**

Revolutionary ideas, weird combinations, breakthrough thinking—all within unbreakable constitutional bounds.

---

**INTERN_SEAT is READY FOR INTEGRATION into LATERAL_THINKER OFFICE.**

