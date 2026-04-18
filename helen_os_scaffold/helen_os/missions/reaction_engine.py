from __future__ import annotations
from typing import Any

def proposals_from_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Non-sovereign. Reads events and emits proposal templates ONLY.
    May NOT create missions or append to any channel.
    """
    if event.get("event_kind") == "step_failed":
        return [{
            "proposal_id": f"R-{event['event_id']}",
            "source": "reaction",
            "title": "Review failed step",
            "goal": f"Review failure of step {event.get('step_id')}",
            "step_kinds": ["review"],
            "input_refs": [event["event_id"]],
            "risk_tier": "low",
        }]
    return []
