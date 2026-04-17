"""Test: Canonical JSON and hashing are deterministic and properly formatted.

Law: There is exactly one canonical serialization and one hash format.

Tests verify:
1. Determinism: same object → same bytes
2. Key ordering: {"b": 1, "a": 2} == {"a": 2, "b": 1} after canonicalization
3. Hash prefix format: sha256:<64 lowercase hex>
4. NaN rejection: allow_nan=False
5. Hash stability across types
6. Format validation
"""
import pytest
from helen_os.governance.canonical import (
    CANONICALIZATION_VERSION,
    HASH_PREFIX,
    canonical_json_bytes,
    sha256_prefixed,
    sha256_hex_from_bytes,
    is_prefixed_sha256,
    assert_prefixed_sha256,
)


def test_canonical_json_bytes_determinism():
    """Same object serialized twice must produce identical bytes."""
    obj = {"z": 3, "a": 1, "m": 2}
    bytes1 = canonical_json_bytes(obj)
    bytes2 = canonical_json_bytes(obj)

    assert bytes1 == bytes2
    assert isinstance(bytes1, bytes)


def test_canonical_json_key_order_independent():
    """Different key order in dicts must produce same canonical bytes."""
    obj1 = {"a": 1, "b": 2, "c": 3}
    obj2 = {"c": 3, "a": 1, "b": 2}
    obj3 = {"b": 2, "c": 3, "a": 1}

    bytes1 = canonical_json_bytes(obj1)
    bytes2 = canonical_json_bytes(obj2)
    bytes3 = canonical_json_bytes(obj3)

    assert bytes1 == bytes2 == bytes3


def test_canonical_json_no_whitespace():
    """Canonical bytes must have no insignificant whitespace."""
    obj = {"name": "test", "value": 42}
    canonical_bytes = canonical_json_bytes(obj)
    canonical_str = canonical_bytes.decode("utf-8")

    # Must not have spaces after separators
    assert ": " not in canonical_str
    assert ", " not in canonical_str


def test_sha256_prefixed_determinism():
    """sha256_prefixed must be stable across calls."""
    obj = {"x": 1, "y": 2}
    hash1 = sha256_prefixed(obj)
    hash2 = sha256_prefixed(obj)

    assert hash1 == hash2
    assert hash1.startswith(HASH_PREFIX)


def test_sha256_prefixed_format():
    """Hash must be in format sha256:<64 lowercase hex>."""
    obj = {"test": "data"}
    hash_val = sha256_prefixed(obj)

    assert hash_val.startswith(HASH_PREFIX)
    hex_part = hash_val[len(HASH_PREFIX):]
    assert len(hex_part) == 64
    assert all(ch in "0123456789abcdef" for ch in hex_part)


def test_sha256_prefixed_from_bytes():
    """sha256_prefixed must work with raw bytes input."""
    data = b"test data"
    hash_val = sha256_prefixed(data)

    assert hash_val.startswith(HASH_PREFIX)
    assert len(hash_val) == len(HASH_PREFIX) + 64


def test_canonical_json_rejects_nan():
    """canonical_json_bytes must reject NaN via allow_nan=False."""
    obj = {"value": float("nan")}

    with pytest.raises(ValueError):
        canonical_json_bytes(obj)


def test_canonical_json_rejects_infinity():
    """canonical_json_bytes must reject Infinity."""
    obj = {"value": float("inf")}

    with pytest.raises(ValueError):
        canonical_json_bytes(obj)


def test_different_objects_different_hashes():
    """Different objects must produce different hashes."""
    obj1 = {"a": 1}
    obj2 = {"a": 2}
    obj3 = {"b": 1}

    hash1 = sha256_prefixed(obj1)
    hash2 = sha256_prefixed(obj2)
    hash3 = sha256_prefixed(obj3)

    assert hash1 != hash2
    assert hash1 != hash3
    assert hash2 != hash3


def test_is_prefixed_sha256_valid():
    """is_prefixed_sha256 must accept valid hashes."""
    obj = {"test": 1}
    hash_val = sha256_prefixed(obj)

    assert is_prefixed_sha256(hash_val) is True


def test_is_prefixed_sha256_invalid():
    """is_prefixed_sha256 must reject invalid formats."""
    assert is_prefixed_sha256("") is False
    assert is_prefixed_sha256("sha256:") is False
    assert is_prefixed_sha256("sha256:abc") is False  # Too short
    assert is_prefixed_sha256("sha256:xyz" + "0" * 61) is False  # Invalid hex
    assert is_prefixed_sha256("sha255:" + "0" * 64) is False  # Wrong prefix
    assert is_prefixed_sha256(123) is False  # Not a string
    assert is_prefixed_sha256(None) is False


def test_assert_prefixed_sha256_valid():
    """assert_prefixed_sha256 must pass for valid hashes."""
    obj = {"test": 1}
    hash_val = sha256_prefixed(obj)

    # Should not raise
    assert_prefixed_sha256(hash_val)


def test_assert_prefixed_sha256_invalid():
    """assert_prefixed_sha256 must raise for invalid hashes."""
    with pytest.raises(ValueError):
        assert_prefixed_sha256("invalid")

    with pytest.raises(ValueError):
        assert_prefixed_sha256("sha256:abc")


def test_canonicalization_version_frozen():
    """CANONICALIZATION_VERSION must be exactly JCS_SHA256_V1."""
    assert CANONICALIZATION_VERSION == "JCS_SHA256_V1"


def test_hash_prefix_frozen():
    """HASH_PREFIX must be exactly sha256:."""
    assert HASH_PREFIX == "sha256:"
