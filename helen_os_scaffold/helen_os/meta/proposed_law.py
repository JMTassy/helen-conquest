"""
helen_os/meta/proposed_law.py — PROPOSED_LAW_V1 schema

A ProposedLaw is a candidate for inscription into the GovernanceVM ledger.
It is NON-AUTHORITATIVE until:
  1. All falsifiers tested (must all fail — law holds under test)
  2. Inscribed via GovernanceVM.propose() in Phase C
  3. Receipt bound: (receipt_id, cum_hash) recorded here

Shipability:
  PROPOSED  → REVIEW (not yet inscribed, cannot ship as fact)
  INSCRIBED → SHIPABLE (bound to receipt, can be referenced in SHIP channel)
  REJECTED  → NONSHIPABLE (falsifier passed — law refuted)

Canonical law objects defined here:
  CANYON_NONINTERFERENCE_V1 — same E_adm → same reducer output + ledger append
  HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 — helen_proposal_used=True only with AUTHZ_RECEIPT_V1
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ── LawStatus ──────────────────────────────────────────────────────────────────

class LawStatus(str, Enum):
    PROPOSED  = "PROPOSED"    # Candidate — not yet inscribed
    INSCRIBED = "INSCRIBED"   # Bound to receipt in GovernanceVM ledger
    REJECTED  = "REJECTED"    # Falsifier passed — law refuted


# ── ProposedLawV1 ─────────────────────────────────────────────────────────────

class ProposedLawV1(BaseModel):
    """
    PROPOSED_LAW_V1 schema.

    Candidates for GovernanceVM inscription. Non-authoritative until inscribed.

    Fields:
      law_id:     Unique identifier (e.g., "CANYON_NONINTERFERENCE_V1")
      statement:  The falsifiable claim.
      scope:      Which modules/interfaces this law governs.
      falsifiers: Explicit conditions that would refute the law.
      proof_hint: Evidence that supports the law (INFERRED/OBSERVED passport).
      status:     PROPOSED → INSCRIBED → REJECTED (one-way except PROPOSED→REJECTED)
      receipt_id: Bound when inscribed via GovernanceVM.propose().
      cum_hash:   Bound when inscribed (chain position).
    """

    type:        str               = "PROPOSED_LAW_V1"
    law_id:      str
    statement:   str
    scope:       str               = ""
    falsifiers:  List[str]         = []
    proof_hint:  Optional[str]     = None
    status:      LawStatus         = LawStatus.PROPOSED
    receipt_id:  Optional[str]     = None   # Set when inscribed
    cum_hash:    Optional[str]     = None   # Set when inscribed

    def to_ledger_payload(self) -> Dict[str, Any]:
        """Receipt-safe payload for GovernanceVM.propose()."""
        return {
            "type":       self.type,
            "law_id":     self.law_id,
            "statement":  self.statement,
            "scope":      self.scope,
            "status":     self.status.value,
            "falsifiers": self.falsifiers,
        }

    def law_hash(self) -> str:
        """SHA256 of canonical (law_id + statement + scope). Stable identifier."""
        payload = json.dumps(
            {"law_id": self.law_id, "statement": self.statement, "scope": self.scope},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def inscribed_with(self, receipt_id: str, cum_hash: str) -> "ProposedLawV1":
        """Return a new ProposedLawV1 with status=INSCRIBED and receipt bindings."""
        return self.model_copy(update={
            "status":     LawStatus.INSCRIBED,
            "receipt_id": receipt_id,
            "cum_hash":   cum_hash,
        })

    def rejected(self, reason: str) -> "ProposedLawV1":
        """Return a new ProposedLawV1 with status=REJECTED."""
        return self.model_copy(update={
            "status":     LawStatus.REJECTED,
            "proof_hint": f"REJECTED: {reason}",
        })


# ── Canonical law objects ──────────────────────────────────────────────────────

CANYON_NONINTERFERENCE_V1 = ProposedLawV1(
    law_id    = "CANYON_NONINTERFERENCE_V1",
    statement = (
        "For any two HELEN proposal streams that yield the same admissible "
        "evidence set E_adm under policy P, the reducer output and ledger "
        "transition are identical. Narrative variation (different proposed_laws, "
        "proposed_metrics, notes) cannot affect the sovereign mutation except "
        "via admissible receipts."
    ),
    scope     = "ConclusionReducer + EvaluationGate + GovernanceVM.propose() interface",
    falsifiers = [
        "Two different HELENConclusion proposals with same sim_result (= same E_adm) "
        "produce different ReducedConclusion gates",
        "Same sim_result produces different verdict_hash_hex under deterministic replay "
        "(payload_hash or cum_hash differs when inputs are identical)",
        "Different E_adm (different sim_results) producing same verdict_hash_hex "
        "when the gate values actually differ",
    ],
    proof_hint = (
        "ConclusionReducer.reduce() reads only sim_result for gate computation. "
        "HELENConclusion.proposed_laws/metrics are never consulted by EvaluationGate. "
        "Proven by CN2.1 (gates identical) + CN4.1 (verdict_hash_hex identical)."
    ),
)

HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 = ProposedLawV1(
    law_id    = "HELEN_PROPOSAL_USE_RECEIPT_GATE_V1",
    statement = (
        "ReducedConclusion.helen_proposal_used may be True iff there exists "
        "an admissible AUTHZ_RECEIPT_V1 that explicitly authorizes proposal "
        "inclusion for the corresponding (verdict_id, verdict_hash_hex) pair. "
        "Without such a receipt, helen_proposal_used MUST be False."
    ),
    scope     = "ReducedConclusion schema + AUTHZ_RECEIPT_V1 validator + ConclusionReducer",
    falsifiers = [
        "helen_proposal_used=True with no AUTHZ_RECEIPT_V1 present in the record",
        "helen_proposal_used=True with an AUTHZ_RECEIPT_V1 that binds to a "
        "different (verdict_id, verdict_hash_hex) than the actual ReducedConclusion",
        "AUTHZ_RECEIPT_V1 exists and binds correctly but verdict_hash_hex was "
        "computed from different canonical fields",
    ],
    proof_hint = (
        "ReducedConclusion model_validator enforces: if helen_proposal_used=True, "
        "authz_receipt must exist and validate_authz_binding must pass. "
        "Proven by AR3.1 (valid), AR3.2 (no receipt → fail), AR3.3 (wrong hash → fail)."
    ),
)

LAW_HELEN_BOUNDED_EMERGENCE_V1 = ProposedLawV1(
    law_id    = "LAW_HELEN_BOUNDED_EMERGENCE_V1",
    statement = (
        "HELEN is an emergent coordination protocol with a frozen constitutional core. "
        "She operates in two distinct modes: CORE (exploratory, non-authoritative — "
        "may generate novel hypotheses, proposals, and patterns freely) and SHIP "
        "(authoritative — may persist state mutations only after required gates pass). "
        "Constitutional constraints (S1–S4, canyon law, receipt schema) are immutable "
        "regardless of mode. HELEN cannot self-authorize any world-effecting action; "
        "she can only make it structurally undeniable that an action should ship."
    ),
    scope     = (
        "HELEN_OS + helen_dialog + GovernanceVM interface + HER/HAL dyad + "
        "Autonomy Loop (action_executor.py + action_policy.json) + "
        "Federation gossip layer (gossip_protocol.py)"
    ),
    falsifiers = [
        "A ledger or kernel write occurs while mode=CORE (no gate receipts present).",
        "SHIP mode persists a state mutation when MayorCheck returns FAIL.",
        "SHIP mode persists a state mutation when AuthorityScan finds a forbidden token "
        "(SHIP / SEALED / APPROVED / FINAL) in the pre-gate output.",
        "SHIP mode persists a state mutation without a bound receipt_id.",
        "A federation gossip emission occurs without required gates and a receipt.",
        "HELEN marks her own output as APPROVED, SEALED, or SHIP without an external gate receipt.",
        "A constitutional constraint (S1–S4) is altered by a CORE or SHIP output "
        "without a human-sealed GovernanceVM inscription.",
    ],
    proof_hint = (
        "S1 (DRAFTS ONLY) already enforces no world effect without human seal. "
        "action_policy.json maps all mutations to 'gated' or 'prohibited' jurisdiction. "
        "authority_bleed_scan() in her_hal_split.py blocks forbidden authority tokens. "
        "EPOCH4 4-log contract (LOG_D authority scan) enforces pre-gate scanning. "
        "Alignment with CANYON_NONINTERFERENCE_V1: same E_adm → same sovereign output; "
        "HELEN's emergent CORE proposals cannot alter the sovereign gate computation."
    ),
)
