# POC FACTORY — Invariance-First Generativity Specification

**Version:** 1.0-IFG
**Status:** ✅ READY FOR IMPLEMENTATION
**Date:** January 16, 2026

---

## ONE-SENTENCE SUMMARY

> **POC FACTORY = Gated pipeline for reproducible capability where innovation is generated but only ships if it survives falsification, reproducibility, and invariant gates.**

---

## ARCHITECTURE: Σ–SEED DISCIPLINE FOR R&D

### State Definition

**State y:** Portfolio of POCs + artifacts

```typescript
interface POCPortfolio {
  pocs: POC[];
  artifact_registry: ArtifactRegistry;
  baseline_suite: Baseline[];
  cost_budget: CostBudget;
  viability_status: {
    in_region: boolean;
    violated_invariants: string[];
  };
}

interface POC {
  poc_id: string;
  status: "PROPOSED" | "IN_PROGRESS" | "GRADUATED" | "KILLED";
  problem_statement: ProblemStatement;
  hypothesis: string;
  minimal_solution: SolutionSpec;
  evaluation_protocol: EvaluationProtocol;  // Pre-registered
  baselines: Baseline[];
  results: Results | null;
  invariants_checklist: InvariantCheck[];
  artifacts: Artifact[];
  recommendation: "SHIP" | "ITERATE" | "KILL";
  certificate: CapabilityCertificate | null;
}
```

### Generator H

**Build Candidate POCs via Standardized Template:**

```typescript
interface Generator {
  input: {
    hypothesis: string;
    technical_target: KPI;
    constraints: Constraint[];
    budget: {
      compute_budget: number;
      time_budget: number;
    };
  };

  output: {
    candidate_poc: POC;
    evaluation_manifest: EvaluationManifest;  // Pre-registered
    baseline_comparisons: BaselineComparison[];
    artifact_bundle: Artifact[];
  };
}
```

---

## INVARIANT BUNDLE (NON-NEGOTIABLE)

### J₁: Determinism (Reproducibility)

```typescript
interface DeterminismInvariant {
  id: "J1_DETERMINISM";
  metric: "Pinned versions, fixed seeds, artifact hashes";
  threshold: {
    version_pinning_required: true;
    seed_fixed_required: true;
    hash_verification_required: true;
  };
  measurement: {
    dependencies_pinned: boolean;
    random_seeds_fixed: boolean;
    artifact_hashes_computed: boolean;
    hash_algorithm: "SHA-256";
  };
  enforcement: {
    block_on_missing_pins: true;
    block_on_floating_seeds: true;
  };
}
```

**Enforcement Checklist:**
```python
def check_determinism(poc: POC) -> InvariantCheck:
    """Verify J₁: Determinism."""
    violations = []

    # Check 1: Version pinning
    if not poc.has_pinned_dependencies():
        violations.append("FLOATING_DEPENDENCIES")

    # Check 2: Fixed seeds
    if not poc.has_fixed_seeds():
        violations.append("NON_DETERMINISTIC_SEEDS")

    # Check 3: Artifact hashes
    if not poc.has_artifact_hashes():
        violations.append("MISSING_ARTIFACT_HASHES")

    return InvariantCheck(
        invariant_id="J1_DETERMINISM",
        pass_fail=len(violations) == 0,
        violations=violations
    )
```

### J₂: Traceability (Reproducibility)

```typescript
interface TraceabilityInvariant {
  id: "J2_TRACEABILITY";
  metric: "Every metric linked to experiment manifest";
  threshold: {
    traceability_coverage: 1.0;  // 100% of metrics
  };
  measurement: {
    total_metrics: number;
    metrics_with_manifest: number;
    coverage: number;  // metrics_with_manifest / total_metrics
  };
  enforcement: {
    block_on_orphaned_metrics: true;
  };
}
```

**Traceability Schema:**
```typescript
interface MetricTrace {
  metric_name: string;
  value: number;
  manifest_link: string;  // Path to experiment manifest
  experiment_run_id: string;
  timestamp: string;
  artifact_hash: string;
  reproducible_command: string;  // Exact command to reproduce
}
```

### J₃: No Metric Laundering (Truthfulness)

```typescript
interface NoMetricLaunderingInvariant {
  id: "J3_NO_METRIC_LAUNDERING";
  metric: "Pre-registered evaluation + held-out tests";
  threshold: {
    pre_registration_required: true;
    held_out_test_required: true;
    data_leakage_score_max: 0.01;  // Near-zero tolerance
  };
  measurement: {
    evaluation_pre_registered: boolean;
    pre_registration_timestamp: string;
    held_out_test_used: boolean;
    data_leakage_detected: boolean;
    p_hacking_score: number;  // Statistical tests for p-hacking
  };
  enforcement: {
    reject_on_post_hoc_eval: true;
    reject_on_data_leakage: true;
  };
}
```

**Pre-Registration Enforcement:**
```python
def check_no_metric_laundering(poc: POC) -> InvariantCheck:
    """Verify J₃: No Metric Laundering."""
    violations = []

    # Check 1: Pre-registration
    if not poc.evaluation_protocol.pre_registered:
        violations.append("POST_HOC_EVALUATION")

    # Check 2: Pre-registration timestamp BEFORE results
    if poc.evaluation_protocol.timestamp >= poc.results.timestamp:
        violations.append("RETROACTIVE_PRE_REGISTRATION")

    # Check 3: Held-out test
    if not poc.has_held_out_test():
        violations.append("NO_HELD_OUT_TEST")

    # Check 4: Data leakage detection
    if poc.detect_data_leakage():
        violations.append("DATA_LEAKAGE_DETECTED")

    # Check 5: P-hacking detection
    if poc.compute_p_hacking_score() > 0.05:
        violations.append("P_HACKING_SUSPECTED")

    return InvariantCheck(
        invariant_id="J3_NO_METRIC_LAUNDERING",
        pass_fail=len(violations) == 0,
        violations=violations
    )
```

### J₄: Baseline Dominance (Truthfulness)

```typescript
interface BaselineDominanceInvariant {
  id: "J4_BASELINE_DOMINANCE";
  metric: "Must beat named baseline with confidence intervals";
  threshold: {
    baseline_required: true;
    confidence_interval_required: true;
    statistical_significance_alpha: 0.05;
    practical_significance_min: 0.10;  // 10% relative improvement
  };
  measurement: {
    baseline_name: string;
    baseline_performance: number;
    poc_performance: number;
    relative_improvement: number;
    confidence_interval: [number, number];
    p_value: number;
    effect_size: number;
  };
  enforcement: {
    reject_if_no_baseline: true;
    reject_if_not_statistically_significant: true;
    reject_if_not_practically_significant: true;
  };
}
```

**Baseline Comparison Protocol:**
```python
def check_baseline_dominance(poc: POC) -> InvariantCheck:
    """Verify J₄: Baseline Dominance."""
    violations = []

    # Check 1: Baseline exists
    if len(poc.baselines) == 0:
        violations.append("NO_BASELINE")
        return InvariantCheck(
            invariant_id="J4_BASELINE_DOMINANCE",
            pass_fail=False,
            violations=violations
        )

    # Check 2: Statistical significance
    for baseline in poc.baselines:
        comparison = poc.compare_to_baseline(baseline)

        if comparison.p_value >= 0.05:
            violations.append(f"NOT_STATISTICALLY_SIGNIFICANT_VS_{baseline.name}")

        # Check 3: Practical significance
        if comparison.relative_improvement < 0.10:
            violations.append(f"NOT_PRACTICALLY_SIGNIFICANT_VS_{baseline.name}")

        # Check 4: Confidence interval required
        if comparison.confidence_interval is None:
            violations.append(f"NO_CONFIDENCE_INTERVAL_VS_{baseline.name}")

    return InvariantCheck(
        invariant_id="J4_BASELINE_DOMINANCE",
        pass_fail=len(violations) == 0,
        violations=violations
    )
```

### J₅: Cost & Time (Budget Discipline)

```typescript
interface CostTimeInvariant {
  id: "J5_COST_TIME";
  metric: "Compute budget capped; cost-per-gain tracked";
  threshold: {
    compute_budget_max: number;  // Per POC
    time_budget_max_hours: number;
    cost_per_gain_max: number;  // Cost per % improvement
  };
  measurement: {
    compute_cost: number;
    time_spent_hours: number;
    performance_gain: number;
    cost_per_gain: number;  // compute_cost / performance_gain
  };
  enforcement: {
    halt_on_budget_exceeded: true;
  };
}
```

### J₆: Data Governance (Safety/Compliance)

```typescript
interface DataGovernanceInvariant {
  id: "J6_DATA_GOVERNANCE";
  metric: "Consent, retention, PII constraints";
  threshold: {
    consent_required: true;
    retention_policy_enforced: true;
    pii_detected_max: 0;
  };
  measurement: {
    consent_obtained: boolean;
    retention_policy_name: string;
    pii_scan_results: PIIScanResult[];
    gdpr_compliant: boolean;
  };
  enforcement: {
    block_on_missing_consent: true;
    block_on_pii_detected: true;
  };
  kill_switch: true;
}
```

### J₇: Operational Readiness (Deployability)

```typescript
interface OperationalReadinessInvariant {
  id: "J7_OPERATIONAL_READINESS";
  metric: "Containerized, one-command demo, rollback plan";
  threshold: {
    containerized: true;
    one_command_demo: true;
    rollback_plan: true;
    monitoring_hooks: true;
  };
  measurement: {
    has_dockerfile: boolean;
    has_demo_command: boolean;
    demo_command_tested: boolean;
    has_rollback_plan: boolean;
    has_monitoring: boolean;
  };
  enforcement: {
    block_on_missing_container: true;
    block_on_missing_rollback: true;
  };
}
```

---

## VIABILITY REGION & GATE (THE FACTORY GATE)

### Viability Region 𝒱

```python
def in_viability_region(poc: POC) -> bool:
    """Check if POC satisfies ALL invariants."""
    return all([
        poc.has_pinned_dependencies(),
        poc.has_fixed_seeds(),
        poc.has_artifact_hashes(),
        poc.has_traceability(),
        poc.evaluation_pre_registered(),
        poc.has_held_out_test(),
        poc.beats_baseline(),
        poc.compute_cost <= poc.budget.compute_budget,
        poc.has_consent(),
        poc.pii_detected == 0,
        poc.has_dockerfile(),
        poc.has_rollback_plan()
    ])
```

### Acceptance Rule (THE FACTORY GATE)

A POC "graduates" **IFF:**

```python
def graduate_poc(poc: POC) -> GraduationDecision:
    """Gate: POC graduates only if viability + certified margin + falsification."""

    # Step 1: Viability check (all invariants)
    if not in_viability_region(poc):
        return GraduationDecision(
            verdict="KILL",
            reason="VIABILITY_BREACH",
            violated_invariants=get_violations(poc)
        )

    # Step 2: Certified margin check
    margin = compute_certified_margin(poc)
    if not margin.is_certified():
        return GraduationDecision(
            verdict="ITERATE",
            reason="INSUFFICIENT_MARGIN",
            margin_needed=margin.threshold,
            margin_observed=margin.value
        )

    # Step 3: Falsification tests
    falsification_results = run_falsification_tests(poc)
    if any(test.killed_poc for test in falsification_results):
        return GraduationDecision(
            verdict="KILL",
            reason="FALSIFICATION_TEST_FAILED",
            failed_tests=falsification_results
        )

    # Step 4: Graduate with certificate
    certificate = generate_capability_certificate(poc, margin, falsification_results)
    return GraduationDecision(
        verdict="SHIP",
        reason="GRADUATED",
        certificate=certificate
    )
```

**Key Insight:** This is NOT peer review. This is experimental physics. Either you pass all gates, or you don't ship.

---

## STANDARD POC TEMPLATE (ONE PAGE)

Every POC MUST include these sections:

```markdown
# POC-{ID}: {Short Title}

## 1. Problem Statement
**Business KPI:** {metric to improve}
**Technical Target:** {specific, measurable goal}
**Baseline Performance:** {current state}

## 2. Hypothesis
{One sentence: "If we do X, then Y will improve by Z because..."}

## 3. Minimal Solution
{Simplest approach to test hypothesis}
- Implementation: {brief description}
- Dependencies: {pinned versions}
- Complexity: {O(n) / lines of code}

## 4. Evaluation Protocol (PRE-REGISTERED)
**Pre-registration timestamp:** {ISO 8601}
**Metrics:** {list}
**Test set:** {description + size}
**Held-out test:** {description}
**Statistical tests:** {t-test / Mann-Whitney / etc.}
**Alpha:** 0.05
**Practical significance threshold:** 10% relative improvement

## 5. Baselines
| Baseline | Performance | Reference |
|----------|-------------|-----------|
| {name}   | {value}     | {link}    |

## 6. Results
| Metric | Baseline | POC | Improvement | CI (95%) | p-value |
|--------|----------|-----|-------------|----------|---------|
| {name} | {value}  | {v} | {%}         | [L, U]   | {p}     |

## 7. Invariants Checklist
- [x] J₁ Determinism: Dependencies pinned, seeds fixed, hashes computed
- [x] J₂ Traceability: All metrics linked to manifests
- [x] J₃ No Metric Laundering: Evaluation pre-registered, held-out test used
- [x] J₄ Baseline Dominance: Beats baseline with p < 0.05, >10% improvement
- [x] J₅ Cost & Time: Compute cost {$X}, time {Y hours}, within budget
- [x] J₆ Data Governance: Consent obtained, no PII detected
- [x] J₇ Operational Readiness: Containerized, demo command, rollback plan

## 8. Artifacts
- Repository: {URL}
- Manifest: `manifest.json` (SHA-256: {hash})
- Reproducible command: `./run_poc.sh --seed 42`
- Container: `docker run poc-{id}:v1`
- Rollback plan: `docs/rollback.md`

## 9. Falsification Tests
| Test | Could Have Killed? | Survived? | Evidence |
|------|-------------------|-----------|----------|
| {name} | YES | YES | {log path} |

## 10. Recommendation
**Verdict:** SHIP / ITERATE / KILL
**Rationale:** {2-3 sentences}
**Certificate:** {link to capability certificate}
```

---

## FALSIFICATION TESTS (CRITICAL)

**Philosophy:** A POC must survive tests designed to kill it.

### Standard Falsification Test Suite

```typescript
interface FalsificationTest {
  test_id: string;
  name: string;
  objective: "KILL";  // Explicitly designed to falsify
  could_have_killed: boolean;  // Was this a real threat?
  survived: boolean;
  evidence_log: string;
}
```

#### Test 1: Adversarial Input
```python
def test_adversarial_input(poc: POC) -> FalsificationTest:
    """Try to break POC with adversarial inputs."""
    adversarial_inputs = generate_adversarial_inputs(poc.input_spec)
    failures = []

    for input in adversarial_inputs:
        result = poc.run(input)
        if result.crashed or result.performance_degraded > 0.20:
            failures.append(input)

    return FalsificationTest(
        name="Adversarial Input",
        could_have_killed=True,
        survived=len(failures) == 0,
        evidence_log=f"adversarial_test_{poc.id}.log"
    )
```

#### Test 2: Distribution Shift
```python
def test_distribution_shift(poc: POC) -> FalsificationTest:
    """Test POC on out-of-distribution data."""
    ood_data = generate_ood_data(poc.training_distribution)
    baseline_performance = poc.baseline.run(ood_data)
    poc_performance = poc.run(ood_data)

    performance_drop = (baseline_performance - poc_performance) / baseline_performance

    return FalsificationTest(
        name="Distribution Shift",
        could_have_killed=True,
        survived=performance_drop < 0.30,  # Max 30% degradation
        evidence_log=f"ood_test_{poc.id}.log"
    )
```

#### Test 3: Resource Exhaustion
```python
def test_resource_exhaustion(poc: POC) -> FalsificationTest:
    """Test POC under resource constraints."""
    stress_conditions = [
        {"memory_limit": "1GB", "cpu_limit": "1 core"},
        {"memory_limit": "512MB", "cpu_limit": "0.5 core"},
    ]

    failures = []
    for condition in stress_conditions:
        result = poc.run_under_constraints(condition)
        if result.crashed or result.timeout:
            failures.append(condition)

    return FalsificationTest(
        name="Resource Exhaustion",
        could_have_killed=True,
        survived=len(failures) == 0,
        evidence_log=f"resource_test_{poc.id}.log"
    )
```

#### Test 4: Baseline Parity Under Uncertainty
```python
def test_baseline_parity_uncertainty(poc: POC) -> FalsificationTest:
    """Test if POC maintains dominance with noisy inputs."""
    noisy_test_set = add_noise(poc.test_set, noise_level=0.10)
    baseline_performance = poc.baseline.run(noisy_test_set)
    poc_performance = poc.run(noisy_test_set)

    still_dominant = poc_performance > baseline_performance

    return FalsificationTest(
        name="Baseline Parity Under Uncertainty",
        could_have_killed=True,
        survived=still_dominant,
        evidence_log=f"noise_test_{poc.id}.log"
    )
```

---

## CAPABILITY CERTIFICATE (OUTPUT)

When a POC graduates, it receives a capability certificate:

```typescript
interface CapabilityCertificate {
  certificate_id: string;
  poc_id: string;
  issued_at: string;
  expires_at: string;

  technical_capability: {
    what_is_achievable: string;
    under_constraints: Constraint[];
    measured_uplift: {
      distribution: Distribution;
      confidence_interval: [number, number];
      p_value: number;
      effect_size: number;
    };
  };

  cost_curves: {
    cost_per_gain: number;
    compute_cost: number;
    time_cost_hours: number;
  };

  failure_modes: {
    mode: string;
    trigger_condition: string;
    invariant_broken: string;
    mitigation: string;
  }[];

  falsification_evidence: FalsificationTest[];

  invariants_passed: InvariantCheck[];

  artifacts: {
    repository: string;
    manifest_hash: string;
    reproducible_command: string;
    container_image: string;
  };

  signature: string;  // HMAC-SHA256
}
```

---

## MINIMAL 2-WEEK LAUNCH

### Week 1: Enforce Template + Baseline Suite

**Deliverables:**
- [ ] POC template (markdown)
- [ ] Manifest schema (JSON)
- [ ] Baseline suite (3 baselines minimum)
- [ ] CI script (checks J₁-J₇)
- [ ] Pre-registration form

**CI Script Example:**
```bash
#!/bin/bash
# ci/validate_poc.sh

POC_DIR=$1

echo "Validating POC: $POC_DIR"

# J₁: Determinism
check_pinned_dependencies "$POC_DIR/requirements.txt" || exit 1
check_fixed_seeds "$POC_DIR/src/" || exit 1
check_artifact_hashes "$POC_DIR/manifest.json" || exit 1

# J₂: Traceability
check_traceability "$POC_DIR/manifest.json" "$POC_DIR/results/" || exit 1

# J₃: No Metric Laundering
check_pre_registration "$POC_DIR/eval_protocol.json" || exit 1
check_held_out_test "$POC_DIR/manifest.json" || exit 1

# J₄: Baseline Dominance
check_baseline_comparison "$POC_DIR/results/" || exit 1

# J₅: Cost & Time
check_budget "$POC_DIR/manifest.json" || exit 1

# J₆: Data Governance
check_consent "$POC_DIR/data_governance.json" || exit 1
check_pii "$POC_DIR/data/" || exit 1

# J₇: Operational Readiness
check_dockerfile "$POC_DIR/Dockerfile" || exit 1
check_rollback_plan "$POC_DIR/docs/rollback.md" || exit 1

echo "✅ POC validation PASSED"
```

### Week 2: Run 3 POCs End-to-End + Kill at Least 1

**Goal:** Establish gate credibility by killing something.

**3 POCs:**
1. **POC-001:** Caching optimization (expected to graduate)
2. **POC-002:** ML-based recommendation (expected to iterate)
3. **POC-003:** Aggressive compression (expected to kill)

**Example Kill:**
```
POC-003: Aggressive Compression
Status: KILLED

Violation: J₄ Baseline Dominance
Reason: Compression degrades quality by 35% (p < 0.001)
Evidence: falsification_test_003.log shows unacceptable quality loss

Gate Decision: KILL
Rationale: Fails practical significance threshold (>10% degradation)
Certificate: NOT ISSUED
```

**Cultural Signal:** "We don't ship everything. The gate is real."

---

## INTEGRATION WITH ORACLE TOWN

See: `IFG_COUPLING_CONTRACT.md`

**Oracle Town sends hypothesis:**
```json
{
  "hypothesis": "Caching will reduce API latency by ≥ 15%",
  "constraints": ["Memory < 500MB", "No external services"],
  "budget": {"compute": 100, "time_hours": 40}
}
```

**POC Factory returns certificate:**
```json
{
  "capability": "Can reduce latency by 18% (CI: [14%, 22%])",
  "cost_per_gain": "$5.50 per % improvement",
  "failure_modes": [
    {"mode": "Cache stampede", "mitigation": "Staggered warmup"}
  ],
  "invariants_passed": ["J1", "J2", "J3", "J4", "J5", "J6", "J7"],
  "recommendation": "SHIP"
}
```

---

## THE "SURPRISING" ADVANTAGE

### What Most Labs Do (FAILS)

```
R&D Project:
  → Build cool demo
  → Cherry-pick best run
  → Present to stakeholders
  → "It works!"
  → No baselines, no reproducibility
  → Doesn't deploy
  → Fades away
```

### What POC Factory Does (IFG)

```
POC Pipeline:
  → Pre-register evaluation
  → Build minimal solution
  → Compare to baseline
  → Run falsification tests
  → Check all invariants
  → Pass gate or kill
  → Issue certificate
  → Ship with evidence
```

**Key Difference:**
- Innovation is GENERATED (by builders)
- But FILTERED (by gate)
- Certificates are EARNED (not given)
- Failures are DOCUMENTED (not hidden)

---

## FORMAL GUARANTEES

### Theorem 1: No False Positives
```
∀ POC p: graduate(p) ⟹ p ∈ 𝒱 ∧ beats_baseline(p) ∧ survives_falsification(p)
```
**Proof:** Gate rejects any POC that violates invariants, doesn't beat baseline, or fails falsification. ∎

### Theorem 2: Reproducibility
```
∀ POC p: graduate(p) ⟹ ∃ manifest m: run(m) = results(p)
```
**Proof:** J₁ + J₂ enforce determinism + traceability. ∎

### Theorem 3: No Metric Laundering
```
∀ POC p: graduate(p) ⟹ eval_pre_registered(p) ∧ has_held_out_test(p)
```
**Proof:** J₃ enforces pre-registration + held-out tests. ∎

---

## CONSTITUTIONAL GUARANTEES

From ORACLE SUPERTEAM v1.0, preserved:

1. ✅ **NO_RECEIPT = NO_SHIP** → No certificate without evidence
2. ✅ **Non-Sovereign Agents** → Builders propose, gate decides
3. ✅ **Binary Verdicts** → SHIP or KILL only (or ITERATE)
4. ✅ **Kill-Switch Dominance** → J₆ violation auto-kills
5. ✅ **Replay Determinism** → Manifest-based reproducibility

New in IFG:

6. ✅ **Viability Preservation** → All graduated POCs stay in 𝒱
7. ✅ **Baseline Dominance** → Must beat named baseline
8. ✅ **Falsification Required** → Must survive killing tests
9. ✅ **Pre-Registration** → No post-hoc evaluation
10. ✅ **Capability Certification** → Explicit what/cost/failure modes

---

## NEXT STEPS

### Immediate (Week 1)
- [ ] Deploy POC template
- [ ] Create manifest schema
- [ ] Build baseline suite
- [ ] Write CI validation script

### Short-Term (Month 1)
- [ ] Run 3 POCs end-to-end
- [ ] Kill at least 1 via gate
- [ ] Issue first capability certificate

### Medium-Term (Quarter 1)
- [ ] Integrate Oracle Town coupling
- [ ] Build certificate registry
- [ ] Enable public POC explorer

---

## CITATION

```bibtex
@software{poc_factory_ifg,
  title={POC FACTORY: Invariance-First Generativity for Reproducible R&D},
  author={JMT Consulting},
  year={2026},
  version={1.0-IFG},
  framework={Σ–SEED Discipline},
  url={https://github.com/yourusername/oracle-superteam}
}
```

---

**This is not a conversation. This is an institution.**

**Status:** ✅ READY FOR IMPLEMENTATION
**Date:** January 16, 2026
**Version:** 1.0-IFG
