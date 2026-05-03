"""Golden-ratio pacing and prime-rhythm logic per HELEN Video OS LaTeX spec.

phi_shot_durations(T, n):
    w_k = phi^k for k = 1..n
    d_k = T * w_k / sum(w_j)
    Result: monotone-increasing shot durations summing exactly to T.

prime_turn_indices(n):
    {p in primes : p <= n}
    Marks shots that receive stronger camera/pose/semantic transitions.
"""

from __future__ import annotations

import math
from typing import List

PHI = (1.0 + math.sqrt(5.0)) / 2.0


def phi_shot_durations(T: float, n: int, precision: int = 12) -> List[float]:
    """Return n shot durations summing to T, weighted by phi^k.

    Rounded to `precision` decimal places per shot for receipt determinism.
    The last shot absorbs any rounding residual so sum(d_k) == T to that
    precision.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if T <= 0:
        raise ValueError("T must be > 0")

    weights = [PHI ** (k + 1) for k in range(n)]
    total_w = sum(weights)
    durations = [round(T * w / total_w, precision) for w in weights]

    # Pin sum to T at the given precision by adjusting the last entry
    drift = round(T - sum(durations), precision)
    if drift != 0.0:
        durations[-1] = round(durations[-1] + drift, precision)

    return durations


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    r = int(math.isqrt(n))
    for p in range(3, r + 1, 2):
        if n % p == 0:
            return False
    return True


def prime_turn_indices(n_shots: int) -> List[int]:
    """Return sorted list of prime indices in [2, n_shots]."""
    return [p for p in range(2, n_shots + 1) if _is_prime(p)]
