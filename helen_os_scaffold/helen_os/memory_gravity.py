import time
import math
from typing import List, Dict, Any, Optional

class MemoryGravity:
    """
    HELEN OS Memory Gravity.
    Governs the weight of past decisions and their influence on future actions.
    Uses exponential decay: Gravity(t) = G0 * e^(-lambda * t)
    """

    def __init__(self, max_age: int = 3600, base_gravity: float = 0.8):
        self.max_age = max_age  # in seconds (time window for decay)
        self.base_gravity = base_gravity
        self.history = []

    def add_decision(self, decision: Any, timestamp: Optional[float] = None) -> None:
        """Add a new decision to memory with a timestamp."""
        entry = {
            'decision': decision,
            'timestamp': timestamp or time.time()
        }
        self.history.append(entry)
        # Self-pruning: remove decisions older than 2x max_age
        current_time = time.time()
        self.history = [d for d in self.history if current_time - d['timestamp'] <= self.max_age * 2]

    def get_gravity(self) -> float:
        """Calculate total gravity based on time-decayed influence of past decisions."""
        current_time = time.time()
        total_gravity = 0.0
        for entry in self.history:
            time_diff = current_time - entry['timestamp']
            if time_diff <= self.max_age:
                # Exponential decay: younger decisions weigh more
                decay_factor = math.exp(-time_diff / self.max_age)
                total_gravity += self.base_gravity * decay_factor
        return total_gravity

    def adjust_gravity(self, system_state: str = "Stable"):
        """
        Dynamic recalibration of memory gravity based on system state.
        States: Stable, Rising, Critical
        """
        current_gravity = self.get_gravity()
        
        # Calibration multipliers
        if system_state == "Critical":
            # In critical state, reduce gravity to allow more radical adaptation (bias breaking)
            self.base_gravity *= 0.5
        elif system_state == "Rising":
            self.base_gravity *= 1.1
        else:
            # Re-center toward baseline
            target = 0.8
            self.base_gravity = self.base_gravity * 0.9 + target * 0.1

        # Clamping
        self.base_gravity = max(0.1, min(self.base_gravity, 1.0))

    def reset(self):
        """Purge all memory gravity (Emergency override)."""
        self.history = []
        self.base_gravity = 0.8
