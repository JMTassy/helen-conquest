"""
research_loop/schema_validate.py — Structural schema validator.

HELEN Research Loop v0.1 — Phase B, Step 1.
(MVP_SPEC_V0_1.md §3)

Validates raw dicts (as would be loaded from ledger NDJSON or received from
an external producer) against the frozen artifact schemas.

This is the first gate: before the kernel runs any logic, the artifact must
be structurally valid. An invalid schema means the artifact is QUARANTINED
(or rejected before it reaches the kernel).

Design:
    - No external dependencies (no jsonschema library required).
    - All validation is explicit field-by-field; no magic.
    - Returns a list of SchemaViolation objects, not exceptions.
    - Raises SchemaValidationError only when called through validate_or_raise().
    - Every artifact type has its own validator function.
    - compose_validate_manifest() validates a full RunManifestV1 dict end-to-end.

Frozen field requirements per MVP_SPEC_V0_1.md:
    MISSION_V1: mission_id, domain, objective, metric_name, maximize
    PROPOSAL_V1: proposal_id, proposer, summary, hypothesis,
                 mutable_files (exactly ["ranker.py"]), replay_command
    EXECUTION_RECEIPT_V1: receipt_id, kind, command, artifact_refs
    EVIDENCE_BUNDLE_V1: evidence_id, dataset_hash, metric_name,
                        metric_value, receipt_ids
    ISSUE_LIST_V1: issue_list_id, issues (each: issue_id, severity, code, message)
    GATE_VECTOR_V1: five boolean gates
    VERDICT_V1: verdict, blocking_reason_codes
    RUN_MANIFEST_V1: manifest_version, manifest_id, ts_utc, mission, proposal,
                     receipts, evidence, issues, gates, verdict,
                     parent_manifest_hash, config_hash, environment_hash,
                     model_digest, eval_output_hash, law_surface_version,
                     law_surface_hash, manifest_hash
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

# ── Constants ─────────────────────────────────────────────────────────────────

ALLOWED_RECEIPT_KINDS = frozenset({"command", "metric", "test"})
ALLOWED_ISSUE_SEVERITIES = frozenset({"low", "medium", "high", "blocker"})
ALLOWED_VERDICTS = frozenset({"SHIP", "NO_SHIP", "QUARANTINE"})
ALLOWED_REASON_CODES = frozenset({
    "MISSING_RECEIPTS", "REPLAY_FAILED", "METRIC_NOT_IMPROVED",
    "BLOCKING_ISSUE", "KERNEL_INTEGRITY_FAILED",
})
SHA256_HEX_LEN = 64
SHA256_HEX_CHARS = frozenset("0123456789abcdef")

MVP_MUTABLE_FILES = frozenset({"ranker.py"})
MVP_MANIFEST_VERSION = "RUN_MANIFEST_V1"
MVP_PROPOSER = "HER"
MVP_METRIC_NAME = "top1_accuracy"
MVP_DOMAIN = "retrieval_ranking"


# ── Violation / error types ───────────────────────────────────────────────────

@dataclass(frozen=True)
class SchemaViolation:
    path:    str    # e.g. "proposal.mutable_files[0]"
    code:    str    # e.g. "INVALID_MUTABLE_FILE"
    message: str


class SchemaValidationError(ValueError):
    """Raised when validate_or_raise() is called and violations exist."""
    def __init__(self, violations: List[SchemaViolation]) -> None:
        self.violations = violations
        lines = "\n".join(f"  [{v.code}] {v.path}: {v.message}" for v in violations)
        super().__init__(f"{len(violations)} schema violation(s):\n{lines}")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _check_required_str(d: dict, key: str, path: str, violations: list) -> bool:
    """Add violation if key is missing or not a non-empty string. Returns True if ok."""
    if key not in d:
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="MISSING_FIELD",
            message=f"Required field '{key}' is absent."
        ))
        return False
    if not isinstance(d[key], str) or not d[key].strip():
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="EMPTY_STRING",
            message=f"Field '{key}' must be a non-empty string."
        ))
        return False
    return True


def _check_required_bool(d: dict, key: str, path: str, violations: list) -> None:
    if key not in d:
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="MISSING_FIELD",
            message=f"Required boolean field '{key}' is absent."
        ))
    elif not isinstance(d[key], bool):
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="TYPE_ERROR",
            message=f"Field '{key}' must be bool, got {type(d[key]).__name__}."
        ))


def _check_required_list(d: dict, key: str, path: str, violations: list) -> bool:
    if key not in d:
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="MISSING_FIELD",
            message=f"Required list field '{key}' is absent."
        ))
        return False
    if not isinstance(d[key], list):
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="TYPE_ERROR",
            message=f"Field '{key}' must be a list, got {type(d[key]).__name__}."
        ))
        return False
    return True


def _check_sha256(d: dict, key: str, path: str, violations: list,
                  optional: bool = False) -> None:
    """Validate that a field is a 64-char lowercase hex string (SHA256)."""
    if key not in d:
        if not optional:
            violations.append(SchemaViolation(
                path=f"{path}.{key}", code="MISSING_FIELD",
                message=f"Required hash field '{key}' is absent."
            ))
        return
    val = d[key]
    if not isinstance(val, str):
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="TYPE_ERROR",
            message=f"Hash field '{key}' must be a string."
        ))
        return
    if len(val) != SHA256_HEX_LEN:
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="INVALID_HASH_LENGTH",
            message=f"Hash field '{key}' must be {SHA256_HEX_LEN} chars, got {len(val)}."
        ))
    elif not all(c in SHA256_HEX_CHARS for c in val):
        violations.append(SchemaViolation(
            path=f"{path}.{key}", code="INVALID_HASH_CHARS",
            message=f"Hash field '{key}' must be lowercase hex only."
        ))


# ── Per-artifact validators ───────────────────────────────────────────────────

def validate_mission(d: Any, path: str = "mission") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    for key in ("mission_id", "domain", "objective", "metric_name"):
        _check_required_str(d, key, path, v)
    _check_required_bool(d, "maximize", path, v)
    # MVP domain check
    if d.get("domain") and d["domain"] != MVP_DOMAIN:
        v.append(SchemaViolation(
            f"{path}.domain", "INVALID_DOMAIN",
            f"MVP domain must be {MVP_DOMAIN!r}, got {d['domain']!r}."
        ))
    # MVP metric check
    if d.get("metric_name") and d["metric_name"] != MVP_METRIC_NAME:
        v.append(SchemaViolation(
            f"{path}.metric_name", "INVALID_METRIC",
            f"MVP metric must be {MVP_METRIC_NAME!r}, got {d['metric_name']!r}."
        ))
    return v


def validate_proposal(d: Any, path: str = "proposal") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    for key in ("proposal_id", "proposer", "summary", "hypothesis", "replay_command"):
        _check_required_str(d, key, path, v)
    # mutable_files: must be a list
    if _check_required_list(d, "mutable_files", path, v):
        files = d["mutable_files"]
        if len(files) == 0:
            v.append(SchemaViolation(
                f"{path}.mutable_files", "EMPTY_LIST",
                "mutable_files must contain at least one entry."
            ))
        elif len(files) > 1:
            v.append(SchemaViolation(
                f"{path}.mutable_files", "TOO_MANY_FILES",
                f"MVP: exactly 1 mutable file allowed, got {len(files)}."
            ))
        for i, f in enumerate(files):
            if f not in MVP_MUTABLE_FILES:
                v.append(SchemaViolation(
                    f"{path}.mutable_files[{i}]", "INVALID_MUTABLE_FILE",
                    f"Only {sorted(MVP_MUTABLE_FILES)} allowed, got {f!r}."
                ))
    # proposer check (MVP: must be HER)
    if d.get("proposer") and d["proposer"] != MVP_PROPOSER:
        v.append(SchemaViolation(
            f"{path}.proposer", "INVALID_PROPOSER",
            f"MVP proposer must be {MVP_PROPOSER!r}, got {d['proposer']!r}."
        ))
    # summary length check
    if "summary" in d and isinstance(d["summary"], str) and len(d["summary"]) > 200:
        v.append(SchemaViolation(
            f"{path}.summary", "SUMMARY_TOO_LONG",
            f"summary must be ≤ 200 chars, got {len(d['summary'])}."
        ))
    return v


def validate_receipt(d: Any, path: str = "receipt") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    for key in ("receipt_id", "command"):
        _check_required_str(d, key, path, v)
    # kind
    if "kind" not in d:
        v.append(SchemaViolation(f"{path}.kind", "MISSING_FIELD",
                                 "Required field 'kind' is absent."))
    elif d["kind"] not in ALLOWED_RECEIPT_KINDS:
        v.append(SchemaViolation(f"{path}.kind", "INVALID_KIND",
                                 f"'kind' must be one of {sorted(ALLOWED_RECEIPT_KINDS)}."))
    # optional hashes
    _check_sha256(d, "stdout_sha256", path, v, optional=True)
    _check_sha256(d, "stderr_sha256", path, v, optional=True)
    # artifact_refs: must be a list
    _check_required_list(d, "artifact_refs", path, v)
    return v


def validate_evidence(d: Any, path: str = "evidence") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    for key in ("evidence_id", "metric_name"):
        _check_required_str(d, key, path, v)
    _check_sha256(d, "dataset_hash", path, v)
    # metric_value: must be a float/int
    if "metric_value" not in d:
        v.append(SchemaViolation(f"{path}.metric_value", "MISSING_FIELD",
                                 "Required field 'metric_value' is absent."))
    elif not isinstance(d["metric_value"], (int, float)):
        v.append(SchemaViolation(f"{path}.metric_value", "TYPE_ERROR",
                                 "metric_value must be numeric."))
    # receipt_ids: non-empty list
    if _check_required_list(d, "receipt_ids", path, v):
        if len(d["receipt_ids"]) == 0:
            v.append(SchemaViolation(f"{path}.receipt_ids", "EMPTY_LIST",
                                     "receipt_ids must reference at least one receipt."))
        for i, rid in enumerate(d["receipt_ids"]):
            if not isinstance(rid, str) or not rid.strip():
                v.append(SchemaViolation(f"{path}.receipt_ids[{i}]", "EMPTY_STRING",
                                         "Each receipt_id must be a non-empty string."))
    # MVP metric check
    if d.get("metric_name") and d["metric_name"] != MVP_METRIC_NAME:
        v.append(SchemaViolation(
            f"{path}.metric_name", "INVALID_METRIC",
            f"MVP metric must be {MVP_METRIC_NAME!r}."
        ))
    return v


def validate_issue(d: Any, path: str = "issue") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    for key in ("issue_id", "code", "message"):
        _check_required_str(d, key, path, v)
    if "severity" not in d:
        v.append(SchemaViolation(f"{path}.severity", "MISSING_FIELD",
                                 "Required field 'severity' is absent."))
    elif d["severity"] not in ALLOWED_ISSUE_SEVERITIES:
        v.append(SchemaViolation(f"{path}.severity", "INVALID_SEVERITY",
                                 f"severity must be one of {sorted(ALLOWED_ISSUE_SEVERITIES)}."))
    return v


def validate_issue_list(d: Any, path: str = "issues") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    _check_required_str(d, "issue_list_id", path, v)
    if _check_required_list(d, "issues", path, v):
        for i, issue in enumerate(d["issues"]):
            v.extend(validate_issue(issue, path=f"{path}.issues[{i}]"))
    return v


def validate_gate_vector(d: Any, path: str = "gates") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    for gate in (
        "G_receipts_present", "G_replay_ok", "G_metric_improved",
        "G_no_blocking_issue", "G_kernel_integrity_ok",
    ):
        _check_required_bool(d, gate, path, v)
    return v


def validate_verdict(d: Any, path: str = "verdict") -> List[SchemaViolation]:
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR", "Expected dict.")]
    if "verdict" not in d:
        v.append(SchemaViolation(f"{path}.verdict", "MISSING_FIELD",
                                 "Required field 'verdict' is absent."))
    elif d["verdict"] not in ALLOWED_VERDICTS:
        v.append(SchemaViolation(f"{path}.verdict", "INVALID_VERDICT",
                                 f"verdict must be one of {sorted(ALLOWED_VERDICTS)}."))
    if _check_required_list(d, "blocking_reason_codes", path, v):
        for i, code in enumerate(d["blocking_reason_codes"]):
            if code not in ALLOWED_REASON_CODES:
                v.append(SchemaViolation(
                    f"{path}.blocking_reason_codes[{i}]", "INVALID_REASON_CODE",
                    f"Unknown reason code {code!r}."
                ))
    # Consistency: SHIP + codes, NO_SHIP without codes
    if d.get("verdict") == "SHIP" and d.get("blocking_reason_codes"):
        v.append(SchemaViolation(
            f"{path}.blocking_reason_codes", "SHIP_WITH_BLOCKING_CODES",
            "SHIP verdict must have empty blocking_reason_codes."
        ))
    if d.get("verdict") == "NO_SHIP" and not d.get("blocking_reason_codes"):
        v.append(SchemaViolation(
            f"{path}.blocking_reason_codes", "NO_SHIP_WITHOUT_CODES",
            "NO_SHIP verdict must have at least one blocking_reason_code."
        ))
    # Law surface: optional presence (VerdictV1 has defaults; validate if present)
    if "law_surface_version" in d:
        if not isinstance(d["law_surface_version"], str) or not d["law_surface_version"].strip():
            v.append(SchemaViolation(
                f"{path}.law_surface_version", "EMPTY_STRING",
                "law_surface_version must be a non-empty string."
            ))
    if "law_surface_hash" in d:
        _check_sha256(d, "law_surface_hash", path, v, optional=True)
    return v


def validate_manifest(d: Any, path: str = "manifest") -> List[SchemaViolation]:
    """
    Full structural validation of a RUN_MANIFEST_V1 dict.
    Does NOT verify the manifest_hash (that is the kernel integrity check).
    Does NOT check the parent_manifest_hash chain (that is the ledger's job).

    Returns a list of SchemaViolation objects (empty = valid).
    """
    v: List[SchemaViolation] = []
    if not isinstance(d, dict):
        return [SchemaViolation(path, "TYPE_ERROR",
                                "Manifest must be a dict (JSON object).")]

    # manifest_version
    if "manifest_version" not in d:
        v.append(SchemaViolation(f"{path}.manifest_version", "MISSING_FIELD",
                                 "Required field 'manifest_version' is absent."))
    elif d["manifest_version"] != MVP_MANIFEST_VERSION:
        v.append(SchemaViolation(f"{path}.manifest_version", "INVALID_VERSION",
                                 f"Expected {MVP_MANIFEST_VERSION!r}, got {d['manifest_version']!r}."))

    # top-level string fields
    for key in ("manifest_id", "ts_utc"):
        _check_required_str(d, key, path, v)

    # hash fields — eval_output_hash is required (§4.1 G_replay_ok dependency)
    # law_surface_hash is required (constitutional binding to legal regime)
    for key in ("parent_manifest_hash", "config_hash", "environment_hash",
                "model_digest", "eval_output_hash", "law_surface_hash", "manifest_hash"):
        _check_sha256(d, key, path, v)

    # law_surface_version: required non-empty string (legal regime identifier)
    _check_required_str(d, "law_surface_version", path, v)

    # sub-objects
    if "mission" in d:
        v.extend(validate_mission(d["mission"], path=f"{path}.mission"))
    else:
        v.append(SchemaViolation(f"{path}.mission", "MISSING_FIELD", "Required sub-object missing."))

    if "proposal" in d:
        v.extend(validate_proposal(d["proposal"], path=f"{path}.proposal"))
    else:
        v.append(SchemaViolation(f"{path}.proposal", "MISSING_FIELD", "Required sub-object missing."))

    # receipts: non-empty list
    if "receipts" not in d:
        v.append(SchemaViolation(f"{path}.receipts", "MISSING_FIELD",
                                 "Required field 'receipts' is absent."))
    elif not isinstance(d["receipts"], list):
        v.append(SchemaViolation(f"{path}.receipts", "TYPE_ERROR",
                                 "Field 'receipts' must be a list."))
    elif len(d["receipts"]) == 0:
        v.append(SchemaViolation(f"{path}.receipts", "EMPTY_LIST",
                                 "At least one receipt is required."))
    else:
        for i, r in enumerate(d["receipts"]):
            v.extend(validate_receipt(r, path=f"{path}.receipts[{i}]"))

    if "evidence" in d:
        v.extend(validate_evidence(d["evidence"], path=f"{path}.evidence"))
    else:
        v.append(SchemaViolation(f"{path}.evidence", "MISSING_FIELD", "Required sub-object missing."))

    if "issues" in d:
        v.extend(validate_issue_list(d["issues"], path=f"{path}.issues"))
    else:
        v.append(SchemaViolation(f"{path}.issues", "MISSING_FIELD", "Required sub-object missing."))

    if "gates" in d:
        v.extend(validate_gate_vector(d["gates"], path=f"{path}.gates"))
    else:
        v.append(SchemaViolation(f"{path}.gates", "MISSING_FIELD", "Required sub-object missing."))

    if "verdict" in d:
        v.extend(validate_verdict(d["verdict"], path=f"{path}.verdict"))
    else:
        v.append(SchemaViolation(f"{path}.verdict", "MISSING_FIELD", "Required sub-object missing."))

    # Cross-field: evidence.receipt_ids ⊆ receipt_ids in receipts list
    if "receipts" in d and isinstance(d["receipts"], list) and \
       "evidence" in d and isinstance(d["evidence"], dict):
        receipt_ids = {r.get("receipt_id") for r in d["receipts"]
                       if isinstance(r, dict)}
        evidence_refs = d["evidence"].get("receipt_ids", [])
        if isinstance(evidence_refs, list):
            for ref in evidence_refs:
                if ref not in receipt_ids:
                    v.append(SchemaViolation(
                        f"{path}.evidence.receipt_ids",
                        "DANGLING_EVIDENCE_REFERENCE",
                        f"receipt_id {ref!r} in evidence is not in receipts list."
                    ))

    # Cross-field: blocker issue → G_no_blocking_issue must be False
    if "issues" in d and isinstance(d["issues"], dict) and \
       "gates" in d and isinstance(d["gates"], dict):
        issues_list = d["issues"].get("issues", [])
        has_blocker = any(
            isinstance(i, dict) and i.get("severity") == "blocker"
            for i in issues_list
        )
        gate_val = d["gates"].get("G_no_blocking_issue")
        if has_blocker and gate_val is True:
            v.append(SchemaViolation(
                f"{path}.gates.G_no_blocking_issue",
                "GATE_ISSUE_MISMATCH",
                "Blocker issues present but G_no_blocking_issue=True."
            ))

    return v


def validate_or_raise(d: Any, path: str = "manifest") -> None:
    """
    Validate and raise SchemaValidationError if any violations are found.
    Use this as the pre-flight check before building a RunManifestV1.
    """
    violations = validate_manifest(d, path=path)
    if violations:
        raise SchemaValidationError(violations)


def is_valid_manifest(d: Any) -> bool:
    """Quick boolean check. True if no violations."""
    return len(validate_manifest(d)) == 0
