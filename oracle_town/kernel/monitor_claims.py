#!/usr/bin/env python3
"""
Monitor Claims: Watch ledger for OpenClaw activity

Tracks:
  - New claims submitted
  - Acceptance/rejection rates
  - Emerging patterns
  - Policy effectiveness

Run: python3 oracle_town/kernel/monitor_claims.py --since 24h
Or:  python3 oracle_town/kernel/monitor_claims.py --since today
Or:  python3 oracle_town/kernel/monitor_claims.py --all

Output: Structured report of claim patterns and K15 enforcement
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict


def parse_iso_date(date_str: str) -> datetime:
    """Parse ISO datetime string"""
    if "Z" in date_str:
        date_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(date_str)


def load_ledger_claims(ledger_root: Path, since_hours: int = None) -> List[Dict[str, Any]]:
    """Load claims from ledger, optionally filtered by recency"""
    claims = []

    if not ledger_root.exists():
        return claims

    cutoff_time = None
    if since_hours:
        cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)

    for year_dir in ledger_root.glob("*"):
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.glob("*"):
            if not month_dir.is_dir():
                continue
            for claim_dir in month_dir.glob("*"):
                if not claim_dir.is_dir():
                    continue

                # Try to load claim + receipt
                claim_file = claim_dir / "claim.json"
                receipt_file = claim_dir / "mayor_receipt.json" if (claim_dir / "mayor_receipt.json").exists() else claim_dir / "receipt.json"

                if claim_file.exists():
                    try:
                        with open(claim_file) as f:
                            claim_data = json.load(f)

                        claim_obj = claim_data.get("claim", {})
                        timestamp_str = claim_obj.get("timestamp", "")

                        # Filter by time if specified
                        if cutoff_time and timestamp_str:
                            try:
                                ts = parse_iso_date(timestamp_str)
                                if ts < cutoff_time:
                                    continue
                            except:
                                pass

                        # Load receipt if available
                        receipt = None
                        if receipt_file.exists():
                            try:
                                with open(receipt_file) as f:
                                    receipt_data = json.load(f)
                                    receipt = receipt_data.get("receipt", {})
                            except:
                                pass

                        claims.append({
                            "claim_id": claim_obj.get("id", claim_dir.name),
                            "timestamp": timestamp_str,
                            "type": claim_obj.get("type", "unknown"),
                            "source": claim_obj.get("source", "unknown"),
                            "intent": claim_obj.get("intent", ""),
                            "target": claim_obj.get("target", ""),
                            "decision": receipt.get("decision", "UNKNOWN") if receipt else "UNKNOWN",
                            "reason": receipt.get("reason", "") if receipt else "",
                            "world_mutation_allowed": receipt.get("world_mutation_allowed", False) if receipt else False
                        })
                    except Exception as e:
                        pass

    return sorted(claims, key=lambda c: c.get("timestamp", ""), reverse=True)


def analyze_claims(claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze claim patterns"""
    analysis = {
        "total_claims": len(claims),
        "accepted": 0,
        "rejected": 0,
        "unknown": 0,
        "acceptance_rate": 0.0,
        "by_source": defaultdict(lambda: {"total": 0, "accepted": 0, "rejected": 0}),
        "by_type": defaultdict(lambda: {"total": 0, "accepted": 0, "rejected": 0}),
        "rejection_reasons": defaultdict(int)
    }

    for claim in claims:
        decision = claim.get("decision", "UNKNOWN")
        source = claim.get("source", "unknown")
        claim_type = claim.get("type", "unknown")
        reason = claim.get("reason", "")

        # Count decisions
        if decision == "ACCEPT":
            analysis["accepted"] += 1
        elif decision == "REJECT":
            analysis["rejected"] += 1
        else:
            analysis["unknown"] += 1

        # By source
        analysis["by_source"][source]["total"] += 1
        if decision == "ACCEPT":
            analysis["by_source"][source]["accepted"] += 1
        elif decision == "REJECT":
            analysis["by_source"][source]["rejected"] += 1

        # By type
        analysis["by_type"][claim_type]["total"] += 1
        if decision == "ACCEPT":
            analysis["by_type"][claim_type]["accepted"] += 1
        elif decision == "REJECT":
            analysis["by_type"][claim_type]["rejected"] += 1

        # Rejection reasons
        if decision == "REJECT" and reason:
            analysis["rejection_reasons"][reason] += 1

    # Calculate acceptance rate
    total_decided = analysis["accepted"] + analysis["rejected"]
    if total_decided > 0:
        analysis["acceptance_rate"] = (analysis["accepted"] / total_decided) * 100

    return analysis


def print_report(claims: List[Dict[str, Any]], analysis: Dict[str, Any], title: str = "CLAIM MONITORING REPORT"):
    """Print formatted monitoring report"""
    print()
    print("╔" + "═" * 78 + "╗")
    print(f"║  {title:76s}  ║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Summary statistics
    print("SUMMARY")
    print("-" * 80)
    print(f"Total claims:        {analysis['total_claims']}")
    print(f"Accepted:            {analysis['accepted']} ({analysis['acceptance_rate']:.1f}%)")
    print(f"Rejected:            {analysis['rejected']}")
    print(f"Unknown/Pending:     {analysis['unknown']}")
    print()

    # By source
    if analysis["by_source"]:
        print("BY SOURCE")
        print("-" * 80)
        for source, stats in sorted(analysis["by_source"].items()):
            rate = (stats["accepted"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"{source:20s} | Total: {stats['total']:3d} | Accept: {stats['accepted']:3d} | Reject: {stats['rejected']:3d} | Rate: {rate:5.1f}%")
        print()

    # By type
    if analysis["by_type"]:
        print("BY TYPE")
        print("-" * 80)
        for claim_type, stats in sorted(analysis["by_type"].items()):
            rate = (stats["accepted"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"{claim_type:20s} | Total: {stats['total']:3d} | Accept: {stats['accepted']:3d} | Reject: {stats['rejected']:3d} | Rate: {rate:5.1f}%")
        print()

    # Top rejection reasons
    if analysis["rejection_reasons"]:
        print("TOP REJECTION REASONS")
        print("-" * 80)
        for reason, count in sorted(analysis["rejection_reasons"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"{count:3d}x {reason}")
        print()

    # Recent claims
    if claims:
        print("RECENT CLAIMS (Last 10)")
        print("-" * 80)
        for claim in claims[:10]:
            decision_icon = "✓" if claim["decision"] == "ACCEPT" else "✗" if claim["decision"] == "REJECT" else "?"
            timestamp = claim.get("timestamp", "?")[:16]
            source = claim.get("source", "?")[:15]
            target = claim.get("target", "?")[:40]
            print(f"{decision_icon} {timestamp} | {source:15s} | {target:40s} | {claim['decision']}")
        print()

    # K15 verification
    print("K15 ENFORCEMENT VERIFICATION")
    print("-" * 80)
    if analysis["rejected"] > 0:
        print(f"✓ K15 ACTIVE: {analysis['rejected']} claim(s) blocked by authority")
    else:
        print("⚠ K15 NOT ACTIVE: No rejections recorded (check policy)")

    if analysis["accepted"] > 0 and analysis["rejected"] > 0:
        print(f"✓ DISCRIMINATION WORKING: System accepts safe claims, rejects unsafe ones")
    elif analysis["accepted"] > 0:
        print("⚠ ALL CLAIMS ACCEPTED: Policy may be too permissive")
    elif analysis["rejected"] > 0:
        print("⚠ ALL CLAIMS REJECTED: Policy may be too restrictive")

    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor OpenClaw claims in ledger")
    parser.add_argument("--ledger", default="oracle_town/ledger", help="Ledger root directory")
    parser.add_argument("--since", default="24h", help="Show claims since (24h, today, 7d, or 'all')")
    parser.add_argument("--format", default="text", choices=["text", "json"], help="Output format")

    args = parser.parse_args()

    ledger_root = Path(args.ledger).resolve()

    # Parse --since argument
    since_hours = None
    if args.since != "all":
        if args.since == "today":
            since_hours = 24
        elif args.since == "24h":
            since_hours = 24
        elif args.since == "7d":
            since_hours = 168
        elif args.since == "30d":
            since_hours = 720
        else:
            try:
                since_hours = int(args.since)
            except:
                since_hours = 24

    # Load and analyze
    claims = load_ledger_claims(ledger_root, since_hours=since_hours)
    analysis = analyze_claims(claims)

    # Output
    if args.format == "json":
        # Prepare JSON-safe version
        json_output = {
            "timestamp": datetime.utcnow().isoformat(),
            "since_hours": since_hours,
            "summary": {
                "total": analysis["total_claims"],
                "accepted": analysis["accepted"],
                "rejected": analysis["rejected"],
                "acceptance_rate": analysis["acceptance_rate"]
            },
            "by_source": dict(analysis["by_source"]),
            "by_type": dict(analysis["by_type"]),
            "recent_claims": claims[:10]
        }
        print(json.dumps(json_output, indent=2, default=str))
    else:
        print_report(claims, analysis, title=f"CLAIM MONITORING REPORT (since {args.since})")


if __name__ == "__main__":
    main()
