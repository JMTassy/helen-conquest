"""
research_loop — HELEN Research Loop v0.1

FROZEN. See MVP_SPEC_V0_1.md.

Core law: NO_RECEIPT = NO_SHIP.
Memory law: Only SHIPped state is optimization memory.

Build order (per spec §11):
    1. schema_validate.py   — structural validator (gate 0)
    2. manifest_ledger.py   — append-only hash-chained ledger
    3. verdict_reducer.py   — sole authority function
    4. replay_checker.py    — enforces G_replay_ok ✅ BUILT
    5. law_surface.py       — constitutional hash binding ✅ BUILT
    6. bounded_harness.py   — enforces budget ✅ BUILT
"""
from research_loop.run_manifest import (
    MANIFEST_VERSION,
    GENESIS_PARENT_HASH,
    MissionV1,
    ProposalV1,
    ExecutionReceiptV1,
    EvidenceBundleV1,
    IssueItemV1,
    IssueListV1,
    GateVectorV1,
    VerdictV1,
    RunManifestV1,
    ManifestValidationError,
    build_run_manifest,
    verify_manifest,
    manifest_to_dict,
    canonical_json,
    sha256_hex,
)
from research_loop.verdict_reducer import (
    IMPROVEMENT_THRESHOLD,
    compute_verdict,
    compute_metric_gate,
    reduce_run,
)
from research_loop.manifest_ledger import (
    LedgerError,
    LedgerIntegrityError,
    LedgerChainError,
    LedgerVerdictError,
    ManifestLedger,
    make_genesis_manifest,
)
from research_loop.schema_validate import (
    SchemaViolation,
    SchemaValidationError,
    validate_manifest,
    validate_or_raise,
    is_valid_manifest,
)
from research_loop.replay_checker import (
    DEFAULT_TIMEOUT_SECONDS,
    ReplayTarget,
    ReplayResult,
    run_replay,
    check_replay,
    make_replay_target,
)
from research_loop.law_surface import (
    LAW_SURFACE_VERSION,
    LAW_SURFACE_SENTINEL,
    LawSurfaceError,
    LawSurfaceMismatchError,
    law_surface_hash,
    verify_law_surface_hash,
    assert_law_surface_hash,
)
from research_loop.bounded_harness import (
    DEFAULT_BUDGET_SECONDS,
    HarnessResult,
    BoundedHarness,
    HarnessError,
    BudgetExceededError,
    HarnessLockError,
    MutableFilesViolationError,
    run_bounded,
)

__all__ = [
    # Constants
    "MANIFEST_VERSION",
    "GENESIS_PARENT_HASH",
    "IMPROVEMENT_THRESHOLD",
    "DEFAULT_TIMEOUT_SECONDS",
    # Artifact types
    "MissionV1",
    "ProposalV1",
    "ExecutionReceiptV1",
    "EvidenceBundleV1",
    "IssueItemV1",
    "IssueListV1",
    "GateVectorV1",
    "VerdictV1",
    "RunManifestV1",
    # Manifest functions
    "build_run_manifest",
    "verify_manifest",
    "manifest_to_dict",
    "canonical_json",
    "sha256_hex",
    # Reducer
    "compute_verdict",
    "compute_metric_gate",
    "reduce_run",
    # Ledger
    "ManifestLedger",
    "make_genesis_manifest",
    # Schema validator
    "SchemaViolation",
    "SchemaValidationError",
    "validate_manifest",
    "validate_or_raise",
    "is_valid_manifest",
    # Replay checker
    "ReplayTarget",
    "ReplayResult",
    "run_replay",
    "check_replay",
    "make_replay_target",
    # Law surface (constitutional binding)
    "LAW_SURFACE_VERSION",
    "LAW_SURFACE_SENTINEL",
    "law_surface_hash",
    "verify_law_surface_hash",
    "assert_law_surface_hash",
    # Bounded harness (Phase B Step 5)
    "DEFAULT_BUDGET_SECONDS",
    "HarnessResult",
    "BoundedHarness",
    "run_bounded",
    # Errors
    "ManifestValidationError",
    "LedgerError",
    "LedgerIntegrityError",
    "LedgerChainError",
    "LedgerVerdictError",
    "LawSurfaceError",
    "LawSurfaceMismatchError",
    "HarnessError",
    "BudgetExceededError",
    "HarnessLockError",
    "MutableFilesViolationError",
]
