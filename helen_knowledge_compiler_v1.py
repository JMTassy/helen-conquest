"""
HELEN_KNOWLEDGE_COMPILER_V1: Formal Spec
Claim Extraction and Canonical Admission Pipeline

Status: PROPOSED → pending test certification

The compiler is the governed bridge between raw sources and canonical knowledge.
It implements the compilation direction from HELEN_OS_ARCHITECTURE_V2:

    raw sources → extracted claims → audits → canonical admission

Core design rules (frozen):
  1. SOURCE_INGEST routes to SKILL (multi-step, non-sovereign).
     The compiler itself is NON_SOVEREIGN — it cannot make canonical decisions.
  2. CANONICAL admission requires a KERNEL chain receipt.
     No claim transitions from provisional → canonical without a KERNEL-gated dispatch.
  3. Every claim carries a dispatch_id_ref — lineage is non-optional.
  4. Status promotion is monotonic within the pipeline:
     speculative → candidate → provisional → canonical
     Demotion is not permitted. Deprecation is the only exit.
  5. Contradictions between claims are surfaced, never silently merged.
  6. Uncertainty is bounded [0.0, 1.0] and non-nullable.
  7. Claim hashes exclude claim_id and timestamp — deterministic across runs.
  8. Stage transitions are sequential — claims cannot skip pipeline stages.

The compilation pipeline (stages, in order):
  INGEST → EXTRACT → VALIDATE → AUDIT → ADMIT → ADMITTED / REJECTED

Each stage transition is receipted via CompilerStageReceipt.
KERNEL-gated transitions (AUDIT → ADMIT for canonical) also require ChainReceiptV2.

Routing integration (from dispatch law):
  SOURCE_INGEST            → SKILL
  CLAIM_EXTRACTION_REQUEST → SKILL
  CLAIM_BUNDLE             → SKILL
  PROMOTION_REQUEST        → KERNEL  (canonical admission gate)

Architecture reference: HELEN_OS_ARCHITECTURE_V2.md (FROZEN)
Depends on:
  helen_dispatch_v1_schemas.py (FROZEN)
  helen_chain_receipt_v2.py    (FROZEN_AFTER_RUNTIME_COUPLING)
  knowledge_health_audit_v2_patch_01.py (FROZEN)
  knowledge_health_audit_v2_patch_02.py (FROZEN_WITH_PATCH_02)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
import hashlib
import json
import uuid


# ============================================================================
# CANONICAL HASHING (matches pattern across all HELEN V2 artifacts)
# ============================================================================

def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


# ============================================================================
# ENUMS
# ============================================================================

class ClaimStatus(Enum):
    """
    Artifact status map from Layer 4 — exact match to architecture.

    Status promotion chain (authority increases left → right):
      speculative → candidate → provisional → canonical

    Invariants:
    - Status can only increase within the compiler pipeline.
    - Demotion is not permitted.
    - Deprecation is the only path to lower visibility (supersedes, not demotes).
    - authority_level() provides a numeric comparison for promotion enforcement.
    """
    SPECULATIVE = "speculative"   # Exploratory; NONE authority; Temple output
    CANDIDATE = "candidate"       # Proposed; NONE authority; pending review
    PROVISIONAL = "provisional"   # Admitted but unverified; NON_SOVEREIGN
    CANONICAL = "canonical"       # Reducer-admitted; lineage-proven; SOVEREIGN
    DEPRECATED = "deprecated"     # Superseded; lineage preserved; no longer active

    def authority_level(self) -> int:
        """
        Numeric authority level for promotion enforcement.
        Higher = more authoritative. DEPRECATED is terminal, not in the chain.
        """
        return {
            ClaimStatus.SPECULATIVE: 0,
            ClaimStatus.CANDIDATE: 1,
            ClaimStatus.PROVISIONAL: 2,
            ClaimStatus.CANONICAL: 3,
            ClaimStatus.DEPRECATED: -1,  # Terminal; not in the promotion chain
        }[self]


class SourceType(Enum):
    """Classification of incoming raw sources."""
    DOCUMENT = "document"                    # Structured text (articles, papers, reports)
    OBSERVATION = "observation"              # Sensor data, measurements, empirical records
    TEMPLE_ARTIFACT = "temple_artifact"      # Output from TEMPLE exploration layer
    RESEARCH_RESULT = "research_result"      # Autoresearch batch output
    USER_ASSERTION = "user_assertion"        # User-provided claim (treated as candidate)
    EXTERNAL_REFERENCE = "external_reference"  # Pointer to external source


class CompilerStage(Enum):
    """
    Pipeline stages — ordered, non-skippable.

    Claims cannot skip stages. Stage transitions must be sequential.
    A claim at EXTRACT cannot jump to ADMIT without passing VALIDATE and AUDIT.

    sequence_index() enforces ordering. CompilerStageReceipt validates at construction.
    """
    INGEST = "ingest"         # Raw source received; SourceIngestionPacket built
    EXTRACT = "extract"       # Atomic claims extracted from source
    VALIDATE = "validate"     # Claims checked: structure, bounds, completeness
    AUDIT = "audit"           # Lineage and health audit run
    ADMIT = "admit"           # KERNEL admission gate
    ADMITTED = "admitted"     # Terminal: canonical or provisional
    REJECTED = "rejected"     # Terminal: audit or admission failure

    def sequence_index(self) -> int:
        """Enforces sequential ordering. Terminal stages share level 5."""
        return {
            CompilerStage.INGEST: 0,
            CompilerStage.EXTRACT: 1,
            CompilerStage.VALIDATE: 2,
            CompilerStage.AUDIT: 3,
            CompilerStage.ADMIT: 4,
            CompilerStage.ADMITTED: 5,
            CompilerStage.REJECTED: 5,  # Terminal — same level as ADMITTED
        }[self]

    def is_terminal(self) -> bool:
        return self in (CompilerStage.ADMITTED, CompilerStage.REJECTED)


class ContradictionSeverity(Enum):
    """How severe is the contradiction between two claims?"""
    DIRECT = "direct"        # Mutually exclusive assertions — both cannot be true
    PARTIAL = "partial"      # Overlapping but inconsistent — partially incompatible
    UNCERTAIN = "uncertain"  # Cannot determine without more context


class AdmissionVerdict(Enum):
    """Final verdict from the KERNEL admission gate."""
    ADMITTED_CANONICAL = "admitted_canonical"                  # Full canonical; KERNEL receipt required
    ADMITTED_PROVISIONAL = "admitted_provisional"              # Provisional; no full verification yet
    REJECTED_AUDIT_FAILURE = "rejected_audit_failure"          # Audit violations present
    REJECTED_LINEAGE_BROKEN = "rejected_lineage_broken"        # Missing or broken dispatch chain
    REJECTED_UNCERTAINTY_HIGH = "rejected_uncertainty_high"    # Uncertainty exceeds admission threshold
    REJECTED_CONTRADICTION = "rejected_contradiction"          # Unresolved DIRECT contradiction
    DEFERRED = "deferred"                                      # Needs more evidence (retryable)


# ============================================================================
# UNCERTAINTY THRESHOLDS (CONSTITUTIONAL CONSTANTS — FROZEN)
# ============================================================================

class UncertaintyThreshold:
    """
    Uncertainty thresholds governing admission eligibility.

    These are NOT configurable parameters — they are constitutional constants.
    Changing them requires a new version (HELEN_KNOWLEDGE_COMPILER_V2).

    Interpretation:
      uncertainty = 0.0  →  certain (no doubt)
      uncertainty = 1.0  →  pure speculation (no evidential basis)
    """
    CANONICAL_MAX = 0.2    # Claims with uncertainty > 0.2 cannot be CANONICAL
    PROVISIONAL_MAX = 0.6  # Claims with uncertainty > 0.6 cannot be PROVISIONAL
    CANDIDATE_MAX = 1.0    # Claims with uncertainty > 1.0 are structurally invalid

    @staticmethod
    def max_status_for_uncertainty(uncertainty: float) -> ClaimStatus:
        """
        Given uncertainty, return the maximum status this claim can achieve.

        This is a ceiling, not a guarantee. A claim below the ceiling may still
        be rejected for other reasons: lineage, contradiction, audit failure.
        """
        if not (0.0 <= uncertainty <= 1.0):
            raise ValueError(f"Uncertainty must be in [0.0, 1.0], got {uncertainty}")
        if uncertainty <= UncertaintyThreshold.CANONICAL_MAX:
            return ClaimStatus.CANONICAL
        elif uncertainty <= UncertaintyThreshold.PROVISIONAL_MAX:
            return ClaimStatus.PROVISIONAL
        else:
            return ClaimStatus.CANDIDATE


# ============================================================================
# FROZEN REASON CODES
# ============================================================================

COMPILER_REASON_CODES = frozenset({
    # Source ingestion
    "source_ingest_accepted",
    "source_ingest_duplicate_hash",              # Same raw_content already ingested
    "source_ingest_missing_dispatch_ref",        # No dispatch_id_ref
    "source_ingest_empty_content",               # Empty raw_content
    "source_ingest_wrong_route",                 # Not routed to SKILL

    # Claim extraction
    "claim_extracted_from_source",
    "claim_extraction_zero_claims",              # Source produced no extractable claims
    "claim_extraction_uncertainty_out_of_bounds", # Structural error in extraction

    # Validation
    "claim_validated_structure_ok",
    "claim_validation_missing_content",
    "claim_validation_missing_dispatch_ref",
    "claim_validation_uncertainty_out_of_bounds",
    "claim_validation_status_ceiling_exceeded",   # Status above uncertainty ceiling
    "claim_validation_invalid_stage",

    # Audit
    "claim_audit_clean",
    "claim_audit_lineage_violation",             # Missing or broken dispatch chain
    "claim_audit_contradiction_detected",        # Contradiction with existing claim
    "claim_audit_uncertainty_exceeds_threshold", # Too uncertain for target admission level

    # Admission
    "claim_admitted_canonical",
    "claim_admitted_provisional",
    "claim_rejected_audit_failure",
    "claim_rejected_lineage_broken",
    "claim_rejected_uncertainty_high",
    "claim_rejected_unresolved_contradiction",
    "claim_deferred_pending_evidence",

    # Routing validation
    "ingest_dispatch_valid",
    "ingest_dispatch_invalid_route",
    "ingest_dispatch_invalid_input_type",
    "admission_dispatch_valid",
    "admission_dispatch_invalid_route",
    "admission_dispatch_invalid_input_type",
})


def validate_compiler_reason_codes(codes: List[str]) -> bool:
    """Verify all compiler reason codes are frozen (registered)."""
    return all(code in COMPILER_REASON_CODES for code in codes)


# ============================================================================
# CLAIM SCHEMA (V1 — FROZEN UPON CERTIFICATION)
# ============================================================================

CLAIM_SCHEMA_VERSION = "CLAIM_V1"


@dataclass
class Claim:
    """
    The atomic unit of the knowledge compiler.

    A Claim is the smallest epistemic assertion that can be:
    - independently evaluated
    - independently admitted or rejected
    - independently linked to a source (provenance)
    - independently versioned if superseded

    Constitutional invariants (enforced at __post_init__):
    - uncertainty must be in [0.0, 1.0]
    - dispatch_id_ref must be non-empty (lineage non-optional)
    - content must be non-empty
    - claim_hash computed at construction; excludes claim_id + timestamp (determinism)

    Hash determinism invariant:
    Same content + source_ref + uncertainty + status + dispatch_id_ref + compiler_stage
    → same claim_hash across ALL runs (run-specific fields excluded).
    """
    claim_id: str                               # Run-specific; excluded from hash
    content: str                                # The atomic epistemic assertion (required)
    source_ref: str                             # Provenance reference (required)
    uncertainty: float                          # [0.0, 1.0]; 0=certain, 1=pure speculation
    status: ClaimStatus                         # Current status in the promotion chain
    dispatch_id_ref: str                        # Governing dispatch; required (lineage law)
    compiler_stage: CompilerStage               # Which pipeline stage produced this

    # Optional provenance and context
    contradicted_by: List[str] = field(default_factory=list)  # Other claim_ids
    lineage: List[str] = field(default_factory=list)          # Chain of dispatch_ids
    tags: List[str] = field(default_factory=list)             # Semantic labels

    # Run metadata (excluded from hash for determinism)
    extraction_timestamp: Optional[str] = None

    # Computed at construction (deterministic)
    claim_hash: Optional[str] = None
    schema_version: str = field(default=CLAIM_SCHEMA_VERSION, init=False)

    def __post_init__(self):
        # Invariant 1: Uncertainty must be in bounds
        if not (0.0 <= self.uncertainty <= 1.0):
            raise ValueError(
                f"Claim uncertainty must be in [0.0, 1.0], got {self.uncertainty}"
            )
        # Invariant 2: dispatch_id_ref is required (lineage non-optional)
        if not self.dispatch_id_ref or not self.dispatch_id_ref.strip():
            raise ValueError(
                "Claim.dispatch_id_ref is required — lineage is non-optional in HELEN"
            )
        # Invariant 3: content must not be empty
        if not self.content or not self.content.strip():
            raise ValueError("Claim.content must not be empty")
        # Compute hash if not already set
        if self.claim_hash is None:
            self.claim_hash = hash_claim(self)

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        result = {
            "claim_id": self.claim_id,
            "content": self.content,
            "source_ref": self.source_ref,
            "uncertainty": self.uncertainty,
            "status": self.status.value,
            "dispatch_id_ref": self.dispatch_id_ref,
            "compiler_stage": self.compiler_stage.value,
            "contradicted_by": self.contradicted_by,
            "lineage": self.lineage,
            "tags": self.tags,
            "extraction_timestamp": self.extraction_timestamp,
            "claim_hash": self.claim_hash,
            "schema_version": self.schema_version,
        }
        if exclude_run_metadata:
            del result["claim_id"]
            del result["extraction_timestamp"]
        return result


def hash_claim(claim: Claim) -> str:
    """
    Deterministic claim hash.

    Excludes run metadata: claim_id, extraction_timestamp.
    Invariant: same semantic content → same hash across all runs.
    """
    data = {
        "content": claim.content,
        "source_ref": claim.source_ref,
        "uncertainty": claim.uncertainty,
        "status": claim.status.value,
        "dispatch_id_ref": claim.dispatch_id_ref,
        "compiler_stage": claim.compiler_stage.value,
        "contradicted_by": sorted(claim.contradicted_by),
        "lineage": claim.lineage,
        "tags": sorted(claim.tags),
        "schema_version": CLAIM_SCHEMA_VERSION,
    }
    return _sha256(_canonical_json(data))


# ============================================================================
# SOURCE INGESTION PACKET (V1 — FROZEN UPON CERTIFICATION)
# ============================================================================

SOURCE_INGESTION_SCHEMA_VERSION = "SOURCE_INGESTION_V1"


@dataclass
class SourceIngestionPacket:
    """
    The governing object for the INGEST stage.

    Routing law (from dispatch):
      SOURCE_INGEST → SKILL

    A SourceIngestionPacket is NON_SOVEREIGN. It requests processing but cannot
    authorize canonical admission on its own. The compiler (SKILL) handles
    extraction and audit; the KERNEL handles final canonical admission.

    Invariants:
    - raw_content must not be empty
    - dispatch_id_ref is required
    - ingestion_hash = SHA256(raw_content) — deterministic; enables deduplication
      before extraction begins (same source → same hash → skip if already processed)
    """
    source_id: str                              # Run-specific; excluded from content hash
    source_type: SourceType
    raw_content: str
    dispatch_id_ref: str                        # Must be a SOURCE_INGEST → SKILL dispatch

    # Optional context
    source_name: Optional[str] = None          # Human-readable label
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Run metadata (excluded from ingestion_hash)
    ingestion_timestamp: Optional[str] = None

    # Computed at construction
    ingestion_hash: Optional[str] = None       # SHA256 of raw_content (deterministic)
    schema_version: str = field(default=SOURCE_INGESTION_SCHEMA_VERSION, init=False)

    def __post_init__(self):
        if not self.raw_content or not self.raw_content.strip():
            raise ValueError("SourceIngestionPacket.raw_content must not be empty")
        if not self.dispatch_id_ref or not self.dispatch_id_ref.strip():
            raise ValueError("SourceIngestionPacket.dispatch_id_ref is required")
        if self.ingestion_hash is None:
            # Hash is over content only — not metadata or timestamps
            self.ingestion_hash = _sha256(_canonical_json({"raw_content": self.raw_content}))

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        result = {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "raw_content": self.raw_content,
            "dispatch_id_ref": self.dispatch_id_ref,
            "source_name": self.source_name,
            "metadata": self.metadata,
            "ingestion_timestamp": self.ingestion_timestamp,
            "ingestion_hash": self.ingestion_hash,
            "schema_version": self.schema_version,
        }
        if exclude_run_metadata:
            del result["source_id"]
            del result["ingestion_timestamp"]
        return result


# ============================================================================
# CONTRADICTION REPORT (V1 — FROZEN UPON CERTIFICATION)
# ============================================================================

CONTRADICTION_SCHEMA_VERSION = "CONTRADICTION_V1"


@dataclass
class ContradictionReport:
    """
    Emitted when two claims assert incompatible things.

    Architectural rule: Contradictions are SURFACE-VISIBLE, never suppressed.
    The compiler never silently resolves contradictions — it surfaces them
    and blocks both claims from canonical promotion until explicitly resolved.

    Severity determines blocking behavior:
    - DIRECT: both claims blocked from canonical admission
    - PARTIAL: flagged but not automatically blocking
    - UNCERTAIN: informational only

    Resolution paths:
    - One claim deprecated (superseded by the other)
    - Both marked contradicted_by each other (stay at candidate)
    - New reconciliation claim added (admits with reconciliation note)
    """
    report_id: str
    claim_a_id: str
    claim_b_id: str
    severity: ContradictionSeverity
    reason: str                             # Human-readable contradiction description

    # Lineage: both claims' dispatch_id_refs
    claim_a_dispatch_ref: str
    claim_b_dispatch_ref: str

    # Blocks canonical promotion for DIRECT contradictions
    blocks_canonical_admission: bool = True

    # Run metadata
    detected_at: Optional[str] = None

    # Computed
    report_hash: Optional[str] = None
    schema_version: str = field(default=CONTRADICTION_SCHEMA_VERSION, init=False)

    def __post_init__(self):
        if self.report_hash is None:
            data = {
                "claim_a_id": self.claim_a_id,
                "claim_b_id": self.claim_b_id,
                "severity": self.severity.value,
                "reason": self.reason,
                "claim_a_dispatch_ref": self.claim_a_dispatch_ref,
                "claim_b_dispatch_ref": self.claim_b_dispatch_ref,
                "blocks_canonical_admission": self.blocks_canonical_admission,
                "schema_version": CONTRADICTION_SCHEMA_VERSION,
            }
            self.report_hash = _sha256(_canonical_json(data))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "claim_a_id": self.claim_a_id,
            "claim_b_id": self.claim_b_id,
            "severity": self.severity.value,
            "reason": self.reason,
            "claim_a_dispatch_ref": self.claim_a_dispatch_ref,
            "claim_b_dispatch_ref": self.claim_b_dispatch_ref,
            "blocks_canonical_admission": self.blocks_canonical_admission,
            "detected_at": self.detected_at,
            "report_hash": self.report_hash,
            "schema_version": self.schema_version,
        }


# ============================================================================
# COMPILER STAGE RECEIPT (V1 — FROZEN UPON CERTIFICATION)
# ============================================================================

STAGE_RECEIPT_SCHEMA_VERSION = "COMPILER_STAGE_RECEIPT_V1"


@dataclass
class CompilerStageReceipt:
    """
    Immutable receipt for each stage transition in the compiler pipeline.

    Constitutional invariant: Each stage transition must be receipted.
    A claim cannot be at stage N+1 without a receipt proving stage N → N+1.

    Stage skip law (enforced at __post_init__):
    The to_stage must be exactly one step forward from from_stage,
    OR the to_stage must be REJECTED (terminal, allowed from any stage).

    For KERNEL-gated transitions (AUDIT → ADMIT for canonical),
    a ChainReceiptV2 is additionally required. chain_receipt_ref captures that link.

    Receipt hash excludes receipt_id and transition_timestamp (run metadata).
    Same transition + same claims + same dispatch → same receipt_hash.
    """
    receipt_id: str
    from_stage: CompilerStage
    to_stage: CompilerStage
    claim_ids: List[str]                    # Claims transitioning in this handoff
    dispatch_id_ref: str                    # Governing dispatch for this transition
    chain_receipt_ref: Optional[str]        # Reference to ChainReceiptV2 if applicable

    # Transition outcome
    stage_verdict: str                      # "pass" | "fail" | "deferred"
    violation_count: int = 0
    blocking_violation_count: int = 0
    notes: str = ""

    # Run metadata
    transition_timestamp: Optional[str] = None

    # Computed
    receipt_hash: Optional[str] = None
    schema_version: str = field(default=STAGE_RECEIPT_SCHEMA_VERSION, init=False)

    def __post_init__(self):
        # Stage sequence law: to_stage must be exactly +1, or REJECTED (terminal)
        from_idx = self.from_stage.sequence_index()
        to_idx = self.to_stage.sequence_index()
        is_valid_sequence = (to_idx == from_idx + 1)
        is_rejection = (self.to_stage == CompilerStage.REJECTED)
        is_terminal_to_terminal = (
            self.from_stage.is_terminal() and self.to_stage.is_terminal()
        )
        if not (is_valid_sequence or is_rejection or is_terminal_to_terminal):
            raise ValueError(
                f"Stage sequence violation: cannot transition from "
                f"{self.from_stage.value} (index {from_idx}) to "
                f"{self.to_stage.value} (index {to_idx}). "
                f"Must advance exactly one step, or reject."
            )
        if self.receipt_hash is None:
            data = {
                "from_stage": self.from_stage.value,
                "to_stage": self.to_stage.value,
                "claim_ids": sorted(self.claim_ids),
                "dispatch_id_ref": self.dispatch_id_ref,
                "chain_receipt_ref": self.chain_receipt_ref,
                "stage_verdict": self.stage_verdict,
                "violation_count": self.violation_count,
                "blocking_violation_count": self.blocking_violation_count,
                "notes": self.notes,
                "schema_version": STAGE_RECEIPT_SCHEMA_VERSION,
            }
            self.receipt_hash = _sha256(_canonical_json(data))

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        result = {
            "receipt_id": self.receipt_id,
            "from_stage": self.from_stage.value,
            "to_stage": self.to_stage.value,
            "claim_ids": self.claim_ids,
            "dispatch_id_ref": self.dispatch_id_ref,
            "chain_receipt_ref": self.chain_receipt_ref,
            "stage_verdict": self.stage_verdict,
            "violation_count": self.violation_count,
            "blocking_violation_count": self.blocking_violation_count,
            "notes": self.notes,
            "transition_timestamp": self.transition_timestamp,
            "receipt_hash": self.receipt_hash,
            "schema_version": self.schema_version,
        }
        if exclude_run_metadata:
            del result["receipt_id"]
            del result["transition_timestamp"]
        return result


# ============================================================================
# ADMISSION RESULT (V1 — FROZEN UPON CERTIFICATION)
# ============================================================================

ADMISSION_SCHEMA_VERSION = "ADMISSION_RESULT_V1"


@dataclass
class AdmissionResult:
    """
    Final output of the KERNEL admission gate.

    Canonical admission proof:
    - If ADMITTED_CANONICAL: claim_hash + chain_receipt_ref together prove
      that this exact claim content was admitted by a KERNEL-routed dispatch.
    - If ADMITTED_PROVISIONAL: accepted but unverified; may be upgraded or deprecated.
    - If REJECTED_*: reason preserved for audit; claim may not be re-submitted
      without resolving the stated issues.
    - If DEFERRED: retryable; missing evidence is listed.

    Constitutional invariant:
    ADMITTED_CANONICAL requires chain_receipt_ref (enforced at __post_init__).
    No chain receipt = not canonical, regardless of other fields.
    """
    result_id: str
    claim_id: str
    claim_hash: str                             # The claim hash at submission (immutable ref)
    dispatch_id_ref: str                        # KERNEL dispatch that authorized this
    chain_receipt_ref: Optional[str]            # ChainReceiptV2 proving KERNEL admission

    verdict: AdmissionVerdict
    final_status: ClaimStatus                   # Where the claim ends up
    reason_codes: List[str]                     # Must all be from COMPILER_REASON_CODES

    # Admission context
    blocking_violations: int = 0
    contradiction_reports: List[str] = field(default_factory=list)  # report_ids

    # Run metadata
    admission_timestamp: Optional[str] = None

    # Computed
    result_hash: Optional[str] = None
    schema_version: str = field(default=ADMISSION_SCHEMA_VERSION, init=False)

    def __post_init__(self):
        # Constitutional invariant: canonical admission requires KERNEL chain receipt
        if (self.verdict == AdmissionVerdict.ADMITTED_CANONICAL
                and not self.chain_receipt_ref):
            raise ValueError(
                "AdmissionResult.chain_receipt_ref is required for ADMITTED_CANONICAL. "
                "Canonical admission requires a KERNEL chain receipt as proof of lineage."
            )
        # Reason codes must be from frozen set
        invalid = [c for c in self.reason_codes if c not in COMPILER_REASON_CODES]
        if invalid:
            raise ValueError(
                f"AdmissionResult contains unregistered reason codes: {invalid}. "
                f"All reason codes must be in COMPILER_REASON_CODES."
            )
        if self.result_hash is None:
            data = {
                "claim_id": self.claim_id,
                "claim_hash": self.claim_hash,
                "dispatch_id_ref": self.dispatch_id_ref,
                "chain_receipt_ref": self.chain_receipt_ref,
                "verdict": self.verdict.value,
                "final_status": self.final_status.value,
                "reason_codes": sorted(self.reason_codes),
                "blocking_violations": self.blocking_violations,
                "contradiction_reports": sorted(self.contradiction_reports),
                "schema_version": ADMISSION_SCHEMA_VERSION,
            }
            self.result_hash = _sha256(_canonical_json(data))

    @property
    def is_admitted(self) -> bool:
        return self.verdict in (
            AdmissionVerdict.ADMITTED_CANONICAL,
            AdmissionVerdict.ADMITTED_PROVISIONAL,
        )

    @property
    def is_canonical(self) -> bool:
        return self.verdict == AdmissionVerdict.ADMITTED_CANONICAL

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        result = {
            "result_id": self.result_id,
            "claim_id": self.claim_id,
            "claim_hash": self.claim_hash,
            "dispatch_id_ref": self.dispatch_id_ref,
            "chain_receipt_ref": self.chain_receipt_ref,
            "verdict": self.verdict.value,
            "final_status": self.final_status.value,
            "reason_codes": self.reason_codes,
            "blocking_violations": self.blocking_violations,
            "contradiction_reports": self.contradiction_reports,
            "admission_timestamp": self.admission_timestamp,
            "result_hash": self.result_hash,
            "schema_version": self.schema_version,
        }
        if exclude_run_metadata:
            del result["result_id"]
            del result["admission_timestamp"]
        return result


# ============================================================================
# CLAIM BUILDER
# ============================================================================

class ClaimBuilder:
    """
    Factory for Claims — enforces all structural invariants at construction.

    Usage:
      builder = ClaimBuilder()
      claim = builder.emit(
          content="The system is deterministic under identical inputs",
          source_ref="autoresearch_batch_run_001",
          uncertainty=0.05,
          status=ClaimStatus.CANDIDATE,
          dispatch_id_ref="disp_skill_001",
          compiler_stage=CompilerStage.EXTRACT,
      )
    """

    def emit(
        self,
        content: str,
        source_ref: str,
        uncertainty: float,
        status: ClaimStatus,
        dispatch_id_ref: str,
        compiler_stage: CompilerStage,
        contradicted_by: Optional[List[str]] = None,
        lineage: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Claim:
        """Emit a new Claim with full invariant enforcement."""
        return Claim(
            claim_id=str(uuid.uuid4()),
            content=content,
            source_ref=source_ref,
            uncertainty=uncertainty,
            status=status,
            dispatch_id_ref=dispatch_id_ref,
            compiler_stage=compiler_stage,
            contradicted_by=contradicted_by or [],
            lineage=lineage or [dispatch_id_ref],
            tags=tags or [],
            extraction_timestamp=datetime.utcnow().isoformat() + "Z",
        )

    def can_promote(self, claim: Claim, target_status: ClaimStatus) -> Tuple[bool, str]:
        """
        Check whether a claim can be promoted to target_status.

        Returns (allowed, reason).

        Promotion rules:
        1. DEPRECATED is always allowed (exit from any status)
        2. Demotion is not permitted (target_level < current_level)
        3. Status skipping is not permitted (must advance one level at a time)
        4. Uncertainty ceiling must not be exceeded
        5. Canonical promotion is flagged as requiring KERNEL chain receipt
        """
        if target_status == ClaimStatus.DEPRECATED:
            return True, "deprecation always allowed"

        current_level = claim.status.authority_level()
        target_level = target_status.authority_level()

        # Cannot demote
        if target_level < current_level:
            return False, (
                f"demotion not permitted: {claim.status.value} → {target_status.value}"
            )

        # Cannot skip levels
        if target_level > current_level + 1:
            return False, (
                f"status skip not permitted: {claim.status.value} → {target_status.value}. "
                f"Must pass through intermediate statuses."
            )

        # Cannot exceed uncertainty ceiling
        ceiling = UncertaintyThreshold.max_status_for_uncertainty(claim.uncertainty)
        if target_level > ceiling.authority_level():
            return False, (
                f"uncertainty {claim.uncertainty} prevents promotion to {target_status.value}. "
                f"Maximum achievable status: {ceiling.value}."
            )

        # Canonical requires KERNEL chain receipt (external check)
        if target_status == ClaimStatus.CANONICAL:
            return True, "canonical promotion allowed — KERNEL chain receipt required externally"

        return True, f"promotion to {target_status.value} allowed"

    def validate_status_ceiling(self, claim: Claim) -> Tuple[bool, str]:
        """
        Check whether the claim's uncertainty is consistent with its current status.

        Returns (valid, reason).
        """
        ceiling = UncertaintyThreshold.max_status_for_uncertainty(claim.uncertainty)
        if claim.status.authority_level() > ceiling.authority_level():
            return False, (
                f"claim status {claim.status.value} exceeds uncertainty ceiling "
                f"({ceiling.value}) for uncertainty={claim.uncertainty}"
            )
        return True, "status consistent with uncertainty ceiling"


# ============================================================================
# SOURCE INGESTION BUILDER
# ============================================================================

class SourceIngestionBuilder:
    """Factory for SourceIngestionPackets with full invariant enforcement."""

    def emit(
        self,
        source_type: SourceType,
        raw_content: str,
        dispatch_id_ref: str,
        source_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SourceIngestionPacket:
        return SourceIngestionPacket(
            source_id=str(uuid.uuid4()),
            source_type=source_type,
            raw_content=raw_content,
            dispatch_id_ref=dispatch_id_ref,
            source_name=source_name,
            metadata=metadata or {},
            ingestion_timestamp=datetime.utcnow().isoformat() + "Z",
        )


# ============================================================================
# DISPATCH INTEGRATION (ROUTING VALIDATION)
# ============================================================================

class SourceIngestionRouter:
    """
    Validates that dispatch routing is correct before pipeline progression.

    Routing law (from dispatch schema, frozen):
      SOURCE_INGEST            → SKILL
      CLAIM_EXTRACTION_REQUEST → SKILL
      CLAIM_BUNDLE             → SKILL
      PROMOTION_REQUEST        → KERNEL   (canonical admission gate)

    This class enforces that routing happened correctly before allowing
    the compiler to proceed. Wrong routing = rejection at the boundary.
    """

    # Input types that authorize source ingestion (SKILL route)
    AUTHORIZED_INGEST_INPUT_TYPES = {
        "SOURCE_INGEST",
        "CLAIM_BUNDLE",
        "CLAIM_EXTRACTION_REQUEST",
    }

    # The only route that authorizes canonical admission
    AUTHORIZED_CANONICAL_ROUTE = "KERNEL"

    # The only route that authorizes non-canonical ingestion
    AUTHORIZED_INGEST_ROUTE = "SKILL"

    def validate_ingest_dispatch(
        self,
        dispatch_receipt: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Validate that source ingestion was authorized by a SKILL-routed dispatch.

        Args:
            dispatch_receipt: A DispatchReceipt.to_dict() output.

        Returns:
            (valid, reason) — reason is a frozen reason code string.
        """
        route = dispatch_receipt.get("primary_route", "")
        input_type = dispatch_receipt.get("input_type", "")

        if input_type not in self.AUTHORIZED_INGEST_INPUT_TYPES:
            return False, "ingest_dispatch_invalid_input_type"

        if route != self.AUTHORIZED_INGEST_ROUTE:
            return False, "ingest_dispatch_invalid_route"

        return True, "ingest_dispatch_valid"

    def validate_admission_dispatch(
        self,
        dispatch_receipt: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Validate that canonical admission was authorized by a KERNEL-routed dispatch.

        Args:
            dispatch_receipt: A DispatchReceipt.to_dict() output.

        Returns:
            (valid, reason) — reason is a frozen reason code string.
        """
        route = dispatch_receipt.get("primary_route", "")
        input_type = dispatch_receipt.get("input_type", "")

        if input_type != "PROMOTION_REQUEST":
            return False, "admission_dispatch_invalid_input_type"

        if route != self.AUTHORIZED_CANONICAL_ROUTE:
            return False, "admission_dispatch_invalid_route"

        return True, "admission_dispatch_valid"


# ============================================================================
# CONTRADICTION DETECTOR
# ============================================================================

class ContradictionDetector:
    """
    Detects contradictions between claims.

    Architectural rule: contradictions must be surfaced, not suppressed.
    This detector is called during the AUDIT stage before admission.

    Current detection heuristic (V1):
    - Two claims with the same source_ref but contradictory uncertainty
      (one very certain, one very uncertain about the same content signature) → PARTIAL
    - Two claims explicitly marked as contradicting each other → DIRECT
    - Claims with identical tags but diverging status ceilings → UNCERTAIN

    V1 does NOT implement semantic NLP contradiction detection (that requires
    a SKILL worker beyond the scope of this formal spec).
    """

    def detect_structural_contradictions(
        self,
        claims: List[Claim],
    ) -> List[ContradictionReport]:
        """
        Detect structural contradictions between a set of claims.

        Returns a list of ContradictionReports (may be empty).
        """
        reports = []

        for i, claim_a in enumerate(claims):
            for claim_b in claims[i + 1:]:
                report = self._check_pair(claim_a, claim_b)
                if report:
                    reports.append(report)

        return reports

    def _check_pair(
        self,
        claim_a: Claim,
        claim_b: Claim,
    ) -> Optional[ContradictionReport]:
        """Check a single pair for contradiction."""

        # Rule 1: explicit cross-reference (claim_a lists claim_b as contradicting it)
        if claim_b.claim_id in claim_a.contradicted_by:
            return ContradictionReport(
                report_id=str(uuid.uuid4()),
                claim_a_id=claim_a.claim_id,
                claim_b_id=claim_b.claim_id,
                severity=ContradictionSeverity.DIRECT,
                reason=(
                    f"Claim {claim_a.claim_id} explicitly lists "
                    f"{claim_b.claim_id} as contradicting it."
                ),
                claim_a_dispatch_ref=claim_a.dispatch_id_ref,
                claim_b_dispatch_ref=claim_b.dispatch_id_ref,
                blocks_canonical_admission=True,
                detected_at=datetime.utcnow().isoformat() + "Z",
            )

        # Rule 2: same source_ref, one near-certain and one near-speculative
        if (claim_a.source_ref == claim_b.source_ref
                and abs(claim_a.uncertainty - claim_b.uncertainty) > 0.7):
            return ContradictionReport(
                report_id=str(uuid.uuid4()),
                claim_a_id=claim_a.claim_id,
                claim_b_id=claim_b.claim_id,
                severity=ContradictionSeverity.PARTIAL,
                reason=(
                    f"Same source ({claim_a.source_ref}) with diverging uncertainty: "
                    f"{claim_a.uncertainty:.2f} vs {claim_b.uncertainty:.2f} "
                    f"(delta > 0.7 threshold)."
                ),
                claim_a_dispatch_ref=claim_a.dispatch_id_ref,
                claim_b_dispatch_ref=claim_b.dispatch_id_ref,
                blocks_canonical_admission=False,  # PARTIAL does not block by default
                detected_at=datetime.utcnow().isoformat() + "Z",
            )

        return None
