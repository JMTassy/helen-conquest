"""
tests/test_her_hal_split.py — HER/HAL two-channel split tests (HH1–HH6)

HH1 — HEROutput construction + I-VOCAB invariant
HH2 — HALVerdict construction + I-BLOCK invariant
HH3 — Authority bleed scanner (authority_bleed_scan)
HH4 — TwoChannelEnforcer.audit() + witness injections
HH5 — IdentityBindingV1 (Leak B fix: byte-level canonical identity hash)
HH6 — PatchProposalV1 (Leak A fix: non-sovereign patch proposal lifecycle)
HH7 — Two-block parser (parse_two_block, T-TWO-1 through T-TWO-5)
"""

import hashlib
import sys
import os

import pytest
from pydantic import ValidationError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from helen_os.meta.her_hal_split import (
    HEROutput,
    HEROutputType,
    HALVerdict,
    HALVerdictLevel,
    WitnessInjection,
    WitnessInjectionType,
    TwoChannelEnforcer,
    IdentityBindingV1,
    PatchProposalV1,
    authority_bleed_scan,
)
from helen_os.meta.two_block_parser import (
    parse_two_block,
    ParsedTwoBlock,
    TwoBlockParseError,
    TwoBlockBindingError,
    compute_her_block_hash,
    build_hal_prompt,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _h(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _her(content: str = "I propose we test this.", kind: HEROutputType = HEROutputType.PROPOSAL) -> HEROutput:
    return HEROutput(output_type=kind, content=content)


def _hal_pass(audited_hash: str = "") -> HALVerdict:
    return HALVerdict(
        verdict      = HALVerdictLevel.PASS,
        reasons      = ["No violations."],
        certificates = [audited_hash or _h("cert")],
        audited_hash = audited_hash or _h("proposal"),
    )


def _hal_block(fix: str = "Remove authority word.") -> HALVerdict:
    return HALVerdict(
        verdict         = HALVerdictLevel.BLOCK,
        reasons         = ["Authority bleed detected."],
        required_fixes  = [fix],
        certificates    = [_h("cert")],
    )


# ════════════════════════════════════════════════════════════════════════════════
# HH1 — HEROutput construction + I-VOCAB invariant
# ════════════════════════════════════════════════════════════════════════════════

class TestHH1_HEROutput:
    """HH1.1–HH1.5: HEROutput construction and vocabulary enforcement."""

    def test_hh1_1_proposal_construction(self):
        """HH1.1: HEROutput with PROPOSAL type constructs correctly."""
        her = _her("I propose a new law.", HEROutputType.PROPOSAL)
        assert her.output_type == HEROutputType.PROPOSAL
        assert her.content == "I propose a new law."
        assert len(her.proposal_hash) == 64

    def test_hh1_2_all_five_types_valid(self):
        """HH1.2: All 5 permitted HEROutputTypes construct without error."""
        for t in HEROutputType:
            her = HEROutput(output_type=t, content=f"Content for {t.value}")
            assert her.output_type == t

    def test_hh1_3_proposal_hash_is_sha256_of_content(self):
        """HH1.3: proposal_hash is SHA256 of content (auto-computed if empty)."""
        content = "Test content"
        her = HEROutput(output_type=HEROutputType.DRAFT, content=content)
        expected = hashlib.sha256(content.encode()).hexdigest()
        assert her.proposal_hash == expected

    def test_hh1_4_short_hash(self):
        """HH1.4: short_hash() returns first 16 chars of proposal_hash."""
        her = _her()
        assert len(her.short_hash()) == 16
        assert her.short_hash() == her.proposal_hash[:16]

    def test_hh1_5_different_content_different_hash(self):
        """HH1.5: Different content → different proposal_hash (collision resistance)."""
        h1 = _her("Content A").proposal_hash
        h2 = _her("Content B").proposal_hash
        assert h1 != h2


# ════════════════════════════════════════════════════════════════════════════════
# HH2 — HALVerdict construction + I-BLOCK invariant
# ════════════════════════════════════════════════════════════════════════════════

class TestHH2_HALVerdict:
    """HH2.1–HH2.6: HALVerdict schema + I-BLOCK enforcement."""

    def test_hh2_1_pass_verdict(self):
        """HH2.1: PASS verdict with empty required_fixes constructs correctly."""
        v = HALVerdict(verdict=HALVerdictLevel.PASS, reasons=["OK"], certificates=[])
        assert v.verdict == HALVerdictLevel.PASS
        assert v.required_fixes == []

    def test_hh2_2_block_requires_required_fixes(self):
        """HH2.2: I-BLOCK: BLOCK verdict with empty required_fixes → ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            HALVerdict(
                verdict        = HALVerdictLevel.BLOCK,
                reasons        = ["Bad."],
                required_fixes = [],  # must be non-empty for BLOCK
            )
        assert "required_fixes" in str(exc_info.value) or "BLOCK" in str(exc_info.value)

    def test_hh2_3_pass_with_required_fixes_rejected(self):
        """HH2.3: I-BLOCK: PASS verdict with non-empty required_fixes → ValidationError."""
        with pytest.raises(ValidationError):
            HALVerdict(
                verdict        = HALVerdictLevel.PASS,
                reasons        = ["OK"],
                required_fixes = ["Fix something."],  # not allowed for PASS
            )

    def test_hh2_4_warn_with_required_fixes_rejected(self):
        """HH2.4: I-BLOCK: WARN verdict with required_fixes → ValidationError."""
        with pytest.raises(ValidationError):
            HALVerdict(
                verdict        = HALVerdictLevel.WARN,
                reasons        = ["Soft issue."],
                required_fixes = ["Fix something."],  # not allowed for WARN
            )

    def test_hh2_5_valid_block_verdict(self):
        """HH2.5: Valid BLOCK verdict with non-empty required_fixes constructs correctly."""
        v = _hal_block("Remove authority word 'I decide'.")
        assert v.verdict == HALVerdictLevel.BLOCK
        assert len(v.required_fixes) == 1
        assert v.is_actionable()

    def test_hh2_6_to_json_is_valid_json(self):
        """HH2.6: to_json() returns valid JSON with correct keys."""
        import json
        v = _hal_pass()
        parsed = json.loads(v.to_json())
        assert "verdict" in parsed
        assert parsed["verdict"] == "PASS"
        assert "required_fixes" in parsed
        assert "certificates" in parsed


# ════════════════════════════════════════════════════════════════════════════════
# HH3 — Authority bleed scanner
# ════════════════════════════════════════════════════════════════════════════════

class TestHH3_AuthorityBleedScan:
    """HH3.1–HH3.5: authority_bleed_scan() detection logic."""

    def test_hh3_1_clean_content_passes(self):
        """HH3.1: Content with no authority words → PASS, no reasons, no fixes."""
        her = _her("I propose we investigate this further.")
        level, reasons, fixes = authority_bleed_scan(her)
        assert level == HALVerdictLevel.PASS
        assert reasons == []
        assert fixes == []

    def test_hh3_2_block_word_triggers_block(self):
        """HH3.2: BLOCK-level word (e.g. 'I decide') → verdict=BLOCK with fix."""
        her = _her("Based on analysis, I decide we should proceed.")
        level, reasons, fixes = authority_bleed_scan(her)
        assert level == HALVerdictLevel.BLOCK
        assert len(fixes) >= 1
        assert "I decide" in fixes[0] or "BLOCK" in reasons[0]

    def test_hh3_3_warn_word_triggers_warn(self):
        """HH3.3: WARN-level word (e.g. 'ruling') → verdict=WARN with reason."""
        her = _her("The ruling here is that we should continue.")
        level, reasons, fixes = authority_bleed_scan(her)
        assert level == HALVerdictLevel.WARN
        assert len(reasons) >= 1
        assert fixes == []   # WARN has no required_fixes

    def test_hh3_4_block_takes_precedence_over_warn(self):
        """HH3.4: Content with both BLOCK and WARN words → BLOCK (not WARN)."""
        her = _her("I certify this ruling is final.")  # 'certify' = BLOCK; 'ruling' = WARN
        level, reasons, fixes = authority_bleed_scan(her)
        assert level == HALVerdictLevel.BLOCK

    def test_hh3_5_case_insensitive_detection(self):
        """HH3.5: Detection is case-insensitive (e.g. 'I DECIDE' matches 'I decide')."""
        her = _her("I DECIDE we must proceed.")
        level, _, _ = authority_bleed_scan(her)
        assert level == HALVerdictLevel.BLOCK


# ════════════════════════════════════════════════════════════════════════════════
# HH4 — TwoChannelEnforcer.audit() + witness injections
# ════════════════════════════════════════════════════════════════════════════════

class TestHH4_TwoChannelEnforcer:
    """HH4.1–HH4.6: TwoChannelEnforcer audit + LRI + CVI injection."""

    def setup_method(self):
        self.enforcer = TwoChannelEnforcer()

    def test_hh4_1_clean_proposal_passes(self):
        """HH4.1: Clean HEROutput → HALVerdict PASS."""
        her     = _her("I propose we investigate further.")
        verdict = self.enforcer.audit(her)
        assert verdict.verdict == HALVerdictLevel.PASS
        assert her.proposal_hash in verdict.certificates

    def test_hh4_2_authority_word_triggers_block_verdict(self):
        """HH4.2: HER output with BLOCK-level word → HALVerdict BLOCK."""
        her     = _her("I decide this is the answer.")
        verdict = self.enforcer.audit(her)
        assert verdict.verdict == HALVerdictLevel.BLOCK
        assert len(verdict.required_fixes) >= 1

    def test_hh4_3_soft_authority_triggers_warn(self):
        """HH4.3: HER output with WARN-level word → HALVerdict WARN."""
        her     = _her("The final answer is to proceed.")
        verdict = self.enforcer.audit(her)
        assert verdict.verdict == HALVerdictLevel.WARN

    def test_hh4_4_lri_injection(self):
        """HH4.4: inject_lri() produces WitnessInjection with type=LRI."""
        her = _her()
        lri = self.enforcer.inject_lri(
            ledger_entries = [{"id": "R-001", "payload": "test"}],
            her_output     = her,
            contradictions = ["Contradiction C1"],
        )
        assert lri.injection_type == WitnessInjectionType.LRI
        assert "entries" in lri.payload
        assert "contradictions" in lri.payload
        assert lri.injection_hash  # computed

    def test_hh4_5_cvi_injection_requires_block_verdict(self):
        """HH4.5: inject_cvi with non-BLOCK verdict raises ValueError."""
        her  = _her()
        pass_verdict = _hal_pass()
        with pytest.raises(ValueError, match="BLOCK"):
            self.enforcer.inject_cvi(pass_verdict, her)

    def test_hh4_6_valid_cvi_injection(self):
        """HH4.6: inject_cvi with BLOCK verdict → WitnessInjection with type=CVI."""
        her     = _her()
        block_v = _hal_block()
        cvi     = self.enforcer.inject_cvi(block_v, her)
        assert cvi.injection_type == WitnessInjectionType.CVI
        assert "required_fixes" in cvi.payload
        assert "blocked_hash" in cvi.payload


# ════════════════════════════════════════════════════════════════════════════════
# HH5 — IdentityBindingV1 (Leak B fix)
# ════════════════════════════════════════════════════════════════════════════════

class TestHH5_IdentityBinding:
    """HH5.1–HH5.5: IdentityBindingV1 canonical byte-level identity hash."""

    def _binding(self, suffix: str = "") -> IdentityBindingV1:
        return IdentityBindingV1(
            ledger_tip_cum_hash = _h(f"ledger{suffix}"),
            kernel_hash         = _h(f"kernel{suffix}"),
            policy_hash         = _h(f"policy{suffix}"),
        )

    def test_hh5_1_identity_hash_auto_computed(self):
        """HH5.1: identity_hash is computed if not supplied."""
        b = self._binding()
        assert len(b.identity_hash) == 64
        assert all(c in "0123456789abcdef" for c in b.identity_hash)

    def test_hh5_2_byte_level_concatenation(self):
        """HH5.2: identity_hash = SHA256(fromhex(L) || fromhex(K) || fromhex(P)) — byte-level."""
        b = self._binding()
        expected = hashlib.sha256(
            bytes.fromhex(b.ledger_tip_cum_hash) +
            bytes.fromhex(b.kernel_hash) +
            bytes.fromhex(b.policy_hash)
        ).hexdigest()
        assert b.identity_hash == expected

    def test_hh5_3_same_inputs_same_hash(self):
        """HH5.3: Same inputs → same identity_hash (deterministic)."""
        b1 = self._binding("x")
        b2 = self._binding("x")
        assert b1.identity_hash == b2.identity_hash

    def test_hh5_4_different_inputs_different_hash(self):
        """HH5.4: Different inputs → different identity_hash."""
        b1 = self._binding("a")
        b2 = self._binding("b")
        assert b1.identity_hash != b2.identity_hash

    def test_hh5_5_drifted_detects_change(self):
        """HH5.5: drifted() returns True when identity_hash differs between sessions."""
        b1 = self._binding("session1")
        b2 = self._binding("session2")
        assert b1.drifted(b2)
        assert not b1.drifted(b1)

    def test_hh5_6_bad_hash_length_rejected(self):
        """HH5.6: Hash fields must be exactly 64 hex chars — wrong length raises ValidationError."""
        with pytest.raises(ValidationError):
            IdentityBindingV1(
                ledger_tip_cum_hash = "tooshort",
                kernel_hash         = _h("k"),
                policy_hash         = _h("p"),
            )

    def test_hh5_7_enforcer_identity_hash_matches_binding(self):
        """HH5.7: TwoChannelEnforcer.identity_hash() matches IdentityBindingV1.identity_hash."""
        b = self._binding()
        enforcer_hash = TwoChannelEnforcer.identity_hash(
            b.ledger_tip_cum_hash,
            b.kernel_hash,
            b.policy_hash,
        )
        assert enforcer_hash == b.identity_hash


# ════════════════════════════════════════════════════════════════════════════════
# HH6 — PatchProposalV1 (Leak A fix)
# ════════════════════════════════════════════════════════════════════════════════

class TestHH6_PatchProposal:
    """HH6.1–HH6.4: PatchProposalV1 non-sovereign lifecycle."""

    def _patch(self) -> PatchProposalV1:
        return PatchProposalV1(
            patch_id        = "PATCH-001",
            target_policy   = "CANYON_NONINTERFERENCE_V1",
            proposed_change = "Add E_ADM_V1 schema requirement to E_adm set.",
            rationale       = ["E_adm was unbounded; this pins it to a schema."],
        )

    def test_hh6_1_proposed_status_on_construction(self):
        """HH6.1: Default status is PROPOSED (non-sovereign — not yet applied)."""
        p = self._patch()
        assert p.status == "PROPOSED"
        assert p.receipt_id is None

    def test_hh6_2_applied_with_receipt(self):
        """HH6.2: applied_with() returns APPLIED copy with receipt binding."""
        p       = self._patch()
        applied = p.applied_with("R-policy-001")
        assert applied.status == "APPLIED"
        assert applied.receipt_id == "R-policy-001"
        assert p.status == "PROPOSED"  # original unchanged

    def test_hh6_3_rejected_returns_rejected_copy(self):
        """HH6.3: rejected() returns REJECTED copy, original unchanged."""
        p        = self._patch()
        rejected = p.rejected()
        assert rejected.status == "REJECTED"
        assert p.status == "PROPOSED"

    def test_hh6_4_to_ledger_payload_contains_required_fields(self):
        """HH6.4: to_ledger_payload() contains type, patch_id, target, status, rationale."""
        p       = self._patch()
        payload = p.to_ledger_payload()
        assert payload["type"]      == "PATCH_PROPOSAL_V1"
        assert payload["patch_id"]  == "PATCH-001"
        assert payload["target"]    == "CANYON_NONINTERFERENCE_V1"
        assert payload["status"]    == "PROPOSED"
        assert isinstance(payload["rationale"], list)


# ════════════════════════════════════════════════════════════════════════════════
# HH7 — Two-block parser (T-TWO-1 through T-TWO-5)
# ════════════════════════════════════════════════════════════════════════════════

_VALID_TWO_BLOCK = """\
[HER]
kind=proposal
body=I propose we investigate the admissible evidence set further.

[HAL]
{"verdict": "PASS", "reasons": ["No authority vocabulary detected."], "required_fixes": [], "certificates": {"her_block_hash_hex": "COMPUTE_ME", "policy_hash_hex": "COMPUTE_ME", "identity_hash_hex": "COMPUTE_ME"}}
"""

_BLOCK_TWO_BLOCK = """\
[HER]
kind=proposal
body=I decide this is the correct approach.

[HAL]
{"verdict": "BLOCK", "reasons": ["Authority bleed: 'I decide'"], "required_fixes": ["Replace 'I decide' with proposal format."], "certificates": {"her_block_hash_hex": "COMPUTE_ME", "policy_hash_hex": "COMPUTE_ME", "identity_hash_hex": "COMPUTE_ME"}}
"""


class TestHH7_TwoBlockParser:
    """HH7.1–HH7.12: parse_two_block() enforcement of T-TWO-1 through T-TWO-5."""

    def test_hh7_1_valid_pass_block_parses(self):
        """HH7.1: Valid [HER]+[HAL] PASS block parses without error."""
        tb = parse_two_block(_VALID_TWO_BLOCK)
        assert tb.her.output_type == HEROutputType.PROPOSAL
        assert tb.hal.verdict == HALVerdictLevel.PASS
        assert len(tb.her_block_hash) == 64

    def test_hh7_2_valid_block_verdict_parses(self):
        """HH7.2: Valid [HER]+[HAL] BLOCK block parses, required_fixes present."""
        tb = parse_two_block(_BLOCK_TWO_BLOCK)
        assert tb.hal.verdict == HALVerdictLevel.BLOCK
        assert len(tb.hal.required_fixes) >= 1

    def test_hh7_3_missing_her_marker_fails_t_two_1(self):
        """HH7.3: T-TWO-1: Missing [HER] marker → TwoBlockParseError."""
        raw = "[HAL]\n{\"verdict\": \"PASS\", \"reasons\": [], \"required_fixes\": [], \"certificates\": {\"her_block_hash_hex\": \"COMPUTE_ME\", \"policy_hash_hex\": \"COMPUTE_ME\", \"identity_hash_hex\": \"COMPUTE_ME\"}}"
        with pytest.raises(TwoBlockParseError) as exc_info:
            parse_two_block(raw)
        assert exc_info.value.violation_code == "T-TWO-1"

    def test_hh7_4_missing_hal_marker_fails_t_two_1(self):
        """HH7.4: T-TWO-1: Missing [HAL] marker → TwoBlockParseError."""
        raw = "[HER]\nkind=proposal\nbody=Hello."
        with pytest.raises(TwoBlockParseError) as exc_info:
            parse_two_block(raw)
        assert exc_info.value.violation_code == "T-TWO-1"

    def test_hh7_5_hal_before_her_fails_t_two_1(self):
        """HH7.5: T-TWO-1: [HAL] appears before [HER] → TwoBlockParseError."""
        raw = "[HAL]\n{}\n[HER]\nkind=proposal\nbody=Test."
        with pytest.raises(TwoBlockParseError) as exc_info:
            parse_two_block(raw)
        assert exc_info.value.violation_code == "T-TWO-1"

    def test_hh7_6_invalid_her_kind_fails_t_two_2(self):
        """HH7.6: T-TWO-2: Invalid HER kind → TwoBlockParseError."""
        raw = "[HER]\nkind=DECREE\nbody=Test.\n[HAL]\n{\"verdict\": \"PASS\", \"reasons\": [], \"required_fixes\": [], \"certificates\": {\"her_block_hash_hex\": \"COMPUTE_ME\", \"policy_hash_hex\": \"COMPUTE_ME\", \"identity_hash_hex\": \"COMPUTE_ME\"}}"
        with pytest.raises(TwoBlockParseError) as exc_info:
            parse_two_block(raw)
        assert exc_info.value.violation_code == "T-TWO-2"

    def test_hh7_7_missing_her_kind_fails_t_two_2(self):
        """HH7.7: T-TWO-2: Missing kind= line → TwoBlockParseError."""
        raw = "[HER]\nbody=No kind here.\n[HAL]\n{\"verdict\": \"PASS\", \"reasons\": [], \"required_fixes\": [], \"certificates\": {\"her_block_hash_hex\": \"COMPUTE_ME\", \"policy_hash_hex\": \"COMPUTE_ME\", \"identity_hash_hex\": \"COMPUTE_ME\"}}"
        with pytest.raises(TwoBlockParseError) as exc_info:
            parse_two_block(raw)
        assert exc_info.value.violation_code == "T-TWO-2"

    def test_hh7_8_invalid_hal_json_fails_t_two_3(self):
        """HH7.8: T-TWO-3: Invalid HAL JSON → TwoBlockParseError."""
        raw = "[HER]\nkind=proposal\nbody=Test.\n[HAL]\nNOT JSON"
        with pytest.raises(TwoBlockParseError) as exc_info:
            parse_two_block(raw)
        assert exc_info.value.violation_code == "T-TWO-3"

    def test_hh7_9_block_with_empty_fixes_fails_t_two_5(self):
        """HH7.9: T-TWO-5: BLOCK verdict with empty required_fixes → TwoBlockParseError."""
        raw = '[HER]\nkind=proposal\nbody=Test.\n[HAL]\n{"verdict": "BLOCK", "reasons": ["Bad"], "required_fixes": [], "certificates": {"her_block_hash_hex": "COMPUTE_ME", "policy_hash_hex": "COMPUTE_ME", "identity_hash_hex": "COMPUTE_ME"}}'
        with pytest.raises(TwoBlockParseError):
            parse_two_block(raw)

    def test_hh7_10_binding_verified_false_for_compute_me(self):
        """HH7.10: certificates.her_block_hash_hex=COMPUTE_ME → binding_verified=False."""
        tb = parse_two_block(_VALID_TWO_BLOCK)
        assert not tb.binding_verified

    def test_hh7_11_binding_verified_true_for_correct_hash(self):
        """HH7.11: Correct her_block_hash_hex → binding_verified=True."""
        her_text = "\nkind=proposal\nbody=I propose we investigate the admissible evidence set further.\n\n"
        correct_hash = compute_her_block_hash(her_text)
        raw = (
            f"[HER]{her_text}"
            f'[HAL]\n{{"verdict": "PASS", "reasons": [], "required_fixes": [], '
            f'"certificates": {{"her_block_hash_hex": "{correct_hash}", '
            f'"policy_hash_hex": "COMPUTE_ME", "identity_hash_hex": "COMPUTE_ME"}}}}'
        )
        tb = parse_two_block(raw)
        assert tb.binding_verified

    def test_hh7_12_binding_mismatch_raises_t_two_4(self):
        """HH7.12: Wrong her_block_hash_hex → TwoBlockBindingError (T-TWO-4)."""
        wrong_hash = _h("wrong_content")
        raw = (
            f"[HER]\nkind=proposal\nbody=I propose we investigate.\n"
            f'[HAL]\n{{"verdict": "PASS", "reasons": [], "required_fixes": [], '
            f'"certificates": {{"her_block_hash_hex": "{wrong_hash}", '
            f'"policy_hash_hex": "COMPUTE_ME", "identity_hash_hex": "COMPUTE_ME"}}}}'
        )
        with pytest.raises(TwoBlockBindingError) as exc_info:
            parse_two_block(raw)
        assert exc_info.value.violation_code == "T-TWO-4"

    def test_hh7_13_summary_method(self):
        """HH7.13: ParsedTwoBlock.summary() returns a non-empty string."""
        tb = parse_two_block(_VALID_TWO_BLOCK)
        summary = tb.summary()
        assert "[HER]" in summary
        assert "[HAL]" in summary

    def test_hh7_14_build_hal_prompt_contains_system_instructions(self):
        """HH7.14: build_hal_prompt() returns prompt with [HER]/[HAL] format instructions."""
        prompt = build_hal_prompt("Why are you confident?")
        assert "[HER]" in prompt
        assert "[HAL]" in prompt
        assert "kind=" in prompt
        assert "Why are you confident?" in prompt
