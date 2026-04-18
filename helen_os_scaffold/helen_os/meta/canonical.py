"""
helen_os/meta/canonical.py — Canonical JSON + artifact SHA256 utilities.

CANONICAL JSON (RFC 8785 subset):
  sort_keys=True, no whitespace (separators=(',', ':')), ensure_ascii=True.
  This gives stable bytes across runtimes, whitespace settings, and key orderings.

ARTIFACT SHA256 — Pattern A (the correct pattern):
  artifact_sha256 = SHA256(canonical_json(artifact WITHOUT artifact_sha256 field))

  The field is EXCLUDED from the hash so that the hash is the hash of the
  stable object content, not a self-referential paradox.

  Verification:
    artifact = json.load(f)
    stored = artifact.pop("artifact_sha256")
    computed = artifact_sha256_of(artifact)
    assert computed == stored

MANIFEST SHA256 — root-of-roots:
  manifest_sha256 = SHA256(canonical_json(sorted_dict_of_file_hashes))
  This is a Merkle root over all content-addressed files.
  A single hash that commits the entire file set.

WHY THIS MATTERS:
  If artifact_sha256 = SHA256(artifact_WITH_artifact_sha256),
  then the stored hash can never match the file hash (self-reference).
  Pattern A avoids this by hashing the pre-insertion object.
  Reviewers can independently verify by popping the field and re-hashing.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


# ── Canonical JSON ────────────────────────────────────────────────────────────

def canonical_json(obj: Any) -> str:
    """
    Produce canonical (deterministic) JSON string.
    RFC 8785-subset: sort_keys=True, no whitespace, ASCII-safe.

    This is stable across:
      - Python versions (JSON key ordering)
      - Whitespace settings (indent/separators)
      - Character encoding (ensure_ascii strips non-ASCII escapes)
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_sha256(obj: Any) -> str:
    """SHA256(canonical_json(obj)). Returns 64-char hex."""
    return hashlib.sha256(canonical_json(obj).encode("ascii")).hexdigest()


# ── Artifact SHA256 (Pattern A) ───────────────────────────────────────────────

ARTIFACT_SHA256_FIELD = "artifact_sha256"
ARTIFACT_SHA256_SCHEME = (
    "SHA256(canonical_json(artifact_without_artifact_sha256_field)); "
    "RFC-8785-subset: sort_keys=True, no whitespace, ensure_ascii=True"
)


def compute_artifact_sha256(artifact: Dict[str, Any]) -> str:
    """
    Pattern A: compute artifact_sha256 over the object WITHOUT the field itself.

    The artifact must NOT contain 'artifact_sha256' when this is called,
    or the result will differ from what's stored (use strip_artifact_sha256 first).

    Returns 64-char hex.
    """
    # Guard: field must not be present
    if ARTIFACT_SHA256_FIELD in artifact:
        raise ValueError(
            f"compute_artifact_sha256: artifact must NOT contain '{ARTIFACT_SHA256_FIELD}'. "
            f"Call strip_artifact_sha256(artifact) first."
        )
    return canonical_sha256(artifact)


def embed_artifact_sha256(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pattern A: compute and embed artifact_sha256 into a copy of the artifact.

    Returns a new dict (does not mutate input) with:
      - artifact_sha256: the computed hash
      - artifact_sha256_scheme: explanation of what was hashed

    Verification:
      stored = result.pop("artifact_sha256")
      _ = result.pop("artifact_sha256_scheme")
      assert canonical_sha256(result) == stored
    """
    if ARTIFACT_SHA256_FIELD in artifact:
        raise ValueError(
            f"embed_artifact_sha256: artifact already has '{ARTIFACT_SHA256_FIELD}'. "
            f"Call strip_artifact_sha256 first."
        )

    h = canonical_sha256(artifact)
    result = dict(artifact)
    result[ARTIFACT_SHA256_FIELD] = h
    result["artifact_sha256_scheme"] = ARTIFACT_SHA256_SCHEME
    return result


def strip_artifact_sha256(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a copy of artifact with artifact_sha256 + artifact_sha256_scheme removed.
    Used for verification: strip → re-hash → compare.
    """
    result = dict(artifact)
    result.pop(ARTIFACT_SHA256_FIELD, None)
    result.pop("artifact_sha256_scheme", None)
    return result


def verify_artifact_sha256(artifact: Dict[str, Any]) -> tuple[bool, str]:
    """
    Verify stored artifact_sha256 matches Pattern A computation.

    Returns (valid: bool, reason: str).
    """
    stored = artifact.get(ARTIFACT_SHA256_FIELD)
    if stored is None:
        return False, f"No '{ARTIFACT_SHA256_FIELD}' field in artifact"

    stripped = strip_artifact_sha256(artifact)
    computed = canonical_sha256(stripped)

    if computed == stored:
        return True, f"artifact_sha256 verified: {stored[:16]}..."
    return False, (
        f"artifact_sha256 MISMATCH: "
        f"stored={stored[:16]}... computed={computed[:16]}..."
    )


# ── Manifest SHA256 (root-of-roots) ──────────────────────────────────────────

def compute_manifest_sha256(file_hashes: Dict[str, str]) -> str:
    """
    Compute manifest_sha256 = SHA256(canonical_json(sorted_file_hashes)).

    This is the root-of-roots over all content-addressed files.
    Stable: canonical JSON sorts keys, so insertion order doesn't matter.

    Args:
        file_hashes: {name: sha256_hex} mapping (e.g., from epoch mark content_hashes).

    Returns 64-char hex.
    """
    # canonical_sha256 sorts keys → stable regardless of insertion order
    return canonical_sha256(file_hashes)


def verify_manifest_sha256(
    manifest_sha256: str,
    file_hashes: Dict[str, str],
) -> tuple[bool, str]:
    """
    Verify a stored manifest_sha256 against a file_hashes dict.
    Returns (valid: bool, reason: str).
    """
    computed = compute_manifest_sha256(file_hashes)
    if computed == manifest_sha256:
        return True, f"manifest_sha256 verified: {manifest_sha256[:16]}..."
    return False, (
        f"manifest_sha256 MISMATCH: "
        f"stored={manifest_sha256[:16]}... computed={computed[:16]}..."
    )
