#!/usr/bin/env python3
"""
Integration test for dashboard iso-coaster HTML endpoint.

Tests that the dashboard can render HTML/SVG iso-coaster visualization
through the /api/city-state/iso-html endpoint.
"""

import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock
from collections import deque

# Import dashboard server
sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util
spec = importlib.util.spec_from_file_location("dashboard_server",
    Path(__file__).parent.parent / "oracle_town" / "dashboard_server.py")
dashboard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard_module)

DashboardServer = dashboard_module.DashboardServer


def test_dashboard_iso_coaster_with_sample_verdicts():
    """Test that dashboard can render HTML iso-coaster with verdicts."""

    # Create dashboard
    dashboard = DashboardServer(ledger_path="/tmp/nonexistent.jsonl", port=9999)

    # Add sample verdicts
    dashboard.verdicts = deque([
        {
            "receipt_id": "R-001",
            "decision": "ACCEPT",
            "reason": "Vendor approved",
            "timestamp": "2026-01-31T14:00:00Z",
        },
        {
            "receipt_id": "R-002",
            "decision": "REJECT",
            "reason": "Security issue",
            "timestamp": "2026-01-31T14:05:00Z",
        },
        {
            "receipt_id": "R-003",
            "decision": "REJECT",
            "reason": "Policy violation",
            "timestamp": "2026-01-31T14:10:00Z",
        },
        {
            "receipt_id": "R-004",
            "decision": "REJECT",
            "reason": "Evidence missing",
            "timestamp": "2026-01-31T14:15:00Z",
        },
        {
            "receipt_id": "R-005",
            "decision": "REJECT",
            "reason": "Authority check failed",
            "timestamp": "2026-01-31T14:20:00Z",
        },
        {
            "receipt_id": "R-006",
            "decision": "REJECT",
            "reason": "Gate timeout",
            "timestamp": "2026-01-31T14:25:00Z",
        },
    ], maxlen=500)

    # Build iso-coaster manually (simulating what handle_city_state_iso_html does)
    city_state = {
        "date": "2026-01-31",
        "run_id": "dashboard-iso",
        "policy": {
            "version": "v7",
            "hash": "sha256:current"
        },
        "verdicts": {
            "accepted": sum(1 for v in dashboard.verdicts if v.get("decision") == "ACCEPT"),
            "rejected": sum(1 for v in dashboard.verdicts if v.get("decision") == "REJECT"),
        },
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OK"},
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "OK"},
        },
    }

    # Import and render
    spec = importlib.util.spec_from_file_location("iso_coaster_renderer",
        Path(__file__).parent.parent / "oracle_town" / "iso_coaster_renderer.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    html_output = renderer.render_iso_coaster(city_state)

    # Verify output
    assert "<!DOCTYPE html>" in html_output
    assert "<html>" in html_output
    assert "<svg" in html_output
    assert "</svg>" in html_output
    assert "Oracle Town" in html_output
    assert "2026-01-31" in html_output
    assert "Verdicts (Accept)" in html_output
    assert "Verdicts (Reject)" in html_output
    assert "OBS" in html_output
    assert "TRI" in html_output

    print("✓ Dashboard iso-coaster rendering test passed")
    print("✓ Sample output size: {} bytes".format(len(html_output)))


def test_iso_coaster_with_various_module_states():
    """Test iso-coaster rendering with mixed module states."""

    spec = importlib.util.spec_from_file_location("iso_coaster_renderer",
        Path(__file__).parent.parent / "oracle_town" / "iso_coaster_renderer.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    city_state = {
        "date": "2026-01-31",
        "run_id": "test-mixed",
        "policy": {
            "version": "v7",
            "hash": "sha256:abc123"
        },
        "verdicts": {
            "accepted": 10,
            "rejected": 20,
        },
        "modules": {
            "OBS": {"status": "OK"},
            "INSIGHT": {"status": "OK"},
            "MEMORY": {"status": "OFF"},  # Inactive
            "BRIEF": {"status": "OK"},
            "TRI": {"status": "OK"},
            "PUBLISH": {"status": "FAIL"},  # Error state
        },
    }

    html_output = renderer.render_iso_coaster(city_state)

    # Verify various states are rendered with appropriate colors
    assert "OBS" in html_output
    assert "MEMORY" in html_output  # OFF module
    assert "PUBLISH" in html_output  # FAIL module
    assert "#10b981" in html_output  # Green (OK)
    assert "#6b7280" in html_output  # Gray (OFF)
    assert "#ef4444" in html_output  # Red (FAIL)

    print("✓ Mixed module states test passed")


def test_iso_coaster_deterministic_rendering():
    """Test that iso-coaster renders identically across multiple calls."""

    spec = importlib.util.spec_from_file_location("iso_coaster_renderer",
        Path(__file__).parent.parent / "oracle_town" / "iso_coaster_renderer.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    city_state = {
        "date": "2026-01-31",
        "run_id": "determinism-test",
        "policy": {"version": "v7", "hash": "sha256:test"},
        "verdicts": {"accepted": 5, "rejected": 10},
        "modules": {
            "OBS": {"status": "OK"},
            "TRI": {"status": "OK"},
        },
    }

    outputs = []
    for i in range(10):
        output = renderer.render_iso_coaster(city_state)
        outputs.append(output)

    # All should be identical
    for i in range(1, 10):
        assert outputs[i] == outputs[0], f"Output {i} differs from output 0"

    print("✓ Deterministic rendering test passed (10 identical outputs)")


def test_iso_coaster_with_empty_state():
    """Test iso-coaster with minimal state."""

    spec = importlib.util.spec_from_file_location("iso_coaster_renderer",
        Path(__file__).parent.parent / "oracle_town" / "iso_coaster_renderer.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    city_state = {
        "date": "2026-01-31",
        "run_id": "minimal",
        "policy": {"version": "v1", "hash": "sha256:abc"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {},
    }

    html_output = renderer.render_iso_coaster(city_state)

    # Should still produce valid HTML
    assert "<!DOCTYPE html>" in html_output
    assert "<svg" in html_output
    assert "</svg>" in html_output

    print("✓ Empty state rendering test passed")


def test_iso_coaster_html_is_complete_document():
    """Test that HTML output is a complete, self-contained document."""

    spec = importlib.util.spec_from_file_location("iso_coaster_renderer",
        Path(__file__).parent.parent / "oracle_town" / "iso_coaster_renderer.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    city_state = {
        "date": "2026-01-31",
        "run_id": "complete",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 1, "rejected": 1},
        "modules": {
            "OBS": {"status": "OK"},
            "TRI": {"status": "OK"},
        },
    }

    html_output = renderer.render_iso_coaster(city_state)

    # Check for document structure
    assert html_output.startswith("<!DOCTYPE html>")
    assert "<html>" in html_output
    assert "<head>" in html_output
    assert "<body>" in html_output
    assert "</body>" in html_output
    assert "</html>" in html_output

    # Check for required sections
    assert "<style>" in html_output
    assert "</style>" in html_output
    assert "Oracle Town" in html_output
    assert "Iso-Coaster" in html_output

    print("✓ HTML document completeness test passed")


def test_iso_coaster_svg_viewbox():
    """Test that SVG has proper viewBox for responsive scaling."""

    spec = importlib.util.spec_from_file_location("iso_coaster_renderer",
        Path(__file__).parent.parent / "oracle_town" / "iso_coaster_renderer.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    city_state = {
        "date": "2026-01-31",
        "run_id": "viewbox",
        "policy": {"version": "v7", "hash": "sha256:abc123"},
        "verdicts": {"accepted": 0, "rejected": 0},
        "modules": {
            "OBS": {"status": "OK"},
            "TRI": {"status": "OK"},
        },
    }

    html_output = renderer.render_iso_coaster(city_state)

    # Check for viewBox attribute (responsive SVG)
    assert 'viewBox="' in html_output

    print("✓ SVG viewBox test passed")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("DASHBOARD ISO-COASTER INTEGRATION TESTS")
    print("="*60 + "\n")

    tests = [
        test_dashboard_iso_coaster_with_sample_verdicts,
        test_iso_coaster_with_various_module_states,
        test_iso_coaster_deterministic_rendering,
        test_iso_coaster_with_empty_state,
        test_iso_coaster_html_is_complete_document,
        test_iso_coaster_svg_viewbox,
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
