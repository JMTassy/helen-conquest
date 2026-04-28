# TEMPLE codex pilot — NON_SOVEREIGN

Local rehearsal of the **CLAUDE_HER → CLAUDE_HAL → CODEX EXECUTOR** bridge.

## Status

- Authority: `NON_SOVEREIGN_EXPLORATION`
- Layer: TEMPLE (Layer 5 per HELEN OS architecture)
- Promotable: **NO**. Outputs here are never auto-promoted to canon, never appended to `town/ledger_v1.ndjson`, never used as evidence for SHIP claims.
- Bridge model: `aura-gemma4:latest` via local Ollama (`http://localhost:11434`)

## Why local Gemma and not Claude

Cost discipline. Rehearsing the receipt/validation/packet flow over many iterations on metered Anthropic/OpenAI tokens for an unproven shape is wasteful. Local Gemma costs $0/run. The pilot tests **the bridge shape**, not the brain quality. When the shape proves out, swap `OLLAMA_MODEL` for a Claude or GPT-4 backend in production.

## What the pilot exercises

```
TASK string
    │
    ▼
┌─────────────┐
│ HER         │  Ollama aura-gemma4 returns Python code
│ (reasoning) │
└─────┬───────┘
      ▼
┌─────────────┐
│ HAL         │  syntax compile + forbidden-pattern firewall
│ (validate)  │  (ledger paths, sovereign paths, destructive ops)
└─────┬───────┘
      ▼ if VALIDATED
┌─────────────┐
│ CODEX EXEC  │  subprocess.run with timeout, captured stdout/stderr
└─────┬───────┘
      ▼
EXECUTION_RECEIPT_V1 sidecar in runs/
authority_status: NON_SOVEREIGN_EXECUTION
```

## Running

```bash
python3 temple/subsandbox/codex_pilot/claude_hal_codex.py "Print SHA256 of 'helen'"
python3 temple/subsandbox/codex_pilot/claude_hal_codex.py --task-file my_task.txt
python3 temple/subsandbox/codex_pilot/claude_hal_codex.py --no-execute "any task"
```

Each run produces a JSON receipt at `runs/{ts}__{task_hash12}.json`.

## What this does not do

- Does not write to `town/ledger_v1.ndjson`
- Does not call MAYOR or the kernel daemon
- Does not produce SHIP claims
- Does not modify memory
- Does not promote canon

It is a sandbox to feel out the shape. Anything found here that wants to graduate must go through the standard HELEN proposal → peer-review → MAYOR → REDUCER chain.
