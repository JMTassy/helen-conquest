#!/usr/bin/env python3
"""
ORACLE TOWN — INS Module Implementation
Insight Clustering & Anomaly Detection (Deterministic)

Clusters observations into insight themes and detects anomalies.
No RNG, no timestamps (date-only), deterministic ordering.

Usage:
  python3 oracle_town/jobs/ins_cluster.py \
    --date 2026-01-30 \
    --run-id 174 \
    --observations artifacts/observations.json \
    --output artifacts/insights.json \
    --receipt artifacts/ins_receipt.json
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set
import hashlib


def normalize_text(text: str) -> str:
    """Strip whitespace, normalize newlines, remove control chars."""
    text = str(text).strip()
    text = text.replace('\t', ' ')  # tabs → spaces
    text = ' '.join(text.split())   # normalize internal whitespace
    return text


def load_observations(obs_file: Path) -> List[Dict[str, Any]]:
    """Load structured observations from OBS output."""
    try:
        with obs_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠ Error loading observations: {e}", file=sys.stderr)
        return []


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract deterministic keywords from text.

    Simple heuristic: split on whitespace, filter common words,
    pick longest remaining words (more likely to be meaningful).
    """
    # Common stop words
    stop_words = {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
        "if", "in", "is", "it", "of", "on", "or", "the", "to", "was",
        "will", "with", "this", "that", "from", "have", "has", "been",
        "been", "been", "do", "does", "did", "can", "could", "would",
        "should", "may", "might", "must", "shall", "get", "got", "make",
        "made", "see", "saw", "come", "came", "go", "went", "know", "knew"
    }

    words = text.lower().split()
    # Filter: no stop words, length > 3, alphanumeric
    candidates = [
        w.rstrip('.,;:!?') for w in words
        if w.lower() not in stop_words and len(w) > 3 and w.replace('-', '').isalnum()
    ]

    # Sort deterministically: by length (descending), then alphabetically
    candidates = sorted(set(candidates), key=lambda x: (-len(x), x))
    return candidates[:max_keywords]


def cluster_observations(observations: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Cluster observations by extracted keywords.

    Returns: {cluster_name: [obs_ids]}
    Deterministic: uses sorted keywords as cluster key.
    """
    clusters: Dict[str, List[str]] = {}

    for obs in observations:
        # Extract keywords from title + body
        title_keywords = extract_keywords(obs.get("title", ""), max_keywords=3)
        body_keywords = extract_keywords(obs.get("body", ""), max_keywords=4)

        # Combine and deduplicate
        all_keywords = sorted(set(title_keywords + body_keywords))

        # Create cluster key: first 2-3 keywords, sorted
        if all_keywords:
            cluster_key = "_".join(all_keywords[:2])  # Use first 2 keywords
        else:
            cluster_key = "uncategorized"

        # Add observation to cluster
        if cluster_key not in clusters:
            clusters[cluster_key] = []
        clusters[cluster_key].append(obs["id"])

    return clusters


def detect_anomalies(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect anomalies in observations.

    Heuristics:
    - LOW confidence (<0.8) + critical/incident tags → weak anomaly
    - Many tags (>3) + "incident"/"critical" → medium anomaly
    - Body length >400 chars + incident/outage → high anomaly

    Returns: List of {code, severity, obs_id, description}
    """
    anomalies = []

    for obs in observations:
        obs_id = obs["id"]
        title = obs.get("title", "").lower()
        body = obs.get("body", "").lower()
        tags = set(t.lower() for t in obs.get("tags", []))
        confidence = obs.get("confidence", 0.8)

        # Check 1: Low confidence + critical tags
        critical_tags = {"incident", "critical", "urgent", "high-priority"}
        if confidence < 0.8 and tags & critical_tags:
            anomalies.append({
                "code": "A1",
                "severity": "weak",
                "obs_id": obs_id,
                "description": f"Low confidence ({confidence}) with critical tags: {', '.join(tags & critical_tags)}"
            })

        # Check 2: Many tags + critical
        if len(tags) > 3 and ("incident" in tags or "critical" in tags):
            anomalies.append({
                "code": "A2",
                "severity": "medium",
                "obs_id": obs_id,
                "description": f"High tag complexity ({len(tags)} tags) with critical classification"
            })

        # Check 3: Long body + incident/outage keywords
        body_length = len(obs.get("body", ""))
        incident_keywords = {"outage", "timeout", "fail", "error", "crash", "down", "unavailable"}
        if body_length > 400 and any(kw in body for kw in incident_keywords):
            anomalies.append({
                "code": "A3",
                "severity": "high",
                "obs_id": obs_id,
                "description": f"Large incident description ({body_length} chars) with system failure indicators"
            })

        # Check 4: Mentions of customer impact
        if "customer" in body or "user" in body:
            if any(kw in body for kw in {"affected", "impact", "lost", "downtime"}):
                anomalies.append({
                    "code": "A4",
                    "severity": "medium",
                    "obs_id": obs_id,
                    "description": "Observable customer/user impact detected"
                })

    return anomalies


def structure_insights(observations: List[Dict[str, Any]],
                      date: str,
                      run_id: int) -> List[Dict[str, Any]]:
    """
    Transform observations into insights and anomalies.

    Returns: List of insight dicts, sorted by ID (determinism).
    """
    insights = []

    # Cluster observations
    clusters = cluster_observations(observations)

    # Generate insight for each cluster
    for cluster_idx, (cluster_name, obs_ids) in enumerate(sorted(clusters.items())):
        # Generate deterministic insight ID
        id_input = f"{date}:{run_id}:{cluster_name}".encode('utf-8')
        id_hash = hashlib.sha256(id_input).hexdigest()[:16]
        insight_id = f"ins_{date.replace('-','')}_{id_hash}"

        # Gather observations in this cluster
        cluster_obs = [obs for obs in observations if obs["id"] in obs_ids]

        # Aggregate tags
        all_tags = set()
        for obs in cluster_obs:
            all_tags.update(obs.get("tags", []))

        # Aggregate confidence (average)
        avg_confidence = sum(obs.get("confidence", 0.8) for obs in cluster_obs) / len(cluster_obs) if cluster_obs else 0.8

        # Create insight summary
        insight = {
            "id": insight_id,
            "date": date,
            "run_id": run_id,
            "cluster": cluster_name,
            "observation_count": len(obs_ids),
            "observation_ids": sorted(obs_ids),  # Deterministic order
            "theme": f"Cluster: {cluster_name.replace('_', ' ').title()}",
            "tags": sorted(all_tags),  # Deduplicated, sorted
            "avg_confidence": round(avg_confidence, 2),
            "links": []
        }

        insights.append(insight)

    # Detect anomalies
    anomalies = detect_anomalies(observations)

    # Add anomalies to insights list
    for anom_idx, anom in enumerate(sorted(anomalies, key=lambda x: x["obs_id"])):
        # Generate deterministic anomaly ID
        id_input = f"{date}:{run_id}:anomaly:{anom['code']}:{anom['obs_id']}".encode('utf-8')
        id_hash = hashlib.sha256(id_input).hexdigest()[:16]
        anom_id = f"anom_{date.replace('-','')}_{id_hash}"

        anomaly_insight = {
            "id": anom_id,
            "date": date,
            "run_id": run_id,
            "type": "anomaly",
            "code": anom["code"],
            "severity": anom["severity"],  # weak, medium, high
            "obs_id": anom["obs_id"],
            "description": anom["description"],
            "links": []
        }

        insights.append(anomaly_insight)

    # Sort by ID for determinism
    insights.sort(key=lambda x: x["id"])

    return insights


def create_receipt(insights: List[Dict[str, Any]],
                  run_id: int,
                  attestor_id: str = "ins_attestor_001") -> Dict[str, Any]:
    """
    Create a receipt structure for cryptographic signing.

    Note: actual ed25519 signing happens at a higher level (TRI/PUB).
    This creates the structure that would be signed.
    """
    # Serialize insights to canonical JSON for hashing
    insights_json = json.dumps(insights, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    insights_hash = hashlib.sha256(insights_json.encode('utf-8')).hexdigest()

    # Count insights and anomalies
    insights_count = len([i for i in insights if i.get("type") != "anomaly"])
    anomalies_count = len([i for i in insights if i.get("type") == "anomaly"])

    receipt = {
        "ins_receipt": {
            "insights_count": insights_count,
            "anomalies_count": anomalies_count,
            "insights_hash": f"sha256:{insights_hash}",
            "run_id": run_id,
            "attestor_id": attestor_id,
            "signature": "ed25519:PLACEHOLDER_SIGNATURE",
            "note": "Signature placeholder; actual signing by attestor_id required"
        }
    }
    return receipt


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ORACLE TOWN INS Module: Insight Clustering"
    )
    ap.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    ap.add_argument("--run-id", type=int, required=True, help="Sequential run ID")
    ap.add_argument("--observations", default="artifacts/observations.json", help="Input observations file")
    ap.add_argument("--output", default="artifacts/insights.json", help="Output insights file")
    ap.add_argument("--receipt", default="artifacts/ins_receipt.json", help="Output receipt file")
    ap.add_argument("--verbose", action="store_true", help="Verbose output")
    args = ap.parse_args()

    obs_file = Path(args.observations)
    output_file = Path(args.output)
    receipt_file = Path(args.receipt)

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    receipt_file.parent.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"[INS] Loading observations from: {obs_file}")

    # Load observations
    observations = load_observations(obs_file)

    if args.verbose:
        print(f"[INS] Loaded {len(observations)} observations")

    # Structure insights
    insights = structure_insights(observations, args.date, args.run_id)

    if args.verbose:
        cluster_count = len([i for i in insights if i.get("type") != "anomaly"])
        anom_count = len([i for i in insights if i.get("type") == "anomaly"])
        print(f"[INS] Structured {cluster_count} clusters + {anom_count} anomalies")
        for insight in insights[:3]:
            if insight.get("type") == "anomaly":
                print(f"      - {insight['id']}: ANOMALY {insight['code']} ({insight['severity']})")
            else:
                print(f"      - {insight['id']}: {insight['cluster']} ({insight['observation_count']} obs)")
        if len(insights) > 3:
            print(f"      ... and {len(insights) - 3} more")

    # Save insights
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(insights, f, sort_keys=True, indent=2, ensure_ascii=True)
        f.write("\n")

    if args.verbose:
        print(f"[INS] Insights saved: {output_file}")

    # Create receipt
    receipt = create_receipt(insights, args.run_id)

    # Save receipt
    with receipt_file.open("w", encoding="utf-8") as f:
        json.dump(receipt, f, sort_keys=True, indent=2, ensure_ascii=True)
        f.write("\n")

    if args.verbose:
        print(f"[INS] Receipt saved: {receipt_file}")
        print(f"[INS] Total insights: {len(insights)}")
        print("[INS] ✓ Complete")

    sys.exit(0)


if __name__ == "__main__":
    main()
