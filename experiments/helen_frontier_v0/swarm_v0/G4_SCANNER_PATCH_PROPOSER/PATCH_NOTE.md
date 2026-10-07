---
schema: GOBLIN_PATCH_NOTE_V0
goblin: G4_SCANNER_PATCH_PROPOSER
authority: false
sovereign: false
canon: false
ledger_effect: none
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
applied: no
git_stage: no
git_commit: no
---

# G4 — structural same-path marking for the autoresearch scanner

🔵 OBSERVED: patch written and checked (`git apply --check` passes). NOT applied. Operator decision required.

## What changes

Target: `temple/autoresearch/autoresearch_scanner.py` (not touched by G4).

- Three helpers added above `write_packet`: `_packet_source_path`, `_find_same_path_packet`, `_mark_structural_duplicate`.
- One call added in `write_packet`, after `_assert_outbox_only` and before the write.
- Diff: +41 / -0 lines. Patch file: `scanner_structural_dedup.patch`.

When a new packet's source path (the single path in `source_refs`, `path:line` form) matches a packet already in the outbox, the new packet gets two extra fields:

- `"duplicate_of": "<existing packet_id>"`
- `"duplicate_check": "structural_same_path"`

The packet is still written. Nothing is rejected or skipped. The earlier packet is never edited.

## Why

The 2026-10-07 dedup probe (`receipts/DEDUP_PROBE_REVIEW_2026_10_07.md`) found 26 scanner packets on 26 distinct paths. Lexical similarity between them (0.75 to 0.78) comes from the shared template, not from duplication. The scanner has no same-path check, so a real same-path twin (a file rescanned after its findings change) would be written silently. This patch marks such twins at write time.

## Behaviour (covered by `test_structural_dedup.py`, 8/8 pass)

| Case | Result |
|---|---|
| Same path, second packet has different findings | second marked `duplicate_of` first |
| Different paths, same text | neither marked |
| Outbox has an unparseable JSON file | packet written, no mark, no exception |
| Outbox listing raises | packet written, no mark, no exception |
| Outbox directory does not exist yet | packet written, no mark |
| Same path, identical `packet_id` (rescan overwrites itself) | not marked (not a new twin) |
| End-to-end `run()`, second scan of a changed file | second marked |
| End-to-end `run()` with a corrupt outbox file | completes, packets unmarked |

## What is NOT changed

- `packet_id`, `summary`, `build_packet`, `scan_file`, the crossing rules, and the dry-run output are unchanged.
- Required packet fields and `validate_packet` / `autoresearch_policy.py` are untouched. The validator has no unknown-key rejection (checked by reading `validate_packet`), so the two new optional fields pass validation.
- The default `repo_root` in `run()` is unchanged.
- No existing outbox file is edited. A read-only check over the current 117 files found 0 same-path groups among the 26 scanner packets, so applying the patch marks nothing retroactively.
- No ledger, kernel, sovereign, or `temple/` file is written.

## How to apply (operator action)

```bash
cd /home/user/helen-conquest
git apply --check experiments/helen_frontier_v0/swarm_v0/G4_SCANNER_PATCH_PROPOSER/scanner_structural_dedup.patch
# review, then, only on operator go:
git apply experiments/helen_frontier_v0/swarm_v0/G4_SCANNER_PATCH_PROPOSER/scanner_structural_dedup.patch
.venv/bin/pytest tests/test_scanner_crossing.py -q
```

`test_structural_dedup.py` imports the COPY in this directory, not the real module. After applying, the operator may repoint its import at `temple/autoresearch/autoresearch_scanner.py` and move it into `tests/`. That is an operator decision and was not done here.

## Risks and open points

1. **Legacy matches.** The key is the source path for any outbox packet, not only scanner packets. The current outbox has 5 same-path groups among hand-written legacy packets, for example `helen_os/autonomy/self_improve_loop_v1.py` (5 packets) and `apps/helen-surface/cockpit_v4.html`. A new scanner packet on one of those paths would be marked as a twin of the first match. This is informational, but the operator may prefer to restrict matching to scanner-origin packets. That needs a reliable origin marker, which the summary format does not provide.
2. **Format mismatch with the reference.** `dedup_probe.SCANNER_TEMPLATE` matches only the retired V1 summary (`Scanner findings in ... signals=[...]`). The current scanner emits V2 (`Boundary-crossing findings in ...`), which the regex does not match. This patch keys on `source_refs`, so it does not depend on the summary format.
3. **Race.** The check and the write are not under a lock. Two concurrent scanner runs can both miss the match and produce an unmarked twin. The fix would be an `fcntl.flock` as in `NDJSONWriter`. It was left out to keep the diff minimal.
4. **Opt-in consumers.** The mark is only useful if triage or the reducer reads `duplicate_of`. Nothing here changes how existing consumers treat twins.
5. **Dry-run.** Marks are applied only on the write path, so `--write`-less dry runs do not show them.
6. **Determinism.** Outbox files are read in sorted filename order and the first match is used, so the result is deterministic for a given outbox state.

## Verification run

- `git apply --check` from repo root: exit 0 (see `GOBLIN_RECEIPT_V0.json` and the final report).
- `test_structural_dedup.py`: 8 passed (`test_output.txt`).
- Existing `tests/test_scanner_crossing.py` run against the patched copy (temporary copy, since deleted): 7 passed.
