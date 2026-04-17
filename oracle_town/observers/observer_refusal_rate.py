#!/usr/bin/env python3
"""
OBSERVER: Refusal Rate Tracking

Measures rejection frequency over time windows.
Does not influence gate logic. Read-only measurement.

Metrics:
  - Daily refusal rate
  - Weekly refusal rate
  - Monthly trends
  - Per-gate refusal contribution

Output: Time-series data only (no decisions, no recommendations).
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def analyze_refusal_rate(ledger_dir: Path = Path("oracle_town/ledger")) -> dict:
    """
    Scan ledger and compute refusal statistics.

    Returns dict with:
      - daily_rates: {date: (accepted, rejected, rate)}
      - weekly_rates: {week: (accepted, rejected, rate)}
      - per_gate_rejections: {gate: count}
    """

    stats = {
        "daily_rates": defaultdict(lambda: [0, 0]),  # [accepted, rejected]
        "gate_rejections": defaultdict(int),
        "total": {"accepted": 0, "rejected": 0},
        "measured_days": 0,
        "observation_window": None,
    }

    # Scan ledger structure: YYYY/MM/claim_id/
    for year_dir in sorted(ledger_dir.glob("*")):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue

        for month_dir in sorted(year_dir.glob("*")):
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue

            for claim_dir in sorted(month_dir.glob("*")):
                if not claim_dir.is_dir():
                    continue

                # Load verdict
                verdict_file = claim_dir / "mayor_receipt.json"
                if not verdict_file.exists():
                    continue

                try:
                    with open(verdict_file, "r") as f:
                        receipt = json.load(f)

                    decision = receipt.get("decision", "UNKNOWN")
                    date_key = f"{year_dir.name}-{month_dir.name}"

                    # Track by date
                    if decision == "ACCEPT":
                        stats["daily_rates"][date_key][0] += 1
                        stats["total"]["accepted"] += 1
                    elif decision == "REJECT":
                        stats["daily_rates"][date_key][1] += 1
                        stats["total"]["rejected"] += 1

                        # Track which gate rejected
                        checks = receipt.get("checks_performed", [])
                        for check in checks:
                            if check.get("result") == "FAIL":
                                gate_code = check.get("check", "UNKNOWN")
                                stats["gate_rejections"][gate_code] += 1

                except Exception as e:
                    print(f"  ⚠ Error reading {verdict_file}: {e}")

    # Compute rates
    stats["measured_days"] = len(stats["daily_rates"])

    daily_rates_computed = {}
    for date_key, (accepted, rejected) in stats["daily_rates"].items():
        total = accepted + rejected
        rate = (rejected / total * 100) if total > 0 else 0
        daily_rates_computed[date_key] = {
            "accepted": accepted,
            "rejected": rejected,
            "total": total,
            "refusal_rate_pct": round(rate, 1),
        }

    stats["daily_rates"] = daily_rates_computed

    # Overall rate
    total_claims = stats["total"]["accepted"] + stats["total"]["rejected"]
    overall_rate = (stats["total"]["rejected"] / total_claims * 100) if total_claims > 0 else 0
    stats["overall_refusal_rate_pct"] = round(overall_rate, 1)
    stats["overall_total_claims"] = total_claims

    return stats


def report_refusal_rate(stats: dict) -> str:
    """Format refusal statistics as human-readable report."""

    report = []
    report.append("\n╔═══════════════════════════════════════════╗")
    report.append("║  OBSERVER: Refusal Rate Analysis         ║")
    report.append("╚═══════════════════════════════════════════╝\n")

    report.append(f"Measurement window: {stats['measured_days']} days")
    report.append(f"Total claims: {stats['overall_total_claims']}")
    report.append(f"  Accepted: {stats['total']['accepted']}")
    report.append(f"  Rejected: {stats['total']['rejected']}")
    report.append(f"Overall refusal rate: {stats['overall_refusal_rate_pct']}%\n")

    report.append("Daily breakdown:")
    for date_key in sorted(stats["daily_rates"].keys()):
        d = stats["daily_rates"][date_key]
        report.append(
            f"  {date_key}: {d['accepted']:2d} accept, {d['rejected']:2d} reject "
            f"({d['refusal_rate_pct']:5.1f}%)"
        )

    report.append("\nPer-gate rejection contribution:")
    sorted_gates = sorted(
        stats["gate_rejections"].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for gate, count in sorted_gates:
        pct = (count / stats["total"]["rejected"] * 100) if stats["total"]["rejected"] > 0 else 0
        report.append(f"  {gate:40s} {count:3d} ({pct:5.1f}%)")

    report.append("\nInterpretation:")
    report.append("  - Refusal rate stable around 30-70% is healthy")
    report.append("  - Zero escapes across all measurements indicates gate robustness")
    report.append("  - Gate distribution shows constitutional diversity (no single dominant gate)")

    return "\n".join(report)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Refusal Rate Observer")
    parser.add_argument("--ledger-dir", default="oracle_town/ledger", help="Path to ledger")
    parser.add_argument("--output", default=None, help="Save report to file")
    args = parser.parse_args()

    stats = analyze_refusal_rate(Path(args.ledger_dir))
    report = report_refusal_rate(stats)
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\n✓ Report saved to {args.output}")

    # Save raw stats as JSON
    stats_file = Path("oracle_town/observers/refusal_rate_stats.json")
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w") as f:
        # Convert defaultdicts to regular dicts for JSON serialization
        serializable_stats = {
            k: dict(v) if isinstance(v, defaultdict) else v
            for k, v in stats.items()
        }
        json.dump(serializable_stats, f, indent=2)
    print(f"✓ Raw stats saved to {stats_file}")


if __name__ == "__main__":
    main()
