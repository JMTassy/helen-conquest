"""
research_loop/law_surface.py — Law surface registry and hash helper.

LAW_SURFACE_V1

The law surface is the frozen set of all structures that influence admissibility,
replay determinism, and state mutation in HELEN OS Research Loop.

Its SHA256 hash is a required field in every RUN_MANIFEST_V1 and VERDICT_V1.
A mismatch between recorded hash and current file is a hard constitutional failure.

Constitutional rule:
    Any structure that can influence admissibility, replay truth, state mutation,
    or best-state transition is law-surface and may not be modified through
    proposal-space.

Usage:
    from research_loop.law_surface import LAW_SURFACE_VERSION, law_surface_hash

    lsh = law_surface_hash()   # SHA256 of law_surface.yaml
    manifest = build_run_manifest(..., law_surface_version=LAW_SURFACE_VERSION,
                                       law_surface_hash=lsh)
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

# ── Constants ──────────────────────────────────────────────────────────────────

LAW_SURFACE_VERSION: str = "LAW_SURFACE_V1"

# Canonical path (relative to this file)
_DEFAULT_LAW_SURFACE_FILE: Path = Path(__file__).parent / "law_surface.yaml"

# Sentinel for tests that do not require the actual file
# ("L" × 64 is clearly a test value, not a real hash)
LAW_SURFACE_SENTINEL: str = "L" * 64


# ── Errors ─────────────────────────────────────────────────────────────────────

class LawSurfaceError(RuntimeError):
    """Raised when the law surface file is missing or unreadable."""


class LawSurfaceMismatchError(RuntimeError):
    """
    Raised when a manifest's law_surface_hash does not match the current
    law surface. This is a hard constitutional failure, not a soft warning.
    """


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_law_surface_bytes(path: Optional[str | Path] = None) -> bytes:
    """
    Load the raw bytes of law_surface.yaml.
    Raises LawSurfaceError if the file is missing.
    """
    p = Path(path) if path is not None else _DEFAULT_LAW_SURFACE_FILE
    if not p.exists():
        raise LawSurfaceError(
            f"Law surface file not found: {p}. "
            f"This is a constitutional artifact and must not be absent."
        )
    return p.read_bytes()


def law_surface_hash(path: Optional[str | Path] = None) -> str:
    """
    Return SHA256 hex digest of law_surface.yaml.

    This is the canonical law-surface fingerprint. Every run manifest and
    verdict must record this hash so the legal regime is replay-visible.

    Raises LawSurfaceError if the file is missing.
    """
    data = load_law_surface_bytes(path)
    return hashlib.sha256(data).hexdigest()


def verify_law_surface_hash(recorded_hash: str, path: Optional[str | Path] = None) -> bool:
    """
    Check that a recorded law_surface_hash still matches the current file.
    Returns True if they match, False if they differ.
    Returns False (not an error) if the file is missing — callers should
    treat this as a hard failure in production.
    """
    try:
        current = law_surface_hash(path)
    except LawSurfaceError:
        return False
    return recorded_hash == current


def assert_law_surface_hash(recorded_hash: str, path: Optional[str | Path] = None) -> None:
    """
    Hard-fail if recorded_hash does not match current law_surface.yaml.
    Raises LawSurfaceMismatchError on mismatch.

    This is the runtime guard for constitutional drift.
    """
    try:
        current = law_surface_hash(path)
    except LawSurfaceError as exc:
        raise LawSurfaceMismatchError(
            f"Cannot verify law surface: {exc}"
        ) from exc
    if recorded_hash != current:
        raise LawSurfaceMismatchError(
            f"Constitutional drift detected. "
            f"Recorded law_surface_hash={recorded_hash!r} does not match "
            f"current law_surface.yaml hash={current!r}. "
            f"This run was produced under a different legal regime. "
            f"Any verdict comparison requires migration receipt."
        )
