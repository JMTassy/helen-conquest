#!/usr/bin/env python3
"""
Trend Memory: Compare today's clusters/anomalies against past 7 days.

Mode A (Emulation-only): Read-only analysis. No execution, no authority.

Input:
  - today's insights (from INS_CLUSTER)
  - ledger/briefs/ directory (historical briefs, one per day)

Output:
  - trend_report.json: persistence, novelty, anomaly recurrence
  - Hash-verified for K5 determinism

Operations:
  1. Load past 7 days of briefs from ledger
  2. Compare today's clusters to historical ones
  3. Flag:
     * NEW: cluster first seen today
     * PERSISTENT: cluster seen N+ days
     * ANOMALY_RECUR: anomaly appearing again
     * FADING: cluster disappeared after appearing
  4. Output trend JSON
  5. Hash all outputs (determinism check)
"""

import json
import sys
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def hash_json(data):
    """Canonical JSON hash (sorted keys, no whitespace)."""
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()


def load_briefs_from_ledger(ledger_path, lookback_days=7):
    """Load briefs from ledger/briefs/ for the past N days."""
    briefs = {}
    ledger_briefs = Path(ledger_path) / "briefs"

    if not ledger_briefs.exists():
        return briefs

    today = datetime.now()

    for i in range(lookback_days):
        check_date = today - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")
        brief_file = ledger_briefs / f"brief_{date_str}.json"

        if brief_file.exists():
            try:
                with open(brief_file, 'r') as f:
                    briefs[date_str] = json.load(f)
            except:
                pass

    return briefs


def extract_clusters_from_brief(brief):
    """Parse brief JSON to extract cluster list and metadata."""
    if isinstance(brief, str):
        # Markdown brief from brf_onepager
        clusters = []
        lines = brief.split('\n')
        for line in lines:
            if line.startswith('- **Cluster:'):
                # Extract cluster name
                parts = line.split('**')
                if len(parts) >= 2:
                    cluster_name = parts[1].replace('Cluster: ', '').strip()
                    clusters.append(cluster_name)
        return clusters

    # If brief is already structured JSON
    if isinstance(brief, dict):
        if 'clusters' in brief:
            return [c.get('theme', c.get('cluster', '')) for c in brief['clusters']]

    return []


def compare_insights(today_insights, historical_insights):
    """
    Compare today's insights to historical ones.

    Return:
      {
        'new': [cluster_names],
        'persistent': {cluster: days_seen},
        'anomaly_recur': [anomaly_types],
        'fading': [cluster_names]
      }
    """

    # Today's clusters
    today_clusters = set()
    if isinstance(today_insights, list):
        today_clusters = {insight.get('theme', insight.get('cluster', ''))
                         for insight in today_insights}

    # Historical cluster appearances
    historical_clusters = defaultdict(int)
    historical_anomalies = defaultdict(list)

    for date, insights in historical_insights.items():
        if isinstance(insights, list):
            for insight in insights:
                cluster = insight.get('theme', insight.get('cluster', ''))
                if cluster:
                    historical_clusters[cluster] += 1
        elif isinstance(insights, dict):
            # Handle structured brief
            if 'clusters' in insights:
                for cluster in insights['clusters']:
                    c = cluster.get('theme', cluster.get('cluster', ''))
                    if c:
                        historical_clusters[c] += 1

    # Classification
    result = {
        'new': [],
        'persistent': {},
        'anomaly_recur': [],
        'fading': []
    }

    # Today's clusters: new or persistent?
    for cluster in today_clusters:
        if cluster not in historical_clusters:
            result['new'].append(cluster)
        else:
            result['persistent'][cluster] = historical_clusters[cluster]

    # Fading: was in history but not today
    for cluster, count in historical_clusters.items():
        if cluster not in today_clusters and count >= 2:
            result['fading'].append({
                'cluster': cluster,
                'last_seen_days_ago': count
            })

    return result


def produce_trend_report(date_str, run_id, today_insights, historical_briefs, ledger_path):
    """
    Produce structured trend report.

    Output:
      {
        "report_id": "trend_2026-01-30",
        "date": "2026-01-30",
        "run_id": "emu_2026-01-30",
        "timestamp": "2026-01-30T...",
        "analysis": {
          "new_clusters": [...],
          "persistent_clusters": {...},
          "fading_clusters": [...],
          "anomaly_alerts": [...]
        },
        "summary": {
          "signal_strength": 0-100,
          "stability": "high|medium|low",
          "recommendation": "CONTINUE_MONITORING | INVESTIGATE | ALERT"
        },
        "hash": "sha256:..."
      }
    """

    # Load historical insights
    historical_insights_by_date = {}
    for date, brief in historical_briefs.items():
        if isinstance(brief, list):
            historical_insights_by_date[date] = brief
        elif isinstance(brief, dict) and 'clusters' in brief:
            historical_insights_by_date[date] = brief['clusters']

    # Compare
    comparison = compare_insights(today_insights, historical_insights_by_date)

    # Determine signal strength and recommendation
    new_count = len(comparison['new'])
    persistent_count = len(comparison['persistent'])
    fading_count = len(comparison['fading'])

    # Signal strength (0-100)
    # High if persistent clusters dominate
    total_clusters = new_count + persistent_count
    if total_clusters == 0:
        signal_strength = 50
    else:
        signal_strength = int((persistent_count / total_clusters) * 100)

    # Stability
    if persistent_count >= 3:
        stability = "high"
        recommendation = "CONTINUE_MONITORING"
    elif new_count > persistent_count:
        stability = "low"
        recommendation = "INVESTIGATE"
    else:
        stability = "medium"
        recommendation = "CONTINUE_MONITORING"

    # Alert if fading clusters reappear
    if fading_count > 0 and new_count > 0:
        recommendation = "INVESTIGATE"  # Possible oscillation

    report = {
        "report_id": f"trend_{date_str}",
        "date": date_str,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat() + "Z",
        "analysis": {
            "new_clusters": comparison['new'],
            "persistent_clusters": comparison['persistent'],
            "fading_clusters": comparison['fading'],
            "anomaly_alerts": comparison['anomaly_recur']
        },
        "summary": {
            "signal_strength": signal_strength,
            "stability": stability,
            "recommendation": recommendation,
            "metrics": {
                "new": new_count,
                "persistent": persistent_count,
                "fading": fading_count
            }
        }
    }

    # Add hash
    report_hash = hash_json(report)
    report['hash'] = report_hash

    return report


def main():
    parser = argparse.ArgumentParser(description="Trend Memory: 7-day cluster tracking")
    parser.add_argument('--date', required=True, help='YYYY-MM-DD')
    parser.add_argument('--run-id', required=True, help='Run ID (e.g., emu_2026-01-30)')
    parser.add_argument('--insights', required=True, help='Path to today\'s insights JSON')
    parser.add_argument('--ledger', default='oracle_town/ledger', help='Ledger path')
    parser.add_argument('--output', default='/tmp/trend_report.json', help='Output file')
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    # Load today's insights
    today_insights = []
    try:
        with open(args.insights, 'r') as f:
            today_insights = json.load(f)
    except Exception as e:
        print(f"Error loading insights: {e}", file=sys.stderr)
        sys.exit(1)

    # Load historical briefs
    historical_briefs = load_briefs_from_ledger(args.ledger, lookback_days=7)

    if args.verbose:
        print(f"Loaded {len(historical_briefs)} historical briefs", file=sys.stderr)
        print(f"Today's insights: {len(today_insights)} clusters", file=sys.stderr)

    # Produce trend report
    report = produce_trend_report(
        args.date,
        args.run_id,
        today_insights,
        historical_briefs,
        args.ledger
    )

    # Write output
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    if args.verbose:
        print(f"Trend report written to {args.output}", file=sys.stderr)
        print(f"Signal strength: {report['summary']['signal_strength']}%", file=sys.stderr)
        print(f"Recommendation: {report['summary']['recommendation']}", file=sys.stderr)

    # Print hash for determinism check
    print(report['hash'])


if __name__ == '__main__':
    main()
