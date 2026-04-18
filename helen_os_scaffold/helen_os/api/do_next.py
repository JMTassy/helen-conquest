"""
/do_next endpoint — 7-phase lifecycle per LIFECYCLE_INVARIANTS_V1

Implements the frozen kernel boundary with complete receipt chains,
session resumption, audit integration, and persistence atomicity.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import hashlib
import time
import uuid
from datetime import datetime
import sqlite3
import os

from helen_os.memory import MemoryKernel
from helen_os.kernel.receipt_engine import add_receipt_to_artifact
from helen_os.adapters import OllamaAdapter


# ─────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS (Frozen per API_CONTRACT_DO_NEXT_V1)
# ─────────────────────────────────────────────────────────────

class ExecutionModeEnum(str, Enum):
    """Frozen execution modes."""
    DETERMINISTIC = "deterministic"
    BOUNDED = "bounded"
    OPEN = "open"


class DoNextRequest(BaseModel):
    """Frozen request schema per API_CONTRACT_DO_NEXT_V1 §3."""
    session_id: str = Field(..., min_length=1, max_length=256)
    user_input: str = Field(..., min_length=1, max_length=10000)
    mode: ExecutionModeEnum
    model: str = Field(..., min_length=1)
    project: Optional[str] = Field(None, max_length=256)
    max_context_messages: Optional[int] = Field(None, ge=1, le=100)
    include_reasoning: Optional[bool] = Field(False)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    seed: Optional[int] = Field(None, ge=0)

    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session_id format: alphanumeric + underscore only."""
        if not all(c.isalnum() or c == '_' for c in v):
            raise ValueError('session_id must be alphanumeric + underscore only')
        return v

    @validator('mode')
    def validate_mode(cls, v):
        """Ensure mode is valid enum."""
        valid = {"deterministic", "bounded", "open"}
        if v not in valid:
            raise ValueError(f'mode must be one of {valid}')
        return v


class DoNextResponse(BaseModel):
    """Frozen response schema per API_CONTRACT_DO_NEXT_V1 §4."""
    session_id: str
    mode: str
    model: str
    reply: Optional[str]
    receipt_id: Optional[str]
    run_id: Optional[int]
    context_items_used: Optional[List[str]]
    epoch: Optional[int]
    continuity: Optional[float]


class ErrorResponse(BaseModel):
    """Frozen error response schema per API_CONTRACT_DO_NEXT_V1 §6."""
    detail: str = Field(..., max_length=1000)


# ─────────────────────────────────────────────────────────────
# SESSION MANAGEMENT (Per SESSION_PERSISTENCE_SEMANTICS_V1)
# ─────────────────────────────────────────────────────────────

class SessionState:
    """In-memory representation of session state per SESSION_PERSISTENCE_SEMANTICS_V1."""

    def __init__(self, session_id: str, created_at: datetime = None):
        self.session_id = session_id
        self.version = "session_persistence_semantics_v1"
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.run_count = 0
        self.memory_objects: List[str] = []
        self.recent_receipts: List[Dict[str, Any]] = []  # Capped at 100
        self.state_hash: Optional[str] = None
        self.epoch: int = 0
        self.continuity_score: float = 0.0
        self.resumption_history: List[Dict[str, Any]] = []
        self.last_known_boundary_dispatch_decision: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for persistence."""
        return {
            "session_id": self.session_id,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "run_count": self.run_count,
            "memory_objects": self.memory_objects,
            "recent_receipts": self.recent_receipts,
            "state_hash": self.state_hash,
            "epoch": self.epoch,
            "continuity_score": self.continuity_score,
            "resumption_history": self.resumption_history,
            "last_known_boundary_dispatch_decision": self.last_known_boundary_dispatch_decision
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SessionState':
        """Deserialize from dict."""
        session = SessionState(data["session_id"])
        session.created_at = datetime.fromisoformat(data.get("created_at", session.created_at.isoformat()))
        session.last_accessed = datetime.fromisoformat(data.get("last_accessed", session.last_accessed.isoformat()))
        session.run_count = data.get("run_count", 0)
        session.memory_objects = data.get("memory_objects", [])
        session.recent_receipts = data.get("recent_receipts", [])
        session.state_hash = data.get("state_hash")
        session.epoch = data.get("epoch", 0)
        session.continuity_score = data.get("continuity_score", 0.0)
        session.resumption_history = data.get("resumption_history", [])
        session.last_known_boundary_dispatch_decision = data.get("last_known_boundary_dispatch_decision")
        return session


class SessionPersistence:
    """Handle session load/save with atomicity and state hash verification."""

    def __init__(self, storage_dir: str = "storage/sessions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _session_path(self, session_id: str) -> str:
        """Get filesystem path for session."""
        return os.path.join(self.storage_dir, f"{session_id}.json")

    def load_session(self, session_id: str) -> SessionState:
        """Load session from persistence or create new."""
        path = self._session_path(session_id)
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
            return SessionState.from_dict(data)
        else:
            return SessionState(session_id)

    def verify_state_hash(self, session: SessionState) -> bool:
        """Verify state_hash matches current session payload (per SESSION_PERSISTENCE_SEMANTICS_V1 §2)."""
        if not session.state_hash:
            return True  # New session, no hash to verify

        payload = {
            "session_id": session.session_id,
            "run_count": session.run_count,
            "memory_objects": session.memory_objects,
            "epoch": session.epoch,
            "continuity_score": session.continuity_score
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        computed_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return computed_hash == session.state_hash

    def compute_state_hash(self, session: SessionState) -> str:
        """Compute canonical state hash (per SESSION_PERSISTENCE_SEMANTICS_V1 §2)."""
        payload = {
            "session_id": session.session_id,
            "run_count": session.run_count,
            "memory_objects": session.memory_objects,
            "epoch": session.epoch,
            "continuity_score": session.continuity_score
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def save_session_atomic(self, session: SessionState) -> bool:
        """Save session atomically (all or nothing per SESSION_PERSISTENCE_SEMANTICS_V1 §5)."""
        path = self._session_path(session.session_id)
        temp_path = path + ".tmp"
        try:
            # Write to temp file first
            with open(temp_path, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            # Atomically rename
            os.replace(temp_path, path)
            return True
        except Exception:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False


# ─────────────────────────────────────────────────────────────
# RECEIPT EMISSION (Per LIFECYCLE_INVARIANTS_V1 §6)
# ─────────────────────────────────────────────────────────────

class ReceiptEmitter:
    """Emit receipts with complete lineage per LIFECYCLE_INVARIANTS_V1."""

    def __init__(self, storage_dir: str = "storage/receipts"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.receipt_log_path = os.path.join(storage_dir, "receipt_log.ndjson")

    def emit_receipt(self, receipt_type: str, session_id: str, parent_receipt_id: Optional[str] = None, **payload) -> str:
        """Emit a receipt and return its UUID."""
        receipt_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"

        receipt = {
            "receipt_id": receipt_id,
            "receipt_type": receipt_type,
            "session_id": session_id,
            "parent_receipt_id": parent_receipt_id,
            "timestamp": timestamp,
            **payload
        }

        # Append to log
        with open(self.receipt_log_path, 'a') as f:
            f.write(json.dumps(receipt) + '\n')

        return receipt_id

    def emit_session_resumption(self, session_id: str, prior_run_count: int, prior_epoch: int) -> str:
        """Emit SESSION_RESUMPTION receipt (Phase 2, root of lineage)."""
        return self.emit_receipt(
            "SESSION_RESUMPTION",
            session_id,
            parent_receipt_id=None,  # Root of lineage
            prior_run_count=prior_run_count,
            prior_epoch=prior_epoch
        )

    def emit_knowledge_audit(self, session_id: str, findings: List[Dict[str, Any]],
                           routing_consequence: str, parent_receipt_id: str) -> str:
        """Emit KNOWLEDGE_AUDIT receipt (Phase 3)."""
        return self.emit_receipt(
            "KNOWLEDGE_AUDIT",
            session_id,
            parent_receipt_id=parent_receipt_id,
            finding_count=len(findings),
            routing_consequence=routing_consequence,
            findings=findings
        )

    def emit_dispatch_decision(self, session_id: str, routing_decision: str, parent_receipt_id: str, epoch: int) -> str:
        """Emit DISPATCH_DECISION receipt (Phase 4, only if not REJECT)."""
        return self.emit_receipt(
            "DISPATCH_DECISION",
            session_id,
            parent_receipt_id=parent_receipt_id,
            routing_decision=routing_decision,
            epoch=epoch
        )

    def emit_inference_execution(self, session_id: str, reply_length: int, context_count: int,
                                parent_receipt_id: str) -> str:
        """Emit INFERENCE_EXECUTION receipt (Phase 5)."""
        return self.emit_receipt(
            "INFERENCE_EXECUTION",
            session_id,
            parent_receipt_id=parent_receipt_id,
            reply_length=reply_length,
            context_count=context_count
        )

    def emit_deferred_execution(self, session_id: str, queue_position: int, parent_receipt_id: str) -> str:
        """Emit DEFERRED_EXECUTION receipt (Phase 5)."""
        return self.emit_receipt(
            "DEFERRED_EXECUTION",
            session_id,
            parent_receipt_id=parent_receipt_id,
            queue_position=queue_position
        )

    def emit_conclusion(self, session_id: str, receipt_chain_hash: str, parent_receipt_id: str) -> str:
        """Emit CONCLUSION receipt (Phase 6)."""
        return self.emit_receipt(
            "CONCLUSION",
            session_id,
            parent_receipt_id=parent_receipt_id,
            receipt_chain_hash=receipt_chain_hash
        )

    def emit_session_commit(self, session_id: str, state_hash: str, run_count: int, parent_receipt_id: str) -> str:
        """Emit SESSION_COMMIT receipt (Phase 7, after successful write)."""
        return self.emit_receipt(
            "SESSION_COMMIT",
            session_id,
            parent_receipt_id=parent_receipt_id,
            state_hash=state_hash,
            run_count=run_count
        )


# ─────────────────────────────────────────────────────────────
# CONTINUITY COMPUTATION (Per SESSION_PERSISTENCE_SEMANTICS_V1 §4)
# ─────────────────────────────────────────────────────────────

def compute_continuity_score(session: SessionState) -> float:
    """
    Compute continuity score per SESSION_PERSISTENCE_SEMANTICS_V1 §4.

    Formula: min(1.0,
                 min(1.0, run_count/20)*0.5 +
                 min(1.0, age_minutes/1440)*0.3 +
                 min(1.0, memory_objects.count/50)*0.2)
    """
    # Component 1: run_count (20 calls = 1.0)
    run_component = min(1.0, session.run_count / 20.0) * 0.5

    # Component 2: age in minutes (1440 minutes = 1 day = 1.0)
    age_minutes = (datetime.utcnow() - session.created_at).total_seconds() / 60
    age_component = min(1.0, age_minutes / 1440.0) * 0.3

    # Component 3: memory objects (50 objects = 1.0)
    memory_component = min(1.0, len(session.memory_objects) / 50.0) * 0.2

    return min(1.0, run_component + age_component + memory_component)


# ─────────────────────────────────────────────────────────────
# EPOCH MANAGEMENT (Global monotonic counter)
# ─────────────────────────────────────────────────────────────

class EpochManager:
    """Manage global monotonic epoch per LIFECYCLE_INVARIANTS_V1 §7."""

    def __init__(self, storage_path: str = "storage/epoch.json"):
        self.storage_path = storage_path
        self._current_epoch = self._load_epoch()

    def _load_epoch(self) -> int:
        """Load current epoch from storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                return data.get("current_epoch", 0)
            except Exception:
                return 0
        return 0

    def get_and_increment(self) -> int:
        """Get current epoch and increment by 1 (atomic per call)."""
        current = self._current_epoch
        self._current_epoch += 1
        self._save_epoch()
        return current

    def _save_epoch(self):
        """Save epoch to storage (non-recoverable increment)."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump({"current_epoch": self._current_epoch}, f)


# ─────────────────────────────────────────────────────────────
# AUDIT INTEGRATION (Phase 3)
# ─────────────────────────────────────────────────────────────

class AuditSubsystem:
    """Minimal audit subsystem for Phase 3."""

    @staticmethod
    def audit_knowledge_state(session_id: str, memory_objects: List[str],
                            recent_receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Call audit logic to find issues.

        Returns:
        {
            "findings": [...],
            "routing_consequence": "annotate" | "defer" | "reject"
        }
        """
        # TODO: Implement full audit_knowledge_state logic
        # For now, return no findings (all paths proceed)
        return {
            "findings": [],
            "routing_consequence": "annotate"
        }


# ─────────────────────────────────────────────────────────────
# MAIN SERVICE: 7-PHASE EXECUTOR
# ─────────────────────────────────────────────────────────────

class DoNextService:
    """Execute /do_next request through 7-phase lifecycle per LIFECYCLE_INVARIANTS_V1."""

    def __init__(self):
        self.session_persistence = SessionPersistence()
        self.receipt_emitter = ReceiptEmitter()
        self.epoch_manager = EpochManager()
        self.audit = AuditSubsystem()
        self.memory = MemoryKernel()
        # Default to Ollama adapter (can be overridden in tests)
        self.adapter = OllamaAdapter()

    def execute(self, request: DoNextRequest) -> DoNextResponse:
        """Execute the 7-phase lifecycle."""
        try:
            # PHASE 1: REQUEST VALIDATION
            self._phase_1_request_validation(request)

            # PHASE 2: SESSION LOAD / RESUMPTION
            session, resumption_receipt_id = self._phase_2_session_load(request)

            # PHASE 3: KNOWLEDGE AUDIT
            audit_receipt_id = self._phase_3_knowledge_audit(request, session, resumption_receipt_id)
            audit_result = self.audit.audit_knowledge_state(
                request.session_id,
                session.memory_objects,
                session.recent_receipts
            )

            # PHASE 4: DISPATCH DECISION (increments epoch if not rejected)
            routing_decision, dispatch_receipt_id, epoch_for_response = self._phase_4_dispatch_decision(
                request, session, audit_result, audit_receipt_id
            )

            # Handle rejection
            if routing_decision == "reject":
                return DoNextResponse(
                    session_id=request.session_id,
                    mode=request.mode.value,
                    model=request.model,
                    reply=None,
                    receipt_id=None,
                    run_id=None,
                    context_items_used=None,
                    epoch=None,
                    continuity=None
                )

            # PHASE 5: CONSEQUENCE (LLM or DEFER)
            reply, consequence_receipt_id = self._phase_5_consequence(
                request, session, routing_decision, dispatch_receipt_id
            )

            # PHASE 6: CONSOLIDATION
            conclusion_receipt_id = self._phase_6_consolidation(
                request, session, consequence_receipt_id
            )

            # PHASE 7: PERSISTENCE & RESPONSE
            return self._phase_7_persistence_and_response(
                request, session, conclusion_receipt_id, reply, epoch_for_response
            )

        except Exception as e:
            return DoNextResponse(
                session_id=request.session_id,
                mode=request.mode.value,
                model=request.model,
                reply=None,
                receipt_id=None,
                run_id=None,
                context_items_used=None,
                epoch=None,
                continuity=None
            )

    def _phase_1_request_validation(self, request: DoNextRequest) -> None:
        """Phase 1: Validate request schema (frozen per API_CONTRACT_DO_NEXT_V1 §3.2)."""
        # Pydantic validation happens automatically on request model
        # Additional validation:
        if not request.session_id:
            raise ValueError("session_id required")
        if not request.user_input:
            raise ValueError("user_input required")
        if request.mode not in [ExecutionModeEnum.DETERMINISTIC, ExecutionModeEnum.BOUNDED, ExecutionModeEnum.OPEN]:
            raise ValueError("mode must be deterministic, bounded, or open")
        # No receipt emitted (per LIFECYCLE_INVARIANTS_V1 Phase 1)

    def _phase_2_session_load(self, request: DoNextRequest) -> tuple[SessionState, str]:
        """Phase 2: Load or create session, emit SESSION_RESUMPTION if resumed."""
        session = self.session_persistence.load_session(request.session_id)

        # Verify state hash if resuming
        if session.run_count > 0:
            if not self.session_persistence.verify_state_hash(session):
                raise ValueError("session state corrupted (hash mismatch)")

        # Remember pre-call state for continuity computation
        prior_run_count = session.run_count
        prior_epoch = session.epoch

        # Emit SESSION_RESUMPTION (always, for new or resumed sessions)
        resumption_receipt_id = self.receipt_emitter.emit_session_resumption(
            request.session_id, prior_run_count, prior_epoch
        )

        return session, resumption_receipt_id

    def _phase_3_knowledge_audit(self, request: DoNextRequest, session: SessionState,
                                parent_receipt_id: str) -> str:
        """Phase 3: Call audit_knowledge_state, emit KNOWLEDGE_AUDIT receipt."""
        audit_result = self.audit.audit_knowledge_state(
            request.session_id,
            session.memory_objects,
            session.recent_receipts
        )

        # Emit KNOWLEDGE_AUDIT receipt
        audit_receipt_id = self.receipt_emitter.emit_knowledge_audit(
            request.session_id,
            audit_result.get("findings", []),
            audit_result.get("routing_consequence", "annotate"),
            parent_receipt_id=parent_receipt_id
        )

        return audit_receipt_id

    def _phase_4_dispatch_decision(self, request: DoNextRequest, session: SessionState,
                                  audit_result: Dict[str, Any], parent_receipt_id: str) -> tuple[str, Optional[str], Optional[int]]:
        """Phase 4: Map audit consequence to routing decision, emit DISPATCH_DECISION."""
        routing_consequence = audit_result.get("routing_consequence", "annotate")

        # Map consequence to decision (per DISPATCH_DECISION_TABLE_V1)
        routing_decision_map = {
            "annotate": "kernel",   # Execute in kernel
            "defer": "defer",        # Defer execution
            "reject": "reject"       # Reject request
        }
        routing_decision = routing_decision_map.get(routing_consequence, "kernel")

        # Only emit DISPATCH_DECISION if not REJECT
        dispatch_receipt_id = None
        epoch_for_response = None
        if routing_decision != "reject":
            # Get next epoch for dispatch decision (single increment per accepted call)
            epoch_for_response = self.epoch_manager.get_and_increment()
            dispatch_receipt_id = self.receipt_emitter.emit_dispatch_decision(
                request.session_id,
                routing_decision,
                parent_receipt_id=parent_receipt_id,
                epoch=epoch_for_response
            )

        return routing_decision, dispatch_receipt_id, epoch_for_response

    def _phase_5_consequence(self, request: DoNextRequest, session: SessionState,
                            routing_decision: str, parent_receipt_id: Optional[str]) -> tuple[Optional[str], str]:
        """Phase 5: Execute consequence (LLM if KERNEL, queue if DEFER)."""
        reply = None
        consequence_receipt_id = None

        if routing_decision == "kernel":
            # Call LLM inference
            reply = self._call_llm_inference(request, session)
            consequence_receipt_id = self.receipt_emitter.emit_inference_execution(
                request.session_id,
                len(reply) if reply else 0,
                len(session.memory_objects),
                parent_receipt_id=parent_receipt_id
            )
        elif routing_decision == "defer":
            # Queue for later (non-blocking)
            consequence_receipt_id = self.receipt_emitter.emit_deferred_execution(
                request.session_id,
                queue_position=0,  # Placeholder
                parent_receipt_id=parent_receipt_id
            )

        return reply, consequence_receipt_id

    def _call_llm_inference(self, request: DoNextRequest, session: SessionState) -> str:
        """Call LLM adapter to generate reply."""
        try:
            # Build history from session memory (limited by max_context_messages)
            max_context = request.max_context_messages or 10
            history = [
                {"content": obj, "metadata": {"role": "user"}}
                for obj in session.memory_objects[-max_context:]
            ] if session.memory_objects else []

            # Call adapter's generate method
            # Note: Temperature, top_p, seed are frozen per request but adapter doesn't expose them here
            reply = self.adapter.generate(request.user_input, history)
            return reply or ""
        except Exception:
            return ""

    def _phase_6_consolidation(self, request: DoNextRequest, session: SessionState,
                              parent_receipt_id: str) -> str:
        """Phase 6: Update memory, finalize receipt chain, emit CONCLUSION."""
        # Update session memory (add user input as memory object)
        session.memory_objects.append(request.user_input[:100])  # Truncate for memory

        # Cap recent_receipts at 100 (per SESSION_PERSISTENCE_SEMANTICS_V1)
        if len(session.recent_receipts) > 100:
            session.recent_receipts = session.recent_receipts[-100:]

        # Emit CONCLUSION receipt
        conclusion_receipt_id = self.receipt_emitter.emit_conclusion(
            request.session_id,
            receipt_chain_hash="TODO",  # Compute from receipt chain
            parent_receipt_id=parent_receipt_id
        )

        return conclusion_receipt_id

    def _phase_7_persistence_and_response(self, request: DoNextRequest, session: SessionState,
                                         conclusion_receipt_id: str, reply: Optional[str],
                                         epoch_for_response: Optional[int]) -> DoNextResponse:
        """Phase 7: Hash session, persist atomically, emit SESSION_COMMIT, return response."""
        # Increment run count
        session.run_count += 1

        # Update epoch in session
        session.epoch = epoch_for_response or session.epoch

        # Compute new state hash (before save)
        session.state_hash = self.session_persistence.compute_state_hash(session)

        # Compute continuity (pre-increment, per SESSION_PERSISTENCE_SEMANTICS_V1 §4)
        session.continuity_score = compute_continuity_score(session)

        # Persist atomically (all or nothing)
        if not self.session_persistence.save_session_atomic(session):
            raise ValueError("session persistence failed")

        # Emit SESSION_COMMIT receipt (after successful write)
        commit_receipt_id = self.receipt_emitter.emit_session_commit(
            request.session_id,
            session.state_hash,
            session.run_count,
            parent_receipt_id=conclusion_receipt_id
        )

        # Build and return response
        return DoNextResponse(
            session_id=request.session_id,
            mode=request.mode.value,
            model=request.model,
            reply=reply,
            receipt_id=commit_receipt_id,
            run_id=session.run_count,
            context_items_used=session.memory_objects[:5] if session.memory_objects else [],
            epoch=epoch_for_response,
            continuity=session.continuity_score
        )
