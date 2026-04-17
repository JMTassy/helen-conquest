#!/bin/bash
# Preflight Nondeterminism Detection Gate
# Purpose: Catch forbidden patterns before they reach determinism testing
# Forbidden: Date.now(), new Date(), Math.random(), randomUUID(), etc.

set -e

REPO_ROOT="/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24"
SEARCH_PATHS=(
  "$REPO_ROOT/marketing_street.cjs"
  "$REPO_ROOT/scripts/marketing_street_*.sh"
  "$REPO_ROOT/scripts/verify_marketing_street_determinism.sh"
)

# Forbidden patterns (unquoted, unless allowlisted)
FORBIDDEN_PATTERNS=(
  "Date\.now\(\)"
  "new Date\("
  "toISOString\(\)"
  "Math\.random\(\)"
  "randomUUID\("
  "process\.hrtime\("
  "performance\.now\("
  "crypto\.randomBytes\("
  "uuid\(\)"
)

echo "=== Preflight Nondeterminism Check ===" >&2
echo "Searching: ${SEARCH_PATHS[*]}" >&2
echo "" >&2

VIOLATIONS=0

for path in "${SEARCH_PATHS[@]}"; do
  if [ ! -f "$path" ]; then
    continue
  fi

  for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
    # Search for pattern, but allow it if followed by "NONDETERMINISTIC_OK" comment
    matches=$(grep -n -E "$pattern" "$path" 2>/dev/null | grep -v "NONDETERMINISTIC_OK" || true)

    if [ -n "$matches" ]; then
      echo "❌ FORBIDDEN PATTERN FOUND: $pattern" >&2
      echo "   File: $path" >&2
      echo "$matches" | sed 's/^/   /' >&2
      echo "" >&2
      ((VIOLATIONS++))
    fi
  done
done

if [ $VIOLATIONS -gt 0 ]; then
  echo "❌ PREFLIGHT FAILED: $VIOLATIONS violations" >&2
  echo "" >&2
  echo "Allowed exceptions: add '// NONDETERMINISTIC_OK: reason' comment on same line" >&2
  exit 1
fi

echo "✅ PREFLIGHT PASSED: No forbidden nondeterminism patterns detected" >&2
exit 0
