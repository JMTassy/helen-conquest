#!/usr/bin/env python3
"""Doctrine Enforcer - Pre-TRI Validation"""

from oracle_town.core.investment_doctrine import InvestmentSubmission, InvestmentClass

class DoctrineEnforcer:
    @staticmethod
    def validate_submission(submission):
        violations = []
        is_valid, errors = submission.validate()
        if not is_valid:
            return (False, "DOCTRINE_VIOLATION", errors)
        
        # Check for narrative laundering
        bad_phrases = ["believe", "feel", "intuitively", "trust my gut"]
        for phrase in bad_phrases:
            if phrase.lower() in submission.intent.lower():
                violations.append(f"Narrative laundering detected: '{phrase}'")
        
        if violations:
            return (False, "NARRATIVE_LAUNDERING", violations)
        
        # CLASS_III checks
        if submission.investment_class == InvestmentClass.CLASS_III:
            if submission.reversibility == "high":
                violations.append("CLASS_III should be irreversible")
            if not submission.is_override:
                violations.append("CLASS_III must be logged as override")
        
        if violations:
            return (False, "CLASS_MISMATCH", violations)
        
        return (True, "VALID", [])

    @staticmethod
    def format_rejection(status_code, violations):
        msg = f"\nDOCTRINE ENFORCER REJECTION\n"
        msg += f"Status: {status_code}\n"
        msg += f"Violations:\n"
        for v in violations:
            msg += f"  - {v}\n"
        return msg
