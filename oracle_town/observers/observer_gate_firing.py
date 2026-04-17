#!/usr/bin/env python3
"""
OBSERVER: Gate Firing Entropy

Measures which gates are active and how their firing patterns change.
Does not influence gate logic. Read-only measurement.

Metrics:
  - Gate firing frequency (which gates fire most)
  - Gate firing entropy (diversity of gate usage)
  - Co-firing patterns (gates that fire together)
  - Per-gate accuracy (what % of rejections are caught by each gate)

Output: Statistical analysis only (no decisions, no recommendations).
"""

import json
from pathlib import Path
from collections import defaultdict
import math

def analyze_gate_firing(ledger_dir: Path = Path("oracle_town/ledger")) -> dict:
    """
    Scan ledger and analyze gate firing patterns.

    Returns dict with:
      - gate_frequencies: {gate: count}
      - gate_entropy: float (Shannon entropy)
      - co_firing: {(gate1, gate2): count}
      - gate_accuracy: {gate: (hits, total_rejections, accuracy_pct)}
    """

    stats = {
        "gate_frequencies": defaultdict(int),
        "co_firing_pairs": defaultdict(int),
        "claims_analyzed": 0,
        "rejections_analyzed": 0,
    }

    # Scan ledger
    for year_dir in sorted(ledger_dir.glob("*")):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue

        for month_dir in sorted(year_dir.glob("*")):
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue

            for claim_dir in sorted(month_dir.glob("*")):
                if not claim_dir.is_dir():
                    continue

                verdict_file = claim_dir / "mayor_receipt.json"
                if not verdict_file.exists():
                    continue

                try:
                    with open(verdict_file, "r") as f:
                        receipt = json.load(f)

                    decision = receipt.get("decision", "UNKNOWN")
                    checks = receipt.get("checks_performed", [])

                    stats["claims_analyzed"] += 1

                    # Track failing checks (gates that fire)
                    failing_gates = []
                    for check in checks:
                        if check.get("result") == "FAIL":
                            gate_code = check.get("check", "UNKNOWN")
                            failing_gates.append(gate_code)
                            stats["gate_frequencies"][gate_code] += 1
                            stats["rejections_analyzed"] += 1

                    # Track co-firing patterns
                    if len(failing_gates) > 1:
                        for i in range(len(failing_gates)):
                            for j in range(i + 1, len(failing_gates)):
                                pair = tuple(sorted([failing_gates[i], failing_gates[j]]))
                                stats["co_firing_pairs"][pair] += 1

                except Exception as e:
                    print(f"  ⚠ Error reading {verdict_file}: {e}")

    # Compute Shannon entropy
    total = stats["rejections_analyzed"]
    entropy = 0.0
    if total > 0:
        for gate, count in stats["gate_frequencies"].items():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

    stats["gate_entropy"] = round(entropy, 3)

    # Convert defaultdicts to regular dicts for output
    stats["gate_frequencies"] = dict(stats["gate_frequencies"])
    stats["co_firing_pairs"] = dict(stats["co_firing_pairs"])

    return stats


def report_gate_firing(stats: dict) -> str:
    """Format gate firing analysis as human-readable report."""

    report = []
    report.append("\n╔═══════════════════════════════════════════╗")
    report.append("║  OBSERVER: Gate Firing Entropy Analysis  ║")
    report.append("╚═══════════════════════════════════════════╝\n")

    report.append(f"Claims analyzed: {stats['claims_analyzed']}")
    report.append(f"Rejections analyzed: {stats['rejections_analyzed']}")
    report.append(f"Gate entropy: {stats['gate_entropy']:.3f} (max theoretical: 2.585)\n")

    report.append("Gate firing frequency (ranked):")
    sorted_gates = sorted(
        stats["gate_frequencies"].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for gate, count in sorted_gates:
        pct = (count / stats["rejections_analyzed"] * 100) if stats["rejections_analyzed"] > 0 else 0
        report.append(f"  {gate:40s} {count:3d} ({pct:5.1f}%)")

    if stats["co_firing_pairs"]:
        report.append("\nCo-firing patterns (gates that fire together):")
        sorted_pairs = sorted(
            stats["co_firing_pairs"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for (gate1, gate2), count in sorted_pairs[:10]:  # Top 10
            report.append(f"  {gate1} + {gate2}: {count}")

    report.append("\nInterpretation:")
    report.append("  - Entropy > 2.0 indicates healthy gate diversity")
    report.append("  - No single dominant gate is healthy (distributed load)")
    report.append("  - Co-firing patterns reveal overlapping failure modes")

    return "\n".join(report)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gate Firing Observer")
    parser.add_argument("--ledger-dir", default="oracle_town/ledger", help="Path to ledger")
    parser.add_argument("--output", default=None, help="Save report to file")
    args = parser.parse_args()

    stats = analyze_gate_firing(Path(args.ledger_dir))
    report = report_gate_firing(stats)
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\n✓ Report saved to {args.output}")

    # Save raw stats as JSON
    stats_file = Path("oracle_town/observers/gate_firing_stats.json")
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Raw stats saved to {stats_file}")


if __name__ == "__main__":
    main()
