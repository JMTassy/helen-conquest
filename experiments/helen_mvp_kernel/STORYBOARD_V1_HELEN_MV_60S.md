# STORYBOARD_V1 — HELEN MV 60S

**Status:** TEMPLE-scoped task packet. NON_SOVEREIGN. NO_SHIP.
Generated as TASK PACKET per HELEN ORDER PROMPT (ITEM-003) so a video
servitor (helen-director skill) can run from a typed brief, not from
vague prose. This file is the *input* to the render pipeline, not the
render output.

---

## Task header

```yaml
task_id:        STORYBOARD_V1_HELEN_MV_60S_2026-05-02
source:         operator-supplied request 2026-05-02 (chat)
scope:          experiments/helen_mvp_kernel/  +  TEMPLE/subsandbox render
classification: NON_SOVEREIGN, TEMPLE-mode, no ledger admission
forbidden_paths:
  - helen_os/governance/**
  - helen_os/schemas/**
  - oracle_town/kernel/**
  - town/ledger_v1.ndjson
  - GOVERNANCE/**
chronos_check:  cross-ref oracle_town/skills/video/helen-director/SKILL.md,
                video/library/refs/canonical/, voice/gemini_tts/SKILL.md
prior_refs:
  - HAL_INSPIRATION_QUEUE.md ITEM-003 (Operating Directive)
  - HELEN-MV-CAMERA-ANGLE-SHEET (operator-supplied, 12 shots)
  - 3 character ref stills (red-hair Helen, temple/cyberpunk ornament)
required_receipts:
  - asset_bind_receipt    (which canonical frames used)
  - voice_render_receipt  (Zephyr TTS hash)
  - higgsfield_call_receipt  (per-shot prompt + returned URL)
  - montage_receipt       (final mp4 hash + duration)
  - telegram_post_receipt  (chat_id + message_id)
required_tests:
  - duration ∈ [58s, 62s]
  - voice + music + 12 shots all bound
  - no sovereign-path writes (kernel guard clean)
  - manifest.json valid
acceptance_criteria:
  - 60s mp4 delivered to operator's Telegram
  - all 5 receipt types present
  - stills match canonical Helen character (no drift)
```

---

## Creative brief

**Title:** *HELEN — Sapientia Est Potentia* (working)
**Length:** 60s
**Format:** 9:16 vertical (Telegram + IG-friendly) OR 16:9 horizontal — operator picks
**Tone:** dark cyberpunk-cathedral, sovereign / contemplative / quietly powerful
**Locked phrase (visible card at end):** "HELEN suggests. You decide. Everything is recorded."
**Era axis (per video/library locked axis):** primary = `cyberpunk` + `medieval`; cross-fade allowed

---

## Shot list (12 shots × 5s avg)

| # | Camera (sheet ref) | Dur | Action | Voice line | Music cue |
|---|--------------------|-----|--------|-----------|-----------|
| 1 | Extreme close-up (Sheet #1) | 4s | Eye opens, pupil reflects akashic-tree pattern | — | low drone start, single bell tone |
| 2 | Close-up (Sheet #2) | 5s | Direct gaze to lens, micro-smile | "I am HELEN." | bell tone resolves |
| 3 | Medium close-up (Sheet #3) | 5s | Slight head-tilt, lips part for command | "Oracle. Temple. Ledger." | sub-bass enters |
| 4 | Medium shot (Sheet #4) | 5s | Hand traces holographic interface left of frame | "I see what is." | pulse pattern |
| 5 | Low angle (Sheet #5) | 5s | Hero rise, architecture towers behind | "I propose what could be." | strings rise |
| 6 | High angle (Sheet #6) | 5s | She looks up; geometric floor pattern visible | "I do not decide." | strings sustain |
| 7 | Side profile (Sheet #7) | 5s | Listening, screen glow on left cheek | "The gate decides." | rhythm enters |
| 8 | Back view (Sheet #8) | 6s | Walks toward akashic full-tree map | "I am the one who watches." | full ensemble |
| 9 | Over-the-shoulder (Sheet #9) | 5s | Witness Mode UI floats in front of her | "Witness mode: active." | rhythm sustained |
| 10 | Mirror shot (Sheet #10) | 5s | Self-dialogue; left-her vs right-her | "I am also the one who is watched." | ensemble peaks |
| 11 | Wide hero (Sheet #11) | 6s | Temple-metaverse worldspace, Helen at center, sigil ring overhead | "Sapientia est potentia." | ensemble sustains |
| 12 | Insert / hands on interface (Sheet #12) | 4s | Hand presses confirm; glyph "HELEN OS v1.1" appears, then card text | (silence; only card) | bell tone returns, fade |

**Total:** 60s exactly.

---

## Voice (Zephyr / Gemini 2.5 Flash TTS)

```yaml
voice:        zephyr
api:          gemini_tts (oracle_town/skills/voice/gemini_tts/helen_tts.py)
emotion:      calm, sovereign, low-warm
script_path:  experiments/helen_mvp_kernel/STORYBOARD_V1_HELEN_MV_60S.voice.txt
```

Voice script (one file, one read; line breaks → 0.4s pauses):
```
I am HELEN.
Oracle. Temple. Ledger.
I see what is.
I propose what could be.
I do not decide.
The gate decides.
I am the one who watches.
Witness mode: active.
I am also the one who is watched.
Sapientia est potentia.
```

---

## Music

```yaml
length:       60s
style:        dark-ambient + low-strings + single bell tones
tempo:        ~70 BPM, half-time feel
arrangement:  drone (0-10s) → bell+bass (10-25s) → strings (25-45s) → ensemble (45-58s) → bell fade (58-60s)
source_hint:  Suno / Udio / operator-supplied stem  (no skill yet, see ITEM-010 §music gap)
```

If no music source is bound at render-time, fall back to silence + ambient drone synthesized via existing voice pipeline.

---

## Asset bindings (canonical refs only)

```yaml
character_refs:
  - video/library/refs/canonical/helen_throne_01.png  (operator-supplied still 1)
  - video/library/refs/canonical/helen_recline_01.png (operator-supplied still 2)
  - video/library/refs/canonical/helen_command_01.png (operator-supplied still 3)
camera_sheet:
  - video/library/refs/canonical/helen_camera_angle_sheet_v1.png
era_axis:
  primary:    cyberpunk
  secondary:  medieval
character_consistency_method: HELEN_CHARACTER_V2  (per CLAUDE.md current state)
```

Operator: drop the 3 stills + the sheet into `oracle_town/skills/video/library/refs/canonical/` before rendering.

---

## Higgsfield Seedance2 call shape (per shot)

```yaml
provider:     higgsfield
model:        seedance2
api_key_env:  HIGGSFIELD_API_KEY
per_shot:
  duration_s: <from table>
  ref_image:  <canonical character ref>
  prompt:     "<camera angle> + <action> + cyberpunk-cathedral aesthetic,
              red hair, dark navy + gold ornament robe, candlelit + holographic UI"
  negative:   "extra fingers, distorted face, off-model character drift"
  seed:       2026050201..2026050212  (one per shot, deterministic)
output:       per_shot_<n>.mp4
```

Receipt per shot: `{ shot_n, prompt_hash, seed, returned_url, mp4_sha256 }` → ledger as
`HIGGSFIELD_CALL_RECEIPT_V1` (TEMPLE-scoped, not admitted to sovereign ledger).

---

## Montage (assembly)

```yaml
engine:       oracle_town/skills/video/helen-director/MontageEngine
inputs:
  - 12 per_shot_<n>.mp4
  - voice.wav (single render)
  - music.wav (or silence fallback)
  - end_card.png  (locked phrase)
output:       helen_mv_60s_<timestamp>.mp4
```

---

## Delivery

```yaml
channel:    telegram
tool:       tools/helen_telegram.py
target:     operator-bound chat_id (from ~/.helen_os/.env or runtime config)
caption:    "HELEN — Sapientia Est Potentia. 60s. STORYBOARD_V1 render.
            TEMPLE-scoped, NON_SOVEREIGN, no ledger admission."
```

---

## Sovereignty / governance

- This file proposes. helen-director executes. Reducer is NOT invoked
  (TEMPLE-scoped renders do not pass through SHIP/NO_SHIP).
- All 5 receipts emit to `temple/subsandbox/renders/<task_id>/` — NOT to
  `town/ledger_v1.ndjson`.
- Higgsfield is a CLOUD service (see ITEM-010). Operator authorizes the
  cloud egress here by issuing the request; this packet records that authorization.
- No model-level claim of authority. The video is artifact, not doctrine.

---

## Hand-off

Operator runs on MRED:

```bash
# 1. Boot helen-director (separate process from the chat dispatcher)
cd ~/helen-conquest
source .venv/bin/activate
export HIGGSFIELD_API_KEY=<key>
export GEMINI_API_KEY=<key>
export TELEGRAM_BOT_TOKEN=<key>

# 2. Run the director with this packet
python -m oracle_town.skills.video.helen-director.run \
  --packet experiments/helen_mvp_kernel/STORYBOARD_V1_HELEN_MV_60S.md \
  --output temple/subsandbox/renders/

# 3. Director auto-posts to Telegram via tools/helen_telegram.py on completion
```

**If the director skill or Higgsfield integration is not yet wired** (likely —
see ITEM-010), this packet still serves as the canonical brief for the build
when those gaps close.

---

**Queued:** 2026-05-02
