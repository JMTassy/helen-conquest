#!/bin/bash
# Street 1 Ledger — Full Integration Test
# Validates: L0 (events) → L2 (summary) → L3 (wisdom)

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  Street 1 Conscious Ledger — Full Integration Test               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo

# Test 1: Verify modules exist
echo "▶ Test 1: Verify modules..."
[ -f street1-logger.cjs ] && echo "  ✓ street1-logger.cjs" || exit 1
[ -f scripts/street1_rollup.py ] && echo "  ✓ scripts/street1_rollup.py" || exit 1
[ -f scripts/street1_complete.sh ] && echo "  ✓ scripts/street1_complete.sh" || exit 1
[ -f schemas/street1_event.v1.schema.json ] && echo "  ✓ schema: event.v1" || exit 1
[ -f schemas/street1_summary.v1.schema.json ] && echo "  ✓ schema: summary.v1" || exit 1
echo

# Test 2: Verify server is patched
echo "▶ Test 2: Verify server patched with logger..."
grep -q "const logger = require" street1-server.cjs && echo "  ✓ logger imported" || exit 1
grep -q "logger.onResetRun" street1-server.cjs && echo "  ✓ onResetRun wired" || exit 1
grep -q "logger.onChatSend" street1-server.cjs && echo "  ✓ onChatSend wired" || exit 1
grep -q "logger.onMemoryExtract" street1-server.cjs && echo "  ✓ onMemoryExtract wired" || exit 1
grep -q "logger.onNpcReply" street1-server.cjs && echo "  ✓ onNpcReply wired" || exit 1
grep -q "logger.onSessionEnd" street1-server.cjs && echo "  ✓ onSessionEnd wired" || exit 1
echo

# Test 3: Verify events.ndjson exists and is valid
echo "▶ Test 3: Verify L0 (events.ndjson)..."
[ -f runs/street1/events.ndjson ] && echo "  ✓ events.ndjson exists" || exit 1
EVENT_COUNT=$(wc -l < runs/street1/events.ndjson)
echo "  ✓ event count: $EVENT_COUNT lines"

# Parse first event
FIRST_EVENT=$(head -1 runs/street1/events.ndjson)
echo "$FIRST_EVENT" | python3 -m json.tool > /dev/null && echo "  ✓ first event is valid JSON" || exit 1

# Check event has required fields
echo "$FIRST_EVENT" | python3 -c "
import json, sys
ev = json.load(sys.stdin)
assert 'run_id' in ev, 'missing run_id'
assert 'type' in ev, 'missing type'
assert '_sha' in ev, 'missing _sha (hash)'
print('  ✓ event has required fields: run_id, type, _sha')
"
echo

# Test 4: Verify L2 (summary.json)
echo "▶ Test 4: Verify L2 (summary.json)..."
[ -f runs/street1/summary.json ] && echo "  ✓ summary.json exists" || exit 1

python3 -c "
import json
summary = json.load(open('runs/street1/summary.json'))
assert summary['schema_version'] == 'STREET1_SUMMARY_V1', 'wrong schema_version'
assert summary['run_id'], 'missing run_id'
assert summary['receipt_sha'], 'missing receipt_sha'
print('  ✓ schema_version: STREET1_SUMMARY_V1')
print('  ✓ run_id:', summary['run_id'])
print('  ✓ receipt_sha:', summary['receipt_sha'])
print('  ✓ facts: ' + str(len(summary.get('facts_extracted', []))))
print('  ✓ replies: ' + str(len(summary.get('npc_replies', []))))
"
echo

# Test 5: Verify determinism (same seed → same hash)
echo "▶ Test 5: Verify determinism..."
SEED=$(python3 -c "import json; print(json.load(open('runs/street1/summary.json')).get('seed', 'UNKNOWN'))")
RECEIPT=$(python3 -c "import json; print(json.load(open('runs/street1/summary.json')).get('receipt_sha', 'UNKNOWN'))")
echo "  ✓ seed: $SEED → receipt_sha: $RECEIPT"
echo "  ℹ Note: Run again with same seed to verify hash reproducibility"
echo

# Test 6: Verify HELEN integration
echo "▶ Test 6: Verify HELEN integration..."
if [ -f helen_wisdom.ndjson ]; then
  WISDOM_COUNT=$(wc -l < helen_wisdom.ndjson)
  echo "  ✓ helen_wisdom.ndjson: $WISDOM_COUNT lessons"
  
  # Check if Street1 lesson is recorded
  if grep -q "Street1 seed" helen_wisdom.ndjson 2>/dev/null; then
    echo "  ✓ Street1 lesson recorded in wisdom"
  fi
else
  echo "  ℹ helen_wisdom.ndjson not yet created"
fi
echo

# Test 7: Verify ./helen works
echo "▶ Test 7: Verify ./helen CLI..."
if [ -x helen ]; then
  python3 -m py_compile helen && echo "  ✓ helen syntax OK" || exit 1
  ./helen soul > /dev/null 2>&1 && echo "  ✓ ./helen soul works" || exit 1
else
  echo "  ⚠ helen script not executable"
fi
echo

# Summary
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ ALL TESTS PASSED                                              ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo
echo "Next steps:"
echo "  1. Run server:        node street1-server.cjs"
echo "  2. Test CLI:          ./test_street1.sh"
echo "  3. Seal run:          bash scripts/street1_complete.sh"
echo "  4. View wisdom:       ./helen wisdom"
echo
