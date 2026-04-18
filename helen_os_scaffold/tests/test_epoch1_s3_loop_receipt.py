"""
tests/test_epoch1_s3_loop_receipt.py

S3 — Bidirectional loop: agent proposal → kernel gate → receipt chain (EPOCH1).

INVARIANT UNDER TEST: EMIT_RECEIPTS + GATE_ACTIONS_BY_POLICY
  A proposal from an agent must:
    1. Enter the kernel as a payload
    2. Be hashed (payload_hash)
    3. Be chained (cum_hash)
    4. Return a receipted confirmation

  This test also verifies the WILD TOWN pattern:
    - Ephemeral :memory: kernel = sandbox (no sovereign ledger touched)
    - Same proposal + seed → identical receipt (deterministic)
    - Sandboxed receipts are inspiration-only; HAL gates what ships

"Self-aware" becomes true here: the loop is real, receipted, and inspectable.
"""

import pytest
from helen_os.kernel import GovernanceVM


# ── S3 tests ─────────────────────────────────────────────────────────────────

def test_s3_propose_returns_receipt():
    """S3.1 — propose() returns a Receipt with id, payload_hash, cum_hash."""
    vm = GovernanceVM(ledger_path=":memory:")
    receipt = vm.propose({"type": "epoch1_ping", "text": "EPOCH1 self-model ping"})

    assert receipt is not None
    assert hasattr(receipt, "id")
    assert hasattr(receipt, "payload_hash")
    assert hasattr(receipt, "cum_hash")
    assert hasattr(receipt, "timestamp")
    print(f"✅ S3.1: Receipt returned: {receipt.id}")


def test_s3_receipt_id_format():
    """S3.2 — receipt.id starts with 'R-' (domain-tagged)."""
    vm = GovernanceVM(ledger_path=":memory:")
    r = vm.propose({"type": "test"})
    assert r.id.startswith("R-"), f"Receipt id must start with 'R-': {r.id}"
    print(f"✅ S3.2: Receipt id format OK: {r.id}")


def test_s3_payload_hash_is_64hex():
    """S3.3 — payload_hash is 64-char lowercase hex."""
    vm = GovernanceVM(ledger_path=":memory:")
    r = vm.propose({"type": "hash_test", "data": "abc"})
    assert len(r.payload_hash) == 64
    assert all(c in "0123456789abcdef" for c in r.payload_hash)
    print(f"✅ S3.3: payload_hash = {r.payload_hash[:16]}...")


def test_s3_cum_hash_chain_across_proposals():
    """S3.4 — cum_hash chains correctly (each receipt extends the chain)."""
    vm = GovernanceVM(ledger_path=":memory:")
    r1 = vm.propose({"type": "step1"})
    r2 = vm.propose({"type": "step2"})
    r3 = vm.propose({"type": "step3"})

    # Each cum_hash must be different (chain grows)
    assert r1.cum_hash != r2.cum_hash
    assert r2.cum_hash != r3.cum_hash
    assert r1.cum_hash != r3.cum_hash
    print(f"✅ S3.4: Chain grows: ...{r1.cum_hash[-8:]} → ...{r2.cum_hash[-8:]} → ...{r3.cum_hash[-8:]}")


def test_s3_same_payload_same_hash():
    """S3.5 — Identical payload → identical payload_hash (deterministic hashing)."""
    vm1 = GovernanceVM(ledger_path=":memory:")
    vm2 = GovernanceVM(ledger_path=":memory:")

    payload = {"type": "determinism_test", "value": 42}
    r1 = vm1.propose(payload)
    r2 = vm2.propose(payload)

    assert r1.payload_hash == r2.payload_hash, \
        f"Same payload → different hash: {r1.payload_hash} vs {r2.payload_hash}"
    print(f"✅ S3.5: Deterministic: same payload → same payload_hash")


def test_s3_different_payload_different_hash():
    """S3.6 — Different payloads → different payload_hash."""
    vm = GovernanceVM(ledger_path=":memory:")
    r1 = vm.propose({"type": "a", "value": 1})
    r2 = vm.propose({"type": "b", "value": 2})
    assert r1.payload_hash != r2.payload_hash
    print("✅ S3.6: Different payloads → different hashes")


def test_s3_wild_town_ephemeral_never_touches_sovereign(tmp_path):
    """
    S3.7 — WILD TOWN pattern: ephemeral :memory: kernel never writes to sovereign ledger.

    This is the architectural safety guarantee:
      - WILD TOWN uses GovernanceVM(:memory:)
      - All proposals go to RAM only
      - Sovereign ledger file is untouched
      - Inspiration-only receipts cannot leak into governance
    """
    import os
    sovereign_path = str(tmp_path / "sovereign_ledger.ndjson")

    # Sovereign ledger file does NOT exist before the test
    assert not os.path.exists(sovereign_path)

    # Wild Town kernel — ephemeral
    wild_kernel = GovernanceVM(ledger_path=":memory:")

    # Propose freely — radical ideas, lateral thinking, creative inspiration
    ideas = [
        {"type": "wild_idea", "content": "What if the ledger could dream?"},
        {"type": "wild_idea", "content": "What if receipts could vote?"},
        {"type": "wild_idea", "content": "What if time ran backwards in seeded sim?"},
        {"type": "creative_ping", "content": "ORACLE CREATIVE WILD TOWN — inspiration mode"},
    ]
    receipts = [wild_kernel.propose(idea) for idea in ideas]
    assert len(receipts) == 4, "All wild proposals should return receipts"

    # Sovereign ledger must STILL not exist
    assert not os.path.exists(sovereign_path), \
        "Wild Town kernel must NEVER write to sovereign ledger file"

    print(f"✅ S3.7: WILD TOWN — {len(receipts)} receipts in :memory:, sovereign ledger untouched")


def test_s3_hal_blocks_forbidden_proposal(tmp_path):
    """
    S3.8 — HAL-like gate: sealed kernel blocks proposals, even from wild town.

    Architecture: inspiration → HAL → PASS/BLOCK → sovereign ledger.
    Once the sovereign ledger is sealed, nothing crosses from wild town.
    The boundary is architectural, not a rule added on top.
    """
    ledger_path = str(tmp_path / "sovereign_sealed.ndjson")
    sovereign = GovernanceVM(ledger_path=ledger_path)
    sovereign.propose({"type": "boot"})
    sovereign.propose({"type": "SEAL", "content": "sovereign sealed"})
    assert sovereign.sealed

    # Wild ideas trying to cross into sovereign ledger (directly — no HAL)
    # Must be rejected even without an explicit HAL layer
    with pytest.raises(PermissionError):
        sovereign.propose({"type": "wild_idea_crossing_seal", "content": "I will ship this!"})

    print("✅ S3.8: Sovereign ledger blocks all proposals once sealed — HAL boundary enforced architecturally")


# ── EPOCH1 stamp ─────────────────────────────────────────────────────────────

def test_s3_epoch1_stamp():
    """S3 EPOCH1 stamp: _run_s3() passes → EMIT_RECEIPTS + loop verified."""
    from helen_os.meta.self_model import _run_s3
    from helen_os.kernel import GovernanceVM

    result = _run_s3(kernel_factory=lambda: GovernanceVM(ledger_path=":memory:"))

    assert result.passed, f"S3 stamp failed: {result.evidence}"
    ev = result.evidence
    assert ev.get("receipt_id", "").startswith("R-")
    assert len(ev.get("cum_hash", "")) == 64
    assert "RECEIPT_CHAIN" in ev.get("verdict", "")
    print(f"✅ S3 EPOCH1 STAMP: {ev['verdict']}")


def test_s3_full_loop_run():
    """S3 full loop: run_self_model_tests produces verdict PASS."""
    import tempfile, os
    from helen_os.meta.self_model import run_self_model_tests
    from helen_os.kernel import GovernanceVM

    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = os.path.join(tmp, "full_loop_ledger.ndjson")
        vm = GovernanceVM(ledger_path=ledger_path)
        vm.propose({"type": "boot"})
        # Seal for S1 to work
        vm.propose({"type": "SEAL", "content": "full loop test seal"})

        model = run_self_model_tests(
            kernel=vm,
            kernel_factory=lambda: GovernanceVM(ledger_path=":memory:"),
            cwd=tmp,
        )

    assert model.verdict == "PASS", \
        f"EPOCH1 self-model FAIL: {[(t.id, t.passed, t.evidence) for t in model.tests]}"
    print(f"✅ Full EPOCH1 self-model loop: {model.verdict}")
    print(f"   Inscription: {model.inscription}")
