"""
Composite admissibility runner — runs all 3 gates in sequence and produces
a single composite verdict + receipt.

Sequence:
  1. spectral_gate           — temporal coherence (luminance Gram)
  2. face_motion_gate        — mouth motion + autocorrelation structure
  3. av_sync_gate            — mouth motion vs audio envelope cross-correlation

Composite verdict:
  PASS         if all 3 gates pass
  REJECT_*     identifying which gate failed first

Caller wires this into the production pipeline as a HARD BLOCK before
delivery (Telegram send, ledger receipt, etc.). NON_SOVEREIGN — gate verdicts
are evidence; the operator + sovereign machinery decide promotion.
"""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from helen_os.gates.spectral_gate import spectral_gate
from helen_os.gates.face_motion_gate import face_motion_gate
from helen_os.gates.av_sync_gate import av_sync_gate


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def composite_admissibility(
    video_path: str | Path,
    spectral_size: int = 32,
    face_motion_size: int = 32,
    face_min_activity: float = 0.15,
    av_threshold: float = 0.35,
    av_target_len: int = 256,
    av_lag_max: int = 10,
) -> dict[str, Any]:
    """
    Run all 3 admissibility gates on a video.

    Returns a single composite receipt dict. Caller inspects
    composite_verdict to decide whether to allow the video to ship.
    """
    video_path = str(video_path)

    # Gate 1
    g1 = spectral_gate(video_path, size=spectral_size)

    # Gate 2 (only if gate 1 passed — false-positive chain blocking)
    if g1["gate_verdict"] == "PASS":
        g2 = face_motion_gate(
            video_path, size=face_motion_size, min_activity=face_min_activity,
        )
    else:
        g2 = {"gate": "face_motion_gate", "gate_verdict": "SKIPPED_PRIOR_FAIL"}

    # Gate 3 (only if gates 1+2 passed)
    if g1["gate_verdict"] == "PASS" and g2.get("gate_verdict") == "PASS":
        g3 = av_sync_gate(
            video_path, threshold=av_threshold,
            target_len=av_target_len, lag_max=av_lag_max,
        )
    else:
        g3 = {"gate": "av_sync_gate", "gate_verdict": "SKIPPED_PRIOR_FAIL"}

    # Composite verdict
    if g1["gate_verdict"] != "PASS":
        composite_verdict = f"REJECT_GATE_1_{g1['gate_verdict']}"
    elif g2.get("gate_verdict") != "PASS":
        composite_verdict = f"REJECT_GATE_2_{g2['gate_verdict']}"
    elif g3.get("gate_verdict") != "PASS":
        composite_verdict = f"REJECT_GATE_3_{g3['gate_verdict']}"
    else:
        composite_verdict = "PASS"

    composite = {
        "schema": "HELEN_AV_ADMISSIBILITY_RECEIPT_V1",
        "authority_status": "NON_SOVEREIGN",
        "generated_at": now_iso(),
        "object_id": video_path,
        "composite_verdict": composite_verdict,
        "gates": {
            "spectral_gate": g1,
            "face_motion_gate": g2,
            "av_sync_gate": g3,
        },
        "thresholds": {
            "spectral_size": spectral_size,
            "face_motion_size": face_motion_size,
            "face_min_activity": face_min_activity,
            "av_threshold": av_threshold,
            "av_target_len": av_target_len,
            "av_lag_max": av_lag_max,
        },
        "validator_id": None,
        "signature": None,
    }
    payload = json.dumps(
        {k: v for k, v in composite.items() if k not in ("validator_id", "signature")},
        sort_keys=True, default=str,
    )
    composite["payload_hash"] = hashlib.sha256(payload.encode()).hexdigest()
    return composite
