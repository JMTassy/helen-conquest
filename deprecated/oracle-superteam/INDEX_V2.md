# ORACLE SUPERTEAM v2.0 — Complete Index

**Version History:**
- v1.0: Constitutional governance framework (consensus voting + kill-switches)
- v2.0-RLM: Meta-cognitive builder integration (recursive reasoning + confidence scoring)

---

## Quick Navigation

### For First-Time Users
1. **Start here:** `META_COGNITIVE_SUMMARY.md` — 5-minute overview
2. **Try the demo:** `python3 meta_cognitive_builder.py`
3. **Learn to use it:** `QUICKSTART_META_COGNITIVE.md`

### For Technical Deep Dive
1. **System specification:** `META_COGNITIVE_BUILDER_SYSTEM.md`
2. **Integration analysis:** `RLM_INTEGRATION_ANALYSIS.md`
3. **Implementation:** `meta_cognitive_builder.py`

### For ORACLE v1 Users
1. **What's new:** See "v2.0 Additions" section below
2. **Migration guide:** See "Integration with v1" section
3. **Constitutional preservation:** All v1 axioms maintained

---

## Repository Structure

```
oracle-superteam/
│
├── ORACLE v1.0 (Governance Layer)
│   ├── README.md                          # v1 overview
│   ├── CONSTITUTION.md                    # Immutable axioms
│   ├── PROJECT_SUMMARY.md                 # Build status
│   ├── QUICKSTART.md                      # v1 quick start
│   │
│   ├── oracle/                            # Core engine
│   │   ├── engine.py                      # Main pipeline
│   │   ├── verdict.py                     # SHIP/NO_SHIP gate
│   │   ├── qi_int_v2.py                   # Consensus scoring
│   │   ├── adjudication.py                # Lexicographic veto
│   │   ├── obligations.py                 # Obligation types
│   │   ├── contradictions.py              # Hard-coded rules
│   │   └── ...
│   │
│   └── test_vault/                        # 10 validation scenarios
│       └── scenarios/*.json
│
├── ORACLE v2.0-RLM (Meta-Cognitive Builder)
│   ├── META_COGNITIVE_SUMMARY.md          # ⭐ START HERE
│   ├── META_COGNITIVE_BUILDER_SYSTEM.md   # Complete specification
│   ├── QUICKSTART_META_COGNITIVE.md       # Usage guide
│   ├── RLM_INTEGRATION_ANALYSIS.md        # Technical synthesis
│   ├── INDEX_V2.md                        # This file
│   │
│   └── meta_cognitive_builder.py          # Implementation
│
└── Documentation
    ├── ARCHITECTURE.md                    # System architecture (legacy)
    ├── ORACLE_README.md                   # ORACLE CLI (5-agent original)
    └── ...
```

---

## What's in Each File

### Meta-Cognitive Builder (v2.0)

| File | Lines | Purpose | Audience |
|------|-------|---------|----------|
| `META_COGNITIVE_SUMMARY.md` | ~400 | Executive overview | Everyone |
| `META_COGNITIVE_BUILDER_SYSTEM.md` | ~1300 | Complete spec | Builders, architects |
| `QUICKSTART_META_COGNITIVE.md` | ~800 | Usage guide | Developers |
| `RLM_INTEGRATION_ANALYSIS.md` | ~1000 | Technical analysis | Researchers |
| `meta_cognitive_builder.py` | ~700 | Working implementation | Developers |

### ORACLE v1 Core

| File | Lines | Purpose | Audience |
|------|-------|---------|----------|
| `README.md` | ~400 | v1 overview | Everyone |
| `CONSTITUTION.md` | ~230 | Axioms & rules | Governance |
| `PROJECT_SUMMARY.md` | ~330 | Build status | DevOps |
| `oracle/engine.py` | ~66 | Main pipeline | Developers |
| `oracle/verdict.py` | ~34 | Verdict gate | Developers |
| `ci/run_test_vault.py` | ~103 | CI runner | QA |

---

## v2.0 Additions

### New Capabilities

1. **Recursive Reasoning** (from MIT RLM)
   - Automatic task decomposition
   - Iterative refinement (max 3 cycles)
   - Token budget management

2. **Confidence Scoring** (from @godofprompt)
   - Calibrated 0.0-1.0 scores
   - Discrete thresholds (0.4 reject, 0.8 trust)
   - Multi-angle verification (4-check protocol)

3. **Meta-Cognitive Pipeline** (synthesis)
   - 5 agents: DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR
   - WILLIAM protocol (adversarial critique)
   - Epistemic tier enforcement (I/II/III)

### Architecture Changes

**v1.0 Flow:**
```
Claim → Votes → Adjudication → Verdict → Manifest
```

**v2.0 Flow:**
```
Consensus Packet → Meta-Cognitive Builder → Obligations → Verdict Engine → Manifest
                    (5-agent pipeline)              (v1 unchanged)
```

**Key Insight:**
> v2.0 is a **pre-processor** for v1. It generates the obligations that v1's Verdict Engine evaluates.

---

## Integration with v1

### Step 1: Generate Obligations (v2.0)

```python
from meta_cognitive_builder import ConsensusPacket, run_builder_pipeline

# Define wedge
packet = ConsensusPacket(
    wedge_definition={"claim": "Add user authentication"},
    global_constraints=["No external services"],
    explicit_exclusions=["OAuth"],
    hard_gates=["Login < 200ms"],
    allowed_evidence=["security_audit"],
    obligation_cap=10,
    confidence_threshold=0.75
)

# Run builder
result = run_builder_pipeline(packet)
```

### Step 2: Submit to Verdict Engine (v1)

```python
from oracle.engine import run_oracle

# Convert to v1 format
manifest = run_oracle({
    "scenario_id": "wedge-auth-001",
    "claim": {
        "id": "claim-auth",
        "assertion": packet.wedge_definition["claim"],
        "tier": "Tier I"
    },
    "evidence": [
        {"id": f"ev-{i}", "type": obl.evidence_type}
        for i, obl in enumerate(result.obligations)
    ],
    "votes": [
        {"team": "Engineering Wing", "vote": "APPROVE"},
        {"team": "Security Sector", "vote": "APPROVE"},
        {"team": "Legal Office", "vote": "APPROVE"}
    ]
})

# Check verdict
print(f"Decision: {manifest['decision']['final']}")
print(f"Ship: {manifest['decision']['ship_permitted']}")
```

### Step 3: Verify Replay (v1)

```python
from oracle.replay import verify_replay_equivalence

# Run again with same inputs
manifest2 = run_oracle({...})  # Same payload

# Should produce identical hashes
assert manifest['hashes']['outputs_hash'] == manifest2['hashes']['outputs_hash']
```

---

## Testing the Complete System

### Test 1: Meta-Cognitive Builder Only

```bash
python3 meta_cognitive_builder.py
```

**Expected:**
- 2 iterations (insufficient progress warning)
- 6 obligations generated
- 3 blocked (confidence < 0.75)
- Verdict: CONTINUE

### Test 2: ORACLE v1 Only

```bash
python3 -m ci.run_test_vault
```

**Expected:**
- 10/10 scenarios pass
- Replay determinism verified (S-08)
- All constitutional guarantees satisfied

### Test 3: Integrated Pipeline

```python
# (See "Integration with v1" above)
# Should produce manifest with:
# - Hashed inputs/outputs
# - SHIP or NO_SHIP verdict
# - Replay determinism
```

---

## Key Concepts

### From v1 (Constitutional Layer)

1. **NO_RECEIPT = NO_SHIP**
   - Every claim needs cryptographically hashable proof

2. **Non-Sovereign Agents**
   - Agents propose, cannot decide

3. **Binary Verdicts**
   - SHIP or NO_SHIP (no soft consensus)

4. **Kill-Switch Dominance**
   - Legal/Security can override anything

5. **Replay Determinism**
   - Same inputs → same outputs (hash-verified)

### From v2 (Meta-Cognitive Layer)

1. **Recursive Reasoning**
   - Problems decompose into sub-problems
   - Iterate until confidence threshold met

2. **Multi-Angle Verification**
   - 4 checks: logic, facts, completeness, assumptions
   - Aggregate = min (most conservative)

3. **Calibrated Confidence**
   - < 0.4: REJECTED
   - 0.4-0.8: UNCERTAIN
   - ≥ 0.8: TRUSTED

4. **Epistemic Tiers**
   - I: Proven (computational proof)
   - II: Falsifiable (explicit protocol)
   - III: Heuristic (labeled, limited use)

5. **WILLIAM Protocol**
   - Adversarial critique (not polite consensus)

---

## Source Papers & Threads

### Primary Sources

1. **MIT RLM Paper** (arxiv.org/pdf/2512.24601)
   - Recursive Language Models framework
   - Token budget management
   - Iterative refinement strategy

2. **@godofprompt Twitter Thread** (Jan 15, 2026)
   - Meta-cognitive reasoning framework
   - Confidence threshold protocol (0.4/0.8)
   - Multi-angle verification (4-check)

3. **ORACLE SUPERTEAM Constitution** (v1.0)
   - Constitutional constraints
   - Epistemic tier discipline
   - Kill-switch semantics

### How They Combine

```
MIT RLM:     [Recursive Decomposition] + [Iterative Refinement]
                        ↓
@godofprompt: + [Multi-Angle Verification] + [Confidence Thresholds]
                        ↓
ORACLE v1:   + [Constitutional Constraints] + [Epistemic Tiers]
                        ↓
                v2.0-RLM BUILDER
```

---

## Comparison Matrix

| Feature | v1 Only | v2 Only | v2 + v1 Integrated |
|---------|---------|---------|---------------------|
| Generate obligations | ❌ Manual | ✅ Auto (5 agents) | ✅ Auto |
| Confidence scoring | ❌ N/A | ✅ 0.0-1.0 | ✅ 0.0-1.0 |
| Multi-angle verify | ❌ N/A | ✅ 4-check | ✅ 4-check |
| Adversarial critique | ⚠️ Implicit | ✅ WILLIAM | ✅ WILLIAM |
| Constitutional limits | ✅ Hard-coded | ✅ Packet | ✅ Both |
| Consensus voting | ✅ QI-INT v2 | ❌ N/A | ✅ QI-INT v2 |
| Kill-switches | ✅ Lex veto | ⚠️ < 0.4 reject | ✅ Both |
| Replay determinism | ✅ Hash-verified | ⚠️ Structure | ✅ Hash-verified |
| Evidence receipts | ✅ Mandatory | ⚠️ Defined | ✅ Mandatory |
| Verdict engine | ✅ SHIP/NO_SHIP | ❌ N/A | ✅ SHIP/NO_SHIP |

**Legend:**
- ✅ = Full support
- ⚠️ = Partial support
- ❌ = Not applicable

---

## Use Case Matrix

| Scenario | Use v1 Only | Use v2 Only | Use v2 + v1 |
|----------|-------------|-------------|-------------|
| **Manual obligation definition** | ✅ | ❌ | ⚠️ Optional |
| **Auto obligation generation** | ❌ | ✅ | ✅ |
| **Complex MVP planning** | ❌ | ✅ | ✅ |
| **Governance review** | ✅ | ❌ | ✅ |
| **Consensus voting** | ✅ | ❌ | ✅ |
| **Kill-switch enforcement** | ✅ | ⚠️ Soft | ✅ Hard |
| **Audit trail** | ✅ | ⚠️ Run hash | ✅ Full manifest |
| **Replay verification** | ✅ | ❌ | ✅ |

**Recommendation:**
- **Research/exploration:** v2 only
- **Production governance:** v2 + v1 integrated
- **Legacy compatibility:** v1 only

---

## Performance Benchmarks

### v2.0 Meta-Cognitive Builder

| Metric | Mock Mode | LLM Mode (estimated) |
|--------|-----------|----------------------|
| **Execution time** | ~0.5s | ~60s (3 iterations) |
| **Token usage** | 0 | ~22,000 tokens |
| **Cost (Claude Sonnet 3.5)** | $0 | ~$0.05 |
| **Obligations generated** | 6 | 4-12 (varies) |
| **Confidence accuracy** | N/A (mock) | TBD (calibration needed) |

### v1 Verdict Engine

| Metric | Value |
|--------|-------|
| **Execution time** | < 100ms |
| **Determinism** | 100% (hash-verified) |
| **Test vault pass rate** | 10/10 (100%) |
| **LOC** | ~500 lines |
| **Dependencies** | 0 (pure Python) |

---

## Roadmap

### v2.1 (Q1 2026)
- [ ] LLM integration (replace mock logic)
- [ ] Human review UI for UNCERTAIN obligations
- [ ] Parallel agent execution (async/await)
- [ ] Confidence calibration dashboard

### v2.2 (Q2 2026)
- [ ] Multi-wedge coordination
- [ ] Cross-project obligation linking
- [ ] Token budget optimization
- [ ] Interactive refinement UI

### v3.0 (Q3 2026)
- [ ] Zero-knowledge evidence proofs
- [ ] Federated builder networks
- [ ] Meta-agent tuning observatory
- [ ] Cross-jurisdiction consensus

---

## Common Questions

### Q: Is this a replacement for v1?
**A:** No, v2 is a **complement** to v1. v2 generates obligations, v1 governs their acceptance.

### Q: Can I use v2 without v1?
**A:** Yes, for research and exploration. For production governance, integrate with v1.

### Q: Does v2 maintain determinism?
**A:** Structural determinism (same packet → same flow), but LLM-powered agents will vary. Use mock mode for full determinism.

### Q: How do I increase confidence scores?
**A:** Add more evidence, reduce assumptions, strengthen falsification tests, or simplify approach.

### Q: What if all candidates are rejected?
**A:** System returns `verdict: CONTINUE` with no obligations. Human must either relax constraints or abort wedge.

### Q: Can I customize the 5 agents?
**A:** Yes, subclass any agent (DECOMPOSER, EXPLORER, CRITIC, BUILDER, INTEGRATOR) and override methods.

---

## Getting Help

### Documentation
- **Quick Start:** `META_COGNITIVE_SUMMARY.md`
- **Usage Guide:** `QUICKSTART_META_COGNITIVE.md`
- **Technical Spec:** `META_COGNITIVE_BUILDER_SYSTEM.md`
- **Analysis:** `RLM_INTEGRATION_ANALYSIS.md`

### Code
- **Implementation:** `meta_cognitive_builder.py`
- **v1 Core:** `oracle/engine.py`, `oracle/verdict.py`
- **Tests:** `ci/run_test_vault.py`

### Community
- GitHub Issues: [oracle-superteam/issues]
- Discussions: [oracle-superteam/discussions]

---

## Citation

```bibtex
@software{oracle_superteam_v2,
  title={ORACLE SUPERTEAM v2.0: Meta-Cognitive Builder with Recursive Reasoning},
  author={JMT Consulting},
  year={2026},
  version={2.0-RLM},
  url={https://github.com/yourusername/oracle-superteam}
}
```

---

## Final Notes

**What this system does:**
- Transforms vague MVP goals into specific, testable obligations
- Scores confidence on every reasoning path
- Verifies from multiple angles (not just "does it work?")
- Enforces constitutional constraints
- Provides audit trail with replay determinism

**What this system does NOT do:**
- Make decisions for you (agents propose, humans decide)
- Guarantee correctness (confidence ≠ truth)
- Replace human judgment (tool, not oracle)
- Generate working code (generates obligations, not implementations)

**Key philosophy:**
> "If the AI can't score its confidence, verify from multiple angles, and explicitly flag uncertainty, it should not be building your MVP."

---

**Built with recursive reasoning. Verified adversarially. Confidence-calibrated by design.**

**ORACLE SUPERTEAM v2.0-RLM**

Status: ✅ Ready for Integration & Production Testing

---

**Document Version:** 1.0
**Last Updated:** January 16, 2026
**Maintained By:** JMT Consulting
