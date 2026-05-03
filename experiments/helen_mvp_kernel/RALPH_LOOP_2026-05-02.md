# RALPH_LOOP_2026-05-02 — 10-epoch HAL-piloted run

**Status:** OPEN. Non-sovereign. Operator-authorized 2026-05-02:
"let HAL decide for 10 epochs in full RALPH mode, I trust him."

## Constitutional bounds (per HAL_INSPIRATION_QUEUE.md ITEM-001)

```
Goal loop may PROPOSE.
Judge may CONTINUE.
Reducer still DECIDES.
Ledger still requires RECEIPTS.

/goal ≠ authority
/goal = persistence of intention
```

- All work scoped to `experiments/helen_mvp_kernel/`
- TEMPLE/subsandbox tagged where applicable
- No writes to forbidden paths (kernel, governance, ledger, helen-director parent, root oracle_town/skills)
- No sovereign admission attempts (kernel daemon down)
- Each epoch emits a 7-field PULL-mode receipt
- Halt on: forbidden-path attempt, epoch budget hit, operator interrupt, sovereign-admission boundary reached

## Goal

Advance the higgsfield video-render pipeline to a runnable DRY_RUN end-to-end
stub, all within `experiments/helen_mvp_kernel/` TEMPLE/subsandbox scope, so
that when the kernel daemon comes up and the operator authorizes, the actual
cloud render is one switch away.

## Epoch plan (HAL-chosen)

| # | Goal | Output artifact |
|---|------|-----------------|
| 1 | Open this loop log | `RALPH_LOOP_2026-05-02.md` |
| 2 | Draft `HIGGSFIELD_CALL_RECEIPT_V1` schema | `schemas/higgsfield_call_receipt_v1.json` |
| 3 | Draft MAYOR precursor packet for schema registration | `MAYOR_TASK_PACKET_HIGGSFIELD_SCHEMA.md` |
| 4 | Scaffold subsandbox skill skeleton | `higgsfield_seedance/` |
| 5 | Build offline-mock `client.py` | `higgsfield_seedance/client.py` |
| 6 | Build receipts emitter | `higgsfield_seedance/receipts.py` |
| 7 | Build smoke test (offline) | `higgsfield_seedance/tests/test_smoke.py` |
| 8 | Run smoke test, capture receipt | epoch receipt + test output |
| 9 | Build music-gen stub (silence fallback) | `higgsfield_seedance/music_stub.py` |
| 10 | Build DRY_RUN orchestrator | `higgsfield_seedance/dry_run.py` |

## Receipt template (per epoch, 7 fields, AUTORESEARCH PULL-mode discipline)

```yaml
epoch:               <n>
carry_forward_state: <what prior epochs left in place>
hypothesis:          <what this epoch tests/builds>
experiment:          <what was actually run/written>
metric:              <how success is measured>
failure_mode:        <what would have caused halt>
keep_reject_rule:    <criterion for keeping the artifact>
upgrade_path:        <next-epoch consequence>
```

## HAL judge protocol

After each epoch, HAL judges:
- `CONTINUE` (keep going)
- `DONE` (goal satisfied, halt early)
- `BLOCK` (forbidden-path or sovereign boundary; halt + report to operator)

Judge fails OPEN per ITEM-001 invariant: ambiguity → CONTINUE.

## Epoch ledger

Each epoch's receipt is appended below. This file IS the loop's
non-sovereign receipt artifact.

---

## Epoch receipts

### Epoch 1 — open loop log

```yaml
epoch:               1
carry_forward_state: branch claude/setup-helen-os-node-b4uj8 at HEAD ce881e1
                     + MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md staged
                     + STORYBOARD_V1_HELEN_MV_60S.md staged
hypothesis:          a typed loop log artifact is a sufficient non-sovereign
                     surface for HAL to record 10 epochs without touching
                     the sovereign ledger
experiment:          wrote RALPH_LOOP_2026-05-02.md with goal, bounds, plan,
                     receipt template, and judge protocol
metric:              file exists, valid markdown, no forbidden-path writes
failure_mode:        write to oracle_town/, town/, helen_os/governance/,
                     kernel/, or any sealed proposal would have halted
keep_reject_rule:    KEEP if file in experiments/helen_mvp_kernel/ and
                     operator can read it via git pull
upgrade_path:        epoch 2 drafts the schema this loop will need
hal_verdict:         CONTINUE
```

### Epoch 2 — draft HIGGSFIELD_CALL_RECEIPT_V1 schema

```yaml
epoch:               2
carry_forward_state: epoch 1 left RALPH_LOOP_2026-05-02.md as the loop's
                     non-sovereign receipt surface
hypothesis:          a draft JSON Schema in experiments/helen_mvp_kernel/schemas/
                     can specify the receipt shape without touching
                     helen_os/schemas/ (sovereign), unblocking later epochs
experiment:          wrote schemas/higgsfield_call_receipt_v1.json with 13
                     required fields + 2 optional (mode, error), additional-
                     Properties: false, scope locked to TEMPLE_SUBSANDBOX,
                     sovereign_admitted locked false
metric:              valid JSON, draft 2020-12 compliant, all field types
                     specified, no fields outside the receipt's actual scope
failure_mode:        write to helen_os/schemas/ would have been a sovereign
                     mutation — staying in experiments/.../schemas/ avoids it
keep_reject_rule:    KEEP if the schema can be referenced by epoch 3's MAYOR
                     packet as the precursor-registration target
upgrade_path:        epoch 3 drafts the MAYOR packet that asks to register
                     this schema in helen_os/schemas/ via a sovereign route
hal_verdict:         CONTINUE
```

---

### Epoch 3 — draft MAYOR precursor packet for schema registration

```yaml
epoch:               3
carry_forward_state: epoch 2 left a JSON Schema draft at
                     experiments/.../schemas/higgsfield_call_receipt_v1.json
hypothesis:          MAYOR will BLOCK the skill-build packet on
                     SCHEMA_NOT_REGISTERED unless the receipt class is
                     pre-admitted; a precursor packet resolves that
                     block in advance
experiment:          wrote MAYOR_TASK_PACKET_HIGGSFIELD_SCHEMA.md targeting
                     two narrow writes (helen_os/schemas/<file>.json and
                     +1 line in helen_os/governance/schema_registry.py),
                     with 8 acceptance criteria and 4 receipt types
metric:              packet has all MAYOR_TASK_PACKET_V1 required fields,
                     forbidden_paths complete, acceptance criteria
                     measurable, hand-off command runnable
failure_mode:        proposing direct edits to helen_os/governance/ from
                     this branch would have tripped the firewall — packet
                     instead asks MAYOR to authorize, never edits directly
keep_reject_rule:    KEEP if operator can route via helen_say.py without
                     edits to the packet
upgrade_path:        epoch 4 begins building the actual skill code in
                     experiments/.../higgsfield_seedance/ (subsandbox,
                     not in oracle_town/) — no further sovereign-path
                     authorization needed for that work
hal_verdict:         CONTINUE
```

---

### Epoch 4 — scaffold subsandbox skill skeleton

```yaml
epoch:               4
carry_forward_state: epoch 3 left a typed precursor packet pending MAYOR
hypothesis:          a subsandbox scaffold under experiments/.../higgsfield_seedance/
                     can host the skill code without touching oracle_town/
                     (which requires sovereign admission)
experiment:          created __init__.py + SKILL.md + tests/__init__.py
metric:              package importable from experiments/.../higgsfield_seedance,
                     SKILL.md declares scope=TEMPLE_SUBSANDBOX explicitly,
                     no writes outside experiments/
failure_mode:        a write into oracle_town/skills/video/ would have
                     required MAYOR — staying in experiments/ avoids it
keep_reject_rule:    KEEP if subsequent epochs (5,6,7) can build on top
                     without modifying constitutional paths
upgrade_path:        epoch 5 fills client.py
hal_verdict:         CONTINUE
```

---

### Epoch 5 — build offline-mock client.py

```yaml
epoch:               5
carry_forward_state: skill skeleton present
hypothesis:          a client with both DRY_RUN (offline) and LIVE branches
                     can be tested without network and without MAYOR-admission;
                     LIVE branch returns SKILL_NOT_ADMITTED until promotion
experiment:          wrote client.py with render_shot(), DRY_RUN fully
                     deterministic, LIVE returns NO_API_KEY or SKILL_NOT_ADMITTED
                     as appropriate; ref_image hashing falls back gracefully
                     for missing files in DRY_RUN
metric:              function returns a dict matching HIGGSFIELD_CALL_RECEIPT_V1
                     fields, deterministic given same inputs
failure_mode:        accidentally hitting the network in DRY_RUN — guarded
                     by branch separation
keep_reject_rule:    KEEP if smoke test (E7) confirms determinism
upgrade_path:        epoch 6 wires receipt emission + validation
hal_verdict:         CONTINUE
```

---

### Epoch 6 — build receipts emitter

```yaml
epoch:               6
carry_forward_state: client emits receipt-shaped dicts
hypothesis:          a receipts module can validate against the JSON Schema
                     draft AND refuse sovereign writes via FORBIDDEN_TARGETS,
                     keeping all output in temple/subsandbox/renders/
experiment:          wrote receipts.py with validate_receipt() and
                     emit_receipt(); jsonschema is optional (manual checks
                     fallback); SovereignWriteRefused exception guards the
                     boundary
metric:              writes only under temple/subsandbox/renders/<task_id>/;
                     locks enforced (scope, sovereign_admitted)
failure_mode:        path-resolution attack writing into town/ledger_v1.ndjson —
                     guarded by FORBIDDEN_TARGETS + scope check
keep_reject_rule:    KEEP if smoke test confirms TEMPLE-only writes
upgrade_path:        epoch 7 builds the smoke test
hal_verdict:         CONTINUE
```

---

### Epoch 7 — build smoke test (offline mode)

```yaml
epoch:               7
carry_forward_state: client + receipts modules in place
hypothesis:          a stdlib-only smoke test can validate the full
                     non-sovereign behavior surface (DRY_RUN determinism,
                     locks, validation rejections, LIVE refusal paths)
experiment:          wrote tests/test_smoke.py with 7 test cases plus a
                     gated LIVE placeholder; tests use tmp_path + monkeypatch
                     so the repo state is never mutated
metric:              7 cases cover DRY_RUN happy path, determinism,
                     subsandbox-only emission, lock enforcement (×2),
                     LIVE NO_API_KEY, LIVE SKILL_NOT_ADMITTED
failure_mode:        a real network call slipping through LIVE — gated
                     behind explicit opt-in env vars
keep_reject_rule:    KEEP if all 7 cases pass under stdlib-only execution
upgrade_path:        epoch 8 actually runs the tests and emits a receipt
hal_verdict:         CONTINUE
```

---

### Epoch 8 — run smoke test, capture receipt

```yaml
epoch:               8
carry_forward_state: tests written but not yet executed
hypothesis:          all 7 smoke tests pass under stdlib-only Python on
                     this Claude Code node (pytest unavailable)
experiment:          executed test cases inline via python3 heredoc;
                     emitted SMOKE_TEST_RECEIPT_V0 to
                     temple/subsandbox/renders/SMOKE_E8/smoke_test_receipt.json
metric:              7/7 PASS, exit_code 0
failure_mode:        any FAIL would have halted the loop and reported up
keep_reject_rule:    KEEP — all assertions held
upgrade_path:        epoch 9 closes the music gap with silence fallback
hal_verdict:         CONTINUE
result:              7/7 PASS
```

---

### Epoch 9 — music-gen stub (silence fallback)

```yaml
epoch:               9
carry_forward_state: render path proven; music gap still open per ITEM-010
hypothesis:          a deterministic silence WAV via stdlib `wave` is
                     sufficient to unblock end-to-end orchestration without
                     introducing a cloud-music dependency
experiment:          wrote music_stub.py with write_silence_wav() and
                     music_for_storyboard(); produces 44.1 kHz mono 16-bit
                     PCM silence of arbitrary duration with stable SHA-256
metric:              60s output is exactly 5,292,044 bytes (60 * 44100 * 2
                     + 44 byte WAV header) — deterministic
failure_mode:        nondeterministic timestamp in WAV header — `wave` does
                     not emit one, so safe
keep_reject_rule:    KEEP — silence is honest about the gap; no fake
                     "music" pretending to be a real generation
upgrade_path:        epoch 10 ties everything to the actual storyboard
hal_verdict:         CONTINUE
```

---

### Epoch 10 — DRY_RUN orchestrator consuming STORYBOARD_V1

```yaml
epoch:               10
carry_forward_state: client, receipts, music stub, smoke-tested scaffold
hypothesis:          the existing STORYBOARD_V1_HELEN_MV_60S.md packet
                     can flow through render_shot + emit_receipt +
                     music_for_storyboard end-to-end in DRY_RUN, producing
                     a manifest that the operator can inspect to verify
                     what a LIVE run WOULD send
experiment:          wrote dry_run.py that parses STORYBOARD_V1, extracts
                     shot table via regex, builds per-shot prompts, calls
                     render_shot(mode=DRY_RUN) for each, emits receipts,
                     produces a 60s silence track, writes manifest.json
                     summarizing the run + listing the 5 prerequisites
                     for switching to LIVE
metric:              executed against the real packet:
                       - task_id: STORYBOARD_V1_HELEN_MV_60S_2026-05-02
                       - 12 shots parsed (matches camera sheet)
                       - 60.0s total (matches storyboard spec)
                       - seeds 2026050201..2026050212 (deterministic)
                       - 12 receipts in receipts.ndjson
                       - music silence wav 5,292,044 bytes
                       - manifest.json written
failure_mode:        regex parse drift if STORYBOARD_V1 format changes —
                     manageable; the parser raises on missing task_id
keep_reject_rule:    KEEP — goal satisfied: DRY_RUN end-to-end stub runs
upgrade_path:        when MAYOR admits both precursor packets and the
                     skill migrates to oracle_town/, switching mode=LIVE
                     in dry_run.py orchestrator wires the cloud render
hal_verdict:         DONE  (goal satisfied at epoch 10)
```

---

## Loop summary

```yaml
loop:           RALPH_LOOP_2026-05-02
epochs_used:    10 / 10
budget_status:  exact-fit (no halt-early, no overrun)
goal_status:    SATISFIED — DRY_RUN end-to-end stub built, smoke-tested,
                exercised against real STORYBOARD_V1 packet
artifacts:
  - experiments/helen_mvp_kernel/RALPH_LOOP_2026-05-02.md           (this file)
  - experiments/helen_mvp_kernel/schemas/higgsfield_call_receipt_v1.json
  - experiments/helen_mvp_kernel/MAYOR_TASK_PACKET_HIGGSFIELD_SCHEMA.md
  - experiments/helen_mvp_kernel/higgsfield_seedance/__init__.py
  - experiments/helen_mvp_kernel/higgsfield_seedance/SKILL.md
  - experiments/helen_mvp_kernel/higgsfield_seedance/client.py
  - experiments/helen_mvp_kernel/higgsfield_seedance/receipts.py
  - experiments/helen_mvp_kernel/higgsfield_seedance/tests/__init__.py
  - experiments/helen_mvp_kernel/higgsfield_seedance/tests/test_smoke.py
  - experiments/helen_mvp_kernel/higgsfield_seedance/music_stub.py
  - experiments/helen_mvp_kernel/higgsfield_seedance/dry_run.py
runtime_outputs (TEMPLE/subsandbox, NOT committed):
  - temple/subsandbox/renders/SMOKE_E8/smoke_test_receipt.json
  - temple/subsandbox/renders/STORYBOARD_V1_HELEN_MV_60S_2026-05-02/manifest.json
  - temple/subsandbox/renders/STORYBOARD_V1_HELEN_MV_60S_2026-05-02/receipts.ndjson
  - temple/subsandbox/renders/STORYBOARD_V1_HELEN_MV_60S_2026-05-02/music_*.wav
sovereign_writes:    0
forbidden_path_hits: 0
ledger_admissions:   0  (kernel daemon down on this node; admissions deferred to MRED)
hal_final_verdict:   DONE
```

## Boundary reached

The loop honored its constitutional bounds:

- HAL only PROPOSED. No sovereign decisions.
- Reducer was never invoked (kernel daemon down; admissions deferred).
- Ledger received zero entries from this loop.
- All 11 committed artifacts live under `experiments/helen_mvp_kernel/`.
- All 4 runtime outputs live under `temple/subsandbox/renders/`.
- Forbidden paths untouched.

## Next sovereign moves (operator-only, not in this loop's scope)

1. Boot kernel daemon on MRED.
2. Route `MAYOR_TASK_PACKET_HIGGSFIELD_SCHEMA.md` (precursor) via
   `tools/helen_say.py`.
3. Route `MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md` (main) via `tools/helen_say.py`.
4. After both PASS, migrate the subsandbox scaffold to
   `oracle_town/skills/video/higgsfield_seedance/`.
5. Set `HIGGSFIELD_API_KEY` + `TELEGRAM_BOT_TOKEN` + `GEMINI_API_KEY`.
6. Issue a LIVE STORYBOARD_V1 task packet.
7. helen-director + Higgsfield + Telegram bot deliver the 60s mp4.

## Closing line

> HAL proposed. Reducer waits. Ledger is silent.
> The skill exists in subsandbox, smoke-tested, ready.
> The boundary holds.
