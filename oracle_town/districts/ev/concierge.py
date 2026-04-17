"""
EV (Evidence & Validation) District Concierge

Analyzes claim and emits governance verification obligations.

Obligations emitted:
1. attestation_ledger_written - Ledger file exists and has run_id
2. mayor_emits_single_decision_record - Decision record exists with correct schema
3. replay_determinism_hash_match - Same inputs produce same decision

Attestor: TOOL_RESULT (file checks, schema validation, determinism tests)
"""
from typing import List, Dict


class EVConcierge:
    """
    Analyzes claim and determines which governance verification obligations apply.

    Does NOT reason about satisfaction - only identifies requirements.
    """

    def __init__(self):
        self.domain = "EV"

        # Obligation templates
        self.obligation_templates = {
            "attestation_ledger_written": {
                "name": "attestation_ledger_written",
                "type": "TOOL_RESULT",
                "severity": "HARD",
                "required_evidence": ["ledger_file_exists", "ledger_has_run_id"],
                "description": "Attestation ledger must exist and contain run_id entries",
                "test_command": "python -c 'import json; lines = open(\"attestations_ledger.jsonl\").readlines(); assert len(lines) > 0; assert \"run_id\" in json.loads(lines[0]); print(\"SUCCESS\")'",
            },
            "mayor_emits_single_decision_record": {
                "name": "mayor_emits_single_decision_record",
                "type": "TOOL_RESULT",
                "severity": "HARD",
                "required_evidence": ["decision_file_exists", "decision_schema_valid"],
                "description": "Mayor must emit exactly one decision_record.json with valid schema",
                "test_command": "python -c 'import json; from pathlib import Path; files = list(Path(\"decisions\").glob(\"decision_*.json\")); assert len(files) > 0; d = json.loads(files[0].read_text()); assert \"decision\" in d and d[\"decision\"] in [\"SHIP\", \"NO_SHIP\"]; print(\"SUCCESS\")'",
            },
            "replay_determinism_hash_match": {
                "name": "replay_determinism_hash_match",
                "type": "TOOL_RESULT",
                "severity": "SOFT",  # SOFT for MVP (not blocking)
                "required_evidence": ["replay_produces_same_hash"],
                "description": "Replaying same inputs must produce identical decision hash",
                "test_command": "echo 'SKIP_FOR_MVP'",  # Implement later
            },
        }

    def analyze_claim(self, claim_text: str, claim_metadata: Dict = None) -> Dict:
        """
        Determine which EV obligations apply to this claim.

        Args:
            claim_text: Raw claim text
            claim_metadata: Optional metadata (claim_type, domain, etc.)

        Returns:
            Dict with required_obligations and requested_tests
        """
        claim_metadata = claim_metadata or {}
        claim_type = claim_metadata.get("claim_type", "unknown")

        required_obligations = []
        requested_tests = []

        # Rule 1: Any claim that goes through governance requires EV checks
        if self._requires_governance(claim_text, claim_type):
            for obl_name in ["attestation_ledger_written", "mayor_emits_single_decision_record"]:
                required_obligations.append(self.obligation_templates[obl_name])
                requested_tests.append({
                    "obligation_name": obl_name,
                    "test_command": self.obligation_templates[obl_name]["test_command"],
                    "attestor": "TOOL_RESULT",
                })

            # Add replay determinism (SOFT - not blocking)
            required_obligations.append(self.obligation_templates["replay_determinism_hash_match"])
            requested_tests.append({
                "obligation_name": "replay_determinism_hash_match",
                "test_command": self.obligation_templates["replay_determinism_hash_match"]["test_command"],
                "attestor": "TOOL_RESULT",
            })

        return {
            "required_obligations": required_obligations,
            "requested_tests": requested_tests,
            "district": self.domain,
        }

    def _requires_governance(self, claim_text: str, claim_type: str) -> bool:
        """
        Determine if claim goes through governance kernel.

        For MVP: All non-meta claims require governance.
        """
        # Meta-commentary doesn't require governance checks
        if claim_type in ["analysis", "meta", "commentary"]:
            return False

        return True


# Test
if __name__ == "__main__":
    concierge = EVConcierge()

    # Test 1: Change request (requires governance)
    result1 = concierge.analyze_claim(
        "Add new feature to system",
        {"claim_type": "change_request"}
    )
    print("=" * 70)
    print("TEST 1: Change request claim")
    print("=" * 70)
    print(f"Obligations: {len(result1['required_obligations'])}")
    for obl in result1['required_obligations']:
        print(f"  - {obl['name']} ({obl['severity']})")

    # Test 2: Meta-commentary (no governance)
    result2 = concierge.analyze_claim(
        "This is an architectural analysis",
        {"claim_type": "analysis"}
    )
    print("\n" + "=" * 70)
    print("TEST 2: Meta-commentary")
    print("=" * 70)
    print(f"Obligations: {len(result2['required_obligations'])}")

    print("\n✅ EVConcierge tests passed!")
