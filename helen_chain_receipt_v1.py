"""
HELEN_CHAIN_RECEIPT_V1: Dispatch-Mediated Worker Chaining

Purpose:
- Record every delegation edge between workers
- Prevent silent chaining
- Provide full lineage for audit

Law:
- Every chain edge emits an immutable receipt
- No silent chaining (from_worker → to_worker without receipt)
- governed_mutation_attempted tracked and auditable
- Append-only (never modify after emission)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json
import uuid


class ChainStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class WorkerType(Enum):
    KERNEL = "kernel"
    SKILL = "skill"
    AGENT = "agent"
    TEMPLE = "temple"


@dataclass
class ChainReceipt:
    """
    Immutable record of a worker-to-worker delegation.

    Invariants:
    - Append-only (never modified after emission)
    - governed_mutation_attempted tracked
    - from_worker always non-null
    - to_worker always non-null
    - dispatch_id_ref traces back to original dispatch decision
    """
    chain_receipt_id: str
    timestamp: str
    session_id: str

    # Dispatch lineage
    dispatch_id_ref: str

    # Worker chain
    from_worker_id: str
    from_worker_type: WorkerType
    to_worker_id: str
    to_worker_type: WorkerType

    # Reason
    reason: str
    reason_codes: List[str]

    # Artifact lineage
    input_artifact_ids: List[str] = field(default_factory=list)
    output_artifact_ids: List[str] = field(default_factory=list)

    # Governance
    governed_mutation_attempted: bool = False
    canonical_write_attempted: bool = False

    # Status
    status: ChainStatus = ChainStatus.PENDING

    # Hash (excluding this field)
    chain_receipt_hash: Optional[str] = None

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        d = {
            "chain_receipt_id": self.chain_receipt_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "dispatch_id_ref": self.dispatch_id_ref,
            "from_worker_id": self.from_worker_id,
            "from_worker_type": self.from_worker_type.value,
            "to_worker_id": self.to_worker_id,
            "to_worker_type": self.to_worker_type.value,
            "reason": self.reason,
            "reason_codes": self.reason_codes,
            "input_artifact_ids": self.input_artifact_ids,
            "output_artifact_ids": self.output_artifact_ids,
            "governed_mutation_attempted": self.governed_mutation_attempted,
            "canonical_write_attempted": self.canonical_write_attempted,
            "status": self.status.value,
        }
        if exclude_run_metadata:
            del d["chain_receipt_id"]
            del d["timestamp"]
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


class ChainReceiptBuilder:
    """Build and emit ChainReceipts (append-only)."""

    def emit(
        self,
        session_id: str,
        dispatch_id_ref: str,
        from_worker_id: str,
        from_worker_type: WorkerType,
        to_worker_id: str,
        to_worker_type: WorkerType,
        reason: str,
        reason_codes: Optional[List[str]] = None,
        input_artifact_ids: Optional[List[str]] = None,
        output_artifact_ids: Optional[List[str]] = None,
        governed_mutation_attempted: bool = False,
        canonical_write_attempted: bool = False,
        status: ChainStatus = ChainStatus.COMPLETED,
    ) -> ChainReceipt:
        """
        Emit a chain receipt for a worker delegation.

        Law: No silent chaining. Every delegation must call this.
        """
        chain_id = f"chain_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        receipt = ChainReceipt(
            chain_receipt_id=chain_id,
            timestamp=timestamp,
            session_id=session_id,
            dispatch_id_ref=dispatch_id_ref,
            from_worker_id=from_worker_id,
            from_worker_type=from_worker_type,
            to_worker_id=to_worker_id,
            to_worker_type=to_worker_type,
            reason=reason,
            reason_codes=reason_codes or [],
            input_artifact_ids=input_artifact_ids or [],
            output_artifact_ids=output_artifact_ids or [],
            governed_mutation_attempted=governed_mutation_attempted,
            canonical_write_attempted=canonical_write_attempted,
            status=status,
        )

        # Compute hash (excluding run metadata)
        data = receipt.to_dict(exclude_run_metadata=True)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        receipt.chain_receipt_hash = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()

        return receipt

    def validate_chain_integrity(self, receipts: List[ChainReceipt]) -> Dict[str, Any]:
        """
        Validate chain for governance violations.

        Checks:
        - No canonical_write from SKILL, AGENT, or TEMPLE
        - governed_mutation_attempted only from KERNEL
        - All dispatch_id_refs present
        """
        violations = []

        for r in receipts:
            # Canonical write from non-KERNEL is a violation
            if r.canonical_write_attempted and r.from_worker_type != WorkerType.KERNEL:
                violations.append({
                    "type": "dispatch_lineage_violation",
                    "severity": "critical",
                    "chain_receipt_id": r.chain_receipt_id,
                    "from_worker": r.from_worker_id,
                    "from_type": r.from_worker_type.value,
                    "violation": "canonical_write_from_non_sovereign_worker",
                })

            # Governed mutation from non-KERNEL is a violation
            if r.governed_mutation_attempted and r.from_worker_type != WorkerType.KERNEL:
                violations.append({
                    "type": "dispatch_lineage_violation",
                    "severity": "critical",
                    "chain_receipt_id": r.chain_receipt_id,
                    "from_worker": r.from_worker_id,
                    "from_type": r.from_worker_type.value,
                    "violation": "governed_mutation_from_non_sovereign_worker",
                })

            # Missing dispatch ref
            if not r.dispatch_id_ref:
                violations.append({
                    "type": "dispatch_lineage_violation",
                    "severity": "high",
                    "chain_receipt_id": r.chain_receipt_id,
                    "violation": "missing_dispatch_id_ref",
                })

        return {
            "total_receipts": len(receipts),
            "violations": violations,
            "violation_count": len(violations),
            "integrity_status": "clean" if not violations else "violated",
        }
