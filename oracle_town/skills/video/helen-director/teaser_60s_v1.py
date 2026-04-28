#!/usr/bin/env python3
"""
HELEN Director — 60s game-launch teaser v1.
NON_SOVEREIGN. ~50 credits (5 Seedance Pro I2V × 10 cr each).

Storyboard (12 × 5s):
  00-05  COLD OPEN     NEW Seedance "fade-up eyes-open"           [10 cr]
  05-10  HELLO         REUSE pilot5 + Zephyr "I am here."         [free]
  10-15  KERNEL        REUSE pilot5 reversed                      [free]
  15-20  IRIS ANOMALY  REUSE v3 (Kling iris)                      [free]
  20-25  TURN          NEW Seedance "head turn toward camera"     [10 cr]
  25-30  WIDE          NEW Seedance "wide cinematic atmosphere"   [10 cr]
  30-35  FLURRY        REUSE pilot8b 0-5s                         [free]
  35-40  EYE CONTACT   NEW Seedance "tight + slow blink"          [10 cr] + Zephyr "I see."
  40-45  HEROICS       REUSE pilot5 slow                          [free]
  45-50  CLIMAX        NEW Seedance "breath + eyes-open hero"     [10 cr]
  50-55  TITLE         ffmpeg drawtext over pilot8a still         [free]
  55-60  TAG OUT       REUSE pilot8a end + Zephyr "One source."   [free]

Voice beats per SKILL §16.4:
  t=05.5  "I am here."    over HELLO segment
  t=35.5  "I see."        over EYE CONTACT segment
  t=58.0  "One source."   over TAG OUT (final beat)

Pipeline:
  1. Submit 5 Seedance Pro I2V jobs in PARALLEL (SKILL §15.1)
  2. Generate 3 Zephyr voice clips (parallel subprocess)
  3. Poll Seedance until all complete (max 8 min)
  4. Download new shots
  5. Normalize all 12 segments to 1080×1920 24fps yuv420p, 5s each
  6. ffmpeg concat + voice overlay + title-card segment
  7. Compress to <49 MB if needed
  8. Telegram + receipt + candidate JSON
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path("/tmp/helen_teaser_60s")
OUT.mkdir(parents=True, exist_ok=True)
SHOTS_DIR = OUT / "shots"
SHOTS_DIR.mkdir(exist_ok=True)
NORM_DIR = OUT / "normalized"
NORM_DIR.mkdir(exist_ok=True)
VOICE_DIR = OUT / "voice"
VOICE_DIR.mkdir(exist_ok=True)

CHAT_ID = 6624890918
SEED_PNG = Path("/Users/jean-marietassy/Desktop/HELEN_OS_PICS/HELEN_AVATAR/"
                "hf_20260411_225542_5f020418-d6e6-4716-b8bb-169f6c12bf53.png")

# Reused footage paths
REUSE_PILOT5 = Path("/tmp/helen_temple/pilot5_916__20260428_170718.mp4")
REUSE_V3     = Path("/tmp/helen_render_pilot_v3/pilot_v3.mp4")
REUSE_8A     = Path("/tmp/helen_temple/PILOT_8A_v3_COMPRESSED.mp4")
REUSE_8B     = Path("/tmp/helen_temple/PILOT_8B_CANONICAL_HELEN_30S_PRESENCE_916__20260428_205358.mp4")

for src in (SEED_PNG, REUSE_PILOT5, REUSE_V3, REUSE_8A, REUSE_8B):
    if not src.exists():
        sys.exit(f"FAIL: missing source {src}")

# Env / credentials
env = {}
helen_env = Path.home() / ".helen_env"
for ln in helen_env.read_text().splitlines():
    ln = ln.strip()
    if ln.startswith("export "):
        ln = ln[7:]
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

HF_ID = env.get("HIGGSFIELD_ID") or env.get("HF_API_KEY") or os.environ.get("HF_API_KEY", "")
HF_SECRET = env.get("HIGGSFIELD_SECRET") or env.get("HF_API_SECRET") or os.environ.get("HF_API_SECRET", "")
TELEGRAM_BOT_TOKEN = env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_KEY = env.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")

if not (HF_ID and HF_SECRET):
    sys.exit("FAIL: Higgsfield credentials missing")
if not TELEGRAM_BOT_TOKEN:
    sys.exit("FAIL: TELEGRAM_BOT_TOKEN missing")
if not GEMINI_KEY:
    sys.exit("FAIL: GEMINI_API_KEY missing (needed for Zephyr voice beats)")

HF_AUTH = f"Key {HF_ID}:{HF_SECRET}"
HF_BASE = "https://platform.higgsfield.ai"
HF_UA = "higgsfield-client-py/1.0"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def hf_req(path: str, method: str = "POST", body=None, timeout: int = 30, raw_url: str | None = None):
    url = raw_url or (path if path.startswith("http") else f"{HF_BASE}/{path.lstrip('/')}")
    h = {"Authorization": HF_AUTH, "User-Agent": HF_UA, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    rq = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


# ── Phase 0: upload seed once, reuse public_url for all Seedance shots ──
def upload_seed_to_cdn() -> str:
    print("[0] Uploading canonical seed to Higgsfield CDN...")
    code, text = hf_req("/files/generate-upload-url", body={"content_type": "image/png"})
    if code != 200:
        sys.exit(f"FAIL upload-url: {code}: {text[:300]}")
    info = json.loads(text)
    public_url = info["public_url"]
    upload_url = info["upload_url"]
    put_req = urllib.request.Request(
        upload_url, data=SEED_PNG.read_bytes(),
        headers={"Content-Type": "image/png"}, method="PUT",
    )
    with urllib.request.urlopen(put_req, timeout=120) as r:
        if r.status not in (200, 201):
            sys.exit(f"FAIL PUT: {r.status}")
    print(f"    public_url: {public_url[:80]}...")
    return public_url


# ── Phase 1: 5 Seedance prompts ──
PROMPTS = [
    {
        "id": "shot1_cold_open",
        "prompt": (
            "1080x1920 9:16 5s 24fps. Locked tripod 35mm cinematic. "
            "Subject HELEN portrait — copper-red wavy hair, blue-grey eyes, fair skin, freckle pattern. "
            "Motion: HELEN's eyes start nearly closed, slowly open from 0% to 100% over 3 seconds, "
            "then 2 seconds of stillness with calm gaze. Identity locked across all 5 seconds. "
            "Painterly festival aesthetic, soft natural light. "
            "No camera movement, no head turn, no facial morph, no text overlay."
        ),
    },
    {
        "id": "shot2_turn",
        "prompt": (
            "1080x1920 9:16 5s 24fps. Locked tripod 35mm. "
            "HELEN — copper-red wavy hair, blue-grey eyes, fair skin, freckles. "
            "Motion: HELEN starts looking down and slightly left. Over 4 seconds she slowly turns "
            "her head to face the camera directly, holding gaze at the end for 1 second. "
            "Subtle natural breathing. Identity preserved across the turn. "
            "No camera movement, no zoom, painterly restraint. No text."
        ),
    },
    {
        "id": "shot3_wide",
        "prompt": (
            "1080x1920 9:16 5s 24fps. Slow forward dolly cinematic 35mm. "
            "Wide environmental shot — HELEN is in the center of the frame in mid-distance, "
            "atmospheric soft daylight, depth, blurred foreground. "
            "Identity visible: copper-red wavy hair, fair skin recognizable. "
            "Camera moves forward gently 5 seconds, no rotation. Festival aesthetic. No text."
        ),
    },
    {
        "id": "shot4_eye_contact",
        "prompt": (
            "1080x1920 9:16 5s 24fps. Locked tripod 35mm tight close-up. "
            "HELEN's face fills the frame — copper-red wavy hair, blue-grey eyes, fair skin, freckles. "
            "Motion: HELEN holds direct eye contact for 2 seconds, then performs one slow soft blink "
            "(eyelids close over 0.5s, hold closed 0.5s, open over 1s), then 1 second of return to "
            "direct gaze. Painterly. Identity preserved across the blink. No text."
        ),
    },
    {
        "id": "shot5_climax",
        "prompt": (
            "1080x1920 9:16 5s 24fps. Locked tripod 35mm. Warm key light from screen-left. "
            "HELEN portrait — copper-red wavy hair, blue-grey eyes, fair skin, freckles. "
            "Motion: starts with eyes closed and lips relaxed, breath rises subtly across chest "
            "over 2 seconds, eyes open slowly to camera over 1.5 seconds, full breath out and "
            "final stillness 1.5 seconds. Festival climax shot. No facial morph, no head turn. "
            "Identity locked. No text."
        ),
    },
]


def submit_seedance(shot: dict, public_url: str) -> dict:
    """Submit one Seedance Pro I2V job. Returns submission info or raises."""
    payload = {
        "prompt": shot["prompt"],
        "input_image": {"type": "image_url", "image_url": public_url},
        "duration": 5,
        "resolution": "1080",
        "aspect_ratio": "9:16",
    }
    code, text = hf_req("/bytedance/seedance/v1/pro/image-to-video", body=payload)
    if code in (200, 201, 202):
        info = json.loads(text)
        return {"shot": shot, "request_id": info.get("request_id"), "status_url": info.get("status_url"), "submit_response": info, "engine": "seedance"}
    # Fallback to Kling if Seedance endpoint unavailable
    print(f"    [{shot['id']}] Seedance unavailable ({code}), falling back to Kling")
    code2, text2 = hf_req("/kling", body=payload)
    if code2 in (200, 201, 202):
        info = json.loads(text2)
        return {"shot": shot, "request_id": info.get("request_id"), "status_url": info.get("status_url"), "submit_response": info, "engine": "kling"}
    if code2 == 403 or code == 403:
        sys.exit("FAIL: 403 Not enough Higgsfield credits — top up at platform.higgsfield.ai/billing")
    raise RuntimeError(f"Both engines failed: seedance={code} kling={code2}")


def poll_until_complete(submissions: list[dict], deadline_s: int = 600) -> list[dict]:
    """Poll all submissions in a single loop until all terminal."""
    print(f"[2] Polling {len(submissions)} jobs in parallel (max {deadline_s}s)...")
    pending = list(submissions)
    deadline = time.time() + deadline_s
    poll_n = 0
    while pending and time.time() < deadline:
        still = []
        for sub in pending:
            url = sub.get("status_url")
            if url and url.startswith("http"):
                code, text = hf_req(url, raw_url=url, method="GET")
            else:
                code, text = hf_req(f"/requests/{sub['request_id']}/status", method="GET")
            try:
                data = json.loads(text)
                status = data.get("status", "?")
            except Exception:
                status = "?"
            if status in ("completed", "COMPLETED"):
                output_url = (
                    data.get("output_url")
                    or data.get("video_url")
                    or (data.get("video") or {}).get("url")
                    or (data.get("outputs") or [{}])[0].get("url")
                    or data.get("result", {}).get("url")
                )
                sub["output_url"] = output_url
                sub["terminal_status"] = "completed"
                sub["status_payload"] = data
            elif status in ("failed", "FAILED", "NSFW", "canceled", "CANCELED"):
                sub["terminal_status"] = status
                sub["status_payload"] = data
            else:
                still.append(sub)
        poll_n += 1
        done = len(submissions) - len(still)
        if poll_n % 6 == 0 or len(still) != len(pending):
            print(f"    poll {poll_n}: {done}/{len(submissions)} done")
        pending = still
        if pending:
            time.sleep(10)
    if pending:
        for sub in pending:
            sub["terminal_status"] = "timeout"
        print(f"    TIMEOUT: {len(pending)} jobs incomplete after {deadline_s}s")
    return submissions


def download_shot(sub: dict, dst: Path) -> bool:
    if sub.get("terminal_status") != "completed" or not sub.get("output_url"):
        return False
    try:
        urllib.request.urlretrieve(sub["output_url"], dst)
        return True
    except Exception as e:
        print(f"    [{sub['shot']['id']}] download failed: {e}")
        return False


# ── Phase 2: Zephyr voice beats (parallel via thread pool) ──
def render_voice(text: str, slug: str) -> Path:
    """Generate one Zephyr clip via helen_tts.py, return wav path."""
    out_path = VOICE_DIR / f"{slug}.wav"
    helen_tts = REPO / "oracle_town" / "skills" / "voice" / "gemini_tts" / "helen_tts.py"
    venv_py = REPO / ".venv" / "bin" / "python"
    tmp_dir = OUT / f"voice_tmp_{slug}"
    tmp_dir.mkdir(exist_ok=True)
    e = os.environ.copy()
    e["GEMINI_API_KEY"] = GEMINI_KEY
    result = subprocess.run(
        [str(venv_py), str(helen_tts), "--output-dir", str(tmp_dir), text],
        capture_output=True, text=True, timeout=60, env=e,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Zephyr {slug} failed: {result.stderr[:300]}")
    for line in result.stdout.splitlines():
        if line.startswith("Audio:"):
            wav_src = Path(line.split("Audio:", 1)[1].strip())
            if wav_src.exists():
                wav_src.rename(out_path)
                return out_path
    raise RuntimeError(f"Zephyr {slug}: no Audio line in output")


VOICE_BEATS = [
    {"slug": "v_intro", "text": "I am here.", "delay_ms": 5500},
    {"slug": "v_mid",   "text": "I see.",     "delay_ms": 35500},
    {"slug": "v_outro", "text": "One source.", "delay_ms": 58000},
]


# ── Phase 3: ffmpeg normalize + compose ──
def normalize_clip(src: Path, dst: Path, start: float = 0, dur: float = 5,
                   reverse: bool = False, slow: bool = False, tint_warm: bool = False) -> bool:
    vf_parts = [
        "scale=1080:1920:force_original_aspect_ratio=increase",
        "crop=1080:1920",
        "setsar=1",
    ]
    if reverse:
        vf_parts.append("reverse")
    if slow:
        vf_parts.append("setpts=2*PTS")
    if tint_warm:
        vf_parts.append("colorbalance=rh=0.08:gh=0.02:bh=-0.04")
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
        print(f"    normalize fail {src.name}: {e.stderr[-300:]}")
        return False


def make_title_card(dst: Path) -> bool:
    """5s title card: HELEN OS + motto."""
    # Use a darkened still from pilot8a as background
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", "5",
        "-i", str(REUSE_8A),
        "-vf",
        ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
         "eq=brightness=-0.25:contrast=1.05,"
         "drawtext=text='HELEN OS':fontcolor=#d4a017:fontsize=120:"
         "x=(w-text_w)/2:y=(h-text_h)/2-100:"
         "fontfile=/System/Library/Fonts/Helvetica.ttc:"
         "alpha='if(lt(t,0.5),t*2,if(lt(t,4.5),1,if(lt(t,5),(5-t)*2,0)))',"
         "drawtext=text='HELEN suggests. You decide. Everything is recorded.':"
         "fontcolor=#ede0c8:fontsize=42:"
         "x=(w-text_w)/2:y=(h-text_h)/2+80:"
         "fontfile=/System/Library/Fonts/Helvetica.ttc:"
         "alpha='if(lt(t,1),0,if(lt(t,1.5),(t-1)*2,if(lt(t,4.5),1,if(lt(t,5),(5-t)*2,0))))',"
         "fps=24"),
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-an", "-t", "5", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    title card fail: {e.stderr[-400:]}")
        return False


def compose_final(segment_paths: list[Path], voice_paths: list[Path], dst: Path) -> bool:
    """Concat 12 segments, overlay 3 voice beats at canonical timestamps."""
    inputs = []
    for p in segment_paths:
        inputs += ["-i", str(p)]
    for vp in voice_paths:
        inputs += ["-i", str(vp)]

    n_seg = len(segment_paths)
    seg_chain = "".join(f"[{i}:v]" for i in range(n_seg))
    concat = f"{seg_chain}concat=n={n_seg}:v=1:a=0[v]"

    audio_offset = n_seg
    audio_parts = []
    for i, beat in enumerate(VOICE_BEATS):
        in_idx = audio_offset + i
        delay = beat["delay_ms"]
        audio_parts.append(f"[{in_idx}:a]adelay={delay}|{delay},volume=1.4[a{i}]")
    audio_mix = "[a0][a1][a2]amix=inputs=3:duration=longest:dropout_transition=0[a]"

    fc = ";".join([concat] + audio_parts + [audio_mix])

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", fc,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-crf", "21", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    compose fail: {e.stderr[-500:]}")
        return False


def compress_for_telegram(src: Path, dst: Path, target_mb: int = 47) -> Path:
    cur_mb = src.stat().st_size / 1024 / 1024
    if cur_mb < target_mb:
        return src
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-c:v", "libx264", "-crf", "26", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        str(dst),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
    return dst


def telegram_send(mp4: Path, caption: str) -> int:
    print(f"[7] Telegram sendVideo ({mp4.stat().st_size/1024:.0f} KB)...")
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


# ────────── MAIN ──────────
def main() -> int:
    print(f"=== HELEN Director — 60s teaser v1 ===")
    print(f"Seed:    {SEED_PNG.name}")
    print(f"Reuse:   pilot5, v3, pilot8a, pilot8b")
    print(f"Engine:  Seedance Pro I2V (Kling fallback)")
    print(f"Budget:  ~50 credits (5 new shots × 10 cr)")
    print(f"Out:     {OUT}")
    print()

    # Phase 0: upload seed once
    public_url = upload_seed_to_cdn()

    # Phase 1: submit 5 Seedance jobs in parallel + Phase 2: voice in parallel
    print(f"[1] Submitting {len(PROMPTS)} Seedance jobs in parallel...")
    submissions = []
    for shot in PROMPTS:
        sub = submit_seedance(shot, public_url)
        submissions.append(sub)
        print(f"    [{shot['id']}] engine={sub['engine']} request_id={sub['request_id']}")

    # Render voice in parallel using thread pool while jobs cook
    voice_paths_dict: dict[str, Path] = {}
    voice_errors: list[str] = []

    def _voice_one(beat):
        try:
            p = render_voice(beat["text"], beat["slug"])
            voice_paths_dict[beat["slug"]] = p
            print(f"    [voice] {beat['slug']}: {beat['text']!r} OK")
        except Exception as e:
            voice_errors.append(f"{beat['slug']}: {e}")

    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(_voice_one, VOICE_BEATS))

    if voice_errors:
        print(f"[!] voice errors (non-fatal, will use silence): {voice_errors}")

    # Phase 3: poll Seedance until all complete
    submissions = poll_until_complete(submissions, deadline_s=600)

    # Phase 4: download new shots
    print("[3] Downloading new shots...")
    new_shot_paths: dict[str, Path] = {}
    for sub in submissions:
        slug = sub["shot"]["id"]
        if sub.get("terminal_status") == "completed":
            dst = SHOTS_DIR / f"{slug}.mp4"
            if download_shot(sub, dst):
                new_shot_paths[slug] = dst
                print(f"    [{slug}] {dst.stat().st_size/1024:.0f} KB")
            else:
                print(f"    [{slug}] download failed — will substitute with REUSE")
        else:
            print(f"    [{slug}] terminal={sub.get('terminal_status')} — substituting REUSE")

    # Substitute fallbacks for any failed new shots (use pilot5 as universal fallback)
    fallback = REUSE_PILOT5
    for slug in (s["id"] for s in PROMPTS):
        if slug not in new_shot_paths:
            new_shot_paths[slug] = fallback

    # Phase 5: normalize all 12 segments to 1080×1920 24fps yuv420p, 5s each
    print("[4] Normalizing 12 segments...")
    seg_specs = [
        ("seg01_cold_open",   new_shot_paths["shot1_cold_open"], 0, 5, False, False, False),
        ("seg02_hello",       REUSE_PILOT5,                       0, 5, False, False, False),
        ("seg03_kernel",      REUSE_PILOT5,                       0, 5, True,  False, True),
        ("seg04_iris",        REUSE_V3,                           0, 5, False, False, False),
        ("seg05_turn",        new_shot_paths["shot2_turn"],       0, 5, False, False, False),
        ("seg06_wide",        new_shot_paths["shot3_wide"],       0, 5, False, False, False),
        ("seg07_flurry",      REUSE_8B,                           0, 5, False, False, False),
        ("seg08_eye_contact", new_shot_paths["shot4_eye_contact"],0, 5, False, False, False),
        ("seg09_heroics",     REUSE_PILOT5,                       0, 5, False, True,  False),
        ("seg10_climax",      new_shot_paths["shot5_climax"],     0, 5, False, False, False),
        # seg11 = title card (special)
        ("seg12_tag_out",     REUSE_8A,                           25, 5, False, False, False),
    ]
    seg_paths: list[Path] = []
    for name, src, start, dur, rev, slow, tint in seg_specs:
        dst = NORM_DIR / f"{name}.mp4"
        if normalize_clip(src, dst, start=start, dur=dur, reverse=rev, slow=slow, tint_warm=tint):
            seg_paths.append(dst)
            # title card belongs at slot index 10 (between seg10 and seg12)
            if name == "seg10_climax":
                tc = NORM_DIR / "seg11_title.mp4"
                if make_title_card(tc):
                    seg_paths.append(tc)
        else:
            print(f"    [{name}] normalize failed — skipping segment")

    if len(seg_paths) < 11:
        sys.exit(f"FAIL: only {len(seg_paths)}/12 segments normalized; aborting compose")

    # Phase 6: compose final
    print("[5] Composing final teaser (concat + voice mix)...")
    voice_paths = []
    for beat in VOICE_BEATS:
        if beat["slug"] in voice_paths_dict:
            voice_paths.append(voice_paths_dict[beat["slug"]])
        else:
            silent = VOICE_DIR / f"silent_{beat['slug']}.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                 "-t", "1", "-c:a", "pcm_s16le", str(silent)],
                check=True, capture_output=True, timeout=10,
            )
            voice_paths.append(silent)

    composed = OUT / "teaser_60s.mp4"
    if not compose_final(seg_paths, voice_paths, composed):
        sys.exit("FAIL: compose step")

    # Phase 7: compress if needed
    print("[6] Compressing for Telegram...")
    final = compress_for_telegram(composed, OUT / "teaser_60s_compressed.mp4")
    print(f"    final: {final}  size: {final.stat().st_size/1024/1024:.2f} MB")

    # Phase 8: Telegram + receipt + candidate
    caption = (
        "HELEN — 60s game-launch teaser v1. Storyboard: 12 × 5s segments, "
        "5 new Seedance shots + reuse (pilot5/v3/8a/8b), Zephyr voice beats. "
        "RATING_PENDING."
    )
    msg_id = telegram_send(final, caption)

    # Receipts
    submitted_engines = {s["shot"]["id"]: s.get("engine", "?") for s in submissions}
    terminal_states = {s["shot"]["id"]: s.get("terminal_status", "?") for s in submissions}
    receipt = {
        "schema": "TEASER_60S_RECEIPT",
        "schema_version": 1,
        "authority_status": "NON_SOVEREIGN_RENDER_RECEIPT",
        "status": "RATING_PENDING",
        "generated_at": now_iso(),
        "seed_path": str(SEED_PNG),
        "seed_sha256": sha256_file(SEED_PNG),
        "engines_used": submitted_engines,
        "shot_terminal_states": terminal_states,
        "voice_beats": [{"slug": b["slug"], "text": b["text"], "delay_ms": b["delay_ms"]} for b in VOICE_BEATS],
        "voice_errors": voice_errors,
        "reuse_sources": {
            "pilot5": str(REUSE_PILOT5),
            "v3":     str(REUSE_V3),
            "pilot8a": str(REUSE_8A),
            "pilot8b": str(REUSE_8B),
        },
        "output_path": str(final),
        "output_sha256": sha256_file(final),
        "output_size_bytes": final.stat().st_size,
        "telegram_chat_id": CHAT_ID,
        "telegram_msg_id": msg_id,
        "operator_decision": None,
        "pipeline_score": None,
        "output_score": None,
        "failure_class": None,
    }
    receipt_path = OUT / "render_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    print(f"    receipt: {receipt_path}")

    candidate = {
        "schema": "MAYOR_PACKET_V1",
        "authority_status": "NON_SOVEREIGN_PACKETIZER",
        "candidate_id": 1,
        "claim": "60s game-launch teaser produced; awaiting operator rating before handoff",
        "obligations": [
            "operator must provide --operator-decision KEEP|REJECT",
            "operator must provide --pipeline-score 1-10 (rails worked)",
            "operator must provide --output-score 1-10 (festival-grade?)",
        ],
        "receipts": [str(receipt_path)],
        "manifest": {
            "render_artifact": str(final),
            "render_sha256": sha256_file(final),
            "telegram_msg_id": msg_id,
            "duration_seconds": 60,
            "format": "1080x1920 9:16 24fps",
            "engines": submitted_engines,
            "voice": "Zephyr × 3 beats",
            "music": None,
        },
        "status": "BLOCK_RATING_PENDING",
    }
    candidate_path = OUT / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2))
    print(f"    candidate: {candidate_path}")

    print()
    print("=== TEASER 60s v1 COMPLETE ===")
    print(f"mp4:        {final}")
    print(f"receipt:    {receipt_path}")
    print(f"candidate:  {candidate_path}")
    print(f"telegram:   msg {msg_id}")
    print(f"status:     RATING_PENDING")
    return 0


if __name__ == "__main__":
    sys.exit(main())
