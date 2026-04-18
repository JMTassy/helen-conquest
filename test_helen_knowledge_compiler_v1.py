"""
Tests for HELEN_KNOWLEDGE_COMPILER_V1

Constitutional proof targets (32 tests):

Claim schema invariants:
  1.  Claim rejects empty content
  2.  Claim rejects missing dispatch_id_ref
  3.  Claim rejects uncertainty below 0.0
  4.  Claim rejects uncertainty above 1.0
  5.  Claim accepts uncertainty at exact bounds (0.0 and 1.0)
  6.  Claim hash is computed at construction

Source ingestion invariants:
  7.  SourceIngestionPacket rejects empty raw_content
  8.  SourceIngestionPacket rejects missing dispatch_id_ref
  9.  SourceIngestionPacket computes ingestion_hash deterministically
  10. Same raw_content → same ingestion_hash (deduplication enabler)

Claim status promotion:
  11. Demotion is not permitted
  12. Status skipping is not permitted (speculative → canonical)
  13. Valid single-step promotion is allowed
  14. Deprecation is always allowed from any status
  15. Uncertainty ceiling: high-uncertainty claim cannot reach canonical
  16. Uncertainty ceiling: exact boundary (0.2 → canonical allowed, 0.21 → not)

Admission gate invariants:
  17. ADMITTED_CANONICAL requires chain_receipt_ref
  18. ADMITTED_CANONICAL without chain_receipt_ref raises ValueError
  19. ADMITTED_PROVISIONAL does not require chain_receipt_ref
  20. AdmissionResult rejects unregistered reason codes
  21. is_admitted property: True for canonical and provisional
  22. is_canonical property: True only for canonical

Contradiction detection:
  23. Explicit contradicted_by cross-reference → DIRECT ContradictionReport
  24. Same source, diverging uncertainty > 0.7 → PARTIAL report
  25. DIRECT contradiction blocks canonical admission
  26. PARTIAL contradiction does NOT block by default

Compiler stage sequencing:
  27. Valid sequential transition accepted
  28. Stage skip violation rejected (INGEST → AUDIT)
  29. REJECTED terminal allowed from any stage
  30. Stage receipt hash is deterministic (excludes run metadata)

Compiler determinism:
  31. Same claim content → same claim_hash across runs
  32. Different claim content → different claim_hash
"""

import pytest
import uuid
from helen_knowledge_compiler_v1 import (
    # Schemas
    Claim, ClaimStatus, ClaimBuilder,
    SourceIngestionPacket, SourceIngestionBuilder, SourceType,
    ContradictionReport, ContradictionSeverity, ContradictionDetector,
    CompilerStageReceipt, CompilerStage,
    AdmissionResult, AdmissionVerdict,
    # Utilities
    hash_claim, validate_compiler_reason_codes,
    UncertaintyThreshold,
    SourceIngestionRouter,
    COMPILER_REASON_CODES,
)


# ===========================================================================
# FIXTURES / HELPERS
# ===========================================================================

def make_claim(
    content="The system preserves determinism under identical inputs.",
    source_ref="autoresearch_batch_run_001",
    uncertainty=0.05,
    status=ClaimStatus.CANDIDATE,
    dispatch_id_ref="disp_skill_001",
    compiler_stage=CompilerStage.EXTRACT,
    contradicted_by=None,
) -> Claim:
    return Claim(
        claim_id=str(uuid.uuid4()),
        content=content,
        source_ref=source_ref,
        uncertainty=uncertainty,
        status=status,
        dispatch_id_ref=dispatch_id_ref,
        compiler_stage=compiler_stage,
        contradicted_by=contradicted_by or [],
        lineage=[dispatch_id_ref],
    )


def make_stage_receipt(
    from_stage=CompilerStage.INGEST,
    to_stage=CompilerStage.EXTRACT,
    dispatch_id_ref="disp_skill_001",
    claim_ids=None,
    stage_verdict="pass",
    chain_receipt_ref=None,
) -> CompilerStageReceipt:
    return CompilerStageReceipt(
        receipt_id=str(uuid.uuid4()),
        from_stage=from_stage,
        to_stage=to_stage,
        claim_ids=claim_ids or ["claim_001"],
        dispatch_id_ref=dispatch_id_ref,
        chain_receipt_ref=chain_receipt_ref,
        stage_verdict=stage_verdict,
    )


def make_admission_result(
    verdict=AdmissionVerdict.ADMITTED_PROVISIONAL,
    final_status=ClaimStatus.PROVISIONAL,
    chain_receipt_ref=None,
    reason_codes=None,
    blocking_violations=0,
) -> AdmissionResult:
    if reason_codes is None:
        reason_codes = ["claim_admitted_provisional"]
    return AdmissionResult(
        result_id=str(uuid.uuid4()),
        claim_id="claim_001",
        claim_hash="sha256:abc123",
        dispatch_id_ref="disp_kernel_001",
        chain_receipt_ref=chain_receipt_ref,
        verdict=verdict,
        final_status=final_status,
        reason_codes=reason_codes,
        blocking_violations=blocking_violations,
    )


# ===========================================================================
# TEST CLASS 1: CLAIM SCHEMA INVARIANTS
# ===========================================================================

class TestClaimSchemaInvariants:
    """6 tests proving Claim structural invariants."""

    def test_claim_rejects_empty_content(self):
        """Empty content raises ValueError."""
        with pytest.raises(ValueError, match="content must not be empty"):
            Claim(
                claim_id="c1",
                content="",
                source_ref="src",
                uncertainty=0.1,
                status=ClaimStatus.CANDIDATE,
                dispatch_id_ref="disp_001",
                compiler_stage=CompilerStage.EXTRACT,
            )

    def test_claim_rejects_whitespace_content(self):
        """Whitespace-only content raises ValueError."""
        with pytest.raises(ValueError, match="content must not be empty"):
            Claim(
                claim_id="c1",
                content="   ",
                source_ref="src",
                uncertainty=0.1,
                status=ClaimStatus.CANDIDATE,
                dispatch_id_ref="disp_001",
                compiler_stage=CompilerStage.EXTRACT,
            )

    def test_claim_rejects_missing_dispatch_id_ref(self):
        """Empty dispatch_id_ref raises ValueError."""
        with pytest.raises(ValueError, match="dispatch_id_ref is required"):
            Claim(
                claim_id="c1",
                content="valid content",
                source_ref="src",
                uncertainty=0.1,
                status=ClaimStatus.CANDIDATE,
                dispatch_id_ref="",
                compiler_stage=CompilerStage.EXTRACT,
            )

    def test_claim_rejects_uncertainty_below_zero(self):
        """Uncertainty < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="uncertainty must be in"):
            make_claim(uncertainty=-0.01)

    def test_claim_rejects_uncertainty_above_one(self):
        """Uncertainty > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="uncertainty must be in"):
            make_claim(uncertainty=1.001)

    def test_claim_accepts_exact_boundary_uncertainties(self):
        """Uncertainty = 0.0 and 1.0 are both valid."""
        c_certain = make_claim(uncertainty=0.0)
        assert c_certain.uncertainty == 0.0
        c_speculative = make_claim(uncertainty=1.0)
        assert c_speculative.uncertainty == 1.0

    def test_claim_hash_computed_at_construction(self):
        """Claim hash is set immediately after construction."""
        claim = make_claim()
        assert claim.claim_hash is not None
        assert claim.claim_hash.startswith("sha256:")


# ===========================================================================
# TEST CLASS 2: SOURCE INGESTION INVARIANTS
# ===========================================================================

class TestSourceIngestionInvariants:
    """4 tests proving SourceIngestionPacket invariants."""

    def test_packet_rejects_empty_content(self):
        """Empty raw_content raises ValueError."""
        with pytest.raises(ValueError, match="raw_content must not be empty"):
            SourceIngestionPacket(
                source_id="s1",
                source_type=SourceType.DOCUMENT,
                raw_content="",
                dispatch_id_ref="disp_skill_001",
            )

    def test_packet_rejects_missing_dispatch_ref(self):
        """Empty dispatch_id_ref raises ValueError."""
        with pytest.raises(ValueError, match="dispatch_id_ref is required"):
            SourceIngestionPacket(
                source_id="s1",
                source_type=SourceType.DOCUMENT,
                raw_content="valid content",
                dispatch_id_ref="",
            )

    def test_ingestion_hash_computed_at_construction(self):
        """ingestion_hash is set after construction."""
        packet = SourceIngestionPacket(
            source_id="s1",
            source_type=SourceType.DOCUMENT,
            raw_content="some content",
            dispatch_id_ref="disp_skill_001",
        )
        assert packet.ingestion_hash is not None
        assert packet.ingestion_hash.startswith("sha256:")

    def test_same_content_same_ingestion_hash(self):
        """Same raw_content → same ingestion_hash (deduplication enabler)."""
        content = "The reducer is the only path to governed state mutations."
        p1 = SourceIngestionPacket(
            source_id="s1",
            source_type=SourceType.DOCUMENT,
            raw_content=content,
            dispatch_id_ref="disp_001",
        )
        p2 = SourceIngestionPacket(
            source_id="s2",  # Different run metadata
            source_type=SourceType.RESEARCH_RESULT,
            raw_content=content,
            dispatch_id_ref="disp_002",
        )
        assert p1.ingestion_hash == p2.ingestion_hash


# ===========================================================================
# TEST CLASS 3: CLAIM STATUS PROMOTION
# ===========================================================================

class TestClaimStatusPromotion:
    """6 tests proving the promotion law."""

    def setup_method(self):
        self.builder = ClaimBuilder()

    def test_demotion_not_permitted(self):
        """Promoting from provisional back to candidate is not allowed."""
        claim = make_claim(status=ClaimStatus.PROVISIONAL, uncertainty=0.1)
        allowed, reason = self.builder.can_promote(claim, ClaimStatus.CANDIDATE)
        assert allowed is False
        assert "demotion" in reason

    def test_status_skip_not_permitted(self):
        """Jumping from speculative directly to canonical is not allowed."""
        claim = make_claim(status=ClaimStatus.SPECULATIVE, uncertainty=0.05)
        allowed, reason = self.builder.can_promote(claim, ClaimStatus.CANONICAL)
        assert allowed is False
        assert "skip" in reason

    def test_valid_single_step_promotion_allowed(self):
        """candidate → provisional is one step and is allowed."""
        claim = make_claim(status=ClaimStatus.CANDIDATE, uncertainty=0.1)
        allowed, reason = self.builder.can_promote(claim, ClaimStatus.PROVISIONAL)
        assert allowed is True

    def test_deprecation_always_allowed(self):
        """Deprecation is always allowed from any status."""
        for status in [ClaimStatus.SPECULATIVE, ClaimStatus.CANDIDATE,
                       ClaimStatus.PROVISIONAL, ClaimStatus.CANONICAL]:
            claim = make_claim(status=status, uncertainty=0.05)
            allowed, reason = self.builder.can_promote(claim, ClaimStatus.DEPRECATED)
            assert allowed is True, f"Expected deprecation from {status.value} to be allowed"

    def test_high_uncertainty_cannot_reach_canonical(self):
        """Claim with uncertainty=0.8 cannot be promoted to canonical."""
        claim = make_claim(status=ClaimStatus.PROVISIONAL, uncertainty=0.8)
        allowed, reason = self.builder.can_promote(claim, ClaimStatus.CANONICAL)
        assert allowed is False
        assert "uncertainty" in reason

    def test_uncertainty_ceiling_boundary(self):
        """uncertainty=0.2 → canonical allowed; uncertainty=0.21 → not."""
        # At boundary (0.2 → canonical ceiling)
        claim_at_boundary = make_claim(status=ClaimStatus.PROVISIONAL, uncertainty=0.2)
        allowed, _ = self.builder.can_promote(claim_at_boundary, ClaimStatus.CANONICAL)
        assert allowed is True

        # Just above boundary
        claim_above = make_claim(status=ClaimStatus.PROVISIONAL, uncertainty=0.21)
        allowed, reason = self.builder.can_promote(claim_above, ClaimStatus.CANONICAL)
        assert allowed is False
        assert "uncertainty" in reason


# ===========================================================================
# TEST CLASS 4: ADMISSION GATE INVARIANTS
# ===========================================================================

class TestAdmissionGateInvariants:
    """6 tests proving canonical admission requirements."""

    def test_canonical_admission_requires_chain_receipt_ref(self):
        """ADMITTED_CANONICAL without chain_receipt_ref raises ValueError."""
        with pytest.raises(ValueError, match="chain_receipt_ref is required"):
            AdmissionResult(
                result_id="r1",
                claim_id="c1",
                claim_hash="sha256:abc",
                dispatch_id_ref="disp_kernel_001",
                chain_receipt_ref=None,  # Missing — should raise
                verdict=AdmissionVerdict.ADMITTED_CANONICAL,
                final_status=ClaimStatus.CANONICAL,
                reason_codes=["claim_admitted_canonical"],
            )

    def test_canonical_admission_with_chain_receipt_succeeds(self):
        """ADMITTED_CANONICAL with chain_receipt_ref is valid."""
        result = AdmissionResult(
            result_id="r1",
            claim_id="c1",
            claim_hash="sha256:abc",
            dispatch_id_ref="disp_kernel_001",
            chain_receipt_ref="chain_receipt_v2_001",
            verdict=AdmissionVerdict.ADMITTED_CANONICAL,
            final_status=ClaimStatus.CANONICAL,
            reason_codes=["claim_admitted_canonical"],
        )
        assert result.is_canonical is True
        assert result.is_admitted is True

    def test_provisional_admission_does_not_require_chain_receipt(self):
        """ADMITTED_PROVISIONAL without chain_receipt_ref is valid."""
        result = make_admission_result(
            verdict=AdmissionVerdict.ADMITTED_PROVISIONAL,
            final_status=ClaimStatus.PROVISIONAL,
            chain_receipt_ref=None,
        )
        assert result.is_admitted is True
        assert result.is_canonical is False

    def test_unregistered_reason_codes_rejected(self):
        """AdmissionResult with unregistered reason codes raises ValueError."""
        with pytest.raises(ValueError, match="unregistered reason codes"):
            make_admission_result(reason_codes=["ad_hoc_reason_not_in_registry"])

    def test_is_admitted_true_for_canonical_and_provisional(self):
        """is_admitted is True for both ADMITTED_CANONICAL and ADMITTED_PROVISIONAL."""
        provisional = make_admission_result(
            verdict=AdmissionVerdict.ADMITTED_PROVISIONAL,
            final_status=ClaimStatus.PROVISIONAL,
        )
        canonical = AdmissionResult(
            result_id="r2",
            claim_id="c2",
            claim_hash="sha256:def",
            dispatch_id_ref="disp_kernel_002",
            chain_receipt_ref="chain_receipt_v2_002",
            verdict=AdmissionVerdict.ADMITTED_CANONICAL,
            final_status=ClaimStatus.CANONICAL,
            reason_codes=["claim_admitted_canonical"],
        )
        assert provisional.is_admitted is True
        assert canonical.is_admitted is True

    def test_is_canonical_true_only_for_canonical(self):
        """is_canonical is True only for ADMITTED_CANONICAL."""
        provisional = make_admission_result(
            verdict=AdmissionVerdict.ADMITTED_PROVISIONAL,
            final_status=ClaimStatus.PROVISIONAL,
        )
        rejected = make_admission_result(
            verdict=AdmissionVerdict.REJECTED_AUDIT_FAILURE,
            final_status=ClaimStatus.CANDIDATE,
            reason_codes=["claim_rejected_audit_failure"],
        )
        assert provisional.is_canonical is False
        assert rejected.is_canonical is False


# ===========================================================================
# TEST CLASS 5: CONTRADICTION DETECTION
# ===========================================================================

class TestContradictionDetection:
    """4 tests proving contradiction surface law."""

    def setup_method(self):
        self.detector = ContradictionDetector()

    def test_explicit_cross_reference_produces_direct_contradiction(self):
        """Claim with contradicted_by reference → DIRECT ContradictionReport."""
        claim_a = make_claim(
            content="The system always converges.",
            dispatch_id_ref="disp_001",
        )
        claim_b = make_claim(
            content="The system may diverge under load.",
            dispatch_id_ref="disp_002",
        )
        # Mark claim_a as contradicted by claim_b
        claim_a.contradicted_by = [claim_b.claim_id]

        reports = self.detector.detect_structural_contradictions([claim_a, claim_b])
        direct_reports = [r for r in reports if r.severity == ContradictionSeverity.DIRECT]
        assert len(direct_reports) >= 1
        assert direct_reports[0].blocks_canonical_admission is True

    def test_same_source_diverging_uncertainty_produces_partial_contradiction(self):
        """Same source_ref with uncertainty delta > 0.7 → PARTIAL report."""
        claim_certain = make_claim(
            content="Ledger entries are append-only.",
            source_ref="shared_source",
            uncertainty=0.01,
            dispatch_id_ref="disp_001",
        )
        claim_uncertain = make_claim(
            content="Ledger entries might be mutable.",
            source_ref="shared_source",
            uncertainty=0.9,
            dispatch_id_ref="disp_002",
        )
        reports = self.detector.detect_structural_contradictions([claim_certain, claim_uncertain])
        partial_reports = [r for r in reports if r.severity == ContradictionSeverity.PARTIAL]
        assert len(partial_reports) >= 1

    def test_direct_contradiction_blocks_canonical_admission(self):
        """DIRECT ContradictionReport has blocks_canonical_admission=True."""
        claim_a = make_claim(content="X is true.", dispatch_id_ref="disp_001")
        claim_b = make_claim(content="X is false.", dispatch_id_ref="disp_002")
        claim_a.contradicted_by = [claim_b.claim_id]

        reports = self.detector.detect_structural_contradictions([claim_a, claim_b])
        for r in reports:
            if r.severity == ContradictionSeverity.DIRECT:
                assert r.blocks_canonical_admission is True

    def test_partial_contradiction_does_not_block_by_default(self):
        """PARTIAL ContradictionReport has blocks_canonical_admission=False by default."""
        claim_a = make_claim(
            content="Y is reliable.",
            source_ref="src",
            uncertainty=0.02,
            dispatch_id_ref="disp_001",
        )
        claim_b = make_claim(
            content="Y is unreliable.",
            source_ref="src",
            uncertainty=0.95,
            dispatch_id_ref="disp_002",
        )
        reports = self.detector.detect_structural_contradictions([claim_a, claim_b])
        for r in reports:
            if r.severity == ContradictionSeverity.PARTIAL:
                assert r.blocks_canonical_admission is False


# ===========================================================================
# TEST CLASS 6: COMPILER STAGE SEQUENCING
# ===========================================================================

class TestCompilerStageSequencing:
    """4 tests proving the stage sequence law."""

    def test_valid_sequential_transition_accepted(self):
        """INGEST → EXTRACT is a valid one-step transition."""
        receipt = make_stage_receipt(
            from_stage=CompilerStage.INGEST,
            to_stage=CompilerStage.EXTRACT,
        )
        assert receipt.from_stage == CompilerStage.INGEST
        assert receipt.to_stage == CompilerStage.EXTRACT
        assert receipt.receipt_hash is not None

    def test_stage_skip_violation_rejected(self):
        """INGEST → AUDIT skips EXTRACT and VALIDATE — raises ValueError."""
        with pytest.raises(ValueError, match="Stage sequence violation"):
            CompilerStageReceipt(
                receipt_id="r1",
                from_stage=CompilerStage.INGEST,
                to_stage=CompilerStage.AUDIT,  # Skips EXTRACT and VALIDATE
                claim_ids=["c1"],
                dispatch_id_ref="disp_001",
                chain_receipt_ref=None,
                stage_verdict="pass",
            )

    def test_rejection_terminal_allowed_from_any_stage(self):
        """REJECTED is a valid terminal from any non-terminal stage."""
        for from_stage in [
            CompilerStage.INGEST,
            CompilerStage.EXTRACT,
            CompilerStage.VALIDATE,
            CompilerStage.AUDIT,
        ]:
            receipt = CompilerStageReceipt(
                receipt_id=str(uuid.uuid4()),
                from_stage=from_stage,
                to_stage=CompilerStage.REJECTED,
                claim_ids=["c1"],
                dispatch_id_ref="disp_001",
                chain_receipt_ref=None,
                stage_verdict="fail",
            )
            assert receipt.to_stage == CompilerStage.REJECTED

    def test_stage_receipt_hash_deterministic(self):
        """Same transition + same claims + same dispatch → same receipt_hash."""
        kwargs = dict(
            from_stage=CompilerStage.VALIDATE,
            to_stage=CompilerStage.AUDIT,
            dispatch_id_ref="disp_skill_007",
            claim_ids=["claim_a", "claim_b"],
            stage_verdict="pass",
        )
        r1 = make_stage_receipt(**kwargs)
        r2 = make_stage_receipt(**kwargs)
        assert r1.receipt_hash == r2.receipt_hash


# ===========================================================================
# TEST CLASS 7: COMPILER DETERMINISM
# ===========================================================================

class TestCompilerDeterminism:
    """4 tests proving determinism of the compiler's core hashing."""

    def test_same_claim_content_same_hash(self):
        """Same semantic content → same claim_hash across all runs."""
        kwargs = dict(
            content="The reducer is the only path to governed state mutations.",
            source_ref="helen_os_architecture_v2",
            uncertainty=0.05,
            status=ClaimStatus.CANDIDATE,
            dispatch_id_ref="disp_skill_001",
            compiler_stage=CompilerStage.EXTRACT,
        )
        c1 = make_claim(**kwargs)
        c2 = make_claim(**kwargs)
        # claim_ids are different (UUID) but hash must be the same
        assert c1.claim_id != c2.claim_id
        assert c1.claim_hash == c2.claim_hash

    def test_different_content_different_hash(self):
        """Different content → different claim_hash."""
        c1 = make_claim(content="Claim A: the ledger is append-only.")
        c2 = make_claim(content="Claim B: the reducer is sovereign.")
        assert c1.claim_hash != c2.claim_hash

    def test_claim_hash_excludes_run_metadata(self):
        """
        hash_claim() must produce the same result regardless of
        claim_id and extraction_timestamp (run-specific fields).
        """
        base_kwargs = dict(
            content="Canonical knowledge requires KERNEL chain receipt.",
            source_ref="architecture_v2",
            uncertainty=0.1,
            status=ClaimStatus.CANDIDATE,
            dispatch_id_ref="disp_skill_002",
            compiler_stage=CompilerStage.EXTRACT,
        )
        c1 = Claim(claim_id="run-1-uuid", extraction_timestamp="2026-01-01T00:00:00Z",
                   **base_kwargs)
        c2 = Claim(claim_id="run-2-uuid", extraction_timestamp="2026-12-31T23:59:59Z",
                   **base_kwargs)
        assert c1.claim_hash == c2.claim_hash

    def test_uncertainty_threshold_max_status_is_deterministic(self):
        """
        UncertaintyThreshold.max_status_for_uncertainty() returns consistent results.
        """
        assert UncertaintyThreshold.max_status_for_uncertainty(0.0) == ClaimStatus.CANONICAL
        assert UncertaintyThreshold.max_status_for_uncertainty(0.2) == ClaimStatus.CANONICAL
        assert UncertaintyThreshold.max_status_for_uncertainty(0.21) == ClaimStatus.PROVISIONAL
        assert UncertaintyThreshold.max_status_for_uncertainty(0.6) == ClaimStatus.PROVISIONAL
        assert UncertaintyThreshold.max_status_for_uncertainty(0.61) == ClaimStatus.CANDIDATE
        assert UncertaintyThreshold.max_status_for_uncertainty(1.0) == ClaimStatus.CANDIDATE


# ===========================================================================
# TEST CLASS 8: DISPATCH ROUTING VALIDATION
# ===========================================================================

class TestDispatchRoutingValidation:
    """4 tests proving the routing law enforcement."""

    def setup_method(self):
        self.router = SourceIngestionRouter()

    def test_source_ingest_to_skill_is_valid(self):
        """SOURCE_INGEST → SKILL is the authorized ingest route."""
        dispatch = {"input_type": "SOURCE_INGEST", "primary_route": "SKILL"}
        valid, reason = self.router.validate_ingest_dispatch(dispatch)
        assert valid is True
        assert reason == "ingest_dispatch_valid"

    def test_source_ingest_to_kernel_is_invalid(self):
        """SOURCE_INGEST → KERNEL is not authorized for ingestion."""
        dispatch = {"input_type": "SOURCE_INGEST", "primary_route": "KERNEL"}
        valid, reason = self.router.validate_ingest_dispatch(dispatch)
        assert valid is False
        assert reason == "ingest_dispatch_invalid_route"

    def test_promotion_request_to_kernel_is_valid(self):
        """PROMOTION_REQUEST → KERNEL is the authorized canonical admission route."""
        dispatch = {"input_type": "PROMOTION_REQUEST", "primary_route": "KERNEL"}
        valid, reason = self.router.validate_admission_dispatch(dispatch)
        assert valid is True
        assert reason == "admission_dispatch_valid"

    def test_promotion_request_to_skill_is_invalid(self):
        """PROMOTION_REQUEST → SKILL is not authorized for canonical admission."""
        dispatch = {"input_type": "PROMOTION_REQUEST", "primary_route": "SKILL"}
        valid, reason = self.router.validate_admission_dispatch(dispatch)
        assert valid is False
        assert reason == "admission_dispatch_invalid_route"


# ===========================================================================
# TEST CLASS 9: REASON CODE REGISTRY
# ===========================================================================

class TestReasonCodeRegistry:
    """2 tests proving the reason code invariant."""

    def test_all_compiler_reason_codes_validate(self):
        """All codes in COMPILER_REASON_CODES pass validate_compiler_reason_codes."""
        all_codes = list(COMPILER_REASON_CODES)
        assert validate_compiler_reason_codes(all_codes) is True

    def test_unregistered_code_fails_validation(self):
        """An unregistered code fails validation."""
        assert validate_compiler_reason_codes(["ad_hoc_string_not_in_registry"]) is False
