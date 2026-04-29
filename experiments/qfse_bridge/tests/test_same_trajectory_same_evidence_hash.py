"""Same trajectory → same hash. Different trajectory → different hash."""
import numpy as np

from qfse_bridge.qfse_evidence_compiler import compile, trajectory_hash


def _traj(seed: int, T: int = 15, D: int = 16) -> list:
    return np.random.default_rng(seed).standard_normal((T, D)).tolist()


def test_same_trajectory_same_hash():
    traj = _traj(7)
    assert trajectory_hash(traj) == trajectory_hash(traj)


def test_hash_has_sha256_prefix():
    assert trajectory_hash(_traj(1)).startswith("sha256:")


def test_different_trajectories_different_hashes():
    assert trajectory_hash(_traj(7)) != trajectory_hash(_traj(8))


def test_evidence_trajectory_hash_matches_direct_hash():
    traj = _traj(99)
    assert compile(traj).trajectory_hash == trajectory_hash(traj)


def test_shape_change_changes_hash():
    rng = np.random.default_rng(42)
    t1 = rng.standard_normal((10, 8)).tolist()
    t2 = rng.standard_normal((10, 16)).tolist()
    assert trajectory_hash(t1) != trajectory_hash(t2)
