"""
helen_os/eval/egregores.py — Egregore aggregators for Town Eval Federation.

An egregore is a composite evaluation entity that aggregates two servitor
reports into a single named verdict.

Egregores:
  Alpha (Foundation)   = T0 (Integrity) + T1 (Manifest)
    "Foundation holds when the ledger chain is intact and all canonical
     artifacts are verifiably present."

  Beta  (Simulation)   = T2 (Replay)    + T3 (Partition)
    "Simulation holds when the governance kernel is deterministic and
     module boundaries are uncrossed."

  Gamma (Sovereignty)  = T4 (Rollback)  + T5 (Claim)
    "Sovereignty holds when sealed state cannot be rolled back and
     the claim graph pipeline is reproducibly stable."

Aggregation rule (inherited from schemas.aggregate_verdict):
  Any BLOCK in servitor reports → Egregore verdict BLOCK
  All PASS                     → Egregore verdict PASS
  Otherwise                    → Egregore verdict WARN

Design:
  - Egregore functions are pure (no side effects, no kernel calls).
  - They receive pre-computed TownReportV1 objects and aggregate.
  - Godmode is the only layer that calls kernel.propose().
"""

from __future__ import annotations

from datetime import datetime, timezone

from .schemas    import EgregorReportV1, TownReportV1, aggregate_verdict


# ── Alpha — Foundation Egregore ───────────────────────────────────────────────

def run_alpha_egregore(t0: TownReportV1, t1: TownReportV1) -> EgregorReportV1:
    """
    Alpha — Foundation Egregore.

    Aggregates:
      T0 (Integrity)  — ledger chain valid, cum_hash non-trivial
      T1 (Manifest)   — canonical artifacts present + verifiable

    A federation cannot proceed without a sound ledger foundation and
    a complete, verifiable artifact manifest.
    """
    verdict = aggregate_verdict([t0.verdict, t1.verdict])
    return EgregorReportV1(
        egregore_id      = "Alpha",
        egregore_name    = "Foundation",
        servitor_ids     = ["T0", "T1"],
        verdict          = verdict,
        servitor_reports = [t0, t1],
        run_at           = datetime.now(timezone.utc).isoformat(),
    )


# ── Beta — Simulation Egregore ────────────────────────────────────────────────

def run_beta_egregore(t2: TownReportV1, t3: TownReportV1) -> EgregorReportV1:
    """
    Beta — Simulation Egregore.

    Aggregates:
      T2 (Replay)     — governance kernel is deterministic
      T3 (Partition)  — eval/ module is isolated from domain-specific imports

    A simulation layer that is not deterministic or not properly isolated
    cannot be used as evidence for governance decisions.
    """
    verdict = aggregate_verdict([t2.verdict, t3.verdict])
    return EgregorReportV1(
        egregore_id      = "Beta",
        egregore_name    = "Simulation",
        servitor_ids     = ["T2", "T3"],
        verdict          = verdict,
        servitor_reports = [t2, t3],
        run_at           = datetime.now(timezone.utc).isoformat(),
    )


# ── Gamma — Sovereignty Egregore ──────────────────────────────────────────────

def run_gamma_egregore(t4: TownReportV1, t5: TownReportV1) -> EgregorReportV1:
    """
    Gamma — Sovereignty Egregore.

    Aggregates:
      T4 (Rollback)   — sealed kernel cannot be mutated (sovereignty is final)
      T5 (Claim)      — CLAIM_GRAPH_V1 pipeline is reproducibly stable

    Sovereignty requires that committed state is immutable (sealed = done)
    and that claim artifacts are deterministically derived from their inputs.
    """
    verdict = aggregate_verdict([t4.verdict, t5.verdict])
    return EgregorReportV1(
        egregore_id      = "Gamma",
        egregore_name    = "Sovereignty",
        servitor_ids     = ["T4", "T5"],
        verdict          = verdict,
        servitor_reports = [t4, t5],
        run_at           = datetime.now(timezone.utc).isoformat(),
    )
