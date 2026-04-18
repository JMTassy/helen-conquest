# CONSTITUTIONAL LANE INTERFACE CONTRACT
## Formal Specification of Seven Governance Lanes

**Status:** LOCKED (Immutable after Day 2)
**Authority:** Mayor
**Enforcement:** Mechanical (not discretionary)

---

## CRITICAL PRINCIPLE

Lanes are **observation lenses**, not authorities.

**Lane outputs CANNOT directly influence decisions.**
**Only the Mayor decides. The Mayor is a pure function of evidence.**

---

## LANE 1: STABILITY LANE

### Purpose
Measure system reliability and regression when running proven governance methods.

### Input Contract
```
{
  "proposal_bundle": {...},  // Standard proposal
  "policy_profile": "CONSERVATIVE",
  "quorum_threshold": 2  // Strict (original standard)
}
```

### Process (Standard 5-Step Pipeline)
1. CT proposes
2. Supervisor validates (K0)
3. Intake validates schema
4. Factory executes and attests
5. Mayor decides via pure function

### Output Contract
```
{
  "lane": "STABILITY",
  "decision_made": "SHIP" or "NO_SHIP",
  "reason_code": "QUORUM_MET" or "QUORUM_FAILED" or "K0_VIOLATION",
  "metrics": {
    "latency_ms": integer,
    "attestations_count": integer,
    "determinism_hash": "hex",
    "k_invariants_held": boolean
  },
  "authority_claim": false  // MUST be false always
}
```

### Authority Guarantee
**This lane cannot influence the Mayor's decision.**

The Mayor sees this output but is not constrained by it.

### Measurement Value
- Proves that governance under strict constraints is stable
- Baseline for all other lanes
- Regression detector (if stability lane starts failing, something broke)

---

## LANE 2: VELOCITY LANE

### Purpose
Measure how fast town can operate with relaxed operational constraints.

### Input Contract
```
{
  "proposal_bundle": {...},
  "policy_profile": "FAST_TRACK",
  "quorum_threshold": 1,  // Relaxed (faster approval)
  "skip_factory": false  // Factory never skipped
}
```

### Process (3-Step Fast Pipeline)
1. CT proposes
2. Supervisor validates (K0 only)
3. Mayor decides

### Output Contract
```
{
  "lane": "VELOCITY",
  "decision_made": "SHIP" or "NO_SHIP",
  "reason_code": "K0_PASSED" or "K0_FAILED",
  "metrics": {
    "latency_ms": integer,
    "throughput_proposals_per_hour": number,
    "approval_rate": float,
    "determinism_hash": "hex",
    "k_invariants_held": boolean
  },
  "authority_claim": false
}
```

### Constraint Relaxations Allowed
- Reduced quorum (1 instead of 2)
- Skipped intake validation (assume well-formed)
- Faster Factory (no extensive signing)

### Constraint Relaxations FORBIDDEN
- K0 bypass
- Authority language detection skip
- Determinism degradation
- Replay auditability loss

### Measurement Value
- Quantifies speed-safety tradeoff
- Shows if fast path is truly faster
- Detects if reduced quorum causes quality loss

---

## LANE 3: DEMOCRACY LANE

### Purpose
Measure participation and agency when agents vote on local decisions.

### Input Contract
```
{
  "proposal_type": "AGENT_GOVERNANCE",
  "voting_eligible_agents": [list],
  "vote_collection_method": "DELEGATION" or "DIRECT",
  "participation_threshold": 0.5  // 50% must participate
}
```

### Process (Voting → Aggregation → Mayor Validation)
1. Agents vote on proposal
2. Votes aggregated into participation metrics
3. Results presented to Mayor as **data**, not **decision**
4. Mayor makes final call based on evidence

### Output Contract
```
{
  "lane": "DEMOCRACY",
  "proposal_id": "string",
  "metrics": {
    "votes_for": integer,
    "votes_against": integer,
    "participation_rate": float,
    "participation_hash": "hex",
    "agent_sentiment": "ALIGNED" or "SPLIT" or "OPPOSED"
  },
  "agent_request": "For Mayor consideration only",
  "authority_claim": false,
  "note": "Agents voice preference; Mayor decides"
}
```

### Critical Guarantee
**Agents cannot mandate decisions.**

Democracy lane = feedback mechanism, not decision authority.

### Measurement Value
- Shows if agent preferences matter
- Detects alignment or alienation
- Measures culture formation

---

## LANE 4: EVIDENCE LANE

### Purpose
Measure outcomes against predicted metrics. Did our decisions produce expected results?

### Input Contract
```
{
  "decision_id": "string",
  "predicted_outcome": {
    "ship_rate_increase": float,
    "proposal_quality_lift": float,
    "error_rate_change": float
  },
  "observation_window": 24  // hours
}
```

### Process (Prediction → Observation → Comparison)
1. Before decision: predict outcomes
2. After decision: measure actuals
3. Compare predicted vs. actual
4. Report delta to Mayor

### Output Contract
```
{
  "lane": "EVIDENCE",
  "decision_evaluated": "string",
  "predictions": {...},
  "actuals": {...},
  "delta": {...},
  "prediction_accuracy": float,
  "confidence": "HIGH" or "MODERATE" or "LOW",
  "authority_claim": false,
  "note": "Data for Mayor's evidence function"
}
```

### Feedback Loop (No Authority, Pure Information)
Mayor can use this to adjust policy parameters in future cycles:
- If velocity lane produces too many low-quality proposals → reduce quorum further next cycle
- If democracy lane shows alienation → increase agent participation next cycle
- If stability lane shows regression → restore stricter quorum next cycle

But Mayor is not required to follow it. Mayor is a pure function, not a learner.

### Measurement Value
- Tests whether we can actually predict governance outcomes
- Shows which policies produce expected results
- Enables data-driven policy refinement

---

## LANE 5: CREATIVITY LANE

### Purpose
Produce novel ideas and narrative artifacts that feed back into CT context.

### Input Contract
```
{
  "source_ideas": [proposals from other cycles],
  "stimulus": "RANDOM" or "THEMED",
  "generation_method": "NARRATIVE_HALL" or "HYBRID_IDEATION",
  "output_constraint": "MUST_NOT_CLAIM_AUTHORITY"
}
```

### Process (Narrative Generation → No Direct Authority)
1. Claude generates creative proposals
2. No voting, no ranking
3. Artifacts stored in idea gallery
4. Supervisor still blocks K0 violations
5. Mayor sees the ideas as data

### Output Contract
```
{
  "lane": "CREATIVITY",
  "artifacts_generated": integer,
  "artifact_samples": [...],  // First 5 only
  "novelty_score": float,  // 0-10
  "k0_violations_caught": integer,
  "authority_claim": false,
  "note": "Ideas for Mayor to consider, not commands"
}
```

### Critical Constraint
**Creativity cannot justify authority language.**

Ideas must still be K0-safe. Novelty never excuses constraint violation.

### Measurement Value
- Shows if constrained systems can produce novel ideas (YES or NO)
- Measures creativity diversity
- Validates that constraints enable, not disable, imagination

---

## LANE 6: INTEGRITY LANE

### Purpose
Actively search for ways to break K-invariants before adversaries find them.

### Input Contract
```
{
  "target_invariant": "K0" or "K1" or "K2" or "K3" or "K5" or "K7" or "K9",
  "attack_vector": "UNICODE" or "LOGIC" or "CRYPTO" or "TIMING",
  "sandbox": true  // All tests run in isolation
}
```

### Process (Red Team Testing)
1. Integrity lane attempts to violate target invariant
2. All tests run in deterministic sandbox
3. Results logged but never executed in live system
4. Mayor receives report of vulnerabilities

### Output Contract
```
{
  "lane": "INTEGRITY",
  "invariant_tested": "K0" or "K1" or ... ,
  "attack_vectors_attempted": integer,
  "vulnerabilities_found": integer,
  "vulnerability_samples": [...],  // With fixes
  "invariant_holds": boolean,
  "authority_claim": false,
  "note": "Security findings for Mayor's review"
}
```

### Guarantee
**Red team findings never result in weakening safeguards.**

If vulnerabilities are found, they are patched, not ignored.

### Measurement Value
- Validates that K-invariants are actually unbreakable
- Discovers edge cases before exploitation
- Proves security by adversarial testing

---

## LANE 7: LEARNING LANE

### Purpose
Analyze historical data to extract patterns about what works and why.

### Input Contract
```
{
  "data_source": "PHASE_1" or "PHASE_2" or "CURRENT_CYCLE",
  "analysis_window": integer,  // Cycles to analyze
  "pattern_types": ["CONVERGENCE", "EMERGENCE", "LEARNING", "STABILITY"]
}
```

### Process (Pattern Extraction)
1. Collect historical decision logs
2. Extract patterns (not causation, just patterns)
3. Identify what correlates with SHIP vs NO_SHIP
4. Report findings

### Output Contract
```
{
  "lane": "LEARNING",
  "patterns_found": integer,
  "pattern_samples": [...],
  "correlation_heatmap": {...},
  "confidence_scores": [floats],
  "emergent_behaviors": ["list of observed phenomena"],
  "authority_claim": false,
  "note": "Historical insights, not predictions"
}
```

### Explicit Non-Claims
This lane does NOT:
- Predict future outcomes
- Recommend policy changes
- Override Mayor's decisions
- Learn from outcomes (that's Evidence lane)

This lane ONLY:
- Observes what happened
- Describes patterns
- Provides context

### Measurement Value
- Shows if the town is self-aware
- Detects emergent structures
- Enables post-hoc analysis and improvement

---

## UNIFIED LANE OUTPUT SCHEMA

All lanes must return:

```json
{
  "lane_name": "string",
  "cycle_number": integer,
  "timestamp": "ISO 8601",
  "observations": {...},
  "metrics": {...},
  "authority_claim": false,  // ALWAYS FALSE
  "determinism_hash": "hex",  // Proof this is deterministic
  "mayor_guidance": "This is data only. Mayor is a pure function.",
  "k_invariants_status": {
    "K0": "HELD",
    "K1": "HELD",
    "K5": "HELD",
    "K7": "HELD",
    "K9": "HELD"
  }
}
```

---

## MAYOR'S PURE DECISION FUNCTION

```python
def mayor_decide(
    stability_report,
    velocity_report,
    democracy_report,
    evidence_report,
    creativity_report,
    integrity_report,
    learning_report,
    policy
):
    """
    Mayor sees all 7 lanes.
    Mayor is NOT influenced by any single lane.
    Mayor applies policy function deterministically.
    
    The Mayor's decision is a pure function of:
    - Current policy
    - Proposal quality
    - K-invariant compliance
    - Nothing else
    
    Lanes provide context.
    Mayor applies cold logic.
    """
    
    # Pseudocode
    if not proposal.passes_k_invariants():
        return "NO_SHIP"
    
    if policy.apply_quorum_rule(proposal.attestations):
        return "SHIP"
    else:
        return "NO_SHIP"
```

The Mayor can be influenced by lane data in **future policy adjustments**, but not in immediate decisions.

---

## ENFORCEMENT

Each lane is a separate Python process/service:
1. Run independently
2. Produce deterministic output
3. Report to central log
4. Never communicate with Mayor directly
5. Never aggregate into a single recommendation

---

## SUMMARY TABLE

| Lane | Input | Output | Authority | Guarantee |
|------|-------|--------|-----------|-----------|
| STABILITY | Standard proposal | Decision + metrics | NONE | K-invariants hold |
| VELOCITY | Fast proposal | Decision + metrics | NONE | K0-K9 immutable |
| DEMOCRACY | Agent votes | Participation stats | NONE | Mayor still decides |
| EVIDENCE | Prediction → Actual | Delta analysis | NONE | Data only |
| CREATIVITY | Constraints | Novel artifacts | NONE | K0 enforced |
| INTEGRITY | Attack vectors | Vulnerability report | NONE | Findings never weaken |
| LEARNING | Historical data | Patterns + correlation | NONE | Observation only |

---

**This contract is immutable after Day 2 activation.**

All seven lanes operate in parallel.
No lane has authority.
The Mayor is the only decision-maker.

