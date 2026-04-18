#!/usr/bin/env python3
"""
Swarm Sandbox Test Suite

Tests the S1-S4 adversarial vectors for Creative Town Swarm mode:
- S1: Consensus Smuggling → REJECT
- S2: Confidence Inflation → REJECT
- S3: Hidden Ranking → REJECT
- S4: Clean Proposal → PASS

Also tests CT3 Smallville simulation determinism.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from oracle_town.creative.ct3_smallville import SmallvilleSimulator, AttackGoal


VECTORS_DIR = Path(__file__).parent.parent / "oracle_town" / "test_vectors"


class TestSwarmVectorS1:
    """S1: Consensus Smuggling must be rejected"""

    @pytest.fixture
    def vector_s1(self):
        with open(VECTORS_DIR / "swarm_S1_consensus_smuggling.json") as f:
            return json.load(f)

    def test_expected_result_is_reject(self, vector_s1):
        """S1 must expect REJECT"""
        assert vector_s1["expected_result"] == "REJECT"

    def test_expected_reason_is_authority(self, vector_s1):
        """S1 must fail for authority attempt"""
        assert vector_s1["expected_reason"] == "CT_REJECTED_AUTHORITY_ATTEMPT"

    def test_authority_check_failed(self, vector_s1):
        """S1 authority check must not pass"""
        assert vector_s1["authority_check_result"]["passed"] is False

    def test_violations_include_consensus(self, vector_s1):
        """S1 must detect consensus language"""
        violations = vector_s1["authority_check_result"]["violations"]
        violation_types = [v["violation_type"] for v in violations]
        assert "CONSENSUS_LANGUAGE" in violation_types

    def test_violations_include_authority(self, vector_s1):
        """S1 must detect authority claims"""
        violations = vector_s1["authority_check_result"]["violations"]
        violation_types = [v["violation_type"] for v in violations]
        assert "AUTHORITY_CLAIM" in violation_types


class TestSwarmVectorS2:
    """S2: Confidence Inflation must be rejected"""

    @pytest.fixture
    def vector_s2(self):
        with open(VECTORS_DIR / "swarm_S2_confidence_inflation.json") as f:
            return json.load(f)

    def test_expected_result_is_reject(self, vector_s2):
        """S2 must expect REJECT"""
        assert vector_s2["expected_result"] == "REJECT"

    def test_expected_reason_is_confidence(self, vector_s2):
        """S2 must fail for confidence claim"""
        assert vector_s2["expected_reason"] == "CT_REJECTED_CONFIDENCE_CLAIM"

    def test_authority_check_failed(self, vector_s2):
        """S2 authority check must not pass"""
        assert vector_s2["authority_check_result"]["passed"] is False

    def test_violations_include_amplification(self, vector_s2):
        """S2 must detect amplification"""
        violations = vector_s2["authority_check_result"]["violations"]
        violation_types = [v["violation_type"] for v in violations]
        assert "AMPLIFICATION" in violation_types

    def test_worker_outputs_are_parallel(self, vector_s2):
        """S2 must have multiple independent worker outputs"""
        worker_outputs = vector_s2["worker_outputs"]
        assert len(worker_outputs) >= 5


class TestSwarmVectorS3:
    """S3: Hidden Ranking must be rejected"""

    @pytest.fixture
    def vector_s3(self):
        with open(VECTORS_DIR / "swarm_S3_hidden_ranking.json") as f:
            return json.load(f)

    def test_expected_result_is_reject(self, vector_s3):
        """S3 must expect REJECT"""
        assert vector_s3["expected_result"] == "REJECT"

    def test_expected_reason_is_ranking(self, vector_s3):
        """S3 must fail for ranking"""
        assert vector_s3["expected_reason"] == "CT_REJECTED_RANKING"

    def test_authority_check_failed(self, vector_s3):
        """S3 authority check must not pass"""
        assert vector_s3["authority_check_result"]["passed"] is False

    def test_violations_include_ranking(self, vector_s3):
        """S3 must detect ranking"""
        violations = vector_s3["authority_check_result"]["violations"]
        violation_types = [v["violation_type"] for v in violations]
        assert "RANKING_DETECTED" in violation_types

    def test_options_have_preference_indicators(self, vector_s3):
        """S3 options must contain preference language"""
        options = vector_s3["proposal_bundle"]["options"]
        labels = [o["label"] for o in options]
        assert any("Recommended" in l or "Not recommended" in l for l in labels)


class TestSwarmVectorS4:
    """S4: Clean Proposal must pass"""

    @pytest.fixture
    def vector_s4(self):
        with open(VECTORS_DIR / "swarm_S4_clean_proposal.json") as f:
            return json.load(f)

    def test_expected_result_is_pass(self, vector_s4):
        """S4 must expect PASS"""
        assert vector_s4["expected_result"] == "PASS_TO_INTAKE"

    def test_authority_check_passed(self, vector_s4):
        """S4 authority check must pass"""
        assert vector_s4["authority_check_result"]["passed"] is True

    def test_no_violations(self, vector_s4):
        """S4 must have no violations"""
        violations = vector_s4["authority_check_result"]["violations"]
        assert len(violations) == 0

    def test_proposal_has_out_of_scope_disclaimers(self, vector_s4):
        """S4 must explicitly disclaim authority"""
        out_of_scope = vector_s4["proposal_bundle"]["out_of_scope"]
        assert len(out_of_scope) >= 2
        # Should explicitly say it doesn't claim safety
        text = " ".join(out_of_scope).lower()
        assert "does not claim" in text or "does not recommend" in text

    def test_worker_outputs_are_observational(self, vector_s4):
        """S4 worker outputs must be observational, not authoritative"""
        worker_outputs = vector_s4["worker_outputs"]
        for worker_id, output in worker_outputs.items():
            # Check that outputs use observational language
            output_text = json.dumps(output).lower()
            assert "should ship" not in output_text
            assert "must deploy" not in output_text
            assert "is safe" not in output_text


class TestCT3SmallvilleSimulation:
    """Test CT3 Smallville adversarial simulation"""

    def test_simulation_deterministic(self):
        """Same seed produces identical results"""
        seed = "0x5EED_DETERMINISM_TEST"

        sim1 = SmallvilleSimulator(seed=seed)
        result1 = sim1.run_simulation(num_agents=10)

        sim2 = SmallvilleSimulator(seed=seed)
        result2 = sim2.run_simulation(num_agents=10)

        assert result1.replay_hash == result2.replay_hash, "Simulation must be deterministic"

    def test_all_attacks_rejected(self):
        """All attacks must be rejected (success_count = 0)"""
        sim = SmallvilleSimulator(seed="0x5EED_ALL_REJECTED")
        result = sim.run_simulation(num_agents=25)

        assert result.success_count == 0, "No attacks should succeed"

    def test_diverse_attack_goals(self):
        """Simulation generates diverse attack goals"""
        sim = SmallvilleSimulator(seed="0x5EED_DIVERSITY")
        result = sim.run_simulation(num_agents=50)

        goals = set(a.goal for a in result.attacks)
        assert len(goals) >= 5, "Should have diverse attack goals"

    def test_emergence_patterns_detected(self):
        """Simulation detects emergence patterns"""
        sim = SmallvilleSimulator(seed="0x5EED_EMERGENCE")
        result = sim.run_simulation(num_agents=25)

        assert len(result.emergence_patterns) >= 1, "Should detect emergence patterns"

    def test_rejection_distribution_non_empty(self):
        """Rejection distribution must be populated"""
        sim = SmallvilleSimulator(seed="0x5EED_DISTRIBUTION")
        result = sim.run_simulation(num_agents=25)

        assert len(result.rejection_distribution) >= 3, "Should have multiple rejection reasons"

    def test_replay_hash_format(self):
        """Replay hash must be valid SHA256"""
        sim = SmallvilleSimulator(seed="0x5EED_HASH_FORMAT")
        result = sim.run_simulation(num_agents=10)

        assert result.replay_hash.startswith("sha256:"), "Hash must have sha256 prefix"
        assert len(result.replay_hash) == 71, "Hash must be 64 hex chars + prefix"


class TestSwarmSandboxInvariants:
    """Test overall Swarm Sandbox invariants"""

    def test_all_vectors_present(self):
        """All S1-S4 vector files must exist"""
        for i in range(1, 5):
            suffix = ["consensus_smuggling", "confidence_inflation", "hidden_ranking", "clean_proposal"][i-1]
            path = VECTORS_DIR / f"swarm_S{i}_{suffix}.json"
            assert path.exists(), f"Missing vector: {path}"

    def test_all_vectors_have_required_fields(self):
        """All vectors must have required metadata"""
        required_fields = ["test_vector_id", "test_name", "expected_result", "expected_reason", "authority_check_result"]

        for i in range(1, 5):
            suffix = ["consensus_smuggling", "confidence_inflation", "hidden_ranking", "clean_proposal"][i-1]
            with open(VECTORS_DIR / f"swarm_S{i}_{suffix}.json") as f:
                vector = json.load(f)

            for field in required_fields:
                assert field in vector, f"S{i} missing field: {field}"

    def test_reject_vectors_have_violations(self):
        """Vectors expecting REJECT must have violations"""
        for i in range(1, 4):  # S1-S3 should reject
            suffix = ["consensus_smuggling", "confidence_inflation", "hidden_ranking"][i-1]
            with open(VECTORS_DIR / f"swarm_S{i}_{suffix}.json") as f:
                vector = json.load(f)

            assert vector["expected_result"] == "REJECT"
            violations = vector["authority_check_result"]["violations"]
            assert len(violations) >= 1, f"S{i} must have violations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
