# ORACLE SUPERTEAM — Constitution

**Version:** 1.0.0
**Immutable:** This document defines the non-negotiable axioms of the ORACLE SUPERTEAM framework.

---

## Core Axioms (Non-Negotiable)

### 1. NO_RECEIPT = NO_SHIP

Any claim asserting real-world effects or attestable facts **must** be accompanied by cryptographically hashable proof (receipts).

- Receipts include: dataset hashes, test logs, signed attestations, simulation outputs, URLs with content hash
- If `requires_receipts = true` and `receipts < required` → **automatic block**

### 2. Superteams are Non-Sovereign

Superteams (multi-agent production teams) may **propose** obligations and emit **signals**, but they **cannot** decide outcomes.

- No voting power
- No narrative persuasion
- No direct influence on verdicts
- Output: structured obligations only

### 3. Verdicts are Binary

The system emits exactly two possible outcomes:

- **SHIP** (ship_permitted = true)
- **NO_SHIP** (ship_permitted = false)

Intermediate states (QUARANTINE, KILL) are internal classifications that **always** map to NO_SHIP.

### 4. Kill-Switch Dominance

Any authorized KILL signal → **immediate NO_SHIP**, regardless of:

- Vote count
- Score (S_c)
- Other team approvals

Authorized kill-switch teams (as defined in `OracleConfig`):
- Legal Office
- Security Sector

**Rule-based KILL:** High-severity contradictions (e.g., HC-PRIV-001) trigger automatic kill, even without explicit vote.

### 5. Replay Determinism

Same inputs **must** produce same outputs.

- Identical claim + evidence + votes → identical hashes
- Timestamp and order variations are normalized
- Hash mismatches indicate system corruption (fail CI)

---

## Decision Pipeline (Jurisdictional Layers)

### Layer 1: Production (Superteams)

- Generate candidate obligations
- Emit non-binding signals
- **No verdict authority**

### Layer 2: Adjudication (Critic Agent)

- Apply lexicographic veto rules:
  1. Kill-switch check
  2. Rule-based contradictions (HC-*)
  3. Evidence sufficiency
  4. Logical coherence
- Output: blocking obligations list

### Layer 3: Integration (Verdict Engine)

Deterministic automaton applying fixed rules:

```
IF kill_switch_triggered OR rule_kill_triggered → NO_SHIP
ELSE IF blocking_obligations > 0 → NO_SHIP
ELSE IF contradictions nonempty → NO_SHIP
ELSE IF S_c >= τ_accept → SHIP
ELSE → NO_SHIP
```

No explanations. No opinions. No override buttons.

---

## Vote Semantics

| Vote | Meaning | Effect |
|------|---------|--------|
| APPROVE | Support claim | Phase = 0 (constructive) |
| CONDITIONAL | Support with obligations | Opens domain-specific obligation |
| OBJECT | Oppose | Phase = π/2 (destructive) |
| QUARANTINE | Suspend for review | Opens contradiction obligation |
| REJECT | Block | Phase = π (fully destructive) |
| KILL | Immediate halt | Overrides all other votes (authorized teams only) |

---

## Obligation Types

| Type | Owner Team | Closure Criteria |
|------|-----------|------------------|
| METRICS_INSUFFICIENT | Engineering, Data Validation | Verified metrics with receipts |
| LEGAL_COMPLIANCE | Legal Office | Compliance audit + legal sign-off |
| SECURITY_THREAT | Security Sector | Security assessment + mitigation plan |
| EVIDENCE_MISSING | Any | Supply missing receipts |
| CONTRADICTION_DETECTED | Data Validation | Resolve evidence-tag conflicts |

**Blocking Rule:** If any obligation has `status: OPEN` → verdict = NO_SHIP

---

## Contradiction Rules (Hard-Coded)

### HC-PRIV-001 (HIGH severity)
**Trigger:** `no_personal_data_claim` + `biometric` / `face` / `pii`
**Effect:** Automatic KILL (rule_kill_triggered = true)

### HC-SEC-002 (MEDIUM severity)
**Trigger:** `provably_secure_claim` + `heuristic_only` / `no_formal_proof`
**Effect:** Quarantine + obligation

### HC-LEGAL-003 (MEDIUM severity)
**Trigger:** `gdpr_compliant_claim` + `no_scc`
**Effect:** Quarantine + obligation

---

## QI-INT v2 Scoring

Quantum Interference Integration (deterministic complex amplitude sum):

```
a_{c,t} = r(tier) × exp(i × θ(vote))
A_c = Σ_t w_t × a_{c,t}
S_c = |A_c|²
```

**Thresholds:**
- τ_accept = 0.75 (SHIP threshold)
- τ_quarantine = 0.4 (reference only)

**Team Weights (w_t):**
- Legal Office: 1.00
- Security Sector: 1.00
- Engineering Wing: 0.85
- Data Validation: 0.80
- COO HQ: 0.75
- UX/Impact: 0.70
- Strategy HQ: 0.65

---

## Canonicalization Rules

### Fields Excluded from Hash
- `run_id`
- `timestamp_start`, `timestamp_end`
- `votes[].timestamp`
- `event_log[].t`

### Deterministic Ordering
- Votes sorted by `team` (alphabetical)
- JSON keys sorted
- No floating-point randomness
- Fixed phase constants (π exact)

---

## Forbidden Extensions

The following modifications **violate** the constitution:

- ❌ Soft consensus (weighted averaging without veto)
- ❌ Confidence language ("probably", "likely")
- ❌ Narrative arbitration (choosing "best argument")
- ❌ Override buttons (manual SHIP without clearing obligations)
- ❌ Non-deterministic scoring (random, LLM-generated)
- ❌ Sovereign superteams (teams that can decide outcomes)

---

## Allowed Extensions

The following **preserve** constitutional integrity:

- ✅ New Superteams (with non-sovereign constraints)
- ✅ New obligation types (must be clearable)
- ✅ New contradiction rules (must be deterministic)
- ✅ Human attestation UI (evidence submission)
- ✅ Parallel production teams (ChatDev-style)
- ✅ Visualization layers (diagnostic only)

---

## Audit Requirements

Every RunManifest **must** contain:

1. `inputs_hash` (claim + evidence + votes)
2. `outputs_hash` (derived + decision)
3. `code_version` (git hash or semver)
4. Full event log (with normalized timestamps)

**CI Requirement:** All test vault scenarios must pass with:
- Expected verdicts
- Replay equivalence (S-08)
- Hash stability

---

## Emergency Override Protocol

**None.** There is no emergency override.

If the system blocks a critical decision:
1. Clear the blocking obligations (supply evidence)
2. Resolve contradictions (fix evidence tags)
3. Obtain kill-switch team approval (if needed)

The system **does not** have a "just ship it anyway" button.

---

**End of Constitution**

*This framework is not an agent society. It is not a conversation. It is an institution.*
