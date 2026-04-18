"""
helen_os/town/validate/validate_receipt_linkage.py — Receipt linkage validator

Validates the full receipt chain across two receipt types:
  1. AUTHZ_RECEIPT_V1   — binds helen_proposal_used=True to (verdict_id, verdict_hash_hex)
  2. CROSS_RECEIPT_V1   — gates cross-town federation evidence via allowlist

This module combines both checks into a single ReceiptLinkageReport, giving Town
operators a one-call audit surface for the entire L0→L1 receipt spine.

Invariants enforced:
  L-AUTHZ:   If authz_receipt is present, it must bind to (verdict_id, verdict_hash_hex).
  L-CROSS:   If cross_receipt is present, source_town_id must be in allowlist.
  L-BUNDLE:  If cross_receipt.bundle_ref.verdict_hash_hex is present and
             reduced_conclusion is provided, they must match exactly.
  L-NOSELF:  source_town_id != target_town_id (re-checked here for belt+suspenders).

Usage:
    report = validate_receipt_linkage(
        authz_receipt      = authz,         # AuthzReceiptV1 or None
        cross_receipt      = cr,            # CrossReceiptV1 or None
        allowlist          = ["TOWN_A"],    # list of permitted source towns
        verdict_id         = "V-a1b2c3d4", # from ReducedConclusion, or None
        verdict_hash_hex   = "<64-hex>",   # from ReducedConclusion, or None
        reduced_conclusion = rc,            # ReducedConclusion, or None
    )
    assert report.all_pass
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── ReceiptLinkageError ────────────────────────────────────────────────────────

class ReceiptLinkageError(ValueError):
    """
    Raised by validate_receipt_linkage when any linkage invariant fails.

    Subclasses ValueError for Pydantic model_validator compatibility.
    """
    pass


# ── ReceiptLinkageReport ───────────────────────────────────────────────────────

@dataclass
class ReceiptLinkageReport:
    """
    Structured result from validate_receipt_linkage().

    Fields:
      checks:    Dict[check_name → {"pass": bool, "note": str}]
      all_pass:  True iff every check passed.
      errors:    List of error messages (empty if all_pass).
    """
    checks:   Dict[str, Dict[str, Any]] = field(default_factory=dict)
    all_pass: bool                       = True
    errors:   List[str]                  = field(default_factory=list)

    def _record(self, name: str, passed: bool, note: str) -> None:
        self.checks[name] = {"pass": passed, "note": note}
        if not passed:
            self.all_pass = False
            self.errors.append(f"[{name}] {note}")

    def summary(self) -> str:
        lines = [f"ReceiptLinkageReport: {'ALL PASS' if self.all_pass else 'FAIL'}"]
        for name, result in self.checks.items():
            mark = "✓" if result["pass"] else "✗"
            lines.append(f"  {mark} {name}: {result['note']}")
        return "\n".join(lines)


# ── validate_receipt_linkage ───────────────────────────────────────────────────

def validate_receipt_linkage(
    authz_receipt:      Optional[Any]       = None,  # AuthzReceiptV1
    cross_receipt:      Optional[Any]       = None,  # CrossReceiptV1
    allowlist:          Optional[List[str]] = None,
    verdict_id:         Optional[str]       = None,
    verdict_hash_hex:   Optional[str]       = None,
    reduced_conclusion: Optional[Any]       = None,  # ReducedConclusion (duck-typed)
    raise_on_failure:   bool                = False,
) -> ReceiptLinkageReport:
    """
    Validate the full receipt linkage chain.

    Checks performed (each independently):
      L-AUTHZ:   authz_receipt binds to (verdict_id, verdict_hash_hex) if both present.
      L-CROSS:   cross_receipt.source_town_id is in allowlist if cross_receipt present.
      L-BUNDLE:  cross_receipt.bundle_ref.verdict_hash_hex matches reduced_conclusion
                 if both bundle_ref and reduced_conclusion are provided.
      L-NOSELF:  cross_receipt.source_town_id != target_town_id (belt+suspenders).

    Args:
        authz_receipt:      Optional AuthzReceiptV1.
        cross_receipt:      Optional CrossReceiptV1.
        allowlist:          Permitted source_town_ids for the target Town.
        verdict_id:         ReducedConclusion.verdict_id if known.
        verdict_hash_hex:   ReducedConclusion.verdict_hash_hex if known.
        reduced_conclusion: Optional ReducedConclusion (for bundle cross-check).
        raise_on_failure:   If True, raises ReceiptLinkageError on first failure.

    Returns:
        ReceiptLinkageReport with per-check results and all_pass flag.

    Raises:
        ReceiptLinkageError: Only if raise_on_failure=True and a check fails.
    """
    report = ReceiptLinkageReport()

    # ── L-AUTHZ ──────────────────────────────────────────────────────────────
    if authz_receipt is not None and (verdict_id or verdict_hash_hex):
        from helen_os.meta.authz_receipt import validate_authz_binding, AuthzBindingError
        try:
            validate_authz_binding(
                authz_receipt,
                verdict_id       or "",
                verdict_hash_hex or "",
            )
            report._record("L-AUTHZ", True,
                           f"authz_receipt {authz_receipt.rid!r} binds to "
                           f"({verdict_id!r}, {(verdict_hash_hex or '')[:16]!r}...)")
        except AuthzBindingError as exc:
            report._record("L-AUTHZ", False, str(exc))
    elif authz_receipt is None and verdict_id:
        report._record("L-AUTHZ", True,
                       "No authz_receipt provided — L-AUTHZ check skipped (helen_proposal_used=False path).")
    else:
        report._record("L-AUTHZ", True, "L-AUTHZ not applicable (no authz_receipt or no verdict_id).")

    # ── L-CROSS ──────────────────────────────────────────────────────────────
    if cross_receipt is not None:
        from helen_os.meta.cross_receipt_v1 import (
            validate_cross_receipt_allowlist,
            CrossReceiptBindingError,
        )
        effective_allowlist = allowlist or []
        try:
            validate_cross_receipt_allowlist(cross_receipt, effective_allowlist)
            report._record("L-CROSS", True,
                           f"cross_receipt {cross_receipt.rid!r}: "
                           f"source_town_id {cross_receipt.source_town_id!r} "
                           f"is in allowlist {effective_allowlist!r}.")
        except CrossReceiptBindingError as exc:
            report._record("L-CROSS", False, str(exc))
    else:
        report._record("L-CROSS", True, "L-CROSS not applicable (no cross_receipt).")

    # ── L-BUNDLE ─────────────────────────────────────────────────────────────
    if (cross_receipt is not None
            and cross_receipt.bundle_ref is not None
            and cross_receipt.bundle_ref.verdict_hash_hex is not None
            and reduced_conclusion is not None):
        rc_hash = getattr(reduced_conclusion, "verdict_hash_hex", None)
        br_hash = cross_receipt.bundle_ref.verdict_hash_hex
        if rc_hash == br_hash:
            report._record("L-BUNDLE", True,
                           f"bundle_ref.verdict_hash_hex matches "
                           f"ReducedConclusion.verdict_hash_hex ({br_hash[:16]!r}...).")
        else:
            report._record("L-BUNDLE", False,
                           f"bundle_ref.verdict_hash_hex mismatch.\n"
                           f"  bundle_ref:         {br_hash[:16]!r}...\n"
                           f"  reduced_conclusion: {(rc_hash or '')[:16]!r}...\n"
                           "  Cross-receipt bundle_ref must match the actual ReducedConclusion.")
    else:
        report._record("L-BUNDLE", True, "L-BUNDLE not applicable (no cross_receipt bundle_ref or no reduced_conclusion).")

    # ── L-NOSELF ─────────────────────────────────────────────────────────────
    if cross_receipt is not None:
        if cross_receipt.source_town_id == cross_receipt.target_town_id:
            report._record("L-NOSELF", False,
                           f"cross_receipt {cross_receipt.rid!r}: "
                           f"source_town_id == target_town_id == {cross_receipt.source_town_id!r}. "
                           "Self-federation is not permitted (CR-SELF invariant).")
        else:
            report._record("L-NOSELF", True,
                           f"source_town_id {cross_receipt.source_town_id!r} != "
                           f"target_town_id {cross_receipt.target_town_id!r}. CR-SELF satisfied.")
    else:
        report._record("L-NOSELF", True, "L-NOSELF not applicable (no cross_receipt).")

    # ── Raise on failure ─────────────────────────────────────────────────────
    if raise_on_failure and not report.all_pass:
        raise ReceiptLinkageError(
            f"Receipt linkage validation failed:\n" +
            "\n".join(f"  {e}" for e in report.errors)
        )

    return report
