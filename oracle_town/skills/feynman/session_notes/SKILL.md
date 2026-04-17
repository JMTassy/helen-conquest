---
name: feynman/session_notes
description: Narrative session notes — a human-readable diary of what happened in a HELEN session. Explicitly NON-LEDGER. Markdown only. Every claim it makes must cite a real ledger receipt by ID.
fused_from: feynman v0.2.20 / session-log (renamed and re-scoped)
helen_classification: NARRATIVE_ARTIFACT
helen_witness: R-20260416-0004 (chained)
---

# Session Notes (HELEN-fused, downgraded from session-log)

> **Important:** This is **not** a log. Not a ledger. Not a journal of record.
> The hash-chained record of truth is `town/ledger_v1.ndjson`.
> Session notes are *prose around* that record, never a substitute.

## Invocation

From repo root (`helen_os_v1/`):

```
python3 tools/helen_say.py "NOTES_REQUEST: <session_id>" --op fetch
```

`--op notes` is reserved but not yet wired. Forbidden ops: `--op log`, `--op journal`, `--op record` — these names are reserved for the hash-chained ledger and may not be used for narrative artifacts.

## HELEN conditions (from witness audit, 2026-04-16)

1. **No reserved words.** The strings `ledger`, `log`, `journal`, `record`, `receipt`, `attestation` may not appear in any output filename, frontmatter `name:`, or top-level heading.
2. **Cite or retract.** Any factual claim ("we shipped X", "HELEN refused Y") must include a parenthetical ledger receipt ID. Uncited claims are noise and must be cut.
3. **Termination is sacred.** Notes end with one of:
   - `SHIP: <what was shipped, with receipt IDs>`
   - `ABORT: <why, with receipt IDs>`

   HELEN.md Property 3 / Rule 5 admits only these two terminators. Open questions become their own claim (`open_question` op) with its own receipt — they are not a third terminator. No "we'll continue this later" prose. That pathology is what HELEN was built to refuse.

## Output

`artifacts/session_notes/<YYYY-MM-DD>__<session_id>.md` — markdown only, never JSON.

## Provenance

See `.provenance.md`.
