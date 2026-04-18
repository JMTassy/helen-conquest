# ORACLE META-COGNITIVE BUILDER — Quick Start Guide

**Version 2.0-RLM** | Recursive Reasoning + Confidence Scoring + Multi-Angle Verification

---

## What This Is

The **Meta-Cognitive Builder** is a 5-agent system that transforms high-level product goals (wedges) into verifiable, evidence-backed obligations using:

1. **Recursive reasoning** (from MIT's RLM paper)
2. **Confidence scoring** (0.0-1.0 calibrated)
3. **Multi-angle verification** (logic, facts, completeness, assumptions)
4. **Adversarial critique** (WILLIAM protocol)
5. **Constitutional constraints** (from ORACLE SUPERTEAM v1)

**This is NOT:**
- A chatbot
- A brainstorming tool
- A "wise AI" making subjective judgments

**This IS:**
- A constraint-based reasoning engine
- An evidence-first obligation generator
- A confidence-calibrated decision system

---

## Installation

```bash
# Navigate to oracle-superteam directory
cd oracle-superteam

# No dependencies required — pure Python 3.8+
python3 meta_cognitive_builder.py
```

---

## 5-Minute Demo

### Step 1: Define Your Wedge (Consensus Packet)

```python
from meta_cognitive_builder import ConsensusPacket, run_builder_pipeline

# Your MVP goal as a consensus packet
packet = ConsensusPacket(
    wedge_definition={
        "id": "WDG-AUTH-001",
        "claim": "Add user authentication without external auth providers"
    },
    global_constraints=[
        "No OAuth providers (Google, Facebook, etc.)",
        "No external identity services",
        "Must support email + password",
        "Session lifetime < 24 hours"
    ],
    explicit_exclusions=[
        "Biometric authentication",
        "Social login",
        "Magic links"
    ],
    hard_gates=[
        "Login response time < 200ms",
        "Password hashing uses bcrypt or stronger",
        "SQL injection protected"
    ],
    allowed_evidence=[
        "security_audit_log",
        "load_test_results",
        "pytest_coverage_report"
    ],
    obligation_cap=12,
    confidence_threshold=0.75
)
```

### Step 2: Run the Pipeline

```python
result = run_builder_pipeline(packet, max_iterations=3)
```

**What happens:**
1. **DECOMPOSER** breaks wedge into subtasks
2. **EXPLORER** generates 3-5 solution candidates per subtask
3. **CRITIC** applies WILLIAM protocol + confidence scoring
4. **BUILDER** converts surviving candidates to obligations
5. **INTEGRATOR** synthesizes final decision (STOP/CONTINUE)

### Step 3: Review Results

```python
print(f"Verdict: {result.integration.verdict}")
print(f"Overall Confidence: {result.integration.confidence_overall:.2f}")
print(f"\nObligations ({len(result.obligations)}):")

for obl in result.obligations:
    print(f"  [{obl.confidence:.2f}] {obl.id}: {obl.action}")
    print(f"           Evidence: {obl.evidence_type}")
    print(f"           Gate: {obl.pass_condition}\n")
```

**Example Output:**
```
Verdict: STOP
Overall Confidence: 0.82

Obligations (8):
  [0.85] OBL-ST-01-C1: Design JWT-based session system
           Evidence: security_audit_log
           Gate: No critical vulnerabilities found

  [0.90] OBL-ST-02-C3: Implement bcrypt password hashing
           Evidence: pytest_coverage_report
           Gate: 100% test coverage on auth module

  [0.78] OBL-ST-03-C5: Add rate limiting (10 attempts/minute)
           Evidence: load_test_results
           Gate: Rate limiter blocks > 10 req/min per IP
```

---

## Understanding Confidence Scores

The system uses **calibrated confidence scoring** (from MIT RLM paper + Twitter thread):

| Score Range | Classification | Meaning | System Action |
|-------------|---------------|---------|---------------|
| **< 0.4** | REJECTED | Fatal flaws, contradictions, or exclusion violations | Candidate rejected |
| **0.4-0.8** | UNCERTAIN | Promising but has gaps or unknowns | Flag for review or iterate |
| **≥ 0.8** | TRUSTED | High confidence, ready to build | Convert to obligation |

**Key Insight:**
> "Paths below 0.4? Rejected. Paths above 0.8? Trusted. In between? AI tells you 'I'm not sure, here's why.'" — [@godofprompt](https://twitter.com/godofprompt)

---

## Multi-Angle Verification (4-Check Protocol)

Every solution candidate is evaluated on **4 dimensions**:

1. **Logic Validity** — Does the inference chain hold?
2. **Fact Grounding** — Are claims evidence-based?
3. **Completeness** — Are all edge cases covered?
4. **Assumption Safety** — Are assumptions explicit and validated?

**Aggregate confidence = MIN(all 4 scores)** (most conservative)

**Example:**
```yaml
Candidate: "Use SHA-256 for hashing user IDs"

Confidence Breakdown:
  logic_validity: 0.95   # SHA-256 is cryptographically secure (well-known)
  fact_grounding: 1.0    # NIST standard, peer-reviewed
  completeness: 0.8      # Doesn't address collision handling
  assumption_safety: 0.9 # Assumes no quantum attacks (reasonable for 2025)

Aggregate: 0.8 (min of all scores)

Verdict: TRUSTED (but document quantum caveat)
```

---

## Epistemic Tiers (Evidence Discipline)

All obligations are labeled with **epistemic tiers**:

| Tier | Claims Allowed | Evidence Required | Can Justify Others? |
|------|---------------|-------------------|---------------------|
| **I** | Proven/Tested | Computational proof, formal verification, deterministic tests | ✅ YES |
| **II** | Falsifiable | Explicit falsification protocol, benchmark with pass/fail | ⚠️ Only II/III |
| **III** | Heuristic | Labeled as heuristic, cannot be sole justification | ❌ NO |

**Example:**
```python
Obligation(
    id="OBL-001",
    action="Implement bcrypt password hashing with salt rounds=12",
    evidence_type="pytest_coverage_report",  # Tier I evidence
    tier=EpistemicTier.TIER_I,               # Provable via tests
    confidence=0.92
)
```

**Rule:**
- Tier III (heuristic) claims **cannot** justify Tier I (proven) obligations
- Tier I requires **computational proof** (formal verification, deterministic tests)

---

## WILLIAM Protocol (Adversarial Critique)

The **CRITIC** agent applies the WILLIAM doctrine:

1. **Reality Scan** — What does this ACTUALLY claim?
2. **Anti-Bullshit Protocol** — Where is uncertainty hidden?
3. **Auto-Demolition** — If dead wrong, what breaks?
4. **Tier Gate Check** — Any epistemic tier violations?
5. **Falsification Hook** — What minimal test settles this?

**Example Output:**
```yaml
Candidate: "Use Redis for caching"

WILLIAM Verdict: INVALID_DANGEROUS
Blocking Issue: "Violates exclusion: 'No external services'"
Confidence: 0.2
Repair Path: "Remove Redis, use in-process LRU cache instead"
```

---

## Recursive Refinement

If the INTEGRATOR returns `verdict: CONTINUE`, the system **automatically iterates**:

```
Iteration 1:
  - Generate initial candidates
  - Confidence: 0.72 (below threshold 0.75)
  - Verdict: CONTINUE

Iteration 2:
  - Refine low-confidence areas
  - Add evidence for gaps
  - Confidence: 0.81 (above threshold)
  - Verdict: STOP ✅
```

**Recursion Limits:**
- Max iterations: 3 (prevent infinite loops)
- Min progress: +0.05 confidence per iteration
- Timeout: 10 minutes total

---

## Integration with ORACLE SUPERTEAM v1

Once obligations are generated, they flow into the **Verdict Engine**:

```python
from oracle.engine import run_oracle

# Convert builder output to ORACLE format
manifest = run_oracle({
    "claim": {
        "assertion": packet.wedge_definition["claim"],
        "tier": "Tier I"
    },
    "evidence": result.evidence_receipts,
    "votes": result.team_signals,
    "obligations": [
        {
            "type": obl.id,
            "status": obl.status,
            "rationale": obl.action
        }
        for obl in result.obligations
    ]
})

print(f"Final Decision: {manifest['decision']['final']}")
print(f"Ship Permitted: {manifest['decision']['ship_permitted']}")
```

**Verdict Rules (from ORACLE v1):**
```
IF kill_switch_triggered → NO_SHIP
ELSE IF obligations.any(status="OPEN") → NO_SHIP
ELSE IF contradictions → NO_SHIP
ELSE IF confidence >= 0.75 → SHIP
ELSE → NO_SHIP
```

---

## Real-World Example: API Caching

### Input Packet

```python
packet = ConsensusPacket(
    wedge_definition={
        "id": "WDG-CACHE-001",
        "claim": "Reduce API latency to < 100ms p99 without external dependencies"
    },
    global_constraints=[
        "No external services (Redis, Memcached)",
        "Memory footprint < 500MB",
        "100% deterministic (no random eviction)"
    ],
    explicit_exclusions=[
        "CDN solutions",
        "Database query optimization"  # Orthogonal concern
    ],
    hard_gates=[
        "p99 latency < 100ms under 10k req/s",
        "Memory usage < 500MB sustained",
        "Cache hit rate >= 80%"
    ],
    allowed_evidence=[
        "memory_profiler_log",
        "load_test_results",
        "pytest_coverage_report"
    ],
    obligation_cap=10,
    confidence_threshold=0.75
)
```

### Output Obligations

```yaml
OBL-001:
  action: "Implement LRU cache with bounded memory (max 500MB)"
  evidence: "memory_profiler_log showing peak < 500MB"
  gate: "Peak memory < 500MB AND hit rate >= 80%"
  confidence: 0.88
  tier: I

OBL-002:
  action: "Write deterministic eviction tests (no randomness)"
  evidence: "pytest_coverage_report >= 95%"
  gate: "All tests pass in CI with same seed → same results"
  confidence: 0.92
  tier: I

OBL-003:
  action: "Benchmark under 10k req/s load"
  evidence: "load_test_results showing p99 < 100ms"
  gate: "p99 latency < 100ms sustained for 5 minutes"
  confidence: 0.81
  tier: I

OBL-004:
  action: "Document cache warming strategy (cold-start handling)"
  evidence: "Architecture doc with analysis"
  gate: "Human review approval"
  confidence: 0.76
  tier: II
```

**Verdict:** `STOP` (all confidence >= 0.75, ready for BUILD phase)

---

## Advanced: Custom Agents

You can extend or replace any of the 5 agents:

```python
class CustomExplorer(Explorer):
    """Custom candidate generation logic"""

    @staticmethod
    def explore(decomposition: Dict, packet: ConsensusPacket) -> List[Candidate]:
        # Your custom exploration strategy
        candidates = []

        # Example: Generate candidates from templates
        for template in YOUR_TEMPLATE_LIBRARY:
            if template.matches(decomposition):
                candidates.append(
                    Candidate(
                        id=f"C-{len(candidates)}",
                        subtask_id=template.subtask_id,
                        approach_type="CONVENTIONAL",
                        description=template.instantiate(),
                        viability_estimate=0.8,
                        confidence=0.85,
                        assumptions=template.assumptions,
                        falsification_test=template.test_strategy
                    )
                )

        return candidates
```

---

## Troubleshooting

### Issue: "Generated obligations exceeds cap"

**Cause:** Too many candidates surviving critique

**Fix:**
1. Increase `obligation_cap` in consensus packet
2. Add more `explicit_exclusions` to filter candidates
3. Raise `confidence_threshold` to be more selective

### Issue: "Insufficient progress, terminating iterations"

**Cause:** Confidence not increasing between iterations

**Fix:**
1. Lower `confidence_threshold` slightly (e.g., 0.75 → 0.70)
2. Simplify `wedge_definition` (may be too ambitious)
3. Review `global_constraints` (may be over-constrained)

### Issue: All candidates marked INVALID_DANGEROUS

**Cause:** Exclusion or constraint violations

**Fix:**
1. Review `explicit_exclusions` — may be too broad
2. Check `global_constraints` for contradictions
3. Inspect CRITIC logs for specific blocking issues

---

## Best Practices

### 1. Start Simple
```python
# ✅ GOOD: Focused wedge
"Add user logout functionality"

# ❌ BAD: Vague or too broad
"Improve user experience"
```

### 2. Explicit Constraints
```python
# ✅ GOOD: Specific and verifiable
"Response time < 200ms p99"

# ❌ BAD: Qualitative or fuzzy
"Should be fast"
```

### 3. Verifiable Evidence
```python
# ✅ GOOD: Deterministic proof
"pytest_coverage_report showing 95% coverage"

# ❌ BAD: Subjective or manual
"Code looks good after review"
```

### 4. Conservative Confidence
```python
# ✅ GOOD: Calibrated and honest
confidence=0.78  # "High confidence but acknowledge gap in X"

# ❌ BAD: Overconfident
confidence=0.99  # "Basically perfect" (rarely true)
```

---

## What's Next?

### Integration Options

1. **Human Review UI** — Web interface for reviewing obligations
2. **CI/CD Pipeline** — Automated obligation execution + evidence collection
3. **ChatDev Integration** — Parallel production teams implementing obligations
4. **Receipt Verification** — Cryptographic proof of evidence

### Extensions

1. **Custom Critics** — Domain-specific verification rules
2. **LLM-Powered Agents** — Replace mock logic with Claude/GPT-4
3. **Multi-Wedge Planning** — Coordinate multiple MVP goals
4. **Token Budget Management** — Optimize recursive calls (RLM paper)

---

## FAQ

**Q: Is this deterministic like ORACLE v1?**

A: The *structure* is deterministic (same packet → same agent flow), but the *candidates* generated by LLM-powered agents will vary. Use mock mode for full determinism.

**Q: Can I use this without LLMs?**

A: Yes, current implementation uses heuristic logic. For production, replace with LLM calls (Claude, GPT-4, etc.)

**Q: What's the difference vs. ORACLE v1?**

A: ORACLE v1 = **Verdict Engine** (consensus + kill-switches)
   Meta-Cognitive Builder = **Obligation Generator** (recursive reasoning + confidence)

They're complementary — Builder feeds Verdict Engine.

**Q: How do I increase confidence scores?**

A: Add more evidence, reduce assumptions, strengthen falsification tests, or simplify the approach.

---

## Resources

- **Paper:** [Recursive Language Models (MIT)](https://arxiv.org/pdf/2512.24601)
- **Thread:** [@godofprompt on Meta-Cognitive Reasoning](https://twitter.com/godofprompt)
- **ORACLE v1:** `README.md` and `CONSTITUTION.md`
- **WILLIAM Protocol:** `ORACLE_README.md`

---

## Citation

```bibtex
@software{oracle_meta_cognitive_builder,
  title={ORACLE Meta-Cognitive Builder: Recursive Reasoning for MVP Construction},
  author={JMT Consulting},
  year={2026},
  version={2.0-RLM},
  url={https://github.com/yourusername/oracle-superteam}
}
```

---

**ORACLE META-COGNITIVE BUILDER is not a conversation. It is a constraint-based reasoning engine.**

Built with recursive reasoning. Verified adversarially. Confidence-calibrated by design.
