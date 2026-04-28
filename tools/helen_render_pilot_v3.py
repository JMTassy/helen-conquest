#!/usr/bin/env python3
"""
HELEN render pilot v3 — single 5s render, receipt-first, rating-deferred.

Contract from operator (NEW DIRECTOR PILOT verb, 2026-04-28):
- Generate exactly ONE 5-second render candidate.
- No scaling, no canon promotion, no memory mutation.
- Write render_receipt.json (always — even without rating).
- Require operator_rating before candidate handoff.
- If no rating: status = RATING_PENDING / BLOCK (do not crash).
- Output: mp4 path + receipt path + candidate JSON.

Differs from v2: v2 fail-fasts at parse time if --operator-decision/scores are
missing (strict-pre). v3 always renders and always writes a receipt; the
status field reflects the rating state. Candidate handoff blocks on
RATING_PENDING but the artifacts persist for later rating.

Differs from v2 prompt: this prompt explicitly asks for ONE subtle impossible
anomaly + more aliveness + less static framing. Identity invariants still
locked. Festival aesthetic.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_parser = argparse.ArgumentParser(description="HELEN render pilot v3 — single render, receipt-first")
_parser.add_argument("--pipeline-score", type=int, default=None, help="1-10")
_parser.add_argument("--output-score", type=int, default=None, help="1-10")
_parser.add_argument("--operator-decision", choices=["KEEP", "REJECT"], default=None)
_parser.add_argument("--failure-class", type=str, default=None)
_ARGS = _parser.parse_args()


def _check_score(name: str, value: int | None) -> None:
    if value is not None and not (1 <= value <= 10):
        raise RuntimeError(f"INVALID_SCORE — --{name} {value} out of range 1-10")


# v3 semantics: scores out of range are still hard errors (caught at parse) but
# missing scores are NOT — the receipt just lands as RATING_PENDING.
_check_score("pipeline-score", _ARGS.pipeline_score)
_check_score("output-score", _ARGS.output_score)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


env: dict[str, str] = {}
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

if not (HF_ID and HF_SECRET):
    sys.exit("FAIL: Higgsfield credentials missing")
if not TELEGRAM_BOT_TOKEN:
    sys.exit("FAIL: TELEGRAM_BOT_TOKEN missing")

OUT = Path("/tmp/helen_render_pilot_v3")
OUT.mkdir(parents=True, exist_ok=True)
CHAT_ID = 6624890918

SEED_PATH = Path(
    "/Users/jean-marietassy/Desktop/HELEN_OS_PICS/HELEN_AVATAR/"
    "hf_20260411_225542_5f020418-d6e6-4716-b8bb-169f6c12bf53.png"
)
if not SEED_PATH.exists():
    sys.exit(f"FAIL: seed not found at {SEED_PATH}")

# v3 ANIMATION PROMPT — operator brief: more alive, less static, ONE subtle impossible
# anomaly (reflection/eye/light/water), no text, festival-grade, 5s exact. Identity
# still locked: copper-red wavy hair, blue-grey eyes, fair skin, freckles preserved.
ANIMATION_PROMPT = (
    "1080px, 9:16, 24fps, 5 seconds exact. Festival-grade cinematic, painterly restraint. "
    "Subject: HELEN — copper-red wavy hair, blue-grey eyes, fair skin, freckle pattern. "
    "Identity invariants locked across all 5 seconds: hair colour, hair length, eye colour, "
    "freckle pattern, garment folds. No facial morph, no head turn, no pose change beyond "
    "small natural breath and slow soft blink.\n\n"
    "MOTION (more alive than locked-tripod pilots): gentle camera-breath drift (≤2px/s "
    "at 1080), subtle parallax of background depth, soft ambient light shift across the 5s. "
    "Subject: natural breathing, one slow blink, faint hair-tip strand movement.\n\n"
    "ANOMALY (exactly ONE subtle impossible element): the reflection in HELEN's iris does "
    "not match the visible scene — it shows a glint of distant warm light no source "
    "explains. Restrained, almost imperceptible, painterly. Festival audience leans in.\n\n"
    "FORBIDDEN: text overlay, captions, watermarks, supernatural glow beyond the single "
    "anomaly, multiple anomalies, extra figures, camera zoom or push, hard cuts."
)

HF_AUTH = f"Key {HF_ID}:{HF_SECRET}"
HF_BASE = "https://platform.higgsfield.ai"
HF_UA = "higgsfield-client-py/1.0"


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


print(f"[1/6] Using existing seed: {SEED_PATH.name}")
print(f"      size: {SEED_PATH.stat().st_size/1024/1024:.2f} MB")

print("[2/6] Higgsfield CDN upload URL...")
code, text = hf_req("/files/generate-upload-url", body={"content_type": "image/png"})
if code != 200:
    sys.exit(f"FAIL upload-url: {code}: {text[:300]}")
info = json.loads(text)
public_url = info["public_url"]
upload_url = info["upload_url"]
print(f"      public_url: {public_url[:80]}...")

print("[3/6] PUT seed to CDN...")
put_req = urllib.request.Request(
    upload_url,
    data=SEED_PATH.read_bytes(),
    headers={"Content-Type": "image/png"},
    method="PUT",
)
try:
    with urllib.request.urlopen(put_req, timeout=120) as r:
        print(f"      PUT {r.status} OK")
except urllib.error.HTTPError as e:
    sys.exit(f"FAIL PUT: {e.code} {e.read().decode()[:300]}")

print("[4/6] Submit Kling I2V (5s, 1080p, 9:16)...")
payload = {
    "prompt": ANIMATION_PROMPT,
    "input_image": {"type": "image_url", "image_url": public_url},
    "duration": 5,
    "resolution": "1080",
    "aspect_ratio": "9:16",
}
code, text = hf_req("/kling", body=payload)
if code not in (200, 201, 202):
    if code == 403:
        sys.exit("FAIL Kling: 403 Not enough credits — top up at platform.higgsfield.ai/billing")
    sys.exit(f"FAIL Kling submit {code}: {text[:400]}")
sub_data = json.loads(text)
request_id = sub_data.get("request_id")
status_url = sub_data.get("status_url")
print(f"      request_id: {request_id}")

print("[5/6] Polling until completed (max 5 min)...")
deadline = time.time() + 300
out_path = None
last_status = "?"
poll_n = 0
while time.time() < deadline:
    if status_url and status_url.startswith("http"):
        code, text = hf_req(status_url, raw_url=status_url, method="GET")
    else:
        code, text = hf_req(f"/requests/{request_id}/status", method="GET")
    try:
        data = json.loads(text)
        status = data.get("status", "?")
    except Exception:
        status = text[:60]

    poll_n += 1
    if status != last_status or poll_n % 6 == 0:
        print(f"      poll {poll_n}: status={status}")
    last_status = status

    if status in ("COMPLETED", "completed"):
        output_url = (
            data.get("output_url")
            or data.get("video_url")
            or (data.get("video") or {}).get("url")
            or (data.get("outputs") or [{}])[0].get("url")
            or data.get("result", {}).get("url")
        )
        if not output_url:
            sys.exit(f"FAIL no output URL: {json.dumps(data, indent=2)[:600]}")
        out_path = OUT / "pilot_v3.mp4"
        urllib.request.urlretrieve(output_url, out_path)
        print(f"      ✓ COMPLETED → {out_path} ({out_path.stat().st_size/1024:.0f} KB)")
        break
    if status in ("FAILED", "failed", "NSFW", "CANCELED", "cancelled"):
        sys.exit(f"FAIL Kling {status}: {json.dumps(data, indent=2)[:600]}")
    time.sleep(5)

if not out_path:
    sys.exit(f"TIMEOUT 5 min — manual check: {status_url}")

print("[6/6] Telegram sendVideo...")
caption = (
    "HELEN render pilot v3 — Higgsfield Kling I2V (5s, 1080p, 9:16, festival-grade). "
    "Brief: more alive than v2, less static, ONE subtle impossible iris-reflection anomaly. "
    "Receipt: RATING_PENDING (operator must rate before candidate handoff)."
)
result = subprocess.run(
    [
        "curl", "-s", "-X", "POST",
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo",
        "-F", f"chat_id={CHAT_ID}",
        "-F", f"video=@{out_path}",
        "-F", f"caption={caption}",
    ],
    capture_output=True, text=True, timeout=180,
)
try:
    tg_data = json.loads(result.stdout)
except Exception:
    sys.exit(f"FAIL telegram parse: {result.stdout[:400]}")
if not tg_data.get("ok"):
    sys.exit(f"FAIL telegram: {result.stdout[:400]}")
msg_id = tg_data["result"]["message_id"]
duration = tg_data["result"].get("video", {}).get("duration", "?")
print(f"      ✓ telegram msg_id={msg_id} duration={duration}s")

# ── Render receipt (always written; status reflects rating state) ──
receipt_path = OUT / "render_receipt.json"

# Determine status based on what was provided at invocation
all_present = all([
    _ARGS.operator_decision is not None,
    _ARGS.pipeline_score is not None,
    _ARGS.output_score is not None,
])
status = "VALIDATED" if all_present else "RATING_PENDING"

receipt = {
    "schema": "RENDER_RECEIPT",
    "schema_version": 3,
    "authority_status": "NON_SOVEREIGN_RENDER_RECEIPT",
    "pilot": "v3",
    "status": status,  # VALIDATED | RATING_PENDING
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z") or time.strftime("%Y-%m-%dT%H:%M:%S"),
    "seed_path": str(SEED_PATH),
    "seed_sha256": _sha256_file(SEED_PATH),
    "prompt_text": ANIMATION_PROMPT,
    "prompt_sha256": _sha256_text(ANIMATION_PROMPT),
    "model_endpoint": "/kling",
    "provider_model": "kling",
    "model_version": sub_data.get("model_version") or sub_data.get("version"),
    "higgsfield_request_id": request_id,
    "higgsfield_status_url": status_url,
    "output_path": str(out_path),
    "output_sha256": _sha256_file(out_path),
    "output_size_bytes": out_path.stat().st_size,
    "output_duration_seconds": duration,
    "telegram_chat_id": CHAT_ID,
    "telegram_msg_id": msg_id,
    "operator_decision": _ARGS.operator_decision,
    "pipeline_score": _ARGS.pipeline_score,
    "output_score": _ARGS.output_score,
    "failure_class": _ARGS.failure_class,
}
receipt_path.write_text(json.dumps(receipt, indent=2))
print(f"      ✓ receipt → {receipt_path}  status={status}")

# ── Candidate JSON (MAYOR_PACKET_V1 shape; status reflects handoff readiness) ──
candidate_path = OUT / "candidate.json"
candidate_status = "READY_FOR_REDUCER" if status == "VALIDATED" else "BLOCK_RATING_PENDING"
candidate = {
    "schema": "MAYOR_PACKET_V1",
    "authority_status": "NON_SOVEREIGN_PACKETIZER",
    "candidate_id": 1,
    "intent_sha256": _sha256_text(ANIMATION_PROMPT),
    "claim": "v3 single-render candidate produced; awaiting operator rating before handoff",
    "obligations": [
        "operator must provide --operator-decision KEEP|REJECT",
        "operator must provide --pipeline-score 1-10",
        "operator must provide --output-score 1-10",
        "if KEEP: clip is canon-candidate, propose via standard chain",
        "if REJECT: optionally set --failure-class for diagnosis",
    ],
    "receipts": [str(receipt_path)],
    "manifest": {
        "render_artifact": str(out_path),
        "render_sha256": _sha256_file(out_path),
        "telegram_msg_id": msg_id,
        "duration_seconds": duration,
        "prompt_intent": "more alive, less static, one subtle impossible iris-reflection anomaly, festival-grade",
        "identity_invariants_locked": True,
    },
    "status": candidate_status,
}
candidate_path.write_text(json.dumps(candidate, indent=2))
print(f"      ✓ candidate → {candidate_path}  status={candidate_status}")

print()
print("=== HELEN RENDER PILOT v3 — RESULT ===")
print(f"mp4 path:       {out_path}")
print(f"receipt path:   {receipt_path}")
print(f"candidate path: {candidate_path}")
print(f"status:         {status}  (candidate: {candidate_status})")
print(f"Telegram msg:   {msg_id} (chat={CHAT_ID}, duration={duration}s)")
if status == "RATING_PENDING":
    print()
    print("HANDOFF BLOCKED: operator must rate before this candidate can graduate.")
    print("To rate, re-run with all three flags:")
    print(f"  --operator-decision KEEP|REJECT --pipeline-score N --output-score N")
    print("(Note: re-run will produce a new render and new receipt; for rating the")
    print(" existing artifact, edit the receipt directly or extend with a sidecar.)")
