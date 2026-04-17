"""ORACLE TOWN — K-Gate: Attestor Registry

Maintains the canonical list of authorized attestors.
Used by K0 gate to verify authority separation.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class AttestorRegistry:
    """
    Registry of authorized attestors.

    Used by TRI gate K0 check: only registered attestors may generate claims.

    Invariant: attestors list is immutable per evaluation run (K7 policy pinning).
    """
    attestors: List[str]

    def is_registered(self, attestor_id: str) -> bool:
        """Check if attestor is authorized."""
        return attestor_id in self.attestors
