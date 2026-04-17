#!/usr/bin/env python3
"""
MASTER OBSERVER RUNNER

Executes all read-only observers and produces integrated report.
Does not influence system. Pure measurement.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def run_observer(observer_script: str, args: list = None) -> tuple[str, bool]:
    """
    Run an observer script and capture output.

    Returns: (output_text, success)
    """
    if args is None:
        args = []

    try:
        cmd = ["python3", f"oracle_town/observers/{observer_script}"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout, result.returncode == 0
    except Exception as e:
        return f"Error running {observer_script}: {e}", False


def main():
    print("\n" + "=" * 60)
    print("ORACLE TOWN OBSERVERS — Integrated Measurement Run")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    observers = [
        ("observer_refusal_rate.py", []),
        ("observer_gate_firing.py", []),
        ("observer_determinism.py", ["--sample-size", "5"]),
    ]

    results = {}
    for observer_script, args in observers:
        print(f"\n[Running] {observer_script}...")
        output, success = run_observer(observer_script, args)
        print(output)
        results[observer_script] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }

    # Summary
    print("\n" + "=" * 60)
    print("OBSERVER SUMMARY")
    print("=" * 60)
    print(f"\nAll observers completed at {datetime.now().isoformat()}")
    print(f"Total observers run: {len(observers)}")
    successful = sum(1 for r in results.values() if r["success"])
    print(f"Successful: {successful}/{len(observers)}")

    # Save summary
    summary_file = Path("oracle_town/observers/observer_run_summary.json")
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "observers_run": len(observers),
            "results": results,
        }, f, indent=2)
    print(f"\n✓ Summary saved to {summary_file}")

    print("\n" + "=" * 60)
    print("OBSERVER STATUS: MEASUREMENT COMPLETE")
    print("=" * 60)
    print("\nKey insight:")
    print("  Observers measure without acting.")
    print("  They reveal system behavior but do not change it.")
    print("  This allows learning without reintroducing optimism bias.")


if __name__ == "__main__":
    main()
