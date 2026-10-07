---
schema: HELEN_PROPOSAL_V1
title: AUTORESEARCH outbox migration proposal (G3) — 2026-10-07
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: swarm_v0 G3_OUTBOX_MIGRATION_PROPOSER · validator temple/autoresearch/autoresearch_policy.py::validate_packet · no packet modified
---

# AUTORESEARCH outbox migration proposal (G3), 2026-10-07

OBSERVED. Proposal only. No outbox packet was written, moved, renamed or edited. Migration would create new versions with a `supersedes` field; see the rule below.

## Baseline

- Outbox: 117 packets. VALID 31. REJECTED 86.
- Family counts for REJECTED packets: missing required fields 61, finding_type not in enum 86, sovereign must be false 34, evidence must be a non-empty list 11, schema must be 16, reducer_required must be true 12, canon must be false 6.
- Cross-check against the existing audit (`docs/proposals/AUTORESEARCH_OUTBOX_POLICY_AUDIT_2026_10_07.md`): rejected set match = True, valid set match = True.
- Distinct free finding_type values, counting an absent key as one value: 38.

## finding_type mapping

| Free value | Enum | Count | Rationale |
|---|---|---:|---|
| `gap` | `proposal` | 30 | free 'gap' names a concrete code or config defect that carries a proposed change |
| `semantic_collision` | `risk` | 10 | one colour token carries two governance meanings, a risk to legibility of governance state |
| `<absent>` | `risk` | 6 | key absent in packet; enum assigned per packet from its own summary (see packets[].finding_type_rationale) |
| `<absent>` | `proposal` | 5 | key absent in packet; enum assigned per packet from its own summary (see packets[].finding_type_rationale) |
| `compound_triple_green_source_live` | `risk` | 1 | one green token signals three independent states, a risk to legibility of governance state |
| `compound_wh_fix_independent` | `proposal` | 1 | proposed token replacement, independent of other changes |
| `constant_drift` | `test_gap` | 1 | constant diverges from the values tests use, and no test imports it |
| `cross_output_contradiction` | `risk` | 1 | two outputs contradict each other, a risk to boot-signal consistency |
| `data_loss` | `risk` | 1 | finding reports silent data loss on a live path |
| `dead_branch` | `compost_candidate` | 1 | unreachable branch |
| `dead_code_state_color_block_plus_shipped_canon_audit` | `compost_candidate` | 1 | STATE_COLOR block is dead code |
| `documentation_mismatch` | `doc_gap` | 1 | docstring or comment contradicts the code |
| `fix_proposal` | `proposal` | 1 | finding is a concrete fix proposal |
| `fix_ready` | `proposal` | 1 | finding reports a fix confirmed ready for operator review |
| `grn_semantic_collision_live_vs_active_operational_states` | `risk` | 1 | live and active operational states share the admitted colour, a risk to legibility of governance state |
| `grn_usage_confirmed_correct_admission_state_machine` | `proposal` | 1 | audit records a correction of a prior prediction with no patch; carried as proposal with no change requested |
| `joint_patch_simulation_safe` | `proposal` | 1 | simulation of a joint patch |
| `live_confirmation + fix_simulation` | `proposal` | 1 | live confirmation of a defect plus a simulated fix |
| `liveness_governance_collision` | `risk` | 1 | a liveness badge shares the governance-admitted colour, a risk to legibility of governance state |
| `metric_unrunnable` | `test_gap` | 1 | the metric as written cannot run, a gap in test coverage |
| `missing_append` | `proposal` | 1 | one-line append is missing from an admission branch; proposed fix |
| `phantom_default` | `risk` | 1 | evaluator reports a default value as if it were measured, a risk to logged data |
| `phantom_reference` | `doc_gap` | 1 | template text references a configuration that does not exist, a documentation accuracy gap |
| `recurrence_residual` | `risk` | 1 | residual of a previously logged collision is still present, a risk |
| `redundant_instruction_3x` | `compost_candidate` | 1 | prompt lines identified as redundant |
| `risk_clearance` | `risk` | 1 | packet records a risk being cleared; kept under 'risk' so the clearance stays attached to the same risk class |
| `sbdot_teal_contingency_resolution` | `proposal` | 1 | proposed token change that resolves a contingency |
| `semantic_collision_benign_rendering` | `risk` | 1 | one colour token carries two meanings; rendering is not broken but the meaning is ambiguous |
| `semantic_collision_benign_rendering_no_existing_slot` | `risk` | 1 | one colour token carries two meanings; rendering is not broken but the meaning is ambiguous |
| `semantic_collision_cascade` | `risk` | 1 | one colour token carries two governance meanings, a risk to legibility of governance state |
| `semantic_collision_fork_resolution` | `risk` | 1 | one colour token carries two governance meanings, a risk to legibility of governance state |
| `semantic_collision_gate_pass_vs_sa_admitted` | `risk` | 1 | a gate PASS verdict shares the governance-admitted colour, a risk to legibility of governance state |
| `semantic_collision_grn_token_dual_use_shipped_and_live_states` | `risk` | 1 | one green token signals two operational states, a risk to legibility of governance state |
| `semantic_collision_live` | `risk` | 1 | one colour token carries two governance meanings, a risk to legibility of governance state |
| `semantic_collision_sb_dot_liveness_vs_sa_admitted` | `risk` | 1 | a liveness dot shares the governance-admitted colour, a risk to legibility of governance state |
| `semantic_collision_structural_token_borrowed_for_emotional_state_plus_dim_option_blocked` | `risk` | 1 | a structural dimming token is borrowed for an emotional state, a risk to colour meaning |
| `semantic_collision_tree_clean_vs_sa_admitted` | `risk` | 1 | a clean-tree state shares the governance-admitted colour, a risk to legibility of governance state |
| `sk1_sk2_type_dot_vs_state_label_pur_collision` | `risk` | 1 | the type and the state share one purple token, a risk to legibility |
| `verification` | `proposal` | 1 | verification of an already proposed guard or fix; carries the proposed change forward |

The 11 absent-key packets get an enum per packet from their own summary; their rationales are in the JSON.

## Supersedes rule (Correction != Erasure)

- A migrated packet is a NEW file. Its `packet_id` gets a `-M1` suffix.
- It carries `"supersedes": {"packet_id": <original>, "file": <original file>}`.
- The original file stays byte-identical and is never edited, moved or deleted.
- The operator decides where the new file is placed and whether it is admitted.

## Normalisation and missing-field rules

- `schema`: AUTORESEARCH_PACKET_V1 (absent or other value normalised)
- `authority_sovereign_canon`: false (absent normalised to false; a true or other value is OPERATOR_INPUT_REQUIRED)
- `ledger_effect`: 'none'
- `reducer_required`: true (absent or false normalised to true)
- `source_refs`: absent: copied from target/target_surface/file/prior_packet/parent_packet if present, else []
- `risk_flags`: absent: []
- `recommended_action`: absent or empty: ROUTE_TO_OPERATOR_FOR_REVIEW (sibling convention, non-action)
- `summary`: absent or empty: copied verbatim from hypothesis, else finding, else key_insight, else OPERATOR_INPUT_REQUIRED
- `evidence`: dict: serialised as 'key: value' list; string: wrapped; empty or absent: OPERATOR_INPUT_REQUIRED
- `in_memory_rule`: Fields marked OPERATOR_INPUT_REQUIRED are not applied to the in-memory copy, so the validator still reports them.

## Result

- would_become_valid (in-memory, validator passes): **81** of 86
- still_invalid: **5**
- Still-invalid reason counts: missing required fields 5, evidence must be a non-empty list 5.
- Every migrated packet still needs operator confirmation of its finding_type. The validator checks shape only.
- Operator input required (not applied in memory): `AR-sandbox-vgrammar-e77-skill-active-pur-collapse.json` (evidence), `AR-sandbox-vgrammar-e78-memory-canon-cy-dual-use.json` (evidence), `AR-sandbox-vgrammar-e79-skill-active-pur-css-confirmed.json` (evidence), `AR-sandbox-vgrammar-e80-task-waiting-amber-triple.json` (evidence), `AR-sandbox-vgrammar-e86-wh-compound-verification.json` (evidence).

## Per-packet table

| Packet | Current finding_type | Proposed enum | Missing required fields (OP = operator input) | Valid after in-memory migration |
|---|---|---|---|---|
| `AR-575d4b83a114.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-9d167217e823.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-context-rank-companion-apply-e17.json` | `fix_ready` | `proposal` | - | yes |
| `AR-context-rank-companion-drop-e14.json` | `data_loss` | `risk` | - | yes |
| `AR-context-rank-companion-fix-e15.json` | `fix_proposal` | `proposal` | - | yes |
| `AR-context-rank-risk-clear-e16.json` | `risk_clearance` | `risk` | risk_flags | yes |
| `AR-contextrank-e35-template-idempotent.json` | `gap` | `proposal` | - | yes |
| `AR-contextrank-e50-propose-action-contradiction.json` | `cross_output_contradiction` | `risk` | sovereign | yes |
| `AR-contextrank-e52-metric-broken.json` | `metric_unrunnable` | `test_gap` | sovereign | yes |
| `AR-contextrank-e53-guard-verified.json` | `verification` | `proposal` | sovereign | yes |
| `AR-contextrank-e54-e28-recency-live.json` | `live_confirmation + fix_simulation` | `proposal` | sovereign | yes |
| `AR-contextrank-e90-history-format-void.json` | `<absent>` | `risk` | finding_type, packet_id, recommended_action, reducer_required, risk_flags, schema, source_refs, sovereign | yes |
| `AR-ctx-rank-stab-e11.json` | `phantom_default` | `risk` | - | yes |
| `AR-ctxrank-e24-sortkeys-list-noop.json` | `gap` | `proposal` | - | yes |
| `AR-ctxrank-e28-last-updated-dropped.json` | `gap` | `proposal` | - | yes |
| `AR-f7ec3779a583.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-halctx-e30-6c84165362c2.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-init-rank-d9c2.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-initrank-e25-docstring-stale.json` | `documentation_mismatch` | `doc_gap` | - | yes |
| `AR-initrank-e37-phantom-tweak-template.json` | `phantom_reference` | `doc_gap` | - | yes |
| `AR-initrank-e45-flags-sev-zeroed.json` | `gap` | `proposal` | recommended_action, reducer_required, risk_flags, sovereign | yes |
| `AR-initrank-e46-noise-discriminator.json` | `gap` | `proposal` | recommended_action, reducer_required, risk_flags, sovereign | yes |
| `AR-initrank-e47-len-tiebreaker.json` | `gap` | `proposal` | recommended_action, reducer_required, risk_flags, sovereign | yes |
| `AR-initrank-e48-refs-tiebreaker.json` | `gap` | `proposal` | recommended_action, reducer_required, risk_flags, sovereign | yes |
| `AR-initrank-e57-analytic-cliff-bounds.json` | `gap` | `proposal` | recommended_action, risk_flags, source_refs, sovereign | yes |
| `AR-initrank-e58-prescreen-formula.json` | `gap` | `proposal` | recommended_action, risk_flags, source_refs, sovereign | yes |
| `AR-initrank-e92-agent-stack-fixed-rank.json` | `<absent>` | `proposal` | finding_type, packet_id, recommended_action, reducer_required, risk_flags, schema, source_refs, sovereign, summary | yes |
| `AR-promptcomp-e22-admitted-skills-id-only.json` | `gap` | `proposal` | - | yes |
| `AR-promptcomp-e23-bootstrap-description-gap.json` | `gap` | `proposal` | - | yes |
| `AR-promptcomp-e36-admitted-lesson-dropped.json` | `gap` | `proposal` | - | yes |
| `AR-promptcomp-e3a1.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-promptcomp-e44-admitted-lesson-missing-append.json` | `missing_append` | `proposal` | sovereign | yes |
| `AR-promptcomp-e51-core-prompt-3line-reduction.json` | `redundant_instruction_3x` | `compost_candidate` | sovereign | yes |
| `AR-promptcomp-e91-weather-unconditional-fetch.json` | `<absent>` | `proposal` | finding_type, packet_id, recommended_action, reducer_required, risk_flags, schema, source_refs, sovereign, summary | yes |
| `AR-promptcomp-fieldmismatch-e9.json` | `gap` | `proposal` | recommended_action, source_refs, sovereign | yes |
| `AR-sandbox-vgrammar-e31-live-shipped-collision.json` | `semantic_collision` | `risk` | risk_flags, source_refs | yes |
| `AR-sandbox-vgrammar-e32-committed-admitted-collision.json` | `semantic_collision` | `risk` | risk_flags, source_refs | yes |
| `AR-sandbox-vgrammar-e33-gonogo-go-green-collision.json` | `semantic_collision` | `risk` | risk_flags, source_refs | yes |
| `AR-sandbox-vgrammar-e39-shipped-chainok-collision.json` | `semantic_collision` | `risk` | risk_flags, source_refs | yes |
| `AR-sandbox-vgrammar-e40-ring-branding-governance-collision.json` | `semantic_collision` | `risk` | risk_flags, source_refs | yes |
| `AR-sandbox-vgrammar-e41-temple-orbit-receipt-collision.json` | `semantic_collision` | `risk` | risk_flags, source_refs | yes |
| `AR-sandbox-vgrammar-e42-liveness-green-residual.json` | `recurrence_residual` | `risk` | risk_flags, source_refs | yes |
| `AR-sandbox-vgrammar-e43-focus-helen2027-presence-green.json` | `liveness_governance_collision` | `risk` | sovereign | yes |
| `AR-sandbox-vgrammar-e59-live-teal.json` | `semantic_collision` | `risk` | risk_flags, source_refs, summary | yes |
| `AR-sandbox-vgrammar-e60-happy-purple.json` | `semantic_collision` | `risk` | risk_flags, source_refs, summary | yes |
| `AR-sandbox-vgrammar-e61-task-check-gold.json` | `semantic_collision` | `risk` | risk_flags, source_refs, summary | yes |
| `AR-sandbox-vgrammar-e62-station-verdict-blue.json` | `semantic_collision` | `risk` | risk_flags, source_refs, summary | yes |
| `AR-sandbox-vgrammar-e63-live-teal-confirmed.json` | `semantic_collision_fork_resolution` | `risk` | risk_flags, source_refs, summary | yes |
| `AR-sandbox-vgrammar-e64-shappy-purple-secondary-collision.json` | `semantic_collision_cascade` | `risk` | risk_flags, source_refs, summary | yes |
| `AR-sandbox-vgrammar-e65-sexcited-blue-sky.json` | `semantic_collision_live` | `risk` | risk_flags, source_refs, summary | yes |
| `AR-sandbox-vgrammar-e66-proud-purple-calm-gold.json` | `semantic_collision_benign_rendering` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e67-scared-red-angry-red.json` | `semantic_collision_benign_rendering_no_existing_slot` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e68-sad-mid-structural-borrow.json` | `semantic_collision_structural_token_borrowed_for_emotional_state_plus_dim_option_blocked` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e69-cockpit-live-grn-teal.json` | `semantic_collision_grn_token_dual_use_shipped_and_live_states` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e70-sbdot-liveness-teal.json` | `semantic_collision_sb_dot_liveness_vs_sa_admitted` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e71-vrd-pass-wh.json` | `semantic_collision_gate_pass_vs_sa_admitted` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e72-tree-clean-wh.json` | `semantic_collision_tree_clean_vs_sa_admitted` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e73-le-st-ok-grn-correct.json` | `grn_usage_confirmed_correct_admission_state_machine` | `proposal` | - | yes |
| `AR-sandbox-vgrammar-e74-silive-grn-pur.json` | `grn_semantic_collision_live_vs_active_operational_states` | `risk` | - | yes |
| `AR-sandbox-vgrammar-e75-shipped-canon-statecolor-dead.json` | `dead_code_state_color_block_plus_shipped_canon_audit` | `compost_candidate` | - | yes |
| `AR-sandbox-vgrammar-e77-skill-active-pur-collapse.json` | `<absent>` | `risk` | evidence (OP), finding_type, packet_id, recommended_action, risk_flags, schema, source_refs, summary | no |
| `AR-sandbox-vgrammar-e78-memory-canon-cy-dual-use.json` | `<absent>` | `risk` | evidence (OP), finding_type, packet_id, recommended_action, risk_flags, schema, source_refs, summary | no |
| `AR-sandbox-vgrammar-e79-skill-active-pur-css-confirmed.json` | `<absent>` | `risk` | canon, evidence (OP), finding_type, packet_id, recommended_action, risk_flags, schema, source_refs, sovereign, summary | no |
| `AR-sandbox-vgrammar-e80-task-waiting-amber-triple.json` | `<absent>` | `risk` | canon, evidence (OP), finding_type, packet_id, recommended_action, risk_flags, schema, source_refs, sovereign, summary | no |
| `AR-sandbox-vgrammar-e81-source-live-compound-green.json` | `compound_triple_green_source_live` | `risk` | canon, packet_id, recommended_action, risk_flags, schema, sovereign | yes |
| `AR-sandbox-vgrammar-e82-skill-active-pur-type-label-split.json` | `sk1_sk2_type_dot_vs_state_label_pur_collision` | `risk` | canon, packet_id, recommended_action, risk_flags, schema, sovereign | yes |
| `AR-sandbox-vgrammar-e83-joint-patch-verify.json` | `joint_patch_simulation_safe` | `proposal` | canon, packet_id, recommended_action, risk_flags, schema, sovereign | yes |
| `AR-sandbox-vgrammar-e84-compound-wh-fix.json` | `compound_wh_fix_independent` | `proposal` | canon, packet_id, recommended_action, risk_flags, schema, sovereign | yes |
| `AR-sandbox-vgrammar-e85-sbdot-wh-resolution.json` | `sbdot_teal_contingency_resolution` | `proposal` | schema | yes |
| `AR-sandbox-vgrammar-e86-wh-compound-verification.json` | `<absent>` | `proposal` | evidence (OP), finding_type, packet_id, recommended_action, reducer_required, risk_flags, schema, source_refs, sovereign | no |
| `AR-sandbox-vgrammar-e87-live-reclassification.json` | `<absent>` | `proposal` | finding_type, packet_id, recommended_action, reducer_required, risk_flags, schema, source_refs, sovereign | yes |
| `AR-sandbox-vgrammar-e88-count-verify.json` | `<absent>` | `proposal` | finding_type, packet_id, recommended_action, reducer_required, risk_flags, schema, source_refs, sovereign | yes |
| `AR-sandbox-vgrammar-f2a9.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-skill-route-d1f7.json` | `gap` | `proposal` | - | yes |
| `AR-skillroute-e34-ok-quarantined-class.json` | `gap` | `proposal` | reducer_required, sovereign | yes |
| `AR-skillroute-e49-inference-rejected-missing.json` | `gap` | `proposal` | source_refs, sovereign | yes |
| `AR-skillroute-e55-manifest-codes-missing.json` | `gap` | `proposal` | source_refs, sovereign | yes |
| `AR-skillroute-e56-parse-failed-optimize.json` | `gap` | `proposal` | source_refs, sovereign | yes |
| `AR-skillroute-e89-hal-model-forbidden.json` | `<absent>` | `risk` | finding_type, packet_id, recommended_action, reducer_required, risk_flags, schema, source_refs, sovereign | yes |
| `AR-skillroute-rule2b-dead-f3c7.json` | `dead_branch` | `compost_candidate` | - | yes |
| `AR-summ-weights-e29-fallback-bias.json` | `gap` | `proposal` | source_refs, sovereign | yes |
| `AR-summ-weights-e38-register-divergence.json` | `gap` | `proposal` | source_refs, sovereign | yes |
| `AR-summ-weights-e43-symbolic-orphan.json` | `gap` | `proposal` | source_refs, sovereign | yes |
| `AR-sumweights-a8f2.json` | `gap` | `proposal` | risk_flags, source_refs | yes |
| `AR-sumweights-e10.json` | `constant_drift` | `test_gap` | risk_flags, source_refs | yes |
| `AR-sumweights-e21-vague-constraint-escape.json` | `gap` | `proposal` | - | yes |

## Decisions for the operator

1. Confirm the free-value to enum mapping above, especially `gap` (30 packets) mapped to `proposal`.
2. Confirm the absent-key enum assignments (11 packets) and the `risk` mapping for the semantic-collision family.
3. Confirm the copied summaries, serialised evidence, and the ROUTE_TO_OPERATOR_FOR_REVIEW default where it was used.
4. Supply source refs and evidence for packets listed as OPERATOR_INPUT_REQUIRED.
5. Decide the destination and whether the -M1 versions are written at all. This proposal writes nothing to the outbox.

## Files

- `migration_proposal.json` (OUTBOX_MIGRATION_PROPOSAL_V0, per-packet detail)
- `migration_proposal.md` (this file)
- `GOBLIN_RECEIPT_V0.json`
