"""
ORACLE TOWN Persistence Layer

Provides session storage, audit trails, and replay capabilities.
Uses JSON files for portability (can be upgraded to SQLite/PostgreSQL).

Components:
- SessionStore: Stores complete processing sessions
- AuditTrail: Immutable log of all system events
- ReplayEngine: Reconstructs sessions from stored data
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List, Dict
from enum import Enum

from oracle_town.core.ledger import AppendOnlyLedger, sha256_hex, canonical_json_bytes


class SessionStatus(str, Enum):
    """Session processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EventType(str, Enum):
    """Audit trail event types"""
    SESSION_CREATED = "session_created"
    CLAIM_COMPILED = "claim_compiled"
    DISTRICT_STARTED = "district_started"
    STREET_TURN = "street_turn"
    STREET_COMPLETED = "street_completed"
    DISTRICT_VERDICT = "district_verdict"
    TOWN_HALL_INTEGRATION = "town_hall_integration"
    MAYOR_VERDICT = "mayor_verdict"
    SESSION_COMPLETED = "session_completed"
    SESSION_FAILED = "session_failed"


@dataclass
class Session:
    """
    Complete processing session with all artifacts.
    """
    session_id: str
    created_at: str
    status: SessionStatus

    # Input
    raw_input: str
    domain: str
    urgency: str = "medium"

    # Compiled claim
    claim_id: Optional[str] = None
    claim_type: Optional[str] = None
    claim_text: Optional[str] = None
    success_criteria: List[str] = field(default_factory=list)

    # District processing
    district_verdicts: List[Dict[str, Any]] = field(default_factory=list)

    # Town Hall
    town_recommendation: Optional[Dict[str, Any]] = None
    qi_int_score: Optional[float] = None

    # Mayor verdict
    final_verdict: Optional[str] = None
    rationale: Optional[str] = None
    blocking_reasons: List[str] = field(default_factory=list)
    remediation_roadmap: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None

    # Hash for integrity
    content_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "status": self.status.value if isinstance(self.status, SessionStatus) else self.status,
            "raw_input": self.raw_input,
            "domain": self.domain,
            "urgency": self.urgency,
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
            "claim_text": self.claim_text,
            "success_criteria": self.success_criteria,
            "district_verdicts": self.district_verdicts,
            "town_recommendation": self.town_recommendation,
            "qi_int_score": self.qi_int_score,
            "final_verdict": self.final_verdict,
            "rationale": self.rationale,
            "blocking_reasons": self.blocking_reasons,
            "remediation_roadmap": self.remediation_roadmap,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create from dictionary"""
        status = data.get("status", "pending")
        if isinstance(status, str):
            status = SessionStatus(status)

        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            status=status,
            raw_input=data["raw_input"],
            domain=data["domain"],
            urgency=data.get("urgency", "medium"),
            claim_id=data.get("claim_id"),
            claim_type=data.get("claim_type"),
            claim_text=data.get("claim_text"),
            success_criteria=data.get("success_criteria", []),
            district_verdicts=data.get("district_verdicts", []),
            town_recommendation=data.get("town_recommendation"),
            qi_int_score=data.get("qi_int_score"),
            final_verdict=data.get("final_verdict"),
            rationale=data.get("rationale"),
            blocking_reasons=data.get("blocking_reasons", []),
            remediation_roadmap=data.get("remediation_roadmap", []),
            completed_at=data.get("completed_at"),
            duration_ms=data.get("duration_ms"),
            error_message=data.get("error_message"),
            content_hash=data.get("content_hash"),
        )

    def compute_hash(self) -> str:
        """Compute content hash for integrity verification"""
        data = self.to_dict()
        data.pop("content_hash", None)  # Exclude hash from hash computation
        return sha256_hex(canonical_json_bytes(data))


class SessionStore:
    """
    Persistent session storage using JSON files.

    Directory structure:
        sessions/
            index.json          # Session index for quick lookups
            {session_id}.json   # Individual session files
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.sessions_dir = base_path / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.sessions_dir / "index.json"

        if not self.index_path.exists():
            self._write_index({})

    def _read_index(self) -> Dict[str, Dict[str, Any]]:
        """Read session index"""
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def _write_index(self, index: Dict[str, Dict[str, Any]]) -> None:
        """Write session index"""
        self.index_path.write_text(
            json.dumps(index, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def create_session(self, raw_input: str, domain: str, urgency: str = "medium") -> Session:
        """
        Create a new session.

        Args:
            raw_input: User's input text
            domain: Claim domain (marketing, product, policy, event)
            urgency: Processing urgency

        Returns:
            New Session object
        """
        session_id = f"SESSION_{uuid.uuid4().hex[:12].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()

        session = Session(
            session_id=session_id,
            created_at=created_at,
            status=SessionStatus.PENDING,
            raw_input=raw_input,
            domain=domain,
            urgency=urgency,
        )

        self.save_session(session)
        return session

    def save_session(self, session: Session) -> None:
        """
        Save session to disk.

        Args:
            session: Session to save
        """
        # Compute hash before saving
        session.content_hash = session.compute_hash()

        # Save session file
        session_path = self.sessions_dir / f"{session.session_id}.json"
        session_path.write_text(
            json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        # Update index
        index = self._read_index()
        index[session.session_id] = {
            "created_at": session.created_at,
            "status": session.status.value if isinstance(session.status, SessionStatus) else session.status,
            "domain": session.domain,
            "final_verdict": session.final_verdict,
            "claim_id": session.claim_id,
        }
        self._write_index(index)

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        session_path = self.sessions_dir / f"{session_id}.json"
        if not session_path.exists():
            return None

        data = json.loads(session_path.read_text(encoding="utf-8"))
        session = Session.from_dict(data)

        # Verify integrity
        expected_hash = session.content_hash
        actual_hash = session.compute_hash()
        if expected_hash and expected_hash != actual_hash:
            raise ValueError(f"Session {session_id} integrity check failed: content has been modified")

        return session

    def list_sessions(
        self,
        status: Optional[SessionStatus] = None,
        domain: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List sessions with optional filtering.

        Args:
            status: Filter by status
            domain: Filter by domain
            limit: Maximum number of results

        Returns:
            List of session summaries
        """
        index = self._read_index()
        results = []

        for session_id, summary in index.items():
            if status and summary.get("status") != status.value:
                continue
            if domain and summary.get("domain") != domain:
                continue

            results.append({
                "session_id": session_id,
                **summary
            })

            if len(results) >= limit:
                break

        # Sort by created_at descending
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (for testing/cleanup only).

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False if not found
        """
        session_path = self.sessions_dir / f"{session_id}.json"
        if not session_path.exists():
            return False

        session_path.unlink()

        index = self._read_index()
        if session_id in index:
            del index[session_id]
            self._write_index(index)

        return True


class AuditTrail:
    """
    Immutable audit trail using append-only ledger.

    Records all system events for:
    - Compliance and governance
    - Debugging and replay
    - Analytics and reporting
    """

    def __init__(self, base_path: Path):
        self.ledger = AppendOnlyLedger(base_path / "audit_trail.jsonl")

    def log_event(
        self,
        event_type: EventType,
        session_id: str,
        data: Dict[str, Any],
        actor: str = "system",
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            session_id: Associated session
            data: Event-specific data
            actor: Who/what triggered the event
        """
        self.ledger.append(
            entry_type=event_type.value,
            payload={
                "session_id": session_id,
                "actor": actor,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }
        )

    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a session (for replay).

        Args:
            session_id: Session to get events for

        Returns:
            List of events in chronological order
        """
        lines = self.ledger._read_lines()
        events = []

        for line in lines:
            entry = json.loads(line)
            if entry.get("payload", {}).get("session_id") == session_id:
                events.append({
                    "seq": entry["seq"],
                    "event_type": entry["entry_type"],
                    "timestamp": entry["payload"]["timestamp"],
                    "actor": entry["payload"]["actor"],
                    "data": entry["payload"]["data"],
                })

        return events

    def verify_integrity(self) -> bool:
        """
        Verify audit trail integrity.

        Returns:
            True if integrity check passes

        Raises:
            AssertionError if integrity check fails
        """
        self.ledger.verify_chain()
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit trail statistics.

        Returns:
            Statistics about events
        """
        lines = self.ledger._read_lines()
        stats = {
            "total_events": len(lines),
            "events_by_type": {},
            "sessions_logged": set(),
        }

        for line in lines:
            entry = json.loads(line)
            event_type = entry["entry_type"]
            session_id = entry.get("payload", {}).get("session_id")

            stats["events_by_type"][event_type] = stats["events_by_type"].get(event_type, 0) + 1
            if session_id:
                stats["sessions_logged"].add(session_id)

        stats["sessions_logged"] = len(stats["sessions_logged"])
        return stats


class ReplayEngine:
    """
    Reconstructs sessions from audit trail for debugging and analysis.
    """

    def __init__(self, session_store: SessionStore, audit_trail: AuditTrail):
        self.session_store = session_store
        self.audit_trail = audit_trail

    def replay_session(self, session_id: str) -> Dict[str, Any]:
        """
        Replay a session from audit events.

        Args:
            session_id: Session to replay

        Returns:
            Reconstructed session timeline
        """
        events = self.audit_trail.get_session_events(session_id)
        session = self.session_store.get_session(session_id)

        timeline = {
            "session_id": session_id,
            "session": session.to_dict() if session else None,
            "events": events,
            "event_count": len(events),
        }

        # Calculate duration from events
        if events:
            first_event = events[0]
            last_event = events[-1]
            timeline["first_event"] = first_event["timestamp"]
            timeline["last_event"] = last_event["timestamp"]

        return timeline

    def compare_sessions(self, session_id_1: str, session_id_2: str) -> Dict[str, Any]:
        """
        Compare two sessions for analysis.

        Args:
            session_id_1: First session
            session_id_2: Second session

        Returns:
            Comparison report
        """
        session_1 = self.session_store.get_session(session_id_1)
        session_2 = self.session_store.get_session(session_id_2)

        if not session_1 or not session_2:
            return {"error": "One or both sessions not found"}

        return {
            "session_1": {
                "id": session_id_1,
                "verdict": session_1.final_verdict,
                "qi_int_score": session_1.qi_int_score,
                "blocking_reasons_count": len(session_1.blocking_reasons),
            },
            "session_2": {
                "id": session_id_2,
                "verdict": session_2.final_verdict,
                "qi_int_score": session_2.qi_int_score,
                "blocking_reasons_count": len(session_2.blocking_reasons),
            },
            "same_verdict": session_1.final_verdict == session_2.final_verdict,
        }


class PersistenceManager:
    """
    Unified persistence manager combining all components.
    """

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            base_path = Path("oracle_town_data")

        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.sessions = SessionStore(base_path)
        self.audit = AuditTrail(base_path)
        self.replay = ReplayEngine(self.sessions, self.audit)

    def create_tracked_session(self, raw_input: str, domain: str, urgency: str = "medium") -> Session:
        """
        Create a session with audit logging.

        Args:
            raw_input: User input
            domain: Claim domain
            urgency: Processing urgency

        Returns:
            New tracked session
        """
        session = self.sessions.create_session(raw_input, domain, urgency)

        self.audit.log_event(
            EventType.SESSION_CREATED,
            session.session_id,
            {
                "raw_input": raw_input[:200],  # Truncate for log
                "domain": domain,
                "urgency": urgency,
            }
        )

        return session

    def log_claim_compiled(self, session: Session, claim_id: str, claim_type: str) -> None:
        """Log claim compilation event"""
        self.audit.log_event(
            EventType.CLAIM_COMPILED,
            session.session_id,
            {"claim_id": claim_id, "claim_type": claim_type}
        )

    def log_district_verdict(self, session: Session, district_name: str, verdict: str, score: float) -> None:
        """Log district verdict event"""
        self.audit.log_event(
            EventType.DISTRICT_VERDICT,
            session.session_id,
            {"district": district_name, "verdict": verdict, "score": score}
        )

    def log_mayor_verdict(self, session: Session, verdict: str, rationale: str) -> None:
        """Log mayor verdict event"""
        self.audit.log_event(
            EventType.MAYOR_VERDICT,
            session.session_id,
            {"verdict": verdict, "rationale": rationale[:500]}
        )

    def complete_session(self, session: Session, start_time: datetime) -> None:
        """
        Mark session as completed with timing.

        Args:
            session: Session to complete
            start_time: When processing started
        """
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.now(timezone.utc).isoformat()
        session.duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        self.sessions.save_session(session)

        self.audit.log_event(
            EventType.SESSION_COMPLETED,
            session.session_id,
            {
                "final_verdict": session.final_verdict,
                "duration_ms": session.duration_ms,
            }
        )

    def fail_session(self, session: Session, error_message: str) -> None:
        """
        Mark session as failed.

        Args:
            session: Session that failed
            error_message: Error description
        """
        session.status = SessionStatus.FAILED
        session.error_message = error_message
        session.completed_at = datetime.now(timezone.utc).isoformat()

        self.sessions.save_session(session)

        self.audit.log_event(
            EventType.SESSION_FAILED,
            session.session_id,
            {"error": error_message}
        )


# Test
if __name__ == "__main__":
    import tempfile

    # Create temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        pm = PersistenceManager(Path(tmpdir))

        # Create a session
        session = pm.create_tracked_session(
            raw_input="Launch eco-lodge on private island",
            domain="product",
            urgency="medium"
        )
        print(f"Created session: {session.session_id}")

        # Update session
        session.claim_id = "CLM_TEST123"
        session.claim_type = "FEATURE"
        session.final_verdict = "SHIP"
        session.qi_int_score = 0.95

        pm.log_claim_compiled(session, "CLM_TEST123", "FEATURE")
        pm.log_mayor_verdict(session, "SHIP", "All checks passed")

        from datetime import datetime, timezone
        pm.complete_session(session, datetime.now(timezone.utc))

        # Retrieve and verify
        retrieved = pm.sessions.get_session(session.session_id)
        print(f"Retrieved session: {retrieved.session_id}")
        print(f"Verdict: {retrieved.final_verdict}")
        print(f"Integrity: {retrieved.content_hash == retrieved.compute_hash()}")

        # Check audit trail
        events = pm.audit.get_session_events(session.session_id)
        print(f"Audit events: {len(events)}")

        # Verify integrity
        pm.audit.verify_integrity()
        print("Audit trail integrity: OK")

        # List sessions
        sessions = pm.sessions.list_sessions()
        print(f"Total sessions: {len(sessions)}")
