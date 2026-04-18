# ORACLE SUPERTEAM — Getting Started Guide

## 🚀 Quick Start (3 Minutes)

### 1. Test the System
```bash
cd oracle-superteam
python3 -m ci.run_test_vault
```

**Expected output:** ✅ ALL TEST VAULT SCENARIOS PASSED (10/10)

---

### 2. Try the Interactive Emulator
```bash
python3 emulator.py --demo
```

**What you'll see:**
- ✅ Successful approval (SHIP)
- ⚠️  Quarantine (obligations blocking)
- 🛑 Kill-switch activation (NO_SHIP)

---

### 3. Submit Your Own Claim
```bash
python3 emulator.py
```

Then select option 1 (Quick Claim Submission).

---

## 📚 What's Available

### 1. **Core Engine** (Production-Ready)
```
oracle/
├── config.py           # Team weights, thresholds
├── canonical.py        # Deterministic hashing
├── contradictions.py   # Evidence conflict detection
├── obligations.py      # Obligation mapping
├── qi_int_v2.py       # Complex amplitude scoring
├── adjudication.py    # Lexicographic veto
├── verdict.py         # Binary verdict gate
├── engine.py          # Main pipeline
├── replay.py          # Determinism verification
└── logger.py          # Error logging (NEW!)
```

### 2. **Hardened Model V1** (Signal-Based)
```
oracle/
├── schemas.py          # Signal/Obligation types (NEW!)
├── obligations_v2.py   # Non-sovereign mapping (NEW!)
└── verdict_v2.py       # Binary SHIP/NO_SHIP (NEW!)
```

### 3. **Testing & Validation**
```
test_vault/scenarios/   # 10 adversarial scenarios
ci/run_test_vault.py   # Automated testing
```

### 4. **Interactive Tools**
```
emulator.py            # Interactive testing environment (NEW!)
example_run.py         # Demo scenarios
```

### 5. **Documentation**
```
CONSTITUTION.md        # Immutable axioms
README.md             # Complete documentation
QUICKSTART.md         # Quick start guide
PROJECT_SUMMARY.md    # Build status
HARDENED_MODEL_V1_SUMMARY.md  # Hardening details (NEW!)
```

### 6. **Academic Paper** (Publication-Ready)
```
paper/
├── oracle_superteam.tex   # Full LaTeX document (NEW!)
├── references.bib         # Bibliography (NEW!)
├── compile.sh             # Easy compilation script (NEW!)
├── Makefile               # Build system (NEW!)
└── README.md              # Paper compilation guide (NEW!)
```

---

## 🛠 Tools You Can Use Now

### Error Logging

```python
from oracle.logger import get_logger

logger = get_logger()

# Basic logging
logger.info("Processing claim")
logger.error("Invalid signal", signal_type="UNKNOWN", team="Bad Team")

# Oracle-specific events
logger.log_claim_submitted(claim_id="c-001", tier="Tier I", domain=["legal"])
logger.log_kill_switch(team="Legal Office", claim_id="c-001", rationale="GDPR violation")
logger.log_verdict(claim_id="c-001", verdict="NO_SHIP", ship_permitted=False, reason_codes=["KILL_SWITCH"])
```

**Output files:**
- Console: Human-readable logs
- `oracle_audit.log`: JSON structured logs

---

### Interactive Emulator

**Demo mode (recommended first step):**
```bash
python3 emulator.py --demo
```

**Interactive menu:**
```bash
python3 emulator.py
```

Options:
1. Quick Claim Submission
2. Run Test Scenario (e.g., S-01)
3. Run Demo Scenarios
4. View History
5. Exit

**Command-line usage:**
```bash
# Run specific test scenario
python3 emulator.py --scenario S-01

# Quick test
python3 emulator.py --quick "Deploy AI feature"
```

---

### Compile Academic Paper

**Option 1: Simple script**
```bash
cd paper
./compile.sh
```

**Option 2: Makefile**
```bash
cd paper
make all      # Generate figures + compile PDF
make view     # Compile and open PDF
make clean    # Remove auxiliary files
```

**Requirements:**
- LaTeX (pdflatex, bibtex)
  - macOS: `brew install --cask mactex-no-gui`
  - Ubuntu: `sudo apt-get install texlive-full`
- Graphviz (optional, for figures)
  - macOS: `brew install graphviz`

---

## 📖 Learning Path

### Beginner (10 minutes)
1. ✅ Run test vault: `python3 -m ci.run_test_vault`
2. ✅ Try emulator demo: `python3 emulator.py --demo`
3. ✅ Read `CONSTITUTION.md`

### Intermediate (30 minutes)
4. ✅ Submit custom claim via emulator
5. ✅ Explore test scenarios: `test_vault/scenarios/`
6. ✅ Read `QUICKSTART.md`

### Advanced (1-2 hours)
7. ✅ Read `HARDENED_MODEL_V1_SUMMARY.md`
8. ✅ Compile academic paper: `cd paper && ./compile.sh`
9. ✅ Read `PROJECT_SUMMARY.md`
10. ✅ Explore code: `oracle/` modules

---

## 🎯 Key Concepts

### Signals (Not Votes!)

**Old (Vote Model):**
```python
{"vote": "APPROVE"}  # ❌ Direct decision authority
```

**New (Signal Model):**
```python
{
  "signal_type": "OBLIGATION_OPEN",      # ✅ Non-sovereign request
  "obligation_type": "METRICS_INSUFFICIENT",
  "rationale": "Need A/B test results"
}
```

**Available signal types:**
- `OBLIGATION_OPEN` — Request obligation be opened
- `RISK_FLAG` — Surface concern (non-blocking)
- `EVIDENCE_WEAK` — Insufficient evidence quality
- `KILL_REQUEST` — Request kill-switch (authorized teams only)

---

### Binary Verdicts

**At the integration gate, there are exactly two outputs:**

1. **SHIP** (ship_permitted = true)
2. **NO_SHIP** (ship_permitted = false)

Internal states (ACCEPT, QUARANTINE, KILL) are diagnostic only.

---

### Lexicographic Veto

**Priority chain (strict order):**
1. ⚠️ Kill-switch → NO_SHIP (immediate)
2. ⚠️ Rule-kill → NO_SHIP (high-severity contradiction)
3. ⚠️ Open obligations → NO_SHIP (blocking requirements)
4. ⚠️ Contradictions → NO_SHIP (evidence conflicts)
5. ✅ QI-INT ≥ 0.75 → SHIP
6. ⚠️ Else → NO_SHIP

---

## 🔧 Troubleshooting

### Test Vault Fails

**Issue:** `python3 -m ci.run_test_vault` fails

**Solution:**
```bash
# Ensure you're in the right directory
cd oracle-superteam

# Check Python version (needs 3.8+)
python3 --version

# Try running directly
python3 ci/run_test_vault.py
```

---

### Emulator Errors

**Issue:** `ModuleNotFoundError: No module named 'oracle'`

**Solution:**
```bash
# Make sure you're in oracle-superteam directory
cd oracle-superteam

# Run emulator
python3 emulator.py
```

---

### Paper Won't Compile

**Issue:** `pdflatex: command not found`

**Solution:**
Install LaTeX:
- macOS: `brew install --cask mactex-no-gui`
- Ubuntu: `sudo apt-get install texlive-full`
- Windows: Download from https://miktex.org/download

---

## 📊 System Status

| Component | Status | Location |
|-----------|--------|----------|
| Core Engine | ✅ Operational | `oracle/*.py` |
| Hardened Model V1 | ✅ Complete | `oracle/schemas.py`, `obligations_v2.py`, `verdict_v2.py` |
| Test Vault | ✅ 100% Pass | `test_vault/scenarios/` |
| Error Logging | ✅ Ready | `oracle/logger.py` |
| Interactive Emulator | ✅ Ready | `emulator.py` |
| Academic Paper | ✅ Ready | `paper/oracle_superteam.tex` |

---

## 🚧 What's Next

### Phase A: Integration (Remaining)
- [ ] Update adjudication.py for signal processing
- [ ] Update engine.py for hardened pipeline
- [ ] Convert test vault to signal model
- [ ] Run full validation

### Phase B: Extensions
- [ ] Web UI for claim submission
- [ ] Interactive city map visualization
- [ ] Receipt verification service
- [ ] Zero-knowledge proof integration

---

## 📞 Support

- **Issues:** Check `PROJECT_SUMMARY.md` for details
- **Questions:** Read `CONSTITUTION.md` for governance rules
- **Examples:** See `example_run.py` and emulator demos

---

## 🎓 Resources

### Read First
1. `CONSTITUTION.md` — System axioms
2. `QUICKSTART.md` — Quick start guide
3. `README.md` — Full documentation

### Deep Dive
4. `HARDENED_MODEL_V1_SUMMARY.md` — Signal model details
5. `PROJECT_SUMMARY.md` — Build status
6. `paper/oracle_superteam.tex` — Academic paper

### Code Examples
7. `example_run.py` — Basic usage
8. `emulator.py` — Interactive testing
9. `ci/run_test_vault.py` — Testing framework

---

**ORACLE SUPERTEAM is not a conversation. It is an institution.**

Built with determinism. Governed by evidence. Auditable by design. 🔒
