"""
HELEN Render Contract — RENDER_REQUEST_V1 / RENDER_RECEIPT_V1

The renderer is a pure function:
  Input:  RENDER_REQUEST_V1 (typed, validated, from execution output)
  Output: RENDER_RECEIPT_V1 (media files + provenance)

No reasoning. No decisions. No state mutation.
"""
from __future__ import annotations

import hashlib
import json
import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


# ─── RENDER_REQUEST_V1 ───────────────────────────────────────────────────────

@dataclass
class Segment:
    kind: str  # "paragraph" | "title" | "quote" | "silence" | "receipt"
    text: str = ""
    duration_hint: float = 0  # seconds, 0 = auto


@dataclass
class RenderRequest:
    render_id: str
    source_artifact_type: str  # "EXECUTION_RESULT_V1" | "TEMPLE_MEDITATION" | etc
    source_artifact_hash: str  # sha256 of the source artifact
    mode: str = "video"  # "video" | "audio" | "image"
    profile: str = "helen_default"  # rendering style profile
    title: str = ""
    body: str = ""  # full text for TTS
    segments: List[Segment] = field(default_factory=list)
    voice: str = "Zephyr"
    resolution: tuple = (1080, 1920)
    fps: int = 30
    authority: str = "NONE"  # ALWAYS NONE — renderer has no authority

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "RENDER_REQUEST_V1",
            "render_id": self.render_id,
            "source_artifact_type": self.source_artifact_type,
            "source_artifact_hash": self.source_artifact_hash,
            "mode": self.mode,
            "profile": self.profile,
            "script": {
                "title": self.title,
                "body": self.body,
                "segments": [{"kind": s.kind, "text": s.text, "duration_hint": s.duration_hint} for s in self.segments],
            },
            "voice": self.voice,
            "resolution": list(self.resolution),
            "fps": self.fps,
            "authority": self.authority,
        }

    def request_hash(self) -> str:
        return _sha256(_canon(self.to_dict()))

    def validate(self) -> List[str]:
        """Validate the render request. Returns list of errors (empty = valid)."""
        errors = []
        if self.authority != "NONE":
            errors.append(f"authority must be NONE, got {self.authority}")
        if not self.render_id:
            errors.append("render_id is required")
        if not self.source_artifact_hash:
            errors.append("source_artifact_hash is required")
        if not self.body and not self.segments:
            errors.append("body or segments required (nothing to render)")
        if self.mode not in ("video", "audio", "image"):
            errors.append(f"mode must be video|audio|image, got {self.mode}")
        return errors


# ─── RENDER_RECEIPT_V1 ────────────────────────────────────────────────────────

@dataclass
class RenderReceipt:
    render_id: str
    request_hash: str
    output_files: List[Dict[str, str]]  # [{"path": "...", "sha256": "...", "type": "video|audio"}]
    voice_used: str = ""
    model_used: str = ""
    duration_seconds: float = 0
    rendered_at: str = ""
    authority: str = "NONE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "RENDER_RECEIPT_V1",
            "render_id": self.render_id,
            "request_hash": self.request_hash,
            "output_files": self.output_files,
            "voice_used": self.voice_used,
            "model_used": self.model_used,
            "duration_seconds": self.duration_seconds,
            "rendered_at": self.rendered_at or _now_utc(),
            "authority": self.authority,
        }

    def receipt_hash(self) -> str:
        return _sha256(_canon(self.to_dict()))


# ─── Render Profiles ──────────────────────────────────────────────────────────

PROFILES = {
    "helen_default": {
        "bg_color": (6, 8, 18),
        "title_color": (201, 169, 97),  # gold
        "text_color": (230, 230, 240),
        "accent_color": (34, 211, 238),  # cyan
        "dim_color": (90, 80, 120),
        "transition": "crossfade",
        "transition_duration": 2.5,
        "ken_burns": True,
        "film_grain": True,
        "letterbox": False,
    },
    "helen_meditation_soft": {
        "bg_color": (6, 8, 18),
        "title_color": (201, 169, 97),
        "text_color": (230, 230, 240),
        "accent_color": (120, 60, 180),  # violet
        "dim_color": (70, 60, 90),
        "transition": "crossfade",
        "transition_duration": 3.0,
        "ken_burns": True,
        "film_grain": True,
        "letterbox": False,
    },
    "helen_directors_cut": {
        "bg_color": (0, 0, 0),
        "title_color": (201, 169, 97),
        "text_color": (230, 230, 240),
        "accent_color": (34, 211, 238),
        "dim_color": (80, 70, 100),
        "transition": "crossfade",
        "transition_duration": 2.5,
        "ken_burns": True,
        "film_grain": True,
        "letterbox": True,
    },
}


def get_profile(name: str) -> Dict[str, Any]:
    return PROFILES.get(name, PROFILES["helen_default"])
