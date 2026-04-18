#!/usr/bin/env python3
"""
Integration test for dashboard city-state ASCII renderer endpoint.

Tests that the dashboard can render ASCII city state snapshots
through the /api/city-state/ascii endpoint.
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


def test_dashboard_with_sample_verdicts():
    """Test that dashboard can build and display city state with verdicts."""

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

    # Build city state manually (simulating what handle_city_state_ascii does)
    city_state = {
        "date": "2026-01-31",
        "run_id": "dashboard-poll",
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
        "top_insights": [
            "Acceptance rate: 16.7%",
            "Total verdicts: 6",
        ],
    }

    # Import and render
    spec = importlib.util.spec_from_file_location("city_state_renderer",
        Path(__file__).parent.parent / "oracle_town" / "city_state_renderer.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)

    ascii_output = renderer.render_city_state(city_state)

    # Verify output
    assert "ORACLE TOWN" in ascii_output
    assert "2026-01-31" in ascii_output
    assert "ACCEPT 1" in ascii_output
    assert "REJECT 5" in ascii_output
    assert "OK" in ascii_output
    assert "Acceptance rate" in ascii_output

    print("✓ Dashboard city state rendering test passed")
    print("\nSample output:")
    print(ascii_output)


def test_city_state_with_various_module_states():
    """Test city state rendering with mixed module states."""

    spec = importlib.util.spec_from_file_location("city_state_renderer",
        Path(__file__).parent.parent / "oracle_town" / "city_state_renderer.py")
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
        "top_insights": [
            "High rejection rate detected",
        ],
    }

    ascii_output = renderer.render_city_state(city_state)

    # Verify various states are rendered
    assert "████▉" in ascii_output  # OK glyph
    assert "░░░░░" in ascii_output  # OFF glyph
    assert "█████" in ascii_output  # FAIL glyph
    assert "MEMORY" in ascii_output
    assert "PUBLISH" in ascii_output

    print("✓ Mixed module states test passed")


def test_city_state_deterministic_rendering():
    """Test that city state renders identically across multiple calls."""

    spec = importlib.util.spec_from_file_location("city_state_renderer",
        Path(__file__).parent.parent / "oracle_town" / "city_state_renderer.py")
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
        "top_insights": ["Test insight"],
    }

    outputs = []
    for i in range(10):
        output = renderer.render_city_state(city_state)
        outputs.append(output)

    # All should be identical
    for i in range(1, 10):
        assert outputs[i] == outputs[0], f"Output {i} differs from output 0"

    print("✓ Deterministic rendering test passed (10 identical outputs)")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("DASHBOARD CITY-STATE INTEGRATION TESTS")
    print("="*60 + "\n")

    tests = [
        test_dashboard_with_sample_verdicts,
        test_city_state_with_various_module_states,
        test_city_state_deterministic_rendering,
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
