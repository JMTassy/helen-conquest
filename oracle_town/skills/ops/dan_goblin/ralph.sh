#!/usr/bin/env bash
# ralph.sh — HELEN_DAN epoch contract runner
# NON-SOVEREIGN. DAN_GOBLIN is a receipt-bound executor. Not a planner. Not a canon editor.
#
# Usage:
#   ./ralph.sh [--dry-run] [--story HD-NNN]
#
# One epoch = one story. Ralph picks the highest-priority todo, runs DAN, writes receipt.
# If no story is specified, Ralph selects by priority=min(status=todo).

set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOT_ROOT="$(cd "${SKILL_ROOT}/../../../.." && pwd)"
PRD_FILE="${SKILL_ROOT}/prd.json"
RECEIPTS_DIR="${SKILL_ROOT}/receipts"
PROGRESS_FILE="${SKILL_ROOT}/scratch/progress.txt"
DRY_RUN=false
STORY_ID=""

# ── arg parsing ───────────────────────────────────────────────────────────────

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true ;;
    --story)   shift; STORY_ID="${1:-}" ;;
    --story=*) STORY_ID="${arg#--story=}" ;;
  esac
done

# ── preflight ─────────────────────────────────────────────────────────────────

echo "=== RALPH EPOCH START ==="
echo "SOT  : ${SOT_ROOT}"
echo "HEAD : $(git -C "${SOT_ROOT}" rev-parse HEAD 2>/dev/null || echo 'not-a-repo')"
echo "DIRTY: $(git -C "${SOT_ROOT}" status --porcelain 2>/dev/null | wc -l | tr -d ' ') files"
echo "DRY  : ${DRY_RUN}"
echo ""

if [[ ! -f "${PRD_FILE}" ]]; then
  echo "ERROR: prd.json not found at ${PRD_FILE}" >&2
  exit 1
fi

mkdir -p "${RECEIPTS_DIR}" "$(dirname "${PROGRESS_FILE}")"

# ── story selection ───────────────────────────────────────────────────────────

if [[ -z "${STORY_ID}" ]]; then
  # Select highest priority (lowest number) todo story
  STORY_ID="$(python3 -c "
import json, sys
stories = json.load(open('${PRD_FILE}'))
todos = [s for s in stories if s.get('status') == 'todo']
if not todos:
    print('NONE')
    sys.exit(0)
best = sorted(todos, key=lambda s: s['priority'])[0]
print(best['id'])
")"
fi

if [[ "${STORY_ID}" == "NONE" || -z "${STORY_ID}" ]]; then
  echo "No todo stories found in prd.json. Nothing to do."
  exit 0
fi

echo "STORY: ${STORY_ID}"
echo ""

# ── epoch ID ──────────────────────────────────────────────────────────────────

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SESSION_SALT="ralph-$$-${RANDOM}"
EPOCH_ID="$(echo -n "${STORY_ID}:${TIMESTAMP}:${SESSION_SALT}" | sha256sum | cut -c1-12)"
RECEIPT_FILE="${RECEIPTS_DIR}/${STORY_ID}_${EPOCH_ID}.json"

echo "EPOCH: ${EPOCH_ID}"
echo "TIME : ${TIMESTAMP}"
echo ""

# ── mark in_progress ──────────────────────────────────────────────────────────

if [[ "${DRY_RUN}" == "false" ]]; then
  python3 -c "
import json
stories = json.load(open('${PRD_FILE}'))
for s in stories:
    if s['id'] == '${STORY_ID}':
        s['status'] = 'in_progress'
        s['epoch_owner'] = '${EPOCH_ID}'
with open('${PRD_FILE}', 'w') as f:
    json.dump(stories, f, indent=2)
print('  marked ${STORY_ID} in_progress')
"
fi

# ── DAN_GOBLIN work phase ─────────────────────────────────────────────────────
# Ralph calls the work; DAN_GOBLIN is Claude Code running in this shell.
# Ralph does not implement — Ralph orchestrates.
# Actual implementation happens in Claude Code session driven by DAN_GOBLIN.md.

echo "=== DAN_GOBLIN WORK PHASE ==="
echo "Read DAN_GOBLIN.md and prd.json. Implement story ${STORY_ID}."
echo "When done, run tests and call: ralph.sh --close ${STORY_ID} GREEN|FAILED"
echo ""

# ── close function (called after work phase) ──────────────────────────────────

ralph_close() {
  local story="$1"
  local outcome="$2"   # GREEN | FAILED
  local failure_type="${3:-null}"

  echo "=== RALPH CLOSE: ${story} ${outcome} ==="

  # Collect artifact manifest
  ARTIFACTS="[]"
  if [[ -d "${SKILL_ROOT}/artifacts" ]]; then
    ARTIFACTS="$(find "${SKILL_ROOT}/artifacts" -type f | sort | python3 -c "
import sys, json, hashlib, pathlib
paths = [l.strip() for l in sys.stdin if l.strip()]
manifest = []
for p in paths:
    digest = hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    manifest.append({'path': p, 'sha256': digest})
print(json.dumps(manifest))
")"
  fi

  # Test report (read from pytest last run if available)
  TEST_CMD="${SOT_ROOT}/.venv/bin/pytest experiments/ -q --tb=no 2>/dev/null"
  TEST_OUT="$(${TEST_CMD} 2>&1 | tail -3 || true)"
  PASSED="$(echo "${TEST_OUT}" | grep -oP '\d+(?= passed)' || echo 0)"
  FAILED_CT="$(echo "${TEST_OUT}" | grep -oP '\d+(?= failed)' || echo 0)"
  TOTAL="$(( PASSED + FAILED_CT ))"

  HAL_VERDICT="FAIL"
  [[ "${outcome}" == "GREEN" ]] && HAL_VERDICT="PASS"

  # Write receipt
  FAILURE_FIELD="null"
  [[ "${failure_type}" != "null" ]] && FAILURE_FIELD="\"${failure_type}\""

  python3 - <<PYEOF
import json, hashlib, datetime

receipt = {
    "schema": "DAN_GOBLIN_RECEIPT_V0",
    "story_id": "${story}",
    "epoch_id": "${EPOCH_ID}",
    "timestamp_utc": "${TIMESTAMP}",
    "outcome": "${outcome}",
    "failure_type": ${FAILURE_FIELD},
    "artifact_manifest": ${ARTIFACTS},
    "test_report": {
        "passed": ${PASSED},
        "failed": ${FAILED_CT},
        "total": ${TOTAL},
        "command": "pytest experiments/ -q --tb=no",
        "stdout_tail": """${TEST_OUT}"""
    },
    "hal_verdict": "${HAL_VERDICT}",
    "hal_notes": "",
    "reducer_decision": None,
    "content_hash": ""
}

# Compute content_hash
payload = {k: v for k, v in receipt.items() if k != "content_hash"}
canon = json.dumps(payload, sort_keys=True, ensure_ascii=True)
receipt["content_hash"] = hashlib.sha256(canon.encode()).hexdigest()

with open("${RECEIPT_FILE}", "w") as f:
    json.dump(receipt, f, indent=2)
print(f"Receipt written: ${RECEIPT_FILE}")
PYEOF

  # Update prd.json story status
  NEW_STATUS="done"
  [[ "${outcome}" == "FAILED" ]] && NEW_STATUS="failed"

  python3 -c "
import json
stories = json.load(open('${PRD_FILE}'))
for s in stories:
    if s['id'] == '${story}':
        s['status'] = '${NEW_STATUS}'
        s['epoch_owner'] = None
with open('${PRD_FILE}', 'w') as f:
    json.dump(stories, f, indent=2)
print('  updated ${story} -> ${NEW_STATUS}')
"

  # Append to progress log
  echo "[${TIMESTAMP}] ${story} ${outcome} epoch=${EPOCH_ID} receipt=${RECEIPT_FILE}" \
    >> "${PROGRESS_FILE}"

  if [[ "${outcome}" == "GREEN" && "${DRY_RUN}" == "false" ]]; then
    echo "  GREEN — commit is authorised. DAN should: git add + git commit."
  else
    echo "  FAILED — no commit. Failure receipt written. Story reset to todo on next epoch."
    python3 -c "
import json
stories = json.load(open('${PRD_FILE}'))
for s in stories:
    if s['id'] == '${story}':
        s['status'] = 'todo'
with open('${PRD_FILE}', 'w') as f:
    json.dump(stories, f, indent=2)
"
  fi

  echo "=== RALPH EPOCH END ==="
}

# Expose close function if called with --close
if [[ "${1:-}" == "--close" ]]; then
  ralph_close "${2}" "${3}" "${4:-null}"
fi
