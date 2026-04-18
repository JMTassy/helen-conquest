"""
CALVI_TWIN: Governance-grade digital twin for Calvi City Council.

ORACLE BACKBONE constitutional architecture:
- Production (non-sovereign teams)
- Adjudication (lexicographic veto)
- Integration (deterministic SHIP/NO_SHIP gate)
"""

from .core import (
    CalviTwin,
    Claim,
    Receipt,
    Signal,
    Obligation,
    BlockingItem,
    RunRecord,
    Tier,
    ObligationType,
    ReasonCode,
    format_run_record
)

__version__ = "0.1.0"
__all__ = [
    "CalviTwin",
    "Claim",
    "Receipt",
    "Signal",
    "Obligation",
    "BlockingItem",
    "RunRecord",
    "Tier",
    "ObligationType",
    "ReasonCode",
    "format_run_record"
]
