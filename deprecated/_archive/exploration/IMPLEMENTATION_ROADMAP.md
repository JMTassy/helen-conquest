# ORACLE TOWN Daily OS — Implementation Roadmap

Your CLAUDE.md has been evolved. Here's how to build the autonomous Daily OS in phases.

## Current State vs. Target

### Current (Governance Decision-Making)
```
Raw Claim
  ↓
[Intake Guard] → Validate
  ↓
[Districts] → Analyze in parallel
  ↓
[Mayor] → Decide SHIP/NO_SHIP
  ↓
[Ledger] → Record decision
```

### Target (Autonomous Daily Intelligence)
```
DAILY OBSERVATIONS
(emails, notes, metrics)
  ↓
[Observation Collector] → Ingest & structure
  ↓
[Claim Compiler] → Create claims
  ↓
[Memory Linker] → Find precedents
  ↓
[Districts] → Analyze in parallel
  ↓
[Insight Engine] → Detect patterns
  ↓
[Mayor] → Decide SHIP/NO_SHIP
  ↓
[Self-Evolution] → Measure accuracy
  ↓
[Ledger] → Record + learn
  ↓
[Dashboard] → Surface insights
```

## Phase 1: Observation Ingestion (Week 1)

**Goal:** Collect daily observations and convert to claims

**Build:**
```python
# oracle_town/observation_collector.py

class ObservationCollector:
  - collect_from_email()
  - collect_from_notes()
  - collect_from_metrics()
  - collect_from_manual_input()
  - → Creates TownInput claims
```

**Commands:**
```bash
# Ingest email summaries
python3 oracle_town/observation_collector.py --source email --inbox insights@domain.com

# Ingest from local file
python3 oracle_town/observation_collector.py --source file --path daily_notes.json

# Manual input
python3 oracle_town/observation_collector.py --manual "Attended board meeting, discussed Q1 planning"
```

**Integration:** Feed observations into existing `orchestrator.py` processing pipeline

**Success Criteria:**
- Convert 5+ observations/day → valid TownInput claims
- Preserve source metadata (where did observation come from?)
- Pass intake guard validation

---

## Phase 2: Memory Linker (Week 2)

**Goal:** Search historical decisions and find precedents

**Build:**
```python
# oracle_town/memory_linker.py

class MemoryLinker:
  - search_by_topic(claim_topic) → Similar past decisions
  - search_by_outcome(claim, success=True) → What succeeded?
  - search_by_district_verdict(district_id, verdict) → Historical patterns
  - semantic_similarity(claim) → Analogous past claims
```

**Database/Index:**
- Full-text search on ledger decisions
- Semantic embeddings for similarity (use existing district analysis)
- Outcome tracking (what really happened after we decided SHIP?)

**Commands:**
```bash
# Interactive search
python3 oracle_town/memory_linker.py --query "Email campaigns in 2025"

# Programmatic usage (in districts)
from oracle_town.memory_linker import MemoryLinker
ml = MemoryLinker(ledger)
precedents = ml.search_by_topic("vendor_approval")  # Returns past decisions
```

**Integration:** Pass precedents to districts as "historical context" during analysis

**Success Criteria:**
- Search 1000+ historical decisions in <1s
- Find semantically similar claims (>80% relevance)
- Surface accuracy metrics for precedents

---

## Phase 3: Autonomous Scheduler (Week 3)

**Goal:** Run ORACLE TOWN on fixed cadence without manual intervention

**Build:**
```python
# oracle_town/os_runner.py

class OSRunner:
  - run_daily(time="09:00")        # Every 24 hours
  - run_continuous(interval="30m")  # Every 30 minutes
  - run_weekly(day="friday", time="17:00")  # Every Friday
  - daemon_mode()  # Run in background
```

**Config:**
```yaml
# oracle_town/config/os_schedule.yaml
daily_digest:
  enabled: true
  time: "09:00"
  observation_sources:
    - email: insights@domain.com
    - file: /data/daily_notes.json
    - metrics: /data/kpi_snapshot.json

continuous_monitoring:
  enabled: false
  check_interval: "30m"

weekly_synthesis:
  enabled: true
  day: "friday"
  time: "17:00"
```

**Commands:**
```bash
# Start daily digest daemon
python3 oracle_town/os_runner.py --mode daily --time 09:00 --daemon

# Run single cycle
python3 oracle_town/os_runner.py --mode daily --run-once

# View logs
tail -f oracle_town/logs/os_runner.log
```

**Integration:** Wraps existing `orchestrator.process()` with scheduling and observation collection

**Success Criteria:**
- Runs reliably on schedule
- Collects observations from all sources
- Processes through full pipeline daily
- Emits verdicts and records in ledger

---

## Phase 4: Insight Engine (Week 4)

**Goal:** Detect patterns and surface actionable insights

**Build:**
```python
# oracle_town/insight_engine.py

class InsightEngine:
  - detect_temporal_patterns()     # When do claims cluster?
  - detect_anomalies()             # What's unusual?
  - detect_correlations()          # Which factors co-occur?
  - detect_emerging_themes()       # What's trending?
  - measure_accuracy_signals()     # Which districts predict best?
```

**Output:**
```json
{
  "date": "2026-01-30",
  "alerts": [
    "Vendor proposal queue +40% vs last week",
    "Thursday submissions bypass quorum 2x"
  ],
  "patterns": {
    "temporal": "Email claims spike Tuesday",
    "emerging_themes": ["data_privacy", "security_compliance"],
    "anomalies": [
      {"type": "unusual_volume", "category": "vendor_proposals", "delta": "+40%"}
    ]
  },
  "accuracy_signals": {
    "technical_district": 0.89,
    "legal_district": 0.82,
    "business_district": 0.87
  },
  "opportunities": [
    "Email campaigns 100% SHIP rate, consider expanding"
  ]
}
```

**Integration:** Runs in parallel with districts, feeds results to dashboard

**Success Criteria:**
- Identify 2-3 meaningful patterns daily
- Detect actual anomalies (e.g., volume spikes)
- Measure district accuracy over time
- Surface actionable opportunities

---

## Phase 5: Self-Evolution (Week 5)

**Goal:** Measure accuracy and automatically refine policies

**Build:**
```python
# oracle_town/self_evolution.py

class SelfEvolution:
  - collect_feedback(verdict_id, outcome)  # Record real-world result
  - measure_accuracy(district_id, timeframe="7d")  # How well did this district predict?
  - recommend_threshold_change(delta_pct)  # Raise/lower threshold?
  - version_policy()  # Create new policy version with changes
  - apply_changes(approval=True)  # Apply recommendations
```

**Feedback Format:**
```json
{
  "verdict_id": "v_20260130_001",
  "claim": "Launch email campaign A",
  "decision": "SHIP",
  "outcome": "success",
  "actual_impact": "12% CTR (target: 10%)"
}
```

**Output:**
```
ACCURACY MEASURED (Week of 2026-01-30)
├─ Technical District: 89% (was 81%, +8%) ✓ Threshold stable
├─ Legal District: 82% (was 82%, ±0%) → Raise 2% (too permissive)
├─ Business District: 87% (was 84%, +3%) → Lower 3% (too strict)
└─ Overall: 86% accuracy across 45 verdicts

POLICY V6 RECOMMENDATIONS:
├─ technical_threshold: 75 → 77 (raise 2%)
├─ business_threshold: 80 → 77 (lower 3%)
└─ legal_threshold: 70 → 70 (no change)
```

**Integration:** Runs weekly; creates new policy versions; old decisions pinned to old policy

**Success Criteria:**
- Collect feedback on 80%+ of verdicts
- Measure accuracy to within 2% margin
- Recommend thresholds that improve future accuracy
- Version policies to maintain audit trail

---

## Phase 6: Interactive Explorer (Week 6)

**Goal:** Allow natural language questions about town decisions

**Build:**
```python
# oracle_town/interactive_explorer.py

class InteractiveExplorer:
  - parse_question(natural_language) → Structured query
  - search_ledger(query) → Relevant past decisions
  - synthesize_answer() → Natural language response
  - explain_reasoning() → Show decision provenance
```

**Example Interaction:**
```
USER: What vendors have we approved in Healthcare?

EXPLORER:
  Searching ledger for "vendor" AND "healthcare"...
  Found 7 decisions (2025-01-15 to 2026-01-30)

  RESULTS:
  ✓ HealthCorp proposal (2026-01-15): SHIP
    - All districts approved
    - Active, no incidents

  ✓ DataHealth vendor (2025-12-28): SHIP (with audit obligation)
    - Legal concern, approved with remediation
    - Outcome: Audit completed successfully

  ✗ MediData integration (2026-01-10): NO_SHIP
    - Legal blocker: Data residency requirement

  Summary: 2 approved, 1 rejected. Approval rate: 67%
  Historical accuracy: 92% for approved vendors
```

**Integration:** Queries ledger; uses memory linker; synthesizes with LLM

**Success Criteria:**
- Answer 80%+ of reasonable questions from ledger
- Return relevant precedents and outcomes
- Explain decision reasoning with evidence
- Support interactive multi-turn conversation

---

## Phase 7: Scenario Simulator (Week 7)

**Goal:** Test policy changes before applying

**Build:**
```python
# oracle_town/scenario_simulator.py

class ScenarioSimulator:
  - load_scenario(policy_changes)  # New thresholds to test
  - replay_claims(claims, new_policy)  # Re-evaluate past claims
  - compare_outcomes() → What would change?
  - measure_impact() → Accuracy before/after
  - generate_report() → Decision impact report
```

**Example:**
```bash
python3 oracle_town/scenario_simulator.py \
  --scenario "raise_technical_from_75_to_85.json"

IMPACT ANALYSIS:
┌─────────────────────────────────────────┐
│ New Policy: Technical threshold 75→85   │
└─────────────────────────────────────────┘

Past 100 claims re-evaluated:
├─ Verdicts changed: 8
│  ├─ SHIP → NO_SHIP: 5 (were marginal approvals)
│  └─ Unclear → NO_SHIP: 3
├─ Accuracy impact: 84% → 87% (+3%)
└─ False negative risk: 2% (claims we'd block that would succeed)

RECOMMENDATION: Apply change. Accuracy improves, risk acceptable.
```

**Integration:** Uses replay infrastructure; compares to known outcomes

**Success Criteria:**
- Replay past 100+ claims in <5s
- Predict accuracy impact within 2%
- Identify verdicts that would change
- Support human decision-making on policies

---

## Phase 8: Dashboard (Week 8)

**Goal:** Real-time web UI showing town activity and insights

**Build:**
```python
# oracle_town/dashboard_server.py

class DashboardServer:
  - /daily-digest → Today's verdicts + insights
  - /weekly-synthesis → Weekly patterns + recommendations
  - /town-metrics → Accuracy, policy evolution, district performance
  - /ledger-search → Interactive query interface
  - /insights → Real-time insight stream
  - /api/* → JSON endpoints for programmatic access
```

**Pages:**
1. **Daily Digest** — Today's observations, verdicts, insights
2. **Insights Stream** — Real-time patterns, alerts, opportunities
3. **Town Metrics** — District accuracy, policy versions, evolution history
4. **Ledger Search** — Search and browse historical decisions
5. **Interactive Explorer** — Ask questions, get answers
6. **Policy Simulator** — Test "what-if" scenarios

**Integration:** Reads from ledger; visualizes insight engine and self-evolution output

**Success Criteria:**
- Real-time updates (< 1s latency)
- Beautiful visualization of insights and metrics
- Interactive search + query
- Mobile responsive

---

## Implementation Order & Dependencies

```
Week 1: Observation Collector
  ↓
Week 2: Memory Linker (uses ledger)
  ↓
Week 3: OS Runner (uses observation collector)
  ↓
Week 4: Insight Engine (uses ledger)
  ↓
Week 5: Self-Evolution (uses ledger + insight engine)
  ↓
Week 6: Interactive Explorer (uses memory linker + insight engine)
  ↓
Week 7: Scenario Simulator (uses replay infrastructure)
  ↓
Week 8: Dashboard (aggregates all outputs)
```

**Parallel work possible:** Phases 2, 4, 6, 7 can start once Phase 3 completes.

---

## Success Metrics

After 8 weeks, your ORACLE TOWN Daily OS should:

✅ **Autonomous:** Runs daily without manual intervention
✅ **Learning:** Measures accuracy; adapts thresholds automatically
✅ **Insightful:** Surfaces 2-3 actionable insights daily
✅ **Precedent-Aware:** New decisions informed by history (92%+ accuracy for similar claims)
✅ **Transparent:** All decisions auditable; insights reproducible
✅ **Interactive:** Answer questions about past decisions in natural language
✅ **Predictive:** Simulate policy changes before applying (87%+ accuracy on impact)
✅ **Discoverable:** Dashboard shows patterns, anomalies, opportunities in real-time

---

## Key File Checklist

Once implemented, your `oracle_town/` directory will have:

```
oracle_town/
├── core/
│   ├── orchestrator.py ✓ (existing)
│   ├── mayor_rsm.py ✓ (existing)
│   ├── policy.py ✓ (existing)
│   ├── ledger.py ✓ (existing)
│   └── crypto.py ✓ (existing)
│
├── os_runtime/  (NEW PHASE 1-8)
│   ├── os_runner.py ✓ (Phase 3)
│   ├── observation_collector.py ✓ (Phase 1)
│   ├── memory_linker.py ✓ (Phase 2)
│   ├── insight_engine.py ✓ (Phase 4)
│   ├── self_evolution.py ✓ (Phase 5)
│   ├── interactive_explorer.py ✓ (Phase 6)
│   ├── scenario_simulator.py ✓ (Phase 7)
│   └── dashboard_server.py ✓ (Phase 8)
│
├── config/ (NEW)
│   └── os_schedule.yaml
│
└── logs/ (NEW)
    └── os_runner.log
```

---

## Next Step

1. Review the updated `CLAUDE.md` — it now documents all of this
2. Pick Phase 1 (Observation Collector) to start
3. Build observation ingestion → feed into existing orchestrator
4. Each phase adds one new capability
5. By week 8, you have a fully autonomous daily intelligence system

**Your CLAUDE.md is ready. Your roadmap is clear. Let's build your autonomous Daily OS.**
