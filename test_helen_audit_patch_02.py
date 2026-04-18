"""
Tests for KNOWLEDGE_HEALTH_AUDIT_V2_PATCH_02

Constitutional proof targets:
THINK lineage:
  1. ThinkTrace with valid invariants + correct dispatch route → clean
  2. ThinkTrace with broken invariants → THINKING_LINEAGE_VIOLATION (CRITICAL)
  3. ThinkTrace linked to non-THINK dispatch route → THINK_ESCALATION (HIGH, blocking)
  4. ThinkTrace with no dispatch_id_ref → THINK_ESCALATION (CRITICAL)

Chain receipt coupling:
  5. Canonical artifact + clean KERNEL receipt → clean
  6. Canonical artifact with no chain receipt → CHAIN_RECEIPT_MISSING (CRITICAL)
  7. Canonical artifact with non-KERNEL receipt only → CHAIN_RECEIPT_MISSING (CRITICAL)
  8. Provisional artifact with no receipt → CHAIN_RECEIPT_MISSING (MODERATE, non-blocking)
  9. Orphan chain receipt → ORPHAN_CHAIN_RECEIPT (CRITICAL)

THINK→canonical shortcut:
  10. THINK worker in canonical handoff chain with non-trace effect → THINK_TO_CANONICAL_SHORTCUT
  11. THINK worker with TRACE_WRITE in canonical chain → clean (preparation is lawful)

Full audit:
  12. Clean batch (all artifacts + receipts + traces lawful) → clean verdict
  13. Mixed batch → correct violation counts per category
  14. Full audit verdict reflects blocking count
"""

import pytest
from helen_chain_receipt_v2 import (
    ChainReceiptBuilderV2, WorkerType, HandoffEffect, ChainStatus
)
from helen_think_trace_v1 import ThinkTraceBuilder, ThinkTrace
from knowledge_health_audit_v2_patch_02 import (
    ThinkLineageAuditor, ChainReceiptCouplingAuditor, FullLineageAuditor,
    Patch02FindingType
)
from knowledge_health_audit_v2_patch_01 import LineageFindingSeverity


# ===========================================================================
# FIXTURES / HELPERS
# ===========================================================================

def make_think_trace(
    session_id="s1",
    dispatch_id_ref="disp_think_001",
    raw_input_summary="Test preparation",
    **kwargs
) -> ThinkTrace:
    builder = ThinkTraceBuilder()
    return builder.emit(
        session_id=session_id,
        dispatch_id_ref=dispatch_id_ref,
        raw_input_summary=raw_input_summary,
        **kwargs
    )


def make_artifact(artifact_id, canonical_status, dispatch_id_ref, worker_type="kernel"):
    return {
        "artifact_id": artifact_id,
        "canonical_status": canonical_status,
        "dispatch_id_ref": dispatch_id_ref,
        "produced_by_worker_type": worker_type,
    }


def make_kernel_receipt(session_id, dispatch_id_ref, artifact_id=None):
    builder = ChainReceiptBuilderV2()
    return builder.emit(
        session_id=session_id,
        dispatch_id_ref=dispatch_id_ref,
        from_worker_id="kernel.reducer",
        from_worker_type=WorkerType.KERNEL,
        to_worker_id="knowledge.canonical",
        to_worker_type=WorkerType.SKILL,
        reason="reducer-admitted canonical write",
        handoff_effect=HandoffEffect.CANONICAL_WRITE,
    )


def make_skill_receipt(session_id, dispatch_id_ref):
    builder = ChainReceiptBuilderV2()
    return builder.emit(
        session_id=session_id,
        dispatch_id_ref=dispatch_id_ref,
        from_worker_id="skill.compiler",
        from_worker_type=WorkerType.SKILL,
        to_worker_id="agent.formatter",
        to_worker_type=WorkerType.AGENT,
        reason="skill to agent",
        handoff_effect=HandoffEffect.CANDIDATE_WRITE,
    )


def make_think_receipt(session_id, dispatch_id_ref, effect=HandoffEffect.TRACE_WRITE):
    builder = ChainReceiptBuilderV2()
    return builder.emit(
        session_id=session_id,
        dispatch_id_ref=dispatch_id_ref,
        from_worker_id="think.decomposer",
        from_worker_type=WorkerType.THINK,
        to_worker_id="skill.extractor",
        to_worker_type=WorkerType.SKILL,
        reason="preparation trace",
        handoff_effect=effect,
    )


# ===========================================================================
# TEST CLASS 1: THINK LINEAGE AUDITOR
# ===========================================================================

class TestThinkLineageAuditor:

    def setup_method(self):
        self.auditor = ThinkLineageAuditor()

    def test_clean_think_trace_correct_route_is_clean(self):
        """Valid ThinkTrace + THINK route → no findings."""
        trace = make_think_trace()
        findings = self.auditor.audit_trace(trace, dispatch_route="THINK")
        assert findings == []

    def test_clean_think_trace_no_route_provided_is_clean(self):
        """Valid ThinkTrace + no dispatch route provided → no findings."""
        trace = make_think_trace()
        findings = self.auditor.audit_trace(trace, dispatch_route=None)
        assert findings == []

    def test_think_escalation_wrong_dispatch_route(self):
        """ThinkTrace linked to AGENT dispatch route → THINK_ESCALATION."""
        trace = make_think_trace(dispatch_id_ref="disp_agent_001")
        findings = self.auditor.audit_trace(trace, dispatch_route="AGENT")
        assert len(findings) == 1
        assert findings[0].finding_type == Patch02FindingType.THINK_ESCALATION
        assert findings[0].blocking is True

    def test_think_escalation_kernel_dispatch_route(self):
        """ThinkTrace emitted under KERNEL dispatch → THINK_ESCALATION (CRITICAL)."""
        trace = make_think_trace(dispatch_id_ref="disp_kernel_001")
        findings = self.auditor.audit_trace(trace, dispatch_route="KERNEL")
        blocking = [f for f in findings if f.blocking]
        assert len(blocking) >= 1

    def test_think_escalation_missing_dispatch_ref(self):
        """ThinkTrace with empty dispatch_id_ref → THINK_ESCALATION."""
        builder = ThinkTraceBuilder()
        # Manually create a trace then clear the ref
        trace = builder.emit(session_id="s1", dispatch_id_ref="temp", raw_input_summary="test")
        trace.dispatch_id_ref = ""  # Force blank
        findings = self.auditor.audit_trace(trace)
        blocking = [f for f in findings if f.blocking]
        assert len(blocking) >= 1

    def test_batch_audit_clean(self):
        """All valid traces + THINK route → clean verdict."""
        traces = [make_think_trace(dispatch_id_ref=f"disp_{i:03d}") for i in range(3)]
        dispatch_routes = {t.dispatch_id_ref: "THINK" for t in traces}
        report = self.auditor.audit_batch(traces, dispatch_routes)
        assert report["verdict"] == "clean"
        assert report["blocking_count"] == 0

    def test_batch_audit_violated(self):
        """One trace with wrong route → violated verdict."""
        traces = [
            make_think_trace(dispatch_id_ref="disp_ok"),
            make_think_trace(dispatch_id_ref="disp_bad"),
        ]
        dispatch_routes = {"disp_ok": "THINK", "disp_bad": "KERNEL"}
        report = self.auditor.audit_batch(traces, dispatch_routes)
        assert report["verdict"] == "violated"
        assert report["escalations"] >= 1


# ===========================================================================
# TEST CLASS 2: CHAIN RECEIPT COUPLING AUDITOR
# ===========================================================================

class TestChainReceiptCouplingAuditor:

    def setup_method(self):
        self.auditor = ChainReceiptCouplingAuditor()

    def test_canonical_with_kernel_receipt_is_clean(self):
        """Canonical artifact + clean KERNEL receipt → no findings."""
        artifacts = [make_artifact("art_001", "canonical", "disp_001")]
        receipts = [make_kernel_receipt("s1", "disp_001")]
        findings = self.auditor.audit_coupling(artifacts, receipts)
        assert findings == []

    def test_canonical_with_no_receipt_is_critical(self):
        """Canonical artifact + no chain receipt → CHAIN_RECEIPT_MISSING (CRITICAL)."""
        artifacts = [make_artifact("art_002", "canonical", "disp_002")]
        findings = self.auditor.audit_coupling(artifacts, [])
        assert len(findings) == 1
        assert findings[0].finding_type == Patch02FindingType.CHAIN_RECEIPT_MISSING
        assert findings[0].severity == LineageFindingSeverity.CRITICAL
        assert findings[0].blocking is True

    def test_canonical_with_skill_receipt_only_is_critical(self):
        """Canonical artifact with only SKILL receipt (no KERNEL) → CHAIN_RECEIPT_MISSING."""
        artifacts = [make_artifact("art_003", "canonical", "disp_003")]
        receipts = [make_skill_receipt("s1", "disp_003")]
        findings = self.auditor.audit_coupling(artifacts, receipts)
        assert any(f.finding_type == Patch02FindingType.CHAIN_RECEIPT_MISSING for f in findings)

    def test_provisional_with_no_receipt_is_moderate(self):
        """Provisional artifact + no receipt → CHAIN_RECEIPT_MISSING (MODERATE, non-blocking)."""
        artifacts = [make_artifact("art_004", "provisional", "disp_004")]
        findings = self.auditor.audit_coupling(artifacts, [])
        assert len(findings) == 1
        assert findings[0].severity == LineageFindingSeverity.MODERATE
        assert findings[0].blocking is False

    def test_speculative_artifact_needs_no_receipt(self):
        """Speculative artifact has no receipt requirement → no findings."""
        artifacts = [make_artifact("art_005", "speculative", None)]
        findings = self.auditor.audit_coupling(artifacts, [])
        assert findings == []

    def test_orphan_receipt_detected(self):
        """Chain receipt with missing dispatch_id_ref → ORPHAN_CHAIN_RECEIPT."""
        builder = ChainReceiptBuilderV2()
        orphan = builder.emit(
            session_id="s1", dispatch_id_ref="",
            from_worker_id="skill.orphan", from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.x", to_worker_type=WorkerType.AGENT,
        )
        findings = self.auditor.audit_orphan_receipts([orphan])
        assert len(findings) == 1
        assert findings[0].finding_type == Patch02FindingType.ORPHAN_CHAIN_RECEIPT
        assert findings[0].blocking is True

    def test_clean_receipt_no_orphan(self):
        """Clean receipt with valid dispatch_id_ref → no orphan finding."""
        receipt = make_kernel_receipt("s1", "disp_valid")
        findings = self.auditor.audit_orphan_receipts([receipt])
        assert findings == []


# ===========================================================================
# TEST CLASS 3: THINK→CANONICAL SHORTCUT DETECTION
# ===========================================================================

class TestThinkToCanonicalShortcut:

    def setup_method(self):
        self.auditor = FullLineageAuditor()

    def test_think_trace_write_in_canonical_chain_is_clean(self):
        """THINK worker with TRACE_WRITE in canonical chain → no shortcut violation."""
        artifacts = [make_artifact("art_001", "canonical", "disp_001")]
        think_receipt = make_think_receipt("s1", "disp_001", effect=HandoffEffect.TRACE_WRITE)
        kernel_receipt = make_kernel_receipt("s1", "disp_001")

        report = self.auditor.full_audit(
            artifacts=artifacts,
            chain_receipts=[think_receipt, kernel_receipt],
        )
        assert report["shortcut_violations"] == 0

    def test_think_canonical_write_in_canonical_chain_is_violation(self):
        """THINK worker attempting CANONICAL_WRITE in chain → THINK_TO_CANONICAL_SHORTCUT."""
        artifacts = [make_artifact("art_002", "canonical", "disp_002")]
        # THINK attempts canonical write — violation (already caught in V2 receipt, but also in audit)
        think_bad_receipt = make_think_receipt("s1", "disp_002", effect=HandoffEffect.CANONICAL_WRITE)
        # Note: this receipt will have a CONSTITUTIONAL_VIOLATION from V2 emit()
        # But the audit also surfaces it as THINK_TO_CANONICAL_SHORTCUT

        report = self.auditor.full_audit(
            artifacts=artifacts,
            chain_receipts=[think_bad_receipt],
        )
        assert report["shortcut_violations"] >= 1
        assert report["verdict"] == "violated"


# ===========================================================================
# TEST CLASS 4: FULL LINEAGE AUDITOR
# ===========================================================================

class TestFullLineageAuditor:

    def setup_method(self):
        self.auditor = FullLineageAuditor()

    def _clean_scenario(self):
        """A fully lawful scenario: canonical artifact, kernel receipt, valid think trace."""
        artifacts = [
            make_artifact("art_canon", "canonical", "disp_001"),
            make_artifact("art_prov", "provisional", "disp_002"),
            make_artifact("art_spec", "speculative", None),
        ]
        receipts = [
            make_kernel_receipt("s1", "disp_001"),
            make_skill_receipt("s1", "disp_002"),
        ]
        traces = [
            make_think_trace(dispatch_id_ref="disp_think_001"),
        ]
        dispatch_routes = {"disp_think_001": "THINK"}
        return artifacts, receipts, traces, dispatch_routes

    def test_clean_full_audit(self):
        """Fully lawful scenario → clean verdict across all categories."""
        artifacts, receipts, traces, dispatch_routes = self._clean_scenario()
        report = self.auditor.full_audit(
            artifacts=artifacts,
            chain_receipts=receipts,
            think_traces=traces,
            dispatch_routes=dispatch_routes,
        )
        assert report["verdict"] == "clean"
        assert report["blocking_count"] == 0
        assert report["think_violations"] == 0
        assert report["coupling_violations"] == 0
        assert report["orphan_violations"] == 0
        assert report["shortcut_violations"] == 0

    def test_violated_full_audit_canonical_no_receipt(self):
        """Canonical artifact without receipt → violated, coupling_violations > 0."""
        artifacts = [make_artifact("art_001", "canonical", "disp_001")]
        report = self.auditor.full_audit(
            artifacts=artifacts,
            chain_receipts=[],  # No receipts
        )
        assert report["verdict"] == "violated"
        assert report["coupling_violations"] >= 1
        assert report["blocking_count"] >= 1

    def test_violated_full_audit_think_escalation(self):
        """ThinkTrace under wrong route → violated, think_violations > 0."""
        traces = [make_think_trace(dispatch_id_ref="disp_bad")]
        dispatch_routes = {"disp_bad": "SKILL"}  # Wrong route for a ThinkTrace
        report = self.auditor.full_audit(
            artifacts=[],
            chain_receipts=[],
            think_traces=traces,
            dispatch_routes=dispatch_routes,
        )
        assert report["verdict"] == "violated"
        assert report["think_violations"] >= 1

    def test_full_audit_mixed_scenario(self):
        """Mixed scenario: 1 clean canonical + 1 uncoupled canonical + 1 escalated trace."""
        artifacts = [
            make_artifact("art_clean", "canonical", "disp_clean"),
            make_artifact("art_bad", "canonical", "disp_bad"),
        ]
        receipts = [make_kernel_receipt("s1", "disp_clean")]
        traces = [make_think_trace(dispatch_id_ref="disp_think_bad")]
        dispatch_routes = {"disp_think_bad": "AGENT"}  # Escalation

        report = self.auditor.full_audit(
            artifacts=artifacts,
            chain_receipts=receipts,
            think_traces=traces,
            dispatch_routes=dispatch_routes,
        )
        assert report["verdict"] == "violated"
        assert report["coupling_violations"] >= 1  # art_bad has no kernel receipt
        assert report["think_violations"] >= 1      # think trace escalation
        assert report["total_artifacts"] == 2

    def test_empty_batch_is_clean(self):
        """Empty batch → clean verdict."""
        report = self.auditor.full_audit(artifacts=[], chain_receipts=[], think_traces=[])
        assert report["verdict"] == "clean"
        assert report["total_findings"] == 0

    def test_full_audit_report_structure(self):
        """Full audit report has all required keys."""
        report = self.auditor.full_audit(artifacts=[], chain_receipts=[])
        required_keys = {
            "total_artifacts", "total_chain_receipts", "total_think_traces",
            "total_findings", "blocking_count",
            "think_violations", "coupling_violations", "orphan_violations", "shortcut_violations",
            "findings", "verdict",
        }
        assert required_keys.issubset(set(report.keys()))
