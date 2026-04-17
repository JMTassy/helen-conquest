#!/usr/bin/env bash
# Street1 REAL Determinism Sweep — 100 seeds × 2 fresh runs
# Uses actual street1-server.cjs + cli_emulate_street1.cjs pipeline
# Verifies: same seed → same event sequence → same receipt_sha

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNS_DIR="$ROOT/runs/street1"
OUT="$RUNS_DIR/determinism_sweep_real.jsonl"

mkdir -p "$RUNS_DIR"
: > "$OUT"

PORT="${PORT:-3001}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Street1 REAL Determinism Sweep — 100 seeds × 2 runs       ║"
echo "║  (actual server pipeline, not smoke test)                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Writing results to: $OUT"
echo ""

PASS_COUNT=0
FAIL_COUNT=0

start_server() {
  node "$ROOT/street1-server.cjs" >/tmp/street1_server.log 2>&1 &
  echo $!
}

stop_server() {
  local pid="$1"
  if ps -p "$pid" >/dev/null 2>&1; then
    kill -INT "$pid" >/dev/null 2>&1 || true
    sleep 0.2
    kill -9 "$pid" >/dev/null 2>&1 || true
  fi
  wait "$pid" >/dev/null 2>&1 || true
}

get_receipt_sha() {
  python3 - <<'PY'
import json, pathlib
try:
  p = pathlib.Path("runs/street1/summary.json")
  if not p.exists():
    print("MISSING")
  else:
    j = json.loads(p.read_text(encoding="utf-8"))
    sha = j.get("receipt_sha")
    if sha is None:
      print("MISSING")
    else:
      print(sha)
except Exception as e:
  print("ERROR")
PY
}

one_run() {
  local seed="$1"

  # Clean up from previous run (use > to truncate, not just rm)
  : > "$RUNS_DIR/events.ndjson"
  rm -f "$RUNS_DIR/summary.json" 2>/dev/null || true

  # Give filesystem time to sync
  sleep 0.2

  # Start fresh server
  local pid
  pid="$(start_server)"

  # Give server time to bind on port
  sleep 0.5

  # Run CLI test with seed injected (no timeout command on macOS, so just run and catch errors)
  SEED="$seed" STREET1_WS="ws://localhost:$PORT" node "$ROOT/cli_emulate_street1.cjs" >/tmp/street1_cli.log 2>&1
  CLI_EXIT=$?

  if [ $CLI_EXIT -ne 0 ]; then
    echo "[WARN] CLI run failed for seed=$seed (exit code: $CLI_EXIT)"
    cat /tmp/street1_cli.log >> /tmp/street1_sweep_errors.log
    stop_server "$pid"
    echo "ERROR"
    return
  fi

  # Wait for server to write END event to ledger
  sleep 1

  # Seal run → produces summary.json with receipt_sha
  if ! bash "$ROOT/scripts/street1_complete.sh" >/tmp/street1_complete.log 2>&1; then
    echo "[WARN] Seal failed for seed=$seed"
    stop_server "$pid"
    echo "ERROR"
    return
  fi

  # Extract receipt_sha from summary.json
  local sha
  sha="$(get_receipt_sha)"

  # Stop server
  stop_server "$pid"

  echo "$sha"
}

# ─────────────────────────────────────────────────────────────────────────
# Main sweep loop
# ─────────────────────────────────────────────────────────────────────────

for s in $(seq 1 100); do
  printf "[%3d/100] seed=%d … " "$s" "$s"

  # Run A
  sha_a="$(one_run "$s")"

  if [[ "$sha_a" == "ERROR" || "$sha_a" == "MISSING" ]]; then
    echo "❌ (A failed)"
    ((FAIL_COUNT++))
    printf '{"seed":%d,"receipt_sha_a":null,"receipt_sha_b":null,"match":false,"error":"run A failed"}\n' "$s" >> "$OUT"
    continue
  fi

  # Run B
  sha_b="$(one_run "$s")"

  if [[ "$sha_b" == "ERROR" || "$sha_b" == "MISSING" ]]; then
    echo "❌ (B failed)"
    ((FAIL_COUNT++))
    printf '{"seed":%d,"receipt_sha_a":null,"receipt_sha_b":null,"match":false,"error":"run B failed"}\n' "$s" >> "$OUT"
    continue
  fi

  # Compare
  if [[ "$sha_a" == "$sha_b" ]]; then
    match="true"
    ((PASS_COUNT++))
    echo "✅ $sha_a"
  else
    match="false"
    ((FAIL_COUNT++))
    echo "❌ MISMATCH"
    echo "  A: $sha_a"
    echo "  B: $sha_b"
  fi

  # Log result (use printf for safe JSON)
  {
    printf '{"seed":%d,"receipt_sha_a":"%s","receipt_sha_b":"%s","match":%s}\n' \
      "$s" "$sha_a" "$sha_b" "$([[ "$match" == "true" ]] && echo "true" || echo "false")"
  } >> "$OUT"

  # Fail fast
  if [[ "$match" != "true" ]]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  ❌ DETERMINISM FAILURE at seed=$s                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo "A: $sha_a"
    echo "B: $sha_b"
    echo "Results so far: $OUT"
    exit 1
  fi
done

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ DETERMINISM VERIFIED: $PASS_COUNT/100 seeds                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Results: $OUT"
echo ""
echo "Summary:"
echo "  Passed:  $PASS_COUNT"
echo "  Failed:  $FAIL_COUNT"
