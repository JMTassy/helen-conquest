"""Telegram post — bot upload + caption pack.

Sends the assembled video + a caption (WULmoji-graded text, per enhancer skill
rules: max 1 emoji per line, never as a claim) to the operator Telegram chat.

Secrets: reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment. Does
NOT print token values. If TELEGRAM_CHAT_ID is unset, defaults to operator's
chat_id from project memory.

Pure stdlib urllib (pip-free).

Usage:
    export TELEGRAM_BOT_TOKEN=...
    python3 scripts/telegram_post.py <video.mp4>
        [--caption-file path.md] [--caption "inline text"] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

DEFAULT_CHAT_ID = "6624890918"
TG_API = "https://api.telegram.org/bot{token}/sendVideo"

CAPTION_TEMPLATE = """\
\U0001f3ac HELEN arc v0.4 — sparse keyframe render
\U0001f4ca {n_keyframes} keyframes over {duration:.0f}s
\U0001f534 stub embedder (pixel_hash); MIA v2 pending operator ratings
\u26aa clone_from_latent TODO — ref-set surrogate until G() is wired
"""


def build_caption(manifest_path: Path | None, extra: str | None) -> str:
    lines = [CAPTION_TEMPLATE]
    if manifest_path and manifest_path.exists():
        m = json.loads(manifest_path.read_text())
        if m.get("counts"):
            c = m["counts"]
            lines.append(f"\n\u2705 {c.get('green', 0)}  \u26a0\ufe0f {c.get('yellow', 0)}  \u274c {c.get('red', 0)}  mirror oracle")
    if extra:
        lines.append(f"\n{extra}")
    return "".join(lines)


def post_video(token: str, chat_id: str, video: Path, caption: str) -> dict:
    import urllib.parse
    import ssl
    boundary = "----helen_arc_boundary_v04"
    body_parts: list[bytes] = []
    def add_field(name: str, value: str):
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body_parts.append(f"{value}\r\n".encode())
    def add_file(name: str, path: Path):
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode()
        )
        body_parts.append(b"Content-Type: video/mp4\r\n\r\n")
        body_parts.append(path.read_bytes())
        body_parts.append(b"\r\n")
    add_field("chat_id", chat_id)
    add_field("caption", caption)
    add_field("supports_streaming", "true")
    add_file("video", video)
    body_parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(body_parts)
    url = TG_API.format(token=token)
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--oracle-report", default=None,
                    help="mirror_oracle.json to include counts in caption")
    ap.add_argument("--caption", default=None)
    ap.add_argument("--caption-file", default=None)
    ap.add_argument("--n-keyframes", type=int, default=12)
    ap.add_argument("--duration", type=float, default=180.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    video = Path(args.video)
    if not video.exists():
        print(f"ERROR: video {video} not found", file=sys.stderr)
        return 2

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", DEFAULT_CHAT_ID)

    global CAPTION_TEMPLATE
    CAPTION_TEMPLATE = CAPTION_TEMPLATE.format(
        n_keyframes=args.n_keyframes, duration=args.duration
    )

    extra = args.caption
    if args.caption_file:
        extra = Path(args.caption_file).read_text()
    caption = build_caption(Path(args.oracle_report) if args.oracle_report else None, extra)

    if args.dry_run or not token:
        reason = "dry-run" if args.dry_run else "TELEGRAM_BOT_TOKEN unset"
        print(f"[telegram_post] {reason}; would send:")
        print(f"  chat_id={chat_id}")
        print(f"  video  ={video}  ({video.stat().st_size} bytes)")
        print(f"  caption:\n{caption}")
        return 0

    result = post_video(token, chat_id, video, caption)
    if result.get("ok"):
        msg_id = result.get("result", {}).get("message_id", "?")
        print(f"[telegram_post] sent  message_id={msg_id}")
        return 0
    else:
        print(f"[telegram_post] ERROR  {result}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
