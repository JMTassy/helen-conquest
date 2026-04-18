"""HELEN Render — canonical data types.

Three dataclasses only. No logic. No imports beyond stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

RenderKind = Literal["video", "audio", "image"]
Tone       = Literal["calm", "warm", "serious", "precise", "reflective"]
Persona    = Literal["helen", "oracle", "concierge", "narrator"]


@dataclass(frozen=True)
class ExecutionArtifactV1:
    """Only lawful input to the render layer."""
    artifact_id:    str
    run_id:         str
    receipt_hash:   str                  # sha256: binding to the governed source
    content:        str                  # text to embody
    summary:        Optional[str]        = None
    tone:           Tone                 = "precise"
    persona:        Persona              = "helen"
    render_targets: List[RenderKind]     = field(default_factory=lambda: ["audio"])
    metadata:       Dict[str, Any]       = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.receipt_hash.startswith("sha256:"):
            raise ValueError("receipt_hash must be sha256: prefixed")


@dataclass(frozen=True)
class MediaArtifactV1:
    """Output of the render layer. Immutable. No authority."""
    media_id:            str
    source_artifact_id:  str
    source_receipt_hash: str
    kind:                RenderKind
    mime_type:           str
    content_hash:        str
    path:                str
    metadata:            Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderReceiptV1:
    """Every render emits one. Bound to source receipt. authority=False always."""
    type:                str
    run_id:              str
    source_artifact_id:  str
    source_receipt_hash: str
    render_kind:         RenderKind
    renderer:            str
    input_hash:          str
    output_hash:         str
    previous_hash:       str
    receipt_hash:        str
    authority:           bool = False

    def __post_init__(self) -> None:
        if self.authority:
            raise ValueError("RenderReceiptV1.authority must be False")
