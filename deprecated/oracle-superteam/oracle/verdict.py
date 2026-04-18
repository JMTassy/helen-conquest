# oracle/verdict.py
from oracle.config import OracleConfig

def decide(final_state: dict, qi_S: float, cfg: OracleConfig) -> dict:
    """
    Returns: {final: ACCEPT|QUARANTINE|KILL, ship_permitted: bool, reason_codes: []}
    """
    reasons = []

    if final_state.get("kill_switch_triggered"):
        reasons.append("KILL_SWITCH")
        return {"final": "KILL", "ship_permitted": False, "reason_codes": reasons}

    if final_state.get("rule_kill_triggered"):
        reasons.append("CONTRADICTION_HIGH_LEGAL")
        return {"final": "KILL", "ship_permitted": False, "reason_codes": reasons}

    open_obs = [o for o in final_state.get("obligations_open", []) if o.get("status") == "OPEN"]
    if len(open_obs) > 0:
        reasons.append("OBLIGATIONS_BLOCKING")
        return {"final": "QUARANTINE", "ship_permitted": False, "reason_codes": reasons}

    if final_state.get("contradictions"):
        reasons.append("CONTRADICTION_PRESENT")
        return {"final": "QUARANTINE", "ship_permitted": False, "reason_codes": reasons}

    if qi_S >= cfg.tau_accept:
        reasons.append("SCORE_PASS")
        return {"final": "ACCEPT", "ship_permitted": True, "reason_codes": reasons}

    reasons.append("SCORE_FAIL")
    # If it isn't good enough to accept, quarantine (not kill) by default.
    return {"final": "QUARANTINE", "ship_permitted": False, "reason_codes": reasons}
