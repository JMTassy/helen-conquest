# CLAUDE.md Quick Reference — What Was Added

**TL;DR:** CLAUDE.md now includes practical development commands, project structure map, and test guidance (303 new lines) while keeping all 1,313 lines of conceptual content intact.

---

## New Sections Added to CLAUDE.md

### 1️⃣ Development Setup
**Location:** Near top of file (after Quick Navigation)
**Contents:**
- Environment activation: `source .venv/bin/activate`
- PYTHONPATH setup: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
- Dependency requirements
- Installation command: `pip install -e ".[dev]"`

### 2️⃣ Common Development Commands
**Location:** After Development Setup
**Contents:**
- CONQUEST simulation: `python3 conquest_v2_hexacycle.py [SEED]`
- Constitutional tests: `python3 run_constitutional_tests.py`
- Oracle CLI: `python3 oracle_cli.py`
- Superteam CLI: `python3 superteam_cli.py --team [NAME]`
- Pytest: `python3 -m pytest tests/ -v`
- All with examples and timing

### 3️⃣ Project Structure Map
**Location:** After Common Commands
**Contents:**
```
.
├── oracle_town/           # Governance kernel
├── ORACLEbot/            # LLM integration
├── tests/                # Test harness
├── kernel/               # Runtime state
├── artifacts/            # Outputs
├── Conquest Scripts      # Main simulations
├── CLI Tools             # Interactive tools
└── Documentation         # Reference docs
```
Plus detailed descriptions of each module's purpose.

### 4️⃣ Running Tests
**Location:** After Project Structure
**Contents:**
- **9 Constitutional Tests** (test_[1-9]_*.py) with K-gate mapping
- **4 Test Categories** (constitutional, regression, integration, rendering)
- **Quick Commands** with examples
- **Debugging Commands** (--pdb, -s, -vv, etc.)

### 5️⃣ Enhanced Quick Navigation
**Location:** Top of file
**Change:** Reordered to show Development sections first

---

## Quick Copy-Paste Commands

### Set Up Environment
```bash
cd /Users/jean-marietassy/Desktop/'JMT CONSULTING - Releve 24'
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Run Simulation
```bash
python3 conquest_v2_hexacycle.py 111
```

### Run All Tests
```bash
python3 -m pytest tests/ -v
```

### Run Constitutional Tests Only
```bash
python3 -m pytest tests/test_[1-9]_*.py -v
```

### Check Oracle Governance
```bash
python3 oracle_cli.py
```

### Coordinate Superteams
```bash
python3 superteam_cli.py --team production
```

---

## File Statistics

| Metric | Value |
|--------|-------|
| Lines Added | 303 |
| Lines Preserved | 1,313 |
| Total Lines | 1,616 |
| Sections Added | 5 |
| Commands Documented | 15+ |
| Test Categories | 4 |
| Directory Levels Mapped | 3 |

---

## What Didn't Change

✅ All 1,313 lines of existing content remain exactly as-is:
- Foundry Town framework (complete)
- Oracle Town reference (complete)
- Agent charters (complete)
- CONQUEST project (complete)
- META-VISION section (complete)
- ADHD working style (complete)
- Atomic intelligence model (complete)
- Anti-burnout measures (complete)

---

## For Future Claude Sessions

When you arrive at this repository:

1. **Read:** CLAUDE.md Quick Navigation section (top)
2. **Set up:** Follow Development Setup commands
3. **Pick a task:** Use Common Development Commands section
4. **Run it:** Example provided for each command
5. **Debug if needed:** Use Running Tests section commands

**Time to first success:** 5-10 minutes

---

## Git Commit Info

**Commit:** 09cea49
**Message:** "Enhance CLAUDE.md with practical development guidance"
**Files Changed:** CLAUDE.md (enhanced), CLAUDE_MD_IMPROVEMENTS_SUMMARY.md (created)
**Branch:** main
**Date:** February 15, 2026

---

## Related Documents

- **CLAUDE_MD_IMPROVEMENTS_SUMMARY.md** — Detailed before/after comparison
- **CLAUDE_MD_FINALIZATION_REPORT.md** — Full quality assurance report
- **CLAUDE.md** — The enhanced file itself

---

**Status: ✅ Complete and ready for production use**
