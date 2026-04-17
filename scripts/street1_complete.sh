#!/bin/bash
# Street1 Conscious Ledger — Complete workflow
# Signature: events.ndjson → summary.json → helen wisdom

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVENTS_LOG="$REPO_ROOT/runs/street1/events.ndjson"
SUMMARY="$REPO_ROOT/runs/street1/summary.json"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Street1 Conscious Ledger — Post-Run Sealing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# ─── Check events exist ───────────────────────────────────────────────────

if [ ! -f "$EVENTS_LOG" ]; then
  echo "[ERROR] No events log found: $EVENTS_LOG"
  echo "Did you run: node street1-server.cjs?"
  exit 1
fi

EVENT_COUNT=$(wc -l < "$EVENTS_LOG")
echo "✓ events.ndjson: $EVENT_COUNT lines"

# ─── Rollup L0 → L2 ──────────────────────────────────────────────────────

echo "▶ Rollup: L0 (events) → L2 (summary)..."
python3 "$REPO_ROOT/scripts/street1_rollup.py" --validate

# ─── Extract key facts ────────────────────────────────────────────────────

if [ ! -f "$SUMMARY" ]; then
  echo "[ERROR] Summary generation failed"
  exit 1
fi

RUN_ID=$(python3 -c "import json; print(json.load(open('$SUMMARY')).get('run_id', 'UNKNOWN'))")
SEED=$(python3 -c "import json; print(json.load(open('$SUMMARY')).get('seed', 0))")
RECEIPT=$(python3 -c "import json; print(json.load(open('$SUMMARY')).get('receipt_sha', 'UNKNOWN'))")
FACTS=$(python3 -c "import json; print(len(json.load(open('$SUMMARY')).get('facts_extracted', [])))")
REPLIES=$(python3 -c "import json; print(len(json.load(open('$SUMMARY')).get('npc_replies', [])))")

echo "✓ summary.json: $REPLIES replies, $FACTS facts extracted"
echo
echo "  run_id      : $RUN_ID"
echo "  seed        : $SEED"
echo "  receipt_sha : $RECEIPT"
echo

# ─── Optional: link to HELEN wisdom ───────────────────────────────────────

if command -v ./helen &> /dev/null; then
  echo "▶ Recording to HELEN wisdom..."
  ./helen add \
    --lesson "Street1 seed=$SEED produced deterministic event trace: receipt_sha=$RECEIPT" \
    --evidence "runs/street1/summary.json#receipt_sha" \
    --kind "lesson" \
    --status "ACTIVE"
  echo "✓ Lesson recorded"
else
  echo "ℹ ./helen not found; skipping wisdom record"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SEALED. No receipt = no claim. Receipt: $RECEIPT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
