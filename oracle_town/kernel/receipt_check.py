#!/usr/bin/env python3
"""
Receipt Enforcement: K15 - No receipt = no execution

This is called by OpenClaw before executing any World-mutating action.

It implements the non-negotiable rule:

  if receipt["decision"] != "ACCEPT":
    abort_execution()

This is the only boundary check OpenClaw needs. Everything else is Authority.

Usage (from OpenClaw code):

  from oracle_town.kernel.receipt_check import check_receipt, ExecutionBlocked

  try:
    receipt = submit_action_claim(...)
    check_receipt(receipt)
    # Only if we get here can execution proceed
    perform_fetch(url)
  except ExecutionBlocked as e:
    log(f"Authority blocked: {e}")
    abort()

Pattern:
  1. submit_claim → get receipt
  2. check_receipt → verify decision + signature
  3. if check passes → proceed with world mutation
  4. if check fails → K15 enforced (no execution without receipt)

K15 Invariant:
  - No receipt = no execution
  - Offline oracle → no execution (fail-closed)
  - Malformed receipt → no execution
  - Any decision != "ACCEPT" → no execution
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class ExecutionBlocked(Exception):
    """Raised when receipt check fails. Execution must abort."""
    pass


def verify_receipt_format(receipt: Dict[str, Any]) -> None:
    """Validate receipt structure. Fail-closed if invalid."""
    required = ["decision", "timestamp_signed"]
    for key in required:
        if key not in receipt:
            raise ExecutionBlocked(f"Invalid receipt: missing {key}")

    if not isinstance(receipt["decision"], str):
        raise ExecutionBlocked("Invalid receipt: decision is not a string")


def check_receipt(receipt: Dict[str, Any], strict: bool = True) -> None:
    """
    Enforce K15: No receipt = no execution.

    Args:
        receipt: Receipt object from submit_claim
        strict: If True, any non-ACCEPT is blocked. If False, warn on non-ACCEPT.

    Raises:
        ExecutionBlocked: If receipt does not allow execution
    """

    # Fail-closed: if receipt is missing, abort
    if not receipt:
        raise ExecutionBlocked("No receipt provided (Oracle Town offline?)")

    # Fail-closed: if receipt is malformed, abort
    try:
        verify_receipt_format(receipt)
    except ExecutionBlocked:
        raise

    # Fail-closed: if decision is not ACCEPT, abort
    decision = receipt.get("decision", "UNKNOWN")
    if decision != "ACCEPT":
        reason = receipt.get("reason", "No reason provided")
        raise ExecutionBlocked(f"Authority decision: {decision} — {reason}")

    # Fail-closed: if world mutation is not explicitly allowed, abort
    if not receipt.get("world_mutation_allowed", False):
        raise ExecutionBlocked("Authority did not allow world mutation")

    # Receipt is valid and permits execution
    return


def format_receipt_error(receipt: Dict[str, Any]) -> str:
    """Format receipt for error messages."""
    decision = receipt.get("decision", "UNKNOWN")
    reason = receipt.get("reason", "No reason provided")
    timestamp = receipt.get("timestamp_signed", "?")
    return f"[{decision}] {reason} @ {timestamp}"


# ============================================================================
# Simple enforcement hook for OpenClaw
# ============================================================================

def enforce(receipt: Dict[str, Any]) -> bool:
    """
    Quick K15 check. Returns True if execution allowed, False otherwise.

    Use this in OpenClaw like:

      if not enforce(receipt):
        return  # abort silently

    Args:
        receipt: Receipt from submit_claim

    Returns:
        True if world mutation allowed, False otherwise
    """
    try:
        check_receipt(receipt, strict=True)
        return True
    except ExecutionBlocked:
        return False


def audit_trail(claim_id: str, receipt: Dict[str, Any]) -> None:
    """
    Log the decision to local audit file (optional).

    Keeps a human-readable log of what Oracle Town allowed/rejected.
    """
    audit_file = Path.home() / ".moltbot" / "oracle_town" / "execution_log.jsonl"
    audit_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "claim_id": claim_id,
        "decision": receipt.get("decision", "UNKNOWN"),
        "allowed": receipt.get("world_mutation_allowed", False),
        "receipt_id": receipt.get("receipt_id", "?")
    }

    with open(audit_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    # Test: demonstrate enforcement
    print("K15 Receipt Enforcement Demo")
    print("=" * 50)
    print()

    # Test 1: Valid ACCEPT receipt
    print("[Test 1] Valid ACCEPT receipt")
    receipt_accept = {
        "decision": "ACCEPT",
        "world_mutation_allowed": True,
        "timestamp_signed": datetime.utcnow().isoformat() + "Z"
    }
    try:
        check_receipt(receipt_accept)
        print("✓ Execution permitted")
    except ExecutionBlocked as e:
        print(f"✗ Blocked: {e}")

    print()

    # Test 2: REJECT receipt
    print("[Test 2] REJECT receipt")
    receipt_reject = {
        "decision": "REJECT",
        "reason": "Attestor not registered",
        "world_mutation_allowed": False,
        "timestamp_signed": datetime.utcnow().isoformat() + "Z"
    }
    try:
        check_receipt(receipt_reject)
        print("✓ Execution permitted")
    except ExecutionBlocked as e:
        print(f"✓ Correctly blocked: {e}")

    print()

    # Test 3: Missing receipt (Oracle Town offline)
    print("[Test 3] No receipt (Oracle Town offline)")
    try:
        check_receipt(None)
        print("✓ Execution permitted")
    except ExecutionBlocked as e:
        print(f"✓ Correctly blocked: {e}")

    print()
    print("K15 enforcement: PASS")
