#!/bin/bash
# Marketing Street Determinism Verification Gate
# Purpose: Fail fast if determinism regresses (CI gate)
# Run this on every commit that touches marketing_street.cjs

set -e

REPO_ROOT="/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
SCRIPT="$REPO_ROOT/marketing_street.cjs"
TEMP_DIR="/tmp/marketing_street_verify_$$"
SEEDS=(1 7 42 111 999)

# Cleanup function
cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

mkdir -p "$TEMP_DIR"

echo "=== Marketing Street Determinism Gate ===" >&2
echo "Script: $SCRIPT" >&2
echo "Testing seeds: ${SEEDS[@]}" >&2
echo "" >&2

FAILED=0
PASSED=0

# Test each seed twice and compare SHA256
for seed in "${SEEDS[@]}"; do
  echo -n "Testing seed=$seed... " >&2

  # Run A
  RUN_A="$TEMP_DIR/run_${seed}_a.json"
  node "$SCRIPT" "$seed" > "$RUN_A" 2>/dev/null || {
    echo "FAIL (run failed)" >&2
    ((FAILED++))
    continue
  }

  # Run B (same seed)
  RUN_B="$TEMP_DIR/run_${seed}_b.json"
  node "$SCRIPT" "$seed" > "$RUN_B" 2>/dev/null || {
    echo "FAIL (second run failed)" >&2
    ((FAILED++))
    continue
  }

  # Compare SHA256
  SHA_A=$(sha256sum "$RUN_A" | awk '{print $1}')
  SHA_B=$(sha256sum "$RUN_B" | awk '{print $1}')

  if [ "$SHA_A" = "$SHA_B" ]; then
    echo "PASS (hash=$SHA_A)" >&2
    ((PASSED++))
  else
    echo "FAIL (hash mismatch)" >&2
    echo "  Run A: $SHA_A" >&2
    echo "  Run B: $SHA_B" >&2

    # Dump diff for debugging
    echo "  Diff:" >&2
    diff "$RUN_A" "$RUN_B" | head -20 | sed 's/^/    /' >&2

    ((FAILED++))
  fi
done

echo "" >&2
echo "=== Results ===" >&2
echo "Passed: $PASSED / ${#SEEDS[@]}" >&2
echo "Failed: $FAILED / ${#SEEDS[@]}" >&2

if [ $FAILED -gt 0 ]; then
  echo "❌ DETERMINISM VERIFICATION FAILED" >&2
  exit 1
fi

echo "✅ DETERMINISM VERIFIED" >&2
exit 0
