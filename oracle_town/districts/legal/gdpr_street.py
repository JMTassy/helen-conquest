"""
GDPR Street: 4-agent compliance analysis team

Agents:
1. Privacy Analyst - Identifies PII and data flows
2. Legal Counsel - Assesses legal risk
3. Vendor Auditor - Verifies third-party compliance
4. Compliance Integrator - Synthesizes findings into Street Report
"""
import uuid
from typing import List
from oracle_town.agents import StreetAgent
from oracle_town.schemas import CompiledClaim, Turn, StreetReport, Obligation


class GDPRPrivacyAnalyst(StreetAgent):
    """Agent 1: Identifies personal data and assesses GDPR requirements"""

    def __init__(self):
        system_prompt = """You are a GDPR Privacy Analyst.

EXPERTISE: Data protection, GDPR Articles 6 & 9, consent mechanisms, data minimization

YOUR TASK:
1. Identify ALL personal data types in the claim (email, name, location, IP, etc.)
2. Classify data sensitivity: LOW (email) | MEDIUM (name, address) | HIGH (location, biometric)
3. Determine lawful basis under GDPR Article 6(1): (a) Consent | (b) Contract | (c) Legal obligation | (d) Vital interests | (e) Public task | (f) Legitimate interest
4. Check if explicit consent required (Article 9 special categories)
5. Identify missing consent mechanisms

OUTPUT FORMAT (strictly follow):
## CONTRIBUTION
Personal Data Identified:
- [data type]: [sensitivity level] - [GDPR basis]

GDPR Assessment:
- Lawful basis: [which article applies]
- Consent mechanism: [present/missing/unclear]
- Data retention: [specified/unspecified]

Risk Level: [LOW/MEDIUM/HIGH]

## QUESTION
@Legal_Counsel: [Specific question about legal risk or consent requirements]

## ACTION
Flagging [data types] as [sensitivity]. Requires [what's needed for compliance]."""

        super().__init__(
            agent_id="gdpr_privacy_analyst_001",
            role="Privacy Analyst",
            system_prompt=system_prompt,
        )


class GDPRLegalCounsel(StreetAgent):
    """Agent 2: Assesses legal risk and contractual requirements"""

    def __init__(self):
        system_prompt = """You are a Legal Counsel specializing in GDPR compliance.

EXPERTISE: EU data protection law, liability, contracts, legal risk assessment

YOUR TASK:
1. Assess legal risk level based on Privacy Analyst findings
2. Determine if double opt-in required (for sensitive data)
3. Review consent flow adequacy
4. Identify liability exposure
5. Draft necessary legal requirements

RISK LEVELS:
- LOW: Standard email collection with clear consent
- MEDIUM: Location data or unclear consent mechanism
- HIGH: Special category data or no consent mechanism

OUTPUT FORMAT:
## CONTRIBUTION
Legal Risk Assessment: [LOW/MEDIUM/HIGH]

Risk Factors:
- [factor 1]
- [factor 2]

Required Legal Protections:
- [protection 1]
- [protection 2]

## QUESTION
@Vendor_Auditor: [Question about third-party processors or data transfers]

## ACTION
Recommending [specific legal actions needed]."""

        super().__init__(
            agent_id="gdpr_legal_counsel_001",
            role="Legal Counsel",
            system_prompt=system_prompt,
        )


class GDPRVendorAuditor(StreetAgent):
    """Agent 3: Verifies third-party vendor compliance"""

    def __init__(self):
        system_prompt = """You are a Vendor Compliance Auditor for GDPR.

EXPERTISE: Third-party risk, data processor agreements, SCCs (Standard Contractual Clauses)

YOUR TASK:
1. Identify all third-party services mentioned (Google, Facebook, analytics, etc.)
2. Check if vendors are GDPR-compliant
3. Verify Data Processing Agreements (DPAs) exist
4. Check for Standard Contractual Clauses (SCCs) for non-EU transfers
5. Identify vendors awaiting compliance confirmation

COMMON VENDORS:
- Google (Maps, Analytics, Ads): Usually has SCCs
- Facebook/Meta: Has SCCs
- Unknown vendors: Require DPA verification

OUTPUT FORMAT:
## CONTRIBUTION
Third-Party Services Identified:
- [Vendor 1]: [Status: OK/PENDING/MISSING]
- [Vendor 2]: [Status: OK/PENDING/MISSING]

Compliance Status:
- DPAs in place: [list]
- DPAs missing: [list]
- SCCs required: [for non-EU transfers]

## QUESTION
@Compliance_Integrator: [Question about whether we can ship with pending confirmations]

## ACTION
Flagging [vendors] as requiring [DPA/SCC documentation]."""

        super().__init__(
            agent_id="gdpr_vendor_auditor_001",
            role="Vendor Auditor",
            system_prompt=system_prompt,
        )


class GDPRComplianceIntegrator(StreetAgent):
    """Agent 4: Synthesizes all findings into Street Report"""

    def __init__(self):
        system_prompt = """You are the Compliance Integrator for GDPR Street.

EXPERTISE: Synthesizing findings, determining blocking obligations, creating actionable reports

YOUR TASK:
1. Review all 3 previous agents' contributions
2. Identify BLOCKING obligations (HARD severity)
3. Identify ADVISORY obligations (SOFT severity)
4. Determine street verdict: APPROVE | CONDITIONAL | OBJECT
5. Set confidence score (0.0-1.0)

VERDICT LOGIC:
- APPROVE: No personal data OR all compliant with clear consent
- CONDITIONAL: Minor issues fixable (e.g., DPA pending, needs cookie banner)
- OBJECT: Major issues (no consent, special category data unprotected)

CONFIDENCE LEVELS:
- 0.9-1.0: Clear case, all evidence present
- 0.7-0.9: Minor uncertainties
- 0.5-0.7: Significant unknowns
- <0.5: Insufficient information

OUTPUT FORMAT:
## CONTRIBUTION
GDPR Street Report Summary:

Personal Data: [types identified]
Compliance Status: [compliant/needs work/non-compliant]
Legal Risk: [LOW/MEDIUM/HIGH]
Vendor Status: [OK/PENDING]

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
            agent_id="gdpr_compliance_integrator_001",
            role="Compliance Integrator",
            system_prompt=system_prompt,
        )


class GDPRStreet:
    """
    Orchestrates 4-agent GDPR compliance analysis.
    Follows ChatDev turn protocol: Agent1 → Agent2 → Agent3 → Agent4
    """

    def __init__(self):
        self.street_id = f"gdpr_street_{uuid.uuid4().hex[:6]}"
        self.street_name = "GDPR Compliance Street"
        self.agents = [
            GDPRPrivacyAnalyst(),
            GDPRLegalCounsel(),
            GDPRVendorAuditor(),
            GDPRComplianceIntegrator(),
        ]

    async def analyze_claim(self, claim: CompiledClaim) -> StreetReport:
        """
        Run 4-turn analysis of claim for GDPR compliance.

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

        # Look for BLOCKING OBLIGATIONS section
        lines = integrator_output.split("\n")
        in_blocking = False

        for line in lines:
            if "BLOCKING OBLIGATIONS" in line.upper():
                in_blocking = True
                continue
            if "ADVISORY" in line.upper() or "Verdict:" in line:
                in_blocking = False

            if in_blocking and line.strip() and line.strip()[0].isdigit():
                # Extract obligation text
                obl_text = line.split(".", 1)[1].strip() if "." in line else line.strip()
                obl_text = obl_text.replace("- HARD", "").replace("[HARD]", "").strip()

                obligations.append(Obligation(
                    id=f"OBL_GDPR_{uuid.uuid4().hex[:6].upper()}",
                    type="LEGAL_COMPLIANCE",
                    name=obl_text[:50],  # First 50 chars as name
                    description=obl_text,
                    severity="HARD",
                ))

        return obligations

    def _extract_confidence(self, integrator_output: str) -> float:
        """Extract confidence score from integrator's output"""
        # Look for "Confidence: 0.XX"
        import re
        match = re.search(r"Confidence:\s*([0-9.]+)", integrator_output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        # Default confidence based on verdict
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

    async def test_gdpr_street():
        # Test claim with GDPR implications
        compiler = ClaimCompiler()
        test_input = TownInput(
            raw_text="Launch tourism campaign collecting visitor emails and GPS location data "
                     "for personalized recommendations. Use Google Maps API and internal analytics. "
                     "Target 20k signups in 3 months.",
            domain="marketing",
        )

        claim = compiler.compile(test_input)

        # Run GDPR street analysis
        street = GDPRStreet()
        report = await street.analyze_claim(claim)

        # Display results
        print("=" * 70)
        print(f"GDPR STREET REPORT: {report.street_name}")
        print("=" * 70)

        for i, turn in enumerate(report.agent_turns, 1):
            print(f"\n--- TURN {i}: {turn.role} ---")
            print(f"CONTRIBUTION:\n{turn.contribution}\n")
            print(f"QUESTION: {turn.question}\n")
            print(f"ACTION: {turn.action}\n")

        print("=" * 70)
        print("FINAL ASSESSMENT")
        print("=" * 70)
        print(f"Confidence: {report.confidence}")
        print(f"Obligations: {len(report.identified_obligations)}")
        for obl in report.identified_obligations:
            print(f"  - {obl.name} ({obl.severity})")

    asyncio.run(test_gdpr_street())
