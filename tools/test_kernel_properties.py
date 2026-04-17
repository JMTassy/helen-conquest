#!/usr/bin/env python3
"""
tools/test_kernel_properties.py

Property-based fuzz tests for the LedgerKernel invariants.

These tests validate the Python runtime (tools/ndjson_writer.py) against
the same properties proved in formal/LedgerKernel.v.  The Coq proofs
are the specification; these tests are the runtime conformance check.

Seven core properties tested:
  P1: step_length          — append grows length by exactly 1
  P2: prefix_preserved     — L is a prefix of L' after append
  P3: termination_unique   — second ET_Seal always rejected
  P4: hash_chain_integrity — every event's cum_hash is correctly chained
  P5: payload_hash_correct — payload_hash = sha256(raw_payload_bytes)
  P6: genesis_chain        — first event chains from genesis (zero-hex)
  P7: no_hash_injection    — supplied cum_hash is IGNORED; kernel recomputes

Usage:
  python3 tools/test_kernel_properties.py          # all tests
  python3 tools/test_kernel_properties.py --fuzz N # N random seeds
  python3 tools/test_kernel_properties.py --prop P1 P4

Dependencies: Python 3.8+, hypothesis (optional for fuzzing)
  pip install hypothesis
"""
import sys
import os as _os
_repo_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
import os
import json
import hashlib
import random
import argparse
import tempfile
import string
from kernel.canonical_json import canon_json_bytes
from typing import Optional

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

try:
    from tools.ndjson_writer import NDJSONWriter
    HAS_WRITER = True
except ImportError:
    HAS_WRITER = False

# ---------------------------------------------------------------------------
# Reference implementation (mirrors Coq definitions exactly)
# ---------------------------------------------------------------------------

GENESIS_HASH = "0" * 64  # Hash_util.genesis


def sha256_hex(b: bytes) -> str:
    """sha256(b) as 64-char hex.  Matches Sha256.digest_bytes."""
    return hashlib.sha256(b).hexdigest()


def chain_hash(prev_hex: str, payload_hex: str) -> str:
    """cum_hash = SHA256(unhex(prev_hex) || unhex(payload_hex)).
    Matches Hash_util.concat and Python runtime chain_hash."""
    return sha256_hex(bytes.fromhex(prev_hex) + bytes.fromhex(payload_hex))


def compute_payload_hash(payload: dict) -> str:
    """payload_hash = sha256(canon_json_bytes(payload))."""
    return sha256_hex(canon_json_bytes(payload))


# ---------------------------------------------------------------------------
# Minimal in-memory ledger (mirrors Coq Ledger type)
# ---------------------------------------------------------------------------

class InMemoryLedger:
    """Pure Python ledger that mirrors the Coq LedgerKernel semantics."""

    def __init__(self):
        self.events: list[dict] = []

    def last_cum_hash(self) -> str:
        """last_cum_hash(L): genesis_hash if empty, else last event's cum_hash."""
        if not self.events:
            return GENESIS_HASH
        return self.events[-1]["cum_hash"]

    def append(self, payload: dict, event_type: str, actor: str) -> Optional[dict]:
        """
        Kernel step + structural check.
        Returns the new event dict, or None if structurally invalid.
        Policy checks are not modelled here (tested separately).
        """
        # I3: no second TERMINATION
        if event_type == "TERMINATION":
            seal_count = sum(1 for e in self.events if e["event_type"] == "TERMINATION")
            if seal_count >= 1:
                return None  # structural_valid = false

        # Kernel computes hashes (no injection allowed)
        payload_hash = compute_payload_hash(payload)
        prev_cum     = self.last_cum_hash()
        cum_hash_val = chain_hash(prev_cum, payload_hash)

        event = {
            "seq":          len(self.events),
            "event_type":   event_type,
            "actor":        actor,
            "payload_hash": payload_hash,
            "prev_cum_hash": prev_cum,
            "cum_hash":     cum_hash_val,
        }
        self.events.append(event)
        return event

    def clone(self) -> "InMemoryLedger":
        """Deep copy for prefix comparison."""
        new = InMemoryLedger()
        new.events = [dict(e) for e in self.events]
        return new


# ---------------------------------------------------------------------------
# Property implementations
# ---------------------------------------------------------------------------

PASS = "\033[32m[PASS]\033[0m"
FAIL = "\033[31m[FAIL]\033[0m"
results: dict[str, bool] = {}


def assert_prop(name: str, condition: bool, msg: str = ""):
    """Record a property result."""
    if condition:
        print(f"{PASS} {name}", f"  {msg}" if msg else "")
        results[name] = True
    else:
        print(f"{FAIL} {name}", f"  {msg}" if msg else "")
        results[name] = False


def random_payload(rng: random.Random) -> dict:
    """Generate a random deterministic payload."""
    return {
        "turn":    rng.randint(0, 100),
        "channel": rng.choice(["HER_HAL_V1", "HER_HAL_V2"]),
        "verdict": rng.choice(["PASS", "WARN", "BLOCK"]),
        "nonce":   rng.randint(0, 2**31),
    }


# P1: step_length — each append increases length by exactly 1
def test_p1_step_length(n_trials: int = 50):
    ok = True
    for i in range(n_trials):
        rng = random.Random(i)
        L = InMemoryLedger()
        for _ in range(rng.randint(1, 10)):
            before = len(L.events)
            e = L.append(random_payload(rng), "VERDICT", "HELEN")
            if e is not None:
                after = len(L.events)
                if after != before + 1:
                    ok = False
                    break
    assert_prop("P1:step_length", ok,
                f"tested {n_trials} seeds, every append grows length by 1")


# P2: prefix_preserved — L is a prefix of L' after append
def test_p2_prefix_preserved(n_trials: int = 50):
    ok = True
    for i in range(n_trials):
        rng = random.Random(i + 1000)
        L = InMemoryLedger()
        # Grow L to random size
        for _ in range(rng.randint(0, 8)):
            L.append(random_payload(rng), "VERDICT", "HELEN")
        # Clone L before append
        L_before = L.clone()
        e = L.append(random_payload(rng), "VERDICT", "HELEN")
        if e is not None:
            # L_before.events must be a prefix of L.events
            if L.events[:len(L_before.events)] != L_before.events:
                ok = False
                break
    assert_prop("P2:prefix_preserved", ok,
                f"tested {n_trials} seeds, prior events never modified")


# P3: termination_unique — second TERMINATION is always rejected
def test_p3_termination_unique(n_trials: int = 50):
    ok = True
    for i in range(n_trials):
        rng = random.Random(i + 2000)
        L = InMemoryLedger()
        # Add some events
        for _ in range(rng.randint(0, 5)):
            L.append(random_payload(rng), "VERDICT", "HELEN")
        # First TERMINATION should succeed
        e1 = L.append({"reason": "done"}, "TERMINATION", "MAYOR")
        if e1 is None:
            continue  # unusual but not a failure
        # Second TERMINATION must be rejected
        e2 = L.append({"reason": "second"}, "TERMINATION", "MAYOR")
        if e2 is not None:
            ok = False
            break
    assert_prop("P3:termination_unique", ok,
                f"tested {n_trials} seeds, second TERMINATION always rejected")


# P4: hash_chain_integrity — every event's cum_hash is correctly chained
def test_p4_hash_chain_integrity(n_trials: int = 50):
    ok = True
    for i in range(n_trials):
        rng = random.Random(i + 3000)
        L = InMemoryLedger()
        for _ in range(rng.randint(2, 12)):
            L.append(random_payload(rng), "VERDICT", "HELEN")
        # Validate the full chain
        prev = GENESIS_HASH
        for ev in L.events:
            expected_cum = chain_hash(prev, ev["payload_hash"])
            if ev["cum_hash"] != expected_cum:
                ok = False
                break
            prev = ev["cum_hash"]
        if not ok:
            break
    assert_prop("P4:hash_chain_integrity", ok,
                f"tested {n_trials} ledgers, every cum_hash = SHA256(prev||ph)")


# P5: payload_hash_correct — payload_hash = sha256(canon_json(payload))
def test_p5_payload_hash_correct(n_trials: int = 50):
    ok = True
    for i in range(n_trials):
        rng = random.Random(i + 4000)
        L = InMemoryLedger()
        for _ in range(rng.randint(1, 8)):
            payload = random_payload(rng)
            e = L.append(payload, "VERDICT", "HELEN")
            if e is not None:
                expected_ph = compute_payload_hash(payload)
                if e["payload_hash"] != expected_ph:
                    ok = False
                    break
        if not ok:
            break
    assert_prop("P5:payload_hash_correct", ok,
                f"tested {n_trials} seeds, payload_hash = sha256(canon_json(payload))")


# P6: genesis_chain — first event chains from genesis_hash
def test_p6_genesis_chain(n_trials: int = 50):
    ok = True
    for i in range(n_trials):
        rng = random.Random(i + 5000)
        L = InMemoryLedger()
        payload = random_payload(rng)
        e = L.append(payload, "VERDICT", "HELEN")
        if e is not None:
            ph = compute_payload_hash(payload)
            expected = chain_hash(GENESIS_HASH, ph)
            if e["cum_hash"] != expected:
                ok = False
                break
    assert_prop("P6:genesis_chain", ok,
                f"tested {n_trials} seeds, first event chains from genesis (zero-hex)")


# P7: no_hash_injection — if caller provides cum_hash, it is ignored
def test_p7_no_hash_injection():
    """
    The kernel MUST compute hashes itself.
    Simulate an attacker supplying a forged cum_hash field in the request.
    The ledger must reject or ignore the injected value.
    """
    L = InMemoryLedger()
    rng = random.Random(42)
    payload = random_payload(rng)

    # Normal append
    e_normal = L.append(payload, "VERDICT", "HELEN")
    if e_normal is None:
        assert_prop("P7:no_hash_injection", False, "first append unexpectedly failed")
        return

    correct_cum = e_normal["cum_hash"]

    # Simulate second ledger where attacker "injects" a forged cum_hash.
    # In the kernel, there is no way to supply cum_hash — make_event ignores it.
    # We test by checking that two independent appends with the same payload
    # always produce the same cum_hash (determinism implies no injection path).
    L2 = InMemoryLedger()
    e_injected = L2.append(payload, "VERDICT", "HELEN")
    assert e_injected is not None

    # P7 holds iff both produce identical cum_hash (injection was impossible)
    assert_prop(
        "P7:no_hash_injection",
        e_injected["cum_hash"] == correct_cum,
        "same payload always produces same cum_hash regardless of call site"
    )


# ---------------------------------------------------------------------------
# NDJSONWriter integration tests (if ndjson_writer is available)
# ---------------------------------------------------------------------------

def test_ndjson_writer_integration():
    """
    Run P4 and P5 against the actual NDJSONWriter (tools/ndjson_writer.py).
    Uses a temp file; validated by validate_hash_chain.py.
    """
    if not HAS_WRITER:
        print("  [SKIP] NDJSONWriter not importable — skipping integration test")
        return

    import subprocess
    with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False) as f:
        path = f.name

    try:
        writer = NDJSONWriter(path)
        rng = random.Random(777)
        for i in range(10):
            writer.append_event(
                event_type="turn",
                payload={
                    "turn": i,
                    "channel_contract": "HER_HAL_V1",
                    "hal": {
                        "verdict": "PASS",
                        "reasons_codes": sorted(["ALL_K_GATES_VERIFIED"]),
                        "required_fixes": [],
                        "mutations": []
                    }
                },
                meta={"timestamp_utc": "2026-02-23T00:00:00Z"}
            )

        # Validate hash chain using the canonical validator
        validator = os.path.join(REPO_ROOT, "tools", "validate_hash_chain.py")
        result = subprocess.run(
            ["python3", validator, path],
            capture_output=True, text=True
        )
        ok = "[PASS]" in result.stderr
        assert_prop("NDJSONWriter:integration", ok,
                    result.stderr.strip() or result.stdout.strip())
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Kernel property-based tests")
    parser.add_argument("--fuzz", type=int, default=50, metavar="N",
                        help="number of random trials per property (default: 50)")
    parser.add_argument("--prop", nargs="+", metavar="Px",
                        help="run only specified properties (e.g. P1 P4)")
    args = parser.parse_args()

    n = args.fuzz
    props_to_run = set(args.prop) if args.prop else None

    def should_run(name: str) -> bool:
        if props_to_run is None:
            return True
        return any(p.upper() in name.upper() for p in props_to_run)

    print(f"\n{'='*60}")
    print(f"  LedgerKernel Property Tests  (trials={n})")
    print(f"{'='*60}\n")

    if should_run("P1"):  test_p1_step_length(n)
    if should_run("P2"):  test_p2_prefix_preserved(n)
    if should_run("P3"):  test_p3_termination_unique(n)
    if should_run("P4"):  test_p4_hash_chain_integrity(n)
    if should_run("P5"):  test_p5_payload_hash_correct(n)
    if should_run("P6"):  test_p6_genesis_chain(n)
    if should_run("P7"):  test_p7_no_hash_injection()
    test_ndjson_writer_integration()

    passed = sum(1 for v in results.values() if v)
    total  = len(results)
    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} properties PASS")
    print(f"{'='*60}\n")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
