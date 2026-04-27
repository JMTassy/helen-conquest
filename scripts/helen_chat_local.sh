#!/usr/bin/env bash
# Bring HELEN's terminal chat surface up locally.
#
# Sets up the helen_os_scaffold venv on first run, verifies the Ollama
# adapter the scaffold's LLM client expects, then drops into `helen talk`
# with an in-memory ledger (sidesteps the sealed-sovereign-ledger crash
# documented in CLAUDE.md > Chat Surfaces).
#
# Usage:
#   scripts/helen_chat_local.sh                     # interactive: re-prompts each turn
#   scripts/helen_chat_local.sh "hello HELEN"       # one-shot: single message, prints reply, exits
#   HELEN_MODE=chat scripts/helen_chat_local.sh     # use `helen chat` (full agent stack) instead

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCAFFOLD="$REPO_ROOT/helen_os_scaffold"
VENV="$SCAFFOLD/.venv"

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-mistral-kernel}"
HELEN_MODE="${HELEN_MODE:-talk}"   # talk | chat
LEDGER="${HELEN_LEDGER:-:memory:}"

if [ ! -d "$SCAFFOLD" ]; then
  echo "[helen-chat] cannot find $SCAFFOLD — run from the helen-conquest repo." >&2
  exit 1
fi

if [ ! -x "$VENV/bin/helen" ]; then
  echo "[helen-chat] first-run: creating venv at $VENV"
  python3 -m venv "$VENV"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  pip install --quiet --upgrade pip
  pip install --quiet -e "$SCAFFOLD"
else
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
fi

if ! curl -fsS --max-time 2 "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
  echo "[helen-chat] Ollama not reachable at $OLLAMA_HOST" >&2
  echo "             start it in another terminal:  ollama serve" >&2
  exit 2
fi

if ! curl -fsS --max-time 2 "$OLLAMA_HOST/api/tags" | grep -q "\"$OLLAMA_MODEL\""; then
  echo "[helen-chat] model '$OLLAMA_MODEL' not present — pulling..."
  ollama pull "$OLLAMA_MODEL"
fi

echo "[helen-chat] mode=$HELEN_MODE ledger=$LEDGER model=$OLLAMA_MODEL"

case "$HELEN_MODE" in
  talk)
    if [ "$#" -gt 0 ]; then
      helen talk "$*" --reply --ledger "$LEDGER"
    else
      while IFS= read -r -p "you> " line; do
        [ -z "$line" ] && continue
        case "$line" in exit|quit) break ;; esac
        helen talk "$line" --reply --ledger "$LEDGER"
      done
    fi
    ;;
  chat)
    helen chat "$@"
    ;;
  *)
    echo "[helen-chat] unknown HELEN_MODE='$HELEN_MODE' (expected: talk | chat)" >&2
    exit 3
    ;;
esac
