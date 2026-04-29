"""Remotion wrapper tests — mocked subprocess, no real Remotion required."""
import hashlib
import importlib
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from helen_video.admissibility_gate import PIPELINE_SALT, verify_receipt_binding
from helen_video import remotion_wrapper
from helen_video.remotion_wrapper import (
    render_candidate,
    build_receipt_from_file,
    _pipeline_hash,
    _props_hash,
    _file_content_hash,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

VIDEO_BYTES = b"fake remotion rendered video content"
COMPOSITION = "Scene"
PROPS = {"title": "HELEN in Oracle Town", "frame": 0}


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _make_fake_video(tmp_path: Path, content: bytes = VIDEO_BYTES) -> Path:
    p = tmp_path / "out.mp4"
    p.write_bytes(content)
    return p


def _patched_render(output_path: Path, content: bytes = VIDEO_BYTES):
    """Mock _invoke_remotion by writing fake bytes to output_path."""
    def _side_effect(composition, out, props, config):
        Path(out).write_bytes(content)
    return patch("helen_video.remotion_wrapper._invoke_remotion", side_effect=_side_effect)


# ── invariant 1: wrapper emits CANDIDATE only ─────────────────────────────────

def test_wrapper_status_is_always_candidate(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    assert c["status"] == "CANDIDATE"


def test_wrapper_never_returns_accept(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    assert c["status"] != "ACCEPT"
    assert c["status"] != "ACCEPTED"
    assert c["status"] != "REJECT"
    assert c["status"] != "PENDING"


def test_wrapper_source_is_remotion(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    assert c["source"] == "remotion"


# ── invariant 2: wrapper never calls gate or ledger ───────────────────────────

def test_wrapper_does_not_import_videolasher():
    """Wrapper module must not import VideoLedger."""
    import ast
    import helen_video.remotion_wrapper as mod
    tree = ast.parse(Path(mod.__file__).read_text())
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
    assert "VideoLedger" not in imported_names
    assert "video_ledger" not in imported_names


def test_wrapper_does_not_call_evaluate():
    """Wrapper module must not call admissibility_gate.evaluate()."""
    import ast
    import helen_video.remotion_wrapper as mod
    tree = ast.parse(Path(mod.__file__).read_text())
    # Check that 'evaluate' is not called as a function in any expression
    calls = [
        node.func.id if isinstance(node.func, ast.Name) else
        (node.func.attr if isinstance(node.func, ast.Attribute) else None)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    ]
    assert "evaluate" not in calls


def test_wrapper_has_no_deliver_methods():
    public = [n for n in dir(remotion_wrapper)
              if not n.startswith("_") and callable(getattr(remotion_wrapper, n))]
    forbidden = {"deliver", "ship", "push", "send", "publish", "export", "accept"}
    assert not (set(public) & forbidden)


# ── invariant 3: content_hash == sha256(file bytes) ──────────────────────────

def test_content_hash_is_sha256_of_file(tmp_path):
    f = _make_fake_video(tmp_path)
    expected = hashlib.sha256(VIDEO_BYTES).hexdigest()
    assert _file_content_hash(f) == expected


def test_candidate_content_hash_matches_file(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    expected = hashlib.sha256(VIDEO_BYTES).hexdigest()
    assert c["content_hash"] == expected
    assert c["receipt"]["content_hash"] == expected


# ── invariant 4: receipt binding passes verify_receipt_binding() ──────────────

def test_receipt_binding_is_valid(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    assert verify_receipt_binding(c["receipt"]) is True


def test_pipeline_hash_bound_to_content_hash(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    content_hash = c["content_hash"]
    expected_ph = _sha256(content_hash + PIPELINE_SALT)
    assert c["receipt"]["pipeline_hash"] == expected_ph


# ── invariant 5: receipt has all required fields ──────────────────────────────

def test_receipt_fields_are_complete(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    required = {"content_hash", "pipeline_hash", "renderer", "composition",
                "props_hash", "timestamp"}
    assert required <= set(c["receipt"].keys())


def test_receipt_content_hash_equals_candidate_content_hash(tmp_path):
    out = tmp_path / "out.mp4"
    with _patched_render(out):
        c = render_candidate(COMPOSITION, out, props=PROPS)
    assert c["receipt"]["content_hash"] == c["content_hash"]


# ── invariant 6: different props → different props_hash ──────────────────────

def test_props_hash_changes_with_props():
    h1 = _props_hash({"title": "A"})
    h2 = _props_hash({"title": "B"})
    assert h1 != h2


def test_props_hash_stable_for_same_props():
    assert _props_hash(PROPS) == _props_hash(PROPS)


# ── error cases ───────────────────────────────────────────────────────────────

def test_render_failure_raises_runtime_error(tmp_path):
    out = tmp_path / "out.mp4"
    with patch("helen_video.remotion_wrapper._invoke_remotion",
               side_effect=RuntimeError("Remotion render failed: exit 1")):
        with pytest.raises(RuntimeError, match="Remotion render failed"):
            render_candidate(COMPOSITION, out, props=PROPS)


def test_missing_output_raises_file_not_found(tmp_path):
    out = tmp_path / "out.mp4"
    with patch("helen_video.remotion_wrapper._invoke_remotion"):
        # _invoke_remotion succeeds but writes nothing → FileNotFoundError
        with pytest.raises(FileNotFoundError):
            render_candidate(COMPOSITION, out, props=PROPS)


# ── build_receipt_from_file ───────────────────────────────────────────────────

def test_build_receipt_from_existing_file(tmp_path):
    f = _make_fake_video(tmp_path)
    receipt = build_receipt_from_file(f, COMPOSITION, props=PROPS)
    assert verify_receipt_binding(receipt) is True
    assert receipt["renderer"] == "remotion"
    assert receipt["composition"] == COMPOSITION
