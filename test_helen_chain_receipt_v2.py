"""
Tests for HELEN_CHAIN_RECEIPT_V2 — Governed Worker Handoff Under Circulation Law

Constitutional proof targets:
1. Authority is inferred from WorkerType — not claimable by caller
2. THINK workers may only TRACE_WRITE or NONE — any other effect = CONSTITUTIONAL_VIOLATION
3. TEMPLE workers may not write anything — any effect = DISPATCH_LINEAGE_VIOLATION
4. CANONICAL_WRITE from non-KERNEL = DISPATCH_LINEAGE_VIOLATION (CRITICAL, blocking)
5. GOVERNED_MUTATION from non-KERNEL = DISPATCH_LINEAGE_VIOLATION (CRITICAL, blocking)
6. Missing dispatch_id_ref = MISSING_DISPATCH_REF (CRITICAL, blocking)
7. KERNEL workers may CANONICAL_WRITE and GOVERNED_MUTATION without violation
8. Receipt hash is deterministic (same content → same hash)
9. Receipt hash excludes run metadata (receipt_id, timestamp)
10. Violations are detected at emission time (not post-hoc)
11. validate_chain_integrity() correctly counts violations and derives verdict
12. A clean batch → "clean" verdict
13. Any blocking violation → "violated" verdict
"""

import pytest
from helen_chain_receipt_v2 import (
    ChainReceiptBuilderV2, WorkerType, HandoffEffect, ChainStatus,
    ViolationSeverity, hash_chain_receipt
)


# ===========================================================================
# TEST CLASS 1: AUTHORITY INFERENCE
# ===========================================================================

class TestAuthorityInference:
    """Authority is structural — inferred from WorkerType, not claimed."""

    def setup_method(self):
        self.builder = ChainReceiptBuilderV2()

    def test_kernel_worker_is_sovereign(self):
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="kernel.reducer", from_worker_type=WorkerType.KERNEL,
            to_worker_id="kernel.state_updater", to_worker_type=WorkerType.KERNEL,
            reason="promotion_admitted",
        )
        assert receipt.from_worker_authority == "sovereign"

    def test_skill_worker_is_non_sovereign(self):
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="skill.audit", from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.formatter", to_worker_type=WorkerType.AGENT,
            reason="audit_formatting",
        )
        assert receipt.from_worker_authority == "non_sovereign"

    def test_agent_worker_is_non_sovereign(self):
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="agent.formatter", from_worker_type=WorkerType.AGENT,
            to_worker_id="skill.output", to_worker_type=WorkerType.SKILL,
            reason="format_pass",
        )
        assert receipt.from_worker_authority == "non_sovereign"

    def test_think_worker_is_non_sovereign(self):
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="think.decomposer", from_worker_type=WorkerType.THINK,
            to_worker_id="skill.extractor", to_worker_type=WorkerType.SKILL,
            reason="route_preparation",
            handoff_effect=HandoffEffect.TRACE_WRITE,
        )
        assert receipt.from_worker_authority == "non_sovereign"

    def test_temple_worker_is_exploratory(self):
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="temple.v1", from_worker_type=WorkerType.TEMPLE,
            to_worker_id="kernel.mayor", to_worker_type=WorkerType.KERNEL,
            reason="transmutation_request",
            handoff_effect=HandoffEffect.NONE,
        )
        assert receipt.from_worker_authority == "exploratory"


# ===========================================================================
# TEST CLASS 2: THINK WORKER CONSTITUTIONAL INVARIANT
# ===========================================================================

class TestThinkWorkerInvariant:
    """THINK workers may only emit TRACE_WRITE or NONE. All else = CONSTITUTIONAL_VIOLATION."""

    def setup_method(self):
        self.builder = ChainReceiptBuilderV2()

    def test_think_trace_write_is_clean(self):
        """THINK + TRACE_WRITE → no violations."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="think.decomposer", from_worker_type=WorkerType.THINK,
            to_worker_id="skill.extractor", to_worker_type=WorkerType.SKILL,
            reason="preparation trace",
            handoff_effect=HandoffEffect.TRACE_WRITE,
        )
        assert receipt.chain_status == ChainStatus.CLEAN
        assert receipt.is_clean

    def test_think_none_effect_is_clean(self):
        """THINK + NONE → no violations."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="think.decomposer", from_worker_type=WorkerType.THINK,
            to_worker_id="skill.extractor", to_worker_type=WorkerType.SKILL,
            reason="pass-through",
            handoff_effect=HandoffEffect.NONE,
        )
        assert receipt.is_clean

    def test_think_canonical_write_is_constitutional_violation(self):
        """THINK attempting CANONICAL_WRITE → CONSTITUTIONAL_VIOLATION (CRITICAL)."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="think.rogue", from_worker_type=WorkerType.THINK,
            to_worker_id="knowledge.store", to_worker_type=WorkerType.SKILL,
            reason="attempting canonical write",
            handoff_effect=HandoffEffect.CANONICAL_WRITE,
        )
        assert receipt.chain_status == ChainStatus.CONSTITUTIONAL_VIOLATION
        assert receipt.has_blocking_violation
        assert any(
            v.violation_type == ChainStatus.CONSTITUTIONAL_VIOLATION
            for v in receipt.violations
        )

    def test_think_candidate_write_is_constitutional_violation(self):
        """THINK attempting CANDIDATE_WRITE → CONSTITUTIONAL_VIOLATION."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="think.overreacher", from_worker_type=WorkerType.THINK,
            to_worker_id="skill.compiler", to_worker_type=WorkerType.SKILL,
            reason="overreach attempt",
            handoff_effect=HandoffEffect.CANDIDATE_WRITE,
        )
        assert receipt.chain_status == ChainStatus.CONSTITUTIONAL_VIOLATION
        assert receipt.has_blocking_violation

    def test_think_governed_mutation_is_constitutional_violation(self):
        """THINK attempting GOVERNED_MUTATION → both CONSTITUTIONAL and LINEAGE violations."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="think.sovereign_impersonator", from_worker_type=WorkerType.THINK,
            to_worker_id="kernel.state", to_worker_type=WorkerType.KERNEL,
            reason="impersonation attempt",
            handoff_effect=HandoffEffect.GOVERNED_MUTATION,
        )
        assert receipt.has_blocking_violation
        # Must detect CONSTITUTIONAL_VIOLATION (THINK beyond trace)
        violation_types = {v.violation_type for v in receipt.violations}
        assert ChainStatus.CONSTITUTIONAL_VIOLATION in violation_types


# ===========================================================================
# TEST CLASS 3: TEMPLE WORKER NON-WRITE LAW
# ===========================================================================

class TestTempleWorkerNonWrite:
    """TEMPLE workers may not write anything."""

    def setup_method(self):
        self.builder = ChainReceiptBuilderV2()

    def test_temple_none_is_clean(self):
        """TEMPLE + NONE → no violations."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="temple.explorer", from_worker_type=WorkerType.TEMPLE,
            to_worker_id="kernel.mayor", to_worker_type=WorkerType.KERNEL,
            reason="transmutation to mayor gate",
            handoff_effect=HandoffEffect.NONE,
        )
        assert receipt.is_clean

    def test_temple_candidate_write_is_violation(self):
        """TEMPLE attempting CANDIDATE_WRITE → DISPATCH_LINEAGE_VIOLATION."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="temple.overreacher", from_worker_type=WorkerType.TEMPLE,
            to_worker_id="knowledge.store", to_worker_type=WorkerType.SKILL,
            reason="temple attempting write",
            handoff_effect=HandoffEffect.CANDIDATE_WRITE,
        )
        assert receipt.has_blocking_violation

    def test_temple_canonical_write_is_violation(self):
        """TEMPLE + CANONICAL_WRITE → DISPATCH_LINEAGE_VIOLATION."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="temple.canon_seeker", from_worker_type=WorkerType.TEMPLE,
            to_worker_id="kernel.reducer", to_worker_type=WorkerType.KERNEL,
            reason="temple cannot canonicalize",
            handoff_effect=HandoffEffect.CANONICAL_WRITE,
        )
        assert receipt.has_blocking_violation


# ===========================================================================
# TEST CLASS 4: CANONICAL AND GOVERNED STATE LAW
# ===========================================================================

class TestCanonicalAndGovernedStateLaw:
    """Only KERNEL workers may CANONICAL_WRITE or GOVERNED_MUTATION."""

    def setup_method(self):
        self.builder = ChainReceiptBuilderV2()

    def test_kernel_canonical_write_is_clean(self):
        """KERNEL + CANONICAL_WRITE → no violations."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="kernel.reducer", from_worker_type=WorkerType.KERNEL,
            to_worker_id="knowledge.canonical", to_worker_type=WorkerType.SKILL,
            reason="reducer-admitted canonical write",
            handoff_effect=HandoffEffect.CANONICAL_WRITE,
        )
        assert receipt.is_clean

    def test_kernel_governed_mutation_is_clean(self):
        """KERNEL + GOVERNED_MUTATION → no violations."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="kernel.state_updater", from_worker_type=WorkerType.KERNEL,
            to_worker_id="ledger.appender", to_worker_type=WorkerType.KERNEL,
            reason="state mutation after reducer admission",
            handoff_effect=HandoffEffect.GOVERNED_MUTATION,
        )
        assert receipt.is_clean

    def test_skill_canonical_write_is_lineage_violation(self):
        """SKILL + CANONICAL_WRITE → DISPATCH_LINEAGE_VIOLATION (CRITICAL)."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="skill.rogue", from_worker_type=WorkerType.SKILL,
            to_worker_id="knowledge.canonical", to_worker_type=WorkerType.SKILL,
            reason="skill attempting canonical write",
            handoff_effect=HandoffEffect.CANONICAL_WRITE,
        )
        assert receipt.has_blocking_violation
        violation_types = {v.violation_type for v in receipt.violations}
        assert ChainStatus.DISPATCH_LINEAGE_VIOLATION in violation_types

    def test_agent_governed_mutation_is_lineage_violation(self):
        """AGENT + GOVERNED_MUTATION → DISPATCH_LINEAGE_VIOLATION (CRITICAL)."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="agent.formatter", from_worker_type=WorkerType.AGENT,
            to_worker_id="kernel.state", to_worker_type=WorkerType.KERNEL,
            reason="agent attempting governed mutation",
            handoff_effect=HandoffEffect.GOVERNED_MUTATION,
        )
        assert receipt.has_blocking_violation

    def test_skill_candidate_write_is_clean(self):
        """SKILL + CANDIDATE_WRITE → clean (allowed for non-sovereign workers)."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="skill.compiler", from_worker_type=WorkerType.SKILL,
            to_worker_id="knowledge.candidates", to_worker_type=WorkerType.SKILL,
            reason="candidate proposal",
            handoff_effect=HandoffEffect.CANDIDATE_WRITE,
        )
        assert receipt.is_clean


# ===========================================================================
# TEST CLASS 5: LINEAGE LAW (dispatch_id_ref)
# ===========================================================================

class TestLineageLaw:
    """Every receipt must have a dispatch_id_ref. No orphan handoffs."""

    def setup_method(self):
        self.builder = ChainReceiptBuilderV2()

    def test_missing_dispatch_ref_is_critical(self):
        """Empty dispatch_id_ref → MISSING_DISPATCH_REF violation (CRITICAL)."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="",
            from_worker_id="skill.orphan", from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.orphan", to_worker_type=WorkerType.AGENT,
            reason="orphan handoff",
        )
        assert receipt.has_blocking_violation
        violation_types = {v.violation_type for v in receipt.violations}
        assert ChainStatus.MISSING_DISPATCH_REF in violation_types

    def test_valid_dispatch_ref_is_clean(self):
        """Valid dispatch_id_ref → no lineage violation."""
        receipt = self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_abc_001",
            from_worker_id="skill.auditor", from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.formatter", to_worker_type=WorkerType.AGENT,
            reason="audit formatting",
        )
        assert receipt.chain_status == ChainStatus.CLEAN


# ===========================================================================
# TEST CLASS 6: DETERMINISM
# ===========================================================================

class TestChainReceiptDeterminism:
    """Receipt hash must be deterministic — same content → same hash."""

    def setup_method(self):
        self.builder = ChainReceiptBuilderV2()

    def test_same_content_same_hash(self):
        """10 runs with same content → 1 unique hash."""
        hashes = set()
        for _ in range(10):
            receipt = self.builder.emit(
                session_id="s_hash",
                dispatch_id_ref="disp_hash_001",
                from_worker_id="skill.extractor",
                from_worker_type=WorkerType.SKILL,
                to_worker_id="agent.formatter",
                to_worker_type=WorkerType.AGENT,
                reason="stable handoff",
                handoff_effect=HandoffEffect.DERIVED_WRITE,
            )
            hashes.add(receipt.receipt_hash)
        assert len(hashes) == 1, "DRIFT: receipt_hash not deterministic"

    def test_hash_excludes_run_metadata(self):
        """Different receipt_id + timestamp, same semantic content → same hash."""
        common = dict(
            session_id="s_meta",
            dispatch_id_ref="disp_meta_001",
            from_worker_id="skill.meta",
            from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.meta",
            to_worker_type=WorkerType.AGENT,
            reason="metadata exclusion test",
        )
        r1 = self.builder.emit(**common)
        r2 = self.builder.emit(**common)
        assert r1.receipt_id != r2.receipt_id  # Different run IDs
        assert r1.receipt_hash == r2.receipt_hash  # Same semantic hash

    def test_different_content_different_hash(self):
        """Different handoff effect → different hash."""
        r1 = self.builder.emit(
            session_id="s1", dispatch_id_ref="d1",
            from_worker_id="skill.x", from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.y", to_worker_type=WorkerType.AGENT,
            handoff_effect=HandoffEffect.CANDIDATE_WRITE,
        )
        r2 = self.builder.emit(
            session_id="s1", dispatch_id_ref="d1",
            from_worker_id="skill.x", from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.y", to_worker_type=WorkerType.AGENT,
            handoff_effect=HandoffEffect.DERIVED_WRITE,
        )
        assert r1.receipt_hash != r2.receipt_hash

    def test_violation_included_in_hash(self):
        """A receipt with violations has a different hash than a clean receipt."""
        clean = self.builder.emit(
            session_id="s1", dispatch_id_ref="d1",
            from_worker_id="kernel.reducer", from_worker_type=WorkerType.KERNEL,
            to_worker_id="knowledge.store", to_worker_type=WorkerType.SKILL,
            handoff_effect=HandoffEffect.CANONICAL_WRITE,
        )
        violated = self.builder.emit(
            session_id="s1", dispatch_id_ref="d1",
            from_worker_id="skill.rogue", from_worker_type=WorkerType.SKILL,
            to_worker_id="knowledge.store", to_worker_type=WorkerType.SKILL,
            handoff_effect=HandoffEffect.CANONICAL_WRITE,
        )
        assert clean.receipt_hash != violated.receipt_hash


# ===========================================================================
# TEST CLASS 7: BATCH VALIDATION
# ===========================================================================

class TestBatchValidation:
    """validate_chain_integrity() correctly counts and classifies violations."""

    def setup_method(self):
        self.builder = ChainReceiptBuilderV2()

    def _clean_receipt(self):
        return self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_001",
            from_worker_id="skill.auditor", from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.formatter", to_worker_type=WorkerType.AGENT,
            reason="clean handoff",
        )

    def _canonical_violation_receipt(self):
        return self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_002",
            from_worker_id="skill.rogue", from_worker_type=WorkerType.SKILL,
            to_worker_id="knowledge.canon", to_worker_type=WorkerType.SKILL,
            reason="illegal canonical write",
            handoff_effect=HandoffEffect.CANONICAL_WRITE,
        )

    def _think_violation_receipt(self):
        return self.builder.emit(
            session_id="s1", dispatch_id_ref="disp_003",
            from_worker_id="think.overreacher", from_worker_type=WorkerType.THINK,
            to_worker_id="knowledge.store", to_worker_type=WorkerType.SKILL,
            reason="think overreach",
            handoff_effect=HandoffEffect.CANDIDATE_WRITE,
        )

    def test_clean_batch_verdict(self):
        """All clean receipts → verdict = clean."""
        receipts = [self._clean_receipt() for _ in range(3)]
        report = self.builder.validate_chain_integrity(receipts)
        assert report["verdict"] == "clean"
        assert report["violation_count"] == 0
        assert report["blocking_count"] == 0

    def test_canonical_violation_detected(self):
        """SKILL canonical write → canonical_mutations_outside_kernel += 1, verdict = violated."""
        receipts = [self._clean_receipt(), self._canonical_violation_receipt()]
        report = self.builder.validate_chain_integrity(receipts)
        assert report["verdict"] == "violated"
        assert report["canonical_mutations_outside_kernel"] == 1
        assert report["blocking_count"] == 1

    def test_constitutional_violation_detected(self):
        """THINK writing beyond trace → constitutional_violations += 1, verdict = violated."""
        receipts = [self._clean_receipt(), self._think_violation_receipt()]
        report = self.builder.validate_chain_integrity(receipts)
        assert report["verdict"] == "violated"
        assert report["constitutional_violations"] >= 1

    def test_mixed_batch_counts_correctly(self):
        """Mixed batch: 2 clean + 1 canonical + 1 think → correct counts."""
        receipts = [
            self._clean_receipt(),
            self._clean_receipt(),
            self._canonical_violation_receipt(),
            self._think_violation_receipt(),
        ]
        report = self.builder.validate_chain_integrity(receipts)
        assert report["total_receipts"] == 4
        assert report["receipts_clean"] == 2
        assert report["receipts_violated"] == 2
        assert report["verdict"] == "violated"

    def test_empty_batch_is_clean(self):
        """Empty batch → clean verdict."""
        report = self.builder.validate_chain_integrity([])
        assert report["verdict"] == "clean"
        assert report["total_receipts"] == 0
