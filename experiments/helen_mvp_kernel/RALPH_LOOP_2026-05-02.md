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

(more epochs appended below as they execute)
