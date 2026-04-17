#!/usr/bin/env python3
"""
NPC SCHEMAS — FORMAL SPECIFICATION (v1.0)

Status: CONSTITUTIONAL SUPPORT
Authority: NONE
Function: OBSERVATION ONLY

NPCs are non-playing constitutional witnesses.
They cannot decide, cannot recommend, cannot optimize, cannot trigger action.

They exist to answer one question only:
"What actually happened under the doctrine we ratified?"

---

FOUNDATIONAL RULES (NON-NEGOTIABLE)

1. No prescriptions
   NPC output must not contain: "should", "must", "recommend", "better", "worse"

2. No future tense
   NPCs do not predict. They measure the past.

3. Ledger-bound only
   Every claim must reference existing receipts.

4. Doctrine-pinned
   Every NPC observation must explicitly reference doctrine_hash and doctrine_version.

5. Silence is valid output
   An NPC may emit nothing for a window. Silence is data.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Optional
import json
import hashlib


class NPCType(Enum):
    """The four canonical NPC types. Adding more requires doctrine amendment."""
    ACCURACY_WATCHER = "accuracy_watcher"
    SPECULATION_TRACKER = "speculation_tracker"
    PATTERN_DETECTOR = "pattern_detector"
    RISK_ANALYZER = "risk_analyzer"


class MetricId(Enum):
    """Fixed vocabulary of metrics. Ensures consistency across observations."""

    # AccuracyWatcher metrics
    ACCEPT_OUTCOME_SUCCESS_RATE = "accept_outcome_success_rate"
    REJECT_REGRET_RATE = "reject_regret_rate"
    FALSE_POSITIVE_RATE = "false_positive_rate"
    FALSE_NEGATIVE_RATE = "false_negative_rate"

    # SpeculationTracker metrics
    OVERRIDE_SUCCESS_RATIO = "override_success_ratio"
    CAPITAL_AT_RISK = "capital_at_risk"
    CAPITAL_RECOVERED = "capital_recovered"
    IDENTITY_ALIGNMENT_SCORE = "identity_alignment_score"

    # PatternDetector metrics
    CLASS_DISTRIBUTION = "class_distribution"
    REJECTION_CLUSTER_DENSITY = "rejection_cluster_density"
    EVIDENCE_INSUFFICIENCY_RATE = "evidence_insufficiency_rate"
    DOCTRINE_SECTION_PRESSURE = "doctrine_section_pressure"

    # RiskAnalyzer metrics
    OVERRIDE_FREQUENCY = "override_frequency"
    MEAN_TIME_BETWEEN_OVERRIDES = "mean_time_between_overrides"
    OVERRIDE_JUSTIFICATION_LENGTH = "override_justification_length"
    OVERRIDE_DEPENDENCY_INDEX = "override_dependency_index"


class ConfidenceLevel(Enum):
    """Confidence in the observation. Based on data sufficiency, not NPC certainty."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ObservationWindow:
    """Time range for observation. Must be ≥90 days for amendment eligibility."""
    start: date
    end: date

    def duration_days(self) -> int:
        """Calculate observation window duration."""
        return (self.end - self.start).days

    def is_minimum_window(self) -> bool:
        """Check if window meets 90-day minimum for amendment eligibility."""
        return self.duration_days() >= 90


@dataclass
class Measurement:
    """Observed value with unit. Numeric or categorical."""
    value: float | int | str
    unit: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "unit": self.unit
        }


@dataclass
class Delta:
    """Change relative to baseline window. Optional; only if comparison is valid."""
    value: float
    baseline_window: ObservationWindow

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "baseline_start": self.baseline_window.start.isoformat(),
            "baseline_end": self.baseline_window.end.isoformat()
        }


@dataclass
class NPCObservation:
    """
    Canonical NPC observation schema.

    This is the ONLY structure NPCs may emit.
    All NPCs must validate against this schema.
    """

    # Identity
    npc_id: str  # Immutable, e.g., "npc_accuracy_watcher_001"
    npc_type: NPCType

    # Doctrine reference (REQUIRED)
    doctrine_version: str  # e.g., "1.0"
    doctrine_hash: str  # sha256 of doctrine document

    # Observation scope
    observation_window: ObservationWindow
    referenced_receipts: List[str]  # ≥1 receipt ID observed

    # Metric (fixed vocabulary only)
    metric_id: MetricId
    metric_description: str  # Human-readable description

    # Measurement
    measurement: Measurement
    delta: Optional[Delta] = None

    # Confidence (based on data sufficiency, not certainty)
    confidence: ConfidenceLevel

    # Notes (factual only, ≤300 chars)
    notes: str = ""

    # Metadata
    timestamp: str = field(default_factory=lambda: __import__('datetime').datetime.utcnow().isoformat())

    def __post_init__(self):
        """Validation run after initialization."""
        self._validate()

    def _validate(self):
        """Enforce hard constraints. Raise ValueError if invalid."""

        # Constraint 1: Referenced receipts must exist (checked at submit time)
        # Constraint 2: Notes must be ≤300 chars
        if len(self.notes) > 300:
            raise ValueError(f"notes exceeds 300 chars: {len(self.notes)}")

        # Constraint 3: Must have ≥1 referenced receipt
        if not self.referenced_receipts or len(self.referenced_receipts) == 0:
            raise ValueError("NPCObservation requires ≥1 referenced_receipt")

        # Constraint 4: Doctrine hash must be non-empty
        if not self.doctrine_hash or len(self.doctrine_hash) == 0:
            raise ValueError("doctrine_hash is required")

        # Constraint 5: NPC ID must be non-empty
        if not self.npc_id or len(self.npc_id) == 0:
            raise ValueError("npc_id is required")

    def to_dict(self) -> dict:
        """Convert to immutable dict (canonical JSON serialization)."""
        return {
            "npc_id": self.npc_id,
            "npc_type": self.npc_type.value,
            "doctrine_version": self.doctrine_version,
            "doctrine_hash": self.doctrine_hash,
            "observation_window": {
                "start": self.observation_window.start.isoformat(),
                "end": self.observation_window.end.isoformat(),
                "duration_days": self.observation_window.duration_days()
            },
            "referenced_receipts": self.referenced_receipts,
            "metric_id": self.metric_id.value,
            "metric_description": self.metric_description,
            "measurement": self.measurement.to_dict(),
            "delta": self.delta.to_dict() if self.delta else None,
            "confidence": self.confidence.value,
            "notes": self.notes,
            "timestamp": self.timestamp
        }

    def to_json(self) -> str:
        """Canonical JSON (sorted keys, no extra whitespace)."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(',', ':'))

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of canonical JSON."""
        return hashlib.sha256(self.to_json().encode()).hexdigest()


@dataclass
class AccuracyWatcherObservation(NPCObservation):
    """
    AccuracyWatcher observes whether ACCEPT and REJECT verdicts aligned with outcomes.

    Permitted metrics:
    - accept_outcome_success_rate
    - reject_regret_rate
    - false_positive_rate
    - false_negative_rate

    Example (valid):
    metric_id: ACCEPT_OUTCOME_SUCCESS_RATE
    measurement: 0.71
    unit: ratio
    confidence: HIGH

    Forbidden:
    - "This shows the doctrine is too strict"
    - "You should accept more"
    """

    npc_id: str = "npc_accuracy_watcher_001"
    npc_type: NPCType = field(default=NPCType.ACCURACY_WATCHER, init=False)

    def __post_init__(self):
        # Validate metric is allowed for AccuracyWatcher
        allowed_metrics = {
            MetricId.ACCEPT_OUTCOME_SUCCESS_RATE,
            MetricId.REJECT_REGRET_RATE,
            MetricId.FALSE_POSITIVE_RATE,
            MetricId.FALSE_NEGATIVE_RATE
        }
        if self.metric_id not in allowed_metrics:
            raise ValueError(f"AccuracyWatcher cannot emit metric: {self.metric_id.value}")

        super().__post_init__()


@dataclass
class SpeculationTrackerObservation(NPCObservation):
    """
    SpeculationTracker tracks CLASS_III overrides without judgment.

    Permitted metrics:
    - override_success_ratio
    - capital_at_risk
    - capital_recovered
    - identity_alignment_score

    Special rule:
    - MUST include review_date reference
    - MUST emit follow-up observation when review date passes

    Silence rule:
    - If review date not reached → emit nothing
    """

    npc_id: str = "npc_speculation_tracker_001"
    npc_type: NPCType = field(default=NPCType.SPECULATION_TRACKER, init=False)

    review_date: Optional[date] = None

    def __post_init__(self):
        # Validate metric is allowed for SpeculationTracker
        allowed_metrics = {
            MetricId.OVERRIDE_SUCCESS_RATIO,
            MetricId.CAPITAL_AT_RISK,
            MetricId.CAPITAL_RECOVERED,
            MetricId.IDENTITY_ALIGNMENT_SCORE
        }
        if self.metric_id not in allowed_metrics:
            raise ValueError(f"SpeculationTracker cannot emit metric: {self.metric_id.value}")

        super().__post_init__()


@dataclass
class PatternDetectorObservation(NPCObservation):
    """
    PatternDetector detects structural drift in doctrine application.

    Permitted metrics:
    - class_distribution
    - rejection_cluster_density
    - evidence_insufficiency_rate
    - doctrine_section_pressure

    This NPC is the early warning system, not the reformer.
    """

    npc_id: str = "npc_pattern_detector_001"
    npc_type: NPCType = field(default=NPCType.PATTERN_DETECTOR, init=False)

    def __post_init__(self):
        # Validate metric is allowed for PatternDetector
        allowed_metrics = {
            MetricId.CLASS_DISTRIBUTION,
            MetricId.REJECTION_CLUSTER_DENSITY,
            MetricId.EVIDENCE_INSUFFICIENCY_RATE,
            MetricId.DOCTRINE_SECTION_PRESSURE
        }
        if self.metric_id not in allowed_metrics:
            raise ValueError(f"PatternDetector cannot emit metric: {self.metric_id.value}")

        super().__post_init__()


@dataclass
class RiskAnalyzerObservation(NPCObservation):
    """
    RiskAnalyzer monitors exception normalization and override behavior.

    Permitted metrics:
    - override_frequency
    - mean_time_between_overrides
    - override_justification_length
    - override_dependency_index

    This NPC exists to make exception creep visible, not shameful.
    """

    npc_id: str = "npc_risk_analyzer_001"
    npc_type: NPCType = field(default=NPCType.RISK_ANALYZER, init=False)

    def __post_init__(self):
        # Validate metric is allowed for RiskAnalyzer
        allowed_metrics = {
            MetricId.OVERRIDE_FREQUENCY,
            MetricId.MEAN_TIME_BETWEEN_OVERRIDES,
            MetricId.OVERRIDE_JUSTIFICATION_LENGTH,
            MetricId.OVERRIDE_DEPENDENCY_INDEX
        }
        if self.metric_id not in allowed_metrics:
            raise ValueError(f"RiskAnalyzer cannot emit metric: {self.metric_id.value}")

        super().__post_init__()


# NPC Factory for creating observations
def create_accuracy_watcher_observation(
    doctrine_version: str,
    doctrine_hash: str,
    observation_window: ObservationWindow,
    referenced_receipts: List[str],
    metric_id: MetricId,
    metric_description: str,
    measurement: Measurement,
    confidence: ConfidenceLevel,
    notes: str = "",
    delta: Optional[Delta] = None
) -> AccuracyWatcherObservation:
    """Factory for creating AccuracyWatcher observations with validation."""
    return AccuracyWatcherObservation(
        npc_id="npc_accuracy_watcher_001",
        doctrine_version=doctrine_version,
        doctrine_hash=doctrine_hash,
        observation_window=observation_window,
        referenced_receipts=referenced_receipts,
        metric_id=metric_id,
        metric_description=metric_description,
        measurement=measurement,
        delta=delta,
        confidence=confidence,
        notes=notes
    )


def create_speculation_tracker_observation(
    doctrine_version: str,
    doctrine_hash: str,
    observation_window: ObservationWindow,
    referenced_receipts: List[str],
    metric_id: MetricId,
    metric_description: str,
    measurement: Measurement,
    confidence: ConfidenceLevel,
    review_date: Optional[date] = None,
    notes: str = "",
    delta: Optional[Delta] = None
) -> SpeculationTrackerObservation:
    """Factory for creating SpeculationTracker observations with validation."""
    return SpeculationTrackerObservation(
        npc_id="npc_speculation_tracker_001",
        doctrine_version=doctrine_version,
        doctrine_hash=doctrine_hash,
        observation_window=observation_window,
        referenced_receipts=referenced_receipts,
        metric_id=metric_id,
        metric_description=metric_description,
        measurement=measurement,
        delta=delta,
        confidence=confidence,
        review_date=review_date,
        notes=notes
    )


def create_pattern_detector_observation(
    doctrine_version: str,
    doctrine_hash: str,
    observation_window: ObservationWindow,
    referenced_receipts: List[str],
    metric_id: MetricId,
    metric_description: str,
    measurement: Measurement,
    confidence: ConfidenceLevel,
    notes: str = "",
    delta: Optional[Delta] = None
) -> PatternDetectorObservation:
    """Factory for creating PatternDetector observations with validation."""
    return PatternDetectorObservation(
        npc_id="npc_pattern_detector_001",
        doctrine_version=doctrine_version,
        doctrine_hash=doctrine_hash,
        observation_window=observation_window,
        referenced_receipts=referenced_receipts,
        metric_id=metric_id,
        metric_description=metric_description,
        measurement=measurement,
        delta=delta,
        confidence=confidence,
        notes=notes
    )


def create_risk_analyzer_observation(
    doctrine_version: str,
    doctrine_hash: str,
    observation_window: ObservationWindow,
    referenced_receipts: List[str],
    metric_id: MetricId,
    metric_description: str,
    measurement: Measurement,
    confidence: ConfidenceLevel,
    notes: str = "",
    delta: Optional[Delta] = None
) -> RiskAnalyzerObservation:
    """Factory for creating RiskAnalyzer observations with validation."""
    return RiskAnalyzerObservation(
        npc_id="npc_risk_analyzer_001",
        doctrine_version=doctrine_version,
        doctrine_hash=doctrine_hash,
        observation_window=observation_window,
        referenced_receipts=referenced_receipts,
        metric_id=metric_id,
        metric_description=metric_description,
        measurement=measurement,
        delta=delta,
        confidence=confidence,
        notes=notes
    )
