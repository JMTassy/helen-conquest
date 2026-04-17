#!/usr/bin/env python3
"""
ORACLE TOWN — OS Runner (Job Graph Orchestrator)

Executes the daily job pipeline:
  1. Rotate state (prev → prev, current → prev)
  2. Run jobs in dependency order (OBS → INS → BRF → TRI → PUB || MEM || EVO)
  3. Render HOME + diff
  4. Report status

This runner is deterministic and replayable. All jobs must be pure functions
with no side effects except writing to designated artifact directories.

Usage:
  python3 oracle_town/os_runner.py --date 2026-01-30 --run-id 174 --mode daily
"""

from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save JSON file with canonical formatting."""
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, indent=2, ensure_ascii=True)
        f.write("\n")


def rotate_state(state_dir: Path) -> None:
    """Rotate state: current → prev, clear current."""
    current = state_dir / "city_current.json"
    prev = state_dir / "city_prev.json"

    if current.exists():
        # Copy current → prev
        prev_data = load_json(current)
        save_json(prev, prev_data)
        print(f"✓ Rotated state: run {prev_data.get('run_id')} → prev")
    else:
        print("⚠ No current state to rotate (first run?)")


def initialize_current_state(state_dir: Path, date: str, run_id: int, mode: str) -> Dict[str, Any]:
    """Create initial city_current.json for this run."""
    state = {
        "alerts": [],
        "anomalies": [],
        "artifacts": [],
        "date": date,
        "mode": mode,
        "modules": {
            "OBS": {"status": "OFF", "progress": 0, "desc": ""},
            "INS": {"status": "OFF", "progress": 0, "desc": ""},
            "BRF": {"status": "OFF", "progress": 0, "desc": ""},
            "TRI": {"status": "OFF", "progress": 0, "desc": ""},
            "PUB": {"status": "OFF", "progress": 0, "desc": ""},
            "MEM": {"status": "OFF", "progress": 0, "desc": ""},
            "EVO": {"status": "OFF", "progress": 0, "desc": ""},
        },
        "one_bet": "",
        "queue": [],
        "run_id": run_id,
    }
    current = state_dir / "city_current.json"
    save_json(current, state)
    print(f"✓ Initialized state: run {run_id} on {date}")
    return state


def build_job_graph() -> List[Dict[str, Any]]:
    """Define the job DAG with dependencies."""
    return [
        {
            "name": "OBS_SCAN",
            "module": "OBS",
            "depends_on": [],
            "command": "python3 oracle_town/jobs/obs_scan.py",
            "blocking": True,  # Blocks if fails
        },
        {
            "name": "INS_CLUSTER",
            "module": "INS",
            "depends_on": ["OBS_SCAN"],
            "command": "python3 oracle_town/jobs/ins_cluster.py",
            "blocking": True,
        },
        {
            "name": "BRF_ONEPAGER",
            "module": "BRF",
            "depends_on": ["INS_CLUSTER"],
            "command": "python3 oracle_town/jobs/brf_onepager.py",
            "blocking": True,
        },
        {
            "name": "TRI_GATE",
            "module": "TRI",
            "depends_on": ["BRF_ONEPAGER"],
            "command": "python3 oracle_town/jobs/tri_gate.py",
            "blocking": True,  # K1: fail-closed
        },
        {
            "name": "PUB_DELIVERY",
            "module": "PUB",
            "depends_on": ["TRI_GATE"],
            "command": "python3 oracle_town/jobs/pub_delivery.py",
            "blocking": False,  # OK if skipped (if TRI=NO_SHIP)
        },
        {
            "name": "MEM_LINK",
            "module": "MEM",
            "depends_on": ["TRI_GATE"],  # Can run in parallel with PUB
            "command": "python3 oracle_town/jobs/mem_link.py",
            "blocking": False,
        },
        {
            "name": "EVO_ADJUST",
            "module": "EVO",
            "depends_on": ["TRI_GATE"],  # Can run in parallel
            "command": "python3 oracle_town/jobs/evo_adjust.py",
            "blocking": False,
        },
    ]


def run_job(job: Dict[str, Any], state_dir: Path, artifacts_dir: Path, date: str, run_id: int) -> bool:
    """Execute a job and update state."""
    print(f"  ⟳ Running {job['name']}...")

    # In a real implementation, this would:
    # 1. Subprocess the job command
    # 2. Poll for completion
    # 3. Check exit code
    # 4. Update city_current.json with module progress/status
    # 5. Verify artifacts produced + receipts signed

    # For now, stub: assume all jobs succeed
    print(f"    ✓ {job['name']} complete")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="ORACLE TOWN OS Runner")
    ap.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    ap.add_argument("--run-id", type=int, required=True, help="Sequential run ID")
    ap.add_argument("--mode", default="DAILY", help="Run mode (DAILY, SIM, etc.)")
    ap.add_argument("--state-dir", default="oracle_town/state", help="State directory")
    ap.add_argument("--artifacts-dir", default="artifacts", help="Artifacts directory")
    args = ap.parse_args()

    state_dir = Path(args.state_dir)
    artifacts_dir = Path(args.artifacts_dir)

    print(f"╔════════════════════════════════════════════════════════════════╗")
    print(f"║  ORACLE TOWN — Daily OS Run {args.run_id:06d}                      ║")
    print(f"║  Date: {args.date}  Mode: {args.mode}                          ║")
    print(f"╚════════════════════════════════════════════════════════════════╝")
    print()

    # 1. Rotate state
    print("[1] Rotating state...")
    rotate_state(state_dir)
    print()

    # 2. Initialize fresh state for this run
    print("[2] Initializing run state...")
    state = initialize_current_state(state_dir, args.date, args.run_id, args.mode)
    print()

    # 3. Build and execute job graph
    print("[3] Executing job graph...")
    jobs = build_job_graph()
    completed = set()
    failed = []

    for job in jobs:
        # Check dependencies
        deps_met = all(dep in completed for dep in job["depends_on"])

        if not deps_met:
            print(f"  ✗ {job['name']}: dependencies not met, skipping")
            if job["blocking"]:
                failed.append(job["name"])
            continue

        # Run job
        success = run_job(job, state_dir, artifacts_dir, args.date, args.run_id)

        if success:
            completed.add(job["name"])
        else:
            print(f"  ✗ {job['name']}: FAILED")
            if job["blocking"]:
                failed.append(job["name"])
                break

    print()
    print(f"[4] Summary")
    print(f"  Completed: {len(completed)}/{len(jobs)}")
    print(f"  Failed: {len(failed)}")

    if failed:
        print(f"  Blocked jobs: {', '.join(failed)}")
        sys.exit(1)

    print()
    print(f"╔════════════════════════════════════════════════════════════════╗")
    print(f"║  ✓ Run {args.run_id:06d} complete                                 ║")
    print(f"║  Ready for: render_home.py → diff_city.py → git commit        ║")
    print(f"╚════════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
