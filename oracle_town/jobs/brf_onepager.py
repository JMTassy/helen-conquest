#!/usr/bin/env python3
"""
ORACLE TOWN — BRF Module Implementation
Brief Synthesis & One-Bet Statement (Deterministic)

Synthesizes insights into a brief narrative with a single "ONE BET" statement.
ONE BET: Single-sentence summary of highest-confidence hypothesis (≤100 chars).
No RNG, no timestamps (date-only), deterministic ordering.

Usage:
  python3 oracle_town/jobs/brf_onepager.py \
    --date 2026-01-30 \
    --run-id 174 \
    --insights artifacts/insights.json \
    --output artifacts/brief.md \
    --one-bet artifacts/one_bet.txt \
    --receipt artifacts/brf_receipt.json
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import hashlib


def normalize_text(text: str) -> str:
    """Strip whitespace, normalize newlines, remove control chars."""
    text = str(text).strip()
    text = text.replace('\t', ' ')  # tabs → spaces
    text = ' '.join(text.split())   # normalize internal whitespace
    return text


def load_insights(insights_file: Path) -> List[Dict[str, Any]]:
    """Load structured insights from INS output."""
    try:
        with insights_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Error loading insights: {e}", file=sys.stderr)
        return []


def select_high_anomalies(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter to HIGH severity anomalies only."""
    return [
        i for i in insights
        if i.get("type") == "anomaly" and i.get("severity") == "high"
    ]


def select_clusters(insights: List[Dict[str, Any]], max_clusters: int = 3) -> List[Dict[str, Any]]:
    """Select top clusters by observation count and confidence."""
    clusters = [i for i in insights if i.get("type") != "anomaly"]
    # Sort by: high confidence first, then observation count
    clusters.sort(
        key=lambda x: (-x.get("avg_confidence", 0.5), -x.get("observation_count", 0))
    )
    return clusters[:max_clusters]


def generate_one_bet(insights: List[Dict[str, Any]],
                     high_anomalies: List[Dict[str, Any]]) -> str:
    """
    Generate a single "ONE BET" statement.

    Strategy:
    1. If high anomalies exist: "HIGH: [anomaly cluster]"
    2. Otherwise: "SIGNAL: [top cluster theme]"
    3. Keep ≤100 characters
    """
    if high_anomalies:
        # Summarize high anomalies
        anom_codes = sorted(set(a.get("code") for a in high_anomalies))
        return f"HIGH: Critical anomalies detected ({', '.join(anom_codes)})."[:100]
    else:
        # Pick the most confident cluster
        clusters = select_clusters(insights, max_clusters=1)
        if clusters:
            theme = clusters[0].get("theme", "No clear signal").replace("Cluster: ", "")
            return f"SIGNAL: {theme}."[:100]
        else:
            return "NEUTRAL: Insufficient data for high-confidence bet."[:100]


def generate_brief_markdown(insights: List[Dict[str, Any]],
                           date: str,
                           run_id: int,
                           high_anomalies: List[Dict[str, Any]]) -> str:
    """
    Generate brief markdown narrative.

    Structure:
    - Title with date/run
    - Summary of clusters
    - Anomalies section (if any)
    - Recommendation section
    """
    lines = []

    # Header
    lines.append(f"# ORACLE TOWN Brief — Run {run_id:06d}")
    lines.append(f"**Date:** {date}")
    lines.append("")

    # High-level summary
    clusters = select_clusters(insights, max_clusters=3)
    lines.append("## Key Clusters")
    if clusters:
        for cluster in clusters:
            theme = cluster.get("theme", "Unknown")
            obs_count = cluster.get("observation_count", 0)
            avg_conf = cluster.get("avg_confidence", 0.5)
            lines.append(f"- **{theme}** ({obs_count} obs, conf: {avg_conf:.0%})")
    else:
        lines.append("- No significant clusters detected")
    lines.append("")

    # Anomalies section
    if high_anomalies:
        lines.append("## ⚠ HIGH Severity Anomalies")
        for anom in sorted(high_anomalies, key=lambda x: x.get("id", "")):
            code = anom.get("code", "?")
            description = anom.get("description", "Unknown issue")
            lines.append(f"- **{code}**: {description}")
        lines.append("")
    else:
        anomalies = [i for i in insights if i.get("type") == "anomaly"]
        if anomalies:
            lines.append("## 📋 Medium/Low Severity Anomalies")
            for anom in sorted(anomalies, key=lambda x: x.get("severity", ""), reverse=True)[:5]:
                code = anom.get("code", "?")
                severity = anom.get("severity", "unknown").upper()
                description = anom.get("description", "Unknown issue")
                lines.append(f"- **{code}** [{severity}]: {description}")
            lines.append("")

    # Recommendation
    lines.append("## 🎯 Recommendation")
    if high_anomalies:
        lines.append("**ACTION REQUIRED**: High-severity anomalies detected. Review and remediate.")
    elif clusters:
        top_cluster = clusters[0].get("theme", "signals")
        lines.append(f"**MONITOR**: {top_cluster}. Continue observation and analysis.")
    else:
        lines.append("**NEUTRAL**: Insufficient data for actionable recommendation.")
    lines.append("")

    # Metadata
    lines.append("---")
    lines.append(f"_Insights: {len([i for i in insights if i.get('type') != 'anomaly'])} clusters, "
                 f"{len([i for i in insights if i.get('type') == 'anomaly'])} anomalies_")

    return "\n".join(lines)


def create_receipt(brief_text: str,
                  one_bet: str,
                  insights_count: int,
                  anomalies_count: int,
                  run_id: int,
                  attestor_id: str = "brf_attestor_001") -> Dict[str, Any]:
    """
    Create a receipt structure for cryptographic signing.
    """
    # Create canonical payload
    payload = {
        "brief": brief_text[:200],  # First 200 chars of brief
        "one_bet": one_bet,
        "insights_count": insights_count,
        "anomalies_count": anomalies_count,
        "run_id": run_id
    }

    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()

    receipt = {
        "brf_receipt": {
            "brief_hash": f"sha256:{payload_hash}",
            "one_bet_length": len(one_bet),
            "run_id": run_id,
            "attestor_id": attestor_id,
            "signature": "ed25519:PLACEHOLDER_SIGNATURE",
            "note": "Signature placeholder; actual signing by attestor_id required"
        }
    }
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ORACLE TOWN BRF Module: Brief Synthesis"
    )
    ap.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    ap.add_argument("--run-id", type=int, required=True, help="Sequential run ID")
    ap.add_argument("--insights", default="artifacts/insights.json", help="Input insights file")
    ap.add_argument("--output", default="artifacts/brief.md", help="Output brief markdown file")
    ap.add_argument("--one-bet", default="artifacts/one_bet.txt", help="Output ONE BET text file")
    ap.add_argument("--receipt", default="artifacts/brf_receipt.json", help="Output receipt file")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    args = ap.parse_args()

    insights_file = Path(args.insights)
    output_file = Path(args.output)
    onebet_file = Path(args.one_bet)
    receipt_file = Path(args.receipt)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    onebet_file.parent.mkdir(parents=True, exist_ok=True)
    receipt_file.parent.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"[BRF] Loading insights from: {insights_file}")

    # Load insights
    insights = load_insights(insights_file)

    if args.verbose:
        print(f"[BRF] Loaded {len(insights)} insights")

    # Select high anomalies
    high_anomalies = select_high_anomalies(insights)

    if args.verbose and high_anomalies:
        print(f"[BRF] Found {len(high_anomalies)} HIGH anomalies")

    # Generate ONE BET
    one_bet = generate_one_bet(insights, high_anomalies)

    if len(one_bet) > 100:
        one_bet = one_bet[:100].rsplit(' ', 1)[0] + "."

    # Generate brief
    brief_text = generate_brief_markdown(insights, args.date, args.run_id, high_anomalies)

    if args.verbose:
        print(f"[BRF] Generated brief ({len(brief_text)} chars)")
        print(f"[BRF] ONE BET: {one_bet}")

    # Save brief
    with output_file.open("w", encoding="utf-8") as f:
        f.write(brief_text)
        f.write("\n")

    if args.verbose:
        print(f"[BRF] Brief saved: {output_file}")

    # Save ONE BET
    with onebet_file.open("w", encoding="utf-8") as f:
        f.write(one_bet)
        f.write("\n")

    if args.verbose:
        print(f"[BRF] ONE BET saved: {onebet_file}")

    # Create receipt
    insights_count = len([i for i in insights if i.get("type") != "anomaly"])
    anomalies_count = len([i for i in insights if i.get("type") == "anomaly"])
    receipt = create_receipt(brief_text, one_bet, insights_count, anomalies_count, args.run_id)

    # Save receipt
    with receipt_file.open("w", encoding="utf-8") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=True)
        f.write("\n")

    if args.verbose:
        print(f"[BRF] Receipt saved: {receipt_file}")
        print("[BRF] ✓ Complete")

    sys.exit(0)


if __name__ == "__main__":
    main()
