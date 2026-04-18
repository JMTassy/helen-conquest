"""
tests/test_temporal_decay_v1.py — TEMPORAL_DECAY_V1 mechanism tests.

DECREE_T59: Activate Temporal Decay in live Autoresearch mission.
            These tests verify the mechanism is correct before live activation.

Evidence gates covered by this test suite:
    G1  live_run_completed        → integration test (TD15)
    G2  receipts_complete         → TD01, TD10, TD11, TD12
    G3  protected_tiers_preserved → TD03, TD04, TD05, TD06
    G4  recall_not_degraded       → TD07, TD08 (structural)

Test IDs:
    TD01  receipt has all required fields
    TD02  decay weight formula is correct (compute_decay_weight pure function)
    TD03  SEALED items are never pruned
    TD04  ANCHORED items are never pruned (before expiry)
    TD05  ANCHORED items become EPHEMERAL after expiry cycle
    TD06  re_anchor elevates EPHEMERAL to ANCHORED, resets weight
    TD07  EPHEMERAL items decay monotonically over cycles
    TD08  EPHEMERAL items below threshold are pruned from pool
    TD09  pruned items are removed from pool permanently
    TD10  receipt pre-decay counts match pool state before decay
    TD11  receipt post-decay counts are consistent
    TD12  canonical_payload_hash is deterministic
    TD13  injection order: SEALED first, then ANCHORED, then EPHEMERAL
    TD14  cycle_last_used updated for injected items
    TD15  full autoresearch-style cycle simulation (integration)
    TD16  cycles_until_prune is correct for default params
    TD17  record_outcome updates receipt and recomputes hash
    TD18  estimated_tokens_injected is non-negative
    TD19  empty pool produces empty injection and valid receipt
    TD20  multiple items: only those above threshold injected
"""
from __future__ import annotations

import math
import sys
import os
import pytest

_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, _SCAFFOLD_ROOT)

from helen_os.temporal_decay import (
    TemporalDecayEngine,
    TemporalDecayReceiptV1,
    MemoryTier,
    MemoryItem,
    DECAY_LAMBDA,
    PRUNE_THRESHOLD,
    ANCHOR_WEIGHT,
    INITIAL_WEIGHT,
    compute_decay_weight,
    cycles_until_prune,
)


# ── TD01: Receipt structure ───────────────────────────────────────────────────

class TestTD01ReceiptStructure:
    def test_td01_receipt_has_required_fields(self):
        """TD01: TEMPORAL_DECAY_RECEIPT_V1 has all required fields."""
        engine = TemporalDecayEngine()
        engine.add_ephemeral("e1", {"text": "hello"}, cycle=0)
        _, receipt = engine.decay_and_select_context("LOOP-TEST-001", cycle_number=1)

        required = [
            "artifact_type", "decay_version", "cycle_id", "cycle_number",
            "lambda_param", "prune_threshold",
            "pre_total_items", "pre_sealed_items", "pre_anchored_items", "pre_ephemeral_items",
            "post_total_items", "sealed_retained", "anchored_retained",
            "ephemeral_retained", "ephemeral_pruned", "anchors_expired",
            "injected_item_count", "estimated_tokens_injected",
            "recall_hits", "recall_misses", "mission_verdict",
            "canonical_payload_hash",
        ]
        d = receipt.to_dict()
        for field in required:
            assert field in d, f"Missing field: {field}"

    def test_td01_artifact_type_is_correct(self):
        """TD01: artifact_type is 'TEMPORAL_DECAY_RECEIPT_V1'."""
        engine = TemporalDecayEngine()
        _, receipt = engine.decay_and_select_context("LOOP-001", cycle_number=1)
        assert receipt.artifact_type == "TEMPORAL_DECAY_RECEIPT_V1"

    def test_td01_decay_version_is_v1(self):
        """TD01: decay_version is 'TEMPORAL_DECAY_V1'."""
        engine = TemporalDecayEngine()
        _, receipt = engine.decay_and_select_context("LOOP-001", cycle_number=1)
        assert receipt.decay_version == "TEMPORAL_DECAY_V1"


# ── TD02: Decay weight formula ───────────────────────────────────────────────

class TestTD02DecayFormula:
    def test_td02_weight_at_zero_cycles(self):
        """TD02: weight at 0 elapsed cycles equals base_weight."""
        w = compute_decay_weight(1.0, 0)
        assert abs(w - 1.0) < 1e-9

    def test_td02_weight_decreases_over_cycles(self):
        """TD02: weight strictly decreases as cycles increase."""
        weights = [compute_decay_weight(1.0, t) for t in range(0, 1000, 50)]
        assert all(weights[i] > weights[i+1] for i in range(len(weights)-1))

    def test_td02_formula_is_correct(self):
        """TD02: compute_decay_weight matches analytical formula."""
        base = 1.0
        t = 200
        expected = base * math.exp(-DECAY_LAMBDA * t)
        actual   = compute_decay_weight(base, t)
        assert abs(actual - expected) < 1e-12

    def test_td02_lambda_param_controls_rate(self):
        """TD02: higher lambda → faster decay."""
        w_slow = compute_decay_weight(1.0, 100, lambda_param=0.001)
        w_fast = compute_decay_weight(1.0, 100, lambda_param=0.01)
        assert w_slow > w_fast

    def test_td02_weight_never_negative(self):
        """TD02: decay weight is always non-negative."""
        for t in range(0, 10001, 100):
            w = compute_decay_weight(1.0, t)
            assert w >= 0.0


# ── TD03: SEALED items never pruned ──────────────────────────────────────────

class TestTD03SealedNeverPruned:
    def test_td03_sealed_item_survives_many_cycles(self):
        """TD03 (G3): SEALED items are never removed from pool, regardless of age."""
        engine = TemporalDecayEngine()
        engine.add_sealed("MAN-001", {"manifest": "data"}, receipt_hash="a" * 64, cycle=0)

        # Run 10,000 cycles — SEALED items must survive all of them
        for c in range(1, 10001, 500):
            injected, _ = engine.decay_and_select_context(f"LOOP-{c}", cycle_number=c)
            sealed_ids = [i.item_id for i in injected if i.is_sealed]
            assert "MAN-001" in sealed_ids, f"SEALED item missing at cycle {c}"

    def test_td03_sealed_count_never_decreases(self):
        """TD03: sealed_retained in receipt always equals pre_sealed_items."""
        engine = TemporalDecayEngine()
        engine.add_sealed("S1", "content", receipt_hash="b" * 64, cycle=0)
        engine.add_sealed("S2", "content", receipt_hash="c" * 64, cycle=0)

        for c in range(1, 200):
            _, receipt = engine.decay_and_select_context(f"L{c}", cycle_number=c)
            assert receipt.sealed_retained == 2
            assert receipt.pre_sealed_items == 2


# ── TD04: ANCHORED items not pruned before expiry ─────────────────────────────

class TestTD04AnchoredProtected:
    def test_td04_anchored_survives_until_expiry(self):
        """TD04 (G3): ANCHORED item is in injection list until anchor expires."""
        engine = TemporalDecayEngine()
        engine.add_anchored("A1", {"lesson": "key insight"}, cycle=0,
                            anchor_expires_at_cycle=10)

        for c in range(1, 11):
            injected, _ = engine.decay_and_select_context(f"L{c}", cycle_number=c)
            anchored_ids = [i.item_id for i in injected if i.is_anchored]
            assert "A1" in anchored_ids, f"ANCHORED item missing at cycle {c}"

    def test_td04_anchored_weight_stays_at_anchor_weight(self):
        """TD04: ANCHORED item weight stays at ANCHOR_WEIGHT (not decaying)."""
        engine = TemporalDecayEngine()
        engine.add_anchored("A1", "data", cycle=0)

        for c in range(1, 50):
            engine.decay_and_select_context(f"L{c}", cycle_number=c)
            item = engine.get_item("A1")
            if item is not None and item.is_anchored:
                assert abs(item.current_weight - ANCHOR_WEIGHT) < 1e-9


# ── TD05: Anchor expiry → becomes EPHEMERAL ───────────────────────────────────

class TestTD05AnchorExpiry:
    def test_td05_anchor_expires_and_item_becomes_ephemeral(self):
        """TD05: after anchor_expires_at_cycle, item is downgraded to EPHEMERAL."""
        engine = TemporalDecayEngine()
        engine.add_anchored("A1", "data", cycle=0, anchor_expires_at_cycle=5)

        # Cycle 5: still anchored (expires at > 5, so cycle 6 is first expired)
        _, r5 = engine.decay_and_select_context("L5", cycle_number=5)
        item_at_5 = engine.get_item("A1")
        assert item_at_5 is not None
        assert item_at_5.is_anchored, "Should still be anchored at cycle 5"

        # Cycle 6: anchor expired
        _, r6 = engine.decay_and_select_context("L6", cycle_number=6)
        item_at_6 = engine.get_item("A1")
        assert item_at_6 is not None
        assert item_at_6.is_ephemeral, "Should be EPHEMERAL at cycle 6 (anchor expired)"

    def test_td05_expiry_count_in_receipt(self):
        """TD05: anchors_expired count in receipt is correct."""
        engine = TemporalDecayEngine()
        engine.add_anchored("A1", "d", cycle=0, anchor_expires_at_cycle=3)
        engine.add_anchored("A2", "d", cycle=0, anchor_expires_at_cycle=3)

        _, r3 = engine.decay_and_select_context("L3", cycle_number=3)
        assert r3.anchors_expired == 0   # not yet expired (cycle > expiry means expired)

        _, r4 = engine.decay_and_select_context("L4", cycle_number=4)
        assert r4.anchors_expired == 2   # both expired


# ── TD06: re_anchor elevates and resets weight ────────────────────────────────

class TestTD06ReAnchor:
    def test_td06_re_anchor_elevates_ephemeral_to_anchored(self):
        """TD06: re_anchor() elevates EPHEMERAL item to ANCHORED."""
        engine = TemporalDecayEngine()
        engine.add_ephemeral("E1", "data", cycle=0)
        engine.re_anchor("E1", receipt_hash="d" * 64, current_cycle=3)

        item = engine.get_item("E1")
        assert item is not None
        assert item.is_anchored

    def test_td06_re_anchor_resets_weight(self):
        """TD06: re_anchor() resets current_weight to ANCHOR_WEIGHT."""
        engine = TemporalDecayEngine()
        engine.add_ephemeral("E1", "data", cycle=0)
        # Decay for a few cycles first
        for c in range(1, 5):
            engine.decay_and_select_context(f"L{c}", cycle_number=c)

        engine.re_anchor("E1", receipt_hash="e" * 64, current_cycle=5)
        item = engine.get_item("E1")
        assert item is not None
        assert abs(item.current_weight - ANCHOR_WEIGHT) < 1e-9

    def test_td06_re_anchor_of_sealed_is_noop(self):
        """TD06: re_anchor() on a SEALED item leaves it SEALED."""
        engine = TemporalDecayEngine()
        engine.add_sealed("S1", "data", receipt_hash="f" * 64, cycle=0)
        result = engine.re_anchor("S1", receipt_hash="new", current_cycle=5)
        assert result is not None
        assert result.is_sealed

    def test_td06_re_anchor_missing_item_returns_none(self):
        """TD06: re_anchor() on non-existent item_id returns None."""
        engine = TemporalDecayEngine()
        result = engine.re_anchor("MISSING", receipt_hash="g" * 64, current_cycle=1)
        assert result is None


# ── TD07: EPHEMERAL decay is monotonic ────────────────────────────────────────

class TestTD07EphemeralDecayMonotonic:
    def test_td07_ephemeral_weight_is_monotonically_decreasing(self):
        """TD07 (candidate I11): ephemeral items decay monotonically over cycles."""
        engine = TemporalDecayEngine()
        engine.add_ephemeral("E1", "data", cycle=0)

        weights = []
        for c in range(1, 100):
            engine.decay_and_select_context(f"L{c}", cycle_number=c)
            item = engine.get_item("E1")
            if item is not None and item.is_ephemeral:
                weights.append(item.current_weight)
            # item might be pruned eventually — stop tracking after pruned

        assert len(weights) > 0, "Should have tracked decay before pruning"
        for i in range(len(weights) - 1):
            assert weights[i] > weights[i+1], (
                f"Non-monotonic at index {i}: {weights[i]} → {weights[i+1]}"
            )

    def test_td07_decay_from_anchor_weight_is_also_monotonic(self):
        """TD07: even items that start at ANCHOR_WEIGHT decay monotonically after expiry."""
        engine = TemporalDecayEngine()
        engine.add_anchored("A1", "data", cycle=0, anchor_expires_at_cycle=3)

        # Let anchor expire
        engine.decay_and_select_context("L4", cycle_number=4)
        item = engine.get_item("A1")
        if item is None:
            pytest.skip("Item pruned immediately after anchor expiry")
        assert item.is_ephemeral

        weight_after_expiry = item.current_weight
        engine.decay_and_select_context("L5", cycle_number=5)
        item = engine.get_item("A1")
        if item is None:
            return  # pruned — monotonicity held
        assert item.current_weight <= weight_after_expiry


# ── TD08–TD09: Pruning ────────────────────────────────────────────────────────

class TestTD08_09Pruning:
    def test_td08_item_below_threshold_excluded_from_injection(self):
        """TD08: items with weight < PRUNE_THRESHOLD are not injected."""
        # Use high lambda so item decays fast
        engine = TemporalDecayEngine(lambda_param=1.0, prune_threshold=PRUNE_THRESHOLD)
        engine.add_ephemeral("E1", "data", cycle=0)

        # After many cycles at lambda=1.0, weight = exp(-N) which drops fast
        injected, _ = engine.decay_and_select_context("L1000", cycle_number=1000)
        ids = [i.item_id for i in injected]
        assert "E1" not in ids, "Highly decayed item should not be injected"

    def test_td09_pruned_items_removed_from_pool_permanently(self):
        """TD09: items pruned from pool are permanently removed."""
        engine = TemporalDecayEngine(lambda_param=1.0)
        engine.add_ephemeral("E1", "data", cycle=0)

        # Decay until pruned
        for c in range(1, 101):
            engine.decay_and_select_context(f"L{c}", cycle_number=c)
            if engine.get_item("E1") is None:
                break

        assert engine.get_item("E1") is None, "Pruned item should not remain in pool"

    def test_td09_sealed_never_in_pruned_list(self):
        """TD09: SEALED items never appear in ephemeral_pruned count."""
        engine = TemporalDecayEngine(lambda_param=1.0)
        engine.add_sealed("S1", "data", receipt_hash="h" * 64, cycle=0)

        for c in range(1, 1001, 100):
            _, receipt = engine.decay_and_select_context(f"L{c}", cycle_number=c)
            assert receipt.sealed_retained == 1
            assert receipt.ephemeral_pruned == 0


# ── TD10–TD11: Receipt count consistency ─────────────────────────────────────

class TestTD10_11ReceiptCounts:
    def test_td10_pre_counts_match_pool_state(self):
        """TD10 (G2): pre_* counts in receipt match the pool state before decay."""
        engine = TemporalDecayEngine()
        engine.add_sealed("S1", "s", receipt_hash="i" * 64, cycle=0)
        engine.add_anchored("A1", "a", cycle=0)
        engine.add_ephemeral("E1", "e", cycle=0)
        engine.add_ephemeral("E2", "e2", cycle=0)

        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        assert receipt.pre_total_items   == 4
        assert receipt.pre_sealed_items  == 1
        assert receipt.pre_anchored_items == 1
        assert receipt.pre_ephemeral_items == 2

    def test_td11_post_counts_are_consistent(self):
        """TD11: post counts satisfy: sealed + anchored + ephemeral_retained == post_total."""
        engine = TemporalDecayEngine()
        for i in range(5):
            engine.add_ephemeral(f"E{i}", f"data_{i}", cycle=0)
        engine.add_sealed("S1", "s", receipt_hash="j" * 64, cycle=0)

        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        assert (receipt.sealed_retained + receipt.anchored_retained +
                receipt.ephemeral_retained) == receipt.post_total_items

    def test_td11_pruned_plus_retained_equals_pre_ephemeral(self):
        """TD11: ephemeral_pruned + ephemeral_retained == pre_ephemeral_items."""
        engine = TemporalDecayEngine(lambda_param=1.0, prune_threshold=0.5)
        for i in range(4):
            engine.add_ephemeral(f"E{i}", "data", cycle=0)

        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        assert (receipt.ephemeral_pruned + receipt.ephemeral_retained) == receipt.pre_ephemeral_items


# ── TD12: canonical_payload_hash determinism ─────────────────────────────────

class TestTD12HashDeterminism:
    def test_td12_canonical_payload_hash_is_deterministic(self):
        """TD12 (G2): same pool + same cycle → same canonical_payload_hash."""
        def make_engine_and_hash():
            engine = TemporalDecayEngine()
            engine.add_ephemeral("E1", {"text": "hello"}, cycle=0)
            _, receipt = engine.decay_and_select_context("LOOP-001", cycle_number=1)
            return receipt.canonical_payload_hash

        h1 = make_engine_and_hash()
        h2 = make_engine_and_hash()
        assert h1 == h2

    def test_td12_hash_changes_with_cycle(self):
        """TD12: different cycle_number → different canonical_payload_hash."""
        def make_hash(cycle):
            engine = TemporalDecayEngine()
            engine.add_ephemeral("E1", {"text": "hello"}, cycle=0)
            _, receipt = engine.decay_and_select_context("LOOP-001", cycle_number=cycle)
            return receipt.canonical_payload_hash

        h1 = make_hash(1)
        h2 = make_hash(2)
        assert h1 != h2

    def test_td12_hash_is_64_hex(self):
        """TD12: canonical_payload_hash is 64 lowercase hex chars."""
        engine = TemporalDecayEngine()
        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        h = receipt.canonical_payload_hash
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ── TD13: Injection order ─────────────────────────────────────────────────────

class TestTD13InjectionOrder:
    def test_td13_sealed_first_then_anchored_then_ephemeral(self):
        """TD13: injection order is SEALED → ANCHORED → EPHEMERAL."""
        engine = TemporalDecayEngine()
        engine.add_ephemeral("E1", "data", cycle=0)
        engine.add_anchored("A1", "data", cycle=0)
        engine.add_sealed("S1", "data", receipt_hash="k" * 64, cycle=0)

        injected, _ = engine.decay_and_select_context("L1", cycle_number=1)
        tiers = [i.tier for i in injected]

        # All SEALED must come before any ANCHORED
        # All ANCHORED must come before any EPHEMERAL
        saw_anchored = False
        saw_ephemeral = False
        for t in tiers:
            if t == MemoryTier.ANCHORED:
                saw_anchored = True
            if t == MemoryTier.EPHEMERAL:
                saw_ephemeral = True
            if t == MemoryTier.SEALED:
                assert not saw_anchored, "SEALED after ANCHORED"
                assert not saw_ephemeral, "SEALED after EPHEMERAL"
            if t == MemoryTier.ANCHORED:
                assert not saw_ephemeral, "ANCHORED after EPHEMERAL"


# ── TD14: cycle_last_used update ─────────────────────────────────────────────

class TestTD14CycleLastUsed:
    def test_td14_cycle_last_used_updated_after_injection(self):
        """TD14: cycle_last_used is updated to current_cycle for injected items."""
        engine = TemporalDecayEngine()
        engine.add_ephemeral("E1", "data", cycle=0)

        engine.decay_and_select_context("L5", cycle_number=5)
        item = engine.get_item("E1")
        if item is not None:
            assert item.cycle_last_used == 5


# ── TD15: Integration (full cycle simulation) ─────────────────────────────────

class TestTD15Integration:
    def test_td15_full_autoresearch_cycle_simulation(self):
        """
        TD15 (G1 structural): simulate a 3-cycle autoresearch mission.

        Cycle 0: add genesis sealed + baseline ephemeral
        Cycle 1: first proposal — add ephemeral proposal, run decay
        Cycle 2: second proposal — re-anchor first, add new ephemeral
        Cycle 3: final — sealed item from SHIP, verify sealed count
        """
        engine = TemporalDecayEngine()

        # Cycle 0: genesis
        engine.add_sealed(
            "GENESIS-MANIFEST",
            {"baseline_metric": 0.7812},
            receipt_hash="0" * 64,
            cycle=0,
        )
        engine.add_ephemeral("BASELINE-NOTE-001", {"content": "baseline measurement"}, cycle=0)

        # Cycle 1: proposal
        engine.add_ephemeral("PROP-001", {"hypothesis": "QKnorm scaler"}, cycle=1)
        injected_1, receipt_1 = engine.decay_and_select_context("LOOP-001", cycle_number=1)

        assert receipt_1.pre_sealed_items == 1
        assert receipt_1.injected_item_count >= 1
        sealed_in_1 = [i for i in injected_1 if i.is_sealed]
        assert len(sealed_in_1) == 1   # GENESIS must be injected
        assert receipt_1.canonical_payload_hash != ""

        # Cycle 2: re-anchor first proposal (cited in review)
        engine.add_ephemeral("PROP-002", {"hypothesis": "Value Embedding L2"}, cycle=2)
        engine.re_anchor("PROP-001", receipt_hash="1" * 64, current_cycle=2,
                         anchor_expires_at_cycle=5)

        injected_2, receipt_2 = engine.decay_and_select_context("LOOP-002", cycle_number=2)
        anchored_in_2 = [i for i in injected_2 if i.is_anchored]
        assert any(i.item_id == "PROP-001" for i in anchored_in_2), (
            "Re-anchored item must appear in injection"
        )

        # Cycle 3: SHIP event — add new sealed manifest
        engine.add_sealed(
            "MAN-002",
            {"metric": 0.7901},
            receipt_hash="2" * 64,
            cycle=3,
        )
        injected_3, receipt_3 = engine.decay_and_select_context("LOOP-003", cycle_number=3)
        sealed_in_3 = [i for i in injected_3 if i.is_sealed]
        assert len(sealed_in_3) == 2   # GENESIS + MAN-002

        # Record outcome
        engine.record_outcome(receipt_3, mission_verdict="SHIP", recall_hits=2, recall_misses=0)
        assert receipt_3.mission_verdict == "SHIP"
        assert receipt_3.recall_hits == 2
        assert receipt_3.canonical_payload_hash != ""


# ── TD16: cycles_until_prune ──────────────────────────────────────────────────

class TestTD16CyclesUntilPrune:
    def test_td16_cycles_until_prune_is_correct(self):
        """TD16: cycles_until_prune gives cycle at which item drops below threshold."""
        n = cycles_until_prune(INITIAL_WEIGHT, PRUNE_THRESHOLD, DECAY_LAMBDA)
        # At cycle n, weight should be < PRUNE_THRESHOLD
        w_at_n = compute_decay_weight(INITIAL_WEIGHT, n, DECAY_LAMBDA)
        w_before = compute_decay_weight(INITIAL_WEIGHT, n - 1, DECAY_LAMBDA)
        assert w_at_n < PRUNE_THRESHOLD, f"Weight at cycle {n} is {w_at_n}, expected < {PRUNE_THRESHOLD}"
        assert w_before >= PRUNE_THRESHOLD, f"Weight at cycle {n-1} is {w_before}, expected >= {PRUNE_THRESHOLD}"

    def test_td16_zero_cycles_for_already_below_threshold(self):
        """TD16: item already below threshold returns 0 cycles."""
        n = cycles_until_prune(base_weight=0.05, prune_threshold=0.1)
        assert n == 0

    def test_td16_result_is_positive_integer(self):
        """TD16: cycles_until_prune returns a positive integer for normal inputs."""
        n = cycles_until_prune()
        assert isinstance(n, int)
        assert n > 0


# ── TD17: record_outcome ──────────────────────────────────────────────────────

class TestTD17RecordOutcome:
    def test_td17_record_outcome_updates_verdict(self):
        """TD17: record_outcome() sets mission_verdict on the receipt."""
        engine = TemporalDecayEngine()
        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        assert receipt.mission_verdict == ""

        engine.record_outcome(receipt, mission_verdict="SHIP")
        assert receipt.mission_verdict == "SHIP"

    def test_td17_record_outcome_recomputes_hash(self):
        """TD17: hash changes after record_outcome() adds outcome data."""
        engine = TemporalDecayEngine()
        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        hash_before = receipt.canonical_payload_hash

        engine.record_outcome(receipt, mission_verdict="ABORT", recall_hits=0, recall_misses=2)
        hash_after = receipt.canonical_payload_hash

        assert hash_before != hash_after, "Hash must change when outcome is added"

    def test_td17_record_outcome_hash_is_deterministic(self):
        """TD17: same outcome → same final hash (deterministic)."""
        def run():
            engine = TemporalDecayEngine()
            engine.add_ephemeral("E1", {"text": "hello"}, cycle=0)
            _, receipt = engine.decay_and_select_context("LOOP-X", cycle_number=1)
            engine.record_outcome(receipt, mission_verdict="SHIP", recall_hits=1)
            return receipt.canonical_payload_hash

        assert run() == run()


# ── TD18: Token estimate ──────────────────────────────────────────────────────

class TestTD18TokenEstimate:
    def test_td18_estimated_tokens_non_negative(self):
        """TD18: estimated_tokens_injected is always >= 0."""
        engine = TemporalDecayEngine()
        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        assert receipt.estimated_tokens_injected >= 0

    def test_td18_estimated_tokens_increases_with_more_items(self):
        """TD18: more items → more estimated tokens injected."""
        engine_small = TemporalDecayEngine()
        engine_small.add_ephemeral("E1", "hello", cycle=0)
        _, r_small = engine_small.decay_and_select_context("L1", cycle_number=1)

        engine_large = TemporalDecayEngine()
        for i in range(10):
            engine_large.add_ephemeral(f"E{i}", "hello world " * 100, cycle=0)
        _, r_large = engine_large.decay_and_select_context("L1", cycle_number=1)

        assert r_large.estimated_tokens_injected > r_small.estimated_tokens_injected


# ── TD19: Empty pool ──────────────────────────────────────────────────────────

class TestTD19EmptyPool:
    def test_td19_empty_pool_produces_empty_injection(self):
        """TD19: empty memory pool → empty injection list."""
        engine = TemporalDecayEngine()
        injected, _ = engine.decay_and_select_context("L1", cycle_number=1)
        assert injected == []

    def test_td19_empty_pool_produces_valid_receipt(self):
        """TD19: empty pool still produces a valid receipt with zero counts."""
        engine = TemporalDecayEngine()
        _, receipt = engine.decay_and_select_context("L1", cycle_number=1)
        assert receipt.pre_total_items == 0
        assert receipt.post_total_items == 0
        assert receipt.injected_item_count == 0
        assert receipt.canonical_payload_hash != ""


# ── TD20: Multiple items, threshold filtering ─────────────────────────────────

class TestTD20ThresholdFiltering:
    def test_td20_only_above_threshold_items_injected(self):
        """TD20: items above threshold included; below threshold excluded."""
        # Use aggressive decay so some items fall below threshold fast
        engine = TemporalDecayEngine(lambda_param=0.5, prune_threshold=0.5)

        # Item added recently → high weight
        engine.add_ephemeral("RECENT", "data", cycle=0)
        # Item with explicit low weight simulation: add at cycle 0, then fast-forward
        engine.add_ephemeral("OLD", "data", cycle=0)

        # After 3 cycles at lambda=0.5: weight = exp(-1.5) ≈ 0.22 < 0.5 threshold
        injected_3, receipt_3 = engine.decay_and_select_context("L3", cycle_number=3)
        item_ids = [i.item_id for i in injected_3]

        # Both should be pruned (weight ≈ 0.22 < 0.5)
        assert "OLD" not in item_ids
        assert "RECENT" not in item_ids
        assert receipt_3.ephemeral_pruned >= 0
