"""higgsfield_seedance.receipts — receipt emission + validation.

Validates against the schema draft at
experiments/helen_mvp_kernel/schemas/higgsfield_call_receipt_v1.json.

Writes to temple/subsandbox/renders/<task_id>/receipts.ndjson.
NEVER writes to town/ledger_v1.ndjson.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "experiments" / "helen_mvp_kernel" / "schemas" / "higgsfield_call_receipt_v1.json"
SUBSANDBOX_RENDERS = REPO_ROOT / "temple" / "subsandbox" / "renders"

# Forbidden write targets — guard against accidental sovereign mutation
FORBIDDEN_TARGETS = {
    REPO_ROOT / "town" / "ledger_v1.ndjson",
}


class SovereignWriteRefused(RuntimeError):
    """Raised if a caller attempts to write a TEMPLE receipt into a sovereign artifact."""


def _load_schema() -> Dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_receipt(receipt: Dict[str, Any]) -> None:
    """Validate against HIGGSFIELD_CALL_RECEIPT_V1.

    Uses jsonschema if available; falls back to manual checks for the
    locks that must hold regardless (scope, sovereign_admitted, schema name).
    """
    if receipt.get("schema") != "HIGGSFIELD_CALL_RECEIPT_V1":
        raise ValueError(f"schema must be HIGGSFIELD_CALL_RECEIPT_V1, got {receipt.get('schema')!r}")
    if receipt.get("scope") != "TEMPLE_SUBSANDBOX":
        raise ValueError(f"scope locked to TEMPLE_SUBSANDBOX, got {receipt.get('scope')!r}")
    if receipt.get("sovereign_admitted") is not False:
        raise ValueError("sovereign_admitted is locked false")

    try:
        import jsonschema  # type: ignore
    except ImportError:
        # Manual check of required fields if jsonschema not installed
        required = {
            "schema", "task_id", "shot_n", "ref_image_sha256", "prompt",
            "prompt_hash", "seed", "duration_s", "returned_url",
            "mp4_sha256", "timestamp_utc", "scope", "sovereign_admitted",
        }
        missing = required - set(receipt.keys())
        if missing:
            raise ValueError(f"missing required fields: {sorted(missing)}")
        return

    schema = _load_schema()
    jsonschema.validate(instance=receipt, schema=schema)


def emit_receipt(receipt: Dict[str, Any], task_id: str) -> Path:
    """Append the receipt to the TEMPLE subsandbox renders ledger."""
    validate_receipt(receipt)

    target_dir = SUBSANDBOX_RENDERS / task_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "receipts.ndjson"

    if target_path.resolve() in {p.resolve() for p in FORBIDDEN_TARGETS if p.exists()}:
        raise SovereignWriteRefused(f"attempted write to sovereign target: {target_path}")

    line = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    with target_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    return target_path
