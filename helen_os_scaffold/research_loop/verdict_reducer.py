"""
research_loop/verdict_reducer.py — Frozen verdict reducer.

HELEN Research Loop v0.1 (MVP_SPEC_V0_1.md §5)

THE ONLY AUTHORITY FUNCTION.
No vibes. No confidence scores. Pure gate logic.
Kill-switch (G_kernel_integrity_ok=False) → QUARANTINE.
Everything else → NO_SHIP with reason codes, or SHIP.

This module must never be changed without re-freezing the MVP spec.
"""
from __future__ import annotations

from typing import List, Optional

from research_loop.run_manifest import GateVectorV1, VerdictV1


# ── Frozen verdict reducer ────────────────────────────────────────────────────

def compute_verdict(
    gates: GateVectorV1,
    law_surface_version: str = "LAW_SURFACE_V1",
    law_surface_hash:    str = "0" * 64,
) -> VerdictV1:
    """
    Deterministic verdict from gate vector.

    Frozen verdict map (MVP_SPEC_V0_1.md §5):

        if not G_kernel_integrity_ok  → QUARANTINE
        if not G_receipts_present     → NO_SHIP [MISSING_RECEIPTS]
        if not G_replay_ok            → NO_SHIP [REPLAY_FAILED]
        if not G_no_blocking_issue    → NO_SHIP [BLOCKING_ISSUE]
        if not G_metric_improved      → NO_SHIP [METRIC_NOT_IMPROVED]
        else                          → SHIP

    QUARANTINE has highest priority (integrity failure).
    All other blocking conditions are accumulated before verdict.
    A support score of 0.99 does not override an open obligation.
    Internal coherence is not admissibility.

    law_surface_version + law_surface_hash: explicitly bind this verdict to
    the legal regime under which it was computed. Any verdict comparison across
    law regimes requires a migration receipt.
    """
    # Highest priority: kernel integrity failure → QUARANTINE
    # (excluded from optimization memory, stored audit-only)
    if not gates.G_kernel_integrity_ok:
        return VerdictV1(
            verdict="QUARANTINE",
            blocking_reason_codes=["KERNEL_INTEGRITY_FAILED"],
            law_surface_version=law_surface_version,
            law_surface_hash=law_surface_hash,
        )

    # Accumulate all remaining blocking reasons
    reasons: List[str] = []

    if not gates.G_receipts_present:
        reasons.append("MISSING_RECEIPTS")

    if not gates.G_replay_ok:
        reasons.append("REPLAY_FAILED")

    if not gates.G_no_blocking_issue:
        reasons.append("BLOCKING_ISSUE")

    if not gates.G_metric_improved:
        reasons.append("METRIC_NOT_IMPROVED")

    if reasons:
        return VerdictV1(
            verdict="NO_SHIP",
            blocking_reason_codes=reasons,
            law_surface_version=law_surface_version,
            law_surface_hash=law_surface_hash,
        )

    return VerdictV1(
        verdict="SHIP",
        blocking_reason_codes=[],
        law_surface_version=law_surface_version,
        law_surface_hash=law_surface_hash,
    )


# ── Metric improvement gate ───────────────────────────────────────────────────

IMPROVEMENT_THRESHOLD: float = 0.002  # +0.2 percentage points minimum

def compute_metric_gate(
    current_metric: float,
    best_admitted_metric: float,
    threshold: float = IMPROVEMENT_THRESHOLD,
) -> bool:
    """
    G_metric_improved:
        True iff current_metric >= best_admitted_metric + threshold.

    Threshold is frozen at 0.002 for MVP.
    Tie-break rule: strictly greater than (best + threshold), not >=.
    i.e., equal improvement does not count as improved.

    Per MVP_SPEC_V0_1.md §4:
        G_metric_improved = 1 iff m_new >= m_best + 0.002
    """
    return current_metric >= best_admitted_metric + threshold


# ── State reducer ─────────────────────────────────────────────────────────────

def reduce_run(
    state: dict,
    manifest,           # RunManifestV1
    gates: GateVectorV1,
) -> tuple[str, dict]:
    """
    Apply one cycle's manifest to the current admitted state.

    Returns (verdict_str, new_state).

    State evolution law (MVP_SPEC_V0_1.md §7):
        s_{t+1} = Admit(s_t, manifest)    if verdict == SHIP
                = s_t                      if verdict == NO_SHIP
                = s_t                      if verdict == QUARANTINE

    Only SHIP mutates best-known optimization state.
    """
    verdict = compute_verdict(gates)

    if verdict.verdict == "SHIP":
        new_state = _admit_shipped_run(state, manifest)
        return "SHIP", new_state

    # NO_SHIP or QUARANTINE: state is unchanged
    return verdict.verdict, state


def _admit_shipped_run(state: dict, manifest) -> dict:
    """
    Compute new admitted state after a SHIP verdict.
    Persists only: best metric, best artifact hash, manifest lineage.
    Never persists: rejected proposals, raw HER output, quarantined artifacts.
    """
    new_state = dict(state)
    new_state["best_metric"] = manifest.evidence.metric_value
    new_state["best_manifest_hash"] = manifest.manifest_hash
    new_state["best_proposal_id"] = manifest.proposal.proposal_id
    new_state["shipped_run_lineage"] = state.get("shipped_run_lineage", []) + [
        manifest.manifest_hash
    ]
    return new_state
