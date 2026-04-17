"""Tool handler implementations for Stage B.1 bounded execution.

Four frozen handlers — each enforces the 3-receipt spine:
  EXECUTION_DECISION → EXECUTION_RESULT → ARTIFACT_WRITE | ARTIFACT_NOOP

Handler contracts (from KNOWLEDGE_COMPILER_V2_IMPLEMENTATION_SPECIFICATION.md):

  WriteFileHandler  — creates or overwrites a file; target may be MISSING (new) or RESOLVED
  EditFileHandler   — edits existing file (append / replace); target MUST be RESOLVED
  AnalyzeHandler    — reads and analyzes; non-mutating (post_state == pre_state)
  RouteHandler      — emits routing advisory; non-sovereign, no execution side-effects

Forbidden effects (never violated by any handler):
  - WriteFileHandler  may not read arbitrary FS paths beyond its target
  - EditFileHandler   may not change file type or replace with binary
  - AnalyzeHandler    may not write any file or mutate external state
  - RouteHandler      may not confirm, authorize, or trigger remote execution
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    POLICY_VERSION,
    ROUTE_NON_SOVEREIGNTY_ASSERTION,
    ArtifactWrite,
    ExecutionDecision,
    ExecutionResult,
    HandlerFailure,
    IdempotenceStatus,
    ReceiptRole,
    StateTransition,
    TargetResolutionState,
    TargetResolutionStatus,
    TransitionStatus,
    _jcs,
    compute_exec_key,
    compute_state_hash,
    failure_mapping,
    resolve_target,
)


# ---------------------------------------------------------------------------
# Handler result — carries the 3-receipt spine + output artifact
# ---------------------------------------------------------------------------

@dataclass
class HandlerResult:
    """Immutable result from any handler invocation.

    Attributes:
        decision_receipt    — EXECUTION_DECISION (pre-execution)
        execution_receipt   — EXECUTION_RESULT (post-attempt)
        artifact_receipt    — ARTIFACT_WRITE or ARTIFACT_NOOP
        idempotence_status  — NEW | DUPLICATE | CONFLICT
        state_transition    — pre/post hash pair
        output_data         — handler-specific output (analysis dict, route record, etc.)
        success             — True iff all three receipts are non-failure
    """
    decision_receipt:  ExecutionDecision
    execution_receipt: ExecutionResult
    artifact_receipt:  ArtifactWrite
    idempotence_status: IdempotenceStatus
    state_transition:  StateTransition
    output_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return (
            self.execution_receipt.status == "SUCCESS"
            and self.artifact_receipt.receipt_type != "ARTIFACT_NOOP"
        ) or self.idempotence_status == IdempotenceStatus.DUPLICATE

    @property
    def spine(self) -> Tuple[ExecutionDecision, ExecutionResult, ArtifactWrite]:
        """The 3-receipt spine, in canonical order."""
        return (self.decision_receipt, self.execution_receipt, self.artifact_receipt)


# ---------------------------------------------------------------------------
# Idempotence registry (in-memory for tests; swap for persistent store)
# ---------------------------------------------------------------------------

class IdempotenceRegistry:
    """Key-value store: exec_key → terminal ExecutionResult.

    Production: back with SQLite / Redis.
    Test: in-memory (default).
    """

    def __init__(self) -> None:
        self._store: Dict[str, ExecutionResult] = {}

    def check(self, exec_key: str) -> IdempotenceStatus:
        if exec_key in self._store:
            return IdempotenceStatus.DUPLICATE
        return IdempotenceStatus.NEW

    def register(self, exec_key: str, result: ExecutionResult) -> None:
        if exec_key in self._store:
            return  # idempotent: never overwrite a terminal receipt
        self._store[exec_key] = result

    def get(self, exec_key: str) -> Optional[ExecutionResult]:
        return self._store.get(exec_key)

    def clear(self) -> None:
        self._store.clear()


# Default registry (shared by handlers unless overridden)
_DEFAULT_REGISTRY = IdempotenceRegistry()


# ---------------------------------------------------------------------------
# Base handler
# ---------------------------------------------------------------------------

class BaseHandler(ABC):
    """Abstract base for all tool handlers.

    Subclasses implement:
      _validate()  — DECISION phase; raises HandlerFailure or returns ok
      _execute()   — EXECUTION phase; returns (output_data, artifact_hash, artifact_uri)
      _tool_type   — string constant (e.g. "WRITE_FILE")
    """

    _tool_type: str = "BASE"

    def __init__(self, registry: Optional[IdempotenceRegistry] = None) -> None:
        # Per-instance registry by default — prevents cross-test contamination.
        # Pass an explicit registry to share state across calls (idempotence tests).
        self._registry = registry if registry is not None else IdempotenceRegistry()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(
        self,
        *,
        action_id: str,
        session_id: str,
        target: str,
        payload: Dict[str, Any],
        session_state: Dict[str, Any],
        prior_artifact_hashes: Optional[List[str]] = None,
        base_dir: Optional[Path] = None,
    ) -> HandlerResult:
        """Execute the full 3-receipt lifecycle.

        Phase order (never inverted):
          1. DECISION   — validate, compute ExecKey, emit ExecutionDecision
          2. IDEMPOTENCE — check registry; short-circuit to ARTIFACT_NOOP if DUPLICATE
          3. EXECUTION  — call _execute(); emit ExecutionResult
          4. ARTIFACT   — compute post-state, emit ArtifactWrite
        """
        t_start = time.monotonic()

        # ── Resolve target ────────────────────────────────────────────
        target_state = resolve_target(target, base_dir)

        # ── DECISION phase ────────────────────────────────────────────
        pre_state_hash = compute_state_hash(
            session_state=session_state,
            target_metadata=target_state.resolution_evidence,
            prior_artifact_hashes=prior_artifact_hashes,
        )

        # Validate (handler-specific); may short-circuit with failure receipt
        validation_error = self._validate(target_state, payload)
        if validation_error is not None:
            return self._fail_decision(
                action_id=action_id,
                session_id=session_id,
                target=target,
                pre_state_hash=pre_state_hash,
                failure=validation_error,
                payload=payload,
            )

        exec_key = compute_exec_key(
            tool_type=self._tool_type,
            normalized_target=target_state.normalized_path,
            payload=payload,
            pre_state_hash=pre_state_hash,
        )

        decision = ExecutionDecision(
            session_id=session_id,
            action_id=action_id,
            exec_key=exec_key,
            execution_type=self._tool_type,
            target=target,
            normalized_target=target_state.normalized_path,
            pre_state_hash=pre_state_hash,
        )

        # ── IDEMPOTENCE check ─────────────────────────────────────────
        idempotence_status = self._registry.check(exec_key)
        if idempotence_status == IdempotenceStatus.DUPLICATE:
            prior_result = self._registry.get(exec_key)
            noop_artifact = ArtifactWrite(
                receipt_type="ARTIFACT_NOOP",
                receipt_role=ReceiptRole.WITNESS_NOOP,
                session_id=session_id,
                action_id=action_id,
                artifact_type="noop",
                pre_state_hash=pre_state_hash,
                post_state_hash=pre_state_hash,
                execution_receipt_hash=self._hash_receipt(prior_result) if prior_result else None,
            )
            return HandlerResult(
                decision_receipt=decision,
                execution_receipt=prior_result or ExecutionResult(
                    session_id=session_id,
                    action_id=action_id,
                    exec_key=exec_key,
                    status="SKIPPED",
                ),
                artifact_receipt=noop_artifact,
                idempotence_status=IdempotenceStatus.DUPLICATE,
                state_transition=StateTransition.noop(pre_state_hash),
            )

        # ── EXECUTION phase ───────────────────────────────────────────
        t_exec_start = time.monotonic()
        exec_error: Optional[HandlerFailure] = None
        output_data: Dict[str, Any] = {}
        artifact_hash: Optional[str] = None
        artifact_uri: str = ""
        artifact_type: str = "unknown"

        try:
            output_data, artifact_hash, artifact_uri, artifact_type = self._execute(
                target_state=target_state,
                payload=payload,
                session_state=session_state,
            )
        except _HandlerExecutionError as exc:
            exec_error = exc.failure_code

        latency_ms = (time.monotonic() - t_exec_start) * 1000.0
        decision_hash = self._hash_receipt(decision)

        if exec_error is not None:
            receipt_type, status, _ = failure_mapping(exec_error, "EXECUTION")
            exec_result = ExecutionResult(
                session_id=session_id,
                action_id=action_id,
                exec_key=exec_key,
                status=status,  # type: ignore[arg-type]
                latency_ms=latency_ms,
                error_code=exec_error.value,
                decision_receipt_hash=decision_hash,
            )
            self._registry.register(exec_key, exec_result)
            fail_artifact = ArtifactWrite(
                receipt_type="ARTIFACT_WRITE",
                receipt_role=ReceiptRole.WITNESS_ARTIFACT,
                session_id=session_id,
                action_id=action_id,
                artifact_type="failure_record",
                pre_state_hash=pre_state_hash,
                post_state_hash=pre_state_hash,
                drift_detected=False,
                execution_receipt_hash=self._hash_receipt(exec_result),
            )
            return HandlerResult(
                decision_receipt=decision,
                execution_receipt=exec_result,
                artifact_receipt=fail_artifact,
                idempotence_status=IdempotenceStatus.NEW,
                state_transition=StateTransition.failed(pre_state_hash),
                output_data=output_data,
            )

        # ── ARTIFACT phase ────────────────────────────────────────────
        post_state_hash = self._compute_post_state(
            session_state=session_state,
            target=target_state.normalized_path,
            artifact_hash=artifact_hash,
            prior_artifact_hashes=prior_artifact_hashes,
            pre_state_hash=pre_state_hash,
        )
        drift = post_state_hash == pre_state_hash and self._is_mutating()

        exec_result = ExecutionResult(
            session_id=session_id,
            action_id=action_id,
            exec_key=exec_key,
            status="SUCCESS",
            result_hash=artifact_hash,
            latency_ms=latency_ms,
            decision_receipt_hash=decision_hash,
        )
        self._registry.register(exec_key, exec_result)

        state_transition = StateTransition(
            pre_state_hash=pre_state_hash,
            post_state_hash=post_state_hash,
            transition_status=TransitionStatus.VERIFIED,
            drift_detected=drift,
        )

        artifact = ArtifactWrite(
            receipt_type="ARTIFACT_WRITE",
            receipt_role=ReceiptRole.WITNESS_ARTIFACT,
            session_id=session_id,
            action_id=action_id,
            artifact_type=artifact_type,
            artifact_hash=artifact_hash,
            artifact_uri=artifact_uri,
            pre_state_hash=pre_state_hash,
            post_state_hash=post_state_hash,
            drift_detected=drift,
            non_sovereignty_assertion=self._non_sovereignty_assertion(),
            execution_receipt_hash=self._hash_receipt(exec_result),
        )

        return HandlerResult(
            decision_receipt=decision,
            execution_receipt=exec_result,
            artifact_receipt=artifact,
            idempotence_status=IdempotenceStatus.NEW,
            state_transition=state_transition,
            output_data=output_data,
        )

    # ------------------------------------------------------------------
    # Subclass contract
    # ------------------------------------------------------------------

    @abstractmethod
    def _validate(
        self,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
    ) -> Optional[HandlerFailure]:
        """Return a HandlerFailure if input is invalid, else None."""

    @abstractmethod
    def _execute(
        self,
        *,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[str], str, str]:
        """Perform the actual operation.

        Returns: (output_data, artifact_hash, artifact_uri, artifact_type)
        Raises:  _HandlerExecutionError on execution failure.
        """

    def _is_mutating(self) -> bool:
        """True for handlers that write to external state."""
        return False

    def _non_sovereignty_assertion(self) -> Optional[str]:
        """Override in RouteHandler."""
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail_decision(
        self,
        *,
        action_id: str,
        session_id: str,
        target: str,
        pre_state_hash: str,
        failure: HandlerFailure,
        payload: Dict[str, Any],
    ) -> HandlerResult:
        """Build a DECISION-phase failure result (3-receipt spine, all failed)."""
        exec_key = compute_exec_key(
            tool_type=self._tool_type,
            normalized_target=target,
            payload=payload,
            pre_state_hash=pre_state_hash,
        )
        decision = ExecutionDecision(
            session_id=session_id,
            action_id=action_id,
            exec_key=exec_key,
            execution_type=self._tool_type,
            target=target,
            normalized_target=target,
            pre_state_hash=pre_state_hash,
        )
        _, status, _ = failure_mapping(failure, "DECISION")
        exec_result = ExecutionResult(
            session_id=session_id,
            action_id=action_id,
            exec_key=exec_key,
            status=status,  # type: ignore[arg-type]
            error_code=failure.value,
            decision_receipt_hash=self._hash_receipt(decision),
        )
        artifact = ArtifactWrite(
            receipt_type="ARTIFACT_WRITE",
            receipt_role=ReceiptRole.WITNESS_ARTIFACT,
            session_id=session_id,
            action_id=action_id,
            artifact_type="failure_record",
            pre_state_hash=pre_state_hash,
            post_state_hash=pre_state_hash,
            execution_receipt_hash=self._hash_receipt(exec_result),
        )
        return HandlerResult(
            decision_receipt=decision,
            execution_receipt=exec_result,
            artifact_receipt=artifact,
            idempotence_status=IdempotenceStatus.NEW,
            state_transition=StateTransition.failed(pre_state_hash),
        )

    @staticmethod
    def _hash_receipt(receipt: Any) -> str:
        """SHA-256 of the receipt's canonical JSON representation."""
        if receipt is None:
            return ""
        # dataclass → dict via __dataclass_fields__
        d = {k: getattr(receipt, k) for k in receipt.__dataclass_fields__}
        return hashlib.sha256(_jcs(d)).hexdigest()

    def _compute_post_state(
        self,
        *,
        session_state: Dict[str, Any],
        target: str,
        artifact_hash: Optional[str],
        prior_artifact_hashes: Optional[List[str]],
        pre_state_hash: str,
    ) -> str:
        new_prior = list(prior_artifact_hashes or [])
        if artifact_hash:
            new_prior.append(artifact_hash)
        target_meta: Dict[str, Any] = {}
        p = Path(target)
        if p.exists():
            stat = p.stat()
            target_meta = {"size": stat.st_size, "mtime": stat.st_mtime}
        return compute_state_hash(
            session_state=session_state,
            target_metadata=target_meta,
            prior_artifact_hashes=new_prior,
        )


class _HandlerExecutionError(Exception):
    """Internal exception used inside _execute() to signal failure."""

    def __init__(self, failure_code: HandlerFailure) -> None:
        super().__init__(failure_code.value)
        self.failure_code = failure_code


# ---------------------------------------------------------------------------
# WriteFileHandler
# ---------------------------------------------------------------------------

class WriteFileHandler(BaseHandler):
    """Creates or overwrites a file with provided content.

    Target resolution:
      RESOLVED → overwrite existing file
      MISSING  → create new file (parent must exist)
      AMBIGUOUS / CONFLICTING → fail-closed (DECISION phase)

    Forbidden effects:
      - May not read arbitrary FS paths beyond its target
      - May not execute shell commands
    """

    _tool_type = "WRITE_FILE"

    def _is_mutating(self) -> bool:
        return True

    def _validate(
        self,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
    ) -> Optional[HandlerFailure]:
        # Target must be RESOLVED or MISSING (new file creation allowed)
        if target_state.status == TargetResolutionStatus.AMBIGUOUS:
            return HandlerFailure.AMBIGUOUS_TARGET
        if target_state.status == TargetResolutionStatus.CONFLICTING:
            if target_state.error_code == "TARGET_INACCESSIBLE":
                return HandlerFailure.TARGET_INACCESSIBLE
            return HandlerFailure.INVALID_TARGET_PATH

        # Payload must contain 'content' key (str)
        if "content" not in payload:
            return HandlerFailure.INVALID_PAYLOAD
        if not isinstance(payload["content"], str):
            return HandlerFailure.INVALID_PAYLOAD

        # Parent directory must exist for new files
        if target_state.status == TargetResolutionStatus.MISSING:
            parent = Path(target_state.normalized_path).parent
            if not parent.exists():
                return HandlerFailure.INVALID_TARGET_PATH

        return None

    def _execute(
        self,
        *,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[str], str, str]:
        content: str = payload["content"]
        path = Path(target_state.normalized_path)

        try:
            path.write_text(content, encoding="utf-8")
        except PermissionError:
            raise _HandlerExecutionError(HandlerFailure.TARGET_INACCESSIBLE)
        except OSError as exc:
            raise _HandlerExecutionError(HandlerFailure.EXECUTION_ERROR)

        artifact_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        artifact_uri = f"file://{path}"
        output_data = {
            "bytes_written": len(content.encode("utf-8")),
            "path": str(path),
            "content_hash": artifact_hash,
        }
        return output_data, artifact_hash, artifact_uri, "file"


# ---------------------------------------------------------------------------
# EditFileHandler
# ---------------------------------------------------------------------------

class EditFileHandler(BaseHandler):
    """Edits an existing file by appending or replacing a substring.

    Target resolution:
      RESOLVED  → proceed
      MISSING   → fail-closed (EXECUTION phase, not DECISION)
      AMBIGUOUS / CONFLICTING → fail-closed (DECISION phase)

    Payload keys:
      mode          : "append" | "replace"
      content       : str  — content to append, OR replacement text
      old_string    : str  — (required for mode="replace") text to replace
      encoding      : str  — default "utf-8"

    Forbidden effects:
      - May not change file type or replace content with binary
      - May not create new files
    """

    _tool_type = "EDIT_FILE"

    def _is_mutating(self) -> bool:
        return True

    def _validate(
        self,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
    ) -> Optional[HandlerFailure]:
        if target_state.status == TargetResolutionStatus.AMBIGUOUS:
            return HandlerFailure.AMBIGUOUS_TARGET
        if target_state.status == TargetResolutionStatus.CONFLICTING:
            if target_state.error_code == "TARGET_INACCESSIBLE":
                return HandlerFailure.TARGET_INACCESSIBLE
            return HandlerFailure.INVALID_TARGET_PATH

        mode = payload.get("mode")
        if mode not in ("append", "replace"):
            return HandlerFailure.INVALID_PAYLOAD
        if "content" not in payload or not isinstance(payload["content"], str):
            return HandlerFailure.INVALID_PAYLOAD
        if mode == "replace" and ("old_string" not in payload or not isinstance(payload["old_string"], str)):
            return HandlerFailure.INVALID_PAYLOAD

        # NOTE: MISSING check deferred to EXECUTION phase (per contract)
        return None

    def _execute(
        self,
        *,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[str], str, str]:
        # MISSING → execution-phase failure
        if target_state.status == TargetResolutionStatus.MISSING:
            raise _HandlerExecutionError(HandlerFailure.TARGET_NOT_FOUND)

        path = Path(target_state.normalized_path)
        encoding = payload.get("encoding", "utf-8")
        mode = payload["mode"]
        content = payload["content"]

        try:
            existing = path.read_text(encoding=encoding)
        except PermissionError:
            raise _HandlerExecutionError(HandlerFailure.TARGET_INACCESSIBLE)
        except OSError:
            raise _HandlerExecutionError(HandlerFailure.EXECUTION_ERROR)

        if mode == "append":
            new_content = existing + content
        else:  # replace
            old_string = payload["old_string"]
            if old_string not in existing:
                # old_string not in current file = pre-state conflict
                raise _HandlerExecutionError(HandlerFailure.CONFLICTING_PRE_STATE)
            new_content = existing.replace(old_string, content, 1)

        try:
            path.write_text(new_content, encoding=encoding)
        except PermissionError:
            raise _HandlerExecutionError(HandlerFailure.TARGET_INACCESSIBLE)
        except OSError:
            raise _HandlerExecutionError(HandlerFailure.EXECUTION_ERROR)

        artifact_hash = hashlib.sha256(new_content.encode(encoding)).hexdigest()
        output_data = {
            "mode": mode,
            "path": str(path),
            "bytes_before": len(existing.encode(encoding)),
            "bytes_after": len(new_content.encode(encoding)),
            "content_hash": artifact_hash,
        }
        return output_data, artifact_hash, f"file://{path}", "file"


# ---------------------------------------------------------------------------
# AnalyzeHandler
# ---------------------------------------------------------------------------

class AnalyzeHandler(BaseHandler):
    """Reads and analyzes a file; non-mutating.

    State law: post_state_hash MUST equal pre_state_hash.

    Payload keys:
      metric    : "line_count" | "char_count" | "word_count" | "hash" | "all"

    Forbidden effects:
      - May not write any file
      - May not mutate external state
    """

    _tool_type = "ANALYZE"

    def _is_mutating(self) -> bool:
        return False  # non-mutating: post == pre

    def _validate(
        self,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
    ) -> Optional[HandlerFailure]:
        if target_state.status == TargetResolutionStatus.AMBIGUOUS:
            return HandlerFailure.AMBIGUOUS_TARGET
        if target_state.status == TargetResolutionStatus.CONFLICTING:
            return HandlerFailure.INVALID_TARGET_PATH

        metric = payload.get("metric", "all")
        if metric not in ("line_count", "char_count", "word_count", "hash", "all"):
            return HandlerFailure.INVALID_PAYLOAD

        return None

    def _execute(
        self,
        *,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[str], str, str]:
        if target_state.status == TargetResolutionStatus.MISSING:
            raise _HandlerExecutionError(HandlerFailure.TARGET_NOT_FOUND)

        path = Path(target_state.normalized_path)
        metric = payload.get("metric", "all")

        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="replace")
        except PermissionError:
            raise _HandlerExecutionError(HandlerFailure.TARGET_INACCESSIBLE)
        except OSError:
            raise _HandlerExecutionError(HandlerFailure.EXECUTION_ERROR)

        content_hash = hashlib.sha256(raw).hexdigest()
        result: Dict[str, Any] = {"path": str(path), "content_hash": content_hash}

        if metric in ("line_count", "all"):
            result["line_count"] = len(text.splitlines())
        if metric in ("char_count", "all"):
            result["char_count"] = len(text)
        if metric in ("word_count", "all"):
            result["word_count"] = len(text.split())
        if metric in ("hash", "all"):
            result["sha256"] = content_hash

        artifact_hash = hashlib.sha256(_jcs(result)).hexdigest()
        return result, artifact_hash, f"analysis://{path}", "analysis_result"

    def _compute_post_state(
        self,
        *,
        session_state: Dict[str, Any],
        target: str,
        artifact_hash: Optional[str],
        prior_artifact_hashes: Optional[List[str]],
        pre_state_hash: str,
    ) -> str:
        """Non-mutating: post_state MUST equal pre_state (FS unchanged)."""
        return pre_state_hash


# ---------------------------------------------------------------------------
# RouteHandler
# ---------------------------------------------------------------------------

class RouteHandler(BaseHandler):
    """Emits a routing advisory / queue record; never executes remotely.

    ROUTE artifact is NON-SOVEREIGN:
      The presence of a ARTIFACT_WRITE with artifact_type='queue_receipt'
      does NOT confirm, authorize, or commit the target service to execute.

    Payload keys:
      destination  : str   — queue name, service ID, or topic
      message      : dict  — body to enqueue
      priority     : int   — optional; default 0

    Forbidden effects:
      - May not confirm remote execution happened
      - May not write local files
      - May not mutate local state
    """

    _tool_type = "ROUTE"

    def _is_mutating(self) -> bool:
        return False

    def _non_sovereignty_assertion(self) -> str:
        return ROUTE_NON_SOVEREIGNTY_ASSERTION

    def _validate(
        self,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
    ) -> Optional[HandlerFailure]:
        # ROUTE target is a logical address, not a FS path —
        # TargetResolutionStatus.MISSING is acceptable (service may be offline)
        if target_state.status == TargetResolutionStatus.AMBIGUOUS:
            return HandlerFailure.AMBIGUOUS_TARGET

        if "destination" not in payload:
            return HandlerFailure.INVALID_PAYLOAD
        if "message" not in payload or not isinstance(payload["message"], dict):
            return HandlerFailure.INVALID_PAYLOAD

        return None

    def _execute(
        self,
        *,
        target_state: TargetResolutionState,
        payload: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[str], str, str]:
        """Build a queue record — pure data, no side-effects."""
        record: Dict[str, Any] = {
            "destination": payload["destination"],
            "message": payload["message"],
            "priority": payload.get("priority", 0),
            "enqueued_at": time.time(),
            "non_sovereignty_assertion": ROUTE_NON_SOVEREIGNTY_ASSERTION,
            "status": "advisory_only",
        }
        record_hash = hashlib.sha256(_jcs(record)).hexdigest()
        artifact_uri = f"queue://{payload['destination']}"
        return record, record_hash, artifact_uri, "queue_receipt"

    def _compute_post_state(
        self,
        *,
        session_state: Dict[str, Any],
        target: str,
        artifact_hash: Optional[str],
        prior_artifact_hashes: Optional[List[str]],
        pre_state_hash: str,
    ) -> str:
        """ROUTE does not mutate local FS — state unchanged."""
        return pre_state_hash


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

__all__ = [
    "HandlerResult",
    "IdempotenceRegistry",
    "WriteFileHandler",
    "EditFileHandler",
    "AnalyzeHandler",
    "RouteHandler",
    "_HandlerExecutionError",
]
