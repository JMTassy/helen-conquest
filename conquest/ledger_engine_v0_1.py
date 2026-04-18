#!/usr/bin/env python3
"""
Conquest Ledger Engine v0.1

Minimal deterministic session simulation.
Tests: entropy trajectory, stability, knowledge impact, overexpansion punishment.

5 State Variables per Session:
  - knowledge: cumulative learning (0-1000, unbounded)
  - territory: controlled cells (0-36)
  - zols: currency (0-∞)
  - entropy: disorder metric (0-1)
  - turn: session counter (0-36)

Deterministic Update Rule (per turn):
  1. Roll action (knowledge check, duel, expansion)
  2. Update state based on action outcome
  3. Apply entropy penalty (overexpansion)
  4. Check collapse condition
  5. Log to ledger

Collapse Condition:
  entropy > 0.8 OR territory > 30 (overexpansion) OR zols < 0 (bankruptcy)

Output: 200 simulated sessions → statistics on balance, winner distribution, entropy curve
"""

import json
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from pathlib import Path
from collections import defaultdict


@dataclass
class SessionState:
    """Single session state snapshot"""
    turn: int
    knowledge: float
    territory: int
    zols: float
    entropy: float
    stability: float = 1.0
    action: str = ""
    outcome: str = ""


@dataclass
class SessionRecord:
    """Complete session ledger"""
    session_id: int
    archetype: str
    seed: int
    final_knowledge: float
    final_territory: int
    final_zols: float
    final_entropy: float
    final_stability: float
    collapse_turn: int
    collapse_reason: str
    winner: bool
    snapshots: List[SessionState]


class LedgerEngine:
    """Deterministic session engine"""

    def __init__(self, seed: int = 111):
        self.seed = seed
        random.seed(seed)
        self.ledger: List[SessionRecord] = []

    def roll_d6(self) -> int:
        """Deterministic 6-sided die"""
        return random.randint(1, 6)

    def session_update(
        self,
        state: SessionState,
        action_type: str,
        knowledge_mod: float = 0.0,
    ) -> SessionState:
        """
        Deterministic state update rule per turn with pressure math.

        Six structural corrections:
        1. Convex entropy growth (nonlinear overexpansion cost)
        2. Knowledge dampens entropy
        3. Stability coupled to entropy
        4. Collapse condition (entropy >= 1.2 or stability <= 0)
        5. Overexpansion trap (soft cap on territory)
        6. Resource pressure (entropy tax on zols)
        """

        # Roll outcome based on knowledge
        knowledge_roll = self.roll_d6() + (state.knowledge // 100)
        knowledge_check = knowledge_roll >= 4

        new_state = SessionState(
            turn=state.turn + 1,
            knowledge=state.knowledge,
            territory=state.territory,
            zols=state.zols,
            entropy=state.entropy,
            stability=state.stability,
            action=action_type,
        )

        # Baseline entropy: every action generates some chaos (baseline 0.02)
        baseline_entropy = 0.02
        new_state.entropy = min(state.entropy + baseline_entropy, 2.0)

        # Action resolution
        if action_type == "knowledge_check":
            # Learn from study
            if knowledge_check:
                new_state.knowledge = state.knowledge + 50
                new_state.zols = state.zols + 100
                new_state.outcome = "SUCCEED: +50 knowledge, +100 zols"
            else:
                new_state.zols = state.zols + 10
                new_state.outcome = "FAIL: +10 zols (minimal gain)"

        elif action_type == "duel":
            # Territory claim via duel (adds moderate entropy)
            duel_entropy = 0.05
            new_state.entropy = min(new_state.entropy + duel_entropy, 2.0)
            if knowledge_check:
                new_state.territory = min(state.territory + 1, 36)
                new_state.zols = state.zols + 200
                new_state.outcome = "VICTORY: +1 territory, +200 zols, +entropy"
            else:
                new_state.zols = max(state.zols - 50, 0)
                new_state.outcome = "DEFEAT: -50 zols, +entropy"

        elif action_type == "expand":
            # Attempt overexpansion (risky, adds heavy entropy)
            cost = 300
            if state.zols >= cost and state.territory < 30:
                new_state.territory = min(state.territory + 2, 36)
                new_state.zols = state.zols - cost
                # CHANGE 1: Convex entropy growth (nonlinear cost)
                entropy_delta = 0.05 + 0.03 * new_state.territory + 0.02 * (new_state.territory ** 1.5)
                new_state.entropy = min(new_state.entropy + entropy_delta, 2.0)
                new_state.outcome = f"EXPAND: +2 territory, -300 zols, +{entropy_delta:.2f} entropy"
            else:
                new_state.entropy = min(new_state.entropy + 0.1, 2.0)
                new_state.outcome = "EXPAND_FAIL: insufficient resources, +0.1 entropy"

        elif action_type == "rest":
            # Recover (reduce entropy, passive recovery)
            recovery = 0.1
            new_state.entropy = max(new_state.entropy - recovery, 0.0)
            new_state.zols = state.zols + 50
            new_state.outcome = f"REST: -{recovery} entropy, +50 zols"

        # CHANGE 2: Knowledge dampens entropy (but only weakly)
        entropy_reduction = 0.001 * new_state.knowledge  # Reduced from 0.01
        new_state.entropy = max(new_state.entropy - entropy_reduction, 0.0)

        # CHANGE 3: Stability coupled to entropy (nonlinear decay) — reduced
        new_state.stability -= 0.02 * new_state.entropy  # Reduced from 0.05

        # CHANGE 5: Overexpansion trap (soft cap) — only penalizes aggressive expansion
        if action_type == "expand" and new_state.territory > 6:
            stability_penalty = 0.2 * (new_state.territory - 6)
            new_state.stability -= stability_penalty

        # CHANGE 6: Resource pressure (entropy tax)
        entropy_tax = int(new_state.entropy * 50)
        new_state.zols = max(new_state.zols - entropy_tax, 0)

        return new_state

    def simulate_session(
        self,
        session_id: int,
        archetype: str = "Generalist",
        max_turns: int = 36,
    ) -> SessionRecord:
        """
        Simulate one complete session (up to 36 turns).
        Returns when: collapse condition hit OR max_turns reached.
        """

        state = SessionState(
            turn=0,
            knowledge=0.0,
            territory=0,
            zols=500,
            entropy=0.0,
            stability=1.0,
        )

        snapshots = [state]
        collapse_turn = -1
        collapse_reason = "none"

        for turn in range(1, max_turns + 1):
            # Deterministic aggressive strategy by turn phase
            if state.stability <= 0:
                action = "rest"
            elif state.entropy > 1.0:
                action = "rest"
            elif turn <= 6:
                action = "knowledge_check"  # Turns 1-6: build knowledge
            elif turn <= 12:
                action = "duel"  # Turns 7-12: claim territory via duels
            elif turn <= 24:
                action = "expand"  # Turns 13-24: aggressive expansion (risk entropy spike)
            elif state.entropy > 0.5:
                action = "rest"  # Turns 25+: if entropy high, recover
            else:
                action = "duel"  # Turns 25+: if stable, keep claiming

            # Apply update
            state = self.session_update(state, action)
            snapshots.append(state)

            # CHANGE 4: Collapse condition is real (entropy >= 1.2 OR stability <= 0)
            if state.entropy >= 1.2:
                collapse_turn = turn
                collapse_reason = "entropy_cascade"
                break
            elif state.stability <= 0:
                collapse_turn = turn
                collapse_reason = "stability_collapse"
                break
            elif state.zols < 0:
                collapse_turn = turn
                collapse_reason = "bankruptcy"
                break

        # Determine winner (reached 6 territories without collapse)
        winner = (state.territory >= 6 and collapse_turn == -1)

        record = SessionRecord(
            session_id=session_id,
            archetype=archetype,
            seed=self.seed,
            final_knowledge=state.knowledge,
            final_territory=state.territory,
            final_zols=state.zols,
            final_entropy=state.entropy,
            final_stability=state.stability,
            collapse_turn=collapse_turn,
            collapse_reason=collapse_reason,
            winner=winner,
            snapshots=snapshots,
        )

        self.ledger.append(record)
        return record

    def run_batch(self, num_sessions: int = 200) -> Dict[str, Any]:
        """
        Run 200 sessions and analyze balance metrics.
        """

        print(f"\n{'='*80}")
        print(f"CONQUEST LEDGER ENGINE v0.1 — {num_sessions} Session Simulation")
        print(f"{'='*80}\n")

        for i in range(num_sessions):
            self.simulate_session(session_id=i, archetype="Generalist")
            if (i + 1) % 50 == 0:
                print(f"  ✓ Sessions {i+1}/{num_sessions} complete")

        # Analyze results
        analysis = self._analyze_ledger()
        return analysis

    def _analyze_ledger(self) -> Dict[str, Any]:
        """Extract balance metrics from completed ledger"""

        if not self.ledger:
            return {}

        winners = [r for r in self.ledger if r.winner]
        collapses = [r for r in self.ledger if r.collapse_turn >= 0]

        # Entropy trajectory
        entropy_by_turn = defaultdict(list)
        for record in self.ledger:
            for snapshot in record.snapshots:
                entropy_by_turn[snapshot.turn].append(snapshot.entropy)

        avg_entropy_trajectory = [
            sum(entropy_by_turn[t]) / len(entropy_by_turn[t])
            for t in sorted(entropy_by_turn.keys())
        ]

        # Knowledge impact
        winners_knowledge = [r.final_knowledge for r in winners]
        losers_knowledge = [r.final_knowledge for r in collapses]

        avg_winner_knowledge = (
            sum(winners_knowledge) / len(winners_knowledge)
            if winners_knowledge
            else 0
        )
        avg_loser_knowledge = (
            sum(losers_knowledge) / len(losers_knowledge) if losers_knowledge else 0
        )

        # Collapse distribution
        collapse_reasons = defaultdict(int)
        for record in collapses:
            collapse_reasons[record.collapse_reason] += 1

        # Territory at collapse
        collapse_territories = [r.collapse_turn for r in collapses]
        avg_collapse_turn = (
            sum(collapse_territories) / len(collapse_territories)
            if collapse_territories
            else 0
        )

        analysis = {
            "total_sessions": len(self.ledger),
            "winners": len(winners),
            "winner_rate": f"{len(winners) / len(self.ledger) * 100:.1f}%",
            "collapses": len(collapses),
            "collapse_rate": f"{len(collapses) / len(self.ledger) * 100:.1f}%",
            "avg_winner_knowledge": f"{avg_winner_knowledge:.0f}",
            "avg_loser_knowledge": f"{avg_loser_knowledge:.0f}",
            "knowledge_impact": f"{avg_winner_knowledge - avg_loser_knowledge:.0f} points advantage",
            "collapse_reasons": dict(collapse_reasons),
            "avg_collapse_turn": f"{avg_collapse_turn:.1f}",
            "entropy_trajectory": [f"{e:.3f}" for e in avg_entropy_trajectory],
            "final_entropy_mean": f"{sum(r.final_entropy for r in self.ledger) / len(self.ledger):.3f}",
            "final_entropy_max": f"{max(r.final_entropy for r in self.ledger):.3f}",
            "final_stability_mean": f"{sum(r.final_stability for r in self.ledger) / len(self.ledger):.3f}",
            "final_stability_min": f"{min(r.final_stability for r in self.ledger):.3f}",
            "final_territory_mean": f"{sum(r.final_territory for r in self.ledger) / len(self.ledger):.1f}",
            "final_zols_mean": f"{sum(r.final_zols for r in self.ledger) / len(self.ledger):.0f}",
        }

        return analysis

    def print_analysis(self, analysis: Dict[str, Any]):
        """Pretty-print analysis results"""

        print(f"\n{'='*80}")
        print("ANALYSIS: BALANCE METRICS")
        print(f"{'='*80}\n")

        print(f"📊 VICTORY DISTRIBUTION")
        print(f"  Winners:         {analysis['winners']}/{analysis['total_sessions']} ({analysis['winner_rate']})")
        print(f"  Collapses:       {analysis['collapses']}/{analysis['total_sessions']} ({analysis['collapse_rate']})")

        print(f"\n🧠 KNOWLEDGE IMPACT")
        print(f"  Winner avg:      {analysis['avg_winner_knowledge']} points")
        print(f"  Loser avg:       {analysis['avg_loser_knowledge']} points")
        print(f"  Advantage:       {analysis['knowledge_impact']}")

        print(f"\n💥 COLLAPSE PATTERNS")
        print(f"  Avg collapse turn: {analysis['avg_collapse_turn']}")
        print(f"  Reasons:")
        for reason, count in analysis["collapse_reasons"].items():
            pct = count / analysis["collapses"] * 100 if analysis["collapses"] > 0 else 0
            print(f"    • {reason}: {count} ({pct:.0f}%)")

        print(f"\n🌀 ENTROPY & STABILITY DYNAMICS")
        print(f"  Entropy mean:    {analysis['final_entropy_mean']}")
        print(f"  Entropy max:     {analysis['final_entropy_max']}")
        print(f"  Stability mean:  {analysis['final_stability_mean']}")
        print(f"  Stability min:   {analysis['final_stability_min']}")
        print(f"  Entropy trajectory (every 4 turns):")
        trajectory = analysis["entropy_trajectory"]
        for i in range(0, len(trajectory), 4):
            turn = i
            entropy = trajectory[i]
            bar = "█" * int(float(entropy) * 20)
            print(f"    Turn {turn:2d}: {bar} ({entropy})")

        print(f"\n🏰 TERRITORY & ECONOMY")
        print(f"  Avg territory:   {analysis['final_territory_mean']} cells")
        print(f"  Avg zols:        {analysis['final_zols_mean']} currency")

        print(f"\n{'='*80}\n")

    def save_ledger(self, filename: str = "conquest_ledger_v0_1.json"):
        """Persist ledger to JSON (first 10 records only for brevity)"""

        sample_records = []
        for record in self.ledger[:10]:
            sample_records.append(
                {
                    "session_id": record.session_id,
                    "archetype": record.archetype,
                    "final_knowledge": record.final_knowledge,
                    "final_territory": record.final_territory,
                    "final_zols": record.final_zols,
                    "final_entropy": record.final_entropy,
                    "collapse_turn": record.collapse_turn,
                    "collapse_reason": record.collapse_reason,
                    "winner": record.winner,
                }
            )

        output = {
            "total_sessions": len(self.ledger),
            "seed": self.seed,
            "sample_records": sample_records,
        }

        path = Path(__file__).parent / filename
        with open(path, "w") as f:
            json.dump(output, f, indent=2)

        print(f"✓ Ledger saved to {path}")


def main():
    """Run the full simulation"""

    engine = LedgerEngine(seed=111)
    analysis = engine.run_batch(num_sessions=200)
    engine.print_analysis(analysis)
    engine.save_ledger()

    print("\n" + "="*80)
    print("INTERPRETATION QUESTIONS")
    print("="*80)
    print("""
1. Does entropy explode?
   → Check: final_entropy_mean. If > 0.6, entropy is growing too fast.

2. Does stability collapse too fast?
   → Check: avg_collapse_turn. If < 15, sessions end too early (balance broken).

3. Is knowledge impactful?
   → Check: knowledge_impact. If < 100 points, knowledge barely matters.

4. Does overexpansion punish predictably?
   → Check: collapse_reasons. If "overexpansion" < 30%, penalty is too weak.

5. What's the winner rate?
   → Check: winner_rate. Should be 5-15% (rare but achievable).

""")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
