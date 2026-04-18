#!/usr/bin/env python3
"""
CONQUEST — Emoji Terrarium + Kaomoji Avatar Engine v1.0
Combines 3-agent EMOWUL emotional simulation with deterministic kaomoji avatars.
"""

import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum

# ============================================================================
# KAOMOJI AVATAR ENGINE (DETERMINISTIC)
# ============================================================================

EMOTIONS = ["JOY", "LOVE", "EXCITED", "SHY", "HUG", "TASTY", 
            "MISCHIEVOUS", "FIGHT", "SAD", "PANIC", "NEUTRAL", "ANIMALS"]

FACE_POOLS = {
    "JOY": ["(๑>ᴗ<๑)", "(≧◡≦)", "(✿◕‿◕)"],
    "LOVE": ["(｡♥‿♥｡)", "(•ө•)♡"],
    "EXCITED": ["(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧", "(╯✧▽✧)╯", "(๑˃̵ᴗ˂̵)و", "(つ≧▽≦)つ"],
    "SHY": ["(⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)", "(｡•́‿•̀｡)"],
    "HUG": ["(づ｡◕‿‿◕｡)づ", "(っ^_^)っ", "(っ´▽`)っ"],
    "TASTY": ["(っ˘ڡ˘ς)"],
    "MISCHIEVOUS": ["(｡•̀ᴗ-)✧", "(￢‿￢)"],
    "FIGHT": ["(ง'̀-'́)ง"],
    "SAD": ["(｡•́︿•̀｡)", "(；ω；)", "(╥﹏╥)", "(；´Д｀)"],
    "PANIC": ["(；´Д｀)", "(╥﹏╥)"],
    "NEUTRAL": ["(￣▽￣)ノ"],
    "ANIMALS": ["ʕ•ᴥ•ʔ", "ʕっ•ᴥ•ʔっ", "(=^･ω･^=)", "(=^･ｪ･^=)", "(ᵔᴥᵔ)", "(•ㅅ•)", "( ͡° ᴥ ͡°)"]
}

EMOTION_COLORS = {
    "JOY": (255, 211, 78),
    "LOVE": (255, 77, 141),
    "EXCITED": (168, 85, 247),
    "SHY": (249, 168, 212),
    "HUG": (96, 165, 250),
    "TASTY": (52, 211, 153),
    "MISCHIEVOUS": (249, 115, 22),
    "FIGHT": (239, 68, 68),
    "SAD": (59, 130, 246),
    "PANIC": (244, 63, 94),
    "NEUTRAL": (163, 163, 163),
    "ANIMALS": (34, 197, 94)
}

OVERLAY_SETS = {
    "JOY": ["✧", "✦", "✪"],
    "LOVE": ["🌹", "✧", "✦"],
    "EXCITED": ["🌀", "✧", "✪"],
    "SHY": ["✧", "🌹", "🜄"],
    "HUG": ["✧", "🜄", "🗝"],
    "TASTY": ["🜃", "✧", "🌹"],
    "MISCHIEVOUS": ["🌀", "✧", "⸸"],
    "FIGHT": ["✝️", "🜂", "💀"],
    "SAD": ["🜄", "⚰️", "✧"],
    "PANIC": ["🌀", "💀", "🜂"],
    "NEUTRAL": ["🜃", "⸸", "✧"],
    "ANIMALS": ["🌹", "🜁", "✧"]
}

def fnv1a_64(key: str) -> int:
    """FNV-1a 64-bit hash."""
    offset_basis = 0xcbf29ce484222325
    fnv_prime = 0x100000001b3
    hash_value = offset_basis
    
    for byte in key.encode('utf-8'):
        hash_value ^= byte
        hash_value = (hash_value * fnv_prime) & 0xffffffffffffffff
    
    return hash_value

def generate_avatar(seed: int, tick: int, agent_id: str) -> Dict:
    """Generate deterministic kaomoji avatar."""
    key = f"CONQUEST|AVATAR|v1|{seed}|{tick}|{agent_id}"
    hash_val = fnv1a_64(key)
    
    emo_idx = hash_val % len(EMOTIONS)
    emotion = EMOTIONS[emo_idx]
    
    face_pool = FACE_POOLS[emotion]
    face_idx = (hash_val >> 8) % len(face_pool)
    face = face_pool[face_idx]
    
    overlay_set = OVERLAY_SETS[emotion]
    o1 = overlay_set[(hash_val >> 16) % len(overlay_set)]
    o2_idx = (hash_val >> 24) % len(overlay_set)
    o2 = overlay_set[(o2_idx + 1) % len(overlay_set) if o2_idx == (hash_val >> 16) % len(overlay_set) else o2_idx]
    o3_idx = (hash_val >> 32) % len(overlay_set)
    while overlay_set[o3_idx] in [o1, o2]:
        o3_idx = (o3_idx + 1) % len(overlay_set)
    o3 = overlay_set[o3_idx]
    
    color_rgb = EMOTION_COLORS[emotion]
    color_hex = f"#{color_rgb[0]:02X}{color_rgb[1]:02X}{color_rgb[2]:02X}"
    
    return {
        "emotion": emotion,
        "face": face,
        "color_rgb": color_rgb,
        "color_hex": color_hex,
        "overlays": [o1, o2, o3]
    }

def render_kaomoji(avatar: Dict, agent_id: str) -> str:
    """Render kaomoji avatar with truecolor."""
    r, g, b = avatar["color_rgb"]
    face = avatar["face"]
    overlays = "".join(avatar["overlays"])
    emotion = avatar["emotion"]
    
    colored_face = f"\x1b[1m\x1b[38;2;{r};{g};{b}m{face}\x1b[0m"
    return f"{agent_id}  [{overlays}]  {colored_face}  {emotion}"

# ============================================================================
# EMOWUL EMOTION MODEL
# ============================================================================

@dataclass
class EMOWUL:
    """Pleasure-Arousal-Dominance emotional state."""
    valence: float = 0.5
    arousal: float = 0.5
    dominance: float = 0.5

    def apply_delta(self, dv: float, da: float, dd: float):
        self.valence = max(0.0, min(1.0, self.valence + dv))
        self.arousal = max(0.0, min(1.0, self.arousal + da))
        self.dominance = max(0.0, min(1.0, self.dominance + dd))

    def __str__(self) -> str:
        v_bar = "█" * int(self.valence * 5) + "░" * (5 - int(self.valence * 5))
        a_bar = "█" * int(self.arousal * 5) + "░" * (5 - int(self.arousal * 5))
        d_bar = "█" * int(self.dominance * 5) + "░" * (5 - int(self.dominance * 5))
        return f"V:{v_bar} A:{a_bar} D:{d_bar}"

# ============================================================================
# GAME STATE
# ============================================================================

@dataclass
class Tile:
    x: int
    y: int
    owner_id: Optional[int] = None
    fortress: bool = False

@dataclass
class Agent:
    agent_id: int
    name: str
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
        if event == "victory":
            self.emowul.apply_delta(+0.2, +0.1, +0.15)
        elif event == "defeat":
            self.emowul.apply_delta(-0.2, +0.1, -0.15)
        elif event == "expansion":
            self.emowul.apply_delta(+0.1, +0.1, +0.05)
        elif event == "fortify":
            self.emowul.apply_delta(+0.05, -0.1, +0.1)
        elif event == "threatened":
            self.emowul.apply_delta(-0.1, +0.2, -0.1)
        elif event == "rest":
            self.emowul.apply_delta(+0.05, -0.15, 0)

class EmojiKaomoji:
    """3×3 terrarium with EMOWUL + Kaomoji avatars."""

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

        self.seed = seed
        self.grid: List[List[Tile]] = self._init_grid()
        self.agents: List[Agent] = self._init_agents()
        self.turn: int = 0
        self.max_turns: int = 20
        self.log: List[str] = []

    def _init_grid(self) -> List[List[Tile]]:
        return [[Tile(x, y) for x in range(3)] for y in range(3)]

    def _init_agents(self) -> List[Agent]:
        agents = []
        agents.append(Agent(
            agent_id=0,
            name="SUNNY",
            emoji="😊",
            emowul=EMOWUL(valence=0.8, arousal=0.6, dominance=0.5)
        ))
        agents.append(Agent(
            agent_id=1,
            name="STORM",
            emoji="😠",
            emowul=EMOWUL(valence=0.3, arousal=0.8, dominance=0.7)
        ))
        agents.append(Agent(
            agent_id=2,
            name="PEACE",
            emoji="😌",
            emowul=EMOWUL(valence=0.6, arousal=0.3, dominance=0.4)
        ))

        starting_positions = [(0, 0), (2, 0), (1, 2)]
        for i, agent in enumerate(agents):
            x, y = starting_positions[i]
            self.grid[y][x].owner_id = i
            self.grid[y][x].fortress = True
            agent.tiles.append((x, y))

        return agents

    def get_adjacent_tiles(self, x: int, y: int) -> List[Tuple[int, int]]:
        adjacent = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 3 and 0 <= ny < 3:
                adjacent.append((nx, ny))
        return adjacent

    def get_agent_adjacent_unclaimed(self, agent: Agent) -> List[Tuple[int, int]]:
        adjacent = set()
        for x, y in agent.tiles:
            for nx, ny in self.get_adjacent_tiles(x, y):
                tile = self.grid[ny][nx]
                if tile.owner_id is None:
                    adjacent.add((nx, ny))
        return list(adjacent)

    def resolve_conflict(self, attacker: Agent, defender: Agent) -> bool:
        attacker_power = attacker.power + (attacker.emowul.dominance * 3)
        defender_defense = defender.stability + (1 - defender.emowul.arousal) * 2

        attacker_roll = attacker_power + random.randint(0, 2)
        defender_roll = defender_defense + random.randint(0, 2)

        return attacker_roll > defender_roll

    def agent_turn(self, agent: Agent):
        if not agent.is_alive():
            return

        # Simple AI
        if agent.agent_id == 0:  # SUNNY: expand
            self._expand_agent(agent)
        elif agent.agent_id == 1:  # STORM: seek conflict
            self._seek_conflict(agent)
        else:  # PEACE: fortify
            self._fortify_agent(agent)

    def _expand_agent(self, agent: Agent):
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
        if not agent.tiles:
            return

        x, y = random.choice(agent.tiles)
        agent.stability += 1
        self.log.append(f"  {agent.emoji} {agent.name} fortifies ({x},{y})")
        agent.update_mood_from_event("fortify")

    def _seek_conflict(self, agent: Agent):
        enemies = []
        for x, y in agent.tiles:
            for nx, ny in self.get_adjacent_tiles(x, y):
                tile = self.grid[ny][nx]
                if tile.owner_id is not None and tile.owner_id != agent.agent_id:
                    enemies.append(((nx, ny), tile.owner_id))

        if not enemies:
            self._expand_agent(agent)
            return

        (ex, ey), enemy_id = random.choice(enemies)
        enemy = self.agents[enemy_id]
        tile = self.grid[ey][ex]

        if self.resolve_conflict(agent, enemy):
            tile.owner_id = agent.agent_id
            tile.fortress = True
            agent.tiles.append((ex, ey))
            if (ex, ey) in enemy.tiles:
                enemy.tiles.remove((ex, ey))

            self.log.append(f"  ⚔️  {agent.emoji} {agent.name} defeats {enemy.emoji} {enemy.name} at ({ex},{ey})")
            agent.update_mood_from_event("victory")
            enemy.update_mood_from_event("defeat")
        else:
            self.log.append(f"  🛡️  {enemy.emoji} {enemy.name} repels {agent.emoji} {agent.name} at ({ex},{ey})")
            agent.update_mood_from_event("defeat")
            enemy.update_mood_from_event("victory")

    def simulate_turn(self):
        self.log.clear()
        self.log.append(f"\n--- TURN {self.turn} ---")

        for agent in self.agents:
            self.agent_turn(agent)

        for line in self.log:
            print(line)

        self.turn += 1

    def print_grid(self):
        print("\n" + "=" * 50)
        print(f"TURN {self.turn} | KAOMOJI AVATARS + EMOWUL")
        print("=" * 50)

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

    def print_agent_cards(self):
        """Print agent cards with kaomoji avatars."""
        print("\n" + "="*80)
        print("KAOMOJI AVATAR DISPLAY (Deterministic per turn)")
        print("="*80 + "\n")

        agent_ids = ["A", "B", "C"]
        for i, agent_id in enumerate(agent_ids):
            agent = self.agents[i]
            avatar = generate_avatar(self.seed, self.turn, agent_id)
            kaomoji_line = render_kaomoji(avatar, agent_id)
            
            status = "ALIVE" if agent.is_alive() else "DEAD"
            emowul_line = f"{agent.emoji} {agent.name:8s} | {agent.emowul} | Tiles:{agent.territory_count():2d} | {status}"
            
            print(kaomoji_line)
            print(emowul_line)
            print()

    def check_victory(self) -> Optional[Agent]:
        for agent in self.agents:
            if agent.territory_count() >= 5:
                return agent
        return None

    def run_simulation(self):
        print("\n" + "="*80)
        print("CONQUEST — Emoji Terrarium + Kaomoji Avatar Engine v1.0")
        print("="*80)

        while self.turn < self.max_turns:
            self.print_grid()
            self.print_agent_cards()
            self.simulate_turn()

            winner = self.check_victory()
            if winner:
                print(f"\n{'='*80}")
                print(f"VICTORY: {winner.emoji} {winner.name} controls {winner.territory_count()} tiles!")
                print(f"{'='*80}")
                return winner

        print(f"\n{'='*80}")
        print("SIMULATION COMPLETE (Turn 20)")
        print(f"{'='*80}\n")

        self.print_grid()
        self.print_agent_cards()

        winner = max(self.agents, key=lambda a: a.territory_count())
        print(f"\nWINNER BY TERRITORY: {winner.emoji} {winner.name} ({winner.territory_count()} tiles)")

        return winner


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys

    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 9137

    game = EmojiKaomoji(seed=seed)
    winner = game.run_simulation()

    print(f"\nFinal Report:")
    print(f"Winner: {winner.emoji} {winner.name}")
    print(f"Territory: {winner.territory_count()} tiles")
