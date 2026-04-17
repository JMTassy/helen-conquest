#!/usr/bin/env bash
# Acceptance gate: Payload/Meta split + VERDICT/RECEIPT/SEAL substrate
# Runs all six validators. If all pass, substrate is accepted.
#
# Gates:
#   1. Hash chain integrity          (validate_hash_chain.py)
#   2. Turn schema — HAL_VERDICT_V1  (validate_turn_schema.py)    [legacy]
#   3. Meta invariance               (test_meta_invariance.py)
#   4. VERDICT_PAYLOAD_V1 schema     (validate_verdict_payload.py)
#   5. RECEIPT triple-binding        (validate_receipt_linkage.py)
#   6. SEAL_V1 closure               (validate_seal_v1.py)
#
# Usage:
#   bash tools/accept_payload_meta.sh [<ledger.ndjson>]

set -euo pipefail

LEDGER="${1:-town/ledger.ndjson}"

if [ ! -f "$LEDGER" ]; then
    echo "[SKIP] Ledger not found: $LEDGER"
    exit 0
fi

echo "================================================================================"
echo "ACCEPTANCE GATE: Payload/Meta + VERDICT/RECEIPT/SEAL Substrate"
echo "Ledger : $LEDGER"
echo "================================================================================"
echo ""

# ── Gate 1: Hash chain integrity ─────────────────────────────────────────────
echo "Gate 1: Hash chain integrity (HELEN_CUM_V1)"
python3 tools/validate_hash_chain.py "$LEDGER" || {
    echo "[FAIL] Gate 1: Hash chain validation failed"
    exit 1
}
echo ""

# ── Gate 2: Turn schema (HAL_VERDICT_V1 — legacy) ────────────────────────────
echo "Gate 2: Turn schema validation (HAL_VERDICT_V1 legacy events)"
python3 tools/validate_turn_schema.py "$LEDGER" || {
    echo "[FAIL] Gate 2: Turn schema validation failed"
    exit 1
}
echo ""

# ── Gate 3: Meta invariance ───────────────────────────────────────────────────
echo "Gate 3: Meta invariance (floats banned, reasons sorted)"
python3 tools/test_meta_invariance.py "$LEDGER" || {
    echo "[FAIL] Gate 3: Meta invariance check failed"
    exit 1
}
echo ""

# ── Gate 4: VERDICT_PAYLOAD_V1 schema ────────────────────────────────────────
echo "Gate 4: VERDICT_PAYLOAD_V1 schema (sorted codes, valid anchors)"
python3 tools/validate_verdict_payload.py "$LEDGER" || {
    echo "[FAIL] Gate 4: VERDICT payload schema validation failed"
    exit 1
}
echo ""

# ── Gate 5: RECEIPT triple-binding + NO RECEIPT = NO SHIP ────────────────────
echo "Gate 5: RECEIPT triple-binding (verdict_id + payload_hash + cum_hash)"
python3 tools/validate_receipt_linkage.py "$LEDGER" || {
    echo "[FAIL] Gate 5: RECEIPT linkage validation failed"
    exit 1
}
echo ""

# ── Gate 6: SEAL_V1 closure ───────────────────────────────────────────────────
echo "Gate 6: SEAL_V1 closure (env_hash, ledger_length, identity_hash, mayor_signature)"
python3 tools/validate_seal_v1.py "$LEDGER" || {
    echo "[FAIL] Gate 6: SEAL validation failed"
    exit 1
}
echo ""

echo "================================================================================"
echo "[PASS] All 6 acceptance gates passed"
echo "[PASS] Payload/Meta + VERDICT/RECEIPT/SEAL substrate accepted"
echo "================================================================================"
