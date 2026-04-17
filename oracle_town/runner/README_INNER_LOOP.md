# ORACLE TOWN Inner Loop: Constitutional Brainstorm Engine

## What This Is

A **fully automatic, recursive governance machine** that:
1. Accepts proposals from Creative Town (Claude or simulation)
2. Applies patches in isolated, safe worktrees
3. Runs tests and tools, captures evidence
4. Signs evidence cryptographically (Ed25519)
5. Feeds back structured decision facts (never reasoning)
6. Repeats until SHIP or barrier trip

**Goal:** Let humans and AI collaborate on code/policy while maintaining:
- **K0: Authority Separation** — CT proposes, Factory attests, Mayor decides
- **K1: Fail-Closed** — default NO_SHIP
- **K5: Determinism** — same inputs → same outputs (hash-verified)
- **K7: Policy Pinning** — policy immutable per run

---

## Architecture (What Runs Where)

```
CT (Claude / Simulation)
  ↓ [proposes patches + ideas]
  ↓
Supervisor (Token Sanitization)
  ├─ Forbid authority language ("ship", "approve")
  ├─ Forbid ranking language ("best", "optimal")
  ├─ Forbid confidence ("95% confident", "guaranteed")
  └─ Detect obfuscation (zero-width characters)
  ↓ [K0 enforcement pass]
  ↓
Intake Adapter (Real Validation)
  ├─ Call real IntakeGuard
  ├─ Check schema, budgets, forbidden fields
  └─ Build briefcase (obligations)
  ↓ [Schema compliance]
  ↓
Worktree (Isolation)
  ├─ Copy repo to temp dir
  ├─ Apply patches with path validation
  └─ Forbid: core/, policies/, keys/, schemas/
  ↓ [Safe sandbox]
  ↓
Factory Adapter (Evidence Production)
  ├─ Run tools (pytest, lint, tests)
  ├─ Compute SHA256 evidence digest
  ├─ Build canonical message (kernel function)
  ├─ Sign with Ed25519
  └─ Validate attestation against schema
  ↓ [Cryptographic receipts]
  ↓
Mayor (Pure Decision)
  ├─ Verify attestations (signatures + registry)
  ├─ Check quorum (K3: min N distinct classes)
  ├─ Apply policy (K1, K2, K7 invariants)
  └─ Return SHIP / NO_SHIP with reason code
  ↓ [Immutable decision]
  ↓
Context Builder (K0-Safe Feedback)
  ├─ Extract decision facts only
  ├─ Policy hash (constitutional reference)
  ├─ Missing obligations (names + classes)
  ├─ Blocking reasons (code + obligation name)
  └─ Do NOT include: Mayor reasoning, checks
  ↓ [Next cycle input]
  ↓
[if NO_SHIP and cycles < max]
  → Back to CT with context
```

---

## Implementation Status

### ✅ Completed (Steps 0-4)

1. **KERNEL_CONTRACTS.md** — Frozen all kernel interfaces (no guessing)
2. **worktree.py** — Safe, isolated patch application
3. **supervisor.py** — Token sanitization with injection defense
4. **intake_adapter.py** — Wraps real IntakeGuard
5. **factory_adapter.py** — Tool execution → signed attestations

### 🔄 In Progress (Steps 5-10)

See `IMPLEMENTATION_PROGRESS.md` for detailed next steps.

---

## Key Modules

### `worktree.py` — Sandboxing
```python
workdir = make_temp_worktree(repo_root)           # Create temp copy
apply_patch(workdir, diff_text)                   # Apply unified diff
cleanup_worktree(workdir)                         # Remove temp dir
```

**Path protection:**
- ✅ Allows: tests/, docs/, examples/, oracle_town/creative/, oracle_town/runner/
- ❌ Forbids: oracle_town/core/, oracle_town/keys/, oracle_town/policies/, oracle_town/schemas/

### `supervisor.py` — Sanitization
```python
supervisor = Supervisor()
decision = supervisor.evaluate(ct_output)  # PASS or REJECT
```

**Forbidden languages:**
- Authority: "ship", "approve", "pass", "safe", "verified"
- Ranking: "best", "optimal", "priority", "recommended"
- Confidence: "confident", "guaranteed", "95%", "probably"

### `intake_adapter.py` — Validation
```python
adapter = IntakeAdapter()
decision = adapter.evaluate(proposal_bundle, ct_run_manifest)
# Returns: IntakeAdapterDecision (ACCEPT or REJECT)
```

### `factory_adapter.py` — Attestation
```python
factory = FactoryAdapter(
    key_registry_path="oracle_town/keys/public_keys.json",
    policy_hash="sha256:abc123...",
    registry_hash="sha256:registry..."
)
attestation = factory.run_tool_and_attest(
    tool_command="pytest -q tests/",
    workdir=workdir,
    run_id="run_001",
    claim_id="claim_001",
    obligation_name="test_pass"
)
# Returns: FactoryAttestation (signed or failed)
```

---

## Usage Example (Once Complete)

```python
from oracle_town.runner import (
    make_temp_worktree, cleanup_worktree,
    Supervisor, IntakeAdapter, FactoryAdapter
)
from oracle_town.core.policy import Policy
from oracle_town.core.key_registry import KeyRegistry

# Load constitutional assets
policy = Policy.load("oracle_town/policies/policy.json")
registry = KeyRegistry("oracle_town/keys/public_keys.json")

# Create isolated worktree
workdir = make_temp_worktree(".")

try:
    # CT proposes
    ct_output = {
        "proposal_bundle": {"name": "add_test"},
        "patches": [{"diff": "...", "rationale": "..."}]
    }

    # Supervisor sanitizes
    supervisor = Supervisor()
    sup_decision = supervisor.evaluate(ct_output)
    if sup_decision.decision == "REJECT":
        print(f"Rejected: {sup_decision.reason_code}")
        exit(1)

    # Intake validates
    intake = IntakeAdapter()
    intake_decision = intake.evaluate(ct_output["proposal_bundle"])
    if intake_decision.decision == "REJECT":
        print(f"Rejected: {intake_decision.detail}")
        exit(1)

    # Factory attests
    factory = FactoryAdapter(
        "oracle_town/keys/public_keys.json",
        policy.policy_hash,
        registry.registry_hash
    )
    attestation = factory.run_tool_and_attest(
        tool_command="pytest tests/test_new.py -v",
        workdir=workdir,
        run_id="run_001",
        claim_id="claim_001",
        obligation_name="test_new_feature"
    )

    if not attestation.valid:
        print(f"Attestation failed: {attestation.validation_errors}")
        exit(1)

    # Mayor decides
    from oracle_town.core.mayor_rsm import MayorRSM
    mayor = MayorRSM(policy, registry, briefcase={...}, ledger={...})
    decision = mayor.decide(run_id="run_001", claim_id="claim_001")
    print(f"Mayor decision: {decision.decision} ({decision.reason_code})")

finally:
    cleanup_worktree(workdir)
```

---

## Critical Invariants

These CANNOT be violated or bypassed:

| Invariant | Meaning | Enforced By |
|-----------|---------|------------|
| **K0** | Authority Separation | Supervisor + IntakeGuard |
| **K1** | Fail-Closed | Mayor default = NO_SHIP |
| **K2** | No Self-Attestation | Mayor checks attestor ≠ agent |
| **K3** | Quorum-by-Class | Mayor requires min N distinct classes |
| **K5** | Determinism | Same inputs → same outputs (hash-verified) |
| **K7** | Policy Pinning | Policy hash immutable per run |
| **K9** | Replay Mode | All runs replayable & auditable |

---

## Testing

### Unit Tests (Current)
```bash
cd oracle_town
PYTHONPATH=. python3 runner/worktree.py      # ✅ 4/4 pass
PYTHONPATH=. python3 runner/supervisor.py    # ✅ 5/5 pass
PYTHONPATH=. python3 runner/intake_adapter.py  # ✅ 4/4 pass
PYTHONPATH=. python3 runner/factory_adapter.py  # ✅ 3/3 pass
```

### Integration Tests (Pending)
Once Steps 5-10 complete:
```bash
# Run test vectors A–H through full pipeline
python3 runner/tests/test_vectors_A_H.py

# Verify determinism (run twice, compare hashes)
python3 runner/tests/test_determinism.py

# Verify attestation signatures
python3 runner/tests/test_signature_verification.py
```

---

## Design Principles

### 1. Fail Closed
Missing field → exception, never silent fallback.
```python
if not evidence_digest or not evidence_digest.startswith("sha256:"):
    raise ValueError("EVIDENCE_DIGEST_MISSING")  # ✅ Fail
    # NOT: evidence_digest = "sha256:0000..."  # ❌ Silent fallback
```

### 2. Reuse Kernel Functions
Never duplicate `build_canonical_message`, `canonical_json_bytes`, etc.
```python
# ✅ Correct
from oracle_town.core.crypto import build_canonical_message
message = build_canonical_message(...)

# ❌ Wrong
message = {
    "run_id": run_id,
    "claim_id": claim_id,
    ...
}
```

### 3. Deterministic Normalization
Normalize tokens the same way everywhere. Catch obfuscation.
```python
# Zero-width character attack
obfuscated = "a\u200bpprove"  # "a​pprove" (with zero-width space)
normalized = normalize_token(obfuscated)  # Returns "approve"
# ✅ Caught and rejected
```

### 4. K0-Safe Feedback
CT sees decision facts, never decision logic.
```python
# ✅ What CT gets
{
    "policy_hash": "sha256:abc123",
    "required_obligations": ["test_pass", "lint_pass"],
    "blocking_reasons": [
        {"code": "QUORUM_MISSING", "obligation": "test_pass"}
    ]
}

# ❌ What CT does NOT get
{
    "mayor_internal_check_2": "attestor class mismatch on line 234",
    "private_reasoning": "...",
    ...
}
```

---

## Pitfalls & Mitigations

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Contract drift | Signature works but Mayor rejects | Reuse kernel functions (KERNEL_CONTRACTS.md) |
| Token scanner miss | Obfuscated approval language | Normalize before splitting (catches zero-width) |
| Patch escape | Patch modifies core/ | Path allowlist + `patch` command |
| Silent fallback | Missing hash → fake hash | Fail closed (raise exception) |
| CT optimization | CT tries to game SHIP rate | Never show ship metrics to CT |

---

## Next: Continue Implementation

**Recommended order:**
1. Step 5: Briefcase/Ledger construction
2. Step 6: Context Builder
3. Step 7: CT Gateway (simulate mode first)
4. Step 8: Innerloop orchestrator
5. Step 9: Creative observer
6. Step 10: Integration tests

See `IMPLEMENTATION_PROGRESS.md` for detailed specs for each step.

---

## References

- **KERNEL_CONTRACTS.md** — Exact kernel signatures (no adapting)
- **IMPLEMENTATION_PROGRESS.md** — Step-by-step blueprints
- **oracle_town/core/mayor_rsm.py** — Pure decision function
- **oracle_town/core/policy.py** — Policy contracts
- **oracle_town/core/crypto.py** — Signing utilities
- **oracle_town/schemas/** — JSON schema for attestations

---

**Built with determinism, governed by evidence, auditable by design.**
