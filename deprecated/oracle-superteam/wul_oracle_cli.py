#!/usr/bin/env python3
"""
wul_oracle_cli.py

WUL-ORACLE Interactive CLI Emulator

Three Modes:
1. Test a claim (validate + evaluate)
2. Ask superteam to improve (with Mayor % evaluation)
3. Ask Mayor to ship (format: LaTeX, code, or text)

Implements complete governance pipeline:
- WUL-CORE validation
- Receipt gap computation
- Mayor decision
- Output formatting
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wul.validate import load_kernel, validate_token_tree, WULValidator
from wul import validate as wul_validate
from receipt.compute_gap import compute_receipt_gap, is_obligation_satisfied
from mayor.decide import compute_decision, emit_decision_with_meta, _hash_payload
from superteam.improve import propose_improvements, apply_improvements, ImprovementProposal


# ANSI color codes for CLI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 60}{Colors.END}\n")


def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'─' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'─' * 60}{Colors.END}")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


class WULOracleCLI:
    """Main CLI application."""

    def __init__(self):
        self.kernel = load_kernel()
        self.validator = WULValidator(self.kernel)
        self.current_claim = None
        self.current_token_tree = None
        self.current_tribunal = None
        self.current_attestations = None
        self.improvement_history = []

    def run(self):
        """Main CLI loop."""
        print_header("WUL-ORACLE Interactive CLI")
        print(f"{Colors.BOLD}Receipt-First Governance for Multi-Agent Systems{Colors.END}")
        print(f"{Colors.CYAN}Version: v0.1.0 | Paper: WUL_ORACLE_PAPER.tex{Colors.END}\n")

        while True:
            self.show_menu()
            choice = input(f"\n{Colors.BOLD}Select option (1-4):{Colors.END} ").strip()

            if choice == "1":
                self.mode_test_claim()
            elif choice == "2":
                self.mode_improve_claim()
            elif choice == "3":
                self.mode_mayor_ship()
            elif choice == "4":
                print_info("Exiting WUL-ORACLE CLI. Goodbye!")
                break
            else:
                print_error("Invalid option. Please choose 1-4.")

    def show_menu(self):
        """Display main menu."""
        print_section("MAIN MENU")
        print(f"{Colors.BOLD}1.{Colors.END} Test a Claim (validate + evaluate)")
        print(f"{Colors.BOLD}2.{Colors.END} Ask Superteam to Improve (with Mayor % evaluation)")
        print(f"{Colors.BOLD}3.{Colors.END} Ask Mayor to SHIP (format: LaTeX | Code | Text)")
        print(f"{Colors.BOLD}4.{Colors.END} Exit")

    def mode_test_claim(self):
        """Mode 1: Test a claim."""
        print_header("MODE 1: TEST A CLAIM")

        # Get claim input
        print(f"{Colors.CYAN}Enter claim (or 'example' for pre-loaded claim):{Colors.END}")
        claim_input = input("> ").strip()

        if claim_input.lower() == "example":
            claim = self.load_example_claim()
        else:
            claim = {"text": claim_input, "id": f"claim_{hashlib.md5(claim_input.encode()).hexdigest()[:8]}"}

        self.current_claim = claim

        print_info(f"Claim ID: {claim['id']}")
        print_info(f"Claim: {claim['text']}")

        # Build token tree
        print_section("Step 1: Build WUL Token Tree")
        token_tree = self.build_token_tree_from_claim(claim)
        self.current_token_tree = token_tree

        print(f"{Colors.CYAN}Token Tree:{Colors.END}")
        print(json.dumps(token_tree, indent=2))

        # Validate token tree
        print_section("Step 2: Validate Against WUL-CORE v0")
        result = self.validator.validate_token_tree(token_tree)

        print(f"Validation Result: {json.dumps(result.to_dict(), indent=2)}")

        if not result.ok:
            print_error(f"Validation FAILED: {result.reason}")
            print_warning("Fix validation errors before proceeding.")
            return
        else:
            print_success("Validation PASSED")
            print_success(f"  - Depth: {result.depth}/{self.validator.max_depth}")
            print_success(f"  - Nodes: {result.nodes}/{self.validator.max_nodes}")
            print_success(f"  - Has R15: {result.has_r15}")

        # Build tribunal
        print_section("Step 3: Build Tribunal Bundle")
        tribunal = self.build_tribunal_bundle(claim, token_tree)
        self.current_tribunal = tribunal

        print(f"Obligations: {len(tribunal['obligations'])}")
        for obl in tribunal['obligations']:
            severity_color = Colors.RED if obl['severity'] == 'HARD' else Colors.YELLOW
            print(f"  {severity_color}[{obl['severity']}]{Colors.END} {obl['name']} - {obl['type']}")

        # Simulate attestations
        print_section("Step 4: Simulate Attestations (Superteam)")
        attestations = self.simulate_attestations(tribunal)
        self.current_attestations = attestations

        print(f"Attestations received: {len(attestations['attestations'])}")

        # Compute receipt gap
        print_section("Step 5: Compute Receipt Gap")
        receipt_gap, missing = compute_receipt_gap(tribunal, attestations)

        print(f"{Colors.BOLD}Receipt Gap:{Colors.END} {receipt_gap}")

        if receipt_gap == 0:
            print_success("All HARD obligations satisfied!")
        else:
            print_error(f"{receipt_gap} HARD obligations unsatisfied:")
            for m in missing:
                print(f"  - {m['name']}: {m['reason_code']}")
                print(f"    {Colors.YELLOW}{m['detail']}{Colors.END}")

        # Build receipt payload
        receipt_payload = {
            "receipt_gap": receipt_gap,
            "missing_obligations": missing
        }

        # Policies
        policies = {
            "kill_switches_pass": True,
            "kill_switches": [
                {"name": "no_free_text", "status": "pass"},
                {"name": "bounded_structure", "status": "pass"}
            ]
        }

        # Compute Mayor decision
        print_section("Step 6: Mayor Decision")
        decision = compute_decision(tribunal, policies, receipt_payload)

        decision_status = decision["decision"]
        if decision_status == "SHIP":
            print_success(f"Decision: SHIP ✓")
        else:
            print_error(f"Decision: NO_SHIP")
            print_warning("Blocking reasons:")
            for block in decision["blocking"]:
                print(f"  [{block['code']}] {block['detail']}")

        # Store for improvement mode
        self.current_decision = decision

        print_section("Test Complete")
        print(f"Summary: {decision_status} | Receipt Gap: {receipt_gap} | Kill Switches: {'PASS' if policies['kill_switches_pass'] else 'FAIL'}")

    def mode_improve_claim(self):
        """Mode 2: Ask superteam to improve."""
        print_header("MODE 2: ASK SUPERTEAM TO IMPROVE")

        if not self.current_claim:
            print_error("No claim loaded. Please run Mode 1 first.")
            return

        print(f"Current Claim: {self.current_claim['text']}")
        print(f"Current Decision: {self.current_decision.get('decision', 'UNKNOWN')}")

        if self.current_decision.get('decision') == 'SHIP':
            print_success("Claim already passes! No improvement needed.")
            return

        print_section("Superteam Improvement Simulation")

        # Show current blocking reasons
        print(f"{Colors.YELLOW}Current blocking reasons:{Colors.END}")
        for block in self.current_decision.get("blocking", []):
            print(f"  [{block['code']}] {block['detail']}")

        # Generate improvements using superteam module
        print("\n" + Colors.CYAN + "Superteam is analyzing claim and generating improvements..." + Colors.END)

        improvements = propose_improvements(
            self.current_claim,
            self.current_tribunal,
            self.current_attestations,
            self.current_decision
        )

        print(f"\n{Colors.GREEN}Superteam proposed {len(improvements)} improvements:{Colors.END}\n")

        for i, imp in enumerate(improvements, 1):
            print(f"{Colors.BOLD}{i}. {imp.type}: {imp.target}{Colors.END}")
            print(f"   {imp.description}")
            print(f"   {Colors.CYAN}Expected impact:{Colors.END} {imp.impact}")
            print(f"   {Colors.GREEN}Mayor evaluation: {imp.mayor_score}% improvement{Colors.END}\n")

        # Ask user to apply
        apply = input(f"{Colors.BOLD}Apply improvements? (y/n):{Colors.END} ").strip().lower()

        if apply == 'y':
            print_section("Applying Improvements")

            # Apply improvements using superteam module
            improved_attestations = apply_improvements(
                self.current_attestations,
                improvements
            )

            # Recompute receipt gap
            receipt_gap, missing = compute_receipt_gap(self.current_tribunal, improved_attestations)

            print(f"{Colors.BOLD}New Receipt Gap:{Colors.END} {receipt_gap} (was: {self.current_decision.get('receipt_gap', 'N/A')})")

            # Recompute decision
            policies = {"kill_switches_pass": True}
            receipt_payload = {"receipt_gap": receipt_gap, "missing_obligations": missing}

            new_decision = compute_decision(self.current_tribunal, policies, receipt_payload)

            if new_decision["decision"] == "SHIP":
                print_success("✓ Improvements successful! Claim now ready to SHIP")
            else:
                print_warning(f"Improvements applied, but still NO_SHIP. Receipt gap: {receipt_gap}")

            # Update current state
            self.current_attestations = improved_attestations
            old_receipt_gap = self.current_decision.get('receipt_gap', 0)
            self.current_decision = new_decision
            self.improvement_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "improvements": [imp.to_dict() for imp in improvements],
                "receipt_gap_before": old_receipt_gap,
                "receipt_gap_after": receipt_gap
            })

    def mode_mayor_ship(self):
        """Mode 3: Ask Mayor to ship."""
        print_header("MODE 3: ASK MAYOR TO SHIP")

        if not self.current_claim or not self.current_decision:
            print_error("No claim or decision available. Run Mode 1 first.")
            return

        decision_status = self.current_decision.get("decision")

        if decision_status != "SHIP":
            print_error("Cannot ship: Decision is NO_SHIP")
            print_warning("Use Mode 2 to improve the claim first.")
            return

        print_success("Decision: SHIP ✓")
        print(f"Claim: {self.current_claim['text']}\n")

        # Choose format
        print(f"{Colors.CYAN}Select output format:{Colors.END}")
        print("1. LaTeX (formal specification)")
        print("2. Code (implementation)")
        print("3. Text (narrative edition)")

        format_choice = input(f"\n{Colors.BOLD}Format (1-3):{Colors.END} ").strip()

        print_section("Generating Shipment Artifact")

        if format_choice == "1":
            output = self.generate_latex_output(self.current_claim, self.current_decision)
            filename = "shipment.tex"
        elif format_choice == "2":
            output = self.generate_code_output(self.current_claim, self.current_decision)
            filename = "shipment.py"
        else:
            output = self.generate_text_output(self.current_claim, self.current_decision)
            filename = "shipment.txt"

        # Compute shipment hash
        shipment_hash = hashlib.sha256(output.encode('utf-8')).hexdigest()

        print_success(f"Shipment artifact generated: {filename}")
        print_info(f"SHA-256: {shipment_hash}")

        # Display output
        print_section(f"Shipment Output ({filename})")
        print(output)

        # Save option
        save = input(f"\n{Colors.BOLD}Save to file? (y/n):{Colors.END} ").strip().lower()

        if save == 'y':
            output_path = Path.cwd() / filename
            output_path.write_text(output, encoding='utf-8')
            print_success(f"Saved to: {output_path}")

            # Generate metadata
            meta = {
                "shipment_hash": shipment_hash,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "claim_id": self.current_claim['id'],
                "decision_record_hash": _hash_payload(self.current_decision),
                "format": filename.split('.')[-1]
            }

            meta_path = output_path.with_suffix('.meta.json')
            meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
            print_success(f"Metadata saved to: {meta_path}")

    # Helper methods

    def load_example_claim(self) -> Dict[str, Any]:
        """Load pre-configured example claim."""
        return {
            "id": "claim_example_001",
            "text": "The WUL-ORACLE system provides deterministic, auditable governance for multi-agent coordination through receipt-first verification.",
            "author": "researcher",
            "timestamp": "2026-01-16T20:00:00Z"
        }

    def build_token_tree_from_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Build WUL token tree from claim."""
        # Simple example: claim with objective return
        return {
            "D01": {  # CLAIM
                "R15": ["E02", "E03"]  # RETURNS_TO(ARTIFACT, OBJECTIVE)
            },
            "objective_return": {
                "R15": ["E02", "E03"]
            }
        }

    def build_tribunal_bundle(self, claim: Dict[str, Any], token_tree: Dict[str, Any]) -> Dict[str, Any]:
        """Build tribunal bundle with obligations."""
        return {
            "claim_id": claim['id'],
            "obligations": [
                {
                    "name": "wul_validation",
                    "type": "validation",
                    "severity": "HARD",
                    "expected_attestor": "wul_validator",
                    "description": "WUL-CORE v0 token tree validation"
                },
                {
                    "name": "determinism_check",
                    "type": "determinism",
                    "severity": "HARD",
                    "expected_attestor": "determinism_checker",
                    "description": "Cross-runtime determinism verification"
                },
                {
                    "name": "schema_validation",
                    "type": "schema",
                    "severity": "HARD",
                    "expected_attestor": "schema_validator",
                    "description": "JSON Schema 2020-12 validation"
                },
                {
                    "name": "documentation",
                    "type": "docs",
                    "severity": "SOFT",
                    "expected_attestor": "docs_team",
                    "description": "Documentation completeness"
                }
            ]
        }

    def simulate_attestations(self, tribunal: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate superteam attestations (partial for demo)."""
        # Simulate: first 2 HARD obligations satisfied, last HARD missing
        return {
            "attestations": [
                {
                    "obligation_name": "wul_validation",
                    "attestor": "wul_validator",
                    "attestation_valid": True,
                    "policy_match": 1,
                    "payload_hash": "abc123def456"
                },
                {
                    "obligation_name": "documentation",
                    "attestor": "docs_team",
                    "attestation_valid": True,
                    "policy_match": 1,
                    "payload_hash": "docs789"
                }
                # determinism_check and schema_validation missing
            ]
        }

    def generate_latex_output(self, claim: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Generate LaTeX shipment output."""
        return f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{amsmath,amssymb}}

\\title{{WUL-ORACLE Shipment: {claim['id']}}}
\\author{{Automated Shipment via Mayor}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle

\\section{{Claim}}
{claim['text']}

\\section{{Mayor Decision}}
\\textbf{{Decision:}} {decision['decision']}

\\textbf{{Receipt Gap:}} {decision['receipt_gap']}

\\textbf{{Kill Switches:}} {decision['kill_switches_pass']}

\\subsection{{Metadata}}
\\begin{{itemize}}
    \\item Mayor Version: {decision['metadata']['mayor_version']}
    \\item Tribunal Hash: \\texttt{{{decision['metadata']['tribunal_bundle_hash'][:16]}...}}
    \\item Receipt Root Hash: \\texttt{{{decision['metadata']['receipt_root_hash'][:16]}...}}
\\end{{itemize}}

\\section{{Conclusion}}
This claim has passed all governance gates and is certified for shipment under WUL-ORACLE constitutional framework.

\\end{{document}}
"""

    def generate_code_output(self, claim: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Generate code shipment output."""
        return f"""#!/usr/bin/env python3
\"\"\"
WUL-ORACLE Shipment: {claim['id']}

AUTO-GENERATED by Mayor Decision System
DO NOT EDIT - This is a certified governance artifact
\"\"\"

CLAIM_ID = "{claim['id']}"
CLAIM_TEXT = \"\"\"
{claim['text']}
\"\"\"

DECISION_RECORD = {{
    "decision": "{decision['decision']}",
    "receipt_gap": {decision['receipt_gap']},
    "kill_switches_pass": {decision['kill_switches_pass']},
    "metadata": {{
        "mayor_version": "{decision['metadata']['mayor_version']}",
        "tribunal_bundle_hash": "{decision['metadata']['tribunal_bundle_hash']}",
        "receipt_root_hash": "{decision['metadata']['receipt_root_hash']}"
    }}
}}

def verify_shipment():
    \"\"\"Verify this shipment artifact.\"\"\"
    assert DECISION_RECORD["decision"] == "SHIP", "Invalid shipment: not SHIP decision"
    assert DECISION_RECORD["receipt_gap"] == 0, "Invalid shipment: receipt gap > 0"
    assert DECISION_RECORD["kill_switches_pass"], "Invalid shipment: kill switches failed"
    return True

if __name__ == "__main__":
    if verify_shipment():
        print("✓ Shipment artifact verified")
    else:
        print("✗ Shipment verification failed")
"""

    def generate_text_output(self, claim: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """Generate text narrative shipment output."""
        return f"""
WUL-ORACLE SHIPMENT CERTIFICATION
═════════════════════════════════════════════════════════════

CLAIM ID: {claim['id']}

CLAIM STATEMENT:
{claim['text']}

GOVERNANCE EVALUATION
─────────────────────────────────────────────────────────────

Mayor Decision: {decision['decision']} ✓
Receipt Gap: {decision['receipt_gap']} (all HARD obligations satisfied)
Kill Switches: {'PASSED' if decision['kill_switches_pass'] else 'FAILED'}

CONSTITUTIONAL COMPLIANCE
─────────────────────────────────────────────────────────────

✓ Invariant 5.1 (No Silent Failures): Blocking array properly formed
✓ Invariant 5.2 (SHIP Implies Zero Gap): Receipt gap == 0
✓ Schema Validation: decision_record.schema.json (2020-12)
✓ Reason Code Allowlist: All codes from canonical registry

RECEIPT BINDING
─────────────────────────────────────────────────────────────

Mayor Version: {decision['metadata']['mayor_version']}
Tribunal Bundle Hash: {decision['metadata']['tribunal_bundle_hash']}
Policies Hash: {decision['metadata']['policies_hash']}
Receipt Root Hash: {decision['metadata']['receipt_root_hash']}

CERTIFICATION
─────────────────────────────────────────────────────────────

This claim has been evaluated under the WUL-ORACLE constitutional
framework and has passed all governance gates. The decision is
deterministic, auditable, and replayable.

Status: CERTIFIED FOR SHIPMENT
Generated: {datetime.utcnow().isoformat()}Z

═════════════════════════════════════════════════════════════
"""


def main():
    """Main entry point."""
    cli = WULOracleCLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user. Exiting...{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
