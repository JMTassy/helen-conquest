#!/usr/bin/env python3
"""
OpenClaw ↔ Oracle Town: Claim Submission Interface

This is what OpenClaw (or any World actor) calls when it wants to do something risky.

Usage (from OpenClaw code):

  from oracle_town.kernel.submit_claim import submit_action_claim

  receipt = submit_action_claim(
    action_type="fetch",
    target="https://moltbook.com/heartbeat",
    evidence_bytes=fetched_bytes,
    intent="Check daily heartbeat instructions"
  )

  if receipt["decision"] != "ACCEPT":
    raise RuntimeError(f"Authority rejected: {receipt['reason']}")

  # Only proceed if receipt exists

Internally:
  1. Creates Claim object
  2. Runs TRI Gate (deterministic verification)
  3. Gets Mayor signature
  4. Records in ledger
  5. Returns receipt with decision

Receipt format:
  {
    "receipt_id": "R-2026-01-30-...",
    "decision": "ACCEPT" | "REJECT",
    "claim_id": "...",
    "policy_pack_hash": "sha256:...",
    "world_mutation_allowed": true | false,
    "timestamp_signed": "...",
    "mayor_signature": "..."
  }

K15: No receipt = no execution (enforced by caller, not here)
"""

import json
import sys
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Find Oracle Town root
ORACLE_TOWN_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ORACLE_TOWN_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

# Import oracle_town modules
from oracle_town.jobs.tri_gate import main as tri_gate_main
from oracle_town.jobs.mayor_sign import main as mayor_sign_main


def read_policy_hash() -> str:
    """Read frozen policy hash from oracle_town/policy_pack_hash.txt"""
    policy_file = ORACLE_TOWN_ROOT / "policy_pack_hash.txt"
    if policy_file.exists():
        return policy_file.read_text().strip()
    return "sha256:policy_v1_2026_01"  # fallback


def sha256(data: bytes) -> str:
    """Compute SHA-256 hash"""
    return hashlib.sha256(data).hexdigest()


def submit_action_claim(
    action_type: str,
    target: str,
    evidence_bytes: Optional[bytes] = None,
    intent: str = "",
    source: str = "OPENCLAW"
) -> Dict[str, Any]:
    """
    Submit an action claim to Oracle Town.

    Args:
        action_type: "fetch", "execute_skill", "write_memory", "modify_heartbeat", etc.
        target: URL, skill name, memory key, etc. (what is being acted upon)
        evidence_bytes: Raw bytes that triggered the action (e.g., fetched content)
        intent: Human-readable why this action is needed
        source: "OPENCLAW", "MOLTBOT", etc.

    Returns:
        Receipt dict with decision and world_mutation_allowed flag

    Raises:
        RuntimeError: If TRI or Mayor fails
    """

    timestamp = datetime.utcnow().isoformat() + "Z"
    claim_id = f"claim_{source.lower()}_{timestamp.replace(':', '').replace('.', '')}"

    # Build claim
    evidence = {}
    if evidence_bytes:
        evidence["raw_bytes"] = {
            "hash": sha256(evidence_bytes),
            "size": len(evidence_bytes)
        }

    claim = {
        "claim": {
            "id": claim_id,
            "timestamp": timestamp,
            "type": f"{source.lower()}_action",
            "source": source,
            "action_type": action_type,
            "target": target,
            "intent": intent or f"Execute {action_type} on {target}",
            "scope": "world_mutation",
            "evidence": evidence,
            "policy_pack_hash": read_policy_hash(),
            "generated_by": f"submit_claim.py({source})"
        }
    }

    # Write claim to temp file
    claim_file = Path("/tmp") / f"{claim_id}.json"
    with open(claim_file, 'w') as f:
        json.dump(claim, f, indent=2)

    try:
        # Run TRI Gate
        tri_verdict_file = Path("/tmp") / f"{claim_id}_tri_verdict.json"
        sys.argv = [
            "tri_gate.py",
            "--claim", str(claim_file),
            "--output", str(tri_verdict_file),
            "--policy-hash", read_policy_hash(),
            "--key-registry", str(ORACLE_TOWN_ROOT / "keys" / "public_keys.json")
        ]
        try:
            tri_gate_main()
        except SystemExit:
            pass

        if not tri_verdict_file.exists():
            raise RuntimeError("TRI Gate did not produce verdict")

        # Run Mayor
        receipt_file = Path("/tmp") / f"{claim_id}_receipt.json"
        sys.argv = [
            "mayor_sign.py",
            "--verdict", str(tri_verdict_file),
            "--claim", str(claim_file),
            "--output", str(receipt_file),
            "--policy-hash", read_policy_hash(),
            "--ledger", str(ORACLE_TOWN_ROOT / "ledger")
        ]
        try:
            mayor_sign_main()
        except SystemExit:
            pass

        if not receipt_file.exists():
            raise RuntimeError("Mayor did not produce receipt")

        # Read receipt
        with open(receipt_file, 'r') as f:
            receipt_data = json.load(f)

        receipt = receipt_data.get("receipt", {})

        # Clean up temp files (optional—leave for audit trail)
        # claim_file.unlink(missing_ok=True)
        # tri_verdict_file.unlink(missing_ok=True)

        return receipt

    except Exception as e:
        # Return REJECT on any error (fail-closed)
        return {
            "decision": "REJECT",
            "reason": f"Submission error: {str(e)}",
            "world_mutation_allowed": False,
            "claim_id": claim_id,
            "timestamp_signed": datetime.utcnow().isoformat() + "Z"
        }


def main():
    """CLI interface for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Submit action claim to Oracle Town")
    parser.add_argument("--type", required=True, help="Action type (fetch, execute, etc.)")
    parser.add_argument("--target", required=True, help="Action target (URL, skill, etc.)")
    parser.add_argument("--intent", default="", help="Human-readable intent")
    parser.add_argument("--source", default="OPENCLAW", help="Claiming source")
    parser.add_argument("--evidence-file", help="Path to evidence bytes file")

    args = parser.parse_args()

    evidence_bytes = None
    if args.evidence_file:
        with open(args.evidence_file, 'rb') as f:
            evidence_bytes = f.read()

    receipt = submit_action_claim(
        action_type=args.type,
        target=args.target,
        evidence_bytes=evidence_bytes,
        intent=args.intent,
        source=args.source
    )

    print(json.dumps(receipt, indent=2))
    sys.exit(0 if receipt.get("decision") == "ACCEPT" else 1)


if __name__ == "__main__":
    main()
