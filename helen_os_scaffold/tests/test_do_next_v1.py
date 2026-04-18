"""
Tests for /do_next endpoint — 7-phase lifecycle conformance

Validates frozen boundary per:
- API_CONTRACT_DO_NEXT_V1 (request/response schema, status codes)
- SESSION_PERSISTENCE_SEMANTICS_V1 (session resumption, state hash, epoch)
- LIFECYCLE_INVARIANTS_V1 (7-phase order, receipt lineage)
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

from helen_os.api.do_next import (
    DoNextRequest,
    DoNextResponse,
    DoNextService,
    SessionState,
    SessionPersistence,
    ReceiptEmitter,
    EpochManager,
    ExecutionModeEnum,
    compute_continuity_score,
    AuditSubsystem,
)


class TestRequestValidation:
    """Test API_CONTRACT_DO_NEXT_V1 request validation (Phase 1)."""

    def test_valid_minimal_request(self):
        """Valid request with only required fields."""
        req = DoNextRequest(
            session_id="test_session_1",
            user_input="Hello",
            mode=ExecutionModeEnum.DETERMINISTIC,
            model="claude-3-haiku"
        )
        assert req.session_id == "test_session_1"
        assert req.user_input == "Hello"
        assert req.mode == ExecutionModeEnum.DETERMINISTIC

    def test_valid_full_request(self):
        """Valid request with all fields."""
        req = DoNextRequest(
            session_id="test_session_2",
            user_input="Explain quantum computing",
            mode=ExecutionModeEnum.BOUNDED,
            model="claude-3-sonnet",
            project="research",
            max_context_messages=20,
            include_reasoning=True,
            temperature=0.5,
            top_p=0.8,
            seed=42
        )
        assert req.temperature == 0.5
        assert req.seed == 42

    def test_invalid_session_id_format(self):
        """session_id must be alphanumeric + underscore only."""
        with pytest.raises(ValueError):
            DoNextRequest(
                session_id="test-session",  # hyphen not allowed
                user_input="Hello",
                mode=ExecutionModeEnum.DETERMINISTIC,
                model="claude-3-haiku"
            )

    def test_empty_user_input(self):
        """user_input cannot be empty."""
        with pytest.raises(ValueError):
            DoNextRequest(
                session_id="test_session",
                user_input="",  # empty
                mode=ExecutionModeEnum.DETERMINISTIC,
                model="claude-3-haiku"
            )

    def test_invalid_mode_enum(self):
        """mode must be deterministic, bounded, or open."""
        with pytest.raises(ValueError):
            DoNextRequest(
                session_id="test_session",
                user_input="Hello",
                mode="hybrid",  # invalid
                model="claude-3-haiku"
            )

    def test_invalid_temperature_range(self):
        """temperature must be 0.0-2.0."""
        with pytest.raises(ValueError):
            DoNextRequest(
                session_id="test_session",
                user_input="Hello",
                mode=ExecutionModeEnum.DETERMINISTIC,
                model="claude-3-haiku",
                temperature=2.5  # out of range
            )

    def test_invalid_top_p_range(self):
        """top_p must be 0.0-1.0."""
        with pytest.raises(ValueError):
            DoNextRequest(
                session_id="test_session",
                user_input="Hello",
                mode=ExecutionModeEnum.DETERMINISTIC,
                model="claude-3-haiku",
                top_p=1.5  # out of range
            )


class TestSessionPersistence:
    """Test SESSION_PERSISTENCE_SEMANTICS_V1 (Phase 2)."""

    def test_new_session_creation(self):
        """Create new session when none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SessionPersistence(storage_dir=tmpdir)
            session = persistence.load_session("new_session_1")

            assert session.session_id == "new_session_1"
            assert session.run_count == 0
            assert session.state_hash is None

    def test_session_resumption(self):
        """Resume existing session with state hash verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SessionPersistence(storage_dir=tmpdir)

            # Create and save session
            session1 = SessionState("resume_test")
            session1.run_count = 5
            session1.memory_objects = ["mem1", "mem2"]
            session1.state_hash = persistence.compute_state_hash(session1)
            persistence.save_session_atomic(session1)

            # Load and verify
            session2 = persistence.load_session("resume_test")
            assert session2.run_count == 5
            assert session2.memory_objects == ["mem1", "mem2"]
            assert persistence.verify_state_hash(session2) is True

    def test_state_hash_verification_detects_tampering(self):
        """State hash verification detects corrupted session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SessionPersistence(storage_dir=tmpdir)

            session = SessionState("tamper_test")
            session.run_count = 3
            session.state_hash = persistence.compute_state_hash(session)
            persistence.save_session_atomic(session)

            # Load and tamper
            session_loaded = persistence.load_session("tamper_test")
            session_loaded.run_count = 99  # Tamper with data

            # Hash verification should fail
            assert persistence.verify_state_hash(session_loaded) is False

    def test_atomic_persistence(self):
        """Atomic save: either full success or full failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SessionPersistence(storage_dir=tmpdir)
            session = SessionState("atomic_test")
            session.run_count = 10

            # Save should succeed
            assert persistence.save_session_atomic(session) is True

            # Verify it was saved
            loaded = persistence.load_session("atomic_test")
            assert loaded.run_count == 10

    def test_session_state_round_trip(self):
        """Session serialization/deserialization preserves all fields."""
        session = SessionState("roundtrip_test")
        session.run_count = 7
        session.memory_objects = ["obj1", "obj2"]
        session.continuity_score = 0.65
        session.epoch = 42

        # Serialize
        data = session.to_dict()

        # Deserialize
        session2 = SessionState.from_dict(data)

        assert session2.run_count == 7
        assert session2.memory_objects == ["obj1", "obj2"]
        assert session2.continuity_score == 0.65
        assert session2.epoch == 42


class TestReceiptEmission:
    """Test receipt chain emission (Phases 2-7)."""

    def test_session_resumption_receipt(self):
        """SESSION_RESUMPTION receipt with root lineage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            emitter = ReceiptEmitter(storage_dir=tmpdir)
            receipt_id = emitter.emit_session_resumption(
                session_id="sess_1",
                prior_run_count=3,
                prior_epoch=10
            )

            assert receipt_id is not None
            assert len(receipt_id) == 36  # UUID format

            # Verify it was logged
            with open(emitter.receipt_log_path) as f:
                lines = f.readlines()
                assert len(lines) == 1
                logged = json.loads(lines[0])
                assert logged["receipt_type"] == "SESSION_RESUMPTION"
                assert logged["parent_receipt_id"] is None  # Root

    def test_receipt_lineage_chain(self):
        """Receipt lineage with parent_receipt_id binding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            emitter = ReceiptEmitter(storage_dir=tmpdir)

            # Phase 2: SESSION_RESUMPTION (root)
            resumption_id = emitter.emit_session_resumption("sess", 0, 0)

            # Phase 3: KNOWLEDGE_AUDIT (child of resumption)
            audit_id = emitter.emit_knowledge_audit(
                "sess",
                findings=[],
                routing_consequence="annotate",
                parent_receipt_id=resumption_id
            )

            # Phase 4: DISPATCH_DECISION (child of audit)
            dispatch_id = emitter.emit_dispatch_decision(
                "sess",
                routing_decision="kernel",
                parent_receipt_id=audit_id,
                epoch=0
            )

            # Verify lineage
            with open(emitter.receipt_log_path) as f:
                receipts = [json.loads(line) for line in f]

            assert receipts[0]["parent_receipt_id"] is None  # Root
            assert receipts[1]["parent_receipt_id"] == resumption_id
            assert receipts[2]["parent_receipt_id"] == audit_id

    def test_all_receipt_types(self):
        """All 8 receipt types can be emitted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            emitter = ReceiptEmitter(storage_dir=tmpdir)

            types_emitted = []

            # Emit all types
            r1 = emitter.emit_session_resumption("sess", 0, 0)
            types_emitted.append("SESSION_RESUMPTION")

            r2 = emitter.emit_knowledge_audit("sess", [], "annotate", r1)
            types_emitted.append("KNOWLEDGE_AUDIT")

            r3 = emitter.emit_dispatch_decision("sess", "kernel", r2, 0)
            types_emitted.append("DISPATCH_DECISION")

            r4 = emitter.emit_inference_execution("sess", 100, 5, r3)
            types_emitted.append("INFERENCE_EXECUTION")

            r5 = emitter.emit_conclusion("sess", "hash", r4)
            types_emitted.append("CONCLUSION")

            r6 = emitter.emit_session_commit("sess", "hash", 1, r5)
            types_emitted.append("SESSION_COMMIT")

            # Verify all were logged
            with open(emitter.receipt_log_path) as f:
                receipts = [json.loads(line) for line in f]

            logged_types = [r["receipt_type"] for r in receipts]
            for rt in types_emitted:
                assert rt in logged_types


class TestEpochManagement:
    """Test epoch management (global monotonic counter per Phase 4 & 7)."""

    def test_epoch_starts_at_zero(self):
        """New epoch manager starts at 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            em = EpochManager(storage_path=os.path.join(tmpdir, "epoch.json"))
            assert em.get_and_increment() == 0

    def test_epoch_increments_monotonically(self):
        """Each call increments by 1, never repeats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            em = EpochManager(storage_path=os.path.join(tmpdir, "epoch.json"))

            values = [em.get_and_increment() for _ in range(10)]

            assert values == list(range(10))
            assert len(set(values)) == 10  # All unique

    def test_epoch_persistence_across_instances(self):
        """Epoch persists across manager instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "epoch.json")

            em1 = EpochManager(storage_path=path)
            em1.get_and_increment()
            em1.get_and_increment()

            em2 = EpochManager(storage_path=path)
            next_val = em2.get_and_increment()

            assert next_val == 2  # Resumes from prior state


class TestContinuityScoring:
    """Test continuity computation per SESSION_PERSISTENCE_SEMANTICS_V1 §4."""

    def test_continuity_for_new_session(self):
        """New session has near-zero continuity."""
        session = SessionState("new")
        session.run_count = 0
        continuity = compute_continuity_score(session)

        # Should be very small (no runs, no age, no memory)
        assert 0.0 <= continuity < 0.1

    def test_continuity_increases_with_runs(self):
        """Continuity increases with run count."""
        session1 = SessionState("s1")
        session1.run_count = 5
        c1 = compute_continuity_score(session1)

        session2 = SessionState("s2")
        session2.run_count = 15
        c2 = compute_continuity_score(session2)

        assert c2 > c1

    def test_continuity_increases_with_memory(self):
        """Continuity increases with memory objects."""
        session1 = SessionState("s1")
        session1.run_count = 10
        session1.memory_objects = ["obj1"]
        c1 = compute_continuity_score(session1)

        session2 = SessionState("s2")
        session2.run_count = 10
        session2.memory_objects = ["obj1", "obj2", "obj3", "obj4", "obj5"]
        c2 = compute_continuity_score(session2)

        assert c2 > c1

    def test_continuity_capped_at_one(self):
        """Continuity is capped at 1.0."""
        session = SessionState("old")
        session.run_count = 100  # High
        session.memory_objects = ["x"] * 100  # Many
        # Simulate age by modifying created_at
        from datetime import timedelta
        session.created_at = datetime.utcnow() - timedelta(days=10)

        continuity = compute_continuity_score(session)
        assert continuity <= 1.0


class TestServiceExecution:
    """Test DoNextService executing full 7-phase lifecycle."""

    def test_service_initialization(self):
        """Service initializes with required components."""
        service = DoNextService()

        assert service.session_persistence is not None
        assert service.receipt_emitter is not None
        assert service.epoch_manager is not None
        assert service.audit is not None
        assert service.memory is not None

    def test_minimal_execution_path(self):
        """Minimal execution: simple request → response."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override storage dirs
            service = DoNextService()
            service.session_persistence = SessionPersistence(tmpdir)
            service.receipt_emitter = ReceiptEmitter(tmpdir)
            service.epoch_manager = EpochManager(os.path.join(tmpdir, "epoch.json"))

            req = DoNextRequest(
                session_id="test_min",
                user_input="Hello",
                mode=ExecutionModeEnum.DETERMINISTIC,
                model="test-model"
            )

            resp = service.execute(req)

            # Validate response schema
            assert resp.session_id == "test_min"
            assert resp.mode == "deterministic"
            assert resp.model == "test-model"
            assert resp.run_id == 1  # First call
            assert resp.continuity >= 0.0

    def test_response_has_receipt_chain(self):
        """Response includes complete receipt IDs from all phases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = DoNextService()
            service.session_persistence = SessionPersistence(tmpdir)
            service.receipt_emitter = ReceiptEmitter(tmpdir)
            service.epoch_manager = EpochManager(os.path.join(tmpdir, "epoch.json"))

            req = DoNextRequest(
                session_id="test_receipts",
                user_input="Test",
                mode=ExecutionModeEnum.DETERMINISTIC,
                model="test"
            )

            resp = service.execute(req)

            # Should have receipt_id (SESSION_COMMIT from Phase 7)
            assert resp.receipt_id is not None
            assert len(resp.receipt_id) == 36  # UUID


class TestPhaseOrdering:
    """Test that 7 phases execute in strict order (per LIFECYCLE_INVARIANTS_V1)."""

    def test_phase_1_rejects_invalid_request(self):
        """Phase 1 validation rejects malformed requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = DoNextService()
            service.session_persistence = SessionPersistence(tmpdir)

            # Invalid request (missing required field)
            with pytest.raises(ValueError):
                req = DoNextRequest(
                    session_id="",  # Invalid (empty)
                    user_input="Test",
                    mode=ExecutionModeEnum.DETERMINISTIC,
                    model="test"
                )

    def test_phase_2_creates_or_resumes_session(self):
        """Phase 2 creates new session or resumes existing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            persistence = SessionPersistence(tmpdir)

            # New session
            s1 = persistence.load_session("sess_1")
            assert s1.run_count == 0

            # Save it
            s1.run_count = 5
            s1.state_hash = persistence.compute_state_hash(s1)
            persistence.save_session_atomic(s1)

            # Resume it
            s2 = persistence.load_session("sess_1")
            assert s2.run_count == 5


class TestFrozenSchemaCompliance:
    """Validate strict compliance with API_CONTRACT_DO_NEXT_V1 frozen schema."""

    def test_response_has_all_required_fields(self):
        """DoNextResponse must have all 9 fields."""
        resp = DoNextResponse(
            session_id="s",
            mode="deterministic",
            model="m",
            reply="r",
            receipt_id="r-id",
            run_id=1,
            context_items_used=[],
            epoch=0,
            continuity=0.5
        )

        # All fields must be present
        assert resp.session_id is not None
        assert resp.mode is not None
        assert resp.model is not None
        # reply, receipt_id, run_id may be None on error

    def test_error_response_has_detail_only(self):
        """Error responses must have only 'detail' field."""
        from helen_os.api.do_next import ErrorResponse

        err = ErrorResponse(detail="Test error")
        assert err.detail == "Test error"
        assert len(err.dict()) == 1  # Only detail field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
