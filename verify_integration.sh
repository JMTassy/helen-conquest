#!/bin/bash
# Verification Script for CONQUEST Procedural Maps Integration
# Run this to verify all components are working

set -e

echo "=========================================="
echo "CONQUEST INTEGRATION VERIFICATION"
echo "=========================================="
echo ""

# Step 1: Check Python version
echo "✓ Checking Python..."
python3 --version
echo ""

# Step 2: Activate venv
echo "✓ Activating virtual environment..."
source .venv/bin/activate
echo ""

# Step 3: Run all tests
echo "✓ Running test suite..."
echo "  - Map Generator Tests (21 tests)"
echo "  - Map Renderer Tests (15 tests)"
echo "  - Integration Tests (21 tests)"
python3 -m pytest tests/test_map_generator_skill.py tests/test_map_renderer_fmg.py tests/test_conquest_integration.py -v --tb=short 2>&1 | tail -5
echo ""

# Step 4: Test integration module directly
echo "✓ Testing integration module..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 oracle_town/skills/conquest_integration.py 222 verify_test_001 2>&1 | head -20
echo ""

# Step 5: Test game engine
echo "✓ Testing game engine..."
python3 conquest_with_procedural_maps.py 333 verify_test_002 2>&1 | head -30
echo ""

# Step 6: Check files exist
echo "✓ Verifying files..."
FILES=(
  "oracle_town/skills/conquest_integration.py"
  "tests/test_conquest_integration.py"
  "conquest_with_procedural_maps.py"
  "docs/CONQUEST_PROCEDURAL_MAPS.md"
  "CONQUEST_INTEGRATION_COMPLETION.md"
)

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "  ✅ $f"
  else
    echo "  ❌ $f (MISSING)"
  fi
done
echo ""

# Step 7: Check ledger
echo "✓ Checking ledger..."
if [ -f "kernel/ledger/conquest_integration.jsonl" ]; then
  ENTRIES=$(wc -l < kernel/ledger/conquest_integration.jsonl)
  echo "  ✅ Ledger exists with $ENTRIES entries"
else
  echo "  ⚠️  Ledger not yet created (will be created on first run)"
fi
echo ""

# Step 8: Check SVG renders
echo "✓ Checking SVG renders..."
if [ -d "artifacts/map_renders" ]; then
  SVG_COUNT=$(ls artifacts/map_renders/*.svg 2>/dev/null | wc -l || echo 0)
  echo "  ✅ SVG directory has $SVG_COUNT maps"
  if [ $SVG_COUNT -gt 0 ]; then
    ls -lh artifacts/map_renders/*.svg | head -3
  fi
else
  echo "  ℹ️  SVG directory not yet created (will be created on first render)"
fi
echo ""

echo "=========================================="
echo "✨ VERIFICATION COMPLETE ✨"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run a game: python3 conquest_with_procedural_maps.py 111 my_game"
echo "  2. Check SVG: open artifacts/map_renders/map_my_game_seed_111.svg"
echo "  3. Read docs: docs/CONQUEST_PROCEDURAL_MAPS.md"
echo ""
