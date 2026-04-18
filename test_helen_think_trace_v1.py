"""
Tests for HELEN_THINK_TRACE_V1 and THINK route in dispatch.

Constitutional proof targets:
1. THINK route is NON_SOVEREIGN (never SOVEREIGN or EXPLORATORY)
2. THINK allows only TRACE_WRITE — no artifact_write, candidate_write, etc.
3. ThinkTrace authority is always "NONE" (invariant, unforgeable)
4. ThinkTrace may_alter_state is always False
5. ThinkTrace may_govern is always False
6. ThinkTrace may_promote is always False
7. ThinkTrace replay_visible is always True
8. ThinkTrace causal_scope is always "preparation_only"
9. ThinkTrace hash is deterministic (same content → same hash)
10. THINK route triggered by explicit THINK_PREPARATION input type
11. THINK route triggered by USER_QUERY with think=True marker
12. THINK secondary routes are SKILL and AGENT (work routes, not KERNEL)
13. THINK forbidden effects include all state-affecting writes
14. All reason codes are frozen (no ad hoc strings)
"""

import pytest
from helen_dispatch_v1_router import DispatchRouter
from helen_dispatch_v1_schemas import (
    RouteType, RouteAuthorityClass, AllowedEffect, ForbiddenEffect,
    DISPATCH_REASON_CODES, InputType
)
from helen_think_trace_v1 import ThinkTrace, ThinkTraceBuilder, hash_think_trace


# ===========================================================================
# TEST CLASS 1: THINK ROUTE IN DISPATCH
# ===========================================================================

class TestThinkRouteDispatch:
    """THINK route: routing law and authority invariants."""

    def setup_method(self):
        self.router = DispatchRouter(session_id="s_think_001", manifest_ref="sha256:test_m")

    def test_think_preparation_input_routes_to_think(self):
        """Explicit THINK_PREPARATION input_type → THINK route."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "payload": {"query": "What should I decompose first?"},
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        assert receipt.primary_route == RouteType.THINK

    def test_user_query_with_think_marker_routes_to_think(self):
        """USER_QUERY + think=True → THINK route."""
        inp = {
            "session_id": "s1",
            "input_type": "user_query",
            "think": True,
            "payload": {"text": "Multi-part complex question requiring decomposition"},
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        assert receipt.primary_route == RouteType.THINK

    def test_think_route_is_non_sovereign(self):
        """THINK authority class is NON_SOVEREIGN — never SOVEREIGN."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        assert receipt.route_authority_class == RouteAuthorityClass.NON_SOVEREIGN
        assert receipt.route_authority_class != RouteAuthorityClass.SOVEREIGN
        assert receipt.route_authority_class != RouteAuthorityClass.EXPLORATORY

    def test_think_allows_trace_write_only(self):
        """THINK allowed effects: READ_ONLY + TRACE_WRITE only."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        allowed = receipt.allowed_effects
        assert AllowedEffect.TRACE_WRITE in allowed
        assert AllowedEffect.READ_ONLY in allowed
        # These must NOT be allowed on THINK route
        assert AllowedEffect.ARTIFACT_WRITE not in allowed
        assert AllowedEffect.CANDIDATE_WRITE not in allowed
        assert AllowedEffect.DERIVED_WRITE not in allowed

    def test_think_forbids_all_state_mutations(self):
        """THINK forbidden effects: all 5 state-mutation types."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        forbidden = receipt.forbidden_effects
        assert ForbiddenEffect.CANONICAL_PROMOTION in forbidden
        assert ForbiddenEffect.RECEIPT_MUTATION in forbidden
        assert ForbiddenEffect.PIPELINE_SUBSTITUTION in forbidden
        assert ForbiddenEffect.MEMORY_SCOPE_CHANGE in forbidden
        assert ForbiddenEffect.SILENT_SUBSTITUTION in forbidden

    def test_think_secondary_routes_are_work_routes(self):
        """THINK secondary routes: SKILL and AGENT — not KERNEL."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        assert RouteType.KERNEL not in receipt.secondary_routes
        assert RouteType.TEMPLE not in receipt.secondary_routes
        # At least one work route
        assert any(r in receipt.secondary_routes for r in (RouteType.SKILL, RouteType.AGENT))

    def test_think_reason_codes_are_frozen(self):
        """All reason codes in THINK receipt are in the frozen set."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        for code in receipt.reason_codes:
            assert code in DISPATCH_REASON_CODES, f"Ad hoc reason code: {code}"

    def test_think_receipt_has_deterministic_hash(self):
        """Same THINK input → same receipt_hash across runs."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "resolution_status": "resolved",
            "payload": {"query": "stable query for hashing"},
        }
        hashes = set()
        for _ in range(10):
            receipt, _ = self.router.route(inp)
            hashes.add(receipt.receipt_hash)
        assert len(hashes) == 1, "DRIFT DETECTED: THINK receipt_hash not deterministic"

    def test_user_query_without_think_marker_routes_to_agent(self):
        """Plain USER_QUERY (no think=True) does NOT route to THINK."""
        inp = {
            "session_id": "s1",
            "input_type": "user_query",
            "payload": {"text": "Simple question"},
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        assert receipt.primary_route != RouteType.THINK

    def test_think_unresolved_still_defers(self):
        """Even THINK_PREPARATION with unresolved pointers → DEFER (not THINK)."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s1",
            "unresolved_pointers": ["ptr://doc_001"],
        }
        receipt, _ = self.router.route(inp)
        assert receipt.primary_route == RouteType.DEFER


# ===========================================================================
# TEST CLASS 2: ThinkTrace CONSTITUTIONAL INVARIANTS
# ===========================================================================

class TestThinkTraceInvariants:
    """ThinkTrace: all constitutional invariants are frozen and verifiable."""

    def setup_method(self):
        self.builder = ThinkTraceBuilder()

    def _basic_trace(self, **kwargs):
        defaults = dict(
            session_id="s_001",
            dispatch_id_ref="disp_001",
            raw_input_summary="Test input",
        )
        defaults.update(kwargs)
        return self.builder.emit(**defaults)

    def test_authority_always_none(self):
        """ThinkTrace.authority is always 'NONE' — cannot be overridden."""
        trace = self._basic_trace()
        assert trace.authority == "NONE"

    def test_may_alter_state_always_false(self):
        """ThinkTrace.may_alter_state is always False."""
        trace = self._basic_trace()
        assert trace.may_alter_state is False

    def test_may_govern_always_false(self):
        """ThinkTrace.may_govern is always False."""
        trace = self._basic_trace()
        assert trace.may_govern is False

    def test_may_promote_always_false(self):
        """ThinkTrace.may_promote is always False."""
        trace = self._basic_trace()
        assert trace.may_promote is False

    def test_replay_visible_always_true(self):
        """ThinkTrace.replay_visible is always True — preparation must be auditable."""
        trace = self._basic_trace()
        assert trace.replay_visible is True

    def test_causal_scope_always_preparation_only(self):
        """ThinkTrace.causal_scope is always 'preparation_only'."""
        trace = self._basic_trace()
        assert trace.causal_scope == "preparation_only"

    def test_validate_non_authority_passes_clean_trace(self):
        """validate_non_authority returns True for a properly constructed trace."""
        trace = self._basic_trace()
        assert self.builder.validate_non_authority(trace) is True

    def test_validate_invariants_returns_all_true(self):
        """All invariants pass for a properly emitted trace."""
        trace = self._basic_trace()
        results = self.builder.validate_invariants(trace)
        for invariant, ok in results.items():
            assert ok, f"Invariant failed: {invariant}"


# ===========================================================================
# TEST CLASS 3: ThinkTrace DETERMINISM
# ===========================================================================

class TestThinkTraceDeterminism:
    """ThinkTrace hash must be deterministic — same content → same hash."""

    def setup_method(self):
        self.builder = ThinkTraceBuilder()

    def test_same_content_same_hash(self):
        """Same decomposition + same dispatch_id_ref → same trace_hash."""
        common_kwargs = dict(
            session_id="s_hash",
            dispatch_id_ref="disp_hash_001",
            raw_input_summary="Stable input for hash test",
            decomposition_steps=[
                {"observation": "Part A", "uncertainty": 0.1, "suggested_route": "SKILL"},
                {"observation": "Part B", "uncertainty": 0.3, "suggested_route": "AGENT"},
            ],
            candidate_routes=["SKILL", "AGENT"],
            preparation_confidence=0.8,
        )
        hashes = set()
        for _ in range(10):
            trace = self.builder.emit(**common_kwargs)
            hashes.add(trace.trace_hash)
        assert len(hashes) == 1, "DRIFT: ThinkTrace hash not deterministic"

    def test_different_content_different_hash(self):
        """Different decomposition → different trace_hash."""
        t1 = self.builder.emit(
            session_id="s1", dispatch_id_ref="d1", raw_input_summary="Input A"
        )
        t2 = self.builder.emit(
            session_id="s1", dispatch_id_ref="d1", raw_input_summary="Input B"
        )
        assert t1.trace_hash != t2.trace_hash

    def test_hash_excludes_run_metadata(self):
        """trace_id and timestamp (run metadata) do not affect hash."""
        common = dict(
            session_id="s_meta",
            dispatch_id_ref="disp_meta",
            raw_input_summary="Meta exclusion test",
            candidate_routes=["SKILL"],
        )
        # Two traces — different trace_id and timestamp, same semantic content
        t1 = self.builder.emit(**common)
        t2 = self.builder.emit(**common)
        assert t1.trace_id != t2.trace_id  # Different run IDs
        assert t1.trace_hash == t2.trace_hash  # Same semantic hash

    def test_hash_includes_constitutional_invariants(self):
        """Constitutional fields (authority, may_alter_state...) are included in hash."""
        trace = self.builder.emit(
            session_id="s_const", dispatch_id_ref="d_const", raw_input_summary="Invariant test"
        )
        hashable = trace.to_dict(exclude_run_metadata=True)
        assert "authority" in hashable
        assert "may_alter_state" in hashable
        assert "may_govern" in hashable
        assert "may_promote" in hashable
        assert "replay_visible" in hashable
        assert "causal_scope" in hashable


# ===========================================================================
# TEST CLASS 4: ThinkTrace STRUCTURE
# ===========================================================================

class TestThinkTraceStructure:
    """ThinkTrace: content structure and decomposition correctness."""

    def setup_method(self):
        self.builder = ThinkTraceBuilder()

    def test_decomposition_steps_emitted_correctly(self):
        """Decomposition steps are correctly built."""
        trace = self.builder.emit(
            session_id="s1",
            dispatch_id_ref="d1",
            raw_input_summary="Complex question",
            decomposition_steps=[
                {"observation": "Requires claim extraction", "uncertainty": 0.2, "suggested_route": "SKILL"},
                {"observation": "Requires format transform", "uncertainty": 0.1, "suggested_route": "AGENT"},
            ],
        )
        assert len(trace.decomposition) == 2
        assert trace.decomposition[0].observation == "Requires claim extraction"
        assert trace.decomposition[1].suggested_route == "AGENT"
        # Constitutional invariants apply to each step
        for step in trace.decomposition:
            assert step.authority == "NONE"
            assert step.may_alter_state is False

    def test_route_preparation_has_no_authority(self):
        """RoutePreparation authority is always 'NONE'."""
        trace = self.builder.emit(
            session_id="s1",
            dispatch_id_ref="d1",
            raw_input_summary="Preparation test",
            candidate_routes=["SKILL", "AGENT"],
            blocking_concerns=["Missing context X"],
        )
        assert trace.route_preparation.authority == "NONE"
        assert trace.route_preparation.candidate_routes == ["SKILL", "AGENT"]

    def test_trace_links_to_dispatch_receipt(self):
        """ThinkTrace has a dispatch_id_ref linking it to the triggering DispatchReceipt."""
        trace = self.builder.emit(
            session_id="s1",
            dispatch_id_ref="disp_abc_123",
            raw_input_summary="Lineage test",
        )
        assert trace.dispatch_id_ref == "disp_abc_123"

    def test_trace_has_hash(self):
        """ThinkTrace emits with a non-null SHA256 hash."""
        trace = self.builder.emit(
            session_id="s1", dispatch_id_ref="d1", raw_input_summary="Hash presence"
        )
        assert trace.trace_hash is not None
        assert trace.trace_hash.startswith("sha256:")


# ===========================================================================
# TEST CLASS 5: INTEGRATION — DISPATCH THINK → TRACE
# ===========================================================================

class TestThinkRouteToTraceIntegration:
    """Integration: THINK route emits receipt, trace links back via dispatch_id_ref."""

    def setup_method(self):
        self.router = DispatchRouter(session_id="s_int", manifest_ref="sha256:manifest_int")
        self.builder = ThinkTraceBuilder()

    def test_think_receipt_to_trace_lineage(self):
        """Dispatch THINK receipt → ThinkTrace with matching dispatch_id_ref."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s_int",
            "payload": {"query": "Decompose this for me"},
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        assert receipt.primary_route == RouteType.THINK

        # Now emit a trace linked to this dispatch
        trace = self.builder.emit(
            session_id="s_int",
            dispatch_id_ref=receipt.dispatch_id,
            raw_input_summary="Decompose this for me",
            candidate_routes=["SKILL"],
        )

        assert trace.dispatch_id_ref == receipt.dispatch_id
        assert self.builder.validate_non_authority(trace) is True
        assert trace.route_preparation.authority == "NONE"

    def test_think_trace_cannot_change_receipt(self):
        """A ThinkTrace cannot modify the dispatch receipt (receipt immutability)."""
        inp = {
            "input_type": "THINK_PREPARATION",
            "session_id": "s_int",
            "resolution_status": "resolved",
        }
        receipt, _ = self.router.route(inp)
        original_hash = receipt.receipt_hash

        # Emit a trace — receipt must remain unchanged
        _ = self.builder.emit(
            session_id="s_int",
            dispatch_id_ref=receipt.dispatch_id,
            raw_input_summary="Cannot touch the receipt",
        )

        assert receipt.receipt_hash == original_hash, "Receipt was mutated — violation"
