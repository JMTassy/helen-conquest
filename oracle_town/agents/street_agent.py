"""Street Agent: Base class for all street-level agents"""
import re
from typing import List, Optional
from datetime import datetime
from oracle_town.schemas import CompiledClaim, Turn


class MockLLM:
    """
    Mock LLM for testing (no API calls).
    Replace with real OpenAI/Anthropic client in production.
    """

    def __init__(self, model: str = "gpt-4"):
        self.model = model

    async def complete(self, system: str, user: str) -> str:
        """Simulate LLM response"""
        # For MVP: Return structured mock response
        # In production: Call actual LLM API
        return f"""## CONTRIBUTION
[Mock analysis based on: {user[:100]}...]

## QUESTION
@NextAgent: What is your assessment?

## ACTION
Flagging for further review."""


class StreetAgent:
    """
    Base class for street-level agents.
    Enforces ChatDev-style turn protocol: CONTRIBUTION → QUESTION → ACTION
    """

    def __init__(
        self,
        agent_id: str,
        role: str,
        system_prompt: str,
        llm: Optional[MockLLM] = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm or MockLLM()

    async def execute_turn(
        self,
        claim: CompiledClaim,
        conversation_history: List[Turn],
    ) -> Turn:
        """
        Execute one turn in the conversation.

        Args:
            claim: The claim being analyzed
            conversation_history: Previous turns in this street

        Returns:
            Turn with CONTRIBUTION, QUESTION, ACTION
        """
        context = self._build_context(claim, conversation_history)

        # Call LLM
        response = await self.llm.complete(
            system=self.system_prompt,
            user=context,
        )

        # Parse and enforce protocol
        turn = self._parse_turn(response)
        turn.agent_id = self.agent_id
        turn.role = self.role
        turn.timestamp = datetime.utcnow().isoformat()

        return turn

    def _build_context(
        self,
        claim: CompiledClaim,
        conversation_history: List[Turn],
    ) -> str:
        """Build context for LLM from claim + conversation history"""
        context_parts = [
            "=== CLAIM UNDER REVIEW ===",
            f"Claim ID: {claim.claim_id}",
            f"Type: {claim.claim_type}",
            f"Text: {claim.claim_text}",
            "",
            "=== SUCCESS CRITERIA ===",
        ]

        for i, criterion in enumerate(claim.success_criteria, 1):
            context_parts.append(f"{i}. {criterion}")

        if claim.initial_obligations:
            context_parts.extend([
                "",
                "=== KNOWN OBLIGATIONS ===",
            ])
            for obl in claim.initial_obligations:
                context_parts.append(f"- {obl.name}: {obl.description}")

        if conversation_history:
            context_parts.extend([
                "",
                "=== PREVIOUS DISCUSSION ===",
            ])
            for turn in conversation_history:
                context_parts.extend([
                    f"",
                    f"[{turn.role}]",
                    f"CONTRIBUTION: {turn.contribution}",
                    f"QUESTION: {turn.question}",
                    f"ACTION: {turn.action}",
                ])

        context_parts.extend([
            "",
            "=== YOUR TASK ===",
            f"As {self.role}, analyze this claim from your expertise area.",
            "You MUST respond with:",
            "1. ## CONTRIBUTION - Your primary analysis/findings",
            "2. ## QUESTION - A question to another agent or next phase",
            "3. ## ACTION - What happens next based on your findings",
        ])

        return "\n".join(context_parts)

    def _parse_turn(self, response: str) -> Turn:
        """
        Parse LLM response into structured Turn.
        Enforces protocol: CONTRIBUTION, QUESTION, ACTION sections required.
        """
        contribution = self._extract_section(response, "CONTRIBUTION")
        question = self._extract_section(response, "QUESTION")
        action = self._extract_section(response, "ACTION")

        # Validate protocol compliance
        if not contribution:
            contribution = "[ERROR: Missing CONTRIBUTION section]"
        if not question:
            question = "[ERROR: Missing QUESTION section]"
        if not action:
            action = "[ERROR: Missing ACTION section]"

        return Turn(
            agent_id=self.agent_id,
            role=self.role,
            contribution=contribution.strip(),
            question=question.strip(),
            action=action.strip(),
        )

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract content of a section (CONTRIBUTION, QUESTION, ACTION)"""
        # Match ## SECTION_NAME followed by content until next ## or end
        pattern = rf"##\s*{section_name}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # Fallback: try without ##
        pattern = rf"{section_name}[:\s]+(.*?)(?=\n(?:CONTRIBUTION|QUESTION|ACTION)|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        return ""


# Example street agent implementations
class PrivacyAnalystAgent(StreetAgent):
    """Specialized agent for GDPR/privacy analysis"""

    def __init__(self, agent_id: str = "privacy_analyst_001"):
        system_prompt = """You are a Privacy Analyst specializing in GDPR compliance.

Your role:
- Identify all personal data types mentioned in the claim
- Check for explicit consent mechanisms
- Verify data retention policies
- Flag PII sensitivity levels (LOW/MEDIUM/HIGH)
- Assess GDPR Article 6 lawful basis

You MUST output in this format:
## CONTRIBUTION
[Your privacy analysis]

## QUESTION
[Question to Legal Counsel or Vendor Auditor]

## ACTION
[What you're flagging or recommending]

Be specific about data types and compliance requirements."""

        super().__init__(
            agent_id=agent_id,
            role="Privacy Analyst",
            system_prompt=system_prompt,
        )


class LegalCounselAgent(StreetAgent):
    """Specialized agent for legal risk assessment"""

    def __init__(self, agent_id: str = "legal_counsel_001"):
        system_prompt = """You are a Legal Counsel specializing in risk assessment.

Your role:
- Assess legal risk level (LOW/MEDIUM/HIGH)
- Review contractual obligations
- Identify liability concerns
- Draft necessary legal disclaimers
- Verify regulatory compliance

You MUST output in this format:
## CONTRIBUTION
[Your legal risk assessment]

## QUESTION
[Question to Vendor Auditor or Compliance Integrator]

## ACTION
[Legal actions required or disclaimers needed]

Be specific about risk levels and required legal protections."""

        super().__init__(
            agent_id=agent_id,
            role="Legal Counsel",
            system_prompt=system_prompt,
        )


# Test
if __name__ == "__main__":
    import asyncio
    from oracle_town.core.claim_compiler import ClaimCompiler
    from oracle_town.schemas import TownInput

    async def test_agent():
        # Compile a test claim
        compiler = ClaimCompiler()
        test_input = TownInput(
            raw_text="Launch campaign collecting user emails for newsletter. "
                     "Target 10k signups in 2 months.",
            domain="marketing",
        )
        claim = compiler.compile(test_input)

        # Create privacy analyst
        agent = PrivacyAnalystAgent()

        # Execute turn
        turn = await agent.execute_turn(claim, [])

        print("=" * 60)
        print(f"AGENT: {turn.role}")
        print("=" * 60)
        print(f"CONTRIBUTION:\n{turn.contribution}\n")
        print(f"QUESTION:\n{turn.question}\n")
        print(f"ACTION:\n{turn.action}\n")

    asyncio.run(test_agent())
