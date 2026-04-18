"""HELEN Render — audio surface (stub).

Real implementation: Gemini TTS Zephyr via oracle_town/skills/voice/gemini_tts/helen_tts.py
Stub preserves the contract without executing.
"""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import canonical_json, sha256_hex


@dataclass(frozen=True)
class AudioRenderProfileV1:
    engine: str = "gemini_tts"
    voice:  str = "Zephyr"
    model:  str = "gemini-2.5-flash-preview-tts"


PROFILE_ZEPHYR = AudioRenderProfileV1()


def compile_audio_spec(artifact, profile: AudioRenderProfileV1) -> dict:
    return {
        "source_artifact_id":  artifact.artifact_id,
        "source_receipt_hash": artifact.receipt_hash,
        "text":                artifact.content,
        "tone":                artifact.tone,
        "persona":             artifact.persona,
        "engine":              profile.engine,
        "voice":               profile.voice,
        "model":               profile.model,
    }


def render_audio_stub(spec: dict) -> dict:
    rendered_payload = canonical_json(spec)
    output_hash      = sha256_hex(rendered_payload)
    return {
        "mime_type":    "audio/wav",
        "content_hash": output_hash,
        "path":         f"artifacts/render/{output_hash[:16]}.wav",
        "metadata":     {"stub": True},
    }
