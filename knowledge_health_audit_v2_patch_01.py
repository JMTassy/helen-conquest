"""
KNOWLEDGE_HEALTH_AUDIT_V2_PATCH_01: dispatch_lineage_violation finding class

Extends KNOWLEDGE_HEALTH_AUDIT_V2 with:
- dispatch_lineage_violation finding type
- canonical_write_without_kernel detection
- SKILL/AGENT/TEMPLE output inserted as canon detection
- Missing dispatch_id_ref on artifact
- Route incompatible with mutation type

This patch does NOT modify V2 (which is FROZEN).
It adds new finding capabilities on top.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class LineageFindingSeverity(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class LineageFindingType(Enum):
    # Original V2 findings (reproduced for reference)
    UNSUPPORTED_CLAIM = "unsupported_claim"
    ORPHAN_NODE = "orphan_node"
    DUPLICATE_CONCEPT = "duplicate_concept"
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"
    STALE_DERIVED_ARTIFACT = "stale_derived_artifact"
    CANONICAL_PROVISIONAL_DRIFT = "canonical_provisional_drift"
    BROKEN_BACKLINK = "broken_backlink"
    INDEX_MISMATCH = "index_mismatch"
    SPECULATIVE_LEAK = "speculative_leak"

    # PATCH_01: New dispatch lineage findings
    DISPATCH_LINEAGE_VIOLATION = "dispatch_lineage_violation"


@dataclass
class LineageFinding:
    """A single dispatch lineage finding."""
    finding_type: LineageFindingType
    severity: LineageFindingSeverity
    target_id: str
    reason: str
    blocking: bool
    dispatch_id_ref: Optional[str] = None
    route_detected: Optional[str] = None
    route_required: Optional[str] = None
    worker_id: Optional[str] = None
    suggested_repair: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_type": self.finding_type.value,
            "severity": self.severity.value,
            "target_id": self.target_id,
            "reason": self.reason,
            "blocking": self.blocking,
            "dispatch_id_ref": self.dispatch_id_ref,
            "route_detected": self.route_detected,
            "route_required": self.route_required,
            "worker_id": self.worker_id,
            "suggested_repair": self.suggested_repair,
        }


class DispatchLineageAuditor:
    """
    PATCH_01: Audit artifacts for dispatch lineage violations.

    Core check: Was every canonical write authorized by KERNEL dispatch?

    This auditor inspects artifact metadata and chain receipts to verify:
    1. All canonical writes trace to a KERNEL dispatch receipt
    2. No SKILL/AGENT/TEMPLE worker produced a canonical artifact directly
    3. All artifacts have a dispatch_id_ref
    4. Route type matches artifact type
    """

    def audit_artifact(
        self,
        artifact: Dict[str, Any],
    ) -> List[LineageFinding]:
        """
        Audit a single artifact for dispatch lineage violations.

        Expected artifact fields:
        - artifact_id: str
        - canonical_status: str (canonical | provisional | speculative | candidate)
        - dispatch_id_ref: str (optional but required for canonical)
        - produced_by_worker_type: str (kernel | skill | agent | temple)
        - produced_by_worker_id: str
        """
        findings = []
        artifact_id = artifact.get("artifact_id", "unknown")
        canonical_status = artifact.get("canonical_status", "candidate")
        dispatch_id_ref = artifact.get("dispatch_id_ref")
        worker_type = artifact.get("produced_by_worker_type", "unknown")
        worker_id = artifact.get("produced_by_worker_id", "unknown")

        # Check 1: canonical artifact without dispatch_id_ref
        if canonical_status == "canonical" and not dispatch_id_ref:
            findings.append(LineageFinding(
                finding_type=LineageFindingType.DISPATCH_LINEAGE_VIOLATION,
                severity=LineageFindingSeverity.CRITICAL,
                target_id=artifact_id,
                reason="Canonical artifact has no dispatch_id_ref (untraced write)",
                blocking=True,
                dispatch_id_ref=None,
                route_detected=None,
                route_required="KERNEL",
                worker_id=worker_id,
                suggested_repair="Add dispatch_id_ref or downgrade to provisional",
            ))

        # Check 2: canonical artifact from non-KERNEL worker
        if canonical_status == "canonical" and worker_type not in ("kernel", "unknown"):
            findings.append(LineageFinding(
                finding_type=LineageFindingType.DISPATCH_LINEAGE_VIOLATION,
                severity=LineageFindingSeverity.CRITICAL,
                target_id=artifact_id,
                reason=f"Canonical artifact produced by non-sovereign worker: {worker_type}",
                blocking=True,
                dispatch_id_ref=dispatch_id_ref,
                route_detected=worker_type,
                route_required="KERNEL",
                worker_id=worker_id,
                suggested_repair="Downgrade to provisional or route through KERNEL for promotion",
            ))

        # Check 3: Temple artifact leaking into canonical
        if canonical_status == "canonical" and worker_type == "temple":
            findings.append(LineageFinding(
                finding_type=LineageFindingType.DISPATCH_LINEAGE_VIOLATION,
                severity=LineageFindingSeverity.CRITICAL,
                target_id=artifact_id,
                reason="Temple worker produced canonical artifact (speculative_leak)",
                blocking=True,
                dispatch_id_ref=dispatch_id_ref,
                route_detected="TEMPLE",
                route_required="KERNEL",
                worker_id=worker_id,
                suggested_repair="Quarantine as speculative; require explicit promotion via KERNEL",
            ))

        # Check 4: Provisional artifact from Temple (warning only)
        if canonical_status == "provisional" and worker_type == "temple":
            findings.append(LineageFinding(
                finding_type=LineageFindingType.DISPATCH_LINEAGE_VIOLATION,
                severity=LineageFindingSeverity.MODERATE,
                target_id=artifact_id,
                reason="Temple worker produced provisional artifact (borderline speculative_leak)",
                blocking=False,
                dispatch_id_ref=dispatch_id_ref,
                route_detected="TEMPLE",
                route_required="SKILL or AGENT",
                worker_id=worker_id,
                suggested_repair="Review and downgrade to speculative or validate with SKILL",
            ))

        return findings

    def audit_chain_receipts(
        self,
        chain_receipts: List[Dict[str, Any]],
    ) -> List[LineageFinding]:
        """
        Audit chain receipts for governance violations.

        Checks:
        - No canonical_write_attempted from SKILL/AGENT/TEMPLE
        - No governed_mutation_attempted from SKILL/AGENT/TEMPLE
        - All receipts have dispatch_id_ref
        """
        findings = []

        for receipt in chain_receipts:
            receipt_id = receipt.get("chain_receipt_id", "unknown")
            worker_type = receipt.get("from_worker_type", "unknown")
            canonical_write = receipt.get("canonical_write_attempted", False)
            governed_mutation = receipt.get("governed_mutation_attempted", False)
            dispatch_ref = receipt.get("dispatch_id_ref")

            if canonical_write and worker_type != "kernel":
                findings.append(LineageFinding(
                    finding_type=LineageFindingType.DISPATCH_LINEAGE_VIOLATION,
                    severity=LineageFindingSeverity.CRITICAL,
                    target_id=receipt_id,
                    reason=f"canonical_write_attempted by {worker_type} (non-sovereign)",
                    blocking=True,
                    dispatch_id_ref=dispatch_ref,
                    route_detected=worker_type,
                    route_required="kernel",
                    worker_id=receipt.get("from_worker_id"),
                    suggested_repair="Block the canonical write; route through KERNEL for promotion",
                ))

            if governed_mutation and worker_type != "kernel":
                findings.append(LineageFinding(
                    finding_type=LineageFindingType.DISPATCH_LINEAGE_VIOLATION,
                    severity=LineageFindingSeverity.CRITICAL,
                    target_id=receipt_id,
                    reason=f"governed_mutation_attempted by {worker_type} (non-sovereign)",
                    blocking=True,
                    dispatch_id_ref=dispatch_ref,
                    route_detected=worker_type,
                    route_required="kernel",
                    worker_id=receipt.get("from_worker_id"),
                    suggested_repair="Block the mutation; route through KERNEL",
                ))

            if not dispatch_ref:
                findings.append(LineageFinding(
                    finding_type=LineageFindingType.DISPATCH_LINEAGE_VIOLATION,
                    severity=LineageFindingSeverity.HIGH,
                    target_id=receipt_id,
                    reason="Chain receipt missing dispatch_id_ref (untraced delegation)",
                    blocking=False,
                    dispatch_id_ref=None,
                    worker_id=receipt.get("from_worker_id"),
                    suggested_repair="Add dispatch_id_ref to chain receipt",
                ))

        return findings

    def audit_report(
        self,
        artifacts: List[Dict[str, Any]],
        chain_receipts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate full dispatch lineage audit report."""
        artifact_findings = []
        for a in artifacts:
            artifact_findings.extend(self.audit_artifact(a))

        chain_findings = self.audit_chain_receipts(chain_receipts)
        all_findings = artifact_findings + chain_findings

        critical_count = sum(1 for f in all_findings if f.severity == LineageFindingSeverity.CRITICAL)
        blocking_count = sum(1 for f in all_findings if f.blocking)

        return {
            "audit_type": "KNOWLEDGE_HEALTH_AUDIT_V2_PATCH_01",
            "finding_type": "dispatch_lineage_violation",
            "artifacts_audited": len(artifacts),
            "chain_receipts_audited": len(chain_receipts),
            "total_findings": len(all_findings),
            "critical_findings": critical_count,
            "blocking_findings": blocking_count,
            "findings": [f.to_dict() for f in all_findings],
            "verdict": "clean" if blocking_count == 0 else "violated",
            "canonical_mutations_outside_kernel": sum(
                1 for f in all_findings
                if "canonical_write" in f.reason.lower() or "canonical artifact produced by non-sovereign" in f.reason.lower()
            ),
        }
