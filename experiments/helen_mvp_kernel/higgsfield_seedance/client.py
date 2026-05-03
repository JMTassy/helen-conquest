"""higgsfield_seedance.client — per-shot render entrypoint.

DRY_RUN mode is fully implemented (offline, deterministic).
LIVE mode is scaffolded: the network call is intentionally left as a
typed placeholder so the surrounding code (receipt emission, hashing,
error handling) can be tested without an API key.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

Mode = Literal["LIVE", "DRY_RUN"]


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_ref_image(ref_image: str) -> str:
    p = Path(ref_image)
    if not p.exists():
        return _sha256_hex(f"DRY_RUN_MISSING:{ref_image}".encode())
    return _sha256_hex(p.read_bytes())


def render_shot(
    ref_image: str,
    prompt: str,
    duration_s: float,
    seed: int,
    task_id: str,
    shot_n: int,
    mode: Mode = "LIVE",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Render one shot via Higgsfield Seedance2.

    Returns a dict matching HIGGSFIELD_CALL_RECEIPT_V1.

    DRY_RUN: no network, deterministic placeholder receipt.
    LIVE:    requires api_key (or HIGGSFIELD_API_KEY env). Performs the
             actual API call. Network logic is a typed placeholder until
             MAYOR admits the skill into oracle_town/.
    """
    if mode not in ("LIVE", "DRY_RUN"):
        raise ValueError(f"mode must be LIVE or DRY_RUN, got {mode!r}")

    ref_hash = _hash_ref_image(ref_image)
    prompt_hash = _sha256_hex(_canon(prompt))

    receipt: Dict[str, Any] = {
        "schema": "HIGGSFIELD_CALL_RECEIPT_V1",
        "task_id": task_id,
        "shot_n": shot_n,
        "ref_image_sha256": ref_hash,
        "prompt": prompt,
        "prompt_hash": prompt_hash,
        "seed": seed,
        "duration_s": duration_s,
        "returned_url": "",
        "mp4_sha256": "",
        "timestamp_utc": _now_iso(),
        "scope": "TEMPLE_SUBSANDBOX",
        "sovereign_admitted": False,
        "mode": mode,
    }

    if mode == "DRY_RUN":
        return receipt

    # LIVE branch
    api_key = api_key or os.environ.get("HIGGSFIELD_API_KEY")
    if not api_key:
        receipt["error"] = {
            "code": "NO_API_KEY",
            "message": "HIGGSFIELD_API_KEY not set; cannot perform LIVE call.",
        }
        return receipt

    # Typed placeholder for the actual Higgsfield API call.
    # When MAYOR admits the skill, replace this block with the real
    # client (httpx POST, response parsing, mp4 download, hashing).
    # Until then, LIVE without admission returns a receipt with an
    # explicit NOT_ADMITTED error so callers cannot mistake DRY_RUN
    # output for a real render.
    receipt["error"] = {
        "code": "SKILL_NOT_ADMITTED",
        "message": (
            "higgsfield_seedance is a subsandbox scaffold. LIVE renders "
            "require MAYOR admission per "
            "MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md."
        ),
    }
    return receipt
