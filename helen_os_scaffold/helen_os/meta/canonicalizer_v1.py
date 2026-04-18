"""
helen_os/meta/canonicalizer_v1.py — CanonicalizerV1 (text output canonicalization).

CONTRACT: CanonicalizerV1

Purpose:
  Produce a stable, deterministic byte representation of a text output
  so that sha256(canonical_bytes) is identical across runs with the same
  semantic content. Used by DeterminismReportV1 to compare run hashes.

Rules (applied in strict order — must be idempotent: f(f(x)) == f(x)):
  R1: Normalize line endings: \\r\\n → \\n, \\r → \\n
  R2: Strip trailing whitespace from each line
  R3: Collapse sequences of > 1 consecutive blank lines to exactly 1 blank line
  R4: Strip leading blank lines (from start of text)
  R5: Strip trailing blank lines + trailing newline (from end of text)
  R6: Encode as UTF-8

For JSON-structured outputs (is_json=True):
  J1: Parse as JSON (fail hard if invalid)
  J2: json.dumps(parsed, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
  J3: Apply R1–R6 to the resulting string

Hash:
  sha256(canonical_bytes).hexdigest() → 64-char hex

Stability requirement (enforced by test):
  canonicalize(canonicalize(text)).hash == canonicalize(text).hash

Stop condition:
  - If text cannot be decoded as UTF-8, raise CanonicalizationError.
  - If is_json=True and text is not valid JSON, raise CanonicalizationError.
  - Never return an unverified result.

Integration:
  from helen_os.meta.canonicalizer_v1 import CanonicalizerV1, canonicalize_text
  result = canonicalize_text("some output\\n")
  # result.canonical_hash → sha256 hex
  # result.rules_applied  → ["R1", "R2", "R3", "R4", "R5", "R6"]
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Exception ─────────────────────────────────────────────────────────────────

class CanonicalizationError(ValueError):
    """Raised when CanonicalizerV1 cannot produce a stable canonical form."""


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class CanonicalizationResult:
    """
    Output of CanonicalizerV1.canonicalize().

    original_len:    len(original text in bytes)
    canonical_text:  The normalized text (string, before UTF-8 encoding)
    canonical_bytes: UTF-8 encoded canonical text
    canonical_hash:  sha256(canonical_bytes).hexdigest() — 64-char hex
    encoding:        "utf-8" (always)
    rules_applied:   Ordered list of rule codes applied
    is_json:         True if JSON path was used
    """
    original_len:    int
    canonical_text:  str
    canonical_bytes: bytes
    canonical_hash:  str
    encoding:        str        = "utf-8"
    rules_applied:   List[str]  = field(default_factory=list)
    is_json:         bool       = False

    def is_idempotent(self, other: "CanonicalizationResult") -> bool:
        """True if two results from the same text produce the same hash."""
        return self.canonical_hash == other.canonical_hash


# ── CanonicalizerV1 ───────────────────────────────────────────────────────────

class CanonicalizerV1:
    """
    Text output canonicalization — deterministic normalization before hashing.

    Usage:
        canon  = CanonicalizerV1()
        result = canon.canonicalize("Hello world\\r\\n  ")
        hash   = result.canonical_hash      # sha256 hex

        # JSON outputs
        result = canon.canonicalize('{"b":1,"a":2}', is_json=True)
        # → canonical_text: '{"a":2,"b":1}'  (sorted keys, no whitespace)

    Idempotence test:
        r1 = canon.canonicalize(text)
        r2 = canon.canonicalize(r1.canonical_text)
        assert r1.canonical_hash == r2.canonical_hash
    """

    # Compiled patterns (one-time cost)
    _CRLF    = re.compile(r"\r\n")
    _CR      = re.compile(r"\r")
    _TRAIL   = re.compile(r"[ \t]+$", re.MULTILINE)
    _BLANKS  = re.compile(r"\n{3,}")

    def canonicalize(
        self,
        text:    str,
        is_json: bool = False,
    ) -> CanonicalizationResult:
        """
        Canonicalize a text output.

        Args:
            text:    The text to canonicalize (str).
            is_json: If True, parse as JSON and apply J1–J3 before R1–R6.

        Returns:
            CanonicalizationResult with canonical_hash.

        Raises:
            CanonicalizationError: if UTF-8 encoding fails or JSON is invalid.
        """
        rules_applied: List[str] = []

        # ── JSON path (J1–J3) ────────────────────────────────────────────────
        if is_json:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as e:
                raise CanonicalizationError(
                    f"CanonicalizerV1: is_json=True but text is not valid JSON: {e}"
                )
            text = json.dumps(
                parsed,
                sort_keys    = True,
                separators   = (",", ":"),
                ensure_ascii = True,
            )
            rules_applied.extend(["J1", "J2"])

        original_len = len(text.encode("utf-8", errors="strict"))

        # ── R1: normalize line endings ────────────────────────────────────────
        text = self._CRLF.sub("\n", text)
        text = self._CR.sub("\n", text)
        rules_applied.append("R1")

        # ── R2: strip trailing whitespace per line ────────────────────────────
        text = self._TRAIL.sub("", text)
        rules_applied.append("R2")

        # ── R3: collapse multiple consecutive blank lines ─────────────────────
        text = self._BLANKS.sub("\n\n", text)
        rules_applied.append("R3")

        # ── R4: strip leading blank lines ─────────────────────────────────────
        text = text.lstrip("\n")
        rules_applied.append("R4")

        # ── R5: strip trailing blank lines + trailing newline ─────────────────
        text = text.rstrip("\n").rstrip()
        rules_applied.append("R5")

        # ── R6: UTF-8 encode ──────────────────────────────────────────────────
        try:
            canonical_bytes = text.encode("utf-8", errors="strict")
        except UnicodeEncodeError as e:
            raise CanonicalizationError(
                f"CanonicalizerV1: cannot encode to UTF-8: {e}"
            )
        rules_applied.append("R6")

        canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

        return CanonicalizationResult(
            original_len    = original_len,
            canonical_text  = text,
            canonical_bytes = canonical_bytes,
            canonical_hash  = canonical_hash,
            encoding        = "utf-8",
            rules_applied   = rules_applied,
            is_json         = is_json,
        )

    def hash_text(self, text: str, is_json: bool = False) -> str:
        """
        Convenience: canonicalize text and return sha256 hex.

        Equivalent to canonicalize(text, is_json).canonical_hash.
        """
        return self.canonicalize(text, is_json=is_json).canonical_hash


# ── Module-level convenience ──────────────────────────────────────────────────

_DEFAULT = CanonicalizerV1()


def canonicalize_text(
    text:    str,
    is_json: bool = False,
) -> CanonicalizationResult:
    """
    Module-level convenience wrapper using the default CanonicalizerV1 instance.

    Args:
        text:    Text to canonicalize.
        is_json: If True, treat text as JSON.

    Returns:
        CanonicalizationResult.
    """
    return _DEFAULT.canonicalize(text, is_json=is_json)


def canonical_text_hash(text: str, is_json: bool = False) -> str:
    """
    Module-level convenience: return sha256(canonicalize(text)).

    Returns 64-char hex.
    """
    return _DEFAULT.hash_text(text, is_json=is_json)
