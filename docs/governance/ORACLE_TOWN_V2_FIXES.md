# 🔧 ORACLE TOWN V2 - Constitutional Fixes Applied

**Date:** January 21, 2026
**Status:** ✅ GOVERNANCE KERNEL COMPLETE
**Architecture:** Simulation UX with Constitutional Core

---

## 🎯 What Was Fixed

### Critical Architectural Issues Resolved

#### 1. Package Import Bug ✅
- **Problem:** `oracle-town/` (hyphen) but importing `oracle_town` (underscore)
- **Fix:** Renamed directory `oracle-town` → `oracle_town`
- **Added:** `pyproject.toml` for proper pip install

#### 2. Confidence/Scoring Removed from Decision Path ✅
- **Problem:** TownHall returned `confidence`, `score`, `recommendation` → Mayor used these for reasoning
- **Fix:** Mayor V2 uses ONLY attestations (no confidence, no reasoning)
- **Constitutional Rule:** `if attestation.policy_match == 1 → satisfied, else → not satisfied`

#### 3. Factory/Verification Layer Added ✅
- **Problem:** Mayor "reasoned" about obligations without verification
- **Fix:** Added `oracle_town/core/factory.py`:
  - Takes obligations from cognition layer
  - Runs verification tests (mocked for MVP, real for production)
  - Emits attestations (truth primitives)
  - Writes append-only ledger (`attestations_ledger.jsonl`)

#### 4. Mayor V2: Constitutional Verdict Engine ✅
- **Problem:** Mayor V1 used scoring, confidence, narrative reasoning
- **Fix:** `oracle_town/core/mayor_v2.py`:
  - NO reasoning, NO confidence
  - Pure lookup: `attestations.contains(obligation) → satisfied`
  - Constitutional rules (immutable):
    1. IF kill_switch → NO_SHIP
    2. ELSE IF unsatisfied_hard_obligations → NO_SHIP
    3. ELSE → SHIP

#### 5. Concierge → Mayor IO Boundary ✅
- **Problem:** Multiple components outputting "verdicts"
- **Fix:**
  - Pre-Mayor: Internal artifacts only (street reports, building briefs)
  - Mayor: ONLY component that writes `decision_record.json`
  - Remediation: Optional `remediation_plan.json` (Mayor-owned)

---

## 📊 New Data Model (JSON-First)

### Attestation (Truth Primitive)
```json
{
  "run_id": "RUN_...",
  "claim_id": "CLM_...",
  "obligation_name": "gdpr_consent_mechanism",
  "attestor": "CI_RUNNER|TOOL_RESULT|HUMAN_SIGNATURE",
  "policy_match": 1,
  "payload_hash": "sha256...",
  "timestamp": "2026-01-21T..."
}
```

### Decision Record (Mayor Output)
```json
{
  "run_id": "RUN_...",
  "claim_id": "CLM_...",
  "decision": "SHIP|NO_SHIP",
  "blocking_obligations": ["obligation_name_1", ...],
  "kill_switch_triggered": false,
  "attestations_checked": 3,
  "timestamp": "2026-01-21T...",
  "code_version": "oracle_town_v2.0.0"
}
```

### Remediation Plan (Optional, if NO_SHIP)
```json
{
  "run_id": "RUN_...",
  "claim_id": "CLM_...",
  "unsatisfied_obligations": [ /* full obligation objects */ ],
  "suggested_actions": [
    {
      "obligation_name": "security_audit",
      "action": "Run automated test",
      "command": "pytest tests/test_security.py",
      "expected_attestor": "CI_RUNNER"
    }
  ]
}
```

---

## ✅ Test Results

### Test Run: `test_oracle_town_v2.py`

**Scenario 1: Meta-commentary (no obligations)**
- Input: "Architectural analysis of codebase..."
- Obligations: 0
- Attestations: 0
- **Result: SHIP** ✅

**Scenario 2: Technical refactor (3 obligations)**
- Input: "Refactor to remove confidence from Mayor..."
- Obligations: 3 (all HARD)
- Attestations: 3 (all policy_match=1)
- **Result: SHIP** ✅

**Scenario 3: Kill-switch (LEGAL blocks)**
- Input: Any claim
- Kill-switch: LEGAL triggered
- **Result: NO_SHIP** ✅ (immediate, no attestation check)

**All tests passed!** 🎉

---

## 🏗️ Current Architecture

```
INPUT → CLAIM COMPILER
    ↓
COGNITION LAYER (Simulation UX)
├─ Streets (4 agents, ChatDev turns)
├─ Buildings (aggregate streets)
├─ Districts (domain expertise)
└─ Concierge (assembles briefcase)
    ↓
GOVERNANCE KERNEL (Truth Layer)
├─ Briefcase (required_obligations)
├─ Factory (verification → attestations)
└─ Mayor V2 (constitutional rules → decision)
    ↓
OUTPUT
├─ decision_record.json (SHIP | NO_SHIP)
└─ remediation_plan.json (if NO_SHIP)
```

---

## 📁 New Files Created

```
oracle_town/
├── core/
│   ├── factory.py              # ✅ NEW: Verification & attestation engine
│   └── mayor_v2.py             # ✅ NEW: Constitutional verdict engine
│
pyproject.toml                  # ✅ NEW: Proper package config
test_oracle_town_v2.py          # ✅ NEW: V2 governance tests
attestations_ledger.jsonl       # ✅ NEW: Append-only truth ledger
decisions/                      # ✅ NEW: Mayor output directory
├── decision_RUN_*.json
└── remediation_RUN_*.json
```

---

## 🎯 What Works Now

### Governance Features ✅
- ✅ NO_RECEIPT = NO_SHIP (enforced by Factory)
- ✅ Binary verdicts (SHIP | NO_SHIP, no maybe)
- ✅ Kill-switch authority (LEGAL/SECURITY)
- ✅ Append-only attestation ledger
- ✅ Deterministic verdicts (same attestations → same decision)
- ✅ No confidence/scoring in decision path
- ✅ Concierge → Mayor IO boundary enforced

### Simulation Features ✅
- ✅ Street agents with ChatDev turn protocol
- ✅ Building/District aggregation
- ✅ Rich debug telemetry (QI-INT scores, confidence for UX only)
- ✅ Spatial town metaphor
- ✅ User-friendly CLI

---

## 🚀 Next Steps

### Immediate (Add Districts)
- [ ] **ENGINEERING District** (code verification, tests, CI)
- [ ] **EV District** (Evidence & Validation, empirical checks)

### Soon
- [ ] Replace mock attestations with real test execution
- [ ] Add human attestation UI (for DOC_SIGNATURE type)
- [ ] Web UI with town visualization
- [ ] Integrate with existing ORACLE SUPERTEAM components

### Production
- [ ] Real LLM integration for cognition layer
- [ ] FastAPI server
- [ ] PostgreSQL for session persistence
- [ ] Agent memory & reflection

---

## 🎓 Key Insight

**"Simulation UX with Governance Kernel Inside"**

- **Cognition layer** (Streets, Buildings, Districts): Can use confidence, scores, narrative → makes system feel alive
- **Governance kernel** (Factory, Mayor): Pure truth checking, no reasoning → makes system trustworthy

This gives:
- ✅ Immediate demo value (visual, agents talking)
- ✅ User-friendly (town metaphor)
- ✅ Constitutional rigor (kernel enforces rules)
- ✅ Migration path (swap mocks → real tests later)

---

## 📊 Compliance Matrix

| Feature | V1 (ChatDev-style) | V2 (Constitutional) |
|---------|-------------------|---------------------|
| Binary verdicts | ✅ | ✅ |
| Uses confidence in decision | ❌ YES (broken) | ✅ NO (fixed) |
| Attestation ledger | ❌ Missing | ✅ Added |
| Factory verification | ❌ Missing | ✅ Added |
| Mayor reasoning | ❌ YES (broken) | ✅ NO (fixed) |
| Kill-switch | ✅ | ✅ |
| Append-only ledger | ❌ | ✅ |
| NO_RECEIPT = NO_SHIP | ❌ | ✅ |

---

## ✅ Status

**ORACLE TOWN V2 is now constitutionally compliant.**

- ✅ Governance kernel operational
- ✅ Simulation UX preserved
- ✅ Tests passing
- ✅ Ready for district expansion

**Ready to add ENGINEERING + EV districts and test with real claims!** 🏛️

---

**Next command:**
```bash
python3 test_oracle_town_v2.py  # Verify all tests pass
```
