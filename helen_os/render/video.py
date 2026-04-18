"""
HELEN Render — video surface.

compile_video_spec now accepts DirectorPlanV1 as its primary creative input.
Profile (engine/avatar/style) remains but serves as renderer config, not story.

Invariant R4: same artifact + same plan → byte-stable compiled spec.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Optional

from .contracts import canonical_json, sha256_hex
from .director import DirectorPlanV1, direct


@dataclass(frozen=True)
class VideoRenderProfileV1:
    """Renderer configuration. Technical, not creative."""
    engine:       str
    avatar:       str
    style:        str
    aspect_ratio: str = "16:9"
    fps:          int = 30


# Canonical renderer profiles
PROFILE_MEDITATION = VideoRenderProfileV1(engine="hyperframes", avatar="helen_zephyr", style="temple_soft")
PROFILE_ORACLE     = VideoRenderProfileV1(engine="hyperframes", avatar="helen_zephyr", style="oracle_precise")
PROFILE_NARRATOR   = VideoRenderProfileV1(engine="hyperframes", avatar="helen_zephyr", style="narrator_warm")


def compile_video_spec(
    artifact,
    profile:      VideoRenderProfileV1,
    plan:         Optional[DirectorPlanV1] = None,
    director_style: str = "meditation",
) -> dict:
    """
    Deterministic: same inputs → same spec bytes (R4).
    If plan is None, generates one via direct() — still deterministic.
    """
    if plan is None:
        plan = direct(artifact, director_style)

    shots_serialized = [dataclasses.asdict(s) for s in plan.shots]

    return {
        # Source provenance
        "source_artifact_id":  artifact.artifact_id,
        "source_receipt_hash": artifact.receipt_hash,
        "plan_id":             plan.plan_id,
        "plan_hash":           plan.plan_hash,

        # Script content
        "script":   artifact.content,
        "tone":     artifact.tone,
        "persona":  artifact.persona,

        # Director layer — creative decisions
        "director": {
            "style":         plan.style,
            "tempo":         plan.tempo,
            "emotion_curve": plan.emotion_curve,
            "shots":         shots_serialized,
            "sound": {
                "music":     plan.sound.music,
                "fx":        list(plan.sound.fx),
                "mix_notes": plan.sound.mix_notes,
            },
            "voice": {
                "state":          plan.voice.state,
                "energy_curve":   list(plan.voice.energy_curve),
                "breath":         plan.voice.breath,
                "tempo":          plan.voice.tempo,
                "first_lines":    plan.voice.first_lines,
                "mid_section":    plan.voice.mid_section,
                "final_line":     plan.voice.final_line,
                "delivery_notes": plan.voice.delivery_notes,
            },
        },

        # Renderer config
        "engine":       profile.engine,
        "avatar":       profile.avatar,
        "style":        profile.style,
        "aspect_ratio": profile.aspect_ratio,
        "fps":          profile.fps,
    }


def render_video_stub(spec: dict) -> dict:
    """Stub. Replace with HyperFrames subprocess when ready."""
    rendered_payload = canonical_json(spec)
    output_hash      = sha256_hex(rendered_payload)
    return {
        "mime_type":    "video/mp4",
        "content_hash": output_hash,
        "path":         f"artifacts/render/{output_hash[:16]}.mp4",
        "metadata":     {
            "stub":          True,
            "director_style": spec.get("director", {}).get("style"),
            "shots":         len(spec.get("director", {}).get("shots", [])),
            "total_duration": sum(
                s.get("duration", 0)
                for s in spec.get("director", {}).get("shots", [])
            ),
        },
    }
