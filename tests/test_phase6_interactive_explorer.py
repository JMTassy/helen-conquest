#!/usr/bin/env python3
"""
Integration tests for Phase 6: Interactive Explorer

Tests natural language query parsing and verdict search functionality.
Verifies K5 determinism (same query → identical results).
"""

import sys
import json
import tempfile
from pathlib import Path

# Add oracle_town to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly to avoid schema conflicts
import importlib.util
spec = importlib.util.spec_from_file_location("interactive_explorer",
    Path(__file__).parent.parent / "oracle_town" / "interactive_explorer.py")
ie_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ie_module)

QueryParser = ie_module.QueryParser
InteractiveExplorer = ie_module.InteractiveExplorer
QueryIntent = ie_module.QueryIntent


def test_query_parser_intent_detection():
    """Test intent detection from natural language questions."""
    parser = QueryParser()

    # Test search_topic intent
    q1 = parser.parse_question("What vendors had security issues?")
    assert q1.intent == 'search_topic', f"Expected search_topic, got {q1.intent}"

    # Test search_entity intent
    q2 = parser.parse_question("What about example.com?")
    assert q2.intent == 'search_entity', f"Expected search_entity, got {q2.intent}"

    # Test search_outcome intent
    q3 = parser.parse_question("What succeeded last week?")
    assert q3.intent == 'search_outcome', f"Expected search_outcome, got {q3.intent}"

    # Test timeline intent
    q4 = parser.parse_question("What happened last week?")
    assert q4.intent == 'timeline', f"Expected timeline, got {q4.intent}"

    print("✓ Intent detection tests passed")


def test_query_parser_entity_extraction():
    """Test entity extraction from questions."""
    parser = QueryParser()

    # Test vendor extraction
    q = parser.parse_question("vendor acme had issues")
    assert 'vendor' in q.entities or any('acme' in str(v).lower() for v in q.entities.values()), \
        f"Expected vendor entity, got {q.entities}"

    # Test gate extraction
    q = parser.parse_question("Show GATE_A rejections")
    assert 'gate' in q.entities, f"Expected gate entity, got {q.entities}"

    # Test decision extraction
    q = parser.parse_question("All REJECT verdicts")
    assert q.filters.get('decision') == 'REJECT', f"Expected REJECT filter, got {q.filters}"

    print("✓ Entity extraction tests passed")


def test_query_parser_time_range():
    """Test time range extraction."""
    parser = QueryParser()

    # Test last week
    q = parser.parse_question("What happened last week?")
    assert q.time_range is not None, "Expected time_range for 'last week'"
    assert len(q.time_range) == 2, "Time range should be (start, end) tuple"

    # Test last month
    q = parser.parse_question("Decisions from last month")
    assert q.time_range is not None, "Expected time_range for 'last month'"

    print("✓ Time range extraction tests passed")


def test_interactive_explorer_initialization():
    """Test InteractiveExplorer initialization."""
    # Create temporary ledger
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        ledger_path = f.name

    try:
        explorer = InteractiveExplorer(ledger_path=ledger_path)
        assert explorer.verdicts == [], "Empty ledger should have no verdicts"
        print("✓ InteractiveExplorer initialization test passed")
    finally:
        Path(ledger_path).unlink()


def test_interactive_explorer_verdict_loading():
    """Test loading verdicts from ledger."""
    # Create temporary ledger with sample verdicts
    verdicts = [
        {
            "receipt_id": "R-2026-01-30-0001",
            "decision": "ACCEPT",
            "reason": "Vendor request for API access approved",
            "timestamp": "2026-01-30T14:22:00Z",
            "gate": "GATE_A",
            "metadata": {}
        },
        {
            "receipt_id": "R-2026-01-30-0002",
            "decision": "REJECT",
            "reason": "Security issue detected: shell command injection",
            "timestamp": "2026-01-30T15:00:00Z",
            "gate": "GATE_B",
            "metadata": {}
        },
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for v in verdicts:
            f.write(json.dumps(v) + '\n')
        ledger_path = f.name

    try:
        explorer = InteractiveExplorer(ledger_path=ledger_path)
        assert len(explorer.verdicts) == 2, f"Expected 2 verdicts, got {len(explorer.verdicts)}"
        assert explorer.verdicts[0]['receipt_id'] == 'R-2026-01-30-0001'
        print("✓ Verdict loading test passed")
    finally:
        Path(ledger_path).unlink()


def test_interactive_explorer_search_topic():
    """Test search by topic."""
    verdicts = [
        {
            "receipt_id": "R-001",
            "decision": "ACCEPT",
            "reason": "Vendor request for security audit",
            "timestamp": "2026-01-30T14:22:00Z",
            "gate": "GATE_A",
        },
        {
            "receipt_id": "R-002",
            "decision": "REJECT",
            "reason": "Technical issue: API timeout",
            "timestamp": "2026-01-30T15:00:00Z",
            "gate": "GATE_B",
        },
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for v in verdicts:
            f.write(json.dumps(v) + '\n')
        ledger_path = f.name

    try:
        explorer = InteractiveExplorer(ledger_path=ledger_path)
        results = explorer.search_topic(QueryIntent(
            intent='search_topic',
            entities={'topic': ['vendor']},
            time_range=None,
            filters={},
            raw_question="What about vendor issues?",
        ))

        assert len(results) > 0, "Should find vendor-related verdicts"
        assert results[0]['receipt_id'] in ['R-001', 'R-002']
        print("✓ Search by topic test passed")
    finally:
        Path(ledger_path).unlink()


def test_interactive_explorer_search_outcome():
    """Test search by outcome."""
    verdicts = [
        {
            "receipt_id": "R-001",
            "decision": "ACCEPT",
            "reason": "Vendor approved",
            "timestamp": "2026-01-30T14:22:00Z",
            "gate": "GATE_A",
        },
        {
            "receipt_id": "R-002",
            "decision": "REJECT",
            "reason": "Security issue",
            "timestamp": "2026-01-30T15:00:00Z",
            "gate": "GATE_B",
        },
        {
            "receipt_id": "R-003",
            "decision": "REJECT",
            "reason": "Policy violation",
            "timestamp": "2026-01-30T16:00:00Z",
            "gate": "GATE_C",
        },
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for v in verdicts:
            f.write(json.dumps(v) + '\n')
        ledger_path = f.name

    try:
        explorer = InteractiveExplorer(ledger_path=ledger_path)
        results = explorer.search_outcome(QueryIntent(
            intent='search_outcome',
            entities={},
            time_range=None,
            filters={'decision': 'REJECT'},
            raw_question="Show rejections",
        ))

        assert len(results) == 2, f"Expected 2 REJECT verdicts, got {len(results)}"
        for r in results:
            assert r['decision'] == 'REJECT', f"Expected REJECT decision, got {r['decision']}"
        print("✓ Search by outcome test passed")
    finally:
        Path(ledger_path).unlink()


def test_interactive_explorer_compare_verdicts():
    """Test comparing two verdicts."""
    verdicts = [
        {
            "receipt_id": "R-001",
            "decision": "ACCEPT",
            "reason": "Vendor A approved",
            "timestamp": "2026-01-30T14:22:00Z",
            "gate": "GATE_A",
        },
        {
            "receipt_id": "R-002",
            "decision": "ACCEPT",
            "reason": "Vendor B approved",
            "timestamp": "2026-01-30T15:00:00Z",
            "gate": "GATE_A",
        },
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for v in verdicts:
            f.write(json.dumps(v) + '\n')
        ledger_path = f.name

    try:
        explorer = InteractiveExplorer(ledger_path=ledger_path)
        comparison = explorer.compare_verdicts('R-001', 'R-002')

        assert 'verdict_1' in comparison
        assert 'verdict_2' in comparison
        assert comparison['same_decision'] == True, "Both should be ACCEPT"
        assert comparison['same_gate'] == True, "Both should be GATE_A"
        print("✓ Verdict comparison test passed")
    finally:
        Path(ledger_path).unlink()


def test_interactive_explorer_determinism():
    """Test K5 determinism: same query → identical results."""
    verdicts = [
        {
            "receipt_id": f"R-{i:03d}",
            "decision": "ACCEPT" if i % 2 == 0 else "REJECT",
            "reason": f"Test verdict {i}",
            "timestamp": "2026-01-30T14:22:00Z",
            "gate": "GATE_A",
        }
        for i in range(10)
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for v in verdicts:
            f.write(json.dumps(v) + '\n')
        ledger_path = f.name

    try:
        # Run same query 10 times
        results_list = []
        for _ in range(10):
            explorer = InteractiveExplorer(ledger_path=ledger_path)
            results = explorer.search_outcome(QueryIntent(
                intent='search_outcome',
                entities={},
                time_range=None,
                filters={'decision': 'ACCEPT'},
                raw_question="Show accepts",
            ))
            results_list.append([r['receipt_id'] for r in results])

        # All results should be identical
        for i in range(1, 10):
            assert results_list[i] == results_list[0], \
                f"K5 determinism violation: iteration {i} differs from iteration 0"

        print("✓ K5 determinism test passed (10 iterations verified identical)")
    finally:
        Path(ledger_path).unlink()


def test_interactive_explorer_format_results():
    """Test result formatting."""
    results = [
        {
            'receipt_id': 'R-001',
            'decision': 'ACCEPT',
            'reason': 'Test reason 1',
            'timestamp': '2026-01-30T14:22:00Z',
            'gate': 'GATE_A',
        },
        {
            'receipt_id': 'R-002',
            'decision': 'REJECT',
            'reason': 'Test reason 2',
            'timestamp': '2026-01-30T15:00:00Z',
            'gate': 'GATE_B',
        },
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        ledger_path = f.name

    try:
        explorer = InteractiveExplorer(ledger_path=ledger_path)

        # Test text format
        text_output = explorer.format_results(results, format='text')
        assert 'R-001' in text_output, "Text output should contain receipt ID"
        assert 'ACCEPT' in text_output, "Text output should contain decision"

        # Test JSON format
        json_output = explorer.format_results(results, format='json')
        parsed = json.loads(json_output)
        assert len(parsed) == 2, "JSON output should contain 2 results"

        print("✓ Result formatting tests passed")
    finally:
        Path(ledger_path).unlink()


def run_all_tests():
    """Run all Phase 6 integration tests."""
    print("\n" + "="*60)
    print("ORACLE TOWN PHASE 6: INTERACTIVE EXPLORER TESTS")
    print("="*60 + "\n")

    tests = [
        test_query_parser_intent_detection,
        test_query_parser_entity_extraction,
        test_query_parser_time_range,
        test_interactive_explorer_initialization,
        test_interactive_explorer_verdict_loading,
        test_interactive_explorer_search_topic,
        test_interactive_explorer_search_outcome,
        test_interactive_explorer_compare_verdicts,
        test_interactive_explorer_determinism,
        test_interactive_explorer_format_results,
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
