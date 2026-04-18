"""
helen_os/meta/cross_receipt_v1.py — CROSS_RECEIPT_V1 schema + allowlist validator

CROSS_RECEIPT_V1 is the federation receipt type emitted by one Town (source)
to be consumed by another Town (target) as candidate E_adm evidence.

Invariants:
  CR-SELF:      source_town_id != target_town_id  (no self-federation)
  CR-HASH:      ledger_tip_hash + bundle_hash must be 64-char SHA256 hex
  CR-RID:       rid must start with "CR-"
  CR-STATUS:    status ∈ {"PENDING", "ACCEPTED", "REJECTED"}
  CR-ALLOWLIST: source_town_id must appear in the receiving Town's allowlist
                (enforced by validate_cross_receipt_allowlist, not by schema)

Flow:
  1. Town A computes its ledger tip hash (last cum_hash) and bundle hash.
  2. Town A emits CROSS_RECEIPT_V1 (status="PENDING").
  3. Town B receives it → validate_cross_receipt_allowlist(receipt, allowlist).
  4. If valid → status "ACCEPTED"; bundle_hash enters Town B's E_adm candidates.
  5. If invalid → status "REJECTED"; logged in audit but not consumed.

Canyon semantics:
  The stone (Town B policy + allowlist) decides if the river (Town A's receipt)
  has permission to enter. Town B's reducer ignores receipts that don't clear
  the allowlist gate.

Bundle semantics:
  bundle_hash = SHA256 of a canonical bundle artifact (e.g., FED_EVAL_V1 JSON).
  bundle_ref is optional structured metadata pointing to the specific verdict
  or evaluation covered by the bundle. It is informational only — the canonical
  anchor is bundle_hash.

No wall clock. No external entropy. All hashes are deterministic.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, field_validator, model_validator


# ── CrossReceiptStatus ─────────────────────────────────────────────────────────

CrossReceiptStatus = Literal["PENDING", "ACCEPTED", "REJECTED"]


# ── CrossReceiptBundleRef ──────────────────────────────────────────────────────

class CrossReceiptBundleRef(BaseModel):
    """
    Optional structured metadata for the bundle covered by a CROSS_RECEIPT_V1.

    Informational only — the canonical anchor is bundle_hash on the parent receipt.
    Changing verdict_hash_hex or verdict_id here does NOT change bundle_hash.
    """
    verdict_id:       Optional[str] = None  # e.g., "V-a1b2c3d4" from ReducedConclusion
    verdict_hash_hex: Optional[str] = None  # 64-char SHA256 if known
    artifact_type:    Optional[str] = None  # e.g., "FED_EVAL_V1", "EPOCH_MARK_V1"
    notes:            Optional[str] = None


# ── CrossReceiptV1 ─────────────────────────────────────────────────────────────

class CrossReceiptV1(BaseModel):
    """
    CROSS_RECEIPT_V1: cross-town federation receipt.

    Emitted by source Town. Consumed by target Town iff allowlist passes.
    The target Town's reducer treats bundle_hash as E_adm candidate evidence
    only after validate_cross_receipt_allowlist() confirms the source is permitted.

    Hard rules (enforced by model_validator):
      - rid must start with "CR-"
      - source_town_id != target_town_id (no self-loop)
      - ledger_tip_hash and bundle_hash must be exactly 64 lowercase hex chars
      - status must be "PENDING", "ACCEPTED", or "REJECTED"
    """

    type:             str                          = "CROSS_RECEIPT_V1"
    rid:              str                          # e.g., "CR-ab1234ef"
    source_town_id:   str                          # emitting Town
    target_town_id:   str                          # receiving Town
    ledger_tip_hash:  str                          # 64-char SHA256 of source ledger tip (last cum_hash)
    bundle_hash:      str                          # 64-char SHA256 of bundle artifact
    bundle_ref:       Optional[CrossReceiptBundleRef] = None  # informational
    allowlist_hash:   Optional[str]               = None  # 64-char SHA256 of allowlist at emission
    status:           CrossReceiptStatus           = "PENDING"
    notes:            Optional[str]               = None

    @field_validator("rid")
    @classmethod
    def check_rid_prefix(cls, v: str) -> str:
        if not v.startswith("CR-"):
            raise ValueError(
                f"CrossReceiptV1.rid must start with 'CR-', got {v!r}. "
                "Use 'CR-' prefix to distinguish cross-town receipts from other types."
            )
        return v

    @field_validator("ledger_tip_hash", "bundle_hash")
    @classmethod
    def check_hex64(cls, v: str, info: Any) -> str:
        field_name = info.field_name if hasattr(info, "field_name") else "hash field"
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            v_preview = repr(v[:20])
            raise ValueError(
                f"CrossReceiptV1.{field_name} must be exactly 64 lowercase hex chars "
                f"(SHA256). Got: {v_preview}... (len={len(v)})"
            )
        return v

    @field_validator("allowlist_hash")
    @classmethod
    def check_allowlist_hash_hex64(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            v_preview = repr(v[:20])
            raise ValueError(
                f"CrossReceiptV1.allowlist_hash must be 64 lowercase hex chars or None. "
                f"Got: {v_preview}..."
            )
        return v

    @model_validator(mode="after")
    def check_no_self_federation(self) -> "CrossReceiptV1":
        """CR-SELF invariant: source and target must be different towns."""
        if self.source_town_id == self.target_town_id:
            raise ValueError(
                f"CrossReceiptV1.source_town_id == target_town_id == {self.source_town_id!r}. "
                "Self-federation is not permitted (CR-SELF invariant). "
                "A town cannot emit a cross-receipt targeting itself."
            )
        return self

    def to_ledger_payload(self) -> Dict[str, Any]:
        """Receipt-safe payload for GovernanceVM.propose() or audit log."""
        return {
            "type":            self.type,
            "rid":             self.rid,
            "source_town_id":  self.source_town_id,
            "target_town_id":  self.target_town_id,
            "ledger_tip_hash": self.ledger_tip_hash,
            "bundle_hash":     self.bundle_hash,
            "status":          self.status,
            "allowlist_hash":  self.allowlist_hash,
        }

    def accepted(self, notes: Optional[str] = None) -> "CrossReceiptV1":
        """Return a copy with status ACCEPTED."""
        return self.model_copy(update={"status": "ACCEPTED", "notes": notes or self.notes})

    def rejected(self, reason: str) -> "CrossReceiptV1":
        """Return a copy with status REJECTED."""
        return self.model_copy(update={"status": "REJECTED", "notes": reason})


# ── CrossReceiptBindingError ───────────────────────────────────────────────────

class CrossReceiptBindingError(ValueError):
    """
    Raised when a CROSS_RECEIPT_V1 fails allowlist validation.

    Subclasses ValueError so model_validators catch it automatically,
    wrapping it into a ValidationError with a clear message.

    Failure modes:
      - source_town_id not in allowlist
      - allowlist is empty (no towns permitted)
      - bundle_ref.verdict_hash_hex mismatches a provided ReducedConclusion
    """
    pass


# ── validate_cross_receipt_allowlist ──────────────────────────────────────────

def validate_cross_receipt_allowlist(
    receipt:   CrossReceiptV1,
    allowlist: List[str],
) -> None:
    """
    Validate that the cross-receipt's source_town_id is in the allowlist.

    This is the canyon gate for federation: the receiving Town's stone
    (allowlist policy) decides if the source Town's river (receipt) may enter.

    Args:
        receipt:   The CROSS_RECEIPT_V1 claiming to carry evidence.
        allowlist: List of permitted source_town_id values for this target Town.

    Raises:
        CrossReceiptBindingError: If source_town_id is not in the allowlist.
    """
    if not allowlist:
        raise CrossReceiptBindingError(
            f"CROSS_RECEIPT_V1 {receipt.rid!r} from {receipt.source_town_id!r}: "
            "allowlist is empty — no source towns are permitted. "
            "Add at least one source_town_id to the target Town's allowlist."
        )
    if receipt.source_town_id not in allowlist:
        raise CrossReceiptBindingError(
            f"CROSS_RECEIPT_V1 {receipt.rid!r}: source_town_id {receipt.source_town_id!r} "
            f"is not in the target Town's allowlist.\n"
            f"  Allowlist: {allowlist!r}\n"
            "  To permit this source, add its town ID to the allowlist before "
            "re-emitting the cross-receipt."
        )


# ── cross_receipt_bundle_hash ──────────────────────────────────────────────────

def cross_receipt_bundle_hash(payload: Dict[str, Any]) -> str:
    """
    Compute a canonical bundle_hash from a dictionary payload.

    Deterministic: same payload → same hash (sort_keys=True, no wall clock).
    Use this to generate bundle_hash at emission time on Town A.

    Args:
        payload: Any JSON-serializable dict representing the bundle artifact.

    Returns:
        64-char lowercase SHA256 hex string.
    """
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(canonical.encode()).hexdigest()
