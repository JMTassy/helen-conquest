#!/usr/bin/env python3
"""
Golden Loop Test: ORACLE TOWN V2 Deterministic Integration Test

Validates end-to-end flow:
1. Create claim.json
2. District produces engineering.attestation.json
3. District produces legal.attestation.json
4. Mayor reads all and produces decision_record.json

Result: Same inputs → identical decision_record.json (deterministic)
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add repo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kernel.canonical_json import to_canonical_json
from kernel.hashing import sha256_canonical_json, sha256_str
from tools.mayor_v2 import MayorV2


def create_test_claim() -> dict:
    """Create a simple test claim"""
    return {
        "claim_id": "C-0001",
        "text": "Implement K-ρ viability gates for decision governance",
        "claim_class": "VIABILITY",
        "requires": {
            "k_rho": True,
            "wul": False,
        },
    }


def create_engineering_attestation(claim: dict) -> dict:
    """District produces engineering attestation"""
    attestation = {
        "schema": "oracle_town.district_attestation.v2",
        "district": "ENGINEERING",
        "attestation_id": "A-ENG-0001",
        "claim_id": claim["claim_id"],
        "attestation_type": "ENGINEERING_REVIEW",
        "verdict": "PASS",
        "reason_codes": ["DESIGN_VERIFIED", "RHO_REQUIREMENTS_MET"],
        "artifacts": [
            {
                "path": "artifacts/rho_summary.json",
                "sha256": "abc123def456" + "0" * 50,
                "artifact_type": "rho_summary",
            }
        ],
        "receipt_refs": [
            {
                "path": "artifacts/runs/RUN-20260221-0001/receipts/plugin.rho_lint.receipt.json",
                "sha256": "def456abc123" + "0" * 50,
                "plugin_type": "rho_lint",
            }
        ],
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "author": "ENGINEERING_DISTRICT",
        },
    }

    # Compute attestation hash (excluding attestation_sha256 itself)
    att_without_hash = {k: v for k, v in attestation.items() if k != "attestation_sha256"}
    attestation["attestation_sha256"] = sha256_canonical_json(att_without_hash)

    return attestation


def create_legal_attestation(claim: dict) -> dict:
    """District produces legal attestation"""
    attestation = {
        "schema": "oracle_town.district_attestation.v2",
        "district": "LEGAL",
        "attestation_id": "A-LEG-0001",
        "claim_id": claim["claim_id"],
        "attestation_type": "LEGAL_REVIEW",
        "verdict": "PASS",
        "reason_codes": ["COMPLIANCE_VERIFIED", "NO_BLOCKING_OBLIGATIONS"],
        "artifacts": [],
        "receipt_refs": [],
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "author": "LEGAL_DISTRICT",
        },
    }

    # Compute attestation hash
    att_without_hash = {k: v for k, v in attestation.items() if k != "attestation_sha256"}
    attestation["attestation_sha256"] = sha256_canonical_json(att_without_hash)

    return attestation


def create_mayor_input(claim: dict, eng_att: dict, leg_att: dict) -> dict:
    """Assemble mayor_input.json from claim and attestations"""
    mayor_input = {
        "schema": "oracle_town.mayor_input.v2",
        "run_id": "RUN-20260221-0001",
        "claim": claim,
        "registries": {
            "plugins_allowlist_sha256": "pluginsha" + "0" * 56,
            "reason_codes_sha256": "reasonsha" + "0" * 56,
            "role_codes_sha256": "rolecodesha" + "0" * 54,
        },
        "attestations": [eng_att, leg_att],
        "policy": {
            "termination_policy_sha256": "policysha" + "0" * 56,
            "mode": "DELIVER_OR_ABORT",
        },
    }
    return mayor_input


def write_fixture(path: str, data: dict) -> str:
    """Write fixture as canonical JSON and return hash"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    canonical = to_canonical_json(data)
    p.write_text(canonical, encoding="utf-8")
    return sha256_str(canonical)


def main():
    """Run golden loop test"""
    test_dir = Path("runs/golden_loop")
    test_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GOLDEN LOOP TEST: ORACLE TOWN V2")
    print("=" * 70)

    # Step 1: Create claim
    print("\n[1] Creating claim...")
    claim = create_test_claim()
    claim_hash = write_fixture(str(test_dir / "claim.json"), claim)
    print(f"    ✓ claim.json ({claim_hash[:8]}...)")

    # Step 2: Engineering attestation
    print("\n[2] Engineering district attests...")
    eng_att = create_engineering_attestation(claim)
    eng_hash = write_fixture(str(test_dir / "districts" / "engineering.attestation.json"), eng_att)
    print(f"    ✓ engineering.attestation.json ({eng_hash[:8]}...)")
    print(f"      Verdict: {eng_att['verdict']}")
    print(f"      Reasons: {', '.join(eng_att['reason_codes'])}")

    # Step 3: Legal attestation
    print("\n[3] Legal district attests...")
    leg_att = create_legal_attestation(claim)
    leg_hash = write_fixture(str(test_dir / "districts" / "legal.attestation.json"), leg_att)
    print(f"    ✓ legal.attestation.json ({leg_hash[:8]}...)")
    print(f"      Verdict: {leg_att['verdict']}")
    print(f"      Reasons: {', '.join(leg_att['reason_codes'])}")

    # Step 4: Mayor input
    print("\n[4] Assembling mayor input...")
    mayor_input = create_mayor_input(claim, eng_att, leg_att)
    mayor_input_hash = write_fixture(str(test_dir / "mayor_input.json"), mayor_input)
    print(f"    ✓ mayor_input.json ({mayor_input_hash[:8]}...)")

    # Step 5: Mayor decides
    print("\n[5] Mayor decides...")
    mayor = MayorV2(str(test_dir / "mayor_input.json"))

    if not mayor.make_decision():
        print("    ✗ Mayor decision failed")
        return 1

    decision_record = mayor.decision_record
    if not mayor.emit_decision(str(test_dir / "decision_record.json")):
        print("    ✗ Failed to emit decision")
        return 1

    print(f"    ✓ decision_record.json emitted")
    print(f"      Decision: {decision_record['decision']}")
    print(f"      Reason codes: {', '.join(decision_record['reason_codes'])}")
    print(f"      Active constraint: {decision_record.get('active_constraint', 'NONE')}")

    # Verify determinism: Run again with same inputs
    print("\n[6] Verifying determinism...")
    mayor2 = MayorV2(str(test_dir / "mayor_input.json"))

    if not mayor2.make_decision():
        print("    ✗ Second run failed")
        return 1

    decision_record2 = mayor2.decision_record

    # Compare decisions
    if decision_record["decision"] != decision_record2["decision"]:
        print("    ✗ Decisions differ!")
        return 1

    if decision_record["decision_sha256"] != decision_record2["decision_sha256"]:
        print("    ✗ Decision hashes differ!")
        return 1

    print(f"    ✓ Deterministic: Same hash ({decision_record['decision_sha256'][:16]}...)")

    print("\n" + "=" * 70)
    print("✓ GOLDEN LOOP TEST PASSED")
    print("=" * 70)
    print(f"\nTest artifacts in: {test_dir}")
    print(f"  - claim.json")
    print(f"  - districts/engineering.attestation.json")
    print(f"  - districts/legal.attestation.json")
    print(f"  - mayor_input.json")
    print(f"  - decision_record.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
