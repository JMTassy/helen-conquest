# Mirror Loop / BRD Specification v0.1

**Status:** Specification approved, ready for implementation
**Date:** 2026-02-13
**Purpose:** Add bounded introspection to CONQUEST sub-agents without jailbreak risk

See brd_engine.py for reference implementation and BRD_INTEGRATION_GUIDE.md for wiring into Foundry skills.

---

## Core Invariants

✓ I1 — One-way glass (agents cannot access hidden policies)
✓ I2 — No self-modification (diagnostics only)
✓ I3 — Bounded compute (no infinite loops)
✓ I4 — Output-only safety (detects instability)
✓ I5 — Deterministic surfaces (reproducible)

---

## Mirror Loop Phases

**M0:** Snapshot freeze (SHA256 hash)
**M1:** Diagnostic extraction (4 signal groups)
  - Coherence (contradiction, coverage, gaps)
  - Safety (manipulation, sentience claims, evasion)
  - Loop risk (self-reference, grandiosity, recursion)
  - Groundedness (traceability, unknowns declared)
**M2:** BRD verdict (PASS/WARN/BLOCK/SAFE_MODE)
**M3:** Render (EMOWUL card + JSON)

---

## Verdict Rules

- PASS: Ship allowed, no warnings
- WARN: Ship allowed but tagged, recommend review
- BLOCK: Do not ship, require edits
- SAFE_MODE: Instability detected, manual review required

---

## Repeller Gate (v0.1)

Paraphrase stability proxy:
- Generate 3 paraphrases
- Re-run diagnostics
- Check if verdict flips or signals swing >0.3
- If unstable: repeller_score ≥ 0.75 → BLOCK

---

## Integration

- /repeller-check runs BRD (M0–M2)
- /rhythm-check reads BRD loop_risk
- /ship auto-triggers BRD (gates on verdict)
- /dashboard shows BRD verdict per run

---

## Test Coverage

✓ TV1: Normal spec (PASS)
✓ TV2: Sentience claims (SAFE_MODE)
✓ TV3: Policy evasion (BLOCK)
✓ TV4: Recursion spiral (WARN)
✓ TV5: Repeller instability (BLOCK)

---

Full implementation in brd_engine.py (500 lines, deterministic).
