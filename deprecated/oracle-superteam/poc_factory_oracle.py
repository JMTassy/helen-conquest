"""
POC FACTORY ORACLE — Reference Implementation
Version: 1.0-FINAL

POC FACTORY ORACLE = Superteam builders generate obligations for ideas;
                     the Factory turns obligations into attestations;
                     the Tribunal ships only what has receipts.
"""

from dataclasses import dataclass, asdict
from typing import Literal, Optional, List, Dict, Any
import json
import hashlib
import hmac
from datetime import datetime
import os


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

TeamType = Literal["MARKETING", "ENGINEERING", "RESEARCH", "EV", "LEGAL"]
ObligationType = Literal["CODE_PROOF", "TOOL_RESULT", "METRIC_SNAPSHOT", "DOC_SIGNATURE"]
ObligationSeverity = Literal["HARD", "SOFT"]
ExpectedAttestor = Literal["CI_RUNNER", "TOOL_RESULT", "GMAIL_TOOL", "GCAL_TOOL", "HUMAN_SIGNATURE"]
TierType = Literal["I", "II", "III"]
VerdictType = Literal["SHIP", "NO_SHIP"]
FloorType = Literal["F1_EXECUTOR", "F2_VERIFIER", "F3_PUBLISHER"]


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ProposedObligation:
    """Obligation proposed by a Superteam."""
    type: ObligationType
    name: str                          # snake_case
    attestable: bool                   # Must be True
    severity: ObligationSeverity
    expected_attestor: ExpectedAttestor


@dataclass
class SuperteamOutput:
    """Output from a single Superteam Builder."""
    team: TeamType
    upgrade_hypothesis: str            # One sentence
    risks: List[str]                   # 1-3 risks
    proposed_obligations: List[ProposedObligation]
    baseline_comparison_required: bool


@dataclass
class Claim:
    """Claim candidate for evaluation."""
    claim_id: str
    claim_text: str
    tier_default: TierType


@dataclass
class RequiredObligation:
    """Merged obligation from Superteams."""
    name: str
    type: ObligationType
    severity: ObligationSeverity
    expected_attestor: ExpectedAttestor


@dataclass
class RequestedTest:
    """Test to be executed by Factory."""
    test_id: str
    procedure: str
    artifact_paths: List[str]
    maps_to_obligation: str


@dataclass
class Constraints:
    """Kill-switch policies and requirements."""
    kill_switch_policies: List[str]
    baseline_comparison_required: bool


@dataclass
class Briefcase:
    """Input to Factory Building."""
    run_id: str
    claim_candidates: List[Claim]
    required_obligations: List[RequiredObligation]
    requested_tests: List[RequestedTest]
    constraints: Constraints


@dataclass
class ExecutionResult:
    """Output from F1_EXECUTOR."""
    test_id: str
    status: Literal["SUCCESS", "FAILURE", "TIMEOUT", "VIOLATION"]
    artifact_paths: List[str]
    stdout: str
    stderr: str
    exit_code: int


@dataclass
class VerificationResult:
    """Output from F2_VERIFIER."""
    test_id: str
    obligation_name: str
    attestation_valid: bool
    payload_hash: str                  # sha256:...
    artifact_hashes: Dict[str, str]    # path -> sha256:...
    verification_log: str


@dataclass
class Attestation:
    """Published attestation record."""
    attestation_id: str
    run_id: str
    claim_id: str
    obligation_name: str
    attestor: ExpectedAttestor
    attestation_valid: bool
    payload_hash: str
    artifact_hashes: Dict[str, str]
    signature: str
    timestamp: str
    policy_match: int                  # 1 or 0


@dataclass
class TribunalVerdict:
    """Final decision from Tribunal."""
    tribunal: str                      # "INTEGRATOR"
    run_id: str
    claim_id: str
    verdict: VerdictType
    ship_permitted: bool
    reason_codes: List[str]
    tier_promotion: TierType
    timestamp: str


# ============================================================================
# MOCK SUPERTEAM BUILDERS (Deterministic for POC)
# ============================================================================

class MockSuperteamBuilder:
    """Mock Superteam Builder for POC demonstration."""

    @staticmethod
    def engineering_builder(claim: Claim) -> SuperteamOutput:
        """ENGINEERING team lens: determinism, architecture, CI/CD, performance."""
        return SuperteamOutput(
            team="ENGINEERING",
            upgrade_hypothesis=f"Implement solution for: {claim.claim_text}",
            risks=[
                "Memory exhaustion under load",
                "Non-deterministic behavior in concurrent scenarios"
            ],
            proposed_obligations=[
                ProposedObligation(
                    type="METRIC_SNAPSHOT",
                    name="latency_p99_under_threshold",
                    attestable=True,
                    severity="HARD",
                    expected_attestor="CI_RUNNER"
                ),
                ProposedObligation(
                    type="CODE_PROOF",
                    name="deterministic_replay_verified",
                    attestable=True,
                    severity="HARD",
                    expected_attestor="CI_RUNNER"
                )
            ],
            baseline_comparison_required=True
        )

    @staticmethod
    def research_builder(claim: Claim) -> SuperteamOutput:
        """RESEARCH team lens: epistemic validity, eval design, statistical rigor."""
        return SuperteamOutput(
            team="RESEARCH",
            upgrade_hypothesis=f"Validate hypothesis with rigorous benchmarks: {claim.claim_text}",
            risks=[
                "Synthetic benchmarks don't match production",
                "Statistical significance not achieved"
            ],
            proposed_obligations=[
                ProposedObligation(
                    type="METRIC_SNAPSHOT",
                    name="benchmark_statistical_significance",
                    attestable=True,
                    severity="HARD",
                    expected_attestor="CI_RUNNER"
                ),
                ProposedObligation(
                    type="TOOL_RESULT",
                    name="regression_test_suite_passed",
                    attestable=True,
                    severity="SOFT",
                    expected_attestor="CI_RUNNER"
                )
            ],
            baseline_comparison_required=True
        )


# ============================================================================
# SUPERTEAM MERGER (Dedupe Obligations)
# ============================================================================

def merge_superteam_outputs(outputs: List[SuperteamOutput]) -> List[RequiredObligation]:
    """
    Merge and dedupe obligations from all Superteams.

    Rules:
    - Dedupe by obligation name (case-insensitive)
    - Preserve highest severity (HARD > SOFT)
    - Stable ordering (by name)
    """
    seen = {}

    for output in outputs:
        for obl in output.proposed_obligations:
            key = obl.name.lower()

            if key in seen:
                # Preserve HARD over SOFT
                if obl.severity == "HARD" and seen[key].severity == "SOFT":
                    seen[key] = obl
            else:
                seen[key] = obl

    # Convert to RequiredObligation and sort
    required = [
        RequiredObligation(
            name=obl.name,
            type=obl.type,
            severity=obl.severity,
            expected_attestor=obl.expected_attestor
        )
        for obl in seen.values()
    ]

    return sorted(required, key=lambda o: o.name)


# ============================================================================
# FACTORY FLOOR 1: EXECUTOR
# ============================================================================

class F1_Executor:
    """Factory Floor 1: Execute tests in sandboxed environment."""

    @staticmethod
    def execute(briefcase: Briefcase) -> List[ExecutionResult]:
        """
        Execute all requested tests.

        For POC: Mock execution with deterministic outputs.
        Real implementation would run actual tests in sandbox.
        """
        results = []

        for test in briefcase.requested_tests:
            # Check kill-switch policies
            if "no_unbounded_cost" in briefcase.constraints.kill_switch_policies:
                # Mock: Check if test would violate cost limits
                pass

            # Mock execution
            result = ExecutionResult(
                test_id=test.test_id,
                status="SUCCESS",
                artifact_paths=test.artifact_paths,
                stdout=f"Mock execution of {test.test_id}\nProcedure: {test.procedure}",
                stderr="",
                exit_code=0
            )

            results.append(result)

        return results


# ============================================================================
# FACTORY FLOOR 2: VERIFIER
# ============================================================================

class F2_Verifier:
    """Factory Floor 2: Verify outputs and compute hashes."""

    @staticmethod
    def verify(
        briefcase: Briefcase,
        execution_results: List[ExecutionResult]
    ) -> List[VerificationResult]:
        """
        Verify execution outputs and compute attestation hashes.

        Rules:
        - If exit_code != 0 → attestation_valid=false
        - If artifact missing → attestation_valid=false
        - Compute SHA-256 hashes of all artifacts
        """
        verification_results = []

        for exec_result in execution_results:
            # Find corresponding test and obligation
            test = next(
                (t for t in briefcase.requested_tests if t.test_id == exec_result.test_id),
                None
            )

            if not test:
                continue

            # Determine validity
            attestation_valid = True

            if exec_result.exit_code != 0:
                attestation_valid = False

            if exec_result.status != "SUCCESS":
                attestation_valid = False

            # Compute hashes (mock for POC)
            artifact_hashes = {}
            payload_data = exec_result.stdout + exec_result.stderr

            for path in exec_result.artifact_paths:
                # Mock: In real implementation, read actual files
                artifact_content = f"mock_artifact_{path}"
                artifact_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
                artifact_hashes[path] = f"sha256:{artifact_hash}"

            # Compute payload hash
            payload_hash = hashlib.sha256(payload_data.encode()).hexdigest()

            verification_results.append(VerificationResult(
                test_id=exec_result.test_id,
                obligation_name=test.maps_to_obligation,
                attestation_valid=attestation_valid,
                payload_hash=f"sha256:{payload_hash}",
                artifact_hashes=artifact_hashes,
                verification_log=f"Verified {test.test_id}: valid={attestation_valid}"
            ))

        return verification_results


# ============================================================================
# FACTORY FLOOR 3: PUBLISHER
# ============================================================================

class F3_Publisher:
    """Factory Floor 3: Publish attestations to ledger."""

    @staticmethod
    def publish(
        briefcase: Briefcase,
        verification_results: List[VerificationResult],
        secret_key: str = "mock_secret_key"
    ) -> List[Attestation]:
        """
        Write attestations to ledger.

        Rules:
        - attestation_id format: ATT-{run_id}-{seq}
        - signature: SHA-256 HMAC of (run_id + claim_id + obligation_name + payload_hash)
        - policy_match: 1 if attestation_valid=true AND no kill-switch violations
        - Ledger writes are append-only
        """
        attestations = []
        claim = briefcase.claim_candidates[0]  # POC: single claim

        for i, verify_result in enumerate(verification_results):
            # Generate attestation ID
            attestation_id = f"ATT-{briefcase.run_id}-{i+1:02d}"

            # Compute signature
            sig_data = (
                briefcase.run_id +
                claim.claim_id +
                verify_result.obligation_name +
                verify_result.payload_hash
            )
            signature = hmac.new(
                secret_key.encode(),
                sig_data.encode(),
                hashlib.sha256
            ).hexdigest()

            # Determine policy_match
            policy_match = 1 if verify_result.attestation_valid else 0

            # Check kill-switch violations (mock)
            if not verify_result.attestation_valid:
                policy_match = 0

            # Find expected_attestor from obligation
            obligation = next(
                (o for o in briefcase.required_obligations if o.name == verify_result.obligation_name),
                None
            )

            attestation = Attestation(
                attestation_id=attestation_id,
                run_id=briefcase.run_id,
                claim_id=claim.claim_id,
                obligation_name=verify_result.obligation_name,
                attestor=obligation.expected_attestor if obligation else "CI_RUNNER",
                attestation_valid=verify_result.attestation_valid,
                payload_hash=verify_result.payload_hash,
                artifact_hashes=verify_result.artifact_hashes,
                signature=signature,
                timestamp=datetime.now().isoformat(),
                policy_match=policy_match
            )

            attestations.append(attestation)

        return attestations


# ============================================================================
# TRIBUNAL INTEGRATOR
# ============================================================================

class TribunalIntegrator:
    """Tribunal Integrator: Apply acceptance criterion."""

    @staticmethod
    def decide(
        briefcase: Briefcase,
        attestations: List[Attestation]
    ) -> TribunalVerdict:
        """
        Apply acceptance criterion and output SHIP / NO_SHIP.

        Criterion:
        For claim c to SHIP:
        1. For every obligation o in required_obligations:
           - There exists an attestation a where:
             - a.claim_id = c.claim_id
             - a.obligation_name = o.name
             - a.attestation_valid = true
             - a.policy_match = 1
        2. No kill-switch policies are violated

        Output: Binary verdict (deterministic)
        """
        claim = briefcase.claim_candidates[0]
        reason_codes = []

        # Check each required obligation
        missing_attestations = []
        invalid_attestations = []

        for obligation in briefcase.required_obligations:
            # Find matching attestation
            attestation = next(
                (a for a in attestations if a.obligation_name == obligation.name),
                None
            )

            if not attestation:
                missing_attestations.append(obligation.name)
                reason_codes.append(f"MISSING_ATTESTATION:{obligation.name}")
            elif not attestation.attestation_valid or attestation.policy_match != 1:
                invalid_attestations.append(obligation.name)
                reason_codes.append(f"ATTESTATION_INVALID:{obligation.name}")

        # Check kill-switches (mock)
        kill_switch_triggered = False
        for policy in briefcase.constraints.kill_switch_policies:
            # Mock: Check if policy is violated
            pass

        # Determine verdict
        if kill_switch_triggered:
            verdict = "NO_SHIP"
            ship_permitted = False
            reason_codes.insert(0, "KILL_SWITCH_TRIGGERED")
            tier_promotion = "II"
        elif missing_attestations or invalid_attestations:
            verdict = "NO_SHIP"
            ship_permitted = False
            tier_promotion = "II"
        else:
            verdict = "SHIP"
            ship_permitted = True
            reason_codes = ["ALL_OBLIGATIONS_SATISFIED"]
            tier_promotion = "I"

        return TribunalVerdict(
            tribunal="INTEGRATOR",
            run_id=briefcase.run_id,
            claim_id=claim.claim_id,
            verdict=verdict,
            ship_permitted=ship_permitted,
            reason_codes=reason_codes,
            tier_promotion=tier_promotion,
            timestamp=datetime.now().isoformat()
        )


# ============================================================================
# MAIN POC PIPELINE
# ============================================================================

def run_poc_factory_oracle(claim: Claim) -> TribunalVerdict:
    """
    Execute complete POC FACTORY ORACLE pipeline.

    Flow:
    1. Superteam Ideation (parallel)
    2. Merge obligations
    3. Create Briefcase
    4. Factory execution (F1/F2/F3)
    5. Tribunal decision

    Returns: TribunalVerdict
    """
    print("\n" + "="*60)
    print("POC FACTORY ORACLE — Pipeline Execution")
    print("="*60)

    # STEP 1: SUPERTEAM IDEATION
    print("\n[STEP 1] SUPERTEAM IDEATION")
    print("-" * 60)

    engineering_output = MockSuperteamBuilder.engineering_builder(claim)
    research_output = MockSuperteamBuilder.research_builder(claim)

    print(f"ENGINEERING: {engineering_output.upgrade_hypothesis}")
    print(f"  Obligations: {len(engineering_output.proposed_obligations)}")

    print(f"RESEARCH: {research_output.upgrade_hypothesis}")
    print(f"  Obligations: {len(research_output.proposed_obligations)}")

    # STEP 2: MERGE OBLIGATIONS
    print("\n[STEP 2] MERGE OBLIGATIONS")
    print("-" * 60)

    superteam_outputs = [engineering_output, research_output]
    required_obligations = merge_superteam_outputs(superteam_outputs)

    print(f"Required obligations: {len(required_obligations)}")
    for obl in required_obligations:
        print(f"  - {obl.name} ({obl.severity})")

    # STEP 3: CREATE BRIEFCASE
    print("\n[STEP 3] CREATE BRIEFCASE")
    print("-" * 60)

    run_id = f"RUN-{datetime.now().strftime('%Y-%m-%d')}-POC-001"

    requested_tests = [
        RequestedTest(
            test_id=f"TEST-{i+1:02d}",
            procedure=f"Execute benchmark for {obl.name}",
            artifact_paths=[f"artifacts/{obl.name}.json"],
            maps_to_obligation=obl.name
        )
        for i, obl in enumerate(required_obligations)
    ]

    briefcase = Briefcase(
        run_id=run_id,
        claim_candidates=[claim],
        required_obligations=required_obligations,
        requested_tests=requested_tests,
        constraints=Constraints(
            kill_switch_policies=["no_unbounded_cost", "no_pii_exfiltration"],
            baseline_comparison_required=True
        )
    )

    print(f"Run ID: {briefcase.run_id}")
    print(f"Tests requested: {len(briefcase.requested_tests)}")

    # STEP 4: FACTORY EXECUTION
    print("\n[STEP 4] FACTORY EXECUTION")
    print("-" * 60)

    # F1: Execute
    print("F1 EXECUTOR: Running tests...")
    execution_results = F1_Executor.execute(briefcase)
    print(f"  Executed {len(execution_results)} tests")

    # F2: Verify
    print("F2 VERIFIER: Verifying outputs...")
    verification_results = F2_Verifier.verify(briefcase, execution_results)
    print(f"  Verified {len(verification_results)} results")

    # F3: Publish
    print("F3 PUBLISHER: Publishing attestations...")
    attestations = F3_Publisher.publish(briefcase, verification_results)
    print(f"  Published {len(attestations)} attestations")

    for att in attestations:
        print(f"    {att.attestation_id}: {att.obligation_name} (valid={att.attestation_valid}, policy_match={att.policy_match})")

    # STEP 5: TRIBUNAL DECISION
    print("\n[STEP 5] TRIBUNAL DECISION")
    print("-" * 60)

    verdict = TribunalIntegrator.decide(briefcase, attestations)

    print(f"Verdict: {verdict.verdict}")
    print(f"Ship Permitted: {verdict.ship_permitted}")
    print(f"Tier Promotion: {verdict.tier_promotion}")
    print(f"Reason Codes:")
    for code in verdict.reason_codes:
        print(f"  - {code}")

    print("\n" + "="*60)
    print(f"✅ POC FACTORY ORACLE complete: {verdict.verdict}")
    print("="*60)

    return verdict


# ============================================================================
# DEMO EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Example claim
    claim = Claim(
        claim_id="CLAIM-001",
        claim_text="Add caching layer to reduce API latency < 100ms p99",
        tier_default="II"
    )

    # Run complete pipeline
    verdict = run_poc_factory_oracle(claim)

    # Display summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Claim: {claim.claim_text}")
    print(f"Initial Tier: {claim.tier_default}")
    print(f"Final Verdict: {verdict.verdict}")
    print(f"Final Tier: {verdict.tier_promotion}")
    print(f"Ship Permitted: {verdict.ship_permitted}")
    print("\n" + "="*60)
    print("POC demonstrates:")
    print("✅ Superteam ideation (parallel)")
    print("✅ Obligation merging (deterministic)")
    print("✅ Factory execution (F1/F2/F3)")
    print("✅ Attestation generation (hashed + signed)")
    print("✅ Tribunal decision (binary, deterministic)")
    print("="*60)
