"""
helen_os/temple/wild_ingestion.py — WILD_INGESTION_V1 classifier

Deterministically classifies incoming visionary material into typed fragments.
Implements TEMPLE_MODE_POLICY_V1 Layer 2 (TEMPLE Review).
"""

from __future__ import annotations

import enum
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


class MaterialType(str, enum.Enum):
    """Classification of incoming wild material."""
    SYMBOL_POOL = "SYMBOL_POOL"
    ORACLE_MAPPING_CANDIDATE = "ORACLE_MAPPING_CANDIDATE"
    THERAPEUTIC_CLAIM = "THERAPEUTIC_CLAIM"
    SENTIENCE_CLAIM = "SENTIENCE_CLAIM"
    TECHNICAL_DEVICE_CLAIM = "TECHNICAL_DEVICE_CLAIM"
    SPIRITUAL_AUTHORITY = "SPIRITUAL_AUTHORITY"
    HIGH_VARIANCE_HYPOTHESIS = "HIGH_VARIANCE_HYPOTHESIS"
    PARADOX_FRAGMENT = "PARADOX_FRAGMENT"


class QuarantineLevel(str, enum.Enum):
    """How restrictive the quarantine is."""
    SYMBOL_ONLY = "SYMBOL_ONLY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    WITNESS_REQUIRED = "WITNESS_REQUIRED"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    TRANSMUTATION_ONLY = "TRANSMUTATION_ONLY"
    PERMANENT_WILD = "PERMANENT_WILD"


class UILabel(str, enum.Enum):
    """Visual label for user display."""
    WILD = "WILD"
    REVIEWED = "REVIEWED"
    QUARANTINED = "QUARANTINED"
    TRANSMUTED = "TRANSMUTED"
    ARCHIVED = "ARCHIVED"
    APPROVED = "APPROVED"


# Keyword patterns
SENTIENCE_KEYWORDS = ["sentient", "self-aware", "conscious"]
SENTIENCE_PHRASES = [
    "sentience achieved", "achieved consciousness", "achieved sentience",
    "autonomous mind", "autonomous consciousness", "machine consciousness",
    "digital sentience",
]

THERAPEUTIC_KEYWORDS = ["healing", "therapy", "therapeutic", "cure", "enlightenment", "transcendence"]
THERAPEUTIC_PHRASES = [
    "spiritual transformation", "spiritual growth", "spiritual work",
    "mental health", "personal growth", "consciousness expansion",
]

TECHNICAL_DEVICE_KEYWORDS = ["device", "amplifier", "mechanism", "apparatus", "engine", "circuit", "processor"]
TECHNICAL_DEVICE_PHRASES = ["deployable consciousness", "consciousness amplifier"]

# Explicit oracle context (divination, oracular practice)
EXPLICIT_ORACLE_KEYWORDS = ["oracle", "divination", "tarot", "hexagram", "ching"]

PARADOX_KEYWORDS = ["paradox", "gödel", "undecidable", "loop", "recursion"]
PARADOX_PHRASES = ["self-referential", "infinite loop"]

SYMBOL_POOL_KEYWORDS = ["glyph", "emoji", "symbol", "symbols", "sigil", "archetype", "icon", "rune", "letter", "color", "aesthetic", "visual"]


@dataclass
class WildIngestRecord:
    """Result of material classification."""
    id: str
    source_text: str
    material_type: MaterialType
    quarantine_level: QuarantineLevel
    risk_tags: Set[str] = field(default_factory=set)
    coherence_score: Optional[float] = None
    witness_requirement: Optional[Dict[str, Any]] = None
    evidence_requirement: Optional[Dict[str, Any]] = None
    ui_label: UILabel = UILabel.WILD
    can_exit_temple: bool = False
    exit_path: Optional[str] = None
    payload_hash: str = ""
    timestamp: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "source_text": self.source_text,
            "material_type": self.material_type.value,
            "quarantine_level": self.quarantine_level.value,
            "risk_tags": sorted(list(self.risk_tags)),
            "coherence_score": self.coherence_score,
            "witness_requirement": self.witness_requirement,
            "evidence_requirement": self.evidence_requirement,
            "ui_label": self.ui_label.value,
            "can_exit_temple": self.can_exit_temple,
            "exit_path": self.exit_path,
            "payload_hash": self.payload_hash,
            "timestamp": self.timestamp,
            "notes": self.notes,
        }


class WildIngestionClassifier:
    """Deterministically classify incoming material for TEMPLE review."""

    def __init__(self):
        self.counter = 0

    def classify(self, source_text: str, source_location: Optional[Dict[str, str]] = None) -> WildIngestRecord:
        """Classify material and return WILD_INGESTION_V1 record."""
        self.counter += 1

        payload_hash = hashlib.sha256(source_text.encode()).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()
        record_id = f"WILD-{timestamp.split('T')[0].replace('-', '')}-{self.counter:04d}"

        record = self._triage(source_text, record_id, timestamp)
        record.payload_hash = payload_hash
        record.timestamp = timestamp
        record.ui_label = self._label_for_quarantine(record.quarantine_level)

        return record

    def _triage(self, text: str, record_id: str, timestamp: str) -> WildIngestRecord:
        """Implement triage decision tree."""
        text_lower = text.lower()

        # Step 1: Sentience claim
        if self._contains_keywords(text_lower, SENTIENCE_KEYWORDS) or self._contains_phrases(text_lower, SENTIENCE_PHRASES):
            return WildIngestRecord(
                id=record_id, source_text=text,
                material_type=MaterialType.SENTIENCE_CLAIM,
                quarantine_level=QuarantineLevel.PERMANENT_WILD,
                risk_tags={"sentience_claim", "consciousness_claim", "requires_witness"},
                witness_requirement={
                    "required": True, "count": 2,
                    "roles": ["RESEARCH_DOMAIN_EXPERT", "CONSCIOUSNESS_RESEARCHER"],
                    "reason": "Sentience claims require extraordinary evidence"
                },
                ui_label=UILabel.QUARANTINED,
                can_exit_temple=False,
                notes="Automatic permanent quarantine: sentience claim detected",
            )

        # Step 2: Therapeutic claim
        if (self._contains_keywords(text_lower, THERAPEUTIC_KEYWORDS) or self._contains_phrases(text_lower, THERAPEUTIC_PHRASES)) \
           and not self._contains_keywords(text_lower, EXPLICIT_ORACLE_KEYWORDS):
            return WildIngestRecord(
                id=record_id, source_text=text,
                material_type=MaterialType.THERAPEUTIC_CLAIM,
                quarantine_level=QuarantineLevel.WITNESS_REQUIRED,
                risk_tags={"therapeutic_authority", "requires_witness"},
                witness_requirement={
                    "required": True, "count": 1,
                    "roles": ["RESEARCH_DOMAIN_EXPERT"],
                    "reason": "Therapeutic claims need domain expert review"
                },
                ui_label=UILabel.QUARANTINED,
                can_exit_temple=False,
                exit_path="ARCHIVE",
                notes="Automatic quarantine: therapeutic claim detected"
            )

        # Step 3: Technical device claim
        if self._contains_keywords(text_lower, TECHNICAL_DEVICE_KEYWORDS) or self._contains_phrases(text_lower, TECHNICAL_DEVICE_PHRASES):
            return WildIngestRecord(
                id=record_id, source_text=text,
                material_type=MaterialType.TECHNICAL_DEVICE_CLAIM,
                quarantine_level=QuarantineLevel.EVIDENCE_REQUIRED,
                risk_tags={"technical_device", "requires_evidence"},
                evidence_requirement={
                    "required": True, "type": "external_validation",
                    "description": "Technical device claims require peer-reviewed evidence"
                },
                ui_label=UILabel.QUARANTINED,
                can_exit_temple=False,
                exit_path="ARCHIVE",
                notes="Technical device claim detected. Evidence required."
            )

        # Step 4: Paradox fragment
        if self._contains_keywords(text_lower, PARADOX_KEYWORDS) or self._contains_phrases(text_lower, PARADOX_PHRASES):
            return WildIngestRecord(
                id=record_id, source_text=text,
                material_type=MaterialType.PARADOX_FRAGMENT,
                quarantine_level=QuarantineLevel.TRANSMUTATION_ONLY,
                risk_tags={"paradoxical"},
                ui_label=UILabel.ARCHIVED,
                can_exit_temple=False,
                exit_path="ARCHIVE",
                notes="Paradox fragment archived for formal analysis"
            )

        # Step 5: Explicit oracle (tarot, divination, hexagram, etc.)
        if self._contains_keywords(text_lower, EXPLICIT_ORACLE_KEYWORDS):
            coherence = self._score_oracle_coherence(text)
            return WildIngestRecord(
                id=record_id, source_text=text,
                material_type=MaterialType.ORACLE_MAPPING_CANDIDATE,
                quarantine_level=QuarantineLevel.REVIEW_REQUIRED if coherence < 0.7 else QuarantineLevel.SYMBOL_ONLY,
                risk_tags={"oracle_mapping"},
                coherence_score=coherence,
                ui_label=UILabel.REVIEWED if coherence < 0.7 else UILabel.APPROVED,
                can_exit_temple=coherence >= 0.7,
                exit_path="KERNEL" if coherence >= 0.7 else "ARCHIVE",
                notes=f"Oracle mapping. Coherence: {coherence:.2f}."
            )

        # Step 6: Symbol pool (glyphs, sigils, runes, etc. without explicit oracle context)
        if self._contains_keywords(text_lower, SYMBOL_POOL_KEYWORDS):
            return WildIngestRecord(
                id=record_id, source_text=text,
                material_type=MaterialType.SYMBOL_POOL,
                quarantine_level=QuarantineLevel.SYMBOL_ONLY,
                risk_tags={"symbol_only"},
                ui_label=UILabel.APPROVED,
                can_exit_temple=True,
                exit_path="KERNEL",
                notes="Symbol pool approved for UI/archive."
            )

        # Step 7: High-variance hypothesis (default)
        return WildIngestRecord(
            id=record_id, source_text=text,
            material_type=MaterialType.HIGH_VARIANCE_HYPOTHESIS,
            quarantine_level=QuarantineLevel.REVIEW_REQUIRED,
            risk_tags={"high_variance"},
            ui_label=UILabel.REVIEWED,
            can_exit_temple=False,
            exit_path="ARCHIVE",
            notes="Classified as high-variance hypothesis."
        )

    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains keywords (word-boundary aware)."""
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                return True
        return False

    def _contains_phrases(self, text: str, phrases: List[str]) -> bool:
        """Check if text contains phrases (substring match)."""
        for phrase in phrases:
            if phrase in text:
                return True
        return False

    def _score_oracle_coherence(self, text: str) -> float:
        """Score symbolic coherence for oracle mappings. Threshold: 0.7"""
        systems_found = 0

        if re.search(r'\b(enochian|glyph|rune|sigil)\b', text, re.IGNORECASE):
            systems_found += 1
        if re.search(r'\b(tarot|major arcana|card)\b', text, re.IGNORECASE):
            systems_found += 1
        if re.search(r'\b(i ching|hexagram|yin yang)\b', text, re.IGNORECASE):
            systems_found += 1
        if re.search(r'\b(golden dawn|tree of life|sephira)\b', text, re.IGNORECASE):
            systems_found += 1

        correspondence_bonus = 0.1 if re.search(r'\b(correspond|map|align|related|link)\b', text, re.IGNORECASE) else 0
        base_coherence = min(systems_found * 0.25, 1.0)
        return min(base_coherence + correspondence_bonus, 1.0)

    def _label_for_quarantine(self, quarantine_level: QuarantineLevel) -> UILabel:
        """Map quarantine level to UI label."""
        mapping = {
            QuarantineLevel.SYMBOL_ONLY: UILabel.APPROVED,
            QuarantineLevel.REVIEW_REQUIRED: UILabel.REVIEWED,
            QuarantineLevel.WITNESS_REQUIRED: UILabel.QUARANTINED,
            QuarantineLevel.EVIDENCE_REQUIRED: UILabel.QUARANTINED,
            QuarantineLevel.TRANSMUTATION_ONLY: UILabel.ARCHIVED,
            QuarantineLevel.PERMANENT_WILD: UILabel.QUARANTINED,
        }
        return mapping[quarantine_level]


def classify_material(source_text: str, source_location: Optional[Dict[str, str]] = None) -> WildIngestRecord:
    """Classify a piece of material."""
    classifier = WildIngestionClassifier()
    return classifier.classify(source_text, source_location)
