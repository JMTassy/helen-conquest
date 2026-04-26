#!/usr/bin/env python3
# lifecycle: CANDIDATE
"""
HELEN Director — 30s masterpiece runner (v1, non-sovereign).

Pipeline (canon: SKILL.md §2, §3, §4, §15):
  1. Soul T2I  — generate 2 seed images (Seed A reflective-ground, Seed B close macro)
  2. Upload    — /files/generate-upload-url + PUT → CDN public_url
  3. Seedance  — 6 × I2V (5s each) submitted in parallel, one anomaly class per shot
  4. ffmpeg    — normalize + concat → single 30s mp4 (1080x1920 24fps yuv420p)
  5. Telegram  — deliver mp4 via tools/helen_telegram.py send_video helper

Defaults to --dry-run: prints plan + estimated cost, no API calls, no spend.
For real execution pass --live and --spend-ok <credits> (guard against accidents).

Endpoint paths marked UNVERIFIED are inferred from SKILL.md §2 route names
(higgsfield-ai/soul/standard, bytedance/seedance/v1/pro/image-to-video).
The only confirmed endpoint in-repo is /kling from kling_shot1_test.py.
First --live run MUST be reviewed for any 404 responses before scaling.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Credentials ──────────────────────────────────────────────────────────────
env: dict[str, str] = {}
helen_env = Path.home() / ".helen_env"
if helen_env.exists():
    for ln in helen_env.read_text().splitlines():
        ln = ln.strip()
        if ln.startswith("export "):
            ln = ln[7:]
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
for k in ("HIGGSFIELD_ID", "HIGGSFIELD_SECRET", "HF_API_KEY", "HF_API_SECRET",
         "TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY"):
    if k in os.environ and k not in env:
        env[k] = os.environ[k]

HF_ID     = env.get("HIGGSFIELD_ID") or env.get("HF_API_KEY", "")
HF_SECRET = env.get("HIGGSFIELD_SECRET") or env.get("HF_API_SECRET", "")
AUTH      = f"Key {HF_ID}:{HF_SECRET}"
BASE      = "https://platform.higgsfield.ai"
UA        = "higgsfield-client-py/1.0"

# ── Canon prompts (from transcript seed design, §4 anomaly classes) ──────────

SEED_A_PROMPT = """1080, 9:16, photoreal documentary still

A shallow puddle of dark water filling a stone slab depression in an empty
courtyard at pre-dawn blue hour. Camera height 1.2m, locked. The puddle occupies
the lower 60% of the frame. No people, no animals, no text. The water surface
is mirror-still and reflects a single distant streetlamp upper-left and one
bare branch entering upper-right. Wet stone perimeter visible: rough, weathered,
cold. Light sources: soft overcast pre-dawn 5500K + warm 2700K streetlamp point.
No fill.

35mm lens, slight grain, visible mineral texture, micro-ripples on water from
cold air. Sharp focus on water surface, gentle falloff to courtyard edges.

No glow, no bloom, no lens flare, no faces, no text, no symbols, no compositing
seams, no plastic surfaces, no AI smoothing, no extra objects, no signs,
no birds in frame.

visible imperfections, natural material response, no artificial smoothness"""

SEED_B_PROMPT = """1080, 9:16, photoreal documentary still

Macro close-up of the same wet stone-and-water surface as Seed A. Identical
mineral grain, identical light register (overcast 5500K + warm 2700K rim from
upper-left). Frame filled by the puddle edge: water bottom-left third, wet
stone top-right two-thirds. A single dry leaf rests on the water surface,
off-center, partially floating. No people, no hand, no symbols.

35mm equivalent, shallow depth on the leaf, stone texture sharp at contact
line. Cold air visible as faint condensation, no fog.

No glow, no bloom, no faces, no text, no extra objects, no plastic surfaces,
no AI smoothing.

visible imperfections, natural material response, no artificial smoothness"""

# One anomaly class per shot (SKILL.md §4). Stacking is forbidden (SKILL.md §1).
SHOTS = [
    {"n": 1, "seed": "A", "anomaly": "establishing",
     "prompt": "Camera locked. Surface absolutely still for 5 seconds. Faintest cold-air micro-ripples only. Light unchanged. No anomaly."},
    {"n": 2, "seed": "A", "anomaly": "timing_stall",
     "prompt": "One concentric ripple expands outward from the streetlamp reflection point. At ~2.5s the ripple freezes in place for ~0.8s while ambient micro-ripples continue, then resumes outward motion. Everything else unchanged."},
    {"n": 3, "seed": "A", "anomaly": "causal_off_center",
     "prompt": "A single water drop strikes the surface dead-center, visibly. The expanding ripple ring geometric center is offset ~3cm to the left of the actual impact point. No second drop. Physics otherwise correct."},
    {"n": 4, "seed": "A", "anomaly": "temporal_lag",
     "prompt": "The streetlamp upper-left flickers off then on once. The flicker appears in the water reflection ~0.9 seconds after it appears in the lamp itself. Surface otherwise stable, no ripple."},
    {"n": 5, "seed": "B", "anomaly": "non_displacement",
     "prompt": "The dry leaf is gently pressed into the water surface by an unseen force until fully submerged at ~3s, then released. Water shows no displacement, no ripple, no wet mark on the leaf when it surfaces. No hand visible."},
    {"n": 6, "seed": "A", "anomaly": "impossible_presence",
     "prompt": "Surface still. A single bright point appears in the reflection at upper-right where the bare branch is — but no equivalent light source exists in the real scene above the water. The point holds for ~4s, then fades. Nothing else changes."},
]

# ── Cost model (SKILL.md §15.3) ──────────────────────────────────────────────
CREDITS_SOUL      = 3
CREDITS_SEEDANCE  = 10   # Seedance Pro I2V 5s 9:16
def total_cost() -> int:
    return 2 * CREDITS_SOUL + len(SHOTS) * CREDITS_SEEDANCE  # 6 + 60 = 66


# ── HTTP helper (pattern from kling_shot1_test.py) ───────────────────────────
def hf_req(path: str, method: str = "POST", body=None, timeout: int = 60, raw_url: str | None = None):
    url = raw_url or (path if path.startswith("http") else f"{BASE}/{path.lstrip('/')}")
    h = {"Authorization": AUTH, "User-Agent": UA, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


# ── Endpoints (UNVERIFIED — inferred from SKILL.md §2 route names) ───────────
# Route name from §2: "higgsfield-ai/soul/standard" — likely POST /soul
# Route name from §2: "bytedance/seedance/v1/pro/image-to-video" — likely POST /seedance or /bytedance/seedance/v1/pro/image-to-video
# The only confirmed endpoint in-repo is /kling (kling_shot1_test.py).
SOUL_ENDPOINT      = "/soul"                              # UNVERIFIED
SEEDANCE_ENDPOINT  = "/bytedance/seedance/v1/pro/image-to-video"  # UNVERIFIED
UPLOAD_ENDPOINT    = "/files/generate-upload-url"         # CONFIRMED via kling_shot1_test.py


def dry_run_plan(outdir: Path) -> None:
    print("═" * 70)
    print("HELEN 30s MASTERPIECE — DRY RUN PLAN")
    print("═" * 70)
    print(f"Output dir        : {outdir}")
    print(f"Total cost est    : {total_cost()} Higgsfield credits")
    print(f"  - 2 × Soul T2I  : {2 * CREDITS_SOUL} credits")
    print(f"  - 6 × Seedance  : {6 * CREDITS_SEEDANCE} credits")
    print(f"Wall-clock est    : ~6–8 min (parallel per SKILL.md §15.1)")
    print(f"Auth              : HIGGSFIELD_ID={'SET' if HF_ID else 'MISSING'}, "
          f"SECRET={'SET' if HF_SECRET else 'MISSING'}")
    print(f"Telegram token    : {'SET' if env.get('TELEGRAM_BOT_TOKEN') else 'MISSING'}")
    print(f"Soul endpoint     : POST {BASE}{SOUL_ENDPOINT}  (UNVERIFIED)")
    print(f"Seedance endpoint : POST {BASE}{SEEDANCE_ENDPOINT}  (UNVERIFIED)")
    print(f"Upload endpoint   : POST {BASE}{UPLOAD_ENDPOINT}  (confirmed)")
    print()
    print("SEEDS:")
    for letter, prompt in [("A", SEED_A_PROMPT), ("B", SEED_B_PROMPT)]:
        print(f"  Seed {letter}: {prompt.splitlines()[0]}  ({len(prompt)} chars)")
    print()
    print("SHOTS (6 × 5s, one anomaly class each, SKILL.md §4):")
    for s in SHOTS:
        print(f"  Shot {s['n']}  seed={s['seed']}  anomaly={s['anomaly']:20s}  "
              f"prompt_chars={len(s['prompt'])}")
    print()
    print("PLANNED REQUEST BODIES:")
    print("  Soul T2I submit:")
    print(json.dumps({"prompt": "<SEED_A or SEED_B>", "aspect_ratio": "9:16",
                      "resolution": "1080"}, indent=2))
    print("  Seedance I2V submit:")
    print(json.dumps({"prompt": "<per-shot motion prompt>",
                      "input_image": {"type": "image_url",
                                      "image_url": "<CDN public_url>"},
                      "duration": 5, "resolution": "1080",
                      "aspect_ratio": "9:16"}, indent=2))
    print()
    print("NOT EXECUTED. Re-run with --live --spend-ok 70 --telegram-chat-id <id>")
    print("to perform the real pipeline.")
    print("═" * 70)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="Print plan only, no API calls (default).")
    ap.add_argument("--live", action="store_true",
                    help="Disable dry-run and execute the pipeline.")
    ap.add_argument("--spend-ok", type=int, default=0,
                    help="Authorized credit ceiling. Required with --live.")
    ap.add_argument("--telegram-chat-id", type=str, default="",
                    help="Telegram chat id to deliver final mp4.")
    ap.add_argument("--outdir", type=Path,
                    default=Path("/tmp/helen_30s_masterpiece"))
    args = ap.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    if not args.live:
        dry_run_plan(args.outdir)
        return 0

    # Live-path guardrails
    cost = total_cost()
    if args.spend_ok < cost:
        print(f"REFUSED: --spend-ok ({args.spend_ok}) < estimated cost ({cost}). "
              f"Pass --spend-ok {cost} or higher to authorize.")
        return 2
    if not args.telegram_chat_id:
        print("REFUSED: --telegram-chat-id is required for --live runs.")
        return 2
    if not HF_ID or not HF_SECRET:
        print("REFUSED: HIGGSFIELD_ID / HIGGSFIELD_SECRET not in env.")
        return 2

    print("LIVE RUN not yet implemented beyond guardrails. Intentional.")
    print("Author of this script (Claude Code) has staged dry-run + auth + "
          "cost checks. Live Soul + Seedance submission loop requires operator "
          "to confirm endpoints (SOUL_ENDPOINT, SEEDANCE_ENDPOINT marked "
          "UNVERIFIED) before scaling. See kling_shot1_test.py for reference.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
