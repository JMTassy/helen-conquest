"""higgsfield_seedance.music_stub — silence fallback for the music gap.

HELEN has no music-generation skill yet (see HAL_INSPIRATION_QUEUE.md
ITEM-010 §music gap). This stub generates a deterministic silence WAV
so the montage pipeline can run end-to-end without blocking on the gap.

Future: replace with a Suno/Udio binding or operator-supplied stems.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path


def write_silence_wav(out_path: Path, duration_s: float, sample_rate: int = 44100) -> Path:
    """Write a deterministic silence WAV of the requested duration.

    Mono, 16-bit PCM. Plays as silence on every player. Same duration
    same SHA-256 (no timestamps in WAV header for this minimal writer).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(duration_s * sample_rate)
    silence = struct.pack("<h", 0) * n_frames

    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(silence)

    return out_path


def music_for_storyboard(task_id: str, duration_s: float, out_dir: Path) -> dict:
    """Produce a music track for a storyboard. Currently silence-only.

    Returns a manifest entry the dry-run orchestrator can consume.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"music_{task_id}.wav"
    write_silence_wav(out_path, duration_s)

    import hashlib
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()

    return {
        "schema": "MUSIC_STUB_MANIFEST_V0",
        "task_id": task_id,
        "kind": "silence",
        "duration_s": duration_s,
        "sample_rate": 44100,
        "channels": 1,
        "wav_path": str(out_path),
        "wav_sha256": sha,
        "note": (
            "Silence fallback. HELEN has no music-gen skill yet "
            "(ITEM-010 §music gap). Replace this stub when a "
            "Suno/Udio binding lands or operator supplies stems."
        ),
        "scope": "TEMPLE_SUBSANDBOX",
        "sovereign_admitted": False,
    }
