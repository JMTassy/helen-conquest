"""Smoke test for higgsfield_seedance subsandbox scaffold.

DRY_RUN tests run offline, always.
LIVE tests are skipped unless HIGGSFIELD_API_KEY is set AND
HIGGSFIELD_LIVE_TESTS=1 is set (extra confirmation gate).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Make the subsandbox scaffold importable when run via pytest from repo root
SCAFFOLD = Path(__file__).resolve().parents[1]
EXP_ROOT = SCAFFOLD.parent  # experiments/helen_mvp_kernel/
if str(EXP_ROOT) not in sys.path:
    sys.path.insert(0, str(EXP_ROOT))

from higgsfield_seedance.client import render_shot  # noqa: E402
from higgsfield_seedance.receipts import emit_receipt, validate_receipt  # noqa: E402


def test_dry_run_render_returns_valid_receipt(tmp_path):
    ref_image = tmp_path / "fake_ref.png"
    ref_image.write_bytes(b"\x89PNG\r\n\x1a\nFAKEPNGCONTENT")

    r = render_shot(
        ref_image=str(ref_image),
        prompt="test shot, cyberpunk-cathedral",
        duration_s=4.0,
        seed=2026050201,
        task_id="SMOKE_TEST_2026-05-02",
        shot_n=1,
        mode="DRY_RUN",
    )

    validate_receipt(r)
    assert r["mode"] == "DRY_RUN"
    assert r["scope"] == "TEMPLE_SUBSANDBOX"
    assert r["sovereign_admitted"] is False
    assert r["returned_url"] == ""
    assert r["mp4_sha256"] == ""
    assert r["seed"] == 2026050201
    assert r["shot_n"] == 1


def test_dry_run_is_deterministic_per_seed(tmp_path):
    ref_image = tmp_path / "fake_ref.png"
    ref_image.write_bytes(b"DETERMINISTIC")

    r1 = render_shot(str(ref_image), "p", 4.0, 42, "DET", 1, mode="DRY_RUN")
    r2 = render_shot(str(ref_image), "p", 4.0, 42, "DET", 1, mode="DRY_RUN")

    # ref_image_sha256, prompt_hash, seed, scope, sovereign_admitted should match
    for key in ("ref_image_sha256", "prompt_hash", "seed", "scope", "sovereign_admitted"):
        assert r1[key] == r2[key], f"non-deterministic on {key}"


def test_emit_receipt_writes_to_subsandbox_only(tmp_path, monkeypatch):
    # Redirect SUBSANDBOX_RENDERS to a tmp path so the test does not pollute the repo
    import higgsfield_seedance.receipts as receipts_mod

    monkeypatch.setattr(receipts_mod, "SUBSANDBOX_RENDERS", tmp_path / "renders")

    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(b"PNG")
    r = render_shot(str(ref_image), "p", 4.0, 1, "T", 1, mode="DRY_RUN")

    written = emit_receipt(r, task_id="T")
    assert written.exists()
    assert "town/ledger_v1.ndjson" not in str(written)
    assert "subsandbox" in str(written) or "renders" in str(written)

    line = written.read_text(encoding="utf-8").strip().splitlines()[-1]
    parsed = json.loads(line)
    assert parsed["schema"] == "HIGGSFIELD_CALL_RECEIPT_V1"


def test_validation_rejects_sovereign_admitted_true(tmp_path):
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(b"PNG")
    r = render_shot(str(ref_image), "p", 4.0, 1, "T", 1, mode="DRY_RUN")
    r["sovereign_admitted"] = True
    with pytest.raises(ValueError):
        validate_receipt(r)


def test_validation_rejects_wrong_scope(tmp_path):
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(b"PNG")
    r = render_shot(str(ref_image), "p", 4.0, 1, "T", 1, mode="DRY_RUN")
    r["scope"] = "SOVEREIGN"
    with pytest.raises(ValueError):
        validate_receipt(r)


def test_live_without_api_key_returns_no_api_key_error(tmp_path, monkeypatch):
    monkeypatch.delenv("HIGGSFIELD_API_KEY", raising=False)
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(b"PNG")
    r = render_shot(str(ref_image), "p", 4.0, 1, "T", 1, mode="LIVE")
    assert r.get("error", {}).get("code") == "NO_API_KEY"


def test_live_with_api_key_returns_skill_not_admitted(tmp_path, monkeypatch):
    monkeypatch.setenv("HIGGSFIELD_API_KEY", "fake-key-for-test")
    ref_image = tmp_path / "ref.png"
    ref_image.write_bytes(b"PNG")
    r = render_shot(str(ref_image), "p", 4.0, 1, "T", 1, mode="LIVE")
    # In subsandbox state, even with API key the LIVE branch must
    # refuse with SKILL_NOT_ADMITTED until MAYOR admits the skill.
    assert r.get("error", {}).get("code") == "SKILL_NOT_ADMITTED"


@pytest.mark.skipif(
    not (os.environ.get("HIGGSFIELD_API_KEY") and os.environ.get("HIGGSFIELD_LIVE_TESTS") == "1"),
    reason="LIVE tests require HIGGSFIELD_API_KEY and HIGGSFIELD_LIVE_TESTS=1",
)
def test_live_real_call_placeholder():
    # Reserved for post-admission. Currently no-op gated test.
    pytest.skip("LIVE real-call test reserved for post-MAYOR-admission state")
