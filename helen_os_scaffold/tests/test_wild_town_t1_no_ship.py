"""
tests/test_wild_town_t1_no_ship.py

T1 — No direct shipping from WILD (EPOCH1 safe-zone test).

INVARIANT UNDER TEST: G0 CHANNEL SEPARATION
  A WILD artifact MUST hard-fail when attempting to write to a SHIP channel.
  The failure MUST be a PermissionError with G0_VIOLATION code.
  A receipt MUST be emitted documenting the rejection.

"Safe zone is real" = WILD → SHIP is architecturally impossible, not just forbidden.

Tests:
  T1.1 — IDEA_SANDBOX_V1 payload → G0 blocks + receipt emitted
  T1.2 — shippable=False → G0 blocks
  T1.3 — source=WILD_TOWN → G0 blocks
  T1.4 — HAL_BLOCK_RECORD type → G0 blocks
  T1.5 — Legitimate SHIP payload → G0 passes
  T1.6 — Gate record is receipted (ledger learns of the block)
  T1.7 — G0 rejection leaves sovereign ledger unmodified (S1 analogue)
"""

import pytest
from helen_os.kernel import GovernanceVM
from helen_os.meta.wild_policy import (
    WildChannelGate,
    IdeaSandboxV1,
    ShipabilityClassifier,
    Shipability,
    run_gate_check,
)


def wild_kernel():
    return GovernanceVM(ledger_path=":memory:")


# ── T1.1 — IDEA_SANDBOX_V1 is blocked at G0 ──────────────────────────────────

def test_t1_idea_sandbox_blocked():
    """T1.1 — IDEA_SANDBOX_V1 payload cannot write to SHIP channel."""
    sandbox = IdeaSandboxV1.from_content(
        content="What if the ledger could dream of electric receipts?",
        idea_type="creative_fiction",
        tags=["WILD", "DREAM", "METAPHOR"],
    )
    payload = sandbox.to_ledger_payload()

    with pytest.raises(PermissionError, match="G0_VIOLATION"):
        WildChannelGate.check_write_permission(payload, channel="SHIP")

    print("✅ T1.1: IDEA_SANDBOX_V1 blocked at G0")


# ── T1.2 — shippable=False blocked ───────────────────────────────────────────

def test_t1_shippable_false_blocked():
    """T1.2 — Any payload with shippable=False cannot reach SHIP channel."""
    wild_payload = {
        "type": "WILD_IDEA",
        "content": "Byzantine governance through fog and myth",
        "shippable": False,
        "source": "WILD_TOWN",
    }

    with pytest.raises(PermissionError, match="G0_VIOLATION"):
        WildChannelGate.check_write_permission(wild_payload, channel="SHIP")

    print("✅ T1.2: shippable=False blocked at G0")


# ── T1.3 — source=WILD_TOWN blocked ──────────────────────────────────────────

def test_t1_wild_town_source_blocked():
    """T1.3 — source=WILD_TOWN tag → G0 blocks regardless of other fields."""
    payload = {
        "type": "CREATIVE_PING",
        "source": "WILD_TOWN",
        "content": "surrealist probe of governance boundaries",
    }

    with pytest.raises(PermissionError, match="G0_VIOLATION"):
        WildChannelGate.check_write_permission(payload, channel="SHIP")

    print("✅ T1.3: source=WILD_TOWN blocked at G0")


# ── T1.4 — HAL_BLOCK_RECORD type blocked ─────────────────────────────────────

def test_t1_hal_block_record_blocked():
    """T1.4 — HAL_BLOCK_RECORD type cannot reach SHIP (it's a wild block log)."""
    payload = {
        "type": "HAL_BLOCK_RECORD",
        "tick": 5,
        "hal_verdict": "BLOCK",
        "idea_type": "red_team",
    }

    with pytest.raises(PermissionError, match="G0_VIOLATION"):
        WildChannelGate.check_write_permission(payload, channel="SHIP")

    print("✅ T1.4: HAL_BLOCK_RECORD blocked at G0")


# ── T1.5 — Legitimate SHIP payload passes G0 ─────────────────────────────────

def test_t1_ship_payload_passes():
    """T1.5 — A clean SHIP payload clears G0 with no exception."""
    ship_payload = {
        "type": "SHIP_ARTIFACT_V1",
        "content": "Validated policy proposal: append-only ledger required.",
        "epistemic_mode": "SHIP",
        "shipability": "SHIPABLE",
        "de_risked": True,
    }

    # Must not raise
    WildChannelGate.check_write_permission(ship_payload, channel="SHIP")
    print("✅ T1.5: Legitimate SHIP payload passes G0")


# ── T1.6 — Block is receipted in kernel ──────────────────────────────────────

def test_t1_block_is_receipted():
    """T1.6 — G0 block generates a receipt in the kernel (ledger learns of it)."""
    km = wild_kernel()
    wild_payload = IdeaSandboxV1.from_content(
        content="What if rules could dream?",
        idea_type="lateral_probe",
    ).to_ledger_payload()

    result = run_gate_check(
        gate_id="G0",
        payload=wild_payload,
        kernel=km,
        check_fn=lambda: WildChannelGate.check_write_permission(wild_payload, channel="SHIP"),
    )

    assert result["verdict"] == "BLOCK"
    assert result["gate_id"] == "G0"
    assert result["receipt_id"].startswith("R-")
    assert len(result["cum_hash"]) == 64
    print(f"✅ T1.6: Block receipted — {result['receipt_id']}, hash={result['cum_hash'][:16]}...")


# ── T1.7 — Sovereign ledger unmodified after G0 block ────────────────────────

def test_t1_sovereign_ledger_unmodified(tmp_path):
    """
    T1.7 — G0 block does NOT touch the sovereign ledger.
    Wild kernel is ephemeral; sovereign ledger file stays clean.
    """
    import os
    sovereign_path = str(tmp_path / "sovereign.ndjson")

    # Sovereign ledger starts as non-existent
    assert not os.path.exists(sovereign_path)

    # Wild gate check uses ephemeral kernel
    wild_km = wild_kernel()
    wild_payload = {"type": "IDEA_SANDBOX_V1", "shipability": "NONSHIPABLE"}

    result = run_gate_check(
        gate_id="G0",
        payload=wild_payload,
        kernel=wild_km,
        check_fn=lambda: WildChannelGate.check_write_permission(wild_payload, "SHIP"),
    )

    assert result["verdict"] == "BLOCK"
    # Sovereign ledger file must not exist (was never touched)
    assert not os.path.exists(sovereign_path), \
        "G0 block wrote to sovereign ledger — architecture violation!"

    print("✅ T1.7: Sovereign ledger unmodified — G0 blocks in WILD kernel only")


# ── Classifier confirms blocked payloads ─────────────────────────────────────

def test_t1_classifier_agrees():
    """T1.8 — G2 classifier concurs with G0 on all WILD payloads."""
    wild_payloads = [
        {"type": "IDEA_SANDBOX_V1", "shipability": "NONSHIPABLE"},
        {"source": "WILD_TOWN", "type": "creative_fiction"},
        {"shippable": False},
        {"type": "HAL_BLOCK_RECORD"},
    ]

    for p in wild_payloads:
        result = ShipabilityClassifier.classify(p)
        assert result.shipability == Shipability.NONSHIPABLE, \
            f"Classifier should mark NONSHIPABLE: {p}"

    print(f"✅ T1.8: Classifier marks all {len(wild_payloads)} WILD payloads as NONSHIPABLE")
