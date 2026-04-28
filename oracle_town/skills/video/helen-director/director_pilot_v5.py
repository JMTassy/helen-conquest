#!/usr/bin/env python3
"""
HELEN Director — Pilot 5: Compliance Test.
NON_SOVEREIGN. Tests whether Seedance can be forced to obey a single visible constraint.

Constraint: HELEN blinks. Exactly 0.5s later her reflection blinks.
If no delayed blink is visible → output is INVALID.

Schema fix from pilot v2: Seedance requires flat image_url field (not input_image.image_url).
9:16 enforced via ffmpeg post-render (API ignores aspect_ratio param).

Cost: ~10 Higgsfield credits (Seedance Pro I2V 5s).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO      = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parent
SEED_IMG  = SKILL_DIR / "references" / "helen_photoreal_front.jpg"
OUT_DIR   = Path("/tmp/helen_temple")
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

HF_ID     = _env.get("HIGGSFIELD_ID") or _env.get("HF_API_KEY", "")
HF_SECRET = _env.get("HIGGSFIELD_SECRET") or _env.get("HF_API_SECRET", "")
AUTH      = f"Key {HF_ID}:{HF_SECRET}"
BASE      = "https://platform.higgsfield.ai"
UA        = "higgsfield-client-py/1.0"

# ── Compliance prompt — single visible constraint, upfront ────────────────────
PILOT_PROMPT = """COMPLIANCE TEST. ONE RULE ONLY.

HELEN blinks at 2.0s. Her reflection blinks at 2.5s. The 0.5s delay is the only anomaly.

[SETUP]
HELEN close-up portrait. Copper-red wavy hair, blue-grey eyes, fair skin, freckles.
Camera locked. 85mm. Shallow depth of field — face sharp, background soft dark wall.
To her left: a dark mirror showing her reflection. Both subject and reflection visible.
Neutral expression. No movement except the blink.

[TIMELINE — EXACT]
0.0s–2.0s : Both HELEN and reflection completely still. Eyes open.
2.0s       : HELEN blinks. Both eyes close and reopen in 0.2s.
2.0s–2.5s  : Reflection remains open-eyed. This is the anomaly.
2.5s       : Reflection blinks. Same 0.2s duration.
2.5s–5.0s  : Both still again. Eyes open. Nothing else moves.

[STYLE]
Cinematic. 35mm grain. Single warm key light from screen-right. Dark background.
No street. No food. No outdoor scene. No zoom. No camera movement.

[IDENTITY LOCK]
Copper-red hair. Blue-grey eyes. Freckles. Fair skin. Locked for all 5 seconds.

[HARD CONSTRAINTS]
No text. No titles. No symbols. No outdoor. No burger. No zoom motion.
No supernatural glow. No additional anomalies. No morph."""

# ── HTTP helper ───────────────────────────────────────────────────────────────
def hf_req(path: str, method: str = "POST", body=None,
           timeout: int = 60, raw_url: str | None = None) -> tuple[int, str]:
    url = raw_url or (path if path.startswith("http") else f"{BASE}/{path.lstrip('/')}")
    headers = {"Authorization": AUTH, "User-Agent": UA, "Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def enforce_916(src: Path, dst: Path) -> None:
    """Scale + pad to 1080x1920 portrait. Seedance ignores aspect_ratio param."""
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", "scale=1080:608:force_original_aspect_ratio=decrease,"
               "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=24",
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-an",
        str(dst),
    ], check=True, capture_output=True)


def write_render_receipt(mp4_raw: Path, mp4_916: Path, request_id: str,
                         prompt_sha: str, valid: str) -> Path:
    receipt = {
        "schema": "NON_SOVEREIGN_RENDER_RECEIPT_V3",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "generated_at": now_iso(),
        "pilot": "director_pilot_v5",
        "artifact_raw": str(mp4_raw),
        "artifact_916": str(mp4_916),
        "artifact_sha256": sha256_file(mp4_916),
        "artifact_size_bytes": mp4_916.stat().st_size,
        "render_params": {
            "model": "bytedance/seedance/v1/pro/image-to-video",
            "duration_s": 5,
            "seed_image": str(SEED_IMG),
            "prompt_sha256": prompt_sha,
        },
        "higgsfield_request_id": request_id,
        "compliance_test": "delayed_blink_0.5s",
        "compliance_result": valid,
        "operator_decision": None,
        "pipeline_score": None,
        "output_score": None,
    }
    receipt_path = OUT_DIR / "render_receipt_v5.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    return receipt_path


def write_candidate(mp4_916: Path, receipt_path: Path, receipt_sha: str) -> dict:
    candidate = {
        "schema": "MAYOR_PACKET_V1",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "candidate_id": "director_pilot_v5_compliance",
        "artifact": str(mp4_916),
        "render_receipt_path": str(receipt_path),
        "render_receipt_hash": receipt_sha,
        "operator_rating": None,
        "rating_notes": None,
        "status": "RATING_PENDING",
        "block_reason": "No operator_rating received. Absence = BLOCK per SKILL.md §17.",
        "compliance_check": "Does the video show HELEN blink at ~2s and reflection blink ~0.5s later?",
        "obligations": [
            "operator must verify delayed blink is visible",
            "operator must rate pipeline_score 1-10 + output_score 1-10 + KEEP|REJECT",
            "if no delayed blink visible → INVALID regardless of score",
        ],
    }
    candidate_path = OUT_DIR / "candidate_v5.json"
    candidate_path.write_text(json.dumps(candidate, indent=2))
    return candidate


def main() -> int:
    if not HF_ID or not HF_SECRET:
        print("ABORT: HIGGSFIELD credentials missing", file=sys.stderr)
        return 2
    if not SEED_IMG.exists():
        print(f"ABORT: seed not found: {SEED_IMG}", file=sys.stderr)
        return 2

    prompt_sha = sha256_text(PILOT_PROMPT)
    print(f"[PILOT5] compliance_test=delayed_blink_0.5s  prompt_sha={prompt_sha[:16]}…")
    print(f"         seed: {SEED_IMG.name}  credits: ~10")
    print()

    # Step 1: Upload
    print("[1/5] CDN upload URL…")
    code, text = hf_req("/files/generate-upload-url", body={"content_type": "image/jpeg"})
    print(f"      → {code}: {text[:180]}")
    if code != 200:
        print(f"ABORT: {text[:200]}", file=sys.stderr); return 1
    info = json.loads(text)
    public_url, upload_url = info["public_url"], info["upload_url"]

    put_req = urllib.request.Request(
        upload_url, data=SEED_IMG.read_bytes(),
        headers={"Content-Type": "image/jpeg"}, method="PUT",
    )
    try:
        with urllib.request.urlopen(put_req, timeout=60) as r:
            print(f"      PUT {r.status} OK  CDN: {public_url[:70]}…")
    except urllib.error.HTTPError as e:
        print(f"ABORT: PUT {e.code}", file=sys.stderr); return 1

    # Step 2: Submit Seedance (confirmed schema: flat image_url)
    print("\n[2/5] Seedance Pro I2V (confirmed flat image_url schema)…")
    payload = {
        "prompt": PILOT_PROMPT,
        "image_url": public_url,
        "duration": 5,
    }
    code, text = hf_req("/bytedance/seedance/v1/pro/image-to-video", body=payload)
    print(f"      → {code}: {text[:200]}")
    if code not in (200, 201, 202):
        if code == 403:
            print("ABORT: 403 — insufficient credits", file=sys.stderr)
        else:
            print(f"ABORT: submit failed", file=sys.stderr)
        return 1
    data = json.loads(text)
    request_id = data.get("request_id")
    status_url = data.get("status_url")
    print(f"      request_id: {request_id}")

    # Step 3: Poll
    print(f"\n[3/5] Polling…")
    deadline = time.time() + 480
    tick = 0
    output_url = None
    while time.time() < deadline:
        if status_url and status_url.startswith("http"):
            code, text = hf_req(status_url, method="GET", raw_url=status_url, timeout=30)
        else:
            code, text = hf_req(f"/requests/{request_id}/status", method="GET", timeout=30)
        try:
            d = json.loads(text); status = d.get("status", "?")
        except Exception:
            d = {}; status = text[:40]

        tick += 1
        if tick % 4 == 0:
            print(f"      t={int(time.time()%10000)}s  status={status}")

        if status.lower() == "completed":
            output_url = (
                d.get("output_url") or d.get("video_url") or
                (d.get("video") or {}).get("url") or
                (d.get("outputs") or [{}])[0].get("url") or
                d.get("result", {}).get("url")
            )
            print(f"\n      COMPLETED  url={str(output_url)[:80]}")
            break
        elif status.lower() in ("failed", "nsfw", "canceled", "cancelled"):
            print(f"\nABORT: {status}", file=sys.stderr); return 1
        time.sleep(10)
    else:
        print("ABORT: timeout", file=sys.stderr); return 1

    if not output_url:
        print(f"ABORT: no output URL. Response:\n{json.dumps(d,indent=2)[:400]}", file=sys.stderr)
        return 1

    # Step 4: Download raw
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mp4_raw = OUT_DIR / f"pilot5_raw__{ts}.mp4"
    print(f"\n[4/5] Download → {mp4_raw}…")
    urllib.request.urlretrieve(output_url, mp4_raw)
    print(f"      {mp4_raw.stat().st_size//1024} KB raw")

    # Step 5: Enforce 9:16 via ffmpeg
    mp4_916 = OUT_DIR / f"pilot5_916__{ts}.mp4"
    print(f"\n[5/5] ffmpeg 9:16 → {mp4_916}…")
    enforce_916(mp4_raw, mp4_916)
    print(f"      {mp4_916.stat().st_size//1024} KB  1080x1920")

    # Receipts
    receipt_path = write_render_receipt(mp4_raw, mp4_916, request_id, prompt_sha, "PENDING_OPERATOR_VERIFICATION")
    receipt_sha  = sha256_file(receipt_path)
    candidate    = write_candidate(mp4_916, receipt_path, receipt_sha)

    print()
    print("=" * 60)
    print("PILOT 5 OUTPUT")
    print("=" * 60)
    print(f"  mp4 (9:16) : {mp4_916}")
    print(f"  receipt    : {receipt_path}")
    print()
    print("CANDIDATE (RATING_PENDING — BLOCKED):")
    print(json.dumps(candidate, indent=2))
    print()
    print("Compliance check: does the video show HELEN blink at ~2s")
    print("and her reflection blink ~0.5s later?")
    print("INVALID if no delayed blink visible, regardless of score.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
