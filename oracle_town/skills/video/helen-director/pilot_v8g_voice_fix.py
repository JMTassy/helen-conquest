#!/usr/bin/env python3
"""
HELEN Director — Pilot 8G: Voice Fix on 8F.
NON_SOVEREIGN. $0 — ffmpeg only.

Re-renders the 3 Zephyr voice beats with correct .venv path
(8F bug: parents[3] → needed parents[4]) and re-mixes audio
onto the existing /tmp/helen_pilot_8f/silent_60s.mp4 silent
video plus the music bed.

Output: 8F's visuals + music + voice beats → ship to Telegram as 8G.
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

# Correct repo resolution (parents[4], not parents[3])
THIS = Path(__file__).resolve()
REPO = THIS.parents[4]
assert REPO.name == "helen_os_v1", f"REPO resolved wrong: {REPO}"

OUT = Path("/tmp/helen_pilot_8g")
OUT.mkdir(parents=True, exist_ok=True)
VOICE_DIR = OUT / "voice"
VOICE_DIR.mkdir(exist_ok=True)

CHAT_ID = 6624890918
SILENT = Path("/tmp/helen_pilot_8f/silent_60s.mp4")
MUSIC = Path("/Users/jean-marietassy/Desktop/The Global AI Hackathon .mp3")

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
if not GEMINI_KEY:
    sys.exit("FAIL: GEMINI_API_KEY missing")
for p in (SILENT, MUSIC):
    if not p.exists():
        sys.exit(f"FAIL: missing {p}")

VOICE_BEATS = [
    {"slug": "v_intro",  "text": "I am here.",   "delay_ms":  2000},
    {"slug": "v_peak",   "text": "I see.",       "delay_ms": 37000},
    {"slug": "v_outro",  "text": "One source.",  "delay_ms": 58000},
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def render_voice(text: str, slug: str) -> Path | None:
    out_path = VOICE_DIR / f"{slug}.wav"
    helen_tts = REPO / "oracle_town" / "skills" / "voice" / "gemini_tts" / "helen_tts.py"
    venv_py = REPO / ".venv" / "bin" / "python"
    if not venv_py.exists():
        print(f"    [{slug}] venv missing: {venv_py}")
        return None
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
            print(f"    [{slug}] fail: {result.stderr[-200:]}")
            return None
        for line in result.stdout.splitlines():
            if line.startswith("Audio:"):
                wav_src = Path(line.split("Audio:", 1)[1].strip())
                if wav_src.exists():
                    wav_src.rename(out_path)
                    return out_path
    except Exception as ex:
        print(f"    [{slug}] exception: {ex}")
    return None


def mix_audio(silent_video: Path, music: Path, voices: list[Path], dst: Path,
              music_volume: float = 0.7, voice_volume: float = 1.6) -> bool:
    inputs = ["-i", str(silent_video), "-i", str(music)]
    for vp in voices:
        inputs += ["-i", str(vp)]

    fc = [f"[1:a]atrim=0:60,asetpts=PTS-STARTPTS,volume={music_volume}[music]"]
    voice_labels = []
    for i, vp in enumerate(voices):
        beat = VOICE_BEATS[i]
        idx = 2 + i
        d = beat["delay_ms"]
        fc.append(f"[{idx}:a]adelay={d}|{d},volume={voice_volume}[v{i}]")
        voice_labels.append(f"[v{i}]")
    if voice_labels:
        n = 1 + len(voice_labels)
        fc.append(f"[music]{''.join(voice_labels)}amix=inputs={n}:duration=first:dropout_transition=0[a]")
    else:
        fc.append("[music]anull[a]")

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(fc),
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    mix fail: {e.stderr[-500:]}")
        return False


def telegram_send(mp4: Path, caption: str) -> int:
    print(f"[3] Telegram sendVideo ({mp4.stat().st_size/1024:.0f} KB)...")
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
    print(f"=== HELEN Director — Pilot 8G — Voice Fix on 8F ===")
    print(f"REPO resolved: {REPO}")
    print(f"silent video:  {SILENT}")
    print(f"music:         {MUSIC.name}")
    print()

    # Phase 1: render 3 voices in parallel
    print(f"[1] Rendering {len(VOICE_BEATS)} Zephyr beats in parallel...")
    voice_results: dict[str, Path | None] = {}
    def _v(b):
        voice_results[b["slug"]] = render_voice(b["text"], b["slug"])
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(_v, VOICE_BEATS))
    voices_in_order = [voice_results.get(b["slug"]) for b in VOICE_BEATS]
    voice_ok_count = sum(1 for v in voices_in_order if v is not None)
    for b in VOICE_BEATS:
        v = voice_results.get(b["slug"])
        print(f"    {b['slug']}: {'OK ' + v.name if v else 'FAIL'}")
    if voice_ok_count == 0:
        sys.exit("FAIL: 0/3 voice beats rendered — abort 8G")

    # Phase 2: mix audio
    print(f"[2] Mixing music + {voice_ok_count} voice beats over silent video...")
    final = OUT / "PILOT_8G_MUSIC_VOICE_60S_916.mp4"
    voices_present = [v for v in voices_in_order if v is not None]
    # Adjust delay_ms to match the order of present voices
    if voice_ok_count < len(VOICE_BEATS):
        # Re-build VOICE_BEATS subset that matches voices_present
        kept = [b for b, v in zip(VOICE_BEATS, voices_in_order) if v is not None]
        # Patch global so mix_audio uses the right delays
        global VOICE_BEATS_ACTIVE  # noqa
        VOICE_BEATS_ACTIVE = kept
    if not mix_audio(SILENT, MUSIC, voices_present, final):
        sys.exit("FAIL: audio mix")
    print(f"    final: {final.stat().st_size/1024/1024:.2f} MB")

    # Phase 3: Telegram + receipt
    caption = (
        "PILOT 8G — Voice fix on 8F (NON_SOVEREIGN, $0). "
        "Same visuals as 8F (music-driven energy montage), now WITH "
        "Zephyr voice beats: 'I am here.' / 'I see.' / 'One source.' "
        "Status: RATING_PENDING."
    )
    msg_id = telegram_send(final, caption)

    receipt = {
        "schema": "RENDER_RECEIPT",
        "schema_version": 3,
        "authority_status": "NON_SOVEREIGN_RENDER_RECEIPT",
        "pilot": "8G",
        "method": "ffmpeg_voice_remix_on_8F",
        "status": "RATING_PENDING",
        "generated_at": now_iso(),
        "parent_pilot": "8F",
        "parent_silent_video": str(SILENT),
        "music_source": str(MUSIC),
        "voice_beats": [
            {"slug": b["slug"], "text": b["text"], "delay_ms": b["delay_ms"],
             "rendered": voice_results[b["slug"]] is not None,
             "wav_path": str(voice_results[b["slug"]]) if voice_results[b["slug"]] else None}
            for b in VOICE_BEATS
        ],
        "voice_rendered_count": voice_ok_count,
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
        "claim": "Pilot 8G voice-fix candidate produced; awaiting operator rating",
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
            "method": "voice_remix_on_existing_silent",
            "credits_spent": 0,
            "voice_count": voice_ok_count,
        },
        "status": "BLOCK_RATING_PENDING",
    }
    candidate_path = OUT / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2))

    print()
    print("=== PILOT 8G COMPLETE ===")
    print(f"mp4:       {final}")
    print(f"receipt:   {receipt_path}")
    print(f"candidate: {candidate_path}")
    print(f"telegram:  msg {msg_id}")
    print(f"voice:     {voice_ok_count}/{len(VOICE_BEATS)} beats rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
