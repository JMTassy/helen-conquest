#!/usr/bin/env python3
"""
Live Monitor for Oracle Town

Real-time visualization of jurisdiction state as observations flow through
the Daily OS pipeline. Shows how the town is built moment by moment.

No interpretation, no prediction, no helpful inference.
Just the structure emerging from evidence.
"""

import sys
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, deque

# Import renderers
import importlib.util
spec_ascii = importlib.util.spec_from_file_location("city_state_renderer",
    Path(__file__).parent / "city_state_renderer.py")
renderer_ascii = importlib.util.module_from_spec(spec_ascii)
spec_ascii.loader.exec_module(renderer_ascii)

spec_iso = importlib.util.spec_from_file_location("iso_coaster_renderer",
    Path(__file__).parent / "iso_coaster_renderer.py")
renderer_iso = importlib.util.module_from_spec(spec_iso)
spec_iso.loader.exec_module(renderer_iso)


class LiveMonitor:
    """Real-time jurisdiction state monitor."""

    def __init__(self):
        self.verdicts = deque(maxlen=500)
        self.observations = deque(maxlen=100)
        self.insights = deque(maxlen=10)
        self.last_update = datetime.utcnow()
        self.state_version = 0

    def load_verdicts_from_ledger(self, ledger_path: str):
        """Load existing verdicts from ledger (if present)."""
        ledger_dir = Path(ledger_path)
        if not ledger_dir.exists():
            return

        # Scan ledger for all mayor_receipt.json files
        for receipt_file in sorted(ledger_dir.glob("*/*/*/mayor_receipt.json")):
            try:
                with open(receipt_file) as f:
                    receipt = json.load(f)
                    verdict = {
                        "receipt_id": receipt.get("receipt_id", "unknown"),
                        "decision": receipt.get("decision", "UNKNOWN"),
                        "timestamp": receipt.get("timestamp", ""),
                        "policy_version": receipt.get("policy_version", ""),
                    }
                    self.verdicts.append(verdict)
            except:
                pass

    def simulate_observation_cycle(self):
        """Simulate an observation batch arriving."""
        now = datetime.utcnow()
        timestamp = now.isoformat() + "Z"

        # Simulate 1-3 new observations
        import random
        num_observations = random.randint(1, 3)

        observation_types = [
            "email_summary",
            "meeting_note",
            "metric_spike",
            "incident_report",
            "manual_input",
        ]

        for _ in range(num_observations):
            obs_type = random.choice(observation_types)
            obs = {
                "type": obs_type,
                "timestamp": timestamp,
                "content": f"Observation: {obs_type}",
            }
            self.observations.append(obs)

        # Simulate some verdicts being issued
        if random.random() > 0.6:  # 40% chance of new verdict
            decision = random.choice(["ACCEPT", "REJECT"])
            verdict = {
                "receipt_id": f"R-{len(self.verdicts):04d}",
                "decision": decision,
                "timestamp": timestamp,
                "policy_version": "v7",
            }
            self.verdicts.append(verdict)

        # Simulate insights being generated
        if len(self.verdicts) >= 5 and random.random() > 0.7:
            accept_rate = sum(
                1 for v in self.verdicts if v.get("decision") == "ACCEPT"
            ) / len(self.verdicts)
            insight = f"Acceptance rate: {accept_rate*100:.1f}%"
            if insight not in self.insights:
                self.insights.append(insight)

        self.state_version += 1
        self.last_update = now

    def build_city_state(self) -> dict:
        """Construct current CityState from accumulated verdicts."""
        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "run_id": f"live-monitor",
            "policy": {"version": "v7", "hash": "sha256:current"},
            "verdicts": {
                "accepted": sum(
                    1 for v in self.verdicts if v.get("decision") == "ACCEPT"
                ),
                "rejected": sum(
                    1 for v in self.verdicts if v.get("decision") == "REJECT"
                ),
            },
            "modules": {
                "OBS": {
                    "status": "OK" if len(self.observations) > 0 else "OFF"
                },
                "INSIGHT": {"status": "OK" if len(self.insights) > 0 else "OFF"},
                "MEMORY": {"status": "OK"},
                "BRIEF": {"status": "OK"},
                "TRI": {"status": "OK"},
                "PUBLISH": {"status": "OK" if len(self.verdicts) > 0 else "OFF"},
            },
            "top_insights": list(self.insights)[-3:],
        }

    def render_ascii(self) -> str:
        """Render ASCII snapshot."""
        city_state = self.build_city_state()
        return renderer_ascii.render_city_state(city_state)

    def render_html(self) -> str:
        """Render HTML iso-coaster."""
        city_state = self.build_city_state()
        return renderer_iso.render_iso_coaster(city_state)

    def display_cycle(self):
        """Display current state in terminal."""
        city_state = self.build_city_state()
        print("\n" + "="*60)
        print("ORACLE TOWN — LIVE MONITOR")
        print("="*60)
        print(f"State: {self.state_version} | Time: {self.last_update.strftime('%H:%M:%S')}")
        print(f"Observations: {len(self.observations)} | Verdicts: {len(self.verdicts)} | Insights: {len(self.insights)}")
        print()
        print(self.render_ascii())
        print()
        print("Recent verdicts:")
        for v in list(self.verdicts)[-5:]:
            symbol = "✓" if v.get("decision") == "ACCEPT" else "✗"
            print(f"  {symbol} {v.get('receipt_id', '?')}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Oracle Town Live Monitor"
    )
    parser.add_argument("--ledger", default="oracle_town/ledger")
    parser.add_argument("--cycles", type=int, default=10, help="Number of cycles to run")

    args = parser.parse_args()

    monitor = LiveMonitor()
    monitor.load_verdicts_from_ledger(args.ledger)

    print("Oracle Town Live Monitor")
    print(f"Starting with {len(monitor.verdicts)} verdicts from ledger")
    print()

    for cycle in range(args.cycles):
        monitor.simulate_observation_cycle()
        monitor.display_cycle()

    print()
    print("Monitor complete")
