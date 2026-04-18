"""
helen_os/kernel package

Core governance kernel modules:
  - governance_vm: GovernanceVM (sovereign state machine)
  - merkle: Merkle tree construction and verification
  - canonical_json: Deterministic canonical JSON serialization
"""

from .governance_vm import GovernanceVM, Receipt, DOMAIN_SEPARATOR

__all__ = ["GovernanceVM", "Receipt", "DOMAIN_SEPARATOR"]
