#!/usr/bin/env python3
"""
NPC DASHBOARD — Command-line interface for NPC observations

Purpose: Display what NPCs observe in real-time and historical context.
Scriptable, auditable, deterministic output.

Usage:
  python3 npc_dashboard_cli.py show-observations
  python3 npc_dashboard_cli.py show-metrics
  python3 npc_dashboard_cli.py show-history
  python3 npc_dashboard_cli.py show-amendment-eligibility
  python3 npc_dashboard_cli.py monitor <npc-type>
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class NPCDashboardCLI:
    """CLI interface for NPC observations."""

    def __init__(self, ledger_path: str = "oracle_town/ledger/observations"):
        self.ledger_path = Path(ledger_path)
        self.doctrine_version = "1.0"
        self.doctrine_hash = "sha256:6ba9551d6a17551a04a719b6f1539b9bae772c72fbb86053d3470607fd68a709"

    def load_observations(self) -> List[Dict]:
        """Load all NPC observations from ledger."""
        observations = []

        if not self.ledger_path.exists():
            return observations

        # Find all observation JSON files
        for obs_file in self.ledger_path.rglob("*.json"):
            try:
                with open(obs_file) as f:
                    data = json.load(f)
                    observations.append(data)
            except (json.JSONDecodeError, IOError):
                pass

        return sorted(observations, key=lambda x: x.get("report_timestamp", ""), reverse=True)

    def show_header(self, title: str):
        """Print formatted header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title:^70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

    def show_observations(self, args):
        """Display current NPC observations."""
        self.show_header("NPC OBSERVATIONS")

        observations = self.load_observations()

        if not observations:
            print(f"{Colors.YELLOW}No observations found in ledger.{Colors.RESET}")
            return

        # Get most recent report
        latest = observations[0] if observations else None
        if not latest:
            print(f"{Colors.YELLOW}No observations available.{Colors.RESET}")
            return

        report = latest

        print(f"Report Period: {Colors.BLUE}{report['report_period']['start']} → {report['report_period']['end']}{Colors.RESET}")
        print(f"Timestamp:     {Colors.BLUE}{report['report_timestamp']}{Colors.RESET}")
        print(f"Doctrine:      {Colors.BLUE}v{report['doctrine_version']}{Colors.RESET}")
        print(f"Duration:      {Colors.BLUE}{report['report_period']['duration_days']} days{Colors.RESET}")

        print(f"\n{Colors.BOLD}Observations:{Colors.RESET}")

        for obs in report.get("observations", []):
            npc_type = obs.get("npc_type")
            metric_id = obs.get("metric_id")
            measurement = obs.get("measurement", {})
            confidence = obs.get("confidence")

            color = {
                "HIGH": Colors.GREEN,
                "MEDIUM": Colors.YELLOW,
                "LOW": Colors.RED,
            }.get(confidence, Colors.RESET)

            print(f"\n  {Colors.BOLD}{npc_type.upper()}{Colors.RESET}")
            print(f"    Metric:      {metric_id}")
            print(f"    Measurement: {color}{measurement.get('value')} {measurement.get('unit', '')}{Colors.RESET}")
            print(f"    Confidence:  {color}{confidence}{Colors.RESET}")
            print(f"    Notes:       {obs.get('notes', 'N/A')}")

        print(f"\n{Colors.BOLD}Overall Health:{Colors.RESET}")
        meta = report.get("meta", {})
        overall = report.get("overall_assessment", {})
        print(f"  System Health:        {Colors.GREEN}{overall.get('system_health', 'UNKNOWN')}{Colors.RESET}")
        print(f"  Doctrine Adherence:   {Colors.GREEN}{overall.get('doctrine_adherence', 'UNKNOWN')}{Colors.RESET}")
        print(f"  Exception Creep:      {Colors.GREEN}Not detected{Colors.RESET if not overall.get('exception_creep_detected') else Colors.RED}Detected{Colors.RESET}")

    def show_metrics(self, args):
        """Display all NPC metrics by type."""
        self.show_header("NPC METRICS BY TYPE")

        observations = self.load_observations()

        if not observations:
            print(f"{Colors.YELLOW}No observations found.{Colors.RESET}")
            return

        latest = observations[0]
        metrics_by_type = {}

        for obs in latest.get("observations", []):
            npc_type = obs.get("npc_type")
            if npc_type not in metrics_by_type:
                metrics_by_type[npc_type] = []

            metrics_by_type[npc_type].append({
                "metric_id": obs.get("metric_id"),
                "measurement": obs.get("measurement"),
                "confidence": obs.get("confidence"),
            })

        npc_display_names = {
            "accuracy_watcher": "AccuracyWatcher (Verdict Alignment)",
            "speculation_tracker": "SpeculationTracker (Override Performance)",
            "pattern_detector": "PatternDetector (Doctrine Drift)",
            "risk_analyzer": "RiskAnalyzer (Exception Creep)",
        }

        for npc_type in sorted(metrics_by_type.keys()):
            display_name = npc_display_names.get(npc_type, npc_type)
            print(f"{Colors.BOLD}{display_name}{Colors.RESET}")

            for metric in metrics_by_type[npc_type]:
                measurement = metric.get("measurement", {})
                value = measurement.get("value")
                unit = measurement.get("unit", "")
                confidence = metric.get("confidence")

                color = {
                    "HIGH": Colors.GREEN,
                    "MEDIUM": Colors.YELLOW,
                    "LOW": Colors.RED,
                }.get(confidence, Colors.RESET)

                print(f"  • {metric['metric_id']}")
                print(f"    Value:      {color}{value}{' ' + unit if unit else ''}{Colors.RESET}")
                print(f"    Confidence: {color}{confidence}{Colors.RESET}")

            print()

    def show_history(self, args):
        """Display historical observation reports."""
        self.show_header("OBSERVATION HISTORY (90-Day Reports)")

        observations = self.load_observations()

        if not observations:
            print(f"{Colors.YELLOW}No historical observations found.{Colors.RESET}")
            return

        print(f"{Colors.BOLD}Available Reports:{Colors.RESET}\n")

        for i, obs in enumerate(observations, 1):
            period = obs.get("report_period", {})
            timestamp = obs.get("report_timestamp", "Unknown")
            health = obs.get("overall_assessment", {}).get("system_health", "Unknown")

            health_color = Colors.GREEN if health == "STABLE" else Colors.YELLOW

            print(f"{i}. {period.get('start')} → {period.get('end')}")
            print(f"   Reported: {timestamp}")
            print(f"   Health:   {health_color}{health}{Colors.RESET}")
            print(f"   NPCs:     {', '.join(obs.get('meta', {}).get('npc_types_reporting', []))}")
            print()

    def show_amendment_eligibility(self, args):
        """Show what NPC evidence could support amendments."""
        self.show_header("AMENDMENT ELIGIBILITY STATUS")

        observations = self.load_observations()

        if not observations:
            print(f"{Colors.YELLOW}No observations available.{Colors.RESET}")
            return

        latest = observations[0]
        npc_types = latest.get("meta", {}).get("npc_types_reporting", [])
        duration = latest.get("report_period", {}).get("duration_days", 0)

        print(f"{Colors.BOLD}Current Status:{Colors.RESET}")
        print(f"  NPC Types Reporting: {len(npc_types)} (require ≥2)")
        print(f"  Observation Window:  {duration} days (require ≥90)")
        print(f"  Doctrine Version:    {latest.get('doctrine_version')}")

        eligibility_status = "✗ NOT ELIGIBLE YET" if len(npc_types) < 2 or duration < 90 else "✓ POTENTIALLY ELIGIBLE"

        color = Colors.GREEN if "ELIGIBLE" in eligibility_status else Colors.YELLOW
        print(f"  Status:              {color}{eligibility_status}{Colors.RESET}")

        print(f"\n{Colors.BOLD}Requirements for Amendment Proposal:{Colors.RESET}")
        print(f"  ✓ ≥2 distinct NPC types:    {Colors.GREEN if len(npc_types) >= 2 else Colors.YELLOW}{'PASS' if len(npc_types) >= 2 else 'FAIL'}{Colors.RESET}")
        print(f"  ✓ ≥90 consecutive days:     {Colors.GREEN if duration >= 90 else Colors.YELLOW}{'PASS' if duration >= 90 else 'FAIL'}{Colors.RESET}")
        print(f"  ✓ Same doctrine section:    {Colors.YELLOW}(check in proposal){Colors.RESET}")

        print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
        if len(npc_types) < 2:
            print(f"  • Wait for additional NPC observations to gather")
        elif duration < 90:
            print(f"  • Wait {90 - duration} more days for observation window to close")
        else:
            print(f"  • Next observation period ends: {observations[-1].get('report_period', {}).get('end') if len(observations) > 1 else 'TBD'}")
            print(f"  • Gather evidence pointing to specific doctrine section")
            print(f"  • Fill AMENDMENT_A_TEMPLATE.md when evidence supports change")

    def show_silence(self, args):
        """Show periods where NPCs emitted nothing."""
        self.show_header("NPC SILENCE ANALYSIS")

        observations = self.load_observations()

        if not observations:
            print(f"{Colors.YELLOW}No observations found.{Colors.RESET}")
            return

        latest = observations[0]
        silence_obs = latest.get("meta", {}).get("silence_observations", [])

        if not silence_obs:
            print(f"{Colors.YELLOW}No periods of NPC silence recorded.{Colors.RESET}")
            print(f"\n{Colors.BOLD}Why silence matters:{Colors.RESET}")
            print("  • Silence = no anomalies detected")
            print("  • Silence is valid output (not absence of observation)")
            print("  • System is working normally when NPCs have nothing to report")
            return

        print(f"{Colors.BOLD}NPC Silence Periods:{Colors.RESET}\n")
        for silence in silence_obs:
            print(f"  • {silence['npc_type']}: {silence['period']}")
            print(f"    Reason: {silence['reason']}")
            print()

    def show_summary(self, args):
        """Show executive summary."""
        self.show_header("NPC DASHBOARD SUMMARY")

        observations = self.load_observations()

        if not observations:
            print(f"{Colors.YELLOW}No observations available.{Colors.RESET}")
            return

        latest = observations[0]

        print(f"{Colors.BOLD}Report:{Colors.RESET}")
        period = latest.get("report_period", {})
        print(f"  Window:    {period.get('start')} → {period.get('end')} ({period.get('duration_days')} days)")
        print(f"  Generated: {latest.get('report_timestamp')}")

        print(f"\n{Colors.BOLD}NPC Observations:{Colors.RESET}")
        for obs in latest.get("observations", []):
            print(f"  • {obs.get('npc_type')}: {obs.get('metric_id')}")

        print(f"\n{Colors.BOLD}System Health:{Colors.RESET}")
        overall = latest.get("overall_assessment", {})
        print(f"  Status:      {Colors.GREEN}{overall.get('system_health')}{Colors.RESET}")
        print(f"  Adherence:   {Colors.GREEN}{overall.get('doctrine_adherence')}{Colors.RESET}")
        print(f"  Exception:   {Colors.GREEN}Not detected{Colors.RESET if not overall.get('exception_creep_detected') else Colors.RED}Detected{Colors.RESET}")

        print(f"\n{Colors.BOLD}Next Observation Window:{Colors.RESET}")
        print(f"  Start: May 1, 2026")
        print(f"  End:   July 31, 2026")
        print(f"  Days:  92 days")

    def run(self):
        """Main CLI handler."""
        parser = argparse.ArgumentParser(
            description="NPC Dashboard — Terminal interface for NPC observations"
        )

        subparsers = parser.add_subparsers(dest="command", help="Command to run")

        subparsers.add_parser("show-observations", help="Display current NPC observations")
        subparsers.add_parser("show-metrics", help="Display all NPC metrics by type")
        subparsers.add_parser("show-history", help="Display historical 90-day reports")
        subparsers.add_parser("show-amendment-eligibility", help="Show amendment eligibility status")
        subparsers.add_parser("show-silence", help="Show periods of NPC silence")
        subparsers.add_parser("show-summary", help="Executive summary")

        args = parser.parse_args()

        if not args.command:
            self.show_summary(args)
            return

        command_map = {
            "show-observations": self.show_observations,
            "show-metrics": self.show_metrics,
            "show-history": self.show_history,
            "show-amendment-eligibility": self.show_amendment_eligibility,
            "show-silence": self.show_silence,
            "show-summary": self.show_summary,
        }

        handler = command_map.get(args.command)
        if handler:
            handler(args)
        else:
            print(f"{Colors.RED}Unknown command: {args.command}{Colors.RESET}")
            sys.exit(1)


if __name__ == "__main__":
    dashboard = NPCDashboardCLI()
    dashboard.run()
