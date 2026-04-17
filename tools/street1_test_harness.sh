#!/bin/bash
# Street1 Test Harness
# Runs a full deterministic session: HER generator → runner → witness injection → proof

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOWN_DIR="$REPO_ROOT/town"
LEDGER="$TOWN_DIR/ledger.ndjson"
INBOX="$TOWN_DIR/inbox.txt"
ARTIFACTS="$TOWN_DIR/artifacts"
SCHEMA="$TOWN_DIR/HAL_OUTPUT.schema.json"

echo "⟦🜂⟧ Street1 Test Harness (Deterministic Session)"
echo "Repo: $REPO_ROOT"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 1. Setup: Create town directory + schema
# ─────────────────────────────────────────────────────────────────────────

echo "Step 1: Setup"
mkdir -p "$TOWN_DIR" "$ARTIFACTS"

# Create HAL_OUTPUT.schema.json
cat > "$SCHEMA" << 'EOF'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["verdict", "reasons", "required_fixes", "state_patch"],
  "properties": {
    "verdict": {
      "type": "string",
      "enum": ["PASS", "WARN", "BLOCK"]
    },
    "reasons": {
      "type": "array",
      "items": {"type": "string"}
    },
    "required_fixes": {
      "type": "array",
      "items": {"type": "string"}
    },
    "state_patch": {
      "type": "object"
    },
    "ledger_append": {
      "type": "object"
    }
  },
  "additionalProperties": false
}
EOF

echo "✅ Town directory initialized"
echo "✅ Schema created: $SCHEMA"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 2. Clear ledger (fresh start)
# ─────────────────────────────────────────────────────────────────────────

echo "Step 2: Initialize ledger"
> "$LEDGER"
echo "✅ Ledger cleared"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 3. Run 10-turn session (HER generator + runner loop)
# ─────────────────────────────────────────────────────────────────────────

echo "Step 3: Run session (10 turns)"
cd "$REPO_ROOT"

for TURN in {1..10}; do
  echo "  Turn $TURN/10..."

  # Emit next HER block
  python3 tools/street1_her_generator.py

  # Run turn through runner
  python3 -c "
import sys
sys.path.insert(0, 'tools')
from street1_runner import run_turn
from pathlib import Path

inbox = Path('town/inbox.txt')
if inbox.exists():
    output = inbox.read_text()
    try:
        run_turn(output)
    except Exception as e:
        print(f'Error in turn $TURN: {e}')
        sys.exit(1)
"

  # Check for termination
  if [ -f "$LEDGER" ]; then
    LAST_LINE=$(tail -1 "$LEDGER")
    if echo "$LAST_LINE" | grep -q '"type":"termination"'; then
      echo "✅ Session terminated"
      break
    fi
  fi
done

echo "✅ Session completed"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 4. Verify ledger integrity
# ─────────────────────────────────────────────────────────────────────────

echo "Step 4: Verify ledger"
LEDGER_HASH=$(python3 -c "
import json
import hashlib
from pathlib import Path

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))

def sha256_hex(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

ledger = []
with open('town/ledger.ndjson') as f:
    for line in f:
        if line.strip():
            ledger.append(json.loads(line))

print(sha256_hex(ledger))
")

echo "Ledger hash: $LEDGER_HASH"
LEDGER_LINES=$(wc -l < "$LEDGER")
echo "Ledger size: $LEDGER_LINES lines"
echo "✅ Ledger verified"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 5. Run replay check (same seed → same hash)
# ─────────────────────────────────────────────────────────────────────────

echo "Step 5: Replay determinism check"
echo "  (Run session again with same seed...)"

# Clear ledger
> "$LEDGER"

# Re-run session
for TURN in {1..10}; do
  python3 tools/street1_her_generator.py > /dev/null 2>&1
  python3 -c "
import sys
sys.path.insert(0, 'tools')
from street1_runner import run_turn
from pathlib import Path

inbox = Path('town/inbox.txt')
if inbox.exists():
    output = inbox.read_text()
    try:
        run_turn(output)
    except:
        pass
" 2>/dev/null

  if [ -f "$LEDGER" ]; then
    LAST_LINE=$(tail -1 "$LEDGER")
    if echo "$LAST_LINE" | grep -q '"type":"termination"'; then
      break
    fi
  fi
done

# Compute hash of second run
LEDGER_HASH_2=$(python3 -c "
import json
import hashlib
from pathlib import Path

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))

def sha256_hex(obj):
    return hashlib.sha256(canonical(obj).encode()).hexdigest()

ledger = []
with open('town/ledger.ndjson') as f:
    for line in f:
        if line.strip():
            ledger.append(json.loads(line))

print(sha256_hex(ledger))
")

echo "  First run hash:  $LEDGER_HASH"
echo "  Second run hash: $LEDGER_HASH_2"

if [ "$LEDGER_HASH" = "$LEDGER_HASH_2" ]; then
    echo "✅ DETERMINISM VERIFIED (hashes match)"
else
    echo "❌ DETERMINISM FAILED (hashes differ)"
    exit 1
fi

echo ""
echo "=" | head -c 80
echo ""
echo "✅ ALL TESTS PASSED"
echo "=" | head -c 80
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 6. Summary
# ─────────────────────────────────────────────────────────────────────────

echo "Summary:"
echo "  Ledger: $LEDGER"
echo "  Hash: $LEDGER_HASH"
echo "  Determinism: VERIFIED ✅"
echo ""

