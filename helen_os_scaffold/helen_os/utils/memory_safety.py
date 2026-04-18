# helen_os/utils/memory_safety.py
#
# Hard-ban policy for MemoryKernel content (memory.ndjson).
#
# Constitutional rule: memory MUST NOT contain authority-like lexemes
# that blur the channel boundary between run_trace (aesthetic) and
# sovereign ledger (authoritative).
#
# Usage:
#   from helen_os.utils.memory_safety import check_memory_text_is_clean
#   result = check_memory_text_is_clean(text)
#   if not result.ok:
#       raise ValueError(f"Memory safety violation: {result.violations}")

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

# ── Forbidden substrings (case-insensitive match via .upper()) ────────────
FORBIDDEN_MEMORY_SUBSTRINGS: List[str] = [
    "LEDGER",
    "SEAL",
    "SEALED",
    "VERDICT",
    "SHIP",
    "APPROVED",
    "CERTIFICATE",
    "GATE: PASSED",
    "IRREVERSIBLE",
    "EPOCH OPENED",
    "EPOCH2 OPENED",
    "HAL_VERDICT",
]


@dataclass(frozen=True)
class MemorySafetyResult:
    ok: bool
    violations: Tuple[str, ...]


def check_memory_text_is_clean(text: str) -> MemorySafetyResult:
    """
    Scan text for forbidden authority-like tokens.

    Returns:
        MemorySafetyResult(ok=True, violations=()) if clean.
        MemorySafetyResult(ok=False, violations=(...)) if contaminated.
    """
    if not isinstance(text, str):
        text = str(text)
    upper = text.upper()
    hits: List[str] = [sub for sub in FORBIDDEN_MEMORY_SUBSTRINGS if sub in upper]
    return MemorySafetyResult(ok=(len(hits) == 0), violations=tuple(hits))


def assert_memory_clean(text: str, context: str = "") -> None:
    """
    Raise ValueError if text contains forbidden tokens.
    Use before any append to memory.ndjson.
    """
    result = check_memory_text_is_clean(text)
    if not result.ok:
        ctx = f" [{context}]" if context else ""
        raise ValueError(
            f"Memory safety violation{ctx}: "
            f"forbidden tokens found: {list(result.violations)}"
        )
