# SKILL — higgsfield_seedance (subsandbox scaffold)

```yaml
skill_name:    higgsfield_seedance
version:       0.1.0-subsandbox
scope:         TEMPLE_SUBSANDBOX
sovereign:     false
admitted:      false
location:      experiments/helen_mvp_kernel/higgsfield_seedance/
target:        oracle_town/skills/video/higgsfield_seedance/  (after MAYOR admission)
backend:       Higgsfield Seedance2 (cloud)
egress:        cloud_egress
api_key_env:   HIGGSFIELD_API_KEY
receipt_class: HIGGSFIELD_CALL_RECEIPT_V1
```

## Purpose

Render per-shot mp4 clips via the Higgsfield Seedance2 cloud API. Consumed
by the helen-director Montage Engine to assemble multi-shot videos
(e.g. STORYBOARD_V1_HELEN_MV_60S).

## Constitutional positioning

- **Non-sovereign.** Only emits `HIGGSFIELD_CALL_RECEIPT_V1` to
  `temple/subsandbox/renders/<task_id>/`. NEVER writes to
  `town/ledger_v1.ndjson`.
- **TEMPLE_ONLY.** Sovereign chat surfaces (helen talk, helen chat,
  helen_dialog, helen_simple_ui, helen_telegram with constitutional
  context) MUST NOT route to this skill. Operator-issued TEMPLE renders
  only.
- **Cloud egress.** Each call leaves the local node. Operator authorizes
  by issuing a TEMPLE-scoped task packet that names this skill as the
  render backend.

## Public surface

```python
from higgsfield_seedance.client import render_shot
from higgsfield_seedance.receipts import emit_receipt
from higgsfield_seedance.dry_run import dry_run_storyboard
```

### `render_shot(ref_image, prompt, duration_s, seed, mode="LIVE") -> dict`

- Inputs: reference image path (canonical character ref), text prompt,
  clip duration, deterministic seed, `mode` ∈ {`LIVE`, `DRY_RUN`}.
- Output: dict matching `HIGGSFIELD_CALL_RECEIPT_V1`.
- DRY_RUN mode: no network call, returns receipt with empty
  `returned_url` and `mp4_sha256`, `mode: "DRY_RUN"`.
- LIVE mode: requires `HIGGSFIELD_API_KEY`, performs API call, downloads
  mp4, hashes it, returns full receipt.

### `emit_receipt(receipt_dict, task_id) -> Path`

- Validates against the schema draft at
  `experiments/helen_mvp_kernel/schemas/higgsfield_call_receipt_v1.json`.
- Writes JSON line to `temple/subsandbox/renders/<task_id>/receipts.ndjson`.
- Returns the path written.

### `dry_run_storyboard(packet_path) -> dict`

- Parses `STORYBOARD_V1_HELEN_MV_60S.md` (or any STORYBOARD_V1).
- For each shot, calls `render_shot(..., mode="DRY_RUN")`.
- Emits per-shot receipts.
- Returns a manifest dict summarizing what WOULD be sent if mode=LIVE.

## Promotion path (out of subsandbox)

1. MAYOR admits `MAYOR_TASK_PACKET_HIGGSFIELD_SCHEMA.md` (precursor)
   → schema lives in `helen_os/schemas/`
2. MAYOR admits `MAYOR_TASK_PACKET_HIGGSFIELD_SKILL.md` (main)
   → code migrates to `oracle_town/skills/video/higgsfield_seedance/`
3. helen-director registers this as a render backend
4. Operator runs LIVE renders via STORYBOARD_V1 packets

Until step 1 completes, this stays in `experiments/`.

## Tests

- `tests/test_smoke.py` — DRY_RUN smoke test (offline, no API key needed)
- LIVE tests gated by `HIGGSFIELD_API_KEY` presence; skipped otherwise

## What this skill does NOT do

- Generate music (gap — see `music_stub.py` for silence fallback)
- Generate voice (uses Zephyr/Gemini TTS via `oracle_town/skills/voice/`)
- Assemble shots into a final mp4 (helen-director Montage Engine)
- Deliver to Telegram (uses `tools/helen_telegram.py`)
- Admit anything to the sovereign ledger

## What this skill DOES do

- Per-shot text-to-video via Higgsfield's wrapped Seedance2
- Deterministic seeding for replay
- Receipt emission per call
- DRY_RUN orchestration of full storyboards offline
