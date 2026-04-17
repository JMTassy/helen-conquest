#!/bin/bash
# Install git hooks for this repository
# Run this once after cloning: bash scripts/install-git-hooks.sh

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing git hooks..."

# Create pre-commit hook for CLAUDE.md index generation
cat > "$HOOKS_DIR/pre-commit" << 'HOOK_EOF'
#!/bin/bash
# Pre-commit hook: Regenerate and verify CLAUDE.md indices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REPO_ROOT=$(git rev-parse --show-toplevel)

# Check if CLAUDE.md was modified
if git diff --cached --quiet CLAUDE.md; then
    # CLAUDE.md not staged, skip check
    exit 0
fi

echo -e "${YELLOW}Checking CLAUDE.md indices...${NC}"

# Regenerate indices
cd "$REPO_ROOT"
python3 scratchpad/generate_claude_index.py > /dev/null 2>&1

# Check if indices changed
if ! git diff --quiet scratchpad/CLAUDE_MD_LINE_INDEX.txt scratchpad/CLAUDE_MD_SECTIONS_BY_LENGTH.txt; then
    echo -e "${YELLOW}CLAUDE.md changed but indices weren't updated.${NC}"
    echo -e "${RED}Auto-generating indices now...${NC}"

    # Stage the regenerated indices
    git add scratchpad/CLAUDE_MD_LINE_INDEX.txt
    git add scratchpad/CLAUDE_MD_SECTIONS_BY_LENGTH.txt

    echo -e "${GREEN}✓ Indices regenerated and staged${NC}"
    echo ""
    echo "New files were generated and added to your commit:"
    git diff --cached --stat scratchpad/CLAUDE_MD_*.txt
else
    echo -e "${GREEN}✓ Indices are current${NC}"
fi

exit 0
HOOK_EOF

chmod +x "$HOOKS_DIR/pre-commit"

echo -e "\033[0;32m✓ Git hooks installed${NC}"
echo ""
echo "Installed hooks:"
echo "  - pre-commit: Auto-regenerates CLAUDE.md indices before commit"
