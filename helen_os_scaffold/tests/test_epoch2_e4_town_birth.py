"""
tests/test_epoch2_e4_town_birth.py

E4 — TownBirthPredicateV1: sovereignty requires proof bundle.

Tests:
  E4.1 — evaluate_all_factions() returns one result per faction (10 factions)
  E4.2 — No faction is eligible in seed=42 run (no town_treaty_v1 emitted)
  E4.3 — Faction with MIN_RECEIPT_COUNT receipts passes condition 1
  E4.4 — Faction without treaty_signature fails condition 2
  E4.5 — to_receipt_payload() produces valid TOWN_BIRTH_PREDICATE_V1 payload
  E4.6 — kernel.propose(result.to_receipt_payload()) succeeds (receipt issued)
  E4.7 — TownBirthResult.reason is human-readable and non-empty
  E4.8 — closure_proof=True only when expedition reached Vault
"""

import pytest
from helen_os.kernel import GovernanceVM
from helen_os.seeds.worlds.conquest_land import ConquestLandWorld, FACTIONS
from helen_os.epoch2.town_birth import TownBirthPredicateV1, TownBirthResult, MIN_RECEIPT_COUNT


SEED = 42
TICKS = 20


def run_world(seed=SEED, ticks=TICKS):
    km = GovernanceVM(ledger_path=":memory:")
    world = ConquestLandWorld(km, world_seed=seed)
    all_receipts = []
    for t in range(1, ticks + 1):
        all_receipts.extend(world.tick(t))
    return all_receipts, world.summary()


# ── E4.1 — 10 results returned ───────────────────────────────────────────────

def test_e4_evaluate_all_factions_count():
    """E4.1 — evaluate_all_factions() returns one result per faction (10)."""
    receipts, summary = run_world()
    results = TownBirthPredicateV1.evaluate_all_factions(receipts, summary)

    assert len(results) == len(FACTIONS), (
        f"Expected {len(FACTIONS)} results, got {len(results)}"
    )
    faction_ids = [r.faction_id for r in results]
    for fid in FACTIONS:
        assert fid in faction_ids, f"Faction {fid} missing from results"
    print(f"✅ E4.1: evaluate_all_factions() returned {len(results)} results")


# ── E4.2 — No eligible faction in standard run ───────────────────────────────

def test_e4_no_eligible_faction():
    """E4.2 — No faction is eligible: treaty_signature condition cannot be met."""
    receipts, summary = run_world()
    results = TownBirthPredicateV1.evaluate_all_factions(receipts, summary)

    eligible = [r for r in results if r.eligible]
    assert len(eligible) == 0, (
        f"Expected no eligible factions, but {[r.faction_id for r in eligible]} are eligible. "
        f"Reason: no town_treaty_v1 is emitted in v0.1.0 world."
    )
    print(f"✅ E4.2: No eligible factions — treaty condition blocks all. "
          f"This is BY DESIGN: sovereignty requires ratification.")


# ── E4.3 — Condition 1: receipt_count ────────────────────────────────────────

def test_e4_condition1_receipt_count():
    """E4.3 — Factions with many receipts pass condition 1."""
    receipts, summary = run_world()
    results = TownBirthPredicateV1.evaluate_all_factions(receipts, summary)

    # F9 (Entropy Fog) emits every tick → should have >= MIN_RECEIPT_COUNT
    f9 = next(r for r in results if r.faction_id == "F9")
    assert f9.bundle.receipt_count >= MIN_RECEIPT_COUNT, (
        f"F9 should have >= {MIN_RECEIPT_COUNT} receipts, "
        f"got {f9.bundle.receipt_count}"
    )
    cond1_passed = [r.faction_id for r in results if r.bundle.receipt_count >= MIN_RECEIPT_COUNT]
    assert len(cond1_passed) > 0, "At least one faction should pass condition 1"
    print(f"✅ E4.3: Factions passing receipt_count condition: {cond1_passed}")


# ── E4.4 — Condition 2: treaty_signature always False ────────────────────────

def test_e4_condition2_treaty_always_false():
    """E4.4 — treaty_signature=False for all factions (no town_treaty_v1 emitted)."""
    receipts, summary = run_world()

    treaty_receipts = [r for r in receipts if r.get("evidence_type") == "town_treaty_v1"]
    assert len(treaty_receipts) == 0, (
        "Expected no town_treaty_v1 receipts in v0.1.0 world"
    )

    results = TownBirthPredicateV1.evaluate_all_factions(receipts, summary)
    for r in results:
        assert not r.bundle.treaty_signature, (
            f"{r.faction_id} has treaty_signature=True with no treaties emitted"
        )
    print(f"✅ E4.4: treaty_signature=False for all factions "
          f"(world v0.1.0 does not emit town_treaty_v1 yet)")


# ── E4.5 — to_receipt_payload() structure ────────────────────────────────────

def test_e4_receipt_payload_structure():
    """E4.5 — to_receipt_payload() has TOWN_BIRTH_PREDICATE_V1 type and required fields."""
    receipts, summary = run_world()
    result = TownBirthPredicateV1.evaluate("F9", receipts, summary)
    payload = result.to_receipt_payload()

    required = [
        "type", "faction_id", "eligible",
        "receipt_count", "treaty_signature", "closure_proof",
        "missing", "reason", "checked_at",
    ]
    for f in required:
        assert f in payload, f"Missing field in to_receipt_payload(): {f!r}"
    assert payload["type"] == "TOWN_BIRTH_PREDICATE_V1"
    assert payload["faction_id"] == "F9"
    print(f"✅ E4.5: to_receipt_payload() structure correct")


# ── E4.6 — kernel.propose() succeeds ────────────────────────────────────────

def test_e4_kernel_propose_succeeds():
    """E4.6 — TOWN_BIRTH_PREDICATE_V1 payload can be proposed to kernel."""
    receipts, summary = run_world()
    km = GovernanceVM(ledger_path=":memory:")

    result = TownBirthPredicateV1.evaluate("F7", receipts, summary)
    receipt = km.propose(result.to_receipt_payload())

    assert receipt.id.startswith("R-"), f"Receipt id malformed: {receipt.id}"
    assert len(receipt.cum_hash) == 64
    print(f"✅ E4.6: TOWN_BIRTH_PREDICATE_V1 receipted — {receipt.id}")


# ── E4.7 — reason is human-readable ──────────────────────────────────────────

def test_e4_reason_human_readable():
    """E4.7 — TownBirthResult.reason is non-empty and contains faction_id."""
    receipts, summary = run_world()
    results = TownBirthPredicateV1.evaluate_all_factions(receipts, summary)

    for r in results:
        assert len(r.reason) > 5, f"reason too short for {r.faction_id}: {r.reason!r}"
        assert r.faction_id in r.reason, (
            f"faction_id {r.faction_id!r} not in reason: {r.reason!r}"
        )
    print(f"✅ E4.7: All reasons are human-readable and contain faction_id")


# ── E4.8 — closure_proof tied to return_warrant ──────────────────────────────

def test_e4_closure_proof_requires_vault():
    """E4.8 — closure_proof=True only when expedition reached Vault."""
    receipts, summary = run_world()

    assert summary["return_achieved"], (
        "seed=42, ticks=20 should reach Vault with F3 fix"
    )

    # F10 (Vault Templar) emits return_warrant — must have closure_proof
    f10 = TownBirthPredicateV1.evaluate("F10", receipts, summary)
    assert f10.bundle.closure_proof, (
        "F10 should have closure_proof=True (it emits in a Vault-reaching run)"
    )

    # Verify that with return_achieved=False, closure_proof=False
    fake_summary = dict(summary)
    fake_summary["return_achieved"] = False
    f10_no_vault = TownBirthPredicateV1.evaluate("F10", receipts, fake_summary)
    assert not f10_no_vault.bundle.closure_proof
    print(f"✅ E4.8: closure_proof=True when Vault reached, False otherwise")
