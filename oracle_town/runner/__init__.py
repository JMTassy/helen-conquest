"""
ORACLE TOWN Inner Loop Runner

Automatic, recursive governance system that:
- Accepts CT proposals + patches
- Runs them in isolated worktrees
- Produces cryptographic evidence (attestations)
- Feeds back K0-safe decision facts to CT
- Bounds recursion with barriers and stagnation detection

Core modules:
- worktree: Isolated patch application
- supervisor: Token sanitization (K0 enforcement)
- intake_adapter: Proposal validation
- factory_adapter: Tool execution → signed attestations
- (pending) briefcase_ledger: Obligation + evidence aggregation
- (pending) context_builder: K0-safe CT feedback
- (pending) ct_gateway: CT integration (simulate or Claude API)
- (pending) innerloop: Orchestration + recursion control
- (pending) creative_observer: Cycle-by-cycle logging
"""

__version__ = "0.1.0"

from .worktree import make_temp_worktree, apply_patch, cleanup_worktree
from .supervisor import Supervisor, SupervisorRejectCode
from .intake_adapter import IntakeAdapter, IntakeAdapterDecision, IntakeAdapterCode
from .factory_adapter import FactoryAdapter, FactoryAttestation, FactoryToolResult

__all__ = [
    # Worktree
    "make_temp_worktree",
    "apply_patch",
    "cleanup_worktree",
    # Supervisor
    "Supervisor",
    "SupervisorRejectCode",
    # Intake
    "IntakeAdapter",
    "IntakeAdapterDecision",
    "IntakeAdapterCode",
    # Factory
    "FactoryAdapter",
    "FactoryAttestation",
    "FactoryToolResult",
]
