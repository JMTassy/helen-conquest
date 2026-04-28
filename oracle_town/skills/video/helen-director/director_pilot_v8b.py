#!/usr/bin/env python3
"""
HELEN Director — Pilot 8B: Canonical 30s Presence Film, multi-image.
NON_SOVEREIGN. $0. ffmpeg only.

3 canonical HELEN portraits cross-dissolved over 30s.
No glow overexposure. No eating. No Higgsfield renders.
Compression built-in (auto-compress to <49MB for Telegram).

Sources (in order):
  1. helen_conquest_adcopy1.png  — designed ad visual, portrait
  2. helen_cyberpunk.jpg          — cinematic/dark mood
  3. helen_canonical1.jpeg        — canonical face, clean portrait

Flow: conquest (0-12s) → dissolve → cyberpunk (10-22s) → dissolve → canonical (20-30s)
Each segment has its own zoompan direction.
"""
from __future__ import annotations

import datetime, hashlib, json, subprocess, sys, urllib.request
from pathlib import Path

AVATAR = Path("/Users/jean-marietassy/Desktop/HELEN_OS_PICS/HELEN_AVATAR")
REFS   = Path("/Users/jean-marietassy/Documents/GitHub/helen_os_v1/oracle_town/skills/video/helen-director/references")
IMG1   = AVATAR / "helen_conquest_adcopy1.png"   # 1272×1886 RGBA
IMG2   = AVATAR / "helen_cyberpunk.jpg"           # 832×1248
IMG3   = AVATAR / "helen_canonical1.jpeg"         # 832×1248
OUT_DIR = Path("/tmp/helen_temple")
OUT_DIR.mkdir(parents=True, exist_ok=True)

_env: dict[str, str] = {}
for ln in (Path.home() / ".helen_env").read_text().splitlines():
    ln = ln.strip()
    if ln.startswith("export "): ln = ln[7:]
    if "=" in ln and not ln.startswith("#"):
        k, v = ln.split("=", 1); _env[k.strip()] = v.strip().strip('"').strip("'")

W, H, FPS = 1080, 1920, 24
SEG = 14     # seconds per segment (overlap creates 30s total)
FADE = 2     # dissolve duration

def sha256_file(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def now_iso() -> str: return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z")

def zp(direction: str, d: int) -> str:
    """Return zoompan filter string for given direction and frame count."""
    if direction == "push_in_center":
        z = f"1.0+on*{0.12/d:.6f}"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif direction == "push_in_left":
        z = f"1.0+on*{0.10/d:.6f}"
        x = f"iw/2-(iw/zoom/2)-on*{20.0/d:.4f}"
        y = f"ih/2-(ih/zoom/2)-on*{15.0/d:.4f}"
    elif direction == "push_in_right":
        z = f"1.0+on*{0.08/d:.6f}"
        x = f"iw/2-(iw/zoom/2)+on*{15.0/d:.4f}"
        y = f"ih/2-(ih/zoom/2)-on*{10.0/d:.4f}"
    return (f"zoompan=z='{z}':x='max(0,{x})':y='max(0,{y})'"
            f":d={d}:s={W}x{H}:fps={FPS}")

def build(raw: Path) -> bool:
    d1 = SEG * FPS  # frames per segment

    # Common post-process: vignette + grain + pulse + grade
    post = (
        "vignette=PI/3.2,"
        "noise=c0s=10:c0f=t+u,"
        f"geq=r='clip(r(X,Y)*(1+0.02*sin(2*3.14159*T/4)),0,255)':"
        f"g='clip(g(X,Y)*(1+0.02*sin(2*3.14159*T/4)),0,255)':"
        f"b='clip(b(X,Y)*(1+0.02*sin(2*3.14159*T/4)),0,255)',"
        "hue=s=1.15,"
        "colorbalance=rh=0.07:gh=0.02:bh=-0.03:bs=0.05:rs=0.02"
    )

    # Fade-in/out via geq brightness ramp
    fade_in  = f"geq=r='r(X,Y)*min(1,T/1.0)':g='g(X,Y)*min(1,T/1.0)':b='b(X,Y)*min(1,T/1.0)'"
    fade_out = f"geq=r='r(X,Y)*min(1,(30-T)/1.0)':g='g(X,Y)*min(1,(30-T)/1.0)':b='b(X,Y)*min(1,(30-T)/1.0)'"

    fc = (
        # Input 1: conquest (RGBA→RGB via format filter)
        f"[0:v]format=rgb24,scale=3240:4320:flags=lanczos,"
        f"{zp('push_in_center', d1)},"
        f"{post}[v1];"

        # Input 2: cyberpunk
        f"[1:v]scale=3240:4320:flags=lanczos,"
        f"{zp('push_in_left', d1)},"
        f"{post}[v2];"

        # Input 3: canonical
        f"[2:v]scale=3240:4320:flags=lanczos,"
        f"{zp('push_in_right', d1)},"
        f"{post}[v3];"

        # Cross-dissolve: v1→v2 at offset=10, v2→v3 at offset=20
        f"[v1][v2]xfade=transition=dissolve:duration={FADE}:offset=10[x12];"
        f"[x12][v3]xfade=transition=dissolve:duration={FADE}:offset=20[xout];"

        # Global fade in + out
        f"[xout]{fade_in}[fin];"
        f"[fin]{fade_out}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(SEG + 2), "-i", str(IMG1),
        "-loop", "1", "-t", str(SEG + 2), "-i", str(IMG2),
        "-loop", "1", "-t", str(SEG + 2), "-i", str(IMG3),
        "-filter_complex", fc,
        "-t", "30",
        "-c:v", "libx264", "-crf", "22", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-an",
        str(raw),
    ]
    print(f"[BUILD] 3-image dissolve · {SEG}s segments · dissolve={FADE}s")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-1500:], file=sys.stderr)
        return False
    print(f"        raw: {raw.stat().st_size/1024/1024:.1f} MB")
    return True


def compress(raw: Path, out: Path) -> bool:
    cmd = [
        "ffmpeg", "-y", "-i", str(raw),
        "-c:v", "libx264", "-crf", "26", "-maxrate", "2200k",
        "-bufsize", "4400k", "-pix_fmt", "yuv420p", "-an", str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr[-500:], file=sys.stderr); return False
    size = out.stat().st_size / 1024 / 1024
    print(f"        compressed: {size:.1f} MB")
    return size < 49


def send_telegram(mp4: Path) -> int:
    token = _env.get("TELEGRAM_BOT_TOKEN", "")
    boundary = b"----boundary1234"
    body = b"--"+boundary+b"\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n6624890918\r\n"
    body += b"--"+boundary+b"\r\nContent-Disposition: form-data; name=\"video\"; filename=\"PILOT_8B.mp4\"\r\nContent-Type: video/mp4\r\n\r\n"
    body += mp4.read_bytes()
    body += b"\r\n--"+boundary+b"--\r\n"
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendVideo", data=body,
        headers={"Content-Type": "multipart/form-data; boundary=----boundary1234"}, method="POST",
    )
    print(f"[TG]   sending {mp4.stat().st_size//1024} KB…")
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read().decode())
        mid = resp["result"]["message_id"]
        print(f"[TG]   OK msg_id={mid}"); return mid


def main() -> int:
    for img in [IMG1, IMG2, IMG3]:
        if not img.exists():
            print(f"ABORT: missing {img}", file=sys.stderr); return 2

    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    raw = OUT_DIR / f"PILOT_8B_raw__{ts}.mp4"
    out = OUT_DIR / f"PILOT_8B_CANONICAL_HELEN_30S_PRESENCE_916__{ts}.mp4"

    if not build(raw): print("ABORT: build failed", file=sys.stderr); return 1
    if not compress(raw, out): print("ABORT: compress failed or still >49MB", file=sys.stderr); return 1

    mid = send_telegram(out)

    receipt = {
        "schema": "NON_SOVEREIGN_RENDER_RECEIPT_V3", "authority_status": "NON_SOVEREIGN_SANDBOX",
        "canon": "NO_SHIP", "generated_at": now_iso(), "pilot": "director_pilot_v8b",
        "sources": [str(IMG1), str(IMG2), str(IMG3)],
        "artifact": str(out), "artifact_sha256": sha256_file(out),
        "method": "ffmpeg_3image_xfade_postproduction", "duration_s": 30,
        "format": f"{W}x{H}", "credits_spent": 0,
        "technique": "zoompan+xfade_dissolve+vignette+grain+pulse+grade+fadeinout",
        "telegram_msg_id": mid, "status": "RATING_PENDING",
        "operator_decision": None, "pipeline_score": None, "output_score": None,
    }
    rp = OUT_DIR / "render_receipt_v8b.json"
    rp.write_text(json.dumps(receipt, indent=2))

    print()
    print("="*55)
    print("PILOT 8B — 3-image dissolve presence film")
    print(f"  mp4     : {out}")
    print(f"  telegram: msg {mid}")
    print(f"  status  : RATING_PENDING — BLOCKED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
