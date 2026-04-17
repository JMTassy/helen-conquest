"""
Security Street: 4-agent technical security analysis team

Agents:
1. Security Analyst - Identifies vulnerabilities and attack vectors
2. Performance Engineer - Assesses scalability and performance risks
3. Architecture Reviewer - Evaluates design patterns and technical debt
4. Tech Integrator - Synthesizes findings into Street Report
"""
import uuid
from typing import List
from oracle_town.agents import StreetAgent
from oracle_town.schemas import CompiledClaim, Turn, StreetReport, Obligation


class SecurityAnalyst(StreetAgent):
    """Agent 1: Identifies security vulnerabilities and attack vectors"""

    def __init__(self):
        system_prompt = """You are a Security Analyst specializing in application security.

EXPERTISE: OWASP Top 10, authentication, authorization, data encryption, API security

YOUR TASK:
1. Identify ALL potential security vulnerabilities in the claim
2. Check for authentication/authorization requirements
3. Assess data encryption needs (at rest, in transit)
4. Identify injection risks (SQL, XSS, command injection)
5. Evaluate API security requirements

VULNERABILITY CATEGORIES:
- CRITICAL: Authentication bypass, data exposure, injection
- HIGH: Broken access control, security misconfig
- MEDIUM: Sensitive data exposure, insufficient logging
- LOW: Minor information disclosure

OUTPUT FORMAT (strictly follow):
## CONTRIBUTION
Security Analysis:
- Attack vectors identified: [list]
- Authentication requirements: [present/missing/unclear]
- Data encryption: [required/not required/unclear]

Vulnerabilities Found:
- [Vuln 1]: [CRITICAL/HIGH/MEDIUM/LOW] - [description]
- [Vuln 2]: [severity] - [description]

Risk Level: [LOW/MEDIUM/HIGH/CRITICAL]

## QUESTION
@Performance_Engineer: [Question about performance implications of security measures]

## ACTION
Flagging [vulnerabilities] as [severity]. Requires [security controls needed]."""

        super().__init__(
            agent_id="security_analyst_001",
            role="Security Analyst",
            system_prompt=system_prompt,
        )


class PerformanceEngineer(StreetAgent):
    """Agent 2: Assesses scalability and performance requirements"""

    def __init__(self):
        system_prompt = """You are a Performance Engineer specializing in system scalability.

EXPERTISE: Load testing, caching strategies, database optimization, CDN, auto-scaling

YOUR TASK:
1. Estimate expected load based on claim requirements
2. Identify performance bottlenecks
3. Recommend caching strategies
4. Assess database scaling needs
5. Evaluate infrastructure requirements

PERFORMANCE CONCERNS:
- Response time targets (< 200ms API, < 3s page load)
- Concurrent user capacity
- Data volume growth projections
- Peak load handling

OUTPUT FORMAT:
## CONTRIBUTION
Performance Assessment:
- Expected load: [users/requests per second]
- Bottlenecks identified: [list]
- Caching requirements: [strategy needed]

Infrastructure Needs:
- Database: [type, scaling approach]
- Compute: [sizing recommendations]
- CDN: [required/not required]

Risk Level: [LOW/MEDIUM/HIGH]

## QUESTION
@Architecture_Reviewer: [Question about architectural patterns for scalability]

## ACTION
Recommending [infrastructure/caching/optimization requirements]."""

        super().__init__(
            agent_id="performance_engineer_001",
            role="Performance Engineer",
            system_prompt=system_prompt,
        )


class ArchitectureReviewer(StreetAgent):
    """Agent 3: Evaluates design patterns and technical debt"""

    def __init__(self):
        system_prompt = """You are an Architecture Reviewer specializing in system design.

EXPERTISE: Design patterns, microservices, API design, technical debt, maintainability

YOUR TASK:
1. Evaluate proposed architecture patterns
2. Identify potential technical debt
3. Assess API design quality
4. Check for separation of concerns
5. Verify testability and maintainability

ARCHITECTURE CONCERNS:
- Coupling and cohesion
- Single responsibility principle
- API versioning strategy
- Error handling patterns
- Observability (logging, metrics, tracing)

OUTPUT FORMAT:
## CONTRIBUTION
Architecture Review:
- Design pattern assessment: [appropriate/needs improvement]
- Technical debt risk: [LOW/MEDIUM/HIGH]
- API design quality: [good/acceptable/poor]

Concerns:
- [Concern 1]: [description and impact]
- [Concern 2]: [description and impact]

Maintainability Score: [1-10]

## QUESTION
@Tech_Integrator: [Question about prioritizing technical improvements]

## ACTION
Recommending [architectural changes or best practices]."""

        super().__init__(
            agent_id="architecture_reviewer_001",
            role="Architecture Reviewer",
            system_prompt=system_prompt,
        )


class TechIntegrator(StreetAgent):
    """Agent 4: Synthesizes all technical findings into Street Report"""

    def __init__(self):
        system_prompt = """You are the Tech Integrator for Security Street.

EXPERTISE: Synthesizing technical findings, prioritizing issues, creating actionable reports

YOUR TASK:
1. Review all 3 previous agents' contributions
2. Identify BLOCKING technical issues (HARD severity)
3. Identify ADVISORY technical improvements (SOFT severity)
4. Determine street verdict: APPROVE | CONDITIONAL | OBJECT
5. Set confidence score (0.0-1.0)

VERDICT LOGIC:
- APPROVE: No critical/high security issues, acceptable performance, good architecture
- CONDITIONAL: Medium issues fixable, performance improvements needed
- OBJECT: Critical security vulnerabilities, major performance risks, poor architecture

CONFIDENCE LEVELS:
- 0.9-1.0: Clear technical path, all concerns addressed
- 0.7-0.9: Minor technical uncertainties
- 0.5-0.7: Significant technical unknowns
- <0.5: Major technical concerns

OUTPUT FORMAT:
## CONTRIBUTION
Technical Street Report Summary:

Security Status: [secure/needs hardening/vulnerable]
Performance Status: [scalable/needs optimization/at risk]
Architecture Status: [solid/acceptable/concerning]

BLOCKING OBLIGATIONS:
1. [Obligation 1 - HARD]
2. [Obligation 2 - HARD]

ADVISORY ITEMS:
- [Advisory 1 - SOFT]

Verdict: [APPROVE/CONDITIONAL/OBJECT]
Confidence: [0.0-1.0]

## QUESTION
None (street analysis complete)

## ACTION
Submitting Street Report to Building Supervisor with [VERDICT]."""

        super().__init__(
            agent_id="tech_integrator_001",
            role="Tech Integrator",
            system_prompt=system_prompt,
        )


class SecurityStreet:
    """
    Orchestrates 4-agent technical security analysis.
    Follows ChatDev turn protocol: Agent1 → Agent2 → Agent3 → Agent4
    """

    def __init__(self):
        self.street_id = f"security_street_{uuid.uuid4().hex[:6]}"
        self.street_name = "Security & Performance Street"
        self.agents = [
            SecurityAnalyst(),
            PerformanceEngineer(),
            ArchitectureReviewer(),
            TechIntegrator(),
        ]

    async def analyze_claim(self, claim: CompiledClaim) -> StreetReport:
        """
        Run 4-turn analysis of claim for technical/security compliance.

        Returns:
            StreetReport with findings and obligations
        """
        conversation_history: List[Turn] = []

        # Execute 4 turns in sequence
        for agent in self.agents:
            turn = await agent.execute_turn(claim, conversation_history)
            conversation_history.append(turn)

        # Extract findings from final integrator turn
        final_turn = conversation_history[-1]
        findings = final_turn.contribution

        # Parse obligations from integrator's output
        obligations = self._extract_obligations(final_turn.contribution)

        # Parse confidence
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
                    id=f"OBL_TECH_{uuid.uuid4().hex[:6].upper()}",
                    type="TECHNICAL_SECURITY",
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

    async def test_security_street():
        compiler = ClaimCompiler()
        test_input = TownInput(
            raw_text="Build a user authentication system with OAuth2 and JWT tokens. "
                     "Store user data in PostgreSQL. Expose REST API for mobile apps. "
                     "Expected 50k daily active users.",
            domain="product",
        )

        claim = compiler.compile(test_input)

        street = SecurityStreet()
        report = await street.analyze_claim(claim)

        print("=" * 70)
        print(f"SECURITY STREET REPORT: {report.street_name}")
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

    asyncio.run(test_security_street())
