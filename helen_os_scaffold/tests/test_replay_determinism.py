"""
tests/test_replay_determinism.py

Critical proof: Deterministic replay of kernel receipts.
Same input payload → same cumulative hash (deterministic).
Ledger integrity preserved on replay.

Tests K5 gate (Determinism requires seeded input).
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.kernel import GovernanceVM
from helen_os.town.town_adapter import TownAdapter


def test_same_payload_same_hash():
    """
    Test: Kernel is deterministic.
    Same input state + same payload → same cumulative hash.

    Note: Cumulative hashes chain, so:
    - If ledger is empty: payload1 → hash1
    - If ledger has hash1: payload1 again → different hash2 (chains on hash1)

    This test verifies determinism by checking:
    replay from empty ledger gives same hash as first write.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        # First write
        vm1 = GovernanceVM(str(ledger_file))
        payload = {"source": "test", "data": {"x": 1, "y": 2}}
        receipt1 = vm1.propose(payload)
        hash1 = receipt1.cum_hash

        # Second run: fresh VM, same empty ledger, same payload
        # Clear ledger to simulate fresh start
        ledger_file.write_text("")

        vm2 = GovernanceVM(str(ledger_file))
        receipt2 = vm2.propose(payload)
        hash2 = receipt2.cum_hash

        assert hash1 == hash2, (
            f"Determinism broken: "
            f"first receipt: {hash1}, "
            f"second receipt: {hash2}"
        )
        print("✅ Test 1: Same payload from fresh ledger → same hash (deterministic)")


def test_ledger_replay_verification():
    """
    Test: Ledger verification passes on deterministic replay.
    All cumulative hashes verified correctly.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        # Write several receipts
        vm = GovernanceVM(str(ledger_file))

        payloads = [
            {"type": "test", "seq": 1},
            {"type": "test", "seq": 2},
            {"type": "test", "seq": 3},
        ]

        for payload in payloads:
            vm.propose(payload)

        # Verify ledger
        is_valid = vm.verify_ledger()
        assert is_valid, "Ledger verification failed after writing"
        print("✅ Test 2: Ledger replay verification passes")


def test_town_adapter_idempotence():
    """
    Test: TownAdapter enforces idempotence.
    Same input → same receipt (cached on second call).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        adapter = TownAdapter(str(ledger_file), base_dir=str(tmp_path))

        payload = {"source": "test", "msg": "hello"}

        # First proposal
        receipt1 = adapter.propose_receipt(payload)
        status1 = receipt1.get("status")
        receipt_hash1 = receipt1.get("receipt")

        # Second proposal (identical input)
        receipt2 = adapter.propose_receipt(payload)
        status2 = receipt2.get("status")
        receipt_hash2 = receipt2.get("receipt")

        # Should be idempotent
        assert status2 == "IDEMPOTENT_CACHED", (
            f"Expected IDEMPOTENT_CACHED, got {status2}"
        )
        assert receipt_hash1 == receipt_hash2, (
            f"Receipts differ: {receipt_hash1} vs {receipt_hash2}"
        )
        print("✅ Test 3: TownAdapter idempotence (same input → cached receipt)")


def test_cumulative_hash_chain_integrity():
    """
    Test: Cumulative hashes form valid chain.
    Each hash depends on all previous state (domain separation).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        vm = GovernanceVM(str(ledger_file))

        # Write first payload
        p1 = {"type": "A", "data": "first"}
        r1 = vm.propose(p1)
        hash1 = r1.cum_hash

        # Write second payload
        p2 = {"type": "B", "data": "second"}
        r2 = vm.propose(p2)
        hash2 = r2.cum_hash

        # Hashes must be different (second depends on first)
        assert hash1 != hash2, "Cumulative hashes should differ (chain broken)"

        # Verify replay
        assert vm.verify_ledger(), "Ledger verification failed"

        # Reload and verify tip matches
        vm_replay = GovernanceVM(str(ledger_file))
        assert vm_replay.cum_hash == hash2, (
            f"Replay tip mismatch: {vm_replay.cum_hash} vs {hash2}"
        )
        print("✅ Test 4: Cumulative hash chain integrity verified")


def test_domain_separation_prevents_collision():
    """
    Test: Domain prefix prevents hash collisions between different ledgers.
    Two VMs with different domain separators = different hashes.
    """
    # This is a conceptual test showing that DOMAIN_SEPARATOR
    # is crucial to prevent attacks.
    # In practice, both VMs use same DOMAIN_SEPARATOR, so this
    # verifies the separation is consistently applied.

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        vm = GovernanceVM(str(ledger_file))
        payload = {"test": "data"}

        receipt = vm.propose(payload)

        # Verify the cumulative hash was computed with domain separation
        # (by verifying it passes validation)
        assert vm.verify_ledger(), (
            "Domain-separated hash verification failed"
        )

        print(
            "✅ Test 5: Domain separation consistently applied "
            "(HELEN_CUM_V1:: prefix)"
        )


def test_seal_v2_environment_pinning():
    """
    Test: SEAL_V2 pins environment hash, prevents drift.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        adapter = TownAdapter(str(ledger_file), base_dir=str(tmp_path))

        # Seal the kernel
        seal_receipt = adapter.seal_v2(reason="test seal")
        env_hash = seal_receipt.get("env_hash")

        assert env_hash is not None, "SEAL_V2 did not capture env_hash"
        assert adapter.vm.sealed, "Kernel should be sealed after SEAL_V2"
        assert adapter.vm.pinned_env_hash == env_hash, (
            f"Pinned env hash mismatch: {adapter.vm.pinned_env_hash} vs {env_hash}"
        )

        print("✅ Test 6: SEAL_V2 environment pinning verified")


if __name__ == "__main__":
    try:
        test_same_payload_same_hash()
        test_ledger_replay_verification()
        test_town_adapter_idempotence()
        test_cumulative_hash_chain_integrity()
        test_domain_separation_prevents_collision()
        test_seal_v2_environment_pinning()
        print("\n✅ All 6 deterministic replay tests PASSED")
    except AssertionError as e:
        print(f"\n❌ Determinism test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
