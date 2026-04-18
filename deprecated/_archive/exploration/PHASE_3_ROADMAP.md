# Oracle Town Phase 3: Integration & Dashboard

**Date:** 2026-01-30
**Status:** Planning (Phase 2 ✅ Complete, Phase 3 🚧 Ready to Code)
**Target:** Operational intelligence + real-time monitoring

---

## Phase 3 Goals

Move Oracle Town from **decision-making system** to **operational intelligence platform**:

1. **Real-time Dashboard** — Web UI showing kernel activity, verdicts, and insights
2. **Moltbot Integration** — Official kernel module for Anthropic's agent framework
3. **Pattern Detection Engine** — Auto-discover patterns, anomalies, and opportunities
4. **Self-Evolution Loop** — Measure accuracy, refine thresholds, adapt policy

---

## Component Breakdown

### Component 1: Dashboard Server (300 lines)

**Purpose:** Real-time web UI for monitoring kernel activity

**Endpoints:**
- `GET /api/status` — Daemon health, uptime, kernel version
- `GET /api/recent-verdicts` — Last 50 verdicts with outcomes
- `GET /api/insights` — Patterns, anomalies, emerging themes (last 7 days)
- `GET /api/metrics` — Acceptance rate, avg decision time, district accuracy
- `GET /api/ledger?claim_id=...` — Search/retrieve historical decisions
- `WebSocket /ws/live` — Real-time verdict stream (as decisions arrive)

**Frontend Stack:**
- HTML5 + vanilla JavaScript (no dependencies)
- Responsive grid layout
- Real-time chart updates (Chart.js)
- Search/filter interface

**Fail-Closed Design:**
- Dashboard shows only historical data (read-only)
- Cannot modify verdicts, policy, or ledger from UI
- Authentication: Simple token-based (stored in daemon config)

---

### Component 2: Moltbot Integration (250 lines)

**Purpose:** Official kernel module for Claude-based agents

**Location:** `oracle_town/integrations/moltbot_kernel.py`

**API:**
```python
from oracle_town.integrations.moltbot_kernel import MoltbotKernel

kernel = MoltbotKernel()

# Integrated into Moltbot's action execution pipeline
decision = kernel.check_action(
    action="fetch",
    target="https://example.com/data.json",
    context={"user_id": "user_123", "scope": {"fetch_depth": 1}}
)

if decision.approved:
    execute_action(target)
    kernel.record_outcome(action, status="success")
else:
    log_rejection(decision.reason)
    kernel.record_outcome(action, status="rejected", reason=decision.reason)
```

**Integration Points:**
1. **Before-Action Hook** → Check proposal through kernel
2. **After-Action Hook** → Record outcome for accuracy measurement
3. **Memory Persistence** → Auto-recall kernel decisions from Supermemory
4. **Policy Updates** → Moltbot can request policy evolution based on outcomes

---

### Component 3: Pattern Detection Engine (350 lines)

**Purpose:** Auto-discover patterns, anomalies, and opportunities

**Location:** `oracle_town/insight_engine.py`

**Pattern Types:**

1. **Temporal Patterns** — Frequency analysis
   ```
   Example: "70% of vendor claims arrive Tuesday morning"
   Detected by: Day-of-week histogram + chi-square test
   ```

2. **Anomaly Detection** — Statistical outliers
   ```
   Example: "Approval rate dropped 25% this week (was 80%, now 55%)"
   Detected by: Rolling mean + std dev bounds
   ```

3. **Correlation Patterns** — Cross-domain relationships
   ```
   Example: "When Legal flags + Technical flags both set, 90% are rejected"
   Detected by: Contingency table analysis
   ```

4. **Emerging Themes** — NLP topic clustering
   ```
   Example: "Data retention concerns appeared in 5 of 7 claims this week"
   Detected by: TF-IDF + K-means clustering
   ```

5. **Accuracy Signals** — Predictive power by source
   ```
   Example: "Technical district 94% accurate, Legal 78%"
   Detected by: Confusion matrix per district, measured against outcomes
   ```

6. **Opportunity Recognition** — High-confidence low-risk segments
   ```
   Example: "Email campaigns: 100% approval rate, high satisfaction scores"
   Detected by: Stratified analysis by claim type + outcome rating
   ```

**Output Format:**
```json
{
  "timestamp": "2026-01-30T17:00:00Z",
  "insights": [
    {
      "type": "anomaly",
      "severity": "medium",
      "title": "Vendor approval rate -25%",
      "description": "Approval rate dropped from 80% to 55% this week",
      "evidence": {
        "past_rate": 0.80,
        "current_rate": 0.55,
        "sample_size": 20,
        "statistical_significance": 0.94
      },
      "recommendation": "Review policy thresholds or changed threat landscape"
    }
  ]
}
```

---

### Component 4: Self-Evolution Module (300 lines)

**Purpose:** Measure verdict accuracy, refine thresholds, adapt policy

**Location:** `oracle_town/self_evolution.py`

**Process:**

1. **Accuracy Measurement** (Weekly)
   ```
   For each verdict from 7 days ago:
     - Retrieve actual outcome (feedback)
     - Compare verdict against outcome
     - Score accuracy per district
     - Flag districts with drift (accuracy changed >5%)
   ```

2. **Threshold Refinement**
   ```
   For each threshold:
     - If accuracy drops, lower threshold (more permissive)
     - If accuracy improves, raise threshold (more strict)
     - Generate recommendation with impact analysis
   ```

3. **Policy Versioning**
   ```
   Old policy pinned to old decisions (K12 invariant)
   New policy version created with updated thresholds
   All future decisions use new policy
   Determinism preserved: same claim + same policy = same verdict
   ```

4. **Feedback Integration**
   ```
   Sources of feedback:
     - User ratings: "This verdict was correct/incorrect"
     - Outcome measurement: Actual business results
     - Incident reports: "This approved action caused incident"
   ```

---

### Component 5: Memory Linker (250 lines)

**Purpose:** Search historical decisions and surface precedents

**Location:** `oracle_town/memory_linker.py`

**Capabilities:**

1. **Full-Text Search**
   ```python
   results = memory.search("vendor healthcare proposal")
   # Returns: Similar past vendor decisions with outcomes
   ```

2. **Semantic Similarity**
   ```python
   similar = memory.find_similar(current_claim, threshold=0.85)
   # Returns: Semantically similar past claims + verdicts
   ```

3. **Precedent Analysis**
   ```python
   precedents = memory.analyze_precedents(current_vendor_id)
   # Returns: All past decisions about this vendor, success rate
   ```

4. **Cross-Reference Integration**
   ```
   When analyzing new claim:
     - Search for similar past claims
     - Link to precedent verdicts
     - Update confidence based on historical accuracy
     - Surface "This vendor was rejected 3x before" type insights
   ```

---

### Component 6: Observation Collector (200 lines)

**Purpose:** Ingest observations from multiple sources → Structured claims

**Location:** `oracle_town/observation_collector.py`

**Input Sources:**

1. **Email** (via IMAP)
   - Auto-summarize top 5 unread emails
   - Extract structured facts
   - Tag by domain (vendor, technical, business)

2. **Meeting Notes** (JSON format)
   ```json
   {
     "meeting": "Q1 Planning",
     "date": "2026-01-30",
     "observations": [
       "Security concern raised about vendor X",
       "Budget approved for tool Y",
       "Performance issues with component Z"
     ]
   }
   ```

3. **Metrics & Events**
   - KPI snapshots (daily)
   - Incident reports
   - Approval/rejection feedback

4. **Manual Input** (CLI or API)
   ```bash
   oracle-town observe "User reported bug in feature X"
   ```

**Output:** Structured claim ready for district analysis

---

## Phase 3 Implementation Order

### Week 1: Foundation
1. Create Dashboard Server (`dashboard_server.py`)
   - Simple HTTP server (Flask or native)
   - API endpoints for status, verdicts, metrics
   - Static HTML frontend
   - Test with kernel daemon running

2. Observation Collector (`observation_collector.py`)
   - Email ingestion (IMAP)
   - JSON parsing for meeting notes
   - Manual CLI input
   - Verify observation → claim conversion

### Week 2: Intelligence
3. Insight Engine (`insight_engine.py`)
   - Temporal pattern detection
   - Anomaly scoring
   - Emerging theme clustering
   - Dashboard integration

4. Memory Linker (`memory_linker.py`)
   - Ledger search interface
   - Semantic similarity matching
   - Precedent analysis
   - Integration with district analysis

### Week 3: Adaptation
5. Self-Evolution Module (`self_evolution.py`)
   - Accuracy measurement
   - Threshold refinement
   - Policy versioning
   - Feedback integration

6. Moltbot Integration (`moltbot_kernel.py`)
   - Official module
   - Before/after hooks
   - Outcome recording
   - Documentation + examples

### Week 4: Integration & Polish
7. End-to-end testing
   - Dashboard with real kernel activity
   - Pattern detection on historical data
   - Self-evolution feedback loop
   - Moltbot integration test scenarios

8. Documentation & deployment
   - Phase 3 completion summary
   - Deployment guide
   - Operations runbook

---

## Architecture Diagram

```
OBSERVATION LAYER (Your Input)
  ├─ Email (auto-parsed)
  ├─ Meeting notes (structured)
  ├─ Metrics (KPIs, events)
  └─ Manual observations (CLI)
       ↓
OBSERVATION COLLECTOR
  ├─ Parse & validate
  ├─ Extract structured facts
  └─ Create claims
       ↓
KERNEL PIPELINE (Phases 1-2)
  ├─ Gate A (Fetch safety)
  ├─ Gate B (Memory safety)
  ├─ Gate C (Invariants)
  ├─ Mayor (Receipt generation)
  └─ Ledger (Immutable record)
       ↓
INSIGHT ENGINE (Phase 3)
  ├─ Pattern detection
  ├─ Anomaly scoring
  ├─ Theme clustering
  └─ Opportunity recognition
       ↓
MEMORY LINKER (Phase 3)
  ├─ Ledger search
  ├─ Semantic matching
  └─ Precedent analysis
       ↓
SELF-EVOLUTION (Phase 3)
  ├─ Accuracy measurement
  ├─ Threshold refinement
  ├─ Policy versioning
  └─ Feedback integration
       ↓
DASHBOARD & REPORTING (Phase 3)
  ├─ Real-time verdicts
  ├─ Pattern insights
  ├─ Accuracy metrics
  └─ Policy recommendations
       ↓
AGENT INTEGRATION (Moltbot, OpenClaw, etc.)
  ├─ Official modules
  ├─ Before/after hooks
  └─ Outcome feedback
```

---

## Success Criteria

### Dashboard
- [ ] Real-time verdict stream via WebSocket
- [ ] Search historical decisions (full-text + filter)
- [ ] Insights visible within 5 seconds of generation
- [ ] Zero DOM errors in browser console

### Pattern Detection
- [ ] Temporal patterns detected (day-of-week, time-of-day)
- [ ] Anomalies surfaced with statistical significance (p < 0.05)
- [ ] Emerging themes clustered (TF-IDF based)
- [ ] Accuracy per district measured and displayed

### Self-Evolution
- [ ] Accuracy measurement accurate (matches manual audit)
- [ ] Threshold changes produce expected verdict changes
- [ ] Policy versions immutable (K12 enforced)
- [ ] Feedback integration automatic (outcomes recorded)

### Moltbot Integration
- [ ] Official module in `oracle_town/integrations/`
- [ ] Before-action hook prevents unsafe actions
- [ ] Outcome recording enables accuracy measurement
- [ ] Documentation + 3 example scenarios

---

## New Invariants (Phase 3)

| Invariant | Description | Enforcement |
|-----------|-------------|------------|
| **K10** | Memory Linkage | All new verdicts reference relevant historical decisions |
| **K11** | Feedback Loop | Outcomes must be recordable; accuracy measured automatically |
| **K12** | Policy Versioning | Policy changes create new version; old claims pinned to version at time of decision |
| **K13** | Insight Validity | All insights must be reproducible from ledger data |
| **K14** | Observation Provenance | Every observation records source (email, meeting, manual, API) |

---

## Risk Mitigation

**Risk:** Insight generation creates new decision points (could weaken fail-closed)
**Mitigation:** Insights are advisory only; humans approve policy changes before apply

**Risk:** Self-evolution with wrong feedback ruins thresholds
**Mitigation:** Dry-run simulation shows impact before changes apply; old policy retained

**Risk:** Dashboard becomes source of truth (overwrites ledger)
**Mitigation:** Dashboard read-only; all mutations require ledger entry + receipt

**Risk:** Moltbot integration creates tight coupling
**Mitigation:** Integration via standard KernelClient; Moltbot remains independent

---

## Deployment

### Development (Local)
```bash
# Start kernel daemon
python3 oracle_town/kernel/kernel_daemon.py &

# Start dashboard
python3 oracle_town/dashboard_server.py

# Open browser
open http://localhost:5000
```

### Production
```bash
# systemd service for kernel daemon
sudo tee /etc/systemd/system/oracle-town-kernel.service <<EOF
[Unit]
Description=Oracle Town Kernel Daemon
After=network.target

[Service]
Type=simple
User=oracle
ExecStart=/usr/bin/python3 /opt/oracle-town/kernel_daemon.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable oracle-town-kernel
sudo systemctl start oracle-town-kernel

# Docker container for dashboard
docker run -d \
  --name oracle-town-dashboard \
  -p 5000:5000 \
  -v ~/.openclaw:/home/oracle/.openclaw \
  oracle-town:v0.2
```

---

## Timeline

**Week 1-4:** Phase 3 Implementation (1,300 total new lines)
**Week 5:** Testing, documentation, security review
**Week 6:** Public beta, feedback integration
**Target Release:** Mid-February 2026

---

## Status

**Phase 1:** ✅ Complete (Gate A, Mayor, Ledger)
**Phase 2:** ✅ Complete (Gate B, Gate C, Daemon, Client)
**Phase 3:** 🚧 Ready to Code (Dashboard, Insights, Evolution, Integration)

**Next Action:** User approval to begin Phase 3 implementation

---

**Estimated Effort:** 4-5 weeks solo, ~2 weeks with pair programming
**Critical Path:** Dashboard + Observation Collector → Insight Engine → Self-Evolution → Moltbot

