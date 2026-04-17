"""
Factory: Verification & Attestation Layer (Governance Kernel)

This is the LEGORACLE v2 compliance layer:
- Takes obligations from cognition layer (teams/streets)
- Runs verification tests
- Emits attestations (truth primitives)
- Writes append-only ledger

NO REASONING. NO CONFIDENCE. Only: does evidence satisfy obligation?
"""
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Attestation:
    """
    Truth primitive: proof that an obligation was satisfied.

    This is the ONLY thing Mayor trusts. No narratives, no scores.
    """
    run_id: str
    claim_id: str
    obligation_name: str  # snake_case, matches obligation
    attestor: str  # "CI_RUNNER" | "TOOL_RESULT" | "HUMAN_SIGNATURE" | "MOCK_FACTORY"
    policy_match: int  # 0 or 1 (binary)
    payload_hash: str  # sha256 of evidence
    evidence_raw: Optional[bytes] = None  # Optional: actual evidence
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> dict:
        """Serialize for ledger (exclude raw evidence)"""
        d = asdict(self)
        d.pop("evidence_raw", None)  # Don't store raw in JSON
        return d

    def is_satisfied(self) -> bool:
        """Binary check: does this attestation satisfy?"""
        return self.policy_match == 1


@dataclass
class Briefcase:
    """
    What Factory receives from Concierge.
    Contains all obligations that need verification.
    """
    run_id: str
    claim_id: str
    required_obligations: List[Dict]  # From teams/streets
    requested_tests: List[Dict]  # Mapping: test -> obligations
    kill_switch_policies: List[str]
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {
                "compiled_at": datetime.utcnow().isoformat(),
                "source": "concierge"
            }


class Factory:
    """
    Verification & Attestation Engine.

    Constitutional Rules:
    1. Only generates attestations, never verdicts
    2. Binary satisfaction: obligation met or not
    3. Append-only ledger (no edits)
    4. Deterministic: same evidence → same attestation
    """

    def __init__(self, ledger_path: str = "attestations_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    async def verify_briefcase(self, briefcase: Briefcase) -> List[Attestation]:
        """
        Main verification loop: for each obligation, run test, emit attestation.

        For MVP: Mock attestations
        For production: Real test execution (pytest, CI, human review)
        """
        attestations = []

        for obligation in briefcase.required_obligations:
            # Find matching test
            test = self._find_test_for_obligation(
                obligation, briefcase.requested_tests
            )

            # Run verification
            attestation = await self._verify_obligation(
                obligation, test, briefcase.run_id, briefcase.claim_id
            )

            # Append to ledger
            self._append_to_ledger(attestation)

            attestations.append(attestation)

        return attestations

    async def _verify_obligation(
        self,
        obligation: Dict,
        test: Optional[Dict],
        run_id: str,
        claim_id: str,
    ) -> Attestation:
        """
        Verify a single obligation.

        For MVP: Mock verification (always returns policy_match=1)
        For production: Execute real test
        """
        obligation_name = obligation.get("name", "unknown_obligation")

        # MVP: Mock attestation (in production, run actual test)
        if test:
            # Simulate test execution
            evidence = self._mock_test_execution(test)
            policy_match = 1  # Test passed
            attestor = "MOCK_FACTORY"
        else:
            # No test found - obligation cannot be verified
            evidence = b"NO_TEST_FOUND"
            policy_match = 0
            attestor = "MOCK_FACTORY"

        # Compute evidence hash
        payload_hash = hashlib.sha256(evidence).hexdigest()

        return Attestation(
            run_id=run_id,
            claim_id=claim_id,
            obligation_name=obligation_name,
            attestor=attestor,
            policy_match=policy_match,
            payload_hash=payload_hash,
            evidence_raw=evidence,
        )

    def _find_test_for_obligation(
        self, obligation: Dict, tests: List[Dict]
    ) -> Optional[Dict]:
        """Find test that verifies this obligation"""
        obl_name = obligation.get("name", "")

        for test in tests:
            if test.get("obligation_name") == obl_name:
                return test

        # Default: create mock test
        return {
            "obligation_name": obl_name,
            "test_type": "mock",
            "expected_evidence": obligation.get("required_evidence", []),
        }

    def _mock_test_execution(self, test: Dict) -> bytes:
        """
        Mock test execution (returns synthetic evidence).

        In production: subprocess.run(test_command) → capture output
        """
        return json.dumps({
            "test": test.get("obligation_name"),
            "result": "PASS",
            "timestamp": datetime.utcnow().isoformat(),
            "evidence": "Mock evidence for MVP"
        }).encode()

    def _append_to_ledger(self, attestation: Attestation):
        """Append attestation to ledger (append-only)"""
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(attestation.to_json()) + "\n")

    def read_ledger(self, run_id: Optional[str] = None) -> List[Attestation]:
        """Read attestations from ledger (optionally filtered by run_id)"""
        attestations = []

        if not self.ledger_path.exists():
            return attestations

        with open(self.ledger_path, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                if run_id is None or data.get("run_id") == run_id:
                    # Reconstruct attestation (without evidence_raw)
                    attestations.append(Attestation(**data))

        return attestations

    def check_satisfaction(
        self,
        obligations: List[Dict],
        attestations: List[Attestation],
    ) -> tuple[List[str], List[str]]:
        """
        Deterministic satisfaction check.

        Returns:
            (satisfied_obligations, unsatisfied_obligations)
        """
        satisfied = []
        unsatisfied = []

        obl_names = {o.get("name") for o in obligations}
        attestation_map = {
            a.obligation_name: a for a in attestations if a.is_satisfied()
        }

        for obl_name in obl_names:
            if obl_name in attestation_map:
                satisfied.append(obl_name)
            else:
                unsatisfied.append(obl_name)

        return satisfied, unsatisfied


# Test
if __name__ == "__main__":
    import asyncio

    async def test_factory():
        # Create mock briefcase
        briefcase = Briefcase(
            run_id="RUN_TEST_001",
            claim_id="CLM_TEST_001",
            required_obligations=[
                {
                    "name": "gdpr_consent_mechanism",
                    "type": "DOC_SIGNATURE",
                    "severity": "HARD",
                    "required_evidence": ["consent_flow_diagram"]
                },
                {
                    "name": "vendor_dpa_confirmation",
                    "type": "DOC_SIGNATURE",
                    "severity": "HARD",
                    "required_evidence": ["dpa_signed"]
                }
            ],
            requested_tests=[
                {
                    "obligation_name": "gdpr_consent_mechanism",
                    "test_type": "document_check",
                    "expected_evidence": ["consent_flow_diagram"]
                }
            ],
            kill_switch_policies=[]
        )

        # Run factory
        factory = Factory(ledger_path="test_attestations.jsonl")
        attestations = await factory.verify_briefcase(briefcase)

        print("=" * 70)
        print("FACTORY VERIFICATION RESULTS")
        print("=" * 70)

        for att in attestations:
            status = "✅ SATISFIED" if att.is_satisfied() else "❌ UNSATISFIED"
            print(f"{status} | {att.obligation_name}")
            print(f"  Attestor: {att.attestor}")
            print(f"  Evidence Hash: {att.payload_hash[:16]}...")
            print()

        # Check satisfaction
        satisfied, unsatisfied = factory.check_satisfaction(
            briefcase.required_obligations, attestations
        )

        print("=" * 70)
        print("SATISFACTION CHECK")
        print("=" * 70)
        print(f"Satisfied: {len(satisfied)}")
        for obl in satisfied:
            print(f"  ✅ {obl}")
        print(f"\nUnsatisfied: {len(unsatisfied)}")
        for obl in unsatisfied:
            print(f"  ❌ {obl}")

    asyncio.run(test_factory())
