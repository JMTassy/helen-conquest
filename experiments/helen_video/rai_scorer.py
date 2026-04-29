"""VIDEO_RAI_SCORE_V1 — RAI Innovation Functional for video candidates.

I_RAI = (P_novel * B_receipt * A_reducer) / (eps + L_sovereignty + D_symbolic)

Operational semantics:
  score == 0   if B_receipt == 0  (no binding)
  score == 0   if A_reducer == 0  (not admitted)
  score → 0    as L_sovereignty → ∞  (sovereignty leakage collapses score)
  score → 0    as D_symbolic → ∞     (symbolic drift collapses score)

Canonical invariant:
  Clip enters timeline ⟺ valid receipt + gate ACCEPT + RAI score ≥ threshold
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from helen_video.admissibility_gate import evaluate, verify_receipt_binding, PIPELINE_SALT

DEFAULT_EPS = 1e-6
DEFAULT_ACCEPT_THRESHOLD = 0.5


# ── score components ──────────────────────────────────────────────────────────

def novelty_score(candidate: dict, prior_hashes: set[str] | None = None) -> float:
    """P_novel — how different this candidate is from prior admitted clips.

    Proxy: 1.0 if content_hash has never been admitted before, 0.0 if duplicate.
    Intermediate values reserved for future embedding-based novelty.
    """
    if prior_hashes is None:
        return 1.0
    ch = candidate.get("receipt", {}).get("content_hash") if "receipt" in candidate else None
    if ch is None:
        return 1.0
    return 0.0 if ch in prior_hashes else 1.0


def receipt_binding_score(receipt: dict | None) -> float:
    """B_receipt — 1.0 if cryptographically bound, 0.0 otherwise.

    Binary: either the pipeline_hash is derived from content_hash or it is not.
    No partial credit — a partially forged receipt is a forged receipt.
    """
    if receipt is None:
        return 0.0
    if not {"content_hash", "pipeline_hash"} <= set(receipt.keys()):
        return 0.0
    return 1.0 if verify_receipt_binding(receipt) else 0.0


def reducer_admission_score(verdict_decision: str) -> float:
    """A_reducer — gate decision mapped to [0, 1].

    ACCEPT  → 1.0  (fully admitted)
    PENDING → 0.5  (deferred — insufficient evidence)
    REJECT  → 0.0  (blocked)
    """
    return {"ACCEPT": 1.0, "PENDING": 0.5, "REJECT": 0.0}.get(verdict_decision, 0.0)


def sovereignty_leakage(candidate: dict) -> float:
    """L_sovereignty — detects if the candidate has a delivery path.

    Checks for delivery-related keys that should never appear in a Ralph candidate.
    Any such key is a sovereignty breach — score collapses.
    """
    forbidden = {"deliver", "ship", "export_path", "timeline_position", "final"}
    leak = forbidden & set(candidate.keys())
    return float(len(leak))


def symbolic_drift(candidate: dict) -> float:
    """D_symbolic — detects unbound symbolic content in the candidate.

    A candidate whose prompt contains no content_hash reference (i.e., the
    generative signal is disconnected from any verifiable artifact) has drift > 0.
    Proxy: 1.0 if receipt is absent or unbound, 0.0 if bound.
    """
    receipt = candidate.get("receipt")
    if receipt is None:
        return 1.0
    if not verify_receipt_binding(receipt):
        return 1.0
    return 0.0


# ── main functional ───────────────────────────────────────────────────────────

def rai_score(
    novelty: float,
    receipt_binding: float,
    reducer_admission: float,
    authority_leakage: float,
    symbolic_drift_val: float,
    eps: float = DEFAULT_EPS,
) -> float:
    """I_RAI = (P_novel * B_receipt * A_reducer) / (eps + L_sovereignty + D_symbolic)."""
    numerator = novelty * receipt_binding * reducer_admission
    denominator = eps + authority_leakage + symbolic_drift_val
    return numerator / denominator


@dataclass(frozen=True)
class RAIVerdict:
    score: float
    decision: str          # ACCEPT | PENDING | REJECT
    gate_decision: str
    components: dict


def score_candidate(
    candidate: dict,
    receipt: dict | None,
    prior_hashes: set[str] | None = None,
    accept_threshold: float = DEFAULT_ACCEPT_THRESHOLD,
    eps: float = DEFAULT_EPS,
) -> RAIVerdict:
    """Full RAI evaluation: gate + score + threshold decision.

    Args:
        candidate:        Ralph-generated candidate dict.
        receipt:          Provenance receipt (may be None).
        prior_hashes:     Set of content_hashes already in the ledger.
        accept_threshold: Minimum score for ACCEPT.
        eps:              Denominator floor (avoid division by zero).

    Returns:
        RAIVerdict with score, decision, gate_decision, and all components.
    """
    gate_verdict = evaluate(candidate, receipt)

    P = novelty_score(candidate, prior_hashes)
    B = receipt_binding_score(receipt)
    A = reducer_admission_score(gate_verdict.decision)
    L = sovereignty_leakage(candidate)
    D = symbolic_drift(candidate)

    score = rai_score(P, B, A, L, D, eps=eps)

    if gate_verdict.decision == "REJECT" or score < accept_threshold:
        decision = "REJECT" if gate_verdict.decision == "REJECT" else "PENDING"
    elif gate_verdict.decision == "PENDING":
        decision = "PENDING"
    else:
        decision = "ACCEPT"

    return RAIVerdict(
        score=score,
        decision=decision,
        gate_decision=gate_verdict.decision,
        components={"P_novel": P, "B_receipt": B, "A_reducer": A,
                    "L_sovereignty": L, "D_symbolic": D, "eps": eps},
    )
