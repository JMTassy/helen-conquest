"""
tests/test_conquest_kernel_isolation.py

Critical enforcement: CONQUEST game engine CANNOT access kernel directly.
CONQUEST is pure simulation (non-sovereign, non-IO).

Verifies:
1. No imports of GovernanceVM in CONQUEST
2. No imports of kernel in CONQUEST
3. No imports of ledger_writer in CONQUEST
4. CONQUEST is 100% pure deterministic engine
"""

import sys
import os
import inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_conquest_engine_has_no_kernel_imports():
    """
    Parse CONQUEST engine source code.
    Verify: zero imports from kernel, governance, or ledger modules.
    """
    from helen_os.conquest import engine

    source = inspect.getsource(engine)

    forbidden_terms = [
        "governance_vm",
        "GovernanceVM",
        "kernel",
        "ledger_writer",
        "LedgerWriterV2",
        "TownAdapter",
        "propose_receipt",
    ]

    for term in forbidden_terms:
        assert (
            term not in source
        ), f"CONQUEST imports forbidden term: {term}. CONQUEST must be pure simulation."

    print("✅ Test 1: CONQUEST engine has zero kernel imports")


def test_conquest_engine_is_pure():
    """
    Verify: CONQUEST engine.step() is a pure function.
    No IO, no randomness, no side effects.
    """
    from helen_os.conquest.engine import ConquestEngine

    engine = ConquestEngine()

    # Test determinism: same input → same output
    state = {"score": 0}
    serpent = {"stations": [1, 2, 3], "domain_state": {"alchemical": "stable"}}

    result1 = engine.step(state, serpent)
    result2 = engine.step(state, serpent)

    assert result1 == result2, "CONQUEST engine is not deterministic (not pure)"
    assert (
        "state_before" in result1 and "state_after" in result1 and "metrics" in result1
    ), "CONQUEST output structure incorrect"

    print("✅ Test 2: CONQUEST engine is pure (deterministic, no IO)")


def test_conquest_engine_has_no_ledger_access():
    """
    Verify: ConquestEngine class has zero methods that write to ledger.
    """
    from helen_os.conquest.engine import ConquestEngine

    engine = ConquestEngine()

    forbidden_methods = [
        "propose",
        "seal",
        "write_ledger",
        "append",
        "commit",
        "persist",
    ]

    for method_name in forbidden_methods:
        assert not hasattr(engine, method_name), (
            f"ConquestEngine has forbidden method: {method_name}. "
            f"CONQUEST cannot write to ledger."
        )

    print("✅ Test 3: CONQUEST engine has zero ledger access methods")


def test_conquest_trace_writes_only_to_run_trace():
    """
    Verify: ConquestTickTracer (if exists) writes ONLY to run_trace.ndjson.
    Never writes to sovereign ledger.
    """
    from helen_os.trace.run_trace import TraceLogger
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        trace_file = tmp_path / "run_trace.ndjson"

        logger = TraceLogger(trace_file)

        # Append a conquest tick
        tick_id = logger.append_conquest_tick(
            epoch=1,
            input_ref={"serpent_ast_hash": "a" * 64},
            state_before={"score": 0},
            state_after={"score": 3},
            metrics={"delta_score": 3},
        )

        # API v2: returns cum_hash (64-char hex), not legacy "tick_" prefix
        assert len(tick_id) == 64 and all(c in "0123456789abcdef" for c in tick_id), \
            f"Expected 64-char hex cum_hash, got: {tick_id}"

        # Verify only one file was written (run_trace.ndjson, not ledger)
        files_written = list(tmp_path.glob("*"))
        assert len(files_written) == 1, (
            f"ConquestTickTracer wrote multiple files: {files_written}. "
            f"Should only write run_trace.ndjson."
        )
        assert files_written[0].name == "run_trace.ndjson", (
            f"Wrong file written: {files_written[0].name}. "
            f"Should be run_trace.ndjson."
        )

        print("✅ Test 4: CONQUEST trace writes ONLY to run_trace.ndjson")


def test_conquest_extract_writes_to_memory_only():
    """
    Verify: CONQUEST extraction writes ONLY to MemoryKernel.
    Never to sovereign ledger.
    """
    # Mock memory class
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
        "metrics": {"delta_score": 5},
    }

    extract_tick_to_memory(mock_memory, tick)

    # Verify facts are all namespaced (conquest.*)
    for key, value, actor, status in mock_memory.facts:
        assert key.startswith("conquest."), (
            f"Fact key not namespaced: {key}. "
            f"Should start with 'conquest.'."
        )
        assert actor == "system", (
            f"Fact actor is not 'system': {actor}. "
            f"CONQUEST extraction must be 'system' only."
        )

    print("✅ Test 5: CONQUEST extract writes to memory.ndjson (namespaced facts)")


def test_no_raw_requests_from_conquest_to_kernel():
    """
    Verify: CONQUEST engine makes zero HTTP/network requests.
    It's a pure computation, not a networked agent.
    """
    from helen_os.conquest.engine import ConquestEngine
    import inspect

    engine = ConquestEngine()
    source = inspect.getsource(ConquestEngine)

    forbidden = [
        "requests",
        "urllib",
        "http",
        "socket",
        "POST",
        "GET",
        "fetch",
    ]

    for term in forbidden:
        assert (
            term not in source
        ), f"CONQUEST has network call: {term}. CONQUEST must be pure simulation."

    print("✅ Test 6: CONQUEST makes zero network requests")


if __name__ == "__main__":
    try:
        test_conquest_engine_has_no_kernel_imports()
        test_conquest_engine_is_pure()
        test_conquest_engine_has_no_ledger_access()
        test_conquest_trace_writes_only_to_run_trace()
        test_conquest_extract_writes_to_memory_only()
        test_no_raw_requests_from_conquest_to_kernel()
        print("\n✅ All 6 CONQUEST isolation tests PASSED")
    except AssertionError as e:
        print(f"\n❌ CONQUEST isolation test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
