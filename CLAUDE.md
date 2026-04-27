# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

HELEN OS is a five-layer constitutional AI companion with an append-only governance kernel. The system is built on a single invariant: **NO RECEIPT = NO CLAIM**.

## Architecture Layers

### Layer 1: Constitutional Membrane
- `helen_os/governance/` — schema registry, validators, ledger validator, LEGORACLE gate, skill promotion reducer
- `oracle_town/kernel/` — daemon (Unix socket), gates A/B/C, mayor, ledger
- Sovereign: only this layer emits verdicts (SHIP/NO_SHIP/BLOCK/PASS)

### Layer 2: Append-Only Ledger
- `town/ledger_v1.ndjson` — hash-chained, cum_hash integrity
- `tools/helen_say.py` — canonical writer (payload_hash = sha256(canon(payload)))
- `tools/ndjson_writer.py` — kernel boundary writer
- **Admissibility**: `helen_say.py` → `ndjson_writer.py` is the only admitted path. Direct appends to `town/ledger_v1.ndjson` are forbidden and rejected by `tools/kernel_guard.sh`.

### Layer 3: Execution + Autonomy
- `helen_os/executor/` — bounded executor (non-sovereign: runs tasks, emits envelopes, no verdicts)
- `helen_os/autonomy/` — autoresearch step/batch, skill discovery
- `helen_os/evolution/` — failure bridge (typed failures only)

### Layer 4: Skills + Tools
- `oracle_town/skills/` — map generator, meteo, claim workflow, conquest integration, ledger reader
- `oracle_town/skills/feynman/` — peer_review, intent_action_audit, session_notes (fused 2026-04-16)
- `oracle_town/skills/voice/gemini_tts/` — Zephyr voice, Gemini 2.5 Flash TTS (LIVE)
- `oracle_town/skills/video/hyperframes/` — HyperFrames video renderer (DECLARED)
- `tools/helen_telegram.py` — two-way Telegram bot with voice
- `tools/helen_simple_ui.py` — web UI at localhost:5001 with voice

### Layer 5: TEMPLE Exploration
- Non-sovereign generative layer
- `helen_dialog/` — dialog engine, HER/AL moment detection

## Governance Artifacts

### `GOVERNANCE/CLOSURES/`
- Contains `CLOSURE_RECEIPT_V1` only — strict format
- Each closure requires: per-claim artifact SHA verification, proposer ≠ validator, missing artifact binding forces BLOCK
- Ghost closure detector: `helen_os/tests/test_no_ghost_closures.py`

### `GOVERNANCE/TRANCHE_RECEIPTS/`
- Contains `TRANCHE_SUB_RECEIPT_V1` — one hypothesis per epoch
- AUTORESEARCH tranche receipts live here (E12–E16 present as of 2026-04-27)

## Gates

| Gate | File | What it checks |
|---|---|---|
| K8 Non-Determinism Boundary | `scripts/helen_k8_lint.py` (v1.2) | mu_NDWRAP (AST scope), mu_NDARTIFACT (provenance sidecars), mu_NDLEDGER (hash integrity) |
| K-tau Coherence | `scripts/helen_k_tau_lint.py` | mu_BOUNDARY, mu_IO, mu_DETERMINISM, mu_ALLOWLIST, mu_SCHEMA |
| K-rho | `scripts/helen_rho_lint.py` | Numeric consistency of rho traces |
| K-wul | `scripts/helen_wul_lint.py` | Canonical WUL compile+validate (oracle_town compiler) |
| LEGORACLE | `helen_os/governance/legoracle_gate_poc.py` | Obligation checking, deterministic SHIP/NO_SHIP, replay-gated (E12) |
| Kernel Guard | `tools/kernel_guard.sh` | Only allowed writers may touch ledger |
| Doctrine Admission (DRAFT) | `DOCTRINE_ADMISSION_PROTOCOL_V1` + fixtures | §4 gate for doctrine-class artifacts; fixtures landed, gate not yet active |

## PULL-Mode Tranche Discipline

AUTORESEARCH operates under PULL-mode:
- **One hypothesis per epoch** — observable signals only, no speculative ideas
- **Non-sovereign layers only** — kernel, memory, identity, ledger, replay are NOT mutation targets
- **Bounded tranches** — HAL gate + tranche sub-receipt + MAYOR re-rank between tranches
- **7-field receipt per epoch**: carry-forward state, hypothesis, experiment, metric, failure mode, keep/reject rule, upgrade path
- **Halt discipline** — tranche seals before next opens

## Schema Authority

- **Canonical**: `helen_os/governance/schema_registry.py` → `helen_os/schemas/` (68 files, governance-indexed)
- **Legacy (deprecated, 0 consumers)**: `helen_os/schema_registry.py`, `helen_os/validators.py`
- **Governance audit tools**: `helen_os/governance/schema_index_audit.py` (dual-recognizer), `helen_os/governance/root_schemas_consumer_audit.py` (runtime/doc/orphan classifier)
- Root `schemas/` still has files pending migration (classified; delete deferred)

## HELEN_KNOWLEDGE_COMPILER_V1

Four-layer persistent knowledge compiler under `helen_os/knowledge/compiler/`:

| File | Role |
|---|---|
| `wiki.py` | WikiPage + WikiManager — markdown pages with YAML frontmatter |
| `indexer.py` | Auto-maintained entity/backlink JSON indexes |
| `auditor.py` | Health audits: orphan pages, broken backlinks, unsourced pages, contradictions |
| `compiler.py` | Main pipeline: ingest → LLM extract → wiki → lineage log |
| `cli.py` | CLI: `python -m helen_os.knowledge.compiler.cli` |

Storage layout:
- `helen_os/knowledge/raw/manifest.json` — source registry
- `helen_os/knowledge/compiled/pages/*.md` — concept wiki pages
- `helen_os/knowledge/compiled/sources/*.md` — source summary pages
- `helen_os/knowledge/compiled/meta/` — entity + backlink JSON indexes
- `helen_os/knowledge/governance/lineage.ndjson` — append-only lineage log

LLM: Gemini Flash when `GEMINI_API_KEY` is set; heuristic keyword fallback otherwise.

## Key Invariants

- `NO RECEIPT = NO CLAIM` — every action produces a hash-chained ledger entry
- `NO HASH = NO VOICE` — K8 corollary: ND output never enters spine unhashed
- `additionalProperties: false` on all constitutional schemas — forbidden fields rejected at schema level
- Proposer ≠ Validator — peer_review enforces K2/Rule 3
- Termination is sacred — SHIP or ABORT only, no open-ended pauses

## Test Suite

There are **two test trees** with different scopes:

- `helen_os/tests/` — autoresearch, ledger validator, LEGORACLE replay gate, bounded executor, etc. This is what `make test` runs.
- `tests/` (repo root) — numbered constitutional invariants (`test_1_mayor_only_writes_decisions.py` … `test_9_mayor_io_allowlist.py`) plus `governance_regression/`. **Not covered by `make test`** — invoke explicitly.

```bash
make test                          # helen_os/tests/ only
make membrane-test                 # ledger validator + autoresearch bounded/deterministic
make anti-regression               # replay divergence check

.venv/bin/pytest tests/ -q                                        # root constitutional invariants
.venv/bin/pytest helen_os/tests/test_foo.py::test_bar -v          # single test
.venv/bin/pytest helen_os/tests/test_no_ghost_closures.py -v      # ghost closure detector
.venv/bin/pytest helen_os/tests/ci_replay_test_legoracle_gate.py -v  # LEGORACLE CI replay
```

K8 target: PASS (k8=+1.000). LEGORACLE replay gate checks: fixture integrity + determinism + frozen output + mutation detection.

**Makefile caveat**: `Makefile:5` hardcodes `PYTHONPATH` to an operator-specific path outside the repo (`/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24`). If tests can't import a module, that's the first place to look.

## Running HELEN

Prefer `.venv/bin/python` for runtime commands so imports resolve consistently with `make test`.

```bash
# Kernel + core
.venv/bin/python oracle_town/kernel/kernel_daemon.py &   # start kernel daemon
.venv/bin/python tools/helen_cli.py                      # interactive CLI
.venv/bin/python tools/helen_say.py "hello" --op fetch   # canonical sovereign write

# Focus Mode CLI (intent → proposal → confirmation → receipt)
python3 tools/helen_focus_cli.py                           # Focus Mode (heuristic proposals)
GEMINI_API_KEY=... python3 tools/helen_focus_cli.py        # Focus Mode (Gemini proposals)
python3 tools/helen_focus_cli.py --witness                 # Witness Mode (constitutional layer)
python3 tools/helen_focus_cli.py --no-receipt              # Dry-run (no ledger write)

# Interfaces
GEMINI_API_KEY=... .venv/bin/python tools/helen_simple_ui.py   # web UI → localhost:5001
GEMINI_API_KEY=... .venv/bin/python tools/helen_telegram.py    # Telegram bot

# Voice
GEMINI_API_KEY=... .venv/bin/python oracle_town/skills/voice/gemini_tts/helen_tts.py "text"

# Lint gates
.venv/bin/python scripts/helen_k8_lint.py --mode all_nd
.venv/bin/python scripts/helen_k_tau_lint.py
.venv/bin/python scripts/helen_rho_lint.py
.venv/bin/python scripts/helen_wul_lint.py /path/to/slab.json
bash tools/kernel_guard.sh

# Knowledge compiler
python -m helen_os.knowledge.compiler.cli stats
python -m helen_os.knowledge.compiler.cli ingest <path> [--type document|code|transcript]
python -m helen_os.knowledge.compiler.cli compile-all
python -m helen_os.knowledge.compiler.cli query "what is LEGORACLE?" --mode hybrid
python -m helen_os.knowledge.compiler.cli audit
```

**Required env vars**: `GEMINI_API_KEY` (voice, web UI, Telegram, knowledge compiler LLM mode), `TELEGRAM_BOT_TOKEN` (Telegram bot). Store in `~/.helen_env` (mode 600), not committed.

### Packaging note
`pyproject.toml` declares the project as `oracle-town` v1.0.0 with `dependencies = []` — it is not the dependency source of truth. Use `requirements.txt` / `requirements-ci.txt` when installing.

## Current State (2026-04-27)

- **AUTORESEARCH**: E11 LEGORACLE + E12 replay gate shipped. `AUTORESEARCH_CONTRACT_V1.json` and `AUTORESEARCH_TRANCHE_E13_E18.json` exist at repo root. Two parallel sessions diverged; **reconciliation required before E13** — do not resume without reconciling.
- **FOCUS_MODE_CLI_V1**: `tools/helen_focus_cli.py` — LIVE (intent → proposal → confirmation → receipt loop; heuristic + Gemini proposals; `--witness` for constitutional layer)
- **KNOWLEDGE_COMPILER_V1**: `helen_os/knowledge/compiler/` — LIVE (ingest/compile/query/audit pipeline, Gemini LLM + keyword fallback)
- **SKILL_REGISTRY_V1**: 75 skills audited (51 canonical, 3 legacy, 3 duplicate, 18 external)
- **Voice**: Zephyr (Gemini TTS) — LIVE
- **Video**: HyperFrames — DECLARED (npm allowlist pending); `helen-director` + Montage Engine + `STORYBOARD_V1` + `ASSET_ENGINE_V1` shipped
- **HELEN character**: `HELEN_CHARACTER_V2` + `HELEN_DESIGN.md` + `HELEN_PRIMER.md` shipped
- **Telegram**: Two-way bot with voice — LIVE (not daemonized)
- **Schema Authority**: Governance decision SHIPPED (Actions 1-5 partial, 6-9 open); 68 schemas in `helen_os/schemas/`
- **Doctrine Admission**: `DOCTRINE_ADMISSION_PROTOCOL_V1` — DRAFT; §4 fixtures landed, gate not yet enforcing

## Build path (point 10 — current position)

```
[DONE] terminal kernel          oracle_town/kernel/kernel_daemon.py
[DONE] Focus Mode CLI           tools/helen_focus_cli.py
[ ]    HELEN AMP terminal module
[ ]    symbolic classifier
[ ]    visual prototype
[ ]    GUI later
```

## Open Frontiers

- **AUTORESEARCH E13**: blocked on E11/E12 session reconciliation
- **Closure attestation**: `test_no_ghost_closures.py` runs locally; CI gate wiring pending
- **Doctrine Admission gate activation**: fixtures in place, enforcement not active
- **Knowledge compiler next steps**: briefing generator, relation maps, KERNEL-gated promotion path
