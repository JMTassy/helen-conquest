from typing import List, Dict, Any, Optional

class Claim:
    """
    HELEN OS Sovereign Claim.
    Represents an atomic piece of knowledge or intent within the Superteam.
    """
    def __init__(self, claim_id: str, claim_type: str, content: str, status: str = "proposed"):
        self.claim_id = claim_id
        self.claim_type = claim_type  # Fact, Concern, Synthesis, etc.
        self.content = content
        self.status = status  # proposed, traded, merged

    def __repr__(self):
        return f"Claim({self.claim_id}, {self.claim_type}, {self.content}, {self.status})"

class Egregor:
    """
    HELEN OS Collective Feedback Loop.
    Aggregates insights from multiple agents (Superteam).
    """
    def __init__(self):
        self.knowledge = []

    def add_knowledge(self, knowledge: str):
        """Add knowledge contribution from an agent."""
        self.knowledge.append(knowledge)

    def aggregate_knowledge(self) -> str:
        """Aggregate and synthesize collective knowledge using majority rule."""
        if not self.knowledge:
            return "No collective knowledge available."
        # Simple majority rule (most frequent item)
        consensus = max(set(self.knowledge), key=self.knowledge.count)
        return consensus

class Superteam:
    """
    HELEN OS Multi-Agent Coordination Layer.
    Facilitates claim trading and merging between agents.
    """
    def __init__(self):
        self.agents = {"researcher": [], "skeptic": [], "synthesizer": []}
        self.claims = []

    def add_claim(self, role: str, claim: Claim):
        """Agents contribute claims to the Superteam."""
        if role in self.agents:
            self.agents[role].append(claim)
            self.claims.append(claim)

    def trade_claim(self, claim_id: str, role_from: str, role_to: str) -> str:
        """Trade claims between agents if complementary."""
        claim_to_trade = None
        if role_from not in self.agents or role_to not in self.agents:
            return f"Invalid roles: {role_from} -> {role_to}"
            
        for claim in self.agents[role_from]:
            if claim.claim_id == claim_id and claim.status == "proposed":
                claim_to_trade = claim
                break
                
        if claim_to_trade:
            self.agents[role_from].remove(claim_to_trade)
            self.agents[role_to].append(claim_to_trade)
            claim_to_trade.status = "traded"
            return f"Claim {claim_id} traded from {role_from} to {role_to}"
        return f"Claim {claim_id} not found or already traded/merged."

    def merge_claims(self, claim_ids: List[str]) -> str:
        """Merge multiple proposed claims into a unified Synthesis claim."""
        claims_to_merge = []
        merged_content = []
        
        for cid in claim_ids:
            for claim in self.claims:
                if claim.claim_id == cid and claim.status != "merged":
                    claims_to_merge.append(claim)
                    merged_content.append(claim.content)
                    claim.status = "merged"
                    break

                    
        if len(claims_to_merge) > 1:
            merged_claim = Claim(
                claim_id=f"merged_{len(self.claims) + 1}",
                claim_type="Synthesis",
                content=" + ".join(merged_content)
            )
            self.claims.append(merged_claim)
            return f"Claims merged into new Synthesis: {merged_claim.content}"
        return "Insufficient valid claims to merge."
