#!/usr/bin/env python3
"""
HELEN Director — Single-shot render pilot v2.
NON_SOVEREIGN. Tests whether HELEN Director improved since last pilot.

Pipeline:
  1. Upload reference seed (helen_photoreal_front.jpg) → Higgsfield CDN
  2. Submit Seedance Pro I2V (5s, 9:16)
  3. Poll until complete
  4. Download mp4 → /tmp/helen_temple/
  5. Write render_receipt.json (NON_SOVEREIGN_RENDER_RECEIPT_V3)
  6. Print candidate JSON (RATING_PENDING — operator must rate before handoff)

Anomaly class: temporal_lag — a subtle reflection blink that trails the subject
by ~0.5s. One impossible property. Not stacked. SKILL.md §4.

Cost: ~10 Higgsfield credits (Seedance Pro I2V 5s). No Soul T2I call (reuses
existing photoreal reference). Total spend: 10 credits.

Rules:
  - No scaling, no canon promotion, no memory mutation
  - Render receipt written before candidate is presented
  - RATING_PENDING until operator rates 1-10 via Telegram or direct input
  - Absence of rating = BLOCK (SKILL.md §17)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO      = Path(__file__).resolve().parents[3]
SKILL_DIR = Path(__file__).resolve().parent
SEED_IMG  = SKILL_DIR / "references" / "helen_photoreal_front.jpg"
OUT_DIR   = Path("/tmp/helen_temple")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Credentials ───────────────────────────────────────────────────────────────
_env: dict[str, str] = {}
_helen_env = Path.home() / ".helen_env"
if _helen_env.exists():
    for ln in _helen_env.read_text().splitlines():
        ln = ln.strip()
        if ln.startswith("export "):
            ln = ln[7:]
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            _env[k.strip()] = v.strip().strip('"').strip("'")

HF_ID     = _env.get("HIGGSFIELD_ID") or _env.get("HF_API_KEY", "")
HF_SECRET = _env.get("HIGGSFIELD_SECRET") or _env.get("HF_API_SECRET", "")
AUTH      = f"Key {HF_ID}:{HF_SECRET}"
BASE      = "https://platform.higgsfield.ai"
UA        = "higgsfield-client-py/1.0"

# ── Anomaly prompt (temporal_lag class, SKILL.md §4) ─────────────────────────
PILOT_PROMPT = """1080, 9:16, 24fps, 5s.

[SHOT]
Close-up portrait. Camera locked on tripod, zero movement, zero drift.
85mm equivalent, shallow depth of field, subject sharp, background soft.

[SUBJECT]
HELEN. Copper-red wavy hair, medium length. Blue-grey eyes, fair skin, freckles.
Facing camera directly. Neutral expression, fully still.
Near a mirror or dark reflective surface just out of frame left — only her
reflection is visible at the left edge of frame, partial, at ~10% frame width.

[ACTION / ANOMALY — temporal_lag class]
[0s–2s] Subject completely still. Reflection matches subject exactly.
[2.5s]  Subject blinks naturally, both eyes, ~0.15s duration.
[2.5s–3.0s]  Reflection does NOT blink. Reflection remains open-eyed.
[3.0s]  Reflection blinks — ~0.5s after the subject blinked. One beat delayed.
[3.0s–5s]  Both subject and reflection fully still again. Match restored.

One impossible property only. The delay is the anomaly. Nothing else unusual.

[STYLE]
Cinematic film still. Shot on 35mm film grain, ISO 800.
Lighting: single key light from screen-right, warm 3200K. Natural fill only.
Skin: real pores visible. Hair: individual strands, natural movement from
ambient air only — no fan effect, no artificial wind.

[CONSTRAINTS]
Subject identity locked for all 5s: copper-red hair, blue-grey eyes, freckles.
No morph, no drift, no wardrobe change, no geometry shift.
Reflection must visibly trail subject's blink by ~0.5s. This is the only anomaly.

[NEGATIVE]
No text overlay. No titles. No symbols. No glow. No bloom. No lens flare.
No camera movement. No supernatural effects. No additional anomalies.
No AI smoothness. No plastic skin. No perfect symmetry."""

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


# ── Receipt helpers ───────────────────────────────────────────────────────────
def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def write_render_receipt(mp4_path: Path, request_id: str, prompt_sha: str) -> Path:
    artifact_sha = sha256_file(mp4_path)
    receipt = {
        "schema": "NON_SOVEREIGN_RENDER_RECEIPT_V3",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "generated_at": now_iso(),
        "pilot": "director_pilot_v2",
        "artifact": str(mp4_path),
        "artifact_sha256": artifact_sha,
        "artifact_size_bytes": mp4_path.stat().st_size,
        "render_params": {
            "model": "bytedance/seedance/v1/pro/image-to-video",
            "duration_s": 5,
            "seed_image": str(SEED_IMG),
            "prompt_sha256": prompt_sha,
        },
        "higgsfield_request_id": request_id,
        "operator_decision": None,
        "pipeline_score": None,
        "output_score": None,
    }
    receipt_path = OUT_DIR / "render_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2))
    return receipt_path


def write_candidate(mp4_path: Path, receipt_path: Path, receipt_sha: str) -> dict:
    candidate = {
        "schema": "MAYOR_PACKET_V1",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "candidate_id": "director_pilot_v2_shot1",
        "artifact": str(mp4_path),
        "render_receipt_path": str(receipt_path),
        "render_receipt_hash": receipt_sha,
        "operator_rating": None,
        "rating_notes": None,
        "status": "RATING_PENDING",
        "block_reason": "No operator_rating received. Absence = BLOCK per SKILL.md §17.",
        "obligations": [
            "operator must rate KEEP|REJECT + pipeline_score 1-10 + output_score 1-10",
            "rating required before status advances to READY_FOR_HAL",
        ],
    }
    candidate_path = OUT_DIR / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2))
    return candidate


def main() -> int:
    if not HF_ID or not HF_SECRET:
        print("ABORT: HIGGSFIELD_ID / HIGGSFIELD_SECRET not in env", file=sys.stderr)
        return 2

    if not SEED_IMG.exists():
        print(f"ABORT: seed image not found: {SEED_IMG}", file=sys.stderr)
        return 2

    prompt_sha = sha256_text(PILOT_PROMPT)
    print(f"[PILOT] director_pilot_v2  prompt_sha={prompt_sha[:16]}…")
    print(f"        seed: {SEED_IMG.name}  out: {OUT_DIR}")
    print(f"        anomaly_class: temporal_lag  duration: 5s  credits: ~10")
    print()

    # ── Step 1: Upload seed ───────────────────────────────────────────────────
    print("[1/4] Requesting CDN upload URL…")
    code, text = hf_req("/files/generate-upload-url", body={"content_type": "image/jpeg"})
    print(f"      → {code}: {text[:200]}")
    if code != 200:
        print(f"ABORT: upload-url failed: {text[:300]}", file=sys.stderr)
        return 1
    info = json.loads(text)
    public_url = info["public_url"]
    upload_url = info["upload_url"]
    print(f"      CDN: {public_url[:80]}…")

    print("[1/4] PUT seed image…")
    put_req = urllib.request.Request(
        upload_url, data=SEED_IMG.read_bytes(),
        headers={"Content-Type": "image/jpeg"}, method="PUT",
    )
    try:
        with urllib.request.urlopen(put_req, timeout=60) as r:
            print(f"      PUT {r.status} OK")
    except urllib.error.HTTPError as e:
        print(f"ABORT: PUT failed {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        return 1

    # ── Step 2: Submit Seedance Pro I2V ───────────────────────────────────────
    print("\n[2/4] Submitting Seedance Pro I2V (5s, 9:16)…")
    seedance_payloads = [
        {
            "prompt": PILOT_PROMPT,
            "input_image": {"type": "image_url", "image_url": public_url},
            "duration": 5,
            "resolution": "1080",
            "aspect_ratio": "9:16",
        },
        {
            "prompt": PILOT_PROMPT,
            "input_image": {"type": "image_url", "image_url": public_url},
            "duration": 5,
        },
        {
            "prompt": PILOT_PROMPT,
            "image_url": public_url,
            "duration": 5,
        },
    ]
    request_id = None
    status_url = None
    for i, payload in enumerate(seedance_payloads):
        code, text = hf_req("/bytedance/seedance/v1/pro/image-to-video", body=payload)
        print(f"      attempt {i+1}: {code} — {text[:200]}")
        if code in (200, 201, 202):
            data = json.loads(text)
            request_id = data.get("request_id")
            status_url = data.get("status_url")
            print(f"      request_id: {request_id}  status_url: {str(status_url)[:80]}")
            break
        if code == 403:
            print("ABORT: 403 — insufficient credits or auth. Check platform.higgsfield.ai/billing",
                  file=sys.stderr)
            return 1

    if not request_id:
        print(f"ABORT: could not submit Seedance job. Last response: {text[:300]}", file=sys.stderr)
        return 1

    # ── Step 3: Poll ──────────────────────────────────────────────────────────
    print(f"\n[3/4] Polling (request_id={request_id})…")
    deadline = time.time() + 480
    tick = 0
    output_url = None
    while time.time() < deadline:
        if status_url and status_url.startswith("http"):
            code, text = hf_req(status_url, method="GET", raw_url=status_url, timeout=30)
        else:
            code, text = hf_req(f"/requests/{request_id}/status", method="GET", timeout=30)
        try:
            data = json.loads(text)
            status = data.get("status", "?")
        except Exception:
            status = text[:60]

        tick += 1
        if tick % 4 == 0:
            print(f"      t={int(time.time() % 10000)}s  status={status}")

        if status.lower() in ("completed",):
            output_url = (
                data.get("output_url") or
                data.get("video_url") or
                (data.get("video") or {}).get("url") or
                (data.get("outputs") or [{}])[0].get("url") or
                data.get("result", {}).get("url")
            )
            print(f"\n      COMPLETED  output_url={str(output_url)[:100]}")
            break
        elif status.lower() in ("failed", "nsfw", "canceled", "cancelled"):
            print(f"\nABORT: render {status} — {json.dumps(data)[:300]}", file=sys.stderr)
            return 1

        time.sleep(10)
    else:
        print("\nABORT: 8-minute timeout. Check status manually.", file=sys.stderr)
        print(f"  status_url: {status_url}")
        return 1

    if not output_url:
        print(f"ABORT: completed but no output URL found. Full response:\n{json.dumps(data, indent=2)[:600]}",
              file=sys.stderr)
        return 1

    # ── Step 4: Download ──────────────────────────────────────────────────────
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    mp4_path = OUT_DIR / f"director_pilot_v2__{ts}.mp4"
    print(f"\n[4/4] Downloading → {mp4_path}…")
    urllib.request.urlretrieve(output_url, mp4_path)
    size_kb = mp4_path.stat().st_size // 1024
    print(f"      {size_kb} KB  OK")

    # ── Receipts & candidate ──────────────────────────────────────────────────
    receipt_path = write_render_receipt(mp4_path, request_id, prompt_sha)
    receipt_sha  = sha256_file(receipt_path)
    candidate    = write_candidate(mp4_path, receipt_path, receipt_sha)

    print()
    print("=" * 60)
    print("PILOT OUTPUT")
    print("=" * 60)
    print(f"  mp4     : {mp4_path}")
    print(f"  receipt : {receipt_path}")
    print(f"  receipt_sha : {receipt_sha[:32]}…")
    print()
    print("CANDIDATE (RATING_PENDING — BLOCKED):")
    print(json.dumps(candidate, indent=2))
    print()
    print("Next: operator rates 1-10. Rating required before handoff to HAL/MAYOR.")
    print("      Absence of rating = BLOCK per SKILL.md §17.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
