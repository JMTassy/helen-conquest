#!/usr/bin/env python3
"""
HELEN Director — Pilot 8D: EATING PALINDROME.
NON_SOVEREIGN. $0 — ffmpeg only on existing footage.

Source: PILOT_4_BURGER_STREET_CUT_916.mp4 (1080×1920, 24fps, 20s)
Pick a 5s "money shot" segment, then palindrome it via §16 recomposition.

Sequence:
  0:00-0:05  fwd            (5s)   bite forward
  0:05-0:15  slow_fwd 2×    (10s)  bite extended, dreamlike
  0:15-0:20  rev            (5s)   un-bite
  0:20-0:30  slow_rev 2×    (10s)  un-bite extended
  TOTAL                    (30s)

Cuts feel seamless because end-frame of rev = start-frame of fwd
(palindrome property per SKILL.md §16).

Pipeline (no Higgsfield calls):
  1. Extract 5s money-shot segment from Pilot 4
  2. Generate 4 transformed clips: fwd, slow_fwd, rev, slow_rev
  3. ffmpeg concat → 30s mp4
  4. Telegram deliver
  5. Write render_receipt + candidate (RATING_PENDING)
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = Path("/tmp/helen_temple/PILOT_4_BURGER_STREET_CUT_916.mp4")
OUT = Path("/tmp/helen_pilot_8d")
OUT.mkdir(parents=True, exist_ok=True)
SEGS = OUT / "segments"
SEGS.mkdir(exist_ok=True)

CHAT_ID = 6624890918

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
if not SOURCE.exists():
    sys.exit(f"FAIL: source missing {SOURCE}")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def make_segment(src: Path, dst: Path, start: float, dur: float,
                 reverse: bool = False, slow_factor: float = 1.0) -> bool:
    """Build one transformed segment via ffmpeg."""
    vf_parts = []
    if reverse:
        vf_parts.append("reverse")
    if slow_factor != 1.0:
        vf_parts.append(f"setpts={slow_factor}*PTS")
    vf_parts.append("fps=24")
    vf = ",".join(vf_parts)
    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-i", str(src), "-t", str(dur),
        "-vf", vf, "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-an", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  segment fail: {e.stderr[-300:]}")
        return False


def concat_segments(segs: list[Path], dst: Path) -> bool:
    """Concat segments via ffmpeg concat demuxer."""
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
    print(f"[5] Telegram sendVideo ({mp4.stat().st_size/1024:.0f} KB)...")
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
    ap = argparse.ArgumentParser(description="HELEN Director Pilot 8D — eating palindrome")
    ap.add_argument("--start", type=float, default=5.0,
                    help="start offset in source seconds (default 5.0 — middle of 20s source)")
    ap.add_argument("--money-shot-dur", type=float, default=5.0,
                    help="duration of the money-shot segment to palindrome (default 5.0)")
    args = ap.parse_args()

    print(f"=== HELEN Director — Pilot 8D — Eating Palindrome ===")
    print(f"Source:        {SOURCE.name}")
    print(f"Money shot:    {args.start}s → {args.start + args.money_shot_dur}s ({args.money_shot_dur}s)")
    print(f"Method:        §16 palindrome (fwd → slow_fwd 2× → rev → slow_rev 2×)")
    print(f"Cost:          $0 (ffmpeg only)")
    print()

    # Build 4 transformed segments
    print("[1] Building forward segment (5s)...")
    fwd = SEGS / "01_fwd.mp4"
    if not make_segment(SOURCE, fwd, args.start, args.money_shot_dur, reverse=False, slow_factor=1.0):
        sys.exit("FAIL: fwd")

    print("[2] Building slow forward segment (10s, 2× slowdown)...")
    slow_fwd = SEGS / "02_slow_fwd.mp4"
    if not make_segment(SOURCE, slow_fwd, args.start, args.money_shot_dur, reverse=False, slow_factor=2.0):
        sys.exit("FAIL: slow_fwd")

    print("[3] Building reverse segment (5s)...")
    rev = SEGS / "03_rev.mp4"
    if not make_segment(SOURCE, rev, args.start, args.money_shot_dur, reverse=True, slow_factor=1.0):
        sys.exit("FAIL: rev")

    print("[4] Building slow reverse segment (10s, 2× slowdown)...")
    slow_rev = SEGS / "04_slow_rev.mp4"
    if not make_segment(SOURCE, slow_rev, args.start, args.money_shot_dur, reverse=True, slow_factor=2.0):
        sys.exit("FAIL: slow_rev")

    # Concat
    print("[5] Concat fwd → slow_fwd → rev → slow_rev → palindrome...")
    final = OUT / "PILOT_8D_EATING_PALINDROME_916.mp4"
    if not concat_segments([fwd, slow_fwd, rev, slow_rev], final):
        sys.exit("FAIL: concat")
    print(f"    final: {final}  size: {final.stat().st_size/1024/1024:.2f} MB  duration: ~30s")

    # Telegram + receipt + candidate
    caption = (
        "PILOT 8D — Eating palindrome (NON_SOVEREIGN, $0). "
        "5s money-shot → fwd / slow_fwd / rev / slow_rev = 30s. "
        "Source: Pilot 4 (existing footage). "
        "Status: RATING_PENDING."
    )
    msg_id = telegram_send(final, caption)

    receipt = {
        "schema": "RENDER_RECEIPT",
        "schema_version": 3,
        "authority_status": "NON_SOVEREIGN_RENDER_RECEIPT",
        "pilot": "8D",
        "method": "ffmpeg_palindrome_recomposition",
        "status": "RATING_PENDING",
        "generated_at": now_iso(),
        "source_path": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "money_shot_start_s": args.start,
        "money_shot_dur_s": args.money_shot_dur,
        "transformations": ["fwd", "slow_fwd_2x", "rev", "slow_rev_2x"],
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
    print(f"    receipt: {receipt_path}")

    candidate = {
        "schema": "MAYOR_PACKET_V1",
        "authority_status": "NON_SOVEREIGN_PACKETIZER",
        "candidate_id": 1,
        "claim": "Pilot 8D eating-palindrome candidate produced; awaiting operator rating",
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
            "method": "ffmpeg_palindrome_§16",
            "credits_spent": 0,
        },
        "status": "BLOCK_RATING_PENDING",
    }
    candidate_path = OUT / "candidate.json"
    candidate_path.write_text(json.dumps(candidate, indent=2))
    print(f"    candidate: {candidate_path}")

    print()
    print("=== PILOT 8D COMPLETE ===")
    print(f"mp4:       {final}")
    print(f"receipt:   {receipt_path}")
    print(f"candidate: {candidate_path}")
    print(f"telegram:  msg {msg_id}")
    print(f"status:    RATING_PENDING")
    return 0


if __name__ == "__main__":
    sys.exit(main())
