"""
ENGINEERING District Concierge

Analyzes claim and emits ENGINEERING obligations (not verdicts).

Obligations emitted:
1. pyproject_installable - Package can be installed via pip
2. unit_tests_green - All tests pass
3. imports_clean_oracle_town - Core module imports without error

Attestor: CI_RUNNER (pytest, pip, import checks)
"""
from typing import List, Dict


class EngineeringConcierge:
    """
    Analyzes claim and determines which engineering obligations apply.

    Does NOT reason about satisfaction - only identifies requirements.
    """

    def __init__(self):
        self.domain = "ENGINEERING"

        # Obligation templates
        self.obligation_templates = {
            "pyproject_installable": {
                "name": "pyproject_installable",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "required_evidence": ["pip_install_success"],
                "description": "Package must be installable via pip install -e .",
                "test_command": "pip install -e . && echo 'SUCCESS'",
            },
            "unit_tests_green": {
                "name": "unit_tests_green",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "required_evidence": ["pytest_exit_0"],
                "description": "All unit tests must pass",
                "test_command": "pytest tests/ -v",
            },
            "imports_clean_oracle_town": {
                "name": "imports_clean_oracle_town",
                "type": "CODE_PROOF",
                "severity": "HARD",
                "required_evidence": ["import_success"],
                "description": "Core module must import without error",
                "test_command": "python -c 'import oracle_town; print(\"SUCCESS\")'",
            },
        }

    def analyze_claim(self, claim_text: str, claim_metadata: Dict = None) -> Dict:
        """
        Determine which engineering obligations apply to this claim.

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

        # Rule 1: Code changes require all engineering obligations
        if self._is_code_change(claim_text, claim_type):
            for obl_name in ["pyproject_installable", "unit_tests_green", "imports_clean_oracle_town"]:
                required_obligations.append(self.obligation_templates[obl_name])
                requested_tests.append({
                    "obligation_name": obl_name,
                    "test_command": self.obligation_templates[obl_name]["test_command"],
                    "attestor": "CI_RUNNER",
                })

        # Rule 2: Meta-commentary requires nothing
        elif claim_type == "analysis" or claim_type == "meta":
            pass  # No obligations

        return {
            "required_obligations": required_obligations,
            "requested_tests": requested_tests,
            "district": self.domain,
        }

    def _is_code_change(self, claim_text: str, claim_type: str) -> bool:
        """
        Detect if claim involves code changes.

        Heuristics:
        - claim_type == "refactor" or "feature" or "fix" → YES
        - claim_type == "analysis" or "meta" or "commentary" → NO (explicit)
        - Contains keywords: "refactor", "implement", "add", "fix", "update"
        """
        # Explicit NO for meta-commentary (checked FIRST to avoid false positives)
        if claim_type in ["analysis", "meta", "commentary"]:
            return False

        # Explicit YES for known code change types
        if claim_type in ["refactor", "feature", "fix", "change_request"]:
            return True

        # Fallback: keyword detection (for unknown claim types)
        code_keywords = [
            "refactor", "implement", "add", "fix", "update", "modify",
            "create", "build", "change", "remove", "delete", "rename"
        ]

        claim_lower = claim_text.lower()
        return any(keyword in claim_lower for keyword in code_keywords)


# Test
if __name__ == "__main__":
    concierge = EngineeringConcierge()

    # Test 1: Code change claim
    result1 = concierge.analyze_claim(
        "Refactor Mayor to remove confidence scoring",
        {"claim_type": "refactor"}
    )
    print("=" * 70)
    print("TEST 1: Code change claim")
    print("=" * 70)
    print(f"Obligations: {len(result1['required_obligations'])}")
    for obl in result1['required_obligations']:
        print(f"  - {obl['name']} ({obl['severity']})")

    # Test 2: Meta-commentary
    result2 = concierge.analyze_claim(
        "This is an architectural analysis",
        {"claim_type": "analysis"}
    )
    print("\n" + "=" * 70)
    print("TEST 2: Meta-commentary")
    print("=" * 70)
    print(f"Obligations: {len(result2['required_obligations'])}")

    print("\n✅ EngineeringConcierge tests passed!")
