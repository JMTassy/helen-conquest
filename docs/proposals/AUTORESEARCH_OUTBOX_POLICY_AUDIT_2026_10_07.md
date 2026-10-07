---
schema: HELEN_PROPOSAL_V1
title: AUTORESEARCH outbox policy audit — 2026-10-07 — read-only
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: branch claude/wonderful-cannon-gua790 · validator temple/autoresearch/autoresearch_policy.py::validate_packet · no packet modified
---

# AUTORESEARCH outbox policy audit — 2026-10-07

🔵 OBSERVED · read-only · no packet modified · no recommendation of migration implied.

Method: every `temple/autoresearch/outbox/*.json` loaded and passed to the repo's own `validate_packet`. Rejection reasons recorded verbatim per packet. Reason families collapsed only for the summary; the appendix keeps the exact messages.

Reading guide: a REJECTED packet is a historical trace that predates or ignores `AUTORESEARCH_PACKET_V1`. Rejection here is a validator verdict on shape, not a judgement on the finding's content. `finding_type` values outside the enum are the dominant cause; 38 distinct free-text values were used where 6 are allowed.

## Summary and appendix (generated output, verbatim)

```
AUTORESEARCH OUTBOX POLICY AUDIT — read-only — 117 packets · VALID 31 · REJECTED 86
validator: temple/autoresearch/autoresearch_policy.py::validate_packet · no file modified

## reason families (packets carrying each)
  86  finding_type not in enum
  61  missing required fields
  34  sovereign must be false (boolean)
  16  schema must be 'AUTORESEARCH_PACKET_V1', got None
  12  reducer_required must be true (boolean)
  11  evidence must be a non-empty list
   6  canon must be false (boolean)

## finding_type values outside the enum (38 distinct)
  30  gap
  11  
  10  semantic_collision
   1  fix_ready
   1  data_loss
   1  fix_proposal
   1  risk_clearance
   1  cross_output_contradiction
   1  metric_unrunnable
   1  verification
   1  live_confirmation + fix_simulation
   1  phantom_default
   1  documentation_mismatch
   1  phantom_reference
   1  missing_append
   1  redundant_instruction_3x
   1  recurrence_residual
   1  liveness_governance_collision
   1  semantic_collision_fork_resolution
   1  semantic_collision_cascade
   1  semantic_collision_live
   1  semantic_collision_benign_rendering
   1  semantic_collision_benign_rendering_no_existing_slot
   1  semantic_collision_structural_token_borrowed_for_emotional_state_plus_dim_option_blocked
   1  semantic_collision_grn_token_dual_use_shipped_and_live_states
   1  semantic_collision_sb_dot_liveness_vs_sa_admitted
   1  semantic_collision_gate_pass_vs_sa_admitted
   1  semantic_collision_tree_clean_vs_sa_admitted
   1  grn_usage_confirmed_correct_admission_state_machine
   1  grn_semantic_collision_live_vs_active_operational_states
   1  dead_code_state_color_block_plus_shipped_canon_audit
   1  compound_triple_green_source_live
   1  sk1_sk2_type_dot_vs_state_label_pur_collision
   1  joint_patch_simulation_safe
   1  compound_wh_fix_independent
   1  sbdot_teal_contingency_resolution
   1  dead_branch
   1  constant_drift

## per-packet
VALID    AR-137a79dbae09.json
VALID    AR-1c394e006626.json
VALID    AR-1f936d1bda4b.json
VALID    AR-332110575215.json
VALID    AR-3521ec730fd4.json
VALID    AR-39307ac76191.json
VALID    AR-3b7799cb88a0.json
VALID    AR-4eedf96f7ace.json
VALID    AR-5602a344e0d6.json
REJECTED AR-575d4b83a114.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
VALID    AR-5832a927028e.json
VALID    AR-603402e9d1c4.json
VALID    AR-622d76f69257.json
VALID    AR-671223d898a2.json
VALID    AR-83d2c37481c7.json
VALID    AR-842e7f4922cf.json
VALID    AR-941d3bbb6333.json
VALID    AR-944b83d2fa9e.json
VALID    AR-9598791758a5.json
REJECTED AR-9d167217e823.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
VALID    AR-a657ef5764d8.json
VALID    AR-b634eae985b4.json
VALID    AR-c1f03861ffdc.json
VALID    AR-c73a8b88fb8d.json
VALID    AR-c8121dc0789e.json
VALID    AR-cecf4c5b553f.json
VALID    AR-cfad921197fc.json
REJECTED AR-context-rank-companion-apply-e17.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'fix_ready'
REJECTED AR-context-rank-companion-drop-e14.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'data_loss'
REJECTED AR-context-rank-companion-fix-e15.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'fix_proposal'
REJECTED AR-context-rank-risk-clear-e16.json
           - missing required fields: ['risk_flags']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'risk_clearance'
REJECTED AR-contextrank-e35-template-idempotent.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-contextrank-e50-propose-action-contradiction.json
           - missing required fields: ['sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'cross_output_contradiction'
REJECTED AR-contextrank-e52-metric-broken.json
           - missing required fields: ['sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'metric_unrunnable'
REJECTED AR-contextrank-e53-guard-verified.json
           - missing required fields: ['sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'verification'
REJECTED AR-contextrank-e54-e28-recency-live.json
           - missing required fields: ['sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'live_confirmation + fix_simulation'
REJECTED AR-contextrank-e90-history-format-void.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['finding_type', 'packet_id', 'recommended_action', 'reducer_required', 'risk_flags', 'schema', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-ctx-rank-stab-e11.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'phantom_default'
REJECTED AR-ctxrank-e24-sortkeys-list-noop.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-ctxrank-e28-last-updated-dropped.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
VALID    AR-d30a1396bd93.json
VALID    AR-e8d1841c6d2f.json
VALID    AR-ea91f2b2230c.json
VALID    AR-ed9bd849fb7e.json
VALID    AR-eec73bbbf239.json
VALID    AR-eee30b74e78d.json
REJECTED AR-f7ec3779a583.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-halctx-e30-6c84165362c2.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-init-rank-d9c2.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-initrank-e25-docstring-stale.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'documentation_mismatch'
REJECTED AR-initrank-e37-phantom-tweak-template.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'phantom_reference'
REJECTED AR-initrank-e45-flags-sev-zeroed.json
           - missing required fields: ['recommended_action', 'reducer_required', 'risk_flags', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-initrank-e46-noise-discriminator.json
           - missing required fields: ['recommended_action', 'reducer_required', 'risk_flags', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-initrank-e47-len-tiebreaker.json
           - missing required fields: ['recommended_action', 'reducer_required', 'risk_flags', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-initrank-e48-refs-tiebreaker.json
           - missing required fields: ['recommended_action', 'reducer_required', 'risk_flags', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-initrank-e57-analytic-cliff-bounds.json
           - missing required fields: ['recommended_action', 'risk_flags', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-initrank-e58-prescreen-formula.json
           - missing required fields: ['recommended_action', 'risk_flags', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-initrank-e92-agent-stack-fixed-rank.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['finding_type', 'packet_id', 'recommended_action', 'reducer_required', 'risk_flags', 'schema', 'source_refs', 'sovereign', 'summary']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-promptcomp-e22-admitted-skills-id-only.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-promptcomp-e23-bootstrap-description-gap.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-promptcomp-e36-admitted-lesson-dropped.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-promptcomp-e3a1.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-promptcomp-e44-admitted-lesson-missing-append.json
           - missing required fields: ['sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'missing_append'
REJECTED AR-promptcomp-e51-core-prompt-3line-reduction.json
           - missing required fields: ['sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'redundant_instruction_3x'
REJECTED AR-promptcomp-e91-weather-unconditional-fetch.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['finding_type', 'packet_id', 'recommended_action', 'reducer_required', 'risk_flags', 'schema', 'source_refs', 'sovereign', 'summary']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-promptcomp-fieldmismatch-e9.json
           - missing required fields: ['recommended_action', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-sandbox-vgrammar-e31-live-shipped-collision.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e32-committed-admitted-collision.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e33-gonogo-go-green-collision.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e39-shipped-chainok-collision.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e40-ring-branding-governance-collision.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e41-temple-orbit-receipt-collision.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e42-liveness-green-residual.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'recurrence_residual'
REJECTED AR-sandbox-vgrammar-e43-focus-helen2027-presence-green.json
           - missing required fields: ['sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'liveness_governance_collision'
REJECTED AR-sandbox-vgrammar-e59-live-teal.json
           - missing required fields: ['risk_flags', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e60-happy-purple.json
           - missing required fields: ['risk_flags', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e61-task-check-gold.json
           - missing required fields: ['risk_flags', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e62-station-verdict-blue.json
           - missing required fields: ['risk_flags', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision'
REJECTED AR-sandbox-vgrammar-e63-live-teal-confirmed.json
           - missing required fields: ['risk_flags', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_fork_resolution'
REJECTED AR-sandbox-vgrammar-e64-shappy-purple-secondary-collision.json
           - missing required fields: ['risk_flags', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_cascade'
REJECTED AR-sandbox-vgrammar-e65-sexcited-blue-sky.json
           - missing required fields: ['risk_flags', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_live'
REJECTED AR-sandbox-vgrammar-e66-proud-purple-calm-gold.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_benign_rendering'
REJECTED AR-sandbox-vgrammar-e67-scared-red-angry-red.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_benign_rendering_no_existing_slot'
REJECTED AR-sandbox-vgrammar-e68-sad-mid-structural-borrow.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_structural_token_borrowed_for_emotional_state_plus_dim_option_blocked'
REJECTED AR-sandbox-vgrammar-e69-cockpit-live-grn-teal.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_grn_token_dual_use_shipped_and_live_states'
REJECTED AR-sandbox-vgrammar-e70-sbdot-liveness-teal.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_sb_dot_liveness_vs_sa_admitted'
REJECTED AR-sandbox-vgrammar-e71-vrd-pass-wh.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_gate_pass_vs_sa_admitted'
REJECTED AR-sandbox-vgrammar-e72-tree-clean-wh.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'semantic_collision_tree_clean_vs_sa_admitted'
REJECTED AR-sandbox-vgrammar-e73-le-st-ok-grn-correct.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'grn_usage_confirmed_correct_admission_state_machine'
REJECTED AR-sandbox-vgrammar-e74-silive-grn-pur.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'grn_semantic_collision_live_vs_active_operational_states'
REJECTED AR-sandbox-vgrammar-e75-shipped-canon-statecolor-dead.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'dead_code_state_color_block_plus_shipped_canon_audit'
REJECTED AR-sandbox-vgrammar-e77-skill-active-pur-collapse.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['evidence', 'finding_type', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-sandbox-vgrammar-e78-memory-canon-cy-dual-use.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['evidence', 'finding_type', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'source_refs', 'summary']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-sandbox-vgrammar-e79-skill-active-pur-css-confirmed.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['canon', 'evidence', 'finding_type', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'source_refs', 'sovereign', 'summary']
           - sovereign must be false (boolean)
           - canon must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-sandbox-vgrammar-e80-task-waiting-amber-triple.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['canon', 'evidence', 'finding_type', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'source_refs', 'sovereign', 'summary']
           - sovereign must be false (boolean)
           - canon must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-sandbox-vgrammar-e81-source-live-compound-green.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['canon', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'sovereign']
           - sovereign must be false (boolean)
           - canon must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'compound_triple_green_source_live'
REJECTED AR-sandbox-vgrammar-e82-skill-active-pur-type-label-split.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['canon', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'sovereign']
           - sovereign must be false (boolean)
           - canon must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'sk1_sk2_type_dot_vs_state_label_pur_collision'
REJECTED AR-sandbox-vgrammar-e83-joint-patch-verify.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['canon', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'sovereign']
           - sovereign must be false (boolean)
           - canon must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'joint_patch_simulation_safe'
REJECTED AR-sandbox-vgrammar-e84-compound-wh-fix.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['canon', 'packet_id', 'recommended_action', 'risk_flags', 'schema', 'sovereign']
           - sovereign must be false (boolean)
           - canon must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'compound_wh_fix_independent'
REJECTED AR-sandbox-vgrammar-e85-sbdot-wh-resolution.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['schema']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'sbdot_teal_contingency_resolution'
REJECTED AR-sandbox-vgrammar-e86-wh-compound-verification.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['evidence', 'finding_type', 'packet_id', 'recommended_action', 'reducer_required', 'risk_flags', 'schema', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-sandbox-vgrammar-e87-live-reclassification.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['finding_type', 'packet_id', 'recommended_action', 'reducer_required', 'risk_flags', 'schema', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-sandbox-vgrammar-e88-count-verify.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['finding_type', 'packet_id', 'recommended_action', 'reducer_required', 'risk_flags', 'schema', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-sandbox-vgrammar-f2a9.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-skill-route-d1f7.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-skillroute-e34-ok-quarantined-class.json
           - missing required fields: ['reducer_required', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-skillroute-e49-inference-rejected-missing.json
           - missing required fields: ['source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-skillroute-e55-manifest-codes-missing.json
           - missing required fields: ['source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-skillroute-e56-parse-failed-optimize.json
           - missing required fields: ['source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-skillroute-e89-hal-model-forbidden.json
           - schema must be 'AUTORESEARCH_PACKET_V1', got None
           - missing required fields: ['finding_type', 'packet_id', 'recommended_action', 'reducer_required', 'risk_flags', 'schema', 'source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - reducer_required must be true (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got ''
           - evidence must be a non-empty list
REJECTED AR-skillroute-rule2b-dead-f3c7.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'dead_branch'
REJECTED AR-summ-weights-e29-fallback-bias.json
           - missing required fields: ['source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-summ-weights-e38-register-divergence.json
           - missing required fields: ['source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-summ-weights-e43-symbolic-orphan.json
           - missing required fields: ['source_refs', 'sovereign']
           - sovereign must be false (boolean)
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-sumweights-a8f2.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
REJECTED AR-sumweights-e10.json
           - missing required fields: ['risk_flags', 'source_refs']
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'constant_drift'
REJECTED AR-sumweights-e21-vague-constraint-escape.json
           - finding_type must be one of ['compost_candidate', 'doc_gap', 'proposal', 'quest_candidate', 'risk', 'test_gap'], got 'gap'
```
