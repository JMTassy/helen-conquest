"""HELEN Render — pipeline wrapper.

Wires artifact → spec → stub → MediaArtifactV1 → RenderReceiptV1.
No reasoning. No state mutation. Pure forward flow.
"""
from __future__ import annotations

from typing import Tuple

from .contracts import canonical_json, sha256_hex
from .models import ExecutionArtifactV1, MediaArtifactV1, RenderReceiptV1
from .receipts import make_render_receipt
from .video import VideoRenderProfileV1, compile_video_spec, render_video_stub
from .audio import AudioRenderProfileV1, compile_audio_spec, render_audio_stub


def run_video_render(
    artifact:      ExecutionArtifactV1,
    profile:       VideoRenderProfileV1,
    previous_hash: str,
    renderer_name: str,
) -> Tuple[MediaArtifactV1, RenderReceiptV1]:
    """
    ExecutionArtifactV1 → (MediaArtifactV1, RenderReceiptV1).
    Pure forward flow. No back-edge into kernel.
    """
    spec       = compile_video_spec(artifact, profile)
    input_hash = sha256_hex(canonical_json(spec))
    result     = render_video_stub(spec)

    media = MediaArtifactV1(
        media_id=            result["content_hash"],
        source_artifact_id=  artifact.artifact_id,
        source_receipt_hash= artifact.receipt_hash,
        kind=                "video",
        mime_type=           result["mime_type"],
        content_hash=        result["content_hash"],
        path=                result["path"],
        metadata=            result["metadata"],
    )

    receipt = make_render_receipt(
        run_id=              artifact.run_id,
        source_artifact_id=  artifact.artifact_id,
        source_receipt_hash= artifact.receipt_hash,
        render_kind=         "video",
        renderer=            renderer_name,
        input_hash=          input_hash,
        output_hash=         media.content_hash,
        previous_hash=       previous_hash,
    )

    return media, receipt


def run_audio_render(
    artifact:      ExecutionArtifactV1,
    profile:       AudioRenderProfileV1,
    previous_hash: str,
    renderer_name: str,
) -> Tuple[MediaArtifactV1, RenderReceiptV1]:
    """ExecutionArtifactV1 → (MediaArtifactV1, RenderReceiptV1) for audio."""
    spec       = compile_audio_spec(artifact, profile)
    input_hash = sha256_hex(canonical_json(spec))
    result     = render_audio_stub(spec)

    media = MediaArtifactV1(
        media_id=            result["content_hash"],
        source_artifact_id=  artifact.artifact_id,
        source_receipt_hash= artifact.receipt_hash,
        kind=                "audio",
        mime_type=           result["mime_type"],
        content_hash=        result["content_hash"],
        path=                result["path"],
        metadata=            result["metadata"],
    )

    receipt = make_render_receipt(
        run_id=              artifact.run_id,
        source_artifact_id=  artifact.artifact_id,
        source_receipt_hash= artifact.receipt_hash,
        render_kind=         "audio",
        renderer=            renderer_name,
        input_hash=          input_hash,
        output_hash=         media.content_hash,
        previous_hash=       previous_hash,
    )

    return media, receipt
