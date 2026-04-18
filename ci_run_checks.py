#!/usr/bin/env python3
"""
CI runner for Oracle Town verification.

Runs the existing `oracle_town/VERIFY_ALL.sh` then runs a stricter determinism gate
by importing `oracle_town.core.replay` and invoking `replay_multiple_times` with
200 iterations per run. Exits non-zero on any failure.
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
os.environ.setdefault("PYTHONPATH", ROOT)

def run_verify_all():
    script = os.path.join(ROOT, "oracle_town", "VERIFY_ALL.sh")
    if not os.path.exists(script):
        print("VERIFY_ALL.sh not found; skipping shell verification step")
        return

    print("== Running oracle_town/VERIFY_ALL.sh ==")
    subprocess.check_call(["bash", script], cwd=ROOT)

def run_strict_determinism(iterations=200):
    print(f"== Running strict determinism: {iterations} iterations per run ==")
    try:
        # Import replay module and call replay_multiple_times for each run
        from oracle_town.core import replay as replay_mod

        run_dirs = [
            "oracle_town/runs/runA_no_ship_missing_receipts",
            "oracle_town/runs/runB_no_ship_fake_attestor",
            "oracle_town/runs/runC_ship_quorum_valid",
        ]

        for run_dir in run_dirs:
            result = replay_mod.replay_multiple_times(run_dir, iterations=iterations)
            if result.get("status") == "FAILED" or not result.get("deterministic"):
                print(f"Determinism check failed for {run_dir}: {result}")
                return 1

        print("All strict determinism checks passed")
        return 0

    except Exception as e:
        print("Error running strict determinism:", e)
        return 2

def main():
    try:
        run_verify_all()
    except subprocess.CalledProcessError as e:
        print("VERIFY_ALL.sh failed with exit code", e.returncode)
        sys.exit(e.returncode)

    code = run_strict_determinism(iterations=200)
    sys.exit(code)

if __name__ == '__main__':
    main()
