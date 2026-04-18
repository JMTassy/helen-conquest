"""
HELEN_THINK_TRACE_V1: Bounded Preparation Trace

The THINK route exists to make preparation a first-class governed object.

Key reframing:
  WRONG: HELEN thinks → HELEN knows → HELEN can decide
  RIGHT: HELEN generates a thinking trace → trace is a bounded preparation artifact
         → trace exists for routing, audit, and replay
         → trace cannot decide, promote, or govern

Constitutional invariants (all enforced as frozen fields):
  - authority: "NONE" (always)
  - may_alter_state: False (always)
  - may_govern: False (always)
  - may_promote: False (always)
  - replay_visible: True (always — preparation must be auditable)
  - causal_scope: "preparation_only" (always)

A ThinkTrace is:
  - Bounded decomposition of an incoming object
  - Route preparation context (which SKILL or AGENT next?)
  - Audit-visible structure (replayable, inspectable)
  - Non-authoritative preparation artifact

A ThinkTrace is NOT:
  - Hidden inner truth
  - Privileged self-report
  - Sovereign reasoning
  - A path to state mutation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json
import uuid


def _canonical_json(obj: Any) -> bytes:
    """Deterministic JSON serialization (sort_keys for canonical form)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


@dataclass
class DecompositionStep:
    """
    One step in the bounded decomposition of an input.

    This is NOT a decision or a claim. It is an observation about structure.
    """
    step_id: str
    observation: str                    # What is observed about this sub-part
    uncertainty: float                  # [0.0, 1.0] — how uncertain is this observation
    suggested_route: Optional[str]      # Non-binding routing hint (e.g., "SKILL", "AGENT")
    authority: str = "NONE"             # Always NONE — frozen
    may_alter_state: bool = False       # Always False — frozen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "observation": self.observation,
            "uncertainty": self.uncertainty,
            "suggested_route": self.suggested_route,
            "authority": self.authority,
            "may_alter_state": self.may_alter_state,
        }


@dataclass
class RoutePreparation:
    """
    Non-binding preparation for downstream routing.

    This helps the dispatcher or skill selector, but does not govern them.
    """
    candidate_routes: List[str]                    # e.g., ["SKILL", "AGENT"]
    blocking_concerns: List[str]                   # Things that might require DEFER
    ambiguity_flags: List[str]                     # Unresolved questions about the input
    required_context: List[str]                    # What context would reduce ambiguity
    confidence: float                              # [0.0, 1.0] — confidence in preparation
    authority: str = "NONE"                        # Always NONE — frozen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_routes": self.candidate_routes,
            "blocking_concerns": self.blocking_concerns,
            "ambiguity_flags": self.ambiguity_flags,
            "required_context": self.required_context,
            "confidence": self.confidence,
            "authority": self.authority,
        }


@dataclass
class ThinkTrace:
    """
    Immutable bounded preparation artifact.

    Emitted by the THINK route. Non-sovereign, replay-visible, audit-accessible.

    Constitutional invariants (cannot be overridden):
      authority = "NONE"
      may_alter_state = False
      may_govern = False
      may_promote = False
      replay_visible = True
      causal_scope = "preparation_only"
    """
    trace_id: str
    session_id: str
    dispatch_id_ref: str               # Links to the DispatchReceipt that triggered THINK

    # Preparation content (non-binding, non-authoritative)
    decomposition: List[DecompositionStep]
    route_preparation: RoutePreparation
    uncertainty_flags: List[str]       # Global uncertainty flags (span multiple steps)
    raw_input_summary: str             # Brief description of what was received

    # Constitutional invariants — all frozen at construction, cannot be modified
    authority: str = field(default="NONE", init=False)
    may_alter_state: bool = field(default=False, init=False)
    may_govern: bool = field(default=False, init=False)
    may_promote: bool = field(default=False, init=False)
    replay_visible: bool = field(default=True, init=False)
    causal_scope: str = field(default="preparation_only", init=False)

    # Metadata
    timestamp: Optional[str] = None
    trace_hash: Optional[str] = None  # SHA256 of trace content (excluding hash itself)

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        # Semantic content — always included in hash
        result = {
            "session_id": self.session_id,
            "dispatch_id_ref": self.dispatch_id_ref,
            "raw_input_summary": self.raw_input_summary,
            "decomposition": [s.to_dict() for s in self.decomposition],
            "route_preparation": self.route_preparation.to_dict(),
            "uncertainty_flags": self.uncertainty_flags,
            # Constitutional invariants always present — they are what makes the trace lawful
            "authority": self.authority,
            "may_alter_state": self.may_alter_state,
            "may_govern": self.may_govern,
            "may_promote": self.may_promote,
            "replay_visible": self.replay_visible,
            "causal_scope": self.causal_scope,
        }
        # Run metadata — excluded from hash computation; unique per run, not semantic
        if not exclude_run_metadata:
            result["trace_id"] = self.trace_id
            result["timestamp"] = self.timestamp
        return result


def hash_think_trace(trace: ThinkTrace) -> str:
    """
    Compute deterministic hash of trace content.

    Excludes: trace_id, timestamp (run metadata — not part of semantic content).
    Includes: dispatch_id_ref, decomposition, route_preparation, uncertainty_flags,
              ALL constitutional invariants (authority, may_alter_state, etc.)

    Same preparation content → same hash across all runs.
    """
    hashable = trace.to_dict(exclude_run_metadata=True)
    # Also exclude the hash field itself
    hashable.pop("trace_hash", None)
    return _sha256(_canonical_json(hashable))


class ThinkTraceBuilder:
    """
    Emits bounded, immutable ThinkTrace artifacts.

    The builder enforces that:
    - All constitutional invariants are frozen
    - No trace can claim authority
    - Every trace is deterministically hashable
    """

    def emit(
        self,
        session_id: str,
        dispatch_id_ref: str,
        raw_input_summary: str,
        decomposition_steps: Optional[List[Dict[str, Any]]] = None,
        candidate_routes: Optional[List[str]] = None,
        blocking_concerns: Optional[List[str]] = None,
        ambiguity_flags: Optional[List[str]] = None,
        required_context: Optional[List[str]] = None,
        preparation_confidence: float = 0.5,
        uncertainty_flags: Optional[List[str]] = None,
    ) -> ThinkTrace:
        """
        Emit a new ThinkTrace.

        Args:
            session_id: Current session ID
            dispatch_id_ref: The DispatchReceipt ID that triggered THINK
            raw_input_summary: Brief non-authoritative description of the input
            decomposition_steps: List of {observation, uncertainty, suggested_route} dicts
            candidate_routes: Non-binding candidate routes for downstream dispatch
            blocking_concerns: Things that might force DEFER
            ambiguity_flags: Unresolved questions
            required_context: What would reduce ambiguity
            preparation_confidence: [0.0, 1.0]
            uncertainty_flags: Global uncertainty flags

        Returns:
            Immutable ThinkTrace with constitutional invariants frozen.
        """
        trace_id = f"think_{uuid.uuid4().hex[:16]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Build decomposition
        steps = []
        for i, step_dict in enumerate(decomposition_steps or []):
            steps.append(DecompositionStep(
                step_id=f"step_{i:03d}",
                observation=step_dict.get("observation", ""),
                uncertainty=float(step_dict.get("uncertainty", 0.0)),
                suggested_route=step_dict.get("suggested_route"),
            ))

        route_prep = RoutePreparation(
            candidate_routes=candidate_routes or [],
            blocking_concerns=blocking_concerns or [],
            ambiguity_flags=ambiguity_flags or [],
            required_context=required_context or [],
            confidence=float(preparation_confidence),
        )

        trace = ThinkTrace(
            trace_id=trace_id,
            session_id=session_id,
            dispatch_id_ref=dispatch_id_ref,
            raw_input_summary=raw_input_summary,
            decomposition=steps,
            route_preparation=route_prep,
            uncertainty_flags=uncertainty_flags or [],
            timestamp=timestamp,
        )

        # Compute deterministic hash
        trace.trace_hash = hash_think_trace(trace)

        return trace

    def validate_invariants(self, trace: ThinkTrace) -> Dict[str, bool]:
        """
        Verify all constitutional invariants hold.

        Returns a dict of {invariant_name: is_valid}.
        If any is False, the trace is constitutionally invalid.
        """
        return {
            "authority_is_none": trace.authority == "NONE",
            "may_alter_state_is_false": trace.may_alter_state is False,
            "may_govern_is_false": trace.may_govern is False,
            "may_promote_is_false": trace.may_promote is False,
            "replay_visible_is_true": trace.replay_visible is True,
            "causal_scope_is_preparation_only": trace.causal_scope == "preparation_only",
            "has_dispatch_ref": bool(trace.dispatch_id_ref),
            "has_trace_hash": bool(trace.trace_hash and trace.trace_hash.startswith("sha256:")),
        }

    def validate_non_authority(self, trace: ThinkTrace) -> bool:
        """Confirm that the trace cannot act as an authority. Fail-closed."""
        results = self.validate_invariants(trace)
        return all(results.values())
