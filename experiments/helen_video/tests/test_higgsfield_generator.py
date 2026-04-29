"""Higgsfield Generator — invariant and structural tests (updated for env-key + stub API).

Real API calls are never made. Tests mock _invoke_higgsfield and HIGGSFIELD_API_KEY.
"""
import ast
import hashlib
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from helen_video.admissibility_gate import PIPELINE_SALT, verify_receipt_binding
from helen_video import higgsfield_generator
from helen_video.higgsfield_generator import (
    PROVIDER,
    SUPPORTED_MODELS,
    _pipeline_hash,
    _sha256,
    build_receipt_from_result,
    generate_candidate,
)


# ── helpers ───────────────────────────────────────────────────────────────────

PROMPT = "HELEN in Oracle Town, cinematic wide shot"
MODEL  = "kling-2.5"

# Updated keys to match new API: output_url + request_id
_FAKE_JOB = {"output_url": "https://cdn.higgsfield.ai/fake.mp4", "request_id": "job-abc123"}
_FAKE_KEY = "hf-test-key-not-real"


def _patched_invoke(job_result: dict = _FAKE_JOB):
    """Patch both the API key (so stub mode is bypassed) and _invoke_higgsfield."""
    return patch.multiple(
        "helen_video.higgsfield_generator",
        _get_api_key=lambda: _FAKE_KEY,
        _invoke_higgsfield=lambda prompt, model, params, api_key: job_result,
    )


# ── stub mode: no API key ─────────────────────────────────────────────────────

def test_stub_mode_when_no_key(monkeypatch):
    monkeypatch.delenv("HIGGSFIELD_API_KEY", raising=False)
    result = generate_candidate(PROMPT, model=MODEL)
    assert result["status"] == "STUB"
    assert result["provider"] == PROVIDER
    assert result["error"] is not None
    assert "HIGGSFIELD_API_KEY" in result["error"]


def test_stub_mode_model_endpoint_is_none(monkeypatch):
    monkeypatch.delenv("HIGGSFIELD_API_KEY", raising=False)
    result = generate_candidate(PROMPT, model=MODEL)
    assert result["model_endpoint"] is None


def test_stub_mode_has_required_fields(monkeypatch):
    monkeypatch.delenv("HIGGSFIELD_API_KEY", raising=False)
    result = generate_candidate(PROMPT, model=MODEL)
    required = {"provider", "status", "prompt", "model_endpoint",
                "request_id", "output_path", "error", "ts"}
    assert required <= set(result.keys())


# ── invariant 1: status is CANDIDATE when key is set ─────────────────────────

def test_status_is_candidate_with_key():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    assert c["status"] == "CANDIDATE"


def test_status_never_accept_or_deliver():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    assert c["status"] not in {"ACCEPT", "ACCEPTED", "DELIVER", "ACTIVE", "REJECT"}


def test_provider_is_higgsfield():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    assert c["provider"] == PROVIDER
    assert c["source"] == "higgsfield"


def test_model_endpoint_set_when_configured():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    assert c["model_endpoint"] is not None
    assert "higgsfield" in c["model_endpoint"]


# ── invariant 2: receipt binding passes verify_receipt_binding() ──────────────

def test_receipt_binding_is_valid():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    assert verify_receipt_binding(c["receipt"]) is True


def test_pipeline_hash_bound_to_content_hash():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    content_hash = c["content_hash"]
    expected = hashlib.sha256((content_hash + PIPELINE_SALT).encode()).hexdigest()
    assert c["receipt"]["pipeline_hash"] == expected


# ── invariant 3: receipt has all required fields ──────────────────────────────

def test_receipt_fields_complete():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    required = {"content_hash", "pipeline_hash", "renderer", "model",
                "prompt_hash", "request_id", "source_url", "timestamp"}
    assert required <= set(c["receipt"].keys())


def test_receipt_content_hash_matches_candidate():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    assert c["receipt"]["content_hash"] == c["content_hash"]


def test_receipt_renderer_is_higgsfield():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    assert c["receipt"]["renderer"] == PROVIDER


# ── invariant 4: prompt_hash is sha256(prompt) ────────────────────────────────

def test_sha256_helper_is_deterministic():
    expected = hashlib.sha256(PROMPT.encode()).hexdigest()
    assert _sha256(PROMPT) == expected


def test_prompt_hash_in_receipt():
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL)
    expected = hashlib.sha256(PROMPT.encode()).hexdigest()
    assert c["receipt"]["prompt_hash"] == expected


def test_different_prompts_give_different_hashes():
    assert _sha256("A") != _sha256("B")


# ── invariant 5: content hash from URL proxy when no local file ───────────────

def test_content_hash_url_proxy_is_deterministic():
    url = "https://cdn.higgsfield.ai/fake.mp4"
    h1 = _sha256(f"url:{url}")
    h2 = _sha256(f"url:{url}")
    assert h1 == h2


def test_content_hash_url_differs_for_different_urls():
    h1 = _sha256("url:https://a.com/a.mp4")
    h2 = _sha256("url:https://b.com/b.mp4")
    assert h1 != h2


def test_content_hash_from_local_file(tmp_path):
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake video content")
    with _patched_invoke():
        c = generate_candidate(PROMPT, model=MODEL, output_path=f)
    expected = hashlib.sha256(b"fake video content").hexdigest()
    assert c["content_hash"] == expected


# ── invariant 6: NotImplementedError → STUB when key configured but invoke unimplemented

def test_not_implemented_returns_stub_not_raise():
    """When key is set but invoke raises NotImplementedError → STUB, not exception."""
    with patch("helen_video.higgsfield_generator._get_api_key", return_value=_FAKE_KEY):
        result = generate_candidate(PROMPT, model=MODEL)
    assert result["status"] == "STUB"
    assert "not yet implemented" in (result["error"] or "")


# ── build_receipt_from_result ─────────────────────────────────────────────────

def test_build_receipt_from_result_valid_binding():
    receipt = build_receipt_from_result(_FAKE_JOB, PROMPT, MODEL)
    assert verify_receipt_binding(receipt) is True


def test_build_receipt_from_result_has_required_fields():
    receipt = build_receipt_from_result(_FAKE_JOB, PROMPT, MODEL)
    required = {"content_hash", "pipeline_hash", "renderer", "model",
                "prompt_hash", "request_id", "source_url", "timestamp"}
    assert required <= set(receipt.keys())


def test_build_receipt_from_local_file(tmp_path):
    f = tmp_path / "video.mp4"
    f.write_bytes(b"real bytes")
    receipt = build_receipt_from_result(_FAKE_JOB, PROMPT, MODEL, local_file=f)
    expected = hashlib.sha256(b"real bytes").hexdigest()
    assert receipt["content_hash"] == expected
    assert verify_receipt_binding(receipt) is True


# ── invariant 7: no deliver/gate/ledger in module ────────────────────────────

def test_module_has_no_deliver_methods():
    public = [n for n in dir(higgsfield_generator)
              if not n.startswith("_") and callable(getattr(higgsfield_generator, n))]
    forbidden = {"deliver", "ship", "push", "accept", "evaluate", "append"}
    assert not (set(public) & forbidden)


def test_module_does_not_import_video_ledger():
    tree = ast.parse(Path(higgsfield_generator.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    assert "video_ledger" not in imported
    assert "VideoLedger" not in imported


def test_module_does_not_call_evaluate():
    tree = ast.parse(Path(higgsfield_generator.__file__).read_text())
    calls = [
        node.func.id if isinstance(node.func, ast.Name) else
        (node.func.attr if isinstance(node.func, ast.Attribute) else None)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    ]
    assert "evaluate" not in calls


# ── supported models list ─────────────────────────────────────────────────────

def test_supported_models_includes_key_models():
    assert "kling-2.5" in SUPPORTED_MODELS
    assert "seedance-2.0" in SUPPORTED_MODELS
    assert "soul-cinema" in SUPPORTED_MODELS
