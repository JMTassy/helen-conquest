"""AUTORESEARCH_EVAL_RECEIPT_V1 — builder and validator.

Law: Evaluation receipts are non-sovereign artifacts.
     They carry deterministic proof of an experimental outcome.
     Authority=NONE. They become receipt payloads in SKILL_PROMOTION_PACKET_V1.

Comparison rules (closed enum):
  gt  — candidate_value >  threshold  → PASS
  gte — candidate_value >= threshold  → PASS
  lt  — candidate_value <  threshold  → PASS  (lower-is-better metrics)
  lte — candidate_value <= threshold  → PASS

Result values (closed enum):
  PASS         — comparison rule satisfied
  FAIL         — comparison rule not satisfied
  INCONCLUSIVE — run was incomplete or environment was compromised

Single responsibility:
  build_eval_receipt()    → construct a valid AUTORESEARCH_EVAL_RECEIPT_V1 dict
  evaluate_result()       → deterministic PASS/FAIL from rule + threshold
  validate_eval_receipt() → schema + invariant check
"""
from __future__ import annotations

from typing import Any

from helen_os.governance.validators import validate_schema


# ── Frozen enums ─────────────────────────────────────────────────────────────

COMPARISON_RULES: frozenset[str] = frozenset({"gt", "gte", "lt", "lte"})
RESULT_VALUES: frozenset[str] = frozenset({"PASS", "FAIL", "INCONCLUSIVE"})


# ── Core pure functions ───────────────────────────────────────────────────────

def evaluate_result(
    candidate_value: float,
    comparison_rule: str,
    threshold: float,
) -> str:
    """
    Pure deterministic evaluation.

    Returns "PASS" or "FAIL" based on comparison_rule applied to
    (candidate_value, threshold).

    Raises:
        ValueError: if comparison_rule is not in COMPARISON_RULES.
    """
    if comparison_rule not in COMPARISON_RULES:
        raise ValueError(
            f"Unknown comparison_rule {comparison_rule!r}. "
            f"Must be one of {sorted(COMPARISON_RULES)}."
        )
    dispatch = {
        "gt":  candidate_value >  threshold,
        "gte": candidate_value >= threshold,
        "lt":  candidate_value <  threshold,
        "lte": candidate_value <= threshold,
    }
    return "PASS" if dispatch[comparison_rule] else "FAIL"


def build_eval_receipt(
    experiment_id: str,
    metric_name: str,
    baseline_value: float,
    candidate_value: float,
    comparison_rule: str,
    threshold: float,
    run_log_hash: str,
    environment_manifest_hash: str,
    doctrine_hash: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Construct a canonical AUTORESEARCH_EVAL_RECEIPT_V1.

    Result is computed deterministically from (candidate_value,
    comparison_rule, threshold) — the caller cannot inject a result.

    Args:
        experiment_id:              Unique run identifier.
        metric_name:                Metric being measured.
        baseline_value:             Metric of baseline (reference).
        candidate_value:            Metric of candidate (new version).
        comparison_rule:            One of {gt, gte, lt, lte}.
        threshold:                  Numeric boundary.
        run_log_hash:               sha256-prefixed hash of raw run log.
        environment_manifest_hash:  sha256-prefixed hash of env manifest.
        doctrine_hash:              sha256-prefixed hash of doctrine/law surface.
        notes:                      Optional non-authoritative notes.

    Returns:
        dict conforming to AUTORESEARCH_EVAL_RECEIPT_V1 schema.

    Raises:
        ValueError: if comparison_rule is invalid.
    """
    result = evaluate_result(candidate_value, comparison_rule, threshold)

    receipt: dict[str, Any] = {
        "schema_name":               "AUTORESEARCH_EVAL_RECEIPT_V1",
        "schema_version":            "1.0.0",
        "experiment_id":             experiment_id,
        "metric_name":               metric_name,
        "baseline_value":            baseline_value,
        "candidate_value":           candidate_value,
        "comparison_rule":           comparison_rule,
        "threshold":                 threshold,
        "result":                    result,
        "run_log_hash":              run_log_hash,
        "environment_manifest_hash": environment_manifest_hash,
        "doctrine_hash":             doctrine_hash,
    }
    if notes is not None:
        receipt["notes"] = notes
    return receipt


def validate_eval_receipt(receipt: Any) -> tuple[bool, str | None]:
    """
    Validate an AUTORESEARCH_EVAL_RECEIPT_V1 against frozen schema +
    structural invariants.

    Returns:
        (True, None)           — valid
        (False, reason_str)    — invalid with reason

    Invariants checked beyond schema:
      I1. comparison_rule ∈ COMPARISON_RULES
      I2. result ∈ RESULT_VALUES
      I3. If result is PASS or FAIL, it must agree with evaluate_result()
          (INCONCLUSIVE is exempt — indicates interrupted run)
    """
    if not isinstance(receipt, dict):
        return False, "receipt is not a dict"

    valid, err = validate_schema(
        "AUTORESEARCH_EVAL_RECEIPT_V1", "1.0.0", receipt
    )
    if not valid:
        return False, err

    # I1: closed comparison_rule enum (also enforced by schema, double-check)
    rule = receipt.get("comparison_rule")
    if rule not in COMPARISON_RULES:
        return False, f"comparison_rule {rule!r} not in {sorted(COMPARISON_RULES)}"

    # I2: closed result enum
    result = receipt.get("result")
    if result not in RESULT_VALUES:
        return False, f"result {result!r} not in {sorted(RESULT_VALUES)}"

    # I3: result coherence (skip INCONCLUSIVE)
    if result != "INCONCLUSIVE":
        expected = evaluate_result(
            receipt["candidate_value"],
            rule,
            receipt["threshold"],
        )
        if result != expected:
            return False, (
                f"result {result!r} is inconsistent with "
                f"evaluate_result({receipt['candidate_value']!r}, "
                f"{rule!r}, {receipt['threshold']!r}) = {expected!r}"
            )

    return True, None
