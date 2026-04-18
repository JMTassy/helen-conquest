#!/bin/bash
# superteam_explore.sh - Explore superteam test results
# Usage: bash superteam_explore.sh

echo "🔍 SUPERTEAM RESULTS EXPLORER"
echo "==============================="
echo ""

# Find latest results
LATEST=$(ls -t results/workflow_*_claims.json 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    echo "❌ No results found. Run: python3 superteam_cli.py \"Your prompt\""
    exit 1
fi

WORKFLOW_ID=$(basename "$LATEST" | sed 's/_claims.json//')
RESULTS_DIR="results"

echo "📁 Latest Workflow: $WORKFLOW_ID"
echo ""

# Count claims
CLAIMS=$(cat "${RESULTS_DIR}/${WORKFLOW_ID}_claims.json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "📋 Claims extracted: $CLAIMS"

# Extract agent names and claims
echo ""
echo "🧠 CLAIMS BY AGENT:"
echo "─────────────────────────────────────────────────────"

python3 << 'PYTHON_SCRIPT'
import json
import sys

agents = [
    ("DAN_Lateral", "🎨 Provocateur"),
    ("LIBRARIAN_Synth", "📚 Pattern Finder"),
    ("POET_Metaphor", "✨ Insight Unlocker"),
    ("HACKER_Sandbox", "⚠️ Vulnerability Scout"),
    ("SAGE_Dialectic", "☯️ Synthesizer"),
    ("DREAMER_Absurd", "🌀 Meta-Transgressor"),
]

try:
    with open("results/" + sys.argv[1] + "_claims.json") as f:
        claims = json.load(f)
    
    for agent_name, agent_emoji in agents:
        matching = [c for c in claims if c.get("source_agent") == agent_name]
        if matching:
            claim = matching[0]
            content = claim.get("content", "")[:70]
            edginess = claim.get("risk_profile", {}).get("tone_edginess", "safe")
            print(f"\n{agent_emoji}")
            print(f"  Content: {content}...")
            print(f"  Edginess: {edginess}")
except Exception as e:
    print(f"Error: {e}")
PYTHON_SCRIPT

echo ""
echo "───────────────────────────────────────────────────"
echo ""

# Validation results
echo "⚖️ VALIDATION RESULTS:"
python3 << 'PYTHON_SCRIPT'
import json
import sys

try:
    with open("results/" + sys.argv[1] + "_validation.json") as f:
        validation = json.load(f)
    
    passed = validation.get("passed", [])
    rejected = validation.get("rejected", [])
    
    print(f"  ✅ Passed: {len(passed)}")
    print(f"  ❌ Rejected: {len(rejected)}")
    
    if rejected:
        print(f"\n  Rejected proposals:")
        for prop in rejected:
            reasons = prop.get("rejection_reasons", [])
            print(f"    • {prop.get('proposal_id', '?')}: {reasons[0] if reasons else 'unknown'}")
except Exception as e:
    print(f"Error: {e}")
PYTHON_SCRIPT

echo ""
echo "📊 FILES GENERATED:"
ls -1 "${RESULTS_DIR}/${WORKFLOW_ID}"_*.json 2>/dev/null | while read f; do
    size=$(wc -c < "$f" | numfmt --to=iec-i 2>/dev/null || wc -c < "$f")
    name=$(basename "$f" | sed "s/${WORKFLOW_ID}_//")
    printf "  %-25s (%s)\n" "$name" "$size"
done

echo ""
echo "🔗 VIEW FULL RESULTS:"
echo "  cat results/${WORKFLOW_ID}_claims.json | python3 -m json.tool | less"
echo "  cat results/${WORKFLOW_ID}_proposals.json | python3 -m json.tool | less"
echo "  cat results/${WORKFLOW_ID}_validation.json | python3 -m json.tool | less"
echo ""
echo "🚀 RUN ANOTHER TEST:"
echo "  python3 superteam_cli.py \"Your new prompt\""
echo ""
