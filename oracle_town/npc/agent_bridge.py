#!/usr/bin/env python3
"""
OpenClaw Agent ↔ Oracle Town NPC Bridge

Wraps an OpenClaw Agent (or compatible agentic system) as an Oracle Town NPC.

Key Constraint:
- NPC can observe and propose claims
- NPC cannot make decisions (authority is reserved for Kernel)
- All NPC output flows through TRI gate

This module bridges autonomy (agents observing) with authority (Oracle Town deciding).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import json


@dataclass
class NPCObservation:
    """
    An observation made by an NPC (agent-as-proposer).

    This is NOT a decision. It is evidence for the Kernel to consider.
    """
    observation_id: str
    npc_role: str
    statement: str
    evidence: Dict[str, Any]
    confidence: float  # [0.0, 1.0]
    proposed_action: Optional[str] = None  # "flag", "approve", "reject", etc.
    reasoning: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_claim(self) -> Dict[str, Any]:
        """
        Convert observation to Oracle Town claim format.

        Returns a claim dict suitable for submission to TRI gate.
        """
        return {
            "claim_id": self.observation_id,
            "claim_type": "npc_observation",
            "npc_role": self.npc_role,
            "statement": self.statement,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "proposed_action": self.proposed_action,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
            "source": "npc_agent_bridge"
        }

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate observation before submission.

        Returns (is_valid, list_of_errors)
        """
        errors = []

        if not self.statement or len(self.statement) < 5:
            errors.append("statement must be at least 5 characters")

        if not (0.0 <= self.confidence <= 1.0):
            errors.append("confidence must be between 0.0 and 1.0")

        if self.proposed_action and self.proposed_action not in [
            "flag", "approve", "reject", "escalate", "monitor", "investigate"
        ]:
            errors.append(
                f"proposed_action '{self.proposed_action}' not recognized. "
                "Use: flag, approve, reject, escalate, monitor, investigate"
            )

        return (len(errors) == 0, errors)


class AgentBridge:
    """
    Wraps any agent-like system (OpenClaw, AutoGPT, etc.) as an Oracle Town NPC.

    The bridge intercepts agent output and converts it to claims rather than actions.
    """

    def __init__(self, agent: Any, role: str, npc_id: Optional[str] = None):
        """
        Initialize the bridge.

        Args:
            agent: Any object with process(stimulus) -> result method
            role: Human-readable role (e.g., "EmailAnalyzer", "VendorInspector")
            npc_id: Optional identifier; auto-generated if not provided
        """
        self.agent = agent
        self.role = role
        self.npc_id = npc_id or f"npc_{role.lower()}_{uuid.uuid4().hex[:8]}"
        self.observation_history: List[NPCObservation] = []
        self.claim_history: List[Dict[str, Any]] = []

    def observe(
        self,
        stimulus: Any,
        evidence: Optional[Dict[str, Any]] = None
    ) -> NPCObservation:
        """
        Agent observes something → generates an NPCObservation.

        This is the core bridge function. It:
        1. Calls agent.process(stimulus)
        2. Extracts result and confidence
        3. Wraps as NPCObservation
        4. Returns (does NOT execute immediately)

        Args:
            stimulus: Input to agent (email, vendor info, metric, etc.)
            evidence: Additional evidence dict to attach

        Returns:
            NPCObservation ready for submission to Oracle Town
        """
        # Call the wrapped agent
        result = self.agent.process(stimulus)

        # Extract relevant fields
        statement = self._extract_statement(result)
        confidence = self._extract_confidence(result)
        proposed_action = self._extract_action(result)
        reasoning = self._extract_reasoning(result)

        # Build evidence dict
        evidence = evidence or {}
        evidence["stimulus"] = self._serialize(stimulus)
        evidence["agent_result"] = self._serialize(result)

        # Create observation
        observation = NPCObservation(
            observation_id=f"obs_{self.npc_id}_{uuid.uuid4().hex[:8]}",
            npc_role=self.role,
            statement=statement,
            evidence=evidence,
            confidence=confidence,
            proposed_action=proposed_action,
            reasoning=reasoning
        )

        # Validate before returning
        is_valid, errors = observation.validate()
        if not is_valid:
            raise ValueError(f"Invalid observation: {errors}")

        # Record in history
        self.observation_history.append(observation)

        return observation

    def submit_observation(
        self,
        observation: NPCObservation,
        submit_fn: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Submit an observation to Oracle Town.

        If submit_fn is provided, uses it. Otherwise, returns claim dict.

        Args:
            observation: NPCObservation to submit
            submit_fn: Optional callable that submits to Oracle Town kernel

        Returns:
            Receipt dict from Oracle Town, or claim dict if no submit_fn
        """
        claim = observation.to_claim()
        self.claim_history.append(claim)

        if submit_fn:
            # Submit to Oracle Town kernel
            return submit_fn(claim)
        else:
            # Return claim for external submission
            return claim

    def read_memory(self, query: str) -> Any:
        """
        Agent can read from Oracle Town memory (unrestricted).

        Args:
            query: Search query (semantic or structured)

        Returns:
            Memory search results
        """
        # This would be wired to oracle_town/memory/search.py
        # For now, placeholder
        if hasattr(self.agent, 'memory'):
            return self.agent.memory.search(query)
        return None

    def get_observation_history(self) -> List[NPCObservation]:
        """
        Get all observations made by this NPC.
        """
        return self.observation_history.copy()

    def get_claim_history(self) -> List[Dict[str, Any]]:
        """
        Get all claims submitted by this NPC.
        """
        return self.claim_history.copy()

    def reset_history(self):
        """
        Clear observation and claim history (for testing).
        """
        self.observation_history.clear()
        self.claim_history.clear()

    # --- Private helper methods ---

    def _extract_statement(self, result: Any) -> str:
        """Extract the main statement from agent result."""
        if isinstance(result, dict) and "statement" in result:
            return result["statement"]
        elif isinstance(result, str):
            return result
        elif hasattr(result, 'statement'):
            return result.statement
        else:
            return str(result)

    def _extract_confidence(self, result: Any) -> float:
        """Extract confidence score from agent result."""
        if isinstance(result, dict) and "confidence" in result:
            conf = result["confidence"]
        elif hasattr(result, 'confidence'):
            conf = result.confidence
        else:
            conf = 0.5

        # Normalize to [0, 1]
        if isinstance(conf, (int, float)):
            return max(0.0, min(1.0, float(conf)))
        return 0.5

    def _extract_action(self, result: Any) -> Optional[str]:
        """Extract proposed action from agent result."""
        if isinstance(result, dict) and "action" in result:
            return result["action"]
        elif isinstance(result, dict) and "proposed_action" in result:
            return result["proposed_action"]
        elif hasattr(result, 'action'):
            return result.action
        return None

    def _extract_reasoning(self, result: Any) -> Optional[str]:
        """Extract reasoning/explanation from agent result."""
        if isinstance(result, dict) and "reasoning" in result:
            return result["reasoning"]
        elif isinstance(result, dict) and "explanation" in result:
            return result["explanation"]
        elif hasattr(result, 'reasoning'):
            return result.reasoning
        return None

    def _serialize(self, obj: Any) -> Any:
        """
        Serialize an object to JSON-safe format for evidence.
        """
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, (dict, list)):
            return obj
        elif hasattr(obj, '__dict__'):
            return self._serialize(obj.__dict__)
        else:
            try:
                return json.loads(json.dumps(obj, default=str))
            except:
                return str(obj)


class NPCRegistry:
    """
    Registry of all NPCs (agent bridges) in the system.
    """

    def __init__(self):
        self.npcs: Dict[str, AgentBridge] = {}

    def register(self, bridge: AgentBridge):
        """Register an NPC (agent bridge)."""
        self.npcs[bridge.npc_id] = bridge

    def get(self, npc_id: str) -> Optional[AgentBridge]:
        """Get an NPC by ID."""
        return self.npcs.get(npc_id)

    def get_by_role(self, role: str) -> List[AgentBridge]:
        """Get all NPCs with a given role."""
        return [npc for npc in self.npcs.values() if npc.role == role]

    def list_all(self) -> List[AgentBridge]:
        """Get all registered NPCs."""
        return list(self.npcs.values())

    def unregister(self, npc_id: str):
        """Unregister an NPC."""
        self.npcs.pop(npc_id, None)


# Global registry
_global_registry = NPCRegistry()


def register_npc(bridge: AgentBridge):
    """Register an NPC in the global registry."""
    _global_registry.register(bridge)


def get_npc(npc_id: str) -> Optional[AgentBridge]:
    """Get an NPC from the global registry."""
    return _global_registry.get(npc_id)


def list_npcs() -> List[AgentBridge]:
    """List all registered NPCs."""
    return _global_registry.list_all()


# --- Testing ---

if __name__ == "__main__":

    # Test 1: Create a mock agent
    class MockAgent:
        def __init__(self, name):
            self.name = name

        def process(self, stimulus):
            return {
                "statement": f"Analyzed {stimulus}",
                "confidence": 0.85,
                "action": "flag" if "suspicious" in str(stimulus).lower() else None,
                "reasoning": "Based on pattern matching"
            }

    # Test 2: Wrap as NPC
    agent = MockAgent("EmailAnalyzer")
    bridge = AgentBridge(agent, role="EmailAnalyzer")
    register_npc(bridge)

    # Test 3: Observe
    obs = bridge.observe({"email": "subject: 'suspicious link'"})
    print(f"✓ Observation created: {obs.observation_id}")
    print(f"  Statement: {obs.statement}")
    print(f"  Confidence: {obs.confidence}")
    print(f"  Proposed action: {obs.proposed_action}")

    # Test 4: Convert to claim
    claim = obs.to_claim()
    print(f"✓ Claim generated: {json.dumps(claim, indent=2)}")

    # Test 5: Registry
    print(f"✓ NPC registered: {bridge.npc_id}")
    print(f"  All NPCs: {[npc.role for npc in list_npcs()]}")

    print("\n✅ Agent bridge tests passed")
