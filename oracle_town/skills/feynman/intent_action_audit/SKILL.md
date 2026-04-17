---
name: feynman/intent_action_audit
description: Compare a stated intention (paper, manifesto, plan) against actual action (codebase, ledger entries, run artifacts). Records the gap, never resolves it. This skill IS HELEN's CONTRADICTION step with a sharper blade.
fused_from: feynman v0.2.20 / paper-code-audit
helen_loop_stage: CONTRADICTION (HELEN.md §"The Consciousness Loop")
helen_witness: R-20260416-0003 (chained)
---

# Intent ↔ Action Audit (HELEN-fused)

Built on Feynman's `/audit` (paper-vs-codebase). Re-pointed inside HELEN to audit any **intention artifact** against any **action artifact**:

| Intention | Action |
|---|---|
| Paper claims | Public codebase |
| HELEN manifesto | Run ledger |
| District spec | District events |
| Conquest rules | Player ledger |
| Slash command help | Slash command behavior |

## Invocation

From repo root (`helen_os_v1/`):

```
python3 tools/helen_say.py "AUDIT_REQUEST: <intention_ref> :: <action_ref>" --op fetch
```

`--op audit` is reserved but not yet wired; today, submit as `--op fetch` payloads tagged `AUDIT_V1`. The audit body itself is produced by a sub-agent reading both refs and emitting the markdown artifact described under "Output" below.

## Subagents used

- `researcher` — extracts claims from the intention artifact
- `verifier` — walks the action artifact, finds matches and mismatches

## HELEN conditions (from witness audit, 2026-04-16)

1. **Record gaps, do not resolve them.** A clean "intention and action agree" verdict is still a *claim awaiting witness*, not a closure. Property 2 (Contradiction Is The Signal) forbids silencing the gap.
2. **`AUDIT_V1` payload, hash-chained.** Every audit run appends to `town/ledger_v1.ndjson` as `op=audit` with `payload_hash` and `cum_hash`. No free-floating markdown without a ledger pointer.
3. **`.provenance.md` is the receipt.** Each audit emits a sidecar listing intention SHA, action SHA, model+seed for any LLM step.

## Output

- `artifacts/audits/AUDIT_V1__<audit_id>.json` (canonical, hashed)
- `artifacts/audits/AUDIT_V1__<audit_id>.md` (human reading)
- `artifacts/audits/AUDIT_V1__<audit_id>.provenance.md`

All three reference each other and the ledger entry.

## Provenance

See `.provenance.md`.
