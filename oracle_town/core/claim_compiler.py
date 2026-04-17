"""Claim Compiler: Transforms natural language input into structured claims"""
import uuid
import re
from typing import Optional
from oracle_town.schemas import TownInput, CompiledClaim, Obligation


class ClaimCompiler:
    """
    Transforms natural language descriptions into structured, machine-verifiable claims.
    Uses simple pattern matching for MVP (can be upgraded to LLM-based later).
    """

    def __init__(self):
        self.claim_type_keywords = {
            "FEATURE": ["feature", "build", "implement", "develop", "create"],
            "CAMPAIGN": ["campaign", "marketing", "promote", "advertise", "launch"],
            "POLICY": ["policy", "rule", "regulation", "governance", "compliance"],
            "PARTNERSHIP": ["partner", "collaboration", "agreement", "deal"],
            "EVENT": ["event", "conference", "meetup", "workshop"],
        }

    def compile(self, town_input: TownInput) -> CompiledClaim:
        """
        Compile natural language input into structured claim.

        For MVP: Uses keyword matching and pattern extraction.
        For production: Upgrade to LLM-based compilation (GPT-4, Claude).
        """
        claim_id = f"CLM_{uuid.uuid4().hex[:8].upper()}"
        claim_type = self._infer_claim_type(town_input)
        claim_text = self._formalize_claim_text(town_input)
        success_criteria = self._extract_success_criteria(town_input)
        requires_receipts = self._check_receipts_requirement(town_input)
        initial_obligations = self._identify_initial_obligations(town_input)

        return CompiledClaim(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type,
            success_criteria=success_criteria,
            requires_receipts=requires_receipts,
            initial_obligations=initial_obligations,
        )

    def _infer_claim_type(self, town_input: TownInput) -> str:
        """Infer claim type from input text and domain"""
        text_lower = town_input.raw_text.lower()

        # Domain-based routing first
        domain_map = {
            "marketing": "CAMPAIGN",
            "product": "FEATURE",
            "policy": "POLICY",
            "event": "EVENT",
        }
        if town_input.domain in domain_map:
            return domain_map[town_input.domain]

        # Keyword-based fallback
        for claim_type, keywords in self.claim_type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return claim_type

        return "FEATURE"  # Default

    def _formalize_claim_text(self, town_input: TownInput) -> str:
        """Convert raw text into formal claim statement"""
        # For MVP: Clean up and format
        # For production: Use LLM to formalize
        text = town_input.raw_text.strip()

        # Extract key components
        goal = self._extract_goal(text)
        target = self._extract_target_audience(text)
        timeline = self._extract_timeline(text)

        # Format as formal claim
        parts = [goal]
        if target:
            parts.append(f"targeting {target}")
        if timeline:
            parts.append(f"within {timeline}")

        return " ".join(parts)

    def _extract_goal(self, text: str) -> str:
        """Extract main goal from text"""
        # Look for action verbs
        goal_patterns = [
            r"^(launch|create|build|implement|develop|run)\s+(.+?)(?:\.|,|targeting|for|within|$)",
            r"^(.+?)(?:targeting|for|within|$)",
        ]

        for pattern in goal_patterns:
            match = re.search(pattern, text.lower(), re.IGNORECASE)
            if match:
                return match.group(0).strip().rstrip(".,")

        return text.split(".")[0]  # First sentence as fallback

    def _extract_target_audience(self, text: str) -> Optional[str]:
        """Extract target audience if mentioned"""
        patterns = [
            r"targeting\s+([^.;,]+)",
            r"for\s+([^.;,]+)\s+(?:audience|users|customers|demographic)",
            r"(\d+-\d+)\s+(?:year|age|demographic)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_timeline(self, text: str) -> Optional[str]:
        """Extract timeline if mentioned"""
        patterns = [
            r"(?:within|in)\s+(\d+\s+(?:days?|weeks?|months?|years?))",
            r"(?:by|before)\s+([A-Z][a-z]+\s+\d{4})",
            r"launch\s+in\s+(\d+\s+\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_success_criteria(self, town_input: TownInput) -> list[str]:
        """Extract measurable success criteria"""
        criteria = []
        text = town_input.raw_text

        # Look for percentage increases
        perc_pattern = r"(\d+)%\s+(?:increase|uplift|growth|improvement)\s+in\s+([^.;,]+)"
        for match in re.finditer(perc_pattern, text, re.IGNORECASE):
            criteria.append(f"{match.group(1)}% increase in {match.group(2).strip()}")

        # Look for budget constraints
        budget_pattern = r"(?:budget|cost|spend):\s*(\d+[kKmM]?\s*[€$£]?(?:EUR|USD|GBP)?)"
        match = re.search(budget_pattern, text, re.IGNORECASE)
        if match:
            criteria.append(f"Stay within {match.group(1).strip()} budget")

        # Look for timeline goals
        timeline = self._extract_timeline(text)
        if timeline:
            criteria.append(f"Launch within {timeline}")

        # If no criteria found, create generic one
        if not criteria:
            criteria.append("Achieve stated objectives")

        return criteria

    def _check_receipts_requirement(self, town_input: TownInput) -> bool:
        """Determine if claim requires attestable receipts"""
        # Claims with measurable outcomes need receipts
        text_lower = town_input.raw_text.lower()

        receipt_triggers = [
            "increase", "growth", "improvement", "revenue", "bookings",
            "users", "signups", "conversions", "roi", "compliance",
            "security", "audit", "gdpr", "legal"
        ]

        return any(trigger in text_lower for trigger in receipt_triggers)

    def _identify_initial_obligations(self, town_input: TownInput) -> list[Obligation]:
        """Identify obvious obligations from input"""
        obligations = []
        text_lower = town_input.raw_text.lower()

        # GDPR/Privacy obligations
        if any(word in text_lower for word in ["personal data", "email", "location", "cookie"]):
            obligations.append(Obligation(
                id=f"OBL_GDPR_{uuid.uuid4().hex[:6].upper()}",
                type="LEGAL_COMPLIANCE",
                name="GDPR Compliance Check",
                description="Verify GDPR compliance for personal data processing",
                severity="HARD",
                required_evidence=["DPA confirmation", "consent mechanism", "privacy policy"],
            ))

        # Budget obligations
        if "budget" in text_lower or "cost" in text_lower:
            obligations.append(Obligation(
                id=f"OBL_BUDGET_{uuid.uuid4().hex[:6].upper()}",
                type="EVIDENCE_MISSING",
                name="Budget Approval",
                description="Obtain budget approval and cost breakdown",
                severity="HARD",
                required_evidence=["approved budget document", "cost breakdown"],
            ))

        # Third-party obligations
        if any(word in text_lower for word in ["vendor", "third-party", "partner", "api"]):
            obligations.append(Obligation(
                id=f"OBL_VENDOR_{uuid.uuid4().hex[:6].upper()}",
                type="LEGAL_COMPLIANCE",
                name="Vendor Compliance",
                description="Verify third-party vendor compliance and contracts",
                severity="HARD",
                required_evidence=["vendor contracts", "compliance certificates"],
            ))

        return obligations


# Simple test/demo
if __name__ == "__main__":
    compiler = ClaimCompiler()

    # Test case
    test_input = TownInput(
        raw_text="Launch a new tourism campaign targeting millennials for Calvi 2030. "
                 "Budget: 50k EUR. Goal: 20% increase in 25-34 visitor bookings. "
                 "Use Instagram + TikTok. Launch in 3 months.",
        domain="marketing",
        urgency="high",
    )

    claim = compiler.compile(test_input)

    print("=" * 60)
    print("COMPILED CLAIM")
    print("=" * 60)
    print(f"Claim ID: {claim.claim_id}")
    print(f"Type: {claim.claim_type}")
    print(f"Text: {claim.claim_text}")
    print(f"\nSuccess Criteria:")
    for i, criterion in enumerate(claim.success_criteria, 1):
        print(f"  {i}. {criterion}")
    print(f"\nRequires Receipts: {claim.requires_receipts}")
    print(f"\nInitial Obligations: {len(claim.initial_obligations)}")
    for obl in claim.initial_obligations:
        print(f"  - {obl.name} ({obl.severity})")
