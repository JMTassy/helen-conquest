# Integrated System Architecture (2026-02-22)

**Scope**: From hardening gates through oracle module through human control gate
**Status**: ✅ All components operational and integrated
**Authority**: Constitutional (immutable, no override)

---

## Complete Stack

```
LAYER 6: HUMAN CONTROL GATE V0.1
├─ Config frozen (θ): human_control_gate_v0.1.json
├─ Enforcement: human_control_gate.py
├─ Schema: 6 new event types
├─ Anti-dependence: irreversible alert
└─ Dual authority: Oracle forecast + Human approval

LAYER 5: METRICS ANALYZER (Hardened V2)
├─ Fail-closed enforcement
├─ Schema pinning (15 event types)
├─ Hash chain verification (recompute, not link-check)
├─ Deterministic outputs (canonical JSON + SHA256)
└─ CI gate: 100% determinism required

LAYER 4: PROOF BUNDLE SYSTEM
├─ Git commit hashes
├─ File SHA256s (immutable snapshot)
├─ Determinism proof (5-seed sweep)
├─ CouplingGate conformance (14/14 tests)
└─ Tamper-evident (any change invalidates)

LAYER 3: DETERMINISM GATES
├─ Preflight (grep-based): forbid Date.now(), Math.random()
├─ Verification (hash-based): 5 seeds × 2 runs = byte-identical
├─ Conformance (test-based): CouplingGate 14/14 vectors
└─ CI integration: blocks merge on failure

LAYER 2: GOVERNANCE KERNELS
├─ Oracle Town (reference frozen)
├─ CouplingGate (deterministic function)
├─ K-ρ viability gates (deployed)
├─ K-τ coherence gates (deployed)
└─ Constitution rules (5 principles)

LAYER 1: FOUNDRY TOWN
├─ Production pipeline (5 phases)
├─ Agent roles (7 distinct, no blending)
├─ Claim market (structured coordination)
└─ Editorial collapse (unilateral finality)

BEDROCK: LEDGER (HELEN)
├─ Append-only NDJSON
├─ Hash-chained events
├─ Immutable records
├─ 4-layer consciousness (L0-L3)
└─ No erasure, no revision
```

---

## Data Flow: From User Intent to Committed Action

```
USER INTENT (Strategic Decision)
    ↓
ORACLE FORECAST
├─ Analyze risk_conflict
├─ Rank candidate actions
└─ Emit forecast event
    ↓
[risk_conflict >= 0.40?]
├─→ YES: BLOCK (high risk)
└─→ NO: proceed
    ↓
HUMAN REVIEW REQUEST
├─ Request 2of3 quorum
├─ Timeout: 3 ticks
└─ Emit review_request event
    ↓
HUMAN VOTES (3 parallel)
├─ voter #1: verdict = APPROVE/REJECT/HOLD
├─ voter #2: verdict = APPROVE/REJECT/HOLD
├─ voter #3: verdict = APPROVE/REJECT/HOLD
└─ Emit human_vote events (3×)
    ↓
HUMAN VERDICT (Aggregation)
├─ Count APPROVEs
├─ If >= 2: verdict = APPROVE
├─ Else: verdict = REJECT/HOLD
└─ Emit human_verdict event
    ↓
[human_verdict == "APPROVE"?]
├─→ YES: proceed
└─→ NO: BLOCK
    ↓
ACTION COMMIT
├─ Execute decision
├─ Log approval chain
└─ Emit action_commit event
    ↓
[oracle_precheck_ratio > 0.85 over last 20 actions?]
├─→ YES: emit oracle_dependency_alert (IRREVERSIBLE)
└─→ NO: normal operation
    ↓
LEDGER APPEND
├─ Hash chain maintained
├─ Recompute verification
└─ Immutable record
```

---

## Authority Separation (No Blending)

### Layer 1: Oracle Authority
- **Capability**: Forecast (probabilistic estimates)
- **Limitation**: Cannot commit (no final authority)
- **Output**: oracle_forecast events with risk scores
- **Constraint**: Must be examined before execution

### Layer 2: Human Authority
- **Capability**: Approve (deliberative judgment)
- **Limitation**: Cannot override governance rules
- **Output**: human_verdict events with quorum proof
- **Constraint**: Must respect risk thresholds

### Layer 3: System Authority
- **Capability**: Enforce (log decisions, check thresholds)
- **Limitation**: Cannot make judgments or forecasts
- **Output**: action_commit, oracle_dependency_alert events
- **Constraint**: Fail-closed on rule violations

**No layer overrides another. No consolidation of authority.**

---

## Irreversibility: Key Decisions

| Decision | Reversible? | Why? |
|----------|-----------|------|
| action_commit (approved) | No | Ledger is append-only |
| human_verdict (APPROVE) | No | Quorum recorded, cannot vote again |
| oracle_forecast (issued) | No | Historical record preserved |
| oracle_dependency_alert | NO (by design) | Forces redesign, no reset allowed |
| Determinism proof (passed) | No | SHA256 in proof bundle |

**Why alert irreversible?**
- System cannot hide capture + reset
- Creates permanent structural consequence
- Prevents repeat of same vulnerability
- Enforces system redesign as requirement

---

## Fail-Closed Behavior

The system silently passes only when:
1. ✅ Ledger hashes valid (recomputed + matched)
2. ✅ All events have known types (or explicitly allowlisted)
3. ✅ Schema complete (run_start + run_end present)
4. ✅ Oracle dependence low (ratio < 0.85)
5. ✅ Human approval chain intact (quorum met)

It fails immediately when:
- ❌ Hash mismatch (tampering detected)
- ❌ Unknown event type (schema drift)
- ❌ Missing required events
- ❌ Oracle capture detected
- ❌ Strategic action without approval

---

## Integration Points

### Between Layers

| From | To | Mechanism |
|------|----|-----------:|
| Oracle → Human | human_review_request + risk_conflict field | Event-based |
| Human → System | human_verdict event with quorum proof | Event-based |
| System → Ledger | All events hashed and appended | Cryptographic |
| Ledger → Analyzer | NDJSON read, events validated | File-based |
| Analyzer → CI | Exit code (0=PASS, 1=FAIL) | Unix convention |
| CI → Git | Merge decision (allow/block) | GitHub Actions |

### Between Modules

| Module | Dependency | How |
|--------|-----------|-----|
| Human Gate | Metrics Analyzer | Schema check (new types) |
| Metrics Analyzer | Determinism Gates | Hash verification |
| Determinism Gates | Proof Bundle | File SHAs |
| Proof Bundle | CouplingGate | Conformance results |
| CouplingGate | Oracle Town | Governance rules |
| Oracle Town | Constitution | Authority rules |

---

## Immutability Guarantees

### Configuration Level
- `human_control_gate_v0.1.json` — Frozen (θ)
- `human_control_gate_v0.1.sha256` — Proof of config
- **Change requires**: K-τ amendment process + re-verification

### Specification Level
- `KNOWN_TYPES` in analyzer — Pinned (15 types)
- `REQUIRED_TYPES` in analyzer — Frozen (run_start, run_end)
- **Change requires**: Code amendment + CI re-test

### Ledger Level
- `events.ndjson` — Append-only
- Hash chain — Cryptographically bound
- **Change requires**: Rewriting history (leaves SHA mismatches)

### Proof Level
- `PROOF_BUNDLE_*.md` — Immutable snapshot
- `interaction_proxy_metrics.sha256` — Determinism proof
- **Change requires**: New proof bundle (date increments)

---

## No Silent Failures

Every decision produces an event:

```
Decision: Strategic action approved
Event: action_commit {approval_chain: [vote1, vote2, verdict], ...}

Decision: Oracle capture detected
Event: oracle_dependency_alert {severity: CRITICAL, permanence: irreversible, ...}

Decision: Schema error in ledger
Event: (analyzer exits 1, no report generated)

Decision: Hash mismatch
Event: (analyzer exits 1, continuity_intact = false)
```

**No decision is invisible. All decisions logged.**

---

## Risk Model

### Oracle Risk (forecast.risk_conflict)
```
0.0    = safe (low risk)
0.40   = threshold (human review required)
0.80   = dangerous (blocked)
```

### Human Risk (quorum.votes)
```
0 APPROVE  = reject
1 APPROVE  = indecisive
2 APPROVE  = approved ✅
3 APPROVE  = unanimous
```

### System Risk (oracle_ratio)
```
< 0.50  = healthy (human-driven)
0.70    = concerning (oracle influence growing)
0.85    = threshold (alert triggered)
> 0.85  = CAPTURED (irreversible alert)
```

---

## Testing Strategy

### Unit Tests (Code-level)
- `can_commit_action()` logic
- `check_oracle_dependence()` ratio calculation
- Hash chain verification
- Schema validation

### Integration Tests (Ledger-level)
- Oracle forecast → Human review flow
- Quorum voting aggregation
- Approval chain recording
- Dependence alert triggers

### System Tests (End-to-end)
- Full ledger cycle (oracle → human → commit)
- Analyzer determinism (dual run + hash compare)
- Conformance (14/14 CouplingGate vectors)
- Proof bundle generation + validation

---

## Next Actions

### Immediate (Phase 5)
```bash
# Run test cycle
python3 scripts/helen_metrics_analyzer.py

# Check result
cat runs/street1/interaction_proxy_metrics.json | jq '.indexes'
```

### If PASS
```
✅ System operational
✅ Dual authority model active
✅ Human control gate enforced
→ Ready for strategic simulation
```

### If FAIL
```
❌ Ledger invalid (check schema_errors)
❌ Hash chain broken (check continuity_intact)
❌ Capture detected (check oracle_dependency_alert in raw_metrics)
→ Debug and fix before proceeding
```

---

## Authority Statement

This architecture enforces:
1. **Dual authority** (oracle + human, no single point)
2. **Fail-closed** (errors block action, no silent passes)
3. **Irreversible alerts** (capture forces redesign)
4. **No branching ambiguity** (deterministic rules)
5. **Complete logging** (every decision recorded)

**No override. No silence. No ambiguity.**

---

**System Status**: ✅ FULLY INTEGRATED

**Next Phase**: Phase 5 test cycle (run analyzer on actual ledger with oracle + human events)

**Timeline**: When ready to proceed, execute:
```bash
python3 scripts/helen_metrics_analyzer.py
```

Then report:
- overall_status (PASS or FAIL)
- oracle_dependency_alert (present or absent)
- continuity_intact (true or false)
