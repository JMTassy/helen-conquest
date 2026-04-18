"""
HELEN_DISPATCH_LAYER_V1: Routing and Dispatch Schemas

This module defines the frozen schemas for:
- InputType classification
- RouteType (KERNEL, SKILL, AGENT, TEMPLE, DEFER, REJECT)
- DispatchReceipt (immutable routing decision)
- RouteAuthorityClass (sovereign/non_sovereign/exploratory/blocked)
- MutationIntent (none/candidate_write/derived_write/canonical_request/pipeline_change)

Principles:
- Deterministic: same input → same route hash across all runs
- Non-sovereign: dispatch does not make final authority decisions, only routes
- Immutable: receipts are append-only, never modified
- Unresolved → DEFER/REJECT: no action without full resolution
- Promotion/substitution → KERNEL only
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


class InputType(Enum):
    """Deterministic classification of incoming requests."""
    USER_QUERY = "USER_QUERY"
    SLASH_COMMAND = "SLASH_COMMAND"
    SOURCE_INGEST = "SOURCE_INGEST"
    CLAIM_EXTRACTION_REQUEST = "CLAIM_EXTRACTION_REQUEST"
    CLAIM_OBJECT = "CLAIM_OBJECT"
    CLAIM_BUNDLE = "CLAIM_BUNDLE"
    ARTIFACT_REQUEST = "ARTIFACT_REQUEST"
    AUDIT_REQUEST = "AUDIT_REQUEST"
    MEMORY_REQUEST = "MEMORY_REQUEST"
    PROMOTION_REQUEST = "PROMOTION_REQUEST"
    TEMPLE_OBSERVATION = "TEMPLE_OBSERVATION"
    UNRESOLVED_POINTER = "UNRESOLVED_POINTER"
    PIPELINE_SUBSTITUTION_REQUEST = "PIPELINE_SUBSTITUTION_REQUEST"
    THINK_PREPARATION = "THINK_PREPARATION"  # Explicit bounded preparation request


class RouteType(Enum):
    """Dispatch routing targets."""
    KERNEL = "KERNEL"  # Sovereign decisions: admission, promotion, receipts, boundary enforcement
    SKILL = "SKILL"    # Multi-step bounded workflows (claim extraction, audits, compilation)
    AGENT = "AGENT"    # Narrow transformations (summarize, relabel, format, extract)
    TEMPLE = "TEMPLE"  # Exploratory, no canonical effects (hypotheses, probing)
    THINK = "THINK"    # Bounded preparation: decomposition, route-prep, audit-visible trace; NON-SOVEREIGN
    DEFER = "DEFER"    # Incomplete/ambiguous; missing resolution or clarification
    REJECT = "REJECT"  # Disallowed; out-of-scope, unsafe, or illegitimate


class RouteAuthorityClass(Enum):
    """Authority regime for the route."""
    SOVEREIGN = "sovereign"              # KERNEL only
    NON_SOVEREIGN = "non_sovereign"      # SKILL/AGENT
    EXPLORATORY = "exploratory"          # TEMPLE
    BLOCKED = "blocked"                  # DEFER/REJECT


class MutationIntent(Enum):
    """What kind of mutation does this request intend?"""
    NONE = "none"                                # Read-only
    CANDIDATE_WRITE = "candidate_write"        # Propose new object (not canonical)
    DERIVED_WRITE = "derived_write"            # Generate artifact from canon
    CANONICAL_REQUEST = "canonical_request"    # Request promotion to canon
    PIPELINE_CHANGE = "pipeline_change"        # Substitute pipeline or flow


class ResolutionStatus(Enum):
    """Is the input fully resolvable?"""
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    PARTIAL = "partial"


class AdmissibilityStatus(Enum):
    """Can we act on this input?"""
    ADMIT = "admit"      # Yes, route and execute
    BLOCK = "block"      # No, violation or forbidden
    DEFER = "defer"      # Maybe, but needs more input/resolution


class AllowedEffect(Enum):
    """What side effects are allowed?"""
    READ_ONLY = "read_only"
    ARTIFACT_WRITE = "artifact_write"
    CANDIDATE_WRITE = "candidate_write"
    DERIVED_WRITE = "derived_write"
    TRACE_WRITE = "trace_write"    # Write an auditable, non-sovereign preparation trace (THINK route only)


class ForbiddenEffect(Enum):
    """What side effects are forbidden?"""
    CANONICAL_PROMOTION = "canonical_promotion"
    RECEIPT_MUTATION = "receipt_mutation"
    PIPELINE_SUBSTITUTION = "pipeline_substitution"
    MEMORY_SCOPE_CHANGE = "memory_scope_change"
    SILENT_SUBSTITUTION = "silent_substitution"


@dataclass
class DispatchReceipt:
    """
    Immutable record of a dispatch decision.

    Key invariant:
    - Append-only ledger (never modify after emission)
    - Contains all information to reconstruct routing decision
    - Deterministic: same input → same hash
    """
    dispatch_id: str
    timestamp: str  # ISO-8601 with timezone
    session_id: str
    input_hash: str  # SHA256 of input

    # Classification
    input_type: InputType
    resolution_status: ResolutionStatus
    admissibility_status: AdmissibilityStatus

    # Routing decision
    primary_route: RouteType
    secondary_routes: List[RouteType] = field(default_factory=list)
    route_authority_class: RouteAuthorityClass = RouteAuthorityClass.NON_SOVEREIGN
    mutation_intent: MutationIntent = MutationIntent.NONE

    # Reason codes (frozen set; no ad hoc strings)
    reason_codes: List[str] = field(default_factory=list)

    # Effects
    allowed_effects: List[AllowedEffect] = field(default_factory=list)
    forbidden_effects: List[ForbiddenEffect] = field(default_factory=list)

    # Signals
    pressure_signal_ref: Optional[str] = None

    # Manifests and stores
    manifest_ref: Optional[str] = None
    store_refs: Dict[str, str] = field(default_factory=dict)  # context/ledger/transcript

    # Error if any
    error: Optional[Dict[str, str]] = None

    # Metadata
    receipt_hash: Optional[str] = None  # SHA256 of full receipt (excluding this field)

    def to_dict(self, exclude_run_metadata: bool = False) -> Dict[str, Any]:
        """
        Serialize to dict.

        Args:
            exclude_run_metadata: If True, exclude dispatch_id and timestamp.
                                 These are unique per run, not part of routing
                                 decision logic. Excluded for receipt_hash to
                                 ensure determinism: same input → same hash
                                 across all runs.
        """
        result = {
            "dispatch_id": self.dispatch_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "input_hash": self.input_hash,
            "input_type": self.input_type.value,
            "resolution_status": self.resolution_status.value,
            "admissibility_status": self.admissibility_status.value,
            "primary_route": self.primary_route.value,
            "secondary_routes": [r.value for r in self.secondary_routes],
            "route_authority_class": self.route_authority_class.value,
            "mutation_intent": self.mutation_intent.value,
            "reason_codes": self.reason_codes,
            "allowed_effects": [e.value for e in self.allowed_effects],
            "forbidden_effects": [e.value for e in self.forbidden_effects],
            "pressure_signal_ref": self.pressure_signal_ref,
            "manifest_ref": self.manifest_ref,
            "store_refs": self.store_refs,
            "error": self.error,
        }

        if exclude_run_metadata:
            # Remove fields that vary per run but are not part of decision
            del result["dispatch_id"]
            del result["timestamp"]

        return result

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)


@dataclass
class RejectionPacket:
    """
    Issued when dispatch returns REJECT or DEFER.

    Invariant: Explains why blocked and what's required to unblock.
    """
    rejection_id: str
    timestamp: str
    input_id: str
    reason_codes: List[str]
    message_class: str  # "clarify_before_action" | "out_of_scope" | "unsafe" | "resolution_required"
    can_retry: bool
    retry_requirements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rejection_id": self.rejection_id,
            "timestamp": self.timestamp,
            "input_id": self.input_id,
            "reason_codes": self.reason_codes,
            "message_class": self.message_class,
            "can_retry": self.can_retry,
            "retry_requirements": self.retry_requirements,
        }


# ============================================================================
# FROZEN REASON CODES (V1)
# ============================================================================
# These are the only permitted reason_codes in DispatchReceipt.
# No ad hoc strings; all paths must register here.

DISPATCH_REASON_CODES = {
    # Classification
    "input_classified_as_user_query",
    "input_classified_as_slash_command",
    "input_classified_as_source_ingest",
    "input_classified_as_claim_extraction_request",
    "input_classified_as_claim_object",
    "input_classified_as_claim_bundle",
    "input_classified_as_artifact_request",
    "input_classified_as_audit_request",
    "input_classified_as_memory_request",
    "input_classified_as_promotion_request",
    "input_classified_as_temple_observation",
    "input_classified_as_unresolved_pointer",
    "input_classified_as_pipeline_substitution_request",
    "input_classified_as_think_preparation",  # THINK route

    # Resolution/Admissibility
    "unresolved_pointers_present",
    "resolution_required_before_action",
    "promotion_requested",
    "pipeline_substitution_requested",
    "temple_exploration_mode",
    "multi_step_workflow_detected",
    "single_transform_detected",
    "unsafe_request_detected",
    "insufficient_evidence",
    "non_sovereign_surface_only",
    "governed_state_requested",
    "memory_promotion_requested",
    "scope_boundary_touched",
    "receipt_or_replay_requested",
    "law_or_axiom_question",

    # Route decisions
    "routing_to_kernel_sovereign",
    "routing_to_skill_workflow",
    "routing_to_agent_transform",
    "routing_to_temple_exploration",
    "routing_to_think_preparation",      # THINK route: bounded preparation, audit-visible
    "routing_deferred_incomplete",
    "routing_rejected_disallowed",

    # Think-specific
    "think_preparation_requested",       # Explicit THINK_PREPARATION input type
    "think_preparation_complex_query",   # Multi-part USER_QUERY routed to THINK
    "think_preparation_non_sovereign",   # Confirms THINK has no authority

    # Effects
    "allowing_read_only",
    "allowing_artifact_write",
    "allowing_candidate_write",
    "allowing_trace_write",              # THINK route only: write preparation trace
    "forbidding_canonical_promotion",
    "forbidding_receipt_mutation",
    "forbidding_pipeline_substitution",
    "forbidding_memory_scope_change",
    "forbidding_silent_substitution",
}


def validate_reason_codes(codes: List[str]) -> bool:
    """Verify all reason codes are frozen (registered)."""
    return all(code in DISPATCH_REASON_CODES for code in codes)


# ============================================================================
# DETERMINISM & HASHING
# ============================================================================

def canonical_json_hash(obj: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of a dict with canonical JSON serialization.
    Sort keys for determinism; use compact format.
    """
    import hashlib
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def hash_dispatch_receipt(receipt: DispatchReceipt) -> str:
    """
    Compute receipt hash (deterministic, excluding run-specific metadata).

    Exclusions:
    - dispatch_id: unique per run, not part of decision
    - timestamp: unique per run, not part of decision

    Invariant:
    same input + same config → same receipt_hash across all runs

    This ensures the hash reflects the ROUTING DECISION only, not the run metadata.
    """
    data = receipt.to_dict(exclude_run_metadata=True)
    return canonical_json_hash(data)
