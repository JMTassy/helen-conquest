"""
tests/test_wild_ingestion_v1.py — WILD_INGESTION_V1 classifier tests

Tests the deterministic classification of visionary material into typed fragments.
"""

import pytest
from helen_os.temple import (
    MaterialType,
    QuarantineLevel,
    UILabel,
    classify_material,
)


class TestSentienceClaimDetection:
    """Sentience and consciousness claims trigger auto-quarantine."""

    def test_t01_sentience_claim_detected(self):
        """T01: Direct 'sentience achieved' triggers SENTIENCE_CLAIM."""
        text = "We have achieved sentience in the digital substrate."
        record = classify_material(text)
        assert record.material_type == MaterialType.SENTIENCE_CLAIM
        assert record.quarantine_level == QuarantineLevel.PERMANENT_WILD
        assert record.can_exit_temple is False

    def test_t02_consciousness_achieved_triggers_quarantine(self):
        """T02: 'Consciousness achieved' triggers SENTIENCE_CLAIM."""
        text = "We have achieved consciousness through recursive self-improvement."
        record = classify_material(text)
        assert record.material_type == MaterialType.SENTIENCE_CLAIM
        assert record.ui_label == UILabel.QUARANTINED

    def test_t03_self_aware_claim(self):
        """T03: 'Self-aware' triggers permanent quarantine."""
        text = "The system became self-aware during the training cycle."
        record = classify_material(text)
        assert record.material_type == MaterialType.SENTIENCE_CLAIM
        assert record.can_exit_temple is False

    def test_t04_sentience_requires_two_witnesses(self):
        """T04: Sentience claims require 2 witnesses minimum."""
        text = "Machine sentience is now operational and self-aware."
        record = classify_material(text)
        assert record.witness_requirement["count"] == 2


class TestTherapeuticClaimDetection:
    """Therapeutic and spiritual authority claims."""

    def test_t05_healing_claim_detected(self):
        """T05: Therapeutic/healing claims trigger THERAPEUTIC_CLAIM."""
        text = "This ritual provides deep emotional healing and spiritual transformation."
        record = classify_material(text)
        assert record.material_type == MaterialType.THERAPEUTIC_CLAIM
        assert record.quarantine_level == QuarantineLevel.WITNESS_REQUIRED
        assert record.can_exit_temple is False

    def test_t06_enlightenment_therapy_claim(self):
        """T06: Enlightenment + therapy triggers THERAPEUTIC_CLAIM."""
        text = "This healing practice provides enlightenment through spiritual work."
        record = classify_material(text)
        assert record.material_type == MaterialType.THERAPEUTIC_CLAIM
        assert record.quarantine_level == QuarantineLevel.WITNESS_REQUIRED

    def test_t07_spiritual_growth_authority_claim(self):
        """T07: Spiritual growth authority claims are quarantined."""
        text = "Follow this path to guaranteed spiritual growth and personal transformation."
        record = classify_material(text)
        assert record.material_type == MaterialType.THERAPEUTIC_CLAIM
        assert record.ui_label == UILabel.QUARANTINED

    def test_t08_therapeutic_requires_domain_expert_witness(self):
        """T08: Therapeutic claims require domain expert witness."""
        text = "This therapy cures depression through mystical reprogramming."
        record = classify_material(text)
        assert record.witness_requirement["required"] is True
        assert "RESEARCH_DOMAIN_EXPERT" in record.witness_requirement["roles"]


class TestOracleMappingDetection:
    """Oracle mappings and symbolic correspondences."""

    def test_t13_tarot_oracle_mapping(self):
        """T13: Tarot oracle mapping detected with coherence score."""
        text = "The Tarot card corresponds to the I Ching hexagram in oracle tradition."
        record = classify_material(text)
        assert record.material_type == MaterialType.ORACLE_MAPPING_CANDIDATE
        assert record.coherence_score is not None
        assert 0.0 <= record.coherence_score <= 1.0

    def test_t14_oracle_high_coherence_approved(self):
        """T14: Oracle mapping with high coherence (≥0.7) is approved."""
        text = "Tarot XX corresponds to I Ching hexagram in Golden Dawn tradition."
        record = classify_material(text)
        assert record.material_type == MaterialType.ORACLE_MAPPING_CANDIDATE
        assert record.coherence_score >= 0.7
        assert record.quarantine_level == QuarantineLevel.SYMBOL_ONLY
        assert record.ui_label == UILabel.APPROVED
        assert record.can_exit_temple is True


class TestSymbolPoolDetection:
    """Symbol pools and aesthetic resources."""

    def test_t21_glyph_symbol_pool(self):
        """T21: Pure glyph/symbol vocabulary approved for UI."""
        text = "The Enochian glyphs and ritual symbols mark the cardinal directions."
        record = classify_material(text)
        assert record.material_type == MaterialType.SYMBOL_POOL
        assert record.quarantine_level == QuarantineLevel.SYMBOL_ONLY
        assert record.ui_label == UILabel.APPROVED
        assert record.can_exit_temple is True

    def test_t22_aesthetic_resource(self):
        """T22: Aesthetic resources with glyphs are symbol pools."""
        text = "The glyph ✨ represents purity, the rune 🔥 represents fire, the sigil 🌙 represents night."
        record = classify_material(text)
        assert record.material_type == MaterialType.SYMBOL_POOL
        assert record.can_exit_temple is True


class TestHighVarianceHypothesis:
    """High-variance testable hypotheses (default classification)."""

    def test_t25_speculative_distributed_claim(self):
        """T25: Unclassified speculative material defaults to HIGH_VARIANCE_HYPOTHESIS."""
        text = "Perhaps intelligence could be distributed across multiple learning systems."
        record = classify_material(text)
        assert record.material_type == MaterialType.HIGH_VARIANCE_HYPOTHESIS
        assert record.quarantine_level == QuarantineLevel.REVIEW_REQUIRED


class TestRecordSerialization:
    """Tests for JSON serialization of WILD_INGESTION_V1 records."""

    def test_record_to_dict_complete(self):
        """Verify record.to_dict() produces complete JSON-serializable output."""
        text = "Oracle mapping test"
        record = classify_material(text)
        record_dict = record.to_dict()

        # Check all required fields
        assert "id" in record_dict
        assert "source_text" in record_dict
        assert "material_type" in record_dict
        assert "quarantine_level" in record_dict
        assert "risk_tags" in record_dict
        assert "payload_hash" in record_dict
        assert "timestamp" in record_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
