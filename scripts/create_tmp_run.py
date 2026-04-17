from oracle_town.core.policy import create_default_policy
from oracle_town.core.crypto import canonical_json_bytes, sign_ed25519
from pathlib import Path
import json
from datetime import datetime

# Load private keys example
pk_path = Path('oracle_town/keys/private_keys_TEST_ONLY.json.example')
priv = json.loads(pk_path.read_text())

# Create policy
policy = create_default_policy()
policy_dict = policy.to_dict()
policy_file = Path('tmp_policy.json')
policy_file.write_text(json.dumps(policy_dict, indent=2))
print('Wrote', policy_file)

# Build briefcase
briefcase = {
    "run_id": "R-TEST-001",
    "claim_id": "CLM-TEST-001",
    "claim_type": "CHANGE_REQUEST",
    "required_obligations": [
        {
            "name": "gdpr_consent_banner",
            "type": "CODE_PROOF",
            "severity": "HARD",
            "description": "Implement GDPR consent banner",
            "required_evidence": ["consent_flow_diagram"]
        }
    ],
    "requested_tests": [],
    "kill_switch_policies": [],
    "metadata": {"policy_hash": policy.policy_hash}
}
Path('tmp_briefcase.json').write_text(json.dumps(briefcase, indent=2))
print('Wrote tmp_briefcase.json')

# Prepare two attestations and sign them

a1 = {
    "attestation_id": "ATT-T1",
    "run_id": briefcase["run_id"],
    "claim_id": briefcase["claim_id"],
    "obligation_name": "gdpr_consent_banner",
    "attestor_id": "ci_runner_01",
    "attestor_class": "CI_RUNNER",
    "policy_hash": policy.policy_hash,
    "evidence_digest": "sha256:abc123",
    "signing_key_id": "key-2026-01-ci",
    "signature": "",
    "policy_match": 1,
    "timestamp": datetime.utcnow().isoformat()
}

a2 = {
    "attestation_id": "ATT-T2",
    "run_id": briefcase["run_id"],
    "claim_id": briefcase["claim_id"],
    "obligation_name": "gdpr_consent_banner",
    "attestor_id": "legal_reviewer_01",
    "attestor_class": "LEGAL",
    "policy_hash": policy.policy_hash,
    "evidence_digest": "sha256:ghi789",
    "signing_key_id": "key-2026-01-legal",
    "signature": "",
    "policy_match": 1,
    "timestamp": datetime.utcnow().isoformat()
}

# Sign using example private keys (base64 seeds)
a_list = [a1,a2]
for a in a_list:
    # build canonical message
    msg = {
        "run_id": a['run_id'],
        "claim_id": a['claim_id'],
        "obligation_name": a['obligation_name'],
        "attestor_id": a['attestor_id'],
        "attestor_class": a['attestor_class'],
        "policy_hash": a['policy_hash'],
        "key_registry_hash": None,
        "evidence_digest": a['evidence_digest'],
        "policy_match": a['policy_match']
    }
    mb = canonical_json_bytes(msg)
    seed_b64 = priv[a['signing_key_id']]
    sig = sign_ed25519(seed_b64, mb)
    a['signature'] = 'ed25519:' + sig

ledger = {
    "run_id": briefcase["run_id"],
    "claim_id": briefcase["claim_id"],
    "policy_hash": policy.policy_hash,
    "attestations": a_list,
    "ledger_digest": "sha256:ledger-test",
    "timestamp": datetime.utcnow().isoformat()
}
Path('tmp_ledger.json').write_text(json.dumps(ledger, indent=2))
print('Wrote tmp_ledger.json')
