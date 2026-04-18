"""
HELEN Render — Director Layer.

Sits between ExecutionArtifactV1 and the renderer.
This is where creativity lives. Not in the renderer.

Chain:
  ExecutionArtifactV1
  → direct(artifact, style) → DirectorPlanV1      ← here
  → compile_video_spec(artifact, plan)
  → render

Invariants:
  D1: same artifact + style → same plan (deterministic)
  D2: authority=False always
  D3: plan carries source_receipt_hash (bound to governed source)
  D4: plan_hash = sha256(canonical(plan without plan_hash field))

HELEN Visual DNA (constitutional):
  colors:  deep blue / gold / black
  motion:  slow, intentional
  camera:  always moving slightly
  light:   volumetric, dust particles
  pacing:  breath-driven
  editing: rhythm variation, silence moments, asymmetry
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .contracts import canonical_json, sha256_hex
from .models import ExecutionArtifactV1, Tone, Persona


# ── Vocabulary ─────────────────────────────────────────────────────────────────

ShotType   = str   # "wide" | "close" | "medium" | "extreme_close" | "aerial"
CameraMove = str   # "slow_push_in" | "pull_back" | "handheld_micro" | "orbit" | "drift" | "static"
EmotionBeat = str  # "calm" | "tension" | "rise" | "release" | "silence" | "float"


# ── Shot ───────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Shot:
    type:         ShotType
    camera:       CameraMove
    duration:     int            # seconds
    visual:       str            # scene description for renderer
    text_overlay: Optional[str]  # None = no text
    fx:           List[str]      = field(default_factory=list)  # per-shot FX


# ── Sound ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SoundDesign:
    music:     str         # "ambient_pad_low" | "temple_drone" | "breath_pulse" | "none"
    fx:        List[str]   # ["breath", "wind_soft", "particles", "low_rumble"]
    mix_notes: str = ""    # director notes for audio mix


# ── Voice directive ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class VoiceDirective:
    """
    Directed voice acting parameters — not TTS config.
    These are performance instructions, not technical settings.
    """
    state:          str   # "controlled_vulnerability" | "oracle_calm" | "witness_precise"
    energy_curve:   List[str]   # ["low", "rising", "collapse"] or ["steady", "break"]
    breath:         str   # "audible" | "subtle" | "none"
    tempo:          str   # "irregular" | "breath_driven" | "steady"
    first_lines:    str   # delivery instruction: "almost whisper"
    mid_section:    str   # "tension, slightly faster"
    final_line:     str   # "slower, heavier, almost breaking"
    delivery_notes: str = ""  # free-form director note


# ── DirectorPlanV1 ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DirectorPlanV1:
    """
    The creative decision layer.
    Generated deterministically from (artifact, style).
    Bound to source artifact via receipt chain.
    """
    plan_id:             str
    source_artifact_id:  str
    source_receipt_hash: str

    # Creative substance
    style:         str            # "meditation" | "oracle" | "witness" | "declaration"
    tempo:         str            # "slow_build" | "pulse" | "breath_driven" | "tension_release"
    emotion_curve: List[EmotionBeat]
    shots:         List[Shot]
    sound:         SoundDesign
    voice:         VoiceDirective

    plan_hash:  str       # sha256 of plan body (D4)
    authority:  bool = False   # D2: always False

    def __post_init__(self) -> None:
        if self.authority:
            raise ValueError("DirectorPlanV1.authority must be False")

    def total_duration(self) -> int:
        return sum(s.duration for s in self.shots)


# ── Style presets ──────────────────────────────────────────────────────────────

_STYLES: dict = {
    "meditation": {
        "tempo":         "slow_build",
        "emotion_curve": ["calm", "tension", "release", "silence"],
        "sound": SoundDesign(
            music="ambient_pad_low",
            fx=["breath", "wind_soft", "particles"],
            mix_notes="pads underneath, breath audible in gaps",
        ),
        "voice": VoiceDirective(
            state="controlled_vulnerability",
            energy_curve=["low", "rising", "collapse"],
            breath="audible",
            tempo="irregular",
            first_lines="almost whisper — aware, precise",
            mid_section="tension, slightly faster, weight building",
            final_line="slower, heavier, almost breaking — then silence",
            delivery_notes="like someone who understands too much but speaks gently",
        ),
    },
    "oracle": {
        "tempo":         "tension_release",
        "emotion_curve": ["float", "rise", "tension", "release"],
        "sound": SoundDesign(
            music="temple_drone",
            fx=["low_rumble", "particles", "tone_strike"],
            mix_notes="drone builds under speech, strike on key lines",
        ),
        "voice": VoiceDirective(
            state="oracle_calm",
            energy_curve=["steady", "rise", "break"],
            breath="subtle",
            tempo="breath_driven",
            first_lines="even, measured — weight without urgency",
            mid_section="precision increases, pauses widen",
            final_line="single syllable drop into silence",
            delivery_notes="authority without claiming it — let the words carry",
        ),
    },
    "witness": {
        "tempo":         "pulse",
        "emotion_curve": ["calm", "float", "silence"],
        "sound": SoundDesign(
            music="none",
            fx=["breath", "room_tone"],
            mix_notes="near silence — only breath and room",
        ),
        "voice": VoiceDirective(
            state="witness_precise",
            energy_curve=["low", "steady"],
            breath="audible",
            tempo="irregular",
            first_lines="neutral, present — not performing",
            mid_section="same register, no arc",
            final_line="shorter. quieter.",
            delivery_notes="receipted language — this happened, not this means",
        ),
    },
    "declaration": {
        "tempo":         "pulse",
        "emotion_curve": ["rise", "tension", "release", "float"],
        "sound": SoundDesign(
            music="breath_pulse",
            fx=["low_bass", "particles", "wind_soft"],
            mix_notes="bass bed, pulse on rhythm, fade at end",
        ),
        "voice": VoiceDirective(
            state="controlled_vulnerability",
            energy_curve=["rising", "peak", "soft_land"],
            breath="subtle",
            tempo="breath_driven",
            first_lines="quiet weight — not announcing",
            mid_section="opening, expanding — not shouting",
            final_line="land softly — the declaration does not need volume",
            delivery_notes="conviction through restraint",
        ),
    },
}


# ── Shot generation ────────────────────────────────────────────────────────────

_SHOT_TEMPLATES: dict = {
    "meditation": [
        Shot("wide",  "slow_push_in",     6, "dark room, single candle, gold dust particles drifting", "Sit with me"),
        Shot("close", "handheld_micro",   4, "hands, breath visible, soft amber light",                None),
        Shot("wide",  "drift",            5, "deep blue space, slow particle field",                   None),
        Shot("close", "static",           4, "face partially lit, breathing",                          None),
        Shot("aerial","pull_back",        6, "dissolve to black, one particle remaining",              None),
    ],
    "oracle": [
        Shot("extreme_close", "static",       3, "eye, gold iris, unfocused depth",                        None),
        Shot("wide",          "orbit",        5, "dark chamber, volumetric light column, dust",            "The record stands."),
        Shot("medium",        "slow_push_in", 4, "figure, back lit, silhouette against blue light",        None),
        Shot("close",         "drift",        5, "hands open, particles rising upward",                    None),
        Shot("wide",          "pull_back",    4, "chamber empties, light narrows to point",                None),
    ],
    "witness": [
        Shot("medium", "static",       5, "empty desk, one object, side light",       "This happened."),
        Shot("close",  "drift",        4, "object detail — receipt, hash, timestamp",  None),
        Shot("wide",   "slow_push_in", 5, "room context — window, no face",           None),
        Shot("medium", "static",       4, "back to object, slightly closer",           None),
    ],
    "declaration": [
        Shot("wide",          "slow_push_in", 5, "horizon line, deep blue, particles rising", None),
        Shot("medium",        "orbit",        4, "figure standing, back to camera",            "We built this."),
        Shot("close",         "handheld_micro", 4, "face, eyes forward, no performance",       None),
        Shot("extreme_close", "drift",        3, "lips, breath",                               None),
        Shot("wide",          "pull_back",    6, "return to horizon, figure small",            None),
    ],
}


# ── Director function (D1: deterministic) ─────────────────────────────────────

def direct(
    artifact: ExecutionArtifactV1,
    style:    str = "meditation",
) -> DirectorPlanV1:
    """
    Deterministic director: same artifact + style → same plan (D1).
    No randomness. No ambient reads. Pure function of inputs.
    """
    if style not in _STYLES:
        style = _tone_to_style(artifact.tone)

    preset  = _STYLES[style]
    shots   = _SHOT_TEMPLATES.get(style, _SHOT_TEMPLATES["meditation"])

    plan_id = sha256_hex(f"{artifact.artifact_id}:{style}")[:16]

    # Build the body for hashing (without plan_hash itself)
    body = {
        "plan_id":             plan_id,
        "source_artifact_id":  artifact.artifact_id,
        "source_receipt_hash": artifact.receipt_hash,
        "style":               style,
        "tempo":               preset["tempo"],
        "emotion_curve":       preset["emotion_curve"],
    }
    plan_hash = sha256_hex(canonical_json(body))

    return DirectorPlanV1(
        plan_id=             plan_id,
        source_artifact_id=  artifact.artifact_id,
        source_receipt_hash= artifact.receipt_hash,
        style=               style,
        tempo=               preset["tempo"],
        emotion_curve=       preset["emotion_curve"],
        shots=               shots,
        sound=               preset["sound"],
        voice=               preset["voice"],
        plan_hash=           "sha256:" + plan_hash,
        authority=           False,
    )


def _tone_to_style(tone: Tone) -> str:
    return {
        "calm":       "meditation",
        "reflective": "witness",
        "precise":    "oracle",
        "serious":    "declaration",
        "warm":       "meditation",
    }.get(tone, "meditation")
