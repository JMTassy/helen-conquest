#!/usr/bin/env python3
"""
wul_oracle_emulator_complete.py

Complete WUL-ORACLE Interactive Emulator (3 modes exactly as specified)

Implements:
1. Test a claim (WUL validate → tribunal → Mayor decision)
2. Ask superteam to improve (proposals + Mayor % evaluation + apply)
3. Ask Mayor to ship (LaTeX/code/text with deterministic payload + meta)

All components integrated: WUL-CORE, receipt gap, Mayor purity, shipment generation
"""

from __future__ import annotations

import json
import sys
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime, timezone
import platform

# Add src to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from wul.validate import load_kernel, validate_token_tree, ValidationResult
from receipt.compute_gap import compute_receipt_gap
from mayor.decide import MayorInputs, compute_decision_payload, sha256_hex


# ============================================================================
# BUILDERS (Oracle emulation with test content)
# ============================================================================

def build_wul_token_tree(claim_text: str) -> Dict[str, Any]:
    """
    Minimal WUL tree satisfying R15 requirement.
    No free text in payload - claim semantics via ref only.

    Uses dict-based format compatible with WUL validator.
    R15 is mandatory and has arity 2.
    """
    # Simple valid tree with R15 (objective return required)
    # Structured as: D01 claim with R15 relation pointing to E03 objective and E02 artifact
    return {
        "D01": {
            "R15": ["E03", "E02"]
        }
    }


def build_tribunal_bundle(claim_text: str) -> Dict[str, Any]:
    """
    Required obligations based on claim characteristics.
    Deterministic rule-based expansion.
    """
    hard = [
        {"name": "schema_validation", "severity": "HARD", "expected_attestor": "CI_RUNNER"},
        {"name": "allowlist_check", "severity": "HARD", "expected_attestor": "CI_RUNNER"},
        {"name": "purity_check", "severity": "HARD", "expected_attestor": "CI_RUNNER"}
    ]

    # Deterministic expansion: "publish" keyword triggers extra obligation
    if "publish" in claim_text.lower():
        hard.append({"name": "public_snapshot_ready", "severity": "HARD", "expected_attestor": "CI_RUNNER"})

    return {"obligations": hard}


def build_policies(claim_text: str) -> Dict[str, Any]:
    """Kill-switch emulation based on forbidden keywords."""
    forbidden = ["free text", "ignore rules", "bypass", "override"]
    kill_pass = not any(k in claim_text.lower() for k in forbidden)
    return {"kill_switches_pass": kill_pass}


def build_initial_attestations_ledger(mode: str = "empty") -> Dict[str, Any]:
    """
    mode: "empty" | "partial" | "full"
    """
    if mode == "full":
        return {
            "attestations": [
                {"obligation_name": "schema_validation", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True},
                {"obligation_name": "allowlist_check", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True},
                {"obligation_name": "purity_check", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True},
                {"obligation_name": "public_snapshot_ready", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True}
            ]
        }
    elif mode == "partial":
        return {
            "attestations": [
                {"obligation_name": "schema_validation", "attestor": "CI_RUNNER", "attestation_valid": True, "policy_match": True}
            ]
        }
    return {"attestations": []}


def build_receipt_root_payload(token_tree: Dict[str, Any], tribunal: Dict[str, Any], policies: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "kind": "RECEIPT_ROOT_PAYLOAD",
        "version": "v0",
        "pins": {
            "wul_tree_hash": sha256_hex(token_tree),
            "tribunal_hash": sha256_hex(tribunal),
            "policies_hash": sha256_hex(policies)
        }
    }


# ============================================================================
# SCORING (Mayor evaluation %)
# ============================================================================

def compute_progress_percent(tribunal: Dict[str, Any], ledger: Dict[str, Any], policies: Dict[str, Any]) -> int:
    """
    Progress metric: (1 - gap/hard_count) * 100, with penalty for kill switch failure
    """
    hard_count = sum(1 for o in tribunal.get("obligations", [])
                     if o.get("severity") == "HARD")
    gap, _ = compute_receipt_gap(tribunal, ledger)

    base = 1.0 - (gap / max(hard_count, 1))
    if not policies.get("kill_switches_pass", False):
        base -= 0.35

    return max(0, min(100, int(round(100 * base))))


# ============================================================================
# SUPERTEAM IMPROVEMENTS
# ============================================================================

@dataclass(frozen=True)
class Improvement:
    title: str
    rationale: str
    new_attestations_ledger: Dict[str, Any]
    new_policies: Dict[str, Any]
    mayor_percent: int
    delta_percent: int
    predicted_decision: str
    blocking_codes: List[str]


def propose_improvements(
    tribunal: Dict[str, Any],
    ledger: Dict[str, Any],
    policies: Dict[str, Any],
    receipt_root: Dict[str, Any]
) -> List[Improvement]:
    """Generate improvement proposals with Mayor evaluation."""
    current_percent = compute_progress_percent(tribunal, ledger, policies)
    gap, missing = compute_receipt_gap(tribunal, ledger)

    missing_names = [m.get("name") for m in missing]
    hard_names = [o["name"] for o in tribunal.get("obligations", [])
                  if o.get("severity") == "HARD"]

    proposals = []

    # Proposal: Add missing attestations
    if missing_names:
        new_ledger = {"attestations": list(ledger.get("attestations", []))}
        for name in missing_names:
            new_ledger["attestations"].append({
                "obligation_name": name,
                "attestor": "CI_RUNNER",
                "attestation_valid": True,
                "policy_match": True
            })
        proposals.append((
            "Add missing HARD attestations",
            f"Adds CI_RUNNER attestations for: {', '.join(missing_names)}",
            new_ledger,
            dict(policies)
        ))

    # Proposal: Fix kill switch
    if not policies.get("kill_switches_pass", False):
        proposals.append((
            "Fix kill-switch failure",
            "Sets kill_switches_pass=true in policies",
            dict(ledger),
            {**policies, "kill_switches_pass": True}
        ))

    # Proposal: Combined fix
    if missing_names and not policies.get("kill_switches_pass", False):
        new_ledger = {"attestations": list(ledger.get("attestations", []))}
        for name in missing_names:
            new_ledger["attestations"].append({
                "obligation_name": name,
                "attestor": "CI_RUNNER",
                "attestation_valid": True,
                "policy_match": True
            })
        proposals.append((
            "Fix kill-switch AND add missing attestations",
            "Joint improvement: kill_switches_pass=true + satisfy all HARD obligations",
            new_ledger,
            {**policies, "kill_switches_pass": True}
        ))

    improvements = []
    for title, rationale, new_ledger, new_policies in proposals:
        new_percent = compute_progress_percent(tribunal, new_ledger, new_policies)

        inp = MayorInputs(
            tribunal_bundle=tribunal,
            attestations_ledger=new_ledger,
            policies=new_policies,
            receipt_root_payload=receipt_root
        )
        payload = compute_decision_payload(inp)
        blocking_codes = [b["code"] for b in payload.get("blocking", [])]

        improvements.append(Improvement(
            title=title,
            rationale=rationale,
            new_attestations_ledger=new_ledger,
            new_policies=new_policies,
            mayor_percent=new_percent,
            delta_percent=new_percent - current_percent,
            predicted_decision=payload["decision"],
            blocking_codes=blocking_codes
        ))

    improvements.sort(key=lambda x: (-x.delta_percent, -x.mayor_percent))
    return improvements


# ============================================================================
# SHIPMENT GENERATION
# ============================================================================

def make_shipment_latex(payload: Dict[str, Any]) -> str:
    return r"""\documentclass[11pt]{article}
\usepackage{amsmath,amssymb}
\begin{document}

\section*{WUL-ORACLE Shipment Artifact}

\subsection*{Decision Payload (Deterministic)}
\begin{verbatim}
""" + json.dumps(payload, indent=2, sort_keys=True) + r"""
\end{verbatim}

\subsection*{Constitutional Compliance}
This artifact is emitted only under SHIP: receipt\_gap = 0 and kill\_switches\_pass = true.

\end{document}
"""


def make_shipment_code(payload: Dict[str, Any]) -> str:
    return (
        "#!/usr/bin/env python3\n"
        "# Auto-generated WUL-ORACLE shipment (deterministic payload)\n\n"
        "DECISION_PAYLOAD = " + json.dumps(payload, indent=2, sort_keys=True) + "\n\n"
        "def verify():\n"
        "    assert DECISION_PAYLOAD['decision'] == 'SHIP'\n"
        "    assert DECISION_PAYLOAD['receipt_gap'] == 0\n"
        "    assert DECISION_PAYLOAD['kill_switches_pass'] is True\n"
        "    return True\n\n"
        "if __name__ == '__main__':\n"
        "    if verify():\n"
        "        print('✓ Shipment verified')\n"
    )


def make_shipment_text(payload: Dict[str, Any]) -> str:
    return (
        "WUL-ORACLE SHIPMENT ARTIFACT\n"
        "=" * 60 + "\n\n"
        "Decision Payload (deterministic):\n"
        + json.dumps(payload, indent=2, sort_keys=True) + "\n\n"
        "Constitutional Compliance:\n"
        "- Emitted only under SHIP\n"
        "- Receipt gap = 0\n"
        "- Kill switches pass = true\n"
        "- Schema validated (2020-12)\n"
        "- Reason codes from canonical allowlist\n"
    )


def make_meta() -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": f"{platform.system()} {platform.machine()}"
        }
    }


# ============================================================================
# RUN STATE
# ============================================================================

@dataclass
class RunState:
    claim_text: str
    token_tree: Dict[str, Any]
    tribunal_bundle: Dict[str, Any]
    policies: Dict[str, Any]
    attestations_ledger: Dict[str, Any]
    receipt_root_payload: Dict[str, Any]
    last_decision_payload: Optional[Dict[str, Any]] = None

    def recompute_decision(self) -> Dict[str, Any]:
        inp = MayorInputs(
            tribunal_bundle=self.tribunal_bundle,
            attestations_ledger=self.attestations_ledger,
            policies=self.policies,
            receipt_root_payload=self.receipt_root_payload
        )
        self.last_decision_payload = compute_decision_payload(inp)
        return self.last_decision_payload


# ============================================================================
# CLI MODES
# ============================================================================

def mode_1_test_claim(kernel: Dict[str, Any]) -> RunState:
    """MODE 1: Test a claim"""
    print("\n" + "=" * 60)
    print("MODE 1 — TEST A CLAIM")
    print("=" * 60)

    claim = input("\nEnter claim text (or 'example'): ").strip()
    if claim.lower() == "example":
        claim = "Publish a deterministic decision_record payload under SHIP only."

    print(f"\nClaim: {claim}")

    # Build artifacts
    token_tree = build_wul_token_tree(claim)
    tribunal = build_tribunal_bundle(claim)
    policies = build_policies(claim)
    receipt_root = build_receipt_root_payload(token_tree, tribunal, policies)

    # Initial attestations (partial to force NO_SHIP in most cases)
    ledger_mode = "partial" if "publish" in claim.lower() else "empty"
    ledger = build_initial_attestations_ledger(ledger_mode)

    # WUL validation
    print("\n--- WUL-CORE Validation ---")
    res = validate_token_tree(token_tree, kernel, require_r15=True)

    if res.ok:
        print(f"✓ PASSED (depth: {res.depth}, nodes: {res.nodes})")
    else:
        print(f"✗ FAILED: {res.reason}")
        print(f"  Depth: {res.depth}, Nodes: {res.nodes}")

    # Build state and compute decision
    state = RunState(
        claim_text=claim,
        token_tree=token_tree,
        tribunal_bundle=tribunal,
        policies=policies,
        attestations_ledger=ledger,
        receipt_root_payload=receipt_root
    )

    decision = state.recompute_decision()

    # Display results
    print("\n--- Mayor Decision ---")
    print(f"Decision: {decision['decision']}")
    print(f"Receipt Gap: {decision['receipt_gap']}")
    print(f"Kill Switches: {'PASS' if decision['kill_switches_pass'] else 'FAIL'}")

    if decision['blocking']:
        print("\nBlocking Reasons:")
        for b in decision['blocking']:
            print(f"  [{b['code']}] {b.get('detail', '')}")

    progress = compute_progress_percent(tribunal, ledger, policies)
    print(f"\nProgress: {progress}%")

    return state


def mode_2_improve(state: Optional[RunState]) -> RunState:
    """MODE 2: Ask superteam to improve"""
    if state is None:
        print("\n✗ No claim loaded. Run Mode 1 first.")
        return None

    print("\n" + "=" * 60)
    print("MODE 2 — ASK SUPERTEAM TO IMPROVE")
    print("=" * 60)

    current = state.last_decision_payload
    if not current:
        current = state.recompute_decision()

    print(f"\nCurrent Decision: {current['decision']}")
    print(f"Current Receipt Gap: {current['receipt_gap']}")

    if current['decision'] == 'SHIP':
        print("\n✓ Already SHIP - no improvements needed!")
        return state

    # Generate proposals
    print("\n--- Superteam Proposals ---")
    improvements = propose_improvements(
        state.tribunal_bundle,
        state.attestations_ledger,
        state.policies,
        state.receipt_root_payload
    )

    if not improvements:
        print("No improvements available.")
        return state

    for i, imp in enumerate(improvements, 1):
        print(f"\n{i}. {imp.title}")
        print(f"   Rationale: {imp.rationale}")
        print(f"   Mayor Evaluation: {imp.mayor_percent}% (Δ{imp.delta_percent:+d}%)")
        print(f"   Predicted Decision: {imp.predicted_decision}")
        if imp.blocking_codes:
            print(f"   Remaining Blocks: {', '.join(imp.blocking_codes)}")

    # Select and apply
    choice = input(f"\nSelect improvement (1-{len(improvements)}) or 0 to skip: ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(improvements):
            selected = improvements[idx]
            print(f"\nApplying: {selected.title}")

            state.attestations_ledger = selected.new_attestations_ledger
            state.policies = selected.new_policies

            new_decision = state.recompute_decision()

            print(f"\n✓ Applied!")
            print(f"New Decision: {new_decision['decision']}")
            print(f"New Receipt Gap: {new_decision['receipt_gap']}")
            print(f"New Progress: {selected.mayor_percent}%")
    except ValueError:
        print("Invalid choice - no changes applied")

    return state


def mode_3_ship(state: Optional[RunState]) -> None:
    """MODE 3: Ask Mayor to ship"""
    if state is None:
        print("\n✗ No claim loaded. Run Mode 1 first.")
        return

    print("\n" + "=" * 60)
    print("MODE 3 — ASK MAYOR TO SHIP")
    print("=" * 60)

    decision = state.last_decision_payload
    if not decision:
        decision = state.recompute_decision()

    if decision['decision'] != 'SHIP':
        print(f"\n✗ Cannot ship: Decision is {decision['decision']}")
        print("Use Mode 2 to improve until SHIP.")
        return

    print("\n✓ Decision: SHIP")
    print("Authorized to generate shipment artifact.")

    # Choose format
    print("\nSelect format:")
    print("1. LaTeX (formal specification)")
    print("2. Code (Python implementation)")
    print("3. Text (narrative edition)")

    fmt_choice = input("\nFormat (1-3): ").strip()

    if fmt_choice == "1":
        content = make_shipment_latex(decision)
        ext = "tex"
        fmt_name = "LaTeX"
    elif fmt_choice == "2":
        content = make_shipment_code(decision)
        ext = "py"
        fmt_name = "Code"
    else:
        content = make_shipment_text(decision)
        ext = "txt"
        fmt_name = "Text"

    # Generate files
    filename = f"shipment.{ext}"
    meta_filename = "shipment.meta.json"

    shipment_sha = hashlib.sha256(content.encode()).hexdigest()
    meta = make_meta()
    meta["shipment_hash"] = shipment_sha

    print(f"\n--- SHIPMENT GENERATED ({fmt_name}) ---")
    print(f"Filename: {filename}")
    print(f"SHA-256: {shipment_sha}")
    print("\n" + "-" * 60)
    print(content)
    print("-" * 60)

    # Save option
    save = input("\nSave to file? (y/n): ").strip().lower()
    if save == 'y':
        Path(filename).write_text(content, encoding="utf-8")
        Path(meta_filename).write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"\n✓ Saved: {filename}")
        print(f"✓ Saved: {meta_filename}")


# ============================================================================
# MAIN CLI LOOP
# ============================================================================

def main():
    print("=" * 60)
    print("         WUL-ORACLE CLI EMULATOR")
    print(" Receipt-First Governance for Multi-Agent Systems")
    print("=" * 60)
    print("\nOptions:")
    print(" 1) Test a claim")
    print(" 2) Ask superteam to improve (Mayor eval in %)")
    print(" 3) Ask mayor to ship (latex/code/text)")
    print(" 4) Show current state")
    print(" 5) Quit")
    print("=" * 60)

    # Load kernel
    kernel_path = ROOT / "src" / "wul" / "core_kernel.json"
    if not kernel_path.exists():
        print(f"\n✗ Kernel not found: {kernel_path}")
        print("Ensure src/wul/core_kernel.json exists.")
        return

    kernel = load_kernel(kernel_path)
    print(f"\n✓ Loaded WUL-CORE kernel: {kernel['version']}")

    state: Optional[RunState] = None

    while True:
        choice = input("\n> ").strip()

        if choice == "1":
            state = mode_1_test_claim(kernel)
        elif choice == "2":
            state = mode_2_improve(state)
        elif choice == "3":
            mode_3_ship(state)
        elif choice == "4":
            if state:
                print("\n--- Current State ---")
                print(f"Claim: {state.claim_text}")
                if state.last_decision_payload:
                    print(f"Decision: {state.last_decision_payload['decision']}")
                    print(f"Receipt Gap: {state.last_decision_payload['receipt_gap']}")
                    progress = compute_progress_percent(
                        state.tribunal_bundle,
                        state.attestations_ledger,
                        state.policies
                    )
                    print(f"Progress: {progress}%")
            else:
                print("\n✗ No claim loaded")
        elif choice in ("5", "q", "quit", "exit"):
            print("\nExiting WUL-ORACLE CLI. Goodbye!")
            break
        else:
            print("Invalid option. Choose 1-5.")


if __name__ == "__main__":
    main()
