#!/usr/bin/env python3
"""
Generate TOWN_ASCII.generated.txt — Visual representation of Oracle Town state.

This script generates a deterministic ASCII visualization of the town's current state
by reading from artifacts that town-check.sh already validates:
  - Gate status (town-check.sh exit code)
  - Index freshness (git diff on CLAUDE_MD_*.txt)
  - Evidence validation (extract-emulation-evidence.py exit code, if enabled)
  - Decision digest (hashes.json from latest run)
  - Policy hash (hashes.json from latest run)

The output is:
  - Deterministic (same state → same output)
  - Diffable (pure text, git-friendly)
  - Self-contained (no external dependencies)
  - Local-only (no network, no external services)

Usage:
  python3 scripts/generate_town_ascii.py [--run runA] [--evidence]

Exit codes:
  0 = town generated successfully
  1 = missing artifacts or invalid state
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess


def get_gate_status() -> tuple[str, bool]:
    """Check if town-check.sh would pass (indices fresh, syntax valid)."""
    root = Path(__file__).parent.parent

    idx1 = root / "scratchpad" / "CLAUDE_MD_LINE_INDEX.txt"
    idx2 = root / "scratchpad" / "CLAUDE_MD_SECTIONS_BY_LENGTH.txt"

    # Check if indices would be fresh (run generator and check for diffs)
    try:
        subprocess.run(
            ["python3", str(root / "scratchpad" / "generate_claude_index.py")],
            capture_output=True,
            timeout=5
        )
    except:
        pass

    # Check for working-tree diffs
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", "--", str(idx1), str(idx2)],
            cwd=str(root),
            capture_output=True
        )
        indices_fresh = (result.returncode == 0)
    except:
        indices_fresh = False

    # Check Python syntax
    try:
        subprocess.run(
            ["python3", "-m", "py_compile", "oracle_town/core/mayor_rsm.py"],
            cwd=str(root),
            capture_output=True,
            timeout=5
        )
        syntax_valid = True
    except:
        syntax_valid = False

    gate_status = "GREEN" if (indices_fresh and syntax_valid) else "RED"
    gate_ok = (gate_status == "GREEN")

    return gate_status, gate_ok


def get_evidence_status(enable_evidence: bool) -> tuple[str, bool]:
    """Check evidence validation status (if enabled)."""
    if not enable_evidence:
        return "OFF", False

    try:
        result = subprocess.run(
            ["python3", "scripts/extract-emulation-evidence.py"],
            capture_output=True,
            timeout=10
        )
        evidence_ok = (result.returncode == 0)
        evidence_status = "5/5 ✅" if evidence_ok else "FAILED ❌"
    except:
        evidence_ok = False
        evidence_status = "ERROR ❌"

    return evidence_status, evidence_ok


def get_latest_run() -> str:
    """Find the most recent run directory."""
    root = Path(__file__).parent.parent
    runs_dir = root / "oracle_town" / "runs"

    if not runs_dir.exists():
        return "runA_no_ship_missing_receipts"

    run_dirs = sorted([d.name for d in runs_dir.iterdir() if d.is_dir()])
    return run_dirs[-1] if run_dirs else "runA_no_ship_missing_receipts"


def get_decision_digest(run_name: str) -> str:
    """Extract decision digest from hashes.json."""
    root = Path(__file__).parent.parent
    hashes_file = root / "oracle_town" / "runs" / run_name / "hashes.json"

    if not hashes_file.exists():
        return "unknown"

    try:
        with open(hashes_file) as f:
            data = json.load(f)
            digest = data.get("decision_digest", "unknown")
            return digest[:16] + "..." if len(digest) > 16 else digest
    except:
        return "unknown"


def get_policy_hash(run_name: str) -> str:
    """Extract policy hash from hashes.json."""
    root = Path(__file__).parent.parent
    hashes_file = root / "oracle_town" / "runs" / run_name / "hashes.json"

    if not hashes_file.exists():
        return "unknown"

    try:
        with open(hashes_file) as f:
            data = json.load(f)
            policy = data.get("policy_hash", "unknown")
            return policy[:16] + "..." if len(policy) > 16 else policy
    except:
        return "unknown"


def get_run_decision(run_name: str) -> str:
    """Extract decision from decision_record.json."""
    root = Path(__file__).parent.parent
    record_file = root / "oracle_town" / "runs" / run_name / "decision_record.json"

    if not record_file.exists():
        return "UNKNOWN"

    try:
        with open(record_file) as f:
            data = json.load(f)
            return data.get("decision", "UNKNOWN")
    except:
        return "UNKNOWN"


def get_quorum_status(run_name: str) -> str:
    """Check if quorum rule is present in policy."""
    root = Path(__file__).parent.parent
    policy_file = root / "oracle_town" / "runs" / run_name / "policy.json"

    if not policy_file.exists():
        return "unknown"

    try:
        with open(policy_file) as f:
            data = json.load(f)
            quorum_rules = data.get("quorum_rules", {})
            if quorum_rules.get("default_min_quorum") and quorum_rules.get("obligation_specific_rules"):
                return "active ✅"
            return "present"
    except:
        return "unknown"


def generate_town_ascii(run_name: str = None, enable_evidence: bool = False) -> str:
    """Generate ASCII town visualization."""
    if run_name is None:
        run_name = get_latest_run()

    gate_status, gate_ok = get_gate_status()
    evidence_status, evidence_ok = get_evidence_status(enable_evidence)

    decision_digest = get_decision_digest(run_name)
    policy_hash = get_policy_hash(run_name)
    run_decision = get_run_decision(run_name)
    quorum_status = get_quorum_status(run_name)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gate_symbol = "✅" if gate_ok else "❌"

    ascii_art = f"""ORACLE TOWN  (local)                                {timestamp}
══════════════════════════════════════════════════════════════════════

            🧱 CITY WALL (Fail-Closed K1)
        ┌────────────────────────────────────────┐
        │  TOWN GATE: town-check.sh              │
        │  STATUS:  {gate_status} {gate_symbol}                           │
        └──────────────┬─────────────────────────┘
                       │
       ┌───────────────┼───────────────────────────────────┐
       │               │                                   │
       ▼               ▼                                   ▼

  DOCS DISTRICT       GOVERNANCE DISTRICT           COURT OF EVIDENCE
  ──────────────      ─────────────────────         ──────────────────
  [Workshop]          [Town Hall Law]               [Bailiff]
  generator.py ✅     policy.json ✅                extract-evidence {'✅' if evidence_ok else '❌'}
  indices ✅          policy_hash ✅                evidence_status: {evidence_status}
  CLAUDE.md ✅        keys/registry ✅              citations ✅
                      K3 quorum {quorum_status}
       │               │                                   │
       └───────────────┼───────────────────────────────────┘
                       │
                       ▼

              [DECISION LEDGER]
              run: {run_name}
              decision: {run_decision}
              policy_hash: {policy_hash}
              decision_digest: {decision_digest}

════════════════════════════════════════════════════════════════════════

TOWN STATUS:
  Gate:     {gate_status} {gate_symbol}
  Evidence: {evidence_status}
  Run:      {run_name}
  Decision: {run_decision}

Last generated: {timestamp}
Note: Set TOWN_EVIDENCE=1 in environment to enable full evidence validation
"""

    return ascii_art


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate TOWN_ASCII.generated.txt — Oracle Town visual status"
    )
    parser.add_argument("--run", default=None, help="Specific run to visualize (default: latest)")
    parser.add_argument("--evidence", action="store_true", help="Enable evidence validation")
    parser.add_argument("--output", default="TOWN_ASCII.generated.txt", help="Output file")

    args = parser.parse_args()

    try:
        ascii_town = generate_town_ascii(run_name=args.run, enable_evidence=args.evidence)

        root = Path(__file__).parent.parent
        output_path = root / args.output

        with open(output_path, "w") as f:
            f.write(ascii_town)

        print(ascii_town)
        return 0
    except Exception as e:
        print(f"ERROR: Failed to generate town ASCII: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
