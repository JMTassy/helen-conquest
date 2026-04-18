# ORACLE SUPERTEAM — Quick Start Guide

## Installation

No installation required. Pure Python 3.8+ with no external dependencies.

```bash
cd oracle-superteam
```

## Run the Test Vault (Recommended First Step)

Validate the entire system with 10 comprehensive scenarios:

```bash
python3 -m ci.run_test_vault
```

Expected output: All 10 scenarios should pass with ✓ markers.

## Run a Single Claim

Create a file `example_claim.py`:

```python
from oracle.engine import run_oracle
import json

payload = {
    "scenario_id": "my-first-claim",
    "claim": {
        "id": "claim-001",
        "assertion": "Deploy new authentication system with OAuth 2.0",
        "tier": "Tier I",
        "domain": ["security", "engineering"],
        "owner_team": "Engineering Wing"
    },
    "evidence": [
        {
            "id": "ev-001",
            "type": "security_audit",
            "tags": ["verified", "oauth2", "security_tested"]
        }
    ],
    "votes": [
        {"team": "Engineering Wing", "vote": "APPROVE", "rationale": "Implementation complete and tested."},
        {"team": "Security Sector", "vote": "APPROVE", "rationale": "Security audit passed."},
        {"team": "Legal Office", "vote": "APPROVE", "rationale": "Complies with data protection requirements."}
    ]
}

manifest = run_oracle(payload)

print(json.dumps({
    "decision": manifest["decision"]["final"],
    "ship_permitted": manifest["decision"]["ship_permitted"],
    "reason_codes": manifest["decision"]["reason_codes"],
    "kill_switch": manifest["derived"]["kill_switch_triggered"],
    "obligations": len(manifest["derived"]["obligations_open"]),
    "score": manifest["derived"]["qi_int"]["S_c"]
}, indent=2))
```

Run:

```bash
python3 example_claim.py
```

Expected output:

```json
{
  "decision": "ACCEPT",
  "ship_permitted": true,
  "reason_codes": ["SCORE_PASS"],
  "kill_switch": false,
  "obligations": 0,
  "score": 2.1525
}
```

## Understanding the Output

### Decision States

- **ACCEPT** → `ship_permitted: true` — Claim approved
- **QUARANTINE** → `ship_permitted: false` — Blocked by obligations or contradictions
- **KILL** → `ship_permitted: false` — Terminated by kill-switch or high-severity contradiction

### Reason Codes

| Code | Meaning |
|------|---------|
| `SCORE_PASS` | QI-INT score ≥ 0.75 (accept threshold) |
| `SCORE_FAIL` | QI-INT score < 0.75 |
| `OBLIGATIONS_BLOCKING` | One or more open obligations |
| `CONTRADICTION_PRESENT` | Evidence contradictions detected |
| `KILL_SWITCH` | Explicit KILL vote from authorized team |
| `CONTRADICTION_HIGH_LEGAL` | High-severity legal/privacy contradiction (auto-kill) |

### Vote Types

| Vote | Effect | Opens Obligation? |
|------|--------|-------------------|
| `APPROVE` | Full support (phase = 0°) | No |
| `CONDITIONAL` | Support with requirements | **Yes** |
| `OBJECT` | Opposition (phase = 90°) | No |
| `QUARANTINE` | Suspend for review (phase = 135°) | **Yes** |
| `REJECT` | Block (phase = 180°) | **Yes** |
| `KILL` | Immediate halt (authorized teams only) | Override |

### Kill-Switch Teams

Only these teams can issue `KILL` votes:

- **Legal Office** (w=1.00)
- **Security Sector** (w=1.00)

## Explore Test Scenarios

All scenarios are in `test_vault/scenarios/`:

```bash
# View scenario 2 (privacy contradiction)
cat test_vault/scenarios/02_privacy_contradiction_legal_kill.json

# View scenario 8 (replay determinism test)
cat test_vault/scenarios/08_consensus_drift_replay_identical.json
```

## Visualize ORACLE TOWN

Generate the governance city map (requires Graphviz):

```bash
dot -Tpng viz/oracle_town.dot -o viz/oracle_town.png
open viz/oracle_town.png  # macOS
# or: xdg-open viz/oracle_town.png  # Linux
```

## Key Files

| File | Purpose |
|------|---------|
| `CONSTITUTION.md` | Immutable axioms and rules |
| `README.md` | Complete documentation |
| `oracle/engine.py` | Main orchestration pipeline |
| `oracle/config.py` | Team weights, thresholds, vote phases |
| `ci/run_test_vault.py` | CI test runner |

## Common Patterns

### Pattern 1: Claim with Missing Evidence

```python
payload = {
    "claim": {"assertion": "This feature is GDPR compliant"},
    "evidence": [],  # No evidence provided
    "votes": [{"team": "Legal Office", "vote": "CONDITIONAL", "rationale": "Need compliance audit."}]
}
# Result: QUARANTINE (OBLIGATIONS_BLOCKING)
```

### Pattern 2: Kill-Switch Override

```python
payload = {
    "claim": {"assertion": "Deploy feature X"},
    "votes": [
        {"team": "Engineering Wing", "vote": "APPROVE"},
        {"team": "Strategy HQ", "vote": "APPROVE"},
        {"team": "Legal Office", "vote": "KILL", "rationale": "Regulatory violation risk"}
    ]
}
# Result: KILL (KILL_SWITCH) — overrides all approvals
```

### Pattern 3: Evidence Contradiction

```python
payload = {
    "claim": {"assertion": "Service is fully anonymous"},
    "evidence": [
        {"tags": ["anonymous_claim"]},
        {"tags": ["biometric", "face"]}  # Contradiction!
    ],
    "votes": [{"team": "Data Validation Office", "vote": "APPROVE"}]
}
# Result: KILL (CONTRADICTION_HIGH_LEGAL) — HC-PRIV-001 rule triggered
```

## Replay Determinism

Test that identical inputs produce identical outputs:

```python
from oracle.engine import run_oracle
from oracle.replay import replay_equivalence

# Run twice with same payload
manifest_a = run_oracle(payload)
manifest_b = run_oracle(payload)

# Verify hashes match
eq = replay_equivalence(manifest_a, manifest_b)
assert eq["inputs_hash_equal"]
assert eq["outputs_hash_equal"]
```

## Next Steps

1. Read `CONSTITUTION.md` to understand the governance axioms
2. Explore `test_vault/scenarios/` to see edge cases
3. Customize `oracle/config.py` to adjust team weights
4. Add new contradiction rules in `oracle/contradictions.py`
5. Build Superteams (multi-agent production teams)

## Troubleshooting

**Q: Why did my claim get QUARANTINE instead of ACCEPT?**

A: Check:
- Are there open obligations? (`obligations_open`)
- Are there contradictions? (`contradictions`)
- Is the QI-INT score too low? (`qi_int.S_c < 0.75`)

**Q: How do I clear an obligation?**

A: Supply the missing evidence, then resubmit. Obligations cannot be manually overridden.

**Q: Can I bypass a KILL decision?**

A: No. There is no override button. Fix the underlying issue (legal compliance, security risk, etc.) first.

## Resources

- Constitution: `CONSTITUTION.md`
- Full Documentation: `README.md`
- Test Scenarios: `test_vault/scenarios/`
- City Map: `viz/oracle_town.dot`

---

**ORACLE SUPERTEAM is not a conversation. It is an institution.**
