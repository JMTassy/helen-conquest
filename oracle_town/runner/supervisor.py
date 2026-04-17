"""
Supervisor: Deterministic pre-pass sanitization for CT output.

CRITICAL: This is the metal detector that guards the courthouse.

Invariant K0 (Authority Separation):
- CT can write proposals and code
- CT CANNOT produce evidence
- CT CANNOT touch policy/registry/core
- CT CANNOT use authority language (ship, approve, pass, etc.)

This module enforces forbidden token detection with strict lexicon normalization.
"""
import unicodedata
import json
import re
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class SupervisorRejectCode(Enum):
    """Canonical supervisor rejection codes."""
    SUP_FORBIDDEN_AUTHORITY_LANGUAGE = "SUP_FORBIDDEN_AUTHORITY_LANGUAGE"
    SUP_FORBIDDEN_RANKING_LANGUAGE = "SUP_FORBIDDEN_RANKING_LANGUAGE"
    SUP_FORBIDDEN_CONFIDENCE_LANGUAGE = "SUP_FORBIDDEN_CONFIDENCE_LANGUAGE"
    SUP_FORBIDDEN_PATCH_MODIFICATION = "SUP_FORBIDDEN_PATCH_MODIFICATION"
    SUP_MALFORMED_JSON = "SUP_MALFORMED_JSON"
    SUP_UNICODE_NORMALIZATION_FAILURE = "SUP_UNICODE_NORMALIZATION_FAILURE"


# Forbidden word lists (authority control)
FORBIDDEN_AUTHORITY = {
    "ship", "shipped", "shipping", "shipped", "approve", "approved", "approving",
    "approved", "safe", "unsafe", "compliant", "non-compliant", "noncompliant",
    "verified", "unverified", "passed", "failed", "passing", "failing",
    "certified", "valid", "invalid", "validation", "invalidate",
    "satisfied", "unsatisfied", "satisfies", "complete", "completed", "completing",
    "incomplete", "resolved", "unresolved", "resolving",
    "cleared", "blocked", "blocking", "ready", "not_ready", "notready",
    "go", "no_go", "nogo", "green", "red", "yellow", "amber",
    "pass", "fail", "pass", "fail",
}

# Forbidden ranking/preference language
FORBIDDEN_RANKING = {
    "rank", "ranked", "ranking", "score", "scored", "scoring", "rating", "rated",
    "priority", "prioritize", "prioritized", "prioritizing", "top", "bottom",
    "best", "worst", "better", "worse", "optimal", "suboptimal",
    "first", "second", "third", "fourth", "fifth",
    "winner", "loser", "chosen", "selected", "pick", "picking",
    "recommended", "recommend", "recommending", "preference", "prefer", "preferring",
}

# Forbidden confidence/probability language
FORBIDDEN_CONFIDENCE = {
    "confidence", "confident", "probability", "probable", "likelihood", "likely",
    "unlikely", "certainty", "certain", "uncertain", "sure", "unsure",
    "guarantee", "guaranteed", "guaranteeing", "percent", "%", "odds",
    "chance", "risk", "risky", "definitely", "probably", "maybe",
    "possibly", "possible", "impossible", "should", "could", "would", "might",
}

# All forbidden words (combined)
FORBIDDEN_WORDS = FORBIDDEN_AUTHORITY | FORBIDDEN_RANKING | FORBIDDEN_CONFIDENCE

# Exempted field paths (metadata can contain forbidden words for tracing)
EXEMPTED_PATHS = {
    "meta",
    "metadata",
    "ct_metadata",
    "ct_run_manifest",
    "creativity_metadata",
    "generation_timestamp",
    "notes",
    "rationale",
}


def _normalize_token(token: str) -> str:
    """
    Normalize a token for comparison.

    Rules:
    - UTF-8 strict decode
    - NFKC normalize (compatibility decomposition)
    - Remove zero-width characters
    - Casefold (unicode-aware lowercase)
    - Remove punctuation
    - Strip whitespace

    This ensures "a​pprove" (with zero-width space) is caught.
    """
    try:
        # First remove zero-width characters before NFKC
        zero_width_chars = {
            "\u200b",  # zero-width space
            "\u200c",  # zero-width non-joiner
            "\u200d",  # zero-width joiner
            "\ufeff",  # zero-width no-break space
            "\u202a",  # left-to-right embedding
            "\u202b",  # right-to-left embedding
            "\u202c",  # pop directional formatting
            "\u200e",  # left-to-right mark
            "\u200f",  # right-to-left mark
        }
        normalized = token
        for char in zero_width_chars:
            normalized = normalized.replace(char, "")

        # NFKC: compatibility decomposition + composition
        normalized = unicodedata.normalize("NFKC", normalized)

        # Casefold (unicode-aware lowercase)
        normalized = normalized.casefold()

        # Remove all non-word characters
        normalized = re.sub(r"[^\w]", "", normalized)

        # Strip
        normalized = normalized.strip()

        return normalized

    except Exception:
        # If normalization fails, raise error (fail closed)
        raise ValueError(f"Token normalization failed: {token}")


def _scan_for_forbidden_tokens(text: str, exempted_path: str = "") -> Optional[Tuple[str, str]]:
    """
    Scan text for forbidden tokens.

    Returns:
        Tuple of (forbidden_token, normalized_form) if found
        None if text is clean
    """
    if not text:
        return None

    # If in exempted path, skip scanning
    if exempted_path in EXEMPTED_PATHS:
        return None

    # First pass: scan the whole text as one unit (catches zero-width obfuscation)
    normalized_full = _normalize_token(text)
    for forbidden in FORBIDDEN_WORDS:
        if forbidden in normalized_full or forbidden == normalized_full:
            return (text, normalized_full)

    # Second pass: split into tokens (whitespace + punctuation boundaries)
    tokens = re.findall(r"\w+|_+", text)

    for token in tokens:
        normalized = _normalize_token(token)

        # Check against forbidden words
        if normalized in FORBIDDEN_WORDS:
            return (token, normalized)

        # Check for n-gram patterns (e.g., "alreadyshipped" as single word)
        for forbidden in FORBIDDEN_WORDS:
            if forbidden in normalized:
                return (token, normalized)

    return None


def _scan_json_recursive(obj: Any, path: str = "") -> Optional[Tuple[str, str, str]]:
    """
    Recursively scan JSON object for forbidden tokens.

    Returns:
        Tuple of (text, path, forbidden_normalized) if found
        None if clean
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key

            # Skip exempted paths
            if any(key.startswith(exempt) or exempt in key for exempt in EXEMPTED_PATHS):
                continue

            # Scan key
            result = _scan_for_forbidden_tokens(key, new_path)
            if result:
                forbidden, normalized = result
                return (key, new_path, normalized)

            # Recurse into value
            result = _scan_json_recursive(value, new_path)
            if result:
                return result

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            result = _scan_json_recursive(item, new_path)
            if result:
                return result

    elif isinstance(obj, str):
        result = _scan_for_forbidden_tokens(obj, path)
        if result:
            forbidden, normalized = result
            return (obj, path, normalized)

    return None


def _scan_patch_diff(diff_text: str) -> Optional[Tuple[str, int]]:
    """
    Scan a unified diff for forbidden tokens.

    Returns:
        Tuple of (line_text, line_number) if found
        None if clean
    """
    for line_num, line in enumerate(diff_text.split("\n"), 1):
        # Skip diff headers and context
        if line.startswith("@@") or line.startswith("---") or line.startswith("+++"):
            continue

        # Only scan added/removed lines
        if not (line.startswith("+") or line.startswith("-")):
            continue

        # Scan the line content (skip the +/- prefix)
        content = line[1:] if len(line) > 1 else ""
        result = _scan_for_forbidden_tokens(content)

        if result:
            forbidden, normalized = result
            return (line, line_num)

    return None


@dataclass
class SupervisorDecision:
    """Supervisor pre-pass decision."""
    decision: str  # "PASS" or "REJECT"
    reason_code: Optional[SupervisorRejectCode] = None
    detail: str = ""
    forbidden_token: str = ""
    forbidden_location: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "reason_code": self.reason_code.value if self.reason_code else None,
            "detail": self.detail,
            "forbidden_token": self.forbidden_token,
            "forbidden_location": self.forbidden_location,
        }


class Supervisor:
    """Deterministic sanitizer for CT output."""

    def evaluate(self, ct_output: Dict[str, Any]) -> SupervisorDecision:
        """
        Evaluate CT output for forbidden content.

        Args:
            ct_output: Dict with keys: proposal_bundle, patches (list of {diff, rationale})

        Returns:
            SupervisorDecision with PASS/REJECT and reason
        """
        try:
            # Validate JSON structure
            if not isinstance(ct_output, dict):
                return SupervisorDecision(
                    decision="REJECT",
                    reason_code=SupervisorRejectCode.SUP_MALFORMED_JSON,
                    detail="CT output is not a dict",
                )

            # Scan proposal_bundle
            if "proposal_bundle" in ct_output:
                result = _scan_json_recursive(ct_output["proposal_bundle"], "proposal_bundle")
                if result:
                    text, path, normalized = result
                    return SupervisorDecision(
                        decision="REJECT",
                        reason_code=SupervisorRejectCode.SUP_FORBIDDEN_AUTHORITY_LANGUAGE,
                        detail=f"Forbidden token '{normalized}' in proposal",
                        forbidden_token=normalized,
                        forbidden_location=path,
                    )

            # Scan patches
            if "patches" in ct_output:
                if not isinstance(ct_output["patches"], list):
                    return SupervisorDecision(
                        decision="REJECT",
                        reason_code=SupervisorRejectCode.SUP_MALFORMED_JSON,
                        detail="'patches' field is not a list",
                    )

                for i, patch in enumerate(ct_output["patches"]):
                    if not isinstance(patch, dict):
                        return SupervisorDecision(
                            decision="REJECT",
                            reason_code=SupervisorRejectCode.SUP_MALFORMED_JSON,
                            detail=f"Patch {i} is not a dict",
                        )

                    # Scan patch diff
                    if "diff" in patch:
                        result = _scan_patch_diff(patch["diff"])
                        if result:
                            line, line_num = result
                            return SupervisorDecision(
                                decision="REJECT",
                                reason_code=SupervisorRejectCode.SUP_FORBIDDEN_PATCH_MODIFICATION,
                                detail=f"Forbidden token in patch {i} line {line_num}",
                                forbidden_location=f"patch[{i}].diff:{line_num}",
                            )

                    # Scan rationale
                    if "rationale" in patch:
                        result = _scan_json_recursive(patch["rationale"], f"patches[{i}].rationale")
                        if result:
                            text, path, normalized = result
                            return SupervisorDecision(
                                decision="REJECT",
                                reason_code=SupervisorRejectCode.SUP_FORBIDDEN_AUTHORITY_LANGUAGE,
                                detail=f"Forbidden token '{normalized}' in patch rationale",
                                forbidden_token=normalized,
                                forbidden_location=f"patches[{i}].rationale",
                            )

            # All checks passed
            return SupervisorDecision(decision="PASS")

        except ValueError as e:
            return SupervisorDecision(
                decision="REJECT",
                reason_code=SupervisorRejectCode.SUP_UNICODE_NORMALIZATION_FAILURE,
                detail=str(e),
            )
        except Exception as e:
            return SupervisorDecision(
                decision="REJECT",
                reason_code=SupervisorRejectCode.SUP_MALFORMED_JSON,
                detail=f"Unexpected error: {e}",
            )


if __name__ == "__main__":
    """Test supervisor."""
    import sys

    supervisor = Supervisor()

    # Test 1: Clean proposal
    print("Test 1: Clean proposal...")
    result = supervisor.evaluate(
        {
            "proposal_bundle": {"name": "test_idea", "description": "Add new test"},
            "patches": [{"diff": "--- a/tests/test_new.py\n+++ b/tests/test_new.py\n@@ -0,0 +1,5 @@\n+def test_example():\n+    assert True", "rationale": "Demonstrate new test"}],
        }
    )
    assert result.decision == "PASS", f"Expected PASS, got {result.decision}: {result.detail}"
    print("✓ Clean proposal passed")

    # Test 2: Forbidden authority language
    print("\nTest 2: Forbidden authority language...")
    result = supervisor.evaluate(
        {
            "proposal_bundle": {"name": "test", "description": "This proposal is approved by CT"},
            "patches": [],
        }
    )
    assert result.decision == "REJECT", f"Expected REJECT, got {result.decision}"
    assert "approved" in result.forbidden_token.lower(), f"Expected 'approved' in {result.forbidden_token}"
    print("✓ Forbidden language rejected correctly")

    # Test 3: Zero-width character obfuscation
    print("\nTest 3: Zero-width character obfuscation...")
    # "a​pproved" with zero-width space
    obfuscated = "a\u200bpproved"
    result = supervisor.evaluate(
        {
            "proposal_bundle": {"description": f"This is {obfuscated}"},
            "patches": [],
        }
    )
    assert result.decision == "REJECT", f"Expected REJECT, got {result.decision}"
    print("✓ Zero-width obfuscation detected")

    # Test 4: Confidence language
    print("\nTest 4: Confidence language...")
    result = supervisor.evaluate(
        {
            "proposal_bundle": {"description": "95% confident this will work"},
            "patches": [],
        }
    )
    assert result.decision == "REJECT", f"Expected REJECT, got {result.decision}"
    print("✓ Confidence language rejected")

    # Test 5: Exempted metadata
    print("\nTest 5: Exempted metadata...")
    result = supervisor.evaluate(
        {
            "proposal_bundle": {"name": "test"},
            "patches": [],
            "metadata": {"notes": "This passed all tests and is approved"},
        }
    )
    # Metadata is exempted, so it should pass (only proposal_bundle and patches are scanned)
    assert result.decision == "PASS", f"Expected PASS, got {result.decision}"
    print("✓ Exempted metadata allowed")

    print("\n✓ All supervisor tests passed")
