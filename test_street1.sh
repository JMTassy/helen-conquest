#!/bin/bash
# Street 1 test harness
# Starts backend + runs CLI emulator

set -e

echo "[Street1] Test harness starting…"
echo ""

# Kill any existing process on port 3001
lsof -ti :3001 | xargs kill -9 2>/dev/null || true

# Start server in background
echo "[Street1] Starting backend on port 3001…"
node street1-server.cjs &
SERVER_PID=$!

# Give server time to boot
sleep 2

# Verify port is listening
if ! lsof -i :3001 >/dev/null 2>&1; then
  echo "[FAIL] Server did not start on port 3001"
  kill $SERVER_PID 2>/dev/null || true
  exit 1
fi

echo "[Street1] Backend listening ✓"
echo ""

# Run CLI emulator
echo "[Street1] Running CLI tests…"
echo ""

node cli_emulate_street1.cjs
TEST_RESULT=$?

# Cleanup
kill $SERVER_PID 2>/dev/null || true

exit $TEST_RESULT
