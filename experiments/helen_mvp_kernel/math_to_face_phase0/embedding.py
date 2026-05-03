"""Phase 0 prime -> latent embedding H(p) -> R^512.

Spec (Phase 0 strict):
    H(p)_j        = sin(2*pi * p   / phi^(j+1))   for j = 0..255
    H(p)_{j+256}  = cos(2*pi * p^2 / phi^(j+2))   for j = 0..255

Determinism:
- math.sin / math.cos are bit-deterministic on IEEE 754 doubles
  within a Python version (CPython uses libm; small platform variance
  is below the 12-decimal rounding floor we apply before hashing).
- All values are rounded to DECIMAL_PRECISION before the receipt hashes
  the canonical-JSON of the embedding.
"""

from __future__ import annotations

import math
from typing import List

LATENT_DIM = 512
PHI = (1.0 + math.sqrt(5.0)) / 2.0


def embed_prime(p: int) -> List[float]:
    """Return the 512-dim embedding H(p) for a single prime p.

    Half is sin of (2*pi * p / phi^(j+1)),
    half is cos of (2*pi * p^2 / phi^(j+2)).
    """
    if p < 2:
        raise ValueError(f"embed_prime expects a prime p >= 2, got {p}")

    z: List[float] = [0.0] * LATENT_DIM
    two_pi = 2.0 * math.pi
    p2 = float(p) * float(p)

    for j in range(256):
        phi_pow_1 = PHI ** (j + 1)
        phi_pow_2 = PHI ** (j + 2)
        z[j] = math.sin(two_pi * float(p) / phi_pow_1)
        z[j + 256] = math.cos(two_pi * p2 / phi_pow_2)

    return z


def round_vector(v: List[float], precision: int) -> List[float]:
    """Round each entry to `precision` decimal places. Used before hashing."""
    return [round(x, precision) for x in v]
