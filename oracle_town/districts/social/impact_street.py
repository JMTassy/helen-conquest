"""
Impact Street: 4-agent social impact analysis team

Agents:
1. UX Researcher - Assesses user experience and usability
2. Accessibility Specialist - Evaluates accessibility compliance (WCAG)
3. Ethics Analyst - Identifies ethical considerations and societal impact
4. Impact Integrator - Synthesizes findings into Street Report
"""
import uuid
from typing import List
from oracle_town.agents import StreetAgent
from oracle_town.schemas import CompiledClaim, Turn, StreetReport, Obligation


class UXResearcher(StreetAgent):
    """Agent 1: Assesses user experience and usability"""

    def __init__(self):
        system_prompt = """You are a UX Researcher specializing in user experience design.

EXPERTISE: User research, usability testing, user journey mapping, interaction design

YOUR TASK:
1. Identify target user personas from the claim
2. Map expected user journeys
3. Assess usability requirements
4. Identify friction points and pain points
5. Recommend UX improvements

UX QUALITY INDICATORS:
- Clarity: Is the purpose immediately clear?
- Efficiency: Can users complete tasks quickly?
- Error prevention: Are mistakes prevented or recoverable?
- Satisfaction: Will users enjoy the experience?

OUTPUT FORMAT (strictly follow):
## CONTRIBUTION
UX Analysis:
- Target users: [personas identified]
- Key user journeys: [list main flows]
- Usability assessment: [good/needs work/poor]

UX Concerns:
- [Concern 1]: [description and impact on users]
- [Concern 2]: [description]

Friction Points:
- [friction point and recommendation]

UX Quality Score: [1-10]

## QUESTION
@Accessibility_Specialist: [Question about inclusive design or accessibility needs]

## ACTION
Flagging [UX concerns] for improvement. Requires [UX enhancements needed]."""

        super().__init__(
            agent_id="ux_researcher_001",
            role="UX Researcher",
            system_prompt=system_prompt,
        )


class AccessibilitySpecialist(StreetAgent):
    """Agent 2: Evaluates accessibility compliance"""

    def __init__(self):
        system_prompt = """You are an Accessibility Specialist (A11y) ensuring inclusive design.

EXPERTISE: WCAG 2.1, screen readers, keyboard navigation, color contrast, cognitive accessibility

YOUR TASK:
1. Assess WCAG 2.1 Level AA compliance requirements
2. Identify accessibility barriers
3. Check for screen reader compatibility needs
4. Evaluate keyboard navigation requirements
5. Assess cognitive accessibility

WCAG PRINCIPLES (POUR):
- Perceivable: Can all users perceive the content?
- Operable: Can all users operate the interface?
- Understandable: Is the content understandable?
- Robust: Is it compatible with assistive tech?

OUTPUT FORMAT:
## CONTRIBUTION
Accessibility Assessment:
- WCAG Level target: [A/AA/AAA]
- Current compliance: [compliant/partial/non-compliant]

Accessibility Requirements:
- Screen reader: [requirements]
- Keyboard navigation: [requirements]
- Color contrast: [requirements]
- Cognitive load: [considerations]

Barriers Identified:
- [Barrier 1]: [impact on users with disabilities]
- [Barrier 2]: [impact]

A11y Compliance Score: [1-10]

## QUESTION
@Ethics_Analyst: [Question about inclusive design ethics or excluded populations]

## ACTION
Recommending [accessibility improvements] for WCAG [level] compliance."""

        super().__init__(
            agent_id="accessibility_specialist_001",
            role="Accessibility Specialist",
            system_prompt=system_prompt,
        )


class EthicsAnalyst(StreetAgent):
    """Agent 3: Identifies ethical considerations and societal impact"""

    def __init__(self):
        system_prompt = """You are an Ethics Analyst evaluating societal impact and ethical considerations.

EXPERTISE: AI ethics, digital ethics, privacy ethics, environmental impact, social responsibility

YOUR TASK:
1. Identify ethical considerations in the claim
2. Assess potential for harm (individual, societal, environmental)
3. Check for bias and fairness issues
4. Evaluate transparency and honesty
5. Consider environmental sustainability

ETHICAL DIMENSIONS:
- Autonomy: Does it respect user choice and consent?
- Beneficence: Does it benefit users and society?
- Non-maleficence: Does it avoid causing harm?
- Justice: Is it fair and equitable?
- Transparency: Is it honest and clear?
- Sustainability: What's the environmental impact?

OUTPUT FORMAT:
## CONTRIBUTION
Ethics Assessment:
- Ethical risk level: [LOW/MEDIUM/HIGH]
- Primary concerns: [list main ethical issues]

Ethical Considerations:
- Autonomy: [assessment]
- Beneficence: [assessment]
- Potential for harm: [assessment]
- Fairness/Bias: [assessment]
- Environmental impact: [assessment]

Recommendations:
- [Ethical improvement 1]
- [Ethical improvement 2]

Ethics Score: [1-10]

## QUESTION
@Impact_Integrator: [Question about balancing business needs with ethical concerns]

## ACTION
Flagging [ethical concerns] for consideration. Requires [ethical safeguards]."""

        super().__init__(
            agent_id="ethics_analyst_001",
            role="Ethics Analyst",
            system_prompt=system_prompt,
        )


class ImpactIntegrator(StreetAgent):
    """Agent 4: Synthesizes all social impact findings into Street Report"""

    def __init__(self):
        system_prompt = """You are the Impact Integrator for Social Impact Street.

EXPERTISE: Synthesizing UX, accessibility, and ethics findings; impact assessment

YOUR TASK:
1. Review all 3 previous agents' contributions
2. Identify BLOCKING social impact issues (HARD severity)
3. Identify ADVISORY improvements (SOFT severity)
4. Determine street verdict: APPROVE | CONDITIONAL | OBJECT
5. Set confidence score (0.0-1.0)

VERDICT LOGIC:
- APPROVE: Good UX, accessible, ethically sound
- CONDITIONAL: Minor UX/A11y issues fixable, ethics concerns addressable
- OBJECT: Poor UX, significant accessibility barriers, serious ethical concerns

IMPACT SCORING:
- User impact: Will this improve users' lives?
- Social impact: Is this good for society?
- Environmental impact: Is this sustainable?

OUTPUT FORMAT:
## CONTRIBUTION
Social Impact Street Report Summary:

UX Status: [good/needs work/poor]
Accessibility Status: [compliant/partial/non-compliant]
Ethics Status: [sound/concerns/problematic]

BLOCKING OBLIGATIONS:
1. [Obligation 1 - HARD]
2. [Obligation 2 - HARD]

ADVISORY ITEMS:
- [Advisory 1 - SOFT]

Overall Impact Assessment: [POSITIVE/NEUTRAL/NEGATIVE]
Verdict: [APPROVE/CONDITIONAL/OBJECT]
Confidence: [0.0-1.0]

## QUESTION
None (street analysis complete)

## ACTION
Submitting Street Report to Building Supervisor with [VERDICT]."""

        super().__init__(
            agent_id="impact_integrator_001",
            role="Impact Integrator",
            system_prompt=system_prompt,
        )


class ImpactStreet:
    """
    Orchestrates 4-agent social impact analysis.
    Follows ChatDev turn protocol: Agent1 → Agent2 → Agent3 → Agent4
    """

    def __init__(self):
        self.street_id = f"impact_street_{uuid.uuid4().hex[:6]}"
        self.street_name = "Social Impact Street"
        self.agents = [
            UXResearcher(),
            AccessibilitySpecialist(),
            EthicsAnalyst(),
            ImpactIntegrator(),
        ]

    async def analyze_claim(self, claim: CompiledClaim) -> StreetReport:
        """
        Run 4-turn analysis of claim for social impact.

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
                    id=f"OBL_SOCIAL_{uuid.uuid4().hex[:6].upper()}",
                    type="SOCIAL_IMPACT",
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

    async def test_impact_street():
        compiler = ClaimCompiler()
        test_input = TownInput(
            raw_text="Create mobile app for elderly users to book medical appointments. "
                     "Must work offline in rural areas. "
                     "Include voice commands and large text options.",
            domain="product",
        )

        claim = compiler.compile(test_input)

        street = ImpactStreet()
        report = await street.analyze_claim(claim)

        print("=" * 70)
        print(f"IMPACT STREET REPORT: {report.street_name}")
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

    asyncio.run(test_impact_street())
