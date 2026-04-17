---
name: feynman/peer_review
description: Tough-but-constructive peer review of any HELEN artifact (manifesto, claim, draft, code change). Wraps the Feynman /review workflow under HELEN's K2 / Rule 3 ("Editor cannot approve own work"). Use when the user asks for a review, critique, or wants to surface weaknesses before SHIP.
fused_from: feynman v0.2.20 / peer-review
helen_gate: K2_RULE_3 (HELEN.md §"Property 1: Authority Cannot Self-Witness")
helen_witness: R-20260416-0002
---

# Peer Review (HELEN-fused)

Surfaces weaknesses, not approvals. Output is a **claim** (pending), not a verdict.

## Invocation

From repo root (`helen_os_v1/`):

```
python3 tools/helen_say.py "REVIEW_REQUEST: <artifact_id_or_path>" --op fetch
```

`--op review` is reserved but not yet wired; today, submit reviews as `--op fetch` payloads tagged `REVIEW_V1`. Do NOT bind `/review` as a slash command — collides with HELEN's CLI grammar.

## Subagents used

- `researcher` — gathers context the artifact references
- `reviewer` — produces severity-graded feedback

## HELEN conditions (from witness audit, 2026-04-16)

1. **reviewer ≠ proposer.** The claim must carry distinct `proposer` and `reviewer` identity hashes. Same identity in both roles → fail-closed at K2.
2. **Output as pending claim, not verdict.** Review writes a `REVIEW_V1` payload that requires an external witness before it becomes binding.
3. **Termination is sacred.** Every review ends `SHIP` or `ABORT` (HELEN.md Property 3 / Rule 5 — only two valid terminators). A review that wants revisions emits `ABORT` with a `revisions[]` payload listing what must change before resubmit; the resubmit is a *new* review claim with its own receipt.

## Output

`artifacts/reviews/REVIEW_V1__<claim_id>__<review_id>.json` — payload-hashed, ledger-linked. Markdown sidecar at the same basename for human reading. Both must reference the source artifact's `cum_hash`.

## Provenance

See `.provenance.md`.
