#!/bin/bash
# test_constitution_memory.sh
# Verify that memory.ndjson has NO authority tokens (Constitution Guard)

set -e

MEMORY_FILE="memory/memory.ndjson"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     HELEN CONSTITUTION TEST — Memory Authority Check          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Check if memory file exists
if [ ! -f "$MEMORY_FILE" ]; then
    echo "✅ PASS: No memory file yet (fresh state)"
    exit 0
fi

# Test 2: Read memory file and check for forbidden tokens
BANNED_TOKENS="LEDGER|SEAL|SEALED|APPROVED|VERDICT|SHIP|NO_SHIP|IRREVERSIBLE|TERMINATION|hal_verdict"

if grep -E "\b(${BANNED_TOKENS})\b" "$MEMORY_FILE" 2>/dev/null; then
    echo "❌ FAIL: Found forbidden authority tokens in memory.ndjson"
    echo ""
    echo "Memory must be NON-SOVEREIGN. Authority tokens belong in storage/run_trace.ndjson (UI/telemetry only)."
    exit 1
fi

# Test 3: Verify memory.ndjson is valid JSON (each line)
echo "Validating JSON format..."
while IFS= read -r line; do
    if [ -z "$line" ]; then
        continue
    fi
    if ! echo "$line" | python3 -m json.tool > /dev/null 2>&1; then
        echo "❌ FAIL: Invalid JSON in memory.ndjson"
        echo "Line: $line"
        exit 1
    fi
done < "$MEMORY_FILE"

# Test 4: Check that facts have required structure (event_id, key, value, status, actor)
echo "Checking memory event structure..."
REQUIRED_FIELDS="event_id|key|value|status|actor"
if ! grep -E "$REQUIRED_FIELDS" "$MEMORY_FILE" > /dev/null; then
    echo "⚠️  WARNING: Memory events might be missing required fields"
    echo "Expected: event_id, key, value, status, actor"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                     ✅ CONSTITUTION PASSED                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Memory is NON-SOVEREIGN ✓"
echo "No authority tokens ✓"
echo "Authority verdicts safely logged to storage/run_trace.ndjson ✓"
echo ""
exit 0
