#!/usr/bin/env python3
"""
K15 Enforcement: No Receipt = No Execution

K15 is the invariant that prevents OpenClaw skills from executing without
an Oracle Town receipt authorizing the action.

This is the final gate: even if everything else succeeds, no world mutation
happens without explicit authorization from the Kernel.

Flow:
1. OpenClaw (or any World actor) wants to execute a skill
2. First: submit claim to Oracle Town
3. Wait: get receipt (SHIP or NO_SHIP)
4. K15: Check receipt before executing
5. If ACCEPT → execute
6. If REJECT or NO_RECEIPT → abort
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import uuid


class ExecutionBlocked(Exception):
    """
    Raised when K15 enforcement blocks execution.
    """
    def __init__(self, reason: str, receipt: Optional[Dict] = None):
        self.reason = reason
        self.receipt = receipt
        super().__init__(reason)


@dataclass
class Receipt:
    """
    Oracle Town receipt authorizing (or denying) an action.
    """
    receipt_id: str
    claim_id: str
    decision: str  # "SHIP" or "NO_SHIP"
    world_mutation_allowed: bool
    reason: str
    timestamp: str
    policy_hash: str
    mayor_signature: str  # cryptographic signature

    def is_valid(self) -> bool:
        """Check if receipt is structurally valid."""
        return all([
            self.receipt_id,
            self.claim_id,
            self.decision in ["SHIP", "NO_SHIP"],
            self.timestamp,
            self.policy_hash,
            self.mayor_signature
        ])


class K15Enforcer:
    """
    Enforces K15: No receipt = no execution.

    This is the core guard that prevents autonomous systems from executing
    actions without explicit authority.
    """

    def __init__(self, audit_log_path: str = "oracle_town/execution.jsonl"):
        """
        Initialize the K15 enforcer.

        Args:
            audit_log_path: Path to audit log of executions
        """
        self.audit_log_path = audit_log_path

    def enforce(self, receipt: Optional[Dict]) -> bool:
        """
        Check if a receipt permits execution (K15).

        This is the fast path: return bool.

        Args:
            receipt: Receipt dict from Oracle Town (or None)

        Returns:
            True if execution is permitted, False otherwise
        """
        # K15: No receipt = no execute
        if not receipt:
            return False

        # Must be SHIP (not NO_SHIP, not UNKNOWN)
        if receipt.get("decision") != "SHIP":
            return False

        # Must explicitly allow world mutation
        if not receipt.get("world_mutation_allowed", False):
            return False

        return True

    def check_receipt(self, receipt: Optional[Dict]) -> Receipt:
        """
        Check if a receipt permits execution (K15).

        This is the strict path: raises if blocked.

        Args:
            receipt: Receipt dict from Oracle Town (or None)

        Raises:
            ExecutionBlocked if receipt doesn't permit execution

        Returns:
            Valid Receipt object if execution is permitted
        """
        # K15: No receipt = no execute
        if not receipt:
            raise ExecutionBlocked(
                "No receipt provided (Oracle Town offline or not submitting)",
                receipt=None
            )

        # Parse receipt
        try:
            r = Receipt(
                receipt_id=receipt["receipt_id"],
                claim_id=receipt["claim_id"],
                decision=receipt["decision"],
                world_mutation_allowed=receipt.get("world_mutation_allowed", False),
                reason=receipt.get("reason", ""),
                timestamp=receipt.get("timestamp", ""),
                policy_hash=receipt.get("policy_hash", ""),
                mayor_signature=receipt.get("mayor_signature", "")
            )
        except KeyError as e:
            raise ExecutionBlocked(
                f"Receipt missing required field: {e}",
                receipt=receipt
            )

        # Validate structure
        if not r.is_valid():
            raise ExecutionBlocked(
                "Receipt is malformed or incomplete",
                receipt=receipt
            )

        # Check decision
        if r.decision != "SHIP":
            raise ExecutionBlocked(
                f"Authority decision: {r.decision} — {r.reason}",
                receipt=receipt
            )

        # Check world mutation flag
        if not r.world_mutation_allowed:
            raise ExecutionBlocked(
                "Receipt does not permit world mutation",
                receipt=receipt
            )

        return r

    def execute_with_authorization(
        self,
        execute_fn: Callable,
        receipt: Optional[Dict],
        skill_id: str,
        fail_closed: bool = True
    ) -> Any:
        """
        Execute a skill only if receipt permits (K15).

        Args:
            execute_fn: Function to execute if authorized
            receipt: Receipt from Oracle Town
            skill_id: ID of skill being executed
            fail_closed: If True, ExecutionBlocked raises; if False, returns None

        Returns:
            Result of execute_fn if permitted
            Raises ExecutionBlocked if not permitted (unless fail_closed=False)
        """
        try:
            # K15: Check receipt
            r = self.check_receipt(receipt)

            # K15: Receipt permits execution
            # Execute the skill
            result = execute_fn()

            # Log successful execution
            self._log_execution(
                skill_id=skill_id,
                decision="EXECUTED",
                receipt_id=r.receipt_id,
                result=result
            )

            return result

        except ExecutionBlocked as e:
            if fail_closed:
                # Log blocked execution
                self._log_execution(
                    skill_id=skill_id,
                    decision="BLOCKED",
                    receipt_id=e.receipt.get("receipt_id") if e.receipt else None,
                    reason=e.reason
                )
                raise
            else:
                # Silent fail
                return None

    def audit_trail(
        self,
        skill_id: str,
        receipt: Dict,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """
        Log an action to the audit trail (whether executed or blocked).

        Args:
            skill_id: ID of skill
            receipt: Receipt from Oracle Town
            result: Optional execution result
            error: Optional error message
        """
        self._log_execution(
            skill_id=skill_id,
            decision=receipt.get("decision", "UNKNOWN"),
            receipt_id=receipt.get("receipt_id"),
            result=result,
            reason=error
        )

    # --- Private helper methods ---

    def _log_execution(
        self,
        skill_id: str,
        decision: str,
        receipt_id: Optional[str] = None,
        result: Optional[Any] = None,
        reason: Optional[str] = None
    ):
        """
        Log an execution (or block) to the audit trail.
        """
        import json

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "skill_id": skill_id,
            "decision": decision,
            "receipt_id": receipt_id,
            "result": str(result)[:100] if result else None,
            "reason": reason
        }

        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Warning: Could not log execution: {e}")


# Global K15 enforcer instance
_k15_enforcer = K15Enforcer()


def enforce(receipt: Optional[Dict]) -> bool:
    """
    Quick K15 check: does receipt permit execution?

    Args:
        receipt: Receipt from Oracle Town

    Returns:
        True if execution permitted, False otherwise
    """
    return _k15_enforcer.enforce(receipt)


def check_receipt(receipt: Optional[Dict]) -> Receipt:
    """
    Strict K15 check: raises if blocked.

    Args:
        receipt: Receipt from Oracle Town

    Raises:
        ExecutionBlocked if receipt doesn't permit execution

    Returns:
        Valid Receipt object
    """
    return _k15_enforcer.check_receipt(receipt)


def execute_with_authorization(
    execute_fn: Callable,
    receipt: Optional[Dict],
    skill_id: str,
    fail_closed: bool = True
) -> Any:
    """
    Execute skill only if receipt permits.

    Args:
        execute_fn: Function to execute
        receipt: Receipt from Oracle Town
        skill_id: ID of skill
        fail_closed: If True, raises on block; if False, returns None

    Returns:
        Result of execute_fn if permitted
    """
    return _k15_enforcer.execute_with_authorization(
        execute_fn, receipt, skill_id, fail_closed
    )


def audit_trail(skill_id: str, receipt: Dict, result: Any = None):
    """
    Log execution to audit trail.
    """
    return _k15_enforcer.audit_trail(skill_id, receipt, result)


# --- Testing ---

if __name__ == "__main__":

    # Test 1: Valid receipt (SHIP)
    valid_receipt = {
        "receipt_id": "receipt_001",
        "claim_id": "claim_001",
        "decision": "SHIP",
        "world_mutation_allowed": True,
        "reason": "Approved by authority",
        "timestamp": datetime.utcnow().isoformat(),
        "policy_hash": "sha256:...",
        "mayor_signature": "sig_..."
    }

    enforcer = K15Enforcer()

    result = enforcer.enforce(valid_receipt)
    print(f"✓ Test 1 (Valid SHIP): {result}")
    assert result is True

    # Test 2: Rejected receipt (NO_SHIP)
    rejected_receipt = {
        "receipt_id": "receipt_002",
        "claim_id": "claim_002",
        "decision": "NO_SHIP",
        "world_mutation_allowed": False,
        "reason": "Failed gate validation",
        "timestamp": datetime.utcnow().isoformat(),
        "policy_hash": "sha256:...",
        "mayor_signature": "sig_..."
    }

    result = enforcer.enforce(rejected_receipt)
    print(f"✓ Test 2 (Valid NO_SHIP): {result}")
    assert result is False

    # Test 3: No receipt (K15 fail-closed)
    result = enforcer.enforce(None)
    print(f"✓ Test 3 (No receipt): {result}")
    assert result is False

    # Test 4: Execute with authorization (succeeds)
    def mock_skill():
        return {"status": "success"}

    result = enforcer.execute_with_authorization(
        mock_skill,
        valid_receipt,
        "skill_001"
    )
    print(f"✓ Test 4 (Execution with valid receipt): {result}")

    # Test 5: Execute with authorization (fails)
    try:
        enforcer.execute_with_authorization(
            mock_skill,
            rejected_receipt,
            "skill_002"
        )
        print("✗ Test 5 (Should have raised ExecutionBlocked)")
    except ExecutionBlocked as e:
        print(f"✓ Test 5 (ExecutionBlocked raised): {e.reason}")

    # Test 6: Check receipt (strict path)
    try:
        r = enforcer.check_receipt(valid_receipt)
        print(f"✓ Test 6 (Valid receipt parsed): {r.receipt_id}")
    except ExecutionBlocked:
        print("✗ Test 6 (Should not have raised)")

    print("\n✅ K15 enforcement tests passed")
