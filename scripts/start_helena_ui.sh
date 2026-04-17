#!/usr/bin/env bash
# Launch Helen UI on an alternate port (default 3334)

UI_PORT=${UI_PORT:-3334}
export UI_PORT

echo "[HELEN_UI] Starting on port $UI_PORT ..."
node helen_ui_server.js &
SERVER_PID=$!

# Give the server a moment to bind
sleep 3

# Simple health‑check
if curl -s "http://localhost:${UI_PORT}/api/state" > /dev/null; then
  echo "[HELEN_UI] Server is up at http://localhost:${UI_PORT}"
else
  echo "[HELEN_UI] Failed to start"
  kill $SERVER_PID
  exit 1
fi

wait $SERVER_PID
