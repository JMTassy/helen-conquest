# oracle/obligations_v2.py
"""
ORACLE SUPERTEAM — Obligation Engine V2 (Signal-Based)

This module replaces vote-based obligation generation with signal-based
deterministic obligation mapping.

KEY PRINCIPLE: Signals do not decide. They only trigger obligations.
The adjudication layer interprets signals and generates obligations.
"""

from typing import List, Dict, Optional


def obligations_from_signals(signals: List[dict]) -> List[dict]:
    """
    Deterministic mapping from signals to obligations.

    Signals are non-sovereign: they request obligations but do not create them directly.
    The adjudication layer evaluates the signal and decides whether to open an obligation.

    Signal Types → Obligation Mapping:
    - OBLIGATION_OPEN → Domain-specific obligation based on team jurisdiction
    - RISK_FLAG → No obligation (flagged for review only)
    - EVIDENCE_WEAK → CONTRADICTION_DETECTED or EVIDENCE_MISSING
    - KILL_REQUEST → No obligation (processed as kill-switch)

    Returns:
        List of obligation dicts with deterministic structure
    """
    obligations = []

    for signal in signals:
        if signal is None:  # APPROVE signals map to None
            continue

        team = signal.get("team")
        signal_type = signal.get("signal_type")
        requested_obligation = signal.get("obligation_type")
        rationale = signal.get("rationale", "")

        # Process signal based on type
        if signal_type == "OBLIGATION_OPEN":
            # Agent requests obligation be opened
            # Adjudication layer validates and opens if justified
            obligation_type = requested_obligation or _infer_obligation_type(team)
            obligations.append((obligation_type, team, rationale))

        elif signal_type == "EVIDENCE_WEAK":
            # Evidence quality signal
            obligation_type = requested_obligation or "CONTRADICTION_DETECTED"
            obligations.append((obligation_type, team, rationale))

        elif signal_type == "RISK_FLAG":
            # Risk flags don't open obligations automatically
            # They're logged for audit but don't block
            pass

        elif signal_type == "KILL_REQUEST":
            # Kill requests are processed separately in adjudication
            # They don't create obligations, they trigger immediate veto
            pass

    # Deduplicate deterministically
    return _deduplicate_obligations(obligations)


def _infer_obligation_type(team: str) -> str:
    """
    Deterministic team-to-obligation mapping.

    This is a fallback when signal doesn't specify obligation_type.
    """
    mapping = {
        "Engineering Wing": "METRICS_INSUFFICIENT",
        "Legal Office": "LEGAL_COMPLIANCE",
        "Security Sector": "SECURITY_THREAT",
        "Data Validation Office": "METRICS_INSUFFICIENT",
    }
    return mapping.get(team, "EVIDENCE_MISSING")


def _deduplicate_obligations(obligations: List[tuple]) -> List[dict]:
    """
    Remove duplicate obligations while preserving deterministic order.

    Args:
        obligations: List of (type, owner_team, rationale) tuples

    Returns:
        List of obligation dicts, deduplicated by (type, owner_team)
    """
    seen = set()
    out = []

    for (typ, owner, rationale) in obligations:
        key = (typ, owner)
        if key in seen:
            continue
        seen.add(key)

        out.append({
            "type": typ,
            "owner_team": owner,
            "closure_criteria": rationale or f"Resolve {typ} flagged by {owner}.",
            "status": "OPEN",
            "opened_by": "signal",  # Audit trail
        })

    return out


def add_contradiction_obligations(contradictions: List[dict],
                                   existing_obligations: List[dict]) -> List[dict]:
    """
    Add contradiction-derived obligations if contradictions detected.

    Contradictions are detected from evidence tags, not from signals.
    This is a deterministic rule application.

    Args:
        contradictions: List of contradiction dicts from contradictions.py
        existing_obligations: Current obligation list

    Returns:
        Updated obligation list with contradiction obligations added
    """
    if not contradictions:
        return existing_obligations

    # Only add if not already present
    has_contradiction_obligation = any(
        o["type"] == "CONTRADICTION_DETECTED"
        for o in existing_obligations
    )

    if has_contradiction_obligation:
        return existing_obligations

    existing_obligations = list(existing_obligations)
    existing_obligations.append({
        "type": "CONTRADICTION_DETECTED",
        "owner_team": "Data Validation Office",
        "closure_criteria": "Resolve detected evidence-tag contradictions.",
        "status": "OPEN",
        "opened_by": "rule",  # Opened by system rule, not signal
    })

    return existing_obligations


# ==============================================================================
# BACKWARD COMPATIBILITY: Vote-to-Signal Migration
# ==============================================================================

def migrate_votes_to_signals(votes: List[dict]) -> List[dict]:
    """
    Convert legacy vote format to signal format.

    This function exists only for backward compatibility.
    New code should emit signals directly.

    Vote → Signal Mapping:
    - APPROVE → None (no signal)
    - CONDITIONAL → OBLIGATION_OPEN
    - OBJECT → RISK_FLAG
    - QUARANTINE → EVIDENCE_WEAK
    - REJECT → EVIDENCE_WEAK
    - KILL → KILL_REQUEST

    Returns:
        List of signal dicts (None values filtered out)
    """
    from oracle.schemas import migrate_vote_to_signal

    signals = []
    for vote in votes:
        signal = migrate_vote_to_signal(vote)
        if signal is not None:
            signals.append(signal)

    return signals


def obligations_from_votes_compat(votes: List[dict]) -> List[dict]:
    """
    Compatibility shim: convert votes to signals, then to obligations.

    This function maintains backward compatibility with existing test vault.

    Args:
        votes: Legacy vote-format list

    Returns:
        Obligations list (same format as obligations_from_signals)
    """
    signals = migrate_votes_to_signals(votes)
    return obligations_from_signals(signals)
