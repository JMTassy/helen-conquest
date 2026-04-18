"""
KNOWLEDGE_HEALTH_AUDIT_V2_PATCH_02: THINK + Chain Receipt Lineage Awareness

Extends KNOWLEDGE_HEALTH_AUDIT_V2_PATCH_01 with:

New finding types:
  - THINKING_LINEAGE_VIOLATION: THINK output crossing authority boundaries
  - CHAIN_RECEIPT_MISSING: canonical/governed artifact with no chain receipt
  - THINK_ESCALATION: ThinkTrace content treated as decision/canon
  - ORPHAN_CHAIN_RECEIPT: chain receipt with no dispatch_id_ref (already in V2 ChainStatus)

This patch does NOT modify V1 or PATCH_01 (both FROZEN).
It adds new lineage-awareness for the THINK + chain receipt layer.

Audit surface extended to:
  - ThinkTrace objects (via ThinkLineageAuditor)
  - ChainReceipt V2 objects (via ChainReceiptCouplingAuditor)
  - Canonical artifacts cross-referenced against chain receipts (via FullLineageAuditor)

The central question of each new auditor:
  ThinkLineageAuditor:          Is THINK output staying in its preparation lane?
  ChainReceiptCouplingAuditor:  Does every canonical artifact have a lawful chain receipt?
  FullLineageAuditor:           Is the full circulation spine clean? (dispatch → THINK → chain → canon)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set

# Import PATCH_01 types (do not modify them)
from knowledge_health_audit_v2_patch_01 import (
    LineageFindingSeverity, LineageFindingType, LineageFinding
)
# Import chain receipt V2 types
from helen_chain_receipt_v2 import (
    ChainReceipt, WorkerType, HandoffEffect, ChainStatus
)
# Import ThinkTrace types
from helen_think_trace_v1 import ThinkTrace, ThinkTraceBuilder


# ============================================================================
# PATCH_02 FINDING TYPES (extends PATCH_01 without modifying it)
# ============================================================================

class Patch02FindingType(Enum):
    """
    New finding types introduced in PATCH_02.

    These are separate from LineageFindingType to preserve PATCH_01's frozen schema.
    A FullLineageAuditor merges findings from both enums in its report.
    """
    # THINK-related findings
    THINKING_LINEAGE_VIOLATION = "thinking_lineage_violation"
    # A ThinkTrace output was referenced as evidence in a canonical artifact
    # OR a ThinkTrace claimed authority it doesn't have

    THINK_ESCALATION = "think_escalation"
    # A ThinkTrace was treated as a decision or canonical claim
    # (e.g., ThinkTrace dispatch_id_ref points to a non-THINK route)

    # Chain receipt coupling findings
    CHAIN_RECEIPT_MISSING = "chain_receipt_missing"
    # A canonical or governed artifact has no chain receipt linking it to dispatch
    # (i.e., it appeared in the knowledge layer without governed handoff evidence)

    ORPHAN_CHAIN_RECEIPT = "orphan_chain_receipt"
    # A chain receipt has no dispatch_id_ref
    # Already detected in V2 emit() but surfaced here for audit completeness

    # Full lineage findings
    THINK_TO_CANONICAL_SHORTCUT = "think_to_canonical_shortcut"
    # A THINK worker appeared directly in the from_worker chain of a canonical artifact
    # without passing through a SKILL/AGENT/KERNEL step first


@dataclass
class Patch02Finding:
    """A single PATCH_02 lineage finding."""
    finding_type: Patch02FindingType
    severity: LineageFindingSeverity
    target_id: str
    reason: str
    blocking: bool
    dispatch_id_ref: Optional[str] = None
    worker_id: Optional[str] = None
    worker_type: Optional[str] = None
    attempted_effect: Optional[str] = None
    suggested_repair: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type.value,
            "severity": self.severity.value,
            "target_id": self.target_id,
            "reason": self.reason,
            "blocking": self.blocking,
            "dispatch_id_ref": self.dispatch_id_ref,
            "worker_id": self.worker_id,
            "worker_type": self.worker_type,
            "attempted_effect": self.attempted_effect,
            "suggested_repair": self.suggested_repair,
        }


# ============================================================================
# THINK LINEAGE AUDITOR
# ============================================================================

class ThinkLineageAuditor:
    """
    Audits ThinkTrace objects for authority escalation.

    Central question: Is THINK output staying in its preparation lane?

    Detects:
    1. THINK_ESCALATION: ThinkTrace with non-THINK dispatch_id_ref
       (i.e., trace was emitted under a KERNEL/SKILL/AGENT dispatch — wrong regime)
    2. THINKING_LINEAGE_VIOLATION: ThinkTrace invariants broken post-emission
       (authority != NONE, may_alter_state != False, etc.)
    3. THINK_TO_CANONICAL_SHORTCUT: ThinkTrace referenced in canonical artifact
       without intermediate SKILL/AGENT/KERNEL step

    Non-findings:
    - ThinkTrace with no decomposition steps → INFO only (not blocking)
    - ThinkTrace with low confidence → not a violation (preparation can be uncertain)
    """

    def __init__(self):
        self._validator = ThinkTraceBuilder()

    def audit_trace(self, trace: ThinkTrace, dispatch_route: Optional[str] = None) -> List[Patch02Finding]:
        """
        Audit a single ThinkTrace.

        Args:
            trace: The ThinkTrace to audit
            dispatch_route: The primary_route of the DispatchReceipt that triggered THINK
                           If provided, verifies it was a THINK route.

        Returns:
            List of Patch02Finding (empty if clean)
        """
        findings = []

        # Finding 1: Constitutional invariants broken
        results = self._validator.validate_invariants(trace)
        failed = {k: v for k, v in results.items() if not v}
        if failed:
            findings.append(Patch02Finding(
                finding_type=Patch02FindingType.THINKING_LINEAGE_VIOLATION,
                severity=LineageFindingSeverity.CRITICAL,
                target_id=trace.trace_id,
                reason=f"ThinkTrace constitutional invariants violated: {list(failed.keys())}. "
                       f"Thinking is cognition-as-preparation — these invariants are unforgeable.",
                blocking=True,
                dispatch_id_ref=trace.dispatch_id_ref,
                suggested_repair="Re-emit the ThinkTrace via ThinkTraceBuilder.emit() — "
                                 "invariants are enforced at construction time.",
            ))

        # Finding 2: THINK_ESCALATION — trace emitted under non-THINK dispatch
        if dispatch_route is not None and dispatch_route != "THINK":
            findings.append(Patch02Finding(
                finding_type=Patch02FindingType.THINK_ESCALATION,
                severity=LineageFindingSeverity.HIGH,
                target_id=trace.trace_id,
                reason=f"ThinkTrace linked to dispatch_id_ref={trace.dispatch_id_ref} "
                       f"which used route={dispatch_route}, not THINK. "
                       f"A ThinkTrace must only be emitted under a THINK-routed dispatch.",
                blocking=True,
                dispatch_id_ref=trace.dispatch_id_ref,
                suggested_repair="Re-route the triggering input as THINK_PREPARATION, "
                                 "then re-emit the ThinkTrace under the resulting dispatch_id.",
            ))

        # Finding 3: Missing dispatch reference
        if not trace.dispatch_id_ref:
            findings.append(Patch02Finding(
                finding_type=Patch02FindingType.THINK_ESCALATION,
                severity=LineageFindingSeverity.CRITICAL,
                target_id=trace.trace_id,
                reason="ThinkTrace has no dispatch_id_ref — lineage is broken. "
                       "Every ThinkTrace must link to the DispatchReceipt that triggered THINK.",
                blocking=True,
                dispatch_id_ref=None,
                suggested_repair="Emit ThinkTrace via ThinkTraceBuilder.emit() with a valid dispatch_id_ref.",
            ))

        return findings

    def audit_batch(
        self,
        traces: List[ThinkTrace],
        dispatch_routes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Audit a batch of ThinkTrace objects.

        Args:
            traces: List of ThinkTrace objects
            dispatch_routes: Optional dict of {dispatch_id_ref: route_type_value}
                            for escalation detection

        Returns:
            Batch audit report
        """
        all_findings = []
        for trace in traces:
            route = (dispatch_routes or {}).get(trace.dispatch_id_ref)
            findings = self.audit_trace(trace, dispatch_route=route)
            all_findings.extend(findings)

        blocking_count = sum(1 for f in all_findings if f.blocking)
        return {
            "total_traces": len(traces),
            "total_findings": len(all_findings),
            "blocking_count": blocking_count,
            "escalations": sum(1 for f in all_findings if f.finding_type == Patch02FindingType.THINK_ESCALATION),
            "invariant_violations": sum(1 for f in all_findings if f.finding_type == Patch02FindingType.THINKING_LINEAGE_VIOLATION),
            "findings": [f.to_dict() for f in all_findings],
            "verdict": "clean" if blocking_count == 0 else "violated",
        }


# ============================================================================
# CHAIN RECEIPT COUPLING AUDITOR
# ============================================================================

class ChainReceiptCouplingAuditor:
    """
    Audits canonical artifacts for chain receipt coupling.

    Central question: Does every canonical artifact have a lawful chain receipt?

    An artifact is "coupled" if there exists at least one ChainReceipt V2 where:
    - The receipt is clean (no violations)
    - The from_worker_type == KERNEL (sovereign handoff)
    - The receipt links to the same dispatch_id_ref as the artifact

    An artifact is "uncoupled" if no such receipt exists.

    Uncoupled canonical artifacts = CHAIN_RECEIPT_MISSING (CRITICAL, blocking).
    Candidate/provisional artifacts without chain receipts = MODERATE (non-blocking).
    """

    def audit_coupling(
        self,
        artifacts: List[Dict[str, Any]],
        chain_receipts: List[ChainReceipt],
    ) -> List[Patch02Finding]:
        """
        Audit artifacts against chain receipts.

        Args:
            artifacts: List of artifact dicts with {artifact_id, canonical_status, dispatch_id_ref, ...}
            chain_receipts: List of ChainReceipt V2 objects

        Returns:
            List of Patch02Finding
        """
        findings = []

        # Build index: dispatch_id_ref → clean KERNEL chain receipts
        kernel_receipts_by_dispatch: Dict[str, List[ChainReceipt]] = {}
        for r in chain_receipts:
            if r.from_worker_type == WorkerType.KERNEL and r.is_clean and r.dispatch_id_ref:
                kernel_receipts_by_dispatch.setdefault(r.dispatch_id_ref, []).append(r)

        # Also index: all clean receipts (for non-canonical artifacts)
        all_clean_by_dispatch: Dict[str, List[ChainReceipt]] = {}
        for r in chain_receipts:
            if r.is_clean and r.dispatch_id_ref:
                all_clean_by_dispatch.setdefault(r.dispatch_id_ref, []).append(r)

        for artifact in artifacts:
            artifact_id = artifact.get("artifact_id", "(unknown)")
            status = artifact.get("canonical_status", "unknown")
            dispatch_ref = artifact.get("dispatch_id_ref")

            if status == "canonical":
                # Must have a clean KERNEL chain receipt
                kernel_receipts = kernel_receipts_by_dispatch.get(dispatch_ref, [])
                if not kernel_receipts:
                    findings.append(Patch02Finding(
                        finding_type=Patch02FindingType.CHAIN_RECEIPT_MISSING,
                        severity=LineageFindingSeverity.CRITICAL,
                        target_id=artifact_id,
                        reason=f"Canonical artifact '{artifact_id}' has no clean KERNEL chain receipt. "
                               f"dispatch_id_ref={dispatch_ref}. "
                               f"Every canonical write must be evidenced by a lawful KERNEL handoff.",
                        blocking=True,
                        dispatch_id_ref=dispatch_ref,
                        suggested_repair="Emit a ChainReceipt V2 with from_worker_type=KERNEL "
                                         "and handoff_effect=CANONICAL_WRITE for this dispatch.",
                    ))

            elif status in ("provisional", "candidate"):
                # Should have at least some clean receipt — non-blocking if missing
                any_receipts = all_clean_by_dispatch.get(dispatch_ref, [])
                if not any_receipts and dispatch_ref:
                    findings.append(Patch02Finding(
                        finding_type=Patch02FindingType.CHAIN_RECEIPT_MISSING,
                        severity=LineageFindingSeverity.MODERATE,
                        target_id=artifact_id,
                        reason=f"{status.capitalize()} artifact '{artifact_id}' has no chain receipt. "
                               f"dispatch_id_ref={dispatch_ref}. "
                               f"Recommendation: emit a handoff receipt for full lineage traceability.",
                        blocking=False,
                        dispatch_id_ref=dispatch_ref,
                        suggested_repair="Emit a ChainReceipt V2 for this handoff to complete lineage.",
                    ))

        return findings

    def audit_orphan_receipts(self, chain_receipts: List[ChainReceipt]) -> List[Patch02Finding]:
        """Detect chain receipts with missing dispatch_id_ref (orphan handoffs)."""
        findings = []
        for r in chain_receipts:
            if r.chain_status == ChainStatus.MISSING_DISPATCH_REF:
                findings.append(Patch02Finding(
                    finding_type=Patch02FindingType.ORPHAN_CHAIN_RECEIPT,
                    severity=LineageFindingSeverity.CRITICAL,
                    target_id=r.receipt_id,
                    reason=f"Chain receipt '{r.receipt_id}' from worker '{r.from_worker_id}' "
                           f"has no dispatch_id_ref — handoff lineage is broken.",
                    blocking=True,
                    worker_id=r.from_worker_id,
                    worker_type=r.from_worker_type.value,
                ))
        return findings


# ============================================================================
# FULL LINEAGE AUDITOR
# ============================================================================

class FullLineageAuditor:
    """
    Full circulation spine audit.

    Combines:
    - PATCH_01 dispatch lineage (canonical writes, missing dispatch refs on artifacts)
    - PATCH_02 think lineage (THINK escalation, invariant violations)
    - PATCH_02 chain receipt coupling (canonical artifacts without KERNEL receipts)
    - PATCH_02 orphan receipts
    - PATCH_02 THINK→canonical shortcuts (THINK workers in canonical handoff chains)

    The full_audit() method returns one consolidated report.
    """

    def __init__(self):
        self._think_auditor = ThinkLineageAuditor()
        self._coupling_auditor = ChainReceiptCouplingAuditor()

    def _detect_think_to_canonical_shortcuts(
        self,
        artifacts: List[Dict[str, Any]],
        chain_receipts: List[ChainReceipt],
    ) -> List[Patch02Finding]:
        """
        Detect THINK workers appearing directly in canonical handoff chains.

        A THINK→canonical shortcut occurs when:
        - A canonical artifact's dispatch_id_ref matches a chain receipt
        - That receipt's from_worker_type is THINK
        - There is no intermediate KERNEL step in the same dispatch lineage

        This would mean a THINK trace drove a canonical write without reducer gate.
        """
        findings = []

        # Index canonical dispatch_ids
        canonical_dispatch_ids = {
            a.get("dispatch_id_ref")
            for a in artifacts
            if a.get("canonical_status") == "canonical" and a.get("dispatch_id_ref")
        }

        # Find THINK workers in chains linked to canonical dispatch IDs
        for r in chain_receipts:
            if (r.dispatch_id_ref in canonical_dispatch_ids
                    and r.from_worker_type == WorkerType.THINK
                    and r.handoff_effect not in (HandoffEffect.NONE, HandoffEffect.TRACE_WRITE)):
                findings.append(Patch02Finding(
                    finding_type=Patch02FindingType.THINK_TO_CANONICAL_SHORTCUT,
                    severity=LineageFindingSeverity.CRITICAL,
                    target_id=r.receipt_id,
                    reason=f"THINK worker '{r.from_worker_id}' appears in the handoff chain "
                           f"for a canonical artifact (dispatch_id_ref={r.dispatch_id_ref}) "
                           f"with effect={r.handoff_effect.value}. "
                           f"THINK output must not drive canonical writes — "
                           f"it must pass through a KERNEL reducer gate first.",
                    blocking=True,
                    dispatch_id_ref=r.dispatch_id_ref,
                    worker_id=r.from_worker_id,
                    worker_type=r.from_worker_type.value,
                    attempted_effect=r.handoff_effect.value,
                    suggested_repair="Route THINK output through SKILL/AGENT for preparation, "
                                     "then through KERNEL for reducer-gated canonical admission.",
                ))

        return findings

    def full_audit(
        self,
        artifacts: List[Dict[str, Any]],
        chain_receipts: List[ChainReceipt],
        think_traces: Optional[List[ThinkTrace]] = None,
        dispatch_routes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Full circulation spine audit.

        Args:
            artifacts: List of knowledge artifact dicts
            chain_receipts: List of ChainReceipt V2 objects
            think_traces: Optional list of ThinkTrace objects
            dispatch_routes: Optional {dispatch_id_ref: route_type_value} for think escalation

        Returns:
            Consolidated audit report with:
            - total_findings
            - blocking_count
            - think_violations, coupling_violations, orphan_violations, shortcut_violations
            - verdict: "clean" | "violated"
            - findings: list of all finding dicts
        """
        all_findings: List[Patch02Finding] = []

        # 1. Think trace audit
        if think_traces:
            think_report = self._think_auditor.audit_batch(think_traces, dispatch_routes)
            # Re-inflate findings from dict (we have the objects in scope)
            for trace in think_traces:
                route = (dispatch_routes or {}).get(trace.dispatch_id_ref)
                all_findings.extend(self._think_auditor.audit_trace(trace, route))

        # 2. Chain receipt coupling audit
        coupling_findings = self._coupling_auditor.audit_coupling(artifacts, chain_receipts)
        all_findings.extend(coupling_findings)

        # 3. Orphan receipt audit
        orphan_findings = self._coupling_auditor.audit_orphan_receipts(chain_receipts)
        all_findings.extend(orphan_findings)

        # 4. THINK→canonical shortcut detection
        shortcut_findings = self._detect_think_to_canonical_shortcuts(artifacts, chain_receipts)
        all_findings.extend(shortcut_findings)

        blocking_count = sum(1 for f in all_findings if f.blocking)

        return {
            "total_artifacts": len(artifacts),
            "total_chain_receipts": len(chain_receipts),
            "total_think_traces": len(think_traces) if think_traces else 0,
            "total_findings": len(all_findings),
            "blocking_count": blocking_count,
            "think_violations": sum(
                1 for f in all_findings
                if f.finding_type in (Patch02FindingType.THINKING_LINEAGE_VIOLATION, Patch02FindingType.THINK_ESCALATION)
            ),
            "coupling_violations": sum(
                1 for f in all_findings
                if f.finding_type == Patch02FindingType.CHAIN_RECEIPT_MISSING
            ),
            "orphan_violations": sum(
                1 for f in all_findings
                if f.finding_type == Patch02FindingType.ORPHAN_CHAIN_RECEIPT
            ),
            "shortcut_violations": sum(
                1 for f in all_findings
                if f.finding_type == Patch02FindingType.THINK_TO_CANONICAL_SHORTCUT
            ),
            "findings": [f.to_dict() for f in all_findings],
            "verdict": "clean" if blocking_count == 0 else "violated",
        }
