#!/usr/bin/env bash
# tools/helen_verify.sh
#
# HELEN's verify command.
#
#   "Accuracy is not declared. Accuracy is attacked until it survives."
#
# When an agent (or a human) says a piece of work is "done," this command
# is the attack surface. It composes existing verification layers into a
# single PASS/FAIL gate and emits a typed receipt.
#
# Layers it runs (in order, each independent):
#
#   1. DIFF        — git diff --stat against HEAD (what's claimed to have changed)
#   2. PYTEST      — focused test slice (red/green)
#   3. SUBSTRATE   — tools/accept_payload_meta.sh (ledger validators) IFF ledger present
#   4. RALPH       — tools/ralph_emit_artifacts.py emits typed evidence from pytest output
#   5. CROSS-MODEL — HOOK (not auto-executed; operator runs DeepSeek/Codex/etc. manually)
#
# Exit code:
#   0   — all RUNNABLE gates passed (cross-model is informational, never blocks)
#   ≥1  — at least one gate failed; receipt at $RECEIPT_PATH says which
#
# Usage:
#   bash tools/helen_verify.sh
#   bash tools/helen_verify.sh --pytest-args "-q tests/test_hash_chain_payload_hash.py"
#   bash tools/helen_verify.sh --ledger town/ledger_v1.ndjson
#   bash tools/helen_verify.sh --skip-pytest
#   bash tools/helen_verify.sh --skip-substrate
#   bash tools/helen_verify.sh --epoch-id <id>     # name the verification epoch
#
# Output:
#   .helen/verify/<EPOCH_ID>/verify_receipt.json   (typed PASS/FAIL receipt)
#   .helen/verify/<EPOCH_ID>/diff.txt              (captured git diff --stat)
#   .helen/verify/<EPOCH_ID>/pytest.txt            (captured pytest output)
#   .helen/verify/<EPOCH_ID>/substrate.txt         (captured accept_payload_meta output)
#
# This command is NON_SOVEREIGN. It does not append the ledger. It does
# not sign anything. It does not promote anything to canon. It produces
# evidence for a MAYOR review, not the verdict itself.

set -uo pipefail

# ── Defaults & arg parsing ───────────────────────────────────────────────
PYTEST_ARGS=""
LEDGER_PATH=""
SKIP_PYTEST=0
SKIP_SUBSTRATE=0
EPOCH_ID="V_$(date +%Y%m%d_%H%M%S)"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --pytest-args) PYTEST_ARGS="$2"; shift 2 ;;
        --ledger) LEDGER_PATH="$2"; shift 2 ;;
        --skip-pytest) SKIP_PYTEST=1; shift ;;
        --skip-substrate) SKIP_SUBSTRATE=1; shift ;;
        --epoch-id) EPOCH_ID="$2"; shift 2 ;;
        --help|-h)
            sed -n '1,40p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "[helen_verify] unknown arg: $1" >&2; exit 2 ;;
    esac
done

OUTDIR="$REPO_ROOT/.helen/verify/$EPOCH_ID"
mkdir -p "$OUTDIR"
RECEIPT_PATH="$OUTDIR/verify_receipt.json"

# Default ledger if not specified and the canonical one exists
if [ -z "$LEDGER_PATH" ] && [ -f "$REPO_ROOT/town/ledger_v1.ndjson" ]; then
    LEDGER_PATH="town/ledger_v1.ndjson"
elif [ -z "$LEDGER_PATH" ] && [ -f "$REPO_ROOT/town/ledger.ndjson" ]; then
    LEDGER_PATH="town/ledger.ndjson"
fi

# Track per-gate outcome
DIFF_STATUS="SKIP"
PYTEST_STATUS="SKIP"
SUBSTRATE_STATUS="SKIP"
RALPH_STATUS="SKIP"
OVERALL=0

banner() {
    echo ""
    echo "================================================================================"
    echo "$1"
    echo "================================================================================"
}

# ── Gate 1: DIFF ──────────────────────────────────────────────────────────
banner "GATE 1 — DIFF (what is claimed to have changed)"
DIFF_FILE="$OUTDIR/diff.txt"
if (cd "$REPO_ROOT" && git diff --stat HEAD) > "$DIFF_FILE" 2>&1; then
    cat "$DIFF_FILE"
    if [ -s "$DIFF_FILE" ]; then
        DIFF_STATUS="PASS_WITH_CHANGES"
    else
        DIFF_STATUS="PASS_NO_CHANGES"
    fi
else
    DIFF_STATUS="FAIL"
    OVERALL=1
fi

# ── Gate 2: PYTEST ────────────────────────────────────────────────────────
banner "GATE 2 — PYTEST (red/green)"
PYTEST_FILE="$OUTDIR/pytest.txt"
if [ "$SKIP_PYTEST" -eq 1 ]; then
    echo "[SKIP] --skip-pytest set"
    PYTEST_STATUS="SKIP"
elif ! command -v pytest >/dev/null 2>&1 && ! python3 -c "import pytest" >/dev/null 2>&1; then
    echo "[SKIP] pytest not installed"
    PYTEST_STATUS="SKIP_NO_PYTEST"
else
    if [ -z "$PYTEST_ARGS" ]; then
        PYTEST_ARGS="-q"
    fi
    if (cd "$REPO_ROOT" && python3 -m pytest $PYTEST_ARGS) > "$PYTEST_FILE" 2>&1; then
        PYTEST_STATUS="PASS"
    else
        PYTEST_STATUS="FAIL"
        OVERALL=1
    fi
    tail -30 "$PYTEST_FILE"
fi

# ── Gate 3: SUBSTRATE (ledger validators via accept_payload_meta.sh) ─────
banner "GATE 3 — SUBSTRATE (ledger validators)"
SUBSTRATE_FILE="$OUTDIR/substrate.txt"
if [ "$SKIP_SUBSTRATE" -eq 1 ]; then
    echo "[SKIP] --skip-substrate set"
    SUBSTRATE_STATUS="SKIP"
elif [ -z "$LEDGER_PATH" ] || [ ! -f "$REPO_ROOT/$LEDGER_PATH" ]; then
    echo "[SKIP] no ledger found at: ${LEDGER_PATH:-<none>}"
    SUBSTRATE_STATUS="SKIP_NO_LEDGER"
elif [ ! -x "$REPO_ROOT/tools/accept_payload_meta.sh" ]; then
    echo "[SKIP] tools/accept_payload_meta.sh not executable"
    SUBSTRATE_STATUS="SKIP_NO_GATE"
else
    if (cd "$REPO_ROOT" && bash tools/accept_payload_meta.sh "$LEDGER_PATH") > "$SUBSTRATE_FILE" 2>&1; then
        SUBSTRATE_STATUS="PASS"
    else
        SUBSTRATE_STATUS="FAIL"
        OVERALL=1
    fi
    tail -30 "$SUBSTRATE_FILE"
fi

# ── Gate 4: RALPH (emit typed evidence from pytest output) ───────────────
banner "GATE 4 — RALPH (typed evidence from pytest output)"
if [ -f "$REPO_ROOT/tools/ralph_emit_artifacts.py" ] && [ -f "$PYTEST_FILE" ]; then
    # Stage focused/full test files in a way the emitter expects
    cp "$PYTEST_FILE" "$OUTDIR/focused_tests.txt"
    cp "$PYTEST_FILE" "$OUTDIR/full_tests.txt"
    if python3 "$REPO_ROOT/tools/ralph_emit_artifacts.py" \
        --epoch-id "$EPOCH_ID" --logdir "$OUTDIR" > "$OUTDIR/ralph_summary.json" 2>&1; then
        RALPH_STATUS="PASS"
        echo "[PASS] artifacts at $OUTDIR/artifacts/"
        ls "$OUTDIR/artifacts/" 2>/dev/null
    else
        RALPH_STATUS="FAIL"
        cat "$OUTDIR/ralph_summary.json"
        OVERALL=1
    fi
else
    echo "[SKIP] ralph emitter or pytest output missing"
    RALPH_STATUS="SKIP"
fi

# ── Gate 5: CROSS-MODEL (HOOK — operator-invoked) ────────────────────────
banner "GATE 5 — CROSS-MODEL CRITIQUE (operator hook, not auto-run)"
cat <<EOF
[HOOK] Cross-model critique is intentionally NOT auto-executed.
       Run one of the following manually if a second-model attack is
       part of your acceptance criterion:

       # Adversarial flaw search:
       cat $DIFF_FILE | <your-deepseek-or-other-cli> --prompt 'Find flaws'

       # Independent re-implementation check:
       cat $DIFF_FILE | <claude-cli> --prompt 'Summarize and challenge'

       Append the second model's verdict to:
       $OUTDIR/cross_model_critique.md

       Then re-run helen_verify with --skip-pytest --skip-substrate to
       update the receipt, or accept this as advisory.
EOF

# ── Receipt ──────────────────────────────────────────────────────────────
banner "VERIFICATION RECEIPT"

GIT_SHA="$(cd "$REPO_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')"
GIT_BRANCH="$(cd "$REPO_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"

cat > "$RECEIPT_PATH" <<EOF
{
  "schema": "VERIFICATION_RECEIPT_V1",
  "authority": "NON_SOVEREIGN",
  "canon": "NO_SHIP",
  "epoch_id": "$EPOCH_ID",
  "git": {
    "sha": "$GIT_SHA",
    "branch": "$GIT_BRANCH"
  },
  "ledger_path": "${LEDGER_PATH:-null}",
  "gates": {
    "diff": "$DIFF_STATUS",
    "pytest": "$PYTEST_STATUS",
    "substrate": "$SUBSTRATE_STATUS",
    "ralph": "$RALPH_STATUS",
    "cross_model": "HOOK_NOT_AUTO_RUN"
  },
  "overall": "$( [ $OVERALL -eq 0 ] && echo PASS || echo FAIL )",
  "ledger_appends": 0,
  "kernel_writes": 0,
  "canon_mutations": 0,
  "captured_files": {
    "diff": "diff.txt",
    "pytest": "pytest.txt",
    "substrate": "substrate.txt",
    "artifacts_dir": "artifacts/"
  }
}
EOF

echo ""
cat "$RECEIPT_PATH"
echo ""
echo "[helen_verify] receipt: $RECEIPT_PATH"
echo "[helen_verify] overall: $( [ $OVERALL -eq 0 ] && echo 'PASS — survived the attack' || echo 'FAIL — at least one gate red' )"

# Doctrine line, every run
echo ""
echo "    Accuracy is not declared. Accuracy is attacked until it survives."
echo ""

exit $OVERALL
