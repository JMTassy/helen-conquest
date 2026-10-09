# EGREGOR DAILY

**Status:** NON_SOVEREIGN · authority=false · ledger_effect=none · experiment (built and tested with fixture lanes; not yet run on real lanes).

One SUPERTEAM cycle per day ([SUPERTEAM_MVP_V0](../../../oracle_town/skills/ops/helen_superteam/SUPERTEAM_MVP_V0.md)) across your lanes, on your own machine, with no paid API: local models through Ollama, Claude and Codex through your subscriptions.

```
inputs (HELEN repo activity · inbox folder · Gmail label)
  → GOBLIN  local model      DreamSeeds          sees raw inputs (raw text never leaves the machine at this step)
  → HER     local model      InsightCandidates   sees stripped DreamSeeds only
  → HAL     Claude (subscr.) ClaimCandidates     sees stripped InsightCandidates only
  → MAYOR   Codex  (subscr.) one verdict         sees stripped ClaimCandidates only, no lineage; other vendor than HAL
  → BRIEF.md + RECEIPT.json for JM               nothing admitted, no ledger touched
```

**What the script guarantees, not the models:** blindness (each lane gets only the previous stage's artifacts, stripped by the superteam functions); governance fields (ids, lineage, `source_refs`, `claim_status`, `authority=false`, `actor`) are set by the script and anything a model writes there is ignored; every artifact is validated against `schemas/helen_superteam/`; invalid lineage, bad enums and anything beyond the daily cadence (10 inputs, 20 seeds, 5 insights, 2 claims, 1 verdict) are dropped and recorded; MAYOR's `next_gate` follows its verdict. The receipt records, per call, the lane, the prompt hash, what the lane saw (ids), what was kept or rejected and why, durations, and what the CLI reported.

## Set up (once, on your PC)
1. **Ollama** running, models pulled (tags in the config; check with `ollama list`):
   `ollama pull qwen3.5:9b-ud-q4` (GOBLIN) and the newer local model for HER, e.g. `ollama pull gemma4:12b`.
2. **Claude Code** logged in with your subscription: run `claude`, then `/login`. **Codex CLI** logged in with your ChatGPT plan: `codex login`.
3. `pip install pyyaml jsonschema` (and `pypdf` to read PDFs from the inbox).
4. Copy `egregor.config.example.yaml` to `egregor.config.yaml` (gitignored) and set: your HELEN repo path, the inbox folder, the Gmail label, and the run time.
5. Gmail: label the e-mails you want the egregor to read (default label `egregor`). They are read through your Claude subscription's Gmail connector; check the tool names with `claude mcp list` and fix `allowed_tools` if they differ.
6. `python egregor_daily.py --check` → every line must say present / found / exists.
7. One manual run: `python egregor_daily.py`. Read `~/HELEN_EGREGOR/<date>/BRIEF.md` and `RECEIPT.json`.
8. Schedule it: `powershell -ExecutionPolicy Bypass -File install_windows_task.ps1 -Time 07:30`
   (macOS/Linux: `30 7 * * * cd <this folder> && python3 egregor_daily.py >> ~/HELEN_EGREGOR/logs/egregor.log 2>&1`).

## Where things go
`~/HELEN_EGREGOR/<date>/` (outside git: inputs include e-mails): `raw/`, `compost/`, `insights/`, `claims/`, `validation/`, `BRIEF.md`, `RECEIPT.json`. Processed inbox files move to `inbox/done/<date>/`. One run per day; a second run the same day refuses.

## Limits
- Lanes are on your machine: the run happens only when the PC is on and you are logged in (missed runs start at next logon).
- Content derived from e-mails reaches Anthropic (HAL, Gmail collector) and OpenAI (MAYOR) through your subscriptions. Raw e-mail text itself goes only to the local GOBLIN.
- The CLI flags (`claude -p`, `codex exec`) and the Gmail connector's tool names are configurable because they change between versions; verify them on the first manual run.
- MAYOR's YES means "ready for JM's admission review", never admitted.

## Tests
`.venv/bin/pytest experiments/helen_mvp_kernel/egregor_daily/tests -q` (fixture lanes, no model, no network).
