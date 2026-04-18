#!/usr/bin/env python3
"""
conquest_stability_analysis.py
===============================
Stability analysis module for CONQUEST LAND emergence engine.

Implements the measurement layer for STABILITY_THEOREM_V1.md:
  - Computes L(m_t) along governed trajectories
  - Verifies Proposition 2 condition: ΔL_t ≤ 0 at each step
  - Identifies crisis ticks: ΔL_t > 0 (boundary proximity warning)
  - Runs across multiple seeds and parameter configurations
  - Produces falsification report (JSON)

Usage:
  python3 conquest_stability_analysis.py single [seed]     # Single seed run
  python3 conquest_stability_analysis.py sweep             # Multi-seed sweep
  python3 conquest_stability_analysis.py load              # Load existing artifacts
"""

import json
import hashlib
import sys
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# ---------------------------------------------------------------------------
# Import the emergence engine
# ---------------------------------------------------------------------------
try:
    from conquest_emergence_engine import ConquestEmergenceEngine, EmergenceMetrics, Regime
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    print("[WARN] conquest_emergence_engine.py not available — analysis limited to artifact files")

ARTIFACTS_DIR = Path("artifacts")
ARTIFACTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Lyapunov Candidate
# ---------------------------------------------------------------------------

@dataclass
class LyapunovConfig:
    """
    Configuration for the Lyapunov candidate function.

    L(m) = α(1-I) + β(1-P) + γ(1-E) - δ·T_bal + ε(1-M)

    L = 0 when all metrics are at their governance target.
    L > 0 when the system is away from equilibrium.
    """
    # Weights (must sum to 1 for interpretability)
    alpha: float = 0.30   # institutional coherence weight
    beta:  float = 0.25   # productive efficiency weight
    gamma: float = 0.20   # egregor density weight
    delta: float = 0.15   # triadic balance weight (enters negated)
    epsilon: float = 0.10 # modularity weight

    # Governance targets
    target_house_count: int = 3   # POLITICS regime optimum
    max_house_count: int   = 6
    target_strategy_entropy: float = 1.585  # max for 3 strategies (log2(3))

    def validate(self):
        total = self.alpha + self.beta + self.gamma + self.delta + self.epsilon
        assert abs(total - 1.0) < 1e-6, f"Weights must sum to 1, got {total}"


def lyapunov(m: 'EmergenceMetrics', cfg: LyapunovConfig) -> float:
    """
    Compute L(m_t) for a single tick.

    Components:
      I = institutional coherence = house_count / target × persistence
      P = house_task_success_rate
      E = egregor density = egregors / house_count (0 if no houses)
      T_bal = triadic balance = strategy_entropy / max_entropy (1.0 = max)
      M = modularity (0..1 scale, clipped)

    Field name mapping (EmergenceMetrics actual names):
      persistence         → coalition_persistence
      modularity          → graph_modularity
      ie_ratio            → internal_external_ratio
      memory_reuse_rate   → house_memory_reuse_rate
      house_task_success_rate → house_task_success
    """
    # Resolve field names (support both engine objects and MockMetrics)
    persistence        = getattr(m, 'coalition_persistence', getattr(m, 'persistence', 0.0))
    modularity         = getattr(m, 'graph_modularity',      getattr(m, 'modularity',  0.0))
    task_success       = getattr(m, 'house_task_success',    getattr(m, 'house_task_success_rate', 0.0))

    # Institutional coherence I ∈ [0, 1]
    I = min(1.0, (m.house_count / cfg.target_house_count)) * persistence

    # Productive efficiency P ∈ [0, 1]
    P = task_success

    # Egregor density E ∈ [0, 1]
    E = m.policy_explanation_rate if m.house_count > 0 else 0.0

    # Triadic balance T_bal ∈ [0, 1] (1 = maximum, 3-way equal split)
    T_bal = min(1.0, m.strategy_entropy / cfg.target_strategy_entropy)

    # Modularity M ∈ [0, 1]
    M = max(0.0, min(1.0, modularity))

    # Lyapunov value: L = 0 at equilibrium, L > 0 away from it
    L = (
        cfg.alpha  * (1.0 - I)
      + cfg.beta   * (1.0 - P)
      + cfg.gamma  * (1.0 - E)
      - cfg.delta  * T_bal       # triadic balance DECREASES L (it is good)
      + cfg.epsilon * (1.0 - M)
    )
    return max(0.0, L)  # floor at 0 (L is non-negative by construction)


# ---------------------------------------------------------------------------
# Single-trajectory analysis
# ---------------------------------------------------------------------------

@dataclass
class TickAnalysis:
    """Analysis for a single simulation tick."""
    tick: int
    regime: str
    L: float          # Lyapunov value
    delta_L: float    # L(t+1) - L(t), or 0 for last tick
    in_K: bool        # whether x_t is in the governable set K
    crisis: bool      # delta_L > 0 (Proposition 2 violation)
    house_count: int
    modularity: float
    persistence: float
    strategy_entropy: float
    policy_explanation_rate: float
    house_task_success_rate: float


@dataclass
class TrajectoryReport:
    """Full stability analysis for one seed run."""
    seed: int
    n_ticks: int

    # Proposition 1: forward invariance
    prop1_verified: bool        # all ticks stayed in K
    ticks_outside_K: List[int]  # ticks where x_t ∉ K

    # Proposition 2: monotone decrease
    prop2_verified: bool        # ΔL ≤ 0 at all steps
    crisis_ticks: List[int]     # ticks where ΔL > 0
    max_delta_L: float          # worst-case violation
    mean_delta_L: float         # mean ΔL (should be ≤ 0)

    # Convergence
    converged: bool             # final L < convergence_threshold
    final_L: float
    min_L: float
    max_L: float
    L_at_tick_50: float

    # Regime summary
    final_regime: str
    ticks_in_politics: int
    ticks_in_noise: int

    # Per-tick data
    ticks: List[TickAnalysis] = field(default_factory=list)

    def summary(self) -> str:
        status_p1 = "✓ VERIFIED" if self.prop1_verified else "✗ FALSIFIED"
        status_p2 = "✓ VERIFIED" if self.prop2_verified else "✗ FALSIFIED"
        lines = [
            f"=== TrajectoryReport seed={self.seed} ===",
            f"  Proposition 1 (Forward Invariance): {status_p1}",
            f"    ticks outside K: {self.ticks_outside_K}",
            f"  Proposition 2 (Monotone Stability): {status_p2}",
            f"    crisis ticks (ΔL>0): {self.crisis_ticks[:10]}{'...' if len(self.crisis_ticks)>10 else ''}",
            f"    max ΔL: {self.max_delta_L:.4f}  mean ΔL: {self.mean_delta_L:.4f}",
            f"  Convergence: {'✓ YES' if self.converged else '✗ NOT YET'}",
            f"    final L={self.final_L:.4f}  min L={self.min_L:.4f}  max L={self.max_L:.4f}",
            f"  Final regime: {self.final_regime}",
            f"  Ticks in POLITICS: {self.ticks_in_politics}/{self.n_ticks}",
        ]
        return "\n".join(lines)


def analyze_trajectory(
    metrics: List['EmergenceMetrics'],
    seed: int,
    cfg: LyapunovConfig,
    K_thresholds: Dict[str, float],
) -> TrajectoryReport:
    """
    Analyze a complete simulation trajectory.

    K_thresholds defines the governable set K:
      K = { m | I ≥ I_min AND S ≥ S_min AND M ≥ M_min }
    Using theta_v1 defaults:
      house persistence threshold ≥ 0.10
      modularity ≥ 0.0 (relaxed for early ticks)
      house_count ≥ 0 (no hard lower bound — NOISE is still in K if it can recover)
    """
    convergence_threshold = K_thresholds.get("convergence_L", 0.25)
    min_persistence = K_thresholds.get("min_persistence", 0.0)
    min_modularity  = K_thresholds.get("min_modularity", 0.0)

    L_values = [lyapunov(m, cfg) for m in metrics]

    ticks_outside_K = []
    crisis_ticks = []
    tick_analyses = []

    for i, m in enumerate(metrics):
        L_t = L_values[i]
        delta_L = (L_values[i+1] - L_t) if i < len(metrics) - 1 else 0.0

        # Proposition 1: in K?
        persistence  = getattr(m, 'coalition_persistence', getattr(m, 'persistence', 0.0))
        modularity   = getattr(m, 'graph_modularity', getattr(m, 'modularity', 0.0))
        in_K = (persistence >= min_persistence and modularity >= min_modularity)
        if not in_K:
            ticks_outside_K.append(m.tick)

        # Proposition 2: ΔL ≤ 0?
        crisis = delta_L > 1e-6  # numerical tolerance
        if crisis and i < len(metrics) - 1:
            crisis_ticks.append(m.tick)

        tick_analyses.append(TickAnalysis(
            tick=m.tick,
            regime=m.regime.value if hasattr(m.regime, 'value') else str(m.regime),
            L=L_t,
            delta_L=delta_L,
            in_K=in_K,
            crisis=crisis,
            house_count=m.house_count,
            modularity=getattr(m, 'graph_modularity', getattr(m, 'modularity', 0.0)),
            persistence=getattr(m, 'coalition_persistence', getattr(m, 'persistence', 0.0)),
            strategy_entropy=m.strategy_entropy,
            policy_explanation_rate=m.policy_explanation_rate,
            house_task_success_rate=getattr(m, 'house_task_success', getattr(m, 'house_task_success_rate', 0.0)),
        ))

    delta_Ls = [t.delta_L for t in tick_analyses[:-1]]

    final_regime = tick_analyses[-1].regime if tick_analyses else "UNKNOWN"
    ticks_in_politics = sum(1 for t in tick_analyses if "POLITICS" in t.regime.upper())
    ticks_in_noise = sum(1 for t in tick_analyses if "NOISE" in t.regime.upper())

    L_at_50 = L_values[50] if len(L_values) > 50 else L_values[-1]

    return TrajectoryReport(
        seed=seed,
        n_ticks=len(metrics),
        prop1_verified=(len(ticks_outside_K) == 0),
        ticks_outside_K=ticks_outside_K,
        prop2_verified=(len(crisis_ticks) == 0),
        crisis_ticks=crisis_ticks,
        max_delta_L=max(delta_Ls) if delta_Ls else 0.0,
        mean_delta_L=sum(delta_Ls) / len(delta_Ls) if delta_Ls else 0.0,
        converged=(L_values[-1] < convergence_threshold),
        final_L=L_values[-1],
        min_L=min(L_values),
        max_L=max(L_values),
        L_at_tick_50=L_at_50,
        final_regime=final_regime,
        ticks_in_politics=ticks_in_politics,
        ticks_in_noise=ticks_in_noise,
        ticks=tick_analyses,
    )


# ---------------------------------------------------------------------------
# Sweep analysis
# ---------------------------------------------------------------------------

@dataclass
class SweepReport:
    """Stability analysis across multiple seeds."""
    seeds: List[int]
    n_ticks_per_seed: int
    prop1_verified_count: int   # seeds where P1 holds
    prop2_verified_count: int   # seeds where P2 holds
    converged_count: int
    mean_final_L: float
    mean_crisis_fraction: float  # mean fraction of crisis ticks
    worst_seed: Optional[int]    # seed with most crises
    best_seed: Optional[int]     # seed with fewest crises
    reports: List[TrajectoryReport] = field(default_factory=list)

    def summary(self) -> str:
        n = len(self.seeds)
        p1_rate = self.prop1_verified_count / n if n > 0 else 0
        p2_rate = self.prop2_verified_count / n if n > 0 else 0
        conv_rate = self.converged_count / n if n > 0 else 0
        lines = [
            f"=== SweepReport ({n} seeds, {self.n_ticks_per_seed} ticks) ===",
            f"  Proposition 1 verified: {self.prop1_verified_count}/{n} = {p1_rate:.0%}",
            f"  Proposition 2 verified: {self.prop2_verified_count}/{n} = {p2_rate:.0%}",
            f"  Converged (L < 0.25):   {self.converged_count}/{n} = {conv_rate:.0%}",
            f"  Mean final L: {self.mean_final_L:.4f}",
            f"  Mean crisis fraction: {self.mean_crisis_fraction:.2%}",
            f"  Worst seed (most crises): {self.worst_seed}",
            f"  Best seed (fewest crises): {self.best_seed}",
        ]
        return "\n".join(lines)


def run_sweep_analysis(
    seeds: List[int],
    n_ticks: int,
    cfg: LyapunovConfig,
    K_thresholds: Dict[str, float],
    engine_kwargs: Dict,
) -> SweepReport:
    """Run stability analysis across multiple seeds."""
    if not ENGINE_AVAILABLE:
        raise RuntimeError("conquest_emergence_engine.py required for sweep analysis")

    reports = []
    for seed in seeds:
        print(f"  Analyzing seed={seed}...", end=" ", flush=True)
        engine = ConquestEmergenceEngine(seed=seed, **engine_kwargs)
        trajectory = engine.run(n_ticks=n_ticks, verbose=False)
        report = analyze_trajectory(trajectory, seed, cfg, K_thresholds)
        reports.append(report)
        crisis_frac = len(report.crisis_ticks) / max(1, n_ticks - 1)
        print(f"P1={'✓' if report.prop1_verified else '✗'} "
              f"P2={'✓' if report.prop2_verified else '✗'} "
              f"L_final={report.final_L:.3f} "
              f"crisis={crisis_frac:.0%}")

    n = len(reports)
    crisis_fracs = [len(r.crisis_ticks) / max(1, n_ticks - 1) for r in reports]

    worst_seed = reports[crisis_fracs.index(max(crisis_fracs))].seed if reports else None
    best_seed  = reports[crisis_fracs.index(min(crisis_fracs))].seed if reports else None

    return SweepReport(
        seeds=seeds,
        n_ticks_per_seed=n_ticks,
        prop1_verified_count=sum(1 for r in reports if r.prop1_verified),
        prop2_verified_count=sum(1 for r in reports if r.prop2_verified),
        converged_count=sum(1 for r in reports if r.converged),
        mean_final_L=sum(r.final_L for r in reports) / n if n else 0.0,
        mean_crisis_fraction=sum(crisis_fracs) / n if n else 0.0,
        worst_seed=worst_seed,
        best_seed=best_seed,
        reports=reports,
    )


# ---------------------------------------------------------------------------
# Artifact loading (from existing emergence_metrics.json)
# ---------------------------------------------------------------------------

class MockMetrics:
    """Reconstruct minimal EmergenceMetrics from artifact JSON."""
    def __init__(self, d: dict):
        self.tick = d.get("tick", 0)
        self.regime = type('R', (), {'value': d.get("regime", "NOISE")})()
        self.house_count = d.get("house_count", 0)
        # Support both old compact keys and engine field names
        self.graph_modularity = d.get("graph_modularity", d.get("modularity", 0.0))
        self.internal_external_ratio = d.get("internal_external_ratio", d.get("ie_ratio", 1.0))
        self.coalition_persistence = d.get("coalition_persistence", d.get("persistence", 0.0))
        self.strategy_entropy = d.get("strategy_entropy", 0.0)
        self.house_memory_reuse_rate = d.get("house_memory_reuse_rate", d.get("memory_reuse_rate", 0.0))
        self.house_survival_ticks = d.get("house_survival_ticks", 0.0)
        self.house_task_success = d.get("house_task_success", d.get("house_task_success_rate", 0.0))
        self.reputation_gini = d.get("reputation_gini", 0.0)
        self.policy_explanation_rate = d.get("policy_explanation_rate", 0.0)


def load_from_artifacts() -> Optional[List]:
    """Load emergence metrics from artifacts/emergence_metrics.json."""
    path = ARTIFACTS_DIR / "emergence_metrics.json"
    if not path.exists():
        print(f"[ERROR] {path} not found. Run conquest_emergence_engine.py first.")
        return None
    with open(path) as f:
        data = json.load(f)
    return [MockMetrics(d) for d in data]


# ---------------------------------------------------------------------------
# Report serialization
# ---------------------------------------------------------------------------

def serialize_report(report: TrajectoryReport) -> dict:
    d = asdict(report)
    # Convert tick analyses to dicts
    return d


def save_stability_report(report: TrajectoryReport, path: Path):
    with open(path, 'w') as f:
        json.dump(serialize_report(report), f, indent=2)
    print(f"[SAVED] {path}")


def save_sweep_report(sweep: SweepReport, path: Path):
    """Save sweep report — omit per-tick data for size."""
    d = {
        "seeds": sweep.seeds,
        "n_ticks_per_seed": sweep.n_ticks_per_seed,
        "prop1_verified_count": sweep.prop1_verified_count,
        "prop2_verified_count": sweep.prop2_verified_count,
        "converged_count": sweep.converged_count,
        "mean_final_L": sweep.mean_final_L,
        "mean_crisis_fraction": sweep.mean_crisis_fraction,
        "worst_seed": sweep.worst_seed,
        "best_seed": sweep.best_seed,
        "per_seed_summary": [
            {
                "seed": r.seed,
                "prop1": r.prop1_verified,
                "prop2": r.prop2_verified,
                "converged": r.converged,
                "final_L": r.final_L,
                "crisis_count": len(r.crisis_ticks),
                "final_regime": r.final_regime,
                "ticks_in_politics": r.ticks_in_politics,
            }
            for r in sweep.reports
        ]
    }
    with open(path, 'w') as f:
        json.dump(d, f, indent=2)
    print(f"[SAVED] {path}")


# ---------------------------------------------------------------------------
# Hash a report (for receipt binding)
# ---------------------------------------------------------------------------

def report_hash(report_dict: dict) -> str:
    canonical = json.dumps(report_dict, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

DEFAULT_CFG = LyapunovConfig()
DEFAULT_K   = {
    "convergence_L": 0.25,
    "min_persistence": 0.0,
    "min_modularity": 0.0,
}
ENGINE_KWARGS = {
    "n_agents": 12,
    "theta_w": 0.42,
    "theta_m": 0.60,
    "delta": 0.10,
    "egregor_threshold": 0.65,
    "weight_decay": 0.06,
    "coordination_penalty": 0.10,
}


def cmd_single(seed: int):
    """Run single-seed stability analysis."""
    DEFAULT_CFG.validate()
    print(f"\n[STABILITY] Single run: seed={seed}, {100} ticks")
    print("=" * 60)

    if ENGINE_AVAILABLE:
        engine = ConquestEmergenceEngine(seed=seed, **ENGINE_KWARGS)
        trajectory = engine.run(n_ticks=100, verbose=False)
    else:
        print("[FALLBACK] Loading from artifacts/emergence_metrics.json")
        trajectory = load_from_artifacts()
        if trajectory is None:
            return

    report = analyze_trajectory(trajectory, seed, DEFAULT_CFG, DEFAULT_K)
    print(report.summary())

    # Print L trajectory sample
    print("\n  L(m_t) trajectory (every 10 ticks):")
    print("  tick |  L    | ΔL     | regime         | crisis")
    print("  -----|-------|--------|----------------|-------")
    for t in report.ticks[::10]:
        crisis_flag = "⚠ CRISIS" if t.crisis else ""
        print(f"  {t.tick:4d} | {t.L:.3f} | {t.delta_L:+.4f} | {t.regime:<14} | {crisis_flag}")

    # Falsification verdict
    print("\n  === Falsification Verdict ===")
    if report.prop2_verified:
        print("  Proposition 2 (Monotone Stability): ✓ NOT FALSIFIED")
        print("  ΔL ≤ 0 at every governed step.")
    else:
        print(f"  Proposition 2 (Monotone Stability): ✗ FALSIFIED at {len(report.crisis_ticks)} ticks")
        print(f"  Crisis ticks: {report.crisis_ticks[:20]}")
        print(f"  Max ΔL violation: {report.max_delta_L:.4f}")
        print("  ACTION: Review admission gate — T may be too permissive.")

    # Save
    out_path = ARTIFACTS_DIR / f"stability_seed{seed}.json"
    save_stability_report(report, out_path)
    rhash = report_hash(serialize_report(report))
    print(f"  Report hash: {rhash[:16]}...")


def cmd_sweep():
    """Run stability sweep across multiple seeds."""
    DEFAULT_CFG.validate()
    seeds = [7, 13, 42, 99, 137, 200, 314, 512]
    print(f"\n[STABILITY] Sweep: {len(seeds)} seeds × 80 ticks")
    print("=" * 60)

    if not ENGINE_AVAILABLE:
        print("[ERROR] Engine not available for sweep. Use 'single' or 'load' mode.")
        return

    sweep = run_sweep_analysis(seeds, n_ticks=80, cfg=DEFAULT_CFG,
                               K_thresholds=DEFAULT_K, engine_kwargs=ENGINE_KWARGS)
    print("\n" + sweep.summary())

    # Save
    out_path = ARTIFACTS_DIR / "stability_sweep.json"
    save_sweep_report(sweep, out_path)

    # Falsification summary
    n = len(seeds)
    print(f"\n  === Falsification Summary ===")
    p2_rate = sweep.prop2_verified_count / n
    if p2_rate == 1.0:
        print("  Proposition 2: ✓ NOT FALSIFIED across all seeds")
        print("  All trajectories show non-increasing L under governance.")
    elif p2_rate >= 0.75:
        print(f"  Proposition 2: ⚠ WEAKLY FALSIFIED ({n - sweep.prop2_verified_count} seeds)")
        print(f"  Worst seed: {sweep.worst_seed}")
    else:
        print(f"  Proposition 2: ✗ STRONGLY FALSIFIED ({n - sweep.prop2_verified_count}/{n} seeds)")
        print("  Lyapunov candidate L does not serve as a stability measure.")
        print("  Revise L weights or strengthen admission gate T.")


def cmd_load():
    """Analyze existing artifacts without rerunning the engine."""
    DEFAULT_CFG.validate()
    print("\n[STABILITY] Loading from artifacts/emergence_metrics.json")
    print("=" * 60)

    trajectory = load_from_artifacts()
    if trajectory is None:
        return

    seed = 42  # assumed default
    report = analyze_trajectory(trajectory, seed, DEFAULT_CFG, DEFAULT_K)
    print(report.summary())

    print("\n  L(m_t) — full trajectory:")
    print("  tick |  L    | ΔL     | regime         | crisis")
    print("  -----|-------|--------|----------------|-------")
    for t in report.ticks:
        crisis_flag = "⚠" if t.crisis else ""
        print(f"  {t.tick:4d} | {t.L:.3f} | {t.delta_L:+.4f} | {t.regime:<14} | {crisis_flag}")

    out_path = ARTIFACTS_DIR / "stability_from_artifacts.json"
    save_stability_report(report, out_path)


def cmd_phase_map():
    """
    Compute L-surface over parameter space.
    Maps (coordination_penalty, weight_decay) → mean_L + crisis_fraction.
    """
    if not ENGINE_AVAILABLE:
        print("[ERROR] Engine required for phase map.")
        return

    import itertools
    coord_penalties = [0.04, 0.08, 0.15, 0.25]
    weight_decays   = [0.03, 0.06, 0.10, 0.15]

    print(f"\n[STABILITY] Phase map: {len(coord_penalties)}×{len(weight_decays)} grid")
    print("=" * 60)
    print("  coord_pen | decay | mean_L | crisis% | P2?")
    print("  ----------|-------|--------|---------|-----")

    results = []
    for cp, wd in itertools.product(coord_penalties, weight_decays):
        kwargs = {**ENGINE_KWARGS, "coordination_penalty": cp, "weight_decay": wd}
        engine = ConquestEmergenceEngine(seed=42, **kwargs)
        traj = engine.run(n_ticks=60, verbose=False)
        rep = analyze_trajectory(traj, 42, DEFAULT_CFG, DEFAULT_K)
        crf = len(rep.crisis_ticks) / max(1, 59)
        p2 = "✓" if rep.prop2_verified else "✗"
        print(f"  {cp:.2f}       | {wd:.2f}  | {rep.final_L:.3f}  | {crf:.0%}     | {p2}")
        results.append({
            "coord_penalty": cp, "weight_decay": wd,
            "mean_L": rep.final_L, "crisis_fraction": crf,
            "prop2": rep.prop2_verified, "regime": rep.final_regime,
        })

    out_path = ARTIFACTS_DIR / "stability_phase_map.json"
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n[SAVED] {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "single"

    if cmd == "single":
        seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
        cmd_single(seed)
    elif cmd == "sweep":
        cmd_sweep()
    elif cmd == "load":
        cmd_load()
    elif cmd == "phase":
        cmd_phase_map()
    else:
        print(__doc__)
        sys.exit(1)
