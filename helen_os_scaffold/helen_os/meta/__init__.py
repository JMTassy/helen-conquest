"""
helen_os/meta — HELEN OS self-model + inspector package.

Provides:
  META_SELF_MODEL_V1 — the ledger's own introspective capability contract.
  InnerWorldSnapshotV1 — inspectable computation state (not experience).
  DeterminismReportV1  — N-run canonical hash check.
  GroundingReportV1    — claim-level passport audit.
  CanonicalizerV1      — text output canonicalization (R1–R6 + JSON path).
  ClaimSegmenterV1     — rule-based atomic claim extractor (UNKNOWN passports).
  HELENConclusion      — non-authoritative proposal artifact (NONSHIPABLE).
  ConclusionReducer    — deterministic reducer: HELEN proposal → ReducedConclusion.
  ProposedLaw          — proposed law (non-authoritative; EPOCH3 kernel decides).
  ReducedConclusion    — verified result with gates recomputed from phase evidence.
  CrossReceiptV1       — cross-town federation receipt (CROSS_RECEIPT_V1).
  CrossReceiptBindingError — raised when allowlist gate fails.
  validate_cross_receipt_allowlist — CR-ALLOWLIST gate check.
  cross_receipt_bundle_hash — deterministic bundle_hash helper.

A self-model is not metaphysics.
It is a structured object stating invariants + capabilities + evidence that those
invariants are enforced.
"""

from .self_model import SelfModel, run_self_model_tests, EPOCH1_INSCRIPTION
from .inspector  import (
    InnerWorldSnapshotV1,
    DeterminismReportV1, DriftSummary,
    GroundingReportV1,
    AtomicClaim, SpanPointerV1,
    make_determinism_report, make_grounding_report,
    DETERMINISM_MIN_RUNS, GROUNDING_MAX_UNGROUNDED_RATE,
)
from .canonicalizer_v1 import (
    CanonicalizerV1,
    CanonicalizationResult, CanonicalizationError,
    canonicalize_text, canonical_text_hash,
)
from .claim_segmenter import ClaimSegmenterV1, MIN_CLAIM_LENGTH
from .conclusion_v1 import (
    HELENConclusion,
    ProposedLaw,
    ReducedConclusion,
    ConclusionReducer,
)
from .proposed_law import (
    ProposedLawV1,
    LawStatus,
    CANYON_NONINTERFERENCE_V1,
    HELEN_PROPOSAL_USE_RECEIPT_GATE_V1,
)
from .authz_receipt import (
    AuthzReceiptV1,
    AuthzReceiptRef,
    AuthzBindingError,
    validate_authz_binding,
)
from .cross_receipt_v1 import (
    CrossReceiptV1,
    CrossReceiptBundleRef,
    CrossReceiptBindingError,
    validate_cross_receipt_allowlist,
    cross_receipt_bundle_hash,
)
from .her_hal_split import (
    HEROutputType,
    HEROutput,
    HALVerdictLevel,
    HALVerdict,
    WitnessInjectionType,
    WitnessInjection,
    TwoChannelEnforcer,
    IdentityBindingV1,
    PatchProposalV1,
    authority_bleed_scan,
    BLOCK_AUTHORITY_WORDS,
    WARN_AUTHORITY_WORDS,
)
from .two_block_parser import (
    parse_two_block,
    ParsedTwoBlock,
    TwoBlockParseError,
    TwoBlockBindingError,
    compute_her_block_hash,
    build_hal_prompt,
    TWO_BLOCK_SYSTEM_PROMPT,
)

__all__ = [
    # Self-model (EPOCH1)
    "SelfModel", "run_self_model_tests", "EPOCH1_INSCRIPTION",
    # Inspector schemas (proposal v0.1)
    "InnerWorldSnapshotV1",
    "DeterminismReportV1", "DriftSummary",
    "GroundingReportV1",
    "AtomicClaim", "SpanPointerV1",
    "make_determinism_report", "make_grounding_report",
    "DETERMINISM_MIN_RUNS", "GROUNDING_MAX_UNGROUNDED_RATE",
    # CanonicalizerV1
    "CanonicalizerV1",
    "CanonicalizationResult", "CanonicalizationError",
    "canonicalize_text", "canonical_text_hash",
    # ClaimSegmenterV1
    "ClaimSegmenterV1", "MIN_CLAIM_LENGTH",
    # HELENConclusion + ConclusionReducer (HELEN_CONCLUSION_V1)
    "HELENConclusion", "ProposedLaw",
    "ReducedConclusion", "ConclusionReducer",
    # ProposedLawV1 (full schema with falsifiers + inscription tracking)
    "ProposedLawV1", "LawStatus",
    "CANYON_NONINTERFERENCE_V1", "HELEN_PROPOSAL_USE_RECEIPT_GATE_V1",
    # AUTHZ_RECEIPT_V1 (receipt-gate for helen_proposal_used=True)
    "AuthzReceiptV1", "AuthzReceiptRef",
    "AuthzBindingError", "validate_authz_binding",
    # CROSS_RECEIPT_V1 (cross-town federation receipt)
    "CrossReceiptV1", "CrossReceiptBundleRef",
    "CrossReceiptBindingError", "validate_cross_receipt_allowlist",
    "cross_receipt_bundle_hash",
    # HER/HAL two-channel enforcer
    "HEROutputType", "HEROutput",
    "HALVerdictLevel", "HALVerdict",
    "WitnessInjectionType", "WitnessInjection",
    "TwoChannelEnforcer",
    "IdentityBindingV1", "PatchProposalV1",
    "authority_bleed_scan",
    "BLOCK_AUTHORITY_WORDS", "WARN_AUTHORITY_WORDS",
    # Two-block parser (T-TWO-1 through T-TWO-5)
    "parse_two_block", "ParsedTwoBlock",
    "TwoBlockParseError", "TwoBlockBindingError",
    "compute_her_block_hash", "build_hal_prompt",
    "TWO_BLOCK_SYSTEM_PROMPT",
]
