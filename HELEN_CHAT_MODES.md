# HELEN Chat Modes (Terminal)

This repo already supports chat via the CLI. If you are only seeing receipts, you are likely running a receipt-only path or writing into a sealed sovereign ledger.

---

## TL;DR (works every time)

### Clean one-shot chat (no receipts)
```bash
cd helen_os_scaffold && source .venv/bin/activate
helen talk --reply --no-receipt --ledger :memory: "Hello HELEN."
```

### Chat + receipts (audit trail in memory)
```bash
helen talk --reply --ledger :memory: "Hello HELEN. Give 3 bullet steps."
```

### Interactive REPL (clean)
```bash
helen talk --reply --no-receipt --ledger :memory:
# You > Hello HELEN
# HELEN: ...
# You > exit
```

### Two-channel HELEN/HAL
```bash
helen talk --reply --hal --ledger :memory: "What is the canyon law?"
```

---

## Why `--ledger :memory:` matters

The default ledger may be a **SEALED sovereign ledger** (e.g. `storage/ledger_epoch*_work.ndjson`).

`helen talk --reply` logs a receipt **before** calling the LLM. If the ledger is sealed, the write fails and chat crashes:
```
PermissionError: LNSA_ERROR: Sovereign ledger is SEALED. No further mutations allowed.
```

**Use:**
- `--ledger :memory:` for ephemeral chat sessions (nothing persists, no files written)
- `--ledger storage/chat_dev.ndjson` for persistent dev chat receipts (unsealed, receipts saved to file)

---

## What NOT to do

### `helen_talk.py`

**`helen_talk.py` is receipt-only by design** — it logs that you spoke into the ledger, but does not call the LLM. HELEN cannot reply through this path.

```bash
python helen_os_scaffold/helen_talk.py   # ❌ no LLM, no reply
helen talk                                # ❌ no LLM (same behavior)
helen talk --reply --ledger :memory:     # ✅ LLM called, reply printed
```

---

## Optional: Local shell helpers (zsh/bash)

These are **local UX conveniences** — not required by the repo, but useful if you use HELEN chat regularly.

Add to `~/.zshrc` (one time):

```bash
# ── HELEN OS ──────────────────────────────────────────────────────────────────
_HELEN_DIR="/path/to/helen_os_scaffold"
export HELEN_LEDGER_MODE="${HELEN_LEDGER_MODE:-memory}"  # memory | dev | sovereign

helen_mode() {
  if [[ -n "$1" ]]; then
    case "$1" in
      memory|dev|sovereign) export HELEN_LEDGER_MODE="$1" ; echo "→ HELEN_LEDGER_MODE=$1" ;;
      *) echo "❌ Unknown mode '$1'. Use: memory | dev | sovereign" ; return 1 ;;
    esac
  else
    echo "HELEN_LEDGER_MODE=${HELEN_LEDGER_MODE}"
  fi
}

_helen_run() {
  local mode="${HELEN_LEDGER_MODE:-memory}"
  local ledger_path
  case "$mode" in
    memory)    ledger_path=":memory:" ;;
    dev)       ledger_path="storage/chat_dev.ndjson" ;;
    sovereign) ledger_path="" ;;
    *)         ledger_path=":memory:" ;;
  esac
  (
    cd "$_HELEN_DIR" || return 1
    [[ "$mode" == "dev" ]] && mkdir -p storage
    source .venv/bin/activate
    if [[ -n "$ledger_path" ]]; then
      helen talk --ledger "$ledger_path" "$@"
    else
      helen talk "$@"
    fi
  )
}

helen_say()  { _helen_run --reply --no-receipt "$@"; }   # clean one-shot
helen_chat() { _helen_run --reply --no-receipt; }         # interactive REPL
helen_hal()  { _helen_run --reply --hal "$@"; }           # two-channel HER/HAL
helen_dev()  { _helen_run --reply "$@"; }                 # receipts saved (mode-aware)
# ─────────────────────────────────────────────────────────────────────────────
```

Then use:
```bash
helen_say "your message"       # one-shot, clean
helen_chat                     # interactive REPL
helen_hal "your message"       # HER/HAL two-channel
helen_dev "your message"       # with receipts (to current mode's ledger)
helen_mode dev                 # switch to dev mode (persistent receipts)
helen_mode memory              # switch back to ephemeral (default)
```

---

## Ledger contract (for reference)

| Ledger        | State    | Use for                          | Rule                             |
|---------------|----------|----------------------------------|---------------------------------|
| `sovereign`   | SEALED   | certified epoch artifacts, tests | Never write chat here            |
| `dev`         | unsealed | persistent chat receipts         | CORE-mode only, not SHIP         |
| `:memory:`    | ephemeral| throwaway chat, REPL, debugging | Gone when process exits          |

SHIP mutations may only cite sovereign ledger receipts.
