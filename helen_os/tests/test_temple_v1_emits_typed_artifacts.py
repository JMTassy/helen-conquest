"""Test: TEMPLE_V1 Emits Typed, Deterministic Artifacts."""
import pytest
import json
from helen_os.temple.temple_v1 import run_temple_exploration
from helen_os.governance.canonical import sha256_prefixed

def test_temple_artifact_has_required_fields():
    """TEMPLE artifact must have all required schema fields."""
    artifact = run_temple_exploration(
        session_id="test_101",
        theme="Basic exploration",
        her_threads=[],
        hal_frictions=[],
        tension_map=[],
        center_sketches=[],
        export_candidates=[],
    )
    required_fields = ["schema_name", "schema_version", "session_id", "theme", "authority",
                       "her_threads", "hal_frictions", "tension_map", "center_sketches", "export_candidates"]
    for field in required_fields:
        assert field in artifact

def test_temple_artifact_is_hashable():
    """TEMPLE artifact can be hashed via canonical.py."""
    artifact = run_temple_exploration(
        session_id="test_102",
        theme="Hashable artifact",
        her_threads=[{"thread_id": "t1", "content": "test"}],
        hal_frictions=[],
        tension_map=[],
        center_sketches=[],
        export_candidates=[],
    )
    artifact_hash = sha256_prefixed(artifact)
    assert isinstance(artifact_hash, str)
    assert artifact_hash.startswith("sha256:")

def test_temple_artifact_deterministic():
    """Same input → same hash (deterministic)."""
    input_data = {
        "session_id": "test_103",
        "theme": "Determinism test",
        "her_threads": [{"thread_id": "t1", "content": "test"}],
        "hal_frictions": [],
        "tension_map": [],
        "center_sketches": [],
        "export_candidates": [],
    }
    artifact1 = run_temple_exploration(**input_data)
    artifact2 = run_temple_exploration(**input_data)
    hash1 = sha256_prefixed(artifact1)
    hash2 = sha256_prefixed(artifact2)
    assert hash1 == hash2
