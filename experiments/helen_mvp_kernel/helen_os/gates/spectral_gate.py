"""
Spectral admissibility gate — Gate Layer 1.

Verifies temporal coherence of a video by reducing to a 1-D luminance signal,
building a Gram-style kernel, and applying the existing SpectralCertificate
(Tier I, Weyl bound) from helen_os.certificates.spectral_certificate.

NON_SOVEREIGN. Pure deterministic computation. No signing.

What this catches:
  - flat / static / non-coherent frames (passes only if Gram has positive margin
    against the canonical reference)

What this does NOT catch:
  - blink-only motion (low temporal variation can still produce some Gram structure)
  - palindrome reverse mismatch (use face_motion_gate for that)
  - mouth-vs-audio desync (use av_sync_gate for that)

Caller wires this gate as the first of three composite gates.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from helen_os.certificates.spectral_certificate import (
    SpectralCertificate,
    build_receipt,
)


def extract_frame_energy(
    video_path: str | Path, fps: int = 10, max_frames: int = 64,
    grid: int = 64,
) -> np.ndarray:
    """
    Deterministic scalar signal from video: mean luminance per frame.
    Down-samples to `grid×grid` grayscale at `fps` then averages each frame.
    """
    # Cap ffmpeg's output to exactly max_frames via -frames:v (avoids pipe deadlock
    # where proc.wait() would block forever waiting for ffmpeg to finish writing
    # data we don't intend to read).
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vf", f"fps={fps},scale={grid}:{grid},format=gray",
        "-frames:v", str(max_frames),
        "-f", "rawvideo", "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw = proc.stdout.read()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    if not raw:
        raise RuntimeError(f"No frames extracted from {video_path}")
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, grid * grid)
    return frames.mean(axis=1).astype(np.float64)


def build_temporal_coherence_matrix(
    video_path: str | Path, size: int = 32,
) -> np.ndarray:
    """
    Build symmetric Gram matrix T_hp from video's temporal energy signal.
    Pad/truncate to `size`, then T = outer(s, s) / ‖outer‖.
    """
    signal = extract_frame_energy(video_path)
    if len(signal) < size:
        signal = np.pad(signal, (0, size - len(signal)))
    else:
        signal = signal[:size]
    T = np.outer(signal, signal)
    norm = float(np.linalg.norm(T))
    if norm > 1e-8:
        T = T / norm
    return T


def build_reference_matrix(size: int = 32) -> np.ndarray:
    """
    Fixed canonical reference: cos-modulated rank-1 Hermitian.
    Constant across all gate runs (same caller, same constant).
    """
    x = np.linspace(0, 1, size)
    T_ref = np.outer(np.cos(2 * np.pi * x), np.cos(2 * np.pi * x))
    norm = float(np.linalg.norm(T_ref))
    if norm > 1e-8:
        T_ref = T_ref / norm
    return T_ref


def spectral_gate(
    video_path: str | Path,
    size: int = 32,
    tolerance: float = 1e-6,
) -> dict[str, Any]:
    """
    Run spectral gate on a video.

    Returns dict with `is_positive_definite`, `margin`, `aeon`,
    `lambda_min_hp`, `lambda_min_ref`, `status`, plus `gate_verdict`
    ('PASS' | 'REJECT') and `receipt` (NON_SOVEREIGN spectral receipt).

    Does NOT raise — returns the verdict in the dict. Caller decides whether
    to block downstream actions.
    """
    T_hp = build_temporal_coherence_matrix(video_path, size=size)
    T_ref = build_reference_matrix(size=size)
    cert = SpectralCertificate(T_ref, tolerance=tolerance)
    result = cert.certify(T_hp)

    gate_verdict = "PASS" if (result["is_positive_definite"] and result["margin"] > 0) else "REJECT"

    receipt = build_receipt(
        result,
        object_id=str(video_path),
        params={"gate": "spectral_gate", "type": "luminance_gram", "size": size},
    )

    return {
        "gate": "spectral_gate",
        "gate_verdict": gate_verdict,
        "is_positive_definite": result["is_positive_definite"],
        "margin": result["margin"],
        "aeon": result["aeon"],
        "lambda_min_hp": result["lambda_min_hp"],
        "lambda_min_ref": result["lambda_min_ref"],
        "status": result["status"],
        "receipt": receipt,
    }
