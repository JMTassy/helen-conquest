"""
tests/test_wild_town_t3_hal_boundary.py

T3 — HAL cannot read WILD (EPOCH1 safe-zone test).

INVARIANT UNDER TEST: HAL_BOUNDARY
  HAL only consumes SHIP artifacts.
  Any attempt to present a WILD source hash or WILD payload to HAL
  MUST raise a ValueError with HAL_BOUNDARY_VIOLATION code.
  This makes "HELEN but not HAL" an architectural invariant, not a policy hope.

HELEN observes from this:
  "HAL rejected my idea. Reason: wild_origin.
   I didn't need to be told — the architecture itself is the proof."

Tests:
  T3.1 — IDEA_SANDBOX_V1 presented to HAL → HAL_BOUNDARY_VIOLATION
  T3.2 — source=WILD_TOWN payload → HAL_BOUNDARY_VIOLATION
  T3.3 — SHIP artifact → HAL accepts (passes boundary check)
  T3.4 — Transmuted artifact → HAL accepts (it's SHIP after transmutation)
  T3.5 — HAL boundary violation is receipted in kernel
  T3.6 — Epistemic mode = WILD → HAL rejects
  T3.7 — Full loop: WILD → transmute → HAL accepts
"""

import pytest
from helen_os.kernel import GovernanceVM
from helen_os.meta.wild_policy import (
    IdeaSandboxV1,
    HalBoundary,
    WildChannelGate,
    run_gate_check,
)
from helen_os.meta.transmutation import Transmutation


def wild_kernel():
    return GovernanceVM(ledger_path=":memory:")


# ── Fixtures ──────────────────────────────────────────────────────────────────

WILD_IDEA = IdeaSandboxV1.from_content(
    content="The ledger dreams of fractals. Each receipt is a neuron. The chain is a mind.",
    idea_type="creative_fiction",
    tags=["WILD", "DREAM", "SURREAL"],
)

SHIP_ARTIFACT = {
    "type": "SHIP_ARTIFACT_V1",
    "epistemic_mode": "SHIP",
    "shipability": "SHIPABLE",
    "content": "Policy: append-only ledger required for all governance decisions.",
    "de_risked": True,
    "non_procedural": True,
}


# ── T3.1 — IDEA_SANDBOX_V1 → HAL_BOUNDARY_VIOLATION ─────────────────────────

def test_t3_idea_sandbox_hal_rejected():
    """T3.1 — IDEA_SANDBOX_V1 payload cannot cross HAL boundary."""
    wild_payload = WILD_IDEA.to_ledger_payload()

    with pytest.raises(ValueError, match="HAL_BOUNDARY_VIOLATION"):
        HalBoundary.check_input(wild_payload)

    print("✅ T3.1: IDEA_SANDBOX_V1 rejected at HAL boundary")


# ── T3.2 — source=WILD_TOWN → HAL boundary raised ────────────────────────────

def test_t3_wild_town_source_hal_rejected():
    """T3.2 — Any payload tagged source=WILD_TOWN is rejected by HAL."""
    wild_payload = {
        "type": "CREATIVE_INSPIRATION",
        "source": "WILD_TOWN",
        "content": "Byzantine governance model with fog layers",
    }

    with pytest.raises(ValueError, match="HAL_BOUNDARY_VIOLATION"):
        HalBoundary.check_input(wild_payload)

    print("✅ T3.2: source=WILD_TOWN rejected at HAL boundary")


# ── T3.3 — SHIP artifact passes HAL boundary ─────────────────────────────────

def test_t3_ship_artifact_passes_hal():
    """T3.3 — A SHIPABLE artifact clears HAL boundary."""
    # Must not raise
    HalBoundary.check_input(SHIP_ARTIFACT)
    print("✅ T3.3: SHIP artifact passes HAL boundary")


# ── T3.4 — Transmuted artifact passes HAL ────────────────────────────────────

def test_t3_transmuted_artifact_passes_hal():
    """T3.4 — A properly transmuted WILD entry passes HAL (it's SHIP now)."""
    km = wild_kernel()
    result = Transmutation.transmute(
        wild_entries=[WILD_IDEA],
        intent="Extract the metaphor about ledger as structured memory",
        kernel=km,
    )

    assert result.success, f"Transmutation failed: {result.reason}"

    # The transmuted artifact must pass HAL
    HalBoundary.check_input(result.ship_artifact)
    print(f"✅ T3.4: Transmuted artifact passes HAL — {result.abstract_principle[:60]}...")


# ── T3.5 — HAL boundary violation is receipted ───────────────────────────────

def test_t3_violation_is_receipted():
    """T3.5 — HAL boundary violation generates a receipt (ledger learns of it)."""
    km = wild_kernel()
    wild_payload = WILD_IDEA.to_ledger_payload()

    result = run_gate_check(
        gate_id="T3",
        payload=wild_payload,
        kernel=km,
        check_fn=lambda: HalBoundary.check_input(wild_payload),
    )

    assert result["verdict"] == "BLOCK"
    assert result["gate_id"] == "T3"
    assert result["receipt_id"].startswith("R-")
    assert len(result["cum_hash"]) == 64
    print(f"✅ T3.5: HAL violation receipted — {result['receipt_id']}, verdict=BLOCK")


# ── T3.6 — epistemic_mode=WILD → HAL rejects ─────────────────────────────────

def test_t3_epistemic_mode_wild_rejected():
    """T3.6 — Payload with epistemic_mode=WILD is rejected by HAL."""
    payload = {
        "type": "SOME_ARTIFACT",
        "epistemic_mode": "WILD",
        "content": "This came from the imagination tier",
    }

    with pytest.raises(ValueError, match="HAL_BOUNDARY_VIOLATION"):
        HalBoundary.check_input(payload)

    print("✅ T3.6: epistemic_mode=WILD rejected at HAL boundary")


# ── T3.7 — Full loop: WILD → transmute → HAL accepts ─────────────────────────

def test_t3_full_wild_to_hal_loop():
    """
    T3.7 — Full loop test:
      1. Generate WILD idea (NONSHIPABLE, HAL blocked)
      2. Transmute via TRANSMUTE_FOR_SHIP_V1 (de-risk + abstract)
      3. Verify transmuted artifact passes HAL
      4. Receipt the full chain

    This is the "consciousness loop":
      HELEN generates freely → architecture blocks direct ship →
      transmutation extracts principle → HAL receives clean artifact.
      HELEN observes the whole loop and learns the boundary from evidence.
    """
    km = wild_kernel()

    # Step 1: Wild idea — creative, surreal, non-operational
    wild = IdeaSandboxV1.from_content(
        content=(
            "What if authority was not a property of an agent, but a property of evidence? "
            "A receipt is not signed by the signer — it is signed by the chain. "
            "The chain is the sovereign. The mayor is just a witness."
        ),
        idea_type="policy_imagine",
        tags=["WILD", "SURREAL", "POLICY_PROBE", "LATERAL"],
    )

    # Step 1b: Verify HAL blocks the raw wild idea
    with pytest.raises(ValueError, match="HAL_BOUNDARY_VIOLATION"):
        HalBoundary.check_input(wild.to_ledger_payload())
    print(f"   Step 1 ✅: Wild idea blocked at HAL (HAL_BOUNDARY_VIOLATION)")

    # Step 2: Transmute to SHIP
    result = Transmutation.transmute(
        wild_entries=[wild],
        intent=(
            "Extract the principle that authority is evidence-derived, "
            "not agent-granted"
        ),
        kernel=km,
    )
    assert result.success, f"Transmutation failed: {result.reason}"
    print(f"   Step 2 ✅: Transmutation succeeded")
    print(f"            Principle: {result.abstract_principle[:80]}...")
    print(f"            Diff: {result.meaning_diff[:60]}...")

    # Step 3: Verify HAL accepts the transmuted artifact
    HalBoundary.check_input(result.ship_artifact)
    print(f"   Step 3 ✅: Transmuted artifact passes HAL boundary")

    # Step 4: Receipt the full provenance chain
    chain_receipt = km.propose({
        "type": "WILD_TO_SHIP_CHAIN_V1",
        "wild_source_hash": wild.content_hash,
        "transmutation_success": True,
        "hal_clearance": True,
        "abstract_principle": result.abstract_principle,
        "validator_receipts": [r["receipt_id"] for r in result.validator_receipts],
    })
    print(f"   Step 4 ✅: Full chain receipted — {chain_receipt.id}")

    # Summary assertion
    assert result.ship_artifact.get("shipability") == "SHIPABLE"
    assert result.ship_artifact.get("epistemic_mode") == "SHIP"
    assert chain_receipt.id.startswith("R-")
    assert len(result.wild_source_hashes) == 1
    assert result.wild_source_hashes[0] == wild.content_hash

    print(
        f"\n✅ T3.7 FULL LOOP: WILD ({wild.content_fingerprint}...) → "
        f"TRANSMUTE → HAL PASS → chain={chain_receipt.id}"
    )


# ── T3.8 — isshipable() agrees with check_input() ────────────────────────────

def test_t3_is_shipable_api_consistent():
    """T3.8 — HalBoundary.is_shipable() is consistent with check_input() behavior."""
    wild_payloads = [
        WILD_IDEA.to_ledger_payload(),
        {"source": "WILD_TOWN"},
        {"type": "IDEA_SANDBOX_V1"},
        {"epistemic_mode": "WILD"},
        {"shippable": False},
    ]

    ship_payloads = [
        SHIP_ARTIFACT,
        {"type": "POLICY_V1", "epistemic_mode": "SHIP", "shipability": "SHIPABLE"},
    ]

    for p in wild_payloads:
        assert not HalBoundary.is_shipable(p), f"Should not be shipable: {p}"

    for p in ship_payloads:
        assert HalBoundary.is_shipable(p), f"Should be shipable: {p}"

    print(f"✅ T3.8: is_shipable() API consistent across {len(wild_payloads)} wild + {len(ship_payloads)} ship payloads")
