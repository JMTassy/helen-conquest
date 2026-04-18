#!/bin/bash
cd /Users/jean-marietassy/Desktop/'JMT CONSULTING - Releve 24'

echo "[TEST] Starting server..."
node street1-server.cjs > /tmp/test_server.log 2>&1 &
SERVER_PID=$!

sleep 2

echo "[TEST] Server PID: $SERVER_PID"
echo "[TEST] Running CLI test..."
SEED=42 node cli_emulate_street1.cjs 2>&1 | head -80

echo "[TEST] Killing server..."
kill -9 $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo "[TEST] Server log:"
tail -20 /tmp/test_server.log
