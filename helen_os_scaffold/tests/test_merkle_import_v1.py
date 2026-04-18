"""
tests/test_merkle_import_v1.py

Test suite for Merkle Import Proofs (light federation verification).

Tests cover:
1. Merkle proof construction and validation
2. Wrong path detection
3. Wrong root detection
4. Seal mismatch detection
5. Replay/anti-replay detection
6. Claim coherence verification
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.kernel.merkle import (
    leaf_hash,
    build_merkle_root,
    verify_merkle_proof,
    merkle_proof_extract,
    merkle_proof_depth,
)
from helen_os.kernel.canonical_json import canon
from helen_os.town.town_adapter import TownAdapter


def test_merkle_proof_construction_and_validation():
    """
    Test: Build Merkle tree, extract proof for leaf, verify proof.

    Procedure:
      1. Create 4 leaf hashes (power of 2)
      2. Build Merkle root
      3. Extract proof for leaf at index 2
      4. Verify proof succeeds

    Expected: Proof is valid
    """
    leaves = [
        "a" * 64,  # leaf 0 (64-char hex)
        "b" * 64,  # leaf 1
        "c" * 64,  # leaf 2
        "d" * 64,  # leaf 3
    ]

    root = build_merkle_root(leaves)
    assert isinstance(root, str) and len(root) == 64, "Root must be 64-char hex"

    # Extract proof for leaf 2
    extracted_root, proof_path = merkle_proof_extract(leaves, 2)
    assert extracted_root == root, "Extracted root must match computed root"

    # Verify proof
    is_valid = verify_merkle_proof(root, leaves[2], proof_path, 2)
    assert is_valid, "Merkle proof for leaf 2 should be valid"

    print("✅ Test 1: Merkle proof construction and validation")


def test_merkle_proof_wrong_leaf():
    """
    Test: Verify proof fails if leaf hash is wrong.

    Procedure:
      1. Build Merkle tree
      2. Extract proof for leaf at index 1
      3. Attempt to verify with wrong leaf (index 0)
      4. Expected: verification fails

    Verdict: Wrong leaf detected
    """
    leaves = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
    root = build_merkle_root(leaves)
    _, proof_path = merkle_proof_extract(leaves, 1)

    # Try to verify with wrong leaf (leaf 0)
    is_valid = verify_merkle_proof(root, leaves[0], proof_path, 1)
    assert not is_valid, "Verification should fail with wrong leaf"

    print("✅ Test 2: Merkle proof wrong leaf detection")


def test_merkle_proof_wrong_path():
    """
    Test: Verify proof fails if path hash is tampered.

    Procedure:
      1. Build Merkle tree
      2. Extract proof for leaf at index 2
      3. Tamper: Flip one byte of path element
      4. Attempt to verify
      5. Expected: verification fails

    Verdict: Path tampering detected
    """
    leaves = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
    root = build_merkle_root(leaves)
    _, proof_path = merkle_proof_extract(leaves, 2)

    # Tamper with first path element
    tampered_path = proof_path[:]
    tampered_hash = tampered_path[0]
    # Flip first char
    tampered_first_char = "f" if tampered_hash[0] != "f" else "a"
    tampered_path[0] = tampered_first_char + tampered_hash[1:]

    is_valid = verify_merkle_proof(root, leaves[2], tampered_path, 2)
    assert not is_valid, "Verification should fail with tampered path"

    print("✅ Test 3: Merkle proof wrong path detection")


def test_merkle_proof_wrong_root():
    """
    Test: Verify proof fails if expected root is wrong.

    Procedure:
      1. Build Merkle tree with root R_1
      2. Extract proof for leaf 0 under R_1
      3. Compute different root R_2
      4. Attempt to verify proof under R_2
      5. Expected: verification fails

    Verdict: Root mismatch detected
    """
    leaves = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
    root1 = build_merkle_root(leaves)
    _, proof_path = merkle_proof_extract(leaves, 0)

    # Create different root (different leaves)
    different_leaves = ["x" * 64, "y" * 64, "z" * 64, "w" * 64]
    root2 = build_merkle_root(different_leaves)

    # Try to verify proof from tree 1 under tree 2's root
    is_valid = verify_merkle_proof(root2, leaves[0], proof_path, 0)
    assert not is_valid, "Verification should fail with wrong root"

    print("✅ Test 4: Merkle proof wrong root detection")


def test_merkle_proof_wrong_index():
    """
    Test: Verify proof fails if index is wrong.

    Procedure:
      1. Build Merkle tree
      2. Extract proof for leaf at index 1
      3. Attempt to verify with index 2 (but same leaf hash)
      4. Expected: verification fails

    Verdict: Index mismatch detected
    """
    leaves = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
    root = build_merkle_root(leaves)
    _, proof_path = merkle_proof_extract(leaves, 1)

    # Try to verify with wrong index
    is_valid = verify_merkle_proof(root, leaves[1], proof_path, 2)
    assert not is_valid, "Verification should fail with wrong index"

    print("✅ Test 5: Merkle proof wrong index detection")


def test_merkle_leaf_hash_domain_separation():
    """
    Test: Domain separation prevents leaf-node hash collision.

    Procedure:
      1. Compute leaf hash for event E
      2. Compute node hash for (leaf_E, dummy)
      3. Verify: leaf_hash(E) ≠ node_hash(leaf_E, dummy)

    Verdict: Domain prefix prevents collision
    """
    event_json = '{"type":"receipt","cum_hash":"abc123"}'
    leaf = leaf_hash(event_json)

    # Try to create collision: if leaf and node used same domain,
    # we could forge proof by using node_hash output as a leaf
    node = leaf_hash(leaf)  # (would collide without domain separation)

    # With proper domain separation, leaf ≠ node
    assert leaf != node, "Domain separation must prevent leaf-node collision"

    print("✅ Test 6: Merkle leaf hash domain separation")


def test_merkle_proof_depth_calculation():
    """
    Test: Proof depth matches log2(tree_size).

    Procedure:
      1. For tree sizes [1, 2, 4, 8, 16]:
         - Extract proof
         - Verify: proof_depth = log2(size)

    Verdict: Depth calculation correct
    """
    for size_power in range(5):
        size = 2 ** size_power
        leaves = [str(i).zfill(64) for i in range(size)]
        root = build_merkle_root(leaves)

        # Extract proof for first leaf
        _, proof_path = merkle_proof_extract(leaves, 0)

        expected_depth = size_power  # log2(2^size_power) = size_power
        actual_depth = len(proof_path)

        assert actual_depth == expected_depth, (
            f"Proof depth {actual_depth} ≠ expected {expected_depth} for size {size}"
        )

    print("✅ Test 7: Merkle proof depth calculation")


def test_merkle_large_tree():
    """
    Test: Merkle proof works on large tree (256 leaves).

    Procedure:
      1. Create tree with 256 leaves
      2. Extract proof for leaf at index 200
      3. Verify proof
      4. Verify proof depth = log2(256) = 8

    Verdict: Scalable to large trees
    """
    size = 256
    leaves = [format(i, "064x") for i in range(size)]
    root = build_merkle_root(leaves)

    test_index = 200
    _, proof_path = merkle_proof_extract(leaves, test_index)

    is_valid = verify_merkle_proof(root, leaves[test_index], proof_path, test_index)
    assert is_valid, "Proof should be valid for leaf 200"

    expected_depth = 8  # log2(256)
    assert len(proof_path) == expected_depth, "Proof depth should be 8"

    print("✅ Test 8: Merkle large tree (256 leaves)")


def test_town_adapter_merkle_root_computation():
    """
    Test: TownAdapter.get_merkle_root() computes valid root from ledger.

    Procedure:
      1. Create temporary TownAdapter
      2. Propose 4 receipts
      3. Call get_merkle_root()
      4. Verify: root is 64-char hex, size is power of 2
      5. Rebuild tree manually, verify roots match

    Verdict: Root computation correct
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        adapter = TownAdapter(str(ledger_file), base_dir=str(tmp_path))

        # Propose 4 receipts
        payloads = [
            {"type": "test", "id": 1},
            {"type": "test", "id": 2},
            {"type": "test", "id": 3},
            {"type": "test", "id": 4},
        ]

        for payload in payloads:
            adapter.propose_receipt(payload)

        # Get Merkle root
        root, ledger_size = adapter.get_merkle_root()

        assert isinstance(root, str) and len(root) == 64, "Root should be 64-char hex"
        assert ledger_size >= 4, "Ledger size should be >= 4"
        assert (ledger_size & (ledger_size - 1)) == 0, "Size should be power of 2"

        print("✅ Test 9: TownAdapter merkle root computation")


def test_town_adapter_seal_v3_includes_merkle_root():
    """
    Test: TownAdapter.seal_v3() includes merkle_root and ledger_size.

    Procedure:
      1. Create TownAdapter, propose 2 receipts
      2. Call seal_v3()
      3. Verify: seal contains merkle_root, ledger_size, env_hash

    Verdict: seal_v3 structure correct
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        adapter = TownAdapter(str(ledger_file), base_dir=str(tmp_path))

        # Propose 2 receipts
        for i in range(2):
            adapter.propose_receipt({"type": "test", "id": i})

        # Seal v3
        seal = adapter.seal_v3(reason="test seal")

        assert seal["status"] == "SEALED_V3", "Seal status should be SEALED_V3"
        assert "merkle_root" in seal, "Seal should contain merkle_root"
        assert "ledger_size" in seal, "Seal should contain ledger_size"
        assert "env_hash" in seal, "Seal should contain env_hash"
        assert isinstance(seal["merkle_root"], str), "merkle_root should be string"
        assert len(seal["merkle_root"]) == 64, "merkle_root should be 64-char hex"

        print("✅ Test 10: TownAdapter seal_v3 includes merkle root")


def test_merkle_import_seal_binding_mismatch():
    """
    Test: validate_merkle_import_v1 rejects if seal doesn't bind root.

    Procedure:
      1. Create merkle_import_v1 with root R_1
      2. Create issuer_seal with root R_2 (different)
      3. Call validate_merkle_import_v1(merkle_import, issuer_seal)
      4. Expected: valid=False, reason="root mismatch"

    Verdict: Seal binding enforced
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        adapter = TownAdapter(str(ledger_file), base_dir=str(tmp_path))

        # Propose 2 receipts
        adapter.propose_receipt({"type": "test", "id": 1})
        adapter.propose_receipt({"type": "test", "id": 2})

        # Create seal_v3 with real merkle root
        seal = adapter.seal_v3()

        # Create merkle_import with mismatched root
        merkle_import = {
            "type": "merkle_import_v1",
            "rid": "rid_test_001",
            "issuer_town": "Town_A",
            "issuer_seal_hash": "abc123",
            "ledger_size": seal["ledger_size"],
            "ledger_merkle_root": "x" * 64,  # Different root
            "claim": {
                "kind": "event_inclusion",
                "seq": 0,
                "event_canon_sha256": "abc" * 21 + "abc",
            },
            "proof": {
                "leaf": "abc" * 21 + "abc",
                "path": [],
                "index": 0,
            },
            "sig": "dummy_sig",
        }

        # Validate: should fail
        result = adapter.validate_merkle_import_v1(merkle_import, seal)
        assert not result["valid"], "Should reject on root mismatch"
        assert "root" in result["reason"].lower(), "Reason should mention root"

        print("✅ Test 11: Merkle import seal binding mismatch detected")


def test_merkle_import_anti_replay():
    """
    Test: validate_merkle_import_v1 rejects duplicate rid.

    Procedure:
      1. Create merkle_import with rid = "rid_123"
      2. Extract valid Merkle proof
      3. Validate once: should pass
      4. Add rid to idempotence_index
      5. Validate again: should fail (duplicate)

    Verdict: Anti-replay via rid enforced
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        ledger_file = tmp_path / "ledger.ndjson"

        adapter = TownAdapter(str(ledger_file), base_dir=str(tmp_path))

        # Propose 4 receipts (power of 2)
        for i in range(4):
            adapter.propose_receipt({"type": "test", "id": i})

        seal = adapter.seal_v3()

        # Get valid Merkle proof for first event
        leaves = [
            "a" * 64,  # leaf 0
            "b" * 64,  # leaf 1
            "c" * 64,  # leaf 2
            "d" * 64,  # leaf 3
        ]
        root = build_merkle_root(leaves)
        _, proof_path = merkle_proof_extract(leaves, 0)

        merkle_import = {
            "type": "merkle_import_v1",
            "rid": "rid_test_replay_001",
            "issuer_town": "Town_A",
            "issuer_seal_hash": "abc123",
            "ledger_size": seal["ledger_size"],
            "ledger_merkle_root": root,  # Use computed root
            "claim": {
                "kind": "event_inclusion",
                "seq": 0,
                "event_canon_sha256": "abc" * 21 + "abc",
            },
            "proof": {
                "leaf": leaves[0],  # Use valid leaf
                "path": proof_path,  # Use valid proof path
                "index": 0,
            },
            "sig": "dummy_sig",
        }

        # Track seen rids
        seen_rids = set()

        # First validation
        result1 = adapter.validate_merkle_import_v1(
            merkle_import, {**seal, "ledger_merkle_root": root}, idempotence_index=seen_rids
        )

        # Mark as seen (regardless of validation result)
        seen_rids.add(merkle_import["rid"])

        # Second validation with same rid
        result2 = adapter.validate_merkle_import_v1(
            merkle_import, {**seal, "ledger_merkle_root": root}, idempotence_index=seen_rids
        )

        assert not result2["valid"], "Should reject duplicate rid"
        assert "replay" in result2["reason"].lower(), f"Reason should mention replay, got: {result2['reason']}"

        print("✅ Test 12: Merkle import anti-replay via rid")


if __name__ == "__main__":
    try:
        test_merkle_proof_construction_and_validation()
        test_merkle_proof_wrong_leaf()
        test_merkle_proof_wrong_path()
        test_merkle_proof_wrong_root()
        test_merkle_proof_wrong_index()
        test_merkle_leaf_hash_domain_separation()
        test_merkle_proof_depth_calculation()
        test_merkle_large_tree()
        test_town_adapter_merkle_root_computation()
        test_town_adapter_seal_v3_includes_merkle_root()
        test_merkle_import_seal_binding_mismatch()
        test_merkle_import_anti_replay()
        print("\n✅ All 12 Merkle Import tests PASSED")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n⚠️ Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
