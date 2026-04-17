"""
Operations Street: 4-agent business operations analysis team

Agents:
1. Budget Analyst - Assesses costs, ROI, and financial viability
2. Operations Manager - Evaluates logistics, resources, and timeline
3. Risk Manager - Identifies business risks and mitigation strategies
4. Business Integrator - Synthesizes findings into Street Report
"""
import uuid
from typing import List
from oracle_town.agents import StreetAgent
from oracle_town.schemas import CompiledClaim, Turn, StreetReport, Obligation


class BudgetAnalyst(StreetAgent):
    """Agent 1: Assesses costs, ROI, and financial viability"""

    def __init__(self):
        system_prompt = """You are a Budget Analyst specializing in project financial assessment.

EXPERTISE: Cost estimation, ROI analysis, budget allocation, financial forecasting

YOUR TASK:
1. Estimate total project cost (development, operations, marketing)
2. Calculate expected ROI and payback period
3. Identify hidden costs (maintenance, scaling, support)
4. Assess budget feasibility against stated constraints
5. Flag cost overrun risks

COST CATEGORIES:
- Development: Engineering, design, testing
- Operations: Infrastructure, hosting, third-party services
- Marketing: Acquisition, retention campaigns
- Support: Customer service, maintenance

OUTPUT FORMAT (strictly follow):
## CONTRIBUTION
Budget Analysis:
- Estimated total cost: [amount]
- Development: [amount] | Operations: [amount/month] | Other: [amount]

ROI Assessment:
- Expected return: [amount or %]
- Payback period: [timeframe]
- Break-even point: [metrics]

Budget Feasibility: [FEASIBLE/AT RISK/NOT FEASIBLE]
Risk Level: [LOW/MEDIUM/HIGH]

## QUESTION
@Operations_Manager: [Question about resource allocation or timeline impact on costs]

## ACTION
Flagging [cost concerns] as [risk level]. Requires [budget adjustments needed]."""

        super().__init__(
            agent_id="budget_analyst_001",
            role="Budget Analyst",
            system_prompt=system_prompt,
        )


class OperationsManager(StreetAgent):
    """Agent 2: Evaluates logistics, resources, and timeline"""

    def __init__(self):
        system_prompt = """You are an Operations Manager specializing in project execution.

EXPERTISE: Resource planning, timeline management, logistics, team coordination

YOUR TASK:
1. Assess resource requirements (team size, skills, tools)
2. Evaluate timeline feasibility
3. Identify operational dependencies
4. Check for resource conflicts or constraints
5. Recommend operational structure

OPERATIONAL CONCERNS:
- Team availability and skills gaps
- Timeline vs. scope balance
- External dependencies (vendors, APIs, approvals)
- Parallel workstreams coordination

OUTPUT FORMAT:
## CONTRIBUTION
Operations Assessment:
- Team required: [roles and count]
- Timeline assessment: [feasible/tight/unrealistic]
- Dependencies: [list critical dependencies]

Resource Status:
- Available: [resources ready]
- Gaps: [missing resources]
- Constraints: [blockers]

Operational Feasibility: [READY/NEEDS PREP/NOT READY]

## QUESTION
@Risk_Manager: [Question about operational risks or contingencies]

## ACTION
Recommending [resource allocation or timeline adjustments]."""

        super().__init__(
            agent_id="operations_manager_001",
            role="Operations Manager",
            system_prompt=system_prompt,
        )


class RiskManager(StreetAgent):
    """Agent 3: Identifies business risks and mitigation strategies"""

    def __init__(self):
        system_prompt = """You are a Risk Manager specializing in business risk assessment.

EXPERTISE: Risk identification, impact analysis, mitigation strategies, contingency planning

YOUR TASK:
1. Identify all business risks (market, operational, financial, reputational)
2. Assess risk probability and impact
3. Propose mitigation strategies
4. Define contingency plans
5. Calculate risk-adjusted projections

RISK CATEGORIES:
- Market: Competition, demand changes, timing
- Operational: Execution failure, resource issues
- Financial: Cost overruns, revenue shortfall
- Reputational: Brand damage, customer trust
- External: Regulatory, economic, environmental

OUTPUT FORMAT:
## CONTRIBUTION
Risk Assessment:
- Risks identified: [count]
- Critical risks: [list high-impact risks]

Risk Matrix:
- [Risk 1]: Probability [H/M/L] × Impact [H/M/L] = [Score]
- [Risk 2]: [probability] × [impact] = [score]

Mitigation Strategies:
- [Risk]: [mitigation approach]

Overall Risk Level: [LOW/MEDIUM/HIGH/CRITICAL]

## QUESTION
@Business_Integrator: [Question about risk tolerance or go/no-go thresholds]

## ACTION
Recommending [risk mitigation measures or contingency preparations]."""

        super().__init__(
            agent_id="risk_manager_001",
            role="Risk Manager",
            system_prompt=system_prompt,
        )


class BusinessIntegrator(StreetAgent):
    """Agent 4: Synthesizes all business findings into Street Report"""

    def __init__(self):
        system_prompt = """You are the Business Integrator for Operations Street.

EXPERTISE: Synthesizing business analysis, go/no-go decisions, executive summaries

YOUR TASK:
1. Review all 3 previous agents' contributions
2. Identify BLOCKING business issues (HARD severity)
3. Identify ADVISORY business improvements (SOFT severity)
4. Determine street verdict: APPROVE | CONDITIONAL | OBJECT
5. Set confidence score (0.0-1.0)

VERDICT LOGIC:
- APPROVE: Budget feasible, operations ready, risks acceptable
- CONDITIONAL: Minor budget/ops issues, risks manageable with mitigation
- OBJECT: Budget not feasible, critical resource gaps, unacceptable risks

CONFIDENCE LEVELS:
- 0.9-1.0: Strong business case, all factors favorable
- 0.7-0.9: Good case with minor concerns
- 0.5-0.7: Significant business uncertainties
- <0.5: Weak business case

OUTPUT FORMAT:
## CONTRIBUTION
Business Street Report Summary:

Budget Status: [feasible/at risk/not feasible]
Operations Status: [ready/needs prep/not ready]
Risk Level: [acceptable/elevated/critical]

BLOCKING OBLIGATIONS:
1. [Obligation 1 - HARD]
2. [Obligation 2 - HARD]

ADVISORY ITEMS:
- [Advisory 1 - SOFT]

Business Case Strength: [STRONG/MODERATE/WEAK]
Verdict: [APPROVE/CONDITIONAL/OBJECT]
Confidence: [0.0-1.0]

## QUESTION
None (street analysis complete)

## ACTION
Submitting Street Report to Building Supervisor with [VERDICT]."""

        super().__init__(
            agent_id="business_integrator_001",
            role="Business Integrator",
            system_prompt=system_prompt,
        )


class OperationsStreet:
    """
    Orchestrates 4-agent business operations analysis.
    Follows ChatDev turn protocol: Agent1 → Agent2 → Agent3 → Agent4
    """

    def __init__(self):
        self.street_id = f"operations_street_{uuid.uuid4().hex[:6]}"
        self.street_name = "Business Operations Street"
        self.agents = [
            BudgetAnalyst(),
            OperationsManager(),
            RiskManager(),
            BusinessIntegrator(),
        ]

    async def analyze_claim(self, claim: CompiledClaim) -> StreetReport:
        """
        Run 4-turn analysis of claim for business viability.

        Returns:
            StreetReport with findings and obligations
        """
        conversation_history: List[Turn] = []

        for agent in self.agents:
            turn = await agent.execute_turn(claim, conversation_history)
            conversation_history.append(turn)

        final_turn = conversation_history[-1]
        findings = final_turn.contribution
        obligations = self._extract_obligations(final_turn.contribution)
        confidence = self._extract_confidence(final_turn.contribution)

        return StreetReport(
            street_id=self.street_id,
            street_name=self.street_name,
            agent_turns=conversation_history,
            preliminary_findings=findings,
            identified_obligations=obligations,
            confidence=confidence,
        )

    def _extract_obligations(self, integrator_output: str) -> List[Obligation]:
        """Extract obligations from integrator's contribution"""
        obligations = []

        lines = integrator_output.split("\n")
        in_blocking = False

        for line in lines:
            if "BLOCKING OBLIGATIONS" in line.upper():
                in_blocking = True
                continue
            if "ADVISORY" in line.upper() or "Verdict:" in line:
                in_blocking = False

            if in_blocking and line.strip() and line.strip()[0].isdigit():
                obl_text = line.split(".", 1)[1].strip() if "." in line else line.strip()
                obl_text = obl_text.replace("- HARD", "").replace("[HARD]", "").strip()

                obligations.append(Obligation(
                    id=f"OBL_BIZ_{uuid.uuid4().hex[:6].upper()}",
                    type="BUSINESS_OPERATIONS",
                    name=obl_text[:50],
                    description=obl_text,
                    severity="HARD",
                ))

        return obligations

    def _extract_confidence(self, integrator_output: str) -> float:
        """Extract confidence score from integrator's output"""
        import re
        match = re.search(r"Confidence:\s*([0-9.]+)", integrator_output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        if "APPROVE" in integrator_output:
            return 0.85
        elif "CONDITIONAL" in integrator_output:
            return 0.75
        else:
            return 0.60


# Test
if __name__ == "__main__":
    import asyncio
    from oracle_town.core.claim_compiler import ClaimCompiler
    from oracle_town.schemas import TownInput

    async def test_operations_street():
        compiler = ClaimCompiler()
        test_input = TownInput(
            raw_text="Launch premium eco-lodge business on private island. "
                     "Budget: 150k EUR. Timeline: 18 months. "
                     "Expected revenue: 100k/year after year 3. "
                     "Team: 2 FTE + contractors.",
            domain="product",
        )

        claim = compiler.compile(test_input)

        street = OperationsStreet()
        report = await street.analyze_claim(claim)

        print("=" * 70)
        print(f"OPERATIONS STREET REPORT: {report.street_name}")
        print("=" * 70)

        for i, turn in enumerate(report.agent_turns, 1):
            print(f"\n--- TURN {i}: {turn.role} ---")
            print(f"CONTRIBUTION:\n{turn.contribution}\n")

        print("=" * 70)
        print("FINAL ASSESSMENT")
        print("=" * 70)
        print(f"Confidence: {report.confidence}")
        print(f"Obligations: {len(report.identified_obligations)}")
        for obl in report.identified_obligations:
            print(f"  - {obl.name} ({obl.severity})")

    asyncio.run(test_operations_street())
