"""Test: TEMPLE_V1 is Non-Sovereign (authority=NONE)."""
import pytest
from helen_os.temple.temple_v1 import run_temple_exploration

def test_temple_authority_is_none():
    """TEMPLE artifacts always have authority='NONE'."""
    artifact = run_temple_exploration(
        session_id="test_001",
        theme="Test exploration",
        her_threads=[],
        hal_frictions=[],
        tension_map=[],
        center_sketches=[],
        export_candidates=[],
    )
    assert artifact["authority"] == "NONE"

def test_temple_no_sovereign_fields():
    """TEMPLE artifacts must not contain sovereign fields."""
    forbidden_fields = ["verdict", "state_mutation", "ship", "decision", "receipt_claimed"]
    artifact = run_temple_exploration(
        session_id="test_002",
        theme="Test exploration",
        her_threads=[{"thread_id": "t1", "content": "test"}],
        hal_frictions=[{"friction_id": "f1", "content": "test"}],
        tension_map=[{"tension_id": "tn1", "pole_a": "A", "pole_b": "B", "description": "test"}],
        center_sketches=[{"sketch_id": "s1", "content": "test"}],
        export_candidates=[{"candidate_id": "e1", "candidate_type": "TRACE", "content": "test"}],
    )
    for field in forbidden_fields:
        assert field not in artifact
