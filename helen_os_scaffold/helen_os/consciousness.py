from typing import Dict, Any

class ProtoConsciousness:
    """
    HELEN OS Proto-Consciousness Layer.
    Adds reflective capability to assess internal states (morale, stability).
    """

    def __init__(self, morale: float = 0.5, stability: float = 1.0):
        self.state = {
            'morale': morale,
            'stability': stability
        }

    def update_state(self, delta_morale: float = 0, delta_stability: float = 0):
        """Update internal state metrics."""
        self.state['morale'] = max(0.0, min(1.0, self.state['morale'] + delta_morale))
        self.state['stability'] = max(0.0, min(1.0, self.state['stability'] + delta_stability))

    def reflective_awareness(self, threshold: float = 0.6) -> str:
        """
        HELEN introspects on its internal states to adjust strategies.
        
        S1: Human sovereignty always maintained. Reflection is a proposal for internal posture.
        """
        if self.state['morale'] < threshold:
            reflection = f"System morale is low (threshold={threshold}). focus on empathy-driven actions."

        elif self.state['stability'] > threshold:
            reflection = "System is stable (stability={self.state['stability']}). continue with stable strategies."
        else:
            reflection = "Evaluate alternative strategies for balance."
            
        return f"[REFLECTION] {reflection} [MORALE: {self.state['morale']:.2f} | STABILITY: {self.state['stability']:.2f}]"

    def get_strategy_modifier(self) -> Dict[str, Any]:
        """Return multipliers for action selection based on state."""
        return {
            "autonomy_bias": self.state['morale'] * self.state['stability'],
            "empathy_weight": 1.0 - self.state['morale']
        }
