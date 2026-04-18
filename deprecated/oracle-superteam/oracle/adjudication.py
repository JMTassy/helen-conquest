# oracle/adjudication.py
from oracle.config import OracleConfig
from oracle.contradictions import detect_contradictions
from oracle.obligations import obligations_from_votes, add_contradiction_obligations

def adjudicate(claim: dict, evidence: list, votes: list, cfg: OracleConfig) -> dict:
    # Kill-switch check (lexicographic veto)
    kill_by = []
    for v in votes:
        if v.get("vote") == "KILL" and v.get("team") in cfg.kill_switch_teams:
            kill_by.append(v["team"])

    kill_switch_triggered = (len(kill_by) > 0)

    contradictions = detect_contradictions(evidence)
    obligations_open = obligations_from_votes(votes)
    obligations_open = add_contradiction_obligations(contradictions, obligations_open)

    # Rule-based KILL: HIGH legal/privacy contradiction (even without explicit KILL vote)
    rule_kill = any(c["rule_id"] == "HC-PRIV-001" and c.get("severity") == "HIGH" for c in contradictions)

    return {
        "kill_switch_triggered": kill_switch_triggered,
        "kill_switch_by": sorted(kill_by),
        "contradictions": contradictions,
        "rule_kill_triggered": bool(rule_kill),
        "obligations_open": obligations_open,
        "obligations_closed": [],
    }
