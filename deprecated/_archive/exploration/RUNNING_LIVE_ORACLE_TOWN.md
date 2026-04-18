# Running Oracle Town Live

**How to watch the jurisdiction build in real time**

---

## Three Ways to Run

### 1. Demo Mode (Easiest)

Watch 10 cycles of simulated observations flowing through the system:

```bash
python3 oracle_town/live_monitor.py --cycles 10
```

**What you'll see:**
- Each cycle shows observations arriving
- Verdicts being issued (ACCEPT/REJECT)
- Insights being generated
- Town structure updating in real time

**No data required.** Simulation generates observations automatically.

---

### 2. Dashboard (Most Visual)

Start the web server and view visualizations in your browser:

```bash
python3 oracle_town/dashboard_server.py
```

Then open:
- **Dashboard:** http://localhost:5000
- **ASCII snapshot:** http://localhost:5000/api/city-state/ascii
- **HTML iso-coaster:** http://localhost:5000/api/city-state/iso-html

**What you'll see:**
- Real-time REST API with verdicts
- ASCII and HTML/SVG visualizations
- Historical search and filtering

Ctrl+C to stop.

---

### 3. Interactive Python REPL

Explore the live monitor directly:

```python
from oracle_town.live_monitor import LiveMonitor

monitor = LiveMonitor()
monitor.load_verdicts_from_ledger("oracle_town/ledger")

# Simulate observations
for i in range(5):
    monitor.simulate_observation_cycle()
    monitor.display_cycle()

# View current state
ascii_snapshot = monitor.render_ascii()
html_visualization = monitor.render_html()
```

---

## What the Monitor Shows

### ASCII Snapshot

Fixed 47-character width display showing:
- Module status (OK, OFF, FAIL)
- Data flow (observation → analysis → verdict)
- Verdict counts (accepts vs rejects)
- Policy version pinned for this run

**What it does NOT do:**
- Predict future verdicts
- Show confidence scores
- Animate progress
- Make inferences about what "should" happen

---

## How the Town "Builds"

Each cycle:

1. **Observation arrives** → OBS marked OK
2. **Pattern detected** → INSIGHT marked OK
3. **Verdict issued** → TRI marked OK
4. **Publication** → PUBLISH marked OK

The visual structure shows which stages are active.

---

## Best Practices

**Do:**
✓ Observe silence (OFF doesn't mean bad—it means no data yet)
✓ Notice patterns (watch reject rates evolve)
✓ Trust immutability (once a verdict is issued, it is locked)

**Don't:**
✗ Predict future verdicts
✗ Confuse activity with correctness
✗ Rush to "fix" OFF modules

---

## Integration

### Daily Check

```bash
python3 oracle_town/live_monitor.py --ledger oracle_town/ledger --cycles 1
```

### Continuous Monitoring

```bash
python3 oracle_town/dashboard_server.py &
# Open http://localhost:5000/api/city-state/ascii
```

### Feed Real Decisions

```bash
# Collect observations from email, notes, metrics
python3 oracle_town/observation_collector.py --source email

# Visualize the town as it builds
python3 oracle_town/live_monitor.py --ledger oracle_town/ledger --cycles 1
```

---

**Start with Demo Mode. Observe for 10 cycles. The town will build itself, piece by piece, refusal by refusal.**
