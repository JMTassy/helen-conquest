# Local Verification Gate: scripts/town-check.sh

## Purpose

Minimal, composable local gate that prevents documentation drift and catches obvious syntax errors.

**One command** to verify doc indices are fresh before committing:

```bash
bash scripts/town-check.sh
```

## What It Does

### Gate 1: Doc Indices Are Current
- Regenerates `scratchpad/CLAUDE_MD_*.txt` via the generator
- Fails if regenerated indices differ from committed ones
- Prevents stale indices from reaching git history

### Gate 2: Python Syntax Is Valid
- Runs `python3 -m py_compile` on all project Python files
- Catches obvious syntax errors early

## Usage

### Check Before Committing
```bash
# Edit CLAUDE.md or any Python code
bash scripts/town-check.sh

# If it passes, safe to commit:
git add your-changes
git commit -m "..."
```

### If Check Fails

**Stale indices error**:
```
ERROR: CLAUDE.md indices are stale

Fix:
  1. Run: python3 scratchpad/generate_claude_index.py
  2. Review changes: git diff --stat scratchpad/CLAUDE_MD_*.txt
  3. Commit: git add scratchpad/CLAUDE_MD_*.txt && git commit -m 'docs: regenerate CLAUDE.md indices'
```

**Python syntax error**:
```
ERROR: Python syntax error detected
Run: python3 -m py_compile <file.py> for details
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All gates passed |
| 1 | Indices stale or syntax error |

## Optional: Run Full Tests

For more comprehensive verification, run:

```bash
# Oracle Town governance hardening tests (13 unit tests + 3 adversarial runs)
bash oracle_town/VERIFY_ALL.sh

# Or CI checks (includes determinism verification)
python3 ci_run_checks.py
```

## Design Notes

- **Minimal**: Only checks what's essential (doc drift + syntax)
- **Composable**: Designed to integrate with `oracle_town/VERIFY_ALL.sh` later via flags (not coupled on day 1)
- **Local-first**: Runs entirely on your machine, no CI required
- **Cheap**: Should complete in <2s on most machines

## Future Enhancements

After this gate has been in daily use for a week:

- Optional pre-commit hook installer (`scripts/install-git-hooks.sh`)
- Append-only iteration ledger (`TOWN_LEDGER.md`)
- File watcher for continuous verification
- Integration with `oracle_town/VERIFY_ALL.sh` behind an opt-in flag

But those are opt-ins, not requirements. The gate itself is sufficient.
