#!/usr/bin/env python3
"""
NPC Integration with Governance

NPC claims enter the system through normal channels:
  NPC Claim → Doctrine Enforcer → TRI Gate → Your Decision → Override Ledger

NPCs have zero authority.
Their claims are proposals, not directives.
"""

import json
from datetime import datetime

class NPCClaimProcessor:
    """Process NPC claims through governance."""
    
    def __init__(self):
        self.processed_claims = []
    
    def submit_npc_claim(self, npc_claim):
        """
        Submit an NPC claim for governance review.
        
        Flow:
        1. Claim arrives (from NPC)
        2. Formatted for human review
        3. You decide: accept, reject, or investigate
        4. Decision logged (if approved)
        """
        
        # Format for human review
        formatted = self._format_for_review(npc_claim)
        
        # Log submission
        self.processed_claims.append({
            "claim_id": npc_claim.claim_id,
            "npc_name": npc_claim.npc_name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "AWAITING_HUMAN_REVIEW"
        })
        
        return formatted
    
    def _format_for_review(self, claim):
        """Format NPC claim for human decision-making."""
        
        msg = "\n" + "="*70 + "\n"
        msg += f"NPC CLAIM AWAITING REVIEW\n"
        msg += "="*70 + "\n\n"
        msg += f"From: {claim.npc_name}\n"
        msg += f"Type: {claim.npc_type.value}\n"
        msg += f"Severity: {claim.severity}\n\n"
        msg += f"OBSERVATION:\n{claim.observation}\n\n"
        msg += f"EVIDENCE:\n"
        for e in claim.evidence:
            msg += f"  • {e}\n"
        msg += f"\nPROPOSED ACTION:\n{claim.proposed_action}\n\n"
        msg += f"RATIONALE:\n{claim.rationale}\n\n"
        msg += f"Requires your decision: {claim.requires_decision}\n\n"
        msg += "="*70 + "\n"
        msg += "DECISION OPTIONS:\n"
        msg += "  1. ACCEPT — Act on this proposal\n"
        msg += "  2. DEFER — Gather more data\n"
        msg += "  3. REJECT — Disagree with proposal\n"
        msg += "="*70 + "\n"
        
        return msg

# Example
if __name__ == "__main__":
    processor = NPCClaimProcessor()
    
    # Simulate an NPC claim
    from enum import Enum
    
    class NPCType(Enum):
        ACCURACY_WATCHER = "accuracy_watcher"
    
    class MockClaim:
        def __init__(self):
            self.claim_id = "NPC_AccuracyWatcher_20260131_001"
            self.npc_name = "AccuracyWatcher"
            self.npc_type = NPCType.ACCURACY_WATCHER
            self.observation = "Recent REJECT verdicts have prevented 10 bad decisions (~€500k prevented)"
            self.evidence = [
                "Last 17 verdicts: 7 ACCEPT, 10 REJECT",
                "Rejection rate: 59%",
                "Each REJECT prevents ~€50k in wasted commitment"
            ]
            self.proposed_action = "Continue current standards."
            self.rationale = "Your rejection discipline is working. System is appropriately selective."
            self.severity = "low"
            self.requires_decision = False
    
    claim = MockClaim()
    formatted = processor.submit_npc_claim(claim)
    print(formatted)
