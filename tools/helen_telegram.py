#!/usr/bin/env python3
"""
HELEN Telegram Bot — Two-way dialogue with voice
Polls for messages, runs them through helen_say + kernel,
generates Zephyr TTS, sends back voice + text.

Usage:
    GEMINI_API_KEY=... python3 tools/helen_telegram.py

Requires: kernel daemon running (oracle_town/kernel/kernel_daemon.py)
"""
import json
import os
import re
import subprocess
import sys
import time
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELEN_SAY = ROOT / "tools" / "helen_say.py"
HELEN_TTS = ROOT / "oracle_town" / "skills" / "voice" / "gemini_tts" / "helen_tts.py"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
LEDGER = ROOT / "town" / "ledger_v1.ndjson"

# Config from openclaw.json
OPENCLAW_CFG = Path.home() / ".openclaw" / "openclaw.json"
with open(OPENCLAW_CFG) as f:
    cfg = json.load(f)
BOT_TOKEN = cfg["channels"]["telegram"]["botToken"]

GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
POLL_INTERVAL = 2  # seconds
OFFSET_FILE = Path.home() / ".openclaw" / "telegram" / "helen-bot-offset.json"

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def load_offset() -> int:
    if OFFSET_FILE.exists():
        try:
            return json.loads(OFFSET_FILE.read_text()).get("offset", 0)
        except Exception:
            pass
    return 0


def save_offset(offset: int):
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_FILE.write_text(json.dumps({"offset": offset}))


def tg_api(method: str, **kwargs):
    """Call Telegram Bot API."""
    import urllib.request
    import urllib.parse
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    # Handle file uploads separately
    files = {}
    data = {}
    for k, v in kwargs.items():
        if isinstance(v, Path) or (isinstance(v, str) and os.path.isfile(v)):
            files[k] = v
        else:
            data[k] = str(v)

    if files:
        # Use curl for multipart (simpler than urllib multipart)
        cmd = ["curl", "-s", "-X", "POST", url]
        for k, v in data.items():
            cmd += ["-F", f"{k}={v}"]
        for k, v in files.items():
            cmd += ["-F", f"{k}=@{v}"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout)
    else:
        payload = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=payload)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())


def get_updates(offset: int):
    return tg_api("getUpdates", offset=offset, timeout=20)


def send_text(chat_id, text):
    # Telegram max message length is 4096
    text = text[:4000]
    return tg_api("sendMessage", chat_id=chat_id, text=text)


def send_voice(chat_id, ogg_path, caption=""):
    return tg_api("sendVoice", chat_id=chat_id, voice=ogg_path, caption=caption[:1024])


def helen_say(msg: str) -> tuple[str, str]:
    """Run helen_say, return (her_text, verdict)."""
    try:
        r = subprocess.run(
            ["python3", str(HELEN_SAY), msg, "--ledger", str(LEDGER)],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT)
        )
        clean = ANSI_RE.sub('', r.stdout + r.stderr)
        her_text = ""
        verdict = "?"
        lines = clean.split("\n")
        in_her = False
        her_lines = []
        for line in lines:
            if "[HER]" in line:
                in_her = True
                continue
            if "[HAL]" in line:
                in_her = False
                if "PASS" in line: verdict = "PASS"
                elif "BLOCK" in line: verdict = "BLOCK"
                elif "WARN" in line: verdict = "WARN"
                continue
            if in_her and line.strip():
                her_lines.append(line.strip())
        her_text = "\n".join(her_lines)
        return (her_text or msg, verdict)
    except Exception as e:
        return (f"[kernel error: {e}]", "BLOCK")


def generate_voice(text: str) -> str | None:
    """Generate TTS, convert to OGG for Telegram voice note. Returns path or None."""
    if not GEMINI_KEY:
        return None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = GEMINI_KEY
            r = subprocess.run(
                [str(VENV_PYTHON), str(HELEN_TTS), "--output-dir", tmp, text],
                capture_output=True, text=True, timeout=30, env=env, cwd=str(ROOT)
            )
            wav_path = None
            for line in r.stdout.split("\n"):
                if line.startswith("Audio:"):
                    wav_path = line.split("Audio:")[-1].strip()
                    break
            if not wav_path or not os.path.exists(wav_path):
                return None
            # Convert WAV to OGG (Telegram voice notes need opus/ogg)
            ogg_path = wav_path.replace(".wav", ".ogg")
            subprocess.run(
                ["ffmpeg", "-y", "-i", wav_path, "-c:a", "libopus", "-b:a", "64k", ogg_path],
                capture_output=True, timeout=15
            )
            if os.path.exists(ogg_path):
                # Copy to a stable tmp path (the tempdir will be cleaned)
                stable = f"/tmp/helen_voice_{int(time.time())}.ogg"
                subprocess.run(["cp", ogg_path, stable])
                return stable
    except Exception as e:
        print(f"  [TTS error] {e}")
    return None


def handle_message(msg: dict):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    user = msg.get("from", {}).get("first_name", "?")

    if not text:
        return

    print(f"  [{user}] {text}")

    # Run through kernel
    her_text, verdict = helen_say(text)
    print(f"  [HELEN {verdict}] {her_text[:80]}")

    # Send text response immediately
    reply = f"[HAL {verdict}]\n{her_text}"
    send_text(chat_id, reply)

    # Generate and send voice (async-ish)
    # Speak only the ACK/receipt part, not the full dump
    speak_text = her_text.split("\n")[0] if her_text else text
    voice_path = generate_voice(speak_text)
    if voice_path:
        try:
            send_voice(chat_id, voice_path, caption="Zephyr")
            os.remove(voice_path)
            print(f"  [voice sent]")
        except Exception as e:
            print(f"  [voice send error] {e}")


def main():
    print(f"HELEN Telegram Bot")
    print(f"  Bot: {BOT_TOKEN[:12]}...")
    print(f"  Voice: {'Zephyr (Gemini TTS)' if GEMINI_KEY else 'OFF (no GEMINI_API_KEY)'}")
    print(f"  Kernel: {HELEN_SAY}")
    print(f"  Polling every {POLL_INTERVAL}s...")
    print()

    offset = load_offset()

    while True:
        try:
            updates = get_updates(offset)
            if not updates.get("ok"):
                print(f"  [poll error] {updates}")
                time.sleep(5)
                continue

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                save_offset(offset)
                if "message" in update:
                    handle_message(update["message"])

        except KeyboardInterrupt:
            print("\nStopped.")
            break
        except Exception as e:
            print(f"  [error] {e}")
            time.sleep(5)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
