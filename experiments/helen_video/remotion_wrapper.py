"""Remotion Wrapper — auto render → auto hash → auto receipt → CANDIDATE.

This module is the bridge between Remotion (deterministic video renderer)
and the HELEN RAI admissibility stack.

Hard invariants:
  - Wrapper emits CANDIDATE only. Never ACCEPT, REJECT, or PENDING.
  - Wrapper never calls admissibility_gate.
  - Wrapper never appends to VideoLedger.
  - Wrapper never calls deliver() or any delivery function.
  - Gate decides later. Ledger is written later. Delivery is separate.

Pipeline:
  composition + props
    → npx remotion render
    → output MP4
    → sha256(file bytes)     → content_hash
    → sha256(props)          → props_hash
    → sha256(content_hash + PIPELINE_SALT) → pipeline_hash
    → CANDIDATE + receipt
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from helen_video.admissibility_gate import PIPELINE_SALT

RENDERER = "remotion"


# ── internal helpers ──────────────────────────────────────────────────────────

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _file_content_hash(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _props_hash(props: dict | None) -> str:
    return _sha256_str(_canonical(props or {}))


def _pipeline_hash(content_hash: str) -> str:
    """Bound to content_hash via PIPELINE_SALT — passes verify_receipt_binding()."""
    return _sha256_str(content_hash + PIPELINE_SALT)


def _invoke_remotion(
    composition: str,
    output_path: Path,
    props: dict | None,
    remotion_config: Path | None,
) -> None:
    """Call Remotion CLI. Raises RuntimeError on non-zero exit."""
    cmd = ["npx", "remotion", "render", composition, str(output_path)]
    if remotion_config:
        cmd += ["--config", str(remotion_config)]
    if props:
        cmd += ["--props", _canonical(props)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Remotion render failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


# ── public API ────────────────────────────────────────────────────────────────

def render_candidate(
    composition: str,
    output_path: str | Path,
    props: dict | None = None,
    remotion_config: str | Path | None = None,
    video_id: str | None = None,
) -> dict:
    """Render a video using Remotion and return a gate-ready CANDIDATE.

    Args:
        composition:    Remotion composition name (e.g. "Scene").
        output_path:    Where to write the rendered MP4.
        props:          Props dict passed to the Remotion composition.
        remotion_config: Optional path to remotion.config.ts.
        video_id:       Optional stable ID; generated if not provided.

    Returns:
        A CANDIDATE dict with receipt. Status is always "CANDIDATE".
        Pass receipt to admissibility_gate.evaluate() when ready.

    Raises:
        RuntimeError: if Remotion render fails.
        FileNotFoundError: if output_path was not written by Remotion.
    """
    output_path = Path(output_path)
    if remotion_config:
        remotion_config = Path(remotion_config)

    _invoke_remotion(composition, output_path, props, remotion_config)

    if not output_path.exists():
        raise FileNotFoundError(
            f"Remotion did not write output file: {output_path}"
        )

    content_hash = _file_content_hash(output_path)
    ph = _props_hash(props)
    pipe_hash = _pipeline_hash(content_hash)
    ts = datetime.now(timezone.utc).isoformat()
    vid = video_id or str(uuid.uuid4())

    receipt = {
        "content_hash": content_hash,
        "pipeline_hash": pipe_hash,
        "renderer": RENDERER,
        "composition": composition,
        "props_hash": ph,
        "timestamp": ts,
    }

    return {
        "video_id": vid,
        "status": "CANDIDATE",
        "source": RENDERER,
        "composition": composition,
        "output_path": str(output_path),
        "content_hash": content_hash,
        "receipt": receipt,
    }


def build_receipt_from_file(
    rendered_file: str | Path,
    composition: str,
    props: dict | None = None,
) -> dict:
    """Build a receipt from an already-rendered file (no subprocess call).

    Use when the render was done externally and you only need the receipt.
    """
    path = Path(rendered_file)
    content_hash = _file_content_hash(path)
    return {
        "content_hash": content_hash,
        "pipeline_hash": _pipeline_hash(content_hash),
        "renderer": RENDERER,
        "composition": composition,
        "props_hash": _props_hash(props),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
