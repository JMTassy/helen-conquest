"""
ORACLE 2: BUILDERS — Reference Implementation
Version: 2.0-FINAL

Core Principle: ORACLE 1 = Judge, ORACLE 2 = Mechanic

ORACLE 2 takes NO_SHIP verdicts and produces strictly weaker, testable V2 proposals.
BUILDERS NEVER DECIDES TRUTH. IT ONLY PREPARES ADMISSIBLE ARTIFACTS.
"""

from dataclasses import dataclass, asdict
from typing import Literal, Optional, List, Dict, Any
import json
import hashlib
from datetime import datetime


# ============================================================================
# TYPE DEFINITIONS (LOCKED)
# ============================================================================

ObligationStatus = Literal["OPEN", "SATISFIED", "WAIVED", "INVALID"]

ObligationType = Literal[
    "BASELINE_REQUIRED",
    "INSTRUMENTATION_INTEGRITY",
    "ATTESTATION_REQUIRED",
    "SECURITY_REVIEW",
    "LEGAL_REVIEW",
    "PRIVACY_REVIEW",
    "REPRODUCIBILITY_REQUIRED",
    "OTHER"
]

ObligationSeverity = Literal["HARD", "SOFT"]

ExpectedAttestor = Literal[
    "METRIC_SNAPSHOT",
    "TOOL_RESULT",
    "CODE_PROOF",
    "AUDITOR_REPORT",
    "LEGAL_DOC",
    "PRIVACY_DOC",
    "HUMAN_REVIEW",
    "NONE"
]

ReasonCode = Literal[
    "NO_RECEIPT",
    "MISSING_BASELINE",
    "MISSING_INSTRUMENTATION",
    "MISSING_ATTESTATION",
    "UNVERIFIABLE",
    "OVERSCOPED",
    "LEGAL_RISK",
    "PRIVACY_RISK",
    "SECURITY_RISK",
    "NON_DETERMINISTIC"
]


# ============================================================================
# BLOCKING OBLIGATION V1 (CANONICAL SCHEMA)
# ============================================================================

@dataclass
class BlockingObligationV1:
    """
    Canonical blocking obligation schema.

    Invariants (hard):
    1. If severity="HARD" and status="OPEN" => blocks SHIP
    2. If status="SATISFIED" => evidence_hash MUST be non-null
    3. created_at MUST be excluded from replay hash
    4. reason_codes must be sorted lexicographically
    """
    # Determinism controls
    canon_version: str  # Must be "OBL_V1"

    # Identity
    id: str             # Pattern: "O-000311"
    name: str           # snake_case label
    type: ObligationType

    # Blocking semantics
    severity: ObligationSeverity
    status: ObligationStatus

    # Attestation binding
    expected_attestor: ExpectedAttestor
    evidence_artifact: Optional[str]
    evidence_format: Optional[str]
    evidence_hash: Optional[str]

    # Governance metadata (replay-safe)
    domain: str
    tier: Literal["I", "II", "III"]
    reason: str
    reason_codes: List[ReasonCode]

    # Telemetry-only (excluded from replay hash)
    created_at: Optional[str] = None

    def __post_init__(self):
        """Validate invariants."""
        if self.canon_version != "OBL_V1":
            raise ValueError(f"Invalid canon_version: {self.canon_version}")

        if self.status == "SATISFIED" and not self.evidence_hash:
            raise ValueError(f"SATISFIED obligation {self.id} missing evidence_hash")

        # Sort reason codes
        self.reason_codes = sorted(set(self.reason_codes))


# ============================================================================
# V2 PROPOSAL STRUCTURES
# ============================================================================

@dataclass
class TierBProposal:
    """Measurable, testable downgrade."""
    metric: str
    baseline: Dict[str, Any]
    acceptance_gate: Dict[str, Any]


@dataclass
class TierCProposal:
    """Narrative, qualitative downgrade."""
    narrative: str
    caveats: List[str]


@dataclass
class DeltaEntry:
    """Change log entry."""
    change: str
    reason: str


@dataclass
class AcceptanceGate:
    """Gate that must be satisfied before SHIP."""
    id: str
    obligation_id: str
    pass_fail: bool  # Always false initially
    description: str


@dataclass
class V2Proposal:
    """
    Strictly weaker V2 proposal.

    Hard Rules:
    - tier_a is ALWAYS None (no Tier I claims)
    - tier_b = measurable downgrade
    - tier_c = narrative downgrade
    - All acceptance_gates start with pass_fail=False
    """
    tier_a: None                        # ALWAYS None
    tier_b: Optional[TierBProposal]
    tier_c: Optional[TierCProposal]
    delta_log: List[DeltaEntry]
    acceptance_gates: List[AcceptanceGate]
    ship_score: int                     # Remaining blockers
    disclaimer: str                     # Required


# ============================================================================
# DETERMINISTIC CANONICALIZATION
# ============================================================================

def canon(obj: Dict) -> bytes:
    """
    Deterministic hash view:
    - UTF-8 JSON
    - Stable key ordering (lexicographic)
    - No whitespace
    - Exclude: *.created_at, timestamps, run IDs
    """
    # Remove telemetry fields
    clean_obj = {k: v for k, v in obj.items() if k != "created_at"}

    return json.dumps(
        clean_obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':')
    ).encode('utf-8')


def obligation_sort_key(obl: Dict) -> tuple:
    """
    Enforce single deterministic ordering.
    """
    severity_rank = 0 if obl["severity"] == "HARD" else 1
    status_rank = {
        "OPEN": 0,
        "SATISFIED": 1,
        "WAIVED": 2,
        "INVALID": 3
    }[obl["status"]]

    return (
        severity_rank,
        status_rank,
        obl["expected_attestor"],
        obl["type"],
        obl["name"],
        obl["id"]
    )


# ============================================================================
# REMEDIATION ENGINE (MINIMAL, DETERMINISTIC)
# ============================================================================

def propose_tier_b_metric(obl: BlockingObligationV1) -> TierBProposal:
    """Generate Tier B metric proposal from obligation."""
    metric_name = obl.name.replace("_required", "").replace("_", ".")

    return TierBProposal(
        metric=metric_name,
        baseline={
            "value": None,
            "measured_at": None,
            "requires_collection": True
        },
        acceptance_gate={
            "condition": f"Verify {obl.expected_attestor}",
            "evidence_type": obl.expected_attestor
        }
    )


def downgrade_to_narrative(obl: BlockingObligationV1) -> TierCProposal:
    """Generate Tier C narrative proposal from obligation."""
    return TierCProposal(
        narrative=f"Pending resolution of {obl.name}",
        caveats=[
            f"{obl.type} not yet completed",
            "This is a weakened claim pending evidence"
        ]
    )


def remediate(
    original_claim: Dict,
    blocking_obligations: List[BlockingObligationV1]
) -> V2Proposal:
    """
    Deterministic remediation engine.

    For each blocker:
    - If metric missing → propose Tier B metric
    - If scope too broad → shrink scope
    - If unverifiable → downgrade to narrative

    Emit:
    - delta_log
    - acceptance_gates (all false)
    - ship_score = count of remaining blockers
    """
    v2 = {
        "tier_a": None,  # ALWAYS None
        "tier_b": None,
        "tier_c": None,
        "delta_log": [],
        "acceptance_gates": [],
        "ship_score": 0,
        "disclaimer": ""
    }

    for obl_dict in blocking_obligations:
        # Convert to dataclass if needed
        if isinstance(obl_dict, dict):
            obl = BlockingObligationV1(**obl_dict)
        else:
            obl = obl_dict

        if obl.status != "OPEN":
            continue

        v2["ship_score"] += 1

        if obl.type == "BASELINE_REQUIRED":
            v2["tier_b"] = asdict(propose_tier_b_metric(obl))
            v2["delta_log"].append({
                "change": "Added baseline metric requirement",
                "reason": obl.reason
            })
            v2["acceptance_gates"].append({
                "id": f"gate-{obl.id}",
                "obligation_id": obl.id,
                "pass_fail": False,
                "description": "Baseline metric verified"
            })

        elif obl.type == "INSTRUMENTATION_INTEGRITY":
            v2["tier_b"] = asdict(propose_tier_b_metric(obl))
            v2["delta_log"].append({
                "change": "Added instrumentation integrity check",
                "reason": obl.reason
            })
            v2["acceptance_gates"].append({
                "id": f"gate-{obl.id}",
                "obligation_id": obl.id,
                "pass_fail": False,
                "description": "Instrumentation verified via CODE_PROOF"
            })

        elif obl.type == "ATTESTATION_REQUIRED":
            v2["tier_c"] = asdict(downgrade_to_narrative(obl))
            v2["delta_log"].append({
                "change": "Downgraded to narrative (attestation pending)",
                "reason": obl.reason
            })
            v2["disclaimer"] += f"\n⚠️  Pending attestation: {obl.name}"

        elif obl.type in ["LEGAL_REVIEW", "PRIVACY_REVIEW", "SECURITY_REVIEW"]:
            v2["tier_c"] = asdict(downgrade_to_narrative(obl))
            v2["delta_log"].append({
                "change": f"Downgraded to narrative ({obl.type} pending)",
                "reason": obl.reason
            })
            v2["disclaimer"] += f"\n⚠️  Pending {obl.type}: {obl.name}"

        elif obl.type == "REPRODUCIBILITY_REQUIRED":
            tier_b_prop = propose_tier_b_metric(obl)
            tier_b_prop.acceptance_gate["requires_replay_manifest"] = True
            v2["tier_b"] = asdict(tier_b_prop)
            v2["delta_log"].append({
                "change": "Added hashable artifacts requirement",
                "reason": obl.reason
            })
            v2["acceptance_gates"].append({
                "id": f"gate-{obl.id}",
                "obligation_id": obl.id,
                "pass_fail": False,
                "description": "Replay manifest verified"
            })

        else:  # OTHER
            v2["tier_c"] = asdict(downgrade_to_narrative(obl))
            v2["delta_log"].append({
                "change": "Downgraded to narrative (unverifiable)",
                "reason": obl.reason
            })

    # Ensure disclaimer is non-empty
    if not v2["disclaimer"]:
        v2["disclaimer"] = "⚠️  This is a V2 proposal. Original claim was blocked."

    return v2


# ============================================================================
# CI VALIDATION GATES
# ============================================================================

def validate_schema(obl: Dict) -> bool:
    """
    Gate 1: Schema validation.

    Validates against BlockingObligationV1 schema.
    """
    required_fields = [
        "canon_version", "id", "name", "type", "severity", "status",
        "expected_attestor", "evidence_artifact", "evidence_format",
        "evidence_hash", "domain", "tier", "reason", "reason_codes"
    ]

    for field in required_fields:
        if field not in obl:
            raise ValueError(f"Missing required field: {field}")

    if obl["canon_version"] != "OBL_V1":
        raise ValueError(f"Invalid canon_version: {obl['canon_version']}")

    return True


def validate_contract(obl: Dict) -> bool:
    """
    Gate 2: Contract validation.

    If status="SATISFIED" then evidence_hash != null.
    """
    if obl["status"] == "SATISFIED" and not obl["evidence_hash"]:
        raise ValueError(f"SATISFIED obligation {obl['id']} missing evidence_hash")

    return True


def validate_replay(obl: Dict) -> bool:
    """
    Gate 3: Replay determinism.

    Re-hash canon(obligation) twice => identical SHA-256.
    """
    hash1 = hashlib.sha256(canon(obl)).hexdigest()
    hash2 = hashlib.sha256(canon(obl)).hexdigest()

    if hash1 != hash2:
        raise ValueError(f"Non-deterministic hash for {obl['id']}")

    return True


def validate_reason_codes(obl: Dict) -> bool:
    """
    Gate 5: Reason codes must be sorted and unique.
    """
    codes = obl["reason_codes"]
    sorted_unique = sorted(set(codes))

    if codes != sorted_unique:
        raise ValueError(f"Reason codes not sorted/unique for {obl['id']}")

    return True


def validate_ordering(obligations: List[Dict]) -> bool:
    """
    Gate 4: Obligations must be sorted by obligation_sort_key.
    """
    sorted_obls = sorted(obligations, key=obligation_sort_key)

    if obligations != sorted_obls:
        raise ValueError("Obligations not properly sorted")

    return True


def ci_validate_obligations(obligations: List[Dict]):
    """
    Run all CI gates. Fail fast on any violation.
    """
    for obl in obligations:
        validate_schema(obl)
        validate_contract(obl)
        validate_replay(obl)
        validate_reason_codes(obl)

    validate_ordering(obligations)

    print("✅ All CI gates passed")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_oracle_2_builders(original_claim: Dict, verdict: Dict) -> Dict:
    """
    Main ORACLE 2 BUILDERS pipeline.

    Input Contract (LOCKED):
    {
        "original_claim": Claim,
        "verdict": {
            "decision": "NO_SHIP",
            "blocking": BlockingObligationV1[]
        }
    }

    Output Contract (LOCKED):
    {
        "v2_proposal": V2Proposal
    }
    """
    # Hard rule: If SHIP, do nothing
    if verdict.get("decision") != "NO_SHIP":
        return {
            "v2_proposal": None,
            "reason": "Original claim was SHIP - no remediation needed"
        }

    # Get blocking obligations
    blocking = verdict.get("blocking", [])

    # Run CI validation
    ci_validate_obligations(blocking)

    # Generate V2 proposal
    v2_proposal = remediate(original_claim, blocking)

    return {
        "v2_proposal": v2_proposal,
        "timestamp": datetime.now().isoformat(),
        "oracle_version": "2.0-FINAL"
    }


# ============================================================================
# CLI COMMANDS
# ============================================================================

def cmd_remediation_sample(domain: str = "engineering") -> Dict:
    """
    Command: legoracle remediation-sample --domain engineering

    Returns canonical example obligation.
    """
    return {
        "canon_version": "OBL_V1",
        "id": "O-000311",
        "name": "baseline_required",
        "type": "BASELINE_REQUIRED",
        "severity": "HARD",
        "status": "OPEN",
        "expected_attestor": "METRIC_SNAPSHOT",
        "evidence_artifact": None,
        "evidence_format": None,
        "evidence_hash": None,
        "domain": domain,
        "tier": "II",
        "reason": f"No pre-change baseline for metric X in {domain}",
        "reason_codes": ["MISSING_BASELINE"]
    }


def cmd_remediation_template(domain: str = "marketing") -> Dict:
    """
    Command: legoracle remediation-template --domain marketing

    Returns blank V2 scaffold.
    """
    return {
        "v2_proposal": {
            "tier_a": None,
            "tier_b": None,
            "tier_c": {
                "narrative": "[YOUR NARRATIVE HERE]",
                "caveats": ["Template only - replace with actual proposal"]
            },
            "delta_log": [],
            "acceptance_gates": [],
            "ship_score": 0,
            "disclaimer": "⚠️  Template only. Replace with actual proposal."
        }
    }


# ============================================================================
# DEMO EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ORACLE 2: BUILDERS — Demo Execution")
    print("="*60)

    # Example input (from ORACLE 1 NO_SHIP verdict)
    original_claim = {
        "assertion": "Reduce API latency to < 100ms p99 without external dependencies"
    }

    verdict = {
        "decision": "NO_SHIP",
        "blocking": [
            {
                "canon_version": "OBL_V1",
                "id": "O-000311",
                "name": "baseline_required",
                "type": "BASELINE_REQUIRED",
                "severity": "HARD",
                "status": "OPEN",
                "expected_attestor": "METRIC_SNAPSHOT",
                "evidence_artifact": None,
                "evidence_format": None,
                "evidence_hash": None,
                "domain": "engineering",
                "tier": "II",
                "reason": "No pre-change baseline for latency p99",
                "reason_codes": ["MISSING_BASELINE"]
            }
        ]
    }

    # Run ORACLE 2 BUILDERS
    result = run_oracle_2_builders(original_claim, verdict)

    # Display results
    print("\n" + "="*60)
    print("ORACLE 1 — Verdict")
    print("="*60)
    print(f"Decision: {verdict['decision']}")
    print(f"Blocking Obligations: {len(verdict['blocking'])}")

    for obl in verdict['blocking']:
        print(f"\n{obl['id']} | {obl['name']} | {obl['severity']} | {obl['status']}")
        print(f"  Reason: {obl['reason']}")

    print("\n" + "="*60)
    print("ORACLE 2 — V2 Proposal")
    print("="*60)

    v2 = result["v2_proposal"]
    print(f"Ship Score: {v2['ship_score']} (lower is better)")

    print(f"\nTier A: {v2['tier_a']}")

    if v2['tier_b']:
        print(f"\nTier B:")
        print(f"  Metric: {v2['tier_b']['metric']}")
        print(f"  Baseline: {'REQUIRES COLLECTION' if v2['tier_b']['baseline']['requires_collection'] else 'SET'}")
        print(f"  Gate: {v2['tier_b']['acceptance_gate']['condition']} (pass_fail: false)")

    if v2['tier_c']:
        print(f"\nTier C:")
        print(f"  Narrative: {v2['tier_c']['narrative']}")

    print(f"\nDisclaimer:")
    print(v2['disclaimer'])

    print(f"\nDelta Log ({len(v2['delta_log'])} changes):")
    for delta in v2['delta_log']:
        print(f"  - {delta['change']}")

    print(f"\nAcceptance Gates ({len(v2['acceptance_gates'])} gates):")
    for gate in v2['acceptance_gates']:
        print(f"  - {gate['id']}: {gate['description']} (pass_fail: {gate['pass_fail']})")

    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Collect baseline metric")
    print("2. Generate evidence_hash")
    print("3. Re-submit with SATISFIED obligations")

    print("\n" + "="*60)
    print("✅ ORACLE 2 BUILDERS execution complete")
    print("="*60)
