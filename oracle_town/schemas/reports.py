"""Street, Building, and District Report Schemas"""
from dataclasses import dataclass, field
from typing import List, Optional
from .claim import Obligation


@dataclass
class Turn:
    """Single agent turn in conversation"""
    agent_id: str
    role: str
    contribution: str
    question: str
    action: str
    timestamp: Optional[str] = None

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "contribution": self.contribution,
            "question": self.question,
            "action": self.action,
            "timestamp": self.timestamp,
        }


@dataclass
class StreetReport:
    """Report from a single street (4 agents)"""
    street_id: str
    street_name: str
    agent_turns: List[Turn]
    preliminary_findings: str
    identified_obligations: List[Obligation]
    confidence: float  # 0.0-1.0
    next_street_recommendations: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "street_id": self.street_id,
            "street_name": self.street_name,
            "agent_turns": [t.to_dict() for t in self.agent_turns],
            "preliminary_findings": self.preliminary_findings,
            "identified_obligations": [o.to_dict() for o in self.identified_obligations],
            "confidence": self.confidence,
            "next_street_recommendations": self.next_street_recommendations,
        }


@dataclass
class BuildingBrief:
    """Aggregated report from a building (2-4 streets)"""
    building_id: str
    building_name: str
    district: str
    street_reports: List[StreetReport]
    consolidated_findings: str
    evidence_artifacts: List[str]  # Links to receipts
    obligations: List[Obligation]
    building_verdict: str  # "APPROVE" | "CONDITIONAL" | "OBJECT"
    supervisor_notes: str

    def to_dict(self):
        return {
            "building_id": self.building_id,
            "building_name": self.building_name,
            "district": self.district,
            "street_reports": [s.to_dict() for s in self.street_reports],
            "consolidated_findings": self.consolidated_findings,
            "evidence_artifacts": self.evidence_artifacts,
            "obligations": [o.to_dict() for o in self.obligations],
            "building_verdict": self.building_verdict,
            "supervisor_notes": self.supervisor_notes,
        }


@dataclass
class DistrictVerdict:
    """Final verdict from a district supervisor"""
    district_id: str
    district_name: str
    building_briefs: List[BuildingBrief]
    overall_verdict: str  # "APPROVE" | "CONDITIONAL" | "OBJECT" | "QUARANTINE" | "KILL"
    blocking_obligations: List[Obligation]
    vote_weight: float  # 0.65-1.00 based on district authority
    phase: float  # 0 (constructive) to π (destructive)
    supervisor_rationale: str

    def to_dict(self):
        return {
            "district_id": self.district_id,
            "district_name": self.district_name,
            "building_briefs": [b.to_dict() for b in self.building_briefs],
            "overall_verdict": self.overall_verdict,
            "blocking_obligations": [o.to_dict() for o in self.blocking_obligations],
            "vote_weight": self.vote_weight,
            "phase": self.phase,
            "supervisor_rationale": self.supervisor_rationale,
        }
