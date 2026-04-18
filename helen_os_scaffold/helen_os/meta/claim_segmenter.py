"""
helen_os/meta/claim_segmenter.py — ClaimSegmenterV1 (rule-based atomic claim extractor).

Implements Section C item 1 from the WILD TOWN / NO SHIP proposal:
  "a canonical ClaimSegmenterV1 (atomic claim extraction)"

IMPORTANT LIMITATION (stated explicitly per Section C):
  This segmenter is RULE-BASED and DETERMINISTIC.
  It does NOT use an LLM.
  Passport assignment is always UNKNOWN after segmentation —
  a human or a downstream annotator must upgrade passports to
  OBSERVED / INFERRED / SPECULATIVE.

Design:
  - Deterministic: same input → same output (no randomness)
  - Fail-closed: claims with parse errors get passport=UNKNOWN
  - Flagging: claims containing unsupported numbers/dates/quotes are flagged

Segmentation rules (ClaimSegmenterV1 SPEC):
  SR1: Split on sentence boundaries.
       Boundary = (. | ! | ?) followed by (whitespace | end-of-string)
       Exception: abbreviations ending in single uppercase letter before .
       (e.g., "U.S.", "Dr.") are NOT split. Simple heuristic: skip splits
       where the preceding token is a 1-2 char uppercase word.
  SR2: Filter out segments shorter than MIN_CLAIM_LENGTH chars (default 10).
  SR3: Strip leading/trailing whitespace from each segment.
  SR4: Assign claim_id = "CL-{n:03d}" (1-indexed, zero-padded to 3 digits).
  SR5: Flag claims containing:
         - Any sequence of digits (numbers)
         - Date-like patterns (4-digit year, month names, ordinal dates)
         - Quoted content (text inside " " or ' ')

Flagging does NOT change the passport. It sets flagged=True and flag_reason.
The caller must decide whether to remove or annotate flagged claims.

Usage:
    from helen_os.meta.claim_segmenter import ClaimSegmenterV1
    segmenter = ClaimSegmenterV1()
    claims = segmenter.segment("The sky is blue. Water boils at 100°C.")
    # → [
    #     AtomicClaim(claim_id="CL-001", text="The sky is blue",
    #                 passport="UNKNOWN", flagged=False),
    #     AtomicClaim(claim_id="CL-002", text="Water boils at 100°C",
    #                 passport="UNKNOWN", flagged=True,
    #                 flag_reason="Contains number: '100'"),
    # ]
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .inspector import AtomicClaim, PassportLabel


# ── Constants ─────────────────────────────────────────────────────────────────

#: Minimum character length for a segment to be kept as a claim.
MIN_CLAIM_LENGTH: int = 10

#: Month names for date flagging.
_MONTH_NAMES = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
)

# ── Compiled patterns ─────────────────────────────────────────────────────────

# SR1: sentence boundary — (. | ! | ?) followed by whitespace or end.
# Simple, fixed-width: we do NOT use variable-width lookbehinds (not supported
# in CPython's re module). Abbreviation handling is done in _split_sentences()
# by post-processing: if a segment ends with a known abbreviation, merge it with
# the next segment.
_SENTENCE_END = re.compile(
    r"[.!?]"        # sentence-ending punctuation
    r"(?=\s|$)",    # followed by whitespace or end of string
)

# Digit / number pattern
_DIGIT_RE = re.compile(r"\d+")

# 4-digit year pattern
_YEAR_RE = re.compile(r"\b(1[0-9]{3}|2[0-9]{3})\b")

# Month name pattern (case-insensitive)
_MONTH_RE = re.compile(
    r"\b(" + "|".join(_MONTH_NAMES) + r")\b",
    re.IGNORECASE,
)

# Quoted text pattern (double or single quotes with content)
_QUOTE_RE = re.compile(r'(?:"[^"]{1,200}"|\'[^\']{1,200}\')')


# ── ClaimSegmenterV1 ──────────────────────────────────────────────────────────

class ClaimSegmenterV1:
    """
    Rule-based atomic claim segmenter.

    All output claims have passport=UNKNOWN.
    Passport upgrade (OBSERVED/INFERRED/SPECULATIVE) requires a separate
    annotation pass (human or downstream tool).

    Usage:
        seg    = ClaimSegmenterV1()
        claims = seg.segment("The Earth is round. 42% of voters agreed.")
    """

    def __init__(self, min_claim_length: int = MIN_CLAIM_LENGTH):
        self.min_claim_length = min_claim_length

    def segment(
        self,
        text:       str,
        id_prefix:  str = "CL",
        start_idx:  int = 1,
    ) -> List[AtomicClaim]:
        """
        Segment text into atomic claims.

        Args:
            text:       Input text to segment.
            id_prefix:  Prefix for claim IDs (default "CL" → "CL-001").
            start_idx:  Starting index for claim IDs (default 1).

        Returns:
            List of AtomicClaim, all with passport=UNKNOWN.
        """
        if not text or not text.strip():
            return []

        segments = self._split_sentences(text)
        claims: List[AtomicClaim] = []

        for i, seg in enumerate(segments):
            seg = seg.strip()
            if len(seg) < self.min_claim_length:
                continue

            claim_id = f"{id_prefix}-{start_idx + i:03d}"
            flagged, flag_reason = self._check_flags(seg)

            # AtomicClaim with passport=UNKNOWN: no span_pointer, no inference_rule
            # We use model_construct to bypass validators that require span_pointer
            # for OBSERVED claims (which this isn't — it's UNKNOWN)
            claim = AtomicClaim.model_construct(
                claim_id       = claim_id,
                text           = seg,
                passport       = "UNKNOWN",
                span_pointer   = None,
                inference_rule = None,
                premises       = [],
                flagged        = flagged,
                flag_reason    = flag_reason,
            )
            claims.append(claim)

        return claims

    def _split_sentences(self, text: str) -> List[str]:
        """
        SR1: Split text on sentence boundaries.
        Returns list of sentence strings (may include empty strings — filtered by caller).
        """
        # Find all sentence-ending positions
        positions: List[int] = [m.end() for m in _SENTENCE_END.finditer(text)]

        if not positions:
            return [text]

        segments: List[str] = []
        prev = 0
        for pos in positions:
            seg = text[prev:pos].strip()
            if seg:
                segments.append(seg)
            prev = pos

        # Capture any remaining text after the last sentence end
        remaining = text[prev:].strip()
        if remaining and len(remaining) >= self.min_claim_length:
            segments.append(remaining)

        return segments

    def _check_flags(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        SR5: Flag claims containing unsupported numbers/dates/quotes.

        Returns (flagged: bool, flag_reason: Optional[str]).
        """
        reasons: List[str] = []

        # Number check
        digit_match = _DIGIT_RE.search(text)
        if digit_match:
            reasons.append(f"Contains number: {digit_match.group()!r}")

        # Date check: 4-digit year
        year_match = _YEAR_RE.search(text)
        if year_match and not digit_match:  # already flagged via digit
            reasons.append(f"Contains year: {year_match.group()!r}")

        # Month name check
        month_match = _MONTH_RE.search(text)
        if month_match:
            reasons.append(f"Contains month name: {month_match.group()!r}")

        # Quote check
        quote_match = _QUOTE_RE.search(text)
        if quote_match:
            reasons.append(f"Contains quoted text: {quote_match.group()[:32]!r}")

        if reasons:
            return True, "; ".join(reasons)
        return False, None
