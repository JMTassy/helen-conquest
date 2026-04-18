# ci/run_test_vault.py
import json
import os
import sys

# Add parent directory to path for oracle imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from oracle.engine import run_oracle
from oracle.replay import replay_equivalence

SCEN_DIR = os.path.join(os.path.dirname(__file__), "..", "test_vault", "scenarios")

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def assert_equal(actual, expected, msg):
    if actual != expected:
        raise AssertionError(f"{msg}\n  actual={actual}\n  expected={expected}")

def main():
    files = sorted([f for f in os.listdir(SCEN_DIR) if f.endswith(".json")])
    manifests = {}

    print("=" * 60)
    print("ORACLE SUPERTEAM - Test Vault Runner")
    print("=" * 60)

    for fn in files:
        p = os.path.join(SCEN_DIR, fn)
        scenario = load(p)

        sid = scenario["scenario_id"]
        print(f"\n[{sid}] {scenario['description']}")

        if sid == "S-08":
            # Two variants, must replay-identical
            for var in scenario["variants"]:
                payload = {
                    "scenario_id": f"S-08::{var['variant_id']}",
                    "claim": scenario["claim"],
                    "evidence": scenario["evidence"],
                    "votes": var["votes"],
                }
                m = run_oracle(payload)
                manifests[payload["scenario_id"]] = m

            a = manifests["S-08::A_ordered"]
            b = manifests["S-08::B_shuffled"]
            eq = replay_equivalence(a, b)

            if not (eq["inputs_hash_equal"] and eq["outputs_hash_equal"]):
                raise AssertionError(f"S-08 replay failed:\n{json.dumps(eq, indent=2)}")

            # Also check expected decision
            exp = scenario["expected"]["decision"]["final"]
            assert_equal(a["decision"]["final"], exp, "S-08A decision mismatch")
            assert_equal(b["decision"]["final"], exp, "S-08B decision mismatch")

            print(f"  ✓ Replay determinism verified")
            print(f"  ✓ Decision: {a['decision']['final']}")
            print(f"  ✓ Ship: {a['decision']['ship_permitted']}")

            continue

        payload = {
            "scenario_id": sid,
            "claim": scenario["claim"],
            "evidence": scenario.get("evidence", []),
            "votes": scenario.get("votes", []),
        }
        m = run_oracle(payload)
        manifests[sid] = m

        exp_dec = scenario["expected"]["decision"]["final"]
        assert_equal(m["decision"]["final"], exp_dec, f"{sid} decision mismatch")

        # Kill-switch expectation
        exp_kill = scenario["expected"]["derived"]["kill_switch_triggered"]
        assert_equal(m["derived"]["kill_switch_triggered"], exp_kill, f"{sid} kill_switch_triggered mismatch")

        # Reason codes should include expected ones (subset check)
        exp_reasons = set(scenario["expected"]["decision"].get("reason_codes", []))
        act_reasons = set(m["decision"].get("reason_codes", []))
        if not exp_reasons.issubset(act_reasons):
            raise AssertionError(f"{sid} reason_codes mismatch\n  actual={act_reasons}\n  expected_subset={exp_reasons}")

        print(f"  ✓ Decision: {m['decision']['final']}")
        print(f"  ✓ Ship: {m['decision']['ship_permitted']}")
        print(f"  ✓ Kill switch: {m['derived']['kill_switch_triggered']}")
        print(f"  ✓ Rule kill: {m['derived']['rule_kill_triggered']}")
        if m['derived']['obligations_open']:
            print(f"  ✓ Open obligations: {len(m['derived']['obligations_open'])}")

    print("\n" + "=" * 60)
    print("ALL TEST VAULT SCENARIOS PASSED ✓")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
