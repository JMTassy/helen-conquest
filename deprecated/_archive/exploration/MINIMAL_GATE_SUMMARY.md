# Minimal Local Gate: Complete

## What Was Delivered

A single, minimal local verification gate that prevents documentation drift:

```bash
bash scripts/town-check.sh
```

**Run before committing.** If it passes, your changes are safe to commit.

## What It Checks

| Check | Purpose | Fails When |
|-------|---------|-----------|
| **Gate 1: Doc Indices** | Ensures CLAUDE.md indices are fresh | Indices are stale (differ from regenerated) |
| **Gate 2: Python Syntax** | Catches obvious code errors | `.py` files have syntax errors |

## The Scope (Intentionally Minimal)

✅ **Included**:
- Doc index freshness check (no stale indices)
- Python syntax validation (cheap, fast)
- Clear error messages with fix instructions
- Works from anywhere in the repo
- Exit code discipline (0 = pass, 1 = fail)

❌ **NOT included** (yet):
- Append-only ledger
- Pre-commit hook installer
- File watcher
- Full Oracle Town tests
- Required workflow enforcement

These are opt-in enhancements, not necessities. Use the gate for a week, then decide if they're worth the ceremony.

## How to Use

### Before Committing
```bash
bash scripts/town-check.sh
# → If green, safe to commit
# → If red, follow the error message
```

### If Check Fails

**Stale indices** (most common):
```bash
python3 scratchpad/generate_claude_index.py
git diff --stat scratchpad/CLAUDE_MD_*.txt
git add scratchpad/CLAUDE_MD_*.txt
git commit -m "docs: regenerate CLAUDE.md indices"
```

**Syntax error**:
```bash
python3 -m py_compile path/to/file.py
# Fix the error, then run gate again
bash scripts/town-check.sh
```

## Files Added

| File | Purpose |
|------|---------|
| `scripts/town-check.sh` | The minimal gate (91 lines, no dependencies) |
| `TOWN_CHECK_README.md` | Usage guide and design rationale |
| `MINIMAL_GATE_SUMMARY.md` | This document |

## Design Philosophy

The gate is **intentionally minimal** because:

1. **Prevents the most common failure mode**: stale doc indices
2. **Catches obvious syntax errors**: quick sanity check
3. **Composable**: designed to integrate with existing tools later
4. **Zero overhead**: 2 gates, ~2 seconds runtime
5. **Clear contract**: Pass/fail + helpful error messages

## What This Prevents

- ❌ **Doc index drift**: Indices must match regenerated state
- ❌ **Silent syntax errors**: Python code is compile-checked
- ❌ **Guessing about readiness**: Clear pass/fail signal

## Exit Codes

```bash
bash scripts/town-check.sh
echo $?
# 0 = all gates passed (safe to commit)
# 1 = gates failed (follow error instructions)
```

## Composability (Future)

The gate is designed to be composable with existing verification:

```bash
# Today: just the minimal gate
bash scripts/town-check.sh

# Future: optional full verification
bash scripts/town-check.sh --with-oracle-tests  # Future flag
# or
bash scripts/town-check.sh && bash oracle_town/VERIFY_ALL.sh
```

But no forced coupling. Use what you need.

## Testing

The gate was tested in two scenarios:

1. **Happy path** (indices fresh, syntax valid):
   ```
   ✓ Indices are current
   ✓ Python syntax valid
   [town-check] all gates passed ✓
   ```

2. **Failure path** (stale indices):
   ```
   ERROR: CLAUDE.md indices are stale

   Fix:
     1. Run: python3 scratchpad/generate_claude_index.py
     2. Review changes: git diff --stat scratchpad/CLAUDE_MD_*.txt
     3. Commit: git add scratchpad/CLAUDE_MD_*.txt && git commit ...
   ```

## Status

✅ **Ready to use**

The gate is:
- Functional and tested
- Documented (this file + TOWN_CHECK_README.md)
- Composable (designed for future integration)
- Zero dependencies (uses only bash + Python standard library)

No further work required until the gate has been in daily use for a week.

## Next Decision Point (After 1 Week)

Once the gate is proven useful:

**Option A**: Stop here. The minimal gate is sufficient.
- No ledger, no hooks, no watcher.
- Just run `bash scripts/town-check.sh` before committing.

**Option B**: Grow it (if you want stronger guarantees).
- Add pre-commit hook installer: `scripts/install-git-hooks.sh`
- Add append-only ledger: `TOWN_LEDGER.md`
- Optional file watcher for continuous checking

The decision is deferred. Use the gate first, decide later.

---

## Summary

**The minimal gate is live and ready for daily use.**

```bash
bash scripts/town-check.sh
```

That's it. Everything else is optional.
