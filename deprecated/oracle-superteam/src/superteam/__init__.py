"""
superteam package

MODE 2: Improvement engine for WUL-ORACLE governance.

Provides:
- ImprovementProposal: Data structure for improvement suggestions
- SuperteamImprover: Engine for analyzing NO_SHIP and proposing fixes
- propose_improvements: Convenience function for analysis
- apply_improvements: Convenience function for applying proposals
"""

from .improve import (
    ImprovementProposal,
    SuperteamImprover,
    propose_improvements,
    apply_improvements
)

__all__ = [
    "ImprovementProposal",
    "SuperteamImprover",
    "propose_improvements",
    "apply_improvements"
]
