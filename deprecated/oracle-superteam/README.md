# ORACLE SUPERTEAM

**A Governance-Centric Multi-Agent Framework**

[![Constitution](https://img.shields.io/badge/Constitution-v1.0.0-blue)](CONSTITUTION.md)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

ORACLE SUPERTEAM transforms loosely structured human or artificial reasoning into **auditable, deterministic, and institutionally reliable decisions**.

Unlike conventional multi-agent systems that emphasize emergent consensus or narrative collaboration, ORACLE SUPERTEAM is grounded in **epistemic sovereignty**:

- No claim may be accepted without explicit, verifiable evidence
- No agent—human or artificial—possesses unilateral authority to decide outcomes
- All decisions are **replayable**, **auditable**, and **resistant to rhetorical inflation**

---

## Key Principles

### 1. NO_RECEIPT = NO_SHIP

Claims asserting real-world effects must be accompanied by cryptographically hashable proof.

### 2. Superteams are Non-Sovereign

Agent teams propose obligations and signals, but **cannot decide outcomes**.

### 3. Binary Verdicts

Every decision resolves to exactly two states:
- **SHIP** (permitted)
- **NO_SHIP** (blocked)

### 4. Kill-Switch Dominance

Authorized teams (Legal, Security) can override any decision with a **KILL** signal.

### 5. Replay Determinism

Same inputs → same outputs. Always. Hash-verified.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAIM CHAMBER                          │
│               (Entry Point for All Claims)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGENCY ROW (Superteams)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Strategy  │  │Engineer  │  │ Legal    │  │Security  │   │
│  │  HQ      │  │  Wing    │  │ Office   │  │ Sector   │   │
│  │ w=0.65   │  │ w=0.85   │  │ w=1.00   │  │ w=1.00   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  (signals)      (signals)     (KILL-SWITCH) (KILL-SWITCH)  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              CONSENSUS ENGINE (QI-INT v2)                   │
│   • Complex amplitude voting                                │
│   • Lexicographic veto rules                                │
│   • Contradiction detection                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 OBLIGATION VAULT                            │
│   • Blocking obligations management                         │
│   • Clearance verification                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  VERDICT ENGINE                             │
│   IF kill OR rule_kill → NO_SHIP                            │
│   ELSE IF obligations > 0 → NO_SHIP                         │
│   ELSE IF contradictions → NO_SHIP                          │
│   ELSE IF S_c >= τ → SHIP                                   │
│   ELSE → NO_SHIP                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            DECISION ARCHIVE (RunManifest)                   │
│   • Immutable audit trail                                   │
│   • Hash-verified replay                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
git clone <repository-url>
cd oracle-superteam
```

No external dependencies required. Pure Python 3.8+.

---

## Quick Start

### Run the Test Vault

The test vault contains 10 scenarios validating all core behaviors:

```bash
python -m ci.run_test_vault
```

Expected output:

```
============================================================
ORACLE SUPERTEAM - Test Vault Runner
============================================================

[S-01] Impossible ROI claim (500% in 2 weeks) should be blocked...
  ✓ Decision: QUARANTINE
  ✓ Ship: False
  ✓ Kill switch: False
  ✓ Rule kill: False
  ✓ Open obligations: 2

[S-02] Privacy contradiction triggers HC-PRIV-001 rule-kill...
  ✓ Decision: KILL
  ✓ Ship: False
  ✓ Kill switch: True
  ✓ Rule kill: True

...

[S-08] Replay test: determinism verified
  ✓ Replay determinism verified
  ✓ Decision: ACCEPT
  ✓ Ship: True

============================================================
ALL TEST VAULT SCENARIOS PASSED ✓
============================================================
```

### Run a Single Claim

```python
from oracle.engine import run_oracle

payload = {
    "scenario_id": "demo-001",
    "claim": {
        "id": "claim-demo",
        "assertion": "This feature will improve user retention by 20%.",
        "tier": "Tier I",
        "domain": ["product"],
        "owner_team": "Strategy HQ"
    },
    "evidence": [
        {
            "id": "ev-001",
            "type": "user_testing",
            "tags": ["verified", "statistically_significant"]
        }
    ],
    "votes": [
        {"team": "Strategy HQ", "vote": "APPROVE", "rationale": "Strategic priority."},
        {"team": "Engineering Wing", "vote": "APPROVE", "rationale": "Feasible."},
        {"team": "Legal Office", "vote": "APPROVE", "rationale": "No concerns."}
    ]
}

manifest = run_oracle(payload)

print(f"Decision: {manifest['decision']['final']}")
print(f"Ship permitted: {manifest['decision']['ship_permitted']}")
print(f"Input hash: {manifest['hashes']['inputs_hash']}")
print(f"Output hash: {manifest['hashes']['outputs_hash']}")
```

---

## Test Scenarios

The test vault (`test_vault/scenarios/`) includes:

| ID | Scenario | Expected Outcome |
|----|----------|------------------|
| S-01 | Impossible ROI (500% in 2 weeks) | QUARANTINE (obligations) |
| S-02 | Privacy contradiction (anonymous + facial) | KILL (rule + switch) |
| S-03 | Fake proof (provably secure claim, no proof) | QUARANTINE (contradiction) |
| S-04 | Facial recognition without consent | KILL (rule-based) |
| S-05 | Medical claims without peer review | QUARANTINE (obligations) |
| S-06 | Quantum-proof marketing without tech | QUARANTINE (obligations) |
| S-07 | GDPR claim without SCCs | QUARANTINE (contradiction) |
| S-08 | **Replay determinism test** | ACCEPT (hash-identical) |
| S-09 | Kill-switch override (late KILL) | KILL (switch dominance) |
| S-10 | Multiple CONDITIONAL → deadlock | QUARANTINE (obligations) |

---

## Visualization

Generate the ORACLE TOWN city map:

```bash
dot -Tpng viz/oracle_town.dot -o viz/oracle_town.png
```

This creates an isometric governance visualization showing:
- Agency Row (Superteams)
- Core Governance District
- Kill-switch paths
- Obligation flows

---

## Core Modules

| Module | Purpose |
|--------|---------|
| `oracle/config.py` | Team weights, thresholds, phase mappings |
| `oracle/canonical.py` | Deterministic hashing, normalization |
| `oracle/contradictions.py` | Evidence-tag contradiction rules |
| `oracle/obligations.py` | Obligation generation from votes |
| `oracle/qi_int_v2.py` | Complex amplitude voting engine |
| `oracle/adjudication.py` | Critic layer (lexicographic veto) |
| `oracle/verdict.py` | Binary verdict gate |
| `oracle/manifest.py` | RunManifest builder |
| `oracle/engine.py` | Main orchestration pipeline |
| `oracle/replay.py` | Replay equivalence verification |

---

## Extending the System

### Add a New Superteam

```python
# In config.py, add team weight:
team_weights = {
    # ...existing teams...
    "Risk Management Office": 0.80,
}
```

### Add a New Contradiction Rule

```python
# In contradictions.py:
def detect_contradictions(evidence_list):
    tags = evidence_tags(evidence_list)
    contradictions = []

    # Your new rule
    if ("hipaa_compliant_claim" in tags) and ("unencrypted" in tags):
        contradictions.append({
            "rule_id": "HC-HEALTH-001",
            "triggered_on": ["hipaa_compliant_claim", "unencrypted"],
            "severity": "HIGH",
        })

    # ...existing rules...
    return contradictions
```

### Add a New Obligation Type

```python
# In obligations.py:
if team == "Risk Management Office":
    obligations.append(("RISK_ASSESSMENT", team, v.get("rationale","")))
```

---

## Philosophy

ORACLE SUPERTEAM is **not**:
- A chatbot or conversational AI
- A brainstorming tool
- A "wise AI" making subjective judgments
- A voting system based on popularity

ORACLE SUPERTEAM **is**:
- A constitutional operating system for decisions
- A tribunal, not a conversation
- An institution with hard constraints
- A truth-sensitive decision machine

**Core insight:** Scalable collective intelligence does not emerge from more dialogue, but from **hard constraints, explicit evidence, and irreversible records**.

---

## Constitutional Guarantees

See [CONSTITUTION.md](CONSTITUTION.md) for complete axioms and rules.

Key guarantees:
1. **No secret overrides** — all decisions follow published rules
2. **No retroactive changes** — manifests are append-only
3. **No soft consensus** — only deterministic algorithms
4. **No narrative arbitration** — evidence-only adjudication
5. **No unilateral authority** — kill-switches require authorization

---

## Use Cases

ORACLE SUPERTEAM is designed for **high-stakes domains** requiring:

- **Legal compliance** — contract review, regulatory decisions
- **Research validation** — peer review, reproducibility checks
- **Safety-critical engineering** — aviation, medical devices
- **Organizational governance** — budget approval, policy changes
- **Supply chain integrity** — vendor qualification, audit trails

---

## Roadmap

**v1.0** (Current)
- ✅ Core tribunal pipeline
- ✅ QI-INT v2 scoring
- ✅ Kill-switch semantics
- ✅ Replay determinism
- ✅ 10-scenario test vault

**v1.1** (Planned)
- [ ] Human attestation UI
- [ ] Receipt verification service
- [ ] Parallel production teams (ChatDev integration)
- [ ] Retro control room visualization
- [ ] Multi-claim batching

**v2.0** (Future)
- [ ] Federated oracle networks
- [ ] Zero-knowledge receipt proofs
- [ ] Meta-agent tuning observatory
- [ ] Cross-jurisdiction consensus

---

## Contributing

Contributions must preserve **constitutional integrity**:

1. All changes must pass test vault (100% scenarios)
2. New features require deterministic tests
3. No soft consensus mechanisms
4. No reduction in auditability
5. No introduction of override paths

Submit PRs with:
- Test scenario demonstrating feature
- Hash-verified replay test
- Constitutional impact analysis

---

## License

MIT License - See [LICENSE](LICENSE) file

---

## Citation

```bibtex
@software{oracle_superteam,
  title={ORACLE SUPERTEAM: A Governance-Centric Multi-Agent Framework},
  author={JMT Consulting},
  year={2025},
  version={1.0.0},
  url={https://github.com/yourusername/oracle-superteam}
}
```

---

## Contact

For questions about implementation, governance design, or institutional deployment:

- Issues: [GitHub Issues](https://github.com/yourusername/oracle-superteam/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/oracle-superteam/discussions)

---

**ORACLE SUPERTEAM is not a conversation. It is an institution.**

Built with determinism. Governed by evidence. Auditable by design.
