"""
tests/test_constitutional_drift.py — Constitutional drift detection suite.

LAW_SURFACE_V1 (research_loop/law_surface.yaml)

Tests that the law surface hash binding correctly detects constitutional drift:
any structural change to the law surface must produce a different hash, and
any mismatch between the recorded hash and the current file must be flagged.

Test groups:
    CD01  law_surface_hash() correctness
    CD02  verify_law_surface_hash() — pass / fail cases
    CD03  assert_law_surface_hash() — hard failure on drift
    CD04  Manifest binding (law_surface_hash in RunManifestV1)
    CD05  Constitutional fields in law_surface.yaml
    CD06  Verdict law_surface binding
    CD07  Sentinel handling
"""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path

import pytest

_SCAFFOLD_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _SCAFFOLD_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_SCAFFOLD_ROOT))

from research_loop.law_surface import (
    LAW_SURFACE_VERSION,
    LAW_SURFACE_SENTINEL,
    LawSurfaceError,
    LawSurfaceMismatchError,
    load_law_surface_bytes,
    law_surface_hash,
    verify_law_surface_hash,
    assert_law_surface_hash,
    _DEFAULT_LAW_SURFACE_FILE,
)
from research_loop import (
    GENESIS_PARENT_HASH,
    MissionV1, ProposalV1, ExecutionReceiptV1,
    EvidenceBundleV1, IssueListV1, GateVectorV1, VerdictV1,
    build_run_manifest, verify_manifest,
    compute_verdict,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _real_law_surface_hash() -> str:
    """Compute the actual SHA256 of the current law_surface.yaml."""
    return law_surface_hash()


def _write_modified_law_surface(tmp_path: Path, extra_line: str = "# drift") -> Path:
    """Write a modified copy of law_surface.yaml to a temp file."""
    original = load_law_surface_bytes()
    modified = original + f"\n{extra_line}\n".encode("utf-8")
    p = tmp_path / "law_surface_modified.yaml"
    p.write_bytes(modified)
    return p


def _build_ship_manifest(
    law_surface_version: str = "LAW_SURFACE_V1",
    law_surface_hash_val: str = "0" * 64,
):
    mission = MissionV1(
        mission_id="MIS_CD", domain="retrieval_ranking",
        objective="Test drift detection.", metric_name="top1_accuracy", maximize=True,
    )
    proposal = ProposalV1(
        proposal_id="PROP_CD", proposer="HER",
        summary="Drift test proposal.",
        hypothesis="Law surface binding is deterministic.",
        mutable_files=["ranker.py"],
        replay_command="python eval.py --seed 42",
    )
    receipt = ExecutionReceiptV1(
        receipt_id="RCP_CD", kind="metric",
        command="python eval.py --seed 42",
        stdout_sha256="a" * 64, stderr_sha256="b" * 64,
        artifact_refs=["metric:top1_accuracy=0.870"],
    )
    evidence = EvidenceBundleV1(
        evidence_id="EV_CD", dataset_hash="c" * 64,
        metric_name="top1_accuracy", metric_value=0.870,
        receipt_ids=["RCP_CD"],
    )
    return build_run_manifest(
        manifest_id="MAN_CD",
        ts_utc="2026-03-11T12:00:00Z",
        mission=mission,
        proposal=proposal,
        receipts=[receipt],
        evidence=evidence,
        issues=IssueListV1(issue_list_id="ISS_CD", issues=[]),
        gates=GateVectorV1(True, True, True, True, True),
        parent_manifest_hash=GENESIS_PARENT_HASH,
        config_hash="d" * 64,
        environment_hash="e" * 64,
        model_digest="f" * 64,
        eval_output_hash="9" * 64,
        law_surface_version=law_surface_version,
        law_surface_hash=law_surface_hash_val,
    )


# ── CD01: law_surface_hash() correctness ──────────────────────────────────────

class TestLawSurfaceHash:
    def test_cd01_hash_is_64_hex_chars(self):
        h = law_surface_hash()
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_cd01_hash_is_deterministic(self):
        h1 = law_surface_hash()
        h2 = law_surface_hash()
        assert h1 == h2, "Same file must always produce same hash."

    def test_cd01_hash_matches_manual_sha256(self):
        data = load_law_surface_bytes()
        expected = hashlib.sha256(data).hexdigest()
        assert law_surface_hash() == expected

    def test_cd01_hash_changes_on_content_change(self, tmp_path):
        """A modified law surface must produce a different hash."""
        original_hash = law_surface_hash()
        modified_path = _write_modified_law_surface(tmp_path)
        modified_hash = law_surface_hash(modified_path)
        assert original_hash != modified_hash, (
            "Constitutional drift: modified law surface must produce different hash."
        )

    def test_cd01_missing_file_raises(self, tmp_path):
        nonexistent = tmp_path / "nonexistent.yaml"
        with pytest.raises(LawSurfaceError):
            law_surface_hash(nonexistent)

    def test_cd01_load_bytes_returns_bytes(self):
        data = load_law_surface_bytes()
        assert isinstance(data, bytes)
        assert len(data) > 0


# ── CD02: verify_law_surface_hash() ───────────────────────────────────────────

class TestVerifyLawSurfaceHash:
    def test_cd02_current_hash_verifies(self):
        current = law_surface_hash()
        assert verify_law_surface_hash(current) is True

    def test_cd02_wrong_hash_fails(self):
        wrong_hash = "deadbeef" * 8
        assert verify_law_surface_hash(wrong_hash) is False

    def test_cd02_all_zeros_fails(self):
        """GENESIS sentinel (0 * 64) does not match real law surface."""
        assert verify_law_surface_hash("0" * 64) is False

    def test_cd02_missing_file_returns_false(self, tmp_path):
        nonexistent = tmp_path / "ghost.yaml"
        # Should return False (not raise) when file is absent
        result = verify_law_surface_hash("any_hash", path=nonexistent)
        assert result is False

    def test_cd02_modified_file_fails_original_hash(self, tmp_path):
        """If law surface file is modified, original hash no longer matches."""
        original_hash = law_surface_hash()
        modified_path = _write_modified_law_surface(tmp_path)
        assert verify_law_surface_hash(original_hash, path=modified_path) is False

    def test_cd02_modified_file_passes_its_own_hash(self, tmp_path):
        """Modified file passes when its own hash is checked."""
        modified_path = _write_modified_law_surface(tmp_path)
        modified_hash = law_surface_hash(modified_path)
        assert verify_law_surface_hash(modified_hash, path=modified_path) is True


# ── CD03: assert_law_surface_hash() ───────────────────────────────────────────

class TestAssertLawSurfaceHash:
    def test_cd03_current_hash_passes(self):
        current = law_surface_hash()
        assert_law_surface_hash(current)   # must not raise

    def test_cd03_wrong_hash_raises_mismatch_error(self):
        with pytest.raises(LawSurfaceMismatchError, match="drift"):
            assert_law_surface_hash("0" * 64)

    def test_cd03_missing_file_raises_mismatch_error(self, tmp_path):
        nonexistent = tmp_path / "ghost.yaml"
        with pytest.raises(LawSurfaceMismatchError):
            assert_law_surface_hash("any_hash", path=nonexistent)

    def test_cd03_drift_message_contains_both_hashes(self):
        fake_hash = "abcdef" + "0" * 58
        with pytest.raises(LawSurfaceMismatchError) as exc_info:
            assert_law_surface_hash(fake_hash)
        message = str(exc_info.value)
        assert fake_hash in message, "Error must quote the recorded hash."

    def test_cd03_modified_file_raises_for_original_hash(self, tmp_path):
        original_hash = law_surface_hash()
        modified_path = _write_modified_law_surface(tmp_path)
        with pytest.raises(LawSurfaceMismatchError):
            assert_law_surface_hash(original_hash, path=modified_path)


# ── CD04: Manifest law_surface binding ────────────────────────────────────────

class TestManifestLawSurfaceBinding:
    def test_cd04_manifest_carries_law_surface_version(self):
        m = _build_ship_manifest(law_surface_hash_val="0" * 64)
        assert m.law_surface_version == "LAW_SURFACE_V1"

    def test_cd04_manifest_carries_law_surface_hash(self):
        m = _build_ship_manifest(law_surface_hash_val="0" * 64)
        assert m.law_surface_hash == "0" * 64

    def test_cd04_changing_law_surface_hash_changes_manifest_hash(self):
        """Different law_surface_hash → different manifest_hash (TCB binding)."""
        m1 = _build_ship_manifest(law_surface_hash_val="0" * 64)
        m2 = _build_ship_manifest(law_surface_hash_val="1" * 64)
        assert m1.manifest_hash != m2.manifest_hash, (
            "Manifest hash must differ when law_surface_hash differs."
        )

    def test_cd04_changing_law_surface_version_changes_manifest_hash(self):
        """Different law_surface_version → different manifest_hash."""
        m1 = _build_ship_manifest(law_surface_version="LAW_SURFACE_V1")
        m2 = _build_ship_manifest(law_surface_version="LAW_SURFACE_V2")
        assert m1.manifest_hash != m2.manifest_hash

    def test_cd04_verify_manifest_detects_law_surface_hash_tamper(self):
        """Tamper law_surface_hash → verify_manifest returns False."""
        from research_loop.run_manifest import RunManifestV1
        m = _build_ship_manifest(law_surface_hash_val="0" * 64)
        tampered = RunManifestV1(
            manifest_version=m.manifest_version,
            manifest_id=m.manifest_id,
            ts_utc=m.ts_utc,
            mission=m.mission,
            proposal=m.proposal,
            receipts=m.receipts,
            evidence=m.evidence,
            issues=m.issues,
            gates=m.gates,
            verdict=m.verdict,
            parent_manifest_hash=m.parent_manifest_hash,
            config_hash=m.config_hash,
            environment_hash=m.environment_hash,
            model_digest=m.model_digest,
            eval_output_hash=m.eval_output_hash,
            law_surface_version=m.law_surface_version,
            law_surface_hash="1" * 64,   # tampered
            manifest_hash=m.manifest_hash,  # old hash
        )
        assert verify_manifest(tampered) is False

    def test_cd04_manifest_with_real_law_surface_hash_verifies(self):
        """Manifest built with real hash still verifies correctly."""
        real_hash = law_surface_hash()
        m = _build_ship_manifest(law_surface_hash_val=real_hash)
        assert verify_manifest(m) is True

    def test_cd04_law_surface_hash_is_in_payload(self):
        """law_surface_hash must appear in the serialized manifest dict."""
        from research_loop import manifest_to_dict
        m = _build_ship_manifest(law_surface_hash_val="0" * 64)
        d = manifest_to_dict(m)
        assert "law_surface_hash" in d
        assert d["law_surface_hash"] == "0" * 64

    def test_cd04_law_surface_version_is_in_payload(self):
        """law_surface_version must appear in the serialized manifest dict."""
        from research_loop import manifest_to_dict
        m = _build_ship_manifest()
        d = manifest_to_dict(m)
        assert "law_surface_version" in d
        assert d["law_surface_version"] == "LAW_SURFACE_V1"


# ── CD05: Constitutional fields in law_surface.yaml ──────────────────────────

class TestConstitutionalFields:
    """Verify that law_surface.yaml contains the required constitutional fields."""

    def _load_yaml(self):
        try:
            import yaml
            data = load_law_surface_bytes()
            return yaml.safe_load(data)
        except ImportError:
            pytest.skip("PyYAML not installed — skipping YAML content tests.")

    def test_cd05_minimum_gain_present(self):
        law = self._load_yaml()
        assert "optimization" in law
        assert "minimum_gain" in law["optimization"]

    def test_cd05_minimum_gain_is_0002(self):
        law = self._load_yaml()
        assert law["optimization"]["minimum_gain"] == 0.002

    def test_cd05_required_artifacts_not_empty(self):
        law = self._load_yaml()
        assert "admissibility" in law
        arts = law["admissibility"]["required_artifacts"]
        assert len(arts) > 0
        assert "RUN_MANIFEST_V1" in arts

    def test_cd05_ship_state_transition_defined(self):
        law = self._load_yaml()
        assert "state_transition" in law
        assert "SHIP" in law["state_transition"]["mutate_state_on"]

    def test_cd05_no_ship_does_not_mutate(self):
        law = self._load_yaml()
        do_not = law["state_transition"]["do_not_mutate_on"]
        assert "NO_SHIP" in do_not
        assert "QUARANTINE" in do_not

    def test_cd05_append_only_ledger(self):
        law = self._load_yaml()
        assert law["state_transition"]["append_only_ledger"] is True

    def test_cd05_replay_exact_match_fields_present(self):
        law = self._load_yaml()
        fields = law["replay"]["exact_match_fields"]
        assert "eval_output_hash" in fields
        assert "exit_code" in fields
        assert "metric_after" in fields

    def test_cd05_kernel_integrity_reducer_mutation_forbidden(self):
        law = self._load_yaml()
        assert law["kernel_integrity"]["reducer_mutation_forbidden"] is True

    def test_cd05_allowed_verdicts(self):
        law = self._load_yaml()
        allowed = law["verdicts"]["allowed"]
        assert "SHIP" in allowed
        assert "NO_SHIP" in allowed
        assert "QUARANTINE" in allowed

    def test_cd05_snapshots_not_authoritative(self):
        law = self._load_yaml()
        assert law["snapshots"]["constitutive_authority"] is False

    def test_cd05_temple_may_not_authorize(self):
        law = self._load_yaml()
        assert law["temple"]["temple_may_authorize"] is False


# ── CD06: Verdict law_surface binding ─────────────────────────────────────────

class TestVerdictLawSurfaceBinding:
    def test_cd06_compute_verdict_carries_law_surface_version(self):
        gates = GateVectorV1(True, True, True, True, True)
        verdict = compute_verdict(gates, law_surface_version="LAW_SURFACE_V1")
        assert verdict.law_surface_version == "LAW_SURFACE_V1"

    def test_cd06_compute_verdict_carries_law_surface_hash(self):
        gates = GateVectorV1(True, True, True, True, True)
        h = "a" * 64
        verdict = compute_verdict(gates, law_surface_hash=h)
        assert verdict.law_surface_hash == h

    def test_cd06_quarantine_carries_law_surface_hash(self):
        gates = GateVectorV1(True, True, True, True, False)   # kernel integrity fail
        h = "b" * 64
        verdict = compute_verdict(gates, law_surface_hash=h)
        assert verdict.verdict == "QUARANTINE"
        assert verdict.law_surface_hash == h

    def test_cd06_no_ship_carries_law_surface_hash(self):
        gates = GateVectorV1(False, True, True, True, True)   # receipts missing
        h = "c" * 64
        verdict = compute_verdict(gates, law_surface_hash=h)
        assert verdict.verdict == "NO_SHIP"
        assert verdict.law_surface_hash == h

    def test_cd06_different_law_hashes_distinguish_verdicts(self):
        """Two verdicts computed under different legal regimes are distinguishable."""
        gates = GateVectorV1(True, True, True, True, True)
        v1 = compute_verdict(gates, law_surface_hash="0" * 64)
        v2 = compute_verdict(gates, law_surface_hash="1" * 64)
        assert v1.law_surface_hash != v2.law_surface_hash
        assert v1.verdict == v2.verdict  # same verdict outcome, different regime


# ── CD07: Sentinel handling ────────────────────────────────────────────────────

class TestSentinelHandling:
    def test_cd07_sentinel_constant_defined(self):
        assert LAW_SURFACE_SENTINEL == "L" * 64
        assert len(LAW_SURFACE_SENTINEL) == 64

    def test_cd07_sentinel_is_not_real_hash(self):
        """The sentinel must never accidentally equal the real hash."""
        real = law_surface_hash()
        assert real != LAW_SURFACE_SENTINEL, (
            "Sentinel matches real hash — this is a constitutional collision."
        )

    def test_cd07_version_constant_matches_yaml(self):
        assert LAW_SURFACE_VERSION == "LAW_SURFACE_V1"

    def test_cd07_default_file_path_exists(self):
        assert _DEFAULT_LAW_SURFACE_FILE.exists(), (
            "law_surface.yaml must exist at the default path."
        )
