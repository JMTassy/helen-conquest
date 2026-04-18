"""
helen_os/meta/conclusion_v1.py — HELEN_CONCLUSION_V1 + ConclusionReducer

HELEN_CONCLUSION_V1 is a NON-AUTHORITATIVE proposal artifact.
It represents what HELEN believes a quest result should contain — proposed laws,
metrics, and sigma deltas.

It CANNOT set gates.
It CANNOT claim sovereign status.

The ConclusionReducer is the deterministic kernel that:
  1. Takes HELEN_CONCLUSION_V1 (proposed laws, metrics, sigma_deltas, notes).
  2. Takes SimLoopResult (actual phase A/B/C evidence from EPOCH3).
  3. RECOMPUTES gates from phase evidence — IGNORES any proposed gate values.
  4. Derives next_quest_seed deterministically from (quest ⊕ receipts ⊕ outputs).
  5. Computes verdict_id + verdict_hash_hex from canonical verdict payload (Pattern A).
  6. Returns ReducedConclusion (verified, receipt-anchored result).

Invariants:
  G-GATE:    HELEN cannot set gates. Gates are pure functions of phase evidence.
  G-SEED:    next_quest_seed = SHA256(canon(quest_id | sorted_receipts | outputs_hash))
             No wall clock. No external entropy.
  G-SHIP:    HELENConclusion.shipability is always "NONSHIPABLE".
  G-PROP:    helen_proposal_used=False by default.
             helen_proposal_used=True ONLY with a matching AUTHZ_RECEIPT_V1
             that binds to (verdict_id, verdict_hash_hex).
             See: HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 law.
  G-VERDICT: verdict_hash_hex = SHA256(canonical_verdict_payload)
             Changing ANY gate, metric, seed, or quest_id changes verdict_hash_hex.
             AUTHZ_RECEIPT_V1 binds to this hash — preventing retroactive authorization.

Reducer guarantee (CANYON_NONINTERFERENCE_V1):
  For same sim_result: reduce(conclusion_A, sim) gates == reduce(conclusion_B, sim) gates
  For same (conclusion, sim_result): verdict_hash_hex is identical across runs.
  Different sim_results are permitted to produce different outputs.

ReducedConclusion JSON shape:
  {
    "quest_id":                 "Q1",
    "quest_type":               "SOLVE_PARADOX",
    "contradiction_resolved":   true,
    "reality_transformed":      true,
    "temporal_insights_gained": true,
    "overall_pass":             true,
    "next_quest_seed":          "<64-char sha256>",
    "verdict_id":               "V-<8-char prefix>",
    "verdict_hash_hex":         "<64-char sha256>",
    "helen_proposal_used":      false,
    "evaluation_receipt_id":    "R-...",
    "authz_receipt":            null,
    "evidence_gates":           { ... }
  }
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, field_validator, model_validator


# ── ProposedLaw ────────────────────────────────────────────────────────────────

class ProposedLaw(BaseModel):
    """
    A law proposed by HELEN (inline, lightweight version).

    For the full PROPOSED_LAW_V1 schema with falsifiers + inscription tracking,
    use helen_os.meta.proposed_law.ProposedLawV1.

    Non-authoritative: inscription requires EPOCH3's sigma gate + kernel.propose().
    """
    law_id:     str
    statement:  str
    proof_hint: Optional[str] = None


# ── HELENConclusion ────────────────────────────────────────────────────────────

class HELENConclusion(BaseModel):
    """
    HELEN_CONCLUSION_V1: Non-authoritative proposal artifact.

    HELEN proposes: laws, metrics, sigma_deltas, receipt_pointers.
    HELEN does NOT propose gate values (contradiction_resolved,
    reality_transformed, temporal_insights_gained). Those are computed by
    EPOCH3 from phase evidence.

    Shipability: ALWAYS NONSHIPABLE. Cannot cross to SHIP without transmutation.
    Notes field: always included in receipt payload; content never authoritative.
    """

    type:                   str                                          = "HELEN_CONCLUSION_V1"
    quest_id:               str
    quest_type:             Literal["SOLVE_PARADOX", "ALTER_REALITY", "EXPLORE_TEMPORAL"]
    proposed_laws:          List[ProposedLaw]                           = []
    proposed_metrics:       Dict[str, float]                            = {}
    proposed_sigma_deltas:  Dict[str, float]                            = {}
    receipt_pointers:       List[str]                                   = []
    notes:                  Optional[str]                               = None
    shipability:            str                                         = "NONSHIPABLE"

    @field_validator("shipability", mode="before")
    @classmethod
    def enforce_nonshipable(cls, v: Any) -> str:
        """HELENConclusion is always NONSHIPABLE. Any value is overridden."""
        return "NONSHIPABLE"

    def to_receipt_payload(self) -> Dict[str, Any]:
        """Return a minimal receipt-safe payload (no raw world content)."""
        return {
            "type":                  self.type,
            "quest_id":              self.quest_id,
            "quest_type":            self.quest_type,
            "proposed_law_ids":      [law.law_id for law in self.proposed_laws],
            "proposed_metrics":      self.proposed_metrics,
            "proposed_sigma_deltas": self.proposed_sigma_deltas,
            "receipt_pointers":      self.receipt_pointers,
            "notes":                 self.notes,
            "shipability":           self.shipability,
        }


# ── ReducedConclusion ──────────────────────────────────────────────────────────

class ReducedConclusion(BaseModel):
    """
    Output of ConclusionReducer.reduce().

    Gates recomputed from phase evidence (NOT from HELENConclusion).
    verdict_id + verdict_hash_hex: Pattern A seal over (gates + seed + quest).
    helen_proposal_used=False by default; True only with matching AUTHZ_RECEIPT_V1.
    """

    quest_id:                   str
    quest_type:                 str
    contradiction_resolved:     bool
    reality_transformed:        bool
    temporal_insights_gained:   bool
    overall_pass:               bool
    next_quest_seed:            str            # 64-char SHA256 hex
    verdict_id:                 str            = ""   # "V-{verdict_hash_hex[:8]}"
    verdict_hash_hex:           str            = ""   # 64-char SHA256 of verdict payload
    helen_proposal_used:        bool           = False
    evaluation_receipt_id:      Optional[str]  = None
    authz_receipt:              Optional[Dict[str, Any]] = None   # AUTHZ_RECEIPT_V1 if authorized
    evidence_gates:             Dict[str, Any] = {}

    @model_validator(mode="after")
    def check_helen_proposal_gate(self) -> "ReducedConclusion":
        """
        G-PROP invariant: helen_proposal_used=True requires AUTHZ_RECEIPT_V1.

        If helen_proposal_used=False (default): always valid.
        If helen_proposal_used=True:
          1. authz_receipt must be present.
          2. authz_receipt must be a valid AUTHZ_RECEIPT_V1.
          3. authz_receipt must bind to (verdict_id, verdict_hash_hex).
        """
        if not self.helen_proposal_used:
            return self

        # helen_proposal_used=True path — requires AUTHZ_RECEIPT_V1 binding
        if self.authz_receipt is None:
            raise ValueError(
                "ReducedConclusion.helen_proposal_used=True requires an "
                "AUTHZ_RECEIPT_V1 (authz_receipt field). "
                "Without a receipt that binds to (verdict_id, verdict_hash_hex), "
                "helen_proposal_used must remain False. "
                "See HELEN_PROPOSAL_USE_RECEIPT_GATE_V1 law."
            )

        # Lazy imports — keep this module free of authz_receipt at module level
        from .authz_receipt import AuthzReceiptV1, validate_authz_binding, AuthzBindingError

        # Validate authz_receipt structure
        try:
            if isinstance(self.authz_receipt, dict):
                authz = AuthzReceiptV1(**self.authz_receipt)
            else:
                authz = self.authz_receipt
        except Exception as exc:
            raise ValueError(
                f"authz_receipt failed AUTHZ_RECEIPT_V1 schema validation: {exc}"
            ) from exc

        # Validate binding: must match (verdict_id, verdict_hash_hex) exactly
        try:
            validate_authz_binding(authz, self.verdict_id, self.verdict_hash_hex)
        except AuthzBindingError as exc:
            raise ValueError(str(exc)) from exc

        return self


# ── ConclusionReducer ──────────────────────────────────────────────────────────

class ConclusionReducer:
    """
    Deterministic reducer: HELENConclusion + SimLoopResult → ReducedConclusion.

    Invariants:
      CANYON_NONINTERFERENCE_V1:
        Same E_adm (sim_result) → same gates AND same verdict_hash_hex.
        Different HELENConclusion proposals cannot change the verdict.

      HELEN_PROPOSAL_USE_RECEIPT_GATE_V1:
        helen_proposal_used=False unless caller explicitly passes authorized authz.
        The model_validator enforces the AUTHZ_RECEIPT_V1 binding.

    Seed derivation (G-SEED):
      next_quest_seed = SHA256(quest_id | sorted_receipts | outputs_hash)
      outputs_hash    = SHA256(canonical_json(gates + metrics))

    Verdict sealing (G-VERDICT / Pattern A):
      verdict_payload  = canonical_json(quest_id + quest_type + gates + seed)
      verdict_hash_hex = SHA256(verdict_payload)
      verdict_id       = "V-{verdict_hash_hex[:8]}"
    """

    @staticmethod
    def _derive_next_quest_seed(
        quest_id:         str,
        receipt_pointers: List[str],
        gate_values:      Dict[str, bool],
        metrics:          Dict[str, Any],
    ) -> str:
        """Derive next_quest_seed deterministically. No wall clock, no entropy."""
        outputs: Dict[str, Any] = {
            "gate_contradiction_resolved":   gate_values["contradiction_resolved"],
            "gate_reality_transformed":      gate_values["reality_transformed"],
            "gate_temporal_insights_gained": gate_values["temporal_insights_gained"],
        }
        for k, v in sorted(metrics.items()):
            outputs[f"metric_{k}"] = v

        outputs_canonical = json.dumps(
            outputs, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        outputs_hash    = hashlib.sha256(outputs_canonical.encode()).hexdigest()
        sorted_receipts = sorted(receipt_pointers)
        seed_input      = "|".join([quest_id] + sorted_receipts + [outputs_hash])
        return hashlib.sha256(seed_input.encode()).hexdigest()

    @staticmethod
    def _derive_verdict_hash(
        quest_id:              str,
        quest_type:            str,
        gate_values:           Dict[str, bool],
        next_quest_seed:       str,
    ) -> tuple[str, str]:
        """
        Derive (verdict_id, verdict_hash_hex) via Pattern A sealing.

        The verdict payload covers (quest_id, quest_type, gates, next_quest_seed).
        Changing ANY of these changes verdict_hash_hex.
        AUTHZ_RECEIPT_V1 binds to this hash — retroactive authorization impossible.

        Returns: (verdict_id, verdict_hash_hex)
        """
        verdict_payload = {
            "quest_id":                  quest_id,
            "quest_type":                quest_type,
            "contradiction_resolved":    gate_values["contradiction_resolved"],
            "reality_transformed":       gate_values["reality_transformed"],
            "temporal_insights_gained":  gate_values["temporal_insights_gained"],
            "overall_pass":              (
                gate_values["contradiction_resolved"]
                and gate_values["reality_transformed"]
                and gate_values["temporal_insights_gained"]
            ),
            "next_quest_seed":           next_quest_seed,
        }
        canonical = json.dumps(
            verdict_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        verdict_hash_hex = hashlib.sha256(canonical.encode()).hexdigest()
        verdict_id       = f"V-{verdict_hash_hex[:8]}"
        return verdict_id, verdict_hash_hex

    @classmethod
    def reduce(
        cls,
        conclusion: HELENConclusion,
        sim_result: Any,   # SimLoopResult — duck-typed to avoid circular import
        kernel:     Any,   # GovernanceVM — required; use GovernanceVM(":memory:") for ephemeral
    ) -> ReducedConclusion:
        """
        Reduce HELENConclusion + SimLoopResult → ReducedConclusion.

        Steps:
          1. Validate kernel is provided.
          2. EvaluationGate.assess(sim_result, kernel) → gates from phase evidence.
             HELEN's proposed values are NOT consulted.
          3. Collect metrics from phase_c for seed derivation.
          4. Derive next_quest_seed (G-SEED, deterministic).
          5. Derive verdict_id + verdict_hash_hex (G-VERDICT, Pattern A seal).
          6. Return ReducedConclusion with helen_proposal_used=False.

        Args:
            conclusion:  HELENConclusion (provides quest_id, receipt_pointers; proposals ignored).
            sim_result:  SimLoopResult (phase A/B/C evidence — drives all gate computation).
            kernel:      GovernanceVM. Pass GovernanceVM(":memory:") for ephemeral non-sovereign.
        """
        from helen_os.epoch3.evaluation import EvaluationGate

        if kernel is None:
            raise ValueError(
                "ConclusionReducer.reduce() requires a kernel (GovernanceVM). "
                "Pass GovernanceVM(ledger_path=':memory:') for an ephemeral kernel."
            )

        # Step 2: Gate computation — HELEN's proposals are ignored
        evaluation = EvaluationGate.assess(sim_result, kernel)

        # Step 3: Phase evidence collection
        pc = sim_result.phase_c
        pb = sim_result.phase_b
        pa = sim_result.phase_a

        evidence_gates: Dict[str, Any] = {
            "contradiction_resolved_from": {
                "sigma_passed":          pc.sigma_passed,
                "delta_closure_success": pc.delta_closure_success,
                "paradox_injected":      pb.paradox_injected,
            },
            "reality_transformed_from": {
                "sigma_passed":       pc.sigma_passed,
                "delta_admissibility": pc.delta_admissibility,
                "shadow_ran":         len(pb.shadow_metrics_list) > 0,
                "base_ticks":         pa.ticks,
            },
            "temporal_insights_gained_from": {
                "sigma_passed":         pc.sigma_passed,
                "laws_inscribed_count": pc.laws_inscribed_count,
            },
        }

        metrics_snapshot: Dict[str, float] = {
            "delta_admissibility":     float(pc.delta_admissibility),
            "delta_sovereignty_drift": float(pc.delta_sovereignty_drift),
            "laws_inscribed_count":    float(pc.laws_inscribed_count),
        }
        try:
            metrics_snapshot["delta_closure_success"] = float(pc.delta_closure_success)
        except (TypeError, ValueError):
            metrics_snapshot["delta_closure_success"] = 1.0 if pc.delta_closure_success else 0.0

        # Step 4: next_quest_seed (G-SEED)
        gate_values: Dict[str, bool] = {
            "contradiction_resolved":   evaluation.contradiction_resolved,
            "reality_transformed":      evaluation.reality_transformed,
            "temporal_insights_gained": evaluation.temporal_insights_gained,
        }
        next_quest_seed = cls._derive_next_quest_seed(
            quest_id         = conclusion.quest_id,
            receipt_pointers = list(conclusion.receipt_pointers),
            gate_values      = gate_values,
            metrics          = metrics_snapshot,
        )

        # Step 5: verdict seal (G-VERDICT / Pattern A)
        verdict_id, verdict_hash_hex = cls._derive_verdict_hash(
            quest_id        = conclusion.quest_id,
            quest_type      = conclusion.quest_type,
            gate_values     = gate_values,
            next_quest_seed = next_quest_seed,
        )

        # Step 6: Return (helen_proposal_used=False — structural default)
        return ReducedConclusion(
            quest_id                  = conclusion.quest_id,
            quest_type                = conclusion.quest_type,
            contradiction_resolved    = evaluation.contradiction_resolved,
            reality_transformed       = evaluation.reality_transformed,
            temporal_insights_gained  = evaluation.temporal_insights_gained,
            overall_pass              = evaluation.overall_pass,
            next_quest_seed           = next_quest_seed,
            verdict_id                = verdict_id,
            verdict_hash_hex          = verdict_hash_hex,
            helen_proposal_used       = False,
            evaluation_receipt_id     = evaluation.evaluation_receipt_id,
            authz_receipt             = None,
            evidence_gates            = evidence_gates,
        )
