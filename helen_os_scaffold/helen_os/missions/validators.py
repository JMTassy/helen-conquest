"""
helen_os/missions/validators.py — Structural invariant checks for V1 artifacts.

Validates proposals, missions, steps, and receipts against structural invariants.
Pure functions; no I/O, no side effects.

Invariants checked:
  - artifact_type is correct
  - Required fields are present and non-empty
  - Enum values are in permitted sets
  - Cross-field consistency (e.g. step_ids length)
"""
from __future__ import annotations

from typing import Any

ALLOWED_STEP_KINDS = frozenset({"analyze", "write", "check", "simulate", "compile", "review"})
ALLOWED_PROPOSAL_STATUSES = frozenset({"pending", "promotable", "rejected"})
ALLOWED_MISSION_STATUSES = frozenset({"pending", "running", "succeeded", "failed"})
ALLOWED_STEP_STATUSES = frozenset({"queued", "running", "succeeded", "failed"})
ALLOWED_RECEIPT_STATUSES = frozenset({"ok", "fail"})
ALLOWED_RISK_TIERS = frozenset({"low", "medium", "high", "critical"})


# ── Proposal ─────────────────────────────────────────────────────────────────

def validate_proposal(p: dict[str, Any]) -> list[str]:
    """
    Return list of violation strings.  Empty list = valid.

    Required fields: artifact_type, proposal_id, source, title, goal,
                     step_kinds, input_refs, risk_tier, status
    """
    violations: list[str] = []

    if p.get("artifact_type") != "PROPOSAL_V1":
        violations.append(f"artifact_type must be PROPOSAL_V1, got {p.get('artifact_type')!r}")

    for field in ("proposal_id", "source", "title", "goal"):
        if not p.get(field):
            violations.append(f"missing or empty field: {field!r}")

    step_kinds = p.get("step_kinds")
    if not step_kinds:
        violations.append("step_kinds must be non-empty list")
    else:
        bad = [k for k in step_kinds if k not in ALLOWED_STEP_KINDS]
        if bad:
            violations.append(f"invalid step_kinds: {bad}")

    if p.get("risk_tier") not in ALLOWED_RISK_TIERS:
        violations.append(
            f"risk_tier must be one of {sorted(ALLOWED_RISK_TIERS)}, "
            f"got {p.get('risk_tier')!r}"
        )

    if p.get("status") not in ALLOWED_PROPOSAL_STATUSES:
        violations.append(
            f"status must be one of {sorted(ALLOWED_PROPOSAL_STATUSES)}, "
            f"got {p.get('status')!r}"
        )

    return violations


# ── Mission ───────────────────────────────────────────────────────────────────

def validate_mission(m: dict[str, Any]) -> list[str]:
    """
    Required: artifact_type, mission_id, source_proposal_id, goal, status, step_ids.
    step_ids must be a non-empty list.
    """
    violations: list[str] = []

    if m.get("artifact_type") != "MISSION_V1":
        violations.append(f"artifact_type must be MISSION_V1, got {m.get('artifact_type')!r}")

    for field in ("mission_id", "source_proposal_id", "goal"):
        if not m.get(field):
            violations.append(f"missing or empty field: {field!r}")

    if m.get("status") not in ALLOWED_MISSION_STATUSES:
        violations.append(
            f"status must be one of {sorted(ALLOWED_MISSION_STATUSES)}, "
            f"got {m.get('status')!r}"
        )

    step_ids = m.get("step_ids")
    if not isinstance(step_ids, list) or len(step_ids) == 0:
        violations.append("step_ids must be a non-empty list")

    return violations


# ── Step ──────────────────────────────────────────────────────────────────────

def validate_step(s: dict[str, Any]) -> list[str]:
    """
    Required: artifact_type, step_id, mission_id, step_kind, status.
    output_refs and receipt_refs must be lists.
    """
    violations: list[str] = []

    if s.get("artifact_type") != "MISSION_STEP_V1":
        violations.append(f"artifact_type must be MISSION_STEP_V1, got {s.get('artifact_type')!r}")

    for field in ("step_id", "mission_id"):
        if not s.get(field):
            violations.append(f"missing or empty field: {field!r}")

    if s.get("step_kind") not in ALLOWED_STEP_KINDS:
        violations.append(
            f"step_kind must be one of {sorted(ALLOWED_STEP_KINDS)}, "
            f"got {s.get('step_kind')!r}"
        )

    if s.get("status") not in ALLOWED_STEP_STATUSES:
        violations.append(
            f"status must be one of {sorted(ALLOWED_STEP_STATUSES)}, "
            f"got {s.get('status')!r}"
        )

    for list_field in ("output_refs", "receipt_refs"):
        val = s.get(list_field)
        if val is not None and not isinstance(val, list):
            violations.append(f"{list_field!r} must be a list, got {type(val).__name__}")

    return violations


# ── Receipt ───────────────────────────────────────────────────────────────────

def validate_receipt(r: dict[str, Any]) -> list[str]:
    """
    Required: artifact_type, receipt_id, mission_id, step_id, worker_id,
              status, input_hash, output_hash.
    status must be 'ok' or 'fail'.
    input_hash and output_hash must be non-empty strings.
    """
    violations: list[str] = []

    if r.get("artifact_type") != "EXECUTION_RECEIPT_V1":
        violations.append(
            f"artifact_type must be EXECUTION_RECEIPT_V1, got {r.get('artifact_type')!r}"
        )

    for field in ("receipt_id", "mission_id", "step_id", "worker_id"):
        if not r.get(field):
            violations.append(f"missing or empty field: {field!r}")

    if r.get("status") not in ALLOWED_RECEIPT_STATUSES:
        violations.append(
            f"status must be 'ok' or 'fail', got {r.get('status')!r}"
        )

    for hash_field in ("input_hash", "output_hash"):
        val = r.get(hash_field)
        if not isinstance(val, str) or len(val) < 8:
            violations.append(f"{hash_field!r} must be a non-empty hex string")

    return violations


# ── Convenience assertion helpers ─────────────────────────────────────────────

def assert_valid_proposal(p: dict[str, Any]) -> None:
    """Raise ValueError if proposal has violations."""
    viols = validate_proposal(p)
    if viols:
        raise ValueError(f"Invalid PROPOSAL_V1: {viols}")


def assert_valid_mission(m: dict[str, Any]) -> None:
    """Raise ValueError if mission has violations."""
    viols = validate_mission(m)
    if viols:
        raise ValueError(f"Invalid MISSION_V1: {viols}")


def assert_valid_step(s: dict[str, Any]) -> None:
    """Raise ValueError if step has violations."""
    viols = validate_step(s)
    if viols:
        raise ValueError(f"Invalid MISSION_STEP_V1: {viols}")


def assert_valid_receipt(r: dict[str, Any]) -> None:
    """Raise ValueError if receipt has violations."""
    viols = validate_receipt(r)
    if viols:
        raise ValueError(f"Invalid EXECUTION_RECEIPT_V1: {viols}")
