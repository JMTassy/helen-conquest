"""
ORACLE builders (EMULATED builders with test content)

Key design choice: user enters natural language claim, but WUL token trees never store free text.
We derive a deterministic identifier ref from sha256(claim_text).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mayor.decide import sha256_hex


def _ref_from_text(prefix: str, text: str, n: int = 16) -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
    return f"{prefix}_{h[:n]}"


def build_wul_token_tree(claim_text: str, objective_ref: str = "OBJECTIVE_MAIN") -> Dict[str, Any]:
    """
    Build minimal WUL token tree satisfying R15 requirement.

    Structure: R15(OBJECTIVE(ref), CLAIM(PROPOSITION(ref)))
    Uses structured format with 'id' and 'args' keys.
    """
    prop_ref = _ref_from_text("PROP", claim_text)
    return {
        "id": "R15",
        "args": [
            {"id": "E03", "args": [], "ref": objective_ref},
            {"id": "D01", "args": [{"id": "E01", "args": [], "ref": prop_ref}]}
        ]
    }


def build_tribunal_bundle(claim_text: str) -> Dict[str, Any]:
    """
    Minimal stable HARD set for emulator.
    You can expand by claim categories, but keep it deterministic.
    """
    hard: List[Dict[str, Any]] = [
        {"name": "schema_validation", "severity": "HARD", "expected_attestor": "CI_RUNNER"},
        {"name": "allowlist_check", "severity": "HARD", "expected_attestor": "CI_RUNNER"},
        {"name": "purity_check", "severity": "HARD", "expected_attestor": "CI_RUNNER"}
    ]

    # Example: if claim mentions "publish" add an extra hard obligation (deterministic rule)
    if "publish" in claim_text.lower():
        hard.append({"name": "public_snapshot_ready", "severity": "HARD", "expected_attestor": "CI_RUNNER"})

    return {"required_obligations": hard}


def build_policies(claim_text: str) -> Dict[str, Any]:
    """
    Kill-switch emulation:
    - if claim contains disallowed keywords, kill_switches_pass = False
    This is intentionally blunt; real system uses policy bundle.
    """
    lowered = claim_text.lower()
    forbidden = ["free text", "ignore rules", "bypass", "override"]
    kill_pass = not any(k in lowered for k in forbidden)
    return {"kill_switches_pass": kill_pass}


def build_receipt_root_payload(token_tree: Dict[str, Any], tribunal_bundle: Dict[str, Any], policies: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic receipt root placeholder. In real system: pins, hashes, artifact listing.
    """
    return {
        "kind": "RECEIPT_ROOT_PAYLOAD",
        "version": "v0",
        "pins": {
            "wul_tree_hash": sha256_hex(token_tree),
            "tribunal_hash": sha256_hex(tribunal_bundle),
            "policies_hash": sha256_hex(policies)
        }
    }


def build_initial_attestations_ledger(mode: str) -> Dict[str, Any]:
    """
    mode:
      - "empty": no attestations
      - "partial": only schema_validation passes
      - "full": all pass
    """
    if mode == "full":
        return {
            "attestations": [
                {"obligation_name": "schema_validation", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True},
                {"obligation_name": "allowlist_check", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True},
                {"obligation_name": "purity_check", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True},
                {"obligation_name": "public_snapshot_ready", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True}
            ]
        }
    if mode == "partial":
        return {
            "attestations": [
                {"obligation_name": "schema_validation", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True}
            ]
        }
    return {"attestations": []}
