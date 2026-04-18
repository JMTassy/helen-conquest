"""
CI Tests for STEPS 4–8:
- HELEN_PRESSURE_SIGNAL_V1
- HELEN_AFFECT_TRANSLATION_V1
- HELEN_CHAIN_RECEIPT_V1
- KNOWLEDGE_HEALTH_AUDIT_V2_PATCH_01
- HELEN_RUNTIME_MANIFEST_V1
"""

import pytest
from helen_pressure_signal_v1 import (
    PressureSignalComputer, EvidenceBasis,
    StabilityState, RoutingEffect, PressureSignal,
)
from helen_affect_translation_v1 import (
    AffectTranslator, PrimaryAffect, AffectState,
)
from helen_chain_receipt_v1 import (
    ChainReceiptBuilder, ChainReceipt, WorkerType, ChainStatus,
)
from knowledge_health_audit_v2_patch_01 import (
    DispatchLineageAuditor, LineageFindingType, LineageFindingSeverity,
)
from helen_runtime_manifest_v1 import (
    ManifestBootstrap, RuntimeManifest, ManifestBootstrap,
)


# ===========================================================================
# STEP 4: PRESSURE SIGNAL
# ===========================================================================

class TestPressureSignal:

    def setup_method(self):
        self.computer = PressureSignalComputer()

    def test_stable_state_on_clean_evidence(self):
        """No evidence → stable state, normal routing."""
        evidence = EvidenceBasis()
        signal = self.computer.compute("sess_001", evidence)

        assert signal.stability_state == StabilityState.STABLE
        assert signal.routing_effect == RoutingEffect.NORMAL
        assert signal.pressure_score == 0.0
        assert signal.ambiguity_score == 0.0

    def test_ontology_claim_always_false(self):
        """ontology_claim must always be False (constitutional invariant)."""
        evidence = EvidenceBasis(contradictions_detected=5, retry_count=3)
        signal = self.computer.compute("sess_001", evidence)
        assert signal.ontology_claim == False

    def test_display_only_false_for_internal_signal(self):
        """Pressure signal is internal (not display-only)."""
        evidence = EvidenceBasis()
        signal = self.computer.compute("sess_001", evidence)
        assert signal.display_only == False

    def test_high_pressure_budget_over_limit(self):
        """Budget over_limit → pressure score ≥ 0.50."""
        evidence = EvidenceBasis(budget_state="over_limit")
        signal = self.computer.compute("sess_001", evidence)
        assert signal.pressure_score >= 0.50

    def test_coercion_triggers_refuse(self):
        """High coercion → REFUSE routing effect."""
        evidence = EvidenceBasis(coercive_patterns_detected=3)
        signal = self.computer.compute("sess_001", evidence)
        assert signal.routing_effect == RoutingEffect.REFUSE
        assert signal.stability_state == StabilityState.BLOCKED

    def test_unresolved_pointers_trigger_clarify(self):
        """Unresolved pointers → CLARIFY_BEFORE_ACTION."""
        evidence = EvidenceBasis(unresolved_pointers=3)
        signal = self.computer.compute("sess_001", evidence)
        assert signal.routing_effect == RoutingEffect.CLARIFY_BEFORE_ACTION

    def test_stability_state_strained_moderate_pressure(self):
        """Moderate pressure → STRAINED state."""
        evidence = EvidenceBasis(contradictions_detected=2, budget_state="near_limit")
        signal = self.computer.compute("sess_001", evidence)
        assert signal.stability_state in (StabilityState.STRAINED, StabilityState.UNSTABLE)
        assert signal.pressure_score > 0.30

    def test_scores_capped_at_one(self):
        """All scores must remain in [0, 1]."""
        evidence = EvidenceBasis(
            contradictions_detected=100,
            retry_count=100,
            denied_operations=100,
            unresolved_pointers=100,
            coercive_patterns_detected=100,
            constraint_violations=100,
            budget_state="over_limit",
        )
        signal = self.computer.compute("sess_001", evidence)
        assert 0.0 <= signal.pressure_score <= 1.0
        assert 0.0 <= signal.ambiguity_score <= 1.0
        assert 0.0 <= signal.coercion_score <= 1.0
        assert 0.0 <= signal.constraint_conflict_score <= 1.0

    def test_pressure_signal_has_id(self):
        """Pressure signal must have a non-empty ID."""
        evidence = EvidenceBasis()
        signal = self.computer.compute("sess_001", evidence)
        assert signal.pressure_signal_id
        assert signal.pressure_signal_id.startswith("ps_")

    def test_risk_posture_protective_on_refuse(self):
        """REFUSE routing → protective risk_posture."""
        evidence = EvidenceBasis(coercive_patterns_detected=3)
        signal = self.computer.compute("sess_001", evidence)
        assert signal.risk_posture == "protective"


# ===========================================================================
# STEP 5: AFFECT TRANSLATION
# ===========================================================================

class TestAffectTranslation:

    def setup_method(self):
        self.computer = PressureSignalComputer()
        self.translator = AffectTranslator()

    def _make_signal(self, evidence: EvidenceBasis) -> PressureSignal:
        return self.computer.compute("sess_001", evidence)

    def test_display_only_invariant_always_true(self):
        """AffectState.display_only must always be True."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert affect.display_only == True

    def test_may_influence_routing_always_false(self):
        """Affect must never influence routing."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert affect.may_influence_routing == False

    def test_may_influence_governance_always_false(self):
        """Affect must never influence governance."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert affect.may_influence_governance == False

    def test_ontology_claim_always_false(self):
        """Affect must never make ontological claims."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert affect.ontology_claim == False

    def test_causal_scope_presentation_only(self):
        """causal_scope must always be 'presentation_only'."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert affect.causal_scope == "presentation_only"

    def test_refuse_routing_produces_firm(self):
        """REFUSE routing → FIRM affect."""
        signal = self._make_signal(EvidenceBasis(coercive_patterns_detected=3))
        assert signal.routing_effect == RoutingEffect.REFUSE
        affect = self.translator.translate(signal)
        assert affect.primary_affect == PrimaryAffect.FIRM

    def test_high_pressure_produces_concerned(self):
        """High pressure score → CONCERNED affect."""
        signal = self._make_signal(EvidenceBasis(
            budget_state="over_limit",
            contradictions_detected=2,
            retry_count=2,
        ))
        assert signal.pressure_score > 0.70
        affect = self.translator.translate(signal)
        assert affect.primary_affect == PrimaryAffect.CONCERNED

    def test_high_ambiguity_produces_hesitant(self):
        """High ambiguity → HESITANT affect."""
        signal = self._make_signal(EvidenceBasis(unresolved_pointers=4))
        assert signal.ambiguity_score > 0.60
        affect = self.translator.translate(signal)
        assert affect.primary_affect in (PrimaryAffect.HESITANT, PrimaryAffect.FIRM)

    def test_stable_novelty_produces_curious(self):
        """Stable + novelty_high → CURIOUS affect."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal, novelty_high=True)
        assert affect.primary_affect == PrimaryAffect.CURIOUS

    def test_clean_closure_produces_relieved(self):
        """Clean closure + low pressure → RELIEVED affect."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal, closure_state="clean")
        assert affect.primary_affect == PrimaryAffect.RELIEVED

    def test_default_calm(self):
        """Default (stable, no novelty, no closure) → CALM affect."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert affect.primary_affect == PrimaryAffect.CALM

    def test_intensity_in_range(self):
        """Intensity must be in [0, 1]."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert 0.0 <= affect.intensity <= 1.0

    def test_affect_references_pressure_signal(self):
        """AffectState must reference source pressure signal ID."""
        signal = self._make_signal(EvidenceBasis())
        affect = self.translator.translate(signal)
        assert affect.source_pressure_signal_id == signal.pressure_signal_id


# ===========================================================================
# STEP 7: CHAIN RECEIPTS
# ===========================================================================

class TestChainReceipts:

    def setup_method(self):
        self.builder = ChainReceiptBuilder()

    def test_chain_receipt_emitted_correctly(self):
        """Basic emission of a chain receipt."""
        receipt = self.builder.emit(
            session_id="sess_001",
            dispatch_id_ref="disp_001",
            from_worker_id="skill.claim_extraction",
            from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.link_proposer",
            to_worker_type=WorkerType.AGENT,
            reason="index_maintenance_required",
            reason_codes=["multi_step_workflow_detected"],
            input_artifact_ids=["artifact_001"],
            output_artifact_ids=["index_patch_001"],
        )

        assert receipt.chain_receipt_id
        assert receipt.dispatch_id_ref == "disp_001"
        assert receipt.from_worker_type == WorkerType.SKILL
        assert receipt.to_worker_type == WorkerType.AGENT
        assert receipt.governed_mutation_attempted == False

    def test_chain_receipt_has_hash(self):
        """Chain receipt must have a computed hash."""
        receipt = self.builder.emit(
            session_id="sess_001",
            dispatch_id_ref="disp_001",
            from_worker_id="kernel.reducer",
            from_worker_type=WorkerType.KERNEL,
            to_worker_id="skill.audit",
            to_worker_type=WorkerType.SKILL,
            reason="audit_triggered",
        )
        assert receipt.chain_receipt_hash
        assert receipt.chain_receipt_hash.startswith("sha256:")

    def test_governance_violation_detected_canonical_write_from_skill(self):
        """SKILL writing canonical raises dispatch_lineage_violation."""
        receipts = [
            {
                "chain_receipt_id": "chain_001",
                "from_worker_type": "skill",
                "from_worker_id": "skill.compiler",
                "canonical_write_attempted": True,
                "governed_mutation_attempted": False,
                "dispatch_id_ref": "disp_001",
            }
        ]
        result = self.builder.validate_chain_integrity(
            [self.builder.emit(
                session_id="s",
                dispatch_id_ref="disp_001",
                from_worker_id="skill.compiler",
                from_worker_type=WorkerType.SKILL,
                to_worker_id="kernel.reducer",
                to_worker_type=WorkerType.KERNEL,
                reason="promote_attempt",
                canonical_write_attempted=True,
            )]
        )
        assert result["violation_count"] > 0

    def test_no_violation_kernel_writes_canonical(self):
        """KERNEL writing canonical is allowed (no violation)."""
        receipt = self.builder.emit(
            session_id="sess_001",
            dispatch_id_ref="disp_001",
            from_worker_id="kernel.reducer",
            from_worker_type=WorkerType.KERNEL,
            to_worker_id="kernel.state_updater",
            to_worker_type=WorkerType.KERNEL,
            reason="promotion_admitted",
            canonical_write_attempted=True,
            governed_mutation_attempted=True,
        )
        result = self.builder.validate_chain_integrity([receipt])
        assert result["violation_count"] == 0

    def test_missing_dispatch_ref_is_violation(self):
        """Chain receipt without dispatch_id_ref is a violation."""
        receipt = self.builder.emit(
            session_id="sess_001",
            dispatch_id_ref="",  # Missing
            from_worker_id="skill.extractor",
            from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.formatter",
            to_worker_type=WorkerType.AGENT,
            reason="formatting",
        )
        receipt.dispatch_id_ref = ""  # Force blank
        result = self.builder.validate_chain_integrity([receipt])
        assert result["violation_count"] > 0


# ===========================================================================
# STEP 6: KNOWLEDGE AUDIT PATCH
# ===========================================================================

class TestKnowledgeAuditPatch01:

    def setup_method(self):
        self.auditor = DispatchLineageAuditor()

    def test_canonical_artifact_without_dispatch_ref_is_critical(self):
        """Canonical artifact with no dispatch_id_ref → critical violation."""
        artifact = {
            "artifact_id": "concept_001",
            "canonical_status": "canonical",
            "dispatch_id_ref": None,
            "produced_by_worker_type": "skill",
            "produced_by_worker_id": "skill.compiler",
        }
        findings = self.auditor.audit_artifact(artifact)
        assert len(findings) > 0
        assert any(f.severity == LineageFindingSeverity.CRITICAL for f in findings)
        assert any(f.blocking for f in findings)

    def test_canonical_artifact_from_temple_is_critical(self):
        """Canonical artifact produced by TEMPLE → critical violation."""
        artifact = {
            "artifact_id": "concept_002",
            "canonical_status": "canonical",
            "dispatch_id_ref": "disp_001",
            "produced_by_worker_type": "temple",
            "produced_by_worker_id": "temple.hypothesis_gen",
        }
        findings = self.auditor.audit_artifact(artifact)
        assert any(f.severity == LineageFindingSeverity.CRITICAL for f in findings)

    def test_clean_artifact_from_kernel_no_findings(self):
        """Clean canonical artifact from KERNEL → no findings."""
        artifact = {
            "artifact_id": "concept_003",
            "canonical_status": "canonical",
            "dispatch_id_ref": "disp_001",
            "produced_by_worker_type": "kernel",
            "produced_by_worker_id": "kernel.reducer",
        }
        findings = self.auditor.audit_artifact(artifact)
        assert len(findings) == 0

    def test_provisional_artifact_from_temple_is_moderate(self):
        """Provisional artifact from TEMPLE → moderate (non-blocking)."""
        artifact = {
            "artifact_id": "concept_004",
            "canonical_status": "provisional",
            "dispatch_id_ref": "disp_001",
            "produced_by_worker_type": "temple",
            "produced_by_worker_id": "temple.hypothesis_gen",
        }
        findings = self.auditor.audit_artifact(artifact)
        assert any(f.severity == LineageFindingSeverity.MODERATE for f in findings)
        assert not any(f.blocking for f in findings)

    def test_candidate_artifact_from_skill_no_findings(self):
        """Candidate artifact from SKILL → no findings (allowed)."""
        artifact = {
            "artifact_id": "concept_005",
            "canonical_status": "candidate",
            "dispatch_id_ref": "disp_001",
            "produced_by_worker_type": "skill",
            "produced_by_worker_id": "skill.extractor",
        }
        findings = self.auditor.audit_artifact(artifact)
        assert len(findings) == 0

    def test_audit_report_clean_batch(self):
        """Batch of clean artifacts → clean verdict."""
        artifacts = [
            {
                "artifact_id": f"art_{i}",
                "canonical_status": "canonical",
                "dispatch_id_ref": f"disp_{i}",
                "produced_by_worker_type": "kernel",
                "produced_by_worker_id": "kernel.reducer",
            }
            for i in range(5)
        ]
        report = self.auditor.audit_report(artifacts, [])
        assert report["verdict"] == "clean"
        assert report["canonical_mutations_outside_kernel"] == 0

    def test_audit_report_violated_batch(self):
        """Batch with violations → violated verdict."""
        artifacts = [
            {
                "artifact_id": "art_bad",
                "canonical_status": "canonical",
                "dispatch_id_ref": None,
                "produced_by_worker_type": "skill",
                "produced_by_worker_id": "skill.compiler",
            }
        ]
        report = self.auditor.audit_report(artifacts, [])
        assert report["verdict"] == "violated"
        assert report["blocking_findings"] > 0


# ===========================================================================
# STEP 8: RUNTIME MANIFEST
# ===========================================================================

class TestRuntimeManifest:

    def test_manifest_has_hash_after_freeze(self):
        """Manifest must have a hash after freeze()."""
        manifest = ManifestBootstrap.create_default("sess_001")
        assert manifest.manifest_hash
        assert manifest.manifest_hash.startswith("sha256:")

    def test_manifest_hash_deterministic(self):
        """Same manifest config → same hash."""
        m1 = RuntimeManifest(
            manifest_id="test",
            kernel_version="v1",
            timestamp_created="2026-04-04T00:00:00Z",
        )
        m2 = RuntimeManifest(
            manifest_id="test",
            kernel_version="v1",
            timestamp_created="2026-04-04T00:00:00Z",
        )
        m1.freeze()
        m2.freeze()
        assert m1.manifest_hash == m2.manifest_hash

    def test_manifest_has_four_stores(self):
        """Default manifest declares exactly 4 stores."""
        manifest = ManifestBootstrap.create_default("sess_001")
        assert len(manifest.stores) == 4

    def test_store_refs_generated_correctly(self):
        """store_refs dict should include all 4 store purposes."""
        manifest = ManifestBootstrap.create_default("sess_001")
        refs = manifest.to_store_refs()
        assert "context" in refs
        assert "ledger" in refs
        assert "transcript" in refs
        assert "shadow" in refs

    def test_validate_receipt_manifest_ref(self):
        """Receipt with correct manifest_hash validates."""
        manifest = ManifestBootstrap.create_default("sess_001")
        assert ManifestBootstrap.validate_receipt_manifest_ref(
            manifest.manifest_hash, manifest
        ) == True

    def test_validate_wrong_manifest_ref_fails(self):
        """Receipt with wrong manifest_hash fails validation."""
        manifest = ManifestBootstrap.create_default("sess_001")
        assert ManifestBootstrap.validate_receipt_manifest_ref(
            "sha256:wronghash", manifest
        ) == False

    def test_capability_surface_declared(self):
        """Default manifest declares skills and agents."""
        manifest = ManifestBootstrap.create_default("sess_001")
        assert manifest.capability_surface.skill_count > 0
        assert manifest.capability_surface.agent_count > 0
        assert manifest.capability_surface.tools_frozen == True
        assert manifest.capability_surface.include_mcp == False


# ===========================================================================
# CROSS-LAYER INTEGRATION TEST
# ===========================================================================

class TestLayerIntegration:

    def test_pressure_feeds_affect_without_routing_change(self):
        """Pressure signal feeds affect; affect does NOT change routing."""
        computer = PressureSignalComputer()
        translator = AffectTranslator()

        evidence = EvidenceBasis(budget_state="near_limit", contradictions_detected=1)
        signal = computer.compute("sess_001", evidence)
        affect = translator.translate(signal)

        # Affect is display-only — routing effect comes from signal, not affect
        assert affect.display_only == True
        assert affect.may_influence_routing == False
        # Signal still drives routing
        assert signal.routing_effect != RoutingEffect.REFUSE  # moderate input

    def test_chain_receipt_links_to_dispatch(self):
        """Chain receipt dispatch_id_ref traces back to dispatch layer."""
        builder = ChainReceiptBuilder()
        receipt = builder.emit(
            session_id="sess_001",
            dispatch_id_ref="disp_STEP3_run42",
            from_worker_id="skill.claim_extraction",
            from_worker_type=WorkerType.SKILL,
            to_worker_id="agent.link_proposer",
            to_worker_type=WorkerType.AGENT,
            reason="linking_required",
        )
        assert receipt.dispatch_id_ref == "disp_STEP3_run42"

    def test_manifest_feeds_dispatch_store_refs(self):
        """Manifest store_refs can be directly used in dispatch receipts."""
        from helen_dispatch_v1_router import DispatchRouter

        manifest = ManifestBootstrap.create_default("sess_integration")
        store_refs = manifest.to_store_refs()

        router = DispatchRouter(
            session_id="sess_integration",
            manifest_ref=manifest.manifest_hash,
        )
        receipt, _ = router.route(
            {"text": "integration test"},
            store_refs=store_refs,
        )

        assert receipt.manifest_ref == manifest.manifest_hash
        assert receipt.store_refs == store_refs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
