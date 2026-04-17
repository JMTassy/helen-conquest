"""
Replay Receipt Plugin

Verifies determinism by running Mayor decision N times.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from oracle_town.core.mayor_rsm import MayorRSM
from oracle_town.core.policy import Policy


def generate_receipt(
    proposal: Dict[str, Any],
    staging_dir: str,
    repo_root: str
) -> Optional[Dict[str, Any]]:
    """
    Run Mayor decision N times and verify determinism.

    Returns: Attestation dict (unsigned - Factory must sign)
    """
    # Load policy and registry
    policy_path = Path(repo_root) / "oracle_town" / "policies" / "policy_POL-PROD-1.json"
    registry_path = Path(repo_root) / "oracle_town" / "keys" / "public_keys.json"

    if not policy_path.exists() or not registry_path.exists():
        print(f"⚠️  Policy or registry not found")
        return None

    with open(policy_path) as f:
        policy = Policy.from_dict(json.load(f))

    mayor = MayorRSM(public_keys_path=str(registry_path))

    # Build mock briefcase and ledger from proposal
    briefcase = {
        "run_id": proposal['cycle_id'],
        "obligations": proposal.get('obligations_claimed', []),
        "zone_context": "oracle_town"
    }

    ledger = {
        "run_id": proposal['cycle_id'],
        "attestations": [],  # Empty for now (no real attestations yet)
    }

    # Run Mayor N times
    result = _verify_determinism(mayor, policy, briefcase, ledger, replays=5)

    # Compute evidence digest
    evidence_digest = _hash_evidence(result)

    # Build attestation (unsigned)
    attestation = {
        "attestor_class": "determinism_automation",
        "signing_key_id": "key-determinism-automation-2026",  # TODO: Get from config
        "obligation": "replay_determinism",
        "evidence_type": "mayor-replay",
        "evidence_digest": evidence_digest,
        "policy_match": 1 if result['deterministic'] else 0,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "replay_count": result['replays'],
            "unique_digests": result['unique_digests'],
            "decision_digest": result['decision_digest']
        }
    }

    return attestation


def _verify_determinism(
    mayor: MayorRSM,
    policy: Policy,
    briefcase: Dict,
    ledger: Dict,
    replays: int = 5
) -> Dict[str, Any]:
    """Run Mayor N times and check for identical decisions"""
    digests = []

    for _ in range(replays):
        decision = mayor.decide(policy, briefcase, ledger)
        digests.append(decision.decision_digest)

    # Check uniqueness
    unique = set(digests)
    deterministic = (len(unique) == 1)

    return {
        'deterministic': deterministic,
        'replays': replays,
        'unique_digests': len(unique),
        'decision_digest': digests[0] if deterministic else "NON_DETERMINISTIC"
    }


def _hash_evidence(result: Dict[str, Any]) -> str:
    """Compute SHA256 hash of canonical evidence"""
    # Canonical evidence (deterministic)
    evidence = {
        'deterministic': result['deterministic'],
        'replays': result['replays'],
        'decision_digest': result['decision_digest']
    }

    canonical = json.dumps(evidence, sort_keys=True, separators=(',', ':'))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
