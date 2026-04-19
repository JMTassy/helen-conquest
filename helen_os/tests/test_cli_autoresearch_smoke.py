"""Smoke test: helen_os.cli imports cleanly and autoresearch run is deterministic.

Two regressions this file locks in (2026-04-19):

1. **Dead-import drift between cli.py and helen_os.governance.ledger_validator_v1.**
   The CLI used to do `from helen_os.governance.ledger_validator_v1 import
   jcs_bytes`, but `jcs_bytes` was renamed to `canonical_json_bytes` (and not
   re-exported under the old name) in the governance module. The import
   silently broke the CLI for any caller doing `python helen_os/cli.py
   autoresearch run …`. No existing test caught it because they all bypass
   the CLI and call `autoresearch_batch_v1` directly. `test_cli_module_imports`
   below catches this exact class of drift.

2. **CLI-level determinism of the 20-epoch debug pattern.**
   `test_cli_autoresearch_20_decisions_is_byte_deterministic` builds a
   20-decision SKILL_PROMOTION_DECISION_V1 fixture (16 ADMITTED, 4 REJECTED),
   runs the CLI command twice via direct call to `cmd_autoresearch_run`, and
   asserts that `state_out.json` and `ledger_out.json` are byte-identical
   across runs. This covers the same surface as `make membrane-test` but
   anchored at the CLI boundary instead of the reducer.

Run:
    pytest helen_os/tests/test_cli_autoresearch_smoke.py -v
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]   # helen_os_v1/
SCHEMAS_DIR = REPO_ROOT / "helen_os" / "schemas"
CLI_PY_PATH = REPO_ROOT / "helen_os" / "cli.py"

DETERMINISTIC_TS = "2026-04-19T17:00:00+00:00"
DEFAULT_BATCH_ID = "smoke_test_2026-04-19"
DEFAULT_RUN_ID = "smoke_run_2026-04-19"


def _load_cli_module():
    """Load helen_os/cli.py by file path, bypassing the accidental
    `helen_os.cli` package shadow (`helen_os/cli/__init__.py` is just
    a docstring; the real CLI lives in cli.py at the same level).

    Cached on sys.modules under '_helen_cli_smoke' so repeated calls
    return the same module object."""
    cached = sys.modules.get("_helen_cli_smoke")
    if cached is not None:
        return cached
    if not CLI_PY_PATH.exists():
        raise FileNotFoundError(f"cli.py not found at {CLI_PY_PATH}")
    spec = importlib.util.spec_from_file_location("_helen_cli_smoke", CLI_PY_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_helen_cli_smoke"] = module
    spec.loader.exec_module(module)
    return module


# ─── 1. import-drift regression ──────────────────────────────────────────────

def test_cli_module_imports() -> None:
    """`helen_os/cli.py` must load without ImportError.

    Regression: a stale `from helen_os.governance.ledger_validator_v1 import
    jcs_bytes` silently broke `python helen_os/cli.py …` for an unknown
    period. `jcs_bytes` was renamed to `canonical_json_bytes` in the
    governance module and not re-exported under the old name. No existing
    test caught it because they all bypass the CLI and call
    `autoresearch_batch_v1` directly.

    This test loads cli.py from disk and asserts every public command
    function survived the import. It will fail loudly the next time
    cli.py imports drift from what the governance module exports.
    """
    cli = _load_cli_module()
    assert callable(getattr(cli, "cmd_autoresearch_run", None)), \
        "cli.cmd_autoresearch_run must be callable"
    assert callable(getattr(cli, "cmd_status", None)), \
        "cli.cmd_status must be callable"
    assert callable(getattr(cli, "now_iso", None)), \
        "cli.now_iso must be callable"


# ─── 2. fixture builders ─────────────────────────────────────────────────────

def _build_initial_state() -> dict:
    return {
        "schema_name": "SKILL_LIBRARY_STATE_V1",
        "schema_version": "1.0.0",
        "law_surface_version": "v1",
        "active_skills": {},
    }


def _build_decisions(n: int = 20) -> list[dict]:
    """Build n SKILL_PROMOTION_DECISION_V1 entries, mixed ADMITTED/REJECTED.

    Pattern: every 5th decision is REJECTED. For n=20 → 16 ADMITTED, 4 REJECTED.
    Identity hashes are derived from decision_id so they are deterministic.
    """
    decisions: list[dict] = []
    for i in range(n):
        is_admit = (i % 5) != 4
        dec_id = f"smoke_dec_{i:03d}"
        d = {
            "schema_name": "SKILL_PROMOTION_DECISION_V1",
            "schema_version": "1.0.0",
            "decision_id": dec_id,
            "skill_id": f"skill.smoke.epoch_{i:02d}",
            "candidate_version": f"1.{i}.0",
            "decision_type": "ADMITTED" if is_admit else "REJECTED",
            "reason_code": "OK_ADMITTED" if is_admit else "ERR_THRESHOLD_NOT_MET",
        }
        if is_admit:
            d["candidate_identity_hash"] = "sha256:" + hashlib.sha256(
                dec_id.encode()
            ).hexdigest()
        decisions.append(d)
    return decisions


def _build_env_manifest() -> dict:
    return {
        "reducer_version": "v1",
        "law_surface_hash": "sha256:" + ("0" * 64),
        "canonicalization": "JCS_SHA256_V1",
        "operator_intent": "SMOKE_TEST_AUTORESEARCH_CLI_2026-04-19",
    }


def _write_fixture(target_dir: Path, n_decisions: int = 20) -> tuple[Path, Path, Path]:
    """Write env / state / decisions JSON into target_dir, return their paths."""
    target_dir.mkdir(parents=True, exist_ok=True)
    env_p = target_dir / "env_manifest.json"
    state_p = target_dir / "initial_state.json"
    decisions_p = target_dir / f"decisions_{n_decisions}.json"
    env_p.write_text(json.dumps(_build_env_manifest(), indent=2))
    state_p.write_text(json.dumps(_build_initial_state(), indent=2))
    decisions_p.write_text(json.dumps(_build_decisions(n_decisions), indent=2))
    return env_p, state_p, decisions_p


def _make_args(*, env_p: Path, state_p: Path, decisions_p: Path, out_dir: Path,
               batch_id: str = DEFAULT_BATCH_ID, run_id: str = DEFAULT_RUN_ID,
               proof_runs: int = 20) -> argparse.Namespace:
    """Build a Namespace matching cli.cmd_autoresearch_run's arg surface."""
    return argparse.Namespace(
        env=str(env_p),
        state=str(state_p),
        decisions=str(decisions_p),
        ledger=None,
        out=str(out_dir),
        max_items=100,
        batch_id=batch_id,
        run_id=run_id,
        deterministic=DETERMINISTIC_TS,
        schemas=str(SCHEMAS_DIR),
        proof_runs=proof_runs,
        quiet=True,
        verbose=False,
    )


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ─── 3. CLI determinism end-to-end ───────────────────────────────────────────

def test_cli_autoresearch_20_decisions_is_byte_deterministic(tmp_path: Path) -> None:
    """20-decision batch via cmd_autoresearch_run produces byte-identical
    state_out.json and ledger_out.json across two runs with same inputs.

    This is the CLI-level analogue of test_autoresearch_batch_is_deterministic;
    it specifically covers the "20 epochs in autonomy AUTORESEARCH for debug"
    workflow.
    """
    cmd_autoresearch_run = _load_cli_module().cmd_autoresearch_run

    fixture_dir = tmp_path / "fixture"
    env_p, state_p, decisions_p = _write_fixture(fixture_dir, n_decisions=20)

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"

    rc1 = cmd_autoresearch_run(_make_args(
        env_p=env_p, state_p=state_p, decisions_p=decisions_p, out_dir=out1
    ))
    rc2 = cmd_autoresearch_run(_make_args(
        env_p=env_p, state_p=state_p, decisions_p=decisions_p, out_dir=out2
    ))
    assert rc1 == 0, f"run1 exited non-zero: {rc1}"
    assert rc2 == 0, f"run2 exited non-zero: {rc2}"

    # All six expected artifact files exist in both runs
    expected = ["ledger_out.json", "state_out.json", "receipt.json",
                "artifact.json", "hal_review.json", "proof.json"]
    for fn in expected:
        assert (out1 / fn).exists(), f"missing {fn} in run1"
        assert (out2 / fn).exists(), f"missing {fn} in run2"

    # State + ledger are byte-identical across replays
    state_h1 = _sha256_file(out1 / "state_out.json")
    state_h2 = _sha256_file(out2 / "state_out.json")
    ledger_h1 = _sha256_file(out1 / "ledger_out.json")
    ledger_h2 = _sha256_file(out2 / "ledger_out.json")

    assert state_h1 == state_h2, (
        "state_out.json diverged across replays — membrane non-deterministic.\n"
        f"  run1: {state_h1}\n  run2: {state_h2}"
    )
    assert ledger_h1 == ledger_h2, (
        "ledger_out.json diverged across replays — membrane non-deterministic.\n"
        f"  run1: {ledger_h1}\n  run2: {ledger_h2}"
    )


def test_cli_autoresearch_receipt_and_proof_shape(tmp_path: Path) -> None:
    """Single-run smoke check: receipt + proof artifacts have the expected
    structural fields and the determinism certificate reports proof_runs=20."""
    cmd_autoresearch_run = _load_cli_module().cmd_autoresearch_run

    fixture_dir = tmp_path / "fixture"
    env_p, state_p, decisions_p = _write_fixture(fixture_dir, n_decisions=20)

    out_dir = tmp_path / "run"
    rc = cmd_autoresearch_run(_make_args(
        env_p=env_p, state_p=state_p, decisions_p=decisions_p, out_dir=out_dir,
        proof_runs=20,
    ))
    assert rc == 0

    receipt = json.loads((out_dir / "receipt.json").read_text())
    proof = json.loads((out_dir / "proof.json").read_text())

    # Receipt: bookkeeping fields
    assert receipt.get("batch_id") == DEFAULT_BATCH_ID
    assert receipt.get("run_id") == DEFAULT_RUN_ID
    assert receipt.get("decisions_processed") == 20
    assert receipt.get("decisions_appended") == 20
    assert receipt.get("initial_state_hash", "").startswith("sha256:")
    assert receipt.get("final_state_hash", "").startswith("sha256:")

    # Proof: determinism certificate honors --proof-runs
    dc = proof.get("determinism_certificate", {})
    assert dc.get("runs") == 20
    assert dc.get("all_decisions_identical") is True
    assert dc.get("all_states_identical") is True

    # Replay proof: corruption_check passes
    rp = proof.get("ledger_replay_proof", {})
    assert rp.get("corruption_check") == "PASS"
    assert rp.get("via_ledger_entries") == 20


def test_cli_autoresearch_decision_split(tmp_path: Path) -> None:
    """Verify the 20-decision fixture splits as expected (16 ADMITTED + 4 REJECTED)
    and that the membrane appends both types — the REJECTED entries must still
    appear in the ledger as REJECTED (the membrane records them; they just don't
    mutate active_skills)."""
    cmd_autoresearch_run = _load_cli_module().cmd_autoresearch_run

    fixture_dir = tmp_path / "fixture"
    env_p, state_p, decisions_p = _write_fixture(fixture_dir, n_decisions=20)

    out_dir = tmp_path / "run"
    rc = cmd_autoresearch_run(_make_args(
        env_p=env_p, state_p=state_p, decisions_p=decisions_p, out_dir=out_dir,
    ))
    assert rc == 0

    ledger = json.loads((out_dir / "ledger_out.json").read_text())
    entries = ledger.get("entries", [])
    assert len(entries) == 20

    types = [e["decision"]["decision_type"] for e in entries]
    assert types.count("ADMITTED") == 16
    assert types.count("REJECTED") == 4

    # entry_index is monotonic from 0
    for i, e in enumerate(entries):
        assert e["entry_index"] == i, f"entry_index gap at position {i}"
