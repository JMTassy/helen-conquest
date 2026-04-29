"""QFSE Evidence Compiler — Pi_kernel projection.

Maps continuous φ-SDE / QFSE trajectories to schema-valid, deterministic
evidence objects admissible to the HELEN sovereign kernel.

Constitutional boundary:
    QFSE never mutates HELEN state.
    QFSE only emits evidence.
    Reducer decides.
"""
from __future__ import annotations

import hashlib
import math

import numpy as np

from qfse_bridge.schemas import QFSEEvidenceObject, validate

PHI = (1.0 + math.sqrt(5.0)) / 2.0  # golden ratio ≈ 1.6180339887

ENTROPY_THRESHOLD = 0.85
COHERENCE_THRESHOLD = 0.60
IDENTITY_THRESHOLD = 0.50
BRAID_THRESHOLD = 0.50


def _as_array(trajectory) -> np.ndarray:
    arr = np.array(trajectory, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError(f"trajectory must be 2D (T × D), got shape {arr.shape}")
    if arr.shape[0] < 2:
        raise ValueError(f"trajectory must have ≥ 2 timesteps, got {arr.shape[0]}")
    return arr


def trajectory_hash(trajectory) -> str:
    """Deterministic sha256 of the trajectory array (shape-prefixed)."""
    arr = _as_array(trajectory)
    shape_prefix = f"{arr.shape[0]}x{arr.shape[1]}:".encode()
    digest = hashlib.sha256(shape_prefix + arr.tobytes()).hexdigest()
    return f"sha256:{digest}"


def compute_entropy(trajectory) -> float:
    """Normalized spectral entropy of the trajectory covariance eigenspectrum.

    Returns a value in [0, 1]. High entropy = disordered latent dynamics.
    """
    arr = _as_array(trajectory)
    T, D = arr.shape
    centered = arr - arr.mean(axis=0)
    cov = (centered.T @ centered) / max(T - 1, 1)
    eigvals = np.linalg.eigvalsh(cov)
    eigvals = np.maximum(eigvals, 0.0)
    total = eigvals.sum()
    if total < 1e-12:
        return 0.0
    p = eigvals / total
    p = p[p > 1e-12]
    entropy = -float(np.sum(p * np.log(p)))
    max_entropy = math.log(D)
    return min(entropy / max_entropy, 1.0) if max_entropy > 0.0 else 0.0


def compute_phi_coherence(trajectory) -> float:
    """Alignment of trajectory norms with the expected φ^{-t} decay curve.

    Returns a value in [0, 1]. High coherence = trajectory respects golden-ratio
    contraction — consistent with φ-SDE attractor dynamics.
    """
    arr = _as_array(trajectory)
    T = arr.shape[0]
    norms = np.linalg.norm(arr, axis=1)
    if norms[0] < 1e-12:
        return 0.0
    normalized = norms / norms[0]
    expected = np.array([PHI ** (-t) for t in range(T)], dtype=np.float64)
    rmse = float(np.sqrt(np.mean((normalized - expected) ** 2)))
    return max(0.0, 1.0 - rmse)


def compute_identity_preservation(trajectory) -> float:
    """Mean cosine similarity between z(t) and z_0.

    Measures directional identity under contraction. Returns 1.0 when the
    trajectory scales z_0 without rotating (perfect φ-SDE attractor behavior).
    Position drift is expected; rotational drift is not.
    """
    arr = _as_array(trajectory)
    z0 = arr[0]
    norm_z0 = float(np.linalg.norm(z0))
    if norm_z0 < 1e-12:
        return 1.0
    norms_t = np.linalg.norm(arr, axis=1)
    valid = norms_t > 1e-12
    if not valid.any():
        return 0.0
    dots = arr[valid] @ z0
    cos_sims = np.clip(dots / (norms_t[valid] * norm_z0), -1.0, 1.0)
    return max(0.0, float(np.mean(cos_sims)))


def compute_braid_stability(trajectory) -> float:
    """Geometric consistency of step-size ratios.

    Stable braids contract at a consistent geometric rate. Returns 1.0 for
    perfect φ-decay (ratio = φ^{-1} at every step, zero variance).
    """
    arr = _as_array(trajectory)
    steps = np.linalg.norm(np.diff(arr, axis=0), axis=1)
    pos_steps = steps[steps > 1e-12]
    if len(pos_steps) < 2:
        return 1.0
    ratios = pos_steps[1:] / pos_steps[:-1]
    mean_ratio = float(ratios.mean())
    cv = float(ratios.std()) / max(mean_ratio, 1e-12)
    return 1.0 / (1.0 + cv)


def compile(trajectory) -> QFSEEvidenceObject:
    """Project a continuous QFSE trajectory into a discrete HELEN evidence object.

    This is Pi_kernel: H_phi → P(E).

    The returned object is schema-validated and deterministic.
    It carries no state mutation authority — the reducer decides what to do with it.
    """
    t_hash = trajectory_hash(trajectory)
    entropy = compute_entropy(trajectory)
    coherence = compute_phi_coherence(trajectory)
    identity = compute_identity_preservation(trajectory)
    braid = compute_braid_stability(trajectory)

    valid = (
        entropy < ENTROPY_THRESHOLD
        and coherence > COHERENCE_THRESHOLD
        and identity > IDENTITY_THRESHOLD
        and braid > BRAID_THRESHOLD
    )

    evidence = QFSEEvidenceObject(
        trajectory_hash=t_hash,
        entropy=entropy,
        phi_coherence=coherence,
        identity_preservation=identity,
        braid_stability=braid,
        valid=valid,
    )
    validate(evidence.to_dict())
    return evidence
