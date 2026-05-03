# MAYOR_TASK_PACKET_V1 — build `oracle_town/skills/video/higgsfield_seedance`

**Status:** PROPOSAL-class typed task packet. Drafted for MAYOR admission.
NOT yet routed through `tools/helen_say.py` (kernel daemon must be up on
the executing node). This file is the input MAYOR consumes; admission
emits the sovereign receipt.

---

## Header

```yaml
task_id:        BUILD_HIGGSFIELD_SEEDANCE_SKILL_V1_2026-05-02
proposer:       claude-code (branch claude/setup-helen-os-node-b4uj8)
operator_auth:  2026-05-02 chat — "ask HELEN to craft a video … HIGGSFIELD seedance2 … TELEGRAM"
                + 2026-05-02 chat — "2" (route through MAYOR confirmed)
class:          PROPOSAL — sovereign-path skill build
target_layer:   Layer 4 (Skills + Tools)
target_path:    oracle_town/skills/video/higgsfield_seedance/
scope_clause:   skill is TEMPLE_ONLY-tagged at runtime (cloud egress not
                permitted from sovereign chat surfaces)
prior_refs:
  - HAL_INSPIRATION_QUEUE.md ITEM-010 (Higgsfield Seedance2 gap analysis)
  - STORYBOARD_V1_HELEN_MV_60S.md (consumer of this skill)
  - oracle_town/skills/video/helen-director/SKILL.md (parent integrator)
  - oracle_town/skills/video/library/refs/canonical/ (asset source)
chronos_check:
  - cross-ref CLAUDE.md "Skills + Tools" — slot exists, no name collision
  - cross-ref existing Seedance candidate runner — DO NOT duplicate; this
    skill wraps Higgsfield's API specifically, not raw ByteDance Seedance
  - cross-ref `tools/helen_telegram.py` — delivery channel, no mutation
```

---

## Forbidden paths (do not write)

- `helen_os/governance/**`
- `helen_os/schemas/**`
- `oracle_town/kernel/**`
- `town/ledger_v1.ndjson`
- `mayor_*.json`
- `GOVERNANCE/CLOSURES/**`
- `GOVERNANCE/TRANCHE_RECEIPTS/**`
- Any constitutional file (`KERNEL_V2.md`, `SOUL.md`, `HELEN.md`, `KERNEL_K_TAU_RULE.md`)
- Existing sealed proposals
- `oracle_town/skills/video/helen-director/**` (parent — only HOOK into it,
  do not modify)

---

## Allowed paths (writes scoped here only)

- `oracle_town/skills/video/higgsfield_seedance/SKILL.md` (NEW)
- `oracle_town/skills/video/higgsfield_seedance/__init__.py` (NEW)
- `oracle_town/skills/video/higgsfield_seedance/client.py` (NEW)
- `oracle_town/skills/video/higgsfield_seedance/receipts.py` (NEW)
- `oracle_town/skills/video/higgsfield_seedance/tests/test_smoke.py` (NEW)
- One hook-line in helen-director's render-backend registry — NOT a refactor

---

## Skill shape (deliverable)

```
oracle_town/skills/video/higgsfield_seedance/
├── SKILL.md           # declaration: scope=TEMPLE_ONLY, tags=[cloud_egress, video_gen]
├── __init__.py
├── client.py          # def render_shot(ref_image, prompt, duration_s, seed) -> dict
│                      #   returns: {url, mp4_sha256, request_hash, response_meta}
├── receipts.py        # HIGGSFIELD_CALL_RECEIPT_V1 emitter
│                      #   writes to: temple/subsandbox/renders/<task_id>/
└── tests/
    └── test_smoke.py  # 1-shot 5s smoke test, requires HIGGSFIELD_API_KEY env
```

Receipt schema (`HIGGSFIELD_CALL_RECEIPT_V1`):
```json
{
  "schema": "HIGGSFIELD_CALL_RECEIPT_V1",
  "task_id": "<storyboard task_id>",
  "shot_n": 1,
  "ref_image_sha256": "...",
  "prompt": "...",
  "prompt_hash": "...",
  "seed": 2026050201,
  "duration_s": 4,
  "returned_url": "...",
  "mp4_sha256": "...",
  "timestamp_utc": "...",
  "scope": "TEMPLE_SUBSANDBOX",
  "sovereign_admitted": false
}
```

---

## Acceptance criteria

1. Skill imports cleanly (`from oracle_town.skills.video.higgsfield_seedance import client`)
2. `client.render_shot()` emits `HIGGSFIELD_CALL_RECEIPT_V1` for every call
3. Receipts land in `temple/subsandbox/renders/<task_id>/` only — NEVER in
   `town/ledger_v1.ndjson`
4. `tests/test_smoke.py` passes with `HIGGSFIELD_API_KEY` set; skipped otherwise
5. `make test` (helen_os/tests/) still green
6. `bash tools/kernel_guard.sh` clean (no sovereign-ledger writes)
7. K-tau lint clean for the new skill files
8. Skill is tagged `TEMPLE_ONLY` in its SKILL.md frontmatter; `helen_dialog`
   and other sovereign chat surfaces MUST NOT route to it

---

## Required tests

- `pytest oracle_town/skills/video/higgsfield_seedance/tests/ -v` → green
- `make test` → green (no regression in helen_os/tests/)
- `python scripts/helen_k_tau_lint.py` → no new findings on the skill files
- `bash tools/kernel_guard.sh` → no sovereign writes
- LEGORACLE replay gate → unchanged (skill is non-sovereign, replay-irrelevant)

---

## Required receipts (admission produces these)

1. `MAYOR_ADMISSION_RECEIPT_V1` — MAYOR's accept/reject of this packet
2. `SKILL_DECLARATION_RECEIPT_V1` — emitted on first SKILL.md commit
3. `K_TAU_LINT_RECEIPT` — emitted by lint pass on the new files
4. `SMOKE_TEST_RECEIPT` — emitted on first green test run

---

## Sovereignty positioning (locked sentence)

> The skill is hands. HELEN governance remains the law.
> Higgsfield is cloud egress permitted ONLY from TEMPLE/subsandbox.
> No sovereign chat surface may route to this skill.

---

## Hand-off — operator invocation

On the MRED node with kernel daemon up:

```bash
cd ~/helen-conquest
source .venv/bin/activate

# 1. Ensure kernel daemon is running
.venv/bin/python oracle_town/kernel/kernel_daemon.py &
sleep 2
ls -la ~/.openclaw/oracle_town.sock   # confirm socket exists

# 2. Route this packet through MAYOR via the canonical writer
.venv/bin/python tools/helen_say.py \
  "PROPOSAL: build oracle_town/skills/video/higgsfield_seedance per MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md (TEMPLE_ONLY, cloud-egress, consumer of STORYBOARD_V1_HELEN_MV_60S)" \
  --op fetch

# 3. Read the HAL verdict.
#    - If verdict=PASS: MAYOR has admitted; build proceeds in a new branch
#      that writes oracle_town/skills/video/higgsfield_seedance/.
#    - If verdict=BLOCK: read reasons_codes / required_fixes, fix, re-route.

# 4. Verify the admission landed
tail -2 town/ledger_v1.ndjson
bash tools/kernel_guard.sh
```

---

## What MAYOR will check (anticipated)

- Schema compliance of this packet against MAYOR_TASK_PACKET_V1 (additionalProperties: false)
- Forbidden-paths list completeness
- Acceptance criteria measurable
- Receipt schemas exist or are declared as new (`HIGGSFIELD_CALL_RECEIPT_V1`
  is new — may need schema registry entry first; if so, MAYOR will BLOCK
  with `SCHEMA_NOT_REGISTERED` and the fix is to declare the schema in
  `helen_os/schemas/` via a separate sovereign task packet)
- CHRONOS overlap with existing Seedance candidate runner
- Operator authorization present (it is — chat 2026-05-02 ×2)

---

## Risk register

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| MAYOR BLOCKs on missing `HIGGSFIELD_CALL_RECEIPT_V1` schema | high | Issue a precursor task packet to register the schema first |
| Operator invokes from sovereign chat surface accidentally | medium | TEMPLE_ONLY tag + hard guard in helen-director's router |
| Higgsfield API rate-limit or auth fail mid-render | medium | client.py implements retry with capped backoff; partial-render receipts emit per-shot |
| Cloud egress blocked by network policy | low | client.py probes connectivity in test_smoke.py first |
| Kernel daemon down at invocation | high (current) | Operator boots daemon before `helen_say.py` |

---

## Status

QUEUED for MAYOR admission.
NOT yet routed (kernel daemon down on this Claude Code node;
operator must invoke from MRED with daemon up).

**Drafted:** 2026-05-02
