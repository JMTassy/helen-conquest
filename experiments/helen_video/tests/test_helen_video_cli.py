"""CLI end-to-end tests — render → gate → ledger → export."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "helen_video_cli.py"
PIPELINE_SALT = "helen_video_v1"


def _pipeline_hash(content_hash: str) -> str:
    return hashlib.sha256((content_hash + PIPELINE_SALT).encode()).hexdigest()


def _run(*args, ledger: Path) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(CLI)] + list(args) + ["--ledger", str(ledger)],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw": result.stdout, "stderr": result.stderr}
    return result.returncode, data


def test_render_accept(tmp_path):
    rc, out = _run(
        "render",
        "--prompt", "HELEN in Oracle Town",
        "--content-hash", "abc123",
        "--visual-coherence", "0.85",
        "--temporal-alignment", "0.72",
        ledger=tmp_path / "v.ndjson",
    )
    assert rc == 0
    assert out["decision"] == "ACCEPT"
    assert "entry_hash" in out


def test_render_pending_when_metrics_absent(tmp_path):
    rc, out = _run(
        "render",
        "--prompt", "dark shot",
        "--content-hash", "abc456",
        ledger=tmp_path / "v.ndjson",
    )
    assert rc == 1
    assert out["decision"] == "PENDING"


def test_render_reject_low_coherence(tmp_path):
    rc, out = _run(
        "render",
        "--prompt", "blurry shot",
        "--content-hash", "abc789",
        "--visual-coherence", "0.3",
        "--temporal-alignment", "0.8",
        ledger=tmp_path / "v.ndjson",
    )
    assert rc == 1
    assert out["decision"] == "REJECT"


def test_export_shows_only_accepted(tmp_path):
    ledger = tmp_path / "v.ndjson"
    _run("render", "--prompt", "good", "--content-hash", "h1",
         "--visual-coherence", "0.9", "--temporal-alignment", "0.8", ledger=ledger)
    _run("render", "--prompt", "bad", "--content-hash", "h2",
         "--visual-coherence", "0.2", "--temporal-alignment", "0.8", ledger=ledger)
    _, out = _run("export", ledger=ledger)
    assert out["accepted_count"] == 1
    assert out["clips"][0]["content_hash"] == "h1"
    assert "timeline_hash" in out


def test_status_chain_valid(tmp_path):
    ledger = tmp_path / "v.ndjson"
    _run("render", "--prompt", "shot", "--content-hash", "h1",
         "--visual-coherence", "0.9", "--temporal-alignment", "0.8", ledger=ledger)
    rc, out = _run("status", ledger=ledger)
    assert rc == 0
    assert out["chain_valid"] is True
    assert out["total_entries"] == 1


def test_verify_empty_ledger(tmp_path):
    rc, out = _run("verify", ledger=tmp_path / "v.ndjson")
    assert rc == 0
    assert out["chain_valid"] is True
