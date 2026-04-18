# ORACLE TOWN — Invariance-First Generativity Specification

**Version:** 1.0-IFG
**Status:** ✅ READY FOR IMPLEMENTATION
**Date:** January 16, 2026

---

## ONE-SENTENCE SUMMARY

> **ORACLE TOWN = Viability-gated civic prediction engine where narrative is generated within certified invariants, and decisions are controlled dynamical system output, not committee drift.**

---

## ARCHITECTURE: VIABILITY-THERMOSTAT SYSTEM

### State Definition

**State x:** Portfolio of town initiatives

```typescript
interface TownInitiative {
  initiative_id: string;
  type: "TOURISM_OFFER" | "INFRA_UPGRADE" | "POLICY_PILOT" | "EVENT" | "PARTNERSHIP";
  proposed_by: string;
  status: "PROPOSED" | "TESTING" | "ACCEPTED" | "REJECTED" | "RUNNING";
  kpi_targets: KPITarget[];
  budget_envelope: {
    allocated: number;
    spent: number;
    currency: "EUR";
  };
  prediction_questions: PredictionQuestion[];
  invariant_impact_estimate: InvariantImpact[];
  go_no_go_decision: Decision | null;
}
```

### Generator G

**Propose–Test–Revise Loop:**

```typescript
interface Generator {
  input: {
    stakeholder_proposals: Proposal[];
    budget_allocation: BudgetPlan;
    campaign_variants: CampaignOption[];
    operational_changes: OperationalDelta[];
  };

  output: {
    candidate_initiatives: TownInitiative[];
    predicted_uplift_distribution: Distribution;
    invariants_impact: InvariantImpact[];
    recommendation: "GO" | "NO_GO" | "ITERATE";
  };
}
```

---

## INVARIANT BUNDLE (NON-NEGOTIABLE)

### I₁: Transparency (Governance & Trust)

```typescript
interface TransparencyInvariant {
  id: "I1_TRANSPARENCY";
  metric: "% decisions with public rationale + data links";
  threshold: {
    critical: 0.95;  // 95% minimum
    target: 0.98;
  };
  measurement: {
    numerator: "count(decisions with published rationale + data links)";
    denominator: "count(all decisions)";
  };
  audit_trail: string[];  // URLs to published rationales
}
```

**Enforcement:**
- Every decision MUST generate:
  - Public rationale document
  - Data links (evidence artifacts)
  - Timestamp + decision_id
- Decisions without rationale → BLOCKED

### I₂: Fairness (Governance & Trust)

```typescript
interface FairnessInvariant {
  id: "I2_FAIRNESS";
  metric: "Disparity metrics across neighborhoods / business sizes";
  threshold: {
    gini_coefficient_max: 0.40;  // Max inequality allowed
    investment_ratio_min: 0.15;  // Min % to smallest quartile
  };
  measurement: {
    neighborhood_investment: Map<string, number>;
    business_size_distribution: Map<BusinessSize, number>;
    gini_coefficient: number;
  };
  alert_on_breach: true;
}
```

### I₃: Budget Integrity (Economics)

```typescript
interface BudgetIntegrityInvariant {
  id: "I3_BUDGET_INTEGRITY";
  metric: "Spend variance vs approved plan";
  threshold: {
    variance_max: 0.10;  // ±10% max variance
    requires_justification_above: 0.05;
  };
  measurement: {
    approved_budget: number;
    actual_spend: number;
    variance: number;  // |actual - approved| / approved
    justification_required: boolean;
  };
}
```

### I₄: ROI Realism (Economics)

```typescript
interface ROIRealismInvariant {
  id: "I4_ROI_REALISM";
  metric: "Forecast error bound tracked over time";
  threshold: {
    mean_absolute_percentage_error_max: 0.25;  // 25% MAPE max
    bias_abs_max: 0.10;  // No systematic over/under prediction
  };
  measurement: {
    forecasts: Forecast[];
    actuals: Actual[];
    mape: number;
    bias: number;  // mean(forecast - actual) / mean(actual)
  };
  calibration_required: true;
}
```

### I₅: Service Quality (Operations)

```typescript
interface ServiceQualityInvariant {
  id: "I5_SERVICE_QUALITY";
  metric: "Complaint rate / NPS / response times";
  threshold: {
    complaint_rate_max: 0.03;  // 3% max
    nps_min: 30;
    response_time_p95_max_hours: 48;
  };
  measurement: {
    complaint_count: number;
    total_interactions: number;
    nps_score: number;
    response_time_p95_hours: number;
  };
}
```

### I₆: Regulatory Compliance (Safety & Compliance)

```typescript
interface RegulatoryComplianceInvariant {
  id: "I6_REGULATORY_COMPLIANCE";
  metric: "Zero critical violations";
  threshold: {
    critical_violations: 0;
    non_critical_max: 2;
  };
  measurement: {
    critical_violations: Violation[];
    non_critical_violations: Violation[];
    last_audit_date: string;
  };
  kill_switch: true;  // Auto-rejects if violated
}
```

### I₇: Forecast Calibration (Signal Integrity - CRITICAL)

```typescript
interface ForecastCalibrationInvariant {
  id: "I7_FORECAST_CALIBRATION";
  metric: "Brier score / log score on resolved questions";
  threshold: {
    brier_score_max: 0.25;  // Lower is better, 0 = perfect
    log_score_min: -0.50;   // Higher is better, 0 = perfect
    min_resolved_questions: 20;  // Minimum sample for calibration
  };
  measurement: {
    resolved_questions: ResolvedQuestion[];
    brier_score: number;
    log_score: number;
    calibration_curve: CalibrationPoint[];
  };
  explanation: "Measures how well predictors' confidence matches actual outcomes";
}
```

**Brier Score Formula:**
```
BS = (1/N) Σ (f_i - o_i)²
where:
  f_i = predicted probability
  o_i = actual outcome (0 or 1)

Perfect prediction: BS = 0
Random guessing: BS = 0.25
Worse than random: BS > 0.25
```

### I₈: Anti-Gaming (Signal Integrity - CRITICAL)

```typescript
interface AntiGamingInvariant {
  id: "I8_ANTI_GAMING";
  metric: "Anomaly score on participation + voting/prediction patterns";
  threshold: {
    anomaly_score_max: 0.15;  // Z-score based
    collusion_clusters_max: 0;
    wash_trading_detected: false;
  };
  measurement: {
    participation_patterns: ParticipationLog[];
    voting_correlation_matrix: number[][];
    anomaly_detections: Anomaly[];
  };
  enforcement: {
    flag_for_review_above: 0.10;
    auto_reject_above: 0.15;
  };
}
```

**Anti-Gaming Detection Rules:**
- Temporal clustering (same users voting within 30s)
- Prediction copying (>90% identical portfolios)
- Wash trading (bidirectional trades with no economic purpose)
- Sybil detection (IP clustering, behavioral fingerprinting)

---

## VIABILITY REGION & GATE (Σ–SEED DISCIPLINE)

### Viability Region 𝒱

```python
def in_viability_region(state: TownState) -> bool:
    """Check if state satisfies ALL invariants."""
    return all([
        state.transparency >= 0.95,
        state.gini_coefficient <= 0.40,
        state.budget_variance <= 0.10,
        state.roi_mape <= 0.25,
        state.complaint_rate <= 0.03,
        state.critical_violations == 0,
        state.brier_score <= 0.25,
        state.anomaly_score <= 0.15
    ])
```

### Acceptance Rule (THE GATE)

A change Δ is accepted **IFF:**

```python
def accept_change(current_state: TownState, proposed_change: Delta) -> Decision:
    """Gate: accept change only if viability + certified margin."""

    # Step 1: Viability check
    new_state = apply_change(current_state, proposed_change)
    if not in_viability_region(new_state):
        return Decision(
            verdict="REJECT",
            reason="VIABILITY_BREACH",
            violated_invariants=get_violations(new_state)
        )

    # Step 2: Certified margin check
    margin = compute_certified_margin(current_state, new_state)
    noise_band = estimate_noise_band(current_state)

    if margin.improvement <= noise_band.upper_bound:
        return Decision(
            verdict="REJECT",
            reason="INSUFFICIENT_MARGIN",
            margin_needed=noise_band.upper_bound,
            margin_observed=margin.improvement
        )

    # Step 3: Accept
    return Decision(
        verdict="ACCEPT",
        reason="VIABILITY_PRESERVED_AND_MARGIN_CERTIFIED",
        margin=margin,
        new_state=new_state
    )
```

**Key Insight:** This is NOT majority vote. This is physics. Either you stay in 𝒱 and improve beyond noise, or you don't ship.

---

## MARKET MECHANISM: PREDICTION QUESTIONS

### Question Types (Tied to Initiatives)

#### Type 1: Occupancy Impact
```typescript
interface OccupancyQuestion {
  question_id: string;
  text: "If we launch Event A, will occupancy in Zone Z rise by ≥ 8% vs baseline next month?";
  resolution_criteria: {
    metric: "occupancy_rate_zone_Z";
    baseline: number;  // Historical average
    threshold: 0.08;   // 8% uplift
    measurement_window: "30_days";
    data_source: "hotel_booking_system";
  };
  prediction_market: {
    current_probability: number;
    volume: number;
    participants: number;
  };
  linked_initiative: string;  // initiative_id
}
```

#### Type 2: Revenue Impact
```typescript
interface RevenueQuestion {
  question_id: string;
  text: "Will average spend per visitor rise by ≥ €X after Offer Bundle B?";
  resolution_criteria: {
    metric: "avg_spend_per_visitor";
    baseline: number;
    threshold: number;  // €X
    measurement_window: "60_days";
    data_source: "pos_system";
  };
  prediction_market: {
    current_probability: number;
    calibration_history: CalibrationPoint[];
  };
  linked_initiative: string;
}
```

#### Type 3: Service Quality Under Load
```typescript
interface ServiceQualityQuestion {
  question_id: string;
  text: "Will complaint rate remain ≤ threshold while foot traffic increases?";
  resolution_criteria: {
    metric: "complaint_rate";
    threshold: 0.03;
    condition: "foot_traffic_increase >= 0.15";  // 15% increase
    measurement_window: "90_days";
  };
  linked_invariant: "I5_SERVICE_QUALITY";
  linked_initiative: string;
}
```

### Market Rules (IFG Discipline)

**CRITICAL:** Predictions do NOT directly decide. They propose. The thermostat decides.

```python
def market_to_decision_flow(question: PredictionQuestion) -> InitiativeDecision:
    """Market predictions inform, but gate decides."""

    # Step 1: Collect market signal
    market_signal = {
        "predicted_probability": question.market.current_probability,
        "confidence_interval": question.market.confidence_interval,
        "calibration_score": compute_calibration(question.market.history),
        "participant_diversity": measure_diversity(question.market.participants)
    }

    # Step 2: Estimate invariant impact
    invariant_impact = estimate_impact_on_invariants(
        initiative=question.linked_initiative,
        market_signal=market_signal
    )

    # Step 3: Run gate
    decision = accept_change(
        current_state=get_current_state(),
        proposed_change=build_delta(question.linked_initiative, invariant_impact)
    )

    return InitiativeDecision(
        initiative_id=question.linked_initiative,
        verdict=decision.verdict,
        reason=decision.reason,
        market_signal=market_signal,
        invariant_check=decision.violated_invariants or []
    )
```

---

## OUTPUT ARTIFACTS (WHAT ORACLE TOWN PRODUCES)

### Ranked Backlog

```typescript
interface RankedBacklog {
  timestamp: string;
  initiatives: RankedInitiative[];
  viability_status: {
    in_region: boolean;
    violated_invariants: string[];
  };
}

interface RankedInitiative {
  initiative_id: string;
  rank: number;

  predicted_uplift: {
    distribution: Distribution;
    p50: number;
    p90: number;
    confidence_interval: [number, number];
  };

  calibration_score: {
    brier_score: number;
    log_score: number;
    predictor_track_record: PredictorScore[];
  };

  invariants_impact: {
    invariant_id: string;
    current_value: number;
    projected_value: number;
    within_threshold: boolean;
  }[];

  decision: {
    verdict: "GO" | "NO_GO" | "ITERATE";
    reason_codes: string[];
    rationale_url: string;
    data_links: string[];
  };

  falsification_tests: {
    test_name: string;
    could_have_killed: boolean;
    survived: boolean;
    evidence_log: string;
  }[];
}
```

### Public Dashboard

**URL:** `/oracle-town/dashboard`

**Components:**
1. **Viability Status Board**
   - 8 invariants with current values + thresholds
   - Traffic light: green (in 𝒱), red (breach)

2. **Active Initiatives**
   - Ranked by certified margin
   - Prediction probabilities + calibration scores
   - Invariant impact projections

3. **Resolution Tracker**
   - Resolved questions with outcomes
   - Calibration curve (predicted vs actual)
   - Predictor leaderboard (by Brier score)

4. **Anomaly Alerts**
   - Gaming detection flags
   - Sybil cluster reports
   - Wash trading incidents

---

## MINIMAL 4-WEEK LAUNCH

### Week 1: Define + Baseline

**Deliverables:**
- [ ] 10 prediction questions (2 per type)
- [ ] KPI baselines (historical 90-day average)
- [ ] 8 invariants with thresholds
- [ ] Anti-gaming detection rules
- [ ] Public dashboard (read-only)

**Example Questions:**
1. "Will Event X increase Zone A occupancy by ≥ 8%?"
2. "Will Offer Bundle Y raise avg spend by ≥ €15?"
3. "Will complaint rate stay ≤ 3% with 15% traffic increase?"
...

### Week 2: First Prediction Cycle + Pilot

**Deliverables:**
- [ ] Run prediction market for 10 questions (7 days)
- [ ] Select 2 initiatives with highest certified margin
- [ ] Run gate check (viability + margin)
- [ ] Execute 2 pilot initiatives
- [ ] Log all decisions with rationale + data links

**Gate Check Example:**
```
Initiative: "Launch Jazz Festival in Old Town"
Market Probability: 0.78 (occupancy increase ≥ 8%)
Invariant Impact:
  - I3 Budget Integrity: +5% spend (WITHIN threshold)
  - I5 Service Quality: complaint rate projected 2.8% (WITHIN threshold)
  - I7 Calibration: Brier score 0.18 (WITHIN threshold)

Gate Decision: ACCEPT
Certified Margin: +12% occupancy (CI: [+8%, +16%])
Noise Band: ±5%
Margin > Noise: YES (12% > 5%)

Verdict: GO
```

### Week 3: Measure + Calibrate

**Deliverables:**
- [ ] Collect resolution data (30 days post-launch)
- [ ] Compute calibration scores (Brier, log score)
- [ ] Update predictor leaderboard
- [ ] Publish resolution report with evidence
- [ ] Audit transparency (I₁) + fairness (I₂)

**Calibration Report:**
```
Resolved Questions: 2
Question 1: Jazz Festival Occupancy
  - Predicted: 78% chance of ≥ 8% increase
  - Actual: 11% increase (YES)
  - Brier Score Contribution: (0.78 - 1)² = 0.048

Question 2: Offer Bundle Spend
  - Predicted: 65% chance of ≥ €15 increase
  - Actual: €12 increase (NO)
  - Brier Score Contribution: (0.65 - 0)² = 0.423

Aggregate Brier Score: 0.236 (WITHIN threshold 0.25)
```

### Week 4: Expand + Anti-Gaming

**Deliverables:**
- [ ] Expand to 5 initiatives
- [ ] Enable anti-gaming checks (I₈)
- [ ] Run anomaly detection on all predictions
- [ ] Flag suspicious patterns for review
- [ ] Publish weekly viability report

**Anti-Gaming Enforcement:**
```
Anomaly Detection Run: 2026-01-16

Participants Scanned: 47
Anomalies Detected: 2

[ALERT 1]
User ID: U-00234, U-00235
Pattern: Identical predictions on 8/10 questions
Correlation: 0.96
Action: FLAGGED for review

[ALERT 2]
User ID: U-00891
Pattern: 15 predictions submitted within 90 seconds
Temporal Clustering Score: 0.18 (above threshold 0.15)
Action: AUTO-REJECTED
```

---

## THE "SURPRISING" ADVANTAGE

### What Most Towns Do (FAILS)

```
Committee Meeting:
  → Debate for 2 hours
  → Loudest voice wins
  → No baseline, no measurement
  → "Let's try it and see"
  → No follow-up
  → Drifts over time
```

### What Oracle Town Does (IFG)

```
Prediction Market:
  → Propose initiative
  → Generate prediction question
  → Collect market signal
  → Estimate invariant impact
  → Run gate (viability + margin)
  → Accept/reject deterministically
  → Measure outcome
  → Update calibration
  → Publish evidence
```

**Key Difference:**
- Narrative is GENERATED (by market), but CONSTRAINED (by invariants)
- Innovation is GENERATED (by proposals), but FILTERED (by gate)
- Decisions are CONTROLLED DYNAMICAL SYSTEM output, not committee drift

---

## INTEGRATION WITH POC FACTORY

See: `IFG_COUPLING_CONTRACT.md`

**Oracle Town sends to POC Factory:**
- Ranked hypotheses with impact distributions
- Constraints (invariants that matter politically/operationally)
- Budget envelope

**POC Factory returns to Oracle Town:**
- Capability certificate (what is technically achievable)
- Measured uplift distributions
- Cost curves
- Failure modes and where invariants break

---

## FORMAL GUARANTEES

### Theorem 1: Viability Preservation
```
∀ initiative i: accept(i) ⟹ new_state ∈ 𝒱
```
**Proof:** Gate rejects any Δ that violates invariants. ∎

### Theorem 2: No Arbitrary Decisions
```
∀ decision d: d has rationale ∧ d has data_links ∧ d passes gate
```
**Proof:** I₁ (transparency) enforces rationale + links. Gate is deterministic. ∎

### Theorem 3: Calibration Accountability
```
∀ predictor p: track(p.brier_score) over time
```
**Proof:** I₇ requires Brier score computation on all resolved questions. ∎

---

## CONSTITUTIONAL GUARANTEES

From ORACLE SUPERTEAM v1.0, preserved:

1. ✅ **NO_RECEIPT = NO_SHIP** → No initiative without evidence
2. ✅ **Non-Sovereign Agents** → Predictions propose, gate decides
3. ✅ **Binary Verdicts** → GO or NO_GO only
4. ✅ **Kill-Switch Dominance** → I₆ violation auto-rejects
5. ✅ **Replay Determinism** → Same inputs → same verdict

New in IFG:

6. ✅ **Viability Preservation** → All changes stay in 𝒱
7. ✅ **Certified Margin Required** → Improvement beyond noise
8. ✅ **Calibration Accountability** → Brier score tracking
9. ✅ **Anti-Gaming Enforcement** → I₈ anomaly detection
10. ✅ **Transparency by Design** → I₁ enforced in gate

---

## NEXT STEPS

### Immediate (Week 1)
- [ ] Deploy invariants dashboard
- [ ] Define 10 prediction questions
- [ ] Set up data pipelines for baselines

### Short-Term (Month 1)
- [ ] Run first prediction cycle
- [ ] Execute 2 pilot initiatives
- [ ] Measure + calibrate

### Medium-Term (Quarter 1)
- [ ] Expand to 20 initiatives
- [ ] Integrate POC Factory coupling
- [ ] Enable public participation

---

## CITATION

```bibtex
@software{oracle_town_ifg,
  title={ORACLE TOWN: Invariance-First Generativity for Civic Prediction},
  author={JMT Consulting},
  year={2026},
  version={1.0-IFG},
  framework={Viability-Thermostat System},
  url={https://github.com/yourusername/oracle-superteam}
}
```

---

**This is not a conversation. This is an institution.**

**Status:** ✅ READY FOR IMPLEMENTATION
**Date:** January 16, 2026
**Version:** 1.0-IFG
