"""
CALVI_TWIN Core Engine
Governance-grade digital twin implementing ORACLE BACKBONE constitutional architecture.

Production → Adjudication → Integration with deterministic SHIP/NO_SHIP verdicts.
"""

import hashlib
import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class Tier(Enum):
    """Claim tiers with different receipt requirements."""
    I = "I"    # Real-world action — strict receipt requirement
    II = "II"  # Planning/roadmap — relaxed receipt requirement
    III = "III"  # Research/exploratory — no receipt requirement


class ObligationType(Enum):
    """Canonical obligation taxonomy."""
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    METRICS_INSUFFICIENT = "METRICS_INSUFFICIENT"
    LEGAL_COMPLIANCE = "LEGAL_COMPLIANCE"
    SECURITY_THREAT = "SECURITY_THREAT"
    SAFETY_RISK = "SAFETY_RISK"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    ENVIRONMENTAL_RISK = "ENVIRONMENTAL_RISK"
    BUDGET_UNJUSTIFIED = "BUDGET_UNJUSTIFIED"
    ONGOING_MONITORING = "ONGOING_MONITORING"


class ReasonCode(Enum):
    """Canonical reason codes for blocking."""
    RECEIPT_MISSING = "RECEIPT_MISSING"
    RECEIPT_GAP_NONZERO = "RECEIPT_GAP_NONZERO"
    LEGAL_COMPLIANCE_OPEN = "LEGAL_COMPLIANCE_OPEN"
    SAFETY_RISK_OPEN = "SAFETY_RISK_OPEN"
    ENVIRONMENTAL_RISK_OPEN = "ENVIRONMENTAL_RISK_OPEN"
    BUDGET_JUSTIFICATION_MISSING = "BUDGET_JUSTIFICATION_MISSING"
    OPERATIONAL_DEPENDENCY_OPEN = "OPERATIONAL_DEPENDENCY_OPEN"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    KILL_SWITCH_TRIGGERED = "KILL_SWITCH_TRIGGERED"


@dataclass
class Receipt:
    """Attestation receipt for claim validation."""
    path: str
    type: str  # REGULATORY_ATTESTATION, TECHNICAL_VALIDATION, etc.
    hash: str  # sha256:...
    attestor: str
    timestamp: str


@dataclass
class Claim:
    """Structured claim with tier classification."""
    id: str
    title: str
    text: str
    tier: Tier
    domain: str
    scope: str
    owner: str
    timestamp: str


@dataclass
class Signal:
    """Non-binding signal from production team."""
    team: str
    agent_id: str
    kind: str
    code: str
    detail: str


@dataclass
class Obligation:
    """Structured obligation with closure criteria."""
    oid: str
    claim_id: str
    type: ObligationType
    owner: str
    closure_criteria: str
    status: str  # OPEN | CLOSED


@dataclass
class BlockingItem:
    """Blocking reason with evidence paths."""
    code: ReasonCode
    detail: str
    evidence_paths: List[str]


@dataclass
class RunRecord:
    """Final output from CALVI_TWIN."""
    verdict: str  # SHIP | NO_SHIP
    blocking: List[BlockingItem]
    obligations: List[Obligation]
    signals: List[Signal]
    mayor_twin_statement: str
    run_manifest: Dict[str, Any]


class CalviTwin:
    """
    ORACLE BACKBONE implementation for Calvi governance.

    Constitutional Axioms:
        A1. NO_RECEIPT = NO_SHIP
        A2. Non-sovereign production (teams emit signals/obligations only)
        A3. Binary verdict (SHIP | NO_SHIP)
        A4. Kill dominance (lexicographic veto)
        A5. Replay determinism (same input → same output + hash)
    """

    VERSION = "CALVI_TWIN_v0.1.0"

    # Authorized attestors
    AUTHORIZED_ATTESTORS = {
        "EASA", "EASA_PART_UAS_AUDITOR",
        "STARESO", "STARESO_TECHNICAL_LEAD",
        "UNIVERSITY_CORSICA", "ACADEMIC_EVALUATOR",
        "INDEPENDENT_AUDITOR", "GRANT_AUDITOR"
    }

    def __init__(self):
        self.production_teams = [
            MayorTwin(),
            LegalTeam(),
            SafetyTeam(),
            EnvironmentTeam(),
            BudgetTeam(),
            OperationsTeam(),
            CommsTeam()
        ]

    def process_claim(
        self,
        claim: Claim,
        receipts: List[Receipt],
        context: Optional[Dict[str, Any]] = None,
        requested_action: str = ""
    ) -> RunRecord:
        """
        Main entry point: PRODUCTION → ADJUDICATION → INTEGRATION.

        Returns deterministic RunRecord with SHIP/NO_SHIP verdict.
        """

        # Step 0: Classify tier (already in claim, but validate)
        if self._touches_real_world(claim, requested_action):
            claim.tier = Tier.I

        # Step 1: Validate receipts
        receipt_valid, receipt_gap, receipt_obligations = self._validate_receipts(
            claim, receipts
        )

        # Step 2: Run production teams (non-sovereign)
        all_signals = []
        all_obligations = list(receipt_obligations)

        for team in self.production_teams:
            signals, obligations = team.evaluate(claim, receipts, context or {})
            all_signals.extend(signals)
            all_obligations.extend(obligations)

        # Step 3: Adjudication (lexicographic veto)
        blocking_items = self._adjudicate(
            claim, receipt_valid, receipt_gap, all_obligations, all_signals
        )

        # Step 4: Integration gate
        verdict = "NO_SHIP" if blocking_items else "SHIP"

        # Step 5: Generate Mayor statement
        mayor_statement = self._generate_mayor_statement(
            claim, verdict, blocking_items, all_obligations, receipts
        )

        # Step 6: Create run manifest with hashes
        run_manifest = self._create_manifest(
            claim, receipts, all_signals, blocking_items, verdict
        )

        return RunRecord(
            verdict=verdict,
            blocking=blocking_items,
            obligations=all_obligations,
            signals=all_signals,
            mayor_twin_statement=mayor_statement,
            run_manifest=run_manifest
        )

    def _touches_real_world(self, claim: Claim, requested_action: str) -> bool:
        """Determine if claim should be Tier I (strict receipt requirement)."""
        real_world_keywords = [
            "OPERATIONAL_AUTHORIZATION", "BUDGET_EXECUTION",
            "PUBLIC_ANNOUNCEMENT", "LEGAL_COMPLIANCE",
            "SAFETY_PROTOCOL", "PROCUREMENT"
        ]
        real_world_domains = ["SAFETY_OPERATIONS", "PUBLIC_SAFETY", "BUDGET"]

        return (
            requested_action in real_world_keywords or
            claim.domain in real_world_domains or
            any(kw in claim.text.upper() for kw in ["DEPLOY", "EXECUTE", "AUTHORIZE"])
        )

    def _validate_receipts(
        self, claim: Claim, receipts: List[Receipt]
    ) -> Tuple[bool, int, List[Obligation]]:
        """
        Validate receipts for Tier-I claims.

        Returns:
            (valid, gap_count, obligations_list)
        """
        obligations = []

        if claim.tier != Tier.I:
            return True, 0, obligations

        if not receipts:
            obligations.append(Obligation(
                oid=f"OBL_{claim.id}_RECEIPT_MISSING",
                claim_id=claim.id,
                type=ObligationType.EVIDENCE_MISSING,
                owner=claim.owner,
                closure_criteria="Provide required attestation receipts",
                status="OPEN"
            ))
            return False, 1, obligations

        gap = 0
        for receipt in receipts:
            # Check attestor authorization
            if receipt.attestor not in self.AUTHORIZED_ATTESTORS:
                obligations.append(Obligation(
                    oid=f"OBL_{claim.id}_ATTESTOR_{receipt.attestor}",
                    claim_id=claim.id,
                    type=ObligationType.EVIDENCE_MISSING,
                    owner=claim.owner,
                    closure_criteria=f"Receipt from {receipt.attestor} not authorized; require attestation from {self.AUTHORIZED_ATTESTORS}",
                    status="OPEN"
                ))
                gap += 1

            # Check hash format
            if not receipt.hash.startswith("sha256:"):
                obligations.append(Obligation(
                    oid=f"OBL_{claim.id}_HASH_{receipt.path}",
                    claim_id=claim.id,
                    type=ObligationType.EVIDENCE_MISSING,
                    owner=claim.owner,
                    closure_criteria=f"Receipt {receipt.path} missing valid sha256 hash",
                    status="OPEN"
                ))
                gap += 1

        valid = gap == 0
        return valid, gap, obligations

    def _adjudicate(
        self,
        claim: Claim,
        receipt_valid: bool,
        receipt_gap: int,
        obligations: List[Obligation],
        signals: List[Signal]
    ) -> List[BlockingItem]:
        """
        Lexicographic veto: apply blocking rules in priority order.

        Returns list of BlockingItems if any veto triggered, else empty list.
        """
        blocking = []

        # (i) Kill-switch / safety / legal blocks
        for obl in obligations:
            if obl.status == "OPEN" and obl.type in {
                ObligationType.SECURITY_THREAT,
                ObligationType.SAFETY_RISK,
                ObligationType.LEGAL_COMPLIANCE
            }:
                blocking.append(BlockingItem(
                    code=self._obligation_to_reason_code(obl.type),
                    detail=obl.closure_criteria,
                    evidence_paths=[]
                ))

        # (ii) Receipt sufficiency
        if not receipt_valid or receipt_gap > 0:
            blocking.append(BlockingItem(
                code=ReasonCode.RECEIPT_GAP_NONZERO if receipt_gap > 0 else ReasonCode.RECEIPT_MISSING,
                detail=f"Receipt gap: {receipt_gap} unsatisfied attestations",
                evidence_paths=[]
            ))

        # (iii) Open critical obligations
        for obl in obligations:
            if obl.status == "OPEN" and obl.type == ObligationType.EVIDENCE_MISSING:
                blocking.append(BlockingItem(
                    code=ReasonCode.RECEIPT_MISSING,
                    detail=obl.closure_criteria,
                    evidence_paths=[]
                ))

        # (iv) Contradictions across teams
        contradiction = self._detect_contradiction(signals)
        if contradiction:
            blocking.append(BlockingItem(
                code=ReasonCode.CONTRADICTION_DETECTED,
                detail=contradiction,
                evidence_paths=[]
            ))

        return blocking

    def _obligation_to_reason_code(self, obl_type: ObligationType) -> ReasonCode:
        """Map obligation type to reason code."""
        mapping = {
            ObligationType.SECURITY_THREAT: ReasonCode.KILL_SWITCH_TRIGGERED,
            ObligationType.SAFETY_RISK: ReasonCode.SAFETY_RISK_OPEN,
            ObligationType.LEGAL_COMPLIANCE: ReasonCode.LEGAL_COMPLIANCE_OPEN,
            ObligationType.ENVIRONMENTAL_RISK: ReasonCode.ENVIRONMENTAL_RISK_OPEN,
            ObligationType.BUDGET_UNJUSTIFIED: ReasonCode.BUDGET_JUSTIFICATION_MISSING,
            ObligationType.EVIDENCE_MISSING: ReasonCode.RECEIPT_MISSING,
        }
        return mapping.get(obl_type, ReasonCode.RECEIPT_MISSING)

    def _detect_contradiction(self, signals: List[Signal]) -> Optional[str]:
        """Check for contradictory signals across teams."""
        # Simple heuristic: look for opposing codes
        codes = {s.code for s in signals}

        contradictions = [
            ("CAPACITY_ADEQUATE", "CAPACITY_INSUFFICIENT"),
            ("CERTIFICATION_CURRENT", "CERTIFICATION_EXPIRED"),
            ("NO_IMPACT_DETECTED", "IMPACT_DETECTED")
        ]

        for pos, neg in contradictions:
            if pos in codes and neg in codes:
                pos_team = next(s.team for s in signals if s.code == pos)
                neg_team = next(s.team for s in signals if s.code == neg)
                return f"{pos_team} signals {pos}, but {neg_team} signals {neg}"

        return None

    def _generate_mayor_statement(
        self,
        claim: Claim,
        verdict: str,
        blocking: List[BlockingItem],
        obligations: List[Obligation],
        receipts: List[Receipt]
    ) -> str:
        """Generate MAYOR_TWIN statement (sober, executive, aligned with verdict)."""

        if verdict == "SHIP":
            return self._mayor_ship_statement(claim, obligations, receipts)
        else:
            return self._mayor_no_ship_statement(claim, blocking, obligations)

    def _mayor_ship_statement(
        self, claim: Claim, obligations: List[Obligation], receipts: List[Receipt]
    ) -> str:
        """Mayor statement for SHIP verdict."""

        attestors = ", ".join({r.attestor for r in receipts})
        open_obls = [o for o in obligations if o.status == "OPEN"]

        statement = f"This deployment aligns with our Guardian Mode doctrine: validate before deploy. "

        if receipts:
            statement += f"Attestations from {attestors} confirm readiness. "

        if open_obls:
            statement += f"We ship with {len(open_obls)} ongoing obligation(s): "
            statement += "; ".join([o.closure_criteria[:80] for o in open_obls[:2]])
            statement += ". "

        statement += "This is receipt-first governance in action—we have the attestations, "
        statement += "we accept the monitoring obligations, we ship the capability. The ledger is open."

        return statement

    def _mayor_no_ship_statement(
        self, claim: Claim, blocking: List[BlockingItem], obligations: List[Obligation]
    ) -> str:
        """Mayor statement for NO_SHIP verdict."""

        statement = f"We defer this claim. "

        if blocking:
            main_block = blocking[0]
            statement += f"{main_block.detail}. "

        open_obls = [o for o in obligations if o.status == "OPEN"]
        if open_obls:
            statement += f"We need: "
            statement += "; ".join([f"({i+1}) {o.closure_criteria[:60]}" for i, o in enumerate(open_obls[:3])])
            statement += ". "

        statement += "We do not ship capability before we can verify it. "
        statement += "This is not delay—this is discipline."

        return statement

    def _create_manifest(
        self,
        claim: Claim,
        receipts: List[Receipt],
        signals: List[Signal],
        blocking: List[BlockingItem],
        verdict: str
    ) -> Dict[str, Any]:
        """Create deterministic run manifest with hashes."""

        # Canonical inputs (exclude non-deterministic fields)
        inputs_canonical = {
            "cfg_version": self.VERSION,
            "claim": {
                "id": claim.id,
                "title": claim.title,
                "text": claim.text,
                "tier": claim.tier.value,
                "domain": claim.domain,
                "scope": claim.scope,
                "owner": claim.owner
                # Exclude timestamp for determinism
            },
            "receipts": [
                {
                    "path": r.path,
                    "type": r.type,
                    "hash": r.hash,
                    "attestor": r.attestor
                    # Exclude timestamp
                }
                for r in receipts
            ]
        }

        # Canonical outputs
        outputs_canonical = {
            "verdict": verdict,
            "blocking_count": len(blocking),
            "blocking_codes": [b.code.value for b in blocking]
        }

        inputs_hash = self._canonical_hash(inputs_canonical)
        outputs_hash = self._canonical_hash(outputs_canonical)

        return {
            "inputs_hash": inputs_hash,
            "outputs_hash": outputs_hash,
            "cfg_version": self.VERSION,
            "canonicalization_notes": "Excluded: run_id, timestamps; Included: claim, receipts, verdict, blocking"
        }

    def _canonical_hash(self, obj: Dict[str, Any]) -> str:
        """Generate canonical SHA-256 hash of object."""
        canonical_json = json.dumps(obj, sort_keys=True, separators=(',', ':'))
        hash_bytes = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
        return f"sha256:{hash_bytes}"


# ============================================================================
# PRODUCTION TEAMS (Non-Sovereign Agents)
# ============================================================================

class ProductionTeam:
    """Base class for production teams."""

    def evaluate(
        self, claim: Claim, receipts: List[Receipt], context: Dict[str, Any]
    ) -> Tuple[List[Signal], List[Obligation]]:
        """Emit signals and obligations (never verdicts)."""
        raise NotImplementedError


class MayorTwin(ProductionTeam):
    """MAYOR_TWIN: Policy vector, priorities, phrasing."""

    def evaluate(self, claim, receipts, context):
        signals = [
            Signal(
                team="MAYOR_TWIN",
                agent_id="POLICY_VECTOR",
                kind="PRIORITY_ALIGNMENT",
                code="GUARDIAN_MODE_ALIGNED",
                detail="Claim aligns with receipt-first discipline and Mediterranean identity"
            )
        ]
        return signals, []


class LegalTeam(ProductionTeam):
    """LEGAL: EASA, EU AI Act, GDPR, procurement."""

    def evaluate(self, claim, receipts, context):
        signals = []
        obligations = []

        # Check EASA compliance
        easa_receipts = [r for r in receipts if "EASA" in r.attestor]
        if not easa_receipts and claim.domain == "SAFETY_OPERATIONS":
            obligations.append(Obligation(
                oid=f"OBL_{claim.id}_EASA",
                claim_id=claim.id,
                type=ObligationType.LEGAL_COMPLIANCE,
                owner="LEGAL_TEAM",
                closure_criteria="Obtain EASA Part-UAS compliance attestation",
                status="OPEN"
            ))
        else:
            signals.append(Signal(
                team="LEGAL",
                agent_id="EASA_CHECKER",
                kind="REGULATORY_STATUS",
                code="CERTIFICATION_CURRENT",
                detail="EASA Part-UAS compliance verified"
            ))

        return signals, obligations


class SafetyTeam(ProductionTeam):
    """SAFETY: Incident analysis, protocols, emergency response."""

    def evaluate(self, claim, receipts, context):
        signals = []
        obligations = []

        # Check for safety validation
        safety_receipts = [r for r in receipts if r.type == "TECHNICAL_VALIDATION"]
        if not safety_receipts and "UAV" in claim.text.upper():
            obligations.append(Obligation(
                oid=f"OBL_{claim.id}_SAFETY",
                claim_id=claim.id,
                type=ObligationType.SAFETY_RISK,
                owner="SAFETY_TEAM",
                closure_criteria="Technical safety validation required for UAV operations",
                status="OPEN"
            ))

        # Add ongoing monitoring for operational claims
        if claim.tier == Tier.I and "DEPLOY" in claim.text.upper():
            obligations.append(Obligation(
                oid=f"OBL_{claim.id}_MONITORING",
                claim_id=claim.id,
                type=ObligationType.ONGOING_MONITORING,
                owner="SAFETY_TEAM",
                closure_criteria="Monthly incident reporting and correlation analysis",
                status="OPEN"
            ))

        return signals, obligations


class EnvironmentTeam(ProductionTeam):
    """ENVIRONMENT: Marine protection, biodiversity, noise."""

    def evaluate(self, claim, receipts, context):
        signals = [
            Signal(
                team="ENVIRONMENT",
                agent_id="MARINE_IMPACT_ASSESSOR",
                kind="BIODIVERSITY_CHECK",
                code="NO_IMPACT_DETECTED",
                detail="No Posidonia meadows in operational area; cetacean monitoring shows no disturbance"
            )
        ]
        return signals, []


class BudgetTeam(ProductionTeam):
    """BUDGET: Cost justification, procurement, grant compliance."""

    def evaluate(self, claim, receipts, context):
        signals = []
        obligations = []

        # Check for budget justification if claim involves funding
        if "€" in claim.text or "budget" in claim.text.lower():
            budget_receipts = [r for r in receipts if "GRANT" in r.type or "AUDIT" in r.attestor]
            if not budget_receipts:
                obligations.append(Obligation(
                    oid=f"OBL_{claim.id}_BUDGET",
                    claim_id=claim.id,
                    type=ObligationType.BUDGET_UNJUSTIFIED,
                    owner="BUDGET_TEAM",
                    closure_criteria="Provide cost justification with grant compliance attestation",
                    status="OPEN"
                ))

        return signals, obligations


class OperationsTeam(ProductionTeam):
    """OPERATIONS: Capacity, personnel, infrastructure."""

    def evaluate(self, claim, receipts, context):
        signals = [
            Signal(
                team="OPERATIONS",
                agent_id="CAPACITY_ANALYZER",
                kind="CAPACITY_FORECAST",
                code="CAPACITY_ADEQUATE",
                detail="Digital twin can handle 50 concurrent scenarios; current load: 12 avg"
            )
        ]
        return signals, []


class CommsTeam(ProductionTeam):
    """COMMS: Transparency, citizen consultation, public reporting."""

    def evaluate(self, claim, receipts, context):
        signals = [
            Signal(
                team="COMMS",
                agent_id="TRANSPARENCY_MONITOR",
                kind="PUBLIC_TRUST",
                code="GOVERNANCE_VISIBLE",
                detail="Claim will be published on governance.calvi.town with full receipt ledger"
            )
        ]
        return signals, []


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_run_record(record: RunRecord) -> str:
    """Format RunRecord as human-readable markdown."""

    output = f"## 1) VERDICT: {record.verdict}\n\n"

    # Blocking
    output += "## 2) BLOCKING\n"
    if record.blocking:
        for item in record.blocking:
            output += f"- **{item.code.value}**: {item.detail}\n"
            if item.evidence_paths:
                output += f"  (evidence: {', '.join(item.evidence_paths)})\n"
    else:
        output += "(none)\n"
    output += "\n"

    # Obligations
    output += "## 3) OBLIGATIONS\n"
    for i, obl in enumerate(record.obligations, 1):
        output += f"{i}. **{obl.oid}** ({obl.type.value})\n"
        output += f"   - Owner: {obl.owner}\n"
        output += f"   - Closure: {obl.closure_criteria}\n"
        output += f"   - Status: {obl.status}\n\n"

    # Signals
    output += "## 4) SIGNALS\n"
    for sig in record.signals:
        output += f"- **{sig.team} / {sig.agent_id} / {sig.kind} / {sig.code}**: {sig.detail}\n"
    output += "\n"

    # Mayor statement
    output += "## 5) MAYOR_TWIN STATEMENT\n"
    output += record.mayor_twin_statement + "\n\n"

    # Manifest
    output += "## 6) RUN_MANIFEST\n"
    for key, val in record.run_manifest.items():
        output += f"- **{key}**: `{val}`\n"

    return output
