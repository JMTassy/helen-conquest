"""
Mayor V2: Constitutional Verdict Engine (LEGORACLE v2 compliant)

NO REASONING. NO CONFIDENCE. NO NARRATIVE.
Only: lookup attestations → apply constitutional rules → emit decision.

Constitutional Rules (immutable):
1. IF kill_switch_triggered → NO_SHIP
2. ELSE IF any_unsatisfied_hard_obligations → NO_SHIP
3. ELSE → SHIP

That's it. No scoring. No probabilistic reasoning.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

from oracle_town.core.factory import Attestation, Briefcase


@dataclass
class DecisionRecord:
    """
    Mayor's ONLY output: binary decision + blocking obligations.

    This is what gets published. Everything else is internal telemetry.
    """
    run_id: str
    claim_id: str
    decision: str  # "SHIP" | "NO_SHIP"
    blocking_obligations: List[str]  # List of unsatisfied obligation names
    kill_switch_triggered: bool
    attestations_checked: int
    timestamp: str = ""
    code_version: str = "oracle_town_v2.0.0"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> dict:
        return asdict(self)

    def save(self, output_dir: str = "decisions"):
        """Save decision record to file"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"decision_{self.run_id}.json"
        filepath = output_path / filename

        with open(filepath, "w") as f:
            json.dump(self.to_json(), f, indent=2)

        return str(filepath)


@dataclass
class RemediationPlan:
    """
    Optional output if NO_SHIP: what obligations need satisfaction.

    This is NOT part of verdict logic. It's a helper for humans.
    """
    run_id: str
    claim_id: str
    unsatisfied_obligations: List[Dict]  # Obligations that blocked SHIP
    suggested_actions: List[Dict]  # How to get attestations
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def save(self, output_dir: str = "decisions"):
        """Save remediation plan"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"remediation_{self.run_id}.json"
        filepath = output_path / filename

        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)

        return str(filepath)


class MayorV2:
    """
    Constitutional verdict engine (LEGORACLE v2 compliant).

    Input: Briefcase (obligations) + Attestations (proofs)
    Output: DecisionRecord (SHIP | NO_SHIP)

    NO reasoning about truth. Only checks:
    - Do attestations exist for all HARD obligations?
    - Was kill-switch triggered?
    """

    def __init__(self, kill_switch_teams: List[str] = None):
        self.kill_switch_teams = kill_switch_teams or [
            "LEGAL",
            "SECURITY"
        ]

    async def decide(
        self,
        briefcase: Briefcase,
        attestations: List[Attestation],
        kill_switch_signals: Optional[List[str]] = None,
    ) -> DecisionRecord:
        """
        Apply constitutional rules to produce verdict.

        Args:
            briefcase: Obligations to satisfy
            attestations: Proofs from Factory
            kill_switch_signals: Optional kill-switch triggers

        Returns:
            DecisionRecord with binary decision
        """
        kill_switch_signals = kill_switch_signals or []

        # Rule 1: Check kill-switch
        kill_switch_triggered = self._check_kill_switch(kill_switch_signals)
        if kill_switch_triggered:
            return DecisionRecord(
                run_id=briefcase.run_id,
                claim_id=briefcase.claim_id,
                decision="NO_SHIP",
                blocking_obligations=[],
                kill_switch_triggered=True,
                attestations_checked=len(attestations),
            )

        # Rule 2: Check obligation satisfaction
        hard_obligations = [
            obl for obl in briefcase.required_obligations
            if obl.get("severity") == "HARD"
        ]

        satisfied_names = {
            att.obligation_name for att in attestations
            if att.is_satisfied()
        }

        unsatisfied = [
            obl["name"] for obl in hard_obligations
            if obl["name"] not in satisfied_names
        ]

        if unsatisfied:
            return DecisionRecord(
                run_id=briefcase.run_id,
                claim_id=briefcase.claim_id,
                decision="NO_SHIP",
                blocking_obligations=unsatisfied,
                kill_switch_triggered=False,
                attestations_checked=len(attestations),
            )

        # Rule 3: All checks pass → SHIP
        return DecisionRecord(
            run_id=briefcase.run_id,
            claim_id=briefcase.claim_id,
            decision="SHIP",
            blocking_obligations=[],
            kill_switch_triggered=False,
            attestations_checked=len(attestations),
        )

    def _check_kill_switch(self, signals: List[str]) -> bool:
        """Check if any authorized team triggered kill-switch"""
        return any(
            signal.upper() in [team.upper() for team in self.kill_switch_teams]
            for signal in signals
        )

    async def generate_remediation(
        self,
        briefcase: Briefcase,
        decision: DecisionRecord,
    ) -> Optional[RemediationPlan]:
        """
        Generate remediation plan for NO_SHIP verdicts.

        Returns actionable steps to satisfy unsatisfied obligations.
        """
        if decision.decision == "SHIP":
            return None  # No remediation needed

        # Get unsatisfied obligations
        unsatisfied_obligations = [
            obl for obl in briefcase.required_obligations
            if obl["name"] in decision.blocking_obligations
        ]

        # Generate suggested actions
        suggested_actions = []
        for obl in unsatisfied_obligations:
            action = self._suggest_action_for_obligation(obl)
            suggested_actions.append(action)

        return RemediationPlan(
            run_id=briefcase.run_id,
            claim_id=briefcase.claim_id,
            unsatisfied_obligations=unsatisfied_obligations,
            suggested_actions=suggested_actions,
        )

    def _suggest_action_for_obligation(self, obligation: Dict) -> Dict:
        """
        Suggest concrete action to satisfy obligation.

        NOT narrative reasoning. Just: what test/evidence is needed?
        """
        obl_type = obligation.get("type", "UNKNOWN")
        obl_name = obligation.get("name", "unknown")

        action_templates = {
            "CODE_PROOF": {
                "action": "Run automated test",
                "command": f"pytest tests/test_{obl_name}.py",
                "expected_attestor": "CI_RUNNER",
            },
            "TOOL_RESULT": {
                "action": "Execute verification tool",
                "command": f"tool verify {obl_name}",
                "expected_attestor": "TOOL_RESULT",
            },
            "DOC_SIGNATURE": {
                "action": "Obtain signed document",
                "command": "Request human signature",
                "expected_attestor": "HUMAN_SIGNATURE",
            },
            "METRIC_SNAPSHOT": {
                "action": "Capture metric",
                "command": f"monitor capture {obl_name}",
                "expected_attestor": "TOOL_RESULT",
            },
        }

        template = action_templates.get(obl_type, {
            "action": f"Satisfy {obl_name}",
            "command": "Manual verification required",
            "expected_attestor": "HUMAN_SIGNATURE",
        })

        return {
            "obligation_name": obl_name,
            "obligation_type": obl_type,
            **template,
            "required_evidence": obligation.get("required_evidence", []),
        }


# Test
if __name__ == "__main__":
    import asyncio

    async def test_mayor_v2():
        # Test case 1: All obligations satisfied → SHIP
        briefcase1 = Briefcase(
            run_id="RUN_TEST_001",
            claim_id="CLM_TEST_001",
            required_obligations=[
                {
                    "name": "gdpr_consent",
                    "severity": "HARD",
                    "type": "DOC_SIGNATURE",
                }
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        attestations1 = [
            Attestation(
                run_id="RUN_TEST_001",
                claim_id="CLM_TEST_001",
                obligation_name="gdpr_consent",
                attestor="MOCK_FACTORY",
                policy_match=1,
                payload_hash="abc123",
            )
        ]

        mayor = MayorV2()
        decision1 = await mayor.decide(briefcase1, attestations1)

        print("=" * 70)
        print("TEST 1: All obligations satisfied")
        print("=" * 70)
        print(f"Decision: {decision1.decision}")
        print(f"Blocking: {decision1.blocking_obligations}")
        print(f"Kill-switch: {decision1.kill_switch_triggered}")
        assert decision1.decision == "SHIP", "Should SHIP when all satisfied"

        # Test case 2: Unsatisfied obligation → NO_SHIP
        briefcase2 = Briefcase(
            run_id="RUN_TEST_002",
            claim_id="CLM_TEST_002",
            required_obligations=[
                {
                    "name": "security_audit",
                    "severity": "HARD",
                    "type": "CODE_PROOF",
                }
            ],
            requested_tests=[],
            kill_switch_policies=[],
        )

        attestations2 = []  # No attestations

        decision2 = await mayor.decide(briefcase2, attestations2)

        print("\n" + "=" * 70)
        print("TEST 2: Unsatisfied obligation")
        print("=" * 70)
        print(f"Decision: {decision2.decision}")
        print(f"Blocking: {decision2.blocking_obligations}")
        assert decision2.decision == "NO_SHIP", "Should NO_SHIP when unsatisfied"

        # Generate remediation
        remediation = await mayor.generate_remediation(briefcase2, decision2)
        print(f"\nRemediation actions: {len(remediation.suggested_actions)}")
        for action in remediation.suggested_actions:
            print(f"  - {action['action']}: {action['command']}")

        # Test case 3: Kill-switch → NO_SHIP
        briefcase3 = Briefcase(
            run_id="RUN_TEST_003",
            claim_id="CLM_TEST_003",
            required_obligations=[],
            requested_tests=[],
            kill_switch_policies=[],
        )

        decision3 = await mayor.decide(
            briefcase3, [], kill_switch_signals=["LEGAL"]
        )

        print("\n" + "=" * 70)
        print("TEST 3: Kill-switch triggered")
        print("=" * 70)
        print(f"Decision: {decision3.decision}")
        print(f"Kill-switch: {decision3.kill_switch_triggered}")
        assert decision3.kill_switch_triggered, "Should detect kill-switch"

        print("\n✅ All tests passed!")

    asyncio.run(test_mayor_v2())
