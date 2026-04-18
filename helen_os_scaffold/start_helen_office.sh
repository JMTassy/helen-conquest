#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────────────────
# start_helen_office.sh — Launch HELEN OS + Star-Office-UI pixel office
#
# Architecture (HELEN OS Canon V1 §5 Channel Model):
#   Port 8000  — HELEN OS FastAPI backend  (cognitive layer)
#   Port 19000 — Star-Office-UI Flask UI   (Channel C, non-sovereign)
#   Bridge     — helen_star_bridge.py      (state pusher, background thread)
#
# Usage:
#   bash start_helen_office.sh          # full stack
#   bash start_helen_office.sh --ui-only  # just Star-Office (no HELEN backend)
# ────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCAFFOLD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAR_OFFICE_DIR="$SCAFFOLD_DIR/Star-Office-UI"
HELEN_VENV="$SCAFFOLD_DIR/.venv"
STAR_VENV="$STAR_OFFICE_DIR/.venv"
LOG_DIR="$SCAFFOLD_DIR/logs"
BRIDGE_LOG="$LOG_DIR/bridge.log"
HELEN_LOG="$LOG_DIR/helen_server.log"
STAR_LOG="$LOG_DIR/star_office.log"

UI_ONLY=false
for arg in "$@"; do
  [[ "$arg" == "--ui-only" ]] && UI_ONLY=true
done

# ── Colors ───────────────────────────────────────────────────────────────────
CYAN="\033[96m"; YELLOW="\033[93m"; MAGENTA="\033[95m"
GREEN="\033[92m"; RED="\033[91m"; RESET="\033[0m"

echo -e "${CYAN}╔═══════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║  HELEN OS + Star-Office Pixel UI              ║${RESET}"
echo -e "${CYAN}╚═══════════════════════════════════════════════╝${RESET}"
echo ""

# ── Prereqs ──────────────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"

if [[ ! -d "$STAR_OFFICE_DIR" ]]; then
  echo -e "${RED}✗ Star-Office-UI not found at $STAR_OFFICE_DIR${RESET}"
  echo "  Clone it first:"
  echo "  git clone https://github.com/ringhyacinth/Star-Office-UI.git $STAR_OFFICE_DIR"
  exit 1
fi

# ── Install Star-Office deps if venv missing ──────────────────────────────────
if [[ ! -d "$STAR_VENV" ]]; then
  echo -e "${YELLOW}⟳ Installing Star-Office-UI dependencies...${RESET}"
  python3 -m venv "$STAR_VENV"
  "$STAR_VENV/bin/pip" install -q -r "$STAR_OFFICE_DIR/backend/requirements.txt"
  echo -e "${GREEN}✓ Star-Office deps installed${RESET}"
fi

# ── Copy sample configs if missing ───────────────────────────────────────────
[[ ! -f "$STAR_OFFICE_DIR/state.json" ]] && \
  cp "$STAR_OFFICE_DIR/state.sample.json" "$STAR_OFFICE_DIR/state.json"

[[ ! -f "$STAR_OFFICE_DIR/join-keys.json" ]] && \
  cp "$STAR_OFFICE_DIR/join-keys.sample.json" "$STAR_OFFICE_DIR/join-keys.json"

# ── Register HELEN agent roster (non-sovereign, Channel C) ───────────────────
echo -e "${MAGENTA}⟳ Registering HELEN agents in pixel office...${RESET}"
if [[ -d "$HELEN_VENV" ]]; then
  "$HELEN_VENV/bin/python" "$SCAFFOLD_DIR/helen_star_bridge.py" --register-agents 2>/dev/null || true
  "$HELEN_VENV/bin/python" "$SCAFFOLD_DIR/helen_star_bridge.py" idle "HELEN OS starting up..." 2>/dev/null || true
  echo -e "${GREEN}✓ Agents registered${RESET}"
fi

# ── Start Star-Office-UI backend (port 19000) ─────────────────────────────────
echo -e "${YELLOW}⟳ Starting Star-Office pixel office (port 19000)...${RESET}"
STAR_OFFICE_PORT=19000

cd "$STAR_OFFICE_DIR/backend"
"$STAR_VENV/bin/python" app.py > "$STAR_LOG" 2>&1 &
STAR_PID=$!
echo -e "${GREEN}✓ Star-Office started (PID $STAR_PID)${RESET}"
cd "$SCAFFOLD_DIR"

# ── Wait for Star-Office to be ready ─────────────────────────────────────────
echo -e "${YELLOW}⟳ Waiting for Star-Office...${RESET}"
for i in {1..15}; do
  if curl -sf "http://localhost:$STAR_OFFICE_PORT/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Star-Office ready${RESET}"
    break
  fi
  sleep 1
done

# ── Start HELEN OS backend (port 8000) ───────────────────────────────────────
if [[ "$UI_ONLY" == "false" ]]; then
  if [[ ! -d "$HELEN_VENV" ]]; then
    echo -e "${RED}✗ HELEN venv not found at $HELEN_VENV${RESET}"
    echo "  Run: cd helen_os_scaffold && python3 -m venv .venv && pip install -e ."
  else
    echo -e "${CYAN}⟳ Starting HELEN OS backend (port 8000)...${RESET}"
    "$HELEN_VENV/bin/python" -m uvicorn server:app --host 0.0.0.0 --port 8000 \
      --log-level warning > "$HELEN_LOG" 2>&1 &
    HELEN_PID=$!
    echo -e "${GREEN}✓ HELEN OS backend started (PID $HELEN_PID)${RESET}"

    # Wait for HELEN to be ready
    for i in {1..20}; do
      if curl -sf "http://localhost:8000/api/status" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ HELEN OS ready${RESET}"
        break
      fi
      sleep 1
    done
  fi
fi

# ── Print access URLs ─────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}  HELEN OS Pixel Office — Ready                 ${RESET}"
echo -e "${CYAN}════════════════════════════════════════════════${RESET}"
echo -e "  ${GREEN}Pixel UI:${RESET}    http://localhost:${STAR_OFFICE_PORT}"
if [[ "$UI_ONLY" == "false" ]]; then
echo -e "  ${GREEN}HELEN API:${RESET}   http://localhost:8000/api/status"
echo -e "  ${GREEN}API docs:${RESET}    http://localhost:8000/docs"
fi
echo ""
echo -e "  ${YELLOW}Bridge controls:${RESET}"
echo -e "  ${YELLOW}  source .venv/bin/activate${RESET}"
echo -e "  ${YELLOW}  python helen_star_bridge.py researching \"Reading receipts...\"${RESET}"
echo -e "  ${YELLOW}  python helen_star_bridge.py idle${RESET}"
echo ""
echo -e "  Logs: $LOG_DIR/"
echo -e "${CYAN}════════════════════════════════════════════════${RESET}"
echo ""

# ── Trap for clean shutdown ───────────────────────────────────────────────────
cleanup() {
  echo ""
  echo -e "${YELLOW}⟳ Shutting down...${RESET}"
  [[ -n "${HELEN_PID:-}" ]] && kill "$HELEN_PID" 2>/dev/null || true
  [[ -n "${STAR_PID:-}" ]] && kill "$STAR_PID" 2>/dev/null || true
  # Set Star-Office state to idle on exit
  "$HELEN_VENV/bin/python" "$SCAFFOLD_DIR/helen_star_bridge.py" idle "HELEN OS offline" 2>/dev/null || true
  echo -e "${GREEN}✓ Clean shutdown complete${RESET}"
}
trap cleanup EXIT INT TERM

# ── Keep running (wait for child processes) ───────────────────────────────────
wait
