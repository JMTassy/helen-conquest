#!/usr/bin/env python3
"""
CONQUESTmon-Gotchi: Interactive CLI

Play your castle through 50 rounds of governance challenge.
"""

import sys
import argparse
from conquestmon_gotchi_core import CastleGame, compute_structural_margin


def render_castle_sprite(territory: float, stability: float, entropy: float) -> str:
    """Return ASCII castle emoji."""
    if territory < 2:
        base = "🏚️"
    elif territory < 4:
        base = "🏠"
    elif territory < 8:
        base = "🏰"
    else:
        base = "👑"

    # Add distress if entropy > stability
    if entropy > stability:
        return base + "⚡"
    return base


def render_bar(value: float, max_val: float, length: int = 10) -> str:
    """Return progress bar."""
    filled = int((value / max_val) * length)
    return "█" * filled + "░" * (length - filled)


def render_state(game: CastleGame) -> str:
    """Render full game state."""
    s = game.state
    margin = compute_structural_margin(s)
    status = game.get_margin_status()

    output = []
    output.append(f"\nRound {s.round} | Day {s.day}")
    output.append("═" * 60)

    # Castle sprite and primary metrics
    sprite = render_castle_sprite(s.territory, s.stability, s.entropy)
    output.append(f"{sprite}  Structural Margin: {margin:+.1f} [{status}]")
    output.append("")

    # Primary
    output.append("PRIMARY METRICS")
    output.append(f"  Territory: {render_bar(s.territory, 20)} {s.territory:5.1f}/20")
    output.append(f"  Stability: {render_bar(s.stability, 10)} {s.stability:5.1f}/10")
    output.append(f"  Cohesion:  {render_bar(s.cohesion, 10)} {s.cohesion:5.1f}/10")
    output.append(f"  Knowledge: {render_bar(s.knowledge, 10)} {s.knowledge:5.1f}/10")
    output.append(f"  Entropy:   {render_bar(s.entropy, 10)} {s.entropy:5.1f}/10")
    output.append("")

    # Secondary (Memory)
    output.append("MEMORY (Hysteresis)")
    output.append(f"  Debt:      {render_bar(s.debt, 10)} {s.debt:5.1f}/10")
    output.append(f"  Inertia:   {render_bar(s.inertia, 10)} {s.inertia:5.1f}/10")
    output.append(f"  Fatigue:   {render_bar(s.fatigue, 10)} {s.fatigue:5.1f}/10")
    output.append("")

    # Opposition
    o = s.opposition
    output.append("OPPOSITION")
    output.append(f"  Posture:    {o.posture}")
    output.append(f"  Aggression: {render_bar(o.aggression, 10)} {o.aggression:5.2f}")
    output.append(f"  Capability: {render_bar(o.capability, 10)} {o.capability:5.2f}")
    output.append("")

    output.append("═" * 60)

    return "\n".join(output)


def render_actions() -> str:
    """Render action menu."""
    output = []
    output.append("\nYour action?")
    output.append(
        "  [1] EXPAND     (+Territory, +Entropy, +Debt) — Grow fast, pay later"
    )
    output.append(
        "  [2] FORTIFY    (+Stability, -Entropy, +Fatigue) — Survive attacks"
    )
    output.append("  [3] CELEBRATE  (+Cohesion, +Fatigue) — Keep spirits up")
    output.append("  [4] STUDY      (+Knowledge, +Inertia) — Long-term resilience")
    output.append("  [5] REST       (-Fatigue, -Debt) — Recover")
    output.append("")
    output.append("  [s] status  [l] ledger  [f] forecast  [q] quit")
    output.append("")
    return "\n".join(output)


def render_ledger(game: CastleGame, last_n: int = 5) -> str:
    """Render last N ledger entries."""
    output = []
    output.append(f"\nLast {last_n} rounds:")
    output.append("─" * 60)

    for entry in game.state.ledger[-last_n:]:
        output.append(
            f"  Round {entry['round']:3d}: {entry['action_name']:9s} "
            f"→ Opposition {entry['opposition_posture']:9s} "
            f"L={entry['state_after']['opposition']['aggression']:.1f}"
        )

    return "\n".join(output)


def forecast_rounds(game: CastleGame, n: int = 10) -> str:
    """Project next n rounds (without playing them)."""
    # This is approximate; real forecast would simulate
    output = []
    output.append(f"\nProjection (next {n} rounds, assuming continued EXPAND):")
    output.append("─" * 60)

    s = game.state
    t = s.territory
    st = s.stability
    e = s.entropy
    d = s.debt

    for i in range(n):
        t += 1.0  # Expand
        e += 0.3
        d += 0.4
        e += 0.1  # drift
        if st > 8 and s.cohesion > 7:
            agg = max(0, s.opposition.aggression - 0.1)
        else:
            agg = s.opposition.aggression + 0.1

        margin = st + 0.5 * s.cohesion + 0.5 * s.knowledge - e - 0.5 * d - 0.2 * agg

        output.append(f"  Round {i+1:2d}: Territory {t:5.1f} | Entropy {e:5.1f} | L {margin:+.1f}")

    return "\n".join(output)


def play_interactive(game: CastleGame):
    """Interactive play loop."""
    print("\n" + "=" * 60)
    print("CONQUESTmon-Gotchi: Raise Your Castle")
    print("=" * 60)
    print("\nYour castle is born. Opposition watches.")
    print(f"Seed: {game.state.seed}")
    print("\nType [?] for help.")

    consecutive_victory_rounds = 0
    victory_threshold = 5

    while not game.game_over:
        print(render_state(game))
        print(render_actions())

        try:
            user_input = input("> ").strip().lower()
        except KeyboardInterrupt:
            print("\nGame interrupted.")
            break

        if user_input == "q":
            print("Game ended.")
            break

        elif user_input == "s":
            print(render_state(game))
            continue

        elif user_input == "l":
            print(render_ledger(game, last_n=10))
            continue

        elif user_input == "f":
            print(forecast_rounds(game, n=10))
            continue

        elif user_input == "?":
            print(render_actions())
            continue

        elif user_input in ["1", "2", "3", "4", "5"]:
            action = int(user_input)
            success, msg = game.execute_round(action)

            if success:
                print(f"\n✓ {msg}")

                # Track legendary victory conditions
                margin = compute_structural_margin(game.state)
                if (
                    game.state.territory >= 8
                    and game.state.entropy < 6
                    and game.state.debt < 2
                    and game.state.opposition.posture == "OBSERVE"
                    and margin > 5
                ):
                    consecutive_victory_rounds += 1
                    if consecutive_victory_rounds >= victory_threshold:
                        game.game_over = True
                        game.victory = True
                        print("\n🏆 VICTORY: LEGENDARY BASTION ACHIEVED!")
                else:
                    consecutive_victory_rounds = 0

            else:
                print(f"\n✗ {msg}")

        else:
            print(f"Unknown command: {user_input}")

    # Game over
    if game.game_over:
        print(render_state(game))
        if game.victory:
            print("\n🏆 " * 10)
            print("YOU HAVE ACHIEVED LEGENDARY BASTION!")
            print("Your castle stands eternal. Opposition bows.")
            print("🏆 " * 10)
        else:
            print("\n💀 " * 10)
            print("YOUR CASTLE HAS COLLAPSED!")
            print("The realm falls to chaos. Opposition consumes all.")
            print("💀 " * 10)

        print(f"\nFinal Stats:")
        print(f"  Rounds Survived: {game.state.round}")
        print(f"  Days Lived: {game.state.day}")
        print(f"  Territory Held: {game.state.territory:.1f}")
        print(f"  Final Margin: {compute_structural_margin(game.state):+.1f}")
        print(f"\nLedger saved with seed {game.state.seed}")


def play_headless(game: CastleGame, rounds: int = 100):
    """Play without user input (for testing)."""
    print(f"Running {rounds} rounds with seed {game.state.seed}...")

    actions = [1, 2, 3, 4, 5]
    action_idx = 0

    for _ in range(rounds):
        if game.game_over:
            break

        action = actions[action_idx % 5]
        action_idx += 1

        success, msg = game.execute_round(action)
        if not success:
            print(f"Round {game.state.round}: {msg}")

    print(f"\nGame ended at round {game.state.round}.")
    print(f"Victory: {game.victory}")
    print(f"Final margin: {compute_structural_margin(game.state):+.1f}")


def main():
    parser = argparse.ArgumentParser(description="CONQUESTmon-Gotchi: Playable Governance")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--headless", action="store_true", help="Play without interaction")
    parser.add_argument("--rounds", type=int, default=100, help="Rounds to play in headless mode")

    args = parser.parse_args()

    game = CastleGame(seed=args.seed)

    if args.headless:
        play_headless(game, rounds=args.rounds)
    else:
        play_interactive(game)


if __name__ == "__main__":
    main()
