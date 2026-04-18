#!/usr/bin/env python3
"""
Integration tests for iso_coaster_renderer.py

Tests pure, deterministic HTML/SVG rendering of CityState iso-coaster visualization.
Verifies K5 determinism: same input → identical output.
"""

import sys
import hashlib
from pathlib import Path

# Import renderer directly to avoid schema conflicts
import importlib.util
spec = importlib.util.spec_from_file_location("iso_coaster_renderer",
    Path(__file__).parent.parent / "oracle_town" / "iso_coaster_renderer.py")
renderer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer_module)

render_iso_coaster = renderer_module.render_iso_coaster


def test_renderer_basic_html_structure():
    """Test that basic ISO-coaster renders valid HTML structure."""
    state = {
        "date": "2026-01-31",
        "run_id": "test-iso",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 1, "rejected": 5},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "FAIL"},
        },
    }

    output = render_iso_coaster(state)

    # Verify HTML structure
    assert "<!DOCTYPE html>" in output
    assert "<html>" in output
    assert "<title>Oracle Town — Iso-Coaster</title>" in output
    assert "<svg" in output
    assert "</svg>" in output
    assert "</html>" in output

    # Verify content (wrapped in stat-value divs)
    assert "2026-01-31" in output
    assert "Verdicts (Accept)" in output
    assert ">1<" in output  # Accept count in value div
    assert "Verdicts (Reject)" in output
    assert ">5<" in output  # Reject count in value div
    assert "v7" in output

    print("✓ Basic HTML structure test passed")


def test_renderer_with_missing_modules():
    """Test rendering with missing modules (graceful degradation)."""
    state = {
        "date": "2026-01-31",
        "run_id": "partial",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {"OBS": {"status": "OK"}},  # Only one module
    }

    output = render_iso_coaster(state)

    # Should still render valid HTML
    assert "<!DOCTYPE html>" in output
    assert "<svg" in output
    assert "OBS" in output  # The provided module should be rendered (may be in SVG text element)

    print("✓ Missing modules test passed")


def test_renderer_with_all_status_types():
    """Test rendering with OK, OFF, and FAIL statuses."""
    state = {
        "date": "2026-01-31",
        "run_id": "all-status",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 10, "rejected": 20},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OFF"},
            "MEMORY": {"status": "FAIL"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "OFF"},
        },
    }

    output = render_iso_coaster(state)

    # All module names should be in output (in SVG text elements, without brackets)
    assert "OBS" in output
    assert "INSIGHT" in output
    assert "MEMORY" in output
    assert "BRIEF" in output
    assert "TRI" in output
    assert "PUBLISH" in output

    # Colors should be applied (hex codes)
    assert "#10b981" in output or "#6b7280" in output or "#ef4444" in output  # Some colors

    print("✓ All status types test passed")


def test_renderer_determinism_5x():
    """Test K5 determinism: 5 identical runs produce identical output."""
    state = {
        "date": "2026-01-31",
        "run_id": "determinism-test",
        "policy": {"version": "v7", "hash": "sha256:abc123def456"},
        "verdicts": {"accepted": 5, "rejected": 10},
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "FAIL"},
        },
    }

    outputs = []
    hashes = []

    for i in range(5):
        output = render_iso_coaster(state)
        outputs.append(output)
        h = hashlib.sha256(output.encode()).hexdigest()
        hashes.append(h)

    # All outputs must be byte-identical
    for i in range(1, 5):
        assert outputs[i] == outputs[0], \
            f"K5 determinism violation at iteration {i}"
        assert hashes[i] == hashes[0], \
            f"K5 hash violation at iteration {i}"

    print(f"✓ K5 determinism verified (5 identical iterations, hash: {hashes[0][:16]}…)")


def test_renderer_determinism_stress_10x():
    """Stress test K5 determinism: 10 iterations."""
    state = {
        "date": "2026-01-31",
        "run_id": "stress-test",
        "policy": {"version": "v5", "hash": "sha256:xyz789"},
        "verdicts": {"accepted": 15, "rejected": 25},
        "modules": {
            "OBS": {"status": "OK"},
            "TRI": {"status": "OK"},
        },
    }

    first_output = render_iso_coaster(state)
    first_hash = hashlib.sha256(first_output.encode()).hexdigest()

    for i in range(10):
        output = render_iso_coaster(state)
        h = hashlib.sha256(output.encode()).hexdigest()
        assert h == first_hash, f"K5 violation at iteration {i}"

    print(f"✓ K5 stress test passed (10 iterations, all identical)")


def test_renderer_with_empty_modules():
    """Test rendering with no modules (edge case)."""
    state = {
        "date": "2026-01-31",
        "run_id": "empty",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {},
    }

    output = render_iso_coaster(state)

    # Should still produce valid HTML
    assert "<!DOCTYPE html>" in output
    assert "<svg" in output
    assert "2026-01-31" in output

    print("✓ Empty modules test passed")


def test_renderer_svg_contains_buildings():
    """Test that SVG contains building elements (polygons for diamonds)."""
    state = {
        "date": "2026-01-31",
        "run_id": "buildings",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 1, "rejected": 1},
        "modules": {
            "OBS": {"status": "OK"},
            "TRI": {"status": "OK"},
        },
    }

    output = render_iso_coaster(state)

    # Should contain polygon elements for buildings
    assert "<polygon" in output
    assert "points=" in output

    # Should contain text labels
    assert "<text" in output
    assert "OBS" in output
    assert "TRI" in output

    # Should contain circles for status indicators
    assert "<circle" in output

    print("✓ SVG buildings test passed")


def test_renderer_tri_immutable_marker():
    """Test that TRI module has immutable marker."""
    state = {
        "date": "2026-01-31",
        "run_id": "immutable-marker",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 1, "rejected": 1},
        "modules": {
            "TRI": {"status": "OK"},
        },
    }

    output = render_iso_coaster(state)

    # TRI should have IMMUTABLE marker
    assert "IMMUTABLE" in output

    print("✓ TRI immutable marker test passed")


def test_renderer_with_missing_verdicts():
    """Test rendering with missing verdict counts."""
    state = {
        "date": "2026-01-31",
        "run_id": "missing-verdicts",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        # Missing verdicts key
        "modules": {
            "OBS": {"status": "OK"},
        },
    }

    output = render_iso_coaster(state)

    # Should handle gracefully
    assert "<!DOCTYPE html>" in output
    assert "<svg" in output

    print("✓ Missing verdicts handling test passed")


def test_renderer_output_has_statistics_header():
    """Test that output includes statistics section."""
    state = {
        "date": "2026-02-15",
        "run_id": "stats-test",
        "policy": {"version": "v8", "hash": "sha256:def456"},
        "verdicts": {"accepted": 7, "rejected": 13},
        "modules": {
            "OBS": {"status": "OK"},
        },
    }

    output = render_iso_coaster(state)

    # Should include stats header
    assert "Policy Version" in output
    assert "Verdicts (Accept)" in output
    assert "Verdicts (Reject)" in output
    assert "Snapshot Date" in output

    # Should include actual values
    assert "v8" in output
    assert "2026-02-15" in output

    print("✓ Statistics header test passed")


def test_renderer_output_has_disclaimer():
    """Test that output includes disclaimer."""
    state = {
        "date": "2026-01-31",
        "run_id": "disclaimer-test",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {},
    }

    output = render_iso_coaster(state)

    # Should include disclaimer
    assert "Disclaimer" in output
    assert "non-authoritative" in output
    assert "ledger" in output

    print("✓ Disclaimer test passed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("ISO-COASTER RENDERER TESTS")
    print("="*60 + "\n")

    tests = [
        test_renderer_basic_html_structure,
        test_renderer_with_missing_modules,
        test_renderer_with_all_status_types,
        test_renderer_determinism_5x,
        test_renderer_determinism_stress_10x,
        test_renderer_with_empty_modules,
        test_renderer_svg_contains_buildings,
        test_renderer_tri_immutable_marker,
        test_renderer_with_missing_verdicts,
        test_renderer_output_has_statistics_header,
        test_renderer_output_has_disclaimer,
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
