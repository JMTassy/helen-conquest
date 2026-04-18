#!/usr/bin/env python3
"""
ORACLE SUPERTEAM — Interactive Emulator

Easy-to-use testing environment for submitting claims and seeing verdicts.

Usage:
    python3 emulator.py                    # Interactive mode
    python3 emulator.py --scenario S-01    # Run specific test scenario
    python3 emulator.py --demo             # Run demo scenarios
"""

import sys
import json
from oracle.engine import run_oracle
from oracle.logger import get_logger

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

logger = get_logger()

# ==============================================================================
# INTERACTIVE EMULATOR
# ==============================================================================

class OracleEmulator:
    """Interactive testing environment for ORACLE SUPERTEAM."""

    def __init__(self):
        self.logger = get_logger()
        self.history = []

    def print_header(self, text: str):
        """Print styled header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

    def print_verdict(self, manifest: dict):
        """Print verdict with color coding."""
        decision = manifest['decision']
        verdict = decision['final']
        ship = decision['ship_permitted']

        # Color based on verdict
        if ship:
            color = Colors.GREEN
            symbol = "✓"
        else:
            color = Colors.RED
            symbol = "✗"

        print(f"\n{color}{Colors.BOLD}{symbol} VERDICT: {verdict}{Colors.END}")
        print(f"   Ship Permitted: {Colors.BOLD}{ship}{Colors.END}")
        print(f"   Reason Codes: {', '.join(decision['reason_codes'])}")

        # Show blocking details
        derived = manifest['derived']
        if derived['kill_switch_triggered']:
            print(f"\n{Colors.RED}🛑 KILL SWITCH ACTIVATED{Colors.END}")
            print(f"   By: {', '.join(derived['kill_switch_by'])}")

        if derived['obligations_open']:
            print(f"\n{Colors.YELLOW}⚠️  BLOCKING OBLIGATIONS:{Colors.END}")
            for i, ob in enumerate(derived['obligations_open'], 1):
                print(f"   {i}. [{ob['type']}] {ob['closure_criteria']}")
                print(f"      Owner: {ob['owner_team']}")

        if derived['contradictions']:
            print(f"\n{Colors.RED}⚠️  CONTRADICTIONS DETECTED:{Colors.END}")
            for c in derived['contradictions']:
                print(f"   • {c['rule_id']} (Severity: {c.get('severity', 'UNKNOWN')})")

        # Show score
        qi = derived['qi_int']
        print(f"\n{Colors.CYAN}📊 QI-INT Score: {qi['S_c']:.4f}{Colors.END}")
        print(f"   Amplitude: Re={qi['A_c']['re']:.4f}, Im={qi['A_c']['im']:.4f}")

    def quick_claim(self, assertion: str, tier: str = "Tier I"):
        """Quick claim submission for testing."""
        self.print_header("Quick Claim Submission")

        print(f"Assertion: {assertion}")
        print(f"Tier: {tier}\n")

        # Gather evidence
        print("Add evidence tags (comma-separated, or press Enter to skip):")
        tags_input = input("> ").strip()
        tags = [t.strip() for t in tags_input.split(",")] if tags_input else []

        # Gather signals
        signals = []
        print("\nAdd team signals (or press Enter to finish):")
        print("Format: TeamName,SignalType,Rationale")
        print("Example: Engineering Wing,OBLIGATION_OPEN,Need metrics")
        print("Available signal types: OBLIGATION_OPEN, RISK_FLAG, EVIDENCE_WEAK, KILL_REQUEST\n")

        while True:
            signal_input = input("Signal> ").strip()
            if not signal_input:
                break

            parts = [p.strip() for p in signal_input.split(",", 2)]
            if len(parts) < 3:
                print(f"{Colors.RED}Invalid format. Try: TeamName,SignalType,Rationale{Colors.END}")
                continue

            team, sig_type, rationale = parts

            # Legacy: convert to vote format for now (until full V2 integration)
            vote_mapping = {
                "OBLIGATION_OPEN": "CONDITIONAL",
                "RISK_FLAG": "OBJECT",
                "EVIDENCE_WEAK": "QUARANTINE",
                "KILL_REQUEST": "KILL",
            }

            vote = vote_mapping.get(sig_type, "CONDITIONAL")

            signals.append({
                "team": team,
                "vote": vote,
                "rationale": rationale
            })

        # Build payload
        payload = {
            "scenario_id": f"emulator-{len(self.history)+1}",
            "claim": {
                "id": f"claim-emu-{len(self.history)+1}",
                "assertion": assertion,
                "tier": tier,
                "domain": ["test"],
                "owner_team": "Emulator"
            },
            "evidence": [{
                "id": "ev-001",
                "type": "test_evidence",
                "tags": tags
            }] if tags else [],
            "votes": signals
        }

        # Run oracle
        print(f"\n{Colors.CYAN}Running ORACLE SUPERTEAM...{Colors.END}")
        manifest = run_oracle(payload)

        # Display result
        self.print_verdict(manifest)

        # Save to history
        self.history.append(manifest)

        print(f"\n{Colors.CYAN}RunManifest ID: {manifest['run_id']}{Colors.END}")

        return manifest

    def run_scenario(self, scenario_id: str):
        """Run a specific test vault scenario."""
        self.print_header(f"Running Test Scenario: {scenario_id}")

        import os
        scenario_path = f"test_vault/scenarios/{scenario_id.lower().replace('s-', '').zfill(2)}_*.json"

        # Find matching scenario file
        import glob
        files = glob.glob(scenario_path)

        if not files:
            print(f"{Colors.RED}Scenario not found: {scenario_id}{Colors.END}")
            return

        with open(files[0], 'r') as f:
            scenario = json.load(f)

        print(f"Description: {scenario['description']}\n")

        # Build payload
        payload = {
            "scenario_id": scenario['scenario_id'],
            "claim": scenario['claim'],
            "evidence": scenario.get('evidence', []),
            "votes": scenario.get('votes', [])
        }

        # Run
        manifest = run_oracle(payload)

        # Display
        self.print_verdict(manifest)

        # Compare with expected
        expected = scenario.get('expected', {})
        if expected:
            exp_verdict = expected['decision']['final']
            actual_verdict = manifest['decision']['final']

            if exp_verdict == actual_verdict:
                print(f"\n{Colors.GREEN}✓ Verdict matches expected: {exp_verdict}{Colors.END}")
            else:
                print(f"\n{Colors.RED}✗ Verdict mismatch!{Colors.END}")
                print(f"   Expected: {exp_verdict}")
                print(f"   Actual: {actual_verdict}")

    def run_demo(self):
        """Run demo scenarios."""
        self.print_header("ORACLE SUPERTEAM — Demo Mode")

        demos = [
            {
                "name": "✅ Successful Approval",
                "assertion": "Deploy OAuth 2.0 authentication",
                "tier": "Tier I",
                "evidence_tags": ["verified", "security_tested"],
                "votes": [
                    {"team": "Engineering Wing", "vote": "APPROVE", "rationale": "Tests passing"},
                    {"team": "Security Sector", "vote": "APPROVE", "rationale": "Audit complete"},
                    {"team": "Legal Office", "vote": "APPROVE", "rationale": "Compliant"}
                ]
            },
            {
                "name": "⚠️  Quarantine (Missing Evidence)",
                "assertion": "AI improves engagement by 40%",
                "tier": "Tier I",
                "evidence_tags": ["preliminary"],
                "votes": [
                    {"team": "Engineering Wing", "vote": "CONDITIONAL", "rationale": "Need A/B test"},
                    {"team": "Data Validation Office", "vote": "CONDITIONAL", "rationale": "Need verified metrics"}
                ]
            },
            {
                "name": "🛑 Kill-Switch (Privacy Violation)",
                "assertion": "Anonymous user tracking with biometrics",
                "tier": "Tier I",
                "evidence_tags": ["anonymous_claim", "biometric", "face"],
                "votes": [
                    {"team": "Legal Office", "vote": "KILL", "rationale": "GDPR contradiction"}
                ]
            }
        ]

        for i, demo in enumerate(demos, 1):
            self.print_header(f"Demo {i}: {demo['name']}")

            payload = {
                "scenario_id": f"demo-{i}",
                "claim": {
                    "id": f"claim-demo-{i}",
                    "assertion": demo['assertion'],
                    "tier": demo['tier'],
                    "domain": ["demo"],
                    "owner_team": "Demo"
                },
                "evidence": [{
                    "id": "ev-demo",
                    "type": "demo_evidence",
                    "tags": demo['evidence_tags']
                }],
                "votes": demo['votes']
            }

            manifest = run_oracle(payload)
            self.print_verdict(manifest)

            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.END}")

    def interactive_menu(self):
        """Main interactive menu."""
        while True:
            self.print_header("ORACLE SUPERTEAM — Emulator")

            print("1. Quick Claim Submission")
            print("2. Run Test Scenario")
            print("3. Run Demo Scenarios")
            print("4. View History")
            print("5. Exit")

            choice = input(f"\n{Colors.BOLD}Select option: {Colors.END}").strip()

            if choice == "1":
                assertion = input("\nClaim assertion: ").strip()
                if assertion:
                    self.quick_claim(assertion)
                else:
                    print(f"{Colors.RED}Assertion cannot be empty{Colors.END}")

            elif choice == "2":
                scenario_id = input("\nScenario ID (e.g., S-01): ").strip()
                if scenario_id:
                    self.run_scenario(scenario_id)

            elif choice == "3":
                self.run_demo()

            elif choice == "4":
                print(f"\n{Colors.CYAN}Run History:{Colors.END}")
                for i, m in enumerate(self.history, 1):
                    print(f"{i}. {m['claim']['assertion'][:50]}... → {m['decision']['final']}")

            elif choice == "5":
                print(f"\n{Colors.GREEN}Goodbye!{Colors.END}\n")
                break

            else:
                print(f"{Colors.RED}Invalid choice{Colors.END}")


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ORACLE SUPERTEAM Interactive Emulator")
    parser.add_argument("--scenario", help="Run specific test scenario (e.g., S-01)")
    parser.add_argument("--demo", action="store_true", help="Run demo scenarios")
    parser.add_argument("--quick", help="Quick claim assertion")

    args = parser.parse_args()

    emulator = OracleEmulator()

    if args.scenario:
        emulator.run_scenario(args.scenario)
    elif args.demo:
        emulator.run_demo()
    elif args.quick:
        emulator.quick_claim(args.quick)
    else:
        # Interactive mode
        emulator.interactive_menu()


if __name__ == "__main__":
    main()
