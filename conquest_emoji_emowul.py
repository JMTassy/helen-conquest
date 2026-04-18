#!/usr/bin/env python3
"""
CONQUEST — Emoji Terrarium with EMOWUL
A 3-agent territorial simulation with emoji avatars and emotional state tracking.

Agents:
- HAPPY (😊): Optimistic, spreads goodwill
- ANGRY (😠): Aggressive, territorial
- CALM (😌): Defensive, seeks stability

EMOWUL Model: Valence (happy←→sad), Arousal (excited←→sleepy), Dominance (control←→submission)
"""

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum

# ============================================================================
# EMOWUL EMOTION MODEL
# ============================================================================

@dataclass
class EMOWUL:
    """Emotional state using PAD model (Pleasure, Arousal, Dominance)"""
    valence: float = 0.5      # 0.0 (sad) to 1.0 (happy)
    arousal: float = 0.5      # 0.0 (sleepy) to 1.0 (excited)
    dominance: float = 0.5    # 0.0 (submissive) to 1.0 (dominant)

    def apply_delta(self, dv: float, da: float, dd: float):
        """Apply emotional change."""
        self.valence = max(0.0, min(1.0, self.valence + dv))
        self.arousal = max(0.0, min(1.0, self.arousal + da))
        self.dominance = max(0.0, min(1.0, self.dominance + dd))

    def get_mood_emoji(self) -> str:
        """Return emoji based on valence + arousal."""
        if self.valence > 0.6 and self.arousal > 0.5:
            return "😊"  # Happy & excited
        elif self.valence > 0.6 and self.arousal <= 0.5:
            return "😌"  # Happy & calm
        elif self.valence <= 0.4 and self.arousal > 0.6:
            return "😠"  # Sad/angry & excited
        elif self.valence <= 0.4:
            return "😢"  # Sad & calm
        else:
            return "😐"  # Neutral

    def get_mood_name(self) -> str:
        """Return mood description."""
        if self.valence > 0.6:
            if self.arousal > 0.6:
                return "EUPHORIC"
            else:
                return "CONTENT"
        elif self.valence < 0.4:
            if self.arousal > 0.6:
                return "FURIOUS"
            else:
                return "MELANCHOLY"
        else:
            return "NEUTRAL"

    def __str__(self) -> str:
        v_bar = "█" * int(self.valence * 5) + "░" * (5 - int(self.valence * 5))
        a_bar = "█" * int(self.arousal * 5) + "░" * (5 - int(self.arousal * 5))
        d_bar = "█" * int(self.dominance * 5) + "░" * (5 - int(self.dominance * 5))
        return f"V:{v_bar} A:{a_bar} D:{d_bar}"

# ============================================================================
# GAME STATE
# ============================================================================

class AgentType(Enum):
    HAPPY = "HAPPY"
    ANGRY = "ANGRY"
    CALM = "CALM"

@dataclass
class Tile:
    """A single tile on the 3×3 grid."""
    x: int
    y: int
    owner_id: Optional[int] = None
    fortress: bool = False

@dataclass
class Agent:
    """An agent with emotional state and territory."""
    agent_id: int
    name: str
    agent_type: AgentType
    emoji: str
    emowul: EMOWUL = field(default_factory=EMOWUL)
    power: int = 5
    stability: int = 5
    tiles: List[Tuple[int, int]] = field(default_factory=list)

    def territory_count(self) -> int:
        return len(self.tiles)

    def is_alive(self) -> bool:
        return self.territory_count() > 0

    def update_mood_from_event(self, event: str):
        """Update emotional state based on game events."""
        if event == "victory":
            self.emowul.apply_delta(+0.2, +0.1, +0.15)  # Happy, excited, dominant
        elif event == "defeat":
            self.emowul.apply_delta(-0.2, +0.1, -0.15)  # Sad, frustrated, submissive
        elif event == "expansion":
            self.emowul.apply_delta(+0.1, +0.1, +0.05)  # Slight happiness & arousal
        elif event == "fortify":
            self.emowul.apply_delta(+0.05, -0.1, +0.1)  # Calm & secure
        elif event == "threatened":
            self.emowul.apply_delta(-0.1, +0.2, -0.1)   # Anxious, aroused
        elif event == "rest":
            self.emowul.apply_delta(+0.05, -0.15, 0)    # Calming down

class EmojiTerrarium:
    """Simple 3×3 grid with 3 agents."""

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

        self.grid: List[List[Tile]] = self._init_grid()
        self.agents: List[Agent] = self._init_agents()
        self.turn: int = 0
        self.max_turns: int = 20
        self.log: List[str] = []

    def _init_grid(self) -> List[List[Tile]]:
        """Create a 3×3 grid."""
        return [[Tile(x, y) for x in range(3)] for y in range(3)]

    def _init_agents(self) -> List[Agent]:
        """Create 3 emotional agents."""
        agents = []

        # Agent 0: HAPPY (top-left)
        agents.append(Agent(
            agent_id=0,
            name="SUNNY",
            agent_type=AgentType.HAPPY,
            emoji="😊",
            emowul=EMOWUL(valence=0.8, arousal=0.6, dominance=0.5)
        ))

        # Agent 1: ANGRY (top-right)
        agents.append(Agent(
            agent_id=1,
            name="STORM",
            agent_type=AgentType.ANGRY,
            emoji="😠",
            emowul=EMOWUL(valence=0.3, arousal=0.8, dominance=0.7)
        ))

        # Agent 2: CALM (bottom)
        agents.append(Agent(
            agent_id=2,
            name="PEACE",
            agent_type=AgentType.CALM,
            emoji="😌",
            emowul=EMOWUL(valence=0.6, arousal=0.3, dominance=0.4)
        ))

        # Place agents on starting tiles
        starting_positions = [(0, 0), (2, 0), (1, 2)]
        for i, agent in enumerate(agents):
            x, y = starting_positions[i]
            self.grid[y][x].owner_id = i
            self.grid[y][x].fortress = True
            agent.tiles.append((x, y))

        return agents

    def current_turn(self) -> int:
        return self.turn

    def get_adjacent_tiles(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Return adjacent tile coordinates (4-connected)."""
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 3 and 0 <= ny < 3:
                adjacent.append((nx, ny))
        return adjacent

    def get_agent_adjacent_unclaimed(self, agent: Agent) -> List[Tuple[int, int]]:
        """Return unclaimed tiles adjacent to agent's territory."""
        adjacent = set()
        for x, y in agent.tiles:
            for nx, ny in self.get_adjacent_tiles(x, y):
                tile = self.grid[ny][nx]
                if tile.owner_id is None:
                    adjacent.add((nx, ny))
        return list(adjacent)

    def resolve_conflict(self, attacker: Agent, defender: Agent) -> bool:
        """Resolve conflict based on stats and emotional state."""
        # Attack power influenced by dominance
        attacker_power = attacker.power + (attacker.emowul.dominance * 3)
        # Defense influenced by emotional stability
        defender_defense = defender.stability + (1 - defender.emowul.arousal) * 2

        attacker_roll = attacker_power + random.randint(0, 2)
        defender_roll = defender_defense + random.randint(0, 2)

        return attacker_roll > defender_roll

    def agent_turn(self, agent: Agent):
        """Execute one agent's turn."""
        if not agent.is_alive():
            return

        # Decide action based on personality
        if agent.agent_type == AgentType.HAPPY:
            # HAPPY agents prefer expansion
            self._expand_agent(agent)
        elif agent.agent_type == AgentType.ANGRY:
            # ANGRY agents seek conflict
            self._seek_conflict(agent)
        else:  # CALM
            # CALM agents fortify
            self._fortify_agent(agent)

    def _expand_agent(self, agent: Agent):
        """Expand into adjacent unclaimed tile."""
        available = self.get_agent_adjacent_unclaimed(agent)
        if not available:
            agent.update_mood_from_event("rest")
            return

        x, y = random.choice(available)
        tile = self.grid[y][x]
        tile.owner_id = agent.agent_id
        tile.fortress = True
        agent.tiles.append((x, y))

        self.log.append(f"  {agent.emoji} {agent.name} expands to ({x},{y})")
        agent.update_mood_from_event("expansion")

    def _fortify_agent(self, agent: Agent):
        """Increase defense on owned tile."""
        if not agent.tiles:
            return

        x, y = random.choice(agent.tiles)
        agent.stability += 1
        self.log.append(f"  {agent.emoji} {agent.name} fortifies ({x},{y})")
        agent.update_mood_from_event("fortify")

    def _seek_conflict(self, agent: Agent):
        """Try to attack adjacent enemy tile."""
        # Find adjacent enemy tiles
        enemies = []
        for x, y in agent.tiles:
            for nx, ny in self.get_adjacent_tiles(x, y):
                tile = self.grid[ny][nx]
                if tile.owner_id is not None and tile.owner_id != agent.agent_id:
                    enemies.append(((nx, ny), tile.owner_id))

        if not enemies:
            # No enemies nearby, try to expand
            self._expand_agent(agent)
            return

        # Pick a random enemy tile to attack
        (ex, ey), enemy_id = random.choice(enemies)
        enemy = self.agents[enemy_id]
        tile = self.grid[ey][ex]

        if self.resolve_conflict(agent, enemy):
            # Attacker wins
            tile.owner_id = agent.agent_id
            tile.fortress = True
            agent.tiles.append((ex, ey))
            if (ex, ey) in enemy.tiles:
                enemy.tiles.remove((ex, ey))

            self.log.append(f"  ⚔️  {agent.emoji} {agent.name} defeats {enemy.emoji} {enemy.name} at ({ex},{ey})")
            agent.update_mood_from_event("victory")
            enemy.update_mood_from_event("defeat")
        else:
            # Defender wins
            self.log.append(f"  🛡️  {enemy.emoji} {enemy.name} repels {agent.emoji} {agent.name} at ({ex},{ey})")
            agent.update_mood_from_event("defeat")
            enemy.update_mood_from_event("victory")

    def simulate_turn(self):
        """Execute one full turn."""
        self.log.clear()
        self.log.append(f"\n--- TURN {self.turn} ---")

        # Each agent acts
        for agent in self.agents:
            self.agent_turn(agent)

        # Print results
        for line in self.log:
            print(line)

        self.turn += 1

    def print_grid(self):
        """Print current grid state."""
        print("\n" + "=" * 35)
        print(f"TURN {self.turn} | Status")
        print("=" * 35)

        agent_chars = {0: "😊", 1: "😠", 2: "😌"}

        for y in range(3):
            row = ""
            for x in range(3):
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
        """Print agent emotional states."""
        for agent in self.agents:
            status = "ALIVE" if agent.is_alive() else "DEAD"
            mood = agent.emowul.get_mood_emoji()
            mood_name = agent.emowul.get_mood_name()
            print(f"{agent.emoji} {agent.name:8s} | {mood} {mood_name:12s} | Tiles: {agent.territory_count()} | {agent.emowul} | {status}")

    def check_victory(self) -> Optional[Agent]:
        """Check if any agent won."""
        for agent in self.agents:
            if agent.territory_count() >= 5:  # Majority of 9 tiles
                return agent
        return None

    def run_simulation(self):
        """Run the full simulation."""
        print("\n" + "=" * 60)
        print("CONQUEST — Emoji Terrarium with EMOWUL")
        print("=" * 60)

        while self.turn < self.max_turns:
            self.print_grid()
            self.print_agent_stats()
            self.simulate_turn()

            winner = self.check_victory()
            if winner:
                print(f"\n{'='*60}")
                print(f"VICTORY: {winner.emoji} {winner.name} controls {winner.territory_count()} tiles!")
                print(f"{'='*60}")
                return winner

        print(f"\n{'='*60}")
        print("SIMULATION COMPLETE (Turn 20)")
        print(f"{'='*60}\n")

        self.print_grid()
        self.print_agent_stats()

        winner = max(self.agents, key=lambda a: a.territory_count())
        print(f"\nWINNER BY TERRITORY: {winner.emoji} {winner.name} ({winner.territory_count()} tiles)")
        print(f"Final Mood: {winner.emowul.get_mood_emoji()} {winner.emowul.get_mood_name()}")
        print(f"Emotional State:\n{winner.emowul}")

        return winner


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None

    game = EmojiTerrarium(seed=seed)
    winner = game.run_simulation()

    print(f"\nFinal Report:")
    print(f"Winner: {winner.emoji} {winner.name}")
    print(f"Type: {winner.agent_type.value}")
    print(f"Territory: {winner.territory_count()} tiles")
    print(f"Mood: {winner.emowul.get_mood_name()}")
