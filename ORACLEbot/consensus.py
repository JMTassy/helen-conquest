"""
ORACLE BOT - Enhanced Consensus Algorithm v2
=============================================
Combines epistemic rigor with emergent collaboration patterns.

Key upgrades from basic voting:
1. WEIGHTED CONFIDENCE voting (not just approve/reject)
2. ADVERSARIAL TENSION as a feature, not a bug
3. EMERGENT SYNTHESIS through structured disagreement
4. BRUTAL HONESTY protocol (WILLIAM-style challenge)
5. KILL-SWITCH integration at consensus level

Inspired by:
- Ant colony optimization (pheromone trails → confidence trails)
- Market dynamics (price discovery → truth discovery)
- Neural networks (weighted connections → weighted votes)
- Swarm intelligence (local rules → global coherence)

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                    CONSENSUS ORCHESTRATOR                        │
│            (Not a voter — a TENSION MANAGER)                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
   DECOMPOSER    EXPLORER      CRITIC       BUILDER
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             ▼
                      INTEGRATOR
                    (Final arbiter)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# VOTE TYPES (beyond simple approve/reject)
# ═══════════════════════════════════════════════════════════════════════════════

class VoteType(Enum):
    STRONG_APPROVE = "STRONG_APPROVE"      # High confidence, no objections
    APPROVE = "APPROVE"                     # Acceptable, minor concerns
    CONDITIONAL = "CONDITIONAL"             # Approve IF specific conditions met
    ABSTAIN = "ABSTAIN"                     # Insufficient info to judge
    OBJECT = "OBJECT"                       # Specific objection (repairable)
    STRONG_OBJECT = "STRONG_OBJECT"         # Fundamental flaw (may be fatal)
    KILL = "KILL"                           # Trigger kill-switch, abort


class ConsensusStatus(Enum):
    UNANIMOUS = "UNANIMOUS"                 # All strong approve
    CONSENSUS = "CONSENSUS"                 # Sufficient agreement
    CONDITIONAL = "CONDITIONAL"             # Agreement with conditions
    CONTESTED = "CONTESTED"                 # Unresolved disagreement
    DEADLOCK = "DEADLOCK"                   # Irreconcilable positions
    KILLED = "KILLED"                       # Kill-switch triggered


# ═══════════════════════════════════════════════════════════════════════════════
# VOTE STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Vote:
    """Enhanced vote with confidence weighting and justification."""
    agent: str
    vote_type: VoteType
    confidence: float              # 0.0 - 1.0
    tier_assessment: str           # "I", "II", "III"
    
    # Justification (required for all non-approve votes)
    primary_concern: Optional[str] = None
    hidden_assumptions: List[str] = field(default_factory=list)
    edge_cases: List[str] = field(default_factory=list)
    
    # Conditions (for CONDITIONAL votes)
    conditions: List[str] = field(default_factory=list)
    
    # Kill-switch (for KILL votes)
    kill_switch_triggered: Optional[str] = None
    
    # Meta
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted vote score."""
        base_scores = {
            VoteType.STRONG_APPROVE: 1.0,
            VoteType.APPROVE: 0.75,
            VoteType.CONDITIONAL: 0.5,
            VoteType.ABSTAIN: 0.0,
            VoteType.OBJECT: -0.5,
            VoteType.STRONG_OBJECT: -0.75,
            VoteType.KILL: -1.0
        }
        return base_scores[self.vote_type] * self.confidence


@dataclass
class Proposal:
    """Proposal being voted on."""
    id: str
    content: Dict[str, Any]
    proposer: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    iteration: int = 1


@dataclass
class ConsensusResult:
    """Result of consensus process."""
    proposal_id: str
    status: ConsensusStatus
    votes: List[Vote]
    weighted_score: float
    conditions_required: List[str]
    objections_unresolved: List[str]
    kill_switches: List[str]
    recommendation: str
    next_action: str


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENSUS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ConsensusEngine:
    """
    Enhanced consensus algorithm with emergent behavior support.
    
    Key principles:
    1. Disagreement is INFORMATION, not failure
    2. Confidence weighting prevents tyranny of the uncertain
    3. Kill-switches provide hard boundaries
    4. Conditions create actionable paths forward
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self.default_config()
        self.history: List[ConsensusResult] = []
        
    @staticmethod
    def default_config() -> Dict:
        return {
            # Thresholds
            "unanimous_threshold": 0.95,      # Weighted score for unanimous
            "consensus_threshold": 0.60,      # Weighted score for consensus
            "conditional_threshold": 0.40,    # Weighted score for conditional
            "deadlock_threshold": -0.30,      # Below this = deadlock
            
            # Weights by agent (can be adjusted based on domain)
            "agent_weights": {
                "DECOMPOSER": 1.0,
                "EXPLORER": 0.9,
                "CRITIC": 1.2,       # CRITIC gets extra weight (adversarial role)
                "BUILDER": 1.0,
                "INTEGRATOR": 1.1    # INTEGRATOR breaks ties
            },
            
            # Kill-switch behavior
            "kill_on_any_kill_vote": True,
            "kill_on_critic_strong_object": False,
            
            # Iteration limits
            "max_iterations": 3,
            "require_condition_resolution": True,
        }
    
    def collect_votes(self, proposal: Proposal, votes: List[Vote]) -> ConsensusResult:
        """
        Process votes and determine consensus status.
        
        Algorithm:
        1. Check for kill-switches (immediate termination)
        2. Calculate weighted scores
        3. Identify conditions and objections
        4. Determine consensus status
        5. Generate recommendation
        """
        
        # 1. Check kill-switches
        kill_switches = [v.kill_switch_triggered for v in votes 
                        if v.vote_type == VoteType.KILL and v.kill_switch_triggered]
        
        if kill_switches and self.config["kill_on_any_kill_vote"]:
            return ConsensusResult(
                proposal_id=proposal.id,
                status=ConsensusStatus.KILLED,
                votes=votes,
                weighted_score=-1.0,
                conditions_required=[],
                objections_unresolved=[],
                kill_switches=kill_switches,
                recommendation="ABORT: Kill-switch triggered",
                next_action=f"Address kill-switch: {kill_switches[0]}"
            )
        
        # 2. Calculate weighted scores
        total_weight = 0.0
        weighted_sum = 0.0
        
        for vote in votes:
            agent_weight = self.config["agent_weights"].get(vote.agent, 1.0)
            total_weight += agent_weight
            weighted_sum += vote.weighted_score * agent_weight
        
        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # 3. Collect conditions and objections
        conditions = []
        objections = []
        
        for vote in votes:
            if vote.vote_type == VoteType.CONDITIONAL:
                conditions.extend(vote.conditions)
            if vote.vote_type in [VoteType.OBJECT, VoteType.STRONG_OBJECT]:
                if vote.primary_concern:
                    objections.append(f"{vote.agent}: {vote.primary_concern}")
        
        # 4. Determine status
        if weighted_score >= self.config["unanimous_threshold"]:
            status = ConsensusStatus.UNANIMOUS
        elif weighted_score >= self.config["consensus_threshold"]:
            status = ConsensusStatus.CONSENSUS
        elif weighted_score >= self.config["conditional_threshold"]:
            status = ConsensusStatus.CONDITIONAL if conditions else ConsensusStatus.CONTESTED
        elif weighted_score >= self.config["deadlock_threshold"]:
            status = ConsensusStatus.CONTESTED
        else:
            status = ConsensusStatus.DEADLOCK
        
        # 5. Generate recommendation
        recommendation, next_action = self._generate_recommendation(
            status, weighted_score, conditions, objections, proposal.iteration
        )
        
        result = ConsensusResult(
            proposal_id=proposal.id,
            status=status,
            votes=votes,
            weighted_score=weighted_score,
            conditions_required=conditions,
            objections_unresolved=objections,
            kill_switches=kill_switches,
            recommendation=recommendation,
            next_action=next_action
        )
        
        self.history.append(result)
        return result
    
    def _generate_recommendation(
        self, 
        status: ConsensusStatus,
        score: float,
        conditions: List[str],
        objections: List[str],
        iteration: int
    ) -> Tuple[str, str]:
        """Generate actionable recommendation based on consensus state."""
        
        if status == ConsensusStatus.UNANIMOUS:
            return (
                "PROCEED: Unanimous agreement achieved",
                "Execute proposal as specified"
            )
        
        if status == ConsensusStatus.CONSENSUS:
            if objections:
                return (
                    f"PROCEED WITH AWARENESS: Consensus ({score:.2f}) with {len(objections)} minor objections",
                    f"Execute but monitor: {objections[0]}"
                )
            return (
                f"PROCEED: Consensus achieved ({score:.2f})",
                "Execute proposal"
            )
        
        if status == ConsensusStatus.CONDITIONAL:
            return (
                f"CONDITIONAL PROCEED: Score {score:.2f}, {len(conditions)} conditions required",
                f"Resolve conditions first: {conditions[0] if conditions else 'N/A'}"
            )
        
        if status == ConsensusStatus.CONTESTED:
            if iteration < self.config["max_iterations"]:
                return (
                    f"ITERATE: Contested ({score:.2f}), iteration {iteration}/{self.config['max_iterations']}",
                    f"Address objection: {objections[0] if objections else 'Clarify positions'}"
                )
            return (
                f"ESCALATE: Max iterations reached, still contested ({score:.2f})",
                "Escalate to human decision or break into sub-proposals"
            )
        
        if status == ConsensusStatus.DEADLOCK:
            return (
                f"DEADLOCK: Irreconcilable positions ({score:.2f})",
                "Fundamental disagreement - requires reformulation or external input"
            )
        
        return ("UNKNOWN", "Review manually")


# ═══════════════════════════════════════════════════════════════════════════════
# BRUTAL HONESTY PROTOCOL (WILLIAM Integration)
# ═══════════════════════════════════════════════════════════════════════════════

class BrutalHonestyProtocol:
    """
    WILLIAM-style challenge layer for the consensus process.
    
    Forces agents to:
    1. Challenge all assumptions
    2. Expose hidden flaws
    3. Call out weak reasoning
    4. Push back on consensus-seeking behavior
    """
    
    CHALLENGE_PROMPTS = {
        "assumption_challenge": """
BRUTAL HONESTY CHECK:
- What assumptions are you making that you haven't stated?
- What would a hostile critic say about this?
- Where are you being lazy or taking shortcuts?
- What's the inconvenient truth you're avoiding?
""",
        
        "consensus_challenge": """
FALSE CONSENSUS CHECK:
- Are you agreeing because it's true, or because it's comfortable?
- Are you avoiding conflict at the expense of accuracy?
- What would you say if you weren't worried about team harmony?
- Is this "consensus" actually just groupthink?
""",
        
        "confidence_challenge": """
OVERCONFIDENCE CHECK:
- How confident are you REALLY? (Not how confident you want to appear)
- What's the probability you're wrong? Be honest.
- What evidence would change your mind?
- Are you stating opinion as fact?
""",
        
        "action_challenge": """
ACTION BIAS CHECK:
- Are you recommending action because it's needed, or because inaction feels uncomfortable?
- What happens if we do nothing?
- Is this the BEST use of resources, or just A use?
- Are you solving the real problem or a proxy?
"""
    }
    
    @classmethod
    def challenge_vote(cls, vote: Vote) -> List[str]:
        """Generate challenges for a vote."""
        challenges = []
        
        # High confidence on non-Tier-I claims
        if vote.confidence > 0.8 and vote.tier_assessment != "I":
            challenges.append(
                f"⚠️ High confidence ({vote.confidence}) on Tier {vote.tier_assessment} claim. "
                "What makes you so certain about something that isn't proven?"
            )
        
        # Approve without concerns
        if vote.vote_type in [VoteType.STRONG_APPROVE, VoteType.APPROVE]:
            if not vote.hidden_assumptions and not vote.edge_cases:
                challenges.append(
                    "⚠️ Approval with no concerns noted. "
                    "Are you really saying there's NOTHING that could go wrong?"
                )
        
        # Abstain without justification
        if vote.vote_type == VoteType.ABSTAIN:
            challenges.append(
                "⚠️ Abstention. Is this genuine uncertainty, or avoidance of taking a position?"
            )
        
        # Object without specifics
        if vote.vote_type in [VoteType.OBJECT, VoteType.STRONG_OBJECT]:
            if not vote.primary_concern:
                challenges.append(
                    "⚠️ Objection without specific concern. What exactly is the problem?"
                )
        
        return challenges
    
    @classmethod
    def challenge_consensus(cls, result: ConsensusResult) -> List[str]:
        """Generate challenges for a consensus result."""
        challenges = []
        
        # Unanimous with no dissent
        if result.status == ConsensusStatus.UNANIMOUS:
            challenges.append(
                "⚠️ UNANIMOUS agreement is suspicious. "
                "Did everyone actually think critically, or is this groupthink?"
            )
        
        # Quick consensus
        if result.weighted_score > 0.8 and len(result.objections_unresolved) == 0:
            challenges.append(
                "⚠️ High agreement with no objections. "
                "Was the CRITIC doing their job? Where's the adversarial pressure?"
            )
        
        # Conditions ignored
        if result.status == ConsensusStatus.CONSENSUS and result.conditions_required:
            challenges.append(
                f"⚠️ Consensus declared but {len(result.conditions_required)} conditions unaddressed. "
                "Are we papering over disagreement?"
            )
        
        return challenges


# ═══════════════════════════════════════════════════════════════════════════════
# EMERGENT SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════════

class EmergentSynthesis:
    """
    Synthesize emergent insights from multi-agent disagreement.
    
    Key insight: Disagreement contains INFORMATION.
    When agents disagree, the pattern of disagreement often reveals
    something that none of them individually saw.
    """
    
    @classmethod
    def analyze_disagreement(cls, votes: List[Vote]) -> Dict[str, Any]:
        """Extract emergent insights from vote patterns."""
        
        # Group votes by type
        vote_groups = {}
        for vote in votes:
            key = vote.vote_type.value
            if key not in vote_groups:
                vote_groups[key] = []
            vote_groups[key].append(vote)
        
        # Identify tension patterns
        tensions = []
        
        # Pattern 1: High-confidence disagreement
        approvers = [v for v in votes if v.vote_type in [VoteType.STRONG_APPROVE, VoteType.APPROVE]]
        objectors = [v for v in votes if v.vote_type in [VoteType.OBJECT, VoteType.STRONG_OBJECT]]
        
        if approvers and objectors:
            avg_approve_confidence = sum(v.confidence for v in approvers) / len(approvers)
            avg_object_confidence = sum(v.confidence for v in objectors) / len(objectors)
            
            if avg_approve_confidence > 0.7 and avg_object_confidence > 0.7:
                tensions.append({
                    "type": "HIGH_CONFIDENCE_SPLIT",
                    "insight": "Both sides are confident. This suggests fundamentally different models, not missing information.",
                    "recommendation": "Don't seek more data—identify the underlying model difference."
                })
        
        # Pattern 2: Tier disagreement
        tier_votes = {}
        for vote in votes:
            tier = vote.tier_assessment
            if tier not in tier_votes:
                tier_votes[tier] = []
            tier_votes[tier].append(vote)
        
        if len(tier_votes) > 1:
            tensions.append({
                "type": "TIER_DISAGREEMENT",
                "insight": f"Agents disagree on epistemic status: {list(tier_votes.keys())}",
                "recommendation": "Clarify what evidence would upgrade/downgrade the tier."
            })
        
        # Pattern 3: Hidden assumption overlap
        all_assumptions = []
        for vote in votes:
            all_assumptions.extend(vote.hidden_assumptions)
        
        # Find common assumptions across disagreeing agents
        if all_assumptions:
            from collections import Counter
            assumption_counts = Counter(all_assumptions)
            common = [a for a, c in assumption_counts.items() if c > 1]
            
            if common:
                tensions.append({
                    "type": "SHARED_BLIND_SPOT",
                    "insight": f"Multiple agents flagged same assumption: {common[0]}",
                    "recommendation": "This assumption is likely critical. Address it first."
                })
        
        return {
            "vote_distribution": {k: len(v) for k, v in vote_groups.items()},
            "tensions": tensions,
            "emergent_insight": cls._synthesize_insight(tensions)
        }
    
    @classmethod
    def _synthesize_insight(cls, tensions: List[Dict]) -> str:
        """Generate emergent insight from tension patterns."""
        if not tensions:
            return "No emergent patterns detected. Agreement may be genuine or superficial."
        
        if any(t["type"] == "HIGH_CONFIDENCE_SPLIT" for t in tensions):
            return ("🔥 CRITICAL: High-confidence split detected. "
                   "This is not a data problem—it's a MODEL problem. "
                   "Agents have fundamentally different frameworks.")
        
        if any(t["type"] == "SHARED_BLIND_SPOT" for t in tensions):
            return ("🎯 OPPORTUNITY: Shared blind spot identified. "
                   "All agents missed the same thing. "
                   "Resolving this may dissolve the disagreement.")
        
        return f"⚡ {len(tensions)} tension patterns detected. Review individually."


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATED CONSENSUS ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class OracleConsensusOrchestrator:
    """
    Full consensus orchestrator integrating:
    - Weighted voting
    - Brutal honesty challenges
    - Emergent synthesis
    - Kill-switch protection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.engine = ConsensusEngine(config)
        self.brutal_honesty = BrutalHonestyProtocol()
        self.emergence = EmergentSynthesis()
        
    def run_consensus(
        self, 
        proposal: Proposal, 
        votes: List[Vote],
        enable_brutal_honesty: bool = True
    ) -> Dict[str, Any]:
        """
        Run full consensus process with all enhancements.
        
        Returns comprehensive result with:
        - Basic consensus result
        - Brutal honesty challenges
        - Emergent insights
        - Final recommendation
        """
        
        # 1. Basic consensus
        result = self.engine.collect_votes(proposal, votes)
        
        # 2. Brutal honesty challenges
        vote_challenges = []
        if enable_brutal_honesty:
            for vote in votes:
                challenges = self.brutal_honesty.challenge_vote(vote)
                if challenges:
                    vote_challenges.append({
                        "agent": vote.agent,
                        "challenges": challenges
                    })
            
            consensus_challenges = self.brutal_honesty.challenge_consensus(result)
        else:
            consensus_challenges = []
        
        # 3. Emergent synthesis
        emergence_analysis = self.emergence.analyze_disagreement(votes)
        
        # 4. Final integrated recommendation
        final_recommendation = self._integrate_recommendation(
            result, consensus_challenges, emergence_analysis
        )
        
        return {
            "consensus_result": {
                "proposal_id": result.proposal_id,
                "status": result.status.value,
                "weighted_score": result.weighted_score,
                "conditions_required": result.conditions_required,
                "objections_unresolved": result.objections_unresolved,
                "kill_switches": result.kill_switches,
                "base_recommendation": result.recommendation,
                "base_next_action": result.next_action
            },
            "brutal_honesty": {
                "vote_challenges": vote_challenges,
                "consensus_challenges": consensus_challenges
            },
            "emergence": emergence_analysis,
            "final_recommendation": final_recommendation
        }
    
    def _integrate_recommendation(
        self,
        result: ConsensusResult,
        challenges: List[str],
        emergence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate all analyses into final recommendation."""
        
        # Base confidence from consensus
        base_confidence = (result.weighted_score + 1) / 2  # Normalize to 0-1
        
        # Adjust for challenges
        challenge_penalty = len(challenges) * 0.05
        
        # Adjust for emergent tensions
        tension_penalty = len(emergence.get("tensions", [])) * 0.1
        
        adjusted_confidence = max(0, base_confidence - challenge_penalty - tension_penalty)
        
        # Determine final action
        if result.status == ConsensusStatus.KILLED:
            action = "ABORT"
            reason = f"Kill-switch: {result.kill_switches[0] if result.kill_switches else 'Unknown'}"
        elif adjusted_confidence >= 0.7 and not challenges:
            action = "EXECUTE"
            reason = "Strong consensus with no significant challenges"
        elif adjusted_confidence >= 0.5:
            action = "EXECUTE_WITH_MONITORING"
            reason = "Moderate consensus - proceed but monitor closely"
        elif emergence.get("tensions"):
            action = "RESOLVE_TENSIONS"
            reason = f"Emergent insight: {emergence.get('emergent_insight', 'N/A')}"
        else:
            action = "ITERATE"
            reason = "Insufficient consensus - requires revision"
        
        return {
            "action": action,
            "reason": reason,
            "adjusted_confidence": adjusted_confidence,
            "requires_human_review": adjusted_confidence < 0.5 or bool(challenges),
            "priority_issue": (
                emergence.get("emergent_insight") or 
                (challenges[0] if challenges else None) or
                (result.objections_unresolved[0] if result.objections_unresolved else None)
            )
        }


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION WITH ORACLE BOT
# ═══════════════════════════════════════════════════════════════════════════════

def create_vote_from_agent_output(agent_name: str, output: str) -> Vote:
    """
    Parse agent output and create a Vote object.
    
    This is a simplified parser - in production, would use
    structured output from the agent.
    """
    import re
    
    # Extract confidence
    confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', output, re.IGNORECASE)
    confidence = float(confidence_match.group(1)) if confidence_match else 0.5
    
    # Extract tier
    tier_match = re.search(r'tier[:\s]+([I]+)', output, re.IGNORECASE)
    tier = tier_match.group(1) if tier_match else "II"
    
    # Determine vote type based on keywords
    output_lower = output.lower()
    
    if "kill" in output_lower or "abort" in output_lower:
        vote_type = VoteType.KILL
    elif "strong object" in output_lower or "fatal" in output_lower:
        vote_type = VoteType.STRONG_OBJECT
    elif "object" in output_lower or "reject" in output_lower:
        vote_type = VoteType.OBJECT
    elif "conditional" in output_lower:
        vote_type = VoteType.CONDITIONAL
    elif "strong approve" in output_lower or "robust" in output_lower:
        vote_type = VoteType.STRONG_APPROVE
    elif "approve" in output_lower or "accept" in output_lower:
        vote_type = VoteType.APPROVE
    else:
        vote_type = VoteType.ABSTAIN
    
    # Extract concerns
    concerns = re.findall(r'concern[:\s]+(.+?)(?:\n|$)', output, re.IGNORECASE)
    assumptions = re.findall(r'assumption[:\s]+(.+?)(?:\n|$)', output, re.IGNORECASE)
    
    return Vote(
        agent=agent_name,
        vote_type=vote_type,
        confidence=confidence,
        tier_assessment=tier,
        primary_concern=concerns[0] if concerns else None,
        hidden_assumptions=assumptions
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("ORACLE BOT - Enhanced Consensus Algorithm v2")
    print("=" * 50)
    
    # Create test votes
    votes = [
        Vote(
            agent="DECOMPOSER",
            vote_type=VoteType.APPROVE,
            confidence=0.85,
            tier_assessment="I",
            hidden_assumptions=["User requirements are complete"]
        ),
        Vote(
            agent="EXPLORER",
            vote_type=VoteType.STRONG_APPROVE,
            confidence=0.9,
            tier_assessment="II",
            hidden_assumptions=["Market conditions stable"]
        ),
        Vote(
            agent="CRITIC",
            vote_type=VoteType.OBJECT,
            confidence=0.75,
            tier_assessment="II",
            primary_concern="Scalability not addressed",
            hidden_assumptions=["User requirements are complete"],
            edge_cases=["High load scenario"]
        ),
        Vote(
            agent="BUILDER",
            vote_type=VoteType.CONDITIONAL,
            confidence=0.7,
            tier_assessment="II",
            conditions=["Must add load testing", "Need database schema review"]
        ),
        Vote(
            agent="INTEGRATOR",
            vote_type=VoteType.APPROVE,
            confidence=0.8,
            tier_assessment="II"
        )
    ]
    
    # Create proposal
    proposal = Proposal(
        id="PROP_001",
        content={"description": "Implement caching layer"},
        proposer="EXPLORER"
    )
    
    # Run consensus
    orchestrator = OracleConsensusOrchestrator()
    result = orchestrator.run_consensus(proposal, votes)
    
    print("\n📊 CONSENSUS RESULT:")
    print(json.dumps(result, indent=2, default=str))
