"""Phase 0 Hamiltonian H_N + symmetric Jacobi eigensolver (stdlib only).

Spec:
    H_N = D_N + epsilon * A_N

    D_kk = log(p_k) / sqrt(p_k)

    A_kj = F_D(p_k, p_j) / (log(N) * |k - j|^c)   for k != j
    A_kk = 0

    F_D = "exp_neg_abs":  F_D(p_k, p_j) = exp(-|p_k - p_j|)

H_N is symmetric. Spectrum computed by classical Jacobi rotation
(stable, deterministic, exact for symmetric matrices in finite arithmetic).
"""

from __future__ import annotations

import math
from typing import List, Tuple

Matrix = List[List[float]]


def fractal_kernel_exp_neg_abs(pk: int, pj: int) -> float:
    return math.exp(-float(abs(pk - pj)))


def build_h_n(
    primes: List[int],
    epsilon: float,
    c: float,
    fractal_kernel: str = "exp_neg_abs",
) -> Matrix:
    """Build the symmetric H_N = D_N + epsilon * A_N matrix."""
    N = len(primes)
    if N < 1:
        raise ValueError("primes list must be non-empty")
    if fractal_kernel != "exp_neg_abs":
        raise ValueError(
            f"Phase 0 strict: fractal_kernel must be 'exp_neg_abs', got {fractal_kernel!r}"
        )

    log_N = math.log(N) if N > 1 else 1.0  # avoid div-by-zero in 1x1 trivial case

    H: Matrix = [[0.0 for _ in range(N)] for _ in range(N)]

    # Diagonal D_N
    for k in range(N):
        pk = primes[k]
        H[k][k] = math.log(pk) / math.sqrt(pk)

    # Off-diagonal A_N (symmetric)
    for k in range(N):
        for j in range(k + 1, N):
            pk = primes[k]
            pj = primes[j]
            f_d = fractal_kernel_exp_neg_abs(pk, pj)
            denom = log_N * (abs(k - j) ** c)
            a = f_d / denom
            H[k][j] += epsilon * a
            H[j][k] += epsilon * a  # enforce symmetry

    return H


def trace(M: Matrix) -> float:
    return sum(M[i][i] for i in range(len(M)))


def frobenius_norm(M: Matrix) -> float:
    s = 0.0
    for row in M:
        for v in row:
            s += v * v
    return math.sqrt(s)


def _copy(M: Matrix) -> Matrix:
    return [row[:] for row in M]


def jacobi_eigenvalues(
    M: Matrix,
    tol: float = 1e-14,
    max_iter: int = 1000,
) -> Tuple[List[float], int]:
    """Classical Jacobi rotation eigenvalue algorithm for symmetric matrices.

    Returns (sorted_eigenvalues, iterations_used).

    Deterministic: same input -> same output. Convergence is monotonic in
    the off-diagonal Frobenius norm.
    """
    A = _copy(M)
    n = len(A)
    if n == 0:
        return [], 0
    if n == 1:
        return [A[0][0]], 0

    iters = 0
    for it in range(max_iter):
        # Find largest off-diagonal magnitude
        p, q = 0, 1
        max_val = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                v = abs(A[i][j])
                if v > max_val:
                    max_val = v
                    p, q = i, j

        if max_val < tol:
            break

        # Compute rotation angle
        a_pp = A[p][p]
        a_qq = A[q][q]
        a_pq = A[p][q]

        if a_pp == a_qq:
            theta = math.pi / 4.0 if a_pq > 0 else -math.pi / 4.0
        else:
            theta = 0.5 * math.atan2(2.0 * a_pq, a_pp - a_qq)

        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        # Apply rotation R^T A R, exploiting symmetry
        new_pp = cos_t * cos_t * a_pp + 2.0 * cos_t * sin_t * a_pq + sin_t * sin_t * a_qq
        new_qq = sin_t * sin_t * a_pp - 2.0 * cos_t * sin_t * a_pq + cos_t * cos_t * a_qq
        A[p][p] = new_pp
        A[q][q] = new_qq
        A[p][q] = 0.0
        A[q][p] = 0.0

        for i in range(n):
            if i == p or i == q:
                continue
            a_ip = A[i][p]
            a_iq = A[i][q]
            new_ip = cos_t * a_ip + sin_t * a_iq
            new_iq = -sin_t * a_ip + cos_t * a_iq
            A[i][p] = new_ip
            A[p][i] = new_ip
            A[i][q] = new_iq
            A[q][i] = new_iq

        iters = it + 1

    eigenvalues = sorted(A[i][i] for i in range(n))
    return eigenvalues, iters


def spectral_summary(eigenvalues: List[float], M: Matrix) -> dict:
    """Return string-formatted spectral summary at the receipt's precision.

    Strings (not floats) so the receipt JSON is bit-identical regardless
    of repr drift between Python versions.
    """
    fmt = "{:.12f}"
    return {
        "lambda_min": fmt.format(eigenvalues[0]),
        "lambda_max": fmt.format(eigenvalues[-1]),
        "trace": fmt.format(trace(M)),
        "frobenius_norm": fmt.format(frobenius_norm(M)),
    }
