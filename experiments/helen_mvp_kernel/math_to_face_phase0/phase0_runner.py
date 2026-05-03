"""Phase 0 orchestrator.

Pipeline:
    fixture.json
        -> build H_N
        -> Jacobi eigenvalues
        -> H_N_SPECTRAL_RECEIPT_V1   emitted
        -> embed_prime(primes[embedding_input_index]) = z_0
        -> phi-SDE Euler-Maruyama (zero noise, zero projection)
        -> z_T
        -> PHI_SDE_TRACE_RECEIPT_V1  emitted
        -> RESEARCH_RUN_RECEIPT_V1   emitted (when called via run_replay)

Determinism:
- All numeric outputs hashed via canonical-JSON of values rounded to
  decimal_precision (12) before SHA-256.
- timestamp_utc is excluded from hashable cores; it is recorded in
  receipts but the *replay invariant* (eigenvalues_hash, trace_hash,
  z_T_hash, operator_hash) is timestamp-free.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

HERE = Path(__file__).resolve().parent
PKG_ROOT = HERE.parent  # experiments/helen_mvp_kernel/
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from math_to_face_phase0.embedding import embed_prime  # noqa: E402
from math_to_face_phase0.h_n import (  # noqa: E402
    build_h_n,
    jacobi_eigenvalues,
    spectral_summary,
)
from math_to_face_phase0.phi_sde_trace import integrate, z_T_summary  # noqa: E402
from math_to_face_phase0.receipts import (  # noqa: E402
    emit_h_n_spectral_receipt,
    emit_phi_sde_trace_receipt,
    emit_research_run_receipt,
    hash_matrix,
    hash_vector,
    sha256_obj,
    now_utc_iso,
)


def load_fixture(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_spectral(fixture: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Compute H_N + spectrum + spectral receipt body. Return (receipt, hash_core).

    hash_core contains the deterministic identity hashes used by replay:
        operator_hash, eigenvalues_hash, primes_hash
    """
    primes = fixture["primes"]
    N = fixture["N"]
    epsilon = fixture["epsilon"]
    c = fixture["c"]
    fractal_kernel = fixture["fractal_kernel"]
    precision = fixture["decimal_precision"]

    if N != len(primes):
        raise ValueError(f"N={N} but len(primes)={len(primes)}")

    H = build_h_n(primes, epsilon, c, fractal_kernel)
    eigenvalues, _iters = jacobi_eigenvalues(H)
    summary = spectral_summary(eigenvalues, H)

    primes_hash = sha256_obj(primes)
    operator_hash = hash_matrix(H, precision)
    eigenvalues_hash = hash_vector(eigenvalues, precision)

    receipt = {
        "schema": "H_N_SPECTRAL_RECEIPT_V1",
        "problem_id": fixture["problem_id"],
        "N": N,
        "primes": primes,
        "epsilon": epsilon,
        "c": c,
        "fractal_kernel": fractal_kernel,
        "primes_hash": primes_hash,
        "operator_hash": operator_hash,
        "eigenvalues_hash": eigenvalues_hash,
        "spectral_summary": summary,
        "decimal_precision": precision,
        "scope": "RESEARCH_SUBSANDBOX",
        "sovereign_admitted": False,
        "timestamp_utc": now_utc_iso(),
    }

    hash_core = {
        "primes_hash": primes_hash,
        "operator_hash": operator_hash,
        "eigenvalues_hash": eigenvalues_hash,
    }
    return receipt, hash_core


def compute_sde(fixture: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Compute embedding + phi-SDE + trace receipt body. Return (receipt, hash_core)."""
    primes = fixture["primes"]
    sde = fixture["phi_sde"]
    precision = fixture["decimal_precision"]
    idx = fixture.get("embedding_input_index", 0)
    p = primes[idx]

    z0 = embed_prime(p)
    z0_hash = hash_vector(z0, precision)

    z_T, n_steps, trace_norms = integrate(
        z0=z0,
        T=sde["T"],
        dt=sde["dt"],
        gamma=sde["gamma"],
        noise_seed=sde["noise_seed"],
        noise_mode=sde["noise_mode"],
        qam_projection=sde["qam_projection"],
    )

    trace_hash = hash_vector(trace_norms, precision)
    z_T_hash = hash_vector(z_T, precision)

    receipt = {
        "schema": "PHI_SDE_TRACE_RECEIPT_V1",
        "problem_id": fixture["problem_id"],
        "z0_hash": z0_hash,
        "T": sde["T"],
        "dt": sde["dt"],
        "n_steps": n_steps,
        "gamma": sde["gamma"],
        "noise_seed": sde["noise_seed"],
        "noise_mode": sde["noise_mode"],
        "qam_projection": sde["qam_projection"],
        "trace_hash": trace_hash,
        "z_T_hash": z_T_hash,
        "z_T_summary": z_T_summary(z_T, precision),
        "decimal_precision": precision,
        "scope": "RESEARCH_SUBSANDBOX",
        "sovereign_admitted": False,
        "timestamp_utc": now_utc_iso(),
    }
    hash_core = {
        "z0_hash": z0_hash,
        "trace_hash": trace_hash,
        "z_T_hash": z_T_hash,
    }
    return receipt, hash_core


def receipt_canonical_hash(receipt: Dict[str, Any]) -> str:
    """Hash a receipt with timestamp_utc excluded.

    Replay invariant: same input -> same hash, regardless of when ran.
    """
    core = {k: v for k, v in receipt.items() if k != "timestamp_utc"}
    return sha256_obj(core)


def run_one(fixture_path: Path, emit: bool = True) -> Dict[str, Any]:
    fixture = load_fixture(fixture_path)

    spectral_receipt, spectral_core = compute_spectral(fixture)
    sde_receipt, sde_core = compute_sde(fixture)

    spectral_hash = receipt_canonical_hash(spectral_receipt)
    sde_hash = receipt_canonical_hash(sde_receipt)

    if emit:
        emit_h_n_spectral_receipt(spectral_receipt, fixture["problem_id"])
        emit_phi_sde_trace_receipt(sde_receipt, fixture["problem_id"])

    return {
        "problem_id": fixture["problem_id"],
        "spectral_receipt": spectral_receipt,
        "sde_receipt": sde_receipt,
        "spectral_receipt_hash": spectral_hash,
        "sde_receipt_hash": sde_hash,
        "operator_hash": spectral_core["operator_hash"],
        "eigenvalues_hash": spectral_core["eigenvalues_hash"],
        "trace_hash": sde_core["trace_hash"],
        "z_T_hash": sde_core["z_T_hash"],
    }


def run_replay(fixture_path: Path, n: int = 3) -> Dict[str, Any]:
    """Run the orchestrator n times. Verify all hashes match. Emit RESEARCH_RUN_RECEIPT_V1."""
    if n < 2:
        raise ValueError("replay requires n >= 2")

    runs = [run_one(fixture_path, emit=(i == 0)) for i in range(n)]
    keys = [
        "operator_hash",
        "eigenvalues_hash",
        "trace_hash",
        "z_T_hash",
        "spectral_receipt_hash",
        "sde_receipt_hash",
    ]
    consistent = all(
        all(runs[i][k] == runs[0][k] for k in keys) for i in range(1, n)
    )

    fixture = load_fixture(fixture_path)
    problem_id = fixture["problem_id"]

    run_receipt = {
        "schema": "RESEARCH_RUN_RECEIPT_V1",
        "loop": "RALPH_LOOP_2026-05-02_PHASE0",
        "problem_id": problem_id,
        "spectral_receipt_hash": runs[0]["spectral_receipt_hash"],
        "sde_receipt_hash": runs[0]["sde_receipt_hash"],
        "replay_n": n,
        "replay_consistent": consistent,
        "replay_check_hashes": {k: runs[0][k] for k in keys},
        "decimal_precision": 12,
        "scope": "RESEARCH_SUBSANDBOX",
        "sovereign_admitted": False,
        "timestamp_utc": now_utc_iso(),
    }
    if consistent:
        emit_research_run_receipt(run_receipt, problem_id)
    return run_receipt


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: python -m math_to_face_phase0.phase0_runner <fixture.json> [--replay N]",
            file=sys.stderr,
        )
        return 2

    fixture_path = Path(sys.argv[1])
    if not fixture_path.exists():
        print(f"fixture not found: {fixture_path}", file=sys.stderr)
        return 1

    if "--replay" in sys.argv:
        idx = sys.argv.index("--replay")
        n = int(sys.argv[idx + 1])
        receipt = run_replay(fixture_path, n=n)
        print(json.dumps(
            {
                "loop": receipt["loop"],
                "problem_id": receipt["problem_id"],
                "replay_n": receipt["replay_n"],
                "replay_consistent": receipt["replay_consistent"],
                "replay_check_hashes": receipt["replay_check_hashes"],
            },
            indent=2,
        ))
        return 0 if receipt["replay_consistent"] else 1

    out = run_one(fixture_path, emit=True)
    print(json.dumps(
        {
            "problem_id": out["problem_id"],
            "operator_hash": out["operator_hash"],
            "eigenvalues_hash": out["eigenvalues_hash"],
            "trace_hash": out["trace_hash"],
            "z_T_hash": out["z_T_hash"],
            "spectral_receipt_hash": out["spectral_receipt_hash"],
            "sde_receipt_hash": out["sde_receipt_hash"],
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
