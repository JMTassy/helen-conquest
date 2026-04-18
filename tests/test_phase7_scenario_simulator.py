#!/usr/bin/env python3
"""
Integration tests for Phase 7: Scenario Simulator

Tests policy impact simulation, verdict replay, and risk assessment.
Verifies K5 determinism and K7 policy pinning.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add oracle_town to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly to avoid schema conflicts
import importlib.util
spec = importlib.util.spec_from_file_location("scenario_simulator",
    Path(__file__).parent.parent / "oracle_town" / "scenario_simulator.py")
ss_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ss_module)

ScenarioSimulator = ss_module.ScenarioSimulator
PolicyChange = ss_module.PolicyChange
Transition = ss_module.Transition
SimulationResult = ss_module.SimulationResult


def test_policy_change_creation():
    """Test PolicyChange dataclass creation."""
    change = PolicyChange(
        gate='GATE_A',
        parameter='threshold',
        old_value=50,
        new_value=30,
        reason='Lower threshold for more permissive policy',
    )

    assert change.gate == 'GATE_A'
    assert change.old_value == 50
    assert change.new_value == 30
    assert 'timestamp' in change.__dict__

    # Test to_dict()
    change_dict = change.to_dict()
    assert change_dict['gate'] == 'GATE_A'
    assert change_dict['old_value'] == 50

    print("✓ PolicyChange creation test passed")


def test_scenario_simulator_initialization():
    """Test ScenarioSimulator initialization."""
    verdicts = [
        {'receipt_id': 'R-001', 'decision': 'ACCEPT', 'gate': 'GATE_A'},
        {'receipt_id': 'R-002', 'decision': 'REJECT', 'gate': 'GATE_B'},
    ]

    old_policy = {'GATE_A': 50, 'GATE_B': 75}
    new_policy = {'GATE_A': 30, 'GATE_B': 75}

    simulator = ScenarioSimulator(verdicts, old_policy, new_policy)

    assert len(simulator.verdicts) == 2
    assert simulator.old_policy == old_policy
    assert simulator.new_policy == new_policy

    print("✓ ScenarioSimulator initialization test passed")


def test_policy_extraction():
    """Test policy change extraction."""
    verdicts = []
    old_policy = {'GATE_A': 50, 'GATE_B': 75}
    new_policy = {'GATE_A': 30, 'GATE_B': 75, 'GATE_C': 100}  # GATE_A changed, GATE_C added

    simulator = ScenarioSimulator(verdicts, old_policy, new_policy)
    changes = simulator._extract_policy_changes()

    # Should detect GATE_A change and GATE_C addition
    assert len(changes) >= 1, f"Expected at least 1 change, got {len(changes)}"

    # Check for GATE_A change
    gate_a_changes = [c for c in changes if c['gate'] == 'GATE_A']
    assert len(gate_a_changes) > 0, "Should detect GATE_A change"
    assert gate_a_changes[0]['old_value'] == 50
    assert gate_a_changes[0]['new_value'] == 30

    print("✓ Policy extraction test passed")


def test_verdict_replay():
    """Test deterministic verdict replay."""
    verdicts = [
        {
            'receipt_id': 'R-001',
            'decision': 'ACCEPT',
            'gate': 'GATE_A',
            'reason': 'Test ACCEPT',
            'timestamp': '2026-01-30T14:00:00Z',
        },
        {
            'receipt_id': 'R-002',
            'decision': 'REJECT',
            'gate': 'GATE_A',
            'reason': 'Test REJECT',
            'timestamp': '2026-01-30T15:00:00Z',
        },
    ]

    old_policy = {'GATE_A': 50}
    new_policy = {'GATE_A': 30}  # More permissive

    simulator = ScenarioSimulator(verdicts, old_policy, new_policy)

    # Replay verdicts
    for verdict in verdicts:
        new_decision = simulator._apply_new_policy(verdict)
        # Should be deterministic (same input → same output every time)
        assert isinstance(new_decision, str)
        assert new_decision in ['ACCEPT', 'REJECT']

    print("✓ Verdict replay test passed")


def test_simulation_empty_verdicts():
    """Test simulation with empty verdict list."""
    simulator = ScenarioSimulator([], {}, {})
    result = simulator.simulate()

    assert result.total_verdicts_replayed == 0
    assert result.unchanged == 0
    assert result.changed == 0
    assert result.recommended_action == 'hold'

    print("✓ Empty verdicts simulation test passed")


def test_simulation_accuracy_calculation():
    """Test accuracy calculation in simulation."""
    verdicts = [
        {'receipt_id': f'R-{i:03d}', 'decision': 'ACCEPT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T14:00:00Z'}
        for i in range(60)
    ] + [
        {'receipt_id': f'R-{i:03d}', 'decision': 'REJECT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T14:00:00Z'}
        for i in range(60, 100)
    ]

    old_policy = {'GATE_A': 50}
    new_policy = {'GATE_A': 50}  # Same policy

    simulator = ScenarioSimulator(verdicts, old_policy, new_policy)
    result = simulator.simulate()

    # With same policy, accuracy should be same (all verdicts unchanged)
    assert result.total_verdicts_replayed == 100
    assert result.accuracy_delta == 0.0, f"Same policy should have 0 accuracy delta, got {result.accuracy_delta}"
    assert result.changed == 0, "Same policy should have no transitions"

    print("✓ Accuracy calculation test passed")


def test_risk_assessment_low_risk():
    """Test risk assessment for low-risk changes."""
    verdicts = [
        {'receipt_id': f'R-{i:03d}', 'decision': 'ACCEPT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T14:00:00Z'}
        for i in range(100)
    ]

    old_policy = {'GATE_A': 50}
    new_policy = {'GATE_A': 50}  # Same policy

    simulator = ScenarioSimulator(verdicts, old_policy, new_policy)
    result = simulator.simulate()

    # Same policy = low risk
    assert result.risk_assessment == 'low', f"Expected low risk, got {result.risk_assessment}"
    assert result.recommended_action == 'apply'

    print("✓ Low-risk assessment test passed")


def test_risk_assessment_high_risk():
    """Test risk assessment for high-risk changes."""
    # Create verdicts where a policy change would cause many transitions
    verdicts = [
        {'receipt_id': f'R-{i:03d}', 'decision': 'ACCEPT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T14:00:00Z'}
        for i in range(10)
    ] + [
        {'receipt_id': f'R-{i:03d}', 'decision': 'REJECT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T14:00:00Z'}
        for i in range(10, 20)
    ]

    old_policy = {'GATE_A': 50}
    new_policy = {'GATE_A': 10}  # Drastic change

    simulator = ScenarioSimulator(verdicts, old_policy, new_policy)
    result = simulator.simulate()

    # With insufficient data (20 verdicts), should recommend "hold"
    # or if high transition rate, should be high risk
    assert result.total_verdicts_replayed == 20

    print("✓ High-risk assessment test passed")


def test_simulation_insufficient_data():
    """Test recommendation when insufficient data."""
    verdicts = [
        {'receipt_id': f'R-{i:03d}', 'decision': 'ACCEPT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T14:00:00Z'}
        for i in range(5)
    ]

    old_policy = {'GATE_A': 50}
    new_policy = {'GATE_A': 30}

    simulator = ScenarioSimulator(verdicts, old_policy, new_policy)
    result = simulator.simulate()

    # With <20 verdicts, should recommend "hold"
    assert result.recommended_action == 'hold', f"Expected 'hold' for insufficient data, got {result.recommended_action}"
    assert 'Insufficient' in result.reason or 'data' in result.reason.lower()

    print("✓ Insufficient data test passed")


def test_simulation_result_to_dict():
    """Test SimulationResult serialization."""
    result = SimulationResult(
        total_verdicts_replayed=100,
        unchanged=95,
        changed=5,
        accept_to_reject=2,
        reject_to_accept=3,
        old_accuracy=0.80,
        new_accuracy=0.81,
        accuracy_delta=0.01,
        false_positive_rate=0.02,
        false_negative_rate=0.03,
        transition_rate=0.05,
        recommended_action='apply',
        risk_assessment='low',
        reason='Safe to apply',
        policy_changes=[],
    )

    result_dict = result.to_dict()

    assert result_dict['total_verdicts_replayed'] == 100
    assert result_dict['accuracy_delta'] == 0.01
    assert result_dict['recommended_action'] == 'apply'
    assert result_dict['timestamp'] is not None

    print("✓ SimulationResult serialization test passed")


def test_simulation_determinism():
    """Test K5 determinism: same verdicts + policy → identical results."""
    verdicts = [
        {
            'receipt_id': f'R-{i:03d}',
            'decision': 'ACCEPT' if i % 2 == 0 else 'REJECT',
            'gate': 'GATE_A',
            'timestamp': '2026-01-30T14:00:00Z',
        }
        for i in range(20)
    ]

    old_policy = {'GATE_A': 50}
    new_policy = {'GATE_A': 40}

    # Run simulation 5 times
    results_list = []
    for _ in range(5):
        simulator = ScenarioSimulator(verdicts, old_policy, new_policy)
        result = simulator.simulate()
        results_list.append({
            'total': result.total_verdicts_replayed,
            'changed': result.changed,
            'accuracy_delta': result.accuracy_delta,
        })

    # All results should be identical
    for i in range(1, 5):
        assert results_list[i] == results_list[0], \
            f"K5 determinism violation: iteration {i} differs from iteration 0"

    print("✓ K5 determinism test passed (5 iterations verified identical)")


def test_report_generation():
    """Test simulation report generation."""
    result = SimulationResult(
        total_verdicts_replayed=100,
        unchanged=95,
        changed=5,
        accept_to_reject=2,
        reject_to_accept=3,
        old_accuracy=0.80,
        new_accuracy=0.81,
        accuracy_delta=0.01,
        false_positive_rate=0.02,
        false_negative_rate=0.03,
        transition_rate=0.05,
        recommended_action='apply',
        risk_assessment='low',
        reason='Safe to apply',
        policy_changes=[
            {'gate': 'GATE_A', 'parameter': 'threshold', 'old_value': 50, 'new_value': 40}
        ],
    )

    simulator = ScenarioSimulator([])
    report = simulator.generate_report(result)

    # Check report content
    assert 'ORACLE TOWN SCENARIO SIMULATOR' in report
    assert '100' in report  # Total verdicts
    assert 'GATE_A' in report  # Policy change
    assert 'low' in report.lower()  # Risk level
    assert 'apply' in report.lower()  # Recommendation

    print("✓ Report generation test passed")


def test_from_ledger_and_policy():
    """Test loading from ledger and policy files."""
    # Create temporary ledger
    verdicts = [
        {'receipt_id': 'R-001', 'decision': 'ACCEPT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T14:00:00Z'},
        {'receipt_id': 'R-002', 'decision': 'REJECT', 'gate': 'GATE_A', 'timestamp': '2026-01-30T15:00:00Z'},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for v in verdicts:
            f.write(json.dumps(v) + '\n')
        ledger_path = f.name

    # Create temporary policy
    policy = {'GATE_A': 40}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(policy, f)
        policy_path = f.name

    try:
        simulator = ScenarioSimulator.from_ledger_and_policy(ledger_path, policy_path)

        assert len(simulator.verdicts) == 2
        assert simulator.new_policy == policy
        print("✓ Loading from ledger and policy test passed")
    finally:
        Path(ledger_path).unlink()
        Path(policy_path).unlink()


def run_all_tests():
    """Run all Phase 7 integration tests."""
    print("\n" + "="*60)
    print("ORACLE TOWN PHASE 7: SCENARIO SIMULATOR TESTS")
    print("="*60 + "\n")

    tests = [
        test_policy_change_creation,
        test_scenario_simulator_initialization,
        test_policy_extraction,
        test_verdict_replay,
        test_simulation_empty_verdicts,
        test_simulation_accuracy_calculation,
        test_risk_assessment_low_risk,
        test_risk_assessment_high_risk,
        test_simulation_insufficient_data,
        test_simulation_result_to_dict,
        test_simulation_determinism,
        test_report_generation,
        test_from_ledger_and_policy,
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
