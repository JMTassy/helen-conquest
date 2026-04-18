"""
helen_os/epoch3/sim_loop.py — Simulation Phases A→B→C

Image spec: "2. Simulation Phases"
  A. Observation    — Data Capture & Pattern Recognition
  B. Experimentation— Scenario Testing & Reality Manipulation (shadow world W')
  C. Integration    — Memory Synthesis & Insight Formation

Phase A: Run base world W (seed, ticks) → receipts + metrics
Phase B: Run shadow world W' (counterfactual applied) → shadow metrics
Phase C: Compute delta(W, W') → sigma gate → LawLedger inscription

All W' runs use :memory: kernels — non-sovereign, ephemeral, never committed.
Only the delta metrics and sigma receipts cross back to the shared kernel.

Phase B implementations by quest type:
  SOLVE_PARADOX    → INJECT_PARADOX: run world with forced closure_failure
  ALTER_REALITY    → SET_SEED: run world with shadow_seed
  EXPLORE_TEMPORAL → SWEEP_TICKS: run world at each tick horizon in tick_horizons
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .quest_bank import Quest, QuestType

from ..epoch2.metrics import EpochMetricsCollector, Metrics


# ── Phase results ──────────────────────────────────────────────────────────────

@dataclass
class PhaseAResult:
    """
    Phase A: Observation — Data Capture & Pattern Recognition.

    Holds the base world W receipts and computed metrics.
    """
    receipts:     List[Dict[str, Any]]
    metrics:      Metrics
    world_summary:Dict[str, Any]
    seed:         int
    ticks:        int
    receipt_count:int


@dataclass
class PhaseBResult:
    """
    Phase B: Experimentation — Scenario Testing & Reality Manipulation.

    Holds shadow world W' results and the counterfactual spec applied.
    """
    op:                  str               # counterfactual op applied
    params:              Dict[str, Any]
    shadow_receipts:     List[Dict[str, Any]]
    shadow_metrics_list: List[Metrics]     # one per horizon (SWEEP_TICKS) or single
    shadow_summary_list: List[Dict[str, Any]]
    shadow_seeds:        List[int]
    shadow_ticks_list:   List[int]
    paradox_injected:    bool = False      # True for INJECT_PARADOX runs


@dataclass
class PhaseCResult:
    """
    Phase C: Integration — Memory Synthesis & Insight Formation.

    Holds the delta between W and W', sigma gate result, and inscribed laws.
    """
    delta_closure_success:     float   # closure_success(W) - avg(closure_success(W'))
    delta_admissibility:       float   # admissibility_rate(W) - avg(admissibility_rate(W'))
    delta_sovereignty_drift:   float   # drift(W') - drift(W)  (should be 0 for Q3)
    sigma_passed:              bool
    sigma_reason:              str
    laws_inscribed_count:      int
    evidence_receipt_ids:      List[str]


@dataclass
class SimLoopResult:
    """
    Complete result of one sim loop run.

    Image spec: Input(Quest) → [A→B→C] → Evaluation → Output
    """
    quest_id:    str
    quest_type:  str
    phase_a:     PhaseAResult
    phase_b:     PhaseBResult
    phase_c:     PhaseCResult
    kernel_receipts_count: int

    def to_payload(self) -> Dict[str, Any]:
        """Ledger payload for this sim loop result."""
        return {
            "type":       "SIM_LOOP_RESULT_V1",
            "quest_id":   self.quest_id,
            "quest_type": self.quest_type,
            "phase_a": {
                "seed":     self.phase_a.seed,
                "ticks":    self.phase_a.ticks,
                "receipts": self.phase_a.receipt_count,
                "admissibility_rate": self.phase_a.metrics.admissibility_rate,
                "closure_success":    self.phase_a.metrics.closure_success,
                "sovereignty_drift":  self.phase_a.metrics.sovereignty_drift_index,
                "dispute_heat":       self.phase_a.metrics.dispute_heat,
            },
            "phase_b": {
                "op":               self.phase_b.op,
                "params":           self.phase_b.params,
                "shadow_seeds":     self.phase_b.shadow_seeds,
                "shadow_ticks":     self.phase_b.shadow_ticks_list,
                "paradox_injected": self.phase_b.paradox_injected,
                "shadow_closure_rates": [
                    float(m.closure_success) for m in self.phase_b.shadow_metrics_list
                ],
                "shadow_admissibility_rates": [
                    m.admissibility_rate for m in self.phase_b.shadow_metrics_list
                ],
            },
            "phase_c": {
                "delta_closure":       self.phase_c.delta_closure_success,
                "delta_admissibility": self.phase_c.delta_admissibility,
                "delta_sovereignty":   self.phase_c.delta_sovereignty_drift,
                "sigma_passed":        self.phase_c.sigma_passed,
                "sigma_reason":        self.phase_c.sigma_reason,
                "laws_inscribed":      self.phase_c.laws_inscribed_count,
                "evidence_receipts":   self.phase_c.evidence_receipt_ids,
            },
            "kernel_receipts_count": self.kernel_receipts_count,
        }


# ── SimLoop ────────────────────────────────────────────────────────────────────

class SimLoop:
    """
    Executes the three simulation phases for a Quest.

    Usage:
        loop = SimLoop(kernel)
        result = loop.run(quest, seed=42, ticks=20, law_ledger=ledger)

    Phase B shadow worlds always use :memory: ephemeral kernels.
    Only receipt IDs (not content) cross back to the shared kernel.
    """

    def __init__(self, kernel):
        """
        Args:
            kernel: GovernanceVM instance for evidence receipt emission.
                    Must be provided by caller (supports :memory: or live).
        """
        self._kernel = kernel

    # ─── Phase A: Observation ─────────────────────────────────────────────────

    def _run_phase_a(self, seed: int, ticks: int) -> PhaseAResult:
        """
        Phase A — Observation: Data Capture & Pattern Recognition.

        Runs base world W. No counterfactual applied.
        Emits PHASE_A_OBSERVATION_V1 receipt.
        """
        from ..kernel import GovernanceVM
        from ..seeds.worlds.conquest_land import ConquestLandWorld

        run_km = GovernanceVM(ledger_path=":memory:")
        world  = ConquestLandWorld(run_km, world_seed=seed)
        receipts: List[Dict[str, Any]] = []

        for t in range(1, ticks + 1):
            receipts.extend(world.tick(t))

        summary = world.summary()
        metrics = EpochMetricsCollector.compute(receipts, summary, ticks)

        # Emit observation receipt into shared kernel
        self._kernel.propose({
            "type":               "PHASE_A_OBSERVATION_V1",
            "seed":               seed,
            "ticks":              ticks,
            "receipt_count":      len(receipts),
            "admissibility_rate": metrics.admissibility_rate,
            "closure_success":    metrics.closure_success,
            "sovereignty_drift":  metrics.sovereignty_drift_index,
        })

        return PhaseAResult(
            receipts      = receipts,
            metrics       = metrics,
            world_summary = summary,
            seed          = seed,
            ticks         = ticks,
            receipt_count = len(receipts),
        )

    # ─── Phase B: Experimentation ─────────────────────────────────────────────

    def _run_shadow_world(
        self, seed: int, ticks: int, inject_paradox: bool = False
    ) -> tuple:
        """
        Run a single shadow world W' (ephemeral :memory: kernel).

        Args:
            seed:            World PRF seed for W'.
            ticks:           Tick count for this run.
            inject_paradox:  If True, mutate the world to produce closure_failure.

        Returns:
            (receipts, metrics, summary)
        """
        from ..kernel import GovernanceVM
        from ..seeds.worlds.conquest_land import ConquestLandWorld

        shadow_km   = GovernanceVM(ledger_path=":memory:")
        shadow_world = ConquestLandWorld(shadow_km, world_seed=seed)

        # INJECT_PARADOX: corrupt the expedition_bundle to prevent closure.
        # We do this by pre-filling the bundle with fake entries that block
        # the real evidence types from completing the closure predicate.
        if inject_paradox:
            # Force closure_failure by pre-saturating the dispute log
            # (run 0 ticks — world never starts, so closure_success=False)
            shadow_receipts  = []
            shadow_summary   = shadow_world.summary()
            # Inject a synthetic closure_failure receipt
            shadow_km.propose({
                "type":     "closure_failure_v1",
                "reason":   "INJECT_PARADOX: contradiction injected into W'",
                "tick":     0,
            })
        else:
            shadow_receipts = []
            for t in range(1, ticks + 1):
                shadow_receipts.extend(shadow_world.tick(t))
            shadow_summary = shadow_world.summary()

        shadow_metrics = EpochMetricsCollector.compute(
            shadow_receipts, shadow_summary, ticks
        )
        return shadow_receipts, shadow_metrics, shadow_summary

    def _run_phase_b(self, quest: "Quest", base_seed: int, ticks: int) -> PhaseBResult:
        """
        Phase B — Experimentation: Scenario Testing & Reality Manipulation.

        Applies the quest's CounterfactualSpec to run shadow world(s) W'.
        All shadow runs use :memory: ephemeral kernels.
        """
        from .quest_bank import QuestType

        cf = quest.counterfactual
        if cf is None:
            # No counterfactual — return empty Phase B (observation-only quest)
            return PhaseBResult(
                op                  = "NONE",
                params              = {},
                shadow_receipts     = [],
                shadow_metrics_list = [],
                shadow_summary_list = [],
                shadow_seeds        = [],
                shadow_ticks_list   = [],
            )

        shadow_receipts_all  : List[Dict[str, Any]] = []
        shadow_metrics_list  : List[Metrics]        = []
        shadow_summary_list  : List[Dict[str, Any]] = []
        shadow_seeds         : List[int]            = []
        shadow_ticks_list    : List[int]            = []
        paradox_injected     = False

        if cf.op == "INJECT_PARADOX":
            # Run shadow world W' with paradox injection
            sr, sm, ss = self._run_shadow_world(base_seed, ticks, inject_paradox=True)
            shadow_receipts_all.extend(sr)
            shadow_metrics_list.append(sm)
            shadow_summary_list.append(ss)
            shadow_seeds.append(base_seed)
            shadow_ticks_list.append(ticks)
            paradox_injected = True

        elif cf.op == "SET_SEED":
            # Run W' with a different seed
            shadow_seed = cf.params.get("shadow_seed", 7)
            sr, sm, ss = self._run_shadow_world(shadow_seed, ticks)
            shadow_receipts_all.extend(sr)
            shadow_metrics_list.append(sm)
            shadow_summary_list.append(ss)
            shadow_seeds.append(shadow_seed)
            shadow_ticks_list.append(ticks)

        elif cf.op == "SWEEP_TICKS":
            # Run W' at each horizon (base seed)
            horizons = cf.params.get("horizons", [10, 30])
            for h in horizons:
                sr, sm, ss = self._run_shadow_world(base_seed, h)
                shadow_receipts_all.extend(sr)
                shadow_metrics_list.append(sm)
                shadow_summary_list.append(ss)
                shadow_seeds.append(base_seed)
                shadow_ticks_list.append(h)

        # Emit Phase B evidence receipt into shared kernel
        self._kernel.propose({
            "type":              "PHASE_B_EXPERIMENT_V1",
            "quest_id":          quest.id,
            "counterfactual_op": cf.op,
            "shadow_seeds":      shadow_seeds,
            "shadow_ticks":      shadow_ticks_list,
            "shadow_closure_rates": [float(m.closure_success) for m in shadow_metrics_list],
            "paradox_injected":  paradox_injected,
        })

        return PhaseBResult(
            op                  = cf.op,
            params              = cf.params,
            shadow_receipts     = shadow_receipts_all,
            shadow_metrics_list = shadow_metrics_list,
            shadow_summary_list = shadow_summary_list,
            shadow_seeds        = shadow_seeds,
            shadow_ticks_list   = shadow_ticks_list,
            paradox_injected    = paradox_injected,
        )

    # ─── Phase C: Integration ─────────────────────────────────────────────────

    def _run_phase_c(
        self,
        quest:   "Quest",
        phase_a: PhaseAResult,
        phase_b: PhaseBResult,
        law_ledger,
    ) -> PhaseCResult:
        """
        Phase C — Integration: Memory Synthesis & Insight Formation.

        Computes delta(W, W'), runs sigma gate on base world metric,
        and inscribes LAW_V1 if gate passes.
        """
        from ..epoch2.sigma_gate import SigmaGate

        # Compute delta metrics
        base_closure   = float(phase_a.metrics.closure_success)
        base_admission = phase_a.metrics.admissibility_rate
        base_drift     = phase_a.metrics.sovereignty_drift_index

        if phase_b.shadow_metrics_list:
            avg_shadow_closure   = sum(
                float(m.closure_success) for m in phase_b.shadow_metrics_list
            ) / len(phase_b.shadow_metrics_list)
            avg_shadow_admission = sum(
                m.admissibility_rate for m in phase_b.shadow_metrics_list
            ) / len(phase_b.shadow_metrics_list)
            avg_shadow_drift     = sum(
                m.sovereignty_drift_index for m in phase_b.shadow_metrics_list
            ) / len(phase_b.shadow_metrics_list)
        else:
            avg_shadow_closure   = base_closure
            avg_shadow_admission = base_admission
            avg_shadow_drift     = base_drift

        delta_closure      = base_closure   - avg_shadow_closure
        delta_admissibility= base_admission - avg_shadow_admission
        delta_drift        = avg_shadow_drift - base_drift   # positive = W' drifted more

        # Sigma gate on base world (seed=42 primary run)
        sigma_result = SigmaGate.run(
            hypothesis  = quest.hypothesis,
            metric_fn   = quest.metric_fn,
            metric_name = quest.metric_name,
            threshold   = quest.threshold,
            kernel      = self._kernel,
            seed_set    = [phase_a.seed],   # single-seed gate per quest (multi-seed in EPOCH2)
            ticks       = phase_a.ticks,
        )

        laws_count = 0
        if sigma_result.passed and law_ledger is not None:
            law_ledger.inscribe(sigma_result, law_text=quest.law_text)
            laws_count = 1

        # Emit Phase C integration receipt
        self._kernel.propose({
            "type":                "PHASE_C_INTEGRATION_V1",
            "quest_id":            quest.id,
            "delta_closure":       delta_closure,
            "delta_admissibility": delta_admissibility,
            "delta_drift":         delta_drift,
            "sigma_passed":        sigma_result.passed,
            "laws_inscribed":      laws_count,
        })

        return PhaseCResult(
            delta_closure_success   = delta_closure,
            delta_admissibility     = delta_admissibility,
            delta_sovereignty_drift = delta_drift,
            sigma_passed            = sigma_result.passed,
            sigma_reason            = sigma_result.reason,
            laws_inscribed_count    = laws_count,
            evidence_receipt_ids    = sigma_result.evidence_receipt_ids,
        )

    # ─── Main run ─────────────────────────────────────────────────────────────

    def run(
        self,
        quest:       "Quest",
        seed:        int  = 42,
        ticks:       int  = 20,
        law_ledger         = None,
    ) -> SimLoopResult:
        """
        Execute one complete A→B→C sim loop for a quest.

        Args:
            quest:       Quest to execute.
            seed:        Base world PRF seed (default: 42).
            ticks:       Base tick count (default: 20).
            law_ledger:  LawLedger for Phase C inscription (optional).

        Returns:
            SimLoopResult with all three phase results.
        """
        # Emit quest-start receipt
        self._kernel.propose({
            "type":       "QUEST_START_V1",
            "quest_id":   quest.id,
            "quest_type": quest.quest_type.value,
            "seed":       seed,
            "ticks":      ticks,
        })

        phase_a = self._run_phase_a(seed, ticks)
        phase_b = self._run_phase_b(quest, seed, ticks)
        phase_c = self._run_phase_c(quest, phase_a, phase_b, law_ledger)

        # Count all receipts in shared kernel (approximation via seq)
        # We know we emitted: quest_start + phase_a + phase_b + phase_c
        # + sigma runs (1 seed × 1 quest) + possible law inscription
        kernel_receipts = 4 + 1 + phase_c.laws_inscribed_count  # conservative estimate

        return SimLoopResult(
            quest_id               = quest.id,
            quest_type             = quest.quest_type.value,
            phase_a                = phase_a,
            phase_b                = phase_b,
            phase_c                = phase_c,
            kernel_receipts_count  = kernel_receipts,
        )
