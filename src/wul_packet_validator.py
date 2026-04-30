"""
wul_packet_validator.py — compile-time WUL packet validator
NON_SOVEREIGN · NO_SHIP · DRAFT
authority: NONE · mutation_rights: NONE · ledger_effect: NONE

Validates symbolic WUL packets before any action layer sees them.
Fails closed: any validation error returns valid=False.

Safe boundary:
- reads packet strings only
- writes nothing to disk
- does not call helen_say.py
- does not touch kernel, ledger, or canon
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PacketTier(Enum):
    ACK = "ACK"
    PRODUCTION = "PRODUCTION"
    KERNEL_ADJACENT = "KERNEL_ADJACENT"


TIER_REQUIRED: dict[PacketTier, set[str]] = {
    PacketTier.ACK: {"ROLE", "WUL"},
    PacketTier.PRODUCTION: {
        "ROLE", "INTENT", "CONF", "IMPACT", "TASK", "TRACE", "DIALECT", "WUL"
    },
    PacketTier.KERNEL_ADJACENT: {
        "ROLE", "INTENT", "CONF", "IMPACT", "TASK", "TRACE",
        "DIALECT", "PERM", "ESCALATE", "WUL"
    },
}

# Unconditional rejections regardless of tier
FORBIDDEN_VALUES: dict[str, set[str]] = {
    "PERM": {"WRITE_SOVEREIGN"},
}

KERNEL_ADJACENT_REQUIRED_GLYPH = "\u23ac"   # ⌬
KERNEL_ADJACENT_REQUIRED_ESCALATE = "OPERATOR"
KERNEL_ADJACENT_CONF_FLOOR = 0.85

VALID_ROLES = {
    "AURA", "HER", "DAN", "HAL", "MAYOR", "TEMPLE", "OPERATOR",
}
VALID_INTENTS = {
    "INFORM", "PROPOSE", "REQUEST", "VERIFY", "HANDOFF",
    "ESCALATE", "ARCHIVE", "REJECT", "ACK", "EXPLORE",
}
VALID_IMPACTS = {
    "LOCAL", "MULTI_AGENT", "KERNEL_ADJACENT", "SOVEREIGN_ADJACENT",
}
VALID_DIALECTS = {
    "TEMPLE", "MAYOR", "HAL", "DAN", "KERNEL_SAFE", "CROWD", "UNDERWARREN_SAFE",
}

_FIELD_RE = re.compile(r"\[([A-Z_]+)::([^\]]*)\]")


@dataclass
class ValidationResult:
    valid: bool
    tier: Optional[PacketTier]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_packet(packet_str: str) -> dict[str, str]:
    """Extract all [KEY::VALUE] pairs from a WUL packet string."""
    return {k: v for k, v in _FIELD_RE.findall(packet_str)}


def detect_tier(fields: dict[str, str]) -> PacketTier:
    """
    Infer tier from fields present.
    KERNEL_ADJACENT if PERM present or IMPACT is kernel/sovereign-adjacent.
    ACK if ≤2 fields and no INTENT.
    PRODUCTION otherwise.
    """
    if "PERM" in fields or fields.get("IMPACT") in {
        "KERNEL_ADJACENT", "SOVEREIGN_ADJACENT"
    }:
        return PacketTier.KERNEL_ADJACENT
    if len(fields) <= 2 and "INTENT" not in fields:
        return PacketTier.ACK
    return PacketTier.PRODUCTION


def validate_packet(
    packet_str: str,
    tier: Optional[PacketTier] = None,
) -> ValidationResult:
    """
    Validate a WUL packet string.

    Returns ValidationResult with valid=False if any rule fails.
    Fails closed: caller must not proceed on invalid result.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not packet_str or not packet_str.strip():
        return ValidationResult(valid=False, tier=None, errors=["Empty packet"])

    fields = parse_packet(packet_str)

    if not fields:
        return ValidationResult(
            valid=False, tier=None,
            errors=["No valid [KEY::VALUE] fields found in packet"],
        )

    detected_tier = tier if tier is not None else detect_tier(fields)
    required = TIER_REQUIRED[detected_tier]

    # 1. Required fields
    missing = required - set(fields)
    if missing:
        errors.append(
            f"Missing required fields for {detected_tier.value}: {sorted(missing)}"
        )

    # 2. Unconditional forbidden values
    for fld, forbidden in FORBIDDEN_VALUES.items():
        if fld in fields and fields[fld] in forbidden:
            errors.append(
                f"FORBIDDEN: [{fld}::{fields[fld]}] is unconditionally rejected"
            )

    # 3. WUL must be non-empty
    if "WUL" in fields and not fields["WUL"].strip():
        errors.append("WUL field must not be empty")

    # 4. Enum warnings (unknown values are warnings, not errors, for forward-compat)
    if "ROLE" in fields and fields["ROLE"] not in VALID_ROLES:
        warnings.append(f"Unknown ROLE '{fields['ROLE']}' — not in canonical set")
    if "INTENT" in fields and fields["INTENT"] not in VALID_INTENTS:
        warnings.append(f"Unknown INTENT '{fields['INTENT']}' — not in canonical enum")
    if "IMPACT" in fields and fields["IMPACT"] not in VALID_IMPACTS:
        warnings.append(f"Unknown IMPACT '{fields['IMPACT']}'")
    if "DIALECT" in fields and fields["DIALECT"] not in VALID_DIALECTS:
        warnings.append(f"Unknown DIALECT '{fields['DIALECT']}'")

    # 5. KERNEL_ADJACENT-specific rules
    if detected_tier == PacketTier.KERNEL_ADJACENT:
        # Confidence floor
        if "CONF" in fields:
            try:
                conf = float(fields["CONF"])
                if conf < KERNEL_ADJACENT_CONF_FLOOR:
                    errors.append(
                        f"KERNEL_ADJACENT requires CONF >= {KERNEL_ADJACENT_CONF_FLOOR},"
                        f" got {conf}. Add ESCALATE::OPERATOR pre-authorization."
                    )
            except ValueError:
                if fields["CONF"] != "HIGH":
                    errors.append(
                        f"KERNEL_ADJACENT CONF must be numeric >= {KERNEL_ADJACENT_CONF_FLOOR}"
                        f" or 'HIGH', got '{fields['CONF']}'"
                    )

        # ⌬ glyph required in WUL
        if "WUL" in fields and KERNEL_ADJACENT_REQUIRED_GLYPH not in fields["WUL"]:
            errors.append(
                f"KERNEL_ADJACENT requires {KERNEL_ADJACENT_REQUIRED_GLYPH} in WUL field"
                f" (sovereign-proximity marker missing)"
            )

        # ESCALATE::OPERATOR required
        if "ESCALATE" in fields and fields["ESCALATE"] != KERNEL_ADJACENT_REQUIRED_ESCALATE:
            errors.append(
                f"KERNEL_ADJACENT requires ESCALATE::OPERATOR,"
                f" got ESCALATE::{fields['ESCALATE']}"
            )

    return ValidationResult(
        valid=len(errors) == 0,
        tier=detected_tier,
        errors=errors,
        warnings=warnings,
    )
