#!/usr/bin/env python3
"""
ORACLE TOWN Command Line Interface

Usage:
    python oracle-town/cli.py "Launch a marketing campaign..."
    python oracle-town/cli.py --domain=policy "Implement new GDPR policy..."
    python oracle-town/cli.py --interactive
"""
import sys
import asyncio
import argparse
from oracle_town.core.orchestrator import OracleTownOrchestrator
from oracle_town.schemas import TownInput


def print_banner():
    """Print ORACLE TOWN ASCII banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                     🏛️  ORACLE TOWN  🏛️                        ║
║          Hierarchical Multi-Agent Governance System          ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_verdict_summary(verdict):
    """Print formatted verdict summary"""
    decision_symbol = "✅" if verdict.decision == "SHIP" else "❌"

    print("\n" + "=" * 70)
    print(f"{decision_symbol} FINAL VERDICT: {verdict.decision}")
    print("=" * 70)
    print(f"Claim ID: {verdict.claim_id}")
    print(f"\nRationale:\n{verdict.rationale}")

    if verdict.blocking_reasons:
        print(f"\nBlocking Reasons ({len(verdict.blocking_reasons)}):")
        for i, reason in enumerate(verdict.blocking_reasons, 1):
            print(f"  {i}. {reason}")

    if verdict.remediation_roadmap:
        print(f"\n{'=' * 70}")
        print(f"REMEDIATION ROADMAP ({len(verdict.remediation_roadmap)} steps)")
        print("=" * 70)
        for i, step in enumerate(verdict.remediation_roadmap, 1):
            print(f"\n[Step {i}] {step.description}")
            print(f"  │ Effort: {step.estimated_effort.upper()}")
            print(f"  │ Timeline: {step.estimated_timeline}")
            print(f"  │ Responsible: {step.responsible}")
            if step.required_evidence:
                print(f"  │ Evidence: {', '.join(step.required_evidence)}")
            print(f"  └─ Success: {step.success_criteria[:80]}...")

    print(f"\n{'=' * 70}")
    if verdict.decision == "SHIP":
        print("✅ APPROVED - Claim may proceed to execution")
    else:
        print("❌ BLOCKED - Complete remediation roadmap to proceed")
    print("=" * 70)


async def process_claim(text: str, domain: str = "marketing"):
    """Process a single claim through ORACLE TOWN"""
    user_input = TownInput(
        raw_text=text,
        domain=domain,
        urgency="medium",
    )

    orchestrator = OracleTownOrchestrator()
    verdict = await orchestrator.process_input(user_input)

    return verdict


async def interactive_mode():
    """Interactive CLI mode"""
    print_banner()
    print("Interactive Mode - Type 'exit' to quit\n")

    while True:
        print("-" * 70)
        text = input("\n📝 Enter your claim (or 'exit' to quit):\n> ").strip()

        if text.lower() in ["exit", "quit", "q"]:
            print("\n👋 Goodbye!")
            break

        if not text:
            print("⚠️  Please enter a claim text")
            continue

        domain = input("📂 Domain [marketing/product/policy/event] (default: marketing):\n> ").strip()
        domain = domain if domain in ["marketing", "product", "policy", "event"] else "marketing"

        print("\n🏛️  Processing through ORACLE TOWN...")
        verdict = await process_claim(text, domain)

        print_verdict_summary(verdict)

        # Ask if user wants to continue
        cont = input("\n\nProcess another claim? [Y/n]: ").strip().lower()
        if cont == "n":
            print("\n👋 Goodbye!")
            break


async def batch_mode(claims_file: str):
    """Process multiple claims from a file"""
    print_banner()
    print(f"Batch Mode - Processing claims from {claims_file}\n")

    try:
        with open(claims_file, "r") as f:
            claims = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        print(f"Found {len(claims)} claims to process\n")

        results = []
        for i, claim_text in enumerate(claims, 1):
            print(f"\n[{i}/{len(claims)}] Processing: {claim_text[:60]}...")
            verdict = await process_claim(claim_text)
            results.append((claim_text, verdict))
            print(f"  → {verdict.decision}")

        # Summary
        print("\n" + "=" * 70)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 70)
        shipped = sum(1 for _, v in results if v.decision == "SHIP")
        blocked = len(results) - shipped

        print(f"Total: {len(results)} claims")
        print(f"✅ SHIP: {shipped}")
        print(f"❌ NO_SHIP: {blocked}")
        print(f"Success Rate: {shipped/len(results)*100:.1f}%")

    except FileNotFoundError:
        print(f"❌ Error: File '{claims_file}' not found")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="ORACLE TOWN CLI - Hierarchical Multi-Agent Governance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single claim
  python oracle-town/cli.py "Launch email campaign collecting user data"

  # Specify domain
  python oracle-town/cli.py --domain=policy "Implement GDPR compliance policy"

  # Interactive mode
  python oracle-town/cli.py --interactive

  # Batch processing
  python oracle-town/cli.py --batch=claims.txt
        """,
    )

    parser.add_argument(
        "claim",
        nargs="?",
        help="Claim text to process (if not using --interactive or --batch)",
    )

    parser.add_argument(
        "-d",
        "--domain",
        choices=["marketing", "product", "policy", "event"],
        default="marketing",
        help="Claim domain (default: marketing)",
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Start interactive mode",
    )

    parser.add_argument(
        "-b",
        "--batch",
        metavar="FILE",
        help="Process claims from file (one per line)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output (show all agent turns)",
    )

    args = parser.parse_args()

    # Determine mode
    if args.interactive:
        asyncio.run(interactive_mode())
    elif args.batch:
        asyncio.run(batch_mode(args.batch))
    elif args.claim:
        print_banner()
        verdict = asyncio.run(process_claim(args.claim, args.domain))
        print_verdict_summary(verdict)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
