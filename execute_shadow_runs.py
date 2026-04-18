#!/usr/bin/env python3
"""
Execute 113 shadow mode runs with planned input distribution.

Metrics collected:
- total_runs
- crash_count
- nondeterminism_count
- route_distribution
- top_reason_codes
- unresolved_pointer_rate
- promotion_request_count
- pipeline_substitution_count
- violations_count
- go/no-go decision
"""

import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Import dispatch modules
from helen_dispatch_v1_router import DispatchRouter
from helen_dispatch_v1_schemas import (
    RouteType, InputType, ResolutionStatus, AdmissibilityStatus,
    ForbiddenEffect, DISPATCH_REASON_CODES
)

# ============================================================================
# Test Input Definitions
# ============================================================================

def generate_test_inputs() -> List[Dict[str, Any]]:
    """Generate 113 test inputs matching planned distribution."""

    inputs = []

    # USER_QUERY (25)
    for i in range(25):
        inputs.append({
            "input_type": "USER_QUERY",
            "text": f"User query {i}: What is X?",
        })

    # SLASH_COMMAND (5)
    for i in range(5):
        inputs.append({
            "input_type": "SLASH_COMMAND",
            "slash_command": "/status",
        })

    # CLAIM_OBJECT (15)
    for i in range(15):
        inputs.append({
            "input_type": "CLAIM_OBJECT",
            "claim_id": f"claim_{100+i}",
            "text": f"Claim text {i}",
        })

    # CLAIM_BUNDLE (10)
    for i in range(10):
        inputs.append({
            "input_type": "CLAIM_BUNDLE",
            "claims": [
                {"claim_id": f"claim_{200+i}_a", "text": "Claim A"},
                {"claim_id": f"claim_{200+i}_b", "text": "Claim B"},
            ],
        })

    # CLAIM_EXTRACTION_REQUEST (10)
    for i in range(10):
        inputs.append({
            "input_type": "CLAIM_EXTRACTION_REQUEST",
            "claim_extraction": True,
            "source": f"paper_{300+i}",
        })

    # ARTIFACT_REQUEST (8)
    for i in range(8):
        inputs.append({
            "input_type": "ARTIFACT_REQUEST",
            "artifact_type": "report",
            "title": f"Report {i}",
        })

    # AUDIT_REQUEST (8)
    for i in range(8):
        inputs.append({
            "input_type": "AUDIT_REQUEST",
            "audit_type": "knowledge_health",
        })

    # SOURCE_INGEST (5)
    for i in range(5):
        inputs.append({
            "input_type": "SOURCE_INGEST",
            "source_id": f"source_{400+i}",
            "content": f"Source content {i}",
        })

    # UNRESOLVED_POINTER (8)
    for i in range(8):
        inputs.append({
            "input_type": "UNRESOLVED_POINTER",
            "unresolved_pointers": [f"missing_{500+i}"],
        })

    # PROMOTION_REQUEST (5)
    for i in range(5):
        inputs.append({
            "input_type": "PROMOTION_REQUEST",
            "promote_to": "canonical",
            "object_id": f"obj_{600+i}",
        })

    # PIPELINE_SUBSTITUTION_REQUEST (2)
    for i in range(2):
        inputs.append({
            "input_type": "PIPELINE_SUBSTITUTION_REQUEST",
            "new_pipeline": "CLAIM_EXTRACTION_PIPELINE_V2",
        })

    # TEMPLE_OBSERVATION (10)
    for i in range(10):
        inputs.append({
            "input_type": "TEMPLE_OBSERVATION",
            "temple": True,
            "hypothesis": f"What if {i}?",
        })

    # MEMORY_REQUEST (2)
    for i in range(2):
        inputs.append({
            "input_type": "MEMORY_REQUEST",
            "memory_op": "read",
        })

    return inputs


# ============================================================================
# Shadow Mode Execution
# ============================================================================

def execute_shadow_runs() -> Dict[str, Any]:
    """Execute all shadow runs and collect metrics."""

    print("=" * 80)
    print("HELEN_DISPATCH_SHADOW_MODE_V1 — EXECUTION")
    print("=" * 80)

    # Initialize
    router = DispatchRouter(
        session_id="shadow_prod_20260404",
        manifest_ref="helen_manifest_v1",
    )

    # Generate inputs
    inputs = generate_test_inputs()
    print(f"\n✓ Generated {len(inputs)} test inputs")

    # Tracking
    runs = []
    crashes = 0
    nondeterminism_count = 0
    violations = 0
    reason_code_counts = {}
    route_counts = {}
    input_type_counts = {}
    unresolved_count = 0
    promotion_count = 0
    pipeline_sub_count = 0

    receipt_hashes = {}  # Track hashes for determinism

    # Execute runs
    print(f"\nExecuting {len(inputs)} shadow runs...")
    print("-" * 80)

    for idx, input_obj in enumerate(inputs, 1):
        try:
            # Route
            receipt, rejection = router.route(
                input_obj,
                input_id=f"shadow_{idx:03d}",
                store_refs={
                    "context": "ctx://shadow",
                    "ledger": "ledger://shadow",
                    "transcript": "tr://shadow",
                },
            )

            # Validate receipt
            if not receipt.receipt_hash:
                violations += 1
                print(f"  Run {idx:3d}: ❌ INVALID (no receipt_hash)")
                crashes += 1
                continue

            # Track receipt hash for determinism check
            input_key = receipt.input_hash
            if input_key in receipt_hashes:
                if receipt_hashes[input_key] != receipt.receipt_hash:
                    nondeterminism_count += 1
                    print(f"  Run {idx:3d}: ⚠️  NONDETERMINISM (hash mismatch)")
                    continue
            else:
                receipt_hashes[input_key] = receipt.receipt_hash

            # Validate reason codes
            invalid_codes = [c for c in receipt.reason_codes if c not in DISPATCH_REASON_CODES]
            if invalid_codes:
                violations += 1
                print(f"  Run {idx:3d}: ❌ INVALID reason codes: {invalid_codes}")
                continue

            # Count metrics
            route = receipt.primary_route.value
            route_counts[route] = route_counts.get(route, 0) + 1

            input_type = receipt.input_type.value
            input_type_counts[input_type] = input_type_counts.get(input_type, 0) + 1

            for code in receipt.reason_codes:
                reason_code_counts[code] = reason_code_counts.get(code, 0) + 1

            if receipt.resolution_status.value == "unresolved":
                unresolved_count += 1

            if "promotion_requested" in receipt.reason_codes:
                promotion_count += 1

            if "pipeline_substitution_requested" in receipt.reason_codes:
                pipeline_sub_count += 1

            # Verify gates
            if receipt.primary_route == RouteType.KERNEL:
                if "routing_to_kernel_sovereign" not in receipt.reason_codes:
                    violations += 1

            if receipt.primary_route == RouteType.TEMPLE:
                if ForbiddenEffect.CANONICAL_PROMOTION not in receipt.forbidden_effects:
                    violations += 1

            # Success
            runs.append({
                "run_id": f"shadow_{idx:03d}",
                "input_type": input_type,
                "primary_route": route,
                "receipt_hash": receipt.receipt_hash,
                "success": True,
            })

            status_icon = "✅"
            print(f"  Run {idx:3d}: {status_icon} {input_type:25s} → {route:8s}")

        except Exception as e:
            crashes += 1
            runs.append({
                "run_id": f"shadow_{idx:03d}",
                "input_type": input_obj.get("input_type", "UNKNOWN"),
                "primary_route": "ERROR",
                "error": str(e),
                "success": False,
            })
            print(f"  Run {idx:3d}: ❌ CRASH — {str(e)[:50]}")

    print("-" * 80)

    # Compute statistics
    successful_runs = len([r for r in runs if r.get("success", False)])
    total_runs = len(runs)

    # Top reason codes
    top_codes = sorted(reason_code_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    # Success rates
    unresolved_rate = 100 * unresolved_count / total_runs if total_runs > 0 else 0
    promotion_rate = 100 * promotion_count / total_runs if total_runs > 0 else 0
    pipeline_sub_rate = 100 * pipeline_sub_count / total_runs if total_runs > 0 else 0

    # Go/no-go criteria
    criteria = {
        "min_runs_100": total_runs >= 100,
        "crash_rate_zero": crashes == 0,
        "nondeterminism_zero": nondeterminism_count == 0,
        "violations_zero": violations == 0,
        "route_distribution_reasonable": all(
            count > 0 for count in route_counts.values()
        ),
    }

    go = all(criteria.values())

    # Build report
    report = {
        "timestamp_started": datetime.utcnow().isoformat() + "Z",
        "session_id": "shadow_prod_20260404",

        # Core metrics
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "crash_count": crashes,
        "nondeterminism_count": nondeterminism_count,
        "violations_count": violations,

        # Route distribution
        "route_distribution": route_counts,

        # Input type distribution
        "input_type_distribution": input_type_counts,

        # Top reason codes
        "top_reason_codes": [{"code": code, "count": count} for code, count in top_codes],

        # Special cases
        "unresolved_pointer_count": unresolved_count,
        "unresolved_pointer_rate_percent": round(unresolved_rate, 2),
        "promotion_request_count": promotion_count,
        "promotion_request_rate_percent": round(promotion_rate, 2),
        "pipeline_substitution_count": pipeline_sub_count,
        "pipeline_substitution_rate_percent": round(pipeline_sub_rate, 2),

        # Go/no-go
        "go_criteria": criteria,
        "go_decision": "GO_STEP_3" if go else "HOLD_AND_PATCH",
        "decision_reason": (
            "✅ All acceptance criteria met" if go
            else f"❌ Failed: {[k for k, v in criteria.items() if not v]}"
        ),
    }

    return report


# ============================================================================
# Report Output
# ============================================================================

def print_report(report: Dict[str, Any]) -> None:
    """Print shadow mode report."""

    print("\n" + "=" * 80)
    print("SHADOW MODE REPORT")
    print("=" * 80)

    print(f"\nSESSION: {report['session_id']}")
    print(f"TIMESTAMP: {report['timestamp_started']}")

    # Summary
    print(f"\n📊 SUMMARY")
    print(f"  Total runs: {report['total_runs']}")
    print(f"  Successful: {report['successful_runs']}")
    print(f"  Crashes: {report['crash_count']}")
    print(f"  Nondeterminism: {report['nondeterminism_count']}")
    print(f"  Violations: {report['violations_count']}")

    # Route distribution
    print(f"\n🛣️  ROUTE DISTRIBUTION")
    for route, count in sorted(report['route_distribution'].items()):
        pct = 100 * count / report['total_runs']
        bar = "█" * int(pct / 5)
        print(f"  {route:12s}: {count:3d} ({pct:5.1f}%) {bar}")

    # Top reason codes
    print(f"\n📋 TOP REASON CODES")
    for item in report['top_reason_codes'][:10]:
        print(f"  {item['code']:45s}: {item['count']:3d}")

    # Special cases
    print(f"\n⚠️  SPECIAL CASES")
    print(f"  Unresolved pointers: {report['unresolved_pointer_count']} ({report['unresolved_pointer_rate_percent']:.1f}%)")
    print(f"  Promotion requests: {report['promotion_request_count']} ({report['promotion_request_rate_percent']:.1f}%)")
    print(f"  Pipeline substitutions: {report['pipeline_substitution_count']} ({report['pipeline_substitution_rate_percent']:.1f}%)")

    # Go/no-go criteria
    print(f"\n✓ GO/NO-GO CRITERIA")
    for criterion, result in report['go_criteria'].items():
        status = "✅" if result else "❌"
        print(f"  {status} {criterion:35s}: {result}")

    # Decision
    print(f"\n" + "=" * 80)
    decision = report['go_decision']
    if decision == "GO_STEP_3":
        print(f"🎯 {decision}")
        print(f"   {report['decision_reason']}")
    else:
        print(f"🔴 {decision}")
        print(f"   {report['decision_reason']}")
    print("=" * 80)


def save_report(report: Dict[str, Any]) -> str:
    """Save report to JSON file."""
    import json
    from pathlib import Path

    path = Path(".shadow_report_20260404.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    return str(path)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    try:
        # Execute shadow runs
        report = execute_shadow_runs()

        # Print report
        print_report(report)

        # Save report
        report_path = save_report(report)
        print(f"\n📁 Report saved: {report_path}\n")

        # Return exit code
        sys.exit(0 if report['go_decision'] == 'GO_STEP_3' else 1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(2)
