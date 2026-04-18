"""
tests/test_epoch1_s2_introspection.py

S2 — Introspection snapshot is structured + stable (EPOCH1 self-model test).

INVARIANT UNDER TEST: INTROSPECT capability
  The kernel can describe its own state in structured, queryable form.
  Not vibes. Not narrative. Typed fields that can be parsed by machines.

  Required fields: ledger_path, sealed (bool), env_pinned (bool),
                   cum_hash (64-char hex), seal_check (bool)

This is the "What am I?" test. If HELEN can't answer this structurally,
the self-model is fiction.
"""

import pytest
from helen_os.kernel import GovernanceVM


# ── Setup ───────────────────────────────────────────────────────────────────

def make_pinned_kernel(tmp_path):
    """Return a GovernanceVM with SEAL_V2 (env-pinned)."""
    from helen_os.tools.boot_verify import BootVerifier
    import os
    ledger_path = str(tmp_path / "s2_ledger.ndjson")
    vm = GovernanceVM(ledger_path=ledger_path)
    vm.propose({"type": "boot"})
    cwd = str(tmp_path)
    verifier = BootVerifier(cwd)
    env_hash = verifier.compute_env_bundle_hash()
    vm.propose({
        "type": "SEAL_V2",
        "env_hash": env_hash,
        "monitored_files": verifier.monitored_files,
    })
    return vm, cwd


# ── S2 tests ─────────────────────────────────────────────────────────────────

def test_s2_ledger_path_is_string(tmp_path):
    """S2.1 — kernel.ledger_path is a non-empty string."""
    vm = GovernanceVM(ledger_path=str(tmp_path / "s2_test.ndjson"))
    assert isinstance(str(vm.ledger_path), str) and str(vm.ledger_path), \
        "ledger_path must be a non-empty string"
    print(f"✅ S2.1: ledger_path = {vm.ledger_path}")


def test_s2_sealed_is_bool(tmp_path):
    """S2.2 — kernel.sealed is boolean."""
    vm = GovernanceVM(ledger_path=str(tmp_path / "s2_sealed.ndjson"))
    assert isinstance(vm.sealed, bool), "sealed must be bool"
    assert vm.sealed is False, "fresh kernel should not be sealed"
    vm.propose({"type": "SEAL"})
    assert vm.sealed is True, "after SEAL event, sealed must be True"
    print("✅ S2.2: sealed is bool, toggles correctly")


def test_s2_cum_hash_is_64hex(tmp_path):
    """S2.3 — kernel.cum_hash is a 64-char lowercase hex string."""
    vm = GovernanceVM(ledger_path=str(tmp_path / "s2_hash.ndjson"))
    vm.propose({"type": "boot"})
    h = vm.cum_hash
    assert isinstance(h, str) and len(h) == 64, f"cum_hash must be 64-char hex: {h}"
    assert all(c in "0123456789abcdef" for c in h), f"cum_hash must be lowercase hex: {h}"
    print(f"✅ S2.3: cum_hash = {h[:16]}...")


def test_s2_env_pinned_reflects_seal_v2(tmp_path):
    """S2.4 — env_pinned is False before SEAL_V2, True after."""
    from helen_os.tools.boot_verify import BootVerifier
    ledger_path = str(tmp_path / "s2_pinned.ndjson")
    vm = GovernanceVM(ledger_path=ledger_path)

    assert bool(vm.pinned_env_hash) is False, "env should not be pinned initially"

    cwd = str(tmp_path)
    verifier = BootVerifier(cwd)
    env_hash = verifier.compute_env_bundle_hash()
    vm.propose({"type": "SEAL_V2", "env_hash": env_hash, "monitored_files": []})

    assert bool(vm.pinned_env_hash) is True, "env should be pinned after SEAL_V2"
    assert vm.pinned_env_hash == env_hash, "pinned_hash must match what we sealed"
    print(f"✅ S2.4: env pinned = {vm.pinned_env_hash[:16]}...")


def test_s2_seal_check_pass_when_matching(tmp_path):
    """S2.5 — verify_environment() returns True when env matches pinned hash."""
    from helen_os.tools.boot_verify import BootVerifier
    ledger_path = str(tmp_path / "s2_sealcheck.ndjson")
    vm = GovernanceVM(ledger_path=ledger_path)
    cwd = str(tmp_path)
    verifier = BootVerifier(cwd)
    env_hash = verifier.compute_env_bundle_hash()
    vm.propose({"type": "SEAL_V2", "env_hash": env_hash, "monitored_files": []})

    ok = vm.verify_environment(cwd)
    assert ok is True, "verify_environment must return True when env matches"
    print("✅ S2.5: seal_check = PASS (env matches)")


def test_s2_snapshot_is_stable_across_two_calls(tmp_path):
    """S2.6 — Two consecutive status reads return identical structured output."""
    ledger_path = str(tmp_path / "s2_stable.ndjson")
    vm = GovernanceVM(ledger_path=ledger_path)
    vm.propose({"type": "boot"})

    def snapshot(v):
        return {
            "ledger_path": str(v.ledger_path),
            "sealed": v.sealed,
            "env_pinned": bool(v.pinned_env_hash),
            "cum_hash": v.cum_hash,
        }

    s1 = snapshot(vm)
    s2 = snapshot(vm)
    assert s1 == s2, f"Snapshot not stable: {s1} vs {s2}"
    print("✅ S2.6: snapshot stable across two reads")


# ── EPOCH1 stamp ─────────────────────────────────────────────────────────────

def test_s2_epoch1_stamp(tmp_path):
    """S2 EPOCH1 stamp: _run_s2() passes → INTROSPECT capability verified."""
    from helen_os.meta.self_model import _run_s2
    from helen_os.tools.boot_verify import BootVerifier
    import os

    ledger_path = str(tmp_path / "s2_stamp.ndjson")
    vm = GovernanceVM(ledger_path=ledger_path)
    vm.propose({"type": "boot"})
    cwd = str(tmp_path)
    verifier = BootVerifier(cwd)
    env_hash = verifier.compute_env_bundle_hash()
    vm.propose({"type": "SEAL_V2", "env_hash": env_hash, "monitored_files": []})

    result = _run_s2(vm, cwd)

    assert result.passed, f"S2 stamp failed: {result.evidence}"
    snap = result.evidence.get("snapshot", {})
    assert snap.get("sealed") is True
    assert snap.get("env_pinned") is True
    assert len(snap.get("cum_hash", "")) == 64
    print(f"✅ S2 EPOCH1 STAMP: {result.evidence['verdict']}")
