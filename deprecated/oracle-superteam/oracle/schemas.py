# oracle/schemas.py
"""
ORACLE SUPERTEAM — Signal & Obligation Schemas (Hardened Model V1)

This module defines the constitutional data structures that enforce:
- Non-sovereign production (signals only, no votes)
- Deterministic obligation mapping
- Binary verdict semantics

NO AGENT MAY VOTE. ONLY SIGNALS ARE PERMITTED.
"""

from dataclasses import dataclass
from typing import Literal, Optional, List

# ==============================================================================
# SIGNAL TYPES (Non-Sovereign Production Layer)
# ==============================================================================

SignalType = Literal[
    "OBLIGATION_OPEN",      # Request obligation be opened (non-sovereign)
    "RISK_FLAG",            # Surface risk for adjudication review
    "EVIDENCE_WEAK",        # Signal insufficient evidence quality
    "KILL_REQUEST",         # Request kill-switch activation (authorized teams only)
]

# ==============================================================================
# OBLIGATION TYPES (Adjudication Layer)
# ==============================================================================

ObligationType = Literal[
    "METRICS_INSUFFICIENT",     # Need verified quantitative evidence
    "LEGAL_COMPLIANCE",         # Need legal review/compliance attestation
    "SECURITY_THREAT",          # Need security assessment/mitigation
    "EVIDENCE_MISSING",         # Need receipts or attestable proof
    "CONTRADICTION_DETECTED",   # Evidence contradictions must be resolved
]

ObligationStatus = Literal[
    "OPEN",        # Blocking shipment
    "RESOLVED",    # Cleared with evidence
    "INVALIDATED", # No longer applicable
]

# ==============================================================================
# VERDICT STATES (Integration Layer)
# ==============================================================================

VerdictState = Literal[
    "SHIP",      # ship_permitted = True
    "NO_SHIP",   # ship_permitted = False
]

# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass(frozen=True)
class Signal:
    """
    Non-sovereign agent output.

    Signals do NOT directly influence verdicts. They are interpreted
    by the adjudication layer to generate obligations or trigger vetos.

    CRITICAL: Agents emit signals, not votes. Signals have no decision authority.
    """
    team: str                           # Team emitting signal
    signal_type: SignalType             # What kind of signal
    obligation_type: Optional[ObligationType]  # Requested obligation (if OBLIGATION_OPEN)
    rationale: str                      # Human-readable explanation

    def __post_init__(self):
        """Validate signal structure."""
        if self.signal_type == "OBLIGATION_OPEN" and not self.obligation_type:
            raise ValueError("OBLIGATION_OPEN signals must specify obligation_type")


@dataclass(frozen=True)
class Obligation:
    """
    Blocking constraint generated from signals during adjudication.

    Open obligations always block SHIP verdict.
    """
    type: ObligationType
    owner_team: str                     # Team responsible for resolution
    closure_criteria: str               # What evidence/action clears this
    status: ObligationStatus
    opened_by_signal: Optional[str]     # Which signal triggered this (audit trail)


@dataclass(frozen=True)
class Verdict:
    """
    Binary decision output from integration gate.

    SHIP = ship_permitted: true
    NO_SHIP = ship_permitted: false

    No intermediate states exist at verdict time.
    QUARANTINE and KILL are internal classifications that map to NO_SHIP.
    """
    final: VerdictState
    ship_permitted: bool
    reason_codes: List[str]             # Why this verdict was chosen
    internal_state: Optional[str]       # ACCEPT/QUARANTINE/KILL (diagnostic only)

    def __post_init__(self):
        """Enforce binary semantics."""
        if self.final == "SHIP" and not self.ship_permitted:
            raise ValueError("SHIP verdict must have ship_permitted=True")
        if self.final == "NO_SHIP" and self.ship_permitted:
            raise ValueError("NO_SHIP verdict must have ship_permitted=False")


# ==============================================================================
# CLAIM SCHEMA
# ==============================================================================

@dataclass(frozen=True)
class Claim:
    """
    Immutable claim submission.

    Once submitted, claims cannot be modified. All changes require new claims.
    """
    id: str
    assertion: str                      # The claim being made
    tier: Literal["Tier I", "Tier II", "Tier III"]
    domain: List[str]                   # e.g., ["legal", "privacy"]
    owner_team: str
    requires_receipts: bool             # Tier I defaults to True


# ==============================================================================
# EVIDENCE & RECEIPT SCHEMA
# ==============================================================================

@dataclass(frozen=True)
class Evidence:
    """
    Attestable proof supporting or contradicting a claim.

    Evidence must be hashable and verifiable.
    """
    id: str
    type: str                           # e.g., "security_audit", "legal_review"
    tags: List[str]                     # Semantic tags for contradiction detection
    hash: Optional[str]                 # SHA-256 of content (if applicable)
    issuer: Optional[str]               # Who provided this evidence


# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================

AUTHORIZED_KILL_TEAMS = {"Legal Office", "Security Sector"}


def validate_signal(signal: dict) -> bool:
    """
    Validate signal structure before processing.

    Returns True if signal is well-formed, False otherwise.
    """
    if signal.get("signal_type") == "KILL_REQUEST":
        return signal.get("team") in AUTHORIZED_KILL_TEAMS
    return True


def validate_obligation_closure(obligation: Obligation, evidence: List[Evidence]) -> bool:
    """
    Check if provided evidence satisfies obligation closure criteria.

    This is a deterministic function—same inputs always yield same result.
    """
    # Placeholder: Real implementation would check evidence against closure_criteria
    # For now, we mark this as the extension point for evidence verification
    return False  # Conservative: obligations remain open unless explicitly cleared


# ==============================================================================
# BACKWARD COMPATIBILITY MAPPING (TEMPORARY)
# ==============================================================================

VOTE_TO_SIGNAL_MAPPING = {
    "APPROVE": None,  # No signal emitted for pure approval
    "CONDITIONAL": ("OBLIGATION_OPEN", None),  # Maps to obligation based on team
    "OBJECT": ("RISK_FLAG", None),
    "QUARANTINE": ("EVIDENCE_WEAK", "CONTRADICTION_DETECTED"),
    "REJECT": ("EVIDENCE_WEAK", "CONTRADICTION_DETECTED"),
    "KILL": ("KILL_REQUEST", None),
}


def migrate_vote_to_signal(vote: dict) -> dict:
    """
    Convert legacy vote format to signal format.

    This function exists only for backward compatibility during transition.
    New code should emit signals directly.
    """
    team = vote.get("team")
    vote_type = vote.get("vote")
    rationale = vote.get("rationale", "")

    mapping = VOTE_TO_SIGNAL_MAPPING.get(vote_type)

    if mapping is None:
        # APPROVE maps to no signal (implicit support)
        return None

    signal_type, default_obligation = mapping

    # Determine obligation type based on team jurisdiction
    obligation_type = default_obligation
    if signal_type == "OBLIGATION_OPEN" and not obligation_type:
        if team == "Engineering Wing":
            obligation_type = "METRICS_INSUFFICIENT"
        elif team == "Legal Office":
            obligation_type = "LEGAL_COMPLIANCE"
        elif team == "Security Sector":
            obligation_type = "SECURITY_THREAT"
        elif team == "Data Validation Office":
            obligation_type = "METRICS_INSUFFICIENT"
        else:
            obligation_type = "EVIDENCE_MISSING"

    return {
        "team": team,
        "signal_type": signal_type,
        "obligation_type": obligation_type,
        "rationale": rationale,
    }
