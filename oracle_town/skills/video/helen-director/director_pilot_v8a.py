#!/usr/bin/env python3
"""
HELEN Director — Pilot 8A: Canonical Day Presence Film.
NON_SOVEREIGN. 30s vertical film from one canonical HELEN image.
No paid renders. No Seedance. ffmpeg post-production only.

Pipeline:
  1. Scale source to 3240x4320 (3x output, headroom for zoompan)
  2. zoompan — 6-phase motion over 720 frames @ 24fps
  3. Glow bloom — gblur + additive blend
  4. Vignette
  5. Film grain (noise filter, temporal)
  6. Gentle pulse (geq sine wave)
  7. Color grade (warm-violet tint for day presence)
  8. Encode → 1080x1920 h264 30s
  9. Write receipt + send Telegram

Phases:
  0-5s   slow push-in (zoom 1.00→1.08)
  5-10s  subtle upward drift + bloom brightens
  10-15s Ken Burns diagonal (zoom 1.08→1.14, pan right)
  15-20s slow orbit continues (zoom 1.14→1.16)
  20-25s warm amber rise, grain intensifies slightly
  25-30s final calm hold, motion nearly stops
"""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

SOURCE = Path("/Users/jean-marietassy/Desktop/HELEN_OS_PICS/HELEN_AVATAR/"
              "hf_20260411_225542_5f020418-d6e6-4716-b8bb-169f6c12bf53.png")
OUT_DIR = Path("/tmp/helen_temple")
OUT_DIR.mkdir(parents=True, exist_ok=True)

_env: dict[str, str] = {}
_helen_env = Path.home() / ".helen_env"
if _helen_env.exists():
    for ln in _helen_env.read_text().splitlines():
        ln = ln.strip()
        if ln.startswith("export "): ln = ln[7:]
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            _env[k.strip()] = v.strip().strip('"').strip("'")

# ── Animation constants ───────────────────────────────────────────────────────
FPS   = 24
DUR   = 30          # seconds
TOTAL = FPS * DUR   # 720 frames
W, H  = 1080, 1920

# zoompan: 6 phases across 720 frames
# zoom: 1.00 → 1.08 → 1.12 → 1.16 → 1.16 → 1.14 → 1.12
# x: centered + gentle rightward drift in mid sections
# y: very slow upward drift (classical Ken Burns)
Z_EXPR = (
    "if(lte(on,60),   1.0+on*0.0013,"            # 0-2.5s: fast pull in 1.00→1.08
    "if(lte(on,180),  1.08+on*0.0002,"           # 2.5-7.5s: ease to 1.12
    "if(lte(on,360),  1.12+(on-180)*0.00022,"    # 7.5-15s: slow push 1.12→1.16
    "if(lte(on,540),  1.16+(on-360)*0.0001,"     # 15-22.5s: creep to 1.18
    "1.18-(on-540)*0.00028))))"                  # 22.5-30s: very slow pull back 1.18→1.16
)
X_EXPR = (
    "iw/2-(iw/zoom/2)"
    "+if(lte(on,360), -on*0.08,"                 # 0-15s: drift left -28.8px
    "(-28.8)+(on-360)*0.12)"                     # 15-30s: drift back right +43.2px
)
Y_EXPR = (
    "max(0, ih/2-(ih/zoom/2)"
    "-if(lte(on,480), on*0.07,"                  # 0-20s: slow upward -33.6px
    "33.6-(on-480)*0.05))"                       # 20-30s: ease down
)

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

def build(out: Path) -> bool:
    fc = (
        # Scale source for zoompan headroom (3x output width)
        f"[0:v]scale=3240:4320:flags=lanczos[scaled];"

        # zoompan: 6-phase motion, 720 frames @ 24fps
        f"[scaled]zoompan="
        f"z='{Z_EXPR}':"
        f"x='{X_EXPR}':"
        f"y='{Y_EXPR}':"
        f"d={TOTAL}:s={W}x{H}:fps={FPS}[zp];"

        # Split: base + glow source
        "[zp]split=2[base][glow_src];"

        # Glow bloom: soft blur + 10% brightness (not overexposing)
        "[glow_src]gblur=sigma=25[blurred];"
        "[blurred]geq="
        "r='min(255,r(X,Y)*0.10)':"
        "g='min(255,g(X,Y)*0.10)':"
        "b='min(255,b(X,Y)*0.10)'[glow];"

        # Additive blend glow onto base
        "[base][glow]blend=all_mode=addition[glowed];"

        # Vignette (darkens corners)
        "[glowed]vignette=PI/3.8[vignetted];"

        # Film grain (temporal, subtle)
        "[vignetted]noise=c0s=9:c0f=t+u[grainy];"

        # Gentle presence pulse: 2.5% amplitude, 5s period
        "[grainy]geq="
        "r='clip(r(X,Y)*(1+0.025*sin(2*3.14159*T/5)),0,255)':"
        "g='clip(g(X,Y)*(1+0.025*sin(2*3.14159*T/5)),0,255)':"
        "b='clip(b(X,Y)*(1+0.025*sin(2*3.14159*T/5)),0,255)'[pulsed];"

        # Color grade: warm-violet day presence
        # slight saturation boost + warm highlight lift + violet shadow tint
        "[pulsed]hue=s=1.12[saturated];"
        # sharpen, then warm-violet grade
        "[saturated]unsharp=5:5:0.6:3:3:0[sharp];"
        "[sharp]colorbalance=rh=0.08:gh=0.03:bh=-0.03:rs=0.03:gs=0:bs=0.06"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(SOURCE),
        "-filter_complex", fc,
        "-t", str(DUR),
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-an",
        str(out),
    ]
    print("[BUILD] Running ffmpeg 30s presence film…")
    print(f"        source: {SOURCE.name}")
    print(f"        output: {out}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-1200:], file=sys.stderr)
        return False
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"        done: {size_mb:.1f} MB")
    return True


def send_telegram(mp4: Path) -> int:
    token = _env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = "6624890918"
    boundary = b"----boundary1234"
    body = b"--" + boundary + b"\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n" + chat_id.encode() + b"\r\n"
    body += b"--" + boundary + b"\r\nContent-Disposition: form-data; name=\"video\"; filename=\"PILOT_8A.mp4\"\r\nContent-Type: video/mp4\r\n\r\n"
    body += mp4.read_bytes()
    body += b"\r\n--" + boundary + b"--\r\n"
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendVideo",
        data=body,
        headers={"Content-Type": "multipart/form-data; boundary=----boundary1234"},
        method="POST",
    )
    print(f"[TG]   Sending {mp4.stat().st_size//1024} KB…")
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read().decode())
        msg_id = resp["result"]["message_id"]
        print(f"[TG]   OK  msg_id={msg_id}")
        return msg_id


def write_receipt(mp4: Path, msg_id: int) -> Path:
    receipt = {
        "schema": "NON_SOVEREIGN_RENDER_RECEIPT_V3",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "canon": "NO_SHIP",
        "generated_at": now_iso(),
        "pilot": "director_pilot_v8a",
        "source_image": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "artifact": str(mp4),
        "artifact_sha256": sha256_file(mp4),
        "artifact_size_bytes": mp4.stat().st_size,
        "method": "ffmpeg_postproduction",
        "duration_s": DUR,
        "format": f"{W}x{H}",
        "credits_spent": 0,
        "technique": "zoompan+glow+vignette+grain+pulse+colorbalance",
        "phases": {
            "0-5s":   "slow push-in zoom 1.0→1.08",
            "5-10s":  "upward drift + bloom",
            "10-15s": "Ken Burns diagonal zoom 1.08→1.16",
            "15-20s": "slow orbit hold",
            "20-25s": "warm settle",
            "25-30s": "final calm hold",
        },
        "telegram_msg_id": msg_id,
        "compliance_target": "iconic_presence",
        "operator_decision": None,
        "pipeline_score": None,
        "output_score": None,
        "status": "RATING_PENDING",
    }
    rp = OUT_DIR / "render_receipt_v8a.json"
    rp.write_text(json.dumps(receipt, indent=2))
    return rp


def main() -> int:
    if not SOURCE.exists():
        print(f"ABORT: source not found: {SOURCE}", file=sys.stderr)
        return 2

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_DIR / f"PILOT_8A_CANONICAL_HELEN_30S_PRESENCE_916__{ts}.mp4"

    if not build(out):
        print("ABORT: ffmpeg failed", file=sys.stderr)
        return 1

    msg_id = send_telegram(out)
    rp = write_receipt(out, msg_id)

    print()
    print("=" * 60)
    print("PILOT 8A OUTPUT")
    print("=" * 60)
    print(f"  mp4     : {out}")
    print(f"  receipt : {rp}")
    print(f"  telegram: msg {msg_id}")
    print(f"  status  : RATING_PENDING — BLOCKED")
    print()
    print("Rate: pipeline=X output=X KEEP|REJECT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
