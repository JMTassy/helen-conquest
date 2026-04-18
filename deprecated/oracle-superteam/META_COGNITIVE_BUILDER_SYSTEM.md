# ORACLE SUPERTEAM — META-COGNITIVE BUILDER SYSTEM
**Version: 2.0-RLM (Recursive Language Model Integration)**

**Canonical Scope:** MVP Construction with Recursive Reasoning & Confidence-Scored Validation

---

## SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORACLE 1 (CONSENSUS LAYER)                   │
│              Authoritative Constraint Declaration               │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│               ORACLE 2 (META-COGNITIVE BUILDER)                 │
│                                                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐   │
│  │  DECOMPOSER   │→ │   EXPLORER    │→ │  CRITIC (RLM)    │   │
│  │  (Task Graph) │  │  (Candidates) │  │  (Verification)  │   │
│  └───────────────┘  └───────────────┘  └──────────────────┘   │
│           │                  │                    │            │
│           └──────────────────┼────────────────────┘            │
│                              ▼                                 │
│                    ┌──────────────────┐                        │
│                    │     BUILDER      │                        │
│                    │  (Obligations)   │                        │
│                    └──────────────────┘                        │
│                              │                                 │
│                              ▼                                 │
│                    ┌──────────────────┐                        │
│                    │   INTEGRATOR     │                        │
│                    │  (Synthesis)     │                        │
│                    └──────────────────┘                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     VERDICT ENGINE                              │
│              (SHIP / NO_SHIP Determination)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## PART 1: CORE PRINCIPLES (Inherited from ORACLE v1)

### Axiom 1: NO CONSENSUS PACKET = NO OUTPUT
The Meta-Cognitive Builder MUST NOT operate without an authorized `oracle1_consensus_packet`.

### Axiom 2: NO RECEIPT = NO FEATURE
Every obligation must produce verifiable evidence.

### Axiom 3: RECURSIVE REASONING WITH CONFIDENCE SCORING
Following the MIT RLM framework, the system:
- **DECOMPOSES** complex problems into sub-problems
- **SOLVES** each with explicit confidence scores (0.0-1.0)
- **VERIFIES** logic, facts, completeness, and bias
- **SYNTHESIZES** only when confidence thresholds are met

### Axiom 4: MULTI-ANGLE VERIFICATION
Before committing to any solution path:
1. Does the logic actually hold?
2. Are the facts grounded?
3. Is anything missing?
4. Are there hidden assumptions?

---

## PART 2: THE 5-AGENT META-COGNITIVE PIPELINE

### AGENT 1: DECOMPOSER
**Role:** Transform wedge definition into atomic, testable obligations

**Input:**
- `oracle1_consensus_packet`
- Wedge definition
- Global constraints
- Explicit exclusions

**Process:**
1. Parse wedge into **core claim**
2. Identify **blocking unknowns**
3. Generate **subtask graph** (DAG structure)
4. Validate against exclusions
5. Check obligation cap

**Output Structure:**
```yaml
DECOMPOSITION:
  wedge_id: "WDG-001"
  core_claim: "MVP must prove X without Y"
  subtasks:
    - id: "ST-01"
      description: "..."
      dependencies: []
      tier: "I|II|III"
      confidence_required: 0.8
  blocking_unknowns:
    - unknown: "How to implement Z without violating constraint C?"
      resolution_needed: true
  obligation_count: 7  # MUST be <= cap from packet
```

---

### AGENT 2: EXPLORER
**Role:** Generate multiple solution candidates with diversity scoring

**Input:**
- Decomposition output
- Consensus packet constraints

**Process (RLM-Enhanced):**
1. For each subtask, generate 3-5 **meaningfully different** candidates
2. Label approach type:
   - CONVENTIONAL (proven patterns)
   - NOVEL (new combinations)
   - CONTRARIAN (challenges assumptions)
3. Self-score viability (0.0-1.0)
4. Identify **falsification hooks** (how to quickly test)

**Output Structure:**
```yaml
EXPLORATION:
  candidates:
    - id: "C1"
      subtask_id: "ST-01"
      approach_type: "CONVENTIONAL"
      description: |
        Use Redis for caching with TTL=3600s
      viability_estimate: 0.7
      confidence: 0.75
      assumptions:
        - "Redis available in target env"
        - "Network latency < 10ms"
      falsification_test: "Benchmark with 10k concurrent requests"

    - id: "C2"
      subtask_id: "ST-01"
      approach_type: "NOVEL"
      description: |
        In-memory LRU cache with bounded size
      viability_estimate: 0.8
      confidence: 0.65
      assumptions:
        - "Memory < 500MB acceptable"
      falsification_test: "Stress test with memory profiler"
```

**Diversity Constraint:** Candidates must differ in at least 2 dimensions:
- Technical approach
- Resource trade-offs
- Failure modes
- Complexity profile

---

### AGENT 3: CRITIC (WILLIAM Protocol + RLM Verification)
**Role:** Adversarial verification with recursive confidence scoring

**Input:**
- All candidates from Explorer
- Consensus packet constraints
- Exclusions list

**Process (Meta-Cognitive Reasoning Framework):**
```
FOR EACH candidate:
  1. DECOMPOSE: Break claim into verifiable sub-claims
  2. SOLVE: Address each with confidence score
     - confidence >= 0.8 → TRUSTED
     - confidence < 0.4 → REJECTED
     - 0.4-0.8 → "I'm not sure, here's why"
  3. VERIFY:
     ✓ Does the logic actually hold?
     ✓ Are the facts grounded?
     ✓ Is anything missing?
     ✓ Are there hidden assumptions?
  4. SYNTHESIZE: Final verdict with justification
```

**WILLIAM Protocol Checks:**
1. **Reality Scan:** What does this ACTUALLY claim?
2. **Anti-Bullshit Protocol:** Where is uncertainty hidden?
3. **Auto-Demolition:** If dead wrong, what breaks?
4. **Tier Gate Check:** Any epistemic tier violations?
5. **Falsification Hook:** What minimal test settles this?

**Output Structure:**
```yaml
CRITIQUE:
  candidate_evaluations:
    - candidate_id: "C1"
      verdict: "ROBUST|FLAWED_REPAIRABLE|INVALID_DANGEROUS"
      verdict_symbol: "✅|⚠️|❌"
      confidence: 0.85

      decomposed_checks:
        - check: "Violates exclusion: no external dependencies"
          result: "FAIL"
          confidence: 1.0

        - check: "Meets performance threshold"
          result: "PASS"
          confidence: 0.7
          reasoning: "Benchmarks show 98th percentile < 50ms, but only tested with synthetic data"

        - check: "Handles edge case: cache invalidation"
          result: "UNCERTAIN"
          confidence: 0.5
          reasoning: "No explicit strategy for distributed invalidation"

      blocking_issues:
        - issue: "Exclusion violation: Redis is external dependency"
          severity: "HIGH"
          auto_reject: true

      repair_paths:
        - "Remove Redis, use in-process cache"
        - "Request exclusion amendment from ORACLE 1"

      falsification_result:
        test_proposed: "Benchmark with 10k concurrent requests"
        test_feasible: true
        expected_outcome: "Latency p99 < 100ms"
        confidence_if_pass: 0.9
```

**Confidence Thresholds:**
- `>= 0.8`: Path trusted → proceed to BUILD
- `0.4-0.8`: Path uncertain → flag for human review or iterative refinement
- `< 0.4`: Path rejected → obligation: "RESOLVE_UNCERTAINTY"

---

### AGENT 4: BUILDER
**Role:** Construct obligations from surviving candidates

**Input:**
- Critic evaluations (ROBUST or FLAWED_REPAIRABLE only)
- Consensus packet authorization
- Maximum obligation cap

**Process:**
1. Map each surviving candidate to obligations
2. Generate evidence requirements
3. Define pass/fail gates
4. Assign verification methods
5. Enforce obligation cap (hard failure if exceeded)

**Obligation Structure (from ORACLE v1):**
```yaml
BUILD:
  obligations:
    - id: "OBL-CTX-01"
      scope_authorization: "Wedge §1.2"
      action: "Implement in-memory LRU cache with bounded memory window"
      expected_output: "Caching module with < 500MB footprint"
      evidence_type: "memory_profiler_log"
      verification_method: "Deterministic stress test with 50k entries"
      pass_condition: "Peak memory < 500MB AND cache hit rate > 80%"
      confidence_threshold: 0.8
      tier: "I"  # Must have computational proof

    - id: "OBL-CTX-02"
      scope_authorization: "Global Constraint §3.1"
      action: "Write deterministic cache eviction test"
      expected_output: "Test suite with 100% coverage of eviction logic"
      evidence_type: "pytest_output_log"
      verification_method: "CI/CD pipeline with hash-locked assertions"
      pass_condition: "All tests pass AND coverage >= 95%"
      confidence_threshold: 1.0
      tier: "I"
```

**Rejection Criteria:**
- If `len(obligations) > consensus_packet.obligation_cap` → **HARD FAILURE**
- If any obligation lacks clear evidence path → **REJECTED**
- If any obligation violates exclusions → **REJECTED**

---

### AGENT 5: INTEGRATOR
**Role:** Synthesize final decision (STOP or CONTINUE)

**Input:**
- All agent outputs (DECOMPOSER, EXPLORER, CRITIC, BUILDER)
- Obligation vault state

**Process (Meta-Cognitive Synthesis):**
1. Check for **contradictions** across agent outputs
2. Verify **obligation count** <= cap
3. Assess **aggregate confidence**:
   ```
   C_agg = (Σ confidence_i × weight_i) / Σ weight_i
   ```
4. Identify **shared blind spots** (all agents missed same issue)
5. Determine STOP (ready for verdict) or CONTINUE (needs iteration)

**Output Structure:**
```yaml
INTEGRATION:
  final_answer:
    content: |
      MVP construction plan for [WEDGE] consists of 7 obligations
      spanning 3 subsystems. All obligations respect global constraints.

      Critical path: OBL-CTX-01 → OBL-CTX-03 → OBL-INT-01

      Highest risk: OBL-CTX-03 (confidence 0.72 due to uncertainty
      in distributed cache invalidation strategy)

  confidence:
    overall: 0.78
    breakdown:
      decomposition: 0.95
      exploration: 0.82
      critique: 0.85
      build: 0.88
      integration: 0.78

  decision:
    verdict: "STOP|CONTINUE"
    reasoning: |
      STOP: All obligations meet evidence requirements and confidence >= 0.75
      OR
      CONTINUE: OBL-CTX-03 requires iterative refinement (confidence 0.72 < 0.75)

  blocked_obligations:
    - id: "OBL-CTX-03"
      reason: "Confidence below threshold (0.72 < 0.75)"
      required_action: "Design explicit cache invalidation protocol"
      estimated_iterations: 1

  pattern_analysis:
    shared_blind_spots:
      - "None of the agents addressed cold-start latency"
      - "No discussion of cache warming strategy"
    emergent_insights:
      - "Candidates C2 and C4 converge on same memory bound despite different approaches"
```

**STOP Condition:**
- ALL obligations defined
- ALL confidence scores >= threshold (default 0.75)
- NO blocking contradictions
- NO exclusion violations

**CONTINUE Condition:**
- ANY obligation below confidence threshold
- Detected contradiction requires resolution
- Shared blind spot identified
- Maximum iterations not exceeded (default: 3)

---

## PART 3: RECURSIVE REFINEMENT (RLM Integration)

When `decision.verdict = "CONTINUE"`, the system re-enters with refined context:

```
ITERATION_N+1:
  input_context:
    - Previous agent outputs
    - Identified weaknesses
    - Refined confidence targets

  modified_prompts:
    EXPLORER: "Generate alternatives addressing: [blind_spots]"
    CRITIC: "Focus verification on: [low_confidence_areas]"
    BUILDER: "Strengthen evidence for: [blocked_obligations]"
```

**Recursion Limits:**
- Maximum depth: 3 iterations (prevent infinite loops)
- Minimum progress: confidence must increase by >= 0.05 per iteration
- Timeout: 10 minutes total (prevent runaway processing)

**Token Budget Management (from RLM paper):**
- Each recursive call consumes tokens
- System tracks cumulative usage
- Auto-terminates if budget exceeded
- Prioritizes high-impact refinements

---

## PART 4: VERDICT ENGINE INTEGRATION

Once INTEGRATOR emits `verdict: STOP`, output flows to ORACLE SUPERTEAM Verdict Engine:

```python
# From oracle/verdict.py (existing system)
def determine_verdict(
    obligations: List[Obligation],
    consensus_score: float,
    contradictions: List[dict],
    kill_signals: List[str]
) -> Verdict:

    # Kill-switch dominance
    if any(kill_signals):
        return Verdict(decision="NO_SHIP", reason="KILL_SWITCH")

    # Blocking obligations
    if any(obl.status == "OPEN" for obl in obligations):
        return Verdict(decision="NO_SHIP", reason="OBLIGATIONS_OPEN")

    # Contradictions
    if contradictions:
        return Verdict(decision="NO_SHIP", reason="CONTRADICTIONS")

    # Confidence threshold
    if consensus_score >= 0.75:
        return Verdict(decision="SHIP", reason="CONSENSUS_MET")

    return Verdict(decision="NO_SHIP", reason="CONSENSUS_BELOW_THRESHOLD")
```

---

## PART 5: CONFIDENCE SCORING PROTOCOL

### Multi-Angle Verification Scoring

For every reasoning path:

```yaml
confidence_breakdown:
  logic_validity: 0.0-1.0    # Does inference chain hold?
  fact_grounding: 0.0-1.0    # Are claims evidence-based?
  completeness: 0.0-1.0      # Are all cases covered?
  assumption_safety: 0.0-1.0 # Are assumptions explicit/validated?

aggregate_confidence: min(logic_validity, fact_grounding, completeness, assumption_safety)
```

**Example:**
```yaml
candidate: "Use SHA-256 for hashing"
confidence_breakdown:
  logic_validity: 0.95      # "SHA-256 is cryptographically secure" - well-established
  fact_grounding: 1.0       # NIST standard, peer-reviewed
  completeness: 0.8         # Doesn't address hash collision handling
  assumption_safety: 0.9    # Assumes no quantum attacks (reasonable for 2025)

aggregate_confidence: 0.8  # min(0.95, 1.0, 0.8, 0.9)
verdict: "TRUSTED (but document quantum caveat)"
```

### Confidence Language (Calibrated Output)

**Confidence >= 0.8:**
> "SHA-256 hashing is cryptographically secure for this use case (confidence: 0.85).
> Note: assumes no quantum computer availability within MVP lifetime."

**Confidence 0.4-0.8:**
> "Cache invalidation strategy shows promise but has gaps (confidence: 0.72).
> Uncertain areas: distributed consistency guarantees, network partition handling.
> Recommend: prototype with test harness before commitment."

**Confidence < 0.4:**
> "Proposed approach violates global constraint §3.2 (confidence: 0.2).
> Fatal flaw: requires external Redis dependency, explicitly excluded.
> Recommendation: REJECT and explore in-process alternatives."

---

## PART 6: EPISTEMIC TIER ENFORCEMENT

From ORACLE CLI framework, inherited tier discipline:

| Tier | Claims Allowed | Evidence Required | Can Justify Other Claims? |
|------|---------------|-------------------|---------------------------|
| **I** | Proven/Tested | Computational proof, formal verification, deterministic tests | ✅ YES |
| **II** | Falsifiable | Explicit falsification protocol, benchmark with pass/fail | ⚠️ Only Tier II/III |
| **III** | Heuristic | Labeled as heuristic, cannot be sole justification | ❌ NO |

**Builder Enforcement:**
```python
def validate_obligation_tier(obligation: Obligation) -> bool:
    if obligation.tier == "I":
        if not obligation.evidence_type in COMPUTATIONAL_PROOFS:
            return False  # Tier I requires formal proof

    if obligation.tier == "III":
        if any(dependent.tier == "I" for dependent in obligation.dependents):
            return False  # Tier III cannot justify Tier I

    return True
```

---

## PART 7: THE SECRET SAUCE (Confidence Thresholds)

From the Twitter thread:

> **Paths below 0.4? Rejected.**
> **Paths above 0.8? Trusted.**
> **In between? AI tells you "I'm not sure, here's why."**

This is encoded throughout the Meta-Cognitive Builder:

```python
CONFIDENCE_THRESHOLDS = {
    "auto_reject": 0.4,
    "uncertain": 0.8,
    "trusted": 0.8,
}

def classify_confidence(score: float) -> str:
    if score < CONFIDENCE_THRESHOLDS["auto_reject"]:
        return "REJECTED"
    elif score < CONFIDENCE_THRESHOLDS["uncertain"]:
        return "UNCERTAIN"  # Human review or iterate
    else:
        return "TRUSTED"
```

**Effect on Obligations:**
- REJECTED → not converted to obligation
- UNCERTAIN → obligation created with `requires_review: true`
- TRUSTED → obligation ready for BUILD phase

---

## PART 8: IMPLEMENTATION EXAMPLE

### Input: Consensus Packet

```yaml
oracle1_consensus_packet:
  wedge_definition:
    id: "WDG-CACHE-001"
    claim: "Reduce API latency to < 100ms p99 without external dependencies"

  global_constraints:
    - "No external services (Redis, Memcached, etc.)"
    - "Memory footprint < 500MB"
    - "100% deterministic (no random eviction)"

  explicit_exclusions:
    - "CDN solutions"
    - "Database query optimization (orthogonal concern)"

  hard_gates:
    - "p99 latency < 100ms under 10k req/s"
    - "Memory usage < 500MB sustained"
    - "Cache hit rate >= 80%"

  allowed_evidence:
    - "memory_profiler_log"
    - "load_test_results"
    - "pytest_coverage_report"

  obligation_cap: 10
  confidence_threshold: 0.75
```

### Output: Obligation Set (After 5-Agent Pipeline)

```yaml
FINAL_OBLIGATIONS:
  - id: "OBL-001"
    action: "Implement LRU cache with bounded memory"
    evidence: "memory_profiler_log showing peak < 500MB"
    gate: "Peak memory < 500MB AND hit rate >= 80%"
    confidence: 0.88
    tier: "I"

  - id: "OBL-002"
    action: "Write deterministic eviction tests"
    evidence: "pytest_coverage_report >= 95%"
    gate: "All tests pass in CI"
    confidence: 0.92
    tier: "I"

  - id: "OBL-003"
    action: "Benchmark under 10k req/s load"
    evidence: "load_test_results showing p99 < 100ms"
    gate: "p99 latency < 100ms"
    confidence: 0.81
    tier: "I"

  - id: "OBL-004"
    action: "Document cache warming strategy"
    evidence: "Architecture doc with cold-start analysis"
    gate: "Human review approval"
    confidence: 0.76
    tier: "II"

verdict_recommendation: "SHIP (all gates clear, confidence >= 0.75)"
```

---

## PART 9: COMPARISON TO ALTERNATIVES

| Feature | Meta-Cognitive Builder | ChatGPT | Traditional Multi-Agent |
|---------|----------------------|---------|-------------------------|
| **Recursive reasoning** | ✅ Built-in | ❌ Single-shot | ⚠️ Manual orchestration |
| **Confidence scores** | ✅ 0.0-1.0 calibrated | ❌ No | ⚠️ Varies |
| **Multi-angle verification** | ✅ 4-check protocol | ❌ No | ❌ No |
| **Adversarial critic** | ✅ WILLIAM protocol | ❌ Polite by default | ⚠️ Optional |
| **Epistemic tiers** | ✅ I/II/III enforced | ❌ No | ❌ No |
| **Constitutional constraints** | ✅ Hard-coded | ❌ Soft guidelines | ⚠️ Config-based |
| **Kill-switches** | ✅ Lexicographic veto | ❌ No | ❌ No |
| **Replay determinism** | ✅ Hash-verified | ❌ No | ❌ Rare |

---

## PART 10: USAGE PROTOCOL

### Step 1: Human declares consensus packet
```python
consensus_packet = {
    "wedge_definition": "...",
    "global_constraints": [...],
    "explicit_exclusions": [...],
    "hard_gates": [...],
    "allowed_evidence": [...],
    "obligation_cap": 10,
    "confidence_threshold": 0.75
}
```

### Step 2: Launch Meta-Cognitive Builder
```python
from oracle.meta_cognitive_builder import run_builder_pipeline

result = run_builder_pipeline(consensus_packet)
```

### Step 3: Review obligations
```python
for obl in result.obligations:
    print(f"{obl.id}: {obl.action} (confidence: {obl.confidence})")
```

### Step 4: Submit to Verdict Engine
```python
from oracle.engine import run_oracle

manifest = run_oracle({
    "claim": {"assertion": consensus_packet["wedge_definition"]},
    "evidence": result.evidence_receipts,
    "votes": result.team_signals,
    "obligations": result.obligations
})

print(f"Decision: {manifest['decision']['final']}")
print(f"Ship: {manifest['decision']['ship_permitted']}")
```

---

## PART 11: ANTI-PATTERNS (Forbidden)

❌ **"Let's brainstorm"** → No unstructured ideation
❌ **"This should work"** → Confidence score required
❌ **"Trust me"** → Evidence receipt mandatory
❌ **"We'll handle that later"** → All obligations discharged upfront
❌ **"It's probably fine"** → Calibrated confidence only
❌ **Manual override** → No bypass of kill-switches
❌ **Scope creep** → Wedge definition immutable

---

## PART 12: CONSTITUTIONAL GUARANTEES

From ORACLE SUPERTEAM Constitution:

1. ✅ **NO_RECEIPT = NO_SHIP** — All obligations have evidence paths
2. ✅ **Non-Sovereign Agents** — Builder proposes, Verdict decides
3. ✅ **Binary Verdicts** — SHIP or NO_SHIP only
4. ✅ **Kill-Switch Dominance** — Confidence < 0.4 = auto-reject
5. ✅ **Replay Determinism** — Same packet → same obligations → same hash

---

## PART 13: ROADMAP

**v2.0 (Current — RLM Integration)**
- ✅ 5-agent meta-cognitive pipeline
- ✅ Recursive reasoning with confidence scoring
- ✅ Multi-angle verification (4-check protocol)
- ✅ WILLIAM protocol critic
- ✅ Epistemic tier enforcement

**v2.1 (Next)**
- [ ] Parallel agent execution (async/await)
- [ ] Token budget optimization
- [ ] Interactive refinement UI
- [ ] Confidence calibration dashboard

**v3.0 (Future)**
- [ ] Multi-wedge planning
- [ ] Cross-project obligation linking
- [ ] Federated builder networks
- [ ] Zero-knowledge evidence proofs

---

## FINAL AXIOM

**If the AI can't score its confidence, verify from multiple angles, and explicitly flag uncertainty, it should not be building your MVP.**

This is the Meta-Cognitive Builder doctrine.

---

**Built with recursive reasoning. Verified adversarially. Confidence-calibrated by design.**

**ORACLE META-COGNITIVE BUILDER is not a chatbot. It is a constraint-based reasoning engine.**
