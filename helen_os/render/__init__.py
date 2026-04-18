"""HELEN Render Boundary — pure function of governed execution output.

Chain: ExecutionArtifactV1 → DirectorPlanV1 → MediaArtifactV1 + RenderReceiptV1

Renderer may:  transform, stylize, materialize media.
Director may:  decide tempo, emotion, shots, sound, voice performance.
Neither may:   reason, claim authority, mutate governed state.
"""
from helen_os.render.models import ExecutionArtifactV1, MediaArtifactV1, RenderReceiptV1
from helen_os.render.director import (
    DirectorPlan, DirectorPlanV1, Shot, SoundDesign, VoiceDirective,
    direct, direct_governed, govern, from_template, TEMPLATES, VISUAL_DNA,
)
from helen_os.render.composition import HTMLCompositionV1, Asset, director_to_html
from helen_os.render.pipeline import run_video_render, run_audio_render, run_hyperframes_render

__all__ = [
    "ExecutionArtifactV1",
    "MediaArtifactV1",
    "RenderReceiptV1",
    "DirectorPlan",
    "DirectorPlanV1",
    "Shot",
    "SoundDesign",
    "VoiceDirective",
    "direct",
    "direct_governed",
    "govern",
    "from_template",
    "TEMPLATES",
    "VISUAL_DNA",
    "HTMLCompositionV1",
    "Asset",
    "director_to_html",
    "run_video_render",
    "run_audio_render",
    "run_hyperframes_render",
]
