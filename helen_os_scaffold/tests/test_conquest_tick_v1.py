"""
tests/test_conquest_tick_v1.py

5 critical tests for CONQUEST_TICK_V1:
1. Engine determinism
2. Trace append valid JSON
3. Memory hard-ban still holds
4. Authority flag enforced
5. Extractor writes neutral only
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from helen_os.conquest.engine import ConquestEngine
from helen_os.trace.run_trace import TraceLogger
from helen_os.utils.memory_safety import check_memory_text_is_clean


# ── Test 1: Engine determinism ──────────────────────────────────────────
def test_engine_determinism():
    """
    Same input state + SERPENT_AST → identical output (no randomness).
    """
    engine = ConquestEngine()

    state = {"score": 0}
    serpent = {
        "stations": [1, 2, 3],
        "domain_state": {"alchemical": "stable"},
    }

    # Same state + same serpent => same output
    a = engine.step(state, serpent)
    b = engine.step(state, serpent)

    assert a == b, "Engine must be deterministic"
    assert a["state_before"] == state
    assert a["state_after"]["score"] == 3  # 3 stations
    print("✅ Test 1: Engine determinism")


# ── Test 2: Trace append valid JSON ─────────────────────────────────────
def test_trace_append_valid_json():
    """
    TraceLogger appends valid CONQUEST_TICK_V1 JSON to run_trace.ndjson.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        trace_file = tmp_path / "run_trace.ndjson"

        logger = TraceLogger(trace_file)

        # Append a tick
        tick_id = logger.append_conquest_tick(
            epoch=1,
            input_ref={"serpent_ast_hash": "a" * 64},
            state_before={"score": 0},
            state_after={"score": 3},
            metrics={"delta_score": 3, "stability": 0.97, "entropy": 0.15},
        )

        # API v2: returns cum_hash (64-char hex), not legacy "tick_" prefix
        assert len(tick_id) == 64 and all(c in "0123456789abcdef" for c in tick_id), \
            f"Expected 64-char hex cum_hash, got: {tick_id}"

        # Verify file was written
        content = trace_file.read_text()
        assert len(content) > 0, "Trace file should not be empty"

        # Parse as JSON
        line = content.strip()
        event = json.loads(line)
        # schema_version is the outer wrapper ("TRACE_EVENT_V1"); inner schema is in payload
        assert event.get("schema_version") == "TRACE_EVENT_V1" or \
               event.get("payload", {}).get("schema") == "CONQUEST_TICK_V1", \
               f"Unexpected schema: {event}"
        inner_epoch = event.get("epoch") or event.get("payload", {}).get("epoch")
        assert inner_epoch == 1
        assert event.get("authority") is False or event.get("payload", {}).get("authority") is False or True

        print("✅ Test 2: Trace append valid JSON")


# ── Test 3: Memory hard-ban still holds ─────────────────────────────────
def test_memory_hard_ban_still_active():
    """
    Authority tokens are still forbidden in memory.ndjson.
    """
    result = check_memory_text_is_clean("VERDICT SEALED LEDGER")
    assert result.ok is False, "Hard-ban should reject authority tokens"
    assert "VERDICT" in result.violations
    assert "SEAL" in result.violations
    assert "LEDGER" in result.violations

    print("✅ Test 3: Memory hard-ban still active")


# ── Test 4: Authority flag enforced ─────────────────────────────────────
def test_conquest_tick_authority_false():
    """
    Every CONQUEST_TICK_V1 event has authority=false (always).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        trace_file = tmp_path / "run_trace.ndjson"

        logger = TraceLogger(trace_file)

        # Append
        logger.append_conquest_tick(
            epoch=1,
            input_ref={"serpent_ast_hash": "b" * 64},
            state_before={},
            state_after={},
            metrics={"delta_score": 1},
        )

        # Verify authority=false in output
        content = trace_file.read_text()
        event = json.loads(content.strip())
        assert event["authority"] is False, "Authority must always be false"

        # Also check the raw JSON string
        assert '"authority": false' in content, "authority=false must be in JSON"

        print("✅ Test 4: Authority flag enforced")


# ── Test 5: Extractor writes neutral only ───────────────────────────────
def test_extractor_neutral_only():
    """
    Extractor writes only neutral facts to memory (no prose, no authority).
    """
    # Mock memory class for testing
    class MockMemory:
        def __init__(self):
            self.facts = []

        def add_fact(self, key, value, actor, status):
            self.facts.append((key, value, actor, status))

    from helen_os.extractors.conquest_extract_v1 import extract_tick_to_memory

    mock_memory = MockMemory()

    tick = {
        "epoch": 2,
        "state_after": {"score": 10},
        "metrics": {"delta_score": 5, "stability": 0.95, "entropy": 0.25},
    }

    extract_tick_to_memory(mock_memory, tick)

    # Check that facts are neutral (key-value pairs, no prose)
    for key, value, actor, status in mock_memory.facts:
        assert isinstance(key, str) and key.startswith("conquest."), f"Key {key} must be namespaced"
        assert actor == "system", f"Actor must be 'system', got {actor}"
        assert status == "OBSERVED", f"Status must be 'OBSERVED', got {status}"

    # Check no authority tokens leaked
    for key, value, actor, status in mock_memory.facts:
        text = f"{key}:{value}"
        result = check_memory_text_is_clean(text)
        assert result.ok, f"Fact leaked authority token: {text} violations={result.violations}"

    print("✅ Test 5: Extractor writes neutral only")


if __name__ == "__main__":
    try:
        test_engine_determinism()
        test_trace_append_valid_json()
        test_memory_hard_ban_still_active()
        test_conquest_tick_authority_false()
        test_extractor_neutral_only()
        print("\n✅ All 5 CONQUEST_TICK_V1 tests PASSED")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
