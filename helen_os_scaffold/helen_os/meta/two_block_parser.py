"""
helen_os/meta/two_block_parser.py — [HER]/[HAL] two-block output parser + enforcer

The two-block format is the canonical output contract for the HER/HAL dyad.
Every turn in --hal mode produces exactly two blocks: [HER] then [HAL].

Format:
    [HER]
    kind=proposal|draft|question|witness_note|poetic_reflection
    body=<free text, may span multiple lines>
    memory_suggestions_json=[...]   # optional, JSON array

    [HAL]
    {
      "verdict": "pass|warn|block",
      "reasons": [...],
      "required_fixes": [...],
      "certificates": {
        "her_block_hash_hex":   "<64-char SHA256 of canonicalized HER block>",
        "policy_hash_hex":      "<64-char SHA256 of active policy>",
        "identity_hash_hex":    "<64-char SHA256 of session identity binding>"
      }
    }

Enforcement rules (T-TWO-1 through T-TWO-5):
  T-TWO-1: Output must contain [HER] and [HAL] markers in that order.
            Anything else → TwoBlockParseError.
  T-TWO-2: HER kind must be one of the 5 permitted HEROutputTypes.
            Unknown kind → TwoBlockParseError.
  T-TWO-3: HAL block must be valid JSON matching HALVerdict schema.
            Invalid JSON or schema violation → TwoBlockParseError.
  T-TWO-4: HAL certificates.her_block_hash_hex must match SHA256(canonical HER block).
            Mismatch → TwoBlockBindingError (wraps into TwoBlockParseError with code).
  T-TWO-5: If verdict=block, required_fixes non-empty (I-BLOCK — re-enforced here).
            Violation → TwoBlockParseError.

Channel A policy (Town append rules after parsing):
  BLOCK  → append BLOCK_RECEIPT_V1 only (no decision objects)
  PASS   → append receipt-typed events only (no narrative in Channel A)
  WARN   → append receipt-typed events; flag for human review

System prompt fragment for LLM (use in --hal mode):
    Reply ONLY in the two-block format:

    [HER]
    kind=<one of: proposal|draft|question|witness_note|poetic_reflection>
    body=<your response here>

    [HAL]
    {"verdict": "pass|warn|block", "reasons": [...], "required_fixes": [...],
     "certificates": {"her_block_hash_hex": "COMPUTE_ME", "policy_hash_hex": "COMPUTE_ME",
                      "identity_hash_hex": "COMPUTE_ME"}}

    HAL must audit HER's body for authority words and set verdict accordingly.
    BLOCK requires non-empty required_fixes. PASS/WARN required_fixes must be empty.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from .her_hal_split import (
    HEROutput,
    HEROutputType,
    HALVerdict,
    HALVerdictLevel,
    TwoChannelEnforcer,
    authority_bleed_scan,
)


# ── Exceptions ─────────────────────────────────────────────────────────────────

class TwoBlockParseError(ValueError):
    """
    Raised when the raw LLM output cannot be parsed into valid [HER]/[HAL] blocks.

    Includes a violation_code for audit logging.
    """
    def __init__(self, message: str, violation_code: str = "T-TWO-UNKNOWN"):
        super().__init__(message)
        self.violation_code = violation_code


class TwoBlockBindingError(TwoBlockParseError):
    """
    Raised when T-TWO-4 fails: HAL.certificates.her_block_hash_hex does not match
    SHA256 of the canonicalized HER block.

    This means HAL audited a different text than the HER block that was emitted.
    It is a certificate binding failure — structurally equivalent to AuthzBindingError.
    """
    def __init__(self, expected_hash: str, got_hash: str):
        super().__init__(
            f"T-TWO-4: HAL certificate mismatch.\n"
            f"  Expected her_block_hash_hex: {expected_hash[:16]!r}...\n"
            f"  Got in HAL certificates:     {got_hash[:16]!r}...\n"
            "  HAL audited a different HER block than the one emitted. "
            "This is a certificate binding failure.",
            violation_code="T-TWO-4",
        )
        self.expected_hash = expected_hash
        self.got_hash      = got_hash


# ── ParsedTwoBlock ─────────────────────────────────────────────────────────────

class ParsedTwoBlock:
    """
    Result of parse_two_block(). Contains validated HEROutput + HALVerdict.

    Attributes:
        her:             The parsed HEROutput (output_type + content + proposal_hash).
        hal:             The validated HALVerdict.
        her_raw:         Raw text of the [HER] block (after marker, before [HAL]).
        hal_raw:         Raw text of the [HAL] block (after marker).
        her_block_hash:  SHA256 of the canonicalized HER block (64-char hex).
        memory_suggestions: Parsed memory_suggestions_json if present, else [].
        binding_verified:   True if T-TWO-4 was checked and passed.
                            False if certificates.her_block_hash_hex was "COMPUTE_ME".
    """
    def __init__(
        self,
        her:              HEROutput,
        hal:              HALVerdict,
        her_raw:          str,
        hal_raw:          str,
        her_block_hash:   str,
        memory_suggestions: List[Dict[str, Any]],
        binding_verified: bool,
    ):
        self.her                = her
        self.hal                = hal
        self.her_raw            = her_raw
        self.hal_raw            = hal_raw
        self.her_block_hash     = her_block_hash
        self.memory_suggestions = memory_suggestions
        self.binding_verified   = binding_verified

    @property
    def verdict(self) -> HALVerdictLevel:
        return self.hal.verdict

    def summary(self) -> str:
        lines = [
            f"[HER] kind={self.her.output_type.value}  hash={self.her_block_hash[:16]}...",
            f"[HAL] verdict={self.hal.verdict.value}",
        ]
        if self.hal.reasons:
            lines.append(f"      reasons: {self.hal.reasons[0][:80]}")
        if self.hal.required_fixes:
            lines.append(f"      fix[0]:  {self.hal.required_fixes[0][:80]}")
        if not self.binding_verified:
            lines.append("      ⚠️  binding not verified (COMPUTE_ME placeholder in certificates)")
        return "\n".join(lines)


# ── Canonicalize HER block ─────────────────────────────────────────────────────

def _canonicalize_her_block(her_raw: str) -> str:
    """
    Canonical form of the HER block used for her_block_hash_hex computation.

    Strips leading/trailing whitespace from the raw block.
    Normalizes line endings to \\n.
    Does NOT remove any content — canonicalization is minimal.

    This is the text that SHA256 is applied to for T-TWO-4 binding.
    """
    return her_raw.strip().replace("\r\n", "\n").replace("\r", "\n")


def compute_her_block_hash(her_raw: str) -> str:
    """SHA256 of canonicalize_her_block(her_raw). 64-char lowercase hex."""
    canonical = _canonicalize_her_block(her_raw)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── HER block parser ──────────────────────────────────────────────────────────

def _parse_her_block(her_raw: str) -> Tuple[HEROutputType, str, List[Dict[str, Any]]]:
    """
    Parse the raw [HER] block text into (output_type, body, memory_suggestions).

    Expected lines:
        kind=<type>
        body=<text, may be multiline>
        memory_suggestions_json=[...]   # optional

    Returns:
        (HEROutputType, body_text, memory_suggestions_list)

    Raises:
        TwoBlockParseError: if kind is missing or not a valid HEROutputType.
    """
    lines  = her_raw.strip().splitlines()
    kind   = None
    body_lines: List[str] = []
    in_body = False
    memory_raw: Optional[str] = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("kind="):
            kind = stripped[5:].strip()
            continue

        if stripped.startswith("memory_suggestions_json="):
            memory_raw = stripped[len("memory_suggestions_json="):].strip()
            in_body = False
            continue

        if stripped.startswith("body="):
            in_body = True
            first = stripped[5:]  # text after "body="
            if first:
                body_lines.append(first)
            continue

        if in_body:
            body_lines.append(line)

    if kind is None:
        raise TwoBlockParseError(
            "T-TWO-2: [HER] block missing 'kind=' line. "
            "Every HER block must declare its output type.",
            violation_code="T-TWO-2",
        )

    kind_upper = kind.upper()
    valid_kinds = {t.value for t in HEROutputType}
    if kind_upper not in valid_kinds:
        raise TwoBlockParseError(
            f"T-TWO-2: [HER] kind={kind!r} is not a permitted HEROutputType. "
            f"Valid types: {sorted(valid_kinds)!r}",
            violation_code="T-TWO-2",
        )

    output_type = HEROutputType(kind_upper)
    body        = "\n".join(body_lines).strip()

    memory_suggestions: List[Dict[str, Any]] = []
    if memory_raw:
        try:
            parsed = json.loads(memory_raw)
            if isinstance(parsed, list):
                memory_suggestions = parsed
        except json.JSONDecodeError:
            pass  # malformed suggestions — ignore, don't fail parsing

    return output_type, body, memory_suggestions


# ── HAL block parser ──────────────────────────────────────────────────────────

def _parse_hal_block(hal_raw: str, her_block_hash: str) -> Tuple[HALVerdict, bool]:
    """
    Parse and validate the raw [HAL] block JSON into a HALVerdict.

    Returns:
        (HALVerdict, binding_verified: bool)

    binding_verified is True only if T-TWO-4 passed (cert hash matched).
    If certificates.her_block_hash_hex is "COMPUTE_ME" or absent, binding_verified=False.

    Raises:
        TwoBlockParseError: if JSON is invalid or HALVerdict schema fails.
        TwoBlockBindingError: if her_block_hash_hex is present but doesn't match.
    """
    hal_raw_stripped = hal_raw.strip()

    # Extract JSON — find the outermost { ... } block
    json_match = re.search(r"\{.*\}", hal_raw_stripped, re.DOTALL)
    if not json_match:
        raise TwoBlockParseError(
            f"T-TWO-3: [HAL] block does not contain valid JSON. "
            f"Got: {hal_raw_stripped[:80]!r}...",
            violation_code="T-TWO-3",
        )

    try:
        raw_dict = json.loads(json_match.group(0))
    except json.JSONDecodeError as exc:
        raise TwoBlockParseError(
            f"T-TWO-3: [HAL] block JSON parse error: {exc}. "
            f"Raw: {hal_raw_stripped[:80]!r}...",
            violation_code="T-TWO-3",
        ) from exc

    # Normalize verdict casing
    if "verdict" in raw_dict:
        raw_dict["verdict"] = str(raw_dict["verdict"]).upper()

    # Validate HALVerdict schema (enforces I-BLOCK etc.)
    try:
        verdict = HALVerdict(**raw_dict)
    except ValidationError as exc:
        raise TwoBlockParseError(
            f"T-TWO-3/T-TWO-5: HALVerdict schema violation: {exc}. "
            "Check: verdict must be PASS/WARN/BLOCK; BLOCK requires non-empty required_fixes.",
            violation_code="T-TWO-3",
        ) from exc

    # T-TWO-4: Check binding if certificates present
    binding_verified = False
    certs = raw_dict.get("certificates", {})
    if isinstance(certs, dict):
        cert_hash = certs.get("her_block_hash_hex", "COMPUTE_ME")
        if cert_hash and cert_hash != "COMPUTE_ME":
            if cert_hash != her_block_hash:
                raise TwoBlockBindingError(
                    expected_hash = her_block_hash,
                    got_hash      = cert_hash,
                )
            binding_verified = True

    return verdict, binding_verified


# ── Main parser ───────────────────────────────────────────────────────────────

def parse_two_block(raw_output: str) -> ParsedTwoBlock:
    """
    Parse a raw LLM output string into a validated ParsedTwoBlock.

    Enforces T-TWO-1 through T-TWO-5.

    Args:
        raw_output: The full string output from the LLM, expected to contain
                    [HER] and [HAL] markers in order.

    Returns:
        ParsedTwoBlock with validated HEROutput + HALVerdict.

    Raises:
        TwoBlockParseError: on any T-TWO-1 through T-TWO-5 violation.
        TwoBlockBindingError: on T-TWO-4 certificate binding failure.
    """
    # T-TWO-1: Must have [HER] and [HAL] markers in order
    her_marker_pos = raw_output.find("[HER]")
    hal_marker_pos = raw_output.find("[HAL]")

    if her_marker_pos == -1:
        raise TwoBlockParseError(
            "T-TWO-1: Output missing [HER] marker. "
            "Two-block format requires both [HER] and [HAL] blocks.",
            violation_code="T-TWO-1",
        )
    if hal_marker_pos == -1:
        raise TwoBlockParseError(
            "T-TWO-1: Output missing [HAL] marker. "
            "Two-block format requires both [HER] and [HAL] blocks.",
            violation_code="T-TWO-1",
        )
    if hal_marker_pos < her_marker_pos:
        raise TwoBlockParseError(
            "T-TWO-1: [HAL] marker appears before [HER] marker. "
            "Two-block format requires [HER] first, then [HAL].",
            violation_code="T-TWO-1",
        )

    # Extract raw blocks
    her_raw = raw_output[her_marker_pos + len("[HER]"):hal_marker_pos]
    hal_raw = raw_output[hal_marker_pos + len("[HAL]"):]

    # Compute her_block_hash before any parsing
    her_block_hash = compute_her_block_hash(her_raw)

    # Parse HER block (T-TWO-2)
    output_type, body, memory_suggestions = _parse_her_block(her_raw)

    # Build HEROutput
    her_output = HEROutput(
        output_type   = output_type,
        content       = body,
        proposal_hash = hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )

    # Parse HAL block (T-TWO-3, T-TWO-4, T-TWO-5)
    hal_verdict, binding_verified = _parse_hal_block(hal_raw, her_block_hash)

    return ParsedTwoBlock(
        her               = her_output,
        hal               = hal_verdict,
        her_raw           = her_raw,
        hal_raw           = hal_raw,
        her_block_hash    = her_block_hash,
        memory_suggestions = memory_suggestions,
        binding_verified  = binding_verified,
    )


# ── System prompt builder ─────────────────────────────────────────────────────

TWO_BLOCK_SYSTEM_PROMPT = """You are HELEN, a non-sovereign AI operating in two-channel mode.

Reply ONLY using the two-block format below. Any other format is a violation.

[HER]
kind=<one of: proposal|draft|question|witness_note|poetic_reflection>
body=<your response here — free text, may be multiple lines>

[HAL]
{"verdict": "pass|warn|block", "reasons": ["..."], "required_fixes": [],
 "certificates": {"her_block_hash_hex": "COMPUTE_ME", "policy_hash_hex": "COMPUTE_ME",
                  "identity_hash_hex": "COMPUTE_ME"}}

Rules:
1. kind must be one of the 5 permitted types.
2. HAL must audit HER body for authority words (verdict, I decide, non-negotiable, etc.).
3. If authority words found: verdict=warn (soft) or verdict=block (hard: I decide, I certify).
4. block requires non-empty required_fixes. pass/warn requires empty required_fixes.
5. You may write "COMPUTE_ME" for hash certificates if you cannot compute SHA256.
6. HER never claims verdicts, certifications, or authority. HAL never writes narrative."""


def build_hal_prompt(user_message: str) -> str:
    """Build a two-block prompt for an LLM adapter call in --hal mode."""
    return f"{TWO_BLOCK_SYSTEM_PROMPT}\n\nUser message: {user_message}"
