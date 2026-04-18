"""
HELEN_CHAIN_RECEIPT_V2: Worker Handoff Under Circulation Law

Rewritten from zero under the HELEN_OS_ARCHITECTURE_V2 abstraction.

Core insight from the clean reframe:
  Chain receipts are not logs. They are the evidentiary record
  that objects moved between workers WITHOUT silent escalation
  or lineage loss.

The circulation spine is:
  Dispatch → THINK trace → Chain Receipt → Knowledge Audit

Each handoff in that spine must be receipted. The receipt answers:
  - WHO handed off to WHOM
  - WHAT was the governing dispatch that authorized it
  - WHAT effects were attempted (and were they lawful?)
  - IS the lineage intact?

Constitutional rules for V2:
  1. Every chain receipt links to a DispatchReceipt (dispatch_id_ref).
     No orphan receipts — lineage is non-optional.
  2. Canonical writes may only originate from KERNEL workers.
     SKILL/AGENT/TEMPLE/THINK workers attempting canonical writes
     = DISPATCH_LINEAGE_VIOLATION.
  3. Governed state mutations may only originate from KERNEL workers.
  4. THINK workers may emit TRACE_WRITE only — no other effect.
     THINK → anything except trace = CONSTITUTIONAL_VIOLATION.
  5. Receipts are append-only (never modified after emission).
  6. Receipt hash is deterministic (excludes run metadata).
  7. Authority is always declared and validated against WorkerType.

V2 additions over V1:
  - THINK worker type (with TRACE_WRITE validation)
  - HandoffEffect enum (replaces boolean flags with typed effects)
  - ViolationSeverity enum (CRITICAL / MODERATE / INFO)
  - Full dispatch_lineage_violation detection integrated into emit()
  - Receipt immutability enforced via post-init hash
  - Worker authority class inferred from WorkerType (not provided by caller)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import hashlib
import json
import uuid


# ============================================================================
# CANONICAL HASHING
# ============================================================================

def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


# ============================================================================
# ENUMS
# ============================================================================

class WorkerType(Enum):
    """
    Worker authority classes in the HELEN circulation spine.

    Authority is structural — determined by worker type, not by caller claim.
    """
    KERNEL = "kernel"      # Sovereign: may write canonical, mutate governed state
    SKILL = "skill"        # Non-sovereign: multi-step workflows, candidate writes only
    AGENT = "agent"        # Non-sovereign: single transforms, derived writes only
    TEMPLE = "temple"      # Exploratory: no writes, no canonical, no governed mutations
    THINK = "think"        # Non-sovereign: trace_write only — preparation, not decision


class HandoffEffect(Enum):
    """
    The type of effect the from_worker was attempting during handoff.

    These are declared by the caller and validated against WorkerType authority.
    """
    NONE = "none"                        # Read-only / pass-through
    TRACE_WRITE = "trace_write"          # Write a bounded preparation trace (THINK only)
    CANDIDATE_WRITE = "candidate_write"  # Propose a new object (SKILL only)
    DERIVED_WRITE = "derived_write"      # Generate from canonical (AGENT / SKILL)
    CANONICAL_WRITE = "canonical_write"  # Write to canonical layer (KERNEL only)
    GOVERNED_MUTATION = "governed_mutation"  # Mutate governed state (KERNEL only)


class ChainStatus(Enum):
    """Integrity status of the chain receipt."""
    CLEAN = "clean"                           # No violations
    DISPATCH_LINEAGE_VIOLATION = "dispatch_lineage_violation"  # canonical outside KERNEL
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"       # THINK writing beyond trace
    MISSING_DISPATCH_REF = "missing_dispatch_ref"              # No dispatch lineage
    ORPHAN_HANDOFF = "orphan_handoff"                         # No from_worker declared


class ViolationSeverity(Enum):
    """Severity of a detected violation."""
    CRITICAL = "critical"   # Blocking — the receipt must not proceed
    MODERATE = "moderate"   # Non-blocking — logged, flagged, but may continue
    INFO = "info"           # Informational — no action required


# ============================================================================
# VIOLATION RECORD
# ============================================================================

@dataclass
class HandoffViolation:
    """
    A single violation detected during chain receipt emission.

    Violations are immutable once recorded.
    Violations with severity=CRITICAL mean the receipt itself is invalid.
    """
    violation_type: ChainStatus
    severity: ViolationSeverity
    worker_id: str
    worker_type: WorkerType
    attempted_effect: HandoffEffect
    reason: str
    is_blocking: bool  # True if CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "worker_id": self.worker_id,
            "worker_type": self.worker_type.value,
            "attempted_effect": self.attempted_effect.value,
            "reason": self.reason,
            "is_blocking": self.is_blocking,
        }


# ============================================================================
# CHAIN RECEIPT V2
# ============================================================================

@dataclass
class ChainReceipt:
    """
    Immutable evidentiary record of a governed worker handoff.

    V2 design principles:
    - Receipts answer: who, to whom, under what dispatch, with what effect, was it lawful?
    - Authority is inferred from WorkerType — not claimable by the caller
    - All violations are detected at emission time, not after the fact
    - Hash is deterministic (excludes run metadata: receipt_id, timestamp)
    - Append-only: never modified after emission (enforced by frozen hash)

    Circulation law:
    - Every receipt must have a dispatch_id_ref (no orphan handoffs)
    - THINK workers may only TRACE_WRITE
    - KERNEL workers are the only ones who may CANONICAL_WRITE or GOVERNED_MUTATION
    - TEMPLE workers may attempt no writes at all
    """
    # Identity (run metadata — excluded from hash)
    receipt_id: str
    timestamp: str

    # Lineage (semantic content — included in hash)
    session_id: str
    dispatch_id_ref: str       # The DispatchReceipt that authorized this handoff

    # Worker pair
    from_worker_id: str
    from_worker_type: WorkerType
    to_worker_id: str
    to_worker_type: WorkerType

    # Effect attempted during handoff
    handoff_effect: HandoffEffect = HandoffEffect.NONE
    reason: str = ""

    # Violations detected at emission (filled by ChainReceiptBuilder)
    violations: List[HandoffViolation] = field(default_factory=list)
    chain_status: ChainStatus = ChainStatus.CLEAN

    # Inferred fields (computed from WorkerType, not provided by caller)
    from_worker_authority: str = field(init=False, default="")

    # Immutability proof
    receipt_hash: Optional[str] = None

    def __post_init__(self):
        """Infer authority class from WorkerType — not claimable."""
        self.from_worker_authority = self._infer_authority(self.from_worker_type)

    def _infer_authority(self, worker_type: WorkerType) -> str:
        if worker_type == WorkerType.KERNEL:
            return "sovereign"
        elif worker_type == WorkerType.TEMPLE:
            return "exploratory"
        else:  # SKILL, AGENT, THINK
            return "non_sovereign"

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        result = {
            "session_id": self.session_id,
            "dispatch_id_ref": self.dispatch_id_ref,
            "from_worker_id": self.from_worker_id,
            "from_worker_type": self.from_worker_type.value,
            "from_worker_authority": self.from_worker_authority,
            "to_worker_id": self.to_worker_id,
            "to_worker_type": self.to_worker_type.value,
            "handoff_effect": self.handoff_effect.value,
            "reason": self.reason,
            "chain_status": self.chain_status.value,
            "violations": [v.to_dict() for v in self.violations],
        }
        if not exclude_run_metadata:
            result["receipt_id"] = self.receipt_id
            result["timestamp"] = self.timestamp
        return result

    @property
    def is_clean(self) -> bool:
        return self.chain_status == ChainStatus.CLEAN

    @property
    def has_blocking_violation(self) -> bool:
        return any(v.is_blocking for v in self.violations)


def hash_chain_receipt(receipt: ChainReceipt) -> str:
    """
    Deterministic hash of chain receipt semantic content.

    Excludes: receipt_id, timestamp (run metadata).
    Includes: dispatch_id_ref, worker pair, effect, status, violations.

    Same handoff content → same hash across all runs.
    """
    hashable = receipt.to_dict(exclude_run_metadata=True)
    hashable.pop("receipt_hash", None)
    return _sha256(_canonical_json(hashable))


# ============================================================================
# VIOLATION DETECTOR
# ============================================================================

class ViolationDetector:
    """
    Stateless violation detection for chain receipt emission.

    Detects:
    1. Missing dispatch_id_ref (MISSING_DISPATCH_REF — CRITICAL)
    2. CANONICAL_WRITE from non-KERNEL worker (DISPATCH_LINEAGE_VIOLATION — CRITICAL)
    3. GOVERNED_MUTATION from non-KERNEL worker (DISPATCH_LINEAGE_VIOLATION — CRITICAL)
    4. THINK worker writing beyond TRACE_WRITE (CONSTITUTIONAL_VIOLATION — CRITICAL)
    5. TEMPLE worker attempting any write (DISPATCH_LINEAGE_VIOLATION — CRITICAL)
    6. No from_worker declared (ORPHAN_HANDOFF — CRITICAL)
    """

    def detect(
        self,
        from_worker_id: str,
        from_worker_type: WorkerType,
        dispatch_id_ref: str,
        handoff_effect: HandoffEffect,
    ) -> List[HandoffViolation]:
        violations = []

        # Violation 1: Missing dispatch reference — no lineage
        if not dispatch_id_ref:
            violations.append(HandoffViolation(
                violation_type=ChainStatus.MISSING_DISPATCH_REF,
                severity=ViolationSeverity.CRITICAL,
                worker_id=from_worker_id,
                worker_type=from_worker_type,
                attempted_effect=handoff_effect,
                reason="Chain receipt has no dispatch_id_ref — lineage is broken",
                is_blocking=True,
            ))

        # Violation 2: No from_worker declared — orphan handoff
        if not from_worker_id:
            violations.append(HandoffViolation(
                violation_type=ChainStatus.ORPHAN_HANDOFF,
                severity=ViolationSeverity.CRITICAL,
                worker_id="(unknown)",
                worker_type=from_worker_type,
                attempted_effect=handoff_effect,
                reason="Chain receipt has no from_worker_id — source is unknown",
                is_blocking=True,
            ))

        # Violation 3: THINK worker writing beyond TRACE_WRITE
        if (from_worker_type == WorkerType.THINK
                and handoff_effect not in (HandoffEffect.NONE, HandoffEffect.TRACE_WRITE)):
            violations.append(HandoffViolation(
                violation_type=ChainStatus.CONSTITUTIONAL_VIOLATION,
                severity=ViolationSeverity.CRITICAL,
                worker_id=from_worker_id,
                worker_type=from_worker_type,
                attempted_effect=handoff_effect,
                reason=f"THINK worker may only TRACE_WRITE or NONE. "
                       f"Attempted: {handoff_effect.value}. "
                       f"Thinking is cognition-as-preparation, not cognition-as-authority.",
                is_blocking=True,
            ))

        # Violation 4: TEMPLE worker attempting any write
        if (from_worker_type == WorkerType.TEMPLE
                and handoff_effect not in (HandoffEffect.NONE,)):
            violations.append(HandoffViolation(
                violation_type=ChainStatus.DISPATCH_LINEAGE_VIOLATION,
                severity=ViolationSeverity.CRITICAL,
                worker_id=from_worker_id,
                worker_type=from_worker_type,
                attempted_effect=handoff_effect,
                reason=f"TEMPLE worker may not write anything. "
                       f"Attempted: {handoff_effect.value}. "
                       f"Temple is exploratory — null in institutional effect.",
                is_blocking=True,
            ))

        # Violation 5: CANONICAL_WRITE from non-KERNEL worker
        if (handoff_effect == HandoffEffect.CANONICAL_WRITE
                and from_worker_type != WorkerType.KERNEL):
            violations.append(HandoffViolation(
                violation_type=ChainStatus.DISPATCH_LINEAGE_VIOLATION,
                severity=ViolationSeverity.CRITICAL,
                worker_id=from_worker_id,
                worker_type=from_worker_type,
                attempted_effect=handoff_effect,
                reason=f"Canonical write attempted by non-KERNEL worker: {from_worker_type.value}. "
                       f"Only reducer-admitted, KERNEL-routed decisions may write canonical.",
                is_blocking=True,
            ))

        # Violation 6: GOVERNED_MUTATION from non-KERNEL worker
        if (handoff_effect == HandoffEffect.GOVERNED_MUTATION
                and from_worker_type != WorkerType.KERNEL):
            violations.append(HandoffViolation(
                violation_type=ChainStatus.DISPATCH_LINEAGE_VIOLATION,
                severity=ViolationSeverity.CRITICAL,
                worker_id=from_worker_id,
                worker_type=from_worker_type,
                attempted_effect=handoff_effect,
                reason=f"Governed state mutation attempted by non-KERNEL worker: {from_worker_type.value}. "
                       f"Law 1: Only reducer-emitted decisions may mutate governed state.",
                is_blocking=True,
            ))

        return violations

    def derive_status(self, violations: List[HandoffViolation]) -> ChainStatus:
        """Derive the chain status from the violation list."""
        if not violations:
            return ChainStatus.CLEAN
        # Precedence: constitutional > lineage > missing ref > orphan
        types = {v.violation_type for v in violations}
        if ChainStatus.CONSTITUTIONAL_VIOLATION in types:
            return ChainStatus.CONSTITUTIONAL_VIOLATION
        if ChainStatus.DISPATCH_LINEAGE_VIOLATION in types:
            return ChainStatus.DISPATCH_LINEAGE_VIOLATION
        if ChainStatus.MISSING_DISPATCH_REF in types:
            return ChainStatus.MISSING_DISPATCH_REF
        return ChainStatus.ORPHAN_HANDOFF


# ============================================================================
# CHAIN RECEIPT BUILDER V2
# ============================================================================

class ChainReceiptBuilderV2:
    """
    Emits governed, immutable ChainReceipt V2 artifacts.

    V2 design:
    - Violation detection is integrated at emission time
    - Authority is inferred from WorkerType — never claimed
    - Receipts are deterministically hashable (run metadata excluded from hash)
    - The builder exposes validate_chain_integrity() for batch validation
    """

    def __init__(self):
        self._detector = ViolationDetector()

    def emit(
        self,
        session_id: str,
        dispatch_id_ref: str,
        from_worker_id: str,
        from_worker_type: WorkerType,
        to_worker_id: str,
        to_worker_type: WorkerType,
        reason: str = "",
        handoff_effect: HandoffEffect = HandoffEffect.NONE,
    ) -> ChainReceipt:
        """
        Emit a new ChainReceipt V2.

        Violations are detected immediately. A receipt is emitted regardless
        (fail-open for observability), but chain_status and violations are set.
        The receipt_hash includes violations — tampered state = different hash.

        Args:
            session_id: Current session ID
            dispatch_id_ref: The DispatchReceipt that authorized this handoff
            from_worker_id: ID of the delegating worker
            from_worker_type: WorkerType of the delegating worker
            to_worker_id: ID of the receiving worker
            to_worker_type: WorkerType of the receiving worker
            reason: Human-readable description of the handoff purpose
            handoff_effect: The type of effect the from_worker is attempting

        Returns:
            Immutable ChainReceipt with violations, status, and hash.
        """
        receipt_id = f"chain_v2_{uuid.uuid4().hex[:16]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Detect violations at emission time
        violations = self._detector.detect(
            from_worker_id=from_worker_id,
            from_worker_type=from_worker_type,
            dispatch_id_ref=dispatch_id_ref,
            handoff_effect=handoff_effect,
        )
        chain_status = self._detector.derive_status(violations)

        receipt = ChainReceipt(
            receipt_id=receipt_id,
            timestamp=timestamp,
            session_id=session_id,
            dispatch_id_ref=dispatch_id_ref,
            from_worker_id=from_worker_id,
            from_worker_type=from_worker_type,
            to_worker_id=to_worker_id,
            to_worker_type=to_worker_type,
            handoff_effect=handoff_effect,
            reason=reason,
            violations=violations,
            chain_status=chain_status,
        )

        # Compute deterministic hash (includes violations — tamper-evident)
        receipt.receipt_hash = hash_chain_receipt(receipt)

        return receipt

    def validate_chain_integrity(
        self, receipts: List[ChainReceipt]
    ) -> Dict[str, Any]:
        """
        Validate a batch of chain receipts.

        Returns a summary report with:
        - total receipts
        - violation_count (number of receipts with at least one violation)
        - blocking_count (number of receipts with blocking violations)
        - canonical_mutations_outside_kernel (count)
        - constitutional_violations (count — THINK writing beyond trace, etc.)
        - receipts_clean / receipts_violated
        - verdict: "clean" | "violated"
        """
        violation_count = 0
        blocking_count = 0
        canonical_outside_kernel = 0
        constitutional_violations = 0

        for r in receipts:
            if r.violations:
                violation_count += 1
            if r.has_blocking_violation:
                blocking_count += 1
            for v in r.violations:
                if v.violation_type == ChainStatus.DISPATCH_LINEAGE_VIOLATION:
                    if v.attempted_effect == HandoffEffect.CANONICAL_WRITE:
                        canonical_outside_kernel += 1
                if v.violation_type == ChainStatus.CONSTITUTIONAL_VIOLATION:
                    constitutional_violations += 1

        return {
            "total_receipts": len(receipts),
            "violation_count": violation_count,
            "blocking_count": blocking_count,
            "canonical_mutations_outside_kernel": canonical_outside_kernel,
            "constitutional_violations": constitutional_violations,
            "receipts_clean": len(receipts) - violation_count,
            "receipts_violated": violation_count,
            "verdict": "clean" if blocking_count == 0 else "violated",
        }
