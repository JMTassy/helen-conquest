# Decisions — 2026-04-20-stabilize-helen-runtime

Chronological. Each decision carries: what, why, who proposed, who validated, timestamp.

---

## D1 — Choose Option A (consolidate onto SOT) over B (admit `~/.helen/` as production) and C (hybrid)

**Timestamp**: 2026-04-20, early session
**Proposed by**: operator
**Validated by**: operator (solo; HELEN canon applied from `~/.claude/CLAUDE.md`)
**Context**: Delta audit surfaced five trees in play (SOT + `~/.helen/` + three active worktrees + 21 dormant worktrees). Three paths forward proposed: consolidate onto SOT (A), admit the drift (B), hybrid (C).
**Decision**: A.
**Rationale**: "HELEN's own law is: one authority path, one canonical reducer path, one receipted system state. Your deployment should mirror that." Operational convenience (B) or ambiguity (C) both violate the canon that drove the rename session in the first place.

---

## D2 — Rename GitHub repo `HELEN_OS` → `helen-conquest` via `gh repo rename` (in-place, preserves history + redirects)

**Timestamp**: 2026-04-20, mid-session
**Proposed by**: operator (initially suggested lowercase rename)
**Validated by**: operator after conflict-flagged by worker
**Context**: Operator proposed renaming to match new scope (OS + CONQUEST + civilization layer, not just kernel). Worker flagged three conflicts: (a) global CLAUDE.md says `HELEN_OS` is canonical, (b) preflight hook validates that, (c) second repo would create new fragmentation. Operator chose in-place GitHub rename (Option A from three alternatives) to preserve single history.
**Decision**: Rename in place. Local `origin` updated, global CLAUDE.md + preflight hook update deferred.
**Rationale**: Keeps one repo, one history, one identity. GitHub's automatic redirect covers the old URL.

---

## D3 — Accept preflight `[DRIFT]` signal as noise until separate policy update

**Timestamp**: 2026-04-20, mid-session
**Proposed by**: operator (chose option "c" — skip policy update, continue with iMac clone)
**Validated by**: operator
**Context**: After the GitHub rename + local `origin` update, preflight started reporting `[DRIFT (got https://github.com/JMTassy/helen-conquest.git)]` because the hook still expects `HELEN_OS.git`. Three options: (a) propose global CLAUDE.md diff now, (b) find and update the preflight hook first, (c) skip and accept noise.
**Decision**: (c). Noise accepted; fix in a separate session.
**Rationale**: Consolidation momentum trumps cosmetic hook alignment. Signal is informational, not blocking.

---

## D4 — Add `jsonschema` to `requirements.txt` (real gap discovered via clean iMac install)

**Timestamp**: 2026-04-20
**Proposed by**: `claude_macbook` (surfaced via iMac Stage 5b pytest failure)
**Validated by**: operator
**Context**: Clean iMac clone + venv install hit `ModuleNotFoundError: No module named 'jsonschema'` during pytest collection. Laptop works because `jsonschema` is installed somewhere else (not declared). `requirements.txt` was incomplete.
**Decision**: Add `jsonschema>=4.26.0` to `requirements.txt`, commit + push.
**Rationale**: Clean install = source of truth for dependencies. Fix at the root, don't patch per-machine.

---

## D5 — Ship voice transcript ingestion as SOT skill + Claude Code memory pointer (option c of the three proposed)

**Timestamp**: 2026-04-20, post-rename
**Proposed by**: operator (chose "3")
**Validated by**: operator
**Context**: Operator pasted a policy for non-sovereign intake of voice/STT content. Worker proposed three homes: (1) skill in SOT only, (2) Claude Code memory only, (3) both.
**Decision**: (3). Skill at `oracle_town/skills/memory/voice_transcript_ingestion/SKILL.md` (authoritative) + `feedback_voice_transcript_ingestion.md` memory (pointer).
**Rationale**: SOT makes the protocol durable across sessions; memory makes it auto-apply in Claude Code.

---

## D6 — Ship tiered signing discipline as SKILL.md §14 amendment + memory pointer

**Timestamp**: 2026-04-20, post-render-plan
**Proposed by**: operator
**Validated by**: operator
**Context**: Operator defined a three-tier signing rule (TikTok silent / partner end-card / festival minimal title). Worker proposed three homes: (a) amend helen-director SKILL.md §14, (b) sibling file, (c) both plus memory.
**Decision**: (c). Amended SKILL.md + `feedback_helen_signing_tiers.md` memory.
**Rationale**: Same pattern as D5. Skill unified, memory is the pointer.

---

## D7 — Remove hardcoded `HELEN_TELEGRAM_TOKEN` from `.zshrc`; `TELEGRAM_BOT_TOKEN` in `~/.helen_env` is canonical

**Timestamp**: 2026-04-20
**Proposed by**: `claude_macbook` (found duplicate while editing .zshrc)
**Validated by**: operator
**Context**: `.zshrc` is mode 644 (world-readable). Token was duplicated in `~/.helen_env` (mode 600) under canonical name `TELEGRAM_BOT_TOKEN`. Two different var names caused ambiguity.
**Decision**: Remove the `.zshrc` line. Verified no code reads `HELEN_TELEGRAM_TOKEN` anywhere (grep-confirmed dead variable).
**Rationale**: Secrets belong in mode-600 files. Duplicate exposure for no benefit.

---

## D8 — Reduce `reference_api_keys.md` memory to pointer-only (no plaintext key values)

**Timestamp**: 2026-04-20
**Proposed by**: operator
**Validated by**: operator
**Context**: Memory file contained plaintext key values duplicating `~/.helen_env`. Operator rule: memory is a pointer, not a second secret store.
**Decision**: Rewrite memory to describe each key's env var and source (`~/.helen_env`), removing all plaintext values.
**Rationale**: Single canonical store (`~/.helen_env` mode 600). Memory tells Claude Code where to look, not what the value is.

---

## D9 — Defer `.zshenv` hygiene pass; do not bundle into §14 signing commit

**Timestamp**: 2026-04-20, late session
**Proposed by**: operator
**Validated by**: operator
**Context**: While fixing `.zshrc`, worker noticed `.zshenv` has stale `sk-....` placeholder OPENAI_API_KEY exports + a `typeset +x` line whose effect is overridden by subsequent `.helen_env` sourcing. Could have bundled into the signing commit; operator declined.
**Decision**: Defer to separate hygiene pass.
**Rationale**: Mixing shell/env surgery into a signing commit muddies the diff. Clean commits, one topic each.

---

## D10 — Adopt run coordination protocol (this skill) + retrofit today's session as `2026-04-20-stabilize-helen-runtime`

**Timestamp**: 2026-04-20, session close
**Proposed by**: operator
**Validated by**: operator (with HELEN canon applied by worker since kernel daemon not running)
**Context**: Operator proposed worker-lane structure (`codex_imac/`, `claude_macbook/`) for clarity. Worker surfaced four sub-decisions: tracked vs gitignored, run-id format, retrofit vs forward, codify as skill.
**Decision**: Tracked. Run-id = `2026-04-20-stabilize-helen-runtime`. Retrofit. Codify as SKILL.md.
**Rationale**: NO RECEIPT = NO CLAIM requires coordination artifacts in the receipted history. Retrofit captures real events (including the Higgsfield probe incident) rather than erasing them. Skill pattern matches D5 and D6.
