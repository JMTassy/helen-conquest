"""
helen_os/kernel/merkle.py

Pure, deterministic Merkle tree verification for CWL federation (Merkle Import Proofs).

Zero IO, zero randomness. Suitable for both building and verifying Merkle roots.

Domain separation:
  - CWL_LEDGER_LEAF_V1: prefix for leaf hashing
  - CWL_MERKLE_NODE_V1: prefix for internal node hashing (optional, for future variants)

Invariants:
  - All hashes are SHA256 (hex string, 64 chars)
  - All paths are lists of sibling hashes (hex strings)
  - Index must match leaf position in tree
  - Tree size must be power of 2 (enforced at verify time)
"""

import hashlib
from typing import List, Tuple
from math import log2


# Domain separators (CWL federation standards)
DOMAIN_LEAF = "CWL_LEDGER_LEAF_V1"
DOMAIN_NODE = "CWL_MERKLE_NODE_V1"


def _hash_deterministic(data: bytes) -> str:
    """
    Deterministic SHA256 hash.

    Args:
        data: Bytes to hash

    Returns:
        Hex string (64 chars, lowercase)
    """
    return hashlib.sha256(data).hexdigest()


def _ensure_bytes(x) -> bytes:
    """Convert string or bytes to bytes."""
    if isinstance(x, str):
        return x.encode("utf-8")
    return x


def leaf_hash(event_canonical_json: str) -> str:
    """
    Compute Merkle leaf hash for a canonical event.

    Domain-separated to prevent leaf-node collision attacks.

    Args:
        event_canonical_json: Canonical JSON representation of event (from canon(e_s))

    Returns:
        Hex string (64 chars)

    Example:
        >>> event_json = '{"type":"receipt","cum_hash":"abc..."}'
        >>> leaf_hash(event_json)
        'ef1234...'
    """
    payload = _ensure_bytes(DOMAIN_LEAF) + b"::" + _ensure_bytes(event_canonical_json)
    return _hash_deterministic(payload)


def node_hash(left: str, right: str) -> str:
    """
    Compute Merkle internal node hash.

    Domain-separated to prevent leaf-node collision.
    Concatenates left + right (order matters; tree is ordered).

    Args:
        left: Left child hash (hex string)
        right: Right child hash (hex string)

    Returns:
        Hex string (64 chars)

    Example:
        >>> left = "abc..."
        >>> right = "def..."
        >>> node_hash(left, right)
        '123456...'
    """
    payload = (
        _ensure_bytes(DOMAIN_NODE)
        + b"::"
        + _ensure_bytes(left)
        + _ensure_bytes(right)
    )
    return _hash_deterministic(payload)


def build_merkle_root(leaves: List[str]) -> str:
    """
    Build Merkle root from list of leaf hashes.

    Tree must have 2^k leaves (power of 2). If not, caller must pad.

    Args:
        leaves: List of leaf hashes (hex strings, in order)

    Returns:
        Root hash (hex string)

    Raises:
        ValueError: If leaf count is not power of 2

    Example:
        >>> leaves = ["leaf0", "leaf1", "leaf2", "leaf3"]
        >>> root = build_merkle_root(leaves)
        >>> len(root) == 64
        True
    """
    n = len(leaves)

    # Verify power of 2
    if n == 0:
        raise ValueError("Merkle tree must have at least 1 leaf")
    if (n & (n - 1)) != 0:
        raise ValueError(f"Leaf count {n} is not power of 2")

    # Single leaf: root is leaf
    if n == 1:
        return leaves[0]

    # Build tree bottom-up
    current_level = leaves[:]

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1]
            parent = node_hash(left, right)
            next_level.append(parent)
        current_level = next_level

    return current_level[0]


def verify_merkle_proof(
    root: str, leaf: str, path: List[str], index: int
) -> bool:
    """
    Verify Merkle inclusion proof.

    Given:
      - root: Expected Merkle root (hex string, 64 chars)
      - leaf: Leaf hash to verify (hex string, 64 chars)
      - path: List of sibling hashes (hex strings, in tree traversal order)
      - index: Position of leaf in tree (0-indexed)

    Verify that leaf is included at position `index` in a tree with root `root`.

    Algorithm:
      1. Start with leaf hash
      2. For each sibling in path:
         - If index is even, hash(leaf, sibling)
         - If index is odd, hash(sibling, leaf)
         - Right-shift index
      3. Final computed root must match expected root

    Returns:
        True if proof is valid, False otherwise

    Example:
        >>> root = "abc..."
        >>> leaf = "leaf_at_3"
        >>> path = ["sibling_2", "parent_0_1"]
        >>> index = 3
        >>> verify_merkle_proof(root, leaf, path, index)
        True
    """
    # Validate input format
    if not isinstance(root, str) or len(root) != 64:
        return False
    if not isinstance(leaf, str) or len(leaf) != 64:
        return False
    if not isinstance(path, list):
        return False
    if not isinstance(index, int) or index < 0:
        return False

    # Validate all path elements are 64-char hex
    for sibling in path:
        if not isinstance(sibling, str) or len(sibling) != 64:
            return False

    # Compute root from leaf and path
    computed = leaf

    for sibling in path:
        if index % 2 == 0:
            # Leaf/node is left child
            computed = node_hash(computed, sibling)
        else:
            # Leaf/node is right child
            computed = node_hash(sibling, computed)

        index //= 2

    # Final check: computed root must match expected root
    return computed == root


def merkle_proof_depth(tree_size: int) -> int:
    """
    Expected proof depth (path length) for tree of given size.

    Formula: depth = log2(size)

    Args:
        tree_size: Number of leaves in tree (must be power of 2)

    Returns:
        Expected path length

    Example:
        >>> merkle_proof_depth(8)  # 2^3 = 8 leaves
        3
    """
    if tree_size <= 1:
        return 0
    if (tree_size & (tree_size - 1)) != 0:
        raise ValueError(f"Tree size {tree_size} is not power of 2")
    return int(log2(tree_size))


def merkle_proof_extract(
    leaves: List[str], index: int
) -> Tuple[str, List[str]]:
    """
    Extract Merkle proof for leaf at given index.

    Helper function for testing. Given full list of leaves,
    compute the root and the inclusion proof for leaves[index].

    Args:
        leaves: Full list of leaf hashes
        index: Index of leaf to prove

    Returns:
        Tuple[root, proof_path]

    Raises:
        ValueError: If index out of range or leaves not power of 2

    Example:
        >>> leaves = ["l0", "l1", "l2", "l3"]
        >>> root, proof = merkle_proof_extract(leaves, 2)
        >>> verify_merkle_proof(root, leaves[2], proof, 2)
        True
    """
    n = len(leaves)

    if index < 0 or index >= n:
        raise ValueError(f"Index {index} out of range [0, {n})")

    if (n & (n - 1)) != 0:
        raise ValueError(f"Leaf count {n} is not power of 2")

    root = build_merkle_root(leaves)
    proof_path = []

    # Track siblings as we build tree bottom-up
    current_level = leaves[:]
    current_index = index

    while len(current_level) > 1:
        # Pair current_index with its sibling
        sibling_index = current_index ^ 1  # Flip last bit (XOR with 1)
        sibling = current_level[sibling_index]
        proof_path.append(sibling)

        # Move to next level
        current_level = [
            node_hash(current_level[i], current_level[i + 1])
            for i in range(0, len(current_level), 2)
        ]
        current_index //= 2

    return root, proof_path
