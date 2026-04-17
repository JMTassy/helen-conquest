"""Building Supervisor: Aggregates street reports into building brief"""
from typing import List
from oracle_town.agents.street_agent import StreetAgent
from oracle_town.schemas import StreetReport, BuildingBrief, Obligation


class BuildingSupervisor(StreetAgent):
    """
    Meta-agent that reviews all street reports in a building.
    Synthesizes findings, identifies conflicts, produces Building Brief.
    """

    def __init__(self, building_id: str, building_name: str, district: str):
        system_prompt = f"""You are the Building Supervisor for {building_name} in {district} District.

EXPERTISE: Aggregating findings, identifying conflicts, synthesizing obligations

YOUR TASK:
1. Review all street reports
2. Identify conflicting findings across streets
3. Consolidate obligations (remove duplicates, merge similar)
4. Verify evidence sufficiency
5. Determine building verdict

VERDICT LOGIC:
- APPROVE: All streets approve, no blocking obligations
- CONDITIONAL: Some streets conditional OR soft obligations present
- OBJECT: Any street objects OR hard blocking obligations

OUTPUT FORMAT:
## CONTRIBUTION
Building Brief for {building_name}:

Streets Reviewed: [number]
Consolidated Findings:
- [Key finding 1]
- [Key finding 2]

Evidence Artifacts:
- [Receipt 1]
- [Receipt 2]

Blocking Obligations: [count]
[List each blocking obligation]

Building Verdict: [APPROVE/CONDITIONAL/OBJECT]

## QUESTION
None (building review complete)

## ACTION
Forwarding Building Brief to District Supervisor."""

        super().__init__(
            agent_id=f"building_supervisor_{building_id}",
            role=f"Building Supervisor - {building_name}",
            system_prompt=system_prompt,
        )

        self.building_id = building_id
        self.building_name = building_name
        self.district = district

    async def aggregate_streets(
        self,
        street_reports: List[StreetReport],
    ) -> BuildingBrief:
        """
        Aggregate multiple street reports into single building brief.

        Args:
            street_reports: List of reports from streets in this building

        Returns:
            BuildingBrief with consolidated findings
        """
        # Build context from all street reports
        context = self._build_aggregation_context(street_reports)

        # Get supervisor's synthesis
        response = await self.llm.complete(
            system=self.system_prompt,
            user=context,
        )

        # Parse response
        turn = self._parse_turn(response)

        # Extract structured data
        consolidated_findings = turn.contribution
        evidence_artifacts = self._extract_evidence(turn.contribution)
        obligations = self._consolidate_obligations(street_reports)
        building_verdict = self._determine_building_verdict(
            street_reports, obligations
        )
        supervisor_notes = turn.action

        return BuildingBrief(
            building_id=self.building_id,
            building_name=self.building_name,
            district=self.district,
            street_reports=street_reports,
            consolidated_findings=consolidated_findings,
            evidence_artifacts=evidence_artifacts,
            obligations=obligations,
            building_verdict=building_verdict,
            supervisor_notes=supervisor_notes,
        )

    def _build_aggregation_context(
        self, street_reports: List[StreetReport]
    ) -> str:
        """Build context for supervisor from all street reports"""
        context_parts = [
            f"=== BUILDING: {self.building_name} ===",
            f"District: {self.district}",
            f"Streets to review: {len(street_reports)}",
            "",
        ]

        for i, report in enumerate(street_reports, 1):
            context_parts.extend([
                f"--- STREET {i}: {report.street_name} ---",
                f"Confidence: {report.confidence}",
                "",
                "Agent Turns:",
            ])

            for turn in report.agent_turns:
                context_parts.extend([
                    f"[{turn.role}]",
                    f"  {turn.contribution[:200]}...",  # Truncate for brevity
                ])

            context_parts.extend([
                "",
                f"Findings: {report.preliminary_findings[:300]}...",
                f"Obligations: {len(report.identified_obligations)}",
            ])

            for obl in report.identified_obligations:
                context_parts.append(f"  - {obl.name} ({obl.severity})")

            context_parts.append("")

        context_parts.extend([
            "=== YOUR TASK ===",
            "Synthesize these street reports into a consolidated Building Brief.",
            "Identify any conflicting findings.",
            "Consolidate obligations (remove duplicates).",
            "Determine building verdict: APPROVE / CONDITIONAL / OBJECT",
        ])

        return "\n".join(context_parts)

    def _extract_evidence(self, contribution: str) -> List[str]:
        """Extract evidence artifacts from contribution"""
        artifacts = []

        # Look for Evidence Artifacts section
        lines = contribution.split("\n")
        in_evidence = False

        for line in lines:
            if "Evidence Artifacts" in line:
                in_evidence = True
                continue
            if in_evidence and line.strip().startswith("-"):
                artifact = line.strip().lstrip("-").strip()
                if artifact:
                    artifacts.append(artifact)
            elif in_evidence and not line.strip():
                break  # End of evidence section

        return artifacts

    def _consolidate_obligations(
        self, street_reports: List[StreetReport]
    ) -> List[Obligation]:
        """Consolidate obligations from all streets, removing duplicates"""
        all_obligations = []
        seen_names = set()

        for report in street_reports:
            for obl in report.identified_obligations:
                # Simple deduplication by name
                if obl.name not in seen_names:
                    all_obligations.append(obl)
                    seen_names.add(obl.name)

        return all_obligations

    def _determine_building_verdict(
        self,
        street_reports: List[StreetReport],
        consolidated_obligations: List[Obligation],
    ) -> str:
        """
        Determine building verdict based on street reports and obligations.

        Logic:
        - OBJECT: If any hard blocking obligations
        - CONDITIONAL: If soft obligations or low confidence
        - APPROVE: Otherwise
        """
        # Check for hard blocking obligations
        hard_obligations = [
            obl for obl in consolidated_obligations if obl.severity == "HARD"
        ]

        if hard_obligations:
            return "CONDITIONAL"  # Has obligations, but not rejecting outright

        # Check street confidence levels
        avg_confidence = sum(r.confidence for r in street_reports) / len(
            street_reports
        )

        if avg_confidence < 0.6:
            return "OBJECT"  # Low confidence
        elif avg_confidence < 0.8:
            return "CONDITIONAL"
        else:
            return "APPROVE"


# Test
if __name__ == "__main__":
    import asyncio
    from oracle_town.schemas import Turn, Obligation

    async def test_building_supervisor():
        # Create mock street reports
        mock_report_1 = StreetReport(
            street_id="gdpr_001",
            street_name="GDPR Street",
            agent_turns=[
                Turn(
                    agent_id="analyst_001",
                    role="Privacy Analyst",
                    contribution="Found email and location data. GDPR applies.",
                    question="What's the legal risk?",
                    action="Flagging HIGH sensitivity",
                )
            ],
            preliminary_findings="GDPR compliance needed for location data",
            identified_obligations=[
                Obligation(
                    id="OBL_001",
                    type="LEGAL_COMPLIANCE",
                    name="GDPR consent mechanism",
                    description="Implement explicit consent for location data",
                    severity="HARD",
                )
            ],
            confidence=0.85,
        )

        mock_report_2 = StreetReport(
            street_id="contract_001",
            street_name="Contract Street",
            agent_turns=[
                Turn(
                    agent_id="contract_001",
                    role="Contract Reviewer",
                    contribution="Vendor contracts look good",
                    question="Any legal issues?",
                    action="Approving",
                )
            ],
            preliminary_findings="All vendor contracts in place",
            identified_obligations=[],
            confidence=0.90,
        )

        # Create building supervisor
        supervisor = BuildingSupervisor(
            building_id="legal_building_001",
            building_name="Legal Compliance Building",
            district="Legal & Compliance",
        )

        # Aggregate
        brief = await supervisor.aggregate_streets([mock_report_1, mock_report_2])

        print("=" * 70)
        print(f"BUILDING BRIEF: {brief.building_name}")
        print("=" * 70)
        print(f"District: {brief.district}")
        print(f"Streets: {len(brief.street_reports)}")
        print(f"\nConsolidated Findings:\n{brief.consolidated_findings[:500]}...")
        print(f"\nObligations: {len(brief.obligations)}")
        for obl in brief.obligations:
            print(f"  - {obl.name} ({obl.severity})")
        print(f"\nBuilding Verdict: {brief.building_verdict}")
        print(f"Supervisor Notes: {brief.supervisor_notes}")

    asyncio.run(test_building_supervisor())
