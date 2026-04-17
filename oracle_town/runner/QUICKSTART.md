# ORACLE TOWN Inner Loop: Quick Start

## Install & Verify

```bash
cd /Users/jean-marietassy/Desktop/JMT\ CONSULTING\ -\ Releve\ 24
export PYTHONPATH=.

# Test all completed modules
python3 oracle_town/runner/worktree.py       # Should print: ✓ All worktree tests passed
python3 oracle_town/runner/supervisor.py     # Should print: ✓ All supervisor tests passed
python3 oracle_town/runner/intake_adapter.py  # Should print: ✓ All intake adapter tests passed
python3 oracle_town/runner/factory_adapter.py # Should print: ✓ Factory adapter tests passed
```

---

## What Each Module Does

### Worktree (Safe Patching)
```python
from oracle_town.runner import make_temp_worktree, apply_patch, cleanup_worktree

# Create isolated copy
workdir = make_temp_worktree(".")

# Apply a unified diff safely (no core/ modifications allowed)
result = apply_patch(workdir, """
--- a/tests/test_new.py
+++ b/tests/test_new.py
@@ -0,0 +1,5 @@
+def test_example():
+    assert True
""")

# Clean up
cleanup_worktree(workdir)
```

### Supervisor (Token Check)
```python
from oracle_town.runner import Supervisor

supervisor = Supervisor()

# This passes (neutral language)
result = supervisor.evaluate({
    "proposal_bundle": {"name": "add_test", "description": "Add test coverage"},
    "patches": [{"diff": "...", "rationale": "More tests needed"}]
})
# result.decision == "PASS"

# This fails (forbidden: "approve")
result = supervisor.evaluate({
    "proposal_bundle": {"description": "This is approved"},
    "patches": []
})
# result.decision == "REJECT"
# result.reason_code == SupervisorRejectCode.SUP_FORBIDDEN_AUTHORITY_LANGUAGE
```

### Intake Adapter (Validation)
```python
from oracle_town.runner import IntakeAdapter

adapter = IntakeAdapter()

result = adapter.evaluate({
    "proposals": [{"name": "test_idea", "description_hash": "sha256:abc123"}]
})

if result.decision == "ACCEPT":
    print(f"Briefcase: {result.briefcase}")
else:
    print(f"Rejected: {result.detail}")
```

### Factory Adapter (Evidence)
```python
from oracle_town.runner import FactoryAdapter
from oracle_town.core.policy import Policy

policy = Policy.load("oracle_town/policies/policy.json")

factory = FactoryAdapter(
    key_registry_path="oracle_town/keys/public_keys.json",
    policy_hash=policy.policy_hash,
    registry_hash=None  # Will use default
)

# Run tool and produce signed attestation
attestation = factory.run_tool_and_attest(
    tool_command="python3 -m pytest tests/ -q",
    workdir="/tmp/oracle_town_work",
    run_id="run_001",
    claim_id="claim_001",
    obligation_name="test_pass"
)

if attestation.valid:
    print(f"Attestation ID: {attestation.attestation_id}")
    print(f"Evidence digest: {attestation.attestation['evidence_digest']}")
else:
    print(f"Failed: {attestation.validation_errors}")
```

---

## Architecture

```
Proposal from CT
        ↓
   Supervisor ← Check for forbidden language (K0)
        ↓
  Intake Adapter ← Validate schema
        ↓
   Worktree ← Create isolated sandbox
        ↓
  Apply Patch ← Safely apply changes
        ↓
Factory Adapter ← Run tools, sign evidence (K7)
        ↓
    Decision
```

---

## Invariants Enforced

| Rule | Example | Enforcer |
|------|---------|----------|
| **K0: No Authority Language** | CT cannot say "ship" or "approve" | Supervisor |
| **K1: Fail-Closed** | Missing evidence → NO_SHIP | Mayor (later) |
| **K5: Determinism** | Same run → same result hash | Canonical JSON |
| **K7: Policy Pinning** | Policy locked per run | Factory stores in attestation |

---

## Common Patterns

### Pattern 1: Simple Tool Execution
```python
factory = FactoryAdapter(...)
att = factory.run_tool_and_attest(
    tool_command="pytest tests/",
    workdir=workdir,
    run_id="r1", claim_id="c1",
    obligation_name="test_pass"
)
```

### Pattern 2: Validate CT Output
```python
supervisor = Supervisor()
sup_decision = supervisor.evaluate(ct_output)
if sup_decision.decision != "PASS":
    print(f"Rejected: {sup_decision.forbidden_token}")
    exit(1)
```

### Pattern 3: Full Pipeline (Simple)
```python
# CT proposes
ct_output = {"proposal_bundle": {...}, "patches": [...]}

# Supervisor checks
sup = Supervisor()
if sup.evaluate(ct_output).decision == "REJECT":
    exit(1)

# Intake validates
intake = IntakeAdapter()
if intake.evaluate(ct_output["proposal_bundle"]).decision == "REJECT":
    exit(1)

# Factory executes
workdir = make_temp_worktree(".")
try:
    apply_patch(workdir, ct_output["patches"][0]["diff"])
    factory = FactoryAdapter(...)
    attestation = factory.run_tool_and_attest(
        tool_command="pytest",
        workdir=workdir,
        run_id="r1", claim_id="c1",
        obligation_name="test_pass"
    )
finally:
    cleanup_worktree(workdir)
```

---

## What's Missing (Pending Steps 5-10)

| Step | Module | Purpose | Status |
|------|--------|---------|--------|
| 5 | briefcase_ledger.py | Aggregate obligations + evidence | Pending |
| 6 | context_builder.py | Build K0-safe feedback | Pending |
| 7 | ct_gateway.py | Accept CT proposals (Claude/simulation) | Pending |
| 8 | innerloop.py | Orchestrate + recursion control | Pending |
| 9 | creative_observer.py | Log cycle-by-cycle evolution | Pending |
| 10 | tests/test_vectors_A_H.py | End-to-end verification | Pending |

---

## Reference Docs

- **KERNEL_CONTRACTS.md** — Exact kernel signatures (frozen, no guessing)
- **README_INNER_LOOP.md** — Full architecture + principles
- **IMPLEMENTATION_PROGRESS.md** — Step 5-10 blueprints
- **INNER_LOOP_DELIVERY_SUMMARY.md** — What was built + what's next

---

## Troubleshooting

### ImportError: No module named 'oracle_town'
```bash
export PYTHONPATH=.  # From repo root
```

### pynacl not installed
```bash
pip install pynacl
```

### "Key registry not found"
Check that `oracle_town/keys/public_keys.json` exists and is valid JSON.

### "Forbidden path in patch"
Patches can only modify: tests/, docs/, examples/, oracle_town/creative/, oracle_town/runner/
Cannot patch: oracle_town/core/, oracle_town/keys/, oracle_town/policies/, oracle_town/schemas/

---

## Next Steps

1. Study `IMPLEMENTATION_PROGRESS.md` for Steps 5-10
2. Implement Step 5 (Briefcase/Ledger) first
3. Test against Phase-2 test vectors
4. Implement Steps 6-10 in order
5. Run full integration tests

**All guardrails are in place. Code is clean. Ready to continue.**
