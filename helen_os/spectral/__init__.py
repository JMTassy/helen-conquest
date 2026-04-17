"""
helen_os.spectral

Spectral Cognitive Field (SCF) v0.1 — Non-sovereign filtering + telemetry layer.

Pure, deterministic analysis of evidence coherence and symmetry.
- Reads: memory (MemoryKernel), trace (RunTrace), frozen params
- Filters: candidate evidence by coherence + symmetry
- Emits: telemetry to Channel C (run_trace)
- Authority: always FALSE

No world effects. SCF output is non-binding; MAYOR gate decides.
"""

from .engine import SpectralAnalyzer, SCFParams

__all__ = ["SpectralAnalyzer", "SCFParams"]
