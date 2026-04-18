#!/usr/bin/env python3
"""
CONQUEST v2.0 — HexaCycle Terrarium
A deterministic, turn-based territorial conquest simulation.

5 agents, 5×5 grid, 36 turns (6 epochs × 6 turns each).
Archetypes: WARLORD, ARCHITECT, DIPLOMAT, SEER, GUARDIAN
Domains: WAR, UNITY, TRADE, SCIENCE, DEFENSE
"""

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class Archetype(Enum):
    WARLORD = "WARLORD"
    ARCHITECT = "ARCHITECT"
    DIPLOMAT = "DIPLOMAT"
    SEER = "SEER"
    GUARDIAN = "GUARDIAN"

class Domain(Enum):
    WAR = "WAR"
    UNITY = "UNITY"
    TRADE = "TRADE"
    SCIENCE = "SCIENCE"
    DEFENSE = "DEFENSE"

class Epoch(Enum):
    GROUNDING = 0
    SEEING = 1
    STRUGGLE = 2
    ORDER = 3
    BONDING = 4
    SHEDDING = 5

# ============================================================================
# GAME STATE
# ============================================================================

@dataclass
class Tile:
    """A single tile on the 5×5 grid."""
    x: int
    y: int
    owner_id: Optional[int] = None
    fortress: bool = False
    defense: int = 0

@dataclass
class Agent:
    """An agent competing for territory."""
    agent_id: int
    name: str
    archetype: Archetype
    domain: Domain
    power: int = 5
    stability: int = 5
    tiles: List[Tuple[int, int]] = field(default_factory=list)

    def territory_count(self) -> int:
        return len(self.tiles)

    def is_alive(self) -> bool:
        return self.territory_count() > 0

class HexaCycleGame:
    """Main game engine."""

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

        self.grid: List[List[Tile]] = self._init_grid()
        self.agents: List[Agent] = self._init_agents()
        self.turn: int = 0
        self.total_turns: int = 36
        self.log: List[str] = []

    def _init_grid(self) -> List[List[Tile]]:
        """Create a 5×5 grid of empty tiles."""
        return [[Tile(x, y) for x in range(5)] for y in range(5)]

    def _init_agents(self) -> List[Agent]:
        """Create 5 agents with distinct archetypes and domains."""
        archetypes = [
            Archetype.WARLORD,
            Archetype.ARCHITECT,
            Archetype.DIPLOMAT,
            Archetype.SEER,
            Archetype.GUARDIAN,
        ]
        domains = [
            Domain.WAR,
            Domain.UNITY,
            Domain.TRADE,
            Domain.SCIENCE,
            Domain.DEFENSE,
        ]

        agents = []
        names = ["ALPHA", "BETA", "GAMMA", "DELTA", "EPSILON"]

        starting_positions = [
            (0, 0),
            (4, 0),
            (4, 4),
            (0, 4),
            (2, 2),
        ]

        for i in range(5):
            agent = Agent(
                agent_id=i,
                name=names[i],
                archetype=archetypes[i],
                domain=domains[i],
                power=5,
                stability=5,
            )

            x, y = starting_positions[i]
            self.grid[y][x].owner_id = i
            self.grid[y][x].fortress = True
            self.grid[y][x].defense = 2
            agent.tiles.append((x, y))

            agents.append(agent)

        return agents

    def current_epoch(self) -> Epoch:
        """Return current epoch (turn 0-5 = GROUNDING, 6-11 = SEEING, etc)."""
        epoch_index = (self.turn // 6) % 6
        return Epoch(epoch_index)

    def epoch_bonus(self, agent: Agent) -> Dict[str, int]:
        """Return power/stability bonuses based on epoch-archetype alignment."""
        epoch = self.current_epoch()
        bonuses = {"power": 0, "stability": 0}

        alignment_map = {
            (Archetype.WARLORD, Epoch.STRUGGLE): {"power": 2, "stability": -1},
            (Archetype.ARCHITECT, Epoch.ORDER): {"power": 0, "stability": 2},
            (Archetype.DIPLOMAT, Epoch.BONDING): {"power": 1, "stability": 1},
            (Archetype.SEER, Epoch.SEEING): {"power": 0, "stability": 2},
            (Archetype.GUARDIAN, Epoch.GROUNDING): {"power": 1, "stability": 2},
        }

        key = (agent.archetype, epoch)
        if key in alignment_map:
            aligned = alignment_map[key]
            bonuses["power"] += aligned.get("power", 0)
            bonuses["stability"] += aligned.get("stability", 0)

        if agent.domain == Domain.WAR and epoch == Epoch.STRUGGLE:
            bonuses["power"] += 1
        elif agent.domain == Domain.DEFENSE and epoch == Epoch.GROUNDING:
            bonuses["stability"] += 1
        elif agent.domain == Domain.SCIENCE and epoch == Epoch.SEEING:
            bonuses["power"] += 1

        return bonuses

    def get_adjacent_tiles(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Return list of adjacent tile coordinates (4-connected)."""
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 5 and 0 <= ny < 5:
                adjacent.append((nx, ny))
        return adjacent

    def get_agent_adjacent_tiles(self, agent: Agent) -> List[Tuple[int, int]]:
        """Return unclaimed tiles adjacent to agent's territory."""
        adjacent = set()
        for x, y in agent.tiles:
            for nx, ny in self.get_adjacent_tiles(x, y):
                tile = self.grid[ny][nx]
                if tile.owner_id is None:
                    adjacent.add((nx, ny))
        return list(adjacent)

    def resolve_conflict(self, attacker: Agent, defender: Agent, tile: Tile) -> bool:
        """Resolve a single conflict."""
        attacker_power = attacker.power + self.epoch_bonus(attacker)["power"]
        defender_stability = defender.stability + self.epoch_bonus(defender)["stability"]

        if tile.fortress:
            defender_stability += tile.defense

        attacker_roll = attacker_power + random.randint(0, 3)
        defender_roll = defender_stability + random.randint(0, 3)

        return attacker_roll > defender_roll

    def agent_turn(self, agent: Agent):
        """Execute one agent's turn."""
        if not agent.is_alive():
            return

        action = self._choose_action(agent)

        if action == "expand":
            self._expand_agent(agent)
        elif action == "fortify":
            self._fortify_agent(agent)

    def _choose_action(self, agent: Agent) -> str:
        """Decide whether agent should expand or fortify."""
        if agent.archetype in [Archetype.WARLORD, Archetype.DIPLOMAT]:
            if agent.power >= agent.stability:
                return "expand"

        if agent.archetype in [Archetype.ARCHITECT, Archetype.GUARDIAN]:
            if agent.stability < agent.power:
                return "fortify"

        available = self.get_agent_adjacent_tiles(agent)
        if available:
            return "expand"
        return "fortify"

    def _expand_agent(self, agent: Agent):
        """Attempt to expand into an adjacent unclaimed tile."""
        available = self.get_agent_adjacent_tiles(agent)
        if not available:
            return

        x, y = random.choice(available)
        tile = self.grid[y][x]

        tile.owner_id = agent.agent_id
        tile.fortress = True
        tile.defense = 1
        agent.tiles.append((x, y))

        self.log.append(f"  {agent.name} expands to ({x},{y})")

    def _fortify_agent(self, agent: Agent):
        """Increase defense on one of agent's tiles."""
        if not agent.tiles:
            return

        x, y = random.choice(agent.tiles)
        tile = self.grid[y][x]

        if tile.defense < 3:
            tile.defense += 1
            agent.stability += 1
            self.log.append(f"  {agent.name} fortifies ({x},{y}) [def={tile.defense}]")

    def simulate_conflicts(self):
        """Check for conflicts between adjacent agents."""
        agent_positions = {}
        for agent in self.agents:
            for x, y in agent.tiles:
                agent_positions[(x, y)] = agent.agent_id

        conflicts_resolved = set()

        for agent in self.agents:
            if not agent.is_alive():
                continue

            for x, y in agent.tiles:
                for nx, ny in self.get_adjacent_tiles(x, y):
                    if (nx, ny) in agent_positions:
                        defender_id = agent_positions[(nx, ny)]
                        if defender_id != agent.agent_id:
                            conflict_key = tuple(sorted([agent.agent_id, defender_id]))
                            if conflict_key not in conflicts_resolved:
                                self._resolve_adjacency_conflict(agent, self.agents[defender_id], x, y, nx, ny)
                                conflicts_resolved.add(conflict_key)

    def _resolve_adjacency_conflict(self, agent_a: Agent, agent_b: Agent, ax: int, ay: int, bx: int, by: int):
        """Resolve a conflict between two adjacent agents."""
        if random.random() > 0.2:
            return

        if random.random() < 0.5:
            attacker, defender = agent_a, agent_b
            tile_pos = (bx, by)
        else:
            attacker, defender = agent_b, agent_a
            tile_pos = (ax, ay)

        tile = self.grid[tile_pos[1]][tile_pos[0]]

        # Safety check: make sure tile is actually owned by defender
        if tile.owner_id != defender.agent_id:
            return

        if self.resolve_conflict(attacker, defender, tile):
            tile.owner_id = attacker.agent_id
            tile.fortress = True
            tile.defense = 1
            attacker.tiles.append(tile_pos)
            if tile_pos in defender.tiles:
                defender.tiles.remove(tile_pos)

            self.log.append(f"  CONFLICT: {attacker.name} seizes ({tile_pos[0]},{tile_pos[1]}) from {defender.name}")
        else:
            self.log.append(f"  CONFLICT: {defender.name} repels {attacker.name} at ({tile_pos[0]},{tile_pos[1]})")

    def apply_epoch_effects(self):
        """Apply epoch bonuses to all agents."""
        for agent in self.agents:
            bonuses = self.epoch_bonus(agent)
            agent.power += bonuses["power"]
            agent.stability += bonuses["stability"]

            agent.power = max(1, min(10, agent.power))
            agent.stability = max(1, min(10, agent.stability))

    def check_victory(self) -> Optional[Agent]:
        """Check if any agent has won."""
        for agent in self.agents:
            if agent.territory_count() >= 13:
                return agent
        return None

    def print_grid(self):
        """Print the current grid state."""
        agent_chars = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}

        print("\n" + "=" * 40)
        print(f"TURN {self.turn:2d} | EPOCH: {self.current_epoch().name:10s}")
        print("=" * 40)

        for y in range(5):
            row = ""
            for x in range(5):
                tile = self.grid[y][x]
                if tile.owner_id is not None:
                    char = agent_chars[tile.owner_id]
                    if tile.fortress:
                        row += f"[{char}]"
                    else:
                        row += f" {char} "
                else:
                    row += " . "
            print(row)

        print()

    def print_agent_stats(self):
        """Print current stats for all agents."""
        for agent in self.agents:
            status = "ALIVE" if agent.is_alive() else "DEAD"
            print(f"{agent.name:8s} | {agent.archetype.value:9s} | {agent.domain.value:7s} | "
                  f"P:{agent.power:2d} S:{agent.stability:2d} | Tiles:{agent.territory_count():2d} | {status}")

    def run_turn(self):
        """Execute a single turn."""
        self.log.clear()

        self.log.append(f"\n--- TURN {self.turn} ({self.current_epoch().name}) ---")

        self.apply_epoch_effects()

        for agent in self.agents:
            self.agent_turn(agent)

        self.simulate_conflicts()

        for line in self.log:
            print(line)

        self.turn += 1

    def run_simulation(self):
        """Run the full 36-turn simulation."""
        print("\n" + "=" * 60)
        print("CONQUEST v2.0 — HexaCycle Terrarium")
        print("=" * 60)

        while self.turn < self.total_turns:
            self.print_grid()
            self.print_agent_stats()
            self.run_turn()

            winner = self.check_victory()
            if winner:
                print(f"\n{'='*60}")
                print(f"VICTORY: {winner.name} controls {winner.territory_count()} tiles!")
                print(f"{'='*60}")
                return winner

        print(f"\n{'='*60}")
        print("SIMULATION COMPLETE (Turn 36)")
        print(f"{'='*60}\n")

        self.print_grid()
        self.print_agent_stats()

        winner = max(self.agents, key=lambda a: a.territory_count())
        print(f"\nWINNER BY TERRITORY: {winner.name} ({winner.territory_count()} tiles)")
        return winner


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None

    game = HexaCycleGame(seed=seed)
    winner = game.run_simulation()

    print(f"\nFinal Stats:")
    print(f"Winner: {winner.name}")
    print(f"Archetype: {winner.archetype.value}")
    print(f"Domain: {winner.domain.value}")
    print(f"Territory: {winner.territory_count()} tiles")
