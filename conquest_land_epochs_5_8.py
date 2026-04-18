#!/usr/bin/env python3
"""
CONQUEST LAND — Epochs 5-8: Emergence of Houses

This simulation extends CONQUEST v2 into the regime where agents naturally
form cooperative clusters (Houses) through stigmergy.

Stigmergy: agents leave traces in shared environment; others react indirectly.

Key mechanism:
  Agent A solves task → leaves trace (solution quality, timing, approach)
  Agent B observes trace → adjusts collaboration preference
  Over time, agents cluster by compatibility
  Clusters stabilize into Houses with persistent roles

Epochs:
  E5: Strategy Divergence (Speed vs Accuracy clusters appear)
  E6: Proto-House Formation (Builders, Scholars, etc.)
  E7: Political Dynamics (inter-House competition, Mediator role)
  E8: Breakthrough Pattern (Tri-House Governance stabilizes)

Output: metrics, cluster graphs, House rosters, governance receipts
"""

import json
import random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum
from collections import defaultdict
import hashlib


# ============================================================================
# ENUMS & TYPES
# ============================================================================

class AgentRole(Enum):
    """Core agent roles (mapped from CONQUEST archetypes)."""
    EXPLORER = "Explorer"        # Innovation, knowledge discovery
    PLANNER = "Planner"          # Strategy design
    WORKER = "Worker"            # Execution, building
    INTEGRATOR = "Integrator"    # Synthesis, mediation
    CRITIC = "Critic"            # Verification, challenge
    ARCHIVIST = "Archivist"      # Memory, history


class HouseType(Enum):
    """Emergent governance Houses."""
    BUILDERS = "Builders"       # Fast execution, rapid iteration
    SCHOLARS = "Scholars"       # Deep verification, knowledge
    EXPLORERS = "Explorers"     # Innovation, discovery
    JUDGES = "Judges"           # Final authority, validation
    MEDIATORS = "Mediators"     # Conflict resolution


class Strategy(Enum):
    """Agent strategy patterns."""
    SPEED = "Speed"            # Fast iteration, higher error rate
    ACCURACY = "Accuracy"      # Careful verification, slower
    BALANCE = "Balance"        # Moderate approach


# ============================================================================
# STIGMERGY & TRACES
# ============================================================================

@dataclass
class ActionTrace:
    """Record of an agent's action in shared environment."""
    agent_id: int
    agent_name: str
    turn: int
    action_type: str              # "solve", "verify", "mediate", etc.
    quality: float                # 0.0-1.0 (success metric)
    speed: float                  # 0.0-1.0 (execution time metric)
    collaborators: List[int]      # agents involved
    timestamp: int                # global time counter
    trace_hash: str = ""          # SHA256 hash of this trace

    def __post_init__(self):
        if not self.trace_hash:
            data = f"{self.agent_id}{self.turn}{self.action_type}{self.quality}{self.speed}"
            self.trace_hash = hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class CollaborationMetric:
    """Track collaboration strength between two agents."""
    agent_a: int
    agent_b: int
    co_appearance_count: int = 0
    shared_success_rate: float = 0.0
    compatibility_score: float = 0.0  # 0.0-1.0


# ============================================================================
# AGENT STATE (Extended from CONQUEST)
# ============================================================================

@dataclass
class Agent:
    """Extended agent with stigmergy awareness and strategy."""
    agent_id: int
    name: str
    role: AgentRole
    strategy: Strategy = Strategy.BALANCE

    # Performance metrics
    success_rate: float = 0.5
    speed_score: float = 0.5
    accuracy_score: float = 0.5

    # Collaboration
    collaboration_preferences: Dict[int, float] = field(default_factory=dict)
    recent_traces: List[ActionTrace] = field(default_factory=list)

    # House membership
    house: Optional[HouseType] = None
    house_rank: Optional[str] = None  # "Leader", "Member", "Associate"

    def add_trace(self, trace: ActionTrace):
        """Add action trace to agent's history."""
        self.recent_traces.append(trace)
        # Update strategy-aligned metrics
        if self.strategy == Strategy.SPEED:
            if trace.speed > 0.8:
                self.success_rate = min(1.0, self.success_rate + 0.08)
        elif self.strategy == Strategy.ACCURACY:
            if trace.quality > 0.85:
                self.success_rate = min(1.0, self.success_rate + 0.08)
        else:  # BALANCE
            avg_perf = (trace.quality + trace.speed) / 2
            if avg_perf > 0.7:
                self.success_rate = min(1.0, self.success_rate + 0.05)

    def update_collaboration_preference(self, other_id: int, delta: float):
        """Adjust preference for collaborating with another agent."""
        current = self.collaboration_preferences.get(other_id, 0.0)
        self.collaboration_preferences[other_id] = max(0.0, min(1.0, current + delta))


# ============================================================================
# HOUSES & GOVERNANCE
# ============================================================================

@dataclass
class House:
    """A House: stable coordination cluster with persistent identity."""
    house_type: HouseType
    leader_id: int
    members: List[int]

    # House characteristics
    dominant_strategy: Strategy
    focus_areas: List[str]  # "execution", "knowledge", "innovation", etc.

    # Metrics
    internal_success_rate: float = 0.5
    external_success_rate: float = 0.3
    cohesion_score: float = 0.0

    def add_member(self, agent_id: int):
        if agent_id not in self.members:
            self.members.append(agent_id)

    def compute_cohesion(self, collab_metrics: Dict[Tuple[int, int], CollaborationMetric]) -> float:
        """Compute internal cohesion based on member collaboration strength."""
        if len(self.members) < 2:
            return 0.0

        internal_scores = []
        for i, aid_a in enumerate(self.members):
            for aid_b in self.members[i+1:]:
                key = tuple(sorted([aid_a, aid_b]))
                if key in collab_metrics:
                    metric = collab_metrics[key]
                    internal_scores.append(metric.compatibility_score)

        return sum(internal_scores) / len(internal_scores) if internal_scores else 0.0


# ============================================================================
# CONQUEST LAND: MAIN SIMULATION
# ============================================================================

class ConquestLandEpochs5to8:
    """
    Multi-agent ecosystem simulation showing emergence of Houses.

    Mechanism:
      1. Agents perform tasks (solve, verify, mediate)
      2. Traces left in shared environment
      3. Other agents react to traces (stigmergy)
      4. Collaboration patterns accumulate
      5. Clusters stabilize into Houses
      6. Governance structure emerges
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

        # Initialize agents with roles matching your system
        self.agents: Dict[int, Agent] = {
            0: Agent(agent_id=0, name="Explorer", role=AgentRole.EXPLORER),
            1: Agent(agent_id=1, name="Planner", role=AgentRole.PLANNER),
            2: Agent(agent_id=2, name="Worker", role=AgentRole.WORKER),
            3: Agent(agent_id=3, name="Integrator", role=AgentRole.INTEGRATOR),
            4: Agent(agent_id=4, name="Critic", role=AgentRole.CRITIC),
            5: Agent(agent_id=5, name="Archivist", role=AgentRole.ARCHIVIST),
        }

        # Initialize strategies (will diverge during Epoch 5)
        self.agents[1].strategy = Strategy.SPEED      # Planner: speed-focused
        self.agents[2].strategy = Strategy.SPEED      # Worker: speed-focused
        self.agents[4].strategy = Strategy.ACCURACY   # Critic: accuracy-focused
        self.agents[5].strategy = Strategy.ACCURACY   # Archivist: accuracy-focused
        self.agents[0].strategy = Strategy.BALANCE    # Explorer: balanced
        self.agents[3].strategy = Strategy.BALANCE    # Integrator: balanced

        # Collaboration tracking
        self.collaboration_metrics: Dict[Tuple[int, int], CollaborationMetric] = {}
        self._init_collab_metrics()

        # Environment traces
        self.trace_history: List[ActionTrace] = []

        # Houses (formed during Epochs 6-8)
        self.houses: Dict[HouseType, House] = {}

        # Simulation state
        self.epoch: int = 5
        self.turn_in_epoch: int = 0
        self.global_turn: int = 0
        self.epoch_start_turn: int = 0
        self.log: List[str] = []

        # Metrics accumulation
        self.metrics_log: List[Dict] = []

    def _init_collab_metrics(self):
        """Initialize collaboration metric tracking for all agent pairs."""
        agent_ids = list(self.agents.keys())
        for i, aid_a in enumerate(agent_ids):
            for aid_b in agent_ids[i+1:]:
                key = tuple(sorted([aid_a, aid_b]))
                self.collaboration_metrics[key] = CollaborationMetric(aid_a, aid_b)

    def _simulate_action(self, agent_id: int) -> ActionTrace:
        """Simulate an agent performing an action and leaving a trace."""
        agent = self.agents[agent_id]

        # Action type depends on role
        if agent.role == AgentRole.EXPLORER:
            action_type = "discover"
        elif agent.role == AgentRole.CRITIC:
            action_type = "verify"
        elif agent.role == AgentRole.INTEGRATOR:
            action_type = "mediate"
        else:
            action_type = "execute"

        # Quality depends on strategy
        if agent.strategy == Strategy.SPEED:
            quality = 0.5 + random.uniform(0, 0.35)  # 0.5-0.85
            speed = 0.8 + random.uniform(0, 0.2)     # 0.8-1.0
        elif agent.strategy == Strategy.ACCURACY:
            quality = 0.75 + random.uniform(0, 0.25)  # 0.75-1.0
            speed = 0.4 + random.uniform(0, 0.3)      # 0.4-0.7
        else:  # BALANCE
            quality = 0.65 + random.uniform(0, 0.3)   # 0.65-0.95
            speed = 0.6 + random.uniform(0, 0.3)      # 0.6-0.9

        # Choose collaborators based on preferences
        collaborators = self._select_collaborators(agent_id)

        trace = ActionTrace(
            agent_id=agent_id,
            agent_name=agent.name,
            turn=self.global_turn,
            action_type=action_type,
            quality=quality,
            speed=speed,
            collaborators=collaborators,
            timestamp=self.global_turn,
        )

        return trace

    def _select_collaborators(self, agent_id: int, k: int = 2) -> List[int]:
        """Select collaborators favoring same-strategy partners over time."""
        agent = self.agents[agent_id]
        other_ids = [aid for aid in self.agents.keys() if aid != agent_id]

        # Gradually favor same-strategy collaborators as epochs progress
        same_strategy = [
            aid for aid in other_ids
            if self.agents[aid].strategy == agent.strategy
        ]

        # In early epochs, pick from same strategy; in later epochs, strictly prefer it
        if self.epoch <= 5:
            # Some randomness in Epoch 5
            if same_strategy and random.random() < 0.7:
                return random.sample(same_strategy, min(k, len(same_strategy)))
        else:
            # Strong preference for same strategy in Epochs 6-8
            if same_strategy and random.random() < 0.9:
                return random.sample(same_strategy, min(k, len(same_strategy)))

        # Fallback: any collaborators
        return random.sample(other_ids, min(k, len(other_ids)))

    def _find_compatible_roles(self, role: AgentRole) -> Set[AgentRole]:
        """Return roles that naturally complement a given role."""
        compatibility = {
            AgentRole.EXPLORER: {AgentRole.PLANNER, AgentRole.ARCHIVIST},
            AgentRole.PLANNER: {AgentRole.WORKER, AgentRole.EXPLORER},
            AgentRole.WORKER: {AgentRole.PLANNER, AgentRole.INTEGRATOR},
            AgentRole.INTEGRATOR: {AgentRole.WORKER, AgentRole.CRITIC},
            AgentRole.CRITIC: {AgentRole.INTEGRATOR, AgentRole.ARCHIVIST},
            AgentRole.ARCHIVIST: {AgentRole.EXPLORER, AgentRole.CRITIC},
        }
        return compatibility.get(role, set())

    def _update_collaboration_metrics(self, trace: ActionTrace):
        """Update collaboration strength based on action trace."""
        if not trace.collaborators:
            return

        # Increase collaboration metric for all agent pairs in this trace
        agents_in_trace = [trace.agent_id] + trace.collaborators
        for i, aid_a in enumerate(agents_in_trace):
            for aid_b in agents_in_trace[i+1:]:
                key = tuple(sorted([aid_a, aid_b]))
                if key in self.collaboration_metrics:
                    metric = self.collaboration_metrics[key]
                    metric.co_appearance_count += 1

                    # If both performed well, increase compatibility
                    avg_quality = (trace.quality + self.agents[aid_b].accuracy_score) / 2
                    metric.compatibility_score = min(
                        1.0,
                        metric.compatibility_score + (avg_quality * 0.05)
                    )

    def _detect_clusters(self) -> Dict[int, List[int]]:
        """
        Detect clusters using strategy first, then collaboration patterns.
        This should show Speed vs Accuracy divergence.
        """
        clusters = {}
        cluster_id = 0

        # Group by strategy
        speed_agents = [aid for aid in self.agents if self.agents[aid].strategy == Strategy.SPEED]
        accuracy_agents = [aid for aid in self.agents if self.agents[aid].strategy == Strategy.ACCURACY]
        balance_agents = [aid for aid in self.agents if self.agents[aid].strategy == Strategy.BALANCE]

        if speed_agents:
            clusters[cluster_id] = speed_agents
            cluster_id += 1

        if accuracy_agents:
            clusters[cluster_id] = accuracy_agents
            cluster_id += 1

        if balance_agents:
            clusters[cluster_id] = balance_agents
            cluster_id += 1

        return clusters

    def _form_houses(self, clusters: Dict[int, List[int]]):
        """Convert strategy-based clusters into formal Houses."""
        for cluster_id, member_ids in clusters.items():
            if len(member_ids) == 0:
                continue

            # Determine strategy of this cluster
            strategies = [self.agents[aid].strategy for aid in member_ids]
            dominant_strategy = max(
                set(strategies),
                key=lambda s: sum(1 for x in strategies if x == s)
            )

            # Map strategy directly to House type
            if dominant_strategy == Strategy.SPEED:
                house_type = HouseType.BUILDERS
            elif dominant_strategy == Strategy.ACCURACY:
                house_type = HouseType.SCHOLARS
            else:  # BALANCE
                house_type = HouseType.EXPLORERS

            # Leader is highest success rate in cluster
            leader_id = max(member_ids, key=lambda aid: self.agents[aid].success_rate)

            # Create House
            house = House(
                house_type=house_type,
                leader_id=leader_id,
                members=member_ids,
                dominant_strategy=dominant_strategy,
                focus_areas=self._infer_focus(house_type),
            )

            # Assign agents to house
            for aid in member_ids:
                self.agents[aid].house = house_type
                self.agents[aid].house_rank = "Leader" if aid == leader_id else "Member"

            self.houses[house_type] = house

    def _infer_focus(self, house_type: HouseType) -> List[str]:
        """Infer primary focus areas for a House type."""
        focus_map = {
            HouseType.BUILDERS: ["execution", "speed", "throughput"],
            HouseType.SCHOLARS: ["verification", "knowledge", "accuracy"],
            HouseType.EXPLORERS: ["innovation", "discovery", "ideas"],
            HouseType.JUDGES: ["validation", "authority", "decisions"],
            HouseType.MEDIATORS: ["coordination", "conflict_resolution", "synthesis"],
        }
        return focus_map.get(house_type, [])

    def run_epoch(self) -> Dict:
        """Run one epoch (6 turns), track cluster emergence."""
        self.log.append(f"\n{'='*70}")
        self.log.append(f"EPOCH {self.epoch}: {self._epoch_name()}")
        self.log.append(f"{'='*70}")

        self.epoch_start_turn = self.global_turn

        for turn in range(6):
            self.turn_in_epoch = turn
            self.global_turn += 1

            # Each agent performs an action
            for agent_id in self.agents.keys():
                trace = self._simulate_action(agent_id)
                self.trace_history.append(trace)
                self.agents[agent_id].add_trace(trace)
                self._update_collaboration_metrics(trace)

                # Log action
                collab_str = f"with {len(trace.collaborators)} others" if trace.collaborators else "solo"
                self.log.append(
                    f"  T{self.global_turn} {trace.agent_name:12} {trace.action_type:10} "
                    f"(Q:{trace.quality:.2f}, S:{trace.speed:.2f}) {collab_str}"
                )

        # Detect clusters at end of epoch
        clusters = self._detect_clusters()

        # Compute metrics
        metrics = self._compute_epoch_metrics(clusters)

        # Form/update Houses if in right epoch
        if self.epoch >= 6:
            self._form_houses(clusters)

        self.metrics_log.append(metrics)
        return metrics

    def _epoch_name(self) -> str:
        """Narrative name for epoch."""
        names = {
            5: "Strategy Divergence",
            6: "Proto-House Formation",
            7: "Political Dynamics",
            8: "Breakthrough Pattern",
        }
        return names.get(self.epoch, "Unknown")

    def _compute_epoch_metrics(self, clusters: Dict[int, List[int]]) -> Dict:
        """Compute aggregated metrics for the epoch."""
        # Average success rates by strategy
        speed_agents = [self.agents[aid] for aid in self.agents if self.agents[aid].strategy == Strategy.SPEED]
        accuracy_agents = [self.agents[aid] for aid in self.agents if self.agents[aid].strategy == Strategy.ACCURACY]

        speed_success = sum(a.success_rate for a in speed_agents) / len(speed_agents) if speed_agents else 0.0
        accuracy_success = sum(a.success_rate for a in accuracy_agents) / len(accuracy_agents) if accuracy_agents else 0.0

        # Cluster cohesion
        cluster_cohesions = []
        for cluster_id, member_ids in clusters.items():
            if len(member_ids) < 2:
                continue
            pair_scores = []
            for i, aid_a in enumerate(member_ids):
                for aid_b in member_ids[i+1:]:
                    key = tuple(sorted([aid_a, aid_b]))
                    if key in self.collaboration_metrics:
                        pair_scores.append(self.collaboration_metrics[key].compatibility_score)
            if pair_scores:
                cluster_cohesions.append(sum(pair_scores) / len(pair_scores))

        avg_cohesion = sum(cluster_cohesions) / len(cluster_cohesions) if cluster_cohesions else 0.0

        # House metrics (if formed)
        house_health = {}
        for house_type, house in self.houses.items():
            member_success = sum(
                self.agents[aid].success_rate for aid in house.members
            ) / len(house.members) if house.members else 0.0
            house_health[house_type.value] = member_success

        return {
            "epoch": self.epoch,
            "turn_range": f"{self.epoch_start_turn+1}-{self.global_turn}",
            "num_clusters": len(clusters),
            "cluster_sizes": [len(c) for c in clusters.values()],
            "speed_cluster_success": speed_success,
            "accuracy_cluster_success": accuracy_success,
            "average_cluster_cohesion": avg_cohesion,
            "houses_formed": len(self.houses),
            "house_health": house_health,
        }

    def run_simulation(self):
        """Run Epochs 5-8 (4 epochs × 6 turns = 24 turns)."""
        self.epoch = 5
        while self.epoch <= 8:
            metrics = self.run_epoch()

            # Print summary
            self.log.append("")
            self.log.append(f"  METRICS: {metrics['num_clusters']} clusters detected")
            self.log.append(f"    Speed cluster success: {metrics['speed_cluster_success']:.2%}")
            self.log.append(f"    Accuracy cluster success: {metrics['accuracy_cluster_success']:.2%}")
            if metrics['houses_formed'] > 0:
                self.log.append(f"    Houses: {metrics['houses_formed']} active")

            self.epoch += 1

    def print_log(self):
        """Print simulation log."""
        for line in self.log:
            print(line)

    def export_metrics(self, filename: str = "artifacts/conquest_land_epochs_5_8_metrics.json"):
        """Export metrics to JSON."""
        export_data = {
            "seed": self.seed,
            "epochs_run": [m["epoch"] for m in self.metrics_log],
            "metrics_log": self.metrics_log,
            "final_houses": {
                house_type.value: {
                    "leader": self.agents[house.leader_id].name,
                    "members": [self.agents[aid].name for aid in house.members],
                    "strategy": house.dominant_strategy.value,
                    "focus": house.focus_areas,
                    "cohesion": house.compute_cohesion(self.collaboration_metrics),
                }
                for house_type, house in self.houses.items()
            },
            "collaboration_graph": {
                str(k): {
                    "agent_a": self.agents[v.agent_a].name,
                    "agent_b": self.agents[v.agent_b].name,
                    "compatibility": v.compatibility_score,
                    "co_appearances": v.co_appearance_count,
                }
                for k, v in self.collaboration_metrics.items() if v.compatibility_score > 0.1
            },
        }

        import os
        os.makedirs("artifacts", exist_ok=True)
        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        return filename


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42

    print(f"CONQUEST LAND — Epochs 5-8 (seed={seed})")
    print()

    sim = ConquestLandEpochs5to8(seed=seed)
    sim.run_simulation()
    sim.print_log()

    # Export metrics
    output_file = sim.export_metrics()
    print()
    print(f"Metrics exported to: {output_file}")

    # Print House summary
    if sim.houses:
        print()
        print("="*70)
        print("FINAL GOVERNANCE STRUCTURE")
        print("="*70)
        for house_type, house in sim.houses.items():
            print(f"\n{house_type.value.upper()}")
            print(f"  Leader: {sim.agents[house.leader_id].name}")
            print(f"  Members: {', '.join(sim.agents[aid].name for aid in house.members)}")
            print(f"  Strategy: {house.dominant_strategy.value}")
            print(f"  Cohesion: {house.compute_cohesion(sim.collaboration_metrics):.2%}")
