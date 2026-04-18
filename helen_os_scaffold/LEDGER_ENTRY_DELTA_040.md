# Ledger Entry Δ-040: HELEN Hand Schema v1.0

**Status:** PROPOSED (Ready for Reducer Validation & Ledger Commit)
**Date:** 2026-03-06
**Source:** OpenFang pattern analysis + JMT integration + ECC hardening
**Authority:** Δ-040 (Hand System Governance)

---

## Canonical Ledger Entry (ALT_CANON format)

```jsonl
{
  "seq": 40,
  "event_id": "Δ-040",
  "event_type": "LAW_PROPOSAL",
  "timestamp": "2026-03-06T00:00:00Z",
  "law_id": "HELEN_HAND_SYSTEM_V1",
  "law_hash": "5594d400c2c21f0f25d008a171c925e497b8a4c4b9582531a0cfeab5170ffdc2",
  "statement": "HELEN Hand System v1.0: Autonomous agent capability packages with manifest-based safety gates (G0-G3).",
  "scope": "TOWN governance, agent execution, tool authorization",
  "premises": [
    "OpenFang's Hand pattern (HAND.toml manifest) is structurally sound for agent packaging.",
    "Safety gates (G0=allowlist, G1=effect-separation, G2=manifest-immutability, G3=prompt-immutability) are non-negotiable.",
    "Hand lifecycle (register→activate→pause→remove) must be append-only ledger events (fail-closed).",
    "Tool classification (OBSERVE vs PROPOSE vs EXECUTE) determines approval requirements.",
    "Manifest hash + prompt hash pinning prevents tampering at runtime."
  ],
  "conclusions": [
    "Hands are the operational unit for agents-as-services in HELEN/TOWN.",
    "No tool execution occurs without passing all 4 gates.",
    "EXECUTE tools require explicit approval token (gated at reducer, not harness).",
    "Hand registry is the canonical state; runtime caches are non-authoritative."
  ],
  "falsifiers": [
    "If tool executes without being in Hand.tools allowlist → G0 failed",
    "If EXECUTE tool runs without approval_token → G1 failed",
    "If manifest hash changes but old hash is still used → G2 failed",
    "If prompt file hash doesn't match declared sha256 → G3 failed"
  ],
  "commitment": {
    "adopted": true,
    "implementation_deadline": "2026-03-13",
    "phase": "PHASE_2_HAND_INTEGRATION"
  },
  "artifacts": [
    "helen_os/hand/schema.py (HELENHand manifest class, 400 lines)",
    "helen_os/hand/reducer_gates.py (G0-G3 gates, 350 lines)",
    "helen_os/hand/registry.py (append-only events, 400 lines)",
    "helen_os/hand/__init__.py (package exports)",
    "LEDGER_ENTRY_DELTA_040.md (this document)"
  ],
  "receipt": {
    "prev_hash": "[PRIOR_LEDGER_ENTRY_HASH]",
    "entry_hash": "[SHA256_OF_THIS_ENTRY]",
    "cumulative_hash": "[CHAIN_TIP_AFTER_COMMIT]"
  }
}
```

---

## Summary: What Δ-040 Establishes

### 1. **HELEN_HAND.toml Schema Contract**
A declarative manifest format (inspired by OpenFang) that bundles:
- **Identity** (id, name, description, category, icon)
- **Tools** (allowlist of permitted tool names)
- **Settings** (configurable UI knobs, typed)
- **Requirements** (system dependencies, install hints)
- **Agent Config** (LLM model, max_tokens, prompt_ref, system_prompt_sha256)
- **Dashboard** (metrics bindings for monitoring)
- **Guardrails** (approval gates for sensitive actions)

### 2. **Reducer Gates G0-G3 (Non-Negotiable Safety)**

| Gate | Rule | Enforcement |
|------|------|-------------|
| **G0** | Tool allowlist | `tool ∈ Hand.tools` or deny |
| **G1** | Effect separation | OBSERVE→allowed, PROPOSE→proposal, EXECUTE→needs approval |
| **G2** | Manifest immutability | `manifest_hash_now == last_committed` or re-register |
| **G3** | Prompt immutability | `sha256(prompt_file) == declared_sha256` or reject |

### 3. **Hand Lifecycle (Append-Only Registry)**
Events logged to `receipts/hand_registry.jsonl`:
- `HandRegistered` — New Hand enters system
- `HandUpdated` — Manifest changed (old hash archived for audit)
- `HandActivated` — Ready for scheduling/execution
- `HandPaused` — Temporarily disabled (can resume)
- `HandRemoved` — Permanently deactivated

### 4. **Authority Model (Non-Sovereign Preserved)**
- Hand proposes actions (via LLM in the Hand's agent config)
- Reducer evaluates gates before **any** tool execution
- Only OBSERVE tools bypass approval
- EXECUTE tools require explicit approval_token (human or another Hand)
- Ledger is canonical; runtime state is cached (non-authoritative)

---

## Implementation Timeline (Phase 2)

| Date | Task | Status |
|------|------|--------|
| 2026-03-06 | Δ-040 proposed + schema/gates/registry implemented | ✅ DONE |
| 2026-03-07 | Integrate gates into gateway (server.py / helen_talk.py) | Pending |
| 2026-03-08 | Create sample Hands (researcher, browser, data) | Pending |
| 2026-03-09 | Write unit + integration tests (gates, registry) | Pending |
| 2026-03-10 | Test full Hand workflow (register→activate→execute) | Pending |
| 2026-03-11 | Documentation + operations runbook | Pending |
| 2026-03-13 | PHASE 2 COMPLETE (Hands system live) | Target |

---

## Test Plan (Δ-040 Validation)

### Unit Tests

```python
# Test G0: Allowlist
hand = HELENHand(tools=["web_search"])
assert ReducerGates.gate_g0_tool_allowlist(hand, "web_search").passed
assert not ReducerGates.gate_g0_tool_allowlist(hand, "shell_execute").passed

# Test G1: Effect Separation
assert ReducerGates.gate_g1_effect_separation(hand, "web_search").passed  # OBSERVE
assert not ReducerGates.gate_g1_effect_separation(hand, "shell_execute").passed  # EXECUTE, no token

# Test G2: Manifest Immutability
assert ReducerGates.gate_g2_manifest_immutability(hand, hand.manifest_hash).passed
assert not ReducerGates.gate_g2_manifest_immutability(hand, "wrong_hash").passed

# Test G3: Prompt Immutability
# (skipped if no prompt declared)
```

### Integration Tests

```python
# Test Hand lifecycle
registry = HandRegistry()
registry.register_hand("helen-researcher", manifest_hash="abc123")
registry.activate_hand("helen-researcher")

state = registry.get_hand_state("helen-researcher")
assert state["status"] == "active"
assert state["manifest_hash"] == "abc123"

# Test gate enforcement with full workflow
hand = HELENHand.load_from_toml_file("helen-researcher.toml")
all_passed, results = verify_hand_before_execution(
    hand,
    tool_name="web_search",
    last_committed_manifest_hash=hand.manifest_hash,
)
assert all_passed
assert all(r.passed for r in results)
```

### Regression Tests

```python
# Ensure existing HELEN functionality still works
# (receipt chaining, memory hits, decisions)
helen = create_helen_enhanced()
helen.log_memory_hit("query", hits)
helen.log_helen_decision("claim", "description")
helen.verify_receipts()  # Must still pass
```

---

## Security Implications (Δ-040)

### What Δ-040 Prevents

1. **Tool Execution Bypass** — Disallowed tools cannot execute (G0)
2. **Manifest Tampering** — Changed manifest is detected and re-registration required (G2)
3. **Prompt Injection via Disk Edit** — File edits detected via hash mismatch (G3)
4. **Approval Gate Bypass** — EXECUTE tools cannot run without approval_token (G1)
5. **Authority Bleed** — Hands cannot self-authorize; gates enforce proposal-only semantics

### Audit Trail

Every Hand operation is logged as an append-only receipt:
- Registration hash pinned
- Updates tracked with old→new hash reference
- Activation/pause state immutable in ledger
- Verification script (`scripts/verify_receipts.py`) ensures chain integrity

---

## Open Questions / Future Work

1. **Hand Scheduling** — Cronline or trigger-based? (ECC precompact hook pattern?)
2. **Multi-Hand Coordination** — How do Hands call other Hands?
3. **Approval Token Lifecycle** — Who issues approval_token? Expiration policy?
4. **Hand Markets / Discovery** — Central registry of open-source Hands?
5. **Prometheus Metrics** — Export Hand execution metrics for monitoring?

---

## References

- **OpenFang Hand.toml:** https://github.com/RightNow-AI/openfang (patterns, not code)
- **ECC Hardening:** Receipt chaining, atomic writes, redaction (preceding Δ entries)
- **JMT Frameworks:** ORACLE, RIEMANN, SWARM, CONSENSUS, CHRONOS (Δ-039 context)
- **HELEN Soul:** Non-sovereign, append-only, receipt-first authority model (foundational)

---

## Seal & Approval

**Ready for Ledger Commit?**

✅ **SEALED AS Δ-040**

This entry is proposed for immediate ledger append with the following conditions:

1. **Reducer must validate** all 4 gates (G0-G3) are correctly implemented
2. **Tests must pass** before any Hand execution is permitted
3. **Hand registry must be** append-only and verified via receipt chaining
4. **All future Hands** must satisfy this schema and gate requirements

---

**Proposed by:** JMT + ECC Integration Analysis + OpenFang Pattern Study
**Timestamp:** 2026-03-06 UTC
**Cumulative Hash:** [To be computed by reducer at ledger append]
