"""District Supervisor: Final district-level judgment with vote weight & phase"""
import math
from typing import List
from oracle_town.agents.street_agent import StreetAgent
from oracle_town.schemas import BuildingBrief, DistrictVerdict, Obligation


# District authority levels (for QI-INT vote weighting)
DISTRICT_WEIGHTS = {
    "Legal & Compliance": 1.00,  # Full authority
    "Technical & Security": 1.00,  # Full authority
    "Business & Operations": 0.75,
    "Social & Impact": 0.70,
}

# Kill-switch authority
KILL_SWITCH_DISTRICTS = ["Legal & Compliance", "Technical & Security"]


class DistrictSupervisor(StreetAgent):
    """
    District-level meta-agent that produces final district verdict.
    Can trigger KILL switch if authorized (Legal/Security only).
    Produces vote with weight and phase for QI-INT calculation.
    """

    def __init__(self, district_id: str, district_name: str):
        system_prompt = f"""You are the District Supervisor for {district_name}.

AUTHORITY LEVEL: {DISTRICT_WEIGHTS.get(district_name, 0.70)}
KILL SWITCH: {"YES" if district_name in KILL_SWITCH_DISTRICTS else "NO"}

EXPERTISE: Final district judgment, blocking obligation assessment, vote casting

YOUR TASK:
1. Review all building briefs in your district
2. Identify critical blocking obligations
3. Assess overall district sentiment
4. Cast district verdict

VERDICT OPTIONS:
- APPROVE: All buildings approve, no concerns
- CONDITIONAL: Obligations present but manageable
- OBJECT: Significant concerns, blocks without resolution
- QUARANTINE: Needs further review before proceeding
- KILL: Immediate halt (Legal/Security only, severe violations)

KILL SWITCH TRIGGERS (Legal/Security only):
- GDPR violation with no consent mechanism
- Critical security vulnerability
- Illegal activity
- Regulatory non-compliance (no path to fix)

OUTPUT FORMAT:
## CONTRIBUTION
District Verdict for {district_name}:

Buildings Reviewed: [count]
Overall Assessment:
- [Key point 1]
- [Key point 2]

Critical Blocking Obligations:
[List only HARD obligations that block SHIP]

District Verdict: [APPROVE/CONDITIONAL/OBJECT/QUARANTINE/KILL]
Reasoning: [Brief explanation of verdict]

## QUESTION
None (district verdict final)

## ACTION
Forwarding verdict to Town Hall with vote weight {DISTRICT_WEIGHTS.get(district_name, 0.70)}."""

        super().__init__(
            agent_id=f"district_supervisor_{district_id}",
            role=f"District Supervisor - {district_name}",
            system_prompt=system_prompt,
        )

        self.district_id = district_id
        self.district_name = district_name
        self.vote_weight = DISTRICT_WEIGHTS.get(district_name, 0.70)
        self.can_kill = district_name in KILL_SWITCH_DISTRICTS

    async def produce_verdict(
        self, building_briefs: List[BuildingBrief]
    ) -> DistrictVerdict:
        """
        Produce final district verdict from building briefs.

        Returns:
            DistrictVerdict with vote weight and phase
        """
        # Build context
        context = self._build_district_context(building_briefs)

        # Get supervisor's verdict
        response = await self.llm.complete(
            system=self.system_prompt,
            user=context,
        )

        # Parse
        turn = self._parse_turn(response)

        # Extract verdict
        overall_verdict = self._extract_verdict(turn.contribution)

        # Get blocking obligations
        blocking_obligations = self._get_blocking_obligations(building_briefs)

        # Calculate phase (for QI-INT)
        phase = self._calculate_phase(overall_verdict)

        return DistrictVerdict(
            district_id=self.district_id,
            district_name=self.district_name,
            building_briefs=building_briefs,
            overall_verdict=overall_verdict,
            blocking_obligations=blocking_obligations,
            vote_weight=self.vote_weight,
            phase=phase,
            supervisor_rationale=turn.contribution,
        )

    def _build_district_context(
        self, building_briefs: List[BuildingBrief]
    ) -> str:
        """Build context from all building briefs"""
        context_parts = [
            f"=== DISTRICT: {self.district_name} ===",
            f"Buildings to review: {len(building_briefs)}",
            f"Your authority level: {self.vote_weight}",
            f"Can trigger KILL: {self.can_kill}",
            "",
        ]

        for i, brief in enumerate(building_briefs, 1):
            context_parts.extend([
                f"--- BUILDING {i}: {brief.building_name} ---",
                f"Verdict: {brief.building_verdict}",
                f"Streets: {len(brief.street_reports)}",
                "",
                f"Findings: {brief.consolidated_findings[:300]}...",
                f"Obligations: {len(brief.obligations)}",
            ])

            for obl in brief.obligations:
                context_parts.append(f"  - [{obl.severity}] {obl.name}")

            context_parts.extend([
                f"Supervisor Notes: {brief.supervisor_notes[:200]}...",
                "",
            ])

        context_parts.extend([
            "=== YOUR TASK ===",
            "Produce final district verdict.",
            "Consider:",
            "- Are there any KILL-worthy violations?",
            "- What are the critical blocking obligations?",
            "- What is the overall district sentiment?",
            "",
            "Cast your verdict: APPROVE / CONDITIONAL / OBJECT / QUARANTINE / KILL",
        ])

        return "\n".join(context_parts)

    def _extract_verdict(self, contribution: str) -> str:
        """Extract verdict from contribution"""
        verdict_keywords = {
            "KILL": "KILL",
            "QUARANTINE": "QUARANTINE",
            "OBJECT": "OBJECT",
            "CONDITIONAL": "CONDITIONAL",
            "APPROVE": "APPROVE",
        }

        contribution_upper = contribution.upper()

        # Check in priority order (KILL > QUARANTINE > OBJECT > CONDITIONAL > APPROVE)
        for keyword, verdict in verdict_keywords.items():
            if f"Verdict: {keyword}" in contribution_upper or f"VERDICT: {keyword}" in contribution_upper:
                return verdict

        # Fallback: search for keywords
        for keyword, verdict in verdict_keywords.items():
            if keyword in contribution_upper:
                return verdict

        return "CONDITIONAL"  # Safe default

    def _get_blocking_obligations(
        self, building_briefs: List[BuildingBrief]
    ) -> List[Obligation]:
        """Collect all HARD blocking obligations across buildings"""
        blocking = []
        seen_ids = set()

        for brief in building_briefs:
            for obl in brief.obligations:
                if obl.severity == "HARD" and obl.id not in seen_ids:
                    blocking.append(obl)
                    seen_ids.add(obl.id)

        return blocking

    def _calculate_phase(self, verdict: str) -> float:
        """
        Calculate phase for QI-INT (quantum interference integration).

        Phase represents constructive vs destructive interference:
        - APPROVE: 0 (fully constructive)
        - CONDITIONAL: π/4 (slight destructive)
        - OBJECT: π/2 (half destructive)
        - QUARANTINE: 3π/4 (mostly destructive)
        - KILL: π (fully destructive)
        """
        phase_map = {
            "APPROVE": 0.0,
            "CONDITIONAL": math.pi / 4,
            "OBJECT": math.pi / 2,
            "QUARANTINE": 3 * math.pi / 4,
            "KILL": math.pi,
        }

        return phase_map.get(verdict, math.pi / 2)


# Test
if __name__ == "__main__":
    import asyncio
    from oracle_town.schemas import StreetReport, Turn

    async def test_district_supervisor():
        # Create mock building briefs
        mock_brief_1 = BuildingBrief(
            building_id="legal_building_001",
            building_name="Legal Compliance Building",
            district="Legal & Compliance",
            street_reports=[],  # Simplified
            consolidated_findings="GDPR issues identified. Consent mechanism missing.",
            evidence_artifacts=["privacy_policy.pdf"],
            obligations=[
                Obligation(
                    id="OBL_001",
                    type="LEGAL_COMPLIANCE",
                    name="GDPR consent mechanism",
                    description="Implement explicit consent for location data",
                    severity="HARD",
                )
            ],
            building_verdict="CONDITIONAL",
            supervisor_notes="Can proceed with obligation tracking",
        )

        mock_brief_2 = BuildingBrief(
            building_id="contract_building_001",
            building_name="Contract Review Building",
            district="Legal & Compliance",
            street_reports=[],
            consolidated_findings="All contracts in order",
            evidence_artifacts=["vendor_contracts.pdf"],
            obligations=[],
            building_verdict="APPROVE",
            supervisor_notes="No issues",
        )

        # Create district supervisor
        supervisor = DistrictSupervisor(
            district_id="legal_district_001",
            district_name="Legal & Compliance",
        )

        # Produce verdict
        verdict = await supervisor.produce_verdict([mock_brief_1, mock_brief_2])

        print("=" * 70)
        print(f"DISTRICT VERDICT: {verdict.district_name}")
        print("=" * 70)
        print(f"Buildings: {len(verdict.building_briefs)}")
        print(f"Verdict: {verdict.overall_verdict}")
        print(f"Vote Weight: {verdict.vote_weight}")
        print(f"Phase: {verdict.phase:.4f} rad ({verdict.phase * 180 / math.pi:.1f}°)")
        print(f"\nBlocking Obligations: {len(verdict.blocking_obligations)}")
        for obl in verdict.blocking_obligations:
            print(f"  - {obl.name}")
        print(f"\nRationale:\n{verdict.supervisor_rationale[:500]}...")

    asyncio.run(test_district_supervisor())
