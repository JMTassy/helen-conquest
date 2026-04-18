# ORACLE TOWN Inner Loop: Delivery Summary

## What Was Built (Steps 0-4 Complete)

An **automatic, recursive governance machine** that accepts Creative Town (Claude/simulation) proposals, validates them through constitutional gates, executes tools safely in isolated sandboxes, produces cryptographic evidence, and feeds back structured decision facts.

---

## Completed Deliverables

### 1. **Kernel Contracts Documentation** (Step 0)
📄 `oracle_town/runner/KERNEL_CONTRACTS.md`

Froze all kernel interfaces to eliminate guessing:
- Policy.load() and policy_hash contract
- KeyRegistry constructor, verify_ed25519(), registry_hash
- Cryptographic utilities (canonical_json_bytes, build_canonical_message, verify_ed25519)
- IntakeGuard.evaluate() signature and rejection codes
- MayorRSM.decide() contract and pure function guarantee
- Attestation schema (required fields, patterns, signature format)
- DecisionRecord schema (immutability, hashing)

**Critical principle:** "Reuse. Don't duplicate." All runner code calls kernel functions directly, never re-implements them.

---

### 2. **Worktree Isolation Module** (Step 1)
📄 `oracle_town/runner/worktree.py`

Safe patch application in isolated temporary directories:

**Functions:**
- `make_temp_worktree(src_repo_root: str) -> str` — Creates isolated copy of repo
- `apply_patch(workdir: str, diff_text: str) -> PatchResult` — Applies unified diffs
- `cleanup_worktree(workdir: str) -> bool` — Removes temp directory

**Safety mechanisms:**
- ✅ Path validation: Rejects path traversal (`../`), absolute paths
- ✅ Allowlist: tests/, docs/, examples/, oracle_town/creative/, oracle_town/runner/
- ❌ Forbids: oracle_town/core/, oracle_town/keys/, oracle_town/policies/, oracle_town/schemas/
- ✅ Uses GNU patch (deterministic semantics)
- ✅ Preserves source repository (never modifies original)

**Tests:** 4/4 pass
- ✅ Create and cleanup worktree
- ✅ Reject forbidden paths
- ✅ Allow patchable paths
- ✅ Reject path traversal

---

### 3. **Supervisor (Token Sanitization)** (Step 2)
📄 `oracle_town/runner/supervisor.py`

Deterministic pre-pass that enforces K0 (Authority Separation) by detecting forbidden language:

**Features:**
- Unicode normalization (NFKC + zero-width character removal)
- Recursive JSON scanning with exempted paths
- Patch diff scanning (+ and - lines only)
- Detection of obfuscated tokens (e.g., "a​pprove" with zero-width space)

**Forbidden languages:**
- **Authority:** "ship", "approve", "safe", "verified", "passed", "certified", "clear", "ready", "go"
- **Ranking:** "best", "optimal", "priority", "recommended", "first", "winner", "chosen"
- **Confidence:** "confident", "guaranteed", "95%", "probably", "likely", "certainly"

**Codes:**
```python
SUP_FORBIDDEN_AUTHORITY_LANGUAGE
SUP_FORBIDDEN_RANKING_LANGUAGE
SUP_FORBIDDEN_CONFIDENCE_LANGUAGE
SUP_FORBIDDEN_PATCH_MODIFICATION
SUP_MALFORMED_JSON
SUP_UNICODE_NORMALIZATION_FAILURE
```

**Tests:** 5/5 pass
- ✅ Clean proposal passes
- ✅ Forbidden authority language rejected
- ✅ Zero-width obfuscation detected
- ✅ Confidence language rejected
- ✅ Exempted metadata allowed

---

### 4. **Intake Adapter** (Step 3)
📄 `oracle_town/runner/intake_adapter.py`

Wraps real IntakeGuard and provides stable interface for runner:

**Class: IntakeAdapter**
```python
def evaluate(
    proposal_bundle: Dict[str, Any],
    ct_run_manifest: Optional[Dict[str, Any]] = None
) -> IntakeAdapterDecision
```

**Returns: IntakeAdapterDecision**
- decision: "ACCEPT" or "REJECT"
- adapter_code: IntakeAdapterCode enum
- kernel_code: RejectionCode enum (from IntakeGuard)
- detail: human-readable explanation
- briefcase: normalized briefcase dict (if ACCEPT)
- ct_boundary_digest: sha256 of CT boundary

**Design principle:** Adapter normalizes output but never overrides decisions. IntakeGuard is source of truth.

**Tests:** 4/4 pass
- ✅ Accept clean bundle
- ✅ Reject forbidden fields
- ✅ Reject budget violation
- ✅ Serialize to JSON

---

### 5. **Factory Adapter (Evidence Production)** (Step 4)
📄 `oracle_town/runner/factory_adapter.py`

Converts tool outputs into Phase-2 signed attestations (the critical link between work and proof):

**Class: FactoryAdapter**
```python
def run_tool_and_attest(
    tool_command: str,
    workdir: str,
    run_id: str,
    claim_id: str,
    obligation_name: str,
    attestor_id: str = "ci_runner_001",
    attestor_class: str = "CI_RUNNER",
    signing_key_id: str = "key-2026-01-ci-prod"
) -> FactoryAttestation
```

**Flow:**
1. Run tool in isolated workdir (pytest, lint, tests, etc.)
2. Capture stdout + stderr
3. Compute evidence_digest = sha256(stdout + stderr)
4. Build canonical message (uses kernel function `build_canonical_message`)
5. Sign with Ed25519 (uses nacl library)
6. Validate attestation against schema

**Critical guarantee:** Uses EXACT same canonical message builder as Mayor verification, ensuring deterministic signatures.

**Attestation structure:**
```json
{
  "attestation_id": "att_run_001_test_pass_...",
  "run_id": "run_001",
  "claim_id": "claim_001",
  "obligation_name": "test_pass",
  "attestor_id": "ci_runner_001",
  "attestor_class": "CI_RUNNER",
  "policy_hash": "sha256:...",
  "key_registry_hash": "sha256:...",
  "evidence_digest": "sha256:...",
  "signing_key_id": "key-2026-01-ci-prod",
  "signature": "ed25519:base64-encoded-64-bytes",
  "policy_match": 1,
  "timestamp": "2026-01-26T..."
}
```

**Tests:** 3/3 pass
- ✅ Attestation structure valid
- ✅ All 11 required fields present
- ✅ Pattern validation (sha256, ed25519 format)

---

## Architecture Summary

```
Creative Town (Proposals)
         ↓
    [Supervisor] ← K0: Authority separation
         ↓
   [Intake Adapter] ← Schema validation
         ↓
    [Worktree] ← Patch isolation
         ↓
  [Factory Adapter] ← Cryptographic evidence
         ↓
    [Mayor RSM] ← Pure decision (kernel)
         ↓
 [Context Builder] ← K0-safe feedback (pending)
         ↓
    [CT Gateway] ← Next proposal (pending)
         ↓
   [InnerLoop] ← Recursion control (pending)
         ↓
  [Creative Observer] ← Cycle diary (pending)
```

---

## Invariants Enforced (So Far)

| Invariant | Mechanism | Status |
|-----------|-----------|--------|
| **K0** | Supervisor forbids authority language | ✅ Implemented |
| **K1** | Mayor defaults to NO_SHIP | ✅ Kernel (ready to use) |
| **K5** | Determinism: same inputs → same outputs | ✅ Canonical JSON + signatures |
| **K7** | Policy pinning: policy_hash immutable | ✅ Factory stores in attestation |

---

## Key Design Decisions

### 1. Fail Closed
Missing field → exception, never silent fallback.
```python
# ✅ Correct
if not evidence_digest or not evidence_digest.startswith("sha256:"):
    raise ValueError("EVIDENCE_DIGEST_MISSING")

# ❌ Wrong
evidence_digest = evidence_digest or "sha256:0000..."
```

### 2. Reuse Kernel Functions
Never duplicate `build_canonical_message`, `canonical_json_bytes`, etc.
```python
# ✅ Always use kernel
from oracle_town.core.crypto import build_canonical_message
message = build_canonical_message(...)

# ❌ Never hand-build
message = {"run_id": ..., "claim_id": ..., ...}
```

### 3. K0-Safe Feedback to CT
CT sees decision facts, not decision reasoning.
```python
# ✅ CT gets facts
{
    "policy_hash": "sha256:...",
    "required_obligations": ["test_pass"],
    "missing_obligations": ["lint_pass"],
    "blocking_reasons": [{"code": "QUORUM_MISSING", "obligation": "test_pass"}]
}

# ❌ CT never sees
{
    "mayor_internal_check": "...",
    "private_reasoning": "...",
    ...
}
```

---

## Ready for Next Steps

The foundation is complete. Steps 5-10 (pending) are now straightforward:

**Step 5: Ledger + Briefcase** → Extract obligations from intake, create ledger from attestations
**Step 6: Context Builder** → Build K0-safe facts for CT feedback
**Step 7: CT Gateway** → Integrate Claude API or simulation mode
**Step 8: InnerLoop** → Orchestrate all steps with recursion control
**Step 9: Creative Observer** → Log cycle-by-cycle evolution
**Step 10: Integration Tests** → Run test vectors A–H through full pipeline

All blueprint specs are in `IMPLEMENTATION_PROGRESS.md`.

---

## Files Delivered

```
oracle_town/runner/
├── KERNEL_CONTRACTS.md              ← ✅ Step 0: Frozen interfaces
├── README_INNER_LOOP.md             ← Overview + usage examples
├── IMPLEMENTATION_PROGRESS.md       ← Detailed specs for Steps 5-10
├── __init__.py                      ← Package init with exports
│
├── worktree.py                      ← ✅ Step 1: Safe patching
│   └── Tests: 4/4 pass
│
├── supervisor.py                    ← ✅ Step 2: Token sanitization
│   └── Tests: 5/5 pass
│
├── intake_adapter.py                ← ✅ Step 3: Validation wrapper
│   └── Tests: 4/4 pass
│
├── factory_adapter.py               ← ✅ Step 4: Evidence production
│   └── Tests: 3/3 pass
│
├── config.yaml                      (existing, for config)
├── logs/                            (for cycle logs)
├── state/                           (for run state)
└── staging/                         (for artifacts)
```

---

## Summary

**What you have:**
1. ✅ Constitutional kernel contracts (no guessing)
2. ✅ Safe, isolated patch application (worktree)
3. ✅ Deterministic token sanitization (supervisor)
4. ✅ Real proposal validation (intake adapter)
5. ✅ Cryptographic evidence production (factory adapter)

**What you can now build:**
- Bridge to CT (Claude API or simulation)
- Feedback loops (context builder)
- Recursion control (innerloop)
- Observation/tracing (creative observer)
- Full end-to-end testing

**Guarantees maintained:**
- K0: Authority Separation (Supervisor + IntakeGuard)
- K5: Determinism (Canonical JSON + Ed25519 signatures)
- K7: Policy Pinning (Immutable hashes per run)
- Fail-Closed behavior (Exceptions on missing fields)

---

## Next Session

Start with Step 5 (Ledger + Briefcase construction). Reference `IMPLEMENTATION_PROGRESS.md` for exact specs.

All critical guardrails are in place. Code reuse is enforced. Contracts are frozen.

**Ready to continue building the creative machine.**
