"""
HELEN Video Renderer — Pure function of RENDER_REQUEST_V1.

Takes a typed render request. Produces media files + receipt.
Does NOT reason, decide, or mutate state.

Pipeline:
  1. Validate RENDER_REQUEST_V1
  2. Generate TTS from script.body
  3. Generate scene images (Grok/FLUX/procedural)
  4. Render frames (Pillow + profile styling)
  5. Mux with ffmpeg
  6. Emit RENDER_RECEIPT_V1
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .contract import (
    RenderRequest, RenderReceipt, Segment,
    get_profile, _sha256, _now_utc,
)


def render_video(
    request: RenderRequest,
    output_dir: Path,
    gemini_key: str = "",
    xai_key: str = "",
    image_provider: str = "procedural",
) -> RenderReceipt:
    """
    Render a video from a RENDER_REQUEST_V1.

    Pure function: input request → output files + receipt.
    No state mutation. No ambient memory access.
    """
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance

    errors = request.validate()
    if errors:
        raise ValueError(f"Invalid render request: {errors}")

    profile = get_profile(request.profile)
    W, H = request.resolution
    FPS = request.fps

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: TTS ──
    wav_path = None
    if request.body and gemini_key:
        try:
            tts_dir = output_dir / "tts"
            tts_dir.mkdir(exist_ok=True)
            venv = Path(__file__).parents[2] / ".venv" / "bin" / "python"
            tts_script = Path(__file__).parents[2] / "oracle_town" / "skills" / "voice" / "gemini_tts" / "helen_tts.py"
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = gemini_key
            r = subprocess.run(
                [str(venv), str(tts_script), "--output-dir", str(tts_dir),
                 "--voice", request.voice, request.body],
                capture_output=True, text=True, timeout=30, env=env,
            )
            for line in r.stdout.split("\n"):
                if line.startswith("Audio:"):
                    wav_path = Path(line.split("Audio:")[-1].strip())
                    break
        except Exception as e:
            print(f"  [render] TTS error: {e}")

    # ── Step 2: Duration ──
    dur = 30.0  # default
    if wav_path and wav_path.exists():
        r = subprocess.run(
            ["ffprobe", "-i", str(wav_path), "-show_entries", "format=duration",
             "-v", "quiet", "-of", "csv=p=0"],
            capture_output=True, text=True,
        )
        try:
            dur = float(r.stdout.strip()) + 2.0
        except:
            pass

    total_frames = int(dur * FPS)

    # ── Step 3: Segments → scenes ──
    segments = request.segments or [Segment(kind="paragraph", text=request.body)]
    n_scenes = len(segments)
    scene_dur = dur / max(1, n_scenes)

    # ── Step 4: Generate frames ──
    try:
        fn_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 44)
        fn_word = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        fn_tag = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12)
    except:
        fn_title = fn_word = fn_tag = ImageFont.load_default()

    bg = profile["bg_color"]
    title_c = profile["title_color"]
    text_c = profile["text_color"]
    accent_c = profile["accent_color"]
    FADE = profile["transition_duration"]

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    random.seed(42)

    for fi in range(total_frames):
        t = fi / FPS
        img = Image.new("RGB", (W, H), bg)
        draw = ImageDraw.Draw(img)

        # Find current segment
        seg_idx = min(int(t / scene_dur), n_scenes - 1)
        seg = segments[seg_idx]
        seg_start = seg_idx * scene_dur
        seg_progress = (t - seg_start) / scene_dur

        # Background breathing glow
        pulse = 0.3 + 0.2 * math.sin(t * 0.8)
        for r in range(150, 0, -10):
            op = int(pulse * 25 * (1 - r / 150))
            c = (accent_c[0] * op // 255, accent_c[1] * op // 255, accent_c[2] * op // 255)
            draw.ellipse([W // 2 - r, H // 3 - r, W // 2 + r, H // 3 + r], fill=c)

        # Particles
        for pi in range(15):
            px = (50 + pi * 73 + int(t * 8 * (1 + pi % 3))) % W
            py = (100 + pi * 127 - int(t * 12 * (1 + pi % 2))) % H
            ps = 1 + (pi % 2)
            pc = title_c if pi % 3 == 0 else accent_c
            pa = max(0, min(255, int(80 * math.sin(t * 0.4 + pi))))
            draw.ellipse([px - ps, py - ps, px + ps, py + ps], fill=tuple(v * pa // 255 for v in pc))

        # Bottom gradient
        for gy in range(1350, H):
            op = int(160 * ((gy - 1350) / (H - 1350)) ** 1.4)
            draw.line([(0, gy), (W, gy)], fill=(0, 0, 0, op))

        # Text
        alpha = min(1.0, (t - seg_start) / 1.0)
        if t > seg_start + scene_dur - 2.0:
            alpha *= max(0, (seg_start + scene_dur - t) / 2.0)

        if seg.kind == "title":
            c = tuple(int(v * alpha) for v in title_c)
            bbox = draw.textbbox((0, 0), seg.text, font=fn_title)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2 + 1, 1501), seg.text, fill=(0, 0, 0, int(120 * alpha)), font=fn_title)
            draw.text(((W - tw) // 2, 1500), seg.text, fill=c, font=fn_title)
        elif seg.kind == "receipt":
            c = tuple(int(v * alpha) for v in accent_c)
            bbox = draw.textbbox((0, 0), seg.text, font=fn_tag)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, 1800), seg.text, fill=c, font=fn_tag)
        else:
            # Word-wrap paragraph
            words = seg.text.split()
            lines = []
            cur = ""
            for w in words:
                test = f"{cur} {w}".strip()
                if len(test) > 35 and cur:
                    lines.append(cur)
                    cur = w
                else:
                    cur = test
            if cur:
                lines.append(cur)

            for li, line in enumerate(lines):
                c = tuple(int(v * alpha) for v in text_c)
                y = 1400 + li * 45
                bbox = draw.textbbox((0, 0), line, font=fn_word)
                tw = bbox[2] - bbox[0]
                draw.text(((W - tw) // 2 + 1, y + 1), line, fill=(0, 0, 0, int(100 * alpha)), font=fn_word)
                draw.text(((W - tw) // 2, y), line, fill=c, font=fn_word)

        # Film grain
        if profile["film_grain"]:
            for _ in range(15):
                gx, gy = random.randint(0, W - 1), random.randint(0, H - 1)
                gv = random.randint(-3, 3)
                try:
                    px = img.getpixel((gx, gy))
                    img.putpixel((gx, gy), tuple(max(0, min(255, v + gv)) for v in px[:3]))
                except:
                    pass

        # Breathing
        img = ImageEnhance.Brightness(img).enhance(1.0 + 0.006 * math.sin(t * 0.5))

        # Fade from/to black
        if t < 1.5:
            img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, min(1.0, t / 1.5))
        if t > dur - 3.0:
            img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, max(0, (dur - t) / 3.0))

        img.save(frames_dir / f"frame_{fi:05d}.png")

    # ── Step 5: Mux ──
    mp4_path = output_dir / f"{request.render_id}.mp4"
    cmd = [
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
    ]
    if wav_path and wav_path.exists():
        cmd += ["-i", str(wav_path), "-c:a", "aac", "-b:a", "192k"]
    cmd += [
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
        "-shortest", str(mp4_path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=300)

    # Cleanup frames
    import shutil
    shutil.rmtree(frames_dir)

    # ── Step 6: Receipt ──
    output_files = []
    if mp4_path.exists():
        with open(mp4_path, "rb") as f:
            video_hash = hashlib.sha256(f.read()).hexdigest()
        output_files.append({"path": str(mp4_path), "sha256": video_hash, "type": "video"})

    if wav_path and wav_path.exists():
        with open(wav_path, "rb") as f:
            audio_hash = hashlib.sha256(f.read()).hexdigest()
        output_files.append({"path": str(wav_path), "sha256": audio_hash, "type": "audio"})

    receipt = RenderReceipt(
        render_id=request.render_id,
        request_hash=request.request_hash(),
        output_files=output_files,
        voice_used=request.voice,
        model_used="gemini-2.5-flash-preview-tts",
        duration_seconds=dur,
        rendered_at=_now_utc(),
    )

    # Save receipt
    receipt_path = output_dir / f"{request.render_id}.receipt.json"
    receipt_path.write_text(json.dumps(receipt.to_dict(), indent=2) + "\n")

    return receipt
