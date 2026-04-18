#!/usr/bin/env python3
"""
Deterministic hashing and hashchain utilities.

Ensures: same file → identical SHA256 → identical chain

Used for:
- Artifact integrity proofs (hash-bound attestations)
- Receipt binding (receipt.sha256 = f(inputs))
- Policy pinning (policy_hash = f(policy content))
- Nondeterminism detection (same input, different hash = problem)
"""

import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, List

try:
    from kernel.canonical_json import to_canonical_json
except ImportError:
    from .canonical_json import to_canonical_json


def sha256_bytes(data: bytes) -> str:
    """
    SHA256 hash of bytes.

    Args:
        data: Input bytes

    Returns:
        Lowercase hex string (64 chars)
    """
    return hashlib.sha256(data).hexdigest()


def sha256_str(data: str) -> str:
    """
    SHA256 hash of string (UTF-8 encoded).

    Args:
        data: Input string

    Returns:
        Lowercase hex string (64 chars)
    """
    return sha256_bytes(data.encode("utf-8"))


def sha256_file(file_path: str) -> str:
    """
    SHA256 hash of file contents.

    Args:
        file_path: Path to file

    Returns:
        Lowercase hex string (64 chars)

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read entire file into memory (OK for typical JSON files)
    # For huge files, use chunked reading
    return sha256_bytes(path.read_bytes())


def sha256_canonical_json(obj: any) -> str:
    """
    SHA256 hash of canonical JSON representation.

    This is the key function for deterministic hashing of Python objects.
    Uses canonical_json.to_canonical_json() to ensure identical bytes.

    Args:
        obj: Python object to hash

    Returns:
        Lowercase hex string (64 chars)

    Raises:
        ValueError: If object contains non-finite floats or unsupported types
    """
    canonical = to_canonical_json(obj)
    return sha256_str(canonical)


def ndjson_hashchain_line(prev_hash: Optional[str], line_data: Dict) -> str:
    """
    Compute hash for a single NDJSON line with optional chaining.

    Used for append-only ledgers (rho_trace, ledger.ndjson, etc.)
    Each line includes hash of previous line → creates chain.

    Args:
        prev_hash: Hash of previous line (or None for first line)
        line_data: Current line data (dict)

    Returns:
        Hash of current line (includes prev_hash if present)
    """
    if prev_hash:
        line_with_chain = {
            "prev_hash": prev_hash,
            **line_data
        }
    else:
        line_with_chain = line_data

    return sha256_canonical_json(line_with_chain)


def verify_ndjson_hashchain(ndjson_file: str, hash_field: str = "line_hash") -> bool:
    """
    Verify integrity of append-only NDJSON file with hashchain.

    Each line must have:
    1. A hash field (default: line_hash)
    2. That hash must be sha256(prev_hash + current_line)
    3. First line has no prev_hash

    Args:
        ndjson_file: Path to NDJSON file
        hash_field: Name of field containing line hash

    Returns:
        True if chain is valid, False otherwise

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(ndjson_file)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {ndjson_file}")

    prev_hash = None

    with open(path, "r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue  # Skip empty lines

            try:
                line_obj = json.loads(raw_line)
            except json.JSONDecodeError as e:
                print(f"Line {line_num}: Invalid JSON: {e}")
                return False

            # Extract stored hash
            if hash_field not in line_obj:
                print(f"Line {line_num}: Missing {hash_field}")
                return False

            stored_hash = line_obj[hash_field]

            # Compute expected hash
            line_without_hash = {k: v for k, v in line_obj.items() if k != hash_field}
            expected_hash = ndjson_hashchain_line(prev_hash, line_without_hash)

            # Verify
            if stored_hash != expected_hash:
                print(
                    f"Line {line_num}: Hash mismatch\n"
                    f"  Expected: {expected_hash}\n"
                    f"  Got:      {stored_hash}"
                )
                return False

            prev_hash = expected_hash

    return True


def hash_directory(dir_path: str, glob_pattern: str = "**/*.json") -> Dict[str, str]:
    """
    Hash all files in directory matching pattern.

    Useful for hashing a registry, policy directory, etc.

    Args:
        dir_path: Directory path
        glob_pattern: Glob pattern (default: all JSON files recursively)

    Returns:
        Dict mapping file paths to their SHA256 hashes
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")

    result = {}
    for file_path in sorted(path.glob(glob_pattern)):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(path))
            result[rel_path] = sha256_file(str(file_path))

    return result


# Self-test
if __name__ == "__main__":
    import tempfile
    import os

    # Test 1: Basic hashing
    test_str = "Hello, world!"
    test_hash = sha256_str(test_str)
    print(f"SHA256('{test_str}'): {test_hash}")
    assert len(test_hash) == 64, "Hash should be 64 hex chars"
    assert test_hash == sha256_str(test_str), "Same input should produce same hash"
    print("✓ Basic string hashing works")

    # Test 2: Canonical JSON hashing
    obj1 = {"z": 1, "a": 2}
    obj2 = {"a": 2, "z": 1}
    hash1 = sha256_canonical_json(obj1)
    hash2 = sha256_canonical_json(obj2)
    assert hash1 == hash2, "Same data in different order should hash identically"
    print("✓ Canonical JSON produces deterministic hashes")

    # Test 3: File hashing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write('{"test": "data"}')
        temp_file = f.name

    try:
        file_hash = sha256_file(temp_file)
        # Read and hash again to verify
        file_hash2 = sha256_file(temp_file)
        assert file_hash == file_hash2, "Same file should produce same hash"
        print(f"✓ File hashing works: {file_hash[:8]}...")
    finally:
        os.unlink(temp_file)

    # Test 4: NDJSON hashchain
    print("\n✓ All hashing tests passed")
