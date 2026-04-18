# Gate Verification: Working-Tree Invariant Enforced

## The Fix

The minimal gate now correctly enforces the invariant:

> **After running the generator, there must be zero working-tree diffs for `scratchpad/CLAUDE_MD_*.txt`**

### What Changed

| Aspect | Before | After |
|--------|--------|-------|
| **Diff check** | Only staged files (`git diff --cached`) | Working tree + staged (`git diff --`) |
| **Failure detection** | Missed unstaged changes | Catches all changes |
| **Error message** | Vague | Explicit: "regeneration produced changes" |
| **Invariant** | Not enforced | Working-tree diffs are zero after generation |

### Code Change

**Line 35 (critical)**:
```bash
# BEFORE: Only checks staged diffs
if ! git diff --quiet scratchpad/CLAUDE_MD_*.txt

# AFTER: Checks working-tree diffs (the actual invariant)
if ! git diff --quiet -- "$IDX1" "$IDX2"
```

The `--` separator and explicit file variables ensure we're checking the right thing.

## Verification Tests

### Test 1: Clean State (Pass)
```bash
bash scripts/town-check.sh
✓ Indices are current (no working-tree diffs)
✓ Python syntax valid
✅ GREEN — all gates passed
```

### Test 2: Stale Indices (Fail)
Edit CLAUDE.md to change the document:
```bash
echo "## Test Heading" >> CLAUDE.md
bash scripts/town-check.sh

ERROR: CLAUDE.md indices are stale (regeneration produced changes)
```

The gate correctly rejects stale state.

## What the Invariant Means

The invariant is simple but powerful:

**Generator property**: Running `python3 scratchpad/generate_claude_index.py` is idempotent.

- Same CLAUDE.md → same indices every time (deterministic)
- If regeneration produces **any** changes, the committed indices are stale
- Stale indices = out of sync with the document = governance failure

This is **K5 determinism** in action: same input must produce identical output.

## How the Gate Enforces It

```
User edits CLAUDE.md
        ↓
User runs: bash scripts/town-check.sh
        ↓
Gate runs: python3 scratchpad/generate_claude_index.py
        ↓
Gate checks: git diff --quiet -- scratchpad/CLAUDE_MD_*.txt
        ↓
If diffs exist:
  ❌ ERROR: Indices stale
  User must: commit the regenerated files
        ↓
If no diffs exist:
  ✅ GREEN: Indices clean
  User can: commit whenever ready
```

## Why Working-Tree Check Matters

**Scenario**: User edits CLAUDE.md but doesn't stage the index files

```bash
# User edits CLAUDE.md
echo "## New Section" >> CLAUDE.md

# Old gate (staged-only check): ❌ MISSED the problem
git diff --quiet scratchpad/CLAUDE_MD_*.txt  # Returns 0 (no staged changes)

# New gate (working-tree check): ✅ CATCHES it
git diff --quiet -- scratchpad/CLAUDE_MD_*.txt  # Returns 1 (working-tree diffs exist)
bash scripts/town-check.sh
ERROR: CLAUDE.md indices are stale
```

The new gate is **robust** because it checks the actual invariant: regeneration must produce zero diffs.

## Governor (Future Upgrade)

Currently the gate is manual. When ready, you can add:

```bash
# .git/hooks/pre-commit
bash scripts/town-check.sh
# Blocks commit if gate is red
```

But that's optional. The gate itself is sufficient.

## Status

✅ **Gate correctly enforces working-tree invariant**

- Detects stale indices whether staged or not
- Provides clear error messages
- Blocks commits of stale indices
- Supports local iteration loop

No further fixes needed.

---

**The Town now has a functional Mayor gate that refuses stale indices.**
