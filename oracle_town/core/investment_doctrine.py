#!/usr/bin/env python3
"""Personal Investment Doctrine Schema"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class InvestmentClass(Enum):
    CLASS_I = "governable"
    CLASS_II = "conditionally_governable"
    CLASS_III = "speculative"
    CLASS_IV = "existential"

@dataclass
class InvestmentSubmission:
    decision_id: str
    title: str
    investment_class: InvestmentClass
    amount_at_risk: float
    timestamp: str
    evidence_exists: bool
    evidence_strength: Optional[str] = None
    external_validation_possible: bool = False
    narrative_dependent: bool = False
    timing_dependent: bool = False
    irreversible: bool = False
    intent: str = ""
    expected_outcome: str = ""
    reversibility: str = "medium"
    exit_clause: Optional[str] = None
    identity_defining: Optional[bool] = None
    identity_rationale: Optional[str] = None
    is_override: bool = False
    override_reason: Optional[str] = None
    override_previous_verdict: Optional[str] = None

    def validate(self):
        errors = []
        if len(self.intent) < 20:
            errors.append("Intent too short")
        if len(self.intent) > 300:
            errors.append("Intent too long")
        return (len(errors) == 0, errors)

    def to_dict(self):
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "investment_class": self.investment_class.value,
            "amount_at_risk": self.amount_at_risk,
            "timestamp": self.timestamp,
            "intent": self.intent,
            "expected_outcome": self.expected_outcome,
            "is_override": self.is_override,
        }
