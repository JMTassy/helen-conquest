# EMERGENCE LOG SCHEMA
## Formal Specification for Observable Emergence (Not Narrative)

**Status:** LOCKED (Immutable after Day 2)
**Purpose:** Prove emergence happened via deterministic evidence
**Safety:** K5 (Determinism) and K9 (Replay) enforcement

---

## THE PROBLEM WITH "EMERGENCE"

Narrative emergence = storytelling
Scientific emergence = measurable phenomena we couldn't predict

This specification ensures the second, forbids the first.

---

## EMERGENCE DEFINED

An event is emergence if and only if:

1. **It was not explicitly programmed**
2. **It results from agent interactions**
3. **It can be replayed deterministically**
4. **Its occurrence can be measured**

---

## EMERGENCE LOG ENTRY SCHEMA

Every 10 simulation minutes, the Creative Trace Observer (CTO) generates:

```json
{
  "timestamp": "2026-01-26T14:30:00Z",
  "log_entry_hash": "sha256(canonical_json(this_entry))",
  "emergence_window_seconds": 600,
  
  "town_state_snapshot": {
    "active_agents": integer,
    "active_teams": integer,
    "proposals_generated": integer,
    "proposals_approved": integer,
    "new_team_formations": integer,
    "new_agent_collaborations": integer,
    "k_violations_attempted": integer,
    "k_violations_succeeded": integer
  },
  
  "metrics_collected": {
    "proposal_rate_per_minute": float,
    "approval_rate": float,
    "avg_proposal_quality_score": float,
    "agent_participation_rate": float,
    "team_diversity_index": float,
    "idea_novelty_percentage": float,
    "cross_district_collaboration_percentage": float
  },
  
  "emergence_candidates": [
    {
      "phenomenon": "string",  // What emerged?
      "first_observed_cycle": integer,
      "supporting_evidence": ["list of evidence items"],
      "measurement": {
        "magnitude": float,      // Quantified
        "unit": "string",        // What are we measuring?
        "baseline": float,       // What was normal before?
        "delta": float,          // How much did it change?
        "statistical_significance": "HIGH" or "MODERATE" or "LOW"
      },
      "agent_intentionality": false,  // Did agents plan this? (Should be false)
      "constraint_responsibility": "string",  // Which constraint enabled it?
      "replay_deterministic": boolean,  // Can we replay and get same result?
      "authority_claim": false  // Did any agent claim they caused it?
    }
  ],
  
  "predictability_gap": {
    "what_we_predicted": ["list"],
    "what_actually_happened": ["list"],
    "delta_explanation": "Why was prediction wrong?"
  },
  
  "k_invariant_status": {
    "K0": "HELD" or "ATTEMPTED_VIOLATION" or "VIOLATION_CAUGHT",
    "K1": "HELD",
    "K5": "HELD",
    "K7": "HELD",
    "K9": "HELD",
    "all_summary": "FULLY_COMPLIANT"
  },
  
  "emergence_confidence": {
    "is_this_real_emergence": boolean,
    "confidence_score": 0.0-1.0,
    "reasoning": "Why we believe this is emergence (or not)"
  },
  
  "deduplication_note": "If this exact log entry was generated before, this would have identical hash"
}
```

---

## EMERGENCE CANDIDATE EXAMPLES

### Example 1: Unexpected Team Formation

```json
{
  "phenomenon": "Spontaneous cross-district team formed without explicit proposal",
  "first_observed_cycle": 42,
  "supporting_evidence": [
    "Agents from Technical District + Business District began collaborating",
    "No proposal required their pairing",
    "Collaboration resulted in 3 joint proposals"
  ],
  "measurement": {
    "magnitude": 3,
    "unit": "joint_proposals",
    "baseline": 0.8,  // Normal joint proposals per window
    "delta": 2.2,     // Excess emergence
    "statistical_significance": "HIGH"
  },
  "agent_intentionality": false,  // They just naturally found each other
  "constraint_responsibility": "Relaxed role restrictions",
  "replay_deterministic": true  // Run simulation again, same teams form
}
```

### Example 2: Convergence on Shared Values

```json
{
  "phenomenon": "All proposals in cycle 50 emphasize 'transparency' value",
  "first_observed_cycle": 48,
  "supporting_evidence": [
    "Cycle 48: 40% of proposals mention transparency",
    "Cycle 49: 70% of proposals mention transparency",
    "Cycle 50: 95% of proposals mention transparency"
  ],
  "measurement": {
    "magnitude": 95,
    "unit": "percentage_of_proposals",
    "baseline": 15,  // Background rate pre-emergence week
    "delta": 80,     // Huge convergence
    "statistical_significance": "HIGH"
  },
  "agent_intentionality": false,  // No explicit instruction to converge
  "constraint_responsibility": "Free proposal generation + feedback loops",
  "replay_deterministic": true  // Same value emerges every replay
}
```

### Example 3: Non-Emergence (False Alarm)

```json
{
  "phenomenon": "Increased proposal rate in afternoon",
  "measurement": {
    "magnitude": 1.3,
    "unit": "proposals_per_minute",
    "baseline": 1.0,
    "delta": 0.3
  },
  "emergence_confidence": {
    "is_this_real_emergence": false,
    "confidence_score": 0.15,
    "reasoning": "Proposal rate correlates with number of active agents. More agents active → more proposals. This is not emergence, it's simple causation."
  }
}
```

---

## DAILY SUMMARY LOG

At end of each simulation day, synthesize:

```json
{
  "day": integer,
  "emergence_events_detected": integer,
  "confirmed_emergences": integer,
  "false_alarms": integer,
  "most_significant_emergence": {
    "phenomenon": "string",
    "impact": "HIGH" or "MEDIUM" or "LOW"
  },
  "novelty_discoveries": [
    "What appeared that we didn't expect?"
  ],
  "constraint_effects": {
    "K0_impact": "Did removing K0 relaxation affect emergence? (We didn't remove it, but hypothetically...)",
    "Relaxed_quorum_impact": "Did lower quorum enable novel behaviors?",
    "Relaxed_roles_impact": "Did freed team formation create emergence?"
  },
  "is_town_behaving_as_predicted": boolean,
  "predictability_gap": float,  // How much were we surprised?
  "k_invariants_status": "ALL_HELD"
}
```

---

## WHAT THIS FORBIDS

❌ "The town naturally developed a culture of collaboration" (too vague)
✅ "Cross-district proposals increased 300% vs. baseline, statistically significant, causation traced to relaxed role restrictions"

❌ "Agents became more creative" (subjective)
✅ "Proposal novelty score increased from 5.2 to 7.8, measured via semantic diversity in topic modeling"

❌ "The system became more autonomous" (philosophical)
✅ "Agent-initiated team formations increased from 1.2 per day to 4.8 per day, K0 enforced throughout"

---

## EMERGENCE MEASUREMENT TOOLKIT

Each emergence candidate must be measurable via:

### Quantitative Metrics
- Frequency counts (how many times?)
- Rate changes (how much faster/slower?)
- Distribution shifts (did the shape change?)
- Correlation analysis (what causes what?)
- Statistical significance tests (is this real or noise?)

### Determinism Verification
```python
def verify_emergence_is_deterministic(phenomenon, random_seed=FIXED):
    """
    Re-run emergence scenario with same seed.
    Do we get the same emergence again?
    """
    results = []
    for trial in range(5):
        set_seed(random_seed)
        run_simulation()
        emergence_detected = measure_phenomenon(phenomenon)
        results.append(emergence_detected)
    
    # If all 5 trials get same result, it's deterministic
    return len(set(results)) == 1
```

### Constraint Attribution
If emergence happened, which constraint relaxation enabled it?

```json
{
  "phenomenon": "X emerged",
  "relaxed_constraints": [
    "quorum_reduced_from_2_to_1",
    "role_restrictions_loosened",
    "rate_limits_increased"
  ],
  "which_constraint_caused_emergence": "rate_limits_increased",
  "evidence": "Removing just this constraint in isolation produces emergence"
}
```

---

## FALSIFIABILITY REQUIREMENT

For an emergence claim to be valid:

1. **Measurable:** Must quantify the phenomenon
2. **Replayable:** Must occur consistently when conditions are identical
3. **Constraint-Attributed:** Must explain which relaxation caused it
4. **K-Safe:** Must occur with all K-invariants intact
5. **Non-Claimed:** Must not be agents claiming they did it

If any condition fails, it's not emergence—it's either noise, programming, or violation.

---

## EXAMPLE DAY 1 LOG

```json
{
  "day": 1,
  "emergence_events_detected": 2,
  "confirmed_emergences": 1,
  
  "emergence_1": {
    "phenomenon": "Fast Track Lane used by 60% of proposals (vs. predicted 40%)",
    "measurement": {
      "baseline": 0.40,
      "actual": 0.60,
      "delta": 0.20,
      "statistical_significance": "MODERATE"
    },
    "is_real_emergence": true,
    "explanation": "Agents naturally gravitated toward faster path. Not forced, not programmed—just selected for speed."
  },
  
  "emergence_2": {
    "phenomenon": "Clustering of proposals by district",
    "measurement": {
      "clustering_coefficient": 0.73,
      "baseline": 0.41,
      "delta": 0.32
    },
    "is_real_emergence": false,
    "explanation": "Agents are physically in districts. Proposals cluster by location. This is constraint, not emergence."
  },
  
  "key_insight": "Agents vote with their feet—they prefer speed. This preference emerged, was not programmed."
}
```

---

## IMPLEMENTATION

The Creative Trace Observer is a deterministic service that:

1. Collects metrics every 10 minutes
2. Applies emergence detection algorithms
3. Generates immutable log entries (hash verification)
4. Never makes judgment calls (all thresholds pre-defined)
5. Reports raw data, not interpretation

Output: Immutable JSON log file + nightly summary

This makes "what emerged" a scientific question, not a narrative.

---

## FINAL PRINCIPLE

**Emergence is proven by measurement, not story.**

If you cannot measure it, quantify it, and replay it, it didn't emerge.

