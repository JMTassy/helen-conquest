"""
ORACLE TOWN Orchestrator: Main execution engine.
Coordinates the entire flow from input → claim → districts → town → mayor → verdict.
"""
import asyncio
from typing import List, Optional
from oracle_town.core.claim_compiler import ClaimCompiler
from oracle_town.core.town_hall import TownHallAgent
from oracle_town.core.mayor import MayorAgent
from oracle_town.schemas import (
    TownInput,
    CompiledClaim,
    MayorVerdict,
    DistrictVerdict,
)


class District:
    """Represents a complete district with buildings and streets"""

    def __init__(
        self,
        district_id: str,
        district_name: str,
        streets: List,  # List of street instances (e.g., GDPRStreet)
    ):
        self.district_id = district_id
        self.district_name = district_name
        self.streets = streets

    async def process_claim(self, claim: CompiledClaim) -> DistrictVerdict:
        """
        Process claim through all streets → buildings → district supervisor.

        For MVP: Single building per district.
        For production: Multiple buildings per district.
        """
        from oracle_town.agents import BuildingSupervisor, DistrictSupervisor

        # 1. Run all streets in parallel
        street_reports = await asyncio.gather(*[
            street.analyze_claim(claim) for street in self.streets
        ])

        # 2. Building supervisor aggregates street reports
        building_supervisor = BuildingSupervisor(
            building_id=f"{self.district_id}_building",
            building_name=f"{self.district_name} Building",
            district=self.district_name,
        )

        building_brief = await building_supervisor.aggregate_streets(street_reports)

        # 3. District supervisor produces final verdict
        district_supervisor = DistrictSupervisor(
            district_id=self.district_id,
            district_name=self.district_name,
        )

        district_verdict = await district_supervisor.produce_verdict([building_brief])

        return district_verdict


class OracleTownOrchestrator:
    """
    Main orchestrator for ORACLE TOWN.

    Coordinates the complete flow:
    INPUT → CLAIM → STREETS → BUILDINGS → DISTRICTS → TOWN HALL → MAYOR → VERDICT
    """

    def __init__(self, districts: Optional[List[District]] = None):
        self.claim_compiler = ClaimCompiler()
        self.districts = districts or self._create_default_districts()
        self.town_hall = TownHallAgent()
        self.mayor = MayorAgent()

    def _create_default_districts(self) -> List[District]:
        """
        Create default district configuration.

        Production: All 4 districts with specialized streets.
        """
        from oracle_town.districts.legal.gdpr_street import GDPRStreet
        from oracle_town.districts.technical.security_street import SecurityStreet
        from oracle_town.districts.business.operations_street import OperationsStreet
        from oracle_town.districts.social.impact_street import ImpactStreet

        # District 1: Legal & Compliance (KILL authority)
        legal_district = District(
            district_id="legal_001",
            district_name="Legal & Compliance",
            streets=[GDPRStreet()],
        )

        # District 2: Technical & Security (KILL authority)
        technical_district = District(
            district_id="technical_001",
            district_name="Technical & Security",
            streets=[SecurityStreet()],
        )

        # District 3: Business & Operations (vote weight: 0.75)
        business_district = District(
            district_id="business_001",
            district_name="Business & Operations",
            streets=[OperationsStreet()],
        )

        # District 4: Social & Impact (vote weight: 0.70)
        social_district = District(
            district_id="social_001",
            district_name="Social & Impact",
            streets=[ImpactStreet()],
        )

        return [legal_district, technical_district, business_district, social_district]

    async def process_input(self, user_input: TownInput) -> MayorVerdict:
        """
        Complete end-to-end processing pipeline.

        Steps:
        1. Compile claim from natural language input
        2. Route to districts (parallel processing)
        3. Town Hall integration (QI-INT + invariants)
        4. Mayor final verdict (+ remediation if NO_SHIP)

        Args:
            user_input: Natural language description of what to do

        Returns:
            MayorVerdict with SHIP/NO_SHIP decision + remediation
        """
        print("\n" + "=" * 70)
        print("ORACLE TOWN PROCESSING PIPELINE")
        print("=" * 70)

        # Step 1: Compile Claim
        print("\n[1/4] Compiling claim...")
        claim = self.claim_compiler.compile(user_input)
        print(f"✓ Claim compiled: {claim.claim_id}")
        print(f"  Type: {claim.claim_type}")
        print(f"  Text: {claim.claim_text[:80]}...")

        # Step 2: District Processing (parallel)
        print(f"\n[2/4] Processing through {len(self.districts)} district(s)...")
        district_verdicts = await asyncio.gather(*[
            district.process_claim(claim) for district in self.districts
        ])

        for verdict in district_verdicts:
            print(f"  ✓ {verdict.district_name}: {verdict.overall_verdict}")
            if verdict.blocking_obligations:
                print(f"    └─ {len(verdict.blocking_obligations)} obligation(s)")

        # Step 3: Town Hall Integration
        print("\n[3/4] Town Hall integration...")
        town_recommendation = await self.town_hall.integrate(district_verdicts)
        print(f"  QI-INT Score: {town_recommendation.qi_int_score:.3f}")
        print(f"  Recommendation: {town_recommendation.recommendation}")

        # Step 4: Mayor Final Verdict
        print("\n[4/4] Mayor rendering verdict...")
        mayor_verdict = await self.mayor.decide(claim, town_recommendation)
        print(f"  ✓ Decision: {mayor_verdict.decision}")

        if mayor_verdict.remediation_roadmap:
            print(f"  └─ Remediation roadmap: {len(mayor_verdict.remediation_roadmap)} step(s)")

        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)

        return mayor_verdict


# Convenience function for quick testing
async def process_text(text: str, domain: str = "marketing") -> MayorVerdict:
    """
    Quick helper function to process text input.

    Usage:
        verdict = await process_text("Launch a marketing campaign...")
    """
    orchestrator = OracleTownOrchestrator()
    user_input = TownInput(raw_text=text, domain=domain)
    return await orchestrator.process_input(user_input)


# Test
if __name__ == "__main__":
    import asyncio

    async def test_orchestrator():
        # Test input
        test_input = TownInput(
            raw_text=(
                "Launch a new tourism campaign for Calvi 2030 targeting millennials. "
                "Collect visitor emails and GPS location data for personalized recommendations. "
                "Use Instagram and TikTok for ads. Use Google Maps API for location features. "
                "Budget: 50k EUR. Goal: 20% increase in 25-34 age group bookings. "
                "Launch in 3 months."
            ),
            domain="marketing",
            urgency="high",
        )

        # Create orchestrator and process
        orchestrator = OracleTownOrchestrator()
        verdict = await orchestrator.process_input(test_input)

        # Display results
        print("\n" + "=" * 70)
        print("FINAL MAYOR VERDICT")
        print("=" * 70)
        print(f"Claim ID: {verdict.claim_id}")
        print(f"Decision: {verdict.decision}")
        print(f"\nRationale:")
        print(verdict.rationale)

        if verdict.blocking_reasons:
            print(f"\nBlocking Reasons:")
            for i, reason in enumerate(verdict.blocking_reasons, 1):
                print(f"  {i}. {reason}")

        if verdict.remediation_roadmap:
            print(f"\n{'='*70}")
            print("REMEDIATION ROADMAP")
            print("=" * 70)
            for i, step in enumerate(verdict.remediation_roadmap, 1):
                print(f"\n{i}. {step.description}")
                print(f"   • Effort: {step.estimated_effort}")
                print(f"   • Timeline: {step.estimated_timeline}")
                print(f"   • Responsible: {step.responsible}")
                print(f"   • Evidence needed: {', '.join(step.required_evidence)}")

        print(f"\n{'='*70}")
        print(f"Timestamp: {verdict.timestamp}")
        print(f"Code Version: {verdict.code_version}")
        print("=" * 70)

        # Summary
        if verdict.decision == "SHIP":
            print("\n✅ VERDICT: SHIP - Claim approved for execution")
        else:
            print("\n❌ VERDICT: NO_SHIP - Complete remediation roadmap to proceed")

    asyncio.run(test_orchestrator())
