# Town Iteration: Local Governance Loop

## The Pattern

The Town iterates locally by refusing to proceed when the Mayor gate is red.

**Default iteration** (daily):
```bash
# 1. Edit (CLAUDE.md, code, etc.)
# 2. Run the Mayor gate
bash scripts/town-check.sh

# 3. If green → commit whenever you want
git add -A && git commit -m "..."
```

**Heavy iteration** (when touching governance / determinism):
```bash
bash oracle_town/VERIFY_ALL.sh
```

## The Gate: scripts/town-check.sh

**What it does**:
- ✅ Regenerates CLAUDE.md indices
- ✅ Verifies regeneration produces zero diffs (working-tree check)
- ✅ Checks Python syntax on tracked files

**Exit codes**:
- `0` = Gate passed (indices clean)
- `1` = Gate failed (indices stale or syntax error)

**Critical invariant**: After running the generator, there must be **zero diffs** in the working tree for these files:
- `scratchpad/CLAUDE_MD_LINE_INDEX.txt`
- `scratchpad/CLAUDE_MD_SECTIONS_BY_LENGTH.txt`

If there are diffs, indices are stale and the gate fails.

## When the Gate Fails

**Stale indices** (most common):
```bash
ERROR: CLAUDE.md indices are stale (regeneration produced changes)

Fix:
  1. Run: python3 scratchpad/generate_claude_index.py
  2. Review changes: git diff --stat -- scratchpad/CLAUDE_MD_*.txt
  3. Commit: git add scratchpad/CLAUDE_MD_*.txt && git commit -m '...'
```

**Python syntax error**:
```bash
ERROR: Python syntax error detected
Run: python3 -m py_compile <file.py> for details
```

## Shell Aliases (Optional)

Make iteration faster with local aliases:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias town='bash scripts/town-check.sh'
alias townfull='bash oracle_town/VERIFY_ALL.sh'
```

Then just:
```bash
town          # Quick gate
townfull      # Heavy verification
```

## Continuous Iteration (Optional)

If you have `watchexec` installed:

```bash
watchexec -e md,py,sh -- bash scripts/town-check.sh
```

Now the gate runs on every file save (Town is "alive").

## The Rule

> The Town commits only when the gate is green.

That's it. No ceremony, no ledger, no GitHub. Just:

1. Edit
2. Gate (green → commit)
3. Repeat

## When to Run VERIFY_ALL.sh

Run the heavy verification when you edit:
- Oracle Town core modules (`oracle_town/core/*`)
- Governance policies
- Determinism-critical code
- Cryptographic modules

Otherwise, `town-check.sh` is sufficient.

## Status

✅ Ready for daily use

- The gate is local-only (works offline)
- No CI required (decisions made on your machine)
- Composable with future tools (ledger, hooks, etc.)
- Deferrable (earn governance upgrades after proven use)

---

**Start here**: `bash scripts/town-check.sh`
