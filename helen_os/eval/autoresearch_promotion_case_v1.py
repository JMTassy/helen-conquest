"""AUTORESEARCH_PROMOTION_CASE_V1 — builder and Mayor assembler.

Law:
  Promotion cases are non-sovereign. They carry an evaluation receipt and
  skill proposal. The Mayor assembles a SKILL_PROMOTION_PACKET_V1 from
  this artifact, embeds the eval receipt as a verified receipt, and routes
  the packet through the governance reducer.

Single responsibility:
  build_promotion_case()    → construct AUTORESEARCH_PROMOTION_CASE_V1
  validate_promotion_case() → schema + invariant check
  assemble_promotion_packet() → Mayor step: case → SKILL_PROMOTION_PACKET_V1

Flow:
  AUTORESEARCH_EVAL_RECEIPT_V1
      ↓
  AUTORESEARCH_PROMOTION_CASE_V1   (authority=NONE)
      ↓  assemble_promotion_packet()
  SKILL_PROMOTION_PACKET_V1        (with receipt embedded + sha256 verified)
      ↓  reduce_promotion_packet()
  SKILL_PROMOTION_DECISION_V1
"""
from __future__ import annotations

from typing import Any, Mapping

from helen_os.governance.canonical import sha256_prefixed
from helen_os.governance.validators import validate_schema
from helen_os.eval.autoresearch_eval_receipt_v1 import validate_eval_receipt


# ── Case builder ─────────────────────────────────────────────────────────────

def build_promotion_case(
    case_id: str,
    skill_id: str,
    candidate_version: str,
    parent_skill_id: str,
    parent_version: str,
    eval_receipt: Mapping[str, Any],
    capability_description: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Construct a canonical AUTORESEARCH_PROMOTION_CASE_V1.

    Args:
        case_id:                 Unique case identifier.
        skill_id:                Skill being proposed for promotion.
        candidate_version:       Semver of candidate.
        parent_skill_id:         Parent skill in active_skills.
        parent_version:          Parent skill version.
        eval_receipt:            Valid AUTORESEARCH_EVAL_RECEIPT_V1 dict.
        capability_description:  Optional human-readable description.
        notes:                   Optional non-authoritative notes.

    Returns:
        dict conforming to AUTORESEARCH_PROMOTION_CASE_V1 schema.
    """
    case: dict[str, Any] = {
        "schema_name":      "AUTORESEARCH_PROMOTION_CASE_V1",
        "schema_version":   "1.0.0",
        "case_id":          case_id,
        "skill_id":         skill_id,
        "candidate_version": candidate_version,
        "parent_skill_id":  parent_skill_id,
        "parent_version":   parent_version,
        "eval_receipt":     dict(eval_receipt),
        "authority":        "NONE",
    }
    if capability_description is not None:
        case["capability_description"] = capability_description
    if notes is not None:
        case["notes"] = notes
    return case


def validate_promotion_case(case: Any) -> tuple[bool, str | None]:
    """
    Validate AUTORESEARCH_PROMOTION_CASE_V1 against schema + invariants.

    Invariants beyond schema:
      I1. eval_receipt must itself pass validate_eval_receipt()
      I2. authority must be "NONE"

    Returns:
        (True, None)           — valid
        (False, reason_str)    — invalid with reason
    """
    if not isinstance(case, dict):
        return False, "case is not a dict"

    valid, err = validate_schema(
        "AUTORESEARCH_PROMOTION_CASE_V1", "1.0.0", case
    )
    if not valid:
        return False, err

    # I1: embedded eval receipt must be valid
    receipt_valid, receipt_err = validate_eval_receipt(case.get("eval_receipt", {}))
    if not receipt_valid:
        return False, f"eval_receipt invalid: {receipt_err}"

    # I2: authority invariant
    if case.get("authority") != "NONE":
        return False, f"authority must be 'NONE', got {case.get('authority')!r}"

    return True, None


# ── Mayor assembler ──────────────────────────────────────────────────────────

def assemble_promotion_packet(
    case: Mapping[str, Any],
    active_state: Mapping[str, Any],
    packet_id: str | None = None,
) -> dict[str, Any]:
    """
    Mayor step: AUTORESEARCH_PROMOTION_CASE_V1 → SKILL_PROMOTION_PACKET_V1.

    This is the governed assembly step. It:
      1. Wraps the eval_receipt as a verified receipt (with sha256)
      2. Derives lineage, doctrine_surface, evaluation from the case
      3. Returns a fully-formed SKILL_PROMOTION_PACKET_V1 ready for the reducer

    The assembled packet passes through reduce_promotion_packet() for the
    6 constitutional gates. No state is mutated here.

    Args:
        case:           Valid AUTORESEARCH_PROMOTION_CASE_V1.
        active_state:   Current SKILL_LIBRARY_STATE_V1 (for doctrine extraction).
        packet_id:      Optional packet identifier (defaults to case_id).

    Returns:
        dict conforming to SKILL_PROMOTION_PACKET_V1.
    """
    eval_receipt = case["eval_receipt"]

    # Build wrapped receipt (Mayor receipt: eval provenance)
    receipt_id = f"receipt_eval_{case['case_id']}"
    receipt_payload = {
        "experiment_id":             eval_receipt["experiment_id"],
        "metric_name":               eval_receipt["metric_name"],
        "baseline_value":            eval_receipt["baseline_value"],
        "candidate_value":           eval_receipt["candidate_value"],
        "comparison_rule":           eval_receipt["comparison_rule"],
        "threshold":                 eval_receipt["threshold"],
        "result":                    eval_receipt["result"],
        "run_log_hash":              eval_receipt["run_log_hash"],
        "environment_manifest_hash": eval_receipt["environment_manifest_hash"],
        "doctrine_hash":             eval_receipt["doctrine_hash"],
    }
    receipt_hashable = {"receipt_id": receipt_id, "payload": receipt_payload}
    wrapped_receipt = {
        "receipt_id": receipt_id,
        "payload":    receipt_payload,
        "sha256":     sha256_prefixed(receipt_hashable),
    }

    # Derive evaluation gate values from eval_receipt
    # result==PASS ↔ passed=True
    eval_passed = eval_receipt["result"] == "PASS"

    # Derive capability_manifest_sha256 from eval_receipt
    capability_manifest = {
        "skill_id":       case["skill_id"],
        "version":        case["candidate_version"],
        "eval_receipt":   eval_receipt["experiment_id"],
        "source":         "AUTORESEARCH_PROMOTION_CASE_V1",
        "authority":      "NONE",
    }

    # Build proposal lineage hash
    proposal_content = {
        "case_id":           case["case_id"],
        "skill_id":          case["skill_id"],
        "candidate_version": case["candidate_version"],
        "eval_receipt_hash": sha256_prefixed(eval_receipt),
    }

    _packet_id = packet_id or f"packet_{case['case_id']}"

    return {
        "schema_name":    "SKILL_PROMOTION_PACKET_V1",
        "schema_version": "1.0.0",
        "packet_id":      _packet_id,
        "skill_id":       case["skill_id"],
        "candidate_version": case["candidate_version"],
        "lineage": {
            "parent_skill_id":  case["parent_skill_id"],
            "parent_version":   case["parent_version"],
            "proposal_sha256":  sha256_prefixed(proposal_content),
        },
        "capability_manifest_sha256": sha256_prefixed(capability_manifest),
        "doctrine_surface": {
            "law_surface_version": active_state.get("law_surface_version", "TEMPLE_LAW_V1"),
            "transfer_required":   False,
        },
        "evaluation": {
            "threshold_name":  f"EVAL_{eval_receipt['metric_name'].upper()}",
            "threshold_value": eval_receipt["threshold"],
            "observed_value":  eval_receipt["candidate_value"],
            "passed":          eval_passed,
        },
        "receipts": [wrapped_receipt],
    }
