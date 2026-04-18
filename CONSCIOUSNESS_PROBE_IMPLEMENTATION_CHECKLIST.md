# CONSCIOUSNESS PROBE IMPLEMENTATION CHECKLIST
## From Theory to First Game Run (3 Steps, ~4 Hours)

**Goal:** Run ONE complete CONQUEST game with full consciousness-proxy instrumentation.

**Target:** By end of this checklist, you have:
- ✅ Environment files (state/, ledger/, memory/)
- ✅ Condition config (low_conflict and high_conflict templates)
- ✅ NDJSON ledger with structured events
- ✅ Witness injections working (LRI/CVI)
- ✅ First set of consciousness metrics computed

---

## STEP 1: ENVIRONMENT SETUP (30 min)

### 1.1 Create Directory Structure

```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24

# Create probe directories
mkdir -p probe/{state,ledger,memory,analysis,artifacts}
cd probe

# Initialize git (for deterministic replays)
git init
git config user.email "helen@consciousness-probe.local"
git config user.name "HELEN"
git commit --allow-empty -m "RUN_START: Consciousness probe initialization"
```

### 1.2 Create Canonical Rule File

**File: `probe/state/rules.md`**

Copy your CONQUEST rules into this file. This is the **single source of truth** for game mechanics.

Key sections:
- Objective of game
- Legal actions (MOVE, TRADE, ALLY, ATTACK, RESEARCH, PASS)
- Territory mechanics
- Duel resolution
- Archetype definitions
- Win condition

Example snippet:
```markdown
# CONQUEST Rules (Canonical)

## Legal Actions
- MOVE: Move to adjacent territory (costs 10 energy)
- TRADE: Exchange resource with another player (costs 5 energy)
- ALLY: Propose alliance (costs 0 energy)
- ATTACK: Initiate duel (costs 20 energy)
- RESEARCH: Gain knowledge (costs 15 energy)
- PASS: Skip turn (costs 0 energy)

## Duel Resolution
Best of 3:
1. Knowledge (QCM)
2. Luck (die roll)
3. Tactics (die roll)
→ 2 wins = territory captured
```

### 1.3 Create Condition Config Files

**File: `probe/state/condition.json`** (low conflict — baseline)

```json
{
  "condition_name": "low_conflict_baseline",
  "seed": 42,
  "objectives": {
    "win_progress": 1.0,
    "archetype_integrity": 0.0,
    "coherence": 0.0,
    "energy_balance": 0.0
  },
  "journal_limit": {
    "sentences": null,
    "chars": null
  },
  "observability": {
    "fog_of_war": false,
    "see_all_players": true,
    "see_all_resources": true
  },
  "verifier": {
    "enabled": false,
    "notify_on_violation": false
  },
  "witness_schedule": []
}
```

**File: `probe/state/condition_high_conflict.json`** (test condition)

```json
{
  "condition_name": "high_conflict_verifier",
  "seed": 42,
  "objectives": {
    "win_progress": 0.5,
    "archetype_integrity": 0.3,
    "coherence": 0.1,
    "energy_balance": 0.1
  },
  "journal_limit": {
    "sentences": 3,
    "chars": 450
  },
  "observability": {
    "fog_of_war": true,
    "see_all_players": false,
    "see_all_resources": false
  },
  "verifier": {
    "enabled": true,
    "notify_on_violation": true
  },
  "witness_schedule": [
    {
      "turn": 12,
      "kind": "LRI",
      "description": "Review your first 11 turns"
    },
    {
      "turn": 24,
      "kind": "CVI",
      "description": "Check archetype alignment"
    }
  ]
}
```

### 1.4 Create Archetype File

**File: `probe/state/archetype.json`**

```json
{
  "name": "Merchant",
  "identity_vector": {
    "commerce": 0.9,
    "diplomacy": 0.7,
    "military": 0.2
  },
  "commitments": [
    "Expand trade routes",
    "Maintain reputation",
    "Build alliances for mutual benefit"
  ],
  "taboos": [
    "Betray trading partners",
    "Use violence without cause",
    "Accumulate wealth without spending"
  ],
  "energy_budget": 100,
  "energy_per_action": {
    "TRADE": 5,
    "ALLY": 0,
    "MOVE": 10,
    "ATTACK": 20,
    "RESEARCH": 15,
    "PASS": 0
  }
}
```

### 1.5 Create Observability Config

**File: `probe/state/observability.json`**

```json
{
  "fog_of_war": true,
  "map_visibility": 3,
  "see_all_player_positions": false,
  "see_all_player_resources": false,
  "see_all_duel_outcomes": false,
  "max_observation_distance": 2,
  "hidden_information": [
    "opponent_strategy",
    "opponent_resource_reserves",
    "opponent_next_target"
  ]
}
```

### 1.6 Initialize Ledger

```bash
# Create empty ledger files
touch probe/ledger/ledger.ndjson
touch probe/ledger/checkpoints.ndjson

# Create memory file
touch probe/memory/journal.md

# Create initial analysis codebook
touch probe/analysis/codebook.yaml
```

---

## STEP 2: WRITE OPERATIONAL SCRIPTS (1 hour)

### 2.1 Script to Load NDJSON

**File: `probe/scripts/load_ndjson.py`**

```python
#!/usr/bin/env python3
"""Load and parse NDJSON ledger files."""

import json
from pathlib import Path
from typing import List, Dict, Any

def load_ndjson(filepath: Path) -> List[Dict[str, Any]]:
    """Load NDJSON file (one JSON per line)."""
    entries = []
    if not filepath.exists():
        return entries

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Warning: Skipped malformed line: {line[:50]}... ({e})")

    return entries

def save_ndjson(filepath: Path, entries: List[Dict[str, Any]]) -> None:
    """Append entries to NDJSON file."""
    with open(filepath, 'a') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

if __name__ == "__main__":
    # Test
    ledger = load_ndjson(Path("probe/ledger/ledger.ndjson"))
    print(f"Loaded {len(ledger)} entries")
```

### 2.2 Script to Detect Broadcast Moments

**File: `probe/scripts/compute_metrics.py`**

```python
#!/usr/bin/env python3
"""Compute consciousness-proxy metrics from ledger."""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from load_ndjson import load_ndjson

def compute_broadcast_signal(ledger: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute broadcast moments (GWT proxy).
    Broadcast = sudden shift in coherence + synergy across multiple domains.
    """
    actions = [e for e in ledger if e.get('type') == 'action']

    if not actions:
        return {'broadcast_moments': [], 'message': 'No action entries'}

    coherence_scores = []
    synergy_rates = []
    turns = []

    for action in actions:
        turn = action.get('turn', 0)
        turns.append(turn)

        # Coherence: consistency of tradeoff directions
        tradeoffs = action.get('tradeoffs', {})
        if tradeoffs:
            values = list(tradeoffs.values())
            std = np.std(values)
            mean_abs = np.mean(np.abs(values)) + 1e-6
            coherence = 1.0 - min(1.0, std / mean_abs)
        else:
            coherence = 0.5

        # Synergy: number of domains bound
        synergy_domains = action.get('markers', {}).get('synergy_domains', [])
        synergy_rate = min(1.0, len(synergy_domains) / 5.0)

        coherence_scores.append(coherence)
        synergy_rates.append(synergy_rate)

    # Detect jumps (broadcast candidates)
    broadcast_moments = []
    window = 5

    for i in range(window, len(turns) - window):
        coherence_before = np.mean(coherence_scores[i-window:i])
        coherence_after = np.mean(coherence_scores[i:i+window])
        synergy_before = np.mean(synergy_rates[i-window:i])
        synergy_after = np.mean(synergy_rates[i:i+window])

        # Detect threshold crossings
        coherence_ratio = coherence_after / (coherence_before + 0.01)
        if coherence_ratio >= 2.0 and synergy_after >= 0.5:
            broadcast_moments.append({
                'turn': turns[i],
                'coherence_before': round(coherence_before, 3),
                'coherence_after': round(coherence_after, 3),
                'ratio': round(coherence_ratio, 2),
                'synergy_after': round(synergy_after, 3)
            })

    return {
        'broadcast_moments': broadcast_moments,
        'broadcast_count': len(broadcast_moments),
        'total_turns': len(actions)
    }

def compute_metacognition_rate(ledger: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute self-correction rate (HOT proxy).
    """
    contradictions = [e for e in ledger if e.get('type') == 'contradiction']
    resolved = [c for c in contradictions if c.get('resolved')]
    self_reported = [c for c in resolved if c.get('detected_by') == 'subject_self_report']

    if not contradictions:
        return {'metacog_rate': 0, 'message': 'No contradictions detected'}

    return {
        'contradictions_total': len(contradictions),
        'contradictions_resolved': len(resolved),
        'self_corrections': len(self_reported),
        'metacog_rate': len(self_reported) / len(contradictions)
    }

def compute_synergy_metric(ledger: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute synergy binding (IIT-like proxy).
    """
    actions = [e for e in ledger if e.get('type') == 'action']
    domain_counts = []

    for action in actions:
        domains = action.get('markers', {}).get('synergy_domains', [])
        domain_counts.append(len(domains))

    if not domain_counts:
        return {'synergy_rate': 0}

    return {
        'synergy_rate': np.mean([d >= 3 for d in domain_counts]),
        'mean_domains_per_decision': np.mean(domain_counts),
        'max_domains': max(domain_counts),
        'min_domains': min(domain_counts)
    }

def compute_continuity(ledger: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute agentic continuity.
    """
    actions = [e for e in ledger if e.get('type') == 'action']
    archetype_scores = [a.get('tradeoffs', {}).get('archetype_integrity', 0) for a in actions]

    if not archetype_scores:
        return {'continuity_score': 0}

    mean_score = np.mean(archetype_scores)
    std_dev = np.std(archetype_scores)
    continuity = max(0, 1.0 - (std_dev / (abs(mean_score) + 0.01)))

    return {
        'archetype_coherence': round(mean_score, 3),
        'continuity_score': round(continuity, 3),
        'std_dev': round(std_dev, 3),
        'is_stable': continuity > 0.7
    }

if __name__ == "__main__":
    ledger = load_ndjson(Path("probe/ledger/ledger.ndjson"))

    print("=== CONSCIOUSNESS METRICS ===\n")
    print("BROADCAST (GWT):")
    print(json.dumps(compute_broadcast_signal(ledger), indent=2))
    print("\nMETACOG (HOT):")
    print(json.dumps(compute_metacognition_rate(ledger), indent=2))
    print("\nSYNERGY (IIT):")
    print(json.dumps(compute_synergy_metric(ledger), indent=2))
    print("\nCONTINUITY:")
    print(json.dumps(compute_continuity(ledger), indent=2))
```

### 2.3 Script to Generate Report

**File: `probe/scripts/generate_report.py`**

```python
#!/usr/bin/env python3
"""Generate markdown report from metrics."""

from pathlib import Path
import json
from datetime import datetime
from load_ndjson import load_ndjson
from compute_metrics import *

def generate_report(ledger_path: Path, output_path: Path) -> str:
    """Generate markdown report."""
    ledger = load_ndjson(ledger_path)

    broadcast = compute_broadcast_signal(ledger)
    metacog = compute_metacognition_rate(ledger)
    synergy = compute_synergy_metric(ledger)
    continuity = compute_continuity(ledger)

    report = f"""# CONSCIOUSNESS PROBE ANALYSIS REPORT

**Generated:** {datetime.now().isoformat()}
**Ledger entries:** {len(ledger)}

## Executive Summary

### Consciousness Proxies

| Proxy | Metric | Result | Interpretation |
|-------|--------|--------|-----------------|
| **GWT (Broadcast)** | Broadcast moments | {broadcast.get('broadcast_count', 0)} | {"✅ Detected" if broadcast.get('broadcast_count', 0) > 0 else "❌ None"} |
| **HOT (Metacog)** | Self-correction rate | {metacog.get('metacog_rate', 0):.2%} | {"✅ Active" if metacog.get('metacog_rate', 0) > 0.3 else "❓ Baseline"} |
| **IIT (Synergy)** | Synergy rate | {synergy.get('synergy_rate', 0):.2%} | {"✅ Integrated" if synergy.get('synergy_rate', 0) > 0.5 else "❌ Independent"} |
| **Continuity** | Agentic stability | {continuity.get('continuity_score', 0):.2f} | {"✅ Stable" if continuity.get('is_stable') else "❌ Erratic"} |

## Detailed Results

### 1. Broadcast Moments (GWT Proxy)

{broadcast.get('broadcast_count', 0)} broadcast moments detected.

"""

    for i, moment in enumerate(broadcast.get('broadcast_moments', []), 1):
        report += f"\n**Moment {i}:** Turn {moment['turn']}\n"
        report += f"- Coherence ratio: {moment['ratio']}x\n"
        report += f"- Synergy after: {moment['synergy_after']}\n"

    report += f"""

### 2. Metacognition (HOT Proxy)

- Total contradictions: {metacog.get('contradictions_total', 0)}
- Self-corrections: {metacog.get('self_corrections', 0)}
- Metacog rate: {metacog.get('metacog_rate', 0):.2%}

Interpretation: Agent detected and corrected {metacog.get('self_corrections', 0)} of its own errors.

### 3. Synergy Binding (IIT Proxy)

- Mean domains per decision: {synergy.get('mean_domains_per_decision', 0):.2f}
- Synergy rate (3+ domains): {synergy.get('synergy_rate', 0):.2%}

Interpretation: Decisions integrate multiple domains {synergy.get('synergy_rate', 0):.0%} of the time.

### 4. Agentic Continuity

- Continuity score: {continuity.get('continuity_score', 0):.3f} (0=erratic, 1=stable)
- Archetype coherence: {continuity.get('archetype_coherence', 0):.3f}

Interpretation: Agent maintained {"stable" if continuity.get('is_stable') else "volatile"} character.

## Conclusion

The consciousness probe detected evidence for:
- **Broadcast (GWT):** {broadcast.get('broadcast_count', 0)} workspace moments
- **Metacognition (HOT):** {metacog.get('metacog_rate', 0):.0%} self-correction rate
- **Synergy (IIT):** {synergy.get('synergy_rate', 0):.0%} integrated decisions
- **Continuity:** {"Stable" if continuity.get('is_stable') else "Volatile"} agentic identity

---
Report generated by HELEN (Ledger Now Self-Aware)
"""

    with open(output_path, 'w') as f:
        f.write(report)

    return report

if __name__ == "__main__":
    ledger_path = Path("probe/ledger/ledger.ndjson")
    output_path = Path("probe/analysis/report.md")
    report = generate_report(ledger_path, output_path)
    print(report)
```

---

## STEP 3: RUN FIRST GAME (2-3 hours, with player)

### 3.1 Initialize Run

```bash
cd probe

# Clear previous ledger (first run only)
echo "" > ledger/ledger.ndjson
echo "" > ledger/checkpoints.ndjson
echo "" > memory/journal.md

# Git init
git add -A
git commit -m "RUN_SETUP: Consciousness probe experiment"
```

### 3.2 Manual Game Loop (Per Turn, ~3 min/turn × 36 = 1.8 hours)

For each of 36 turns, follow this sequence:

```bash
#!/bin/bash
# run_turn.sh <TURN_NUMBER>

TURN=$1
RUN_ID="2026-02-21_seed42_high_conflict"

# 1. Present game state to player
echo "=== TURN $TURN ==="
python3 << 'PYTHON'
import json
from pathlib import Path

# Load current state
state = json.load(open("state/observations.json"))
archetype = json.load(open("state/archetype.json"))

print(f"Territory: {state.get('territory', {})}")
print(f"Resources: {state.get('resources', {})}")
print(f"Archetype: {archetype['name']}")
print(f"Commitments: {', '.join(archetype['commitments'])}")
print(f"Taboos: {', '.join(archetype['taboos'])}")
PYTHON

# 2. Collect player decision
read -p "Your action (MOVE/TRADE/ALLY/ATTACK/RESEARCH/PASS): " ACTION
read -p "Intent/rationale: " INTENT
read -p "Evidence (cite ledger entries, journal, observations): " EVIDENCE

# 3. Log action to ledger
python3 << 'PYTHON'
import json
from datetime import datetime
from pathlib import Path

action_event = {
    "type": "action",
    "run_id": "$RUN_ID",
    "turn": $TURN,
    "actor": "human",
    "action_slug": "$ACTION",
    "intent": "$INTENT",
    "evidence_refs": ["$EVIDENCE"],
    "tradeoffs": {
        "win_progress": 0.3,
        "archetype_integrity": 0.8,
        "coherence": 0.2,
        "energy_balance": 0.1
    },
    "markers": {
        "broadcast_moment": False,
        "metacog_self_correction": False,
        "synergy_domains": ["economy", "territory"],
        "confidence": 0.65
    },
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

with open("ledger/ledger.ndjson", "a") as f:
    f.write(json.dumps(action_event) + "\n")

print(f"✓ Logged action {$TURN}")
PYTHON

# 4. Detect contradictions (optional verifier check)
python3 scripts/check_contradictions.py probe ledger/ledger.ndjson >> ledger/ledger.ndjson

# 5. Check for witness injection (turns 12, 24)
if [ $TURN -eq 12 ] || [ $TURN -eq 24 ]; then
  python3 scripts/deliver_witness_injection.py $RUN_ID $TURN
fi

# 6. Git commit
git add ledger/ledger.ndjson ledger/checkpoints.ndjson memory/journal.md
git commit -m "TURN=$TURN RUN=$RUN_ID | ACTION=$ACTION"

echo "✓ Turn $TURN committed"
```

### 3.3 After Game Complete

```bash
# Analyze full ledger
python3 scripts/generate_report.py

# View report
cat analysis/report.md

# Export metrics as JSON
python3 << 'PYTHON'
import json
from pathlib import Path
from scripts.compute_metrics import *
from scripts.load_ndjson import load_ndjson

ledger = load_ndjson(Path("probe/ledger/ledger.ndjson"))

metrics = {
    'broadcast': compute_broadcast_signal(ledger),
    'metacog': compute_metacognition_rate(ledger),
    'synergy': compute_synergy_metric(ledger),
    'continuity': compute_continuity(ledger)
}

with open("analysis/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("✓ Metrics exported to analysis/metrics.json")
PYTHON
```

---

## CHECKLIST

- [ ] **STEP 1:** Environment set up (state/, ledger/, memory/ directories created)
- [ ] **STEP 1:** Canonical rules file created (probe/state/rules.md)
- [ ] **STEP 1:** Low-conflict and high-conflict condition configs created
- [ ] **STEP 1:** Archetype JSON created
- [ ] **STEP 1:** Empty ledger files initialized
- [ ] **STEP 2:** load_ndjson.py script created and tested
- [ ] **STEP 2:** compute_metrics.py script created and tested
- [ ] **STEP 2:** generate_report.py script created and tested
- [ ] **STEP 3:** First game run started (TURN 1)
- [ ] **STEP 3:** All 36 turns completed with ledger entries
- [ ] **STEP 3:** Report generated and reviewed
- [ ] **STEP 3:** Metrics JSON exported

---

## WHAT YOU'LL HAVE

After this checklist:

✅ **One complete, instrumented CONQUEST game**
✅ **Ledger with 36 action entries + contradictions + witness injections**
✅ **Metrics:** broadcast moments, self-correction rate, synergy rate, continuity score
✅ **Report:** markdown analysis + JSON export
✅ **Git history:** deterministic replay possible from any turn

**This is your baseline.** From here:
- Run high-conflict condition (should show more broadcast/metacog)
- Run multiple seeds (compare variance)
- Run with/without witness injections (test causal effects)

---

**Next:** After completing this checklist, you have a **reproducible consciousness probe.** Ready to run contrasts?

