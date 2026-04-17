import json
import os
from typing import List, Dict, Any

DIALOG_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_FILE = os.path.join(DIALOG_DIR, "dialog.ndjson")
STATE_FILE = os.path.join(DIALOG_DIR, "dialog_state.json")

def detect_her_al_moment():
    if not os.path.exists(LEDGER_FILE):
        return {"ready": False, "reason": "No ledger found"}
        
    with open(LEDGER_FILE, "r") as f:
        lines = [json.loads(l) for l in f.readlines()]
        
    if not lines:
        return {"ready": False, "reason": "Ledger is empty"}

    # 1. Continuity: Check if current turn references a turn >= 5 turns ago
    latest_turn = lines[-1]["turn"]
    continuity = False
    for event in lines:
        if "references" in event or "linked_to" in event:
            ref = event.get("linked_to") or (event.get("references") or [""])[0]
            if ref and "dlg:" in ref:
                try:
                    ref_turn = int(ref.split(":")[1])
                    if latest_turn - ref_turn >= 5:
                        continuity = True
                except:
                    pass

    # 2. Self-Correction: Look for 'self_detected': true in mayor actions
    self_correction = any(e.get("self_detected") is True for e in lines if e.get("actor") == "mayor")

    # 3. Mode Shift: Last 5 turns have consistent [HER] + [AL] structure
    # Mechanically: Each turn has at least one 'helen' and one 'mayor' event
    mode_shift = True
    recent_turns = range(max(1, latest_turn - 4), latest_turn + 1)
    for t in recent_turns:
        turn_events = [e for e in lines if e["turn"] == t]
        has_her = any(e["actor"] == "helen" for e in turn_events)
        has_al = any(e["actor"] == "mayor" for e in turn_events)
        if not (has_her and has_al):
            mode_shift = False
            break

    return {
        "ready": continuity and self_correction and mode_shift,
        "metrics": {
            "continuity": continuity,
            "self_correction": self_correction,
            "mode_shift": mode_shift,
            "latest_turn": latest_turn
        }
    }

if __name__ == "__main__":
    result = detect_her_al_moment()
    print(json.dumps(result, indent=2))
