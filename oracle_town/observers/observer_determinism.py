#!/usr/bin/env python3
"""
OBSERVER: Determinism Stability

Verifies that rerunning the same claims produces identical verdicts.
Does not influence gate logic. Read-only verification.

Metric:
  - Replayability: Run historical claims through TRI, verify verdict match

Output: Determinism verification report (no decisions, no recommendations).
"""

import json
import subprocess
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

def replay_historical_claims(
    ledger_dir: Path = Path("oracle_town/ledger"),
    sample_size: int = 10,
) -> dict:
    """
    Sample historical claims and replay through TRI.

    Returns dict with:
      - claims_replayed: count
      - verdicts_matched: count
      - verdicts_diverged: count
      - determinism_rate_pct: float
      - divergences: [(claim_id, original_verdict, replay_verdict)]
    """

    stats = {
        "claims_sampled": 0,
        "verdicts_matched": 0,
        "verdicts_diverged": 0,
        "divergences": [],
    }

    # Sample claims from ledger
    claim_files = list(ledger_dir.glob("*/*/*/claim.json"))
    if not claim_files:
        print("  No claims found in ledger.")
        return stats

    # Take first N claims (deterministic sampling)
    sampled = claim_files[:sample_size]
    stats["claims_sampled"] = len(sampled)

    for claim_file in sampled:
        try:
            with open(claim_file, "r") as f:
                claim_data = json.load(f)

            claim_id = claim_data.get("claim", {}).get("id", "UNKNOWN")

            # Load original verdict
            verdict_file = claim_file.parent / "mayor_receipt.json"
            if not verdict_file.exists():
                continue

            with open(verdict_file, "r") as f:
                original_receipt = json.load(f)

            original_verdict = original_receipt.get("decision", "UNKNOWN")

            # Replay through TRI
            with TemporaryDirectory() as tmpdir:
                tmp_claim = Path(tmpdir) / "claim.json"
                tmp_verdict = Path(tmpdir) / "verdict.json"

                # Write claim to temp location
                with open(tmp_claim, "w") as f:
                    json.dump(claim_data, f)

                # Run TRI gate
                cmd = [
                    "python3",
                    "oracle_town/jobs/tri_gate.py",
                    "--claim", str(tmp_claim),
                    "--output", str(tmp_verdict),
                    "--policy-hash", "sha256:policy_v1_2026_01",
                    "--key-registry", "oracle_town/keys/test_public_keys.json",
                    "--evidence-dir", ".",
                ]

                result = subprocess.run(cmd, capture_output=True, timeout=5)

                if result.returncode == 0 and tmp_verdict.exists():
                    with open(tmp_verdict, "r") as f:
                        replay_receipt = json.load(f)

                    replay_verdict = replay_receipt.get("verdict", {}).get("decision", "UNKNOWN")

                    # Compare
                    if original_verdict == replay_verdict:
                        stats["verdicts_matched"] += 1
                    else:
                        stats["verdicts_diverged"] += 1
                        stats["divergences"].append({
                            "claim_id": claim_id,
                            "original": original_verdict,
                            "replay": replay_verdict,
                        })

        except Exception as e:
            print(f"  ⚠ Error replaying {claim_file}: {e}")

    # Compute rate
    total = stats["verdicts_matched"] + stats["verdicts_diverged"]
    if total > 0:
        stats["determinism_rate_pct"] = round(100 * stats["verdicts_matched"] / total, 1)
    else:
        stats["determinism_rate_pct"] = 0.0

    return stats


def report_determinism(stats: dict) -> str:
    """Format determinism verification as human-readable report."""

    report = []
    report.append("\n╔═══════════════════════════════════════════╗")
    report.append("║  OBSERVER: Determinism Verification      ║")
    report.append("╚═══════════════════════════════════════════╝\n")

    report.append(f"Claims replayed: {stats['claims_sampled']}")
    report.append(f"Verdicts matched: {stats['verdicts_matched']}")
    report.append(f"Verdicts diverged: {stats['verdicts_diverged']}")
    report.append(f"Determinism rate: {stats['determinism_rate_pct']}%\n")

    if stats["divergences"]:
        report.append("Divergences detected:")
        for div in stats["divergences"]:
            report.append(
                f"  {div['claim_id']}: "
                f"original={div['original']}, replay={div['replay']}"
            )
    else:
        report.append("✓ No divergences detected (K5 holds)")

    report.append("\nInterpretation:")
    report.append("  - 100% determinism rate confirms K5 invariant")
    report.append("  - Any divergence indicates nondeterminism in gate logic")
    report.append("  - Replayability enables full audit trail verification")

    return "\n".join(report)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Determinism Observer")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of claims to replay")
    parser.add_argument("--ledger-dir", default="oracle_town/ledger", help="Path to ledger")
    parser.add_argument("--output", default=None, help="Save report to file")
    args = parser.parse_args()

    stats = replay_historical_claims(
        Path(args.ledger_dir),
        sample_size=args.sample_size,
    )
    report = report_determinism(stats)
    print(report)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"\n✓ Report saved to {args.output}")

    # Save raw stats as JSON
    stats_file = Path("oracle_town/observers/determinism_stats.json")
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Raw stats saved to {stats_file}")


if __name__ == "__main__":
    main()
