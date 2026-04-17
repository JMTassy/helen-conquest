"""
Town Hall Agent: Integrates district verdicts using QI-INT v2 scoring.
Checks invariants and produces town-level recommendation.
"""
import math
import cmath
from typing import List, Dict
from oracle_town.schemas import DistrictVerdict, TownRecommendation, Obligation


class TownHallAgent:
    """
    Town Hall integration layer.

    Applies:
    1. QI-INT v2 (Quantum Interference Integration) scoring
    2. Invariants checking
    3. Kill-switch detection
    4. Aggregates blocking obligations
    """

    def __init__(self, invariants_config: Dict = None):
        self.invariants_config = invariants_config or self._default_invariants()
        self.accept_threshold = 0.75  # τ_accept from ORACLE SUPERTEAM

    def _default_invariants(self) -> Dict:
        """Default invariants (from ORACLE TOWN spec)"""
        return {
            "transparency": {
                "threshold": 0.95,
                "description": "% decisions with public rationale + data links",
            },
            "fairness": {
                "threshold": 0.40,  # Max Gini coefficient
                "description": "Disparity metrics across stakeholders",
            },
            "budget_integrity": {
                "threshold": 0.10,  # Max variance
                "description": "Spend variance vs approved plan",
            },
            "roi_realism": {
                "threshold": 0.25,  # Max MAPE
                "description": "Forecast error bound tracked over time",
            },
            "service_quality": {
                "threshold": 0.85,  # Min quality score
                "description": "Service delivery quality metrics",
            },
        }

    async def integrate(
        self,
        district_verdicts: List[DistrictVerdict],
    ) -> TownRecommendation:
        """
        Integrate district verdicts into town-level recommendation.

        Steps:
        1. Check for kill switches
        2. Calculate QI-INT score
        3. Check invariants
        4. Aggregate blocking obligations
        5. Produce recommendation
        """
        # 1. Check kill switches
        kill_switch_triggered = self._check_kill_switches(district_verdicts)

        # 2. Calculate QI-INT score
        qi_int_score = self._calculate_qi_int(district_verdicts)

        # 3. Check invariants
        invariants_check = self._check_invariants(district_verdicts)

        # 4. Aggregate blocking obligations
        blocking_obligations = self._aggregate_obligations(district_verdicts)

        # 5. Determine recommendation
        recommendation, confidence = self._determine_recommendation(
            kill_switch_triggered=kill_switch_triggered,
            qi_int_score=qi_int_score,
            invariants_check=invariants_check,
            blocking_obligations=blocking_obligations,
        )

        return TownRecommendation(
            district_verdicts=district_verdicts,
            qi_int_score=qi_int_score,
            invariants_check=invariants_check,
            blocking_obligations=blocking_obligations,
            kill_switch_triggered=kill_switch_triggered,
            recommendation=recommendation,
            confidence=confidence,
        )

    def _check_kill_switches(
        self, district_verdicts: List[DistrictVerdict]
    ) -> bool:
        """Check if any district triggered KILL switch"""
        return any(v.overall_verdict == "KILL" for v in district_verdicts)

    def _calculate_qi_int(self, district_verdicts: List[DistrictVerdict]) -> float:
        """
        Calculate QI-INT v2 score using complex amplitude interference.

        Formula:
        a_{c,d} = w_d × e^(i × θ_d)
        A_c = Σ_d a_{c,d}
        S_c = |A_c|²

        where:
        - w_d = district vote weight (0.65-1.00)
        - θ_d = phase based on verdict (0 to π)
        - S_c = final score (0.0-1.0+)
        """
        # Sum complex amplitudes
        total_amplitude = 0 + 0j

        for verdict in district_verdicts:
            # Create complex amplitude: weight × e^(i×phase)
            amplitude = verdict.vote_weight * cmath.exp(1j * verdict.phase)
            total_amplitude += amplitude

        # Score is magnitude squared: |A_c|²
        score = abs(total_amplitude) ** 2

        # Normalize by max possible (all districts APPROVE with full weight)
        max_possible = sum(v.vote_weight for v in district_verdicts) ** 2
        if max_possible > 0:
            score = score / max_possible

        return min(score, 1.0)  # Cap at 1.0

    def _check_invariants(
        self, district_verdicts: List[DistrictVerdict]
    ) -> Dict[str, bool]:
        """
        Check all town invariants.

        For MVP: Simple pass/fail based on obligations and verdicts.
        For production: Integrate with actual metrics system.
        """
        # For MVP: Assume all pass unless evidence suggests otherwise
        invariants_status = {
            "transparency": True,
            "fairness": True,
            "budget_integrity": True,
            "roi_realism": True,
            "service_quality": True,
        }

        # Check if any obligations suggest invariant violations
        for verdict in district_verdicts:
            for obl in verdict.blocking_obligations:
                # Service quality issues
                if "ux" in obl.name.lower() or "quality" in obl.name.lower():
                    invariants_status["service_quality"] = False

                # Budget issues
                if "budget" in obl.name.lower() or "cost" in obl.name.lower():
                    invariants_status["budget_integrity"] = False

                # Transparency issues
                if "evidence" in obl.name.lower() or "documentation" in obl.name.lower():
                    invariants_status["transparency"] = False

        return invariants_status

    def _aggregate_obligations(
        self, district_verdicts: List[DistrictVerdict]
    ) -> List[Obligation]:
        """Aggregate all blocking obligations across districts"""
        all_obligations = []
        seen_ids = set()

        for verdict in district_verdicts:
            for obl in verdict.blocking_obligations:
                if obl.id not in seen_ids:
                    all_obligations.append(obl)
                    seen_ids.add(obl.id)

        return all_obligations

    def _determine_recommendation(
        self,
        kill_switch_triggered: bool,
        qi_int_score: float,
        invariants_check: Dict[str, bool],
        blocking_obligations: List[Obligation],
    ) -> tuple[str, float]:
        """
        Determine town recommendation and confidence.

        Logic (in priority order):
        1. Kill switch → NO_GO (confidence: 1.0)
        2. Blocking obligations > 0 → NO_GO
        3. Any invariant failed → NO_GO
        4. Score < threshold → NO_GO
        5. Otherwise → GO

        Returns:
            (recommendation, confidence)
        """
        # 1. Kill switch (immediate NO_GO)
        if kill_switch_triggered:
            return ("NO_GO", 1.0)

        # 2. Blocking obligations
        if blocking_obligations:
            confidence = max(0.7, 1.0 - len(blocking_obligations) * 0.05)
            return ("NO_GO", confidence)

        # 3. Invariants check
        if not all(invariants_check.values()):
            failed_count = sum(1 for v in invariants_check.values() if not v)
            confidence = max(0.6, 1.0 - failed_count * 0.1)
            return ("NO_GO", confidence)

        # 4. Score threshold
        if qi_int_score < self.accept_threshold:
            confidence = qi_int_score  # Confidence tracks score
            return ("NO_GO", confidence)

        # 5. All checks pass
        confidence = min(0.95, qi_int_score + 0.05)
        return ("GO", confidence)


# Test
if __name__ == "__main__":
    import asyncio

    async def test_town_hall():
        # Create mock district verdicts
        verdicts = [
            DistrictVerdict(
                district_id="legal_001",
                district_name="Legal & Compliance",
                building_briefs=[],
                overall_verdict="CONDITIONAL",
                blocking_obligations=[
                    Obligation(
                        id="OBL_001",
                        type="LEGAL_COMPLIANCE",
                        name="GDPR consent mechanism",
                        description="Needs consent banner",
                        severity="HARD",
                    )
                ],
                vote_weight=1.0,
                phase=math.pi / 4,  # CONDITIONAL
                supervisor_rationale="Minor GDPR issues",
            ),
            DistrictVerdict(
                district_id="technical_001",
                district_name="Technical & Security",
                building_briefs=[],
                overall_verdict="APPROVE",
                blocking_obligations=[],
                vote_weight=1.0,
                phase=0.0,  # APPROVE
                supervisor_rationale="All technical checks pass",
            ),
            DistrictVerdict(
                district_id="business_001",
                district_name="Business & Operations",
                building_briefs=[],
                overall_verdict="APPROVE",
                blocking_obligations=[],
                vote_weight=0.75,
                phase=0.0,
                supervisor_rationale="ROI looks good",
            ),
            DistrictVerdict(
                district_id="social_001",
                district_name="Social & Impact",
                building_briefs=[],
                overall_verdict="CONDITIONAL",
                blocking_obligations=[
                    Obligation(
                        id="OBL_002",
                        type="UX_ISSUE",
                        name="Mobile optimization",
                        description="Mobile UX needs work",
                        severity="HARD",
                    )
                ],
                vote_weight=0.70,
                phase=math.pi / 4,
                supervisor_rationale="UX concerns",
            ),
        ]

        # Create Town Hall and integrate
        town_hall = TownHallAgent()
        recommendation = await town_hall.integrate(verdicts)

        print("=" * 70)
        print("TOWN HALL RECOMMENDATION")
        print("=" * 70)
        print(f"QI-INT Score: {recommendation.qi_int_score:.4f} (threshold: 0.75)")
        print(f"Kill Switch: {recommendation.kill_switch_triggered}")
        print(f"\nInvariants Check:")
        for inv, status in recommendation.invariants_check.items():
            status_str = "✓ PASS" if status else "✗ FAIL"
            print(f"  {inv}: {status_str}")
        print(f"\nBlocking Obligations: {len(recommendation.blocking_obligations)}")
        for obl in recommendation.blocking_obligations:
            print(f"  - {obl.name}")
        print(f"\n{'='*70}")
        print(f"RECOMMENDATION: {recommendation.recommendation}")
        print(f"Confidence: {recommendation.confidence:.2f}")
        print("=" * 70)

    asyncio.run(test_town_hall())
