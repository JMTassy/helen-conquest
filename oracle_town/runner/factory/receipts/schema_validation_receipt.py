"""
Schema Validation Receipt Plugin

Validates proposal against JSON Schema.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def generate_receipt(
    proposal: Dict[str, Any],
    staging_dir: str,
    repo_root: str
) -> Optional[Dict[str, Any]]:
    """
    Validate proposal against schema and generate attestation.

    Returns: Attestation dict (unsigned - Factory must sign)
    """
    if not JSONSCHEMA_AVAILABLE:
        print("⚠️  jsonschema not available, skipping schema validation")
        return None

    # Load schema
    schema_path = Path(repo_root) / "oracle_town" / "schemas" / "proposal_bundle.schema.json"

    if not schema_path.exists():
        print(f"⚠️  Schema not found: {schema_path}")
        return None

    with open(schema_path) as f:
        schema = json.load(f)

    # Validate
    result = _validate_schema(proposal, schema)

    # Compute evidence digest
    evidence_digest = _hash_evidence(result)

    # Build attestation (unsigned)
    attestation = {
        "attestor_class": "schema_automation",
        "signing_key_id": "key-schema-automation-2026",  # TODO: Get from config
        "obligation": "schema_compliance",
        "evidence_type": "jsonschema-validation",
        "evidence_digest": evidence_digest,
        "policy_match": 1 if result['valid'] else 0,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {
            "schema_version": schema.get('$id', 'unknown'),
            "validation_errors": result.get('errors', [])
        }
    }

    return attestation


def _validate_schema(proposal: Dict[str, Any], schema: Dict) -> Dict[str, Any]:
    """Validate proposal against schema"""
    try:
        # Validate using jsonschema
        jsonschema.validate(instance=proposal, schema=schema)

        return {
            'valid': True,
            'errors': []
        }

    except jsonschema.ValidationError as e:
        return {
            'valid': False,
            'errors': [str(e.message)]
        }
    except Exception as e:
        return {
            'valid': False,
            'errors': [f"Validation error: {str(e)}"]
        }


def _hash_evidence(result: Dict[str, Any]) -> str:
    """Compute SHA256 hash of canonical evidence"""
    # Canonical evidence (deterministic)
    evidence = {
        'valid': result['valid'],
        'error_count': len(result.get('errors', []))
    }

    canonical = json.dumps(evidence, sort_keys=True, separators=(',', ':'))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()}"
