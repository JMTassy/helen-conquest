"""
tests/test_town_eval_federation.py — Town Eval Federation (T0–T5, Egregores, Godmode)

Spec: "TOWN_EVAL_FEDERATION_V1 — T0–T5 servitors → Alpha/Beta/Gamma egregores
       → Godmode → FED_EVAL_V1 receipt"

Test plan:
  ── Servitor tests (TF1.x) ────────────────────────────────────────────────────
  TF1.1  T0 Integrity : fresh :memory: kernel after 1 receipt → all checks PASS
  TF1.2  T1 Manifest  : canonical artifact files all pass manifest check
  TF1.3  T2 Replay    : same 3-step payload sequence → identical cum_hash × 3
  TF1.4  T3 Partition : eval/ source files have no forbidden domain imports
  TF1.5  T4 Rollback  : sealed kernel raises PermissionError
  TF1.6  T5 Claim     : source_digest stable × 3 runs == sha256(fixture_text)

  ── Egregore tests (TF2.x) ───────────────────────────────────────────────────
  TF2.1  Alpha (Foundation)  = T0 + T1 → PASS
  TF2.2  Beta  (Simulation)  = T2 + T3 → PASS
  TF2.3  Gamma (Sovereignty) = T4 + T5 → PASS

  ── Godmode tests (TF3.x) ────────────────────────────────────────────────────
  TF3.1  Godmode PASS: all 3 egregores pass → FedEvalV1 verdict PASS
  TF3.2  FED_EVAL_V1 receipt non-trivial (64-hex cum_hash, R-prefix receipt_id)
  TF3.3  FED_EVAL_V1 Pydantic model round-trips to JSON cleanly
  TF3.4  FedEvalRunResult.summary() is non-empty string with verdict keyword

"No receipt → no federation."
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.kernel           import GovernanceVM
from helen_os.eval.servitors   import (
    run_t0_integrity, run_t1_manifest,
    run_t2_replay,    run_t3_partition,
    run_t4_rollback,  run_t5_claim,
)
from helen_os.eval.egregores   import (
    run_alpha_egregore, run_beta_egregore, run_gamma_egregore,
)
from helen_os.eval.godmode     import run_godmode
from helen_os.eval.run_fed_eval import (
    run_fed_eval_canonical,
    CANONICAL_REPLAY_SEQUENCE,
    REQUIRED_ARTIFACTS,
    DEFAULT_EVAL_PATH,
)

# ── Paths ─────────────────────────────────────────────────────────────────────

FIXTURE_PATH   = os.path.join("fixtures", "decay_dialogue_v1.txt")
ARTIFACTS_PATH = "artifacts"


# ── TF1.x — Servitor Tests ────────────────────────────────────────────────────

def test_tf1_1_t0_integrity_pass():
    """
    TF1.1 — T0 Integrity.

    A :memory: kernel seeded with 1 receipt must pass all three T0 checks:
      T0.1: verify_ledger() is True
      T0.2: cum_hash is 64 hex chars
      T0.3: cum_hash is non-trivial (not all zeros)
    """
    km = GovernanceVM(ledger_path=":memory:")
    km.propose({"type": "FED_EVAL_SEED_V1", "purpose": "T0 probe"})
    km.propose({"type": "FED_EVAL_SEED_V1", "purpose": "T0 probe 2"})

    report = run_t0_integrity(km)

    assert report.servitor_id   == "T0"
    assert report.servitor_name == "Integrity"
    assert report.verdict       == "PASS", (
        f"T0 Integrity should PASS. Checks:\n"
        + "\n".join(
            f"  {c.check_id}: {c.verdict} — {c.detail}"
            for c in report.checks
        )
    )
    assert len(report.checks) >= 3, (
        f"Expected >= 3 checks, got {len(report.checks)}"
    )
    # Every check must PASS
    for chk in report.checks:
        assert chk.verdict == "PASS", (
            f"Check {chk.check_id!r} failed: {chk.detail}"
        )


def test_tf1_2_t1_manifest_pass():
    """
    TF1.2 — T1 Manifest.

    All 5 canonical artifact files must exist, be valid JSON,
    and carry an 'artifact_sha256' field.
    """
    report = run_t1_manifest(ARTIFACTS_PATH, REQUIRED_ARTIFACTS)

    assert report.servitor_id   == "T1"
    assert report.servitor_name == "Manifest"
    assert report.verdict       != "BLOCK", (
        f"T1 Manifest must not BLOCK. Blocked checks:\n"
        + "\n".join(
            f"  {c.check_id}: {c.detail}"
            for c in report.checks
            if c.verdict == "BLOCK"
        )
    )
    assert len(report.checks) == len(REQUIRED_ARTIFACTS), (
        f"Expected {len(REQUIRED_ARTIFACTS)} checks, got {len(report.checks)}"
    )
    # No check may be BLOCK
    blocked = [c for c in report.checks if c.verdict == "BLOCK"]
    assert not blocked, (
        f"Blocked checks: {[(c.check_id, c.detail) for c in blocked]}"
    )


def test_tf1_3_t2_replay_deterministic():
    """
    TF1.3 — T2 Replay.

    The same 3-step payload sequence proposed to 3 independent :memory: kernels
    must produce identical cum_hashes (determinism invariant).
    """
    report = run_t2_replay(CANONICAL_REPLAY_SEQUENCE)

    assert report.servitor_id   == "T2"
    assert report.servitor_name == "Replay"
    assert report.verdict       == "PASS", (
        f"T2 Replay should PASS. Checks:\n"
        + "\n".join(
            f"  {c.check_id}: {c.verdict} — {c.detail}"
            for c in report.checks
        )
    )
    # Verify specific check IDs
    check_ids = {c.check_id for c in report.checks}
    assert "T2.1" in check_ids, "T2.1 (determinism) check missing"
    assert "T2.2" in check_ids, "T2.2 (non-trivial) check missing"


def test_tf1_4_t3_partition_clean():
    """
    TF1.4 — T3 Partition.

    eval/ module source files must contain no references to forbidden
    domain-specific or ARGUMENT_SIM_V1 residue module names.
    """
    report = run_t3_partition(DEFAULT_EVAL_PATH)

    assert report.servitor_id   == "T3"
    assert report.servitor_name == "Partition"
    assert report.verdict       == "PASS", (
        f"T3 Partition should PASS. Violations:\n"
        + "\n".join(
            f"  {c.check_id}: {c.detail}"
            for c in report.checks
            if c.verdict == "BLOCK"
        )
    )
    # No BLOCK checks
    assert not any(c.verdict == "BLOCK" for c in report.checks), (
        f"Partition violations: {[c.detail for c in report.checks if c.verdict == 'BLOCK']}"
    )


def test_tf1_5_t4_rollback_seals():
    """
    TF1.5 — T4 Rollback.

    After a SEAL event, the kernel must reject further proposals with
    PermissionError (the SEALED invariant cannot be rolled back).
    """
    report = run_t4_rollback()

    assert report.servitor_id   == "T4"
    assert report.servitor_name == "Rollback"
    assert report.verdict       == "PASS", (
        f"T4 Rollback should PASS. Checks:\n"
        + "\n".join(
            f"  {c.check_id}: {c.verdict} — {c.detail}"
            for c in report.checks
        )
    )
    check_ids = {c.check_id for c in report.checks}
    assert "T4.1" in check_ids, "T4.1 (PermissionError raised) check missing"
    assert "T4.2" in check_ids, "T4.2 (pre-seal hash non-trivial) check missing"


def test_tf1_6_t5_claim_stable():
    """
    TF1.6 — T5 Claim.

    run_epoch4() must produce:
      - source_digest == sha256(fixture_text), stable across 3 independent runs
      - G-set stable (same sorted node list) across 3 independent runs
    """
    report = run_t5_claim(FIXTURE_PATH)

    assert report.servitor_id   == "T5"
    assert report.servitor_name == "Claim"
    assert report.verdict       == "PASS", (
        f"T5 Claim should PASS. Checks:\n"
        + "\n".join(
            f"  {c.check_id}: {c.verdict} — {c.detail}"
            for c in report.checks
        )
    )
    check_ids = {c.check_id for c in report.checks}
    assert "T5.1" in check_ids, "T5.1 (source_digest stable) check missing"
    assert "T5.2" in check_ids, "T5.2 (G-set stable) check missing"


# ── TF2.x — Egregore Tests ───────────────────────────────────────────────────

def test_tf2_1_alpha_egregore_pass():
    """
    TF2.1 — Alpha Egregore (Foundation).

    Alpha = T0 (Integrity) + T1 (Manifest) → must not BLOCK.
    """
    km = GovernanceVM(ledger_path=":memory:")
    km.propose({"type": "FED_EVAL_SEED_V1", "purpose": "alpha probe"})

    t0    = run_t0_integrity(km)
    t1    = run_t1_manifest(ARTIFACTS_PATH, REQUIRED_ARTIFACTS)
    alpha = run_alpha_egregore(t0, t1)

    assert alpha.egregore_id   == "Alpha"
    assert alpha.egregore_name == "Foundation"
    assert alpha.verdict       != "BLOCK", (
        f"Alpha should not BLOCK. T0={t0.verdict}, T1={t1.verdict}"
    )
    assert set(alpha.servitor_ids)     == {"T0", "T1"}
    assert len(alpha.servitor_reports) == 2

    # Reports preserved correctly
    ids_in_report = {r.servitor_id for r in alpha.servitor_reports}
    assert ids_in_report == {"T0", "T1"}


def test_tf2_2_beta_egregore_pass():
    """
    TF2.2 — Beta Egregore (Simulation).

    Beta = T2 (Replay) + T3 (Partition) → must PASS.
    """
    t2   = run_t2_replay(CANONICAL_REPLAY_SEQUENCE)
    t3   = run_t3_partition(DEFAULT_EVAL_PATH)
    beta = run_beta_egregore(t2, t3)

    assert beta.egregore_id   == "Beta"
    assert beta.egregore_name == "Simulation"
    assert beta.verdict       == "PASS", (
        f"Beta should PASS. T2={t2.verdict}, T3={t3.verdict}"
    )
    assert set(beta.servitor_ids)     == {"T2", "T3"}
    assert len(beta.servitor_reports) == 2


def test_tf2_3_gamma_egregore_pass():
    """
    TF2.3 — Gamma Egregore (Sovereignty).

    Gamma = T4 (Rollback) + T5 (Claim) → must PASS.
    """
    t4    = run_t4_rollback()
    t5    = run_t5_claim(FIXTURE_PATH)
    gamma = run_gamma_egregore(t4, t5)

    assert gamma.egregore_id   == "Gamma"
    assert gamma.egregore_name == "Sovereignty"
    assert gamma.verdict       == "PASS", (
        f"Gamma should PASS. T4={t4.verdict}, T5={t5.verdict}"
    )
    assert set(gamma.servitor_ids)     == {"T4", "T5"}
    assert len(gamma.servitor_reports) == 2


# ── TF3.x — Godmode Tests ────────────────────────────────────────────────────

def test_tf3_1_godmode_pass():
    """
    TF3.1 — Godmode PASS.

    All 3 egregores pass → FedEvalV1 verdict PASS.
    Servitor count == 6 (2 per egregore × 3 egregores).
    Egregore IDs == ["Alpha", "Beta", "Gamma"].
    """
    result = run_fed_eval_canonical(
        ledger_path    = ":memory:",
        fixture_path   = FIXTURE_PATH,
        artifacts_path = ARTIFACTS_PATH,
        eval_path      = DEFAULT_EVAL_PATH,
    )

    assert result.fed_eval.verdict != "BLOCK", (
        f"Godmode must not BLOCK. "
        f"Alpha={result.alpha_report.verdict}, "
        f"Beta={result.beta_report.verdict}, "
        f"Gamma={result.gamma_report.verdict}"
    )
    assert result.fed_eval.verdict       == "PASS", (
        f"Godmode verdict should be PASS, got {result.fed_eval.verdict!r}"
    )
    assert result.fed_eval.servitor_count == 6
    assert result.fed_eval.egregore_ids  == ["Alpha", "Beta", "Gamma"]
    assert result.is_pass


def test_tf3_2_fed_eval_receipt_nontrivial():
    """
    TF3.2 — FED_EVAL_V1 receipt non-trivial.

    receipt_id starts with "R-".
    cum_hash is 64 hex chars and not all-zeros.
    """
    result = run_fed_eval_canonical(
        ledger_path    = ":memory:",
        fixture_path   = FIXTURE_PATH,
        artifacts_path = ARTIFACTS_PATH,
        eval_path      = DEFAULT_EVAL_PATH,
    )

    assert result.receipt_id.startswith("R-"), (
        f"receipt_id must start with 'R-'. Got: {result.receipt_id!r}"
    )
    assert len(result.cum_hash) == 64, (
        f"cum_hash must be 64 hex chars. Got len={len(result.cum_hash)}"
    )
    assert result.cum_hash != "0" * 64, (
        "cum_hash must be non-trivial (not all zeros)"
    )


def test_tf3_3_fed_eval_json_roundtrip():
    """
    TF3.3 — FED_EVAL_V1 JSON round-trip.

    FedEvalV1.model_dump() must serialize to valid JSON and recover correctly.
    Nested structure: 3 egregore_reports, each with 2 servitor_reports.
    """
    result = run_fed_eval_canonical(
        ledger_path    = ":memory:",
        fixture_path   = FIXTURE_PATH,
        artifacts_path = ARTIFACTS_PATH,
        eval_path      = DEFAULT_EVAL_PATH,
    )

    fed     = result.fed_eval
    payload = fed.model_dump()

    # Must be JSON-serializable
    json_str  = json.dumps(payload, sort_keys=True)
    recovered = json.loads(json_str)

    assert recovered["type"]             == "FED_EVAL_V1"
    assert recovered["verdict"]          in ("PASS", "WARN", "BLOCK")
    assert recovered["servitor_count"]   == 6
    assert len(recovered["egregore_ids"])    == 3
    assert len(recovered["egregore_reports"]) == 3

    # Each egregore has exactly 2 servitor reports
    for er in recovered["egregore_reports"]:
        assert len(er["servitor_reports"]) == 2, (
            f"Egregore {er['egregore_id']!r} should have 2 servitor_reports, "
            f"got {len(er['servitor_reports'])}"
        )

    # Counts are consistent
    total = recovered["pass_count"] + recovered["warn_count"] + recovered["block_count"]
    assert total == 6, (
        f"pass + warn + block = {total}, expected 6"
    )


def test_tf3_4_summary_non_empty():
    """
    TF3.4 — FedEvalRunResult.summary() is informative.

    summary() must be a non-empty string containing the verdict keyword.
    """
    result = run_fed_eval_canonical(
        ledger_path    = ":memory:",
        fixture_path   = FIXTURE_PATH,
        artifacts_path = ARTIFACTS_PATH,
        eval_path      = DEFAULT_EVAL_PATH,
    )

    s = result.summary()
    assert isinstance(s, str) and len(s) > 0, "summary() must be a non-empty string"
    assert result.fed_eval.verdict in s, (
        f"summary() must contain verdict {result.fed_eval.verdict!r}. Got: {s!r}"
    )
    assert "FED_EVAL_V1" in s, "summary() must mention FED_EVAL_V1"
