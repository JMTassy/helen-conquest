"""
helen_os/eval/godmode.py — Godmode aggregator for Town Eval Federation.

Godmode is the terminal layer of the Town Eval Federation. It:
  1. Receives 3 egregore reports (Alpha / Beta / Gamma)
  2. Aggregates their verdicts (conservative: any BLOCK → BLOCK)
  3. Emits a FED_EVAL_V1 receipt via kernel.propose()
  4. Returns a FedEvalV1 artifact (receipt_id + cum_hash anchored)

"No receipt → no federation."

Design invariants:
  - Godmode is the ONLY layer in eval/ that calls kernel.propose().
  - Servitors and egregores are pure (no side effects).
  - The FED_EVAL_V1 receipt payload is compact (summary only, not full tree).
    Full tree is in the FedEvalV1.egregore_reports field.
  - No authority tokens: verdict is an observation, not a command.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from .schemas import EgregorReportV1, FedEvalV1, aggregate_verdict


def run_godmode(
    egregore_reports: List[EgregorReportV1],
    kernel,
) -> FedEvalV1:
    """
    Godmode aggregator — aggregates all egregore reports, emits FED_EVAL_V1 receipt.

    Args:
        egregore_reports: List of EgregorReportV1 (Alpha, Beta, Gamma in order).
        kernel:           GovernanceVM instance. Godmode calls kernel.propose()
                          once to anchor the FED_EVAL_V1 artifact.

    Returns:
        FedEvalV1 with receipt_id and cum_hash from kernel.

    Raises:
        PermissionError: If kernel is sealed (propagated from kernel.propose()).
    """
    run_at = datetime.now(timezone.utc).isoformat()

    # ── Count servitor verdicts across all egregores ───────────────────────────
    all_servitor_reports = []
    for er in egregore_reports:
        all_servitor_reports.extend(er.servitor_reports)

    pass_count  = sum(1 for r in all_servitor_reports if r.verdict == "PASS")
    block_count = sum(1 for r in all_servitor_reports if r.verdict == "BLOCK")
    warn_count  = sum(1 for r in all_servitor_reports if r.verdict == "WARN")
    servitor_count = len(all_servitor_reports)

    # ── Overall verdict — conservative aggregate of egregore verdicts ──────────
    verdict = aggregate_verdict([er.verdict for er in egregore_reports])

    # ── Build compact receipt payload (FED_EVAL_V1) ───────────────────────────
    payload = {
        "type":            "FED_EVAL_V1",
        "egregore_ids":    [er.egregore_id for er in egregore_reports],
        "verdict":         verdict,
        "servitor_count":  servitor_count,
        "pass_count":      pass_count,
        "block_count":     block_count,
        "warn_count":      warn_count,
        "egregore_verdicts": {
            er.egregore_id: er.verdict for er in egregore_reports
        },
        "run_at":          run_at,
    }

    # ── Emit FED_EVAL_V1 receipt ───────────────────────────────────────────────
    receipt = kernel.propose(payload)

    return FedEvalV1(
        egregore_ids     = [er.egregore_id for er in egregore_reports],
        verdict          = verdict,
        egregore_reports = egregore_reports,
        servitor_count   = servitor_count,
        pass_count       = pass_count,
        block_count      = block_count,
        warn_count       = warn_count,
        receipt_id       = receipt.id,
        cum_hash         = receipt.cum_hash,
        run_at           = run_at,
    )
