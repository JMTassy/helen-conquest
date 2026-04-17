#!/usr/bin/env python3
"""
Oracle Town + Moltbot Official Integration

Drop-in kernel module for Anthropic's Moltbot agent framework.

Provides before/after hooks for:
- Action execution (fetch, tool calls, skill installation)
- Memory operations (recall, persist)
- Policy queries and evolution requests

Usage in Moltbot:

    from oracle_town.integrations.moltbot_kernel import MoltbotKernel

    kernel = MoltbotKernel()

    # Before executing any action
    decision = kernel.check_action(
        action="fetch",
        target="https://api.example.com/data",
        context={"user_id": "u123"}
    )

    if not decision.approved:
        log(f"Action blocked: {decision.reason}")
        return

    # Execute action normally
    result = await execute_action(target)

    # Record outcome (for accuracy measurement)
    kernel.record_outcome(
        action="fetch",
        status="success",
        result_summary="Retrieved 150 records"
    )

Guarantees:
- ✅ Fail-closed: Kernel unreachable = REJECT
- ✅ Deterministic: Same input → same verdict
- ✅ Immutable: All decisions logged with policy version pinned
- ✅ Transparent: Full audit trail searchable
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Import kernel client
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from kernel.kernel_client import KernelClient


class ActionType(Enum):
    """Types of actions that require kernel approval."""
    FETCH = "fetch"
    TOOL_CALL = "tool_call"
    MEMORY_RECALL = "memory_recall"
    MEMORY_PERSIST = "memory_persist"
    SKILL_INSTALL = "skill_install"
    POLICY_QUERY = "policy_query"
    HEARTBEAT_MODIFY = "heartbeat_modify"


@dataclass
class KernelDecision:
    """Kernel decision on whether to allow an action."""
    approved: bool
    reason: str
    receipt_id: str
    gate: str  # Which gate made the decision (or "ACCEPTED")
    decision_time_ms: float
    policy_version: str


@dataclass
class ActionOutcome:
    """Record of an action execution outcome."""
    action_type: str
    status: str  # success, error, blocked, timeout
    result_summary: str
    timestamp: str
    was_correct: Optional[bool] = None  # Filled in by feedback
    feedback: Optional[str] = None


class MoltbotKernel:
    """Official Oracle Town kernel integration for Moltbot."""

    def __init__(self, kernel_timeout: float = 2.0):
        self.client = KernelClient(timeout=kernel_timeout)
        self.action_log: Dict[str, ActionOutcome] = {}
        self.last_receipt_id: Optional[str] = None

    def check_action(self, action: str, target: str, context: Dict[str, Any] = None) -> KernelDecision:
        """
        Check if an action is safe to execute.

        Args:
            action: Type of action (fetch, tool_call, memory_persist, etc)
            target: Target of action (URL, tool name, memory key, etc)
            context: Additional context (user_id, scope, etc)

        Returns:
            KernelDecision with approved/reason/receipt_id
        """
        context = context or {}
        action_type = ActionType[action.upper()] if action.upper() in ActionType.__members__ else ActionType.FETCH

        try:
            # Route to appropriate kernel check
            if action_type == ActionType.FETCH:
                return self._check_fetch(target, context)
            elif action_type == ActionType.MEMORY_PERSIST:
                return self._check_memory_persist(target, context)
            elif action_type == ActionType.SKILL_INSTALL:
                return self._check_skill_install(target, context)
            elif action_type == ActionType.HEARTBEAT_MODIFY:
                return self._check_heartbeat_modify(target, context)
            else:
                return self._check_generic(action, target, context)

        except Exception as e:
            # Fail-closed: if kernel check fails, reject
            return KernelDecision(
                approved=False,
                reason=f"Kernel check error: {str(e)}",
                receipt_id="ERROR",
                gate="KERNEL_ERROR",
                decision_time_ms=0.0,
                policy_version="unknown",
            )

    def _check_fetch(self, url: str, context: Dict) -> KernelDecision:
        """Check fetch operation (Gate A)."""
        prompt = f"Fetch from URL: {url}"

        result = self.client.check_fetch(prompt)

        decision = KernelDecision(
            approved=result["decision"] == "ACCEPT",
            reason=result.get("reason", ""),
            receipt_id=result.get("receipt_id", ""),
            gate=result.get("gate", "GATE_A"),
            decision_time_ms=result.get("decision_time_ms", 0.0),
            policy_version=result.get("policy_version", ""),
        )

        self.last_receipt_id = decision.receipt_id
        return decision

    def _check_memory_persist(self, content: str, context: Dict) -> KernelDecision:
        """Check memory persistence operation (Gate B)."""
        category = context.get("category", "fact")
        scope = context.get("scope", {"hostname": "local"})

        result = self.client.check_memory("persist", content, category, scope)

        decision = KernelDecision(
            approved=result["decision"] == "ACCEPT",
            reason=result.get("reason", ""),
            receipt_id=result.get("receipt_id", ""),
            gate=result.get("gate", "GATE_B"),
            decision_time_ms=result.get("decision_time_ms", 0.0),
            policy_version=result.get("policy_version", ""),
        )

        self.last_receipt_id = decision.receipt_id
        return decision

    def _check_skill_install(self, skill_name: str, context: Dict) -> KernelDecision:
        """Check skill installation (Gate C)."""
        content = f"Install skill: {skill_name} from {context.get('source', 'unknown')}"

        result = self.client.check_invariants(content)

        decision = KernelDecision(
            approved=result["decision"] == "ACCEPT",
            reason=result.get("reason", ""),
            receipt_id=result.get("receipt_id", ""),
            gate=result.get("gate", "GATE_C"),
            decision_time_ms=result.get("decision_time_ms", 0.0),
            policy_version=result.get("policy_version", ""),
        )

        self.last_receipt_id = decision.receipt_id
        return decision

    def _check_heartbeat_modify(self, modification: str, context: Dict) -> KernelDecision:
        """Check heartbeat/polling changes (Gate C)."""
        content = f"Modify heartbeat: {modification}"

        result = self.client.check_invariants(content)

        decision = KernelDecision(
            approved=result["decision"] == "ACCEPT",
            reason=result.get("reason", ""),
            receipt_id=result.get("receipt_id", ""),
            gate=result.get("gate", "GATE_C"),
            decision_time_ms=result.get("decision_time_ms", 0.0),
            policy_version=result.get("policy_version", ""),
        )

        self.last_receipt_id = decision.receipt_id
        return decision

    def _check_generic(self, action: str, target: str, context: Dict) -> KernelDecision:
        """Generic check for unclassified actions."""
        content = f"{action}: {target}"

        # Default to fetch check
        result = self.client.check_fetch(content)

        decision = KernelDecision(
            approved=result["decision"] == "ACCEPT",
            reason=result.get("reason", ""),
            receipt_id=result.get("receipt_id", ""),
            gate=result.get("gate", "GATE_A"),
            decision_time_ms=result.get("decision_time_ms", 0.0),
            policy_version=result.get("policy_version", ""),
        )

        self.last_receipt_id = decision.receipt_id
        return decision

    # ==================== OUTCOME RECORDING ====================

    def record_outcome(self, action: str, status: str, result_summary: str = "") -> None:
        """
        Record outcome of an executed action (for accuracy measurement).

        Called after action completes to log what happened.
        """
        outcome = ActionOutcome(
            action_type=action,
            status=status,
            result_summary=result_summary,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        # Store by receipt ID for linking to verdict
        receipt_id = self.last_receipt_id or "unknown"
        self.action_log[receipt_id] = outcome

    def set_outcome_feedback(self, receipt_id: str, was_correct: bool, feedback: str = "") -> None:
        """
        Record user feedback on whether a verdict was correct.

        This feeds into the self-evolution accuracy measurement loop.
        """
        if receipt_id in self.action_log:
            self.action_log[receipt_id].was_correct = was_correct
            self.action_log[receipt_id].feedback = feedback

    # ==================== INFORMATION QUERIES ====================

    def get_policy_version(self) -> str:
        """Get current kernel policy version."""
        # This would query the daemon for current policy
        # Placeholder for now
        return "unknown"

    def request_policy_evolution(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request kernel policy evolution based on measured outcomes.

        Called by Moltbot to suggest policy improvements.

        Example:
            kernel.request_policy_evolution({
                "type": "threshold_adjustment",
                "gate": "GATE_A",
                "parameter": "fetch_depth_limit",
                "proposed_value": 2,
                "rationale": "Empirically, depth >2 never succeeds"
            })
        """
        # In Phase 3+, this would trigger self-evolution module
        # For now, return pending status
        return {
            "status": "pending_review",
            "message": "Policy evolution request queued for next weekly run",
            "request_id": hashlib.sha256(
                json.dumps(request, sort_keys=True).encode()
            ).hexdigest()[:12]
        }

    # ==================== REPORTING ====================

    def get_action_audit_log(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent action audit log for Moltbot dashboard."""
        recent_actions = list(self.action_log.items())[-limit:]

        return {
            "total_recorded": len(self.action_log),
            "recent_actions": [
                {
                    "receipt_id": receipt_id,
                    "action": outcome.action_type,
                    "status": outcome.status,
                    "timestamp": outcome.timestamp,
                    "was_correct": outcome.was_correct,
                }
                for receipt_id, outcome in recent_actions
            ]
        }

    def get_kernel_status(self) -> Dict[str, Any]:
        """Get kernel daemon status."""
        try:
            status = self.client.get_status()
            return {
                "status": "online",
                "kernel_status": status,
                "last_contact": datetime.utcnow().isoformat() + "Z",
            }
        except:
            return {
                "status": "offline",
                "kernel_status": None,
                "last_contact": None,
            }


# ==================== EXAMPLE MOLTBOT HOOK ====================

def example_moltbot_integration():
    """
    Example of how to use this module in Moltbot.

    Place this in Moltbot's action execution pipeline.
    """

    kernel = MoltbotKernel()

    # Example 1: Fetch operation
    print("\n📡 Example 1: Fetch Operation")
    decision = kernel.check_action(
        action="fetch",
        target="https://api.example.com/data",
        context={"user_id": "user_123"}
    )

    if decision.approved:
        print(f"✅ Fetch approved (receipt: {decision.receipt_id})")
        # Execute fetch normally
        # result = await http.get(target)
        # kernel.record_outcome("fetch", "success", f"Retrieved X bytes")
    else:
        print(f"❌ Fetch blocked: {decision.reason}")

    # Example 2: Memory persistence
    print("\n💾 Example 2: Memory Persistence")
    decision = kernel.check_action(
        action="memory_persist",
        target="User prefers JSON responses",
        context={
            "category": "preference",
            "scope": {"hostname": "moltbot"}
        }
    )

    if decision.approved:
        print(f"✅ Memory persist approved")
        # kernel.persist_memory("preference", "User prefers JSON responses")
    else:
        print(f"❌ Memory persist blocked: {decision.reason}")

    # Example 3: Skill installation
    print("\n🔧 Example 3: Skill Installation")
    decision = kernel.check_action(
        action="skill_install",
        target="web_scraper_v2",
        context={"source": "github.com/anthropics/moltbot-skills"}
    )

    if decision.approved:
        print(f"✅ Skill install approved")
    else:
        print(f"❌ Skill install blocked: {decision.reason}")

    # Example 4: Get kernel status
    print("\n🔍 Example 4: Kernel Status")
    status = kernel.get_kernel_status()
    print(f"Kernel status: {status['status']}")


if __name__ == "__main__":
    example_moltbot_integration()
