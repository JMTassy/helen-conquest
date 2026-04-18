#!/usr/bin/env python3
"""
Multi-Castle Federation Implementation (Axis 4B)

Deterministic multi-agent governance with MAGI-driven coordination.
K5 compliance: same seed + same policies + same MAGI = identical outcome.

Author: Claude Code
Date: February 15, 2026
Status: Phase 2 Implementation
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Tuple
from datetime import datetime, timezone
from enum import Enum
import hashlib


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

class Faction(Enum):
    """Faction definitions."""
    TEMPLAR = "✝️"
    ROSICRUCIAN = "🌹"
    CHAOS = "🌀"


@dataclass
class OppositionState:
    """Opposition state (same as Axis 1)."""
    posture: str
    aggression: float
    capability: float


@dataclass
class CastleState:
    """Single castle state (Axis 1, unchanged)."""
    territory: float = 1.0
    stability: float = 5.0
    cohesion: float = 5.0
    knowledge: float = 3.0
    entropy: float = 2.0
    debt: float = 0.0
    inertia: float = 0.0
    fatigue: float = 0.0
    opposition: OppositionState = field(default_factory=lambda: OppositionState(
        posture="OBSERVE", aggression=2.0, capability=2.0
    ))


@dataclass
class WorldStateMultiCastle:
    """Multi-castle world state (Axis 4B)."""
    tick: int = 0
    castles: Dict[str, CastleState] = field(default_factory=dict)
    faction_allegiances: Dict[str, str] = field(default_factory=dict)
    entropy_global: float = 2.0
    ledger: List[Dict] = field(default_factory=list)

    def entropy_pool(self) -> float:
        if not self.castles:
            return 0.0
        return sum(c.entropy for c in self.castles.values()) / len(self.castles)

    def update_entropy_global(self) -> None:
        self.entropy_global = self.entropy_pool()

    def ledger_entries_for_tick(self, tick: int) -> List[Dict]:
        return [e for e in self.ledger if e.get('tick') == tick]

    def ledger_entries_for_castle(self, castle_id: str) -> List[Dict]:
        return [e for e in self.ledger if e.get('source_castle') == castle_id]

    def ledger_entries_targeting_castle(self, castle_id: str, tick_offset: int = 1) -> List[Dict]:
        target_tick = self.tick - tick_offset
        if target_tick < 0:
            return []
        return [e for e in self.ledger
                if e.get('tick') == target_tick
                and e.get('target_castle') == castle_id]


# ============================================================================
# AXIS 1 PHYSICS ENGINE (REUSED)
# ============================================================================

def compute_structural_margin(state: CastleState) -> float:
    return (
        state.stability +
        0.5 * state.cohesion +
        0.5 * state.knowledge -
        state.entropy -
        0.5 * state.debt -
        0.5 * state.inertia -
        0.3 * state.fatigue -
        0.2 * state.opposition.aggression
    )


def apply_entropy_drift(state: CastleState) -> None:
    state.entropy = min(10.0, state.entropy + 0.1)


def apply_debt_decay(state: CastleState) -> None:
    state.debt = max(0.0, state.debt - 0.05)


def apply_inertia_decay(state: CastleState) -> None:
    state.inertia = max(0.0, state.inertia - 0.1)


def apply_fatigue_decay(state: CastleState) -> None:
    state.fatigue = max(0.0, state.fatigue - 0.15)


def apply_opposition_effect(state: CastleState) -> None:
    pass


def action_expand(state: CastleState) -> None:
    state.territory = min(20.0, state.territory + 1.0)
    state.entropy = min(10.0, state.entropy + 0.3)
    state.debt = min(10.0, state.debt + 0.4)


def action_fortify(state: CastleState) -> None:
    state.stability = min(10.0, state.stability + 1.5)
    state.entropy = max(0.0, state.entropy - 0.2)
    state.fatigue = min(10.0, state.fatigue + 0.5)


def action_celebrate(state: CastleState) -> None:
    if state.fatigue >= 8.0:
        return
    state.cohesion = min(10.0, state.cohesion + 1.2)
    state.fatigue = min(10.0, state.fatigue + 0.3)
    state.entropy = max(0.0, state.entropy - 0.1)


def action_study(state: CastleState) -> None:
    state.knowledge = min(10.0, state.knowledge + 1.0)
    state.inertia = min(10.0, state.inertia + 0.2)


def action_rest(state: CastleState) -> None:
    state.fatigue = max(0.0, state.fatigue - 1.0)
    state.debt = max(0.0, state.debt - 0.1)


def apply_physics(state: CastleState) -> None:
    apply_entropy_drift(state)
    apply_debt_decay(state)
    apply_inertia_decay(state)
    apply_fatigue_decay(state)


# ============================================================================
# AXIS 4B: POLICY TABLE
# ============================================================================

class PolicyTable:
    """Deterministic decision rules for one castle."""

    def __init__(self, castle_id: str, faction: str):
        self.castle_id = castle_id
        self.faction = faction
        self.last_decision = None
        self.decision_history = []

    def decide_action(self,
                      state: CastleState,
                      world: WorldStateMultiCastle,
                      magi_entries: List[Dict] = None) -> int:

        if magi_entries is None:
            magi_entries = []

        margin = compute_structural_margin(state)

        if margin <= -3:
            return 5

        if state.stability <= 0:
            return 5

        if state.territory <= 0:
            return 5

        if state.opposition.posture == "ATTACK":
            return 2

        if state.opposition.posture == "SABOTAGE":
            allies = self._count_magi_allies(magi_entries)
            if allies > 0:
                return 1
            else:
                return 2

        if state.opposition.posture == "PROBE":
            if state.fatigue > 5:
                return 5
            else:
                return 1

        if state.debt > 5:
            return 5

        if state.fatigue > 8:
            return 5

        if margin > 8 and state.territory < 8:
            return 1

        if margin > 5 and state.entropy > 7:
            return 4

        if state.cohesion < 3:
            if state.fatigue < 8:
                return 3
            else:
                return 5

        if state.knowledge < 4 and state.entropy < 4:
            return 4

        return 2

    def _count_magi_allies(self, magi_entries: List[Dict]) -> int:
        count = 0
        for entry in magi_entries:
            if entry.get('target_castle') == self.castle_id:
                if entry.get('faction') == self.faction:
                    count += 1
        return count


# ============================================================================
# AXIS 4B: MULTI-CASTLE ROUND EXECUTION
# ============================================================================

def execute_round_multi(world: WorldStateMultiCastle) -> None:

    decisions = {}
    for castle_id, castle_state in world.castles.items():
        policy = PolicyTable(castle_id, world.faction_allegiances[castle_id])
        magi_targeting = world.ledger_entries_targeting_castle(castle_id, tick_offset=1)
        action = policy.decide_action(castle_state, world, magi_targeting)
        decisions[castle_id] = action

    sorted_castle_ids = sorted(world.castles.keys())

    for castle_id in sorted_castle_ids:
        castle_state = world.castles[castle_id]
        action = decisions[castle_id]

        if action == 1:
            action_expand(castle_state)
        elif action == 2:
            action_fortify(castle_state)
        elif action == 3:
            action_celebrate(castle_state)
        elif action == 4:
            action_study(castle_state)
        elif action == 5:
            action_rest(castle_state)

        apply_physics(castle_state)

        counter = len([e for e in world.ledger
                       if e['tick'] == world.tick
                       and e.get('source_castle') == castle_id])

        action_names = {1: "EXPAND", 2: "FORTIFY", 3: "CELEBRATE", 4: "STUDY", 5: "REST"}

        ledger_entry = {
            'tick': world.tick,
            'counter': counter,
            'source_castle': castle_id,
            'action': action,
            'action_name': action_names[action],
            'opposition_posture': castle_state.opposition.posture,
            'structural_margin': compute_structural_margin(castle_state),
            'state_after': asdict(castle_state),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        world.ledger.append(ledger_entry)

    world.update_entropy_global()

    for castle_id, castle_state in world.castles.items():
        castle_state.opposition = decide_opposition_posture_multi(
            castle_state, world.entropy_global, world.faction_allegiances[castle_id]
        )

    world.tick += 1


def decide_opposition_posture_multi(state: CastleState,
                                     entropy_global: float,
                                     faction: str) -> OppositionState:

    margin = compute_structural_margin(state)

    faction_mults = {
        "✝️": 1.0,
        "🌹": 0.9,
        "🌀": 1.2,
    }
    mult = faction_mults.get(faction, 1.0)

    if entropy_global > 8:
        if margin <= -3:
            return OppositionState(posture="ATTACK", aggression=4.0 * mult, capability=4.0 * mult)
        elif margin <= 0:
            return OppositionState(posture="SABOTAGE", aggression=3.0 * mult, capability=3.0 * mult)
        elif margin <= 5:
            return OppositionState(posture="PROBE", aggression=2.5 * mult, capability=2.5 * mult)
        else:
            return OppositionState(posture="OBSERVE", aggression=1.5 * mult, capability=1.5 * mult)

    if margin <= -3:
        return OppositionState(posture="ATTACK", aggression=4.0 * mult, capability=4.0 * mult)
    elif margin <= 0:
        return OppositionState(posture="SABOTAGE", aggression=3.0 * mult, capability=3.0 * mult)
    elif margin <= 5:
        return OppositionState(posture="PROBE", aggression=2.0 * mult, capability=2.0 * mult)
    else:
        return OppositionState(posture="OBSERVE", aggression=1.0 * mult, capability=1.0 * mult)


# ============================================================================
# AXIS 4B: MAGI OPERATIONS
# ============================================================================

def fnv1a64_truncated(data: str) -> str:
    h = hashlib.sha256(data.encode()).hexdigest()[:4].upper()
    return h


def issue_magi(source_castle: str,
               target_castle: str,
               world: WorldStateMultiCastle,
               faction: str = None,
               operator: str = None,
               state: str = None) -> bool:

    if faction is None:
        faction = world.faction_allegiances.get(source_castle, "🌹")

    if operator is None:
        operator = "🜄"
    if state is None:
        state = "⚰"

    valid_operators = ["🜄", "🜂", "🜁", "🜃", "⚗", "⚔"]
    valid_states = ["⚰", "🌑", "🖤"]

    if operator not in valid_operators or state not in valid_states:
        return False

    pair = operator + faction
    act_map = {
        ("✝️", "🜄"): "🛡️",
        ("✝️", "🜂"): "🧱",
        ("🌹", "🜄"): "📜",
        ("🌹", "🜂"): "🔬",
        ("🌀", "🜄"): "🔥",
        ("🌀", "🜂"): "🗡",
    }
    act = act_map.get((faction, operator), "🔬")

    effects = {
        ("✝️", "🜄", "⚰"): {"coherence": 1, "chaos": 0, "stability": 1, "entropy": 0},
        ("🌹", "🜄", "⚰"): {"coherence": 1, "chaos": -1, "stability": 0, "entropy": 0},
        ("🌀", "🜄", "⚰"): {"coherence": 0, "chaos": 1, "stability": -1, "entropy": 1},
    }
    delta = effects.get((faction, operator, state), {"coherence": 0, "chaos": 0, "stability": 0, "entropy": 0})

    proof = fnv1a64_truncated(f"{faction}::{operator}->{state}")

    counter = len([e for e in world.ledger if e['tick'] == world.tick])

    magi_entry = {
        'tick': world.tick,
        'counter': counter,
        'source_castle': source_castle,
        'target_castle': target_castle,
        'faction': faction,
        'operator': operator,
        'state': state,
        'pair': pair,
        'act': act,
        'proof': proof,
        'channel': 'WHITE',
        'delta': delta,
        'type': 'magi',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }

    world.ledger.append(magi_entry)
    return True


def verify_determinism(run1: WorldStateMultiCastle,
                        run2: WorldStateMultiCastle) -> Tuple[bool, str]:

    if run1.tick != run2.tick:
        return False, f"Ticks differ: {run1.tick} vs {run2.tick}"

    for castle_id in run1.castles:
        c1 = run1.castles[castle_id]
        c2 = run2.castles[castle_id]

        for attr in ['territory', 'stability', 'cohesion', 'knowledge', 'entropy', 'debt', 'inertia', 'fatigue']:
            v1 = getattr(c1, attr)
            v2 = getattr(c2, attr)
            if abs(v1 - v2) > 0.001:
                return False, f"Castle {castle_id}.{attr} differs: {v1} vs {v2}"

    for castle_id in run1.castles:
        c1 = run1.castles[castle_id]
        c2 = run2.castles[castle_id]
        if c1.opposition.posture != c2.opposition.posture:
            return False, f"Castle {castle_id} opposition differs: {c1.opposition.posture} vs {c2.opposition.posture}"

    if len(run1.ledger) != len(run2.ledger):
        return False, f"Ledger lengths differ: {len(run1.ledger)} vs {len(run2.ledger)}"

    for i, (e1, e2) in enumerate(zip(run1.ledger, run2.ledger)):
        if e1.get('action') != e2.get('action'):
            return False, f"Entry {i} action differs: {e1.get('action')} vs {e2.get('action')}"

    return True, "✅ Determinism verified (K5 compliant)"


def generate_tick_summary(world: WorldStateMultiCastle) -> Dict:

    tick_entries = world.ledger_entries_for_tick(world.tick)

    aggregate_delta = {
        'coherence': sum(e.get('delta', {}).get('coherence', 0) for e in tick_entries),
        'chaos': sum(e.get('delta', {}).get('chaos', 0) for e in tick_entries),
        'stability': sum(e.get('delta', {}).get('stability', 0) for e in tick_entries),
        'entropy': sum(e.get('delta', {}).get('entropy', 0) for e in tick_entries),
    }

    proofs = sorted([str(e.get('proof', '')) for e in tick_entries])
    tick_hash = fnv1a64_truncated(''.join(proofs))

    return {
        'tick': world.tick,
        'aggregate_delta': aggregate_delta,
        'tick_hash': tick_hash,
        'channel': 'WHITE',
        'num_castles': len(world.castles),
        'num_entries': len(tick_entries),
        'entropy_global': world.entropy_global,
    }


if __name__ == "__main__":
    print("=" * 80)
    print("CONQUEST Multi-Castle Federation (Axis 4B)")
    print("=" * 80)

    world = WorldStateMultiCastle(
        castles={
            "simperfidelis": CastleState(
                territory=2.0, stability=6.0, cohesion=5.5,
                knowledge=3.5, entropy=2.0, debt=0.5,
                inertia=0.0, fatigue=0.0
            ),
            "avalon": CastleState(
                territory=1.5, stability=5.5, cohesion=6.0,
                knowledge=4.0, entropy=1.8, debt=0.0,
                inertia=0.1, fatigue=0.0
            ),
            "camelot": CastleState(
                territory=1.8, stability=5.0, cohesion=5.0,
                knowledge=3.0, entropy=2.5, debt=0.3,
                inertia=0.0, fatigue=0.2
            ),
        },
        faction_allegiances={
            "simperfidelis": "🌹",
            "avalon": "🌹",
            "camelot": "✝️",
        }
    )

    print(f"\n📋 Initial State:")
    print(f"  Castles: {list(world.castles.keys())}")
    print(f"  Entropy (global): {world.entropy_global:.1f}")
    print(f"  Tick: {world.tick}")

    print(f"\n🎮 Simulating 5 rounds...")
    for round_num in range(5):
        execute_round_multi(world)
        summary = generate_tick_summary(world)

        print(f"\n  Round {world.tick}:")
        print(f"    Entropy: {world.entropy_global:.2f}")
        print(f"    Entries logged: {summary['num_entries']}")

        for cid, castle in world.castles.items():
            margin = compute_structural_margin(castle)
            print(f"      {cid}: margin={margin:+.1f}, opposition={castle.opposition.posture}")

    print(f"\n✅ Axis 4B implementation complete!")
    print(f"  Total ledger entries: {len(world.ledger)}")
    print(f"  Final tick: {world.tick}")
    print(f"  Final entropy (global): {world.entropy_global:.2f}")


# ============================================================================
# ENHANCED DETERMINISM VERIFIER (HARDENED)
# ============================================================================

def verify_determinism_strict(run1: WorldStateMultiCastle,
                               run2: WorldStateMultiCastle) -> Tuple[bool, str]:
    """
    Enhanced determinism verification that checks:
    1. Ledger integrity (no tampering, no reordering)
    2. Final state equivalence
    3. Exact ledger sequence match
    """

    # Check 1: Exact ledger length match
    if len(run1.ledger) != len(run2.ledger):
        return False, f"Ledger length mismatch: {len(run1.ledger)} vs {len(run2.ledger)}"

    # Check 2: Ledger entry-by-entry verification
    for i, (e1, e2) in enumerate(zip(run1.ledger, run2.ledger)):
        # Compare all fields
        for key in set(list(e1.keys()) + list(e2.keys())):
            v1 = e1.get(key)
            v2 = e2.get(key)

            # Structural margin can have small float diffs
            if key == 'structural_margin':
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    if abs(v1 - v2) > 0.001:
                        return False, f"Entry {i} {key} tampered: {v1} vs {v2}"
                continue

            # All other fields must match exactly
            if v1 != v2:
                return False, f"Entry {i} {key} mismatch: {v1} vs {v2}"

    # Check 3: Final state match
    for castle_id in run1.castles:
        c1 = run1.castles[castle_id]
        c2 = run2.castles[castle_id]

        for attr in ['territory', 'stability', 'cohesion', 'knowledge', 'entropy', 'debt', 'inertia', 'fatigue']:
            v1 = getattr(c1, attr)
            v2 = getattr(c2, attr)
            if abs(v1 - v2) > 0.001:
                return False, f"Castle {castle_id}.{attr} diverged: {v1} vs {v2}"

        if c1.opposition.posture != c2.opposition.posture:
            return False, f"Castle {castle_id} opposition differs"

    # Check 4: Final tick match
    if run1.tick != run2.tick:
        return False, f"Tick count differs: {run1.tick} vs {run2.tick}"

    return True, "✅ Strict determinism verified (ledger + state identical)"
