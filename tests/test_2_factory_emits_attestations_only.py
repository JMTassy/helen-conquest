"""
Constitutional Test 2: Factory Emits Attestations Only

RULE: Factory may only emit attestations to append-only ledger.
      No verdicts, no decisions, no SHIP/NO_SHIP semantics.

ENFORCEMENT:
- Factory code must not contain verdict vocabulary
- Forbidden terms: SHIP, NO_SHIP, decision_record, verdict, blocking_obligations

VIOLATION: Architecture violation → NO_SHIP
"""
import pytest
from pathlib import Path

FORBIDDEN_TERMS = [
    "SHIP",
    "NO_SHIP",
    "decision_record",
    "verdict",
    "blocking_obligations",
    "remediation_plan",
]

# Allow these terms only in comments/docstrings
ALLOWED_IN_COMMENTS = ["SHIP", "NO_SHIP"]


def test_factory_has_no_verdict_semantics():
    """
    Constitutional Test 2: Factory Emits Attestations Only

    Scans factory.py for verdict-related vocabulary.
    Factory must only produce attestations (truth primitives).
    """
    repo_root = Path(__file__).parent.parent
    factory_files = list((repo_root / "oracle_town" / "core").rglob("*factory*.py"))

    assert factory_files, "Factory file must exist"

    for factory_file in factory_files:
        content = factory_file.read_text(encoding="utf-8", errors="ignore")

        # Remove comments and docstrings for cleaner analysis
        import re
        # Remove single-line comments
        content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
        # Remove docstrings (simple heuristic)
        content_no_comments = re.sub(r'""".*?"""', '', content_no_comments, flags=re.DOTALL)
        content_no_comments = re.sub(r"'''.*?'''", '', content_no_comments, flags=re.DOTALL)

        violations = []
        for term in FORBIDDEN_TERMS:
            if term in content_no_comments:
                # Check if it's in a string literal (allowed for error messages)
                if f'"{term}"' not in content_no_comments and f"'{term}'" not in content_no_comments:
                    violations.append(term)

        assert not violations, (
            f"CONSTITUTIONAL VIOLATION: Factory contains verdict semantics:\n"
            f"File: {factory_file.relative_to(repo_root)}\n"
            f"Forbidden terms found: {violations}\n\n"
            f"Factory may only emit attestations, not verdicts."
        )


def test_factory_emits_to_ledger_only():
    """Verify Factory writes to attestations ledger, not decisions"""
    repo_root = Path(__file__).parent.parent
    factory_file = repo_root / "oracle_town" / "core" / "factory.py"

    content = factory_file.read_text()

    # Factory should write to ledger
    assert "ledger" in content.lower(), "Factory must reference ledger"
    assert "append" in content.lower() or "write" in content.lower(), (
        "Factory must write to ledger"
    )

    # Factory should NOT write to decisions directory
    assert "decisions/" not in content, (
        "Factory must not write to decisions/ directory"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
