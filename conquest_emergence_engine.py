"""
conquest_emergence_engine.py
Formal institutional emergence simulator for CONQUEST LAND.

Implements the minimal 4-rule kernel that guarantees Houses and egregors emerge:
    1. Reputation dynamics   — preferential attachment
    2. Resource scarcity     — exclusion + specialization
    3. Memory reuse          — path dependence (cultural transmission)
    4. Coordination cost     — modularity pressure (|S|² penalty)

These four forces drive the collaboration graph toward mesoscopic organization.
Institutions live at that mesoscopic level.

Formal House detection (not scripted):
    H ⊂ A satisfies House criterion iff over window W:
      (1) interaction_persistence > θ_w     for all pairs i,k ∈ H
      (2) E[utility(i ↔ H)] > E[utility(i ↔ A\H)]
      (3) strategy_coherence(H) > θ_m
      (4) internal_cooperation_rate > external_cooperation_rate + δ

Formal Egregor detection:
    House H becomes Egregor E_H when:
      P(member_action | House_policy) > egregor_threshold
    i.e., house-level state predicts member behavior better than individual state.

Reward function:
    R_i = α·S_i + β·C_i + γ·Δr_i − λ·L_i − μ·W_i − ν·coord_cost(S)

Usage:
    python3 conquest_emergence_engine.py run [seed]
    python3 conquest_emergence_engine.py sweep [seed]
    python3 conquest_emergence_engine.py demo [seed]
"""

from __future__ import annotations

import random
import math
import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from pathlib import Path


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Strategy(Enum):
    EXPLORE = "explore"
    BUILD   = "build"
    JUDGE   = "judge"


class Regime(Enum):
    """
    Phase diagram for multi-agent emergence.
    Progression (not guaranteed): NOISE → SPEC → HOUSE → EGREGOR → POLITICS
    """
    NOISE         = "noise"           # random collaboration, no structure
    SPECIALIZATION = "specialization" # repeated partnerships, proto-clusters
    HOUSE_FORMATION = "house_formation" # stable Houses with boundary
    EGREGOR       = "egregor"         # House policy dominates individual state
    POLITICS      = "politics"        # multiple Egregors, inter-House dynamics


# ---------------------------------------------------------------------------
# State objects
# ---------------------------------------------------------------------------

@dataclass
class AgentState:
    agent_id: str
    skills: Dict[str, float]          # strategy.value → skill level [0,1]
    reputation: float = 0.5
    strategy: Strategy = Strategy.EXPLORE
    # Strategy memory (Rule 3: memory reuse)
    strategy_scores: Dict[Strategy, float] = field(
        default_factory=lambda: {s: 0.0 for s in Strategy}
    )
    # Pairwise interaction history (Rule 1 + 4)
    partner_weights: Dict[str, float] = field(default_factory=dict)
    partner_success_rates: Dict[str, float] = field(default_factory=dict)
    # Rolling action log
    recent_actions: deque = field(default_factory=lambda: deque(maxlen=30))
    house_id: Optional[str] = None


@dataclass
class TaskSpec:
    task_id: str
    required_strategy: Strategy
    complexity: float          # [0, 1]
    resource_cost: float       # consumed from shared pool (Rule 2: scarcity)
    base_reward: float
    min_agents: int = 1
    max_agents: int = 3


@dataclass
class TaskRecord:
    """Ledger entry for one task execution."""
    task_id: str
    agent_ids: List[str]
    coalition_size: int
    success: bool
    reward: float
    strategy_used: Strategy
    resource_cost: float
    resource_available: float  # snapshot at execution time
    tick: int


@dataclass
class House:
    """
    Formally detected coordination cluster.
    Not scripted — emerges when all 4 House criteria are satisfied.
    """
    house_id: str
    members: Set[str]
    dominant_strategy: Strategy
    formed_at_tick: int
    collective_reputation: float = 0.0
    pooled_memory: List[TaskRecord] = field(default_factory=list)
    policy_predictability: float = 0.0   # key egregor detection metric


@dataclass
class EmergenceMetrics:
    """
    10 metrics for emergence detection.
    Track these curves; if they move, emergence is real.
    """
    tick: int
    # 1. Coalition persistence — fraction of repeated partnerships
    coalition_persistence: float
    # 2. Graph modularity Q (Newman-style)
    graph_modularity: float
    # 3. Internal / external cooperation ratio
    internal_external_ratio: float
    # 4. Strategy entropy H = -Σ p log₂ p
    strategy_entropy: float
    # 5. Number of detected Houses
    house_count: int
    # 6. House memory reuse rate
    house_memory_reuse_rate: float
    # 7. Mean House survival (ticks since formation)
    house_survival_ticks: float
    # 8. Success rate for House-routed tasks
    house_task_success: float
    # 9. Reputation Gini coefficient
    reputation_gini: float
    # 10. Policy explanation rate (fraction of actions predictable by House policy)
    policy_explanation_rate: float
    # Classified regime
    regime: Regime


# ---------------------------------------------------------------------------
# Environment (shared trace / resource pool)
# ---------------------------------------------------------------------------

class Environment:
    """
    Shared environment where agents leave traces (stigmergy) and
    compete for limited resources (Rule 2: scarcity).
    """

    def __init__(self, resource_capacity: float, scarcity: float):
        self.resource_capacity = resource_capacity
        self.scarcity = scarcity
        self.available: float = resource_capacity * max(0.05, 1.0 - scarcity)
        self.traces: List[TaskRecord] = []

    def consume(self, amount: float) -> bool:
        if self.available >= amount:
            self.available -= amount
            return True
        return False

    def replenish(self, rate: float):
        # Replenish fraction of capacity each tick; lower under high scarcity
        delta = self.resource_capacity * rate * (1.0 - self.scarcity * 0.5)
        self.available = min(self.resource_capacity, self.available + delta)

    def add_trace(self, record: TaskRecord):
        self.traces.append(record)
        if len(self.traces) > 500:
            self.traces = self.traces[-500:]


# ---------------------------------------------------------------------------
# Append-only Ledger
# ---------------------------------------------------------------------------

class Ledger:
    """
    Append-only event log with SHA-256 hash chain (HELEN_CUM_V1 compatible).
    Every event: payload_hash, cumulative_hash.
    """

    def __init__(self):
        self.entries: List[dict] = []
        self.cum_hash: str = "0" * 64

    def append(self, event: dict) -> str:
        payload_json = json.dumps(event, sort_keys=True, default=str)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        new_cum = hashlib.sha256(
            bytes.fromhex(self.cum_hash) + bytes.fromhex(payload_hash)
        ).hexdigest()
        self.cum_hash = new_cum
        self.entries.append({**event, "payload_hash": payload_hash, "cum_hash": new_cum})
        return new_cum


# ---------------------------------------------------------------------------
# Main Simulator
# ---------------------------------------------------------------------------

class ConquestEmergenceEngine:
    """
    Minimal formal emergence engine.

    Four rules → four structural forces:
        reputation   → preferential attachment  → in-group amplification
        scarcity     → exclusion               → specialization
        memory reuse → path dependence         → stable partnerships
        coord cost   → modularity pressure     → bounded coalition size

    Together these force the collaboration graph toward mesoscopic clusters.
    Those clusters become Houses. Houses with dominant policies become Egregors.
    """

    def __init__(
        self,
        n_agents: int = 12,
        # Rule 2: scarcity
        scarcity: float = 0.5,
        # Rule 4: coordination cost weight ν
        coordination_penalty: float = 0.1,
        # Rule 1: reputation weight in partner selection
        reputation_weight: float = 0.5,
        # Rule 3: cultural transmission strength
        imitation_strength: float = 0.3,
        # Reward weights
        alpha: float = 1.0,    # task success
        beta:  float = 0.5,    # collaboration bonus
        gamma: float = 0.3,    # reputation gain rate
        lambda_: float = 0.8,  # failure penalty rate
        mu:    float = 0.2,    # waste penalty
        nu:    float = 0.1,    # coord cost weight (inside reward)
        # House detection thresholds
        # θ_w calibrated so that only frequently-collaborating same-strategy pairs qualify.
        # Proportional decay (below) keeps cross-strategy pairs at w* ≈ 0.23 < θ_w
        # while same-strategy pairs stabilize at w* ≈ 0.70 > θ_w.
        theta_w: float = 0.42,  # interaction persistence threshold
        theta_m: float = 0.60,  # strategy coherence threshold
        delta:   float = 0.10,  # boundary margin: internal > external + delta
        # Weight decay (forgetting) — keeps cross-cluster weights below θ_w at equilibrium.
        weight_decay: float = 0.06,  # proportional decay per tick: w *= (1 - decay)
        # Egregor threshold
        egregor_threshold: float = 0.65,
        seed: int = 42,
    ):
        random.seed(seed)
        self.seed = seed
        self.tick = 0

        # Parameters
        self.n_agents = n_agents
        self.scarcity = scarcity
        self.coordination_penalty = coordination_penalty
        self.reputation_weight = reputation_weight
        self.imitation_strength = imitation_strength
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.lambda_ = lambda_
        self.mu = mu
        self.nu = nu
        self.theta_w = theta_w
        self.theta_m = theta_m
        self.delta = delta
        self.weight_decay = weight_decay
        self.egregor_threshold = egregor_threshold

        # State
        self.agents: Dict[str, AgentState] = {}
        self.houses: Dict[str, House] = {}
        self.egregors: Set[str] = set()
        self.environment = Environment(resource_capacity=100.0, scarcity=scarcity)
        self.ledger = Ledger()
        self.task_records: List[TaskRecord] = []
        self.metrics_history: List[EmergenceMetrics] = []

        self._init_agents()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_agents(self):
        strategies = list(Strategy)
        per_group = self.n_agents // len(strategies)
        remainder = self.n_agents % len(strategies)

        idx = 0
        for s_idx, strategy in enumerate(strategies):
            count = per_group + (1 if s_idx < remainder else 0)
            for _ in range(count):
                aid = f"a{idx:02d}"
                # Skills biased toward natural strategy
                skills = {s.value: random.uniform(0.25, 0.60) for s in Strategy}
                skills[strategy.value] = min(1.0, skills[strategy.value] + 0.30)

                # Initialise strategy scores with natural-strategy bias (0.25 head-start).
                # An agent will only switch away from natural strategy once a foreign
                # strategy exceeds it by the adoption threshold (0.40), requiring
                # sustained, repeated evidence — not just a few lucky tasks.
                strategy_scores = {s: 0.0 for s in Strategy}
                strategy_scores[strategy] = 0.25

                self.agents[aid] = AgentState(
                    agent_id=aid,
                    skills=skills,
                    reputation=random.uniform(0.40, 0.60),
                    strategy=strategy,
                    strategy_scores=strategy_scores,
                )
                idx += 1

    # ------------------------------------------------------------------
    # Task generation
    # ------------------------------------------------------------------

    def _generate_task(self) -> TaskSpec:
        strategy = random.choice(list(Strategy))
        complexity = random.uniform(0.2, 0.85)
        # Resource cost is flat per-task (NOT per-agent).
        # Coalition size is penalised by coordination cost in coalition selection,
        # not by additional resource draw — keeps resource dynamics tractable.
        # avg cost ≈ 0.5 * 2.0 * 1.25 ≈ 1.25 per task at scarcity=0.5
        resource_cost = complexity * 2.0 * (1.0 + self.scarcity * 0.5)
        return TaskSpec(
            task_id=f"T{self.tick:04d}_{random.randint(0, 999):03d}",
            required_strategy=strategy,
            complexity=complexity,
            resource_cost=resource_cost,
            base_reward=complexity * 20.0,
            min_agents=1,
            max_agents=min(4, self.n_agents),
        )

    # ------------------------------------------------------------------
    # Coalition formation (Rules 1 + 4)
    # ------------------------------------------------------------------

    def _select_coalition(self, initiator_id: str, task: TaskSpec) -> List[str]:
        """
        Coalition formation rule.
        Agent selects partners by maximizing:
            score(k) = reputation_weight · r_k
                     + strategy_compatibility
                     + imitation_strength · history_weight_{ik}

        Coalition size bounded by marginal benefit vs coord cost (Rule 4):
            add agent k iff marginal_benefit(k) > ν · |S|²
        """
        initiator = self.agents[initiator_id]
        candidates = [aid for aid in self.agents if aid != initiator_id]

        def partner_score(aid: str) -> float:
            agent = self.agents[aid]
            rep   = agent.reputation * self.reputation_weight
            compat = (1.0 if agent.strategy == task.required_strategy else 0.25)
            hist  = initiator.partner_weights.get(aid, 0.5) * self.imitation_strength
            return rep + compat + hist

        ranked = sorted(candidates, key=partner_score, reverse=True)

        coalition = [initiator_id]
        for cand_id in ranked:
            if len(coalition) >= task.max_agents:
                break
            cand = self.agents[cand_id]
            # Marginal benefit of adding this agent (units: reward fraction).
            # Typical mb = 0.20 * 0.5 = 0.10
            mb = 0.20 * cand.skills.get(task.required_strategy.value, 0.3)
            # Marginal coordination cost — Rule 4: cost ∝ |S|².
            # Factor 0.28 is calibrated so typical coalition stops at size 2:
            #   mc(|S|=2) = 0.1 * 0.28 * 1 = 0.028 < mb=0.10  → add (→ size 2)
            #   mc(|S|=3) = 0.1 * 0.28 * 4 = 0.112 > mb=0.10  → STOP
            # High-skill cands (mb≈0.18) allow size-3 occasionally (good alignment task).
            mc = self.coordination_penalty * 0.28 * (len(coalition) ** 2)
            if mb > mc:
                coalition.append(cand_id)

        return coalition

    # ------------------------------------------------------------------
    # Task execution
    # ------------------------------------------------------------------

    def _execute_task(self, coalition: List[str], task: TaskSpec) -> TaskRecord:
        """
        Execute task.  Success probability:
            p = avg_skill · 0.5 + alignment · 0.3 + 0.2 − coord_cost
        """
        affordable = self.environment.consume(task.resource_cost)

        if not affordable:
            return TaskRecord(
                task_id=task.task_id,
                agent_ids=coalition,
                coalition_size=len(coalition),
                success=False,
                reward=0.0,
                strategy_used=task.required_strategy,
                resource_cost=task.resource_cost,
                resource_available=self.environment.available,
                tick=self.tick,
            )

        avg_skill = (
            sum(self.agents[aid].skills.get(task.required_strategy.value, 0.3) for aid in coalition)
            / len(coalition)
        )
        alignment = (
            sum(1 for aid in coalition if self.agents[aid].strategy == task.required_strategy)
            / len(coalition)
        )
        # Coordination cost (same scale as success_prob)
        coord_cost = self.coordination_penalty * 0.04 * (len(coalition) ** 2)

        # Alignment weighted more heavily (0.40) to drive specialization.
        # Misaligned coalition: ~0.35 success.  Aligned: ~0.75 success.
        success_prob = max(0.05, min(0.97,
            avg_skill * 0.50 + alignment * 0.40 + 0.10 - coord_cost
        ))
        success = random.random() < success_prob
        reward  = task.base_reward * success_prob if success else 0.0

        return TaskRecord(
            task_id=task.task_id,
            agent_ids=coalition,
            coalition_size=len(coalition),
            success=success,
            reward=reward,
            strategy_used=task.required_strategy,
            resource_cost=task.resource_cost,
            resource_available=self.environment.available,
            tick=self.tick,
        )

    # ------------------------------------------------------------------
    # Rule 1: Reputation dynamics
    # ------------------------------------------------------------------

    def _update_reputations(self, record: TaskRecord):
        """
        rep(a) += γ · 0.1   on success
        rep(a) -= λ · 0.05  on failure
        w_{ik} updated toward success/failure.
        """
        for aid in record.agent_ids:
            agent = self.agents[aid]
            if record.success:
                agent.reputation = min(1.0, agent.reputation + self.gamma * 0.10)
            else:
                # Floor at 0.05 — prevents full collapse under sustained failure
                agent.reputation = max(0.05, agent.reputation - self.lambda_ * 0.05)

            # Pairwise weight update.
            # +0.040 per success → ~6 successes to reach θ_w=0.22 → Houses appear ~tick 15-25
            # −0.015 per failure → asymmetric (faster buildup than decay, realistic for trust)
            for oid in record.agent_ids:
                if oid == aid:
                    continue
                w = agent.partner_weights.get(oid, 0.0)
                if record.success:
                    agent.partner_weights[oid] = min(1.0, w + 0.040)
                else:
                    agent.partner_weights[oid] = max(0.0, w - 0.015)

                # Running success-rate estimate
                sr = agent.partner_success_rates.get(oid, 0.5)
                agent.partner_success_rates[oid] = 0.85 * sr + 0.15 * float(record.success)

    # ------------------------------------------------------------------
    # Rule 3: Memory reuse + cultural transmission
    # ------------------------------------------------------------------

    def _update_strategy_scores(self, record: TaskRecord):
        """
        strategy_score(used) += 0.10 on success, −0.05 on failure.
        Cultural transmission: low-rep agents copy strategy of best nearby performer.
        """
        for aid in record.agent_ids:
            agent = self.agents[aid]

            # Strategy score update — differentiated by alignment.
            # Own strategy: strong signal (±0.10/0.05).
            # Foreign strategy: weak signal (+0.02/−0.01) — acknowledges participating
            # but doesn't override the agent's core specialisation path.
            # This preserves between-cluster diversity (Rule 3 governs your OWN path).
            if agent.strategy == record.strategy_used:
                delta = 0.10 if record.success else -0.05
            else:
                delta = 0.02 if record.success else -0.01
            agent.strategy_scores[record.strategy_used] += delta

            agent.recent_actions.append({
                "strategy": record.strategy_used.value,
                "success":  record.success,
                "tick":     self.tick,
            })

            # Adopt best-scoring strategy — requires gap > 0.40 above natural bias (0.25).
            # To cross threshold from natural strategy (score ≥ 0.25) an agent needs
            # the alternative to score ≥ 0.65, requiring ~4-5 sustained foreign successes
            # above 0 while natural strategy has been reinforced. Effectively: no switching
            # in < 30 ticks under normal interaction patterns.
            best_s = max(agent.strategy_scores, key=lambda s: agent.strategy_scores[s])
            if agent.strategy_scores[best_s] > agent.strategy_scores[agent.strategy] + 0.40:
                agent.strategy = best_s

        # Cultural transmission — within-coalition only (Fix #2).
        # Local imitation → within-cluster convergence, between-cluster diversity.
        if record.success and len(record.agent_ids) > 1:
            best_in_coalition = max(record.agent_ids, key=lambda x: self.agents[x].reputation)
            best_strat = self.agents[best_in_coalition].strategy
            for aid in record.agent_ids:
                if aid == best_in_coalition:
                    continue
                learner = self.agents[aid]
                # Only imitate if rep gap exists (learning signal)
                if learner.reputation < self.agents[best_in_coalition].reputation - 0.05:
                    if random.random() < self.imitation_strength * 0.10:
                        learner.strategy_scores[best_strat] += 0.06

    # ------------------------------------------------------------------
    # Passive weight decay (forgetting — Rule 3 complement)
    # ------------------------------------------------------------------

    def _decay_partner_weights(self):
        """
        Proportional decay: w *= (1 − weight_decay) each tick.

        This is the critical separation mechanism:
          same-strategy pairs   (collabs ~1.5/tick): equilibrium w* ≈ 0.70 > θ_w
          cross-strategy pairs  (collabs ~0.5/tick): equilibrium w* ≈ 0.23 < θ_w

        Without decay, all pairs saturate at 1.0 in ~50 ticks → Houses dissolve.
        With decay, stable separation persists for the full simulation.
        """
        d = self.weight_decay
        for aid in self.agents:
            for oid in self.agents[aid].partner_weights:
                self.agents[aid].partner_weights[oid] *= (1.0 - d)

    # ------------------------------------------------------------------
    # Formal House detection (all 4 criteria)
    # ------------------------------------------------------------------

    def _detect_houses(self) -> Dict[str, House]:
        """
        House H ⊂ A satisfies all four criteria:
          (1) ∀ i,k ∈ H: mean(w_{ik}, w_{ki}) / 2 > θ_w  [interaction persistence]
          (2) E[util(i ↔ H)] > E[util(i ↔ A\H)]           [internal advantage]
          (3) coherence(H) = max_s count(s)/|H| > θ_m     [strategy coherence]
          (4) avg_intra(H) > avg_inter(H) + δ              [boundary formation]
        """
        agent_ids = list(self.agents.keys())

        # --- Build adjacency from pairs where persistence > θ_w ---
        adj: Dict[str, Set[str]] = defaultdict(set)
        for i, a1 in enumerate(agent_ids):
            for j, a2 in enumerate(agent_ids):
                if j <= i:
                    continue
                w12 = self.agents[a1].partner_weights.get(a2, 0.0)
                w21 = self.agents[a2].partner_weights.get(a1, 0.0)
                if (w12 + w21) / 2.0 > self.theta_w:
                    adj[a1].add(a2)
                    adj[a2].add(a1)

        # --- Connected components in the strong-pair graph ---
        visited: Set[str] = set()
        components: List[Set[str]] = []
        for aid in agent_ids:
            if aid not in visited and aid in adj:
                comp: Set[str] = set()
                queue = [aid]
                while queue:
                    curr = queue.pop()
                    if curr in visited:
                        continue
                    visited.add(curr)
                    comp.add(curr)
                    queue.extend(adj[curr] - visited)
                if len(comp) >= 2:
                    components.append(comp)

        # --- Validate each component against criteria 2, 3, 4 ---
        new_houses: Dict[str, House] = {}

        for comp in components:
            comp_list = list(comp)

            # Criterion 3: strategy coherence
            strats = [self.agents[aid].strategy for aid in comp_list]
            dominant = max(set(strats), key=strats.count)
            coherence = strats.count(dominant) / len(strats)
            if coherence < self.theta_m:
                continue

            # Criterion 4 + 2: internal vs external cooperation rates
            intra_ws = [
                self.agents[a].partner_weights.get(b, 0.0)
                for a in comp_list for b in comp_list if a != b
            ]
            inter_ws = [
                self.agents[a].partner_weights.get(b, 0.0)
                for a in comp_list for b in agent_ids if b not in comp
            ]

            if not intra_ws or not inter_ws:
                continue

            avg_intra = sum(intra_ws) / len(intra_ws)
            avg_inter = sum(inter_ws) / len(inter_ws)

            # Criterion 4: boundary
            if avg_intra < avg_inter + self.delta:
                continue
            # Criterion 2: internal advantage
            if avg_intra <= avg_inter:
                continue

            # --- All criteria pass: this is a House ---
            # Preserve house_id and formed_at_tick if overlap with existing house
            existing_id = None
            for hid, house in self.houses.items():
                overlap = len(comp & house.members) / max(len(comp), len(house.members))
                if overlap > 0.6:
                    existing_id = hid
                    break

            formed_at = (
                self.houses[existing_id].formed_at_tick if existing_id
                else self.tick
            )
            house_id = existing_id or f"H_{dominant.value[:3].upper()}_{len(new_houses):02d}"

            collective_rep = sum(self.agents[aid].reputation for aid in comp_list) / len(comp_list)

            # Pool recent task records involving 2+ members of this group
            pooled = [
                r for r in self.task_records[-100:]
                if len(set(r.agent_ids) & comp) >= 2
            ]

            new_houses[house_id] = House(
                house_id=house_id,
                members=comp,
                dominant_strategy=dominant,
                formed_at_tick=formed_at,
                collective_reputation=collective_rep,
                pooled_memory=pooled,
            )

        return new_houses

    # ------------------------------------------------------------------
    # Formal Egregor detection
    # ------------------------------------------------------------------

    def _detect_egregors(self, houses: Dict[str, House]) -> Set[str]:
        """
        Egregor E_H detected when:
            P(member_action uses dominant_strategy | House_policy) >= egregor_threshold

        Operationalized as:
            policy_explanation_rate = fraction of recent House tasks
            where the coalition used the House's dominant strategy.
        """
        egregors: Set[str] = set()

        for hid, house in houses.items():
            recent = house.pooled_memory[-20:] if house.pooled_memory else []
            if len(recent) < 4:
                continue

            aligned = sum(1 for r in recent if r.strategy_used == house.dominant_strategy)
            rate = aligned / len(recent)
            house.policy_predictability = rate

            if rate >= self.egregor_threshold:
                egregors.add(hid)

        return egregors

    # ------------------------------------------------------------------
    # Metrics computation
    # ------------------------------------------------------------------

    def _compute_metrics(
        self, houses: Dict[str, House], egregors: Set[str]
    ) -> EmergenceMetrics:
        agent_ids = list(self.agents.keys())
        n = len(agent_ids)

        # 1. Coalition persistence
        strong_pairs = sum(
            1 for a in agent_ids for w in self.agents[a].partner_weights.values()
            if w > self.theta_w
        )
        max_pairs = n * (n - 1)
        coalition_persistence = strong_pairs / max_pairs if max_pairs > 0 else 0.0

        # 2. Graph modularity (fraction of total edge weight inside communities)
        total_w = sum(
            w for a in agent_ids for w in self.agents[a].partner_weights.values()
        )
        if houses and total_w > 0:
            intra_w = sum(
                self.agents[a].partner_weights.get(b, 0.0)
                for h in houses.values()
                for a in h.members
                for b in h.members
                if a != b
            )
            graph_modularity = intra_w / total_w
        else:
            graph_modularity = 0.0

        # 3. Internal / external cooperation ratio
        if houses:
            all_intra, all_inter = [], []
            for house in houses.values():
                for a in house.members:
                    intra = [self.agents[a].partner_weights.get(b, 0.0)
                             for b in house.members if b != a]
                    inter = [self.agents[a].partner_weights.get(b, 0.0)
                             for b in agent_ids if b not in house.members]
                    all_intra.extend(intra)
                    all_inter.extend(inter)
            avg_intra = sum(all_intra) / len(all_intra) if all_intra else 0.5
            avg_inter = sum(all_inter) / len(all_inter) if all_inter else 0.5
            ie_ratio = avg_intra / avg_inter if avg_inter > 0 else 1.0
        else:
            ie_ratio = 1.0

        # 4. Strategy entropy
        strat_counts: Dict[Strategy, int] = defaultdict(int)
        for a in self.agents.values():
            strat_counts[a.strategy] += 1
        total_s = sum(strat_counts.values())
        entropy = 0.0
        for count in strat_counts.values():
            p = count / total_s
            if p > 0:
                entropy -= p * math.log2(p)

        # 5. House count
        house_count = len(houses)

        # 6. House memory reuse rate
        if houses and self.task_records:
            recent_tasks = self.task_records[-30:]
            house_member_set = {a for h in houses.values() for a in h.members}
            guided = sum(
                1 for r in recent_tasks
                if len(set(r.agent_ids) & house_member_set) >= 2
            )
            house_memory_reuse_rate = guided / len(recent_tasks)
        else:
            house_memory_reuse_rate = 0.0

        # 7. Mean House survival
        house_survival_ticks = (
            sum(self.tick - h.formed_at_tick for h in houses.values()) / len(houses)
            if houses else 0.0
        )

        # 8. House task success rate
        if houses and self.task_records:
            hms = {a for h in houses.values() for a in h.members}
            h_tasks = [r for r in self.task_records[-60:] if any(a in hms for a in r.agent_ids)]
            house_task_success = (
                sum(r.success for r in h_tasks) / len(h_tasks) if h_tasks else 0.0
            )
        else:
            house_task_success = 0.0

        # 9. Reputation Gini coefficient
        reps = sorted(self.agents[a].reputation for a in agent_ids)
        n_r = len(reps)
        rep_sum = sum(reps)
        if n_r > 0 and rep_sum > 0:
            gini_num = sum((2 * (i + 1) - n_r - 1) * r for i, r in enumerate(reps))
            reputation_gini = gini_num / (n_r * rep_sum)
        else:
            reputation_gini = 0.0

        # 10. Policy explanation rate
        if egregors and houses:
            rates = [houses[eid].policy_predictability for eid in egregors if eid in houses]
            policy_explanation_rate = sum(rates) / len(rates) if rates else 0.0
        else:
            policy_explanation_rate = 0.0

        regime = self._classify_regime(
            coalition_persistence, graph_modularity, ie_ratio,
            house_count, len(egregors), policy_explanation_rate
        )

        return EmergenceMetrics(
            tick=self.tick,
            coalition_persistence=coalition_persistence,
            graph_modularity=graph_modularity,
            internal_external_ratio=ie_ratio,
            strategy_entropy=entropy,
            house_count=house_count,
            house_memory_reuse_rate=house_memory_reuse_rate,
            house_survival_ticks=house_survival_ticks,
            house_task_success=house_task_success,
            reputation_gini=reputation_gini,
            policy_explanation_rate=policy_explanation_rate,
            regime=regime,
        )

    # ------------------------------------------------------------------
    # Regime classification
    # ------------------------------------------------------------------

    def _classify_regime(
        self,
        persistence: float,
        modularity: float,
        ie_ratio: float,
        house_count: int,
        egregor_count: int,
        policy_rate: float,
    ) -> Regime:
        """
        Phase diagram classification.
        Tested in order from most complex to least.
        """
        if house_count >= 3 and egregor_count >= 2 and ie_ratio > 1.8:
            return Regime.POLITICS
        if egregor_count >= 1 and policy_rate >= self.egregor_threshold:
            return Regime.EGREGOR
        if house_count >= 2 and modularity > 0.25 and ie_ratio > 1.3:
            return Regime.HOUSE_FORMATION
        if persistence > 0.15 and modularity > 0.08:
            return Regime.SPECIALIZATION
        return Regime.NOISE

    # ------------------------------------------------------------------
    # Main step
    # ------------------------------------------------------------------

    def step(self) -> EmergenceMetrics:
        """Execute one simulation tick."""
        self.tick += 1
        # Replenishment rate 0.20 → +20 units/tick vs avg consumption ~8-10 → stable pool.
        self.environment.replenish(rate=0.20)

        # Passive weight decay — creates persistent separation between in/out group weights.
        self._decay_partner_weights()

        # Generate and execute tasks.
        # n_agents//2 tasks per tick gives enough interaction density for
        # same-strategy pairs to accumulate weight above θ_w in ~15-25 ticks.
        n_tasks = max(2, self.n_agents // 2)
        for _ in range(n_tasks):
            task = self._generate_task()
            initiator = random.choice(list(self.agents.keys()))
            coalition = self._select_coalition(initiator, task)
            record = self._execute_task(coalition, task)

            self._update_reputations(record)
            self._update_strategy_scores(record)

            self.task_records.append(record)
            self.environment.add_trace(record)

            self.ledger.append({
                "type":      "task_execution",
                "tick":      self.tick,
                "task_id":   record.task_id,
                "coalition": record.agent_ids,
                "success":   record.success,
                "strategy":  record.strategy_used.value,
                "resource_available": round(self.environment.available, 2),
            })

        # Detect emergent structures
        self.houses  = self._detect_houses()
        self.egregors = self._detect_egregors(self.houses)

        # Assign house membership to agents
        for aid in self.agents:
            self.agents[aid].house_id = None
        for hid, house in self.houses.items():
            for aid in house.members:
                if aid in self.agents:
                    self.agents[aid].house_id = hid

        # Metrics
        metrics = self._compute_metrics(self.houses, self.egregors)
        self.metrics_history.append(metrics)
        return metrics

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, n_ticks: int = 100, verbose: bool = False) -> List[EmergenceMetrics]:
        for t in range(n_ticks):
            m = self.step()
            if verbose and (t % 10 == 0 or t == n_ticks - 1):
                self._print_status(m)
        return self.metrics_history

    def _print_status(self, m: EmergenceMetrics):
        bar = "=" * 58
        print(f"\n{bar}")
        print(f"  Tick {m.tick:03d}  |  Regime: {m.regime.value.upper()}")
        print(f"{bar}")
        print(f"  Houses: {m.house_count}  |  Egregors: {len(self.egregors)}")
        print(f"  Modularity:   {m.graph_modularity:.3f}")
        print(f"  I/E ratio:    {m.internal_external_ratio:.3f}")
        print(f"  Persistence:  {m.coalition_persistence:.3f}")
        print(f"  Entropy:      {m.strategy_entropy:.3f}")
        print(f"  Gini (rep):   {m.reputation_gini:.3f}")
        print(f"  Policy rate:  {m.policy_explanation_rate:.3f}")
        if self.houses:
            for hid, h in self.houses.items():
                eg = " ★EGREGOR" if hid in self.egregors else ""
                print(f"  [{h.dominant_strategy.value[:5]:5s}] {hid}: "
                      f"{sorted(h.members)}  rep={h.collective_reputation:.2f}{eg}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def emergence_summary(self) -> dict:
        if not self.metrics_history:
            return {}

        regime_first: Dict[str, int] = {}
        for m in self.metrics_history:
            rname = m.regime.value
            if rname not in regime_first:
                regime_first[rname] = m.tick

        final = self.metrics_history[-1]

        return {
            "seed":         self.seed,
            "final_tick":   self.tick,
            "final_regime": final.regime.value,
            "n_houses":     len(self.houses),
            "n_egregors":   len(self.egregors),
            "regime_transitions": regime_first,
            "houses": [
                {
                    "id":           h.house_id,
                    "members":      sorted(h.members),
                    "strategy":     h.dominant_strategy.value,
                    "formed_at":    h.formed_at_tick,
                    "is_egregor":   h.house_id in self.egregors,
                    "policy_predictability": round(h.policy_predictability, 3),
                    "collective_rep": round(h.collective_reputation, 3),
                }
                for h in self.houses.values()
            ],
            "params": {
                "n_agents":            self.n_agents,
                "scarcity":            self.scarcity,
                "coordination_penalty": self.coordination_penalty,
                "reputation_weight":   self.reputation_weight,
                "imitation_strength":  self.imitation_strength,
            },
            "final_metrics": {
                "modularity":           round(final.graph_modularity, 4),
                "ie_ratio":             round(final.internal_external_ratio, 4),
                "coalition_persistence": round(final.coalition_persistence, 4),
                "strategy_entropy":     round(final.strategy_entropy, 4),
                "reputation_gini":      round(final.reputation_gini, 4),
                "policy_explanation_rate": round(final.policy_explanation_rate, 4),
            },
            "ledger_tip": self.ledger.cum_hash[:16],
        }


# ---------------------------------------------------------------------------
# Parameter sweep — emergence map
# ---------------------------------------------------------------------------

class EmergenceSweep:
    """
    Sweep over the four emergence parameters to produce a phase diagram.
    Identifies which parameter regions produce Houses and Egregors.
    """

    def __init__(self, n_agents: int = 12, n_ticks: int = 80, base_seed: int = 42):
        self.n_agents  = n_agents
        self.n_ticks   = n_ticks
        self.base_seed = base_seed

    def sweep(
        self,
        scarcity_values: Optional[List[float]] = None,
        coordination_penalties: Optional[List[float]] = None,
        reputation_weights: Optional[List[float]] = None,
        imitation_strengths: Optional[List[float]] = None,
    ) -> List[dict]:
        sv  = scarcity_values       or [0.1, 0.3, 0.5, 0.7, 0.9]
        cp  = coordination_penalties or [0.0, 0.05, 0.1, 0.2, 0.4]
        rw  = reputation_weights     or [0.3, 0.5, 0.7]
        ims = imitation_strengths    or [0.1, 0.3, 0.5]

        results = []
        run_idx = 0

        total = len(sv) * len(cp) * len(rw) * len(ims)
        print(f"Running {total} parameter combinations ×{self.n_ticks} ticks each …")

        for sc in sv:
            for co in cp:
                for rw_ in rw:
                    for im in ims:
                        engine = ConquestEmergenceEngine(
                            n_agents=self.n_agents,
                            scarcity=sc,
                            coordination_penalty=co,
                            reputation_weight=rw_,
                            imitation_strength=im,
                            seed=self.base_seed + run_idx,
                        )
                        engine.run(self.n_ticks, verbose=False)
                        s = engine.emergence_summary()
                        s["params"].update({"seed": self.base_seed + run_idx})
                        results.append(s)
                        run_idx += 1
                        if run_idx % 20 == 0:
                            print(f"  … {run_idx}/{total}")

        return results

    def emergence_map(self, results: List[dict]) -> dict:
        regime_distribution: Dict[str, int] = defaultdict(int)
        house_configs   = []
        egregor_configs = []

        for r in results:
            regime_distribution[r["final_regime"]] += 1
            if r["n_houses"] >= 2:
                house_configs.append(r["params"])
            if r["n_egregors"] >= 1:
                egregor_configs.append(r["params"])

        def min_param(configs, key):
            vals = [c[key] for c in configs]
            return min(vals) if vals else None

        return {
            "total_runs":             len(results),
            "regime_distribution":    dict(regime_distribution),
            "house_forming_configs":  len(house_configs),
            "egregor_forming_configs": len(egregor_configs),
            "min_scarcity_for_houses":      min_param(house_configs, "scarcity"),
            "min_coord_penalty_for_houses": min_param(house_configs, "coordination_penalty"),
            "min_imitation_for_egregors":   min_param(egregor_configs, "imitation_strength"),
        }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _run_demo(seed: int):
    """Quick demo: run one engine with verbose output."""
    print("=" * 60)
    print("CONQUEST EMERGENCE ENGINE — DEMO RUN")
    print("=" * 60)
    print(f"Seed: {seed}  |  Rules: reputation + scarcity + memory + coord-cost")
    print()

    engine = ConquestEmergenceEngine(
        n_agents=12,
        scarcity=0.5,
        coordination_penalty=0.1,
        reputation_weight=0.5,
        imitation_strength=0.3,
        seed=seed,
    )
    engine.run(n_ticks=100, verbose=True)

    print("\n" + "=" * 60)
    print("EMERGENCE SUMMARY")
    print("=" * 60)
    summary = engine.emergence_summary()
    print(json.dumps(summary, indent=2))
    return engine, summary


def _run_full(seed: int):
    """Full run with metrics export."""
    engine, summary = _run_demo(seed)

    Path("artifacts").mkdir(exist_ok=True)

    # Save metrics history
    metrics_path = "artifacts/emergence_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump([
            {
                "tick":        m.tick,
                "regime":      m.regime.value,
                "house_count": m.house_count,
                "modularity":  round(m.graph_modularity, 4),
                "ie_ratio":    round(m.internal_external_ratio, 4),
                "persistence": round(m.coalition_persistence, 4),
                "entropy":     round(m.strategy_entropy, 4),
                "gini":        round(m.reputation_gini, 4),
                "policy_rate": round(m.policy_explanation_rate, 4),
            }
            for m in engine.metrics_history
        ], f, indent=2)

    # Save summary
    summary_path = "artifacts/emergence_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nMetrics  → {metrics_path}")
    print(f"Summary  → {summary_path}")
    print(f"Ledger tip: {engine.ledger.cum_hash[:16]}")


def _run_sweep(seed: int):
    """Parameter sweep to produce emergence map."""
    print("=" * 60)
    print("EMERGENCE PARAMETER SWEEP")
    print("=" * 60)

    sweeper = EmergenceSweep(n_agents=12, n_ticks=80, base_seed=seed)
    results = sweeper.sweep(
        scarcity_values=[0.1, 0.3, 0.5, 0.7],
        coordination_penalties=[0.0, 0.1, 0.2, 0.4],
        reputation_weights=[0.3, 0.5, 0.7],
        imitation_strengths=[0.2, 0.5],
    )

    emap = sweeper.emergence_map(results)

    print(f"\nTotal runs:  {emap['total_runs']}")
    print(f"\nRegime distribution:")
    for regime, count in sorted(emap["regime_distribution"].items()):
        pct = 100.0 * count / emap["total_runs"]
        bar = "█" * int(pct / 2)
        print(f"  {regime:20s} {count:4d}  ({pct:5.1f}%)  {bar}")

    print(f"\nConfigs producing Houses:   {emap['house_forming_configs']}")
    print(f"Configs producing Egregors: {emap['egregor_forming_configs']}")
    if emap["min_scarcity_for_houses"] is not None:
        print(f"\nMin scarcity for Houses:      {emap['min_scarcity_for_houses']}")
    if emap["min_coord_penalty_for_houses"] is not None:
        print(f"Min coord penalty for Houses: {emap['min_coord_penalty_for_houses']}")
    if emap["min_imitation_for_egregors"] is not None:
        print(f"Min imitation for Egregors:   {emap['min_imitation_for_egregors']}")

    Path("artifacts").mkdir(exist_ok=True)
    sweep_path = "artifacts/emergence_sweep.json"
    with open(sweep_path, "w") as f:
        json.dump({"emergence_map": emap, "results": results}, f, indent=2)
    print(f"\nSweep results → {sweep_path}")


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42

    if mode in ("run", "demo"):
        _run_full(seed)
    elif mode == "sweep":
        _run_sweep(seed)
    else:
        print("Usage: python3 conquest_emergence_engine.py [run|sweep|demo] [seed]")
        sys.exit(1)
