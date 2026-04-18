#!/usr/bin/env python3
"""Test Suite: Axis 4B (Multi-Castle Federation)"""

import sys
sys.path.insert(0, '/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24')

from conquestmon_gotchi_multi import (
    CastleState, WorldStateMultiCastle, OppositionState, PolicyTable,
    execute_round_multi, issue_magi, compute_structural_margin,
    decide_opposition_posture_multi, verify_determinism, generate_tick_summary,
)


def test_policy_table_determinism():
    """Same castle state → same action every time (100 iterations)."""
    print("\n[TEST 1] Policy Table Determinism")
    state = CastleState(
        territory=2.0, stability=6.0, cohesion=5.5,
        knowledge=3.5, entropy=2.0, debt=0.5,
        opposition=OppositionState(posture="OBSERVE", aggression=1.0, capability=1.0)
    )
    world = WorldStateMultiCastle(castles={"test": state})
    table = PolicyTable("test", "🌹")
    actions = [table.decide_action(state, world, []) for _ in range(100)]
    assert all(a == actions[0] for a in actions), f"Actions vary: {set(actions)}"
    print(f"  ✅ PASS: 100 iterations all returned action {actions[0]}")


def test_multi_castle_round_execution():
    """3 castles execute one round, ledger consistent."""
    print("\n[TEST 2] Multi-Castle Round Execution")
    world = WorldStateMultiCastle(
        castles={
            "a": CastleState(territory=2.0, stability=6.0, entropy=2.0),
            "b": CastleState(territory=1.5, stability=5.5, entropy=2.2),
            "c": CastleState(territory=1.8, stability=5.0, entropy=2.5),
        },
        faction_allegiances={"a": "🌹", "b": "🌹", "c": "✝️"}
    )
    initial_tick = world.tick
    execute_round_multi(world)
    assert world.tick == initial_tick + 1
    entries = world.ledger_entries_for_tick(initial_tick)
    assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"
    castle_ids = {e['source_castle'] for e in entries}
    assert castle_ids == {"a", "b", "c"}
    print(f"  ✅ PASS: 3 castles executed, 3 ledger entries created")


def test_determinism_k5():
    """K5 compliance: same seed + same policies → identical outcome."""
    print("\n[TEST 3] K5 Determinism Verification")
    def create_world():
        return WorldStateMultiCastle(
            castles={
                "simperfidelis": CastleState(territory=2.0, stability=6.0, cohesion=5.5, knowledge=3.5, entropy=2.0, debt=0.5),
                "avalon": CastleState(territory=1.5, stability=5.5, cohesion=6.0, knowledge=4.0, entropy=1.8),
            },
            faction_allegiances={"simperfidelis": "🌹", "avalon": "🌹"}
        )
    world1 = create_world()
    world2 = create_world()
    for _ in range(10):
        execute_round_multi(world1)
        execute_round_multi(world2)
    is_deterministic, msg = verify_determinism(world1, world2)
    assert is_deterministic, f"Determinism failed: {msg}"
    print(f"  ✅ PASS: K5 compliance verified")
    print(f"    Both runs: {world1.tick} ticks, {len(world1.ledger)} ledger entries")


def test_policy_precedence():
    """Policy rules follow correct precedence."""
    print("\n[TEST 4] Policy Precedence")
    world = WorldStateMultiCastle(castles={"test": CastleState()})
    table = PolicyTable("test", "🌹")

    # Test: Opposition ATTACK rule (highest priority after emergency)
    state_attack = CastleState(
        opposition=OppositionState(posture="ATTACK", aggression=4.0, capability=4.0)
    )
    action = table.decide_action(state_attack, world, [])
    assert action == 2, f"Opposition ATTACK rule: expected 2 (FORTIFY), got {action}"

    # Test: Debt rule (high debt)
    state_debt = CastleState(
        debt=6.0,
        opposition=OppositionState(posture="OBSERVE", aggression=1.0, capability=1.0)
    )
    action = table.decide_action(state_debt, world, [])
    assert action == 5, f"Debt rule: expected 5 (REST), got {action}"

    # Test: Fatigue rule
    state_fatigue = CastleState(
        fatigue=9.0,
        opposition=OppositionState(posture="OBSERVE", aggression=1.0, capability=1.0)
    )
    action = table.decide_action(state_fatigue, world, [])
    assert action == 5, f"Fatigue rule: expected 5 (REST), got {action}"

    print(f"  ✅ PASS: All precedence rules verified")


def test_magi_issuance():
    """MAGI message issued, appears in ledger."""
    print("\n[TEST 5] MAGI Issuance")
    world = WorldStateMultiCastle(
        castles={"a": CastleState(), "b": CastleState()},
        faction_allegiances={"a": "🌹", "b": "🌹"}
    )
    initial_entries = len(world.ledger)
    success = issue_magi("a", "b", world, faction="🌹", operator="🜄", state="⚰")
    assert success, "MAGI issuance failed"
    assert len(world.ledger) == initial_entries + 1, "Ledger entry not added"
    magi_entry = world.ledger[-1]
    assert magi_entry['source_castle'] == 'a'
    assert magi_entry['target_castle'] == 'b'
    assert magi_entry['faction'] == "🌹"
    assert 'proof' in magi_entry
    assert len(magi_entry['proof']) == 4
    print(f"  ✅ PASS: MAGI issued, proof={magi_entry['proof']}")


if __name__ == "__main__":
    print("=" * 80)
    print("CONQUEST Axis 4B Test Suite")
    print("=" * 80)

    tests = [
        ("Policy Table Determinism", test_policy_table_determinism),
        ("Multi-Castle Round Execution", test_multi_castle_round_execution),
        ("K5 Determinism", test_determinism_k5),
        ("Policy Precedence", test_policy_precedence),
        ("MAGI Issuance", test_magi_issuance),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    if failed == 0:
        print("\n✅ ALL TESTS PASSED (Axis 4B ready for deployment)")
    else:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)
