#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Street1 HER Generator Stub (Test Mode)

Deterministic synthetic two-block output generator.
Feeds [HER] + [HAL] blocks into inbox.txt for session orchestrator to consume.

Seeded RNG (Mulberry32 equivalent in Python) ensures:
- Same seed → identical sequence of proposals
- No timestamps
- No randomness outside deterministic selection
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

# ============================================================================
# CONFIG
# ============================================================================

ROOT = Path("./town")
INBOX_PATH = ROOT / "inbox.txt"
LEDGER_PATH = ROOT / "ledger.ndjson"
SEED = "street1:seed:0001"

# Deterministic RNG (linear congruential, seeded)
class SeededRandom:
    """Deterministic pseudo-random generator (seeded)."""
    def __init__(self, seed_str: str):
        # Convert seed string to integer
        self.state = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % (2**32)

    def next_int(self, max_val: int) -> int:
        """Return next integer in [0, max_val)."""
        self.state = (self.state * 1103515245 + 12345) % (2**32)
        return (self.state // 65536) % max_val

# ============================================================================
# PROPOSAL TEMPLATES
# ============================================================================

HER_TEMPLATES = [
    "Increase NPC interaction tracking to detect emergent behavior patterns.",
    "Verify policy activation log for consistency and completeness.",
    "Check if state mutations align with approved policy deltas.",
    "Propose constraint amplification: require explicit witness notes on contradictions.",
    "Analyze ledger for any authority-leakage patterns.",
    "Request more detailed HAL certificates for K-gate compliance.",
    "Suggest witness injection at policy decision boundaries.",
]

HAL_VERDICTS = [
    {
        "verdict": "PASS",
        "reasons": ["All K-gates verified", "Ledger coherent"],
        "required_fixes": [],
        "state_patch": {},
    },
    {
        "verdict": "WARN",
        "reasons": ["Policy_award count unusual", "Consider additional witness"],
        "required_fixes": ["Add witness note"],
        "state_patch": {},
    },
    {
        "verdict": "BLOCK",
        "reasons": ["SCHEMA_VIOLATION"],
        "required_fixes": ["Remove timestamp field", "Verify canonical JSON"],
        "state_patch": {},
    },
]

REVISION_INTENTS = [
    "Revised proposal per required_fixes: removed timestamp references.",
    "Complied with HAL constraint: added explicit witness note.",
    "Restructured proposal to maintain canonical form.",
]

# ============================================================================
# GENERATION
# ============================================================================

def generate_her_block(rng: SeededRandom, turn: int) -> str:
    """
    Generate [HER] block (human-readable proposal).
    Deterministic selection from templates.
    """
    idx = rng.next_int(len(HER_TEMPLATES))
    return HER_TEMPLATES[idx]

def generate_hal_block(rng: SeededRandom, turn: int, her_block: str) -> Dict[str, Any]:
    """
    Generate [HAL] block (MAYOR verdict).
    Deterministic selection from verdict templates.

    Logic: if turn is early, more PASS; if mid, mix; if late, may BLOCK.
    """
    # Simple heuristic: early turns mostly PASS, mid has mix, late has BLOCK
    if turn < 5:
        verdict_idx = rng.next_int(2)  # favor PASS
    elif turn < 15:
        verdict_idx = rng.next_int(3)  # full mix
    else:
        verdict_idx = rng.next_int(3)  # mix but allow BLOCK

    verdict_idx = min(verdict_idx, len(HAL_VERDICTS) - 1)
    return dict(HAL_VERDICTS[verdict_idx])

def generate_two_block(rng: SeededRandom, turn: int) -> str:
    """
    Generate full two-block response for given turn.
    Format: [HER]\n<text>\n\n[HAL]\n<json>
    """
    her_text = generate_her_block(rng, turn)
    hal_obj = generate_hal_block(rng, turn, her_text)

    # Format HAL JSON canonically (sorted keys, no whitespace)
    hal_json = json.dumps(hal_obj, sort_keys=True, separators=(",", ":"))

    return f"[HER]\n{her_text}\n\n[HAL]\n{hal_json}"

def generate_revision_block(rng: SeededRandom, turn: int) -> str:
    """
    Generate revision proposal when HAL verdict was BLOCK.
    """
    intent_idx = rng.next_int(len(REVISION_INTENTS))
    revision_text = REVISION_INTENTS[intent_idx]

    # Revised HAL: always PASS after revision
    hal_obj = {
        "verdict": "PASS",
        "reasons": ["Revised proposal complies with constraints"],
        "required_fixes": [],
        "state_patch": {},
        "ledger_append": {
            "type": "revision",
            "actor": "helen",
            "turn": turn,
            "revises": f"p:{turn-1}",
            "new_proposal_id": f"p:{turn}",
            "notes": revision_text,
        }
    }

    hal_json = json.dumps(hal_obj, sort_keys=True, separators=(",", ":"))

    return f"[HER]\n{revision_text}\n\n[HAL]\n{hal_json}"

def is_termination_turn(ledger: List[Dict[str, Any]]) -> bool:
    """Check if session should terminate."""
    if not ledger:
        return False

    # Terminate after N turns with final PASS
    if len(ledger) >= 10:
        recent_verdicts = [e for e in ledger[-3:] if e.get("type") == "verdict"]
        if recent_verdicts and all(v.get("verdict") == "PASS" for v in recent_verdicts):
            return True

    return False

def generate_termination_block() -> str:
    """Generate final termination verdict."""
    hal_obj = {
        "verdict": "PASS",
        "reasons": ["Session stable", "All gates passed", "Ready to finalize"],
        "required_fixes": [],
        "state_patch": {},
        "ledger_append": {
            "type": "termination",
            "actor": "mayor",
            "outcome": "SHIP",
        }
    }

    hal_json = json.dumps(hal_obj, sort_keys=True, separators=(",", ":"))

    return f"[HER]\nSession complete. All objectives achieved.\n\n[HAL]\n{hal_json}"

# ============================================================================
# MAIN
# ============================================================================

def load_ledger() -> List[Dict[str, Any]]:
    """Load current ledger."""
    if not LEDGER_PATH.exists():
        return []
    return [json.loads(line) for line in LEDGER_PATH.read_text().splitlines()]

def emit_next_block():
    """
    Generate and emit next two-block output to inbox.txt.
    Call this once per session turn.
    """
    ledger = load_ledger()
    turn = len(ledger) + 1

    # Initialize RNG with seed
    rng = SeededRandom(SEED)

    # Advance RNG state to this turn (deterministic)
    for _ in range(turn):
        rng.next_int(2**16)

    # Check termination
    if is_termination_turn(ledger):
        two_block = generate_termination_block()
    else:
        # Check if last verdict was BLOCK
        if ledger and ledger[-1].get("type") == "verdict" and ledger[-1].get("verdict") == "BLOCK":
            two_block = generate_revision_block(rng, turn)
        else:
            two_block = generate_two_block(rng, turn)

    # Write to inbox
    ROOT.mkdir(exist_ok=True)
    INBOX_PATH.write_text(two_block)

    print(f"⟦🜂⟧ HER Generator: Turn {turn}")
    print(f"Emitted to: {INBOX_PATH}")

def generate_full_session(max_turns: int = 12):
    """
    Convenience: generate a full test session (blocking).
    Emits one block per iteration.
    """
    for turn in range(1, max_turns + 1):
        emit_next_block()
        ledger = load_ledger()
        if ledger and ledger[-1].get("type") == "termination":
            print(f"⟦🜃⟧ Session terminated at turn {turn}")
            break

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        # Generate full session
        max_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 12
        generate_full_session(max_turns)
    else:
        # Generate single block
        emit_next_block()
