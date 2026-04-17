#!/usr/bin/env python3
"""
HELEN Voice — Gemini TTS
=========================
Speaks HELEN's sealed verdicts. Voice = transport, NEVER editor.
Audio carries HAL output verbatim, never softened or rephrased.

Usage:
    python3 oracle_town/skills/voice/gemini_tts/helen_tts.py "text to speak"
    python3 oracle_town/skills/voice/gemini_tts/helen_tts.py --from-receipt R-20260416-0002
    python3 oracle_town/skills/voice/gemini_tts/helen_tts.py --voice Kore "text"
    python3 oracle_town/skills/voice/gemini_tts/helen_tts.py --list-voices

Requires: pip install google-genai
API key: set GEMINI_API_KEY env var (or GOOGLE_API_KEY)

K8 compliance: every audio render produces a sibling .provenance.json
with model, voice, seed, text SHA, audio SHA. NO HASH = NO VOICE.

Ref: https://github.com/GoogleCloudPlatform/generative-ai/blob/main/audio/speech/getting-started/get_started_with_gemini_tts_voices.ipynb
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import wave
from pathlib import Path

# ─── Constants ────────────────────────────────────────────────────────────────

VOICES = [
    "Achernar", "Achird", "Algenib", "Algieba", "Alnilam",
    "Aoede", "Autonoe", "Callirrhoe", "Charon", "Despina",
    "Enceladus", "Erinome", "Fenrir", "Gacrux", "Iapetus",
    "Kore", "Laomedeia", "Leda", "Orus", "Puck",
    "Pulcherrima", "Rasalgethi", "Sadachbia", "Sadaltager", "Schedar",
    "Sulafat", "Umbriel", "Vindemiatrix", "Zephyr", "Zubenelgenubi",
]

HELEN_DEFAULT_VOICE = "Zephyr"
HELEN_DEFAULT_MODEL = "gemini-2.5-flash-preview-tts"
SAMPLE_RATE = 24000
SAMPLE_WIDTH = 2
CHANNELS = 1

REPO_ROOT = Path(__file__).resolve().parents[4]  # helen_os_v1/
ARTIFACTS_AUDIO = REPO_ROOT / "artifacts" / "audio"

# ─── Utilities ────────────────────────────────────────────────────────────────

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def save_wav(path: Path, pcm: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm)


# ─── K8 provenance (NO HASH = NO VOICE) ──────────────────────────────────────

def write_provenance(audio_path: Path, text: str, model: str, voice: str, pcm: bytes) -> Path:
    """Write .provenance.json sidecar. K8 μ_NDARTIFACT requires this."""
    provenance = {
        "schema": "AUDIO_PROVENANCE_V1",
        "timestamp_utc": now_utc_iso(),
        "model": model,
        "voice": voice,
        "sample_rate": SAMPLE_RATE,
        "text_sha256": sha256_hex(text.encode("utf-8")),
        "audio_sha256": sha256_hex(pcm),
        "audio_file": audio_path.name,
        "text_length": len(text),
        "audio_bytes": len(pcm),
        "payload_hash": sha256_hex(canon({
            "model": model,
            "voice": voice,
            "text_sha256": sha256_hex(text.encode("utf-8")),
            "audio_sha256": sha256_hex(pcm),
        })),
    }
    prov_path = audio_path.with_name(audio_path.stem + ".provenance.json")
    prov_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return prov_path


# ─── TTS ──────────────────────────────────────────────────────────────────────

def speak(text: str, voice: str = HELEN_DEFAULT_VOICE, model: str = HELEN_DEFAULT_MODEL,
          output_dir: Path | None = None) -> tuple[Path, Path]:
    """Generate speech from text. Returns (wav_path, provenance_path)."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("ERROR: pip install google-genai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: set GEMINI_API_KEY or GOOGLE_API_KEY env var", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                ),
            ),
        ),
    )

    pcm = response.candidates[0].content.parts[0].inline_data.data

    # Output path
    out = output_dir or ARTIFACTS_AUDIO
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    basename = f"{ts}__{voice.lower()}"
    wav_path = out / f"{basename}.wav"
    save_wav(wav_path, pcm)
    prov_path = write_provenance(wav_path, text, model, voice, pcm)

    return wav_path, prov_path


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="HELEN Voice — Gemini TTS")
    ap.add_argument("text", nargs="*", help="Text to speak (or use --from-receipt)")
    ap.add_argument("--voice", default=HELEN_DEFAULT_VOICE, choices=VOICES,
                    help=f"Voice name (default: {HELEN_DEFAULT_VOICE})")
    ap.add_argument("--model", default=HELEN_DEFAULT_MODEL,
                    help=f"Model (default: {HELEN_DEFAULT_MODEL})")
    ap.add_argument("--output-dir", type=Path, default=None,
                    help=f"Output directory (default: {ARTIFACTS_AUDIO})")
    ap.add_argument("--list-voices", action="store_true", help="List available voices and exit")
    ap.add_argument("--from-receipt", help="Read text from a ledger receipt ID (searches town/ledger_v1.ndjson)")
    args = ap.parse_args()

    if args.list_voices:
        print(f"{len(VOICES)} voices available:")
        for v in VOICES:
            marker = " (HELEN default)" if v == HELEN_DEFAULT_VOICE else ""
            print(f"  {v}{marker}")
        return

    text = " ".join(args.text).strip() if args.text else ""

    if args.from_receipt and not text:
        ledger = REPO_ROOT / "town" / "ledger_v1.ndjson"
        if not ledger.exists():
            print(f"ERROR: ledger not found at {ledger}", file=sys.stderr)
            sys.exit(1)
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                ev = json.loads(line)
                # Match by looking for the receipt ID in the event's text
                payload = ev.get("payload", {})
                ev_text = payload.get("text", "")
                if args.from_receipt in str(ev):
                    text = ev_text
                    break
            except Exception:
                continue
        if not text:
            print(f"ERROR: receipt {args.from_receipt} not found in ledger", file=sys.stderr)
            sys.exit(1)

    if not text:
        print("ERROR: provide text to speak or --from-receipt", file=sys.stderr)
        sys.exit(1)

    print(f"Voice: {args.voice}  Model: {args.model}")
    print(f"Text ({len(text)} chars): {text[:120]}{'...' if len(text) > 120 else ''}")
    wav, prov = speak(text, voice=args.voice, model=args.model, output_dir=args.output_dir)
    print(f"Audio: {wav}")
    print(f"Provenance: {prov}")
    print(f"K8 compliant: payload_hash in provenance sidecar")


if __name__ == "__main__":
    main()
