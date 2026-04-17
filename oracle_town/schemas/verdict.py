"""Town and Mayor Verdict Schemas"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .reports import DistrictVerdict
from .claim import Obligation


@dataclass
class TownRecommendation:
    """Integrated recommendation from Town Hall"""
    district_verdicts: List[DistrictVerdict]
    qi_int_score: float  # Complex amplitude sum → |A_c|²
    invariants_check: Dict[str, bool]
    blocking_obligations: List[Obligation]
    kill_switch_triggered: bool
    recommendation: str  # "GO" | "NO_GO"
    confidence: float

    def to_dict(self):
        return {
            "district_verdicts": [d.to_dict() for d in self.district_verdicts],
            "qi_int_score": self.qi_int_score,
            "invariants_check": self.invariants_check,
            "blocking_obligations": [o.to_dict() for o in self.blocking_obligations],
            "kill_switch_triggered": self.kill_switch_triggered,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
        }


@dataclass
class RemediationStep:
    """Single step in remediation roadmap"""
    step_id: str
    obligation_id: str
    description: str
    required_evidence: List[str]
    estimated_effort: str  # "low" | "medium" | "high"
    estimated_timeline: str  # e.g. "1 week", "2 weeks"
    responsible: str  # Which building/district
    tier_downgrade: Optional[str] = None  # "A→B" | "A→C" | "B→C"
    success_criteria: str = ""

    def to_dict(self):
        return {
            "step_id": self.step_id,
            "obligation_id": self.obligation_id,
            "description": self.description,
            "required_evidence": self.required_evidence,
            "estimated_effort": self.estimated_effort,
            "estimated_timeline": self.estimated_timeline,
            "responsible": self.responsible,
            "tier_downgrade": self.tier_downgrade,
            "success_criteria": self.success_criteria,
        }


@dataclass
class MayorVerdict:
    """Final binary verdict from Mayor"""
    claim_id: str
    decision: str  # "SHIP" | "NO_SHIP"
    rationale: str
    evidence_bundle: List[str]
    blocking_reasons: List[str] = field(default_factory=list)
    remediation_roadmap: List[RemediationStep] = field(default_factory=list)
    timestamp: str = ""
    code_version: str = ""  # Git hash for replay

    def to_dict(self):
        return {
            "claim_id": self.claim_id,
            "decision": self.decision,
            "rationale": self.rationale,
            "evidence_bundle": self.evidence_bundle,
            "blocking_reasons": self.blocking_reasons,
            "remediation_roadmap": [s.to_dict() for s in self.remediation_roadmap],
            "timestamp": self.timestamp,
            "code_version": self.code_version,
        }
