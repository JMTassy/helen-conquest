"""Phase 0 receipt emitters.

Validates against schema drafts at
experiments/helen_mvp_kernel/schemas/{h_n_spectral,phi_sde_trace,research_run}_receipt_v1.json.

Writes to temple/subsandbox/research/<problem_id>/.
NEVER writes to town/ledger_v1.ndjson.
NEVER writes to temple/subsandbox/renders/  (blocked path per HAL verdict).
"""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = REPO_ROOT / "experiments" / "helen_mvp_kernel" / "schemas"
SUBSANDBOX_RESEARCH = REPO_ROOT / "temple" / "subsandbox" / "research"

# Forbidden write targets — guard against accidental sovereign / mis-scoped writes
FORBIDDEN_TARGETS = {
    REPO_ROOT / "town" / "ledger_v1.ndjson",
    REPO_ROOT / "temple" / "subsandbox" / "renders",
}


class SovereignWriteRefused(RuntimeError):
    """Raised on any attempt to write outside the research subsandbox path."""


def now_utc_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_obj(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_vector(v: List[float], precision: int) -> str:
    """Hash a numeric vector by canonical-JSON of rounded entries."""
    rounded = [round(x, precision) for x in v]
    return sha256_obj(rounded)


def hash_matrix(M: List[List[float]], precision: int) -> str:
    rounded = [[round(x, precision) for x in row] for row in M]
    return sha256_obj(rounded)


def _validate_lock(receipt: Dict[str, Any], schema_const: str) -> None:
    if receipt.get("schema") != schema_const:
        raise ValueError(
            f"schema must be {schema_const}, got {receipt.get('schema')!r}"
        )
    if receipt.get("scope") != "RESEARCH_SUBSANDBOX":
        raise ValueError(
            f"scope locked to RESEARCH_SUBSANDBOX, got {receipt.get('scope')!r}"
        )
    if receipt.get("sovereign_admitted") is not False:
        raise ValueError("sovereign_admitted is locked false")
    if receipt.get("decimal_precision") != 12:
        raise ValueError(
            f"decimal_precision locked to 12, got {receipt.get('decimal_precision')!r}"
        )


def _validate_required(receipt: Dict[str, Any], schema_path: Path) -> None:
    """Best-effort validation. Uses jsonschema if available; manual fallback otherwise."""
    try:
        import jsonschema  # type: ignore
    except ImportError:
        with schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        required = set(schema.get("required", []))
        missing = required - set(receipt.keys())
        if missing:
            raise ValueError(f"missing required fields: {sorted(missing)}")
        return

    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=receipt, schema=schema)


def validate_h_n_spectral(receipt: Dict[str, Any]) -> None:
    _validate_lock(receipt, "H_N_SPECTRAL_RECEIPT_V1")
    _validate_required(receipt, SCHEMA_DIR / "h_n_spectral_receipt_v1.json")


def validate_phi_sde_trace(receipt: Dict[str, Any]) -> None:
    _validate_lock(receipt, "PHI_SDE_TRACE_RECEIPT_V1")
    _validate_required(receipt, SCHEMA_DIR / "phi_sde_trace_receipt_v1.json")


def validate_research_run(receipt: Dict[str, Any]) -> None:
    _validate_lock(receipt, "RESEARCH_RUN_RECEIPT_V1")
    _validate_required(receipt, SCHEMA_DIR / "research_run_receipt_v1.json")


def _safe_target(target: Path) -> None:
    """Refuse forbidden targets."""
    target_resolved = target.resolve()
    for f in FORBIDDEN_TARGETS:
        try:
            f_resolved = f.resolve(strict=False)
        except Exception:
            continue
        # Direct match or descendant
        if target_resolved == f_resolved:
            raise SovereignWriteRefused(f"forbidden write target: {target}")
        try:
            target_resolved.relative_to(f_resolved)
        except ValueError:
            continue
        else:
            raise SovereignWriteRefused(f"forbidden write target (descendant): {target}")


def emit_h_n_spectral_receipt(receipt: Dict[str, Any], problem_id: str) -> Path:
    validate_h_n_spectral(receipt)
    target_dir = SUBSANDBOX_RESEARCH / problem_id
    _safe_target(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "h_n_spectral_receipt.json"
    _safe_target(path)
    path.write_text(
        canonical_json(receipt) + "\n", encoding="utf-8"
    )
    return path


def emit_phi_sde_trace_receipt(receipt: Dict[str, Any], problem_id: str) -> Path:
    validate_phi_sde_trace(receipt)
    target_dir = SUBSANDBOX_RESEARCH / problem_id
    _safe_target(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "phi_sde_trace_receipt.json"
    _safe_target(path)
    path.write_text(
        canonical_json(receipt) + "\n", encoding="utf-8"
    )
    return path


def emit_research_run_receipt(receipt: Dict[str, Any], problem_id: str) -> Path:
    validate_research_run(receipt)
    target_dir = SUBSANDBOX_RESEARCH / problem_id
    _safe_target(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "research_run_receipt.json"
    _safe_target(path)
    path.write_text(
        canonical_json(receipt) + "\n", encoding="utf-8"
    )
    return path
