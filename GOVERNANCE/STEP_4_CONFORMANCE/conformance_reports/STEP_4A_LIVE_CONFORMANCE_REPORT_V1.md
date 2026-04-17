# STEP_4A_LIVE_CONFORMANCE_REPORT_V1

Generated: 2026-04-05T17:35:45.503592Z
Base URL: http://localhost:8000
Storage Dir: storage/do_next_sessions

Verdict: FAIL

## Checks
- KERNEL_RESPONSE_SCHEMA: FAIL
  Law: API_CONTRACT_DO_NEXT_V1 response schema
  Evidence: status=0, fields=no response
- DEFER_PATH: FAIL
  Law: LIFECYCLE_INVARIANTS_V1 Phase 5 (DEFER)
  Evidence: status=0, receipt_id=None
- REJECT_PATH: FAIL
  Law: LIFECYCLE_INVARIANTS_V1 Phase 4 (REJECT)
  Evidence: status=0, receipt_id=None
- SESSION_RESUMPTION_PARENT: FAIL
  Law: LIFECYCLE_INVARIANTS_V1 §14
  Evidence: session not found
- RECEIPT_LINEAGE: FAIL
  Law: LIFECYCLE_INVARIANTS_V1 §§6–10
  Evidence: session not found
- EPOCH_CONFORMANCE: FAIL
  Law: SESSION_PERSISTENCE_SEMANTICS_V1
  Evidence: session not found
- REPLAY_CONFORMANCE: FAIL
  Law: LIFECYCLE_INVARIANTS_V1 §16
  Evidence: status_a=0, status_b=0, reply_match=True
