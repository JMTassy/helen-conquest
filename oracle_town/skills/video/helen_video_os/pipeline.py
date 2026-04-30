"""
HELEN VIDEO OS — Autonomous Cinematic Intelligence Pipeline
Non-sovereign. No ledger writes. Outputs: mp4 artifacts + Telegram delivery.
"""
from __future__ import annotations
import subprocess, os, random, json, time, math, requests, wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────
W, H   = 720, 1280          # canonical portrait frame
FPS    = 24
SW, SH = 580, 326           # screen embed area (16:9)
SX     = (W - SW) // 2
SY     = 280
BEZEL  = 18

Mode = Literal["slow","medium","fast","flash"]

# ── Project State ──────────────────────────────────────────────────────────────
@dataclass
class VideoState:
    project_id: str
    footage_pool: list[dict]         # {path, duration, tags, orientation}
    audio_pool:   list[dict]         # {path, type: music|voice|fx}
    best_score:   float = 0.0
    best_output:  Optional[Path] = None
    epoch:        int = 0
    history:      list[dict] = field(default_factory=list)

# ── I. INITIALIZE ──────────────────────────────────────────────────────────────
def initialize_project(footage_dir: str = "~/Downloads",
                       audio_dir: str   = "artifacts/audio") -> VideoState:
    footage_pool = []
    for name, tags, orient in [
        ("grok-video-b5f928bb-e53e-4ad1-90cb-0929a0e61eb9.mp4",
            ["helen","portrait","night","street"], "portrait"),
        ("hf_20260424_151853_10244b74-4383-45a0-858c-cb6ef7e59bfd.mp4",
            ["helen","portrait","cinematic"], "portrait"),
        ("hf_20260427_175306_a7e78498-2b27-445c-b582-730e5cab60e1.mp4",
            ["helen","landscape","cinematic"], "landscape"),
        ("hf_20260424_220138_b4513ff7-1e06-414e-925f-fe275e3adbcc.mp4",
            ["helen","landscape","close"], "landscape"),
        ("unripple_festival_song.mp4",
            ["helen","portrait","water","anomaly"], "portrait"),
        ("GHA.mp4",   ["helen","landscape","agentic","long"], "landscape"),
        ("GHA_1.mp4", ["helen","landscape","agentic","long"], "landscape"),
    ]:
        p = Path(os.path.expanduser(footage_dir)) / name
        if not p.exists(): continue
        r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","csv=p=0",str(p)], capture_output=True, text=True)
        try: dur = float(r.stdout.strip())
        except: dur = 10.0
        footage_pool.append({"path": str(p), "duration": dur,
                              "tags": tags, "orientation": orient})

    audio_pool = []
    music = Path(os.path.expanduser("~/Downloads/DUB of new wave Paris.mp3"))
    if music.exists():
        audio_pool.append({"path": str(music), "type": "music"})
    music2 = Path(os.path.expanduser(
        "~/Music/Music/Media.localized/Music/agentxxx/Unknown Album/Keep On Dreaming.mp3"))
    if music2.exists():
        audio_pool.append({"path": str(music2), "type": "music"})

    for wav in sorted(Path(audio_dir).glob("*__zephyr.wav"))[-6:]:
        audio_pool.append({"path": str(wav), "type": "voice"})

    return VideoState(
        project_id = f"HELEN_{int(time.time())}",
        footage_pool = footage_pool,
        audio_pool   = audio_pool,
    )

# ── II. TIMELINE GENERATOR ──────────────────────────────────────────────────────
def generate_timeline(state: VideoState, total_target: float = 90.0) -> list[dict]:
    """Narrative rhythm: intro → build → push → climax → landing."""
    structure = [
        ("intro",   0.15, "slow"),
        ("build",   0.30, "medium"),
        ("push",    0.25, "fast"),
        ("climax",  0.15, "flash"),
        ("landing", 0.15, "slow"),
    ]
    timeline = []
    for act, frac, mode in structure:
        act_dur = total_target * frac
        t = 0.0
        while t < act_dur - 1.0:
            d = shot_duration(mode)
            timeline.append({"act": act, "mode": mode, "duration": min(d, act_dur - t)})
            t += d
    return timeline

def shot_duration(mode: Mode) -> float:
    if mode == "slow":   return random.uniform(6.0, 9.0)
    if mode == "medium": return random.uniform(3.5, 5.5)
    if mode == "fast":   return random.uniform(2.0, 3.5)
    if mode == "flash":  return random.uniform(1.0, 2.0)
    return 4.0

# ── III. SHOT SELECTOR ──────────────────────────────────────────────────────────
def select_clips(timeline: list[dict], pool: list[dict]) -> list[dict]:
    """Assign footage to each timeline slot. Balance portrait/landscape."""
    portrait = [f for f in pool if f["orientation"] == "portrait"]
    landscape= [f for f in pool if f["orientation"] == "landscape"]
    clips = []
    for slot in timeline:
        # slow/intro → prefer portrait for visual weight; flash → any
        if slot["mode"] in ("slow","medium"):
            src = random.choice(portrait if portrait else pool)
        else:
            src = random.choice(pool)
        max_start = max(0.0, src["duration"] - slot["duration"] - 0.5)
        start = random.uniform(0.0, max_start)
        clips.append({**slot, "src": src["path"],
                      "start": start, "orientation": src["orientation"]})
    return clips

# ── IV. DYNAMIC FILTER GRAPH ────────────────────────────────────────────────────
def build_filter_complex(clips: list[dict], abyme: bool = True,
                         abyme_src: Optional[str] = None) -> str:
    """
    Build ffmpeg filter_complex string.
    Input indices: 0..N-1 = clips, N = bezel.png (if abyme), N+1 = bezel (otherwise skip)
    Returns filter string + output pad name.
    """
    n = len(clips)
    bezel_idx = n  # bezel PNG is last input

    parts = []

    # Base: first clip as background
    parts.append(f"[0:v]scale={W}:{H},fps={FPS},"
                 "eq=brightness=0.02:contrast=1.08:saturation=1.12,"
                 "colorbalance=rs=0.06:gs=-0.02:bs=-0.04[v0]")

    # Chain remaining clips as overlays (hard cut via concat is separate)
    # Actually: each clip becomes its own stream, concat handles the timeline
    # The filter_complex here is for SPATIAL compositing (mise en abyme)
    # Temporal cuts are handled by pre-extracted clip files + ffmpeg concat

    # Grade each clip
    for i in range(1, n):
        parts.append(f"[{i}:v]scale={W}:{H},fps={FPS},"
                     f"eq=brightness=0.02:contrast=1.08:saturation=1.12,"
                     f"colorbalance=rs=0.06:gs=-0.02:bs=-0.04[v{i}]")

    # If mise en abyme: embed one landscape clip as a screen inside the first clip
    if abyme and abyme_src is not None:
        # abyme_src is input index n (separate input)
        parts.append(
            f"[{n}:v]scale={SW}:{SH},fps={FPS},"
            "geq=lum='if(mod(Y\\,2)\\,p(X\\,Y)\\,p(X\\,Y)*0.82)':cb='cb(X\\,Y)':cr='cr(X\\,Y)'"
            "[abyme_raw]"
        )
        parts.append("[abyme_raw]gblur=sigma=6[abyme_glow]")
        parts.append(f"[v0][abyme_glow]overlay={SX-4}:{SY-4}[v0_glow]")
        parts.append(f"[v0_glow][abyme_raw]overlay={SX}:{SY}[v0_screen]")
        bezel_idx = n + 1
        parts.append(f"[v0_screen][{bezel_idx}:v]overlay=0:0[v0_final]")
        chain_start = "v0_final"
    else:
        chain_start = "v0"

    return ";".join(parts), chain_start, bezel_idx

# ── V. EXTRACT CLIPS ────────────────────────────────────────────────────────────
def extract_clips(clips: list[dict], workdir: Path) -> list[Path]:
    paths = []
    for i, c in enumerate(clips):
        out = workdir / f"clip_{i:03d}.mp4"
        subprocess.run([
            "ffmpeg","-y","-ss",str(c["start"]),"-i",c["src"],
            "-t",str(c["duration"]),
            "-vf",
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,fps={FPS},"
            "eq=brightness=0.02:contrast=1.08:saturation=1.12,"
            "colorbalance=rs=0.06:gs=-0.02:bs=-0.04",
            "-c:v","libx264","-crf","20","-pix_fmt","yuv420p","-an",str(out)
        ], capture_output=True)
        if out.exists() and out.stat().st_size > 5000:
            paths.append(out)
    return paths

# ── VI. RENDER ──────────────────────────────────────────────────────────────────
def render(state: VideoState, clips: list[dict], workdir: Path,
           abyme: bool = True) -> Optional[Path]:
    from PIL import Image, ImageDraw

    extracted = extract_clips(clips, workdir)
    if not extracted:
        return None

    # Concat silent
    cl = workdir / "concat.txt"
    cl.write_text("\n".join(f"file '{p}'" for p in extracted))
    silent = workdir / "silent.mp4"
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(cl),
        "-c","copy",str(silent)], capture_output=True)

    dur = float(subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(silent)],
        capture_output=True, text=True).stdout.strip() or "90")

    # Generate bezel
    bezel_path = workdir / "bezel.png"
    _draw_bezel(bezel_path)

    # Music
    music = next((a for a in state.audio_pool if a["type"]=="music"), None)
    # Voice beats
    voices = [a for a in state.audio_pool if a["type"]=="voice"][-3:]

    out = workdir / "output.mp4"

    inputs = ["-i", str(silent)]
    if music: inputs += ["-i", music["path"]]
    for v in voices: inputs += ["-i", v["path"]]

    mi = 1  # music input index
    vi_start = 2  # voice inputs start
    n_voices = len(voices)

    voice_parts = []
    for j, beat_t in enumerate([3, dur*0.45, dur*0.82]):
        if j >= n_voices: break
        idx = vi_start + j
        ms  = int(beat_t * 1000)
        end = min(beat_t + 8, dur)
        voice_parts.append(
            f"[{idx}:a]adelay={ms}|{ms},afade=t=in:st=0:d=0.3,"
            f"afade=t=out:st={end-beat_t-1:.1f}:d=1.5,volume=1.8[vc{j}]"
        )

    music_part = (f"[{mi}:a]afade=t=in:st=0:d=2,afade=t=out:st={dur-6:.1f}:d=5,"
                  "volume=0.58[music]") if music else ""

    all_parts  = ([music_part] if music_part else []) + voice_parts
    mix_inputs = (["[music]"] if music_part else []) + [f"[vc{j}]" for j in range(len(voice_parts))]
    n_mix      = len(mix_inputs)
    mix        = f"{''.join(mix_inputs)}amix=inputs={n_mix}:duration=longest[aout]"
    filter_str = ";".join(all_parts + [mix])

    if abyme:
        # Pick a landscape source for the embedded screen
        landscape = next(
            (f for f in state.footage_pool if f["orientation"]=="landscape"), None
        )
        if landscape:
            abyme_input = ["-stream_loop","-1","-i", landscape["path"]]
            # Simple abyme via two-pass: first burn screen into silent, then add audio
            screen_burn = workdir / "screen_burn.mp4"
            r = subprocess.run([
                "ffmpeg","-y",
                "-i",str(silent),
                "-stream_loop","-1","-i",landscape["path"],
                "-i",str(bezel_path),
                "-filter_complex",
                f"[0:v][1:v]overlay=0:0[tmp];"   # placeholder base
                f"[1:v]scale={SW}:{SH},fps={FPS},"
                "geq=lum='if(mod(Y\\,2)\\,p(X\\,Y)\\,p(X\\,Y)*0.82)':cb='cb(X\\,Y)':cr='cr(X\\,Y)'[sc_raw];"
                "[sc_raw]gblur=sigma=5[sc_glow];"
                f"[0:v][sc_glow]overlay={SX-4}:{SY-4}[bg_g];"
                f"[bg_g][sc_raw]overlay={SX}:{SY}[bg_s];"
                "[bg_s][2:v]overlay=0:0[out]",
                "-map","[out]","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
                "-t",str(dur),str(screen_burn)
            ], capture_output=True, text=True)
            if screen_burn.exists() and screen_burn.stat().st_size > 10000:
                silent = screen_burn  # use abyme version

    # Mux with audio
    cmd = ["ffmpeg","-y","-i",str(silent)] + (
        ["-i",music["path"]] if music else []
    ) + ["-i",str(v["path"]) for v in voices]
    cmd += ["-filter_complex", filter_str,
            "-map","0:v","-map","[aout]",
            "-c:v","libx264","-crf","20","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","192k","-t",str(dur), str(out)]
    subprocess.run(cmd, capture_output=True)
    return out if (out.exists() and out.stat().st_size > 10000) else None

def _draw_bezel(path: Path):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, H), (0,0,0,0))
    d   = ImageDraw.Draw(img)
    bx0, by0 = SX-BEZEL, SY-BEZEL
    bx1, by1 = SX+SW+BEZEL, SY+SH+BEZEL
    d.rounded_rectangle([bx0,by0,bx1,by1], radius=14,
        fill=(22,22,30,235), outline=(60,200,240,180), width=2)
    d.rounded_rectangle([SX-2,SY-2,SX+SW+2,SY+SH+2], radius=3,
        fill=None, outline=(40,180,220,200), width=2)
    for r in range(28,0,-4):
        alpha = int(50*(1-r/28))
        d.rounded_rectangle([SX-BEZEL-r,SY-BEZEL-r,SX+SW+BEZEL+r,SY+SH+BEZEL+r],
            radius=14+r, fill=None, outline=(40,160,255,alpha), width=2)
    d.rectangle([bx0-40,by1+2,bx1+40,by1+10], fill=(30,30,40,180))
    img.save(path)

# ── VII. COHERENCE EVALUATOR (Σ-SEED) ──────────────────────────────────────────
def evaluate_video(output: Path, clips: list[dict]) -> float:
    """
    Simple coherence score [0,1]:
    - rhythm_score: cut variance (lower variance = higher score)
    - visual_score: portrait-dominant = better for mobile
    - diversity: variety of sources used
    """
    if not output or not output.exists():
        return 0.0

    durations   = [c["duration"] for c in clips]
    mean_d      = sum(durations) / len(durations)
    variance    = sum((d - mean_d)**2 for d in durations) / len(durations)
    rhythm_score = 1.0 / (1.0 + math.sqrt(variance) / mean_d)

    portrait_ratio = sum(1 for c in clips if c["orientation"] == "portrait") / len(clips)
    visual_score   = 0.4 + 0.6 * portrait_ratio

    sources      = len(set(c["src"] for c in clips))
    diversity    = min(1.0, sources / 4.0)

    total = 0.4*rhythm_score + 0.4*visual_score + 0.2*diversity
    return round(total, 4)

# ── VIII. MAIN PIPELINE ─────────────────────────────────────────────────────────
def HELEN_VIDEO_PIPELINE(n_epochs: int = 3, target_duration: float = 90.0,
                          abyme: bool = True, send_best: bool = True) -> Optional[Path]:
    state   = initialize_project()
    workdir = Path(f"/tmp/helen_temple/helen_video_os_{state.project_id}")
    workdir.mkdir(parents=True, exist_ok=True)

    print(f"HELEN_VIDEO_OS · {state.project_id}")
    print(f"Footage: {len(state.footage_pool)} sources · Audio: {len(state.audio_pool)} tracks")
    print(f"Running {n_epochs} epochs · target {target_duration:.0f}s · abyme={abyme}\n")

    for epoch in range(n_epochs):
        epoch_dir = workdir / f"epoch_{epoch:02d}"
        epoch_dir.mkdir(exist_ok=True)

        timeline = generate_timeline(state, total_target=target_duration)
        clips    = select_clips(timeline, state.footage_pool)
        output   = render(state, clips, epoch_dir, abyme=abyme)
        score    = evaluate_video(output, clips)

        print(f"  Epoch {epoch}: {len(clips)} clips · score={score:.4f} · "
              f"{'NEW BEST ✓' if score > state.best_score else 'no improvement'}")

        state.history.append({"epoch": epoch, "score": score,
                               "n_clips": len(clips), "path": str(output)})

        if score > state.best_score:
            state.best_score  = score
            state.best_output = output

        state.epoch = epoch + 1

    (workdir / "run_log.json").write_text(json.dumps(state.history, indent=2))

    if send_best and state.best_output:
        _send_telegram(state.best_output, state)

    return state.best_output

def _send_telegram(path: Path, state: VideoState):
    import os
    token = os.environ.get("TELEGRAM_BOT_TOKEN","")
    if not token: return
    # Compress if needed
    sz = path.stat().st_size // 1024
    upload = path
    if sz > 45000:
        comp = path.parent / "tg_compressed.mp4"
        subprocess.run(["ffmpeg","-y","-i",str(path),"-c:v","libx264","-crf","26",
            "-maxrate","2.4M","-bufsize","4M","-pix_fmt","yuv420p",
            "-c:a","aac","-b:a","128k",str(comp)], capture_output=True)
        upload = comp

    caption = (
        f"HELEN VIDEO OS · {state.project_id}\n"
        f"{state.epoch} epochs · best score {state.best_score:.3f} · abyme=True\n\n"
        "Système cinématographique autonome.\n"
        "HELEN evolves audiovisual states toward maximal coherence."
    )
    with open(upload,"rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendVideo",
            data={"chat_id":"6624890918","caption":caption},
            files={"video":(upload.name,f,"video/mp4")},
            timeout=300
        )
    print(f"  Telegram: {r.status_code} msg={r.json().get('result',{}).get('message_id')}")


if __name__ == "__main__":
    import sys
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    HELEN_VIDEO_PIPELINE(n_epochs=epochs, target_duration=90.0, abyme=True)
