#!/bin/bash
cd /Users/jean-marietassy/Desktop/'JMT CONSULTING - Releve 24'

echo "🧪 Test Single Determinism Run"
echo ""

# Clean
rm -f runs/street1/events.ndjson runs/street1/summary.json

# Start server
node street1-server.cjs > /tmp/test_single_server.log 2>&1 &
SERVER_PID=$!
echo "[Server] PID=$SERVER_PID"

sleep 2

# Run CLI
echo "[CLI] Starting with SEED=77..."
SEED=77 node cli_emulate_street1.cjs 2>&1 | tee /tmp/test_single_cli.log
CLI_EXIT=$?
echo "[CLI] Exit code: $CLI_EXIT"

sleep 1

# Seal
echo "[Seal] Calling street1_complete.sh..."
bash scripts/street1_complete.sh 2>&1 | tail -20
SEAL_EXIT=$?
echo "[Seal] Exit code: $SEAL_EXIT"

# Check artifacts
echo ""
echo "📁 Artifacts:"
ls -lh runs/street1/ 2>/dev/null | tail -5
echo ""
echo "📝 Events log:"
cat runs/street1/events.ndjson 2>/dev/null | head -10
echo ""
echo "📊 Summary:"
cat runs/street1/summary.json 2>/dev/null | jq .

# Clean up
kill -9 $SERVER_PID 2>/dev/null || true
