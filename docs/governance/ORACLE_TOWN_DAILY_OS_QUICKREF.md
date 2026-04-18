# ORACLE TOWN Daily OS — Quick Reference

Your CLAUDE.md has been evolved to position ORACLE TOWN as an **autonomous daily operating system** that continuously collects observations, discovers patterns, and evolves its own governance policies.

## Five Operating Modes

```
┌──────────────────────────────────────────────────────────────┐
│                    ORACLE TOWN DAILY OS                       │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  MODE 1: DAILY DIGEST               (Every 24 hours)         │
│  ├─ Collect observations from past day                        │
│  ├─ Compile to claims & run districts                         │
│  ├─ Emit verdicts + insights                                  │
│  └─ Measure accuracy, adapt thresholds                        │
│                                                                │
│  MODE 2: CONTINUOUS MONITORING      (Every 30 min)           │
│  ├─ Poll observation sources                                  │
│  ├─ Real-time claim processing                                │
│  ├─ High-confidence alerts                                    │
│  └─ Continuous learning in real-time                          │
│                                                                │
│  MODE 3: WEEKLY SYNTHESIS           (Every Friday)           │
│  ├─ Aggregate all verdicts/outcomes from week                 │
│  ├─ Deep pattern detection                                    │
│  ├─ Measure district accuracy                                 │
│  └─ Generate policy recommendations                           │
│                                                                │
│  MODE 4: INTERACTIVE EXPLORER       (On-demand)              │
│  ├─ Ask the town natural language questions                   │
│  ├─ Memory linker searches ledger                             │
│  ├─ Synthesize answer from historical decisions               │
│  └─ Get decision provenance + reasoning                       │
│                                                                │
│  MODE 5: SCENARIO SIMULATOR         (Ad-hoc)                 │
│  ├─ Test "what-if" policy changes                             │
│  ├─ Replay past 100 claims through new policy                 │
│  ├─ Compare outcomes & accuracy impact                        │
│  └─ Make informed policy decisions                            │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Daily OS Architecture

```
YOUR INPUT (Observations)
  ↓
  ├─ Email (auto-summary top unread)
  ├─ Meeting notes (yesterday's meetings)
  ├─ Metrics (KPI snapshots)
  └─ Manual note (quick observations)
       ↓
  CLAIM COMPILATION
  ├─ Intake Guard validates schema
  ├─ Claim Compiler structures claims
  └─ Memory Linker finds past precedents
       ↓
  PARALLEL ANALYSIS
  ├─ Legal & Compliance District
  ├─ Technical & Metrics District
  ├─ Business & Opportunity District
  └─ Insight & Pattern District (NEW)
       ↓
  AGGREGATION + LEARNING
  ├─ QI-INT v2 scoring
  ├─ Accuracy measurement vs. history
  └─ Threshold refinement
       ↓
  MAYOR VERDICT
  ├─ Binary: SHIP / NO_SHIP
  ├─ Remediation guidance
  └─ Pattern alerts
       ↓
  LEDGER RECORD + EVOLUTION
  ├─ Append decision immutably
  ├─ Feedback loop: Did this work?
  └─ Update town memory & thresholds
       ↓
  YOUR DASHBOARD
  ├─ Today's verdicts + insights
  ├─ Emerging patterns (week/month)
  └─ Town evolution metrics
```

## Quick Start Commands

### Mode 1: Daily Digest (Recommended Start)
```bash
# Run every 24 hours at 9 AM
python3 oracle_town/os_runner.py --mode daily --time 09:00 --daemon

# View insights in web dashboard
open http://localhost:5000/daily-digest
```

### Mode 2: Continuous Monitoring
```bash
# Check for new observations every 30 minutes
python3 oracle_town/os_runner.py --mode continuous --check-interval 30m

# Real-time alerts will be emitted
```

### Mode 3: Weekly Synthesis
```bash
# Run every Friday at 5 PM for deep pattern detection
python3 oracle_town/os_runner.py --mode weekly --day friday --time 17:00

# Read weekly report
open http://localhost:5000/weekly-synthesis
```

### Mode 4: Interactive Explorer (Use Right Now)
```bash
# Ask the town questions interactively
python3 oracle_town/interactive_explorer.py

# Examples:
# > What vendors have we approved in Healthcare?
# > Show weeks where we had most claims
# > Why did we SHIP the email campaign?
# > Patterns emerging this month?
```

### Mode 5: Scenario Simulator
```bash
# Test new policy before applying
python3 oracle_town/scenario_simulator.py --scenario new_policy.json

# Review impact report
# Example: Raising Technical threshold from 75 to 85
# Output: Shows 8 of 100 past claims would change verdict
```

## Key New Capabilities

### 🧠 Self-Evolution
The town learns from its own decisions:
- Measures accuracy daily
- Adjusts district thresholds based on performance
- Versions policies to maintain audit trail
- Uses real-world feedback to improve

### 📚 Memory & Precedent
When analyzing new claims:
- Searches ledger for similar past decisions
- Finds successful precedents
- Updates confidence based on historical accuracy
- Explains reasoning with evidence references

### 🔍 Insight Engine
Continuous pattern detection discovers:
- **Temporal Patterns:** When do events cluster?
- **Anomalies:** What's unusual this week?
- **Emerging Themes:** What's trending?
- **Accuracy Signals:** Which districts predict best?
- **Opportunities:** What's working really well?

### 📊 Dashboard
Real-time visibility into town activity:
- Verdicts and outcomes
- Emerging patterns
- Accuracy metrics by district
- Policy evolution recommendations

## Self-Evolution Example

**Day 1:** SHIP decision "Launch email campaign A"
↓
**Day 8:** Outcome measured → "12% CTR, exceeded 10% target"
↓
**Week 2:** Accuracy measured
- Legal: 85% (stable)
- Technical: 72% (too permissive, raise 5%)
- Business: 91% (too strict, lower 3%)
↓
**Policy Updated:** Districts now use refined thresholds
↓
**Old Decisions Protected:** Email campaign decision pinned to original policy version
↓
**Learning Continues:** Each claim improves the town

## Memory Linker in Action

```bash
python3 oracle_town/interactive_explorer.py

> What vendor decisions have we made in Healthcare?

RESULTS (from ledger):
  2026-01-15: HealthCorp proposal → SHIP
    Legal: ✓ Compliance OK
    Technical: ✓ Security review passed
    Business: ✓ ROI justified
    Outcome: Active, no incidents

  2026-01-10: MediData integration → NO_SHIP
    Legal: ✗ Data residency violation
    Technical: ✓ System ready
    Business: ✓ Cost justified
    Reason: Legal blocking critical

  2025-12-28: DataHealth vendor → SHIP (with remediation)
    Legal: ~ Approved with audit obligation
    Technical: ✓ Platform validated
    Business: ✓ Cost effective
    Outcome: Audit completed on time, zero incidents

> Why did we SHIP DataHealth if it had concerns?

RESPONSE:
  Technical & Business districts validated remediation plan.
  Legal added obligation: "Annual audit required by Q2."
  Historical accuracy: 92% for vendors with remediation.
  This decision proved sound (audit completed successfully).
```

## Insight Engine Output Example

```
ORACLE TOWN INSIGHTS — 2026-01-30

ALERTS
├─ Vendor proposal queue +40% vs last week
├─ Thursday submissions bypass quorum 2x (pattern detected)
└─ Data privacy mentions: 40% of claims (vs 15% baseline)

EMERGING PATTERNS
├─ "Data retention" topic: 5/7 claims (trend change)
├─ Security flags: 35% of claims (was 18% month ago)
└─ Email campaigns: 100% SHIP rate (8/8), proven high confidence

ACCURACY IMPROVEMENTS
├─ Technical district: 81% → 89% (Policy V5 change effective)
├─ Business district: 84% → 87% (Threshold adjustment helped)
└─ Legal district: 82% → 82% (stable, no change needed)

OPPORTUNITIES
├─ Email campaigns: Expand budget? (Perfect record, high accuracy)
└─ Vendor approvals: 3 successful Healthcare vendors could signal industry shift

RECOMMENDATIONS
├─ Schedule security training (spike in Technical flags)
├─ Update privacy policy (emerging concern in claims)
└─ Consider email campaign expansion (proven track record)
```

## New Files in CLAUDE.md

The updated CLAUDE.md now includes comprehensive documentation for:

1. **Daily OS Architecture** (Overview section)
   - Complete flow from observations → insights
   - Self-evolution explained
   - Memory linkage mechanism

2. **Daily OS Operation Modes** (New dedicated section)
   - 5 modes with detailed process + commands
   - When to use each mode
   - Expected output

3. **New Modules** (Key Files section)
   - `oracle_town/os_runner.py` — Scheduler
   - `oracle_town/insight_engine.py` — Pattern detection
   - `oracle_town/self_evolution.py` — Learning & adaptation
   - `oracle_town/memory_linker.py` — Historical search
   - `oracle_town/observation_collector.py` — Data ingestion
   - `oracle_town/dashboard_server.py` — Web UI

4. **Daily OS Scenarios** (Common Development Scenarios)
   - OS-1: Set up daily digest
   - OS-2: Measure & evolve accuracy
   - OS-3: Search memory for precedents
   - OS-4: Detect emerging patterns

5. **New Invariants** (Architecture Enhancements)
   - K10: Memory Linkage
   - K11: Feedback Loop
   - K12: Policy Versioning
   - K13: Insight Validity
   - K14: Observation Provenance

## Key Principles

**Autonomous:** Town runs on its own schedule; you don't need to submit claims manually

**Learning:** Measures accuracy daily, refines policies automatically

**Transparent:** All decisions auditable, insights reproducible from ledger

**Precedent-Aware:** New decisions informed by historical success/failure

**Evolving:** Districts improve over time; thresholds adjust automatically

**Insightful:** Continuous pattern detection surfaces opportunities and anomalies

## Next Phase: Implementation

To fully realize this Daily OS, implement these modules in order:

1. **os_runner.py** — Orchestrate scheduling and execution
2. **observation_collector.py** — Ingest from email, notes, metrics
3. **memory_linker.py** — Search and cross-reference historical decisions
4. **insight_engine.py** — Pattern detection engine
5. **self_evolution.py** — Accuracy measurement and policy refinement
6. **interactive_explorer.py** — Natural language Q&A interface
7. **scenario_simulator.py** — Policy testing and impact analysis
8. **dashboard_server.py** — Real-time web UI for insights

Each integrates with existing governance core (Mayor, Districts, Ledger, Crypto).

---

**Your ORACLE TOWN now operates as a personal autonomous intelligence system that learns daily and discovers insights for you continuously.**
