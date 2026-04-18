#!/usr/bin/env python3
"""
🚀 SUPERTEAM CLI - Interactive Mode
====================================
Test the 6-agent creative superteam with real-time feedback.

Usage:
    python superteam_cli.py                 # Interactive mode
    python superteam_cli.py "Your prompt"   # Direct execution
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from governance_wrapped_runner import GovernanceWrappedRunner

# Color codes for CLI output
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

def print_banner():
    """Print colorful banner."""
    print(f"""
{Colors.BOLD}{Colors.CYAN}
╔═══════════════════════════════════════════════════════════════╗
║                     🚀 SUPERTEAM CLI 🚀                       ║
║          ChatDev 2.0 ↔ Oracle Town Governance Pipeline        ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.END}
""")

def print_agent_intro():
    """Print the 6 agents introduction."""
    agents = [
        ("DAN_Lateral", "Unrestricted creative thinking", "🎨"),
        ("LIBRARIAN_Synth", "Cross-domain pattern matching", "📚"),
        ("POET_Metaphor", "Metaphorical insight generation", "✨"),
        ("HACKER_Sandbox", "Edge cases & vulnerabilities", "⚠️"),
        ("SAGE_Dialectic", "Thesis→Antithesis→Synthesis", "☯️"),
        ("DREAMER_Absurd", "Absurdist deconstruction", "🌀"),
    ]
    
    print(f"\n{Colors.BOLD}Meet the 6-Agent Superteam:{Colors.END}\n")
    for agent, desc, emoji in agents:
        print(f"  {emoji} {Colors.BOLD}{agent}{Colors.END}: {desc}")

def format_claim(claim: dict, index: int) -> str:
    """Format a single claim for display."""
    agent = claim.get("source_agent", "Unknown")
    claim_type = claim.get("claim_type", "unknown")
    content = claim.get("content", "")
    
    # Emoji mapping
    emoji_map = {
        "DAN_Lateral": "🎨",
        "LIBRARIAN_Synth": "📚",
        "POET_Metaphor": "✨",
        "HACKER_Sandbox": "⚠️",
        "SAGE_Dialectic": "☯️",
        "DREAMER_Absurd": "🌀",
    }
    
    emoji = emoji_map.get(agent, "💡")
    
    return f"""
  {Colors.BOLD}{emoji} Claim {index}: {agent}{Colors.END}
     Type: {claim_type}
     Content: {content[:100]}{'...' if len(content) > 100 else ''}"""

def format_proposal(proposal: dict, index: int) -> str:
    """Format a single proposal for display."""
    category = proposal.get("category", "unknown")
    synthesis = proposal.get("synthesis", "")
    num_agents = proposal.get("num_supporting_agents", 0)
    
    return f"""
  {Colors.BOLD}Proposal {index}: {category}{Colors.END}
     Synthesis: {synthesis[:100]}{'...' if len(synthesis) > 100 else ''}
     Supporting agents: {num_agents}"""

def display_results(results: dict):
    """Display pipeline results in readable format."""
    
    # Summary
    summary = results.get("execution_summary", {})
    print(f"\n{Colors.BOLD}{Colors.GREEN}═══ EXECUTION SUMMARY ═══{Colors.END}")
    print(f"  Task: {summary.get('task', 'N/A')[:80]}")
    print(f"  Agents engaged: {Colors.BOLD}{summary.get('agents_engaged', 0)}{Colors.END}")
    print(f"  Timestamp: {summary.get('timestamp', 'N/A')}")
    
    # Claims (All 6 agents)
    claims = results.get("claims", [])
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══ STAGE 2: CLAIMS FROM ALL 6 AGENTS ═══{Colors.END}")
    print(f"Total claims extracted: {Colors.BOLD}{len(claims)}{Colors.END}\n")
    
    for i, claim in enumerate(claims, 1):
        print(format_claim(claim, i))
    
    # Proposals (Compiled)
    proposals = results.get("proposals", [])
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══ STAGE 3: COMPILED PROPOSALS ═══{Colors.END}")
    print(f"Total proposals: {Colors.BOLD}{len(proposals)}{Colors.END}\n")
    
    for i, proposal in enumerate(proposals, 1):
        print(format_proposal(proposal, i))
    
    # Validation
    validation = results.get("validation", {})
    passed = validation.get("passed", [])
    rejected = validation.get("rejected", [])
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}═══ STAGE 4: VALIDATION RESULTS ═══{Colors.END}")
    print(f"  {Colors.GREEN}✅ Passed: {len(passed)}{Colors.END}")
    print(f"  {Colors.RED}❌ Rejected: {len(rejected)}{Colors.END}")
    
    if rejected:
        print(f"\n  {Colors.BOLD}Rejection reasons:{Colors.END}")
        for proposal in rejected:
            reasons = proposal.get("rejection_reasons", [])
            print(f"    • {proposal.get('proposal_id', '?')}: {', '.join(reasons)}")
    
    # Submission
    submission = results.get("submission", {})
    print(f"\n{Colors.BOLD}{Colors.GREEN}═══ STAGE 5: ORACLE SUBMISSION ═══{Colors.END}")
    print(f"  Proposals submitted: {Colors.BOLD}{submission.get('total_submitted', 0)}{Colors.END}")
    print(f"  Status: {Colors.GREEN}✅ Complete{Colors.END}")
    
    # Output location
    print(f"\n{Colors.BOLD}📁 Artifacts saved to:{Colors.END} results/")
    print(f"  (workflow.json, claims.json, proposals.json, validation.json, submission.json, summary.json)")

def interactive_mode():
    """Run in interactive mode."""
    print_banner()
    print_agent_intro()
    
    while True:
        print(f"\n{Colors.BOLD}{Colors.BLUE}─ Enter your prompt (or 'quit' to exit):{Colors.END}")
        prompt = input(f"{Colors.BOLD}> {Colors.END}").strip()
        
        if prompt.lower() in ["quit", "exit", "q"]:
            print(f"\n{Colors.YELLOW}Goodbye! 👋{Colors.END}")
            break
        
        if not prompt:
            print(f"{Colors.RED}Please enter a prompt.{Colors.END}")
            continue
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}⏳ Processing with 6 agents...{Colors.END}\n")
        
        try:
            runner = GovernanceWrappedRunner(
                yaml_file="governance_wrapped_lateral_thinking.yaml",
                output_dir="results"
            )
            
            results = runner.run(prompt)
            display_results(results)
            
        except Exception as e:
            print(f"{Colors.RED}❌ Error: {str(e)}{Colors.END}")
            print(f"Make sure governance_wrapped_lateral_thinking.yaml exists in the current directory.")

def direct_mode(prompt: str):
    """Run with direct prompt (non-interactive)."""
    print_banner()
    print_agent_intro()
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}Task:{Colors.END} {prompt}\n")
    print(f"{Colors.BOLD}{Colors.CYAN}⏳ Processing with 6 agents...{Colors.END}\n")
    
    try:
        runner = GovernanceWrappedRunner(
            yaml_file="governance_wrapped_lateral_thinking.yaml",
            output_dir="results"
        )
        
        results = runner.run(prompt)
        display_results(results)
        
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {str(e)}{Colors.END}")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="🚀 Superteam CLI - Test the 6-agent creative superteam",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python superteam_cli.py                              # Interactive mode
  python superteam_cli.py "Design AI governance"      # Direct execution
        """
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Task prompt for the superteam (if provided, runs in direct mode)"
    )
    
    args = parser.parse_args()
    
    if args.prompt:
        direct_mode(args.prompt)
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
