"""
adapters/write_gate.py — THE SINGLE SOVEREIGN WRITE CHOKE-POINT.

Rule: This is the only file in the repo that may open storage/*.ndjson for write.

All other modules must go through append_event().
Violations caught by: tests/test_import_firewall.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

ChannelName = Literal["town", "memory", "trace"]

# ── Exceptions ────────────────────────────────────────────────────────────────

class WriteGateError(Exception):
    """Base class for sovereign write-gate errors."""

class MissingReceiptError(WriteGateError):
    """Raised when a sovereign append is attempted without a receipt_id."""

class DialogueLaunderingError(WriteGateError):
    """Raised when a payload tries to cite dialogue directly."""

class SchemaValidationError(WriteGateError):
    """Raised when the minimal payload contract is violated."""

class AppendOnlyViolation(WriteGateError):
    """Raised when a non-append write is attempted."""

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
STORAGE_ROOT = REPO_ROOT / "storage"

CHANNEL_PATHS: dict[ChannelName, Path] = {
    "town":   STORAGE_ROOT / "town"   / "ledger.ndjson",
    "memory": STORAGE_ROOT / "memory" / "memory.ndjson",
    "trace":  STORAGE_ROOT / "trace"  / "run_trace.ndjson",
}

# ── Dialogue laundering rules ─────────────────────────────────────────────────

BANNED_REF_TYPES = {
    "DIALOG_TURN_V1", "DIALOG_LOG", "DIALOG_NDJSON",
    "DIALOGUE_TURN", "DIALOGUE_LOG", "DIALOG_SESSION_V1",
}

ALLOWED_REF_TYPES = {
    "CLAIM_GRAPH_V1", "EVALUATION_RECEIPT", "GATE_RECEIPT",
    "LAW_INSCRIPTION_RECEIPT", "AUTHZ_RECEIPT_V1", "CROSS_RECEIPT_V1",
    "HAL_VERDICT_RECEIPT_V1", "BLOCK_RECEIPT_V1", "POLICY_UPDATE_RECEIPT_V1",
    "TOWN_RECEIPT_V1", "MEMORY_EVENT_V1", "TRACE_EVENT_V1",
    "WORLD_MANIFEST_V1", "SCENARIO_MANIFEST_V1", "EXECUTION_RECEIPT_V1",
}

BANNED_PATH_PATTERNS = (
    "dialog.ndjson", "dialogue.ndjson",
    "helen_os/dialogue/", "helen_os/dialogue", "dialogue/",
)

# ── Canonical JSON / hashing ──────────────────────────────────────────────────

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()

# ── Result ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class WriteGateResult:
    channel: ChannelName
    event_hash: str
    previous_hash: str | None
    cumulative_hash: str
    path: str
    line_no: int

# ── Public API ────────────────────────────────────────────────────────────────

def append_event(
    *,
    channel: ChannelName,
    payload: dict[str, Any],
) -> WriteGateResult:
    """
    The ONLY sanctioned append path to sovereign storage.

    Required minimal payload fields:
      - type: str
      - receipt_id: str
      - refs: optional list[dict]

    Enforces:
      1. Minimal schema contract
      2. No dialogue laundering
      3. Canonical JSON + SHA256 chain
      4. Append-only NDJSON line
    """
    _validate_minimal_payload(payload)
    _assert_no_dialogue_laundering(payload)

    target = CHANNEL_PATHS[channel]
    target.parent.mkdir(parents=True, exist_ok=True)

    previous_hash, next_line_no = _read_previous_hash_and_line_no(target)

    envelope = {
        "channel": channel,
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "previous_hash": previous_hash,
    }

    event_json = canonical_json(envelope)
    event_hash = sha256_hex(event_json)
    cumulative_hash = sha256_hex((previous_hash or "") + event_hash)

    record = {
        "type": "WRITE_GATE_EVENT_V1",
        "channel": channel,
        "event_hash": event_hash,
        "cumulative_hash": cumulative_hash,
        "previous_hash": previous_hash,
        "payload": payload,
        "ts": envelope["ts"],
    }

    _append_ndjson_line(target, canonical_json(record))

    return WriteGateResult(
        channel=channel,
        event_hash=event_hash,
        previous_hash=previous_hash,
        cumulative_hash=cumulative_hash,
        path=str(target),
        line_no=next_line_no,
    )

# ── Validation ────────────────────────────────────────────────────────────────

def _validate_minimal_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise SchemaValidationError("payload must be a dict")
    event_type = payload.get("type")
    if not isinstance(event_type, str) or not event_type.strip():
        raise SchemaValidationError("payload.type must be a non-empty string")
    receipt_id = payload.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        raise MissingReceiptError("payload.receipt_id is required")
    refs = payload.get("refs")
    if refs is not None and not isinstance(refs, list):
        raise SchemaValidationError("payload.refs must be a list if present")

def _assert_no_dialogue_laundering(payload: dict[str, Any]) -> None:
    refs = payload.get("refs", [])
    if isinstance(refs, list):
        for idx, ref in enumerate(refs):
            if not isinstance(ref, dict):
                raise SchemaValidationError(f"payload.refs[{idx}] must be a dict")
            ref_type = ref.get("type")
            if not isinstance(ref_type, str) or not ref_type.strip():
                raise SchemaValidationError(f"payload.refs[{idx}].type must be non-empty")
            if ref_type in BANNED_REF_TYPES:
                raise DialogueLaunderingError(
                    f"payload.refs[{idx}] contains banned ref type '{ref_type}'"
                )
            if ref_type not in ALLOWED_REF_TYPES:
                raise DialogueLaunderingError(
                    f"payload.refs[{idx}] contains unknown ref type '{ref_type}'"
                )
            _scan_string_values(ref, prefix=f"refs[{idx}]")
    _scan_string_values(payload, prefix="payload")

def _scan_string_values(obj: Any, prefix: str, depth: int = 0) -> None:
    if depth > 10:
        return
    if isinstance(obj, dict):
        for key, val in obj.items():
            _scan_string_values(val, prefix=f"{prefix}.{key}", depth=depth + 1)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _scan_string_values(item, prefix=f"{prefix}[{i}]", depth=depth + 1)
    elif isinstance(obj, str):
        lowered = obj.lower()
        for pattern in BANNED_PATH_PATTERNS:
            if pattern.lower() in lowered:
                raise DialogueLaunderingError(
                    f"{prefix} contains banned dialogue reference '{pattern}'"
                )

# ── NDJSON helpers ────────────────────────────────────────────────────────────

def _read_previous_hash_and_line_no(path: Path) -> tuple[str | None, int]:
    if not path.exists():
        return None, 1
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None, 1
    last = json.loads(lines[-1])
    prev = last.get("cumulative_hash")
    if prev is not None and not isinstance(prev, str):
        raise AppendOnlyViolation(f"{path} has invalid cumulative_hash in last line")
    return prev, len(lines) + 1

def _append_ndjson_line(path: Path, line: str) -> None:
    if "\n" in line:
        raise AppendOnlyViolation("NDJSON line must not contain embedded newlines")
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
