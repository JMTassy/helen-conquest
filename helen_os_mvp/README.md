# HELEN OS MVP (v0.1)

Minimal, terminal-first conversational OS with:
- Persistent append-only memory (memory.ndjson)
- Conflict confirmation (ask + keep both w/ timestamps)
- Optional LLM backends (Ollama or OpenAI-compatible)

## Quick Start
```bash
# Chat REPL
python3 helen_os_mvp/cli.py chat

# One-shot run
python3 helen_os_mvp/cli.py run "Draft a memory kernel spec"
```

## Environment
- `HELEN_BACKEND=ollama|openai|none` (default: none)
- `OLLAMA_HOST=http://localhost:11434`
- `OPENAI_API_KEY=...`
- `OPENAI_MODEL=gpt-4.1-mini` (or any Responses API model)

## Memory
- Append-only: `helen_os_mvp/memory/memory.ndjson`
- Schema: `helen_os_mvp/memory/memory_schema_v1.json`

## Validators
```bash
python3 helen_os_mvp/tools/memory_validate.py
python3 helen_os_mvp/tools/memory_replay.py
```
