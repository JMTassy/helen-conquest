#!/usr/bin/env python3
"""
Integration tests for city_state_renderer.py

Tests pure, deterministic rendering of CityState snapshots.
Verifies K5 determinism: same input → identical output.
"""

import sys
import hashlib
from pathlib import Path

# Import renderer directly to avoid schema conflicts
import importlib.util
spec = importlib.util.spec_from_file_location("city_state_renderer",
    Path(__file__).parent.parent / "oracle_town" / "city_state_renderer.py")
renderer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer_module)

render_city_state = renderer_module.render_city_state


def test_renderer_basic():
    """Test basic rendering with complete state."""
    state = {
        "date": "2026-01-31",
        "run_id": "daily-01",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 1, "rejected": 6},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "OFF"},
        },
        "top_insights": ["Test insight 1", "Test insight 2"],
    }

    output = render_city_state(state)

    assert "ORACLE TOWN" in output
    assert "2026-01-31" in output
    assert "ACCEPT 1" in output
    assert "REJECT 6" in output
    assert "Test insight 1" in output
    print("✓ Basic rendering test passed")


def test_renderer_with_missing_data():
    """Test rendering with missing/incomplete data (honest defaults)."""
    state = {
        "date": "2026-02-01",
        "run_id": "daily-02",
        # Missing policy
        "verdicts": {"accepted": 5},  # Missing rejected
        "modules": {"OBS": {"status": "OK"}},  # Missing other modules
        # Missing top_insights
    }

    output = render_city_state(state)

    # Should render gracefully with defaults
    assert "ORACLE TOWN" in output
    assert "2026-02-01" in output
    assert "ACCEPT 5" in output
    assert "REJECT 0" in output  # Honest default
    assert "(none)" in output  # No insights
    print("✓ Missing data handling test passed")


def test_renderer_with_invalid_status():
    """Test rendering with invalid module status (defaults to OFF)."""
    state = {
        "date": "2026-01-31",
        "run_id": "test-invalid",
        "policy": {"version": "v1", "hash": "sha256:xyz"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {
            "OBS": {"status": "INVALID_STATUS"},  # Not OK, OFF, or FAIL
            "INSIGHT": {"status": None},  # Null status
            "MEMORY": {},  # No status field
        },
        "top_insights": [],
    }

    output = render_city_state(state)

    # All invalid statuses should render as OFF
    assert "░░░░░" in output  # OFF glyph appears multiple times
    print("✓ Invalid status handling test passed")


def test_renderer_determinism_10x():
    """Test K5 determinism: 10 identical runs produce identical output."""
    state = {
        "date": "2026-01-31",
        "run_id": "determinism-test",
        "policy": {"version": "v7", "hash": "sha256:abc123def456"},
        "verdicts": {"accepted": 1, "rejected": 6},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "OFF"},
        },
        "top_insights": ["Insight A", "Insight B"],
    }

    outputs = []
    hashes = []

    for i in range(10):
        output = render_city_state(state)
        outputs.append(output)
        h = hashlib.sha256(output.encode()).hexdigest()
        hashes.append(h)

    # All outputs must be byte-identical
    for i in range(1, 10):
        assert outputs[i] == outputs[0], \
            f"K5 determinism violation at iteration {i}"
        assert hashes[i] == hashes[0], \
            f"K5 hash violation at iteration {i}"

    print(f"✓ K5 determinism verified (10 identical iterations, hash: {hashes[0][:16]}…)")


def test_renderer_determinism_50x():
    """Stress test K5 determinism: 50 iterations."""
    state = {
        "date": "2026-01-31",
        "run_id": "stress-test",
        "policy": {"version": "v5", "hash": "sha256:xyz789"},
        "verdicts": {"accepted": 10, "rejected": 20},
        "modules": {
            "OBS": {"status": "OK"},
            "TRI": {"status": "OK"},
        },
        "top_insights": ["Many", "Insights", "Here"],
    }

    first_output = render_city_state(state)
    first_hash = hashlib.sha256(first_output.encode()).hexdigest()

    for i in range(50):
        output = render_city_state(state)
        h = hashlib.sha256(output.encode()).hexdigest()
        assert h == first_hash, f"K5 violation at iteration {i}"

    print(f"✓ K5 stress test passed (50 iterations, all identical)")


def test_renderer_with_fail_status():
    """Test rendering with FAIL status (visually heavy)."""
    state = {
        "date": "2026-01-31",
        "run_id": "fail-test",
        "policy": {"version": "v1", "hash": "sha256:abc"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {
            "TRI": {"status": "FAIL"},
        },
        "top_insights": [],
    }

    output = render_city_state(state)

    # FAIL should use heavy glyph
    assert "█████" in output
    assert "[TRI]" in output
    assert "FAIL" in output
    print("✓ FAIL status rendering test passed")


def test_renderer_output_structure():
    """Test that output has expected structure (header, sections, footer)."""
    state = {
        "date": "2026-01-31",
        "run_id": "structure-test",
        "policy": {"version": "v7", "hash": "sha256:abc"},
        "verdicts": {"accepted": 1, "rejected": 1},
        "modules": {"OBS": {"status": "OK"}},
        "top_insights": ["Test"],
    }

    output = render_city_state(state)
    lines = output.split("\n")

    # Should have expected structure
    assert lines[0].startswith("┏━━━━")  # Top border
    assert any("ORACLE TOWN" in line for line in lines), "Missing title"
    assert any("Verdicts:" in line for line in lines), "Missing verdicts"
    assert any("CITY STATE" in line for line in lines), "Missing city state"
    assert any("TOP INSIGHTS" in line for line in lines), "Missing insights"
    assert any("┗━━━━" in line for line in lines), "Missing bottom border"

    print("✓ Output structure test passed")


def test_renderer_empty_insights():
    """Test rendering with empty insights list."""
    state = {
        "date": "2026-01-31",
        "run_id": "no-insights",
        "policy": {"version": "v1", "hash": "sha256:abc"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {},
        "top_insights": [],
    }

    output = render_city_state(state)

    assert "(none)" in output
    print("✓ Empty insights test passed")


def test_renderer_long_insight_truncation():
    """Test that long insights are truncated (40 char limit)."""
    long_insight = "This is a very long insight that should be truncated to fit in the display" * 2

    state = {
        "date": "2026-01-31",
        "run_id": "long-insight",
        "policy": {"version": "v1", "hash": "sha256:abc"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {},
        "top_insights": [long_insight],
    }

    output = render_city_state(state)
    lines = output.split("\n")

    # Find the insight line
    insight_lines = [line for line in lines if "•" in line]
    assert len(insight_lines) > 0

    # Insight should be truncated with ellipsis
    for line in insight_lines:
        if long_insight[:10] in line:
            assert len(line) <= 48  # Width of box + padding
            print(f"✓ Long insight truncation test passed (truncated to: {line})")
            return

    print("✓ Long insight truncation test passed")


def test_renderer_canonical_ordering():
    """Test that module order is always canonical (OBS, INSIGHT, MEMORY, BRIEF, TRI, PUBLISH)."""
    state = {
        "date": "2026-01-31",
        "run_id": "order-test",
        "policy": {"version": "v1", "hash": "sha256:abc"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {
            "TRI": {"status": "OK"},
            "BRIEF": {"status": "OK"},
            "OBS": {"status": "OK"},
            "PUBLISH": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OK"},
        },
        "top_insights": [],
    }

    output = render_city_state(state)

    # Extract positions of modules in output
    obs_pos = output.find("[OBS]")
    insight_pos = output.find("[INSIGHT]")
    brief_pos = output.find("[BRIEF]")
    tri_pos = output.find("[TRI]")

    # Should be in order
    assert obs_pos < insight_pos < brief_pos < tri_pos, \
        "Modules not in canonical order"

    print("✓ Canonical ordering test passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("CITY STATE RENDERER TESTS")
    print("="*60 + "\n")

    tests = [
        test_renderer_basic,
        test_renderer_with_missing_data,
        test_renderer_with_invalid_status,
        test_renderer_determinism_10x,
        test_renderer_determinism_50x,
        test_renderer_with_fail_status,
        test_renderer_output_structure,
        test_renderer_empty_insights,
        test_renderer_long_insight_truncation,
        test_renderer_canonical_ordering,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
