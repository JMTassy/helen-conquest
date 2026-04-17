#!/usr/bin/env python3
"""
helen_os/spectral/engine.py

Spectral Cognitive Field (SCF) v0.1

Pure, deterministic filtering + telemetry for non-sovereign dialogue layer.
- Reads: memory (MemoryKernel), trace (RunTrace), frozen params
- Filters: candidate evidence by coherence + symmetry
- Emits: telemetry to Channel C (run_trace)
- Authority: always FALSE
"""

import hashlib
import json
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional


@dataclass(frozen=True)
class SCFParams:
    """Frozen SCF parameters (immutable, versioned)."""
    alpha_fp: int = 1000000      # fixed-point scale
    beta_fp: int = 500000
    gamma_fp: int = 250000
    coh_target_fp: int = 500000
    coh_band_fp: int = 100000
    sym_min_fp: int = 600000
    dim: int = 128
    scale_fp: int = 1000000
    version: str = "scf-v0.1"

    def canonical_hash(self) -> str:
        """SHA256 of canonical JSON (for reproducibility)."""
        canonical = json.dumps(
            {k: v for k, v in self.__dict__.items()},
            sort_keys=True,
            separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode()).hexdigest()


class SpectralAnalyzer:
    """
    Non-sovereign SCF engine. Deterministic filtering + telemetry.
    """

    def __init__(self, params: SCFParams):
        self.params = params
        self.params_hash = params.canonical_hash()

    # ────────────────────────────────────────────────────────────────
    # Deterministic Feature Extraction
    # ────────────────────────────────────────────────────────────────

    def _hash_bucketed(self, obj: Dict[str, Any]) -> np.ndarray:
        """
        Convert object to fixed-dimensional feature vector via hash bucketing.
        Deterministic: same input → same vector.
        """
        v = np.zeros(self.params.dim, dtype=np.int64)
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256(canonical.encode()).digest()

        for i, b in enumerate(h):
            v[(i * 131) % self.params.dim] += int(b)

        return v

    def _feat_evidence(self, e: Dict[str, Any]) -> np.ndarray:
        """Feature vector for evidence item."""
        return self._hash_bucketed(e)

    def _feat_conflicts(self, memory_facts: List[Dict]) -> List[Tuple[int, np.ndarray]]:
        """Extract conflict signals from DISPUTED/RETRACTED memory events."""
        conflicts = []
        for fact in memory_facts:
            status = fact.get("status", "")
            if status in ("DISPUTED", "RETRACTED"):
                weight = int(fact.get("severity_fp", self.params.scale_fp))
                feat = self._hash_bucketed(fact)
                conflicts.append((weight, feat))
        return conflicts

    def _feat_anomalies(self, trace_events: List[Dict]) -> List[Tuple[int, np.ndarray]]:
        """Extract anomalies from trace."""
        anomalies = []
        for event in trace_events:
            if event.get("event_type", "").startswith("anomaly_"):
                weight = int(event.get("weight_fp", self.params.scale_fp))
                feat = self._hash_bucketed(event)
                anomalies.append((weight, feat))
        return anomalies

    # ────────────────────────────────────────────────────────────────
    # Operator Construction
    # ────────────────────────────────────────────────────────────────

    def _build_operator(
        self, memory_facts: List[Dict], trace_events: List[Dict]
    ) -> np.ndarray:
        """
        Build self-adjoint operator A_t = αI + βC_t + γK_t
        C_t: conflict operator (from memory)
        K_t: trace anomaly operator
        """
        d = self.params.dim
        C = np.zeros((d, d), dtype=np.float64)
        K = np.zeros((d, d), dtype=np.float64)

        # Conflict operator
        for w_fp, u in self._feat_conflicts(memory_facts):
            u = u.astype(np.float64)
            C += (w_fp / self.params.scale_fp) * np.outer(u, u)

        # Anomaly operator
        for v_fp, z in self._feat_anomalies(trace_events):
            z = z.astype(np.float64)
            K += (v_fp / self.params.scale_fp) * np.outer(z, z)

        # Combined operator
        A = (
            (self.params.alpha_fp / self.params.scale_fp) * np.eye(d)
            + (self.params.beta_fp / self.params.scale_fp) * C
            + (self.params.gamma_fp / self.params.scale_fp) * K
        )

        # Enforce symmetry numerically
        A = 0.5 * (A + A.T)
        return A

    # ────────────────────────────────────────────────────────────────
    # Coherence & Symmetry Scoring
    # ────────────────────────────────────────────────────────────────

    def _coherence_fp(self, A: np.ndarray, y: np.ndarray) -> int:
        """Compute coherence energy (fixed-point)."""
        y = y.astype(np.float64)
        val = float(y.T @ A @ y)
        return int(round(val * self.params.scale_fp))

    def _symmetry_fp(self, e: Dict[str, Any]) -> int:
        """
        Compute symmetry score (fixed-point, 0–1 scale).
        Forward: required fields present
        Reverse: no authority leakage
        """
        # Forward check: required fields
        forward = 0
        for k in ("type", "rid", "payload"):
            forward += 1 if k in e else 0

        # Reverse check: forbids authority
        reverse = 1 if ("authority" not in e and "SHIP" not in json.dumps(e)) else 0

        # Score: [0, 1]
        score = (forward / 3.0) * (reverse / 1.0)
        return int(round(score * self.params.scale_fp))

    # ────────────────────────────────────────────────────────────────
    # Top Eigenvalues (Tension Spectrum)
    # ────────────────────────────────────────────────────────────────

    def _top_eigenvalues(self, A: np.ndarray, k: int = 8) -> List[int]:
        """Compute top k eigenvalues (fixed-point)."""
        eigvals = np.linalg.eigvalsh(A)
        top_vals = eigvals[::-1][:k]  # Largest k eigenvalues
        # Convert to fixed-point (scale 10^6)
        return [int(round(v * self.params.scale_fp)) for v in top_vals]

    # ────────────────────────────────────────────────────────────────
    # Filtering & Telemetry
    # ────────────────────────────────────────────────────────────────

    def process(
        self,
        candidates: List[Dict[str, Any]],
        memory_facts: List[Dict],
        trace_events: List[Dict],
        turn: int,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filter candidates and emit telemetry.

        Returns:
            (filtered_evidence, telemetry_event)
        """
        # Build operator from memory + trace
        A = self._build_operator(memory_facts, trace_events)

        # Score each candidate
        filtered = []
        coherence_bins = {"low": 0, "medium": 0, "high": 0}
        symmetry_flags = {"pass": 0, "fail": 0}

        for e in candidates:
            x = self._feat_evidence(e)
            coh = self._coherence_fp(A, x)
            sym = self._symmetry_fp(e)

            # Acceptance criterion
            coh_in_band = abs(coh - self.params.coh_target_fp) <= self.params.coh_band_fp
            sym_ok = sym >= self.params.sym_min_fp

            if coh_in_band and sym_ok:
                filtered.append(e)
                symmetry_flags["pass"] += 1
            else:
                symmetry_flags["fail"] += 1

            # Bin coherence
            if coh < self.params.coh_target_fp - self.params.coh_band_fp:
                coherence_bins["low"] += 1
            elif coh > self.params.coh_target_fp + self.params.coh_band_fp:
                coherence_bins["high"] += 1
            else:
                coherence_bins["medium"] += 1

        # Emit telemetry
        telemetry = {
            "event_id": f"scf:{turn}",
            "turn": turn,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "scf",
            "type": "scf_annotation_v1",
            "scf_version": self.params.version,
            "params_hash": self.params_hash,
            "evidence_in_count": len(candidates),
            "evidence_out_count": len(filtered),
            "coherence_summary": coherence_bins,
            "symmetry_flags": {
                "all_pass": symmetry_flags["fail"] == 0,
                "fail_count": symmetry_flags["fail"],
                "fail_reason": "none",  # SCF filtering is non-binding; no authority claim
            },
            "tension_modes": self._top_eigenvalues(A),
            "authority": False,
        }

        return filtered, telemetry


# Singleton instance
_scf_instance: Optional[SpectralAnalyzer] = None


def get_scf(params: Optional[SCFParams] = None) -> SpectralAnalyzer:
    """Get or create SCF instance."""
    global _scf_instance
    if _scf_instance is None:
        _scf_instance = SpectralAnalyzer(params or SCFParams())
    return _scf_instance
