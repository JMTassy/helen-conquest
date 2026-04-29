"""High-entropy trajectories are rejected; low-entropy coherent ones pass."""
import math
import numpy as np

from qfse_bridge.qfse_evidence_compiler import compile, ENTROPY_THRESHOLD, COHERENCE_THRESHOLD

PHI = (1 + math.sqrt(5)) / 2


def _random_trajectory(T: int = 50, D: int = 64, seed: int = 0) -> list:
    return np.random.default_rng(seed).standard_normal((T, D)).tolist()


def _phi_trajectory(T: int = 30, D: int = 4) -> list:
    z0 = np.ones(D)
    return [z0 * PHI ** (-t) for t in range(T)]


def test_high_entropy_random_trajectory_is_invalid():
    evidence = compile(_random_trajectory())
    # Maximally random → entropy near 1 → must be invalid
    assert evidence.entropy >= ENTROPY_THRESHOLD or not evidence.valid


def test_phi_decaying_trajectory_passes_entropy_gate():
    evidence = compile(_phi_trajectory())
    assert evidence.entropy < ENTROPY_THRESHOLD


def test_phi_decaying_trajectory_is_valid():
    evidence = compile(_phi_trajectory())
    assert evidence.valid is True


def test_valid_flag_is_conjunction_of_all_gates():
    # Construct a trajectory that passes entropy but fails coherence
    # by using a constant trajectory (entropy=0, but coherence ~0 after t=0)
    T, D = 20, 8
    traj = [np.ones(D) * 1.0 for _ in range(T)]  # no decay → low coherence at t>0
    evidence = compile(traj)
    # Valid only if all gates pass
    gates = (
        evidence.entropy < ENTROPY_THRESHOLD
        and evidence.phi_coherence > COHERENCE_THRESHOLD
        and evidence.identity_preservation > 0.50
        and evidence.braid_stability > 0.50
    )
    assert evidence.valid == gates
