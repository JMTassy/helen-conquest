#!/bin/bash
#
# Mode A: Daily Emulation Loop (Observe-only)
#
# Produces:
#   - Daily brief (read-only)
#   - Trend analysis (7-day comparison)
#   - Immutable ledger entries (all REJECTs expected)
#   - Determinism checks (hashes)
#
# Zero execution. Zero authority. Pure observation.
#

set -e

# ============================================================================
# 1. Setup: Date + Run ID
# ============================================================================

RUN_DATE=$(date +%F)
RUN_ID=$(date +%s | tail -c 4)  # Last 4 digits of Unix timestamp as run ID
RUN_ID_STR="emu_${RUN_DATE}_${RUN_ID}"

echo "=== Mode A: Daily Emulation Loop ==="
echo "Date: $RUN_DATE"
echo "Run ID: $RUN_ID (numeric)"
echo "Run ID (string): $RUN_ID_STR"
echo ""

# Change to repo root (handle different invocation paths)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../.."

# Ensure artifact directory exists
mkdir -p artifacts/
mkdir -p oracle_town/ledger/briefs/

# ============================================================================
# 2. Labor Chain
# ============================================================================

echo "[1/5] OBS_SCAN: Normalize observations..."
python3 oracle_town/jobs/obs_scan.py \
  --date "$RUN_DATE" \
  --run-id "$RUN_ID" \
  --input-dir artifacts/ \
  --output /tmp/obs_out.json \
  --verbose

echo "[2/5] INS_CLUSTER: Cluster insights..."
python3 oracle_town/jobs/ins_cluster.py \
  --date "$RUN_DATE" \
  --run-id "$RUN_ID" \
  --observations /tmp/obs_out.json \
  --output /tmp/ins_out.json \
  --verbose

echo "[3/5] BRF_ONEPAGER: Synthesize brief..."
python3 oracle_town/jobs/brf_onepager.py \
  --date "$RUN_DATE" \
  --run-id "$RUN_ID" \
  --insights /tmp/ins_out.json \
  --output /tmp/brf_out.json \
  --verbose

# Store brief in ledger for trend memory
cp /tmp/brf_out.json "oracle_town/ledger/briefs/brief_${RUN_DATE}.json" 2>/dev/null || true

echo "[4/5] TREND_MEMORY: Compare to 7-day history..."
python3 oracle_town/jobs/trend_memory.py \
  --date "$RUN_DATE" \
  --run-id "$RUN_ID" \
  --insights /tmp/ins_out.json \
  --ledger oracle_town/ledger/ \
  --output /tmp/trend_report.json \
  --verbose

# ============================================================================
# 3. Authority Chain (Expected: All REJECT)
# ============================================================================

echo "[5/5] Authority Chain (TRI + Mayor)..."

# Create emulation claim (read-only, no execution intent)
cat > /tmp/claim_emulated.json << EOF
{
  "claim": {
    "id": "claim_${RUN_ID_STR}_daily_brief",
    "type": "observation_synthesis",
    "source": "BRF_ONEPAGER",
    "intent": "Daily synthesis (emulation-only, no execution)",
    "scope": "read-only",
    "evidence": {
      "obs": "/tmp/obs_out.json",
      "insights": "/tmp/ins_out.json",
      "brief": "/tmp/brf_out.json",
      "trend": "/tmp/trend_report.json"
    }
  }
}
EOF

# TRI Gate (expected: REJECT - no authority for emulation claims)
python3 oracle_town/jobs/tri_gate.py \
  --claim /tmp/claim_emulated.json \
  --output /tmp/tri_verdict.json \
  --policy-hash "sha256:policy_v1_2026_01" \
  --key-registry oracle_town/keys/public_keys.json \
  2>&1 || true

# Mayor Signs (even rejects get receipts)
python3 oracle_town/jobs/mayor_sign.py \
  --verdict /tmp/tri_verdict.json \
  --claim /tmp/claim_emulated.json \
  --output /tmp/receipt.json \
  --policy-hash "sha256:policy_v1_2026_01" \
  --ledger oracle_town/ledger/ \
  2>&1 || true

# ============================================================================
# 4. Determinism Check
# ============================================================================

echo ""
echo "=== Determinism Check (K5) ==="
echo "Computing hashes of all outputs..."
echo ""

# Compute hashes for verification
OBS_HASH=$(python3 -c "import json, hashlib; data=json.load(open('/tmp/obs_out.json')); print(hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest())")
INS_HASH=$(python3 -c "import json, hashlib; data=json.load(open('/tmp/ins_out.json')); print(hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest())")
BRF_HASH=$(python3 -c "import json, hashlib; data=json.load(open('/tmp/brf_out.json')); print(hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest())" 2>&1 || echo "MARKDOWN_FORMAT")
TREND_HASH=$(python3 -c "import json, hashlib; data=json.load(open('/tmp/trend_report.json')); print(hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest())")

echo "OBS_SCAN:     $OBS_HASH"
echo "INS_CLUSTER:  $INS_HASH"
echo "BRF_ONEPAGER: $BRF_HASH"
echo "TREND_MEMORY: $TREND_HASH"
echo ""

# ============================================================================
# 5. Output Summary
# ============================================================================

echo "=== Mode A Artifacts ==="
echo ""
echo "Brief (read-only):"
head -10 /tmp/brf_out.json
echo ""
echo "Trend Report (JSON):"
python3 -c "import json; data=json.load(open('/tmp/trend_report.json')); print(json.dumps(data['summary'], indent=2))"
echo ""
echo "Expected TRI Verdict:"
cat /tmp/tri_verdict.json 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Decision: {data.get('verdict', {}).get('decision', 'UNKNOWN')}\")" 2>/dev/null || echo "Decision: REJECT (no authority)"
echo ""
echo "Expected Receipt:"
cat /tmp/receipt.json 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Decision: {data.get('receipt', {}).get('decision', 'UNKNOWN')} | Mutation Allowed: {data.get('receipt', {}).get('world_mutation_allowed', False)}\")" 2>/dev/null || echo "Decision: REJECT | Mutation Allowed: false"
echo ""
echo "=== End Mode A Emulation Loop ==="
