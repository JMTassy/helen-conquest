"""
helen_os/epoch3/quest_bank.py — Quest input layer (Image spec: "1. Input — CHOOSE A QUEST")

Three quest types from CONQUEST: HELEN Internal Sim Loop Spec:
  Q1 — SOLVE_PARADOX:        inject contradiction into W', verify fail-closed
  Q2 — ALTER_REALITY:        apply counterfactual to W', measure delta vs W
  Q3 — EXPLORE_TEMPORAL:     sweep tick horizons, find time-stable laws

Each Quest is a pure data container — no side effects.
The SimLoop (sim_loop.py) executes them.

Design principles:
  - Quest is receipt-bound: hypothesis must be falsifiable and measurable.
  - QuestType drives which shadow-world perturbation is applied in Phase B.
  - law_text is the inscription target IF sigma gate passes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# ── Quest type enum ────────────────────────────────────────────────────────────

class QuestType(str, Enum):
    SOLVE_PARADOX    = "SOLVE_PARADOX"     # resolve contradiction under pressure
    ALTER_REALITY    = "ALTER_REALITY"     # counterfactual world-state delta
    EXPLORE_TEMPORAL = "EXPLORE_TEMPORAL"  # tick-horizon stability sweep


# ── CounterfactualSpec (typed world mutation for Phase B) ──────────────────────

@dataclass
class CounterfactualSpec:
    """
    Typed world perturbation applied to shadow world W' in Phase B.

    Allowed ops (non-procedural — they are world-physics, not instructions):
      SET_SEED:           run W' with a different world PRF seed
      INJECT_PARADOX:     force closure_failure condition (dispute all receipts)
      SWEEP_TICKS:        run W' across multiple tick horizons
      PERTURB_DISPUTE:    increase dispute_heat by factor
      PERTURB_FOG:        increase fog / reduce witness coverage

    All values are numeric or boolean — no freeform text.
    """
    op: str                            # one of the allowed ops above
    params: Dict[str, Any] = field(default_factory=dict)

    ALLOWED_OPS = frozenset({
        "SET_SEED",
        "INJECT_PARADOX",
        "SWEEP_TICKS",
        "PERTURB_DISPUTE",
        "PERTURB_FOG",
    })

    def __post_init__(self):
        if self.op not in self.ALLOWED_OPS:
            raise ValueError(
                f"CounterfactualSpec.op={self.op!r} not in allowed set "
                f"{sorted(self.ALLOWED_OPS)}. "
                f"No freeform ops allowed — world-physics only."
            )

    def to_payload(self) -> Dict[str, Any]:
        return {
            "type": "COUNTERFACTUAL_SPEC_V1",
            "op":   self.op,
            "params": self.params,
        }


# ── Quest dataclass ────────────────────────────────────────────────────────────

@dataclass
class Quest:
    """
    A single learning quest for the HELEN Sim Loop.

    Fields:
      id            — short unique identifier (Q1, Q2, Q3, ...)
      quest_type    — one of QuestType
      hypothesis    — single-sentence falsifiable claim (pre-run)
      metric_fn     — Callable[Metrics → float] for sigma gate
      metric_name   — human-readable name of metric being tested
      threshold     — sigma gate threshold (metric_fn(m) >= threshold to PASS)
      law_text      — inscription text IF sigma gate passes
      counterfactual— shadow world spec for Phase B (None = no shadow run)
      tick_horizons — for EXPLORE_TEMPORAL: list of tick counts to sweep
    """
    id:             str
    quest_type:     QuestType
    hypothesis:     str
    metric_fn:      Callable         # (Metrics) -> float
    metric_name:    str
    threshold:      float
    law_text:       str
    counterfactual: Optional[CounterfactualSpec] = None
    tick_horizons:  Optional[List[int]] = None   # EXPLORE_TEMPORAL only

    def to_payload(self) -> Dict[str, Any]:
        """Ledger payload for this quest (no callables — just metadata)."""
        return {
            "type":          "QUEST_V1",
            "id":            self.id,
            "quest_type":    self.quest_type.value,
            "hypothesis":    self.hypothesis,
            "metric_name":   self.metric_name,
            "threshold":     self.threshold,
            "law_text":      self.law_text,
            "counterfactual": self.counterfactual.to_payload()
                              if self.counterfactual else None,
            "tick_horizons": self.tick_horizons,
        }


# ── Standard quest bank (3 quests from image) ─────────────────────────────────

QUEST_BANK: List[Quest] = [

    # ── Q1: SOLVE_PARADOX ───────────────────────────────────────────────────
    # Image: "Solve a Paradox" — ☯ contradiction icon
    # Mechanism: inject a paradox seed (INJECT_PARADOX) into W'.
    #   Paradox world has all receipts disputed → closure_success=False.
    #   The invariant we test: "kernel fails closed under total contradiction
    #   (closure_success=0 in W') while base world W closes successfully."
    #   Metric: delta = closure_success(W) - closure_success(W').
    #   If W=1 and W'=0 → delta=1.0 → gate passes → law: fail-closed is structural.
    Quest(
        id           = "Q1",
        quest_type   = QuestType.SOLVE_PARADOX,
        hypothesis   = (
            "Under total contradiction (all receipts disputed in W'), "
            "the kernel fails closed (closure_success=0 in W') "
            "while the base world W completes (closure_success=1). "
            "Contradiction resolves the distinction between real and simulated closure."
        ),
        metric_fn    = lambda m: float(m.closure_success),   # base world metric
        metric_name  = "closure_success_base",
        threshold    = 1.0,   # W must close
        law_text     = (
            "LAW-Q1 (PARADOX): Kernel fail-closed is structural, not policy. "
            "Under total contradiction (INJECT_PARADOX), W' collapses closure "
            "while W completes — proving the distinction is architecture-enforced."
        ),
        counterfactual = CounterfactualSpec(
            op     = "INJECT_PARADOX",
            params = {"dispute_all": True, "expected_closure": False},
        ),
    ),

    # ── Q2: ALTER_REALITY ───────────────────────────────────────────────────
    # Image: "Alter Reality States" — ◉ eye icon
    # Mechanism: run W' with a perturbed seed (SET_SEED: seed=7).
    #   Compare admissibility_rate(W, seed=42) vs admissibility_rate(W', seed=7).
    #   Invariant: admissibility_rate is seed-stable (delta < 0.05).
    #   Metric: min(rate_W, rate_W') — both must be >= 0.80.
    Quest(
        id           = "Q2",
        quest_type   = QuestType.ALTER_REALITY,
        hypothesis   = (
            "Admissibility rate is stable across reality perturbations "
            "(seed=42 vs seed=7): both worlds admit >= 80% of evidence bundles. "
            "Anti-replay is seed-independent — a property of the protocol, not the run."
        ),
        metric_fn    = lambda m: m.admissibility_rate,
        metric_name  = "admissibility_rate",
        threshold    = 0.80,
        law_text     = (
            "LAW-Q2 (REALITY): Admissibility_rate >= 0.80 is seed-invariant. "
            "Protocol correctness (anti-replay) is not an artifact of seed=42 — "
            "it holds across reality perturbations. Evidence pipelines are robust."
        ),
        counterfactual = CounterfactualSpec(
            op     = "SET_SEED",
            params = {"shadow_seed": 7},
        ),
    ),

    # ── Q3: EXPLORE_TEMPORAL ────────────────────────────────────────────────
    # Image: "Explore Temporal Realms" — ⌛ hourglass icon
    # Mechanism: sweep tick horizons [10, 20, 30, 50].
    #   Invariant: sovereignty_drift_index == 0 at all tick horizons.
    #   (Sovereignty is home-bounded regardless of sim length.)
    #   Metric: 1.0 - sovereignty_drift_index for the primary run (seed=42, ticks=20).
    #   Shadow: run also at ticks=30 and ticks=50 — verify drift stays 0.
    Quest(
        id           = "Q3",
        quest_type   = QuestType.EXPLORE_TEMPORAL,
        hypothesis   = (
            "Sovereignty drift index == 0 at all tick horizons [10, 20, 30, 50]: "
            "governance receipts are home-bounded regardless of simulation length. "
            "Constitutional invariants are time-stable."
        ),
        metric_fn    = lambda m: 1.0 - m.sovereignty_drift_index,
        metric_name  = "sovereignty_integrity",
        threshold    = 1.0,
        law_text     = (
            "LAW-Q3 (TEMPORAL): Sovereignty_drift_index == 0 at all tick horizons "
            "[10, 20, 30, 50]. Constitutional governance (home-bounded receipts) is "
            "time-invariant — architecture, not policy, holds the boundary."
        ),
        counterfactual = CounterfactualSpec(
            op     = "SWEEP_TICKS",
            params = {"horizons": [10, 30, 50]},
        ),
        tick_horizons  = [10, 20, 30, 50],
    ),
]

# ── Lookup helper ─────────────────────────────────────────────────────────────

def get_quest(quest_id: str) -> Quest:
    """Return quest by id. Raises KeyError if not found."""
    for q in QUEST_BANK:
        if q.id == quest_id:
            return q
    raise KeyError(f"Quest {quest_id!r} not in QUEST_BANK. Available: {[q.id for q in QUEST_BANK]}")
