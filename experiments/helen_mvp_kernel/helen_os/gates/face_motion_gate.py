"""
Face-motion admissibility gate — Gate Layer 2.

Extracts mouth-region motion energy from each frame using OpenCV's
deterministic Haar cascade face detector (no ML weights download), then
checks two things:

  1. Mouth activity score (total variation of motion signal) >= MIN_ACTIVITY
     → catches static frames that pass the spectral gate but have no real
       articulation
  2. Spectral structure of the mouth motion autocorrelation passes the
     existing SpectralCertificate against a fixed reference
     → catches noise without rhythm (true talking has structured oscillation)

NON_SOVEREIGN. Deterministic. No ML model downloads.

What this catches:
  - blink-only motion (mouth area static)
  - random lighting flicker (no autocorrelation structure)
  - palindrome reverse mismatch (autocorrelation breaks at the reverse seam)

What this does NOT catch:
  - mouth motion that is rhythmic but DOESN'T match the audio
    (use av_sync_gate for that)
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from helen_os.certificates.spectral_certificate import (
    SpectralCertificate,
    build_receipt,
)

MIN_ACTIVITY = 0.15  # tunable; total-variation threshold on normalized signal


def extract_mouth_signal(
    video_path: str | Path, max_frames: int = 64,
) -> np.ndarray:
    """
    Per-frame mouth-region motion signal (mean abs diff between consecutive
    mouth regions). Uses OpenCV Haar cascade for face detection — deterministic,
    bundled with cv2, no ML model download.

    If no face is detected in a frame, motion = 0 for that frame.
    Returns a normalized 1-D array of length min(N_frames, max_frames).
    """
    cap = cv2.VideoCapture(str(video_path))
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    motion_signal: list[float] = []
    prev_mouth: np.ndarray | None = None
    n = 0
    while n < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            motion_signal.append(0.0)
            prev_mouth = None
            n += 1
            continue
        x, y, w, h = faces[0]
        mouth_y0 = y + int(2 * h / 3)
        mouth_y1 = y + h
        mouth_x0 = x
        mouth_x1 = x + w
        mouth = gray[mouth_y0:mouth_y1, mouth_x0:mouth_x1]
        if prev_mouth is None or prev_mouth.shape != mouth.shape:
            motion_signal.append(0.0)
        else:
            diff = float(np.mean(np.abs(mouth.astype(np.float64) - prev_mouth.astype(np.float64))))
            motion_signal.append(diff)
        prev_mouth = mouth
        n += 1
    cap.release()
    arr = np.array(motion_signal, dtype=np.float64)
    norm = float(np.linalg.norm(arr))
    if norm > 1e-8:
        arr = arr / norm
    return arr


def mouth_activity_score(signal: np.ndarray) -> float:
    """Total variation of the (already-normalized) signal."""
    if len(signal) < 2:
        return 0.0
    return float(np.sum(np.abs(np.diff(signal))))


def build_mouth_motion_kernel(signal: np.ndarray, size: int = 32) -> np.ndarray:
    """
    Build Gram-style kernel from autocorrelation of the motion signal.
    Captures rhythmic structure (talking ≈ structured oscillation).
    """
    if len(signal) < size:
        signal = np.pad(signal, (0, size - len(signal)))
    else:
        signal = signal[:size]
    autocorr = np.correlate(signal, signal, mode="full")
    autocorr = autocorr[len(autocorr) // 2:]  # positive lag half
    autocorr = autocorr[:size]
    T = np.outer(autocorr, autocorr)
    norm = float(np.linalg.norm(T))
    if norm > 1e-8:
        T = T / norm
    return T


def build_reference_matrix(size: int = 32) -> np.ndarray:
    """Same canonical reference shape as spectral_gate (cos-modulated rank-1)."""
    x = np.linspace(0, 1, size)
    T_ref = np.outer(np.cos(2 * np.pi * x), np.cos(2 * np.pi * x))
    norm = float(np.linalg.norm(T_ref))
    if norm > 1e-8:
        T_ref = T_ref / norm
    return T_ref


def face_motion_gate(
    video_path: str | Path,
    size: int = 32,
    tolerance: float = 1e-6,
    min_activity: float = MIN_ACTIVITY,
) -> dict[str, Any]:
    """
    Run face-motion gate.

    Returns dict with:
      gate_verdict: 'PASS' | 'REJECT_NO_ACTIVITY' | 'REJECT_NO_STRUCTURE'
      activity:     mouth motion total variation
      activity_threshold: MIN_ACTIVITY
      spectral_margin, aeon, lambda_min_hp, lambda_min_ref, status
      receipt (NON_SOVEREIGN)

    Does NOT raise.
    """
    signal = extract_mouth_signal(video_path)
    activity = mouth_activity_score(signal)

    if activity < min_activity:
        return {
            "gate": "face_motion_gate",
            "gate_verdict": "REJECT_NO_ACTIVITY",
            "activity": activity,
            "activity_threshold": min_activity,
            "spectral_margin": None,
            "aeon": None,
            "lambda_min_hp": None,
            "lambda_min_ref": None,
            "status": "REJECTED_BEFORE_SPECTRAL",
            "receipt": None,
            "n_frames_analyzed": int(len(signal)),
        }

    T_hp = build_mouth_motion_kernel(signal, size=size)
    T_ref = build_reference_matrix(size=size)
    cert = SpectralCertificate(T_ref, tolerance=tolerance)
    result = cert.certify(T_hp)

    spectral_pass = result["is_positive_definite"] and result["margin"] > 0
    gate_verdict = "PASS" if spectral_pass else "REJECT_NO_STRUCTURE"

    receipt = build_receipt(
        result,
        object_id=str(video_path),
        params={
            "gate": "face_motion_gate",
            "type": "mouth_autocorrelation_gram",
            "size": size,
            "activity": activity,
            "activity_threshold": min_activity,
        },
    )

    return {
        "gate": "face_motion_gate",
        "gate_verdict": gate_verdict,
        "activity": activity,
        "activity_threshold": min_activity,
        "spectral_margin": result["margin"],
        "aeon": result["aeon"],
        "lambda_min_hp": result["lambda_min_hp"],
        "lambda_min_ref": result["lambda_min_ref"],
        "status": result["status"],
        "receipt": receipt,
        "n_frames_analyzed": int(len(signal)),
    }
