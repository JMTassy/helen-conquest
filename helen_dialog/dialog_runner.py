import json
import os
import sys
import datetime
from typing import List, Dict, Any

DIALOG_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(DIALOG_DIR, "dialog_state.json")
LEDGER_FILE = os.path.join(DIALOG_DIR, "dialog.ndjson")

def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {"turn": 0, "session_id": "new_session", "oath": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state: Dict[str, Any]):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def append_ledger(event: Dict[str, Any]):
    with open(LEDGER_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

def get_recent_events(n: int = 100) -> List[Dict[str, Any]]:
    if not os.path.exists(LEDGER_FILE):
        return []
    with open(LEDGER_FILE, "r") as f:
        lines = f.readlines()
    return [json.loads(l) for l in lines[-n:]]

def detect_contradictions(history: List[Dict[str, Any]], user_input: str) -> List[Dict[str, Any]]:
    conflicts = []
    # Simple keyword-based contradiction
    input_lower = user_input.lower()
    if any(k in input_lower for k in ["magic", "conscious", "mystic"]):
        conflicts.append({"turn_a": "oath", "turn_b": "current", "topic": "mysticism"})
    
    # Check history for conflicting claims (Phase C requirement)
    has_magical = False
    for e in history:
        text = (e.get("proposal") or e.get("intent") or "").lower()
        if any(k in text for k in ["magic", "mystic", "conscious"]):
            has_magical = True
            break
            
    if has_magical and "mechanical" in input_lower:
        conflicts.append({"turn_a": "prior_turns", "turn_b": "current", "topic": "mysticism_vs_mechanical", "self_detected": True})
        
    return conflicts

def generate_her_al(user_input: str, state: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simulates HELEN (HER) and MAYOR (AL) response.
    In a real scenario, this would call Ollama with a specific prompt.
    For Phase B, we implement the structure.
    """
    turn = state["turn"] + 1
    
    # Simple logic for HER
    her_text = f"[HER] I hear you regarding: '{user_input}'. Let me record this as part of our sequence."
    
    # Simple logic for AL
    al_decision = "Proceed"
    al_checks = "PASS"
    
    # Run contradiction scan
    conflicts = detect_contradictions(history, user_input)
    
    if conflicts:
        al_checks = f"WARN: Contradiction detected: {conflicts[0]['topic']}"
        her_text = f"[HER] I notice a tension between your current request and prior turns regarding {conflicts[0]['topic']}."
        if "self_detected" in conflicts[0]:
            al_decision = "Self-Correction Required"
    
    event_id = f"dlg:{turn}"
    
    her_event = {
        "type": "witness" if conflicts else "proposal",
        "actor": "helen",
        "turn": turn,
        "proposal": her_text,
        "entry_id": f"{event_id}:her",
        "t": datetime.datetime.now().isoformat()
    }
    
    al_event = {
        "type": "contradiction_scan" if conflicts else "check",
        "actor": "mayor",
        "turn": turn,
        "check": "oath_compliance",
        "result": al_checks,
        "entry_id": f"{event_id}:al",
        "t": datetime.datetime.now().isoformat(),
        "contradictions": conflicts,
        "self_detected": any(c.get("self_detected") for c in conflicts)
    }
    
    return {
        "her": her_text,
        "al": {
            "decision": al_decision,
            "checks": al_checks,
            "state_update": {"turn": turn}
        },
        "events": [her_event, al_event]
    }

def process_turn(user_message: str, reference: str = None):
    state = load_state()
    history = get_recent_events()
    
    # Log user input
    user_turn = state["turn"] + 1
    user_event = {
        "type": "oath" if "oath" in user_message.lower() else "proposal",
        "actor": "user",
        "turn": user_turn,
        "intent": user_message,
        "entry_id": f"dlg:{user_turn}:u",
        "t": datetime.datetime.now().isoformat()
    }
    if reference:
        user_event["references"] = [reference]
    append_ledger(user_event)
    
    # Generate response
    response_data = generate_her_al(user_message, state, history)
    
    for ev in response_data["events"]:
        if reference and ev["actor"] == "helen":
            ev["linked_to"] = reference
        append_ledger(ev)
        
    # Update state
    state["turn"] = user_turn
    state["last_state_patch"] = response_data["al"]["state_update"]
    save_state(state)
    
    return response_data

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = sys.argv[1]
        ref = sys.argv[2] if len(sys.argv) > 2 else None
        resp = process_turn(msg, ref)
        print(json.dumps(resp, indent=2))
    else:
        print("Usage: python3 dialog_runner.py 'your message' [reference]")
