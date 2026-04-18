# Quick Start: Autonomous Mode

**You are here:** Month 1, Day 1 of Oracle Town autonomous iteration

---

## Three Daily Commands

### 1. Green Gate (Always First)

```bash
bash scripts/town-check.sh
```
- **Time:** 65ms
- **Output:** GREEN or RED
- **What:** Doc indices current + Python syntax valid
- **When:** Every iteration before commit

### 2. Optional Evidence Check

```bash
TOWN_EVIDENCE=1 bash scripts/town-check.sh
```
- **Time:** 100ms total
- **Output:** Details of 5 breakthroughs
- **What:** Validates all claims grounded in artifacts
- **When:** Before submitting report or claiming governance

### 3. Heavy Verification (Optional)

```bash
bash oracle_town/VERIFY_ALL.sh
```
- **Time:** ~10 seconds
- **Output:** All K0–K7 tests pass
- **What:** 13 unit tests + 3 adversarial runs + 30 determinism checks
- **When:** End of iteration or before major claims

---

## Submit External Knowledge

### Math Proof
```bash
cat << 'EOF' | python3 scripts/bibliotheque_intake.py MATH_PROOF
Claim: [your claim]
Proof: [your proof]
EOF
```

### Code Archive
```bash
cat << 'EOF' | python3 scripts/bibliotheque_intake.py CODE_ARCHIVE
[your code: Python/Go/Rust/etc]
EOF
```

### Research Paper / Data / Logs / Policy
```bash
cat << 'EOF' | python3 scripts/bibliotheque_intake.py RESEARCH
[research excerpt or paper summary]
EOF
```

---

## Three Key Invariants

| Invariant | Meaning | Enforced |
|-----------|---------|----------|
| **K3: Quorum** | Decisions need 2+ distinct attestor classes | Mayor RSM checks before SHIP |
| **K5: Determinism** | Same input → same output (30x verified) | Replay test on every run |
| **K7: Policy Pinning** | Policy immutable via hash (structure validated) | decision_record.json references policy hash |

---

## System Architecture (30-Second Overview)

```
Your Claim
    ↓
[Intake Guard] — Validate schema, detect anomalies
    ↓
[Districts] — Legal, Technical, Business, Social analysis
    ↓
[Town Hall] — Score + invariant checks
    ↓
[Mayor RSM] — Pure function: (policy, briefcase, ledger) → decision
    ↓
[Ledger] — Append-only record with cryptographic receipt
    ↓
[Evidence System] — Auto-validate claims (no silent drift)
```

---

## This Month's Goal

Demonstrate that **soft governance can be converted to hard constraints through test failures**.

**Example:** Add Privacy District to handle GDPR claims
1. Create `SCENARIO_NEW_DISTRICT.md` (walk-through)
2. Define soft policy (PDF best-effort approach)
3. Write first test (fails on soft language)
4. Harden policy (deterministic rules)
5. Test passes
6. Record in decision_record.json
7. Cite proof in BIBLIOTHEQUE_INTAKE.md

---

## If Gates Turn Red

### Indices Stale
```bash
python3 scratchpad/generate_claude_index.py
git add scratchpad/CLAUDE_MD_*.txt
git commit -m "docs: regenerate CLAUDE.md indices"
```

### Python Syntax Error
```bash
python3 -m py_compile <file.py>  # Find the exact error
# Fix and re-run: bash scripts/town-check.sh
```

### Evidence Failed
```bash
TOWN_EVIDENCE=1 bash scripts/town-check.sh  # See which breakthrough failed
python3 scripts/extract-emulation-evidence.py  # Debug details
# Check artifacts:
ls -la oracle_town/runs/runA_no_ship_missing_receipts/
cat oracle_town/runs/runA_no_ship_missing_receipts/decision_record.json
```

---

## Key Files Reference

| File | Purpose | Size |
|------|---------|------|
| `AUTONOMOUS_MODE_ACTIVATED.md` | Full system state | 282 lines |
| `SCENARIO_NEW_DISTRICT.md` | Month 1 walkthrough | 366 lines |
| `MONTH_1_OBSERVATION_LOG.md` | Metrics template | 373 lines |
| `oracle_town/memory/BIBLIOTHEQUE_INTAKE.md` | Knowledge base protocol | 320+ lines |
| `ORACLE_TOWN_EMULATION_EVIDENCE.md` | 5 breakthroughs | 359 lines |
| `EVIDENCE_SYSTEM_README.md` | Why drift matters | 215 lines |

---

## Status Right Now

✅ **All gates GREEN**
✅ **All 5 breakthroughs validated**
✅ **Knowledge base live**
✅ **Ready to iterate**

**Next:** Submit knowledge or follow SCENARIO_NEW_DISTRICT.md

