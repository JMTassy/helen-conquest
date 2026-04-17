#!/bin/bash
set -e

echo "════════════════════════════════════════════════════════════════"
echo "ORACLE TOWN State Management System - Full Test"
echo "════════════════════════════════════════════════════════════════"
echo

# Test 1: Render basic
echo "[1/5] Testing basic render (ASCII)..."
python3 render_home.py > /dev/null && echo "✓ render_home.py works"

# Test 2: Render enhanced unicode
echo "[2/5] Testing enhanced render (Unicode)..."
python3 render_home_enhanced.py --unicode > /dev/null && echo "✓ render_home_enhanced.py --unicode works"

# Test 3: Render enhanced ASCII
echo "[3/5] Testing enhanced render (ASCII)..."
python3 render_home_enhanced.py --ascii > /dev/null && echo "✓ render_home_enhanced.py --ascii works"

# Test 4: Diff
echo "[4/5] Testing diff..."
python3 diff_city.py > /dev/null && echo "✓ diff_city.py works"

# Test 5: Simulate 14 days
echo "[5/5] Testing 14-day simulator..."
python3 simulate_14_days.py > /dev/null
COUNT=$(ls sim_day_*.json 2>/dev/null | wc -l)
if [ "$COUNT" -eq 28 ]; then
    echo "✓ simulate_14_days.py generated 28 files (14 days × 2)"
else
    echo "✗ Expected 28 files, got $COUNT"
    exit 1
fi

echo
echo "════════════════════════════════════════════════════════════════"
echo "✓ ALL TESTS PASSED"
echo "════════════════════════════════════════════════════════════════"
echo
echo "System is ready. Try:"
echo "  python3 render_home_enhanced.py --unicode"
echo "  python3 diff_city.py"
echo "  python3 rotate_state.py"
