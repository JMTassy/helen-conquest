#!/usr/bin/env python3
"""
CONQUEST — Emulation Game  v0.1
================================
Tagline : Le savoir mène au pouvoir.
Genre   : territory-control + knowledge-to-power + autonomous castle builders

Architecture
------------
  GameState      — immutable snapshot per tick
  apply_actions  — pure reducer (state × actions → state)
  Agents         — pure functions (state → [Proposal])
  Renderer       — pure functions (state → str)
  CLI            — interactive loop (human approves proposals, advances turns)

Determinism contract
--------------------
  * Same seed  → identical run every time
  * All RNG through a single seeded Random instance stored in state
  * Every tick logs state-hash + chosen actions

Usage
-----
  python3 conquest_v1.py              # seed 111  (default)
  python3 conquest_v1.py 222          # seed 222
  python3 conquest_v1.py --replay 222 # replay in headless mode (30 turns)
  python3 conquest_v1.py --help       # show help
"""

import sys, random, hashlib, json, copy, os, textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional, Set

# ── optional colour ──────────────────────────────────────────────────────────
try:
    from colorama import Fore, Back, Style, init as _cinit
    _cinit(autoreset=True)
    USE_COLOR = True
except ImportError:
    USE_COLOR = False
    class _C:
        def __getattr__(self, _): return ""
    Fore = Back = Style = _C()

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

VERSION        = "0.1.0"
MAP_W          = 25          # columns
MAP_H          = 18          # rows
CASTLE_SIZE    = 5           # castle grid is 5×5

# Terrain ─ (glyph, base_capture_p_cost, k_yield, p_yield, m_yield, threat_spawn_weight)
TERRAIN = {
    "plain":    (".", 2, 0, 1, 1, 1),
    "forest":   ("*", 3, 1, 0, 2, 2),
    "mountain": ("^", 5, 0, 2, 1, 1),
    "water":    ("~", 9, 0, 0, 0, 0),   # nearly uncapturable MVP
    "ruins":    ("#", 4, 3, 1, 0, 4),
}

THREAT_ALPHA = 2   # power_cost += threat * THREAT_ALPHA when capturing

# Castle modules ─ (cost_k, cost_p, cost_m, build_ticks, effects_dict)
MODULE_DEFS: Dict[str, dict] = {
    "keep":        dict(k=0,  p=0,  m=0,  t=0,  eff={"P_tick":2},           desc="Central stronghold (pre-built)"),
    "wall":        dict(k=0,  p=2,  m=5,  t=2,  eff={"def":2},              desc="Defensive wall segment"),
    "gatehouse":   dict(k=2,  p=3,  m=6,  t=3,  eff={"def":3,"P_tick":1},   desc="Fortified entrance"),
    "barracks":    dict(k=3,  p=4,  m=5,  t=3,  eff={"P_tick":2,"def":1},   desc="Military quarters"),
    "library":     dict(k=5,  p=2,  m=4,  t=4,  eff={"K_tick":3},           desc="Knowledge repository"),
    "scriptorium": dict(k=8,  p=1,  m=3,  t=5,  eff={"K_tick":4},           desc="Advanced scholarship"),
    "forge":       dict(k=3,  p=2,  m=6,  t=4,  eff={"M_tick":3,"def":1},   desc="Weapons and tools"),
    "granary":     dict(k=2,  p=1,  m=4,  t=2,  eff={"stab":2},             desc="Food store, reduces famine"),
    "observatory": dict(k=10, p=3,  m=5,  t=6,  eff={"K_tick":5},           desc="Astronomical research"),
    "shrine":      dict(k=4,  p=2,  m=3,  t=3,  eff={"K_tick":2,"stab":1},  desc="Sacred site"),
}

# Tech tree ─ (cost_k, requires[], label)
TECH_TREE: Dict[str, dict] = {
    "writing":       dict(k=15, req=[],           lbl="Writing  → library efficiency +50%"),
    "fortification": dict(k=20, req=[],           lbl="Fortification → wall cost -25%"),
    "astronomy":     dict(k=30, req=["writing"],  lbl="Astronomy → observatory +100%"),
    "metallurgy":    dict(k=25, req=["writing"],  lbl="Metallurgy → forge +50%"),
    "logistics":     dict(k=20, req=[],           lbl="Logistics → capture cost -20%"),
}

# Victory conditions
VICTORY_DOMINION  = 0.55   # control ≥55% of non-water tiles
VICTORY_ASCENSION = 200    # reach K≥200 with observatory built
SURVIVAL_TURNS    = 50     # survive 50 turns under escalating raids

# ═══════════════════════════════════════════════════════════════════════════════
# 2.  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Tile:
    x: int; y: int
    terrain:   str   = "plain"
    owner:     str   = "neutral"   # neutral | player | enemy
    threat:    int   = 0
    fortified: bool  = False
    site:      str   = "none"      # none | ruin | mine | shrine | tower
    yield_k:   int   = 0
    yield_p:   int   = 0
    yield_m:   int   = 0


@dataclass
class CastleModule:
    mid:        str
    mtype:      str
    slot:       Tuple[int,int]
    built:      bool = False
    progress:   int  = 0
    total_time: int  = 0


@dataclass
class BuildQueueItem:
    mtype:   str
    slot:    Tuple[int,int]
    ticks:   int
    total:   int
    pid:     str = ""


@dataclass
class Proposal:
    pid:       str
    agent:     str           # LEGO1 role (PLANNER, ECONOMIST, etc.)
    ptype:     str           # build | capture | fortify | research | upgrade
    target:    Any
    cost_k:    int; cost_p: int; cost_m: int
    ticks:     int
    delta:     Dict[str,int]     # {"K":+2,"P":-1, ...}
    priority:  int               # 1..5
    tags:      List[str]         # rationale tags (no prose)
    superteam: str = ""     # PRODUCTION | DEFENSE | EXPANSION | SCIENCE
    district:  str = ""     # FOUNDRY | FRONTIER | SCIENCE | LEDGER
    status:    str = "pending"  # pending | approved | denied | executed


@dataclass
class Superteam:
    """LEGO2: Group of roles for a domain."""
    name:     str           # PRODUCTION | DEFENSE | EXPANSION | SCIENCE
    roles:    List[str]     # LEGO1 role names
    purpose:  str           # what this team does


@dataclass
class District:
    """LEGO3: Specialized superteams operating on a rhythm."""
    name:      str
    superteams: List[str]   # which teams are in this district
    rhythm:    int          # activate every N turns (1=every turn)
    boundary:  str          # kernel constraint description


@dataclass
class Event:
    turn: int; etype: str; desc: str; data: Dict = field(default_factory=dict)


@dataclass
class GameState:
    seed:         int
    turn:         int
    house:        str
    K: int; P: int; M: int             # resources
    tiles:        Dict[Tuple[int,int], Tile]
    castle:       List[CastleModule]
    build_queue:  List[BuildQueueItem]
    proposals:    List[Proposal]
    events:       List[Event]
    tech:         Set[str]
    objectives:   List[str]
    stability:    int
    defense:      int
    K_tick:       int
    P_tick:       int
    M_tick:       int
    rng:          random.Random
    turn_hashes:  List[str]
    # ── THREE HOUSES LAYER ─────────────────────────────────────
    agent_weights:  Dict[str, float] = field(default_factory=dict)  # per-House agent priority multipliers
    mist_pressure:  int = 0              # 0..10, escalates toward victory/loss
    opus_phase:     int = 1              # 1..7 (SEPTEM: alchemical progression)
    # ────────────────────────────────────────────────────────────
    game_over:    bool = False
    victory:      str  = ""
    pid_counter:  int  = 0

# ═══════════════════════════════════════════════════════════════════════════════
# 3.  MAP GENERATOR  (seeded, deterministic)
# ═══════════════════════════════════════════════════════════════════════════════

def _gen_map(rng: random.Random) -> Dict[Tuple[int,int], Tile]:
    tiles: Dict[Tuple[int,int], Tile] = {}

    # Base terrain via weighted noise
    terrain_pool = (
        ["plain"]*40 + ["forest"]*25 + ["mountain"]*15 + ["water"]*12 + ["ruins"]*8
    )

    # Build a simple blob map: cluster water/mountains
    for y in range(MAP_H):
        for x in range(MAP_W):
            t = rng.choice(terrain_pool)
            tile = Tile(x=x, y=y, terrain=t)
            props = TERRAIN[t]
            tile.yield_k = props[2]; tile.yield_p = props[3]; tile.yield_m = props[4]
            tiles[(x,y)] = tile

    # Place water clusters (rivers)
    for _ in range(3):
        cx, cy = rng.randint(2, MAP_W-3), rng.randint(2, MAP_H-3)
        for dx in range(-1, 3):
            for dy in range(-1, 2):
                if (cx+dx, cy+dy) in tiles:
                    tiles[(cx+dx,cy+dy)].terrain = "water"
                    tiles[(cx+dx,cy+dy)].yield_k = 0
                    tiles[(cx+dx,cy+dy)].yield_p = 0
                    tiles[(cx+dx,cy+dy)].yield_m = 0

    # Place mountain ranges
    for _ in range(2):
        cx, cy = rng.randint(5, MAP_W-6), rng.randint(3, MAP_H-4)
        for i in range(rng.randint(3,6)):
            mx = min(MAP_W-1, max(0, cx+i))
            tiles[(mx,cy)].terrain = "mountain"
            tiles[(mx,cy)].yield_p = 2; tiles[(mx,cy)].yield_m = 1

    # Sites
    site_pool = ["ruin","ruin","ruin","mine","mine","shrine","shrine","tower","observatory"]
    for _ in range(12):
        sx, sy = rng.randint(0,MAP_W-1), rng.randint(0,MAP_H-1)
        t = tiles[(sx,sy)]
        if t.terrain != "water" and t.site == "none":
            s = rng.choice(site_pool)
            t.site = s
            if s in ("ruin",):
                t.threat = rng.randint(2,4)
                t.yield_k += 2
            elif s == "mine":
                t.yield_m += 2
            elif s == "shrine":
                t.yield_k += 1; t.yield_p += 1
            elif s == "observatory":
                t.yield_k += 3

    # Player start: centre-left cluster, 3×3 around (4, MAP_H//2)
    px, py = 4, MAP_H//2
    for dy in range(-1,2):
        for dx in range(-1,2):
            pos = (px+dx, py+dy)
            if pos in tiles:
                tiles[pos].owner = "player"
                tiles[pos].terrain = "plain"
                tiles[pos].yield_k = 0; tiles[pos].yield_p = 1; tiles[pos].yield_m = 1
                tiles[pos].threat  = 0

    # Enemy start: centre-right cluster
    ex, ey = MAP_W-5, MAP_H//2
    for dy in range(-1,2):
        for dx in range(-1,2):
            pos = (ex+dx, ey+dy)
            if pos in tiles:
                tiles[pos].owner = "enemy"
                tiles[pos].threat = max(tiles[pos].threat, 2)

    return tiles


def _gen_castle(rng: random.Random) -> List[CastleModule]:
    """Start with a pre-built keep at (2,2) and empty slots."""
    keep = CastleModule(mid="keep_0", mtype="keep", slot=(2,2),
                        built=True, progress=0, total_time=0)
    return [keep]

# ═══════════════════════════════════════════════════════════════════════════════
# 4.  GAME STATE FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def new_game(seed: int, house: str = "AVALON") -> GameState:
    """Create a new game with a House choice (AVALON | CAMELOT | MORGANA).

    Normalizes house name and loads House-specific agent weights.
    """
    # Normalize house name (case-insensitive, full name)
    house_norm = house.upper() if house else "AVALON"
    if house_norm not in HOUSE_CONFIGS:
        house_norm = "AVALON"  # Default if invalid

    rng = random.Random(seed)
    tiles  = _gen_map(rng)
    castle = _gen_castle(rng)

    # Load House-specific agent weights
    house_cfg = HOUSE_CONFIGS[house_norm]
    agent_weights = house_cfg["agent_weights"]

    gs = GameState(
        seed=seed, turn=1, house=house_norm,
        K=20, P=15, M=20,
        tiles=tiles, castle=castle,
        build_queue=[], proposals=[], events=[],
        tech=set(), objectives=["Expand north", "Build a Library"],
        stability=5, defense=2,
        K_tick=0, P_tick=2, M_tick=0,
        rng=rng, turn_hashes=[],
        agent_weights=agent_weights,
        mist_pressure=0,
        opus_phase=1,
    )
    _recompute_ticks(gs)

    # Startup message with House lore
    sigil = house_cfg["sigil"]
    name = house_cfg["name"]
    desc = house_cfg["desc"]
    gs.events.append(Event(1,"start",f"{sigil} {name}: {desc}"))
    gs.events.append(Event(1,"start","Campaign begins. Le savoir mène au pouvoir."))

    return gs


def _recompute_ticks(gs: GameState) -> None:
    """Recompute per-tick yields from tiles + castle modules."""
    K = P = M = 0
    # Tiles
    for t in gs.tiles.values():
        if t.owner == "player":
            K += t.yield_k; P += t.yield_p; M += t.yield_m
    # Castle modules
    def_bonus = 0; stab_bonus = 0
    for m in gs.castle:
        if m.built:
            eff = MODULE_DEFS[m.mtype]["eff"]
            K += eff.get("K_tick",0); P += eff.get("P_tick",0)
            M += eff.get("M_tick",0); def_bonus += eff.get("def",0)
            stab_bonus += eff.get("stab",0)
    # Tech bonuses
    if "writing" in gs.tech:
        for m in gs.castle:
            if m.built and m.mtype in ("library","scriptorium"):
                K += MODULE_DEFS[m.mtype]["eff"].get("K_tick",0) // 2
    if "metallurgy" in gs.tech:
        for m in gs.castle:
            if m.built and m.mtype == "forge":
                M += MODULE_DEFS[m.mtype]["eff"].get("M_tick",0) // 2
    gs.K_tick = max(K,0); gs.P_tick = max(P,0); gs.M_tick = max(M,0)
    gs.defense = 2 + def_bonus; gs.stability = max(1, gs.stability + stab_bonus - gs.stability)

# ═══════════════════════════════════════════════════════════════════════════════
# 5.  REDUCER  — pure(ish) state transitions
# ═══════════════════════════════════════════════════════════════════════════════

def _state_hash(gs: GameState) -> str:
    blob = f"{gs.turn}|{gs.K}|{gs.P}|{gs.M}"
    for pos in sorted(gs.tiles):
        t = gs.tiles[pos]
        blob += f"|{pos[0]},{pos[1]}:{t.owner[0]}{t.threat}"
    return hashlib.md5(blob.encode()).hexdigest()[:12]


def collect_resources(gs: GameState) -> None:
    _recompute_ticks(gs)
    gs.K += gs.K_tick; gs.P += gs.P_tick; gs.M += gs.M_tick


def process_build_queue(gs: GameState) -> None:
    completed = []
    for item in gs.build_queue:
        item.ticks -= 1
        if item.ticks <= 0:
            # Instantiate the module
            mdef = MODULE_DEFS[item.mtype]
            mid  = f"{item.mtype}_{item.slot[0]}_{item.slot[1]}"
            cm = CastleModule(mid=mid, mtype=item.mtype, slot=item.slot,
                              built=True, total_time=mdef["t"])
            gs.castle.append(cm)
            completed.append(item)
            gs.events.append(Event(gs.turn,"build_complete",
                f"{item.mtype.capitalize()} at slot {item.slot} is complete!"))
    for c in completed:
        gs.build_queue.remove(c)


def process_threats(gs: GameState) -> None:
    """Escalating raids on high-threat frontier tiles."""
    rng = gs.rng
    total_threat = sum(t.threat for t in gs.tiles.values() if t.owner == "enemy")
    raid_chance  = min(0.05 * gs.turn // 5, 0.40)

    if rng.random() < raid_chance:
        # Find player border tiles
        border = [pos for pos, t in gs.tiles.items()
                  if t.owner == "player" and _adjacent_enemy(gs.tiles, pos)]
        if border:
            target = rng.choice(border)
            dmg = rng.randint(1,3)
            gs.P = max(0, gs.P - dmg)
            gs.events.append(Event(gs.turn,"raid",
                f"Enemy raid on {target}! Lost {dmg} Power.", {"tile":target,"dmg":dmg}))

    # Slow natural threat-spread
    for pos, t in gs.tiles.items():
        if t.owner == "enemy" and t.threat < 5:
            if rng.random() < 0.06:
                t.threat = min(5, t.threat+1)


def check_victory(gs: GameState) -> None:
    land = [t for t in gs.tiles.values() if t.terrain != "water"]
    owned = [t for t in land if t.owner == "player"]
    if len(owned)/len(land) >= VICTORY_DOMINION:
        gs.game_over = True; gs.victory = "DOMINION"
        gs.events.append(Event(gs.turn,"victory","DOMINION — You control the realm!"))
        return
    has_obs = any(m.built and m.mtype=="observatory" for m in gs.castle)
    if has_obs and gs.K >= VICTORY_ASCENSION:
        gs.game_over = True; gs.victory = "ASCENSION"
        gs.events.append(Event(gs.turn,"victory","ASCENSION — Your knowledge transcends conquest!"))
        return
    if gs.turn >= SURVIVAL_TURNS:
        gs.game_over = True; gs.victory = "SURVIVAL"
        gs.events.append(Event(gs.turn,"victory",f"SURVIVAL — You endured {SURVIVAL_TURNS} turns!"))


def advance_turn(gs: GameState) -> None:
    """Full tick: resources → build → threats → victory check → mist escalation → hash."""
    collect_resources(gs)
    process_build_queue(gs)
    process_threats(gs)

    # ── THREE HOUSES: Mist Escalation (LEGO3+ Narrative) ────────────────────
    # Escalate mist pressure: 0→1→...→10 (final reckoning at T30)
    gs.mist_pressure = min(10, gs.mist_pressure + 1)

    # Check for Mist events at T10, T20, T30
    for trigger_turn, event_name, event_desc in MIST_EVENTS:
        if gs.turn == trigger_turn:
            gs.events.append(Event(gs.turn, "mist_event", event_desc))
            # Advance Opus phase every Mist event (1→2→3)
            if gs.opus_phase < 7:
                gs.opus_phase += 1
            new_opus = OPUS_PHASES.get(gs.opus_phase, ("???", "?", "unknown"))
            gs.events.append(Event(gs.turn, "opus_phase",
                f"OPUS: {new_opus[0]} {new_opus[1]} — {new_opus[2]}"))

    # ────────────────────────────────────────────────────────────────────────

    check_victory(gs)
    h = _state_hash(gs)
    gs.turn_hashes.append(h)
    gs.turn += 1


# ═══════════════════════════════════════════════════════════════════════════════
# 5a.  KERNEL CONSTRAINT VALIDATION (LEGO4)
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_proposal_kernel(gs: GameState, p: Proposal) -> List[str]:
    """LEGO4: Soft constraint checks. Returns list of violations (if any).

    K1: Role Separation — LEGO1 boundaries
    K2: Superteam Authority — Proposer ≠ Validator
    K3: District Independence — No inter-district dependencies
    K4: Ledger Immutability — Write-once log
    K5: No Self-Modification — Agent cannot override decisions
    """
    violations = []

    # K1: Role Separation
    # Check that proposal agent matches expected role
    agent_role = p.agent
    if agent_role == "PLANNER" and p.ptype != "build":
        violations.append("K1_ROLE: PLANNER proposes non-build action")
    elif agent_role == "ECONOMIST" and p.ptype not in ("build", "research"):
        violations.append("K1_ROLE: ECONOMIST proposes capture or fortify")
    elif agent_role == "DEFENDER" and p.ptype not in ("fortify", "build"):
        violations.append("K1_ROLE: DEFENDER proposes capture or research")
    elif agent_role == "RESEARCHER" and p.ptype != "research":
        violations.append("K1_ROLE: RESEARCHER proposes non-research action")
    elif agent_role == "BUILDER" and p.ptype != "build":
        violations.append("K1_ROLE: BUILDER proposes non-build action")
    elif agent_role == "EXPLORER" and p.ptype != "capture":
        violations.append("K1_ROLE: EXPLORER proposes non-capture action")

    # K3: Tech DAG (no cycles)
    if p.ptype == "research" and "tech" in p.target:
        tech = p.target["tech"]
        if tech in TECH_TREE:
            for req in TECH_TREE[tech]["req"]:
                if req in gs.tech:
                    pass  # Dependency satisfied
                else:
                    violations.append(f"K3_DAG: Tech {tech} requires {req}")

    return violations


def log_kernel_violations(gs: GameState, p: Proposal, violations: List[str]) -> None:
    """Log constraint violations as soft events."""
    if violations:
        for v in violations:
            gs.events.append(Event(gs.turn, "kernel_constraint",
                f"[SOFT] {p.agent} proposal {p.pid}: {v}"))

# ═══════════════════════════════════════════════════════════════════════════════
# 5b.  PLAYER ACTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _adjacent(pos: Tuple[int,int]) -> List[Tuple[int,int]]:
    x,y = pos
    return [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]

def _adjacent_player(tiles: Dict, pos: Tuple[int,int]) -> bool:
    return any(tiles.get(a,Tile(0,0)).owner=="player" for a in _adjacent(pos))

def _adjacent_enemy(tiles: Dict, pos: Tuple[int,int]) -> bool:
    return any(tiles.get(a,Tile(0,0)).owner=="enemy" for a in _adjacent(pos))

def capture_tile(gs: GameState, pos: Tuple[int,int]) -> Tuple[bool, str]:
    """Attempt to capture a tile. Returns (success, message)."""
    if pos not in gs.tiles:
        return False, "Tile not found."
    t = gs.tiles[pos]
    if t.owner == "player":
        return False, "Already yours."
    if t.terrain == "water":
        return False, "Cannot capture water tiles."
    if not _adjacent_player(gs.tiles, pos):
        return False, "Not adjacent to your territory."
    props  = TERRAIN[t.terrain]
    logmod = 0.80 if "logistics" in gs.tech else 1.0
    cost_p = int((props[1] + t.threat * THREAT_ALPHA) * logmod)
    if gs.P < cost_p:
        return False, f"Need {cost_p} Power (have {gs.P})."
    gs.P    -= cost_p
    t.owner  = "player"
    t.threat = max(0, t.threat - 1)
    gs.events.append(Event(gs.turn,"capture",
        f"Captured {t.terrain} tile at {pos}. Cost {cost_p}P.", {"pos":pos}))
    return True, f"Captured {pos}! (-{cost_p}P)"


def fortify_tile(gs: GameState, pos: Tuple[int,int]) -> Tuple[bool, str]:
    if pos not in gs.tiles or gs.tiles[pos].owner != "player":
        return False, "Must own tile to fortify."
    t = gs.tiles[pos]
    if t.fortified:
        return False, "Already fortified."
    cost = 3
    if gs.P < cost:
        return False, f"Need {cost}P."
    gs.P -= cost; t.fortified = True; t.threat = max(0, t.threat-2)
    gs.events.append(Event(gs.turn,"fortify",f"Tile {pos} fortified."))
    return True, f"Tile {pos} fortified. (-{cost}P)"


def queue_build(gs: GameState, mtype: str, slot: Tuple[int,int],
                pid: str = "") -> Tuple[bool, str]:
    if mtype not in MODULE_DEFS:
        return False, f"Unknown module: {mtype}"
    # Check slot free
    occupied = {m.slot for m in gs.castle}
    occupied |= {b.slot for b in gs.build_queue}
    if slot in occupied:
        return False, f"Slot {slot} already occupied."
    if not (0 <= slot[0] < CASTLE_SIZE and 0 <= slot[1] < CASTLE_SIZE):
        return False, f"Slot {slot} out of castle grid."
    d = MODULE_DEFS[mtype]
    # Tech discounts
    ck, cp, cm = d["k"], d["p"], d["m"]
    if mtype in ("wall","gatehouse") and "fortification" in gs.tech:
        cm = max(0, int(cm*0.75))
    if gs.K < ck or gs.P < cp or gs.M < cm:
        return False, f"Need K≥{ck} P≥{cp} M≥{cm} (have K={gs.K} P={gs.P} M={gs.M})."
    gs.K -= ck; gs.P -= cp; gs.M -= cm
    gs.build_queue.append(BuildQueueItem(mtype=mtype, slot=slot,
                                         ticks=d["t"], total=d["t"], pid=pid))
    gs.events.append(Event(gs.turn,"queue",
        f"Queued {mtype} at {slot}. Est. {d['t']} ticks."))
    return True, f"Queued {mtype} at slot {slot} ({d['t']} ticks)."


def research_tech(gs: GameState, tech: str) -> Tuple[bool, str]:
    if tech not in TECH_TREE:
        return False, f"Unknown tech: {tech}"
    if tech in gs.tech:
        return False, "Already researched."
    td = TECH_TREE[tech]
    for req in td["req"]:
        if req not in gs.tech:
            return False, f"Requires '{req}' first."
    if gs.K < td["k"]:
        return False, f"Need {td['k']}K (have {gs.K})."
    gs.K -= td["k"]
    gs.tech.add(tech)
    gs.events.append(Event(gs.turn,"research",f"Researched: {tech}. {td['lbl']}"))
    _recompute_ticks(gs)
    return True, f"Researched {tech}!"

# ═══════════════════════════════════════════════════════════════════════════════
# 6.  AUTONOMOUS AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

def _next_pid(gs: GameState) -> str:
    gs.pid_counter += 1
    return f"P{gs.pid_counter:04d}"


def agent_planner(gs: GameState) -> List[Proposal]:
    """LEGO1: PLANNER — 'I design castle layout and optimize adjacency bonuses.'"""
    proposals = []
    built_types = {m.mtype for m in gs.castle if m.built}
    in_queue    = {b.mtype for b in gs.build_queue}
    occupied    = {m.slot for m in gs.castle} | {b.slot for b in gs.build_queue}

    def free_slot():
        for y in range(CASTLE_SIZE):
            for x in range(CASTLE_SIZE):
                if (x,y) not in occupied:
                    return (x,y)
        return None

    # Suggest library if not yet built and K_tick low
    if "library" not in built_types and "library" not in in_queue and gs.K_tick < 4:
        sl = free_slot()
        if sl:
            d = MODULE_DEFS["library"]
            p = Proposal(
                pid=_next_pid(gs), agent="PLANNER", ptype="build",
                target={"mtype":"library","slot":sl},
                cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                delta={"K_tick":+3}, priority=4,
                tags=["K_DEFICIT","ADJ_BONUS"],
                superteam="PRODUCTION", district="FOUNDRY"
            )
            proposals.append(p)

    # Suggest observatory if library built and K high
    if "library" in built_types and "observatory" not in built_types \
       and "observatory" not in in_queue and gs.K >= 10:
        sl = free_slot()
        if sl:
            d = MODULE_DEFS["observatory"]
            p = Proposal(
                pid=_next_pid(gs), agent="PLANNER", ptype="build",
                target={"mtype":"observatory","slot":sl},
                cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                delta={"K_tick":+5}, priority=3,
                tags=["ASCENSION_PATH","K_BONUS"],
                superteam="PRODUCTION", district="FOUNDRY"
            )
            proposals.append(p)

    # Suggest scriptorium adjacent to library
    if "library" in built_types and "scriptorium" not in built_types \
       and "scriptorium" not in in_queue:
        lib_slot = next((m.slot for m in gs.castle if m.mtype=="library" and m.built), None)
        if lib_slot:
            ax, ay = lib_slot[0]+1, lib_slot[1]
            if (ax,ay) not in occupied and ax < CASTLE_SIZE:
                d = MODULE_DEFS["scriptorium"]
                p = Proposal(
                    pid=_next_pid(gs), agent="PLANNER", ptype="build",
                    target={"mtype":"scriptorium","slot":(ax,ay)},
                    cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                    delta={"K_tick":+4}, priority=3,
                    tags=["ADJ_BONUS","SCHOLAR_SYNERGY"],
                    superteam="PRODUCTION", district="FOUNDRY"
                )
                proposals.append(p)
    return proposals


def agent_economist(gs: GameState) -> List[Proposal]:
    """LEGO1: ECONOMIST — 'I balance resources and prevent deficits.'"""
    proposals = []
    built_types = {m.mtype for m in gs.castle if m.built}
    in_queue    = {b.mtype for b in gs.build_queue}
    occupied    = {m.slot for m in gs.castle} | {b.slot for b in gs.build_queue}

    def free_slot():
        for y in range(CASTLE_SIZE):
            for x in range(CASTLE_SIZE):
                if (x,y) not in occupied:
                    return (x,y)
        return None

    # If materials very low, suggest forge (PRODUCTION team)
    if gs.M < 10 and "forge" not in built_types and "forge" not in in_queue:
        sl = free_slot()
        if sl:
            d = MODULE_DEFS["forge"]
            p = Proposal(
                pid=_next_pid(gs), agent="ECONOMIST", ptype="build",
                target={"mtype":"forge","slot":sl},
                cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                delta={"M_tick":+3}, priority=4,
                tags=["M_DEFICIT","ECONOMY"],
                superteam="PRODUCTION", district="FOUNDRY"
            )
            proposals.append(p)

    # If granary not built and stability < 3 (PRODUCTION team)
    if "granary" not in built_types and "granary" not in in_queue and gs.stability < 3:
        sl = free_slot()
        if sl:
            d = MODULE_DEFS["granary"]
            p = Proposal(
                pid=_next_pid(gs), agent="ECONOMIST", ptype="build",
                target={"mtype":"granary","slot":sl},
                cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                delta={"stab":+2}, priority=5,
                tags=["STAB_DEFICIT","FAMINE_RISK"],
                superteam="PRODUCTION", district="FOUNDRY"
            )
            proposals.append(p)

    # Suggest Logistics tech if P is a bottleneck (EXPANSION team)
    if gs.K >= 25 and "logistics" not in gs.tech and gs.P < 20:
        p = Proposal(
            pid=_next_pid(gs), agent="ECONOMIST", ptype="research",
            target={"tech":"logistics"},
            cost_k=20, cost_p=0, cost_m=0, ticks=0,
            delta={"capture_cost":-20}, priority=3,
            tags=["P_DEFICIT","TECH_UNLOCK"],
            superteam="EXPANSION", district="FRONTIER"
        )
        proposals.append(p)
    return proposals


def agent_defender(gs: GameState) -> List[Proposal]:
    """LEGO1: DEFENDER — 'I identify threats and recommend fortifications.'"""
    proposals = []
    built_types = {m.mtype for m in gs.castle if m.built}
    in_queue    = {b.mtype for b in gs.build_queue}
    occupied    = {m.slot for m in gs.castle} | {b.slot for b in gs.build_queue}

    def free_slot():
        for y in range(CASTLE_SIZE):
            for x in range(CASTLE_SIZE):
                if (x,y) not in occupied:
                    return (x,y)
        return None

    # High-threat unfortified player tiles (DEFENSE team, FRONTIER district)
    hotspots = [pos for pos,t in gs.tiles.items()
                if t.owner=="player" and t.threat>=3 and not t.fortified]
    if hotspots:
        hotspots.sort(key=lambda p: gs.tiles[p].threat, reverse=True)
        for pos in hotspots[:2]:
            p = Proposal(
                pid=_next_pid(gs), agent="DEFENDER", ptype="fortify",
                target={"pos":pos},
                cost_k=0, cost_p=3, cost_m=0, ticks=0,
                delta={"threat":-2,"def":+1}, priority=4,
                tags=["FRONTIER_RISK","FORTIFY"],
                superteam="DEFENSE", district="FRONTIER"
            )
            proposals.append(p)

    # Barracks if none (DEFENSE team, builds for FRONTIER)
    if "barracks" not in built_types and "barracks" not in in_queue and gs.P_tick < 4:
        sl = free_slot()
        if sl:
            d = MODULE_DEFS["barracks"]
            p = Proposal(
                pid=_next_pid(gs), agent="DEFENDER", ptype="build",
                target={"mtype":"barracks","slot":sl},
                cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                delta={"P_tick":+2,"def":+1}, priority=3,
                tags=["P_DEFICIT","DEFENSE"],
                superteam="DEFENSE", district="FRONTIER"
            )
            proposals.append(p)

    # Wall if under frequent raids (DEFENSE team, FRONTIER district)
    raid_count = sum(1 for e in gs.events[-10:] if e.etype=="raid")
    if raid_count >= 2 and "wall" not in built_types and "wall" not in in_queue:
        sl = free_slot()
        if sl:
            d = MODULE_DEFS["wall"]
            p = Proposal(
                pid=_next_pid(gs), agent="DEFENDER", ptype="build",
                target={"mtype":"wall","slot":sl},
                cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                delta={"def":+2}, priority=5,
                tags=["RAID_RESPONSE","DEFENSE"],
                superteam="DEFENSE", district="FRONTIER"
            )
            proposals.append(p)
    return proposals


def agent_researcher(gs: GameState) -> List[Proposal]:
    """LEGO1: RESEARCHER — 'I identify tech gaps and research paths.'"""
    proposals = []

    # Suggest Writing tech (SCIENCE district, but needed by PRODUCTION)
    if "writing" not in gs.tech and gs.K >= 15:
        p = Proposal(
            pid=_next_pid(gs), agent="RESEARCHER", ptype="research",
            target={"tech":"writing"},
            cost_k=15, cost_p=0, cost_m=0, ticks=0,
            delta={"K_tick":+2}, priority=4,
            tags=["TECH_UNLOCK","SCHOLAR_PATH"],
            superteam="SCIENCE", district="SCIENCE"
        )
        proposals.append(p)

    # Suggest Astronomy after Writing (SCIENCE district, ASCENSION path)
    if "writing" in gs.tech and "astronomy" not in gs.tech and gs.K >= 30:
        p = Proposal(
            pid=_next_pid(gs), agent="RESEARCHER", ptype="research",
            target={"tech":"astronomy"},
            cost_k=30, cost_p=0, cost_m=0, ticks=0,
            delta={"K_tick":+5}, priority=3,
            tags=["ASCENSION_PATH","TECH_UNLOCK"],
            superteam="SCIENCE", district="SCIENCE"
        )
        proposals.append(p)

    # Suggest Metallurgy (SCIENCE district, supports PRODUCTION)
    if "writing" in gs.tech and "metallurgy" not in gs.tech and gs.K >= 25:
        p = Proposal(
            pid=_next_pid(gs), agent="RESEARCHER", ptype="research",
            target={"tech":"metallurgy"},
            cost_k=25, cost_p=0, cost_m=0, ticks=0,
            delta={"M_tick":+2}, priority=2,
            tags=["TECH_UNLOCK","ECONOMY"],
            superteam="SCIENCE", district="SCIENCE"
        )
        proposals.append(p)
    return proposals


def agent_builder(gs: GameState) -> List[Proposal]:
    """LEGO1: BUILDER — 'I schedule construction and manage queues.'"""
    proposals = []
    # If queue is empty and resources are healthy, nudge a build (PRODUCTION team)
    if not gs.build_queue and gs.M >= 20 and gs.K >= 10:
        built_types = {m.mtype for m in gs.castle if m.built}
        occupied    = {m.slot for m in gs.castle} | {b.slot for b in gs.build_queue}
        priority_list = ["library","barracks","forge","granary","shrine"]
        for mtype in priority_list:
            if mtype not in built_types:
                for y in range(CASTLE_SIZE):
                    for x in range(CASTLE_SIZE):
                        if (x,y) not in occupied:
                            d = MODULE_DEFS[mtype]
                            p = Proposal(
                                pid=_next_pid(gs), agent="BUILDER", ptype="build",
                                target={"mtype":mtype,"slot":(x,y)},
                                cost_k=d["k"], cost_p=d["p"], cost_m=d["m"], ticks=d["t"],
                                delta=dict(d["eff"]), priority=2,
                                tags=["QUEUE_IDLE","MASON_SCHEDULE"],
                                superteam="PRODUCTION", district="FOUNDRY"
                            )
                            proposals.append(p)
                            return proposals
    return proposals


def agent_explorer(gs: GameState) -> List[Proposal]:
    """LEGO1: EXPLORER — 'I find expansion targets and map intelligence.'"""
    proposals = []
    # Find capturable tiles with good yields (EXPANSION team, FRONTIER district)
    candidates = []
    for pos, t in gs.tiles.items():
        if t.owner != "player" and t.terrain != "water":
            if _adjacent_player(gs.tiles, pos):
                score = t.yield_k*2 + t.yield_p + t.yield_m - t.threat*2
                props  = TERRAIN[t.terrain]
                logmod = 0.80 if "logistics" in gs.tech else 1.0
                cost_p = int((props[1] + t.threat * THREAT_ALPHA) * logmod)
                candidates.append((score, cost_p, pos, t))

    candidates.sort(key=lambda c: c[0], reverse=True)
    for score, cost_p, pos, t in candidates[:3]:
        priority = 4 if score >= 3 else 3 if score >= 1 else 2
        p = Proposal(
            pid=_next_pid(gs), agent="EXPLORER", ptype="capture",
            target={"pos":pos},
            cost_k=0, cost_p=cost_p, cost_m=0, ticks=0,
            delta={"K_tick":t.yield_k,"P_tick":t.yield_p,"M_tick":t.yield_m},
            priority=priority,
            tags=["EXPAND","SCOUT_REC",
                  "SITE" if t.site!="none" else "STANDARD",
                  t.terrain.upper()],
            superteam="EXPANSION", district="FRONTIER"
        )
        proposals.append(p)
    return proposals


# ═══════════════════════════════════════════════════════════════════════════════
# 6a. THREE HOUSES CONFIGURATION (LEGO3+ Narrative Layer)
# ═══════════════════════════════════════════════════════════════════════════════

# HOUSE_CONFIGS: Each House biases agent priorities differently
# Principle: "Lux in tenebris — lux tenenda, non ostentanda" (light held, not displayed)
HOUSE_CONFIGS = {
    "AVALON": {
        "sigil": "⚜",
        "name": "House of Fixation",
        "desc": "The Tower holds light steady: BUILDER + PLANNER favored, slow expansion",
        "agent_weights": {
            "PLANNER": 1.4,      # Architectural vision
            "BUILDER": 1.3,      # Module construction focus
            "ECONOMIST": 1.0,    # Steady state
            "DEFENDER": 0.9,     # Passive defense
            "EXPLORER": 0.7,     # Conservative expansion
            "RESEARCHER": 1.1,   # Incremental research
        },
    },
    "CAMELOT": {
        "sigil": "⚔",
        "name": "House of Law",
        "desc": "The Crown expands territory: EXPLORER + DEFENDER favored, aggressive borders",
        "agent_weights": {
            "EXPLORER": 1.5,     # Territorial conquest
            "DEFENDER": 1.4,     # Militant protection
            "ECONOMIST": 1.0,    # Resource balance
            "PLANNER": 0.9,      # Reactive architecture
            "BUILDER": 0.8,      # Lower construction priority
            "RESEARCHER": 0.8,   # Military-focused research only
        },
    },
    "MORGANA": {
        "sigil": "🜍",
        "name": "House of Alchemy",
        "desc": "The Mist shifts knowledge: RESEARCHER + ECONOMIST favored, hidden paths",
        "agent_weights": {
            "RESEARCHER": 1.5,   # Deep knowledge pursuit
            "ECONOMIST": 1.4,    # Resource manipulation
            "PLANNER": 1.1,      # Creative design
            "BUILDER": 0.9,      # Mystical construction
            "DEFENDER": 0.7,     # Trusts mist for defense
            "EXPLORER": 0.8,     # Seeks knowledge sites
        },
    },
}

# OPUS_PHASES: SEPTEM alchemical stages (1–7)
# Progression mirrors game phases: exploration → action → transformation → resolution
OPUS_PHASES = {
    1: ("CALCINATIO", "🜂", "things burn"),
    2: ("SOLUTIO", "🜄", "ego dissolves"),
    3: ("SEPARATION", "🜁", "essences part"),
    4: ("CONJUNCTION", "🜅", "opposites unite"),
    5: ("FERMENTATION", "🜆", "spirit rises"),
    6: ("DISTILLATION", "🜇", "essence distills"),
    7: ("COAGULATIO", "🜈", "stone is made"),
}

# MIST_EVENTS: Escalation triggers at T10, T20, T30
# Each event is (turn, event_name, House-specific description)
MIST_EVENTS = [
    (10, "mist_gathering", "The Mist stirs. Threats coalesce at the border."),
    (20, "mist_pressure_peak", "The Mist presses inward. Territory destabilizes."),
    (30, "mist_reckoning", "The Mist crowns a victor or consumes all. Final choice."),
]


ALL_AGENTS = [agent_planner, agent_economist, agent_defender,
              agent_researcher, agent_builder, agent_explorer]

# LEGO2 Superteam definitions
SUPERTEAMS = {
    "PRODUCTION":   Superteam("PRODUCTION", ["PLANNER","ECONOMIST","BUILDER"],
                             "Convert resources into built structures"),
    "DEFENSE":      Superteam("DEFENSE", ["DEFENDER"],
                             "Prevent raids, fortify frontier, defend territory"),
    "EXPANSION":    Superteam("EXPANSION", ["EXPLORER","ECONOMIST"],
                             "Capture tiles, scout threats, grow territory"),
    "SCIENCE":      Superteam("SCIENCE", ["RESEARCHER"],
                             "Research technology, unlock bonuses"),
}

# LEGO3 District definitions (note: agent activation map below)
DISTRICTS = {
    "FOUNDRY":  District("FOUNDRY", ["PRODUCTION"], 1,
                        "Production loop: K/P/M → castle modules"),
    "FRONTIER": District("FRONTIER", ["EXPANSION","DEFENSE"], 1,
                        "Expansion & conflict: capture, fortify, defend"),
    "SCIENCE":  District("SCIENCE", ["SCIENCE"], 3,
                        "Research: slow-paced tech unlocks (every 3 turns)"),
}

# Map agents to districts (for rhythm-aware activation)
AGENT_TO_DISTRICT = {
    "agent_planner": "FOUNDRY",
    "agent_economist": ["FOUNDRY", "FRONTIER"],  # Multi-district
    "agent_defender": "FRONTIER",
    "agent_researcher": "SCIENCE",
    "agent_builder": "FOUNDRY",
    "agent_explorer": "FRONTIER",
}

def run_agents(gs: GameState) -> None:
    """Run all agents, organize proposals by LEGO2 superteam + LEGO3 district.

    Respects district rhythm: SCIENCE district activates every 3 turns only.
    """
    # Clear old pending proposals
    gs.proposals = [p for p in gs.proposals if p.status not in ("pending",)]

    # Run agents, checking district activation rhythm
    for agent_fn in ALL_AGENTS:
        agent_name = agent_fn.__name__
        dist_map = AGENT_TO_DISTRICT.get(agent_name)

        if dist_map is None:
            continue  # Unknown agent, skip

        dists = [dist_map] if isinstance(dist_map, str) else dist_map

        # Check if any of this agent's districts are active this turn
        active = False
        for d in dists:
            if d in DISTRICTS and gs.turn % DISTRICTS[d].rhythm == 0:
                active = True
                break

        if not active:
            continue  # Skip this agent, its district(s) inactive this turn

        try:
            new_props = agent_fn(gs)
            # LEGO4: Validate proposals against kernel constraints
            for p in new_props:
                violations = _validate_proposal_kernel(gs, p)
                log_kernel_violations(gs, p, violations)

            # LEGO3+ (Three Houses): Apply House-specific agent weight multipliers
            for p in new_props:
                agent_role = p.agent  # e.g., "PLANNER", "EXPLORER"
                weight = gs.agent_weights.get(agent_role, 1.0)
                p.priority = max(1, int(p.priority * weight))  # clamp to [1,5+]

            gs.proposals.extend(new_props)
        except Exception as ex:
            gs.events.append(Event(gs.turn,"agent_error",
                f"Agent {agent_name} error: {ex}"))


def auto_approve(gs: GameState, priority_threshold: int = 5,
                 risk_limit: int = 1) -> int:
    """Auto-approve proposals above priority_threshold with low threat delta."""
    approved = 0
    for p in gs.proposals:
        if p.status != "pending": continue
        if p.priority >= priority_threshold:
            ok, msg = _execute_proposal(gs, p)
            if ok:
                p.status = "approved"; approved += 1
    return approved


def _execute_proposal(gs: GameState, p: Proposal) -> Tuple[bool, str]:
    if p.ptype == "build":
        mtype = p.target["mtype"]; slot = p.target["slot"]
        return queue_build(gs, mtype, slot, p.pid)
    elif p.ptype == "capture":
        pos = p.target["pos"]
        return capture_tile(gs, pos)
    elif p.ptype == "fortify":
        pos = p.target["pos"]
        return fortify_tile(gs, pos)
    elif p.ptype == "research":
        tech = p.target["tech"]
        return research_tech(gs, tech)
    return False, f"Unknown proposal type: {p.ptype}"

# ═══════════════════════════════════════════════════════════════════════════════
# 7.  ASCII RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

_OWNER_COLORS = {
    "player":  Fore.GREEN,
    "enemy":   Fore.RED,
    "neutral": Fore.WHITE,
}

_TERRAIN_GLYPHS = {t: v[0] for t, v in TERRAIN.items()}

def render_map(gs: GameState) -> str:
    lines = []
    # Header
    land   = [t for t in gs.tiles.values() if t.terrain!="water"]
    owned  = [t for t in land if t.owner=="player"]
    pct    = int(100*len(owned)/max(len(land),1))
    lines.append(
        f"{Fore.YELLOW}TURN {gs.turn:03d}  "
        f"HOUSE: {gs.house}  "
        f"K={gs.K}(+{gs.K_tick}/t)  "
        f"P={gs.P}(+{gs.P_tick}/t)  "
        f"M={gs.M}(+{gs.M_tick}/t)  "
        f"Dominion={pct}%{Style.RESET_ALL}"
    )
    lines.append(
        f"{Fore.CYAN}LEGEND: .=plain *=forest ^=mountain ~=water #=ruins  "
        f"Uppercase=YOURS  lowercase=enemy  ·=neutral{Style.RESET_ALL}"
    )
    lines.append("   " + "".join(f"{x%10}" for x in range(MAP_W)))

    for y in range(MAP_H):
        row = f"{y:2d} "
        for x in range(MAP_W):
            t = gs.tiles.get((x,y))
            if t is None:
                row += " "; continue
            g = _TERRAIN_GLYPHS[t.terrain]
            site_marks = {"ruin":"R","mine":"$","shrine":"S","tower":"T","observatory":"O"}
            if t.site in site_marks:
                g = site_marks[t.site]
            if t.owner == "player":
                col = Fore.GREEN
                g   = g.upper() if not t.fortified else f"{g.upper()}"
                if t.fortified: col = Fore.CYAN
            elif t.owner == "enemy":
                col = Fore.RED
                g   = g.lower()
            else:
                col = Fore.WHITE
            if t.threat >= 4:
                col = Fore.MAGENTA
            row += col + g + Style.RESET_ALL
        lines.append(row)
    return "\n".join(lines)


def render_castle(gs: GameState) -> str:
    grid = [["  ." for _ in range(CASTLE_SIZE)] for _ in range(CASTLE_SIZE)]
    for m in gs.castle:
        x, y = m.slot
        if 0<=x<CASTLE_SIZE and 0<=y<CASTLE_SIZE:
            sym = m.mtype[:2].upper()
            if m.built:
                grid[y][x] = Fore.GREEN + f"[{sym}]"[:4].ljust(3) + Style.RESET_ALL
            else:
                pct = int(100*m.progress/max(m.total_time,1))
                grid[y][x] = Fore.YELLOW + f"({sym})" + Style.RESET_ALL
    for item in gs.build_queue:
        x, y = item.slot
        if 0<=x<CASTLE_SIZE and 0<=y<CASTLE_SIZE:
            sym = item.mtype[:2].upper()
            rem = item.ticks
            grid[y][x] = Fore.YELLOW + f"~{sym}~" + Style.RESET_ALL

    lines = [f"{Fore.YELLOW}═══ CASTLE — {gs.house} ═══{Style.RESET_ALL}"]
    lines.append("    " + "  ".join(str(i) for i in range(CASTLE_SIZE)))
    for y, row in enumerate(grid):
        lines.append(f" {y}  " + "  ".join(row))

    built = [m for m in gs.castle if m.built]
    lines.append("")
    lines.append(f"{Fore.CYAN}Built modules ({len(built)}):{Style.RESET_ALL}")
    for m in built:
        eff = MODULE_DEFS[m.mtype]["eff"]
        eff_str = " | ".join(f"{k}:{v:+d}" for k,v in eff.items())
        lines.append(f"  [{m.mtype.upper():12s}] slot={m.slot}  {eff_str}")

    if gs.build_queue:
        lines.append(f"\n{Fore.YELLOW}Build queue:{Style.RESET_ALL}")
        for b in gs.build_queue:
            bar = "█"*max(0,b.total-b.ticks) + "░"*b.ticks
            lines.append(f"  {b.mtype.upper():12s} {b.ticks}/{b.total}t  [{bar}]")

    if gs.tech:
        lines.append(f"\n{Fore.CYAN}Technologies:{Style.RESET_ALL} " +
                     ", ".join(sorted(gs.tech)))
    return "\n".join(lines)


def render_council(gs: GameState) -> str:
    pending = [p for p in gs.proposals if p.status=="pending"]

    # Add opus mark to council header (narrative layer)
    opus_tuple = OPUS_PHASES.get(gs.opus_phase, ("?", "?", ""))
    opus_mark = opus_tuple[1]

    lines   = [f"{Fore.YELLOW}═══ COUNCIL — {len(pending)} PROPOSALS {opus_mark} ═══{Style.RESET_ALL}"]
    if not pending:
        lines.append("  (No pending proposals — agents are silent.)")
        return "\n".join(lines)

    pending_sorted = sorted(pending, key=lambda p: -p.priority)
    for i, p in enumerate(pending_sorted):
        cost_str  = f"K:{p.cost_k} P:{p.cost_p} M:{p.cost_m}"
        delta_str = " ".join(f"{k}:{v:+d}" for k,v in p.delta.items())
        tag_str   = ",".join(p.tags)
        # Friendly target label
        tgt = p.target
        if isinstance(tgt, dict):
            if "mtype" in tgt and "slot" in tgt:
                target_s = f"{tgt['mtype']}@{tgt['slot']}"
            elif "pos" in tgt:
                target_s = f"tile{tgt['pos']}"
            elif "tech" in tgt:
                target_s = f"tech:{tgt['tech']}"
            else:
                target_s = str(tgt)[:20]
        else:
            target_s = str(tgt)[:20]

        # District + Superteam labels
        dist_lbl = f"[{p.district}]" if p.district else ""
        team_lbl = f"{p.superteam}" if p.superteam else ""

        lines.append(
            f"{Fore.CYAN}[{i+1:2d}]{Style.RESET_ALL} "
            f"{Fore.GREEN}{dist_lbl:12s}{Style.RESET_ALL} "
            f"{Fore.MAGENTA}{team_lbl:12s}{Style.RESET_ALL} "
            f"{Fore.MAGENTA}P{p.priority}{Style.RESET_ALL} "
            f"{p.agent:12s} {p.ptype:9s} "
            f"{Style.BRIGHT}{target_s[:20]:20s}{Style.RESET_ALL} "
            f"({cost_str}) δ({delta_str})"
        )
    return "\n".join(lines)


def render_log(gs: GameState, n: int = 15) -> str:
    lines = [f"{Fore.YELLOW}═══ EVENT LOG (last {n}) ═══{Style.RESET_ALL}"]
    recent = gs.events[-n:]
    for e in reversed(recent):
        col = Fore.WHITE
        if e.etype == "raid":      col = Fore.RED
        if e.etype in ("victory","build_complete"): col = Fore.GREEN
        if e.etype == "capture":   col = Fore.CYAN
        if e.etype == "research":  col = Fore.MAGENTA
        lines.append(f"  {col}T{e.turn:03d} [{e.etype:16s}] {e.desc}{Style.RESET_ALL}")
    return "\n".join(lines)


def render_status(gs: GameState) -> str:
    land  = [t for t in gs.tiles.values() if t.terrain!="water"]
    owned = [t for t in land if t.owner=="player"]
    pct   = int(100*len(owned)/max(len(land),1))

    # House sigil + name
    house_cfg = HOUSE_CONFIGS.get(gs.house, HOUSE_CONFIGS["AVALON"])
    house_sigil = house_cfg["sigil"]

    # Opus phase with symbol
    opus_tuple = OPUS_PHASES.get(gs.opus_phase, ("UNKNOWN", "?", ""))
    opus_name, opus_mark, opus_desc = opus_tuple

    # Mist pressure bar (visual: ▓▓▓░░░ = 3/10)
    mist_bar = "▓" * gs.mist_pressure + "░" * (10 - gs.mist_pressure)

    lines = [
        f"{Fore.YELLOW}CONQUEST v{VERSION}  Seed={gs.seed}  Turn={gs.turn}{Style.RESET_ALL}",
        f"House: {house_sigil} {Fore.GREEN}{gs.house}{Style.RESET_ALL}   "
        f"K={Fore.CYAN}{gs.K}{Style.RESET_ALL}(+{gs.K_tick})  "
        f"P={Fore.CYAN}{gs.P}{Style.RESET_ALL}(+{gs.P_tick})  "
        f"M={Fore.CYAN}{gs.M}{Style.RESET_ALL}(+{gs.M_tick})",
        f"Territory: {Fore.GREEN}{len(owned)}/{len(land)}{Style.RESET_ALL} ({pct}%)  "
        f"Defense={gs.defense}  Stability={gs.stability}",
        f"Opus: {opus_mark} {Fore.MAGENTA}{opus_name}{Style.RESET_ALL} — {opus_desc}",
        f"Mist: {Fore.RED}{mist_bar}{Style.RESET_ALL} ({gs.mist_pressure}/10)",
        f"Objectives: {', '.join(gs.objectives)}",
        f"Victory paths: Dominion≥{int(VICTORY_DOMINION*100)}%  |  "
        f"Ascension K≥{VICTORY_ASCENSION}+Observatory  |  "
        f"Survival {SURVIVAL_TURNS} turns",
    ]
    if gs.turn_hashes:
        lines.append(f"Turn hash: {gs.turn_hashes[-1]}")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════════════════
# 8.  HELP TEXT
# ═══════════════════════════════════════════════════════════════════════════════

HELP = f"""
{Fore.YELLOW}══ CONQUEST COMMANDS ══{Style.RESET_ALL}
  map  / m           — show map
  castle / c         — show castle layout + build queue
  council / co       — show agent proposals
  log  / l [N]       — show last N events (default 15)
  status / s         — show resource summary
  tech               — list available technologies

  capture X Y        — capture tile at (X,Y)   [cost: Power]
  fortify X Y        — fortify owned tile       [cost: 3 Power]
  build MODULE X Y   — queue module in castle slot (X,Y)
  research TECH      — research a technology

  approve N          — approve proposal #N from council
  approve all        — approve all priority≥4 proposals
  deny N             — deny proposal #N

  next / n           — advance one turn (agents re-run)
  next N             — advance N turns automatically
  replay             — show turn hash log (determinism proof)
  seed               — show current seed
  quit / q           — quit

{Fore.CYAN}Castle modules:{Style.RESET_ALL}
""" + "\n".join(
    f"  {k:12s} K{v['k']} P{v['p']} M{v['m']} [{v['t']}t]  {v['desc']}"
    for k,v in MODULE_DEFS.items()
) + f"\n\n{Fore.CYAN}Technologies:{Style.RESET_ALL}\n" + "\n".join(
    f"  {k:14s} {v['lbl']}"
    for k,v in TECH_TREE.items()
)

# ═══════════════════════════════════════════════════════════════════════════════
# 9.  CLI  — interactive game loop
# ═══════════════════════════════════════════════════════════════════════════════

def _clear():
    os.system("clear" if os.name=="posix" else "cls")

def _parse_pos(parts: List[str], offset: int = 0) -> Optional[Tuple[int,int]]:
    try:
        return (int(parts[offset]), int(parts[offset+1]))
    except (IndexError, ValueError):
        return None

def _pending_list(gs: GameState) -> List[Proposal]:
    return sorted([p for p in gs.proposals if p.status=="pending"],
                  key=lambda p: -p.priority)

def game_loop(gs: GameState) -> None:
    print(render_status(gs))
    print(render_map(gs))
    run_agents(gs)
    pending = _pending_list(gs)
    if pending:
        print(f"\n{Fore.CYAN}{len(pending)} agent proposals ready.  Type 'council' to review.{Style.RESET_ALL}")

    while not gs.game_over:
        try:
            raw = input(f"\n{Fore.YELLOW}[T{gs.turn:03d}]>{Style.RESET_ALL} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break
        if not raw: continue
        parts = raw.lower().split()
        cmd   = parts[0]

        # ── VIEW COMMANDS ──────────────────────────────────────────────
        if cmd in ("map","m"):
            print(render_map(gs))

        elif cmd in ("castle","c"):
            print(render_castle(gs))

        elif cmd in ("council","co"):
            run_agents(gs)
            print(render_council(gs))

        elif cmd in ("log","l"):
            n = int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 15
            print(render_log(gs, n))

        elif cmd in ("status","s"):
            print(render_status(gs))

        elif cmd == "tech":
            print(f"{Fore.CYAN}Technologies:{Style.RESET_ALL}")
            for k, v in TECH_TREE.items():
                avail = all(r in gs.tech for r in v["req"])
                done  = k in gs.tech
                stat  = f"{Fore.GREEN}DONE{Style.RESET_ALL}" if done else \
                        (f"{Fore.YELLOW}AVAIL{Style.RESET_ALL}" if avail else "LOCKED")
                print(f"  [{stat}] {k:14s} K≥{v['k']:3d}  {v['lbl']}")

        elif cmd in ("seed",):
            print(f"Seed: {gs.seed}")

        elif cmd == "replay":
            print(f"{Fore.CYAN}Turn hashes (determinism proof):{Style.RESET_ALL}")
            for i,h in enumerate(gs.turn_hashes,1):
                print(f"  T{i:03d} → {h}")

        elif cmd in ("help","h","?"):
            print(HELP)

        # ── ACTIONS ───────────────────────────────────────────────────
        elif cmd == "capture":
            pos = _parse_pos(parts, 1)
            if pos is None:
                print("Usage: capture X Y")
            else:
                ok, msg = capture_tile(gs, pos)
                print((Fore.GREEN if ok else Fore.RED)+msg+Style.RESET_ALL)

        elif cmd == "fortify":
            pos = _parse_pos(parts, 1)
            if pos is None:
                print("Usage: fortify X Y")
            else:
                ok, msg = fortify_tile(gs, pos)
                print((Fore.GREEN if ok else Fore.RED)+msg+Style.RESET_ALL)

        elif cmd == "build":
            if len(parts) < 4:
                print("Usage: build MODULE SLOT_X SLOT_Y")
            else:
                mtype = parts[1]
                slot  = _parse_pos(parts, 2)
                if slot is None:
                    print("Bad slot coordinates.")
                else:
                    ok, msg = queue_build(gs, mtype, slot)
                    print((Fore.GREEN if ok else Fore.RED)+msg+Style.RESET_ALL)

        elif cmd == "research":
            if len(parts) < 2:
                print("Usage: research TECH_NAME")
            else:
                ok, msg = research_tech(gs, parts[1])
                print((Fore.GREEN if ok else Fore.RED)+msg+Style.RESET_ALL)

        # ── COUNCIL ACTIONS ───────────────────────────────────────────
        elif cmd == "approve":
            run_agents(gs)
            pending = _pending_list(gs)
            if not pending:
                print("No pending proposals.")
            elif len(parts) > 1 and parts[1] == "all":
                count = 0
                for p in [x for x in pending if x.priority >= 4]:
                    ok, msg = _execute_proposal(gs, p)
                    if ok:
                        p.status = "approved"; count += 1
                    else:
                        p.status = "denied"
                print(f"Auto-approved {count} proposals.")
            else:
                idx = int(parts[1])-1 if len(parts)>1 and parts[1].isdigit() else -1
                if idx < 0 or idx >= len(pending):
                    print(f"Choose 1..{len(pending)}")
                else:
                    p  = pending[idx]
                    ok, msg = _execute_proposal(gs, p)
                    p.status = "approved" if ok else "denied"
                    print((Fore.GREEN if ok else Fore.RED)+msg+Style.RESET_ALL)

        elif cmd == "deny":
            run_agents(gs)
            pending = _pending_list(gs)
            idx = int(parts[1])-1 if len(parts)>1 and parts[1].isdigit() else -1
            if idx < 0 or idx >= len(pending):
                print(f"Choose 1..{len(pending)}")
            else:
                pending[idx].status = "denied"
                print(f"Proposal {pending[idx].pid} denied.")

        # ── TURN ADVANCE ──────────────────────────────────────────────
        elif cmd in ("next","n"):
            turns = int(parts[1]) if len(parts)>1 and parts[1].isdigit() else 1
            for _ in range(turns):
                advance_turn(gs)
                run_agents(gs)
                if gs.game_over: break
            print(render_status(gs))
            new_events = gs.events[-turns*3:]
            for e in new_events[-5:]:
                col = Fore.RED if e.etype=="raid" else \
                      Fore.GREEN if e.etype in ("victory","build_complete") else Fore.WHITE
                print(f"  {col}[{e.etype}] {e.desc}{Style.RESET_ALL}")
            pending = _pending_list(gs)
            if pending:
                print(f"\n{Fore.CYAN}{len(pending)} proposals from council. Type 'council' to review.{Style.RESET_ALL}")
            if gs.game_over:
                print(f"\n{Fore.YELLOW}{'═'*55}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}  GAME OVER — {gs.victory}{Style.RESET_ALL}")
                last = [e for e in gs.events if e.etype=="victory"]
                if last: print(f"  {last[-1].desc}")
                print(f"{Fore.YELLOW}{'═'*55}{Style.RESET_ALL}")
                break

        elif cmd in ("quit","q","exit"):
            print("Au revoir.")
            break

        else:
            print(f"Unknown command: '{raw}'  — type 'help' for commands.")

    if gs.game_over:
        print("\nFinal turn hashes (replay proof):")
        for i,h in enumerate(gs.turn_hashes,1):
            print(f"  T{i:03d} → {h}")

# ═══════════════════════════════════════════════════════════════════════════════
# 10.  HEADLESS REPLAY MODE
# ═══════════════════════════════════════════════════════════════════════════════

def run_headless(seed: int, turns: int = 30, house: str = "AVALON") -> None:
    print(f"CONQUEST headless replay — seed={seed}  house={house}  turns={turns}")
    gs = new_game(seed, house)
    for t in range(turns):
        run_agents(gs)
        # Auto-approve priority≥4
        for p in [x for x in gs.proposals if x.status=="pending" and x.priority>=4]:
            ok, msg = _execute_proposal(gs, p)
            p.status = "approved" if ok else "denied"
        advance_turn(gs)
        if gs.game_over: break
    print(render_status(gs))
    print(render_map(gs))
    print(f"\nVictory: {gs.victory or 'none'}")
    print(f"Turn hashes ({len(gs.turn_hashes)}):")
    for i,h in enumerate(gs.turn_hashes,1):
        print(f"  T{i:03d} → {h}")
    # Determinism check: replay same seed
    print("\nDeterminism check: replaying same seed…", end=" ")
    gs2 = new_game(seed, house)
    for _ in range(turns):
        run_agents(gs2)
        for p in [x for x in gs2.proposals if x.status=="pending" and x.priority>=4]:
            ok, _ = _execute_proposal(gs2, p)
            p.status = "approved" if ok else "denied"
        advance_turn(gs2)
        if gs2.game_over: break
    if gs.turn_hashes == gs2.turn_hashes:
        print(f"{Fore.GREEN}PASS — identical hashes.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}FAIL — hashes differ!{Style.RESET_ALL}")

# ═══════════════════════════════════════════════════════════════════════════════
# 11.  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    args   = sys.argv[1:]
    replay = "--replay" in args
    if replay: args.remove("--replay")

    if "--help" in args or "-h" in args:
        print(f"CONQUEST v{VERSION}")
        print("Usage: python3 conquest_v1.py [SEED] [--house HOUSE] [--replay]")
        print("  SEED     integer seed (default 111)")
        print("  --house  AVALON | CAMELOT | MORGANA (default AVALON)")
        print("  --replay headless replay for 30 turns + determinism check")
        sys.exit(0)

    seed = 111
    house = "AVALON"

    # Parse arguments
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--house" and i+1 < len(args):
            house = args[i+1].upper()
            i += 2
        elif a.isdigit():
            seed = int(a)
            i += 1
        else:
            i += 1

    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}║  CONQUEST v{VERSION}   seed={seed:<6d}                 ║{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}║  House: {house:<36s}║{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}║  Le savoir mène au pouvoir.                  ║{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}╚══════════════════════════════════════════════╝{Style.RESET_ALL}")

    if replay:
        run_headless(seed, 30, house)
    else:
        gs = new_game(seed, house)
        game_loop(gs)


if __name__ == "__main__":
    main()
