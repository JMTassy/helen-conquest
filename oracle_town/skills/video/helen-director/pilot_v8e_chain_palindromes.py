#!/usr/bin/env python3
"""
HELEN Director — Pilot 8E: CHAIN PALINDROMES.
NON_SOVEREIGN. $0 — ffmpeg only on existing single-shot footage.

Three single-shot sources (none are pre-cuts), each palindromed fwd+rev to 10s,
chained in sequence to a 30s real montage:

  A  Pilot 5     (Seedance HELEN zoom)         5s native, 1080×1920
  B  My v3       (Kling iris-anomaly)          5s, 828×1112 → scale+crop to 1080×1920
  C  shot4_eye   (Kling close-up + slow blink) 5s, 828×1112 → scale+crop to 1080×1920

Sequence (each source palindromed fwd 5s + rev 5s = 10s):
  0:00-0:05  A_fwd      HELEN zoom in
  0:05-0:10  A_rev      HELEN unzoom (seamless cut at end-frame = start-frame)
  0:10-0:15  B_fwd      iris reflection forward
  0:15-0:20  B_rev      iris unforward
  0:20-0:25  C_fwd      eye contact + blink
  0:25-0:30  C_rev      blink un-blink + eye contact

Per SKILL.md §16 palindrome property: end-frame of rev IS start-frame of fwd,
so palindrome cuts are seamless. Cross-source cuts (A→B, B→C) are hard cuts
but happen at moments of similar visual register (HELEN portrait → HELEN
portrait → HELEN portrait), so cohesion holds.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = Path("/tmp/helen_pilot_8e")
OUT.mkdir(parents=True, exist_ok=True)
SEGS = OUT / "segments"
SEGS.mkdir(exist_ok=True)

CHAT_ID = 6624890918

SOURCE_A = Path("/tmp/helen_temple/pilot5_916__20260428_170718.mp4")
SOURCE_B = Path("/tmp/helen_render_pilot_v3/pilot_v3.mp4")
SOURCE_C = Path("/tmp/helen_teaser_60s/shots/shot4_eye_contact.mp4")

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
if not TELEGRAM_BOT_TOKEN:
    sys.exit("FAIL: TELEGRAM_BOT_TOKEN missing")

for src in (SOURCE_A, SOURCE_B, SOURCE_C):
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


def normalize_5s(src: Path, dst: Path) -> bool:
    """Scale+crop to 1080×1920 24fps yuv420p, 5s. Identical to teaser pipeline."""
    cmd = [
        "ffmpeg", "-y", "-i", str(src), "-t", "5",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=24",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-an", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  normalize fail {src.name}: {e.stderr[-300:]}")
        return False


def reverse_5s(src_normalized: Path, dst: Path) -> bool:
    """Reverse a 5s normalized clip."""
    cmd = [
        "ffmpeg", "-y", "-i", str(src_normalized),
        "-vf", "reverse,fps=24",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-an", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  reverse fail: {e.stderr[-300:]}")
        return False


def concat(segs: list[Path], dst: Path) -> bool:
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
        print(f"  concat fail: {e.stderr[-300:]}")
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
    print(f"=== HELEN Director — Pilot 8E — Chain Palindromes ===")
    print(f"Sources:")
    print(f"  A  Pilot 5      (Seedance HELEN zoom)")
    print(f"  B  My v3        (Kling iris)")
    print(f"  C  shot4_eye    (Kling close-up blink)")
    print(f"Method: each source → 5s fwd + 5s rev = 10s palindrome; chain 3 = 30s")
    print(f"Cost:   $0 (ffmpeg only)")
    print()

    sources = [
        ("A_pilot5", SOURCE_A),
        ("B_v3",     SOURCE_B),
        ("C_shot4",  SOURCE_C),
    ]

    final_segments: list[Path] = []
    for tag, src in sources:
        print(f"[{tag}] normalizing 5s window...")
        norm = SEGS / f"{tag}_norm.mp4"
        if not normalize_5s(src, norm):
            sys.exit(f"FAIL: normalize {tag}")
        print(f"[{tag}] reversing...")
        rev = SEGS / f"{tag}_rev.mp4"
        if not reverse_5s(norm, rev):
            sys.exit(f"FAIL: reverse {tag}")
        final_segments.append(norm)
        final_segments.append(rev)

    print(f"[concat] chaining 6 segments → 30s palindrome chain...")
    final = OUT / "PILOT_8E_CHAIN_PALINDROMES_916.mp4"
    if not concat(final_segments, final):
        sys.exit("FAIL: concat")
    print(f"    final: {final}  size: {final.stat().st_size/1024/1024:.2f} MB  duration: ~30s")

    caption = (
        "PILOT 8E — Chain palindromes (NON_SOVEREIGN, $0). "
        "3 single-shot sources × fwd+rev each = 30s real montage. "
        "Source A: Seedance zoom · B: Kling iris · C: Kling blink. "
        "Status: RATING_PENDING."
    )
    msg_id = telegram_send(final, caption)

    receipt = {
        "schema": "RENDER_RECEIPT",
        "schema_version": 3,
        "authority_status": "NON_SOVEREIGN_RENDER_RECEIPT",
        "pilot": "8E",
        "method": "ffmpeg_chain_palindromes",
        "status": "RATING_PENDING",
        "generated_at": now_iso(),
        "sources": {
            "A_pilot5":      {"path": str(SOURCE_A), "sha256": sha256_file(SOURCE_A), "engine": "seedance"},
            "B_v3":          {"path": str(SOURCE_B), "sha256": sha256_file(SOURCE_B), "engine": "kling"},
            "C_shot4":       {"path": str(SOURCE_C), "sha256": sha256_file(SOURCE_C), "engine": "kling"},
        },
        "transformations": ["A_fwd", "A_rev", "B_fwd", "B_rev", "C_fwd", "C_rev"],
        "duration_seconds": 30,
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
        "claim": "Pilot 8E chain-palindrome candidate produced; awaiting operator rating",
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
            "duration_seconds": 30,
            "format": "1080x1920 9:16 24fps",
            "method": "ffmpeg_chain_palindromes_§16",
            "credits_spent": 0,
            "sources_count": 3,
        },
        "status": "BLOCK_RATING_PENDING",
    }
    candidate_path = OUT / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2))

    print()
    print("=== PILOT 8E COMPLETE ===")
    print(f"mp4:       {final}")
    print(f"receipt:   {receipt_path}")
    print(f"candidate: {candidate_path}")
    print(f"telegram:  msg {msg_id}")
    print(f"status:    RATING_PENDING")
    return 0


if __name__ == "__main__":
    sys.exit(main())
