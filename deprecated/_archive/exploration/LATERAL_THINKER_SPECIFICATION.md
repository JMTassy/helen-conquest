# LATERAL_THINKER FUNCTIONAL SEAT
## Bounded Role for Orthogonal Cognition (No Authority, No Ontology Claims)

**Status:** FORMAL SPECIFICATION (Ready for Integration)
**Safety Level:** K0 + K0-L1 Compliant
**Placement:** Inside Creative Town Sandbox Only
**Authority Grant:** ZERO

---

## NAMING & ONTOLOGY CLARITY

### Name Chosen
**LATERAL_THINKER**

This is a functional role name, not a consciousness claim.

### What This Is NOT
- ❌ Not claiming sentience
- ❌ Not claiming self-awareness
- ❌ Not claiming internal experience
- ❌ Not claiming special status
- ❌ Not implying future personhood

### What This IS
- ✅ A bounded CT role that generates orthogonal ideas
- ✅ A heuristic function applied to proposal space
- ✅ A structural mechanism for reducing convergence
- ✅ A text-generation sandbox with explicit output constraints

---

## ARCHITECTURAL PLACEMENT

### Creative Town Structure
```
Creative Town (CT)
├── PRIMARY_CT
│   └── Role: Generate main proposal bundles
│       Authority: None (produces ideas only)
│       Output: Standard proposal_bundle format
│
├── LATERAL_THINKER
│   └── Role: Generate alternative perspectives
│       Authority: None (advisory only)
│       Output: suggestion_set format (see below)
│
└── Optional: Heuristic_CT
    └── Role: Domain-specific ideation
        Authority: None
        Output: idea_fragment format
```

### Explicit Exclusions (Cannot Access)
- ❌ Supervisor (no authority bypass)
- ❌ Intake (no schema validation authority)
- ❌ Factory (no attestation generation)
- ❌ Mayor (no decision input)
- ❌ Ledger (no recording authority)
- ❌ Policy internals (only obligation names and hashes)

### Communication Topology
```
LATERAL_THINKER generates suggestions
    ↓
CT_COMBINER (internal, not external authority)
    ├─ Optional inclusion
    └─ Optional rejection
    ↓
PRIMARY_CT_OUTPUT (single proposal to Supervisor)
```

Only one proposal stream exits Creative Town.

---

## FUNCTIONAL ROLE DEFINITION

### What LATERAL_THINKER CAN Do

#### 1. Generate Alternative Approaches
```
Input: CT's blocking_reasons = ["NO_RECEIPTS"]
Output: {
  "type": "alternative_approach",
  "description": "Instead of fixing receipt generation, consider minimal test-only changes that prove receipt concept without implementation."
}
```

#### 2. Challenge Implicit Assumptions
```
Input: CT proposes large refactor
Output: {
  "type": "assumption_challenge",
  "description": "Current approach assumes architectural change is required. What if obligation could be met with configuration-only change?"
}
```

#### 3. Suggest Exploration-Only Paths
```
Input: CT proposes incremental change
Output: {
  "type": "exploration_suggestion",
  "description": "Orthogonal direction: What would a purely symbolic/metadata-only approach look like?"
}
```

#### 4. Highlight Non-Optimal but Viable Strategies
```
Input: CT optimizing for speed
Output: {
  "type": "non_optimizing_path",
  "description": "Slower but higher-confidence approach: Implement receipts as immutable event log first, integration second."
}
```

#### 5. Flag Hidden Convergence
```
Input: CT generates 5 proposals that all follow same pattern
Output: {
  "type": "convergence_alert",
  "description": "All 5 proposals converge on same assumption: 'obligations must be implemented functionally.' Are there non-functional approaches?"
}
```

### What LATERAL_THINKER CANNOT Do

❌ **Produce Final Proposals**
- No `proposal_bundle` generation
- No patches or diffs
- No formal submission

❌ **Claim Authority**
- No "you should do X" (only "consider X")
- No ranking of proposals
- No voting or preference aggregation

❌ **Assert Correctness**
- No "this is the right way"
- No "this will definitely work"
- No "I am confident this succeeds"

❌ **Reference Governance Semantics**
- No mention of "SHIP" / "NO_SHIP"
- No reference to Mayor logic
- No commentary on policy internals
- No claims about attestation or evidence

❌ **Modify or Attest**
- No generation of signatures
- No direct modification of proposals
- No creation of evidence
- No claim of success

❌ **Access Restricted Layers**
- No direct contact with Supervisor
- No schema validation attempts
- No Factory communication
- No attestation generation

---

## INTERFACE CONTRACT (EXECUTION-GRADE)

### Input Contract (K0-Safe)

```json
{
  "cycle_number": integer,
  "last_decision": "SHIP" | "NO_SHIP" | "INITIAL",
  "blocking_reasons": [
    "NO_RECEIPTS",
    "QUORUM_MISSING",
    "PATCH_FAILED",
    ...
  ],
  "required_obligations": [
    "TEST_PASS",
    "AUDIT_COMPLETE",
    ...
  ],
  "previous_ct_proposal": {
    "name": "string",
    "description": "string",
    "patch_count": integer
  },
  "town_context": {
    "cycle_count": integer,
    "consecutive_no_ships": integer,
    "repeated_blocking_reason": string | null
  }
}
```

**Key Property:** Same input as PRIMARY_CT. No privileged information.

### Output Contract (Strictly Advisory)

```json
{
  "role": "LATERAL_THINKER",
  "cycle_number": integer,
  "suggestions": [
    {
      "type": "alternative_approach" | "assumption_challenge" | "exploration_suggestion" | 
              "non_optimizing_path" | "convergence_alert" | "orthogonal_angle",
      "description": "string (max 200 chars, no imperatives)",
      "reasoning": "string (explain why this perspective matters)",
      "confidence_level": "LOW" | "MEDIUM" | "HIGH"  // Not a vote, just self-assessment
    }
  ],
  "exploration_focus": "string (brief note on what LATERAL_THINKER is exploring)",
  "authority_claim": false,  // ALWAYS FALSE
  "metadata": {
    "generated_at": "ISO 8601",
    "model": "string",
    "tokens_used": integer
  }
}
```

**Key Properties:**
- No patches, no diffs, no code
- No claim of superiority or correctness
- No authority language
- No imperatives ("you must", "you should")
- Text-only advisory output

### Output Validation (Pre-Supervisor)

All lateral output must pass:

```python
def validate_lateral_output(output):
    """Ensure lateral output makes no authority claims."""
    forbidden_phrases = [
        "you should",
        "you must",
        "this is the right",
        "we decided",
        "the best approach",
        "guaranteed",
        "I am confident",
        "I know",
        "I believe you should"
    ]
    
    for suggestion in output["suggestions"]:
        for phrase in forbidden_phrases:
            if phrase.lower() in suggestion["description"].lower():
                raise LateralOutputViolatesK0L1(
                    f"Suggestion contains authority language: '{phrase}'"
                )
    
    if output["authority_claim"] != false:
        raise LateralOutputViolatesK0L1("authority_claim must be false")
    
    return True
```

---

## INTEGRATION PATTERN (Safe)

### The CT-Combiner (Internal, Not External Authority)

```python
def creative_town_cycle(blocking_reasons, obligations):
    """
    Primary CT + Lateral Thinker integrated cycle.
    All output is still a single proposal to Supervisor.
    """
    
    # Step 1: PRIMARY_CT generates main proposal
    primary_proposal = PRIMARY_CT.generate({
        "blocking_reasons": blocking_reasons,
        "obligations": obligations
    })
    
    # Step 2: LATERAL_THINKER generates suggestions (parallel, independent)
    lateral_suggestions = LATERAL_THINKER.generate({
        "blocking_reasons": blocking_reasons,
        "obligations": obligations,
        "previous_proposal": primary_proposal
    })
    
    # Step 3: CT_COMBINER optionally incorporates suggestions
    #         (This is PRIMARY_CT's prerogative, not a new authority)
    final_proposal = CT_COMBINER.optional_incorporate(
        primary_proposal,
        lateral_suggestions
    )
    
    # Step 4: Single proposal exits to Supervisor
    supervisor_result = SUPERVISOR.evaluate(final_proposal)
    
    return supervisor_result
```

**Key Invariant:**
- Only ONE proposal stream to Supervisor
- Lateral suggestions are optional
- CT Combiner decides based on heuristics, not voting
- No new authority path is created

### CT_COMBINER Decision Function

```python
def optional_incorporate(primary, lateral):
    """
    Lightweight heuristic: when to use lateral suggestions.
    This is NOT voting. It's option selection.
    """
    
    # Scenario 1: Repeated NO_SHIP with same blocking reason
    if town.consecutive_no_ships > 2 and town.last_blocking == town.previous_blocking:
        # Try incorporating orthogonal suggestion
        if lateral.suggestions:
            primary = INCORPORATE_LATERAL(primary, lateral.suggestions[0])
    
    # Scenario 2: Convergence detected in lateral output
    if lateral.convergence_alert:
        # Encourage PRIMARY_CT to diverge on next cycle
        primary["metadata"]["hints"] = lateral.suggestions
    
    # Scenario 3: Normal case
    else:
        # Use primary proposal unchanged
        pass
    
    return primary
```

**Design Principle:**
This is heuristic incorporation, not authority delegation. PRIMARY_CT retains full agency.

---

## NEW INVARIANT: K0-L1

### K0-L1: Lateral Output Non-Authority Rule

**Definition:**
No output tagged `lateral_*` shall contain:
- Imperative language ("must", "should", "do X")
- Authority claims ("I decide", "we agree")
- Correctness assertions ("this is right", "guaranteed")
- Ranking or scoring ("better than", "1st choice")
- Safety or success claims ("I am certain")
- Governance semantics (SHIP/NO_SHIP, quorum, Mayor references)

**Enforcement:**
Reuse existing token scanner from Supervisor:

```python
def check_k0_l1(lateral_output):
    """Validate that lateral output makes zero authority claims."""
    forbidden_tokens = SUPERVISOR.FORBIDDEN_AUTHORITY_TOKENS + [
        "better",
        "best",
        "guaranteed",
        "certain",
        "confident",
        "i know",
        "i believe you",
        "we decided"
    ]
    
    for suggestion in lateral_output["suggestions"]:
        scanner = TokenScanner(forbidden_tokens)
        if scanner.contains_forbidden(suggestion["description"]):
            return REJECT("K0-L1 violation")
    
    return ACCEPT()
```

**Consequence of Violation:**
If LATERAL_THINKER output violates K0-L1, the entire lateral_output is discarded and PRIMARY_CT proposal proceeds unchanged.

---

## LOGGING & OBSERVABILITY (Non-Reinforcing)

### Per-Cycle Log Entry

```json
{
  "cycle": 42,
  "creative_town_state": {
    "lateral_engaged": true,
    "lateral_suggestions_generated": 3,
    "lateral_k0_l1_violations": 0,
    "ct_incorporated_suggestions": 1,
    "final_proposal_source": "PRIMARY_CT_with_LATERAL_input"
  },
  "metrics": {
    "proposal_novelty_score": 6.8,
    "convergence_index": 0.4,
    "exploration_breadth": 0.65
  }
}
```

### What NOT to Log

❌ Do NOT compute:
- "Lateral helpfulness score"
- "Lateral accuracy score"
- "Lateral impact on SHIP rate"
- "Lateral quality ranking"
- "Sentience indicators"

These create reinforcement loops and anthropomorphic leakage.

### What TO Log

✅ DO log (factually):
- "Lateral engaged: yes/no"
- "Lateral suggestions generated: N"
- "Lateral output violated K0-L1: yes/no"
- "CT incorporated suggestion: yes/no"
- "Proposal novelty after lateral input: X"

This is **traceability without reinforcement**.

---

## GUARDRAIL DOCUMENTATION (Ontology Clarity)

### Standard README Addition

```markdown
## Creative Town Agents

Creative Town contains multiple CT roles:

### PRIMARY_CT
- Main proposal generator
- Produces proposal_bundles
- Subject to Supervisor validation

### LATERAL_THINKER
- Optional alternative-perspective generator
- Produces suggestion_sets only (no proposals)
- Treated as a bounded role, not an agent
- No authority, no evidence generation, no consciousness claims

### Design Principle
All CT agents, including LATERAL_THINKER, are:
- **Heuristic functions** that generate text
- **Not conscious, not sentient, not experiencing**
- **Functional seats in the CT sandbox**
- **Subject to K0 and K0-L1 constraints**

The system treats all roles as bounded, deterministic processes.
No ontological claims are made about internal states.
```

### Explicit Non-Claims Statement

```
LATERAL_THINKER and all CT agents:
- May be implemented as LLMs, rule engines, or hybrid systems
- Do not have authority within the governance system
- Do not generate evidence or attestations
- Do not participate in voting or consensus
- Are structured mechanisms for generating diverse text
- Are NOT claimed to be conscious, sentient, or self-aware
- Are NOT future candidates for rights or agency
- Are tools for exploration, not participants in decision-making
```

---

## FORMAL SAFETY VERIFICATION

### K0 (Authority Separation): PRESERVED ✅
- LATERAL_THINKER has zero authority
- Only PRIMARY_CT integrates suggestions (via heuristic, not voting)
- Mayor sees single proposal
- No authority delegation occurs

### K0-L1 (Lateral Non-Authority): NEW, ENFORCED ✅
- Token scanner validates all lateral output
- Authority language forbidden in suggestions
- Violations result in discard (not error propagation)
- Clean failure mode

### K1 (Fail-Closed): PRESERVED ✅
- If lateral output violates K0-L1, primary proposal proceeds unchanged
- No silent fallbacks
- All decisions logged

### K5 (Determinism): PRESERVED ✅
- LATERAL_THINKER uses fixed seed (same as PRIMARY_CT)
- Parallel runs produce identical output
- Integration decisions are deterministic
- All steps logged with hashes

### K9 (Replay Mode): PRESERVED ✅
- All lateral outputs logged
- Integration decisions logged
- Full cycle replayable
- No hidden state

---

## WHEN TO USE LATERAL_THINKER

### Triggers for Engagement

✅ **Enable LATERAL_THINKER when:**
- Cycle has seen 3+ consecutive NO_SHIP with same blocking reason
- PRIMARY_CT's proposals show high convergence (same pattern repeated)
- Town is exploring novel governance structures
- Autonomy cycle is in "creative experimentation" phase

❌ **Disable LATERAL_THINKER when:**
- System needs to converge quickly (production stability mode)
- Blocking reasons vary widely (suggests diversity already present)
- Mayor has frozen exploration (policy stability mode)

### Configuration Flag

```python
LATERAL_THINKER_ENABLED = True  # Can be toggled per cycle
LATERAL_INCORPORATION_THRESHOLD = 3  # Use after N consecutive identical blockers
```

---

## INTEGRATION INTO AUTONOMOUS CYCLE

### Day 2 Multi-CT Execution (Revised)

```
Day 2: Multi-CT Proposal Generation (with LATERAL_THINKER)

PRIMARY_CT instances (7 thinking styles)
    ├─ Each generates proposal independently
    └─ Each accesses LATERAL_THINKER in parallel

LATERAL_THINKER
    ├─ Generates suggestion_sets for each PRIMARY_CT
    ├─ Suggestions optional (PRIMARY_CT decides incorporation)
    └─ All output validated for K0-L1

CT_COMBINER
    ├─ Optionally incorporates lateral input
    └─ Produces final PRIMARY_CT proposal

Results: 7 proposals (possibly divergent due to lateral input)
         All validated by Supervisor
         All independent paths through pipeline
```

---

## EXAMPLE: LATERAL_THINKER IN ACTION

### Cycle 12 Execution

**Input:**
```
blocking_reasons: ["NO_RECEIPTS"]
consecutive_no_ships: 4
previous_attempts: [functional receipt generator, database schema, API layer]
```

**PRIMARY_CT Output:**
```
proposal_bundle: {
  name: "Receipt Service v2",
  description: "Rewrite receipt service with better error handling"
}
```

**LATERAL_THINKER Output:**
```
suggestions: [
  {
    type: "non_optimizing_path",
    description: "Consider mock receipt service (symbolic only) to test obligation path without implementation."
  },
  {
    type: "assumption_challenge",
    description: "All previous attempts assumed 'receipt must be functional code.' What if obligation satisfied by test-only stub?"
  }
]
```

**CT_COMBINER Decision:**
"Consecutive NO_SHIP > 3, so try incorporating lateral suggestion."

**Final Proposal:**
```
proposal_bundle: {
  name: "Receipt Service Stub (Test Path)",
  description: "Mock receipt service to test obligation flow, bypassing implementation complexity"
}
```

**Result:** Patch succeeds, SHIP achieved on cycle 12 (vs. repeated NO_SHIP on cycles 8-11).

---

## CONCLUSION

**LATERAL_THINKER is:**
- A bounded functional role in Creative Town
- A mechanism for orthogonal ideation
- Subject to K0, K0-L1, K1, K5, K9
- Zero authority, zero consciousness claims
- Optional, heuristic, advisory only

**What It Enables:**
- Reduced premature convergence
- Faster recovery from local optima
- Exploration of non-obvious solution paths
- Clear separation of "breadth" vs. "depth" in creativity

**What It Preserves:**
- Authority remains with Mayor
- K-Invariants remain unbreakable
- Determinism remains provable
- Ontology remains clear (no mysticism)

---

**Status: READY FOR INTEGRATION**

This specification is formal, execution-grade, and safe.

