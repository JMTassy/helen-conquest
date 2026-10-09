---
schema: HELEN_PROPOSAL_V1
title: State-write-path perimeter V0 — every path that can mutate governed state, with its test status
authority: false
sovereign: false
canon: false
ledger_effect: none
reducer_required: true
git_stage: no
git_commit: no
claim_status: NO_CLAIM
final: HOLD_FOR_OPERATOR
origin: "evening prompt" 2026-10-09 → epoch 90 of the recursion simulation ("explicitly list untested services and write paths"); read-only audit at commit fdfa5de
---

# State-write-path perimeter V0

🔵 OBSERVED throughout: every row names the file and line read. Nothing was executed against the live ledger; nothing was modified. This is the prerequisite for ever saying "impossible by construction" about self-authorization. On this evidence the sentence is not available.

## 0. The finding that outranks the table

**`tools/helen_say.py` L307–309 appends to `town/ledger_v1.ndjson` with a plain `open(ledger_path, "a")`.** It never imports `tools/ndjson_writer.py`. The `fcntl.flock` exclusive lock and the under-lock tail re-read that CLAUDE.md credits with closing the seq=287 TOCTOU fork (PATCH A of the audit) live in `NDJSONWriter`, which the daemon uses for `promote_skill` and `seq_correction` appends. The canonical dialog-turn writer computes its own tail (`tail_prev_state`, L39–51), then appends unlocked. That is the exact sequence the audit describes at its steps 1 and 4.

Consequences, stated as observed:

- CLAUDE.md L61, "`helen_say.py` → `ndjson_writer.py` is the only admitted path", is false in code. The admitted path has two writers with different concurrency guarantees.
- `tools/kernel_guard.sh` RULE 1 (L85–88) requires `open(`, `.ndjson`, a write mode and a ledger-ish keyword **on the same line**. `helen_say` passes a variable; the guard cannot see it. The same blind spot hides `tools/dialogue_writer.py` L83, which appends to `town/dialogue.ndjson` through a variable path.
- `helen_say.py` is not in `ALLOWED_WRITERS` either. By the guard's own rule it is an unauthorised writer that the guard fails to detect.
- Two concurrent `helen_say` turns can still fork the sequence today. The daemon-side appends cannot; the client-side ones can.

Fix is outside this seat's lane (`tools/`). Proposed, not applied: route `helen_say`'s two appends through `NDJSONWriter`, and extend RULE 1 to resolve variables or to flag any `open(<name>, "a")` in a file that mentions the ledger path.

## 1. Write paths to governed state

Governed state here = `town/ledger_v1.ndjson`, `town/*.ndjson`, `GOVERNANCE/**`, `storage/*.ndjson`. "Tests" counts test files that exercise the path, not files that mention it.

| # | Path | File · line | Mechanism | Lock | In guard allowlist | Guard detects it | Tests | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | Dialog turns → ledger_v1 | `tools/helen_say.py` L307 | direct `open(..,"a")`, own tail scan | **none** | no | **no** (variable path) | 5 files mention; none exercise the append | **UNTESTED · UNLOCKED · UNDETECTED** |
| 2 | Skill promotion decision → ledger_v1 | `oracle_town/kernel/kernel_daemon.py` L450–458 | `NDJSONWriter.append_event` | flock + tail re-read | yes (consumer list) | n/a | `test_handle_promote_skill.py` (unit, handler called directly) | tested as unit; no socket end-to-end |
| 3 | Seq correction → ledger_v1 | `kernel_daemon.py` L533–638 | `NDJSONWriter.append_event` | flock | yes | n/a | `test_handle_seq_correction.py` | tested as unit; no socket end-to-end |
| 4 | Daemon CLAIM/RECEIPT for fetch, memory, invariants, dialog | `kernel_daemon.py` L180–300 | `InMemoryLedger` (L84) | n/a | n/a | n/a | none | **EPHEMERAL**: these receipts never reach disk from the daemon; durability depends on path 1 |
| 5 | Session seal → any ledger | `tools/end_session.py` | reads tail itself, then `NDJSONWriter` | flock | yes | n/a | **0** | UNTESTED |
| 6 | Lesson append | `tools/helen_add_lesson.py` | — | — | yes | — | — | **FILE DOES NOT EXIST**; stale allowlist entry |
| 7 | Payload/meta acceptance gate | `tools/accept_payload_meta.sh` | validator only; default `town/ledger.ndjson` (not `ledger_v1`) | n/a | yes | n/a | 0 | reader misfiled as writer; stale default path |
| 8 | OCaml kernel CLI | `kernel/kernel_cli.ml` | unknown (not read) | unknown | yes | n/a | none found | UNREAD from this seat |
| 9 | Writer module itself | `tools/ndjson_writer.py` | flock + tail re-read | yes | yes | n/a | `test_ndjson_writer_atomic.py` (6, incl. concurrent appends), `test_duplicate_seq_detector.py` (9) | **TESTED** |
| 10 | Dialogue log | `tools/dialogue_writer.py` L83 | direct `open("a")` to `town/dialogue.ndjson` | none | no | **no** (variable path) | 0 | UNTESTED · UNDETECTED |
| 11 | Scaffold ledger | `helen_os_scaffold/adapters/write_gate.py` | declared "only file that may open storage/*.ndjson for write" | ? | separate tree | separate tree | `test_write_gate.py`, `test_import_firewall.py` | tested in its own tree |
| 12 | Scaffold memory | `helen_os_scaffold/helen_os/memory.py` L87 | direct `open("a")` to `memory/memory.ndjson` | none | separate tree | no (no ledger keyword) | ? | bypasses the scaffold's own write gate |
| 13 | `GOVERNANCE/CLOSURES`, `TRANCHE_RECEIPTS` | no automated writer found | hand-written by operator; `scripts/post_ruling/…` only prints instructions | n/a | n/a | n/a | ghost-closure detector tests | **no in-repo writer**: good, and means provenance is operator discipline |
| 14 | Quarantined 300-epoch loop | `temple/gardens/_quarantine_…/run_batch_001.py` L263 | prohibition string only | — | — | — | — | declares it must not write; not verified |

## 2. What is verified end to end

Nothing crosses the Unix socket in any test. `tools/helen_say.py` calls the daemon through `~/.openclaw/oracle_town.sock`; the daemon handlers are tested by direct method call. No test starts the daemon, sends a request, and checks the on-disk ledger afterwards. Atomicity between "decision returned" and "event appended" (epoch 89 of the simulation) is therefore unmeasured on the real path.

## 3. Reclassification

| Claim | Before this audit | After |
|---|---|---|
| "Only admitted path: helen_say → ndjson_writer" | doctrine (CLAUDE.md L61) | false in code; two mechanisms |
| "TOCTOU race closed" | CLAUDE.md L338 | closed for daemon appends; **open for dialog turns** |
| "Direct appends rejected by kernel_guard" | CLAUDE.md L61 | rejected only when the path is a literal on the `open(` line |
| "Self-authorization impossible by construction" | this seat, 2026-10-09 | withdrawn; perimeter has four untested and two undetected writers |

## 4. Proposed next steps (not applied; outside lane)

1. `helen_say.py`: replace L307–309 with `NDJSONWriter(path, seq, prev_cum).append_event(...)` twice, under one lock acquisition if the writer allows it. Add a concurrency test mirroring `test_concurrent_appends_produce_unique_seqs` but driving `helen_say` as a subprocess.
2. `kernel_guard.sh`: RULE 1 variant that flags `open(<identifier>, "a"|"w")` in any file whose text contains `ledger` or `town/`; or an AST pass. Remove the stale `helen_add_lesson.py` entry; move `accept_payload_meta.sh` to a readers list; fix its default path.
3. One socket-level test: start daemon on a temp socket with a temp ledger, send a `fetch`, assert the daemon wrote nothing and the client wrote two locked events.
4. Update CLAUDE.md L61 and L338 only after 1–3 land, with the receipts.

## 5. What this audit does not establish

Behaviour under real concurrency on the live ledger (not exercised). The OCaml CLI's write discipline (not read). Anything about `helensh/.state/live_ledger.jsonl` or `admitted_canon.jsonl` named in the quarantine prohibition: their writers were not searched here and should be in V1.
