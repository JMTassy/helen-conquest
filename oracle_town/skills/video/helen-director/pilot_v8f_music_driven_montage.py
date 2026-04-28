#!/usr/bin/env python3
"""
HELEN Director — Pilot 8F: Music-Driven Energy Montage.
NON_SOVEREIGN. $0 — ffmpeg only on existing footage + music bed.

Music: "From Toronto to Tokyo : The Global Hackathon" by agentxxx (182s)
Use first 60s of song. Visual energy curve maps to music's natural arc:

  PHASE 1  INTRO    0-15s   low energy     single sustained 8A portrait, slow zoom
  PHASE 2  BUILD    15-30s  rising         Pilot 5 palindrome (5s fwd + 5s rev + 5s fwd)
  PHASE 3  PEAK     30-45s  max energy     rapid cuts: v3 iris(2.5s) → shot4(2.5s) →
                                              shot5(2.5s) → 8B(2.5s) → v3(2.5s) → shot4(2.5s)
  PHASE 4  RESOLVE  45-60s  falling        slow fade-through 8A presence, ending on still

Voice beats:
  t=02.0   "I am here."     (over INTRO)
  t=37.0   "I see."         (over PEAK)
  t=58.0   "One source."    (over RESOLVE final 2s)

Cuts respect music phase boundaries (every 15s = major energy shift).
PEAK section uses 6 × 2.5s cuts → fast rhythm matches expected drop in pop song.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path("/tmp/helen_pilot_8f")
OUT.mkdir(parents=True, exist_ok=True)
SEGS = OUT / "segments"
SEGS.mkdir(exist_ok=True)
VOICE_DIR = OUT / "voice"
VOICE_DIR.mkdir(exist_ok=True)

CHAT_ID = 6624890918

# Sources
MUSIC = Path("/Users/jean-marietassy/Desktop/The Global AI Hackathon .mp3")
SRC_8A    = Path("/tmp/helen_temple/PILOT_8A_v3_COMPRESSED.mp4")
SRC_5     = Path("/tmp/helen_temple/pilot5_916__20260428_170718.mp4")
SRC_V3    = Path("/tmp/helen_render_pilot_v3/pilot_v3.mp4")
SRC_8B    = Path("/tmp/helen_temple/PILOT_8B_CANONICAL_HELEN_30S_PRESENCE_916__20260428_205358.mp4")
SRC_SHOT4 = Path("/tmp/helen_teaser_60s/shots/shot4_eye_contact.mp4")
SRC_SHOT5 = Path("/tmp/helen_teaser_60s/shots/shot5_climax.mp4")

env: dict[str, str] = {}
helen_env = Path.home() / ".helen_env"
for ln in helen_env.read_text().splitlines():
    ln = ln.strip()
    if ln.startswith("export "):
        ln = ln[7:]
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
TELEGRAM_BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_KEY = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")

if not TELEGRAM_BOT_TOKEN:
    sys.exit("FAIL: TELEGRAM_BOT_TOKEN missing")

for src in (MUSIC, SRC_8A, SRC_5, SRC_V3, SRC_8B, SRC_SHOT4, SRC_SHOT5):
    if not src.exists():
        sys.exit(f"FAIL: missing source {src}")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def normalize(src: Path, dst: Path, start: float = 0, dur: float = 5,
              reverse: bool = False, slow_factor: float = 1.0) -> bool:
    """Scale+crop to 1080×1920 24fps. Optional reverse + slow."""
    vf_parts = [
        "scale=1080:1920:force_original_aspect_ratio=increase",
        "crop=1080:1920",
        "setsar=1",
    ]
    if reverse:
        vf_parts.append("reverse")
    if slow_factor != 1.0:
        vf_parts.append(f"setpts={slow_factor}*PTS")
    vf_parts.append("fps=24")
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-i", str(src), "-t", str(dur),
        "-vf", ",".join(vf_parts), "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-an", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    fail {dst.name}: {e.stderr[-300:]}")
        return False


def render_voice(text: str, slug: str) -> Path | None:
    """Generate one Zephyr clip via helen_tts.py. Returns wav path or None on fail."""
    if not GEMINI_KEY:
        return None
    out_path = VOICE_DIR / f"{slug}.wav"
    helen_tts = REPO / "oracle_town" / "skills" / "voice" / "gemini_tts" / "helen_tts.py"
    venv_py = REPO / ".venv" / "bin" / "python"  # CORRECT: parents[3] = repo
    tmp_dir = OUT / f"voice_tmp_{slug}"
    tmp_dir.mkdir(exist_ok=True)
    e = os.environ.copy()
    e["GEMINI_API_KEY"] = GEMINI_KEY
    try:
        result = subprocess.run(
            [str(venv_py), str(helen_tts), "--output-dir", str(tmp_dir), text],
            capture_output=True, text=True, timeout=60, env=e,
        )
        if result.returncode != 0:
            print(f"    voice {slug} fail: {result.stderr[-200:]}")
            return None
        for line in result.stdout.splitlines():
            if line.startswith("Audio:"):
                wav_src = Path(line.split("Audio:", 1)[1].strip())
                if wav_src.exists():
                    wav_src.rename(out_path)
                    return out_path
    except Exception as e2:
        print(f"    voice {slug} exception: {e2}")
    return None


VOICE_BEATS = [
    {"slug": "v_intro",  "text": "I am here.",   "delay_ms":  2000},
    {"slug": "v_peak",   "text": "I see.",       "delay_ms": 37000},
    {"slug": "v_outro",  "text": "One source.",  "delay_ms": 58000},
]


# Segment specs: (name, src, start, dur, reverse, slow_factor)
# Total = 60s
PHASE_1_INTRO = [
    ("01_intro_8a",       SRC_8A, 0,  15, False, 1.0),
]
PHASE_2_BUILD = [
    ("02_build_p5_fwd",   SRC_5,  0,   5, False, 1.0),
    ("03_build_p5_rev",   SRC_5,  0,   5, True,  1.0),
    ("04_build_p5_fwd",   SRC_5,  0,   5, False, 1.0),
]
PHASE_3_PEAK = [
    ("05_peak_v3",        SRC_V3,    0, 2.5, False, 1.0),
    ("06_peak_shot4",     SRC_SHOT4, 0, 2.5, False, 1.0),
    ("07_peak_shot5",     SRC_SHOT5, 0, 2.5, False, 1.0),
    ("08_peak_8b",        SRC_8B,    0, 2.5, False, 1.0),
    ("09_peak_v3_rev",    SRC_V3,    0, 2.5, True,  1.0),
    ("10_peak_shot4_rev", SRC_SHOT4, 0, 2.5, True,  1.0),
]
PHASE_4_RESOLVE = [
    ("11_resolve_8a_slow", SRC_8A, 14, 7.5, False, 2.0),  # 7.5s slow → 15s output
]
ALL_SEGS = PHASE_1_INTRO + PHASE_2_BUILD + PHASE_3_PEAK + PHASE_4_RESOLVE


def concat_segments(segs: list[Path], dst: Path) -> bool:
    list_path = OUT / "concat_list.txt"
    list_path.write_text("\n".join(f"file '{p}'" for p in segs))
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path),
        "-c:v", "libx264", "-crf", "21", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-an", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    concat fail: {e.stderr[-300:]}")
        return False


def mix_audio(video_silent: Path, music: Path, voice_paths: list[Path | None],
              dst: Path, music_volume: float = 0.7, voice_volume: float = 1.4) -> bool:
    """Overlay music + voice beats onto silent video. Music ducks slightly under voice."""
    inputs = ["-i", str(video_silent), "-i", str(music)]
    voice_inputs = []
    for vp in voice_paths:
        if vp is not None and vp.exists():
            voice_inputs.append(vp)

    for vp in voice_inputs:
        inputs += ["-i", str(vp)]

    # Audio chain: video[no audio] + music(trimmed to 60s) + voice beats with adelay
    fc_parts = [
        f"[1:a]atrim=0:60,asetpts=PTS-STARTPTS,volume={music_volume}[music]",
    ]
    voice_labels = []
    for i, vp in enumerate(voice_inputs):
        beat = VOICE_BEATS[i] if i < len(VOICE_BEATS) else {"delay_ms": 0}
        idx = 2 + i  # input idx (0=video, 1=music, 2..=voices)
        d = beat["delay_ms"]
        fc_parts.append(f"[{idx}:a]adelay={d}|{d},volume={voice_volume}[v{i}]")
        voice_labels.append(f"[v{i}]")

    if voice_labels:
        mix_inputs = "[music]" + "".join(voice_labels)
        n = 1 + len(voice_labels)
        fc_parts.append(f"{mix_inputs}amix=inputs={n}:duration=first:dropout_transition=0[a]")
    else:
        fc_parts.append("[music]anull[a]")

    fc = ";".join(fc_parts)
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", fc,
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    mix fail: {e.stderr[-500:]}")
        return False


def telegram_send(mp4: Path, caption: str) -> int:
    print(f"[8] Telegram sendVideo ({mp4.stat().st_size/1024:.0f} KB)...")
    result = subprocess.run(
        ["curl", "-s", "-X", "POST",
         f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo",
         "-F", f"chat_id={CHAT_ID}",
         "-F", f"video=@{mp4}",
         "-F", f"caption={caption}"],
        capture_output=True, text=True, timeout=300,
    )
    try:
        tg = json.loads(result.stdout)
    except Exception:
        sys.exit(f"FAIL telegram parse: {result.stdout[:400]}")
    if not tg.get("ok"):
        sys.exit(f"FAIL telegram: {result.stdout[:400]}")
    msg_id = tg["result"]["message_id"]
    print(f"    OK msg_id={msg_id}")
    return msg_id


def main() -> int:
    print(f"=== HELEN Director — Pilot 8F — Music-Driven Energy Montage ===")
    print(f"Music:  {MUSIC.name} (60s of 182s used)")
    print(f"Phases: INTRO 15s · BUILD 15s · PEAK 15s · RESOLVE 15s")
    print(f"Cost:   $0 (ffmpeg only)")
    print()

    # Phase A: build all segments
    print(f"[1] Building {len(ALL_SEGS)} segments...")
    seg_paths = []
    for name, src, start, dur, rev, slow in ALL_SEGS:
        dst = SEGS / f"{name}.mp4"
        ok = normalize(src, dst, start=start, dur=dur, reverse=rev, slow_factor=slow)
        if not ok:
            sys.exit(f"FAIL: segment {name}")
        seg_paths.append(dst)
        print(f"    [{name}] {dst.stat().st_size/1024:.0f} KB")

    # Phase B: voice in parallel
    print(f"[2] Generating {len(VOICE_BEATS)} Zephyr voice beats in parallel...")
    voice_results: dict[str, Path | None] = {}

    def _voice(beat):
        voice_results[beat["slug"]] = render_voice(beat["text"], beat["slug"])

    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(_voice, VOICE_BEATS))
    voice_paths_ordered = [voice_results.get(b["slug"]) for b in VOICE_BEATS]
    voice_ok = sum(1 for p in voice_paths_ordered if p is not None)
    print(f"    voice ready: {voice_ok}/{len(VOICE_BEATS)}")

    # Phase C: concat
    print(f"[3] Concatenating to silent 60s video...")
    silent = OUT / "silent_60s.mp4"
    if not concat_segments(seg_paths, silent):
        sys.exit("FAIL: concat")
    print(f"    silent: {silent.stat().st_size/1024/1024:.2f} MB")

    # Phase D: audio mix
    print(f"[4] Mixing music + voice beats over video...")
    final = OUT / "PILOT_8F_MUSIC_DRIVEN_60S_916.mp4"
    if not mix_audio(silent, MUSIC, voice_paths_ordered, final):
        sys.exit("FAIL: audio mix")
    print(f"    final: {final.stat().st_size/1024/1024:.2f} MB")

    # Phase E: telegram + receipt
    caption = (
        "PILOT 8F — Music-Driven Energy Montage (NON_SOVEREIGN, $0). "
        "60s, music: 'The Global AI Hackathon' (agentxxx). "
        "4 phases mapped to song energy: INTRO/BUILD/PEAK/RESOLVE. "
        "Existing footage + Zephyr voice beats. "
        "Status: RATING_PENDING."
    )
    msg_id = telegram_send(final, caption)

    receipt = {
        "schema": "RENDER_RECEIPT",
        "schema_version": 3,
        "authority_status": "NON_SOVEREIGN_RENDER_RECEIPT",
        "pilot": "8F",
        "method": "ffmpeg_music_driven_energy_montage",
        "status": "RATING_PENDING",
        "generated_at": now_iso(),
        "music_source": str(MUSIC),
        "music_title": "From Toronto to Tokyo : The Global Hackathon",
        "music_artist": "agentxxx",
        "phases": {
            "INTRO":   {"t": "0-15",  "shots": [s[0] for s in PHASE_1_INTRO]},
            "BUILD":   {"t": "15-30", "shots": [s[0] for s in PHASE_2_BUILD]},
            "PEAK":    {"t": "30-45", "shots": [s[0] for s in PHASE_3_PEAK]},
            "RESOLVE": {"t": "45-60", "shots": [s[0] for s in PHASE_4_RESOLVE]},
        },
        "voice_beats": [{"text": b["text"], "delay_ms": b["delay_ms"], "rendered": voice_results[b["slug"]] is not None} for b in VOICE_BEATS],
        "duration_seconds": 60,
        "output_path": str(final),
        "output_sha256": sha256_file(final),
        "output_size_bytes": final.stat().st_size,
        "credits_spent": 0,
        "telegram_chat_id": CHAT_ID,
        "telegram_msg_id": msg_id,
        "operator_decision": None,
        "pipeline_score": None,
        "output_score": None,
        "failure_class": None,
    }
    receipt_path = OUT / "render_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))

    candidate = {
        "schema": "MAYOR_PACKET_V1",
        "authority_status": "NON_SOVEREIGN_PACKETIZER",
        "candidate_id": 1,
        "claim": "Pilot 8F music-driven energy montage produced; awaiting operator rating",
        "obligations": [
            "operator must provide --operator-decision KEEP|REJECT",
            "operator must provide --pipeline-score 1-10",
            "operator must provide --output-score 1-10",
        ],
        "receipts": [str(receipt_path)],
        "manifest": {
            "render_artifact": str(final),
            "render_sha256": sha256_file(final),
            "telegram_msg_id": msg_id,
            "duration_seconds": 60,
            "format": "1080x1920 9:16 24fps",
            "method": "music_driven_energy_montage",
            "credits_spent": 0,
        },
        "status": "BLOCK_RATING_PENDING",
    }
    candidate_path = OUT / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2))

    print()
    print("=== PILOT 8F COMPLETE ===")
    print(f"mp4:       {final}")
    print(f"receipt:   {receipt_path}")
    print(f"candidate: {candidate_path}")
    print(f"telegram:  msg {msg_id}")
    print(f"voice:     {voice_ok}/{len(VOICE_BEATS)} beats rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
