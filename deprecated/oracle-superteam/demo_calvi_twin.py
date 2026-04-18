#!/usr/bin/env python3
"""
CALVI_TWIN Demonstration
Shows SHIP and NO_SHIP verdicts with ORACLE BACKBONE governance.
"""

import sys
sys.path.insert(0, 'src')

from calvi_twin import (
    CalviTwin,
    Claim,
    Receipt,
    Tier,
    format_run_record
)


def demo_ship_verdict():
    """Example: Digital twin deployment with valid attestations → SHIP"""

    print("=" * 80)
    print("DEMO 1: SHIP VERDICT (Digital Twin UAV Validation)")
    print("=" * 80)
    print()

    twin = CalviTwin()

    claim = Claim(
        id="C8_DIGITAL_TWIN_DEPLOYMENT",
        title="Deploy digital twin for UAV flight validation",
        text="CALVI_TWIN will validate all UAV flights through pre-deployment simulation with ≥95% scenario coverage before real-world authorization",
        tier=Tier.I,
        domain="SAFETY_OPERATIONS",
        scope="TRAINING_ACADEMY",
        owner="MAYOR_OFFICE",
        timestamp="2026-01-17T14:30:00Z"
    )

    receipts = [
        Receipt(
            path="attestations/easa_uav_simulation_framework_v2.pdf",
            type="REGULATORY_ATTESTATION",
            hash="sha256:a3f2b4e8c9d1f5a7...",
            attestor="EASA",
            timestamp="2026-01-15T09:00:00Z"
        ),
        Receipt(
            path="technical/digital_twin_validation_report_Q4_2025.pdf",
            type="TECHNICAL_VALIDATION",
            hash="sha256:7c8d1e9f2a3b4c5d...",
            attestor="STARESO_TECHNICAL_LEAD",
            timestamp="2025-12-20T16:45:00Z"
        )
    ]

    context = {
        "city_state": {
            "active_training_programs": 4,
            "current_uav_incidents_12mo": 3,
            "digital_twin_scenario_library_size": 87,
            "easa_compliance_status": "CERTIFIED"
        }
    }

    record = twin.process_claim(
        claim=claim,
        receipts=receipts,
        context=context,
        requested_action="OPERATIONAL_AUTHORIZATION"
    )

    print(format_run_record(record))


def demo_no_ship_verdict():
    """Example: Training efficiency claim without RCT → NO_SHIP"""

    print("=" * 80)
    print("DEMO 2: NO_SHIP VERDICT (Training Claim Without RCT)")
    print("=" * 80)
    print()

    twin = CalviTwin()

    claim = Claim(
        id="C1_TRAINING_EFFICIENCY",
        title="30-35% reduction in time-to-competency",
        text="Calvi Academy training achieves 30-35% reduction vs. traditional programs",
        tier=Tier.I,
        domain="TRAINING",
        scope="ACADEMY_CURRICULUM",
        owner="ACADEMY_DIRECTOR",
        timestamp="2026-01-17T15:00:00Z"
    )

    # Only curriculum design, no experimental validation
    receipts = [
        Receipt(
            path="planning/curriculum_design_2026.pdf",
            type="PLANNING_DOC",
            hash="sha256:4f8a9b2c3d1e5f7a...",
            attestor="ACADEMY_DIRECTOR",  # Not in AUTHORIZED_ATTESTORS
            timestamp="2026-01-10T11:00:00Z"
        )
    ]

    context = {
        "city_state": {
            "active_training_programs": 4,
            "rct_protocol_registered": False,
            "independent_evaluator_selected": False
        }
    }

    record = twin.process_claim(
        claim=claim,
        receipts=receipts,
        context=context,
        requested_action="PUBLIC_ANNOUNCEMENT"
    )

    print(format_run_record(record))


def demo_no_ship_surveillance():
    """Example: Surveillance request without oversight → NO_SHIP (kill-switch)"""

    print("=" * 80)
    print("DEMO 3: NO_SHIP VERDICT (Surveillance Without Oversight - Kill Switch)")
    print("=" * 80)
    print()

    twin = CalviTwin()

    claim = Claim(
        id="SEC_UAV_FESTIVAL_2026",
        title="UAV crowd monitoring for summer festival",
        text="Deploy UAV with video capture for crowd safety during Festival du Vent 2026",
        tier=Tier.I,
        domain="PUBLIC_SAFETY",
        scope="FESTIVAL_SECURITY",
        owner="POLICE_MUNICIPALE",
        timestamp="2026-01-17T16:00:00Z"
    )

    # Police request but no prefect authorization or GDPR assessment
    receipts = [
        Receipt(
            path="requests/police_festival_support_2026.pdf",
            type="OPERATIONAL_REQUEST",
            hash="sha256:5e9f2a3b4c1d7e8a...",
            attestor="POLICE_CHIEF",  # Not in AUTHORIZED_ATTESTORS
            timestamp="2026-01-17T14:00:00Z"
        )
    ]

    context = {
        "city_state": {
            "prefect_authorization": False,
            "gdpr_impact_assessment": False,
            "oversight_protocol_defined": False
        }
    }

    # This will trigger LEGAL_COMPLIANCE kill-switch
    record = twin.process_claim(
        claim=claim,
        receipts=receipts,
        context=context,
        requested_action="OPERATIONAL_AUTHORIZATION"
    )

    print(format_run_record(record))


if __name__ == "__main__":
    demo_ship_verdict()
    print("\n\n")
    demo_no_ship_verdict()
    print("\n\n")
    demo_no_ship_surveillance()
    print("\n" + "=" * 80)
    print("CALVI_TWIN demonstrations complete.")
    print("The Mediterranean does not need promises. It needs receipts.")
    print("=" * 80)
