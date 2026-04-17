#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Street1 Dialog Runner

Core execution engine:
- Parse two-block [HER]/[HAL] format
- Validate HAL against schema
- Append events to ledger.ndjson
- Live witness injection
- HER/HAL moment detection
- Proof artifact emission
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Optional: jsonschema validation (fallback to manual if not available)
try:
    from jsonschema import validate
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# ============================================================================
# CONFIG
# ============================================================================

ROOT = Path("./town")
LEDGER_PATH = ROOT / "ledger.ndjson"
STATE_PATH = ROOT / "state.json"
SCHEMA_PATH = ROOT / "HAL_OUTPUT.schema.json"
ARTIFACT_DIR = ROOT / "artifacts"

K_WINDOW = 8  # rolling window for HER/HAL moment detection

# ============================================================================
# UTILITIES
# ============================================================================

def canonical(obj: Any) -> str:
    """Deterministic canonical JSON (sorted keys, no whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(obj: Any) -> str:
    """SHA256 hash of canonical JSON."""
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()

# ============================================================================
# IO
# ============================================================================

def load_ledger() -> List[Dict[str, Any]]:
    """Load ledger from NDJSON file."""
    if not LEDGER_PATH.exists():
        return []
    events = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events

def append_ledger(event: Dict[str, Any]) -> None:
    """Append event to ledger (append-only)."""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(canonical(event) + "\n")

def load_state() -> Dict[str, Any]:
    """Load state from JSON file."""
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))

def save_state(state: Dict[str, Any]) -> None:
    """Save state to JSON file."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(canonical(state), encoding="utf-8")

def load_schema() -> Dict[str, Any]:
    """Load HAL output schema."""
    if not SCHEMA_PATH.exists():
        return {}
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

# ============================================================================
# FORMAT PARSING
# ============================================================================

def parse_two_block(text: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse two-block format: [HER]...[HAL]...

    Returns (her_text, hal_json)
    """
    pattern = r"\[HER\]\n(.*?)\n\n\[HAL\]\n(.*)"
    match = re.fullmatch(pattern, text.strip(), re.DOTALL)

    if not match:
        raise ValueError(f"Invalid two-block format. Expected:\n[HER]\n<text>\n\n[HAL]\n<json>")

    her_text = match.group(1).strip()
    hal_json_str = match.group(2).strip()

    try:
        hal_json = json.loads(hal_json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"HAL JSON parse error: {e}")

    return her_text, hal_json

# ============================================================================
# VALIDATION
# ============================================================================

def validate_hal(hal: Dict[str, Any]) -> None:
    """Validate HAL output against schema (manual or jsonschema)."""
    # Manual validation (minimal)
    required_fields = ["verdict", "reasons", "required_fixes", "state_patch"]
    for field in required_fields:
        if field not in hal:
            raise ValueError(f"Missing required HAL field: {field}")

    # Check verdict is valid
    if hal.get("verdict") not in ["PASS", "WARN", "BLOCK"]:
        raise ValueError(f"Invalid verdict: {hal.get('verdict')}")

    # Check reasons is list
    if not isinstance(hal.get("reasons"), list):
        raise ValueError("reasons must be a list")

    # Check required_fixes is list
    if not isinstance(hal.get("required_fixes"), list):
        raise ValueError("required_fixes must be a list")

    # Check state_patch is dict
    if not isinstance(hal.get("state_patch"), dict):
        raise ValueError("state_patch must be a dict")

    # Optional: use jsonschema if available
    if HAS_JSONSCHEMA:
        schema = load_schema()
        if schema:
            try:
                validate(instance=hal, schema=schema)
            except Exception as e:
                raise ValueError(f"Schema validation failed: {e}")

# ============================================================================
# LIVE WITNESS INJECTION
# ============================================================================

def inject_witness(ledger: List[Dict[str, Any]], turn: int) -> None:
    """
    Live witness injection (LRI).
    Detect contradictions in recent events and add witness note.
    """
    if len(ledger) < 2:
        return

    # Check for policy conflicts in last 3 events
    recent = ledger[-3:]

    for i in range(1, len(recent)):
        prev_ev = recent[i - 1]
        curr_ev = recent[i]

        if (prev_ev.get("type") == "verdict" and
            curr_ev.get("type") == "proposal"):

            if prev_ev.get("verdict") == "BLOCK":
                append_ledger({
                    "type": "witness_note",
                    "actor": "helen",
                    "turn": turn,
                    "note": f"Responding to constraint: {prev_ev.get('reasons', [])}",
                })
                return

# ============================================================================
# HER/HAL MOMENT DETECTION
# ============================================================================

def detect_her_hal_moment(ledger: List[Dict[str, Any]]) -> bool:
    """
    Detect HER/HAL moment: convergence pattern where both modules stabilize.

    Criteria:
    - At least 2 BLOCK verdicts in window
    - At least 2 revisions in window
    - Pattern: proposal→verdict→revision repeats ≥2 times
    """
    if len(ledger) < K_WINDOW:
        return False

    window = ledger[-K_WINDOW:]

    # Count verdicts and revisions
    verdicts = [e for e in window if e.get("type") == "verdict" and e.get("verdict") == "BLOCK"]
    revisions = [e for e in window if e.get("type") == "revision"]

    if len(verdicts) < 2 or len(revisions) < 2:
        return False

    # Check for proposal→verdict→revision cycle pattern
    pattern = [e.get("type") for e in window]

    cycle_count = 0
    for i in range(len(pattern) - 2):
        if pattern[i:i+3] == ["proposal", "verdict", "revision"]:
            cycle_count += 1

    return cycle_count >= 2

# ============================================================================
# PROOF ARTIFACTS
# ============================================================================

def emit_proof_artifacts(turn: int) -> Dict[str, Any]:
    """Emit proof artifacts (receipt, certificates)."""
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    ledger = load_ledger()
    state = load_state()

    receipt_hash = sha256_hex(ledger)
    state_hash = sha256_hex(state)

    certificates = {
        "run_id": "street1:seed:0001",
        "ledger_hash": f"sha256:{receipt_hash}",
        "state_hash": f"sha256:{state_hash}",
        "ledger_length": len(ledger),
        "moment_detected": detect_her_hal_moment(ledger),
    }

    (ARTIFACT_DIR / "receipt.json").write_text(canonical(certificates), encoding="utf-8")

    return certificates

# ============================================================================
# TERMINATION LOGIC
# ============================================================================

def should_terminate(hal: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Determine if session should terminate.

    Returns (terminate, outcome)
    """
    verdict = hal.get("verdict")

    if verdict == "PASS":
        return True, "SHIP"

    if verdict == "BLOCK" and "TERMINATION_REQUIRED" in hal.get("reasons", []):
        return True, "ABORT"

    return False, None

# ============================================================================
# CORE TURN EXECUTION
# ============================================================================

def run_turn(raw_output: str) -> None:
    """
    Execute one session turn.

    Input: raw two-block output from stdin/inbox
    Side effects:
      - Appends events to ledger.ndjson
      - Injects witness notes
      - Detects HER/HAL moment
      - Emits proof artifacts on termination
    """
    ledger = load_ledger()
    turn = len(ledger) + 1

    # Parse and validate
    try:
        her_text, hal = parse_two_block(raw_output)
        validate_hal(hal)
    except Exception as e:
        print(f"ERROR Turn {turn}: {e}")
        raise

    proposal_id = f"p:{turn}"

    # Append proposal
    append_ledger({
        "type": "proposal",
        "actor": "helen",
        "turn": turn,
        "proposal_id": proposal_id,
        "intent": her_text[:240],
    })

    # Append verdict
    append_ledger({
        "type": "verdict",
        "actor": "mayor",
        "turn": turn,
        "target": proposal_id,
        "verdict": hal.get("verdict"),
        "reasons": hal.get("reasons", []),
        "required_fixes": hal.get("required_fixes", []),
    })

    # Apply state patch (if provided)
    if hal.get("state_patch"):
        state = load_state()
        state.update(hal["state_patch"])
        save_state(state)

    # Apply ledger append (if provided, e.g., revision)
    if hal.get("ledger_append"):
        append_ledger(hal["ledger_append"])

    # Reload ledger for witness injection
    ledger = load_ledger()

    # Live witness injection
    inject_witness(ledger, turn)

    # Reload ledger for moment detection
    ledger = load_ledger()

    # Detect HER/HAL moment
    if detect_her_hal_moment(ledger):
        append_ledger({
            "type": "milestone",
            "actor": "mayor",
            "turn": turn,
            "name": "her_hal_moment",
        })

    # Check termination
    should_term, outcome = should_terminate(hal)
    if should_term:
        certificates = emit_proof_artifacts(turn)
        append_ledger({
            "type": "termination",
            "actor": "mayor",
            "turn": turn,
            "outcome": outcome,
            "proof_hash": certificates["ledger_hash"],
        })

    print(f"✅ Turn {turn}: {hal.get('verdict')} | {len(ledger)} events")

# ============================================================================
# UTILITIES FOR TESTING
# ============================================================================

def replay_check() -> str:
    """Compute deterministic hash of entire ledger."""
    ledger = load_ledger()
    return sha256_hex(ledger)

if __name__ == "__main__":
    import sys
    raw = sys.stdin.read()
    run_turn(raw)
