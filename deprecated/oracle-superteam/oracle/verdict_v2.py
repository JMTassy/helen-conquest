# oracle/verdict_v2.py
"""
ORACLE SUPERTEAM — Binary Verdict Gate V2 (Hardened)

This module implements the deterministic integration layer that outputs
binary verdicts: SHIP or NO_SHIP.

CONSTITUTIONAL GUARANTEE: There are exactly two verdict states.
Internal classifications (ACCEPT, QUARANTINE, KILL) map to these two states:
- ACCEPT → SHIP
- QUARANTINE → NO_SHIP
- KILL → NO_SHIP

The verdict gate applies lexicographic veto rules in strict priority order.
"""

from oracle.config import OracleConfig
from typing import Dict, List


def decide(final_state: dict, qi_S: float, cfg: OracleConfig) -> dict:
    """
    Deterministic binary verdict gate.

    Priority (lexicographic veto):
    1. Kill-switch (immediate NO_SHIP)
    2. Rule-based kill (high-severity contradiction → NO_SHIP)
    3. Open obligations (any OPEN obligation → NO_SHIP)
    4. Contradictions present (any contradiction → NO_SHIP)
    5. QI-INT score threshold (S_c >= τ → SHIP, else NO_SHIP)

    Args:
        final_state: Adjudication output (kill signals, obligations, contradictions)
        qi_S: QI-INT score (diagnostic only if kills/obligations active)
        cfg: Configuration with thresholds

    Returns:
        Binary verdict dict:
        {
            "final": "SHIP" | "NO_SHIP",
            "ship_permitted": bool,
            "reason_codes": [str],
            "internal_state": "ACCEPT" | "QUARANTINE" | "KILL"  # diagnostic
        }
    """
    reasons = []
    internal_state = None

    # Priority 1: Kill-switch (authorized team KILL_REQUEST)
    if final_state.get("kill_switch_triggered"):
        reasons.append("KILL_SWITCH")
        return _verdict(
            final="NO_SHIP",
            ship_permitted=False,
            reason_codes=reasons,
            internal_state="KILL"
        )

    # Priority 2: Rule-based kill (high-severity contradiction)
    if final_state.get("rule_kill_triggered"):
        reasons.append("CONTRADICTION_HIGH_LEGAL")
        return _verdict(
            final="NO_SHIP",
            ship_permitted=False,
            reason_codes=reasons,
            internal_state="KILL"
        )

    # Priority 3: Open obligations
    open_obs = [
        o for o in final_state.get("obligations_open", [])
        if o.get("status") == "OPEN"
    ]
    if len(open_obs) > 0:
        reasons.append("OBLIGATIONS_BLOCKING")
        reasons.append(f"OPEN_COUNT_{len(open_obs)}")  # Diagnostic detail
        return _verdict(
            final="NO_SHIP",
            ship_permitted=False,
            reason_codes=reasons,
            internal_state="QUARANTINE"
        )

    # Priority 4: Contradictions (medium/low severity)
    if final_state.get("contradictions"):
        reasons.append("CONTRADICTION_PRESENT")
        return _verdict(
            final="NO_SHIP",
            ship_permitted=False,
            reason_codes=reasons,
            internal_state="QUARANTINE"
        )

    # Priority 5: QI-INT score check
    if qi_S >= cfg.tau_accept:
        reasons.append("SCORE_PASS")
        reasons.append(f"QI_INT_{qi_S:.4f}")  # Diagnostic value
        return _verdict(
            final="SHIP",
            ship_permitted=True,
            reason_codes=reasons,
            internal_state="ACCEPT"
        )

    # Default: Score insufficient → NO_SHIP
    reasons.append("SCORE_FAIL")
    reasons.append(f"QI_INT_{qi_S:.4f}_BELOW_{cfg.tau_accept}")
    return _verdict(
        final="NO_SHIP",
        ship_permitted=False,
        reason_codes=reasons,
        internal_state="QUARANTINE"
    )


def _verdict(final: str, ship_permitted: bool, reason_codes: List[str], internal_state: str) -> dict:
    """
    Construct verdict dict with validation.

    Ensures binary semantics are enforced:
    - SHIP must have ship_permitted=True
    - NO_SHIP must have ship_permitted=False
    """
    if final == "SHIP" and not ship_permitted:
        raise ValueError("SHIP verdict must have ship_permitted=True")
    if final == "NO_SHIP" and ship_permitted:
        raise ValueError("NO_SHIP verdict must have ship_permitted=False")

    return {
        "final": final,
        "ship_permitted": ship_permitted,
        "reason_codes": reason_codes,
        "internal_state": internal_state,  # ACCEPT, QUARANTINE, or KILL (diagnostic)
    }


def verdict_summary(verdict: dict) -> str:
    """
    Human-readable verdict summary.

    Example: "NO_SHIP (QUARANTINE) — OBLIGATIONS_BLOCKING, OPEN_COUNT_2"
    """
    final = verdict["final"]
    internal = verdict.get("internal_state", "UNKNOWN")
    reasons = ", ".join(verdict["reason_codes"])

    return f"{final} ({internal}) — {reasons}"


# ==============================================================================
# BACKWARD COMPATIBILITY
# ==============================================================================

def decide_compat(final_state: dict, qi_S: float, cfg: OracleConfig) -> dict:
    """
    Backward compatibility wrapper that returns old format.

    Old format uses ACCEPT/QUARANTINE/KILL instead of SHIP/NO_SHIP.
    This function translates the hardened V2 verdict back to old format
    for existing test vault scenarios.

    Returns:
        {"final": "ACCEPT"|"QUARANTINE"|"KILL", ...}
    """
    verdict_v2 = decide(final_state, qi_S, cfg)

    # Map internal_state to old "final" field for compatibility
    internal_state = verdict_v2.get("internal_state", "QUARANTINE")

    return {
        "final": internal_state,  # ACCEPT, QUARANTINE, or KILL
        "ship_permitted": verdict_v2["ship_permitted"],
        "reason_codes": verdict_v2["reason_codes"],
        # Include V2 verdict for audit
        "verdict_v2": {
            "final": verdict_v2["final"],
            "internal_state": internal_state,
        }
    }
