"""
HELEN Montage Engine — MONTAGE_PLAN_V1

Assembles N clips into a single film:
  - FFmpeg xfade transition chaining
  - Audio mixing (voiceover + music bed)
  - Rhythm-driven transition assignment
  - Duration-target trimming (clips trimmed to hit target)
  - Deterministic receipted output

Pipeline position:
  DirectorPlan → Clip Generation → MONTAGE_PLAN_V1 → ffmpeg → MONTAGE_RECEIPT_V1

Law: No receipt = no reality. authority: False on every receipt.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _plan_hash(plan: "MontagePlanV1") -> str:
    payload = _canonical({
        "plan_id":         plan.plan_id,
        "duration_target": plan.duration_target,
        "rhythm":          plan.rhythm,
        "clips": [
            {"src": c.src, "start": c.start, "duration": c.duration,
             "transition_out": c.transition_out}
            for c in plan.clips
        ],
        "audio": {
            "voiceover": plan.audio.voiceover,
            "music":     plan.audio.music,
        },
    })
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _probe_duration(path: str) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-i", path, "-show_entries", "format=duration",
             "-v", "quiet", "-of", "csv=p=0"],
            capture_output=True, text=True, timeout=10,
        )
        return float(r.stdout.strip())
    except Exception:
        return 8.0


# ── Transitions ────────────────────────────────────────────────────────────────

TRANSITIONS: Dict[str, Dict[str, Any]] = {
    "fade":        {"ffmpeg": "fade",        "duration": 1.0},
    "dissolve":    {"ffmpeg": "dissolve",    "duration": 1.5},
    "slideleft":   {"ffmpeg": "slideleft",   "duration": 1.0},
    "slideright":  {"ffmpeg": "slideright",  "duration": 1.0},
    "slideup":     {"ffmpeg": "slideup",     "duration": 0.8},
    "circleopen":  {"ffmpeg": "circleopen",  "duration": 1.0},
    "circleclose": {"ffmpeg": "circleclose", "duration": 1.0},
    "wipeleft":    {"ffmpeg": "wipeleft",    "duration": 0.8},
    "wiperight":   {"ffmpeg": "wiperight",   "duration": 0.8},
    "radial":      {"ffmpeg": "radial",      "duration": 1.2},
    "smoothleft":  {"ffmpeg": "smoothleft",  "duration": 1.0},
    "smoothright": {"ffmpeg": "smoothright", "duration": 1.0},
    "hard_cut":    {"ffmpeg": None,          "duration": 0.0},
}

RHYTHMS: Dict[str, List[str]] = {
    "cinematic_breath": ["fade", "dissolve", "fade", "circleopen", "fade"],
    "fast_cuts":        ["hard_cut", "hard_cut", "slideleft", "hard_cut"],
    "smooth_flow":      ["dissolve", "smoothleft", "dissolve", "smoothright"],
    "dramatic":         ["fade", "circleclose", "hard_cut", "fade", "circleopen"],
    "minimal":          ["fade", "fade", "fade"],
}


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class ClipSpec:
    src: str
    start: float = 0.0
    duration: float = 0.0          # 0 = use full clip
    transition_out: str = "fade"
    label: str = ""

    def resolve_duration(self) -> float:
        if self.duration > 0:
            return self.duration
        return _probe_duration(self.src)


@dataclass
class AudioSpec:
    voiceover: str = ""            # path to voiceover WAV/MP3
    music: str = ""                # path to music track
    music_volume: float = 0.15
    voiceover_delay: float = 1.0


@dataclass
class MontagePlanV1:
    plan_id: str
    duration_target: float
    clips: List[ClipSpec]
    audio: AudioSpec
    rhythm: str
    resolution: tuple = (1920, 1080)
    fps: int = 30
    authority: bool = False

    def __post_init__(self) -> None:
        if self.authority:
            raise ValueError("MontagePlanV1.authority must be False")

    @property
    def plan_hash(self) -> str:
        return _plan_hash(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type":            "MONTAGE_PLAN_V1",
            "plan_id":         self.plan_id,
            "duration_target": self.duration_target,
            "rhythm":          self.rhythm,
            "clips": [
                {"src": c.src, "start": c.start, "duration": c.duration,
                 "transition_out": c.transition_out, "label": c.label}
                for c in self.clips
            ],
            "audio": {
                "voiceover":        self.audio.voiceover,
                "music":            self.audio.music,
                "music_volume":     self.audio.music_volume,
                "voiceover_delay":  self.audio.voiceover_delay,
            },
            "authority": False,
        }


# ── Plan builder ───────────────────────────────────────────────────────────────

def build_montage_plan(
    clips: List[str | ClipSpec],
    duration_target: float = 30.0,
    voiceover: str = "",
    music: str = "",
    music_volume: float = 0.15,
    rhythm: str = "cinematic_breath",
    plan_id: str = "",
    labels: Optional[List[str]] = None,
) -> MontagePlanV1:
    """
    Build a MONTAGE_PLAN_V1 from clip paths or ClipSpec objects.

    Assigns rhythm transitions and trims clip durations to hit duration_target.
    Clips that exist on disk are probed; missing clips get a default 8s duration.
    """
    if not plan_id:
        src_list = [c if isinstance(c, str) else c.src for c in clips]
        plan_id = "mp_" + hashlib.sha256("".join(src_list).encode()).hexdigest()[:12]

    trans_cycle = RHYTHMS.get(rhythm, RHYTHMS["cinematic_breath"])
    n = len(clips)

    # Normalise to ClipSpec
    specs: List[ClipSpec] = []
    for i, c in enumerate(clips):
        if isinstance(c, ClipSpec):
            specs.append(c)
        else:
            specs.append(ClipSpec(
                src=c,
                transition_out=trans_cycle[i % len(trans_cycle)],
                label=labels[i] if labels and i < len(labels) else Path(c).stem,
            ))

    # Assign transitions (override only if not already set by caller)
    for i, spec in enumerate(specs):
        if spec.transition_out == "fade":          # still default — assign from rhythm
            spec.transition_out = trans_cycle[i % len(trans_cycle)]

    # Compute total transition overhead
    def _trans_dur(idx: int) -> float:
        if idx >= n - 1:
            return 0.0
        t = TRANSITIONS.get(specs[idx].transition_out, TRANSITIONS["fade"])
        return t["duration"]

    trans_total = sum(_trans_dur(i) for i in range(n - 1))

    # Time budget available for clip content
    content_budget = duration_target + trans_total  # overlap is reclaimed
    per_clip = content_budget / n if n else duration_target

    for spec in specs:
        if spec.duration == 0:
            spec.duration = round(per_clip, 2)

    return MontagePlanV1(
        plan_id=plan_id,
        duration_target=duration_target,
        clips=specs,
        audio=AudioSpec(
            voiceover=voiceover,
            music=music,
            music_volume=music_volume,
        ),
        rhythm=rhythm,
    )


# ── Render stub (no ffmpeg) ────────────────────────────────────────────────────

def render_montage_stub(plan: MontagePlanV1, output_path: str) -> Dict[str, Any]:
    """Hash-only render for CI / tests — no subprocess, no ffmpeg."""
    payload = _canonical(plan.to_dict())
    video_hash = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    return {
        "type":        "MONTAGE_RECEIPT_V1",
        "plan_id":     plan.plan_id,
        "plan_hash":   plan.plan_hash,
        "clip_count":  len(plan.clips),
        "duration":    plan.duration_target,
        "rhythm":      plan.rhythm,
        "output_path": output_path,
        "video_hash":  video_hash,
        "rendered_at": _now_utc(),
        "stub":        True,
        "success":     True,
        "authority":   False,
    }


# ── Real render (ffmpeg) ───────────────────────────────────────────────────────

def render_montage(
    plan: MontagePlanV1,
    output_path: str,
    timeout: int = 600,
) -> Dict[str, Any]:
    """
    Render a MONTAGE_PLAN_V1 to MP4 using ffmpeg xfade.

    Returns a MONTAGE_RECEIPT_V1 with sha256 of every input and output.
    """
    W, H = plan.resolution
    n = len(plan.clips)

    # ── Build input flags ──────────────────────────────────────────────────────
    inputs: List[str] = []
    for clip in plan.clips:
        inputs += ["-i", clip.src]

    # ── Build filter_complex: scale + trim + xfade chain ──────────────────────
    filters: List[str] = []

    for i, clip in enumerate(plan.clips):
        trim = ""
        if clip.start > 0 or clip.duration > 0:
            s = clip.start
            d = clip.duration if clip.duration > 0 else 999.0
            trim = f",trim=start={s}:duration={d},setpts=PTS-STARTPTS"
        filters.append(
            f"[{i}:v]settb=AVTB,fps={plan.fps},"
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2{trim}[v{i}]"
        )

    # Chain xfade (or concat for hard cuts)
    if n == 1:
        filters.append("[v0]null[vout]")
    else:
        offset = 0.0
        prev = "v0"
        for i in range(1, n):
            prev_clip = plan.clips[i - 1]
            src_dur = prev_clip.duration if prev_clip.duration > 0 else _probe_duration(prev_clip.src)
            trans = TRANSITIONS.get(prev_clip.transition_out, TRANSITIONS["fade"])
            tag = f"x{i}" if i < n - 1 else "vout"

            if trans["ffmpeg"] is None:
                offset += src_dur
                filters.append(f"[{prev}][v{i}]concat=n=2:v=1:a=0[{tag}]")
            else:
                offset += src_dur - trans["duration"]
                filters.append(
                    f"[{prev}][v{i}]xfade=transition={trans['ffmpeg']}:"
                    f"duration={trans['duration']}:offset={offset:.3f}[{tag}]"
                )
            prev = tag

    filter_str = ";\n    ".join(filters)

    # ── Audio mixing ───────────────────────────────────────────────────────────
    audio_filters: List[str] = []
    audio_inputs: List[str] = []
    audio_idx = n

    if plan.audio.voiceover and os.path.exists(plan.audio.voiceover):
        inputs += ["-i", plan.audio.voiceover]
        delay_ms = int(plan.audio.voiceover_delay * 1000)
        audio_filters.append(
            f"[{audio_idx}:a]adelay={delay_ms}|{delay_ms},volume=1.5[vo]"
        )
        audio_inputs.append("[vo]")
        audio_idx += 1

    if plan.audio.music and os.path.exists(plan.audio.music):
        inputs += ["-i", plan.audio.music]
        audio_filters.append(f"[{audio_idx}:a]volume={plan.audio.music_volume}[mus]")
        audio_inputs.append("[mus]")

    if audio_inputs:
        filter_str += ";\n    " + ";\n    ".join(audio_filters)
        mix_n = len(audio_inputs)
        filter_str += (
            f";\n    {''.join(audio_inputs)}"
            f"amix=inputs={mix_n}:duration=longest:dropout_transition=3[aout]"
        )
        map_args = ["-map", "[vout]", "-map", "[aout]"]
        audio_enc = ["-c:a", "aac", "-b:a", "192k"]
    else:
        map_args = ["-map", "[vout]"]
        audio_enc = ["-an"]

    cmd = (
        ["ffmpeg", "-y"] + inputs
        + ["-filter_complex", filter_str]
        + map_args
        + ["-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p"]
        + audio_enc
        + [output_path]
    )

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    # ── Build receipt ──────────────────────────────────────────────────────────
    input_hashes: Dict[str, str] = {}
    for clip in plan.clips:
        if os.path.exists(clip.src):
            input_hashes[clip.label or Path(clip.src).stem] = _sha256_file(clip.src)

    if plan.audio.voiceover and os.path.exists(plan.audio.voiceover):
        input_hashes["voiceover"] = _sha256_file(plan.audio.voiceover)

    video_hash = ""
    output_size_kb = 0
    if os.path.exists(output_path):
        video_hash = _sha256_file(output_path)
        output_size_kb = os.path.getsize(output_path) // 1024

    receipt: Dict[str, Any] = {
        "type":         "MONTAGE_RECEIPT_V1",
        "plan_id":      plan.plan_id,
        "plan_hash":    plan.plan_hash,
        "clip_count":   n,
        "duration":     plan.duration_target,
        "rhythm":       plan.rhythm,
        "output_path":  output_path,
        "video_hash":   video_hash,
        "input_hashes": input_hashes,
        "rendered_at":  _now_utc(),
        "stub":         False,
        "success":      result.returncode == 0,
        "authority":    False,
    }

    if result.returncode == 0:
        receipt["output_size_kb"] = output_size_kb
    else:
        receipt["error"] = result.stderr[-800:] if result.stderr else "unknown ffmpeg error"

    return receipt
