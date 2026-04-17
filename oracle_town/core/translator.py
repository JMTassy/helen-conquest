"""
Translator Agent - Proposal → WUL Bridge

Deterministic, non-creative agent that converts Creative Town proposals into:
1. Concrete WUL glyphs
2. Concrete evaluation protocols
3. Concrete obligation sets

CRITICAL PROPERTIES:
- Non-creative (deterministic translation only)
- Fail-closed (invalid proposals die silently)
- No narrative authority (cannot persuade)
- Proposals that fail translation are rejected (not fixed)
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass
from oracle_town.creative.creative_town import ProposalEnvelope, ProposalType
from oracle_town.core.wul_compiler import WULCompiler


@dataclass
class TranslationResult:
    """Result of proposal → WUL translation"""
    success: bool
    wul_tree: Optional[Dict[str, Any]]
    obligations: Optional[List[Dict[str, Any]]]
    evaluation_protocol: Optional[str]
    rejection_reason: Optional[str]


class ProposalTranslator:
    """
    Translates Creative Town proposals into governance-ready artifacts.

    Translation rules:
    - EDGE_CASE_EXPLORATION → new obligation with test_extension
    - ATTACK_VECTOR → HARD obligations from obligation_addition
    - SIMPLIFICATION → parameter changes with metric target
    - If translation fails → proposal dies (no rescue)
    """

    def __init__(self):
        self.compiler = WULCompiler()

    def translate(self, proposal: ProposalEnvelope) -> TranslationResult:
        """
        Translate proposal into WUL + obligations.

        Args:
            proposal: ProposalEnvelope from Creative Town

        Returns:
            TranslationResult (success or typed rejection)
        """
        # Route by proposal type
        if proposal.proposal_type == ProposalType.EDGE_CASE_EXPLORATION:
            return self._translate_edge_case(proposal)
        elif proposal.proposal_type == ProposalType.ATTACK_VECTOR:
            return self._translate_attack_vector(proposal)
        elif proposal.proposal_type == ProposalType.SIMPLIFICATION:
            return self._translate_simplification(proposal)
        elif proposal.proposal_type == ProposalType.TEST_EXTENSION:
            return self._translate_test_extension(proposal)
        else:
            return TranslationResult(
                success=False,
                wul_tree=None,
                obligations=None,
                evaluation_protocol=None,
                rejection_reason=f"No translation rule for {proposal.proposal_type.value}"
            )

    def _translate_edge_case(self, proposal: ProposalEnvelope) -> TranslationResult:
        """
        Translate EDGE_CASE_EXPLORATION proposal.

        Creates:
        - WUL claim: "Edge case X must be tested"
        - Obligation: new test with severity SOFT (exploratory)
        - Protocol: run test, check exit code
        """
        try:
            # Extract test_extension
            test_extension = proposal.suggested_changes.get("test_extension")
            if not test_extension:
                return TranslationResult(
                    success=False,
                    wul_tree=None,
                    obligations=None,
                    evaluation_protocol=None,
                    rejection_reason="Missing test_extension in suggested_changes"
                )

            # Compile to WUL
            claim_text = f"Edge case test required: {proposal.proposal_id}"
            compilation = self.compiler.compile(claim_text)

            if not compilation.success:
                return TranslationResult(
                    success=False,
                    wul_tree=None,
                    obligations=None,
                    evaluation_protocol=None,
                    rejection_reason=f"WUL compilation failed: {compilation.reason_code}"
                )

            # Create obligation (SOFT for exploratory)
            obligation = {
                "name": f"edge_case_{proposal.proposal_id}",
                "type": "CODE_PROOF",
                "severity": "SOFT",  # Exploratory, non-blocking
                "required_evidence": [f"test_result_{proposal.proposal_id}"],
                "test_command": test_extension
            }

            # Evaluation protocol
            protocol = f"pytest {test_extension}"

            return TranslationResult(
                success=True,
                wul_tree=compilation.token_tree,
                obligations=[obligation],
                evaluation_protocol=protocol,
                rejection_reason=None
            )

        except Exception as e:
            return TranslationResult(
                success=False,
                wul_tree=None,
                obligations=None,
                evaluation_protocol=None,
                rejection_reason=f"Translation exception: {str(e)}"
            )

    def _translate_attack_vector(self, proposal: ProposalEnvelope) -> TranslationResult:
        """
        Translate ATTACK_VECTOR proposal.

        Creates:
        - WUL claim: "Attack vector X must be defended"
        - Obligations: HARD obligations from obligation_addition
        - Protocol: run defensive tests
        """
        try:
            obligation_names = proposal.suggested_changes.get("obligation_addition")
            if not obligation_names:
                return TranslationResult(
                    success=False,
                    wul_tree=None,
                    obligations=None,
                    evaluation_protocol=None,
                    rejection_reason="Missing obligation_addition"
                )

            # Compile to WUL
            claim_text = f"Attack vector defense required: {proposal.proposal_id}"
            compilation = self.compiler.compile(claim_text)

            if not compilation.success:
                return TranslationResult(
                    success=False,
                    wul_tree=None,
                    obligations=None,
                    evaluation_protocol=None,
                    rejection_reason=f"WUL compilation failed: {compilation.reason_code}"
                )

            # Create HARD obligations (attack defense is non-negotiable)
            obligations = []
            for obl_name in obligation_names[:10]:  # Limit to 10 per schema
                obligations.append({
                    "name": obl_name,
                    "type": "CODE_PROOF",
                    "severity": "HARD",
                    "required_evidence": [f"defense_{obl_name}"]
                })

            protocol = f"Run defensive tests for {len(obligations)} attack vectors"

            return TranslationResult(
                success=True,
                wul_tree=compilation.token_tree,
                obligations=obligations,
                evaluation_protocol=protocol,
                rejection_reason=None
            )

        except Exception as e:
            return TranslationResult(
                success=False,
                wul_tree=None,
                obligations=None,
                evaluation_protocol=None,
                rejection_reason=f"Translation exception: {str(e)}"
            )

    def _translate_simplification(self, proposal: ProposalEnvelope) -> TranslationResult:
        """
        Translate SIMPLIFICATION proposal.

        Creates:
        - WUL claim: "Simplification achieves metric target"
        - Obligations: metric verification
        - Protocol: measure metric before/after
        """
        try:
            metric = proposal.suggested_changes.get("metric")
            parameter_delta = proposal.suggested_changes.get("parameter_delta")

            if not metric or not parameter_delta:
                return TranslationResult(
                    success=False,
                    wul_tree=None,
                    obligations=None,
                    evaluation_protocol=None,
                    rejection_reason="Missing metric or parameter_delta"
                )

            # Compile to WUL
            claim_text = f"Simplification improves {metric}"
            compilation = self.compiler.compile(claim_text)

            if not compilation.success:
                return TranslationResult(
                    success=False,
                    wul_tree=None,
                    obligations=None,
                    evaluation_protocol=None,
                    rejection_reason=f"WUL compilation failed: {compilation.reason_code}"
                )

            # Create obligation (SOFT for optimization)
            obligation = {
                "name": f"simplification_metric_{metric}",
                "type": "TOOL_RESULT",
                "severity": "SOFT",
                "required_evidence": [f"metric_improvement_{metric}"]
            }

            protocol = f"Measure {metric} with delta {parameter_delta}"

            return TranslationResult(
                success=True,
                wul_tree=compilation.token_tree,
                obligations=[obligation],
                evaluation_protocol=protocol,
                rejection_reason=None
            )

        except Exception as e:
            return TranslationResult(
                success=False,
                wul_tree=None,
                obligations=None,
                evaluation_protocol=None,
                rejection_reason=f"Translation exception: {str(e)}"
            )

    def _translate_test_extension(self, proposal: ProposalEnvelope) -> TranslationResult:
        """Translate TEST_EXTENSION (similar to edge_case)"""
        return self._translate_edge_case(proposal)  # Same mechanics


def translate_proposal_to_wul(proposal: ProposalEnvelope) -> Tuple[bool, Dict[str, Any] | None, str | None]:
    """
    Convenience function: translate proposal and return (success, wul_tree, rejection_reason).

    Args:
        proposal: ProposalEnvelope

    Returns:
        (success, wul_tree, rejection_reason)
    """
    translator = ProposalTranslator()
    result = translator.translate(proposal)
    return result.success, result.wul_tree, result.rejection_reason
