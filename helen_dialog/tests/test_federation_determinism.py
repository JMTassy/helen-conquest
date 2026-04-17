#!/usr/bin/env python3
"""
helen_dialog/tests/test_federation_determinism.py

Federation determinism tests (root venv, Python 3.9.6).

FED-1  Same scenario JSON → same tip_hash on independent runs.
FED-2  Different seeds produce different tip hashes.
FED-3  GOSSIP_MSG_V1 absolute bans enforce raw-dialogue exclusion.
FED-4  Canonical JSON is order-stable (sort_keys).
FED-5  Round seed is deterministic from (base_seed, round_id, prev_hash).

These tests prove the federation layer satisfies the determinism requirement:
  "simulate --scenario X produces identical receipt hashes under replay."
"""

import sys
import os
import json

# Path to the oracle_town directory
REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, REPO_ROOT)

from oracle_town.federation.fed_sim_minimal_v1 import (
    FederationSimMinimalV1,
    GossipMsgV1,
    canonical_json,
    sha256_hex,
    derive_round_seed,
    ABSOLUTE_BANS,
)

SCENARIO_PATH = os.path.join(
    REPO_ROOT, "oracle_town", "federation", "scenarios", "baseline_round.json"
)


def load_baseline_scenario():
    with open(SCENARIO_PATH, "r") as f:
        return json.load(f)


# ── FED-1: Same scenario → same tip_hash ─────────────────────────────────────

def test_fed1_replay_stability():
    """
    FED-1: Run the baseline scenario twice. Both runs must produce identical tip_hash.

    This is the core receipt requirement: same inputs → same sovereign output.
    """
    scenario = load_baseline_scenario()

    h1 = FederationSimMinimalV1().run(scenario)
    h2 = FederationSimMinimalV1().run(scenario)

    assert h1 == h2, (
        f"FED-1 FAIL: tip_hash differs between runs.\n"
        f"  Run 1: {h1}\n"
        f"  Run 2: {h2}\n"
        "Federation replay is not deterministic. Constitutional violation."
    )
    # Sanity: hash is a 64-char hex string
    assert len(h1) == 64 and all(c in "0123456789abcdef" for c in h1)


def test_fed1_tip_hash_is_pinned():
    """
    FED-1b: The baseline tip_hash must not change unless the scenario or sim logic changes.

    If this test fails: recompute and update EXPECTED_TIP_HASH, then document why.
    """
    scenario = load_baseline_scenario()
    tip = FederationSimMinimalV1().run(scenario)

    # Pin was computed on first run. To update: run the sim, copy the output here.
    EXPECTED_TIP_HASH = tip  # Self-sealing: fails if the value changes on next run.

    # The real enforcement is the pinned constant below. Update it explicitly when
    # you change the scenario or sim logic.
    PINNED = "ab607afe4e51848070e6369a785576949025eb4ceccf6a7e6b45cb685bf1c4bc"

    if PINNED != "auto":
        assert tip == PINNED, (
            f"FED-1b FAIL: tip_hash changed.\n"
            f"  Expected (pinned): {PINNED}\n"
            f"  Actual:            {tip}\n"
            "Update PINNED only after reviewing the scenario diff."
        )
    # If PINNED == "auto", the test passes but logs the hash for pinning.
    print(f"\n[FED-1b] Current tip_hash (pin this): {tip}")


# ── FED-2: Different seeds → different hashes ─────────────────────────────────

def test_fed2_different_seeds_diverge():
    """
    FED-2: Changing the seed must produce a different tip_hash.

    Proves the simulation is actually sensitive to the seed (not trivially constant).
    """
    scenario = load_baseline_scenario()
    h_seed42 = FederationSimMinimalV1().run(scenario)

    scenario_alt = dict(scenario, seed=99)
    h_seed99 = FederationSimMinimalV1().run(scenario_alt)

    assert h_seed42 != h_seed99, (
        "FED-2 FAIL: different seeds produced identical tip_hash. "
        "Simulation is not seed-sensitive."
    )


# ── FED-3: Absolute ban enforcement ───────────────────────────────────────────

def test_fed3_raw_dialogue_banned_in_gossip():
    """
    FED-3: GossipMsgV1 must reject messages containing banned field names.

    Banned: raw_dialogue, prompt_text, claim_spans, user_identifier.
    This enforces the D→E→L separation: dialogue cannot be laundered into
    the federation layer as a direct gossip payload.
    """
    import pytest

    for banned_key in ABSOLUTE_BANS:
        # Attempt to create a GossipMsgV1 with a banned key in pattern_vector
        with pytest.raises(ValueError, match="GOSSIP_MSG_V1 violation"):
            GossipMsgV1(
                peer_id="TOWN_A",
                round_id=0,
                pattern_vector={banned_key: 0.5},
                stats={"messages_sent": 1},
            )


def test_fed3_aggregate_vectors_allowed():
    """
    FED-3b: Non-banned aggregate fields pass without error.
    """
    msg = GossipMsgV1(
        peer_id="TOWN_A",
        round_id=0,
        pattern_vector={"c": 0.1, "r": 0.2, "coherence": 0.75},
        stats={"messages_sent": 3, "rounds_participated": 1},
        prev_round_hash="0" * 64,
    )
    # No exception → passes ban check
    assert msg.peer_id == "TOWN_A"
    assert len(msg.msg_hash()) == 64


# ── FED-4: Canonical JSON stability ───────────────────────────────────────────

def test_fed4_canonical_json_is_order_stable():
    """
    FED-4: canonical_json must produce identical output regardless of dict insertion order.

    This guarantees that the round_hash is not sensitive to Python dict ordering.
    """
    obj_a = {"z": 1, "a": 2, "m": 3}
    obj_b = {"a": 2, "m": 3, "z": 1}
    obj_c = {"m": 3, "z": 1, "a": 2}

    canon_a = canonical_json(obj_a)
    canon_b = canonical_json(obj_b)
    canon_c = canonical_json(obj_c)

    assert canon_a == canon_b == canon_c, (
        "FED-4 FAIL: canonical_json is not order-stable. "
        f"a={canon_a!r} b={canon_b!r} c={canon_c!r}"
    )


# ── FED-5: Round seed derivation is deterministic ─────────────────────────────

def test_fed5_round_seed_is_deterministic():
    """
    FED-5: derive_round_seed(base, round_id, prev_hash) must always produce
    the same integer for the same inputs.

    This prevents non-determinism from propagating between rounds.
    """
    s1 = derive_round_seed(42, 0, "0" * 64)
    s2 = derive_round_seed(42, 0, "0" * 64)
    s3 = derive_round_seed(42, 1, "0" * 64)
    s4 = derive_round_seed(99, 0, "0" * 64)

    assert s1 == s2, "FED-5 FAIL: same inputs produced different seeds."
    assert s1 != s3, "FED-5 FAIL: different round_id produced same seed."
    assert s1 != s4, "FED-5 FAIL: different base_seed produced same seed."


if __name__ == "__main__":
    test_fed1_replay_stability()
    test_fed1_tip_hash_is_pinned()
    test_fed2_different_seeds_diverge()
    test_fed3_raw_dialogue_banned_in_gossip()
    test_fed3_aggregate_vectors_allowed()
    test_fed4_canonical_json_is_order_stable()
    test_fed5_round_seed_is_deterministic()
    print("\n✅ All federation determinism tests passed")
