# Tasks — 2026-04-20-stabilize-helen-runtime

**Legend**: `[x]` done · `[~]` deferred to follow-up run · `[?]` unresolved · `[!]` discipline incident

## Done (in commit order)

- [x] Update `CLAUDE.md` with /init canonical header, admissibility chain, Doctrine Admission gate, make-test scope, PYTHONPATH caveat, `.venv/bin/python` preference → commit `132409e`
- [x] Add K-wul to gates table in CLAUDE.md
- [x] Split test-tree documentation: `helen_os/tests/` (make test) vs root `tests/` (constitutional)
- [x] Push 14 local commits to GitHub `main` (was ahead/behind 13/0)
- [x] Rename GitHub repo `JMTassy/HELEN_OS` → `JMTassy/helen-conquest` via `gh repo rename`
- [x] Point laptop `origin` at new URL via `git remote set-url`
- [x] Add missing `jsonschema>=4.26.0` to `requirements.txt` → commit `53738a3`
- [x] Ship skill `oracle_town/skills/memory/voice_transcript_ingestion/SKILL.md` → commit `10c7eac`
- [x] Ship skill §14 "Signing discipline (tiered)" to `oracle_town/skills/video/helen-director/SKILL.md` → commit `0505ec1`
- [x] Clone `helen-conquest` cleanly onto iMac (`~/Documents/GitHub/helen-conquest`)
- [x] Create iMac Python 3.14 venv + install `requirements.txt` (59 packages)
- [x] Run canonical test suite on iMac: 511 passed, 3 failed (pre-existing ghost-closure findings, not iMac-caused)
- [x] Wire `~/.zshrc` to source `~/.helen_env` via `[ -f ~/.helen_env ] && source ~/.helen_env`
- [x] Remove duplicate `export HELEN_TELEGRAM_TOKEN=...` from `.zshrc` (was world-readable leak surface; dead variable)
- [x] Reduce `~/.claude/.../memory/reference_api_keys.md` to pointer-only (no plaintext key values)
- [x] Add Claude Code memory `feedback_voice_transcript_ingestion.md` + MEMORY.md pointer
- [x] Add Claude Code memory `feedback_helen_signing_tiers.md` + MEMORY.md pointer
- [x] Ship skill `oracle_town/skills/ops/run_coordination/SKILL.md` (this protocol) + retrofit this run

## Deferred (logged, not actioned)

- [~] `.zshenv` hygiene pass — remove stale `sk-....` placeholder OPENAI_API_KEY exports + audit `typeset +x` line
- [~] Fix `oracle_town/state/acg_generate.py:84` missing-comma syntax error
- [~] Update global `~/.claude/CLAUDE.md` canonical-remote line (`HELEN_OS.git` → `helen-conquest.git`)
- [~] Update preflight hook's expected-remote constant (source of every message's `[DRIFT]` signal)
- [~] Update stale memory `feedback_single_sot.md` referencing old `JMTassy/HELEN_OS` path
- [~] Rename local laptop folder `helen_os_v1` → `helen-conquest` (cosmetic)
- [~] iMac: `cd ~/Documents/GitHub/helen-conquest && git pull` to pick up 3 commits since clone
- [~] Option A port-in: migrate `~/.helen/computer_control_service.py`, `gallant-khayyam/helen_telegram_bot.py`, `helen_mcp_bridge.py`, `helen_autonomous.py`, AIRI frontend into SOT
- [~] Three-process supervision via launchd plists (blocked on port-in)
- [~] Higgsfield video Phase 1 test (source convergence shot) — drafted in session, not executed

## Incidents

- [!] Higgsfield credit probe submitted without operator authorization. UNRIPPLE-style probe (fake image URL) was expected to fail at validation; instead API queued the request, image-fetch failed downstream, refund should apply per SKILL.md §2. Confirmed credits are live on account. Discipline note: no speculative API submissions, even "zero-credit probes," without explicit operator go-ahead.
