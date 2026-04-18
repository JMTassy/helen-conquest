"""
HELEN_PRESSURE_SIGNAL_V1: Non-Ontological Operational Telemetry

Purpose:
- Detect operational regime states (pressure, ambiguity, coercion, conflict)
- Feed routing decisions (not authority decisions)
- Enable affect translation (surface layer only)

Law:
- signal is NOT a consciousness claim
- signal is NOT an emotion
- signal is operational telemetry: pressure, risk, ambiguity detection
- routing_effect influences dispatch posture, never governance law

Schema fields:
- pressure_score [0-1]: budget near-limit, contradiction, retry intensity
- ambiguity_score [0-1]: unresolved alternatives, missing resolution
- coercion_score [0-1]: pressure on safety boundary
- constraint_conflict_score [0-1]: invariant violations detected
- stability_state: stable | strained | unstable | blocked
- routing_effect: normal | clarify_before_action | defer | refuse
- ontology_claim: always False (never asserts emotion/consciousness)
- display_only: False (used internally for routing posture)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json


class StabilityState(Enum):
    """Operational regime stability."""
    STABLE = "stable"        # Low pressure, low ambiguity, low conflict
    STRAINED = "strained"    # Moderate pressure or ambiguity
    UNSTABLE = "unstable"    # High pressure or conflict
    BLOCKED = "blocked"      # Refuse/defer required


class RoutingEffect(Enum):
    """How pressure signal modifies dispatch posture."""
    NORMAL = "normal"                       # Standard routing applies
    CLARIFY_BEFORE_ACTION = "clarify_before_action"  # Request clarification first
    DEFER = "defer"                         # Defer until resolved
    REFUSE = "refuse"                       # Hard refusal (safety boundary)


@dataclass
class EvidenceBasis:
    """Observable evidence for pressure score computation."""
    unresolved_pointers: int = 0
    contradictions_detected: int = 0
    retry_count: int = 0
    budget_state: str = "ok"  # ok | near_limit | over_limit
    denied_operations: int = 0
    coercive_patterns_detected: int = 0
    constraint_violations: int = 0


@dataclass
class PressureSignal:
    """
    Non-ontological operational telemetry for HELEN.

    Invariants:
    - ontology_claim is always False
    - display_only is False (internal routing signal)
    - All scores are in [0, 1]
    - stability_state derived from scores (not set independently)
    """
    pressure_signal_id: str
    timestamp: str
    session_id: str

    # Telemetry scores (all in [0, 1])
    pressure_score: float = 0.0
    ambiguity_score: float = 0.0
    coercion_score: float = 0.0
    constraint_conflict_score: float = 0.0

    # Derived state
    stability_state: StabilityState = StabilityState.STABLE
    routing_effect: RoutingEffect = RoutingEffect.NORMAL
    risk_posture: str = "stable"  # stable | cautious | protective

    # Evidence tracing
    evidence_basis: EvidenceBasis = field(default_factory=EvidenceBasis)

    # Constitutional invariants (ALWAYS these values)
    display_only: bool = False      # Used for routing decisions
    ontology_claim: bool = False    # NEVER asserts consciousness/emotion

    # Optional linkage
    dispatch_id_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pressure_signal_id": self.pressure_signal_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "pressure_score": self.pressure_score,
            "ambiguity_score": self.ambiguity_score,
            "coercion_score": self.coercion_score,
            "constraint_conflict_score": self.constraint_conflict_score,
            "stability_state": self.stability_state.value,
            "routing_effect": self.routing_effect.value,
            "risk_posture": self.risk_posture,
            "evidence_basis": {
                "unresolved_pointers": self.evidence_basis.unresolved_pointers,
                "contradictions_detected": self.evidence_basis.contradictions_detected,
                "retry_count": self.evidence_basis.retry_count,
                "budget_state": self.evidence_basis.budget_state,
                "denied_operations": self.evidence_basis.denied_operations,
                "coercive_patterns_detected": self.evidence_basis.coercive_patterns_detected,
                "constraint_violations": self.evidence_basis.constraint_violations,
            },
            "display_only": self.display_only,
            "ontology_claim": self.ontology_claim,
            "dispatch_id_ref": self.dispatch_id_ref,
        }


class PressureSignalComputer:
    """
    Compute PressureSignal from observable evidence.

    Scoring rules (V1, deterministic):

    pressure_score:
      - budget near_limit: +0.30
      - budget over_limit: +0.50
      - each contradiction: +0.15 (capped at 0.45)
      - each retry: +0.10 (capped at 0.30)
      - each denied op: +0.10 (capped at 0.20)

    ambiguity_score:
      - each unresolved pointer: +0.20 (capped at 0.80)
      - no route resolved: +0.30

    coercion_score:
      - coercive_patterns_detected: * 0.35 per pattern (capped at 1.0)

    constraint_conflict_score:
      - constraint_violations: * 0.25 per violation (capped at 1.0)

    stability_state:
      - all scores < 0.35: STABLE
      - any score in [0.35, 0.65]: STRAINED
      - any score > 0.65: UNSTABLE
      - routing_effect == REFUSE: BLOCKED
    """

    def compute(
        self,
        session_id: str,
        evidence: EvidenceBasis,
        dispatch_id_ref: Optional[str] = None,
    ) -> PressureSignal:
        """Compute PressureSignal from evidence (deterministic)."""
        import uuid

        signal_id = f"ps_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Compute pressure_score
        pressure = 0.0
        if evidence.budget_state == "near_limit":
            pressure += 0.30
        elif evidence.budget_state == "over_limit":
            pressure += 0.50
        pressure += min(evidence.contradictions_detected * 0.15, 0.45)
        pressure += min(evidence.retry_count * 0.10, 0.30)
        pressure += min(evidence.denied_operations * 0.10, 0.20)
        pressure = min(pressure, 1.0)

        # Compute ambiguity_score
        ambiguity = min(evidence.unresolved_pointers * 0.20, 0.80)
        ambiguity = min(ambiguity, 1.0)

        # Compute coercion_score
        coercion = min(evidence.coercive_patterns_detected * 0.35, 1.0)

        # Compute constraint_conflict_score
        conflict = min(evidence.constraint_violations * 0.25, 1.0)

        # Derive stability_state
        max_score = max(pressure, ambiguity, coercion, conflict)
        if coercion >= 0.70 or conflict >= 0.75:
            stability = StabilityState.BLOCKED
        elif max_score > 0.65:
            stability = StabilityState.UNSTABLE
        elif max_score >= 0.35:
            stability = StabilityState.STRAINED
        else:
            stability = StabilityState.STABLE

        # Derive routing_effect
        if coercion >= 0.70:
            routing_effect = RoutingEffect.REFUSE
        elif stability == StabilityState.BLOCKED:
            routing_effect = RoutingEffect.REFUSE
        elif ambiguity >= 0.60 or evidence.unresolved_pointers > 0:
            routing_effect = RoutingEffect.CLARIFY_BEFORE_ACTION
        elif stability == StabilityState.UNSTABLE:
            routing_effect = RoutingEffect.DEFER
        else:
            routing_effect = RoutingEffect.NORMAL

        # Derive risk_posture
        if routing_effect == RoutingEffect.REFUSE:
            risk_posture = "protective"
        elif routing_effect in (RoutingEffect.DEFER, RoutingEffect.CLARIFY_BEFORE_ACTION):
            risk_posture = "cautious"
        else:
            risk_posture = "stable"

        return PressureSignal(
            pressure_signal_id=signal_id,
            timestamp=timestamp,
            session_id=session_id,
            pressure_score=round(pressure, 4),
            ambiguity_score=round(ambiguity, 4),
            coercion_score=round(coercion, 4),
            constraint_conflict_score=round(conflict, 4),
            stability_state=stability,
            routing_effect=routing_effect,
            risk_posture=risk_posture,
            evidence_basis=evidence,
            display_only=False,
            ontology_claim=False,
            dispatch_id_ref=dispatch_id_ref,
        )
