"""Deterministic compilation and schema validity."""
import numpy as np
import pytest

from qfse_bridge.qfse_evidence_compiler import compile
from qfse_bridge.schemas import SCHEMA_TYPE, COMPILER_VERSION


def _phi_trajectory(T: int = 20, D: int = 8, seed: int = 42) -> list:
    PHI = (1 + 5 ** 0.5) / 2
    rng = np.random.default_rng(seed)
    z0 = rng.standard_normal(D)
    return [z0 * PHI ** (-t) for t in range(T)]


def test_compilation_produces_correct_schema_type():
    evidence = compile(_phi_trajectory())
    assert evidence.type == SCHEMA_TYPE
    assert evidence.compiler_version == COMPILER_VERSION


def test_compilation_metrics_are_bounded():
    evidence = compile(_phi_trajectory())
    assert 0.0 <= evidence.entropy <= 1.0
    assert 0.0 <= evidence.phi_coherence <= 1.0
    assert 0.0 <= evidence.identity_preservation <= 1.0
    assert 0.0 < evidence.braid_stability <= 1.0
    assert isinstance(evidence.valid, bool)


def test_compilation_is_fully_deterministic():
    traj = _phi_trajectory()
    e1 = compile(traj)
    e2 = compile(traj)
    assert e1.trajectory_hash == e2.trajectory_hash
    assert e1.entropy == e2.entropy
    assert e1.phi_coherence == e2.phi_coherence
    assert e1.identity_preservation == e2.identity_preservation
    assert e1.braid_stability == e2.braid_stability
    assert e1.valid == e2.valid


def test_canonical_json_is_stable():
    traj = _phi_trajectory()
    e1 = compile(traj)
    e2 = compile(traj)
    assert e1.canonical_json() == e2.canonical_json()


def test_trajectory_too_short_raises():
    with pytest.raises(ValueError, match="≥ 2 timesteps"):
        compile([[1.0, 2.0]])
