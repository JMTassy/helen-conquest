# MAYOR_TASK_PACKET_V1 — register Phase 0 research receipt schemas

**Status:** PROPOSAL-class typed task packet.
**NOT SUBMITTED.**
**SOVEREIGN_ADMISSION_REQUIRED.**

Drafted as the precursor route for promoting the three Phase 0 research
receipt schemas from `experiments/helen_mvp_kernel/schemas/` (subsandbox
draft) into `helen_os/schemas/` (sovereign canonical). Held; not routed
through `tools/helen_say.py` until operator authorizes.

---

## Header

```yaml
task_id:        REGISTER_PHASE0_RESEARCH_SCHEMAS_V1_2026-05-02
proposer:       claude-code (branch claude/setup-helen-os-node-b4uj8)
operator_auth:  2026-05-02 — RESEARCH_RALPH_PHASE0 verdict (CONTINUE)
                Note: this verdict authorizes the Ralph loop only.
                Sovereign promotion of these schemas requires a SEPARATE
                explicit operator authorization before submission.
class:          PROPOSAL — sovereign-path schema registration
target_layer:   Layer 1 (Constitutional Membrane) — schema registry
target_paths:
  - helen_os/schemas/h_n_spectral_receipt_v1.json
  - helen_os/schemas/phi_sde_trace_receipt_v1.json
  - helen_os/schemas/research_run_receipt_v1.json
  - helen_os/governance/schema_registry.py  (+3 lines, registry entries)
draft_sources:
  - experiments/helen_mvp_kernel/schemas/h_n_spectral_receipt_v1.json
  - experiments/helen_mvp_kernel/schemas/phi_sde_trace_receipt_v1.json
  - experiments/helen_mvp_kernel/schemas/research_run_receipt_v1.json
prior_refs:
  - RALPH_LOOP_2026-05-02_PHASE0.md (this loop)
  - oracle_town/skills/video/math_to_face/SKILL.md §6 (Phase 0-9 roadmap)
  - HAL_INSPIRATION_QUEUE.md ITEM-003 (Operating Directive — TASK PACKET LAW)
chronos_check:
  - cross-ref helen_os/governance/schema_registry.py for naming collisions
  - cross-ref helen_os/schemas/ for similar receipt classes
  - confirm RESEARCH_SUBSANDBOX scope tag is honored by validators
```

---

## Forbidden paths (do not write at admission time)

- `town/ledger_v1.ndjson` (writes only via tools/ndjson_writer.py)
- `helen_os/render/` (target of Phase 1+, not Phase 0)
- `oracle_town/kernel/` (sovereign firewall)
- All paths from CLAUDE.md off-limits except the four allowed targets above

---

## Allowed writes (admission scope)

1. Three NEW schema files in `helen_os/schemas/` (copies of drafts with `$id`
   rewritten to point at the canonical path)
2. Three new entries in `helen_os/governance/schema_registry.py`. Single
   append; no other modification.

---

## Schema content

Each canonical file is a copy of its `experiments/helen_mvp_kernel/schemas/`
draft with two changes:

1. `$id`: rewrite from
   `experiments/helen_mvp_kernel/schemas/<name>.json` →
   `helen_os/schemas/<name>.json`
2. Description: drop "Proposal-class draft pending MAYOR admission" sentence

All locks preserved unchanged:
- `additionalProperties: false`
- `scope` enum locked to `["RESEARCH_SUBSANDBOX"]`
- `sovereign_admitted` const `false`
- `decimal_precision` const `12`

---

## Acceptance criteria

1. Three schema files exist in `helen_os/schemas/` and validate as
   draft-2020-12
2. `helen_os/governance/schema_registry.py` registers all three; module
   imports cleanly
3. `helen_os/governance/schema_index_audit.py` finds 100% indexed status
   maintained (count goes from N to N+3)
4. `make test` — full helen_os/tests/ green (no regression)
5. `python scripts/helen_k_tau_lint.py` — no new findings on the new files
6. `bash tools/kernel_guard.sh` — clean (no direct ledger writes)
7. Negative validation tests pass: a receipt with `sovereign_admitted: true`
   is rejected; a receipt with `scope: "TEMPLE_SUBSANDBOX"` is rejected
   (research scope must be exclusive)

---

## Required tests

- `pytest helen_os/tests/ -q` → green
- `python helen_os/governance/schema_index_audit.py` → +3 indexed
- Validation smoke (positive): load each schema, validate a sample receipt
  produced by `phase0_runner.py`, expect PASS
- Validation smoke (negative): each schema rejects mutated receipts (lock
  violations)

---

## Required receipts

1. `MAYOR_ADMISSION_RECEIPT_V1` — admit/reject of this packet
2. `SCHEMA_REGISTRY_DELTA_RECEIPT_V1` — records the +3 schema delta
3. `K_TAU_LINT_RECEIPT` — clean lint
4. `SCHEMA_VALIDATION_SMOKE_RECEIPT` — positive + negative tests pass

---

## Sovereignty positioning

These schemas describe **non-sovereign** receipt classes (RESEARCH_SUBSANDBOX
scope, sovereign_admitted const false). Registration itself is a sovereign
act (touches `helen_os/schemas/` and `helen_os/governance/`), but the
receipts the schemas describe never enter `town/ledger_v1.ndjson`.

The point of registration is the same as the Higgsfield precursor (ITEM-010):
the constitutional membrane KNOWS about the receipt class, so it can REJECT
any attempt to admit a `RESEARCH_*_RECEIPT` to the sovereign ledger. Without
registration, the membrane has no rule to enforce.

> Schema registered. Sovereign membrane sees it.
> Receipts remain RESEARCH_SUBSANDBOX-bound by their own lock.
> The membrane refuses; the membrane does not generate.

---

## Hand-off — operator invocation (when authorized)

On a node with kernel daemon up:

```bash
cd ~/helen-conquest
git pull
source .venv/bin/activate

# Boot kernel daemon
.venv/bin/python oracle_town/kernel/kernel_daemon.py &
sleep 2

# Route this packet through MAYOR
.venv/bin/python tools/helen_say.py \
  "PROPOSAL: register H_N_SPECTRAL_RECEIPT_V1 + PHI_SDE_TRACE_RECEIPT_V1 + RESEARCH_RUN_RECEIPT_V1 in helen_os/schemas/ per MAYOR_TASK_PACKET_PHASE0_SCHEMAS.md. Drafts at experiments/helen_mvp_kernel/schemas/. PRECURSOR to math_to_face Phase 1+ promotion." \
  --op fetch

tail -2 town/ledger_v1.ndjson
```

If MAYOR PASSes: a follow-on session executes the writes.
If MAYOR BLOCKs: read reasons, fix, re-route.

---

## Status

```
NOT SUBMITTED
SOVEREIGN_ADMISSION_REQUIRED
```

This packet is held in subsandbox until the operator explicitly authorizes
submission. The Phase 0 Research Ralph loop does NOT require this packet
to PASS — Phase 0 emits subsandbox-only receipts under draft schemas. This
packet exists only to unblock Phase 1+ promotion.

**Drafted:** 2026-05-02 (Ralph Phase 0 epoch 3)
