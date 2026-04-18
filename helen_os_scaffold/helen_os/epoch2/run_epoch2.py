"""
helen_os/epoch2/run_epoch2.py — EPOCH2 canonical learning loop orchestrator.

Wires Steps A→E into one deterministic execution.

  A. Hypothesis bank (3 pre-written hypotheses)
  B. Deterministic sim run (ConquestLandWorld, seed, ticks)
  C. Extract 5 metrics (EpochMetricsCollector)
  D. Sigma gate (SigmaGate across [42, 7, 99])
  E. Inscribe passing laws → LAW_V1 receipts (LawLedger)
  + TOWN_BIRTH_PREDICATE_V1 evaluated and receipted for all 10 factions

Default: seed=42, ticks=20. Expected outcome: closure_success=True, 3 laws.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ── Hypothesis bank (Step A) ─────────────────────────────────────────────────
#
# Each hypothesis is a dict with:
#   id         — short identifier
#   text       — single-sentence claim (what HELEN hypothesises before running)
#   metric_fn  — Callable[[Metrics], float] extracting the tested value
#   metric_name — human-readable name for sigma gate output
#   threshold  — all seeds must yield metric_fn(metrics) >= threshold
#   law_text   — law statement inscribed if sigma gate passes
#
# WHY THESE THREE?
#
# H1 (admissibility_rate >= 0.80):
#   The anti-replay scheme uses per-(faction, evidence_type, tick) rids.
#   Since rids are unique by construction, anti-replay blocks are near-zero.
#   This is a structural invariant discoverable only by running the sim.
#
# H2 (closure_success): With the proactive escort (F3 siege_critical path),
#   the expedition completes in 20 ticks for all standard seeds.
#   This proves the Avalon→Vault path is viable under normal conditions.
#
# H3 (sovereignty_drift == 0):
#   All governance receipts (oath_pass, cleansing, fog_pass, return_warrant)
#   are issued by home-town factions only. No cross-faction governance.
#   "Sovereignty is home-bounded" — a constitutional invariant.

HYPOTHESES = [
    {
        "id":          "H1",
        "text":        (
            "admissibility_rate >= 0.80 across seed set [42,7,99]: "
            "the anti-replay scheme does not over-block legitimate evidence"
        ),
        "metric_fn":   lambda m: m.admissibility_rate,
        "metric_name": "admissibility_rate",
        "threshold":   0.80,
        "law_text":    (
            "LAW-H1: admissibility_rate >= 0.80 in all standard runs. "
            "Per-(faction, evidence_type, tick) rids produce near-zero anti-replay blocks. "
            "Evidence pipeline integrity is structurally guaranteed."
        ),
    },
    {
        "id":          "H2",
        "text":        (
            "closure_success == True in 20-tick runs: "
            "expedition reaches Vault of Return when F3 escorts on siege_critical"
        ),
        "metric_fn":   lambda m: float(m.closure_success),
        "metric_name": "closure_success",
        "threshold":   1.0,
        "law_text":    (
            "LAW-H2: closure_success == True for seeds [42,7,99] in 20 ticks. "
            "The proactive escort (F3, siege_distance <= 1) closes the T2→T3 gap, "
            "making the Avalon→Vault path viable without wolf engagement. "
            "Constitutional closure is structurally achievable."
        ),
    },
    {
        "id":          "H3",
        "text":        (
            "sovereignty_drift_index == 0.0 across seed set [42,7,99]: "
            "all governance receipts are issued by home-town factions only"
        ),
        "metric_fn":   lambda m: 1.0 - m.sovereignty_drift_index,
        "metric_name": "sovereignty_integrity",
        "threshold":   1.0,
        "law_text":    (
            "LAW-H3: sovereignty_drift_index == 0.0 in all standard runs. "
            "Governance receipts (oath, cleansing, fog_pass, return_warrant) "
            "are issued exclusively by home-town factions. "
            "Sovereignty is home-bounded by world architecture, not by policy."
        ),
    },
]


# ── Run result ────────────────────────────────────────────────────────────────

@dataclass
class Epoch2RunResult:
    """
    Complete output of a run_epoch2_canonical() call.
    All claims are receipt-backed or empty.
    """
    seed: int
    ticks: int
    metrics: "Metrics"                           # type: ignore
    town_birth_results: List[Dict[str, Any]]     # TownBirthResult.to_receipt_payload()
    sigma_results: List[Dict[str, Any]]          # SigmaResult.to_receipt_payload()
    laws_inscribed: List[Dict[str, Any]]         # LawV1.to_ledger_payload()
    law_receipts: List[str]                      # receipt IDs from LawLedger.inscribe()
    world_summary: Dict[str, Any]
    kernel_cum_hash: str
    run_receipts_count: int
    run_at: str

    def to_artifact(self) -> Dict[str, Any]:
        """Serialize as EPOCH2_RUN_V1 artifact dict (no sha256 yet)."""
        return {
            "type":               "EPOCH2_RUN_V1",
            "seed":               self.seed,
            "ticks":              self.ticks,
            "metrics":            self.metrics.to_dict(),
            "town_birth_results": self.town_birth_results,
            "sigma_results":      self.sigma_results,
            "laws_inscribed":     self.laws_inscribed,
            "law_receipts":       self.law_receipts,
            "world_summary":      self.world_summary,
            "kernel_cum_hash":    self.kernel_cum_hash,
            "run_receipts_count": self.run_receipts_count,
            "hypotheses":         [
                {"id": h["id"], "text": h["text"], "threshold": h["threshold"]}
                for h in HYPOTHESES
            ],
            "run_at":             self.run_at,
        }


# ── Canonical EPOCH2 run ──────────────────────────────────────────────────────

def run_epoch2_canonical(
    seed: int = 42,
    ticks: int = 20,
    ledger_path: str = ":memory:",
) -> Epoch2RunResult:
    """
    Run the canonical EPOCH2 learning loop (Steps A–E + Town Birth).

    Args:
        seed:         World PRF seed for primary run (default: 42).
        ticks:        Number of sim ticks (default: 20).
        ledger_path:  Kernel ledger path (default: ":memory:" — non-sovereign).

    Returns:
        Epoch2RunResult with all evidence receipted.
    """
    from ..kernel import GovernanceVM
    from ..seeds.worlds.conquest_land import ConquestLandWorld
    from .metrics import EpochMetricsCollector
    from .sigma_gate import SigmaGate
    from .law_ledger import LawLedger
    from .town_birth import TownBirthPredicateV1

    run_at = datetime.now(timezone.utc).isoformat()

    # ── Step B: Primary sim run ───────────────────────────────────────────────
    km = GovernanceVM(ledger_path=ledger_path)
    world = ConquestLandWorld(km, world_seed=seed)
    all_receipts: List[Dict[str, Any]] = []

    for t in range(1, ticks + 1):
        tick_rs = world.tick(t)
        all_receipts.extend(tick_rs)

    world_summary = world.summary()

    # ── Step C: Extract metrics ───────────────────────────────────────────────
    metrics = EpochMetricsCollector.compute(all_receipts, world_summary, ticks)

    # Emit metrics receipt
    metrics_receipt = km.propose(metrics.as_receipt_payload())

    # ── TOWN_BIRTH_PREDICATE_V1: evaluate all factions ────────────────────────
    birth_results = TownBirthPredicateV1.evaluate_all_factions(
        all_receipts, world_summary
    )
    town_birth_payloads: List[Dict[str, Any]] = []
    for br in birth_results:
        r = km.propose(br.to_receipt_payload())
        town_birth_payloads.append({
            **br.to_receipt_payload(),
            "receipt_id": r.id,
        })

    # ── Steps D+E: Sigma gate + law inscription ───────────────────────────────
    law_ledger = LawLedger(km)
    sigma_payloads: List[Dict[str, Any]] = []
    law_receipts: List[str] = []

    for hyp in HYPOTHESES:
        sigma_result = SigmaGate.run(
            hypothesis=hyp["text"],
            metric_fn=hyp["metric_fn"],
            metric_name=hyp["metric_name"],
            threshold=hyp["threshold"],
            kernel=km,
            ticks=ticks,
        )
        sigma_payloads.append(sigma_result.to_receipt_payload())

        if sigma_result.passed:
            receipt = law_ledger.inscribe(sigma_result, law_text=hyp["law_text"])
            law_receipts.append(receipt.id)

    # ── Final kernel state ────────────────────────────────────────────────────
    # Emit EPOCH2_RUN_SUMMARY receipt (anchors everything)
    laws = law_ledger.list_laws()
    summary_receipt = km.propose({
        "type": "EPOCH2_RUN_SUMMARY_V1",
        "seed": seed,
        "ticks": ticks,
        "closure_success": metrics.closure_success,
        "laws_inscribed_count": len(laws),
        "law_receipts": law_receipts,
        "town_birth_eligible_count": sum(
            1 for br in birth_results if br.eligible
        ),
        "metrics_receipt_id": metrics_receipt.id,
    })

    # Total receipts in this kernel run (all proposals)
    total_receipts = (
        len(all_receipts)            # sim tick receipts
        + 1                          # metrics receipt
        + len(birth_results)         # town birth receipts
        + len(HYPOTHESES)            # sigma run receipts per hypothesis (×3 seeds each)
        + len(laws)                  # law inscription receipts
        + 1                          # summary receipt
    )

    return Epoch2RunResult(
        seed=seed,
        ticks=ticks,
        metrics=metrics,
        town_birth_results=town_birth_payloads,
        sigma_results=sigma_payloads,
        laws_inscribed=[law.to_ledger_payload() for law in laws],
        law_receipts=law_receipts,
        world_summary=world_summary,
        kernel_cum_hash=summary_receipt.cum_hash,
        run_receipts_count=total_receipts,
        run_at=run_at,
    )
