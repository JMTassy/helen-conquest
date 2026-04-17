"""Frozen data structures for bounded execution (Stage B.1).

Operationalizes 6 ratification patches from
KNOWLEDGE_COMPILER_V2_IMPLEMENTATION_SPECIFICATION.md:

  Patch 01 — ExecutionKey & IdempotenceStatus
  Patch 02 — ROUTE non-sovereignty
  Patch 03 — TargetResolutionState & TargetObjectModel
  Patch 04 — StateTransition (pre/post hash law)
  Patch 05 — Receipt role separation (DECISION / RESULT / ARTIFACT)
  Patch 06 — HandlerFailure taxonomy & deterministic FailureMapping
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

POLICY_VERSION = "v2.0.0"

# ---------------------------------------------------------------------------
# PATCH 01 — Canonical Execution Identity
# ---------------------------------------------------------------------------

class IdempotenceStatus(str, Enum):
    """Result of idempotence check (PATCH 01)."""
    NEW = "NEW"           # First execution of this ExecKey
    DUPLICATE = "DUPLICATE"  # Prior terminal receipt exists — skip
    CONFLICT = "CONFLICT"    # Should not occur; indicates hash collision


def _jcs(obj: Any) -> bytes:
    """Canonical JSON (sort_keys, no spaces) — deterministic."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def compute_exec_key(
    *,
    tool_type: str,
    normalized_target: str,
    payload: Dict[str, Any],
    pre_state_hash: str,
    policy_version: str = POLICY_VERSION,
) -> str:
    """Frozen ExecKey formula (PATCH 01).

    ExecKey = H(tool_type, normalized_target, normalized_payload_hash,
                pre_state_hash, policy_version)

    Invariant: different pre_state_hash → different ExecKey even if
    tool_type + target + payload are identical. Prevents false skips.
    """
    payload_hash = hashlib.sha256(_jcs(payload)).hexdigest()
    key_dict = {
        "tool_type": tool_type,
        "normalized_target": normalized_target,
        "normalized_payload_hash": payload_hash,
        "pre_state_hash": pre_state_hash,
        "policy_version": policy_version,
    }
    return hashlib.sha256(_jcs(key_dict)).hexdigest()


def compute_state_hash(session_state: Dict[str, Any], target_metadata: Optional[Dict[str, Any]] = None, prior_artifact_hashes: Optional[List[str]] = None) -> str:
    """Frozen pre/post-state hash formula (PATCH 04).

    pre_state_hash = H(session.state, target.metadata, prior_artifacts)
    """
    state_dict = {
        "session_state": session_state,
        "target_metadata": target_metadata or {},
        "prior_artifact_hashes": sorted(prior_artifact_hashes or []),
    }
    return hashlib.sha256(_jcs(state_dict)).hexdigest()


# ---------------------------------------------------------------------------
# PATCH 02 — ROUTE Non-Sovereignty Assertion
# ---------------------------------------------------------------------------

ROUTE_NON_SOVEREIGNTY_ASSERTION = (
    "ROUTE artifact is a non-sovereign advisory or queue record. "
    "It carries zero authority over remote execution. "
    "The presence of a queue receipt does NOT confirm, authorize, or commit "
    "the target service to execute the queued work."
)


# ---------------------------------------------------------------------------
# PATCH 03 — Target Resolution State & Object Model
# ---------------------------------------------------------------------------

class TargetResolutionStatus(str, Enum):
    """Frozen target resolution states (PATCH 03).

    RESOLVED   — target resolves to exactly one object; mutation may proceed
    AMBIGUOUS  — target matches >1 object; fail-closed
    MISSING    — target does not exist (handler-specific handling)
    CONFLICTING — target exists but preconditions fail
    """
    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"


@dataclass
class TargetResolutionState:
    """Result of target resolution (PATCH 03)."""
    status: TargetResolutionStatus
    target_selector: str           # original target from plan
    normalized_path: str           # canonical absolute path
    resolved_target_id: str        # unique id (inode / registry key)
    resolution_evidence: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_detail: Optional[str] = None


def resolve_target(target: str, base_dir: Optional[Path] = None) -> TargetResolutionState:
    """Resolve and validate a file-system target (PATCH 03).

    Rules:
      1. Must be absolute path (or resolve to one within base_dir)
      2. Must not contain .. (path traversal)
      3. Must resolve to exactly one object
    """
    # Absolute path required
    p = Path(target)
    if base_dir:
        # Relative paths resolved within base_dir, then checked for escape
        try:
            resolved = (base_dir / target).resolve()
            resolved.relative_to(base_dir.resolve())  # raises if escape
            p = resolved
        except ValueError:
            return TargetResolutionState(
                status=TargetResolutionStatus.CONFLICTING,
                target_selector=target,
                normalized_path=str(p),
                resolved_target_id="",
                error_code="INVALID_TARGET_PATH",
                error_detail="Target escapes base_dir",
            )
    else:
        if not p.is_absolute():
            return TargetResolutionState(
                status=TargetResolutionStatus.CONFLICTING,
                target_selector=target,
                normalized_path=target,
                resolved_target_id="",
                error_code="INVALID_TARGET_PATH",
                error_detail="Target must be absolute path",
            )

    # Reject path traversal
    if ".." in p.parts:
        return TargetResolutionState(
            status=TargetResolutionStatus.CONFLICTING,
            target_selector=target,
            normalized_path=str(p),
            resolved_target_id="",
            error_code="INVALID_TARGET_PATH",
            error_detail="Target contains path traversal (..)",
        )

    # Check existence
    if not p.exists():
        return TargetResolutionState(
            status=TargetResolutionStatus.MISSING,
            target_selector=target,
            normalized_path=str(p),
            resolved_target_id="",
            resolution_evidence={"exists": False},
        )

    # Check permissions
    if not os.access(p, os.R_OK):
        return TargetResolutionState(
            status=TargetResolutionStatus.CONFLICTING,
            target_selector=target,
            normalized_path=str(p),
            resolved_target_id="",
            error_code="TARGET_INACCESSIBLE",
            error_detail="Permission denied",
        )

    stat = p.stat()
    return TargetResolutionState(
        status=TargetResolutionStatus.RESOLVED,
        target_selector=target,
        normalized_path=str(p),
        resolved_target_id=f"inode:{stat.st_ino}",
        resolution_evidence={
            "exists": True,
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "mode": oct(stat.st_mode),
        },
    )


# ---------------------------------------------------------------------------
# PATCH 04 — Pre/Post State Hash Law
# ---------------------------------------------------------------------------

class TransitionStatus(str, Enum):
    """State transition verification result (PATCH 04)."""
    VERIFIED = "VERIFIED"      # post_state_hash matches expected
    FAILED = "FAILED"          # execution failed; no post state
    CONFLICTING = "CONFLICTING" # post_state_hash ≠ expected (drift)


@dataclass
class StateTransition:
    """Pre/post-state hash pair for mutation verification (PATCH 04).

    Mandatory for ALL mutating handlers (WRITE, EDIT).
    Non-mutating (ANALYZE, ROUTE): post_state_hash == pre_state_hash.
    """
    pre_state_hash: str
    post_state_hash: str
    transition_status: TransitionStatus
    drift_detected: bool = False

    @classmethod
    def noop(cls, pre_state_hash: str) -> "StateTransition":
        """Non-mutating result: state unchanged."""
        return cls(
            pre_state_hash=pre_state_hash,
            post_state_hash=pre_state_hash,
            transition_status=TransitionStatus.VERIFIED,
            drift_detected=False,
        )

    @classmethod
    def failed(cls, pre_state_hash: str) -> "StateTransition":
        """Execution failed: no post state."""
        return cls(
            pre_state_hash=pre_state_hash,
            post_state_hash=pre_state_hash,
            transition_status=TransitionStatus.FAILED,
            drift_detected=False,
        )

    def verify(self, expected_post_hash: str) -> bool:
        """Check post-state matches expected (replay/determinism test)."""
        return self.post_state_hash == expected_post_hash


# ---------------------------------------------------------------------------
# PATCH 05 — Receipt Role Separation
# ---------------------------------------------------------------------------

class ReceiptRole(str, Enum):
    """Explicit receipt role (PATCH 05) — no role can carry authority."""
    AUTHORIZATION = "authorization_before_execution"   # EXECUTION_DECISION
    WITNESS_ATTEMPT = "witness_to_execution_attempt"   # EXECUTION_RESULT
    WITNESS_ARTIFACT = "witness_to_artifact_and_state_change"  # ARTIFACT_WRITE
    WITNESS_NOOP = "witness_to_idempotent_noop"        # ARTIFACT_NOOP


@dataclass(frozen=True)
class ExecutionDecision:
    """Pre-execution authorization receipt (PATCH 05).

    Emitted BEFORE handler execution.
    Semantics: "Authorization to execute this plan."
    Sovereignty: NON-SOVEREIGN. Does not predict success.
    """
    receipt_type: Literal["EXECUTION_DECISION"] = "EXECUTION_DECISION"
    receipt_role: ReceiptRole = ReceiptRole.AUTHORIZATION
    is_sovereign: bool = False          # ALWAYS False

    session_id: str = ""
    action_id: str = ""
    exec_key: str = ""

    # Authorization basis (frozen)
    decision_basis: str = "frozen_execution_plan"
    decision_mode: str = "non_interpretive_execution"
    confidence: None = None             # NEVER a prediction — always None

    # Execution intent
    execution_type: str = ""
    target: str = ""
    normalized_target: str = ""

    # State before execution
    pre_state_hash: str = ""

    def __post_init__(self) -> None:
        assert not self.is_sovereign, "ExecutionDecision must never be sovereign"
        assert self.confidence is None, "confidence must always be None (not a prediction)"


@dataclass(frozen=True)
class ExecutionResult:
    """Post-execution witness receipt (PATCH 05).

    Emitted AFTER handler attempted execution (success or failure).
    Semantics: "Handler ran and produced this outcome."
    Sovereignty: NON-SOVEREIGN. Status=SUCCESS means handler completed,
    NOT that remote/target system accepted the work.
    """
    receipt_type: Literal["EXECUTION_RESULT"] = "EXECUTION_RESULT"
    receipt_role: ReceiptRole = ReceiptRole.WITNESS_ATTEMPT
    is_sovereign: bool = False

    session_id: str = ""
    action_id: str = ""
    exec_key: str = ""

    status: Literal["SUCCESS", "FAILED", "TIMEOUT", "SKIPPED"] = "FAILED"
    result_hash: Optional[str] = None
    latency_ms: float = 0.0

    error_code: Optional[str] = None
    error_detail: Optional[str] = None

    # Lineage — binds to EXECUTION_DECISION
    decision_receipt_hash: Optional[str] = None

    def __post_init__(self) -> None:
        assert not self.is_sovereign, "ExecutionResult must never be sovereign"


@dataclass(frozen=True)
class ArtifactWrite:
    """Post-artifact verification receipt (PATCH 05).

    Emitted AFTER artifact verified.
    Semantics: "Artifact was recorded and hashes match."
    Sovereignty: NON-SOVEREIGN. ROUTE artifact_type='queue_receipt' does NOT
    imply remote execution happened.
    """
    receipt_type: Literal["ARTIFACT_WRITE", "ARTIFACT_NOOP"] = "ARTIFACT_WRITE"
    receipt_role: ReceiptRole = ReceiptRole.WITNESS_ARTIFACT
    is_sovereign: bool = False

    session_id: str = ""
    action_id: str = ""

    artifact_type: str = "file"  # "file"|"analysis_result"|"queue_receipt"|"routing_advisory"
    artifact_hash: Optional[str] = None
    artifact_uri: str = ""

    # State transition
    pre_state_hash: str = ""
    post_state_hash: str = ""
    drift_detected: bool = False

    # Non-sovereignty assertion for ROUTE
    non_sovereignty_assertion: Optional[str] = None

    # Lineage — binds to EXECUTION_RESULT
    execution_receipt_hash: Optional[str] = None

    def __post_init__(self) -> None:
        assert not self.is_sovereign, "ArtifactWrite must never be sovereign"


# ---------------------------------------------------------------------------
# PATCH 06 — Failure Taxonomy & Deterministic Mapping
# ---------------------------------------------------------------------------

class HandlerFailure(str, Enum):
    """Frozen failure codes — 4 categories, 14 codes (PATCH 06)."""

    # Category A: Invalid Input / Validation
    INVALID_TARGET_PATH = "invalid_target_path"
    AMBIGUOUS_TARGET = "ambiguous_target"
    TARGET_NOT_FOUND = "target_not_found"
    PRECONDITION_FAILED = "precondition_failed"
    INVALID_PAYLOAD = "invalid_payload"
    BOUNDS_VIOLATION = "bounds_violation"

    # Category B: State Conflicts
    CONFLICTING_PRE_STATE = "conflicting_pre_state"
    TARGET_LOCKED = "target_locked"
    TARGET_INACCESSIBLE = "target_inaccessible"
    CONCURRENT_MODIFICATION = "concurrent_modification"

    # Category C: Execution Errors
    EXECUTION_ERROR = "execution_error"
    ARTIFACT_WRITE_FAILED = "artifact_write_failed"
    RECEIPT_EMISSION_FAILED = "receipt_emission_failed"
    TIMEOUT = "timeout"

    # Category D: Idempotence & Rerun
    DUPLICATE_EXECUTION = "duplicate_execution"
    DRIFT_DETECTED = "drift_detected"


# Deterministic receipt mapping: (failure_code, phase) → (receipt_type, status, http_code)
# Pure function — no ambiguity, no invention (PATCH 06).
_FAILURE_MAPPING: Dict[Tuple[HandlerFailure, str], Tuple[str, str, int]] = {
    # Decision-phase failures → 400
    (HandlerFailure.INVALID_TARGET_PATH, "DECISION"):    ("EXECUTION_DECISION", "FAILED", 400),
    (HandlerFailure.AMBIGUOUS_TARGET,    "DECISION"):    ("EXECUTION_DECISION", "FAILED", 400),
    (HandlerFailure.PRECONDITION_FAILED, "DECISION"):    ("EXECUTION_DECISION", "FAILED", 400),
    (HandlerFailure.INVALID_PAYLOAD,     "DECISION"):    ("EXECUTION_DECISION", "FAILED", 400),
    (HandlerFailure.BOUNDS_VIOLATION,    "DECISION"):    ("EXECUTION_DECISION", "FAILED", 400),

    # Execution-phase failures → 200 (request OK, execution failed)
    (HandlerFailure.TARGET_NOT_FOUND,          "EXECUTION"): ("EXECUTION_RESULT", "FAILED", 200),
    (HandlerFailure.TARGET_LOCKED,             "EXECUTION"): ("EXECUTION_RESULT", "FAILED", 200),
    (HandlerFailure.TARGET_INACCESSIBLE,       "EXECUTION"): ("EXECUTION_RESULT", "FAILED", 200),
    (HandlerFailure.CONFLICTING_PRE_STATE,     "EXECUTION"): ("EXECUTION_RESULT", "FAILED", 200),
    (HandlerFailure.EXECUTION_ERROR,           "EXECUTION"): ("EXECUTION_RESULT", "FAILED", 200),
    (HandlerFailure.TIMEOUT,                   "EXECUTION"): ("EXECUTION_RESULT", "FAILED", 200),
    (HandlerFailure.CONCURRENT_MODIFICATION,   "EXECUTION"): ("EXECUTION_RESULT", "FAILED", 200),

    # Artifact-phase failures → 200
    (HandlerFailure.ARTIFACT_WRITE_FAILED,   "ARTIFACT"): ("ARTIFACT_WRITE", "FAILED", 200),
    (HandlerFailure.RECEIPT_EMISSION_FAILED, "ARTIFACT"): ("ARTIFACT_WRITE", "FAILED", 200),
    (HandlerFailure.DRIFT_DETECTED,          "ARTIFACT"): ("ARTIFACT_WRITE", "FAILED", 200),

    # Idempotence → NOOP → 200
    (HandlerFailure.DUPLICATE_EXECUTION, "IDEMPOTENCE"): ("ARTIFACT_NOOP", "SKIPPED", 200),
}


def failure_mapping(
    failure_code: HandlerFailure,
    phase: Literal["DECISION", "EXECUTION", "ARTIFACT", "IDEMPOTENCE"],
) -> Tuple[str, str, int]:
    """Pure function: (failure_code, phase) → (receipt_type, status, http_code).

    No ambiguity. Developers cannot invent new codes or mappings.
    Raises KeyError if unmapped combination (constitutional violation).
    """
    key = (failure_code, phase)
    if key not in _FAILURE_MAPPING:
        raise KeyError(
            f"No mapping for ({failure_code.value!r}, {phase!r}). "
            "Add to _FAILURE_MAPPING or fix failure_code."
        )
    return _FAILURE_MAPPING[key]


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

__all__ = [
    # Patch 01
    "IdempotenceStatus",
    "compute_exec_key",
    "compute_state_hash",
    # Patch 02
    "ROUTE_NON_SOVEREIGNTY_ASSERTION",
    # Patch 03
    "TargetResolutionStatus",
    "TargetResolutionState",
    "resolve_target",
    # Patch 04
    "TransitionStatus",
    "StateTransition",
    # Patch 05
    "ReceiptRole",
    "ExecutionDecision",
    "ExecutionResult",
    "ArtifactWrite",
    # Patch 06
    "HandlerFailure",
    "failure_mapping",
    # Utilities
    "POLICY_VERSION",
    "compute_exec_key",
]
