"""
LEGORACLE Gate POC — Minimal obligation-checking validator.

Input:  proposal JSON (structured artifact with obligations + attestations)
Output: decision_record JSON (deterministic SHIP | NO_SHIP)

Contract:
  - Compile required obligations from proposal schema
  - Check attestations/receipts per obligation
  - Emit deterministic verdict with receipt-gap computation
  - Log missing obligations explicitly
  - Same input → identical output hash (replay-safe)

Non-sovereign: this gate proposes a verdict. MAYOR ships.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


def _canon(obj: Any) -> bytes:
    """Canonical JSON: sorted keys, no spaces, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ─── Obligation Registry ──────────────────────────────────────────────────────

# Each schema_name maps to a list of required obligations.
# An obligation is a field path that must be present AND attested (non-empty).
OBLIGATION_REGISTRY: Dict[str, List[str]] = {
    "SKILL_PROMOTION_PACKET_V1": [
        "schema_name",
        "schema_version",
        "packet_id",
        "skill_id",
        "candidate_version",
        "lineage.parent_skill_id",
        "lineage.parent_version",
        "lineage.proposal_sha256",
        "capability_manifest_sha256",
        "doctrine_surface.law_surface_version",
        "evaluation.passed",
        "receipts",  # minItems: 1 enforced
    ],
    "FAILURE_REPORT_V1": [
        "schema_name",
        "schema_version",
        "failure_report_id",
        "failure_class",
        "reason_code",
        "typed_failure.message",
        "typed_failure.detected_at",
    ],
    "EXECUTION_ENVELOPE_V1": [
        "schema_name",
        "schema_version",
        "skill_id",
        "task_id",
        "exit_code",
        "input_canonical_sha256",
        "output_canonical_sha256",
        "trace",
        "wall_time_ms",
    ],
}


def _resolve_path(obj: Any, path: str) -> Any:
    """Resolve a dotted path (e.g., 'lineage.parent_skill_id') against an object."""
    parts = path.split(".")
    cur = obj
    for p in parts:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
        if cur is None:
            return None
    return cur


# ─── Gate ──────────────────────────────────────────────────────────────────────

@dataclass
class ObligationResult:
    path: str
    satisfied: bool
    detail: str


@dataclass
class GateDecision:
    schema_name: str
    verdict: str  # "SHIP" | "NO_SHIP"
    obligations_total: int
    obligations_satisfied: int
    obligations_missing: List[str]
    obligation_results: List[ObligationResult]
    input_hash: str
    decision_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_name": "LEGORACLE_DECISION_V1",
            "schema_version": "1.0.0",
            "proposal_schema": self.schema_name,
            "verdict": self.verdict,
            "obligations_total": self.obligations_total,
            "obligations_satisfied": self.obligations_satisfied,
            "obligations_missing": self.obligations_missing,
            "input_hash": self.input_hash,
            "decision_hash": self.decision_hash,
        }


def evaluate_proposal(proposal: Mapping[str, Any]) -> GateDecision:
    """
    Evaluate a proposal against its obligation registry.

    Deterministic: same proposal JSON → identical GateDecision hash.
    Non-sovereign: emits SHIP/NO_SHIP but does not mutate state.

    Args:
        proposal: structured artifact with schema_name field

    Returns:
        GateDecision with verdict, obligation gap, and deterministic hashes
    """
    input_hash = _sha256(_canon(proposal))

    schema_name = proposal.get("schema_name")
    if not schema_name:
        decision = GateDecision(
            schema_name="UNKNOWN",
            verdict="NO_SHIP",
            obligations_total=1,
            obligations_satisfied=0,
            obligations_missing=["schema_name"],
            obligation_results=[ObligationResult("schema_name", False, "missing schema_name field")],
            input_hash=input_hash,
            decision_hash="",
        )
        decision.decision_hash = _sha256(_canon(decision.to_dict()))
        return decision

    obligations = OBLIGATION_REGISTRY.get(schema_name)
    if obligations is None:
        decision = GateDecision(
            schema_name=schema_name,
            verdict="NO_SHIP",
            obligations_total=1,
            obligations_satisfied=0,
            obligations_missing=[f"registry:{schema_name}"],
            obligation_results=[ObligationResult(
                f"registry:{schema_name}", False,
                f"no obligation registry for schema {schema_name}"
            )],
            input_hash=input_hash,
            decision_hash="",
        )
        decision.decision_hash = _sha256(_canon(decision.to_dict()))
        return decision

    results: List[ObligationResult] = []
    missing: List[str] = []

    for path in obligations:
        value = _resolve_path(proposal, path)
        if path == "receipts":
            # Special: must be non-empty list
            if not isinstance(value, list) or len(value) == 0:
                results.append(ObligationResult(path, False, "receipts empty or missing (NO_RECEIPT = NO_SHIP)"))
                missing.append(path)
            else:
                results.append(ObligationResult(path, True, f"{len(value)} receipt(s) present"))
        elif path.endswith(".passed"):
            # Special: must be True
            if value is not True:
                results.append(ObligationResult(path, False, f"evaluation not passed (got {value})"))
                missing.append(path)
            else:
                results.append(ObligationResult(path, True, "evaluation passed"))
        elif value is None:
            results.append(ObligationResult(path, False, f"missing: {path}"))
            missing.append(path)
        elif isinstance(value, str) and len(value) == 0:
            results.append(ObligationResult(path, False, f"empty string: {path}"))
            missing.append(path)
        else:
            results.append(ObligationResult(path, True, "present"))

    verdict = "SHIP" if len(missing) == 0 else "NO_SHIP"

    decision = GateDecision(
        schema_name=schema_name,
        verdict=verdict,
        obligations_total=len(obligations),
        obligations_satisfied=len(obligations) - len(missing),
        obligations_missing=missing,
        obligation_results=results,
        input_hash=input_hash,
        decision_hash="",
    )
    decision.decision_hash = _sha256(_canon(decision.to_dict()))
    return decision
