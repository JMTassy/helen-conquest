# IFG COUPLING CONTRACT — Oracle Town ↔ POC Factory

**Version:** 1.0-IFG
**Status:** ✅ READY FOR IMPLEMENTATION
**Date:** January 16, 2026

---

## ONE-SENTENCE SUMMARY

> **The Coupling Contract = Oracle Town sends ranked hypotheses with constraints; POC Factory returns capability certificates with failure modes; shared invariants prevent gaming and metric laundering across both systems.**

---

## ARCHITECTURE: TWO COUPLED VIABILITY-THERMOSTAT SYSTEMS

```
┌─────────────────────────────────────────────────────────────┐
│                     ORACLE TOWN                             │
│              (Social/Market Interface)                      │
│                                                             │
│  Input: Stakeholder proposals + budget                     │
│  Process: Prediction market + invariants gate              │
│  Output: Ranked hypotheses with constraints                │
│                                                             │
│  Invariants: I₁-I₈ (transparency, fairness, calibration)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ COUPLING INTERFACE
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    POC FACTORY                              │
│            (Engineering/Science Back-End)                   │
│                                                             │
│  Input: Hypotheses + constraints + budget                  │
│  Process: Build + test + falsify + gate                    │
│  Output: Capability certificates with failure modes        │
│                                                             │
│  Invariants: J₁-J₇ (reproducibility, truthfulness, cost)   │
└─────────────────────────────────────────────────────────────┘
```

---

## COUPLING INTERFACE: ORACLE TOWN → POC FACTORY

### 1. Hypothesis Queue (Oracle Town Output)

**Schema:**
```typescript
interface HypothesisQueue {
  queue_id: string;
  timestamp: string;
  hypotheses: RankedHypothesis[];
  viability_status: {
    oracle_town_in_region: boolean;
    violated_invariants: string[];
  };
}

interface RankedHypothesis {
  hypothesis_id: string;
  rank: number;
  priority: "HIGH" | "MEDIUM" | "LOW";

  // Core hypothesis
  hypothesis_text: string;
  technical_target: KPI;
  expected_impact: {
    distribution: Distribution;
    p50: number;
    p90: number;
    confidence_interval: [number, number];
  };

  // Constraints from Oracle Town invariants
  constraints: {
    political_constraints: string[];  // From I₂ fairness
    operational_constraints: string[]; // From I₅ service quality
    budget_constraints: BudgetConstraint;  // From I₃ budget integrity
    timeline_constraints: TimelineConstraint;
  };

  // Market signal (for context, not decision)
  market_signal: {
    predicted_probability: number;
    calibration_score: number;
    participant_diversity: number;
  };

  // Evidence requirements (from I₁ transparency)
  required_evidence_types: string[];

  // Link back to Oracle Town
  linked_initiative_id: string;
  linked_prediction_questions: string[];
}
```

**Example:**
```json
{
  "queue_id": "Q-2026-01-16-001",
  "timestamp": "2026-01-16T10:00:00Z",
  "hypotheses": [
    {
      "hypothesis_id": "HYP-001",
      "rank": 1,
      "priority": "HIGH",
      "hypothesis_text": "In-memory caching will reduce API latency by ≥ 15%",
      "technical_target": {
        "metric": "api.latency.p99",
        "current_value": 180,
        "target_value": 153,
        "unit": "ms",
        "improvement_required": 0.15
      },
      "expected_impact": {
        "distribution": "normal(mean=0.18, std=0.04)",
        "p50": 0.18,
        "p90": 0.24,
        "confidence_interval": [0.14, 0.22]
      },
      "constraints": {
        "political_constraints": [
          "No external service dependencies (fairness to small operators)"
        ],
        "operational_constraints": [
          "Memory footprint < 500MB (I₅ service quality)",
          "Complaint rate must stay ≤ 3% during rollout"
        ],
        "budget_constraints": {
          "compute_budget": 100,
          "time_budget_hours": 40,
          "currency": "EUR"
        },
        "timeline_constraints": {
          "poc_deadline": "2026-02-15",
          "resolution_window": "30_days"
        }
      },
      "market_signal": {
        "predicted_probability": 0.78,
        "calibration_score": 0.18,
        "participant_diversity": 0.82
      },
      "required_evidence_types": [
        "BASELINE_MEASUREMENT",
        "LOAD_TEST_RESULTS",
        "REPRODUCIBLE_BENCHMARK"
      ],
      "linked_initiative_id": "INI-CACHE-001",
      "linked_prediction_questions": ["PQ-001", "PQ-002"]
    }
  ]
}
```

---

## COUPLING INTERFACE: POC FACTORY → ORACLE TOWN

### 2. Capability Certificate (POC Factory Output)

**Schema:**
```typescript
interface CapabilityCertificateResponse {
  response_id: string;
  hypothesis_id: string;
  timestamp: string;

  verdict: "GRADUATED" | "KILLED" | "ITERATE_REQUIRED";

  capability_certificate: CapabilityCertificate | null;  // null if KILLED

  oracle_town_feedback: {
    invariants_oracle_town_cares_about: InvariantFeedback[];
    risk_flags: RiskFlag[];
    recommended_prediction_update: PredictionUpdate | null;
  };
}

interface CapabilityCertificate {
  certificate_id: string;
  poc_id: string;
  issued_at: string;
  expires_at: string;

  // What is technically achievable
  technical_capability: {
    what_is_achievable: string;
    under_constraints: Constraint[];
    measured_uplift: {
      distribution: Distribution;
      confidence_interval: [number, number];
      p_value: number;
      effect_size: number;
      baseline_name: string;
      baseline_value: number;
      poc_value: number;
    };
  };

  // Cost curves (for Oracle Town I₃ budget integrity)
  cost_curves: {
    total_cost: number;
    cost_per_gain: number;
    compute_cost: number;
    time_cost_hours: number;
    cost_breakdown: CostBreakdown;
  };

  // Failure modes (for Oracle Town risk assessment)
  failure_modes: {
    mode: string;
    trigger_condition: string;
    invariant_broken: string;  // Which Oracle Town invariant?
    probability_estimate: number;
    mitigation: string;
    residual_risk: "LOW" | "MEDIUM" | "HIGH";
  }[];

  // Falsification evidence (for Oracle Town I₇ calibration)
  falsification_evidence: FalsificationTest[];

  // Invariants passed (POC Factory J₁-J₇)
  invariants_passed: InvariantCheck[];

  // Artifacts (for Oracle Town I₁ transparency)
  artifacts: {
    repository: string;
    manifest_hash: string;
    reproducible_command: string;
    container_image: string;
    public_dashboard_url: string;
  };

  // Signature (for Oracle Town audit trail)
  signature: string;  // HMAC-SHA256
}

interface InvariantFeedback {
  oracle_town_invariant_id: string;  // e.g., "I5_SERVICE_QUALITY"
  impact_estimate: {
    current_value: number;
    projected_value: number;
    stays_in_threshold: boolean;
  };
  confidence: number;
  evidence: string;
}

interface RiskFlag {
  flag_id: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  description: string;
  affected_invariants: string[];  // Oracle Town invariant IDs
  mitigation_required: boolean;
}
```

**Example:**
```json
{
  "response_id": "RESP-2026-01-16-001",
  "hypothesis_id": "HYP-001",
  "timestamp": "2026-01-16T12:00:00Z",
  "verdict": "GRADUATED",
  "capability_certificate": {
    "certificate_id": "CERT-POC-001",
    "poc_id": "POC-001",
    "issued_at": "2026-01-16T12:00:00Z",
    "expires_at": "2026-07-16T12:00:00Z",
    "technical_capability": {
      "what_is_achievable": "Can reduce API latency p99 by 18% (CI: [14%, 22%]) under production load",
      "under_constraints": [
        "Memory footprint: 450MB (within 500MB limit)",
        "No external services",
        "100% deterministic"
      ],
      "measured_uplift": {
        "distribution": "normal(mean=0.18, std=0.02)",
        "confidence_interval": [0.14, 0.22],
        "p_value": 0.001,
        "effect_size": 1.2,
        "baseline_name": "no_cache_baseline",
        "baseline_value": 180,
        "poc_value": 148
      }
    },
    "cost_curves": {
      "total_cost": 95,
      "cost_per_gain": 5.28,
      "compute_cost": 85,
      "time_cost_hours": 38,
      "cost_breakdown": {
        "dev_time": 30,
        "compute": 85,
        "testing": 15,
        "deployment": 5
      }
    },
    "failure_modes": [
      {
        "mode": "Cache stampede on cold start",
        "trigger_condition": "Pod restart under high load",
        "invariant_broken": "I5_SERVICE_QUALITY (response time spike)",
        "probability_estimate": 0.15,
        "mitigation": "Staggered cache warmup + circuit breaker",
        "residual_risk": "LOW"
      },
      {
        "mode": "Memory pressure eviction",
        "trigger_condition": "Traffic spike > 150% baseline",
        "invariant_broken": "I5_SERVICE_QUALITY (complaint rate increase)",
        "probability_estimate": 0.08,
        "mitigation": "Auto-scaling trigger + LRU with size limits",
        "residual_risk": "LOW"
      }
    ],
    "falsification_evidence": [
      {
        "test_id": "FALS-001",
        "name": "Adversarial traffic spike",
        "could_have_killed": true,
        "survived": true,
        "evidence_log": "logs/adversarial_test_001.log"
      },
      {
        "test_id": "FALS-002",
        "name": "Cold start stress test",
        "could_have_killed": true,
        "survived": true,
        "evidence_log": "logs/cold_start_002.log"
      }
    ],
    "invariants_passed": [
      {"invariant_id": "J1_DETERMINISM", "pass_fail": true},
      {"invariant_id": "J2_TRACEABILITY", "pass_fail": true},
      {"invariant_id": "J3_NO_METRIC_LAUNDERING", "pass_fail": true},
      {"invariant_id": "J4_BASELINE_DOMINANCE", "pass_fail": true},
      {"invariant_id": "J5_COST_TIME", "pass_fail": true},
      {"invariant_id": "J6_DATA_GOVERNANCE", "pass_fail": true},
      {"invariant_id": "J7_OPERATIONAL_READINESS", "pass_fail": true}
    ],
    "artifacts": {
      "repository": "https://github.com/example/poc-cache-001",
      "manifest_hash": "sha256:a7b8c9d0e1f2...",
      "reproducible_command": "docker run poc-001:v1 --seed 42",
      "container_image": "ghcr.io/example/poc-001:v1",
      "public_dashboard_url": "https://dashboard.example.com/poc-001"
    },
    "signature": "hmac_sha256:f3e4d5c6b7a8..."
  },
  "oracle_town_feedback": {
    "invariants_oracle_town_cares_about": [
      {
        "oracle_town_invariant_id": "I5_SERVICE_QUALITY",
        "impact_estimate": {
          "current_value": 0.028,
          "projected_value": 0.029,
          "stays_in_threshold": true
        },
        "confidence": 0.85,
        "evidence": "Complaint rate increased by 0.1% in stress tests (within 3% threshold)"
      },
      {
        "oracle_town_invariant_id": "I3_BUDGET_INTEGRITY",
        "impact_estimate": {
          "current_value": 95,
          "projected_value": 95,
          "stays_in_threshold": true
        },
        "confidence": 1.0,
        "evidence": "Total cost €95, within €100 budget"
      }
    ],
    "risk_flags": [
      {
        "flag_id": "RISK-001",
        "severity": "LOW",
        "description": "Cache stampede possible under cold start + high load",
        "affected_invariants": ["I5_SERVICE_QUALITY"],
        "mitigation_required": true
      }
    ],
    "recommended_prediction_update": {
      "question_id": "PQ-001",
      "current_probability": 0.78,
      "recommended_probability": 0.88,
      "reason": "POC demonstrates 18% improvement (CI: [14%, 22%]), exceeding 15% target"
    }
  }
}
```

---

## SHARED INVARIANTS (NON-NEGOTIABLE ACROSS BOTH SYSTEMS)

### S₁: Evidence Integrity (No Metric Laundering)

**Applies to:**
- Oracle Town: I₇ (forecast calibration)
- POC Factory: J₃ (no metric laundering)

**Contract:**
```typescript
interface EvidenceIntegrityInvariant {
  id: "S1_EVIDENCE_INTEGRITY";
  rule: "NO_METRIC_LAUNDERING";
  enforcement: {
    oracle_town: {
      pre_register_prediction_questions: true;
      resolve_with_verified_data_only: true;
      no_retroactive_question_edits: true;
    };
    poc_factory: {
      pre_register_evaluation_protocol: true;
      use_held_out_tests: true;
      no_post_hoc_metrics: true;
    };
  };
  violation_consequence: "AUTO_REJECT";
}
```

**Why this matters:**
- Prevents p-hacking in both prediction markets and POCs
- Same data integrity standard across social and technical layers

### S₂: Auditability (Transparency)

**Applies to:**
- Oracle Town: I₁ (transparency)
- POC Factory: J₂ (traceability)

**Contract:**
```typescript
interface AuditabilityInvariant {
  id: "S2_AUDITABILITY";
  rule: "EVERY_DECISION_TRACED_TO_ARTIFACTS";
  enforcement: {
    oracle_town: {
      publish_rationale_for_all_decisions: true;
      link_to_evidence_artifacts: true;
      make_prediction_history_public: true;
    };
    poc_factory: {
      link_metrics_to_manifests: true;
      publish_reproducible_commands: true;
      make_artifact_registry_public: true;
    };
  };
  violation_consequence: "BLOCK_DECISION";
}
```

**Why this matters:**
- Same transparency standard for political and technical decisions
- Citizens can audit both market signals and technical claims

### S₃: Anti-Gaming (Integrity)

**Applies to:**
- Oracle Town: I₈ (anti-gaming)
- POC Factory: (implicitly via J₃ + J₄)

**Contract:**
```typescript
interface AntiGamingInvariant {
  id: "S3_ANTI_GAMING";
  rule: "DETECT_AND_REJECT_MANIPULATION";
  enforcement: {
    oracle_town: {
      detect_prediction_copying: true;
      detect_wash_trading: true;
      detect_sybil_clusters: true;
      anomaly_score_threshold: 0.15;
    };
    poc_factory: {
      detect_cherry_picking: true;
      require_baseline_dominance: true;
      require_falsification_tests: true;
    };
  };
  violation_consequence: "AUTO_REJECT + FLAG_FOR_REVIEW";
}
```

**Why this matters:**
- Same integrity standard for market manipulation and metric laundering
- Gaming is rejected at both the social and technical layers

---

## COUPLING WORKFLOW (END-TO-END)

### Step 1: Oracle Town Generates Hypothesis

```
Human Proposal:
  "Launch caching to reduce API latency"

Oracle Town Process:
  1. Bouncer admits claim
  2. Concierge routes to prediction market
  3. Market generates probability: 78%
  4. Check invariants (I₁-I₈): ALL PASS
  5. Rank hypothesis: #1 (highest certified margin)

Oracle Town Output:
  HypothesisQueue with ranked hypothesis + constraints
```

### Step 2: Coupling Interface (Oracle Town → POC Factory)

```
Hypothesis Queue Sent:
  {
    "hypothesis_id": "HYP-001",
    "hypothesis_text": "Caching will reduce latency by ≥ 15%",
    "constraints": {
      "memory < 500MB",
      "no external services",
      "complaint rate ≤ 3%"
    },
    "budget": {"compute": 100, "time_hours": 40}
  }
```

### Step 3: POC Factory Builds & Tests

```
POC Factory Process:
  1. Create POC-001 with pre-registered eval
  2. Build minimal caching solution
  3. Run tests against baseline
  4. Run falsification tests (adversarial, OOD, resource stress)
  5. Check invariants (J₁-J₇): ALL PASS
  6. Compute failure modes + risk estimates

POC Factory Output:
  CapabilityCertificate with:
    - Measured uplift: 18% (CI: [14%, 22%])
    - Cost: €95 (within budget)
    - Failure modes: 2 (both mitigated)
    - Risk flags: 1 LOW severity
```

### Step 4: Coupling Interface (POC Factory → Oracle Town)

```
Capability Certificate Sent:
  {
    "verdict": "GRADUATED",
    "capability": "18% improvement (CI: [14%, 22%])",
    "cost": €95,
    "failure_modes": [
      {"mode": "Cache stampede", "residual_risk": "LOW"}
    ],
    "oracle_town_feedback": {
      "I5_SERVICE_QUALITY": "stays within threshold",
      "I3_BUDGET_INTEGRITY": "within budget"
    }
  }
```

### Step 5: Oracle Town Updates & Decides

```
Oracle Town Process:
  1. Receive certificate
  2. Update prediction market (78% → 88%)
  3. Re-check invariants with new information
  4. Run gate: viability + certified margin
  5. Decision: ACCEPT

Oracle Town Output:
  Initiative Decision: GO
  Rationale: POC demonstrates 18% improvement, exceeds 15% target
  Evidence: Certificate CERT-POC-001
  Predicted outcome: 88% probability of success
```

### Step 6: Deploy & Measure

```
Deployment:
  1. Deploy caching solution (containerized)
  2. Monitor for 30 days
  3. Measure actual improvement
  4. Resolve prediction questions

Actual Outcome:
  Latency improvement: 16% (within CI)
  Complaint rate: 2.9% (within threshold)
  No failure modes triggered

Calibration Update:
  Predicted: 88% (YES)
  Actual: YES (16% ≥ 15%)
  Brier Score: (0.88 - 1)² = 0.014 (excellent)
```

---

## FEEDBACK LOOPS (CONTINUOUS IMPROVEMENT)

### Loop 1: Calibration Update

```python
def update_calibration(oracle_town, poc_factory, resolution):
    """Update both systems based on resolution."""

    # Oracle Town: Update predictor scores
    oracle_town.update_brier_scores(resolution)
    oracle_town.update_calibration_curve()

    # POC Factory: Update baseline suite
    if resolution.succeeded:
        poc_factory.add_to_baseline_suite(resolution.poc)
        poc_factory.update_cost_curves(resolution.cost_actuals)

    # Shared: Update anti-gaming models
    shared_integrity_system.update_anomaly_detectors(resolution)
```

### Loop 2: Failure Mode Learning

```python
def learn_from_failure_modes(oracle_town, poc_factory, incident):
    """Update both systems when failure mode triggers."""

    # POC Factory: Update falsification tests
    poc_factory.add_falsification_test(incident.failure_mode)
    poc_factory.update_risk_estimates(incident.failure_mode)

    # Oracle Town: Update invariant thresholds
    if incident.violated_invariant:
        oracle_town.tighten_invariant_threshold(incident.violated_invariant)

    # Shared: Flag for future hypotheses
    coupling_contract.add_risk_flag(incident.failure_mode)
```

### Loop 3: Cost Learning

```python
def update_cost_models(oracle_town, poc_factory, actuals):
    """Update cost estimates based on actuals."""

    # POC Factory: Update cost-per-gain models
    poc_factory.update_cost_curves(actuals.cost, actuals.gain)

    # Oracle Town: Update budget constraints
    oracle_town.update_budget_model(actuals.cost_by_initiative_type)

    # Shared: Update resource allocation
    coupling_contract.update_resource_allocation_policy(actuals)
```

---

## MINIMAL LAUNCH (4-WEEK INTEGRATED)

### Week 1: Setup Both Systems

**Oracle Town:**
- [ ] Deploy invariants dashboard (I₁-I₈)
- [ ] Define 10 prediction questions
- [ ] Set up coupling API endpoint

**POC Factory:**
- [ ] Deploy POC template + CI
- [ ] Create baseline suite
- [ ] Set up coupling API endpoint

**Coupling:**
- [ ] Define HypothesisQueue schema
- [ ] Define CapabilityCertificate schema
- [ ] Deploy coupling middleware

### Week 2: First Integrated Run

**Oracle Town:**
- [ ] Run prediction market (7 days)
- [ ] Generate HypothesisQueue (rank 3 hypotheses)
- [ ] Send to POC Factory

**POC Factory:**
- [ ] Build 3 POCs from queue
- [ ] Test + falsify
- [ ] Send back 3 certificates (expect 1 KILL)

**Coupling:**
- [ ] Verify schemas
- [ ] Log all exchanges
- [ ] Monitor latency

### Week 3: Deploy & Measure

**Oracle Town:**
- [ ] Accept 2 graduated POCs
- [ ] Deploy initiatives
- [ ] Monitor for 30 days

**POC Factory:**
- [ ] Monitor deployed POCs
- [ ] Collect failure mode data
- [ ] Update baseline suite

**Coupling:**
- [ ] Track resolution data
- [ ] Update calibration
- [ ] Measure feedback loops

### Week 4: Calibrate & Iterate

**Oracle Town:**
- [ ] Resolve prediction questions
- [ ] Update Brier scores
- [ ] Publish calibration report

**POC Factory:**
- [ ] Update cost-per-gain models
- [ ] Add falsification tests
- [ ] Issue lessons-learned report

**Coupling:**
- [ ] Verify shared invariants (S₁-S₃)
- [ ] Publish integrated dashboard
- [ ] Plan expansion

---

## INTEGRATION TESTS (CRITICAL)

### Test 1: Oracle Town Proposes, POC Factory Kills

```
Hypothesis: "Aggressive compression will reduce storage by 40%"

Oracle Town: 65% probability (market signal)
Constraints: "Data loss < 0.1%"

POC Factory: KILLED
Reason: J₄ Baseline Dominance violated (data loss 2.5%)
Certificate: NOT ISSUED

Oracle Town: Update market to 5% (hypothesis falsified)
Calibration: Poor initial prediction, but system learned
```

**Key Test:** POC Factory kill should override market optimism.

### Test 2: Oracle Town Kills Despite POC Success

```
Hypothesis: "ML recommendation engine will increase engagement"

POC Factory: GRADUATED
Certificate: 25% engagement increase (CI: [20%, 30%])
Cost: €80 (within budget)

Oracle Town: REJECTED
Reason: I₂ Fairness violated (benefits only premium users)
Gate: Viability breach

POC Factory: Archive POC with "killed by policy" tag
```

**Key Test:** Oracle Town invariants should override technical success.

### Test 3: Calibration Feedback Loop

```
Hypothesis: "Event X will increase occupancy by 10%"

Oracle Town Prediction: 70%
POC Factory Certificate: 12% improvement (CI: [9%, 15%])
Oracle Town Updated Prediction: 85%

Actual Outcome: 11% improvement (YES)

Calibration:
  Initial: (0.70 - 1)² = 0.09
  Updated: (0.85 - 1)² = 0.023
  Improvement: 74% reduction in Brier score
```

**Key Test:** POC Factory evidence should improve Oracle Town calibration.

---

## FORMAL COUPLING GUARANTEES

### Theorem 1: Double-Gated Safety
```
∀ hypothesis h: deploy(h) ⟹ oracle_town_gate(h) ∧ poc_factory_gate(h)
```
**Proof:** Deployment requires both Oracle Town acceptance (invariants I₁-I₈) AND POC Factory graduation (invariants J₁-J₇). ∎

### Theorem 2: Calibration Accountability
```
∀ prediction p: track(p.brier_score) ∧ update_on_poc_evidence(p)
```
**Proof:** Oracle Town I₇ requires calibration tracking. POC Factory certificates provide evidence for updates. ∎

### Theorem 3: No Hidden Failures
```
∀ poc p: graduate(p) ⟹ failure_modes(p) documented ∧ sent_to_oracle_town(p)
```
**Proof:** POC Factory certificate schema requires failure modes. Coupling contract requires transmission to Oracle Town. ∎

---

## THE SURPRISING ADVANTAGE (INTEGRATED)

### What Most Systems Do (FAILS)

```
Siloed Systems:
  → Politicians promise without technical reality check
  → Engineers build without political viability check
  → No feedback loop
  → Narrative diverges from capability
  → Trust collapses
```

### What IFG Coupling Does (WINS)

```
Coupled Viability-Thermostat:
  → Oracle Town: Can we promise this? (political viability)
  → POC Factory: Can we deliver this? (technical capability)
  → Coupling: Update beliefs based on evidence
  → Narrative constrained by certificates
  → Trust preserved via transparency
```

**Key Insight:**
- Political decisions informed by technical reality
- Technical work guided by political constraints
- Continuous calibration closes the gap
- Failures documented and learned from

---

## CONSTITUTIONAL GUARANTEES (INTEGRATED)

From ORACLE SUPERTEAM v1.0 + IFG:

1. ✅ **NO_RECEIPT = NO_SHIP** → Both systems require evidence
2. ✅ **Non-Sovereign Agents** → Markets propose, gates decide
3. ✅ **Binary Verdicts** → GO/NO_GO at both layers
4. ✅ **Kill-Switch Dominance** → I₆ + J₆ violations auto-kill
5. ✅ **Replay Determinism** → Both systems deterministic
6. ✅ **Viability Preservation** → Double-gated safety
7. ✅ **Evidence Integrity** → S₁ enforced across both
8. ✅ **Auditability** → S₂ enforced across both
9. ✅ **Anti-Gaming** → S₃ enforced across both
10. ✅ **Calibration Accountability** → Continuous feedback

---

## CITATION

```bibtex
@software{ifg_coupling_contract,
  title={IFG Coupling Contract: Oracle Town ↔ POC Factory},
  author={JMT Consulting},
  year={2026},
  version={1.0-IFG},
  framework={Coupled Viability-Thermostat Systems},
  url={https://github.com/yourusername/oracle-superteam}
}
```

---

**This is not a conversation. This is an institution.**

**Status:** ✅ READY FOR IMPLEMENTATION
**Date:** January 16, 2026
**Version:** 1.0-IFG

---

## NEXT STEPS

1. **Week 1:** Deploy both systems with coupling APIs
2. **Week 2:** Run first integrated hypothesis → certificate flow
3. **Week 3:** Deploy 2 initiatives, monitor outcomes
4. **Week 4:** Resolve predictions, update calibration, publish report

**The coupling is not optional. It's the innovation.**
