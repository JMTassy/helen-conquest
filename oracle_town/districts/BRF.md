# BRF District Charter

**Module:** Brief & Synthesis

## Purpose

Synthesize insights into a single actionable brief: the "ONE BET" for this run. BRF is the narrative layer—it tells the story of what happened and why it matters.

## Inputs

**Required:**
- `artifacts/insights.json` (from INS)
- `artifacts/anomalies.json` (from INS)
- `oracle_town/memory/index.json` (precedents and context)
- `oracle_town/ledger/decisions.jsonl` (past decisions, for narrative consistency)

**No direct state mutations.** BRF reads `city_current.json` for metadata only.

## Outputs

**Artifacts produced:**
- `brief.md` — Markdown brief (~300–500 words)
- `one_bet.txt` — Single-sentence summary for state
- `brf_receipt.json` — Cryptographic proof

**State mutations:**
- Writes to `city_current.json`: `one_bet`, `modules.BRF.progress`, `modules.BRF.status`, `modules.BRF.desc`
- Appends to `oracle_town/ledger/artifacts.jsonl` (brief metadata)

## One Bet Format

**Constraint:** Single sentence, max 100 characters, actionable.

**Example:** "Reduce customer churn by prioritizing renewal outreach to top 10% accounts."

## Brief Schema (Markdown)

```markdown
# Brief — Run 173

## Summary
[1–2 sentence executive summary]

## Key Insights
- Insight 1: Theme + action
- Insight 2: Theme + action
- Insight 3: Theme + action

## Anomalies
[List of flagged issues]

## Recommendation
[Why this ONE BET? What will it accomplish?]

## Risk & Blockers
[Any concerns for TRI gate?]
```

## Gates (Enforced by TRI)

**BRF cannot proceed unless:**
1. `brief.md` exists and is valid Markdown
2. `one_bet.txt` is exactly 1 line, ≤100 chars
3. Brief references all high-severity anomalies
4. Brief is ≤2000 chars (fits git diffs, not essay-length)
5. `brf_receipt.json` signed by registered attestor

**Failure mode:** TRI → NO_SHIP (K1 fail-closed)

## Determinism Contract

**BRF must guarantee:**
- Same insights + same memory state → identical brief
- Narrative ordering deterministic (sort insights by ID, anomalies by severity then code)
- No timestamps (only run date/ID for metadata)
- Stable markdown formatting (consistent heading levels, bullet ordering)

**Test:** Run BRF twice; markdown hash must match.

## Forbidden Actions

- BRF may NOT modify insights or anomalies
- BRF may NOT write to other modules' state
- BRF may NOT call external LLMs for synthesis (must be deterministic templating)
- BRF may NOT create new memory entries (read-only)

## State Writes Allowed

```json
{
  "one_bet": "string (max 100 chars)",
  "modules": {
    "BRF": {
      "status": "OFF|BLD|OK|WRN|FLR",
      "progress": 0-8,
      "desc": "string (max 50 chars)"
    }
  }
}
```

## Receipts Required

```json
{
  "brf_receipt": {
    "timestamp_unix": 1706601600,
    "brief_length": 1200,
    "brief_hash": "sha256:ghi789...",
    "one_bet": "...",
    "run_id": 173,
    "attestor_id": "brf_attestor_001",
    "signature": "ed25519:def123..."
  }
}
```

**K0 enforcement:** Only brf_attestor_001 can sign BRF receipts.

## Integration with Daily OS

**Workflow step:**
```bash
python3 oracle_town/jobs/brf_onepager.py \
  --insights artifacts/insights.json \
  --anomalies artifacts/anomalies.json \
  --output artifacts/brief.md \
  --one-bet artifacts/one_bet.txt \
  --receipt artifacts/brf_receipt.json
```

**Before TRI:** Brief locked in, ONE BET frozen for this run.

---

**Status:** Charter Active
**Last Updated:** 2026-01-30
