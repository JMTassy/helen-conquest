# ORACLE TOWN Inner Loop: Implementation Progress

## Completed Steps (✅)

### Step 0: Kernel Contracts Documentation
**File:** `KERNEL_CONTRACTS.md`

Froze all kernel interfaces with exact signatures:
- Policy.load() contract
- KeyRegistry constructor and verify_ed25519()
- Cryptographic utilities (canonical_json_bytes, build_canonical_message)
- IntakeGuard.evaluate() signature
- MayorRSM.decide() contract
- Attestation schema requirements
- DecisionRecord schema requirements

**Key principle:** Reuse kernel functions directly. Never duplicate or adapt them.

---

### Step 1: Worktree Isolation (✅)
**File:** `worktree.py`

Implemented safe patching in temporary directories:
- `make_temp_worktree()` — creates isolated copy of repo
- `apply_patch()` — applies unified diffs with path validation
- Path traversal protection (rejects `../`, absolute paths)
- Allowlisted paths: tests/, docs/, examples/, oracle_town/creative/, oracle_town/runner/
- Forbidden paths: oracle_town/core/, oracle_town/policies/, oracle_town/keys/, oracle_town/schemas/
- Cleanup with `cleanup_worktree()`

**Tests:** All 4 tests pass (creation, forbidden paths, patchable paths, path traversal)

---

### Step 2: Supervisor Pre-Pass (✅)
**File:** `supervisor.py`

Deterministic token sanitization with injection defense:
- `SupervisorRejectCode` enum (5 frozen codes)
- Unicode normalization (NFKC + zero-width removal)
- Forbidden words: AUTHORITY, RANKING, CONFIDENCE languages
- Recursive JSON scanning with exempted path list
- Patch diff scanning (+ and - lines only)
- Detection of obfuscated tokens (e.g., "a​pprove" with zero-width space)

**Invariant K0:** CT cannot use authority/approval language
**Tests:** All 5 tests pass (clean, forbidden, zero-width, confidence, exempted metadata)

---

### Step 3: Intake Adapter (✅)
**File:** `intake_adapter.py`

Wraps real IntakeGuard with stable interface:
- `IntakeAdapterDecision` dataclass for normalized output
- Maps kernel `RejectionCode` to `IntakeAdapterCode`
- Preserves all information; never drops data
- Serializable to JSON (for logging)

**Invariant:** IntakeGuard is source of truth. Adapter only normalizes.
**Tests:** All 4 tests pass (accept, forbidden fields, budget violation, serialization)

---

### Step 4: Factory Adapter (✅)
**File:** `factory_adapter.py`

Converts tool outputs into Phase-2 signed attestations:
- `_run_tool()` — executes command in isolated workdir, captures output
- `_build_attestation()` — builds signed attestation using kernel functions
- `_sign_canonical_message()` — Ed25519 signing with nacl library
- `_validate_attestation()` — schema-based validation
- `FactoryToolResult` and `FactoryAttestation` dataclasses

**Critical:** Uses `build_canonical_message()` and `canonical_json_bytes()` from kernel. Never hand-builds digests.

**Invariant K0:** Only Factory produces evidence. CT proposes work only.
**Tests:** All 3 tests pass (initialization, structure validation, required fields)

---

## Next Steps (Pending)

### Step 5: Ledger + Briefcase Construction
**What to build:**
```python
# Create briefcase from intake decision
class BriefcaseBuilder:
    def from_intake_decision(intake_decision) -> Dict:
        # Extract obligations from briefcase field
        # Build obligations list with:
        #   - name
        #   - type (HARD, SOFT)
        #   - severity
        #   - required_attestor_classes
        #   - min_quorum
        return briefcase_dict

# Create ledger for Mayor
class LedgerBuilder:
    def from_attestations(attestations: List[Dict]) -> Dict:
        # Build ledger with attestations array
        # Compute ledger_digest
        return ledger_dict
```

**Testing:** Run Phase-2 test vectors (A–H) through MayorRSM

---

### Step 6: Context Builder (K0-Safe Feedback)
**What to build:**
```python
class ContextBuilder:
    def build_context_for_ct(
        decision_record: Dict,
        policy: Policy,
        briefcase: Dict
    ) -> Dict:
        # Return K0-safe facts:
        # - policy_hash
        # - required_obligations (names + classes + quorum)
        # - last_decision (SHIP / NO_SHIP)
        # - blocking_reasons (reason_code + obligation_name only)
        # - missing_obligations list
        # Do NOT include: Mayor reasoning, internal checks

        return context_dict
```

**Invariant K0:** CT sees decision facts, not decision logic

---

### Step 7: CT Gateway
**What to build:**
```python
class CTGateway:
    def evaluate_ct_output(
        ct_output: Dict,
        context: Dict
    ) -> Dict:  # Must be JSON
        # Mode 1: SIMULATE
        #   - Return hardcoded test patches deterministically
        # Mode 2: CLAUDE
        #   - Call Claude API with context
        #   - Parse JSON response
        #   - Fail closed if not JSON

        return ct_output_dict
```

---

### Step 8: Innerloop Orchestrator
**What to build:**
```python
class InnerLoop:
    def run_cycle(
        cycle_n: int,
        context: Dict,
        workdir: str
    ) -> Dict:  # Decision record
        # Step 1: CT gateway (propose patches)
        # Step 2: Supervisor (sanitize)
        # Step 3: Intake adapter (validate)
        # Step 4: Factory (execute + attest)
        # Step 5: Mayor adapter (decide)
        # Step 6: Log to cycle diary
        return decision_record

    def run_full_innerloop(
        max_cycles: int = 10,
        rejection_barrier: int = 3
    ) -> Dict:  # Final decision record
        # Bounded recursion with barriers:
        # - MAX_CYCLES (default 10)
        # - REJECTION_STREAK (stop if 3 rejections in a row)
        # - MAX_PROPOSAL_BYTES (10 KB)
        # - MAX_PATCH_BYTES (50 KB)
        # Fixed randomness seed for determinism
```

**Invariant K5:** Determinism across runs

---

### Step 9: Creative Trace Observer
**What to build:**
```python
class CreativeObserver:
    def log_cycle(
        cycle_n: int,
        context: Dict,
        ct_output: Dict,
        supervisor_decision: Dict,
        intake_decision: Dict,
        factory_attestations: List[Dict],
        decision_record: Dict
    ):
        # Save to cycle_n/ directory:
        # - context.txt (K0-safe)
        # - ct_output.json
        # - supervisor_decision.json
        # - intake_decision.json
        # - factory_evidence.bin (gzipped)
        # - attestations.json
        # - decision_record.json
        # - summary.md (generated by runner, not Mayor)
```

**This is the "town diary" for observing creative evolution.**

---

### Step 10: Integration Tests
**What to test:**
- Run Phase-2 test vectors (A–H) through full runner pipeline
- Compare with direct kernel outputs
- Verify determinism (same run twice = same decision_record_hash)
- Check all attestations validate against schema
- Verify signatures with real keys

---

## Critical Guardrails

1. **Fail Closed:** Missing field = exception, never silent fallback
2. **Determinism:** Same inputs → identical outputs (hash-verified)
3. **Authority Separation (K0):** CT proposes → Factory attests → Mayor decides
4. **Reuse Kernel:** Never duplicate build_canonical_message, canonical_json_bytes, etc.
5. **Immutable Records:** Ledger is append-only, decision_records are immutable

---

## File Structure

```
oracle_town/runner/
├── KERNEL_CONTRACTS.md          ✅ (Step 0)
├── IMPLEMENTATION_PROGRESS.md   (this file)
├── worktree.py                  ✅ (Step 1)
├── supervisor.py                ✅ (Step 2)
├── intake_adapter.py            ✅ (Step 3)
├── factory_adapter.py           ✅ (Step 4)
├── briefcase_ledger.py          (Step 5)
├── context_builder.py           (Step 6)
├── ct_gateway.py                (Step 7)
├── innerloop.py                 (Step 8)
├── creative_observer.py         (Step 9)
├── __init__.py
├── config.yaml
├── logs/
├── state/
└── staging/
```

---

## Next: Implement Steps 5-10

Each step is independent (once Step 4 complete). Recommend order:
1. **Step 5** (briefcase/ledger) — enables Mayor integration
2. **Step 6** (context builder) — enables CT feedback
3. **Step 7** (CT gateway) — enables proposals
4. **Step 8** (innerloop) — orchestrates everything
5. **Step 9** (creative observer) — logging
6. **Step 10** (integration tests) — validation

Each step should:
- Have clear docstrings
- Include `if __name__ == "__main__"` tests
- Pass before moving to next step
- Be reviewed against KERNEL_CONTRACTS.md

---

## Known Risks

**Pitfall A (Contract Drift):** ✅ Mitigated by KERNEL_CONTRACTS.md + reusing kernel functions

**Pitfall B (Token Scanner):** ✅ Fixed by normalizing before splitting (catches zero-width)

**Pitfall C (Patch Application):** ✅ Fixed by using GNU patch + path validation

**Pitfall D (CT Optimization):** Mitigate by never showing ship-rate metrics to CT

**Pitfall E (Silent Fallbacks):** ✅ Mitigated by failing closed on missing hashes

---

**Status:** Ready for Steps 5-10 implementation.
