#!/bin/bash
cd /Users/jean-marietassy/Desktop/'JMT CONSULTING - Releve 24'

echo "Testing seed=1 determinism (2 runs)"

for run in A B; do
  echo ""
  echo "=== RUN $run (seed=1) ==="

  # Kill any server
  pkill -9 node 2>/dev/null
  sleep 2

  # Clean
  rm -f runs/street1/events.ndjson runs/street1/summary.json

  # Start server
  node street1-server.cjs > /tmp/test_seed1_${run}_server.log 2>&1 &
  sleep 2

  # Run CLI
  SEED=1 node cli_emulate_street1.cjs > /tmp/test_seed1_${run}_cli.log 2>&1
  echo "[CLI] Exit: $?"

  # Wait for all writes
  sleep 3

  # Rollup
  python3 scripts/street1_rollup.py > /tmp/test_seed1_${run}_rollup.log 2>&1
  echo "[Rollup] Done"

  # Save events
  cp runs/street1/events.ndjson runs/street1/events_${run}.ndjson

  # Get receipt
  SHA=$(python3 -c "import json; print(json.load(open('runs/street1/summary.json')).get('receipt_sha'))")
  echo "receipt_sha=$SHA"

  # Count events
  LINES=$(wc -l < runs/street1/events_${run}.ndjson)
  echo "event_lines=$LINES"
done

echo ""
echo "=== DIFF ==="
diff runs/street1/events_A.ndjson runs/street1/events_B.ndjson | head -100
