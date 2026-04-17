"""
Mayor Agent: Final authority for binary SHIP/NO_SHIP verdict.
Applies constitutional rules. Generates remediation roadmap for NO_SHIP.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from oracle_town.schemas import (
    CompiledClaim,
    TownRecommendation,
    MayorVerdict,
    RemediationStep,
    Obligation,
)


class MayorAgent:
    """
    Final decision authority applying constitutional rules.

    Constitutional Rules (immutable, from ORACLE SUPERTEAM):
    1. IF kill_switch → NO_SHIP (immediate)
    2. ELSE IF blocking_obligations > 0 → NO_SHIP
    3. ELSE IF contradictions detected → NO_SHIP
    4. ELSE IF S_c < τ_accept → NO_SHIP
    5. ELSE → SHIP

    No explanations. No opinions. No override buttons.
    """

    def __init__(self, code_version: str = "oracle_town_v1.0.0"):
        self.code_version = code_version
        self.accept_threshold = 0.75  # τ_accept

    async def decide(
        self,
        claim: CompiledClaim,
        town_recommendation: TownRecommendation,
    ) -> MayorVerdict:
        """
        Apply constitutional rules to produce final verdict.

        Args:
            claim: The claim being evaluated
            town_recommendation: Integrated recommendation from Town Hall

        Returns:
            MayorVerdict with decision + optional remediation roadmap
        """
        # Collect evidence bundle
        evidence_bundle = self._collect_evidence(town_recommendation)

        # Apply constitutional rules (in order)
        decision, rationale, blocking_reasons = self._apply_constitutional_rules(
            town_recommendation
        )

        # Generate remediation roadmap if NO_SHIP
        remediation_roadmap = []
        if decision == "NO_SHIP":
            remediation_roadmap = await self._generate_remediation(
                claim, town_recommendation
            )

        return MayorVerdict(
            claim_id=claim.claim_id,
            decision=decision,
            rationale=rationale,
            evidence_bundle=evidence_bundle,
            blocking_reasons=blocking_reasons,
            remediation_roadmap=remediation_roadmap,
            timestamp=datetime.utcnow().isoformat(),
            code_version=self.code_version,
        )

    def _collect_evidence(
        self, town_recommendation: TownRecommendation
    ) -> List[str]:
        """Collect all evidence artifacts from district verdicts"""
        evidence = set()

        for district_verdict in town_recommendation.district_verdicts:
            for building_brief in district_verdict.building_briefs:
                evidence.update(building_brief.evidence_artifacts)

        return sorted(list(evidence))

    def _apply_constitutional_rules(
        self, town_recommendation: TownRecommendation
    ) -> tuple[str, str, List[str]]:
        """
        Apply constitutional rules in strict order.

        Returns:
            (decision, rationale, blocking_reasons)
        """
        blocking_reasons = []

        # Rule 1: Kill switch check
        if town_recommendation.kill_switch_triggered:
            return (
                "NO_SHIP",
                "Kill switch triggered by authorized district (Legal/Security). "
                "Immediate halt per constitutional rules.",
                ["Kill switch triggered"],
            )

        # Rule 2: Blocking obligations check
        if town_recommendation.blocking_obligations:
            for obl in town_recommendation.blocking_obligations:
                blocking_reasons.append(f"{obl.name}: {obl.description}")

            return (
                "NO_SHIP",
                f"{len(town_recommendation.blocking_obligations)} blocking obligations "
                f"must be resolved before SHIP.",
                blocking_reasons,
            )

        # Rule 3: Contradictions check (simplified for MVP)
        # In production: implement full contradiction detection from ORACLE SUPERTEAM
        # For now: check if invariants failed (indicates contradictions)
        failed_invariants = [
            inv
            for inv, status in town_recommendation.invariants_check.items()
            if not status
        ]

        if failed_invariants:
            for inv in failed_invariants:
                blocking_reasons.append(f"Invariant failed: {inv}")

            return (
                "NO_SHIP",
                f"Invariants failed: {', '.join(failed_invariants)}. "
                f"Contradictions detected in requirements vs capabilities.",
                blocking_reasons,
            )

        # Rule 4: Score threshold check
        if town_recommendation.qi_int_score < self.accept_threshold:
            blocking_reasons.append(
                f"Score {town_recommendation.qi_int_score:.3f} below threshold {self.accept_threshold}"
            )

            return (
                "NO_SHIP",
                f"QI-INT score ({town_recommendation.qi_int_score:.3f}) below acceptance "
                f"threshold ({self.accept_threshold}). Insufficient district approval.",
                blocking_reasons,
            )

        # Rule 5: All checks pass → SHIP
        return (
            "SHIP",
            f"All constitutional checks passed. QI-INT score: {town_recommendation.qi_int_score:.3f}. "
            f"All invariants satisfied. No blocking obligations. Verdict: SHIP.",
            [],
        )

    async def _generate_remediation(
        self,
        claim: CompiledClaim,
        town_recommendation: TownRecommendation,
    ) -> List[RemediationStep]:
        """
        Generate remediation roadmap using monotonic weakening.

        Strategy:
        1. For each blocking obligation, create a remediation step
        2. Estimate effort based on obligation type
        3. Assign to responsible district/building
        4. Order by: HARD obligations first, then estimated effort (low to high)
        """
        remediation_steps = []

        for obl in town_recommendation.blocking_obligations:
            step = RemediationStep(
                step_id=f"REM_{uuid.uuid4().hex[:6].upper()}",
                obligation_id=obl.id,
                description=self._generate_step_description(obl),
                required_evidence=obl.required_evidence,
                estimated_effort=self._estimate_effort(obl),
                estimated_timeline=self._estimate_timeline(obl),
                responsible=self._assign_responsible(obl, town_recommendation),
                tier_downgrade=self._suggest_tier_downgrade(obl, claim),
                success_criteria=self._define_success_criteria(obl),
            )
            remediation_steps.append(step)

        # Sort: HARD first, then by effort
        effort_order = {"low": 1, "medium": 2, "high": 3}
        remediation_steps.sort(
            key=lambda s: (
                0 if s.estimated_effort else 1,  # Prioritize known effort
                effort_order.get(s.estimated_effort, 2),
            )
        )

        return remediation_steps

    def _generate_step_description(self, obl: Obligation) -> str:
        """Generate actionable description for remediation step"""
        action_verbs = {
            "LEGAL_COMPLIANCE": "Implement",
            "EVIDENCE_MISSING": "Provide",
            "SECURITY_THREAT": "Mitigate",
            "UX_ISSUE": "Optimize",
        }

        verb = action_verbs.get(obl.type, "Address")
        return f"{verb} {obl.name.lower()}: {obl.description}"

    def _estimate_effort(self, obl: Obligation) -> str:
        """Estimate effort level based on obligation type and description"""
        desc_lower = (obl.name + " " + obl.description).lower()

        # High effort indicators
        if any(
            word in desc_lower
            for word in ["redesign", "rebuild", "migrate", "audit", "certification"]
        ):
            return "high"

        # Low effort indicators
        if any(
            word in desc_lower
            for word in ["banner", "button", "label", "text", "copy", "document"]
        ):
            return "low"

        # Default: medium
        return "medium"

    def _estimate_timeline(self, obl: Obligation) -> str:
        """Estimate timeline based on effort"""
        effort = self._estimate_effort(obl)

        timeline_map = {
            "low": "1 week",
            "medium": "2-3 weeks",
            "high": "4-6 weeks",
        }

        return timeline_map.get(effort, "2-3 weeks")

    def _assign_responsible(
        self, obl: Obligation, town_recommendation: TownRecommendation
    ) -> str:
        """Assign obligation to responsible district/building"""
        # Map obligation types to districts
        type_to_district = {
            "LEGAL_COMPLIANCE": "Legal & Compliance District",
            "EVIDENCE_MISSING": "Business & Operations District",
            "SECURITY_THREAT": "Technical & Security District",
            "UX_ISSUE": "Social & Impact District",
        }

        # Try to find which district raised this obligation
        for verdict in town_recommendation.district_verdicts:
            if any(o.id == obl.id for o in verdict.blocking_obligations):
                return verdict.district_name

        # Fallback: use type mapping
        return type_to_district.get(obl.type, "Town Hall")

    def _suggest_tier_downgrade(
        self, obl: Obligation, claim: CompiledClaim
    ) -> str | None:
        """
        Suggest tier downgrade (monotonic weakening) if applicable.

        For MVP: Return None (no tier system yet).
        For production: Implement full tier downgrade logic (A→B, B→C).
        """
        # Future: Analyze claim.claim_type and obligation to suggest downgrades
        # e.g., "Full campaign" (Tier A) → "Pilot campaign" (Tier B)
        return None

    def _define_success_criteria(self, obl: Obligation) -> str:
        """Define clear success criteria for obligation closure"""
        if obl.type == "LEGAL_COMPLIANCE":
            return f"Legal team signs off on {obl.name} with documented evidence"
        elif obl.type == "EVIDENCE_MISSING":
            return f"Required evidence provided and verified: {', '.join(obl.required_evidence)}"
        elif obl.type == "SECURITY_THREAT":
            return f"Security audit passes with no critical vulnerabilities"
        elif obl.type == "UX_ISSUE":
            return f"UX metrics meet target thresholds (specified in obligation)"
        else:
            return f"Obligation {obl.name} marked as closed by responsible team"


# Test
if __name__ == "__main__":
    import asyncio
    import math

    async def test_mayor():
        # Create mock claim
        from oracle_town.schemas import CompiledClaim, Obligation

        claim = CompiledClaim(
            claim_id="CLM_TEST_001",
            claim_text="Launch tourism campaign with GPS tracking",
            claim_type="CAMPAIGN",
            success_criteria=["20% booking increase", "Launch in 3 months"],
            requires_receipts=True,
        )

        # Create mock town recommendation (with obstacles)
        from oracle_town.schemas import DistrictVerdict, BuildingBrief

        district_verdicts = [
            DistrictVerdict(
                district_id="legal_001",
                district_name="Legal & Compliance",
                building_briefs=[],
                overall_verdict="CONDITIONAL",
                blocking_obligations=[
                    Obligation(
                        id="OBL_GDPR_001",
                        type="LEGAL_COMPLIANCE",
                        name="GDPR consent mechanism",
                        description="Implement cookie consent banner for GPS tracking",
                        severity="HARD",
                        required_evidence=["consent_flow_diagram", "legal_sign_off"],
                    )
                ],
                vote_weight=1.0,
                phase=math.pi / 4,
                supervisor_rationale="GDPR issues",
            ),
        ]

        town_rec = TownRecommendation(
            district_verdicts=district_verdicts,
            qi_int_score=0.72,  # Below threshold
            invariants_check={
                "transparency": True,
                "fairness": True,
                "budget_integrity": True,
                "roi_realism": True,
                "service_quality": False,  # Failed
            },
            blocking_obligations=[district_verdicts[0].blocking_obligations[0]],
            kill_switch_triggered=False,
            recommendation="NO_GO",
            confidence=0.75,
        )

        # Mayor decides
        mayor = MayorAgent()
        verdict = await mayor.decide(claim, town_rec)

        print("=" * 70)
        print("MAYOR VERDICT")
        print("=" * 70)
        print(f"Claim ID: {verdict.claim_id}")
        print(f"Decision: {verdict.decision}")
        print(f"\nRationale:\n{verdict.rationale}")
        print(f"\nBlocking Reasons:")
        for reason in verdict.blocking_reasons:
            print(f"  - {reason}")

        if verdict.remediation_roadmap:
            print(f"\n{'='*70}")
            print("REMEDIATION ROADMAP")
            print("=" * 70)
            for i, step in enumerate(verdict.remediation_roadmap, 1):
                print(f"\n{i}. {step.description}")
                print(f"   Effort: {step.estimated_effort} | Timeline: {step.estimated_timeline}")
                print(f"   Responsible: {step.responsible}")
                print(f"   Success: {step.success_criteria}")

        print(f"\n{'='*70}")
        print(f"Timestamp: {verdict.timestamp}")
        print(f"Code Version: {verdict.code_version}")
        print("=" * 70)

    asyncio.run(test_mayor())
