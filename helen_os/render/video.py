"""HELEN Render — video surface.

Invariant R4: same artifact + same profile => byte-stable compiled spec.
Stub is correct for now: preserves the contract without pretending to execute.
"""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import canonical_json, sha256_hex


@dataclass(frozen=True)
class VideoRenderProfileV1:
    engine:       str
    avatar:       str
    style:        str
    aspect_ratio: str = "16:9"
    fps:          int = 30


# Canonical profiles
PROFILE_MEDITATION = VideoRenderProfileV1(
    engine="hyperframes",
    avatar="helen_zephyr",
    style="temple_soft",
)
PROFILE_ORACLE = VideoRenderProfileV1(
    engine="hyperframes",
    avatar="helen_zephyr",
    style="oracle_precise",
)
PROFILE_NARRATOR = VideoRenderProfileV1(
    engine="hyperframes",
    avatar="helen_zephyr",
    style="narrator_warm",
)


def compile_video_spec(artifact, profile: VideoRenderProfileV1) -> dict:
    """
    Deterministic: same artifact + same profile => same dict bytes.
    No hidden state. No ambient reads. Pure function.
    """
    return {
        "source_artifact_id":  artifact.artifact_id,
        "source_receipt_hash": artifact.receipt_hash,
        "script":              artifact.content,
        "tone":                artifact.tone,
        "persona":             artifact.persona,
        "engine":              profile.engine,
        "avatar":              profile.avatar,
        "style":               profile.style,
        "aspect_ratio":        profile.aspect_ratio,
        "fps":                 profile.fps,
    }


def render_video_stub(spec: dict) -> dict:
    """
    Stub renderer. Preserves contract: produces content_hash from spec.
    Replace with real HyperFrames subprocess call when ready.
    """
    rendered_payload = canonical_json(spec)
    output_hash      = sha256_hex(rendered_payload)
    return {
        "mime_type":    "video/mp4",
        "content_hash": output_hash,
        "path":         f"artifacts/render/{output_hash[:16]}.mp4",
        "metadata":     {"stub": True},
    }
