#!/bin/bash

#
# run_dialog_box.sh
#
# Deterministic dialogue box runner.
#
# This script implements the persistent, file-based dialogue loop:
#   1. Read user input (or interactive prompt)
#   2. Build context prompt (state + history)
#   3. Call Claude Haiku (or LLM of choice)
#   4. Parse two-channel response
#   5. Append events to dialogue.ndjson
#   6. Update dialog_state.json
#   7. Check for HER/AL moment
#   8. Repeat
#
# All state lives on disk. Restart anytime.
#

set -euo pipefail

# ──────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIALOG_DIR="${SCRIPT_DIR}"
# Prefer scaffold venv Python (required for SCF / helen_os imports)
SCAFFOLD_PYTHON="$(dirname "${SCRIPT_DIR}")/helen_os_scaffold/.venv/bin/python3"
if [ -z "${PYTHON:-}" ]; then
    if [ -x "${SCAFFOLD_PYTHON}" ]; then
        PYTHON="${SCAFFOLD_PYTHON}"
    else
        PYTHON="python3"
    fi
fi
LLM_MODEL="${LLM_MODEL:-claude-3-5-haiku-20241022}"
LLM_MAX_TOKENS="${LLM_MAX_TOKENS:-1000}"

STATE_FILE="${DIALOG_DIR}/dialog_state.json"
LOG_FILE="${DIALOG_DIR}/dialog.ndjson"
INBOX_FILE="${DIALOG_DIR}/inbox_user.txt"
OUTBOX_FILE="${DIALOG_DIR}/outbox_helen.txt"

# ──────────────────────────────────────────────────────────────────
# Functions
# ──────────────────────────────────────────────────────────────────

log_info() {
    echo "[INFO] $*" >&2
}

log_error() {
    echo "[ERROR] $*" >&2
}

init_dialogue_dir() {
    mkdir -p "${DIALOG_DIR}"
    log_info "Dialogue directory: ${DIALOG_DIR}"
}

read_user_input() {
    local prompt="${1:-JM: }"

    if [ -f "${INBOX_FILE}" ]; then
        # Read from inbox_user.txt if it exists
        cat "${INBOX_FILE}"
        rm "${INBOX_FILE}"  # Consume it
    else
        # Interactive prompt
        read -p "$prompt" user_input
        echo "$user_input"
    fi
}

call_lmm() {
    local prompt_file="$1"

    log_info "Calling LLM (${LLM_MODEL})..."

    # This is a placeholder. In production, use:
    #   - Claude API via curl
    #   - anthropic SDK
    #   - Claude Code API wrapper
    #
    # For now, we'll read from a pre-recorded response or use a mock.

    if command -v claude >/dev/null 2>&1; then
        # If Claude Code CLI is available
        claude api call "${LLM_MODEL}" \
            --max-tokens "${LLM_MAX_TOKENS}" \
            --system "You are HELEN, a two-channel dialogue assistant. Always output [HER] and [AL] sections." \
            < "${prompt_file}"
    else
        # Fallback: mock response for testing
        cat <<'EOF'
[HER] I understand. Let me think about this carefully. The pattern you're identifying is important—it shows how we can measure genuine dialogue continuity without claiming consciousness.

[AL]
{
  "decision": "Proceed with dialogue box implementation",
  "checks": ["SCHEMA_VALID", "NO_AUTHORITY_BLEED"],
  "state_update": {"mode": "dyadic_exploring"},
  "verdict": "PASS"
}
EOF
    fi
}

build_prompt() {
    local user_message="$1"

    # Call Python engine to build context-aware prompt
    ${PYTHON} - <<PYTHON_SCRIPT
import json
import sys
sys.path.insert(0, "${DIALOG_DIR}")

from helen_dialog_engine import DialogueEngine
from pathlib import Path

engine = DialogueEngine(Path("${DIALOG_DIR}"))
prompt = engine.build_prompt("""${user_message}""")
print(prompt)
PYTHON_SCRIPT
}

process_turn() {
    local user_message="$1"
    local lmm_response="$2"

    # Call Python engine to process turn
    ${PYTHON} - <<PYTHON_SCRIPT
import json
import sys
sys.path.insert(0, "${DIALOG_DIR}")

from helen_dialog_engine import DialogueEngine
from pathlib import Path

engine = DialogueEngine(Path("${DIALOG_DIR}"))
result = engine.process_turn("""${user_message}""", """${lmm_response}""")

print(json.dumps(result, indent=2))

if result.get("moment_fired"):
    print("\n✨ HER/AL MOMENT DETECTED at turn", result["turn"], "✨")
PYTHON_SCRIPT
}

check_moment() {
    # Run her_al_moment_detector
    ${PYTHON} "${DIALOG_DIR}/her_al_moment_detector.py" "${LOG_FILE}"
}

interactive_loop() {
    log_info "Starting interactive dialogue loop..."
    log_info "Type your messages. Enter empty line to exit."
    log_info ""

    while true; do
        echo ""
        user_input=$(read_user_input "JM: ")

        if [ -z "$user_input" ]; then
            log_info "Exiting dialogue loop."
            break
        fi

        # Build prompt
        log_info "Building context prompt..."
        prompt_text=$(build_prompt "$user_input")

        # Call LMM
        log_info "Calling LMM..."
        lmm_output=$(call_lmm <(echo "$prompt_text"))

        # Process turn
        log_info "Processing turn..."
        result=$(process_turn "$user_input" "$lmm_output")

        # Display result
        echo ""
        echo "========== DIALOGUE STATE =========="
        echo "$result"

        # Display HELEN + MAYOR output
        echo ""
        echo "[OUTBOX]"
        echo "$lmm_output"

        # Save outbox
        echo "$lmm_output" > "${OUTBOX_FILE}"

        echo ""
    done
}

summary() {
    log_info "Dialogue summary:"
    log_info "State file: ${STATE_FILE}"
    log_info "Log file: ${LOG_FILE}"

    if [ -f "${STATE_FILE}" ]; then
        log_info "Current turn: $(jq '.turn' ${STATE_FILE})"
        log_info "Current mode: $(jq -r '.mode' ${STATE_FILE})"
        log_info "HER/AL moment fired: $(jq '.her_al_moment_fired' ${STATE_FILE})"
    fi

    log_info ""
    log_info "To check HER/AL moment detection:"
    log_info "  ${PYTHON} her_al_moment_detector.py dialog.ndjson"
}

# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────

main() {
    init_dialogue_dir

    case "${1:-interactive}" in
        interactive)
            interactive_loop
            ;;
        summary)
            summary
            ;;
        check-moment)
            check_moment
            ;;
        single)
            # Single turn: usage: run_dialog_box.sh single "your message"
            if [ -z "${2:-}" ]; then
                log_error "Usage: $0 single <message>"
                exit 1
            fi

            user_msg="$2"
            log_info "Processing: $user_msg"

            prompt_text=$(build_prompt "$user_msg")
            lmm_output=$(call_lmm <(echo "$prompt_text"))
            result=$(process_turn "$user_msg" "$lmm_output")

            echo ""
            echo "[RESULT]"
            echo "$result"
            ;;
        *)
            log_error "Usage: $0 [interactive|single <msg>|summary|check-moment]"
            exit 1
            ;;
    esac
}

main "$@"
