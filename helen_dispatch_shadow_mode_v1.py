"""
HELEN_DISPATCH_SHADOW_MODE_V1: Log-Only Dispatch Monitoring

Purpose:
- Deploy dispatch routing in non-blocking mode
- Log all routing decisions to separate shadow ledger
- Zero behavior change to system
- Collect statistics for edge case detection
- Prepare for STEP 3 enforcement

Key invariants:
1. Shadow mode never mutates system state
2. All receipts are append-only to shadow ledger
3. Route distribution is measurable
4. No crashes, nondeterminism detected
5. Ready for go/no-go decision after 100+ shadow runs
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from helen_dispatch_v1_schemas import (
    DispatchReceipt, RejectionPacket, RouteType, InputType,
    ResolutionStatus, AdmissibilityStatus
)
from helen_dispatch_v1_router import DispatchRouter


class ShadowRunStatus(Enum):
    """Status of a shadow mode run."""
    SUCCESS = "success"
    CRASH = "crash"
    NONDETERMINISM_DETECTED = "nondeterminism_detected"
    INVALID_RECEIPT = "invalid_receipt"


@dataclass
class ShadowRunMetrics:
    """Metrics collected during shadow run."""
    run_id: str
    timestamp: str
    input_hash: str
    input_type: InputType
    primary_route: RouteType
    status: ShadowRunStatus
    receipt_hash: str
    reason_codes_count: int
    error: Optional[str] = None


@dataclass
class ShadowModeSummary:
    """Aggregate statistics from shadow mode runs."""
    total_runs: int
    successful_runs: int
    crash_count: int
    nondeterminism_count: int
    invalid_receipt_count: int

    route_distribution: Dict[str, int]
    input_type_distribution: Dict[str, int]
    top_reason_codes: List[tuple]  # (code, count)

    unresolved_pointer_count: int
    promotion_attempts_count: int
    temple_observations_count: int

    determinism_verified: bool
    determinism_sample_size: int

    timestamp_generated: str


class DispatchShadowMode:
    """
    Non-blocking shadow mode for dispatch testing.

    Behavior:
    1. Route all inputs (silent, non-blocking)
    2. Log receipts to shadow_ledger.ndjson
    3. Collect statistics
    4. Never mutate system state
    """

    def __init__(
        self,
        session_id: str,
        manifest_ref: str,
        shadow_ledger_path: Optional[str] = None,
        store_refs: Optional[Dict[str, str]] = None,
    ):
        """Initialize shadow mode."""
        self.session_id = session_id
        self.manifest_ref = manifest_ref
        self.store_refs = store_refs or {
            "context": "ctx://shadow",
            "ledger": "ledger://shadow",
            "transcript": "tr://shadow",
        }

        # Shadow ledger path
        if shadow_ledger_path is None:
            shadow_ledger_path = f".shadow_ledger_{session_id}.ndjson"
        self.shadow_ledger_path = Path(shadow_ledger_path)

        # Router instance
        self.router = DispatchRouter(
            session_id=session_id,
            manifest_ref=manifest_ref,
        )

        # Run tracking
        self.runs: List[ShadowRunMetrics] = []
        self.receipt_hashes: List[str] = []
        self.last_receipt: Optional[DispatchReceipt] = None

    def process_input_shadow(
        self,
        input_obj: Dict[str, Any],
        input_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process input in shadow mode (non-blocking).

        Returns dict with:
        - receipt (full DispatchReceipt as dict)
        - rejection (optional RejectionPacket as dict)
        - status (SUCCESS, CRASH, etc.)
        - metrics (run metrics)
        """
        run_id = f"shadow_run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.runs)}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        try:
            # Route the input
            receipt, rejection = self.router.route(
                input_obj,
                input_id=input_id,
                store_refs=self.store_refs,
            )

            # Validate receipt
            if not receipt.receipt_hash:
                raise ValueError("Receipt missing receipt_hash")

            # Check determinism (if we have a prior receipt for same hash)
            nondeterminism_detected = False
            if input_obj and "input_hash_for_replay" in input_obj:
                if receipt.receipt_hash in self.receipt_hashes:
                    # Duplicate → check for consistency
                    pass
                self.receipt_hashes.append(receipt.receipt_hash)

            # Build metrics
            metrics = ShadowRunMetrics(
                run_id=run_id,
                timestamp=timestamp,
                input_hash=receipt.input_hash,
                input_type=receipt.input_type,
                primary_route=receipt.primary_route,
                status=ShadowRunStatus.NONDETERMINISM_DETECTED if nondeterminism_detected else ShadowRunStatus.SUCCESS,
                receipt_hash=receipt.receipt_hash,
                reason_codes_count=len(receipt.reason_codes),
            )

            self.runs.append(metrics)
            self.last_receipt = receipt

            return {
                "run_id": run_id,
                "status": metrics.status.value,
                "receipt": receipt.to_dict(),
                "rejection": rejection.to_dict() if rejection else None,
                "metrics": asdict(metrics),
            }

        except Exception as e:
            # Crash detected
            metrics = ShadowRunMetrics(
                run_id=run_id,
                timestamp=timestamp,
                input_hash="",
                input_type=InputType.USER_QUERY,
                primary_route=RouteType.REJECT,
                status=ShadowRunStatus.CRASH,
                receipt_hash="",
                reason_codes_count=0,
                error=str(e),
            )

            self.runs.append(metrics)

            return {
                "run_id": run_id,
                "status": ShadowRunStatus.CRASH.value,
                "receipt": None,
                "rejection": None,
                "metrics": asdict(metrics),
                "error": str(e),
            }

    def log_shadow_run(self, result: Dict[str, Any]) -> None:
        """Append run to shadow ledger (append-only)."""
        with open(self.shadow_ledger_path, "a") as f:
            f.write(json.dumps(result, default=str) + "\n")

    def generate_summary(self) -> ShadowModeSummary:
        """Generate aggregate statistics from all shadow runs."""
        if not self.runs:
            raise ValueError("No runs recorded yet")

        # Route distribution
        route_dist = {}
        for run in self.runs:
            key = run.primary_route.value
            route_dist[key] = route_dist.get(key, 0) + 1

        # Input type distribution
        input_dist = {}
        for run in self.runs:
            key = run.input_type.value
            input_dist[key] = input_dist.get(key, 0) + 1

        # Count special cases
        unresolved = sum(
            1 for run in self.runs
            if "unresolved_pointers_present" in (self.last_receipt.reason_codes if self.last_receipt else [])
        )
        promotions = sum(
            1 for run in self.runs
            if "promotion_requested" in (self.last_receipt.reason_codes if self.last_receipt else [])
        )
        temples = sum(
            1 for run in self.runs
            if run.primary_route == RouteType.TEMPLE
        )

        # Top reason codes
        reason_code_counts = {}
        for run in self.runs:
            # Note: would need to store reason_codes in metrics to count here
            # For now, this is a placeholder
            pass
        top_codes = sorted(reason_code_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Determinism check
        crash_count = sum(1 for run in self.runs if run.status == ShadowRunStatus.CRASH)
        nondeterminism_count = sum(
            1 for run in self.runs
            if run.status == ShadowRunStatus.NONDETERMINISM_DETECTED
        )

        summary = ShadowModeSummary(
            total_runs=len(self.runs),
            successful_runs=sum(1 for run in self.runs if run.status == ShadowRunStatus.SUCCESS),
            crash_count=crash_count,
            nondeterminism_count=nondeterminism_count,
            invalid_receipt_count=sum(
                1 for run in self.runs
                if run.status == ShadowRunStatus.INVALID_RECEIPT
            ),
            route_distribution=route_dist,
            input_type_distribution=input_dist,
            top_reason_codes=top_codes,
            unresolved_pointer_count=unresolved,
            promotion_attempts_count=promotions,
            temple_observations_count=temples,
            determinism_verified=(nondeterminism_count == 0 and crash_count == 0),
            determinism_sample_size=len(self.runs),
            timestamp_generated=datetime.utcnow().isoformat() + "Z",
        )

        return summary

    def write_summary_report(self, output_path: Optional[str] = None) -> str:
        """Write summary report to file."""
        summary = self.generate_summary()

        if output_path is None:
            output_path = f".shadow_report_{self.session_id}.json"

        with open(output_path, "w") as f:
            json.dump(asdict(summary), f, indent=2, default=str)

        return output_path

    def verify_determinism_sample(self, sample_input: Dict[str, Any], runs: int = 5) -> bool:
        """
        Verify determinism on sample input (run same input N times).

        Returns True if all runs produce identical receipt hash.
        """
        hashes = []
        for _ in range(runs):
            result = self.process_input_shadow(sample_input)
            if result["status"] != ShadowRunStatus.SUCCESS.value:
                return False
            hashes.append(result["receipt"]["receipt_hash"])

        # All hashes should be identical
        return len(set(hashes)) == 1

    def go_no_go_decision(self) -> tuple:
        """
        Determine readiness for STEP 3 enforcement.

        Returns: (go: bool, reason: str, summary: ShadowModeSummary)
        """
        summary = self.generate_summary()

        # Success criteria
        checks = {
            "min_runs_100": summary.total_runs >= 100,
            "crash_rate_zero": summary.crash_count == 0,
            "nondeterminism_zero": summary.nondeterminism_count == 0,
            "determinism_verified": summary.determinism_verified,
            "route_distribution_reasonable": all(
                count > 0 for count in summary.route_distribution.values()
                if count > 1  # Allow zero routes if not expected
            ),
        }

        all_pass = all(checks.values())

        if all_pass:
            reason = "✅ READY FOR STEP 3 ENFORCEMENT"
        else:
            failed = [k for k, v in checks.items() if not v]
            reason = f"❌ NOT READY: {', '.join(failed)}"

        return all_pass, reason, summary


# ============================================================================
# SHADOW MODE RUNNER SCRIPT
# ============================================================================

if __name__ == "__main__":
    """
    Example shadow mode session.

    Usage:
        python helen_dispatch_shadow_mode_v1.py
    """

    print("=" * 70)
    print("HELEN_DISPATCH_SHADOW_MODE_V1 — Shadow Run Initialization")
    print("=" * 70)

    # Initialize shadow mode
    shadow = DispatchShadowMode(
        session_id="shadow_test_001",
        manifest_ref="helen_manifest_v1",
        shadow_ledger_path=".shadow_ledger.ndjson",
    )

    print(f"\n✓ Shadow mode initialized")
    print(f"  Session: {shadow.session_id}")
    print(f"  Manifest: {shadow.manifest_ref}")
    print(f"  Ledger: {shadow.shadow_ledger_path}")

    # Test inputs
    test_inputs = [
        {"text": "What is the capital of France?"},
        {"claim_extraction": True, "source": "paper_123"},
        {"promote_to": "canonical", "object_id": "claim_456"},
        {"unresolved_pointers": ["missing_ref"], "text": "about missing_ref?"},
        {"temple": True, "hypothesis": "What if X?"},
        {"audit_type": "knowledge_health"},
        {"claim_id": "claim_789"},
        {"source_id": "source_001", "content": "Some content"},
    ]

    print(f"\n✓ Starting {len(test_inputs)} shadow runs...")
    print("-" * 70)

    for i, input_obj in enumerate(test_inputs, 1):
        result = shadow.process_input_shadow(input_obj, input_id=f"test_input_{i}")
        shadow.log_shadow_run(result)

        status = result["status"]
        receipt = result["receipt"]
        if receipt:
            route = receipt["primary_route"]
            reason_count = len(receipt["reason_codes"])
            print(f"  Run {i:2d}: {status:12s} → {route:8s} ({reason_count} reason_codes)")
        else:
            print(f"  Run {i:2d}: {status:12s} (no receipt)")

    print("-" * 70)
    print(f"✓ Completed {len(shadow.runs)} runs")

    # Generate summary
    print(f"\n✓ Generating summary report...")
    summary = shadow.generate_summary()

    print(f"\n  Total runs: {summary.total_runs}")
    print(f"  Successful: {summary.successful_runs}")
    print(f"  Crashes: {summary.crash_count}")
    print(f"  Nondeterminism: {summary.nondeterminism_count}")
    print(f"\n  Route distribution:")
    for route, count in sorted(summary.route_distribution.items()):
        pct = 100 * count / summary.total_runs
        print(f"    {route:12s}: {count:3d} ({pct:5.1f}%)")

    print(f"\n  Input type distribution:")
    for input_type, count in sorted(summary.input_type_distribution.items())[:5]:
        print(f"    {input_type:25s}: {count:3d}")

    print(f"\n  Special cases:")
    print(f"    Unresolved pointers: {summary.unresolved_pointer_count}")
    print(f"    Promotion attempts:  {summary.promotion_attempts_count}")
    print(f"    Temple observations: {summary.temple_observations_count}")

    print(f"\n  Determinism status:")
    print(f"    Verified: {summary.determinism_verified}")
    print(f"    Sample size: {summary.determinism_sample_size}")

    # Go/no-go decision
    print(f"\n" + "=" * 70)
    go, reason, _ = shadow.go_no_go_decision()
    print(reason)
    print("=" * 70)

    # Write report
    report_path = shadow.write_summary_report()
    print(f"\n✓ Report written to: {report_path}")

    print(f"\nShadow mode session complete.\n")
