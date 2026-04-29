"""Higgsfield Generator — adapter skeleton.

Mirrors the RalphGenerator interface style.
Reads HIGGSFIELD_API_KEY from environment only — never logs or exposes it.
Runs in stub/dry-run mode when the key is absent.

Hard invariants:
  - No memory mutation.
  - No canon promotion.
  - No delivery path.
  - Status is always CANDIDATE (real) or STUB (dry-run).
  - Never writes to ledger. Never calls admissibility_gate.evaluate().

lifecycle: EXPERIMENTAL_ADAPTER_SKELETON
canon: NO_SHIP
"""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from helen_video.admissibility_gate import PIPELINE_SALT

PROVIDER = "higgsfield"

# Default model; callers may override.
DEFAULT_MODEL_ENDPOINT = "https://api.higgsfield.ai/v1/video/generate"

SUPPORTED_MODELS = frozenset({
    "kling-2.5",
    "veo-3",
    "sora-2",
    "seedance-2.0",
    "soul-cinema",
    "minimax-hailuo",
    "wan-2.6",
})


# ── internal helpers ──────────────────────────────────────────────────────────

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _pipeline_hash(content_hash: str) -> str:
    return _sha256(content_hash + PIPELINE_SALT)


def _get_api_key() -> str | None:
    """Read HIGGSFIELD_API_KEY from environment. Returns None if absent."""
    return os.environ.get("HIGGSFIELD_API_KEY") or None


def _is_configured() -> bool:
    return _get_api_key() is not None


# ── result builder ────────────────────────────────────────────────────────────

def _build_result(
    *,
    status: str,
    prompt: str,
    model: str,
    request_id: str | None = None,
    output_path: str | None = None,
    error: str | None = None,
    configured: bool,
) -> dict:
    """Assemble the structured result dict compatible with the render pipeline."""
    return {
        "provider": PROVIDER,
        "status": status,
        "prompt": prompt,
        "model_endpoint": DEFAULT_MODEL_ENDPOINT if configured else None,
        "request_id": request_id,
        "output_path": output_path,
        "error": error,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


# ── stub mode ─────────────────────────────────────────────────────────────────

def _stub_result(prompt: str, model: str) -> dict:
    """Return a dry-run result when HIGGSFIELD_API_KEY is not set."""
    return _build_result(
        status="STUB",
        prompt=prompt,
        model=model,
        request_id=f"stub-{uuid.uuid4()}",
        output_path=None,
        error="HIGGSFIELD_API_KEY not set — running in stub/dry-run mode",
        configured=False,
    )


# ── real call (skeleton) ──────────────────────────────────────────────────────

def _invoke_higgsfield(
    prompt: str,
    model: str,
    params: dict | None,
    api_key: str,
) -> dict:
    """Submit a generation job to Higgsfield. Skeleton — raises NotImplementedError.

    When implemented:
      POST DEFAULT_MODEL_ENDPOINT with Authorization: Bearer <api_key>
      Poll until job complete, return {"request_id": str, "output_url": str}.

    Raises:
        NotImplementedError: until real API call is implemented.
    """
    raise NotImplementedError(
        "Real Higgsfield API call not yet implemented. "
        "Implement this function to POST to DEFAULT_MODEL_ENDPOINT "
        "with the key from HIGGSFIELD_API_KEY."
    )


# ── public API ────────────────────────────────────────────────────────────────

def generate_candidate(
    prompt: str,
    model: str = "kling-2.5",
    params: dict | None = None,
    output_path: str | Path | None = None,
    video_id: str | None = None,
) -> dict:
    """Generate a video candidate via Higgsfield.

    Runs in stub mode if HIGGSFIELD_API_KEY is not set.
    Returns a CANDIDATE dict (or STUB dict) compatible with the render pipeline.

    Args:
        prompt:      Text prompt for the video.
        model:       Model key (e.g. "kling-2.5", "soul-cinema").
        params:      Optional generation params (aspect_ratio, seed, etc.)
        output_path: Optional local path to save the output.
        video_id:    Stable ID for this candidate; generated if not provided.

    Returns:
        Structured result dict. Fields: provider, status, prompt,
        model_endpoint, request_id, output_path, error, ts.
        Plus receipt sub-dict when status == CANDIDATE.
    """
    api_key = _get_api_key()
    out = Path(output_path) if output_path else None
    vid = video_id or str(uuid.uuid4())

    if not api_key:
        return _stub_result(prompt, model)

    try:
        job = _invoke_higgsfield(prompt, model, params, api_key)
    except NotImplementedError as exc:
        return _build_result(
            status="STUB",
            prompt=prompt,
            model=model,
            error=str(exc),
            configured=True,
        )
    except Exception as exc:
        return _build_result(
            status="ERROR",
            prompt=prompt,
            model=model,
            error=str(exc),
            configured=True,
        )

    request_id = job.get("request_id", str(uuid.uuid4()))
    output_url  = job.get("output_url", "")
    out_str     = str(out) if out else None

    # Content hash: from local file if written, else from URL proxy
    if out and out.exists():
        content_hash = hashlib.sha256(out.read_bytes()).hexdigest()
    else:
        content_hash = _sha256(f"url:{output_url}")

    receipt = {
        "content_hash":  content_hash,
        "pipeline_hash": _pipeline_hash(content_hash),
        "renderer":      PROVIDER,
        "model":         model,
        "prompt_hash":   _sha256(prompt),
        "request_id":    request_id,
        "source_url":    output_url,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    }

    result = _build_result(
        status="CANDIDATE",
        prompt=prompt,
        model=model,
        request_id=request_id,
        output_path=out_str,
        configured=True,
    )
    result["video_id"] = vid
    result["source"]   = PROVIDER
    result["content_hash"] = content_hash
    result["receipt"]  = receipt
    return result


def build_receipt_from_result(
    job_result: dict,
    prompt: str,
    model: str,
    local_file: str | Path | None = None,
) -> dict:
    """Build a receipt from an already-completed Higgsfield job.

    Use when the job ran externally and you only need the receipt.
    """
    output_url  = job_result.get("output_url", "")
    request_id  = job_result.get("request_id", "")

    if local_file:
        content_hash = hashlib.sha256(Path(local_file).read_bytes()).hexdigest()
    else:
        content_hash = _sha256(f"url:{output_url}")

    return {
        "content_hash":  content_hash,
        "pipeline_hash": _pipeline_hash(content_hash),
        "renderer":      PROVIDER,
        "model":         model,
        "prompt_hash":   _sha256(prompt),
        "request_id":    request_id,
        "source_url":    output_url,
        "timestamp":     datetime.now(timezone.utc).isoformat(),
    }
