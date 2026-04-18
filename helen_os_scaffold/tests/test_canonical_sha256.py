"""
tests/test_canonical_sha256.py

Tests for helen_os/meta/canonical.py — Pattern A artifact_sha256 scheme.

The cryptographic pitfall being tested:
  WRONG:  artifact["artifact_sha256"] = sha256(artifact_WITH_field)
          → hash-of-preimage, not hash-of-file. Self-referential. Unverifiable.

  RIGHT (Pattern A):  artifact_sha256 = sha256(canonical_json(artifact_WITHOUT_field))
  → Anyone can: strip field, re-hash canonical JSON, compare.
  → Stable across whitespace and key orderings.

Tests:
  C1 — canonical_json is deterministic (key order doesn't matter)
  C2 — canonical_json is whitespace-stable
  C3 — embed/verify round-trip is correct
  C4 — mutating one field changes artifact_sha256 (tamper detection)
  C5 — artifact with field present → compute raises ValueError (guard)
  C6 — manifest_sha256 is root-of-roots (key order doesn't matter)
  C7 — manifest verify: right hashes pass, wrong fail
  C8 — full EPOCH_MARK_V1 pattern: build → embed → strip → verify
"""

import json
import hashlib
import pytest
from helen_os.meta.canonical import (
    canonical_json,
    canonical_sha256,
    compute_artifact_sha256,
    embed_artifact_sha256,
    strip_artifact_sha256,
    verify_artifact_sha256,
    compute_manifest_sha256,
    verify_manifest_sha256,
    ARTIFACT_SHA256_FIELD,
)


# ── C1 — canonical_json is key-order invariant ───────────────────────────────

def test_c1_canonical_json_key_order_invariant():
    """C1 — Inserting keys in different orders gives same canonical JSON."""
    a = {"z": 1, "a": 2, "m": 3}
    b = {"a": 2, "m": 3, "z": 1}
    c = {"m": 3, "z": 1, "a": 2}

    ca = canonical_json(a)
    cb = canonical_json(b)
    cc = canonical_json(c)

    assert ca == cb == cc
    # Must be sorted
    assert ca == '{"a":2,"m":3,"z":1}'
    print(f"✅ C1: canonical_json = '{ca}'")


# ── C2 — canonical_json is whitespace-stable ─────────────────────────────────

def test_c2_canonical_json_whitespace_stable():
    """C2 — json.dumps with indent=2 vs separators=(',',':') give different bytes."""
    obj = {"key": "value", "num": 42}
    canonical = canonical_json(obj)
    indented = json.dumps(obj, indent=2)

    # Different bytes (indent adds whitespace)
    assert canonical != indented
    # But canonical_sha256 is stable
    h1 = canonical_sha256(obj)
    h2 = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    assert h1 == h2

    print(f"✅ C2: canonical='{canonical}' ≠ indented (has whitespace)")


# ── C3 — embed/verify round-trip is correct ──────────────────────────────────

def test_c3_embed_verify_roundtrip():
    """C3 — embed → verify round-trip: stored hash matches re-computed hash."""
    artifact = {
        "type": "EPOCH_MARK_V1",
        "epoch": "EPOCH1",
        "verdict": "PASS",
        "data": {"tests": 94, "passed": 94},
    }

    # Embed
    result = embed_artifact_sha256(artifact)
    assert ARTIFACT_SHA256_FIELD in result
    stored = result[ARTIFACT_SHA256_FIELD]

    # Verify: strip field → re-hash → compare
    valid, reason = verify_artifact_sha256(result)
    assert valid, f"Verification failed: {reason}"

    # Manual re-check
    stripped = strip_artifact_sha256(result)
    assert ARTIFACT_SHA256_FIELD not in stripped
    manual = canonical_sha256(stripped)
    assert manual == stored

    print(f"✅ C3: embed/verify round-trip — sha256={stored[:16]}...")


# ── C4 — Mutating one field changes artifact_sha256 (tamper detection) ────────

def test_c4_tamper_detection():
    """C4 — Any field mutation changes artifact_sha256 → verify fails."""
    artifact = {
        "epoch": "EPOCH1",
        "verdict": "PASS",
        "test_count": 94,
    }
    sealed = embed_artifact_sha256(artifact)
    valid, _ = verify_artifact_sha256(sealed)
    assert valid, "Initial verify should pass"

    # Tamper: change verdict
    tampered = dict(sealed)
    tampered["verdict"] = "FAIL"

    valid_after, reason = verify_artifact_sha256(tampered)
    assert not valid_after, f"Tampered artifact should fail verification: {reason}"

    print(f"✅ C4: Tamper detected — verdict changed → sha256 mismatch")


# ── C5 — compute raises ValueError if field already present ───────────────────

def test_c5_compute_raises_if_field_present():
    """C5 — compute_artifact_sha256 raises if artifact already has the field."""
    artifact_with_field = {
        "epoch": "EPOCH1",
        ARTIFACT_SHA256_FIELD: "x" * 64,
    }

    with pytest.raises(ValueError, match=ARTIFACT_SHA256_FIELD):
        compute_artifact_sha256(artifact_with_field)

    print("✅ C5: compute raises ValueError if field already present")


# ── C6 — manifest_sha256 is key-order invariant ──────────────────────────────

def test_c6_manifest_sha256_key_order_invariant():
    """C6 — manifest_sha256 is stable regardless of file_hashes insertion order."""
    hashes_a = {
        "test_s1": "aaa" + "0" * 61,
        "test_s2": "bbb" + "0" * 61,
        "artifact": "ccc" + "0" * 61,
    }
    hashes_b = {
        "artifact": "ccc" + "0" * 61,
        "test_s1": "aaa" + "0" * 61,
        "test_s2": "bbb" + "0" * 61,
    }

    m_a = compute_manifest_sha256(hashes_a)
    m_b = compute_manifest_sha256(hashes_b)
    assert m_a == m_b

    print(f"✅ C6: manifest_sha256 key-order invariant: {m_a[:16]}...")


# ── C7 — manifest verify: right passes, wrong fails ──────────────────────────

def test_c7_manifest_verify():
    """C7 — verify_manifest_sha256 passes for correct, fails for tampered."""
    hashes = {"file_a": "a" * 64, "file_b": "b" * 64}
    correct = compute_manifest_sha256(hashes)

    valid, reason = verify_manifest_sha256(correct, hashes)
    assert valid, f"Correct manifest should pass: {reason}"

    # Tamper one hash
    tampered = dict(hashes)
    tampered["file_a"] = "f" * 64

    valid2, reason2 = verify_manifest_sha256(correct, tampered)
    assert not valid2, f"Tampered manifest should fail: {reason2}"

    print(f"✅ C7: manifest verify — correct PASS, tampered FAIL: {reason2[:50]}...")


# ── C8 — Full EPOCH_MARK_V1 pattern ──────────────────────────────────────────

def test_c8_full_epoch_mark_pattern():
    """
    C8 — Full EPOCH_MARK_V1 construction:
      1. Build mark dict (no artifact_sha256 yet)
      2. Compute manifest_sha256 over file hashes
      3. embed_artifact_sha256 (Pattern A)
      4. verify_artifact_sha256 (strip → re-hash → compare)
      5. Verify manifest_sha256 independently
    """
    # Step 1: file hashes (simulated)
    file_hashes = {
        "meta_self_model":   "a" * 64,
        "meta_wild_policy":  "b" * 64,
        "test_s1":           "c" * 64,
        "test_t1":           "d" * 64,
    }

    # Step 2: manifest
    manifest_sha = compute_manifest_sha256(file_hashes)

    # Step 3: build mark (no artifact_sha256 yet)
    mark = {
        "type": "EPOCH_MARK_V1",
        "epoch": "EPOCH1",
        "name": "SELF_MODEL_ONLINE",
        "content_hashes": file_hashes,
        "manifest_sha256": manifest_sha,
        "manifest_sha256_scheme": "SHA256(canonical_json(content_hashes))",
        "verdict": "PASS",
    }

    # Step 4: embed artifact_sha256 (Pattern A)
    mark_sealed = embed_artifact_sha256(mark)

    # Step 5: verify
    valid, reason = verify_artifact_sha256(mark_sealed)
    assert valid, f"C8 artifact verify failed: {reason}"

    # Step 6: manifest verify
    valid_m, reason_m = verify_manifest_sha256(
        mark_sealed["manifest_sha256"],
        mark_sealed["content_hashes"],
    )
    assert valid_m, f"C8 manifest verify failed: {reason_m}"

    print(f"✅ C8: Full EPOCH_MARK pattern — artifact verified, manifest verified")
    print(f"   artifact_sha256  = {mark_sealed['artifact_sha256'][:16]}...")
    print(f"   manifest_sha256  = {manifest_sha[:16]}...")


# ── C9 — The original wrong pattern is detectably wrong ──────────────────────

def test_c9_wrong_pattern_is_detectable():
    """
    C9 — The OLD (wrong) pattern is detectable by verify_artifact_sha256.

    Wrong pattern: hash(artifact WITH field) → stored in field.
    → When you strip the field and re-hash, it doesn't match.
    → verify_artifact_sha256 correctly returns False.
    """
    import json, hashlib

    artifact = {"epoch": "EPOCH1", "verdict": "PASS"}

    # Old wrong pattern: embed field, then hash the full object
    artifact_with_wrong_hash = dict(artifact)
    artifact_with_wrong_hash[ARTIFACT_SHA256_FIELD] = "placeholder"
    wrong_hash = hashlib.sha256(
        json.dumps(artifact_with_wrong_hash, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    artifact_with_wrong_hash[ARTIFACT_SHA256_FIELD] = wrong_hash

    # Verify should fail (it's a hash-of-preimage-including-field, not Pattern A)
    valid, reason = verify_artifact_sha256(artifact_with_wrong_hash)
    assert not valid, (
        "C9: Wrong pattern should fail verify_artifact_sha256 "
        "(hash includes the field itself)"
    )

    print(f"✅ C9: Wrong pattern correctly detected as invalid by verify_artifact_sha256")
    print(f"   Reason: {reason[:70]}...")
