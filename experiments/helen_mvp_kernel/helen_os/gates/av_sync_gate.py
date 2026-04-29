"""
Audio-visual sync admissibility gate — Gate Layer 3 (the talking-proof gate).

Verifies that mouth motion CAUSALLY tracks the audio speech envelope at the
right temporal lag. Uses normalized cross-correlation across a small lag scan.

Mathematical statement (per upstream architecture):

    S_AV = max_{tau in [-tau_max, tau_max]} corr(m(t), a(t - tau)) >= theta

  where:
    m(t) = mouth-region motion energy (from face_motion_gate.extract_mouth_signal)
    a(t) = audio speech envelope (smoothed amplitude)
    theta = AV_SYNC_THRESHOLD admissibility threshold
    tau* = optimal lag (audio lead/lag relative to video)

NON_SOVEREIGN. Deterministic. No ASR. No ML.

What this catches (the actual 8H failure class):
  - delayed voice over silent face
  - voice mixed at the wrong point in the timeline
  - palindrome reverse with forward-only voice (correlation drops)
  - voice + static face (no mouth signal to correlate)

What this does NOT prove:
  - that HELEN says the *correct* phrase (next layer: phoneme-envelope match)
  - that the words are intelligible
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from helen_os.gates.face_motion_gate import extract_mouth_signal


AV_SYNC_THRESHOLD = 0.35  # tunable empirically


def extract_audio_envelope(
    video_path: str | Path,
    sr_target: int = 16000,
    max_samples: int = 16000,
    smooth_kernel: int = 400,
) -> np.ndarray:
    """
    Speech-envelope approximation via:
      1. ffmpeg → raw PCM s16 mono at sr_target
      2. abs() → amplitude
      3. moving-average smoothing (kernel of `smooth_kernel` samples)

    Returns normalized 1-D array, length <= max_samples. Deterministic.
    Returns empty array if no audio track present.
    """
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-ac", "1",
        "-ar", str(sr_target),
        "-f", "s16le",
        "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw = proc.stdout.read()
    proc.wait()
    if not raw:
        return np.zeros(0, dtype=np.float64)
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    audio = np.abs(audio)
    if smooth_kernel > 1 and len(audio) >= smooth_kernel:
        kernel = np.ones(smooth_kernel) / smooth_kernel
        audio = np.convolve(audio, kernel, mode="same")
    audio = audio[:max_samples]
    norm = float(np.linalg.norm(audio))
    if norm > 1e-8:
        audio = audio / norm
    return audio


def resample_signal(signal: np.ndarray, target_len: int = 256) -> np.ndarray:
    """Linear interpolation to a fixed target length."""
    if len(signal) == 0:
        return np.zeros(target_len, dtype=np.float64)
    if len(signal) == target_len:
        return signal.astype(np.float64)
    x = np.linspace(0, 1, len(signal))
    x_new = np.linspace(0, 1, target_len)
    return np.interp(x_new, x, signal).astype(np.float64)


def compute_av_sync(
    video_path: str | Path,
    target_len: int = 256,
    lag_max: int = 10,
) -> dict[str, Any]:
    """
    Cross-correlate mouth motion against audio envelope at each lag in
    [-lag_max, lag_max]. Returns the best (sync_score, optimal_lag).
    """
    audio = extract_audio_envelope(video_path)
    mouth = extract_mouth_signal(video_path)

    if len(audio) == 0 or len(mouth) == 0:
        return {
            "sync_score": -1.0,
            "optimal_lag": 0,
            "audio_present": len(audio) > 0,
            "mouth_present": len(mouth) > 0,
            "audio_energy": 0.0,
            "mouth_energy": 0.0,
            "target_len": target_len,
            "lag_max": lag_max,
            "no_signal": True,
        }

    audio_r = resample_signal(audio, target_len=target_len)
    mouth_r = resample_signal(mouth, target_len=target_len)

    # Re-normalize after resample
    a_norm = float(np.linalg.norm(audio_r))
    m_norm = float(np.linalg.norm(mouth_r))
    if a_norm > 1e-8:
        audio_r = audio_r / a_norm
    if m_norm > 1e-8:
        mouth_r = mouth_r / m_norm

    best_corr = -1.0
    best_tau = 0
    for tau in range(-lag_max, lag_max + 1):
        if tau < 0:
            a_slice = audio_r[:tau]
            m_slice = mouth_r[-tau:]
        elif tau > 0:
            a_slice = audio_r[tau:]
            m_slice = mouth_r[:-tau]
        else:
            a_slice = audio_r
            m_slice = mouth_r
        if len(a_slice) == 0 or len(m_slice) == 0:
            continue
        n_min = min(len(a_slice), len(m_slice))
        a_slice = a_slice[:n_min]
        m_slice = m_slice[:n_min]
        corr = float(np.dot(a_slice, m_slice))
        if corr > best_corr:
            best_corr = corr
            best_tau = tau

    return {
        "sync_score": best_corr,
        "optimal_lag": best_tau,
        "audio_present": True,
        "mouth_present": True,
        "audio_energy": float(np.mean(audio_r)),
        "mouth_energy": float(np.mean(mouth_r)),
        "target_len": target_len,
        "lag_max": lag_max,
        "no_signal": False,
    }


def av_sync_gate(
    video_path: str | Path,
    threshold: float = AV_SYNC_THRESHOLD,
    target_len: int = 256,
    lag_max: int = 10,
) -> dict[str, Any]:
    """
    Run AV sync gate.

    Returns dict with:
      gate_verdict: 'PASS' | 'REJECT_BELOW_THRESHOLD' | 'REJECT_NO_SIGNAL'
      sync_score, optimal_lag, threshold
      audio_present, mouth_present
      receipt fields

    Does NOT raise.
    """
    av = compute_av_sync(video_path, target_len=target_len, lag_max=lag_max)

    if av.get("no_signal", False):
        verdict = "REJECT_NO_SIGNAL"
    elif av["sync_score"] < threshold:
        verdict = "REJECT_BELOW_THRESHOLD"
    else:
        verdict = "PASS"

    return {
        "gate": "av_sync_gate",
        "gate_verdict": verdict,
        "sync_score": av["sync_score"],
        "optimal_lag": av["optimal_lag"],
        "threshold": threshold,
        "audio_present": av["audio_present"],
        "mouth_present": av["mouth_present"],
        "audio_energy": av["audio_energy"],
        "mouth_energy": av["mouth_energy"],
        "lag_max": lag_max,
        "target_len": target_len,
    }
