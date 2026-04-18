"""
helen_os/epoch2/sigma_gate.py — Sigma gate for invariant validation.

The sigma gate validates that a hypothesis holds across a seed set.
An invariant is only promoted to a LAW when it passes the sigma gate.

Contract:
  - Run len(seed_set) independent simulations (default: [42, 7, 99])
  - Each run uses its own GovernanceVM(:memory:) — fully isolated
  - For each run: compute Metrics, apply metric_fn, compare to threshold
  - Gate PASSES iff metric_fn(metrics) >= threshold for ALL seeds
  - Evidence receipts are emitted per run (receipts prove the gate ran)

Adversarial stressors (v1.0):
  The three standard seeds [42, 7, 99] serve as the seed stress set.
  True adversarial stressors (fog-variant, wolf-variant, decoy-saturated)
  require world configuration extensions — planned for EPOCH3.
  adversarial_gates_passed is [] in v1.0; populated when stressors are added.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .metrics import EpochMetricsCollector, Metrics


# ── Sigma result ──────────────────────────────────────────────────────────────

@dataclass
class SigmaResult:
    """
    Result of a sigma gate validation run.

    If passed=True: the hypothesis holds across all seeds.
    Evidence receipts in evidence_receipt_ids prove the runs happened.
    """
    passed: bool
    hypothesis: str
    seed_set: List[int]
    metric_name: str
    metric_values: Dict[int, float]   # seed → metric value
    threshold: float
    adversarial_gates_passed: List[str]
    adversarial_gates_failed: List[str]
    reason: str
    evidence_receipt_ids: List[str] = field(default_factory=list)

    def to_receipt_payload(self) -> Dict[str, Any]:
        """Ledger payload for sigma gate result — used by LawLedger.inscribe()."""
        return {
            "type": "SIGMA_GATE_V1",
            "hypothesis": self.hypothesis,
            "verdict": "PASS" if self.passed else "FAIL",
            "seed_set": self.seed_set,
            "metric_name": self.metric_name,
            "metric_values": {str(k): v for k, v in self.metric_values.items()},
            "threshold": self.threshold,
            "adversarial_gates_passed": self.adversarial_gates_passed,
            "adversarial_gates_failed": self.adversarial_gates_failed,
            "evidence_receipt_ids": self.evidence_receipt_ids,
            "reason": self.reason,
        }


# ── Sigma gate ────────────────────────────────────────────────────────────────

class SigmaGate:
    """
    Multi-seed invariant validator.

    Usage:
        result = SigmaGate.run(
            hypothesis="admissibility_rate >= 0.80 across seed set",
            metric_fn=lambda m: m.admissibility_rate,
            metric_name="admissibility_rate",
            threshold=0.80,
            kernel=km,   # for evidence receipt emission
        )
        if result.passed:
            law_ledger.inscribe(result, law_text="...")
    """

    DEFAULT_SEEDS: List[int] = [42, 7, 99]

    @classmethod
    def run(
        cls,
        hypothesis: str,
        metric_fn: Callable[[Metrics], float],
        metric_name: str,
        threshold: float,
        kernel,                          # GovernanceVM for evidence receipts
        seed_set: Optional[List[int]] = None,
        ticks: int = 20,
    ) -> SigmaResult:
        """
        Run multi-seed validation for a hypothesis.

        Steps per seed:
          1. Create independent ConquestLandWorld(:memory:)
          2. Run ticks
          3. Compute Metrics via EpochMetricsCollector
          4. Apply metric_fn → float
          5. Emit SIGMA_RUN_V1 receipt (via shared kernel)
          6. Check threshold

        Args:
            hypothesis:   Single-sentence claim being validated.
            metric_fn:    Extracts a float from Metrics (threshold comparison).
            metric_name:  Human-readable name of the metric being tested.
            threshold:    All seed values must be >= this.
            kernel:       GovernanceVM for evidence receipt emission.
            seed_set:     Seeds to run (default: [42, 7, 99]).
            ticks:        Number of sim ticks per seed.

        Returns:
            SigmaResult
        """
        from ..kernel import GovernanceVM
        from ..seeds.worlds.conquest_land import ConquestLandWorld

        seeds = seed_set if seed_set is not None else cls.DEFAULT_SEEDS
        metric_values: Dict[int, float] = {}
        evidence_receipt_ids: List[str] = []

        for seed in seeds:
            # Isolated run — each seed gets its own ephemeral kernel
            run_km = GovernanceVM(ledger_path=":memory:")
            world = ConquestLandWorld(run_km, world_seed=seed)
            all_receipts: List[Dict[str, Any]] = []

            for t in range(1, ticks + 1):
                tick_rs = world.tick(t)
                all_receipts.extend(tick_rs)

            summary = world.summary()
            metrics = EpochMetricsCollector.compute(all_receipts, summary, ticks)
            val = metric_fn(metrics)
            metric_values[seed] = round(val, 6)

            # Emit evidence receipt into shared kernel (proves this seed ran)
            r = kernel.propose({
                "type": "SIGMA_RUN_V1",
                "hypothesis": hypothesis,
                "seed": seed,
                "metric_name": metric_name,
                "metric_value": val,
                "threshold": threshold,
                "ticks": ticks,
                "closure_success": metrics.closure_success,
            })
            evidence_receipt_ids.append(r.id)

        # Gate: all seeds must meet threshold
        failed_seeds = [s for s, v in metric_values.items() if v < threshold]
        passed = len(failed_seeds) == 0

        if passed:
            reason = (
                f"All {len(seeds)} seeds pass threshold {threshold}: "
                f"{metric_values}"
            )
        else:
            reason = (
                f"Seeds {failed_seeds} failed threshold {threshold}: "
                f"{metric_values}"
            )

        return SigmaResult(
            passed=passed,
            hypothesis=hypothesis,
            seed_set=seeds,
            metric_name=metric_name,
            metric_values=metric_values,
            threshold=threshold,
            adversarial_gates_passed=[],   # v1.0: no adversarial stressors
            adversarial_gates_failed=[],
            reason=reason,
            evidence_receipt_ids=evidence_receipt_ids,
        )
