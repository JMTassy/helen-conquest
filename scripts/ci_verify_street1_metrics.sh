#!/usr/bin/env bash

# CI Gate: Street1 Metrics Determinism Verification
# Purpose: Ensure metrics analyzer produces deterministic output
# Exit codes: 0 = PASS, 1 = FAIL (CI blocks merge)

set -euo pipefail

REPO_ROOT="/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
ANALYZER="$REPO_ROOT/scripts/helen_metrics_analyzer.py"
SHA_FILE="$REPO_ROOT/runs/street1/interaction_proxy_metrics.sha256"

echo "=== CI VERIFY: Street1 Metrics Determinism ===" >&2

# Check if analyzer exists
if [ ! -f "$ANALYZER" ]; then
  echo "❌ FAIL: analyzer not found at $ANALYZER" >&2
  exit 1
fi

# Run analyzer (first time)
echo "Run 1: Computing metrics..." >&2
python3 "$ANALYZER" >/dev/null 2>&1 || {
  echo "❌ FAIL: analyzer exited non-zero (ledger may be invalid)" >&2
  exit 1
}

# Get first hash
if [ ! -f "$SHA_FILE" ]; then
  echo "❌ FAIL: metrics output not found at $SHA_FILE" >&2
  exit 1
fi

H1=$(cat "$SHA_FILE")
echo "SHA1: $H1" >&2

# Run analyzer again (determinism check)
echo "Run 2: Verifying determinism..." >&2
python3 "$ANALYZER" >/dev/null 2>&1 || {
  echo "❌ FAIL: analyzer exited non-zero on second run" >&2
  exit 1
}

# Get second hash
H2=$(cat "$SHA_FILE")
echo "SHA2: $H2" >&2

# Compare
if [ "$H1" != "$H2" ]; then
  echo "❌ FAIL: nondeterministic metrics output" >&2
  echo "Hash mismatch:" >&2
  echo "  Run 1: $H1" >&2
  echo "  Run 2: $H2" >&2
  exit 1
fi

echo "" >&2
echo "✅ PASS: metrics deterministic" >&2
echo "Canonical hash: $H1" >&2
exit 0
