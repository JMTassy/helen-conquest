"""HELEN Render — receipt constructor.

Invariant R5: every render receipt must point back to the governed source receipt.
Invariant: authority=False always, structurally enforced.
"""
from __future__ import annotations

from .contracts import canonical_json, sha256_hex
from .models import RenderReceiptV1


def make_render_receipt(
    *,
    run_id:              str,
    source_artifact_id:  str,
    source_receipt_hash: str,
    render_kind:         str,
    renderer:            str,
    input_hash:          str,
    output_hash:         str,
    previous_hash:       str,
) -> RenderReceiptV1:
    """Build and hash a RENDER_RECEIPT_V1. authority=False structurally."""
    base = {
        "type":                "RENDER_RECEIPT_V1",
        "run_id":              run_id,
        "source_artifact_id":  source_artifact_id,
        "source_receipt_hash": source_receipt_hash,
        "render_kind":         render_kind,
        "renderer":            renderer,
        "input_hash":          input_hash,
        "output_hash":         output_hash,
        "previous_hash":       previous_hash,
        "authority":           False,
    }
    receipt_hash = sha256_hex(canonical_json(base))
    return RenderReceiptV1(**base, receipt_hash=receipt_hash)
