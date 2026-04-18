"""
helen_os/meta/authz_receipt.py — AUTHZ_RECEIPT_V1 schema + canyon validator

AUTHZ_RECEIPT_V1 is the receipt-gate for ReducedConclusion.helen_proposal_used=True.

Without a matching AUTHZ_RECEIPT_V1 that binds to the exact
(verdict_id, verdict_hash_hex), helen_proposal_used MUST remain False.

This implements CANYON_AUTHORIZED: the stone explicitly permits a specific
river channel — not by ignoring the gate, but by passing through it with
a signed receipt that names the exact verdict it authorizes.

Invariant (HELEN_PROPOSAL_USE_RECEIPT_GATE_V1):
  helen_proposal_used=True is ONLY valid when:
    1. authz_receipt is present in ReducedConclusion
    2. authz_receipt.refs.verdict_id == conclusion.verdict_id
    3. authz_receipt.refs.verdict_hash_hex == conclusion.verdict_hash_hex

Binding semantics:
  The binding is to an exact (verdict_id, verdict_hash_hex) pair.
  Changing ANY of (quest_id, quest_type, gates, metrics, next_quest_seed)
  changes verdict_hash_hex → invalidates the AUTHZ_RECEIPT_V1.
  This prevents retroactive authorization.

Usage:
  authz = AuthzReceiptV1(
      rid = "R-...",
      refs = AuthzReceiptRef(
          verdict_id       = reduced.verdict_id,
          verdict_hash_hex = reduced.verdict_hash_hex,
      ),
      authorizes = {
          "field": "ReducedConclusion.helen_proposal_used",
          "value": True,
      },
  )
  # Then validate before using:
  validate_authz_binding(authz, reduced.verdict_id, reduced.verdict_hash_hex)
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, model_validator


# ── AuthzReceiptRef ────────────────────────────────────────────────────────────

class AuthzReceiptRef(BaseModel):
    """
    Binding reference: ties an AUTHZ_RECEIPT_V1 to an exact ReducedConclusion.

    Changing ANY field in the ReducedConclusion verdict payload changes
    verdict_hash_hex and therefore invalidates this ref.
    """

    verdict_id:       str   # "V-{verdict_hash_hex[:8]}"
    verdict_hash_hex: str   # 64-char SHA256 of canonical verdict payload


# ── AuthzReceiptV1 ─────────────────────────────────────────────────────────────

class AuthzReceiptV1(BaseModel):
    """
    AUTHZ_RECEIPT_V1: receipt-gate for helen_proposal_used=True.

    Hard rules (enforced by model_validator):
      - authorizes.field MUST be "ReducedConclusion.helen_proposal_used"
      - authorizes.value MUST be True
      - reason_codes MUST include "CANYON_AUTHORIZED"

    The receipt is meaningless without also passing validate_authz_binding(),
    which checks that refs.(verdict_id, verdict_hash_hex) matches the actual
    ReducedConclusion being authorized.
    """

    type:         str                = "AUTHZ_RECEIPT_V1"
    rid:          str                # e.g., "R-ab1234cd"
    refs:         AuthzReceiptRef
    authorizes:   Dict[str, Any]     # {"field": "...", "value": True}
    reason_codes: List[str]          = ["CANYON_AUTHORIZED"]

    @model_validator(mode="after")
    def check_authz_target(self) -> "AuthzReceiptV1":
        """
        Structural invariant: AUTHZ_RECEIPT_V1 can ONLY authorize
        ReducedConclusion.helen_proposal_used = True.
        Any other target or value is rejected at construction time.
        """
        field = self.authorizes.get("field")
        value = self.authorizes.get("value")

        if field != "ReducedConclusion.helen_proposal_used":
            raise ValueError(
                f"AUTHZ_RECEIPT_V1.authorizes.field must be "
                f"'ReducedConclusion.helen_proposal_used', got {field!r}. "
                "This receipt type cannot authorize other fields."
            )

        if value is not True:
            raise ValueError(
                f"AUTHZ_RECEIPT_V1.authorizes.value must be True, got {value!r}. "
                "This receipt type only authorizes setting helen_proposal_used=True."
            )

        if "CANYON_AUTHORIZED" not in self.reason_codes:
            raise ValueError(
                "AUTHZ_RECEIPT_V1.reason_codes must include 'CANYON_AUTHORIZED'. "
                f"Got: {self.reason_codes!r}"
            )

        return self

    def binds_to(self, verdict_id: str, verdict_hash_hex: str) -> bool:
        """
        Return True if this receipt binds to the given (verdict_id, verdict_hash_hex).
        Both fields must match exactly (no partial binding).
        """
        return (
            self.refs.verdict_id       == verdict_id
            and self.refs.verdict_hash_hex == verdict_hash_hex
        )


# ── AuthzBindingError ──────────────────────────────────────────────────────────

class AuthzBindingError(ValueError):
    """
    Raised when an AUTHZ_RECEIPT_V1 does not bind to the claimed verdict.

    Subclasses ValueError so Pydantic model_validators catch it automatically,
    wrapping it in a ValidationError with a clear error message.
    """
    pass


# ── validate_authz_binding ────────────────────────────────────────────────────

def validate_authz_binding(
    authz:            AuthzReceiptV1,
    verdict_id:       str,
    verdict_hash_hex: str,
) -> None:
    """
    Validate that authz binds to the given (verdict_id, verdict_hash_hex) pair.

    This is the canyon gate: the stone decides if the river has permission.

    Args:
        authz:            The AUTHZ_RECEIPT_V1 claiming to authorize.
        verdict_id:       The ReducedConclusion's verdict_id (V-{hash[:8]}).
        verdict_hash_hex: The ReducedConclusion's verdict_hash_hex (64-char SHA256).

    Raises:
        AuthzBindingError: If the binding doesn't match exactly.
    """
    if not authz.binds_to(verdict_id, verdict_hash_hex):
        raise AuthzBindingError(
            f"AUTHZ_RECEIPT_V1 {authz.rid!r} does not bind to this verdict.\n"
            f"  Expected verdict_id:       {verdict_id!r}\n"
            f"  Expected verdict_hash_hex: {verdict_hash_hex[:16]!r}...\n"
            f"  Got refs.verdict_id:       {authz.refs.verdict_id!r}\n"
            f"  Got refs.verdict_hash_hex: {authz.refs.verdict_hash_hex[:16]!r}...\n"
            "Retroactive authorization is not permitted. "
            "The receipt must bind to the exact verdict it authorizes."
        )
