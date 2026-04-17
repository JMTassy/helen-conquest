#!/bin/bash
# Minimal local gate: ensure doc indices are fresh and code is syntactically valid
# Usage: scripts/town-check.sh
#        TOWN_EVIDENCE=1 scripts/town-check.sh  (also validate emulation evidence)
# Composable: designed to integrate with oracle_town/VERIFY_ALL.sh later if needed
#
# Invariant: After running the generator, there must be zero working-tree diffs
#            for CLAUDE_MD_*.txt files. If not, indices are stale.
#
# Exit codes:
#   0 = all gates passed
#   1 = indices stale or syntax error or evidence validation failed

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"
cd "$ROOT"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[town-check] starting local verification gate${NC}"
echo ""

# ============================================================================
# GATE 1: Documentation indices must be current (working-tree check)
# ============================================================================
echo -e "${YELLOW}[town-check] gate 1: doc indices${NC}"

IDX1="scratchpad/CLAUDE_MD_LINE_INDEX.txt"
IDX2="scratchpad/CLAUDE_MD_SECTIONS_BY_LENGTH.txt"

if ! python3 scratchpad/generate_claude_index.py >/dev/null 2>&1; then
    echo -e "${RED}ERROR: Generator failed to run${NC}"
    exit 1
fi

# CRITICAL: Check working-tree diffs, not just staged diffs
# The invariant is: after regeneration, there must be zero diffs in the working tree
if ! git diff --quiet -- "$IDX1" "$IDX2"; then
    echo -e "${RED}ERROR: CLAUDE.md indices are stale (regeneration produced changes)${NC}"
    echo ""
    echo "Fix:"
    echo "  1. Run: python3 scratchpad/generate_claude_index.py"
    echo "  2. Review changes:"
    echo "     git diff --stat -- $IDX1 $IDX2"
    echo "  3. Commit:"
    echo "     git add $IDX1 $IDX2"
    echo "     git commit -m 'docs: regenerate CLAUDE.md indices'"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Indices are current (no working-tree diffs)${NC}"
echo ""

# ============================================================================
# GATE 2: Python syntax is valid (cheap sanity check)
# ============================================================================
echo -e "${YELLOW}[town-check] gate 2: python syntax${NC}"

if ! python3 -m py_compile $(git ls-files '*.py' 2>/dev/null | head -50) 2>/dev/null; then
    echo -e "${RED}ERROR: Python syntax error detected${NC}"
    echo "Run: python3 -m py_compile <file.py> for details"
    exit 1
fi

echo -e "${GREEN}✓ Python syntax valid${NC}"

echo ""

# ============================================================================
# GATE 3: Evidence validation (optional, only if TOWN_EVIDENCE=1)
# ============================================================================
if [ "${TOWN_EVIDENCE:-0}" = "1" ]; then
    echo -e "${YELLOW}[town-check] gate 3: emulation evidence${NC}"

    if ! python3 scripts/extract-emulation-evidence.py; then
        echo ""
        echo -e "${RED}ERROR: Evidence validation failed${NC}"
        echo "Some artifacts cited in ORACLE_TOWN_EMULATION_EVIDENCE.md are missing or changed."
        echo ""
        exit 1
    fi

    echo -e "${GREEN}✓ Emulation evidence validated${NC}"
    echo ""
fi

# ============================================================================
# GATE 4: Generate ASCII town visualization (always runs on success)
# ============================================================================
echo -e "${YELLOW}[town-check] gate 4: generating town ascii${NC}"

# Generate ASCII town (pass evidence flag if enabled)
if [ "${TOWN_EVIDENCE:-0}" = "1" ]; then
    python3 scripts/generate_town_ascii.py --evidence >/dev/null 2>&1
else
    python3 scripts/generate_town_ascii.py >/dev/null 2>&1
fi

if [ -f "TOWN_ASCII.generated.txt" ]; then
    echo -e "${GREEN}✓ Town ASCII generated${NC}"
else
    echo -e "${YELLOW}⚠ Town ASCII generation skipped${NC}"
fi

echo ""

# ============================================================================
# All gates passed - Display town visualization
# ============================================================================
echo -e "${GREEN}[town-check] ✅ GREEN — all gates passed${NC}"
echo ""

# Show the generated town (if available)
if [ -f "TOWN_ASCII.generated.txt" ]; then
    echo ""
    cat TOWN_ASCII.generated.txt
    echo ""
fi

echo "Next:"
echo "  • Continue iterating (indices are clean)"
echo "  • Commit when ready: git add && git commit"
echo "  • Heavy verification (optional): bash oracle_town/VERIFY_ALL.sh"
echo "  • Evidence validation (optional): TOWN_EVIDENCE=1 bash scripts/town-check.sh"
echo ""

exit 0
