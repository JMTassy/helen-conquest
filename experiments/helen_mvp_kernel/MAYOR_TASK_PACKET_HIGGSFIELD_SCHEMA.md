# MAYOR_TASK_PACKET_V1 — register `HIGGSFIELD_CALL_RECEIPT_V1` schema

**Status:** PROPOSAL-class typed task packet. PRECURSOR to
`MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md` — registers the receipt schema
that the skill will emit. NOT yet routed (kernel daemon must be up).

This packet exists because MAYOR will likely BLOCK the skill-build packet
with `SCHEMA_NOT_REGISTERED` until the receipt class is admitted to
`helen_os/schemas/`. Resolving that block in advance.

---

## Header

```yaml
task_id:        REGISTER_HIGGSFIELD_CALL_RECEIPT_V1_SCHEMA_2026-05-02
proposer:       claude-code (branch claude/setup-helen-os-node-b4uj8)
operator_auth:  2026-05-02 chat — "let HAL decide for 10 epochs in full
                RALPH mode, I trust him" (epoch 3)
class:          PROPOSAL — sovereign-path schema registration
target_layer:   Layer 1 (Constitutional Membrane) — schema registry
target_path:    helen_os/schemas/higgsfield_call_receipt_v1.json
                +1 line in helen_os/governance/schema_registry.py
draft_source:   experiments/helen_mvp_kernel/schemas/higgsfield_call_receipt_v1.json
prior_refs:
  - HAL_INSPIRATION_QUEUE.md ITEM-010 (Higgsfield gap analysis)
  - MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md (downstream consumer)
  - STORYBOARD_V1_HELEN_MV_60S.md (originating storyboard)
  - RALPH_LOOP_2026-05-02.md epoch 2 (schema draft)
chronos_check:
  - cross-ref helen_os/governance/schema_registry.py — verify no name
    collision with existing receipt classes
  - cross-ref helen_os/schemas/ index — verify naming convention match
    (lowercase_v1.json)
  - cross-ref CLAUDE.md "Schema Authority" — canonical path is
    helen_os/governance/schema_registry.py → helen_os/schemas/
```

---

## Forbidden paths (do not write)

- All paths from CLAUDE.md off-limits list except the two allowed below
- Specifically: NO writes to ledger, kernel, governance code (only to
  the schema registry index entry and the schema file itself)
- NO modification of existing schemas
- NO modification of validators, ledger validator, LEGORACLE gate

---

## Allowed writes (admission scope)

1. `helen_os/schemas/higgsfield_call_receipt_v1.json` (NEW file, copy of
   draft from `experiments/.../schemas/`, with `$id` rewritten to point
   at the canonical path)
2. `helen_os/governance/schema_registry.py` — append ONE registry entry
   referencing the new file. No other modification.

---

## Schema content

Copy of `experiments/helen_mvp_kernel/schemas/higgsfield_call_receipt_v1.json`
with two changes for canonical placement:

1. `$id`: change from
   `experiments/helen_mvp_kernel/schemas/higgsfield_call_receipt_v1.json`
   to
   `helen_os/schemas/higgsfield_call_receipt_v1.json`
2. Description: drop the "Proposal-class draft staged in experiments/"
   sentence (it's no longer a draft after admission)

All other fields, types, constraints, and locks (`additionalProperties:
false`, `scope` enum locked to `TEMPLE_SUBSANDBOX`, `sovereign_admitted`
const `false`) carry over unchanged.

---

## Acceptance criteria

1. `helen_os/schemas/higgsfield_call_receipt_v1.json` exists and validates
   against draft-2020-12
2. `helen_os/governance/schema_registry.py` registers the new schema and
   imports/parses cleanly
3. `helen_os/governance/schema_index_audit.py` (dual-recognizer) finds
   100% indexed status maintained — no orphaned schemas
4. `make test` — full helen_os/tests/ green (no regression)
5. `python scripts/helen_k_tau_lint.py` — no new findings
6. `bash tools/kernel_guard.sh` — clean (no direct ledger writes)
7. `additionalProperties: false` preserved
8. Locks preserved: `scope` enum = `["TEMPLE_SUBSANDBOX"]`,
   `sovereign_admitted` const = `false`

---

## Required tests

- `pytest helen_os/tests/ -q` → green
- `python helen_os/governance/schema_index_audit.py` → 48/48 indexed
  (was 47, now 48)
- Validation smoke: load the schema, validate a sample receipt, expect PASS
- Negative test: try a receipt with `sovereign_admitted: true`, expect
  validation FAIL (the lock is enforced)

---

## Required receipts

1. `MAYOR_ADMISSION_RECEIPT_V1` — admit/reject of this packet
2. `SCHEMA_REGISTRY_DELTA_RECEIPT_V1` — records the +1 schema delta
3. `K_TAU_LINT_RECEIPT` — clean lint on the new file
4. `SCHEMA_VALIDATION_SMOKE_RECEIPT` — positive + negative tests pass

---

## Sovereignty positioning

The schema registers a TEMPLE-only receipt class. Registration itself is
a sovereign act (touches `helen_os/schemas/` and `helen_os/governance/`),
but the receipts the schema describes are non-sovereign and never enter
`town/ledger_v1.ndjson`.

This separation is the point: the constitutional membrane KNOWS about
the receipt class (via the registry), so it can REJECT any attempt to
write a `HIGGSFIELD_CALL_RECEIPT_V1` to the sovereign ledger. Without
registration, the membrane has no rule to enforce.

> Schema registered. Sovereign membrane sees it.
> Receipts remain TEMPLE-bound by their own lock.
> The membrane refuses; the membrane does not generate.

---

## Hand-off — operator invocation

On the MRED node with kernel daemon up:

```bash
cd ~/helen-conquest
git pull
source .venv/bin/activate

# Boot kernel daemon
.venv/bin/python oracle_town/kernel/kernel_daemon.py &
sleep 2

# Route precursor schema-registration packet through MAYOR
.venv/bin/python tools/helen_say.py \
  "PROPOSAL: register HIGGSFIELD_CALL_RECEIPT_V1 schema in helen_os/schemas/ per MAYOR_TASK_PACKET_HIGGSFIELD_SCHEMA.md. Draft at experiments/helen_mvp_kernel/schemas/higgsfield_call_receipt_v1.json. PRECURSOR to MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md." \
  --op fetch

# Read HAL verdict, tail ledger
tail -2 town/ledger_v1.ndjson
```

If MAYOR PASSes: a follow-on session executes the two writes (schema
file + registry entry) and verifies acceptance criteria.

If MAYOR BLOCKs: read reasons, fix, re-route.

---

## Status

QUEUED for MAYOR admission. PRECURSOR to skill-build packet.

**Drafted:** 2026-05-02 (Ralph epoch 3)
