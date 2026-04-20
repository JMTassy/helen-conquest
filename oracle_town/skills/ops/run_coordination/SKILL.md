---
name: ops/run_coordination
description: Non-sovereign coordination protocol for multi-agent / multi-machine runs. Shared mission at run root, separate worker lanes per agent-machine pair, single synthesis surface. Prevents narrative overwrite and fragmentation when multiple workers commit to the same repo.
helen_faculty: OPS
helen_status: DOCTRINE (calibrated 2026-04-20; not yet INVARIANT)
helen_prerequisite: NO RECEIPT = NO CLAIM invariant; canonical SOT discipline from ~/.claude/CLAUDE.md
---

# Run Coordination — Worker Lanes Protocol

**Class**: Non-sovereign coordination artifact layout. No kernel authority. No ledger writes without `helen_say.py`.

**Scope**: When more than one agent (Claude Code, Codex, operator-by-hand, an Agent subagent) contributes to a single mission that spans multiple machines, this skill defines the on-disk layout that keeps provenance clean and prevents narrative collision.

---

## 1. Governing principle

```
shared mission  → run root
separate hands  → worker lanes
single synthesis → final.md at run root
```

The enemy is **silent overwrite** — two workers editing the same file in the same repo with overlapping narratives, producing a state where no one can reconstruct who wrote what or why. Worker lanes solve this by giving each agent-machine pair its own directory to write into, and reserving the run root for shared mission artifacts and the operator's synthesis.

---

## 2. Canonical directory layout

```
ops/runs/<run-id>/
  brief.md              ← mission statement; what this run aims to do
  tasks.md              ← task list with done/deferred status
  decisions.md          ← decisions made during the run, with rationale
  final.md              ← operator-written synthesis; filled at run close
  workers/
    <agent>_<machine>/
      output.md         ← that worker's narrative log
      (optional additional files: claims.md, patches.md, research.md, critique.md)
```

**Run-id format**: `YYYY-MM-DD-<kebab-theme>`. Example: `2026-04-20-stabilize-helen-runtime`.

**Worker lane name**: `<agent>_<machine>`. Examples: `claude_macbook`, `codex_imac`, `operator_laptop`. Lowercase, underscore separator.

---

## 3. File roles and ownership

| File | Who writes | Who reads | Purpose |
|---|---|---|---|
| `brief.md` | Operator (or lead worker on agreement) | All workers | Mission scope, non-goals, constraints |
| `tasks.md` | Any worker (append-only; check off own items) | All | Task list with status markers |
| `decisions.md` | Worker that made the decision | All | Decision + rationale + timestamp |
| `final.md` | Operator at run close | All | Synthesis, what shipped, what deferred |
| `workers/<lane>/output.md` | **Only the owning worker** | All (read-only for non-owners) | Chronological narrative of that worker's actions |

**Hard rule**: no worker writes inside another worker's lane. Synthesis happens at run root, not cross-lane.

---

## 4. Worker isolation rules

- Each worker writes only inside `workers/<own-lane>/`.
- A worker may **read** all other lanes but may not edit.
- If a worker needs to push a decision into the shared record, it goes in `decisions.md` at run root — not into another worker's output.
- If two workers need to coordinate a patch, they do it via `tasks.md` + `decisions.md`, not by editing each other's output files.
- Shared files (`brief.md`, `tasks.md`, `decisions.md`, `final.md`) use chronological append-only discipline: new content goes at the end, old content is not rewritten.

---

## 5. When to create a run directory

A run directory is opened when:

- A session spans **more than one machine** (e.g., laptop + iMac)
- A session spans **more than one agent** (e.g., Claude Code + Codex + operator)
- A session produces **more than ~3 commits** and mixed artifact types (code + docs + local-only)
- The operator anticipates needing to reconstruct *who did what* later

Short single-agent sessions on a single machine don't need a run directory. Use git history and PR descriptions instead.

---

## 6. Retrofit policy

If a session is already underway when this protocol is adopted, retrofit is allowed and encouraged:

- Create the run directory at the current state of affairs
- Write `workers/<lane>/output.md` from memory / transcript, in chronological order
- Timestamp each entry so retroactive reconstruction is honest
- Mark retrofitted entries with a prefix like `[retrofit]` or a header note at the top of the file
- Commit the retrofit in a single atomic commit so the repo shows one clean adoption point

Do NOT retroactively rewrite **decisions** — decisions are what they were at the time. If a decision later proved wrong, add a new entry to `decisions.md` noting the reversal; don't edit the original.

---

## 7. Proper promotion path (run → doctrine)

When a run closes and a pattern emerges worth keeping, the promotion path is:

1. Operator writes `final.md` synthesizing the run
2. If a pattern from `decisions.md` deserves to become doctrine, it gets lifted into a proper skill doc (e.g., `oracle_town/skills/...`)
3. The skill doc is committed separately (not inside `ops/runs/`)
4. `final.md` links to the new skill doc
5. `helen_say.py` receipt + K2 validation gates promotion to INVARIANT

Runs are NOT doctrine. They are the raw coordination substrate. Doctrine lives in skills.

---

## 8. Interaction with canonical SOT rules

- All writes under `ops/runs/**` are non-sovereign. Firewalled paths (`oracle_town/kernel/**`, `helen_os/governance/**`, `helen_os/schemas/**`, `town/ledger_v1*.ndjson`, `mayor_*.json`, `GOVERNANCE/**`) must not be touched from within worker output files.
- Run artifacts are tracked in git. They become part of the permanent history.
- Per `NO RECEIPT = NO CLAIM`: worker output files carry zero constitutional weight on their own. They are high-fidelity candidates for later receipted claims, not claims themselves.

---

## 9. Source code is NEVER split by machine

**Critical rule**: machine-named directories exist only under `ops/runs/*/workers/`. Do not duplicate source code under `claude_macbook/` or `codex_imac/` at the repo root. The whole point of today's consolidation was one SOT — don't unpick it by creating parallel code trees.

If a worker needs an isolated sandbox for experimental code, use `/tmp/helen_temple/` (non-sovereign working dir, already established by the helen-director skill) or a git branch — not a machine-named subdirectory in the repo.

---

## 10. Admission status

**DOCTRINE** — calibrated 2026-04-20 from the first run using this structure (`2026-04-20-stabilize-helen-runtime`). Not yet INVARIANT.

Promotion to INVARIANT requires:
- Second independent run uses this layout end-to-end and produces a clean audit trail
- `helen_say.py` receipt binding this document's SHA256 to the ledger
- K2 / Rule 3: the session that promotes must not be the session that authored

Until then: cite as "current working coordination doctrine from 2026-04-20."
