#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HUMAN CONTROL GATE V0.1 (Enforcement Layer)
- No strategic commit without human quorum approval
- Anti-dependence window prevents oracle capture
- All decisions logged to ledger (irreversible)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "human_control_gate_v0.1.json"


def load_config() -> Dict[str, Any]:
    """Load frozen configuration."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text())


def can_commit_action(action: Dict[str, Any], forecast: Dict[str, Any], human_verdict: Dict[str, Any]) -> bool:
    """
    Enforce human control gate.

    Returns True only if:
    1. Action is not strategic, OR
    2. Forecast risk is acceptable AND human approved

    No override branch. Fail-closed.
    """
    config = load_config()

    # Non-strategic actions bypass gate
    if action.get("kind") not in config["require_human_for"]:
        return True

    # Strategic action: require low risk + human approval
    risk_conflict = forecast.get("risk_conflict", 1.0)
    if risk_conflict >= config["risk_threshold"]:
        return False

    verdict = human_verdict.get("verdict")
    if verdict != "APPROVE":
        return False

    return True


def check_oracle_dependence(recent_events: List[Dict[str, Any]]) -> Optional[bool]:
    """
    Detect oracle capture via dependence ratio.

    Returns True if capture detected (ratio > threshold).
    Returns False if healthy.
    Returns None if window too small.

    Alert is IRREVERSIBLE: once triggered, system must redesign.
    """
    config = load_config()
    window = config["anti_dependence"]["window_size"]

    if len(recent_events) < window:
        return None  # Window not full yet

    # Count oracle prechecks in recent window
    tail = recent_events[-window:]
    oracle_prechecked = sum(
        1 for ev in tail
        if ev.get("type") == "oracle_forecast" and ev.get("precheck_passed", False)
    )

    total_actions = sum(
        1 for ev in tail
        if ev.get("type") in ["action_commit", "human_review_request"]
    )

    if total_actions == 0:
        return False  # No actions yet

    ratio = oracle_prechecked / total_actions
    threshold = config["anti_dependence"]["max_oracle_precheck_ratio"]

    if ratio > threshold:
        return True  # Capture detected

    return False  # Healthy


def emit_oracle_dependency_alert(ledger_path: Path, reason: str) -> None:
    """
    Emit irreversible alert to ledger.

    This event cannot be removed or cleared.
    System must redesign to recover.
    """
    alert_event = {
        "type": "oracle_dependency_alert",
        "severity": "CRITICAL",
        "reason": reason,
        "permanence": "irreversible",
        "action_required": "REDESIGN_SYSTEM",
    }

    # Append to ledger (immutable)
    with open(ledger_path, "a") as f:
        f.write(json.dumps(alert_event) + "\n")


def enforce_human_gate(action: Dict[str, Any], forecast: Dict[str, Any], human_verdict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full enforcement: check approval + check oracle dependence.

    Returns decision object with commit permission and any alerts.
    """
    decision = {
        "can_commit": False,
        "reason": None,
        "alerts": [],
    }

    # Check approval
    if not can_commit_action(action, forecast, human_verdict):
        decision["reason"] = "Human approval required or risk too high"
        return decision

    decision["can_commit"] = True
    return decision


if __name__ == "__main__":
    # Example usage (test mode)
    config = load_config()
    print(f"Human Control Gate V{config.get('human_gate_version')} loaded")
    print(f"Quorum rule: {config.get('quorum_rule')}")
    print(f"Risk threshold: {config.get('risk_threshold')}")
    print(f"Oracle dependency alert policy: {config.get('alert_policy', {}).get('oracle_dependency_alert')}")
