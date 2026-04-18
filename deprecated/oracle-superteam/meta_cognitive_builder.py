"""
ORACLE SUPERTEAM — META-COGNITIVE BUILDER
Version: 2.0-RLM (Recursive Language Model Integration)

5-Agent Pipeline: DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR
With recursive reasoning, confidence scoring, and multi-angle verification.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum
import json
import hashlib
from datetime import datetime


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class EpistemicTier(Enum):
    """Tier I: Proven | Tier II: Falsifiable | Tier III: Heuristic"""
    TIER_I = "I"
    TIER_II = "II"
    TIER_III = "III"


class ConfidenceLevel(Enum):
    """Confidence classification thresholds"""
    REJECTED = "REJECTED"      # < 0.4
    UNCERTAIN = "UNCERTAIN"    # 0.4-0.8
    TRUSTED = "TRUSTED"        # >= 0.8


class CriticVerdict(Enum):
    """WILLIAM Protocol verdicts"""
    ROBUST = "ROBUST"
    FLAWED_REPAIRABLE = "FLAWED_REPAIRABLE"
    INVALID_DANGEROUS = "INVALID_DANGEROUS"


@dataclass
class ConsensusPacket:
    """ORACLE 1 authoritative constraint declaration"""
    wedge_definition: Dict[str, str]
    global_constraints: List[str]
    explicit_exclusions: List[str]
    hard_gates: List[str]
    allowed_evidence: List[str]
    obligation_cap: int
    confidence_threshold: float = 0.75


@dataclass
class Subtask:
    """Atomic decomposed task"""
    id: str
    description: str
    dependencies: List[str]
    tier: EpistemicTier
    confidence_required: float


@dataclass
class Candidate:
    """Solution candidate from EXPLORER"""
    id: str
    subtask_id: str
    approach_type: Literal["CONVENTIONAL", "NOVEL", "CONTRARIAN"]
    description: str
    viability_estimate: float
    confidence: float
    assumptions: List[str]
    falsification_test: str


@dataclass
class ConfidenceBreakdown:
    """Multi-angle verification scores"""
    logic_validity: float       # Does inference chain hold?
    fact_grounding: float       # Are claims evidence-based?
    completeness: float         # Are all cases covered?
    assumption_safety: float    # Are assumptions validated?

    @property
    def aggregate(self) -> float:
        """Aggregate is the MINIMUM (most conservative)"""
        return min(
            self.logic_validity,
            self.fact_grounding,
            self.completeness,
            self.assumption_safety
        )


@dataclass
class CriticEvaluation:
    """CRITIC assessment of candidate"""
    candidate_id: str
    verdict: CriticVerdict
    confidence: float
    confidence_breakdown: ConfidenceBreakdown
    blocking_issues: List[Dict[str, str]]
    repair_paths: List[str]
    falsification_result: Dict[str, any]


@dataclass
class Obligation:
    """Atomic buildable unit (from ORACLE v1)"""
    id: str
    scope_authorization: str
    action: str
    expected_output: str
    evidence_type: str
    verification_method: str
    pass_condition: str
    confidence: float
    tier: EpistemicTier
    status: Literal["OPEN", "CLOSED"] = "OPEN"


@dataclass
class IntegrationResult:
    """Final synthesis from INTEGRATOR"""
    verdict: Literal["STOP", "CONTINUE"]
    confidence_overall: float
    confidence_breakdown: Dict[str, float]
    blocked_obligations: List[Dict[str, str]]
    pattern_analysis: Dict[str, List[str]]
    final_answer: str
    reasoning: str


@dataclass
class BuilderOutput:
    """Complete pipeline output"""
    obligations: List[Obligation]
    integration: IntegrationResult
    evidence_receipts: List[Dict[str, str]]
    team_signals: List[Dict[str, str]]
    run_hash: str
    timestamp: str
    iteration_count: int


# ============================================================================
# CONFIDENCE THRESHOLDS
# ============================================================================

CONFIDENCE_THRESHOLDS = {
    "auto_reject": 0.4,
    "uncertain": 0.8,
}


def classify_confidence(score: float) -> ConfidenceLevel:
    """Classify confidence score into discrete levels"""
    if score < CONFIDENCE_THRESHOLDS["auto_reject"]:
        return ConfidenceLevel.REJECTED
    elif score < CONFIDENCE_THRESHOLDS["uncertain"]:
        return ConfidenceLevel.UNCERTAIN
    else:
        return ConfidenceLevel.TRUSTED


# ============================================================================
# AGENT 1: DECOMPOSER
# ============================================================================

class Decomposer:
    """Transforms wedge into task graph"""

    @staticmethod
    def decompose(packet: ConsensusPacket) -> Dict[str, any]:
        """
        Parse wedge into subtasks, validate against constraints.

        Returns:
            {
                "wedge_id": str,
                "core_claim": str,
                "subtasks": List[Subtask],
                "blocking_unknowns": List[dict],
                "obligation_count_estimate": int
            }
        """
        wedge = packet.wedge_definition
        core_claim = wedge.get("claim", "")

        # Generate subtasks (simplified for demo)
        subtasks = [
            Subtask(
                id="ST-01",
                description=f"Design solution for: {core_claim}",
                dependencies=[],
                tier=EpistemicTier.TIER_II,
                confidence_required=packet.confidence_threshold
            ),
            Subtask(
                id="ST-02",
                description="Implement with evidence generation",
                dependencies=["ST-01"],
                tier=EpistemicTier.TIER_I,
                confidence_required=packet.confidence_threshold
            ),
            Subtask(
                id="ST-03",
                description="Verify against hard gates",
                dependencies=["ST-02"],
                tier=EpistemicTier.TIER_I,
                confidence_required=1.0  # Gate verification must be certain
            )
        ]

        # Check obligation cap
        estimated_obligations = len(subtasks) * 2  # Heuristic
        if estimated_obligations > packet.obligation_cap:
            raise ValueError(
                f"Estimated obligations ({estimated_obligations}) exceeds cap ({packet.obligation_cap})"
            )

        return {
            "wedge_id": wedge.get("id", "WDG-UNKNOWN"),
            "core_claim": core_claim,
            "subtasks": subtasks,
            "blocking_unknowns": [],
            "obligation_count_estimate": estimated_obligations
        }


# ============================================================================
# AGENT 2: EXPLORER
# ============================================================================

class Explorer:
    """Generates diverse solution candidates"""

    @staticmethod
    def explore(decomposition: Dict, packet: ConsensusPacket) -> List[Candidate]:
        """
        For each subtask, generate 3-5 meaningfully different candidates.

        Returns: List[Candidate]
        """
        candidates = []

        for subtask in decomposition["subtasks"]:
            # Generate diverse approaches (simplified)
            candidates.extend([
                Candidate(
                    id=f"C{len(candidates)+1}",
                    subtask_id=subtask.id,
                    approach_type="CONVENTIONAL",
                    description=f"Standard approach for {subtask.description}",
                    viability_estimate=0.75,
                    confidence=0.80,
                    assumptions=["Standard patterns apply"],
                    falsification_test="Unit tests + integration tests"
                ),
                Candidate(
                    id=f"C{len(candidates)+2}",
                    subtask_id=subtask.id,
                    approach_type="NOVEL",
                    description=f"Novel approach for {subtask.description}",
                    viability_estimate=0.65,
                    confidence=0.70,
                    assumptions=["Requires validation", "May have unknown edge cases"],
                    falsification_test="Prototype + stress test"
                )
            ])

        return candidates


# ============================================================================
# AGENT 3: CRITIC (WILLIAM Protocol + RLM)
# ============================================================================

class Critic:
    """Adversarial verification with confidence scoring"""

    @staticmethod
    def critique(
        candidates: List[Candidate],
        packet: ConsensusPacket
    ) -> List[CriticEvaluation]:
        """
        Apply WILLIAM protocol + multi-angle verification.

        For each candidate:
        1. DECOMPOSE: Break into verifiable sub-claims
        2. SOLVE: Score confidence on each
        3. VERIFY: 4-check protocol (logic, facts, completeness, assumptions)
        4. SYNTHESIZE: Final verdict

        Returns: List[CriticEvaluation]
        """
        evaluations = []

        for candidate in candidates:
            # Multi-angle verification
            breakdown = Critic._verify_multi_angle(candidate, packet)

            # Check for blocking issues
            blocking_issues = Critic._check_violations(candidate, packet)

            # Determine verdict
            if blocking_issues:
                verdict = CriticVerdict.INVALID_DANGEROUS
            elif breakdown.aggregate >= CONFIDENCE_THRESHOLDS["uncertain"]:
                verdict = CriticVerdict.ROBUST
            else:
                verdict = CriticVerdict.FLAWED_REPAIRABLE

            evaluations.append(CriticEvaluation(
                candidate_id=candidate.id,
                verdict=verdict,
                confidence=breakdown.aggregate,
                confidence_breakdown=breakdown,
                blocking_issues=blocking_issues,
                repair_paths=Critic._suggest_repairs(candidate, blocking_issues),
                falsification_result={
                    "test_proposed": candidate.falsification_test,
                    "test_feasible": True,
                    "expected_outcome": "Pass with confidence >= 0.8"
                }
            ))

        return evaluations

    @staticmethod
    def _verify_multi_angle(candidate: Candidate, packet: ConsensusPacket) -> ConfidenceBreakdown:
        """
        4-check protocol:
        1. Logic validity
        2. Fact grounding
        3. Completeness
        4. Assumption safety
        """
        # Simplified scoring (in real system, would use LLM)
        logic_score = 0.9 if candidate.approach_type == "CONVENTIONAL" else 0.7
        fact_score = candidate.confidence
        completeness_score = 0.8  # Would analyze coverage
        assumption_score = 0.85 if len(candidate.assumptions) < 3 else 0.7

        return ConfidenceBreakdown(
            logic_validity=logic_score,
            fact_grounding=fact_score,
            completeness=completeness_score,
            assumption_safety=assumption_score
        )

    @staticmethod
    def _check_violations(candidate: Candidate, packet: ConsensusPacket) -> List[Dict[str, str]]:
        """Check for exclusion violations or constraint breaks"""
        issues = []

        # Check exclusions
        for exclusion in packet.explicit_exclusions:
            if exclusion.lower() in candidate.description.lower():
                issues.append({
                    "issue": f"Violates exclusion: {exclusion}",
                    "severity": "HIGH",
                    "auto_reject": "true"
                })

        return issues

    @staticmethod
    def _suggest_repairs(candidate: Candidate, issues: List[Dict]) -> List[str]:
        """Generate repair paths for flawed candidates"""
        if not issues:
            return []

        repairs = []
        for issue in issues:
            if "exclusion" in issue["issue"].lower():
                repairs.append("Redesign to avoid excluded approach")
            else:
                repairs.append("Address identified gap with additional evidence")

        return repairs


# ============================================================================
# AGENT 4: BUILDER
# ============================================================================

class Builder:
    """Constructs obligations from surviving candidates"""

    @staticmethod
    def build(
        evaluations: List[CriticEvaluation],
        candidates: List[Candidate],
        decomposition: Dict,
        packet: ConsensusPacket
    ) -> List[Obligation]:
        """
        Convert ROBUST and FLAWED_REPAIRABLE candidates into obligations.

        Returns: List[Obligation]
        """
        obligations = []

        # Filter to surviving candidates
        surviving = [
            (eval, next(c for c in candidates if c.id == eval.candidate_id))
            for eval in evaluations
            if eval.verdict in [CriticVerdict.ROBUST, CriticVerdict.FLAWED_REPAIRABLE]
        ]

        for eval, candidate in surviving:
            # Create obligation from candidate
            obl = Obligation(
                id=f"OBL-{candidate.subtask_id}-{candidate.id}",
                scope_authorization=f"Wedge §1.0 (Subtask {candidate.subtask_id})",
                action=candidate.description,
                expected_output=f"Implementation satisfying: {candidate.falsification_test}",
                evidence_type=packet.allowed_evidence[0] if packet.allowed_evidence else "test_log",
                verification_method=candidate.falsification_test,
                pass_condition="All tests pass AND confidence >= threshold",
                confidence=eval.confidence,
                tier=Builder._determine_tier(candidate, eval)
            )

            obligations.append(obl)

            # If repairable, add repair obligation
            if eval.verdict == CriticVerdict.FLAWED_REPAIRABLE and eval.repair_paths:
                repair_obl = Obligation(
                    id=f"OBL-REPAIR-{candidate.id}",
                    scope_authorization=f"Remediation for {candidate.id}",
                    action=eval.repair_paths[0],
                    expected_output="Issue resolved, confidence >= 0.75",
                    evidence_type="review_log",
                    verification_method="Manual review or automated check",
                    pass_condition="Blocking issue cleared",
                    confidence=0.6,  # Lower until repaired
                    tier=EpistemicTier.TIER_II
                )
                obligations.append(repair_obl)

        # Check obligation cap
        if len(obligations) > packet.obligation_cap:
            raise ValueError(
                f"Generated obligations ({len(obligations)}) exceeds cap ({packet.obligation_cap})"
            )

        return obligations

    @staticmethod
    def _determine_tier(candidate: Candidate, eval: CriticEvaluation) -> EpistemicTier:
        """Determine epistemic tier based on evidence strength"""
        if eval.confidence >= 0.9 and candidate.approach_type == "CONVENTIONAL":
            return EpistemicTier.TIER_I
        elif eval.confidence >= 0.7:
            return EpistemicTier.TIER_II
        else:
            return EpistemicTier.TIER_III


# ============================================================================
# AGENT 5: INTEGRATOR
# ============================================================================

class Integrator:
    """Synthesizes final decision (STOP or CONTINUE)"""

    @staticmethod
    def integrate(
        obligations: List[Obligation],
        decomposition: Dict,
        evaluations: List[CriticEvaluation],
        packet: ConsensusPacket
    ) -> IntegrationResult:
        """
        Analyze aggregate confidence, detect contradictions, decide STOP/CONTINUE.

        Returns: IntegrationResult
        """
        # Calculate aggregate confidence
        confidence_scores = {
            "decomposition": 0.95,  # High confidence in decomposition
            "exploration": sum(e.confidence for e in evaluations) / len(evaluations) if evaluations else 0,
            "critique": sum(e.confidence for e in evaluations) / len(evaluations) if evaluations else 0,
            "build": sum(o.confidence for o in obligations) / len(obligations) if obligations else 0,
        }
        confidence_scores["integration"] = sum(confidence_scores.values()) / len(confidence_scores)

        overall_confidence = confidence_scores["integration"]

        # Check for blocked obligations
        blocked = [
            {
                "id": obl.id,
                "reason": f"Confidence {obl.confidence:.2f} below threshold {packet.confidence_threshold}",
                "required_action": "Increase evidence or iterate"
            }
            for obl in obligations
            if obl.confidence < packet.confidence_threshold
        ]

        # Detect shared blind spots (simplified)
        pattern_analysis = {
            "shared_blind_spots": [],
            "emergent_insights": [
                f"Generated {len(obligations)} obligations from {len(evaluations)} candidates"
            ]
        }

        # Determine STOP or CONTINUE
        if blocked:
            verdict = "CONTINUE"
            reasoning = f"{len(blocked)} obligations below confidence threshold, requires iteration"
        elif overall_confidence < packet.confidence_threshold:
            verdict = "CONTINUE"
            reasoning = f"Overall confidence {overall_confidence:.2f} < threshold {packet.confidence_threshold}"
        else:
            verdict = "STOP"
            reasoning = f"All obligations meet threshold, overall confidence {overall_confidence:.2f}"

        return IntegrationResult(
            verdict=verdict,
            confidence_overall=overall_confidence,
            confidence_breakdown=confidence_scores,
            blocked_obligations=blocked,
            pattern_analysis=pattern_analysis,
            final_answer=f"MVP construction plan: {len(obligations)} obligations for wedge {decomposition['wedge_id']}",
            reasoning=reasoning
        )


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_builder_pipeline(
    consensus_packet: ConsensusPacket,
    max_iterations: int = 3
) -> BuilderOutput:
    """
    Execute 5-agent meta-cognitive pipeline with recursive refinement.

    Pipeline: DECOMPOSER → EXPLORER → CRITIC → BUILDER → INTEGRATOR

    Args:
        consensus_packet: ORACLE 1 authoritative packet
        max_iterations: Maximum recursion depth

    Returns:
        BuilderOutput with obligations, confidence scores, and verdict
    """
    iteration = 0
    previous_confidence = 0.0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}")
        print(f"{'='*60}\n")

        # AGENT 1: DECOMPOSER
        print("🔍 DECOMPOSER: Breaking down wedge...")
        decomposition = Decomposer.decompose(consensus_packet)
        print(f"   → Generated {len(decomposition['subtasks'])} subtasks")

        # AGENT 2: EXPLORER
        print("🧭 EXPLORER: Generating candidate solutions...")
        candidates = Explorer.explore(decomposition, consensus_packet)
        print(f"   → Generated {len(candidates)} candidates")

        # AGENT 3: CRITIC
        print("⚔️  CRITIC: Applying WILLIAM protocol...")
        evaluations = Critic.critique(candidates, consensus_packet)
        robust_count = sum(1 for e in evaluations if e.verdict == CriticVerdict.ROBUST)
        print(f"   → {robust_count}/{len(evaluations)} candidates marked ROBUST")

        # AGENT 4: BUILDER
        print("🔨 BUILDER: Constructing obligations...")
        obligations = Builder.build(evaluations, candidates, decomposition, consensus_packet)
        print(f"   → Generated {len(obligations)} obligations")

        # AGENT 5: INTEGRATOR
        print("🎯 INTEGRATOR: Synthesizing decision...")
        integration = Integrator.integrate(obligations, decomposition, evaluations, consensus_packet)
        print(f"   → Verdict: {integration.verdict}")
        print(f"   → Overall confidence: {integration.confidence_overall:.2f}")
        print(f"   → Reasoning: {integration.reasoning}")

        # Check stopping condition
        if integration.verdict == "STOP":
            break

        # Check progress
        if integration.confidence_overall - previous_confidence < 0.05:
            print("\n⚠️  WARNING: Insufficient progress, terminating iterations")
            break

        previous_confidence = integration.confidence_overall

    # Generate final output
    def serialize_obj(obj):
        """Convert dataclass objects to JSON-serializable format"""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, EpistemicTier):
                    result[key] = value.value
                elif isinstance(value, Enum):
                    result[key] = value.value
                elif isinstance(value, list):
                    result[key] = [serialize_obj(item) for item in value]
                elif hasattr(value, '__dict__'):
                    result[key] = serialize_obj(value)
                else:
                    result[key] = value
            return result
        return obj

    run_data = {
        "consensus_packet": serialize_obj(consensus_packet),
        "obligations": [serialize_obj(o) for o in obligations],
        "integration": serialize_obj(integration),
        "iteration_count": iteration
    }
    run_hash = hashlib.sha256(json.dumps(run_data, sort_keys=True).encode()).hexdigest()

    return BuilderOutput(
        obligations=obligations,
        integration=integration,
        evidence_receipts=[],  # Populated during execution
        team_signals=[],       # Populated during execution
        run_hash=run_hash,
        timestamp=datetime.now().isoformat(),
        iteration_count=iteration
    )


# ============================================================================
# DEMO EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Example consensus packet
    packet = ConsensusPacket(
        wedge_definition={
            "id": "WDG-CACHE-001",
            "claim": "Reduce API latency to < 100ms p99 without external dependencies"
        },
        global_constraints=[
            "No external services (Redis, Memcached, etc.)",
            "Memory footprint < 500MB",
            "100% deterministic (no random eviction)"
        ],
        explicit_exclusions=[
            "CDN solutions",
            "Database query optimization"
        ],
        hard_gates=[
            "p99 latency < 100ms under 10k req/s",
            "Memory usage < 500MB sustained",
            "Cache hit rate >= 80%"
        ],
        allowed_evidence=[
            "memory_profiler_log",
            "load_test_results",
            "pytest_coverage_report"
        ],
        obligation_cap=10,
        confidence_threshold=0.75
    )

    # Run pipeline
    print("\n" + "="*60)
    print("ORACLE META-COGNITIVE BUILDER — Demo Execution")
    print("="*60)

    result = run_builder_pipeline(packet)

    # Display results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"\nRun Hash: {result.run_hash}")
    print(f"Iterations: {result.iteration_count}")
    print(f"Timestamp: {result.timestamp}")
    print(f"\nIntegration Verdict: {result.integration.verdict}")
    print(f"Overall Confidence: {result.integration.confidence_overall:.2f}")
    print(f"\nGenerated Obligations ({len(result.obligations)}):")
    for obl in result.obligations:
        print(f"  - {obl.id}: {obl.action[:60]}... (confidence: {obl.confidence:.2f}, tier: {obl.tier.value})")

    print(f"\nBlocked Obligations: {len(result.integration.blocked_obligations)}")
    for blocked in result.integration.blocked_obligations:
        print(f"  - {blocked['id']}: {blocked['reason']}")

    print("\n" + "="*60)
    print("✅ Pipeline execution complete")
    print("="*60)
