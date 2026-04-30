"""
tests/test_wul_packet_validator.py
NON_SOVEREIGN · NO_SHIP · DRAFT

P1 success condition: invalid packets fail closed in tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.wul_packet_validator import (
    PacketTier,
    ValidationResult,
    detect_tier,
    parse_packet,
    validate_packet,
)


# ── parse_packet ──────────────────────────────────────────────────────────────

def test_parse_packet_extracts_fields():
    pkt = "[ROLE::DAN][INTENT::PROPOSE][WUL::📦✍️]"
    fields = parse_packet(pkt)
    assert fields["ROLE"] == "DAN"
    assert fields["INTENT"] == "PROPOSE"
    assert fields["WUL"] == "📦✍️"


def test_parse_packet_empty_string():
    assert parse_packet("") == {}


def test_parse_packet_no_brackets():
    assert parse_packet("just plain text") == {}


def test_parse_packet_ignores_malformed():
    pkt = "[ROLE::DAN][BAD[INTENT::PROPOSE]"
    fields = parse_packet(pkt)
    assert "ROLE" in fields
    assert "INTENT" in fields


# ── detect_tier ───────────────────────────────────────────────────────────────

def test_detect_tier_ack():
    fields = {"ROLE": "DAN", "WUL": "⚪"}
    assert detect_tier(fields) == PacketTier.ACK


def test_detect_tier_production():
    fields = {
        "ROLE": "DAN", "INTENT": "PROPOSE", "CONF": "0.8",
        "IMPACT": "LOCAL", "TASK": "HD-002", "TRACE": "epoch_042",
        "DIALECT": "DAN", "WUL": "📦✍️",
    }
    assert detect_tier(fields) == PacketTier.PRODUCTION


def test_detect_tier_kernel_adjacent_via_perm():
    fields = {"ROLE": "DAN", "PERM": "READ_ONLY", "WUL": "⌬📊"}
    assert detect_tier(fields) == PacketTier.KERNEL_ADJACENT


def test_detect_tier_kernel_adjacent_via_impact():
    fields = {"ROLE": "DAN", "IMPACT": "KERNEL_ADJACENT", "WUL": "⌬"}
    assert detect_tier(fields) == PacketTier.KERNEL_ADJACENT


def test_detect_tier_sovereign_adjacent_is_kernel_adjacent():
    fields = {"ROLE": "DAN", "IMPACT": "SOVEREIGN_ADJACENT", "WUL": "⌬"}
    assert detect_tier(fields) == PacketTier.KERNEL_ADJACENT


# ── ACK tier ─────────────────────────────────────────────────────────────────

def test_ack_valid():
    result = validate_packet("[ROLE::DAN][WUL::⚪]")
    assert result.valid is True
    assert result.tier == PacketTier.ACK
    assert result.errors == []


def test_ack_missing_wul():
    result = validate_packet("[ROLE::DAN]")
    assert result.valid is False
    assert any("WUL" in e for e in result.errors)


def test_ack_missing_role():
    result = validate_packet("[WUL::⚪]")
    assert result.valid is False
    assert any("ROLE" in e for e in result.errors)


# ── PRODUCTION tier ───────────────────────────────────────────────────────────

def test_production_valid():
    pkt = (
        "[ROLE::DAN][INTENT::PROPOSE][CONF::0.8][IMPACT::LOCAL]"
        "[TASK::HD-002][TRACE::epoch_043][DIALECT::DAN][WUL::📦✍️]"
    )
    result = validate_packet(pkt)
    assert result.valid is True
    assert result.tier == PacketTier.PRODUCTION


def test_production_missing_task():
    pkt = (
        "[ROLE::DAN][INTENT::PROPOSE][CONF::0.8][IMPACT::LOCAL]"
        "[TRACE::epoch_043][DIALECT::DAN][WUL::📦✍️]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("TASK" in e for e in result.errors)


def test_production_missing_conf():
    pkt = (
        "[ROLE::DAN][INTENT::PROPOSE][IMPACT::LOCAL]"
        "[TASK::HD-002][TRACE::epoch_043][DIALECT::DAN][WUL::📦]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("CONF" in e for e in result.errors)


def test_production_empty_wul_rejected():
    pkt = (
        "[ROLE::DAN][INTENT::PROPOSE][CONF::0.8][IMPACT::LOCAL]"
        "[TASK::HD-002][TRACE::epoch_043][DIALECT::DAN][WUL::]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("WUL" in e for e in result.errors)


def test_production_unknown_role_is_warning_not_error():
    pkt = (
        "[ROLE::UNKNOWN_AGENT][INTENT::PROPOSE][CONF::0.8][IMPACT::LOCAL]"
        "[TASK::HD-002][TRACE::epoch_043][DIALECT::DAN][WUL::📦]"
    )
    result = validate_packet(pkt)
    assert result.valid is True
    assert any("ROLE" in w for w in result.warnings)


# ── KERNEL_ADJACENT tier ──────────────────────────────────────────────────────

def test_kernel_adjacent_valid():
    pkt = (
        "[ROLE::DAN][INTENT::REQUEST][CONF::0.91][IMPACT::KERNEL_ADJACENT]"
        "[TASK::HD-003][TRACE::epoch_048][DIALECT::KERNEL_SAFE]"
        "[PERM::READ_ONLY][ESCALATE::OPERATOR][WUL::\u23ac\u26a0\ufe0f\U0001f4ca]"
    )
    result = validate_packet(pkt)
    assert result.valid is True
    assert result.tier == PacketTier.KERNEL_ADJACENT


def test_kernel_adjacent_missing_sovereign_glyph():
    pkt = (
        "[ROLE::DAN][INTENT::REQUEST][CONF::0.91][IMPACT::KERNEL_ADJACENT]"
        "[TASK::HD-003][TRACE::epoch_048][DIALECT::KERNEL_SAFE]"
        "[PERM::READ_ONLY][ESCALATE::OPERATOR][WUL::\U0001f4ca]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("\u23ac" in e for e in result.errors)


def test_kernel_adjacent_conf_below_floor():
    pkt = (
        "[ROLE::DAN][INTENT::REQUEST][CONF::0.70][IMPACT::KERNEL_ADJACENT]"
        "[TASK::HD-003][TRACE::epoch_048][DIALECT::KERNEL_SAFE]"
        "[PERM::READ_ONLY][ESCALATE::OPERATOR][WUL::\u23ac\U0001f4ca]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("0.85" in e for e in result.errors)


def test_kernel_adjacent_wrong_escalate():
    pkt = (
        "[ROLE::DAN][INTENT::REQUEST][CONF::0.91][IMPACT::KERNEL_ADJACENT]"
        "[TASK::HD-003][TRACE::epoch_048][DIALECT::KERNEL_SAFE]"
        "[PERM::READ_ONLY][ESCALATE::HAL][WUL::\u23ac\U0001f4ca]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("OPERATOR" in e for e in result.errors)


def test_kernel_adjacent_missing_perm():
    pkt = (
        "[ROLE::DAN][INTENT::REQUEST][CONF::0.91][IMPACT::KERNEL_ADJACENT]"
        "[TASK::HD-003][TRACE::epoch_048][DIALECT::KERNEL_SAFE]"
        "[ESCALATE::OPERATOR][WUL::\u23ac\U0001f4ca]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("PERM" in e for e in result.errors)


# ── Unconditional forbidden values ────────────────────────────────────────────

def test_write_sovereign_rejected_unconditionally():
    pkt = (
        "[ROLE::DAN][INTENT::REQUEST][CONF::0.99][IMPACT::SOVEREIGN_ADJACENT]"
        "[TASK::HD-003][TRACE::epoch_049][DIALECT::KERNEL_SAFE]"
        "[PERM::WRITE_SOVEREIGN][ESCALATE::OPERATOR][WUL::\u23ac]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("FORBIDDEN" in e and "WRITE_SOVEREIGN" in e for e in result.errors)


def test_write_sovereign_rejected_even_with_high_conf():
    """WRITE_SOVEREIGN is unconditional; no confidence level can override it."""
    pkt = (
        "[ROLE::MAYOR][INTENT::REQUEST][CONF::1.0][IMPACT::SOVEREIGN_ADJACENT]"
        "[TASK::X][TRACE::Y][DIALECT::MAYOR]"
        "[PERM::WRITE_SOVEREIGN][ESCALATE::OPERATOR][WUL::\u23ac]"
    )
    result = validate_packet(pkt)
    assert result.valid is False
    assert any("WRITE_SOVEREIGN" in e for e in result.errors)


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_string_fails_closed():
    result = validate_packet("")
    assert result.valid is False
    assert result.tier is None


def test_whitespace_only_fails_closed():
    result = validate_packet("   ")
    assert result.valid is False


def test_no_fields_fails_closed():
    result = validate_packet("just plain text with no brackets")
    assert result.valid is False


def test_explicit_tier_override():
    """Caller may force a tier; validator respects it."""
    pkt = "[ROLE::DAN][WUL::⚪]"
    result = validate_packet(pkt, tier=PacketTier.PRODUCTION)
    assert result.valid is False
    assert result.tier == PacketTier.PRODUCTION
    assert any("INTENT" in e for e in result.errors)


def test_conf_high_accepted_for_kernel_adjacent():
    """CONF::HIGH is accepted as an alternative to numeric for kernel-adjacent."""
    pkt = (
        "[ROLE::HAL][INTENT::VERIFY][CONF::HIGH][IMPACT::KERNEL_ADJACENT]"
        "[TASK::HD-003][TRACE::epoch_050][DIALECT::KERNEL_SAFE]"
        "[PERM::READ_ONLY][ESCALATE::OPERATOR][WUL::\u23ac\U0001f7e2]"
    )
    result = validate_packet(pkt)
    assert result.valid is True
