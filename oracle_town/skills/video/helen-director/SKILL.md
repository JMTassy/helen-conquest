---
name: video/helen-director
description: Deterministic pipeline for producing HELEN-signature cinematic video — photoreal image-to-video with invisible anomaly discipline, seed continuity across shots, dual festival/TikTok output, and zero-credit post-production. Complements HELEN_VIDEO_PROMPT_V1.md (shot grammar) with the end-to-end production system.
helen_faculty: RENDER
helen_status: DOCTRINE (calibrated from 2026-04-19/20 UNRIPPLE session; not yet receipted as INVARIANT)
helen_prerequisite: HELEN_VIDEO_PROMPT_V1 (shot grammar), Higgsfield API credentials (HF_API_KEY + HF_API_SECRET), Telegram bot credentials
---

# HELEN Director — Video Production Skill

**Class**: Non-sovereign skill. No kernel authority. No ledger write without `helen_say.py`.

**Scope**: How to take one creative concept and produce an 8-shot festival cut + 9 TikTok derivatives + 3-minute music clip from a single render budget.

---

## 1. Core principle

HELEN is not visible. HELEN is detected through one violation of physical expectation per shot.

Every shot gets exactly **one impossible property**. Felt, not named. If a viewer can point and say "this is the message" → the shot failed.

Forbidden:
- visible text overlays spelling HELEN (unless explicitly operator-approved per-artifact)
- glow, bloom, lens flare, visible VFX register
- constellations spelling words
- symbolic effects where there should be physics
- multiple simultaneous anomalies (stacking reads as "AI glitch," not intelligence)

Required:
- photoreal baseline; documentary realism as default
- camera locked or slow forward dolly only (no pan/tilt/rotate/lateral)
- one impossible property, physical in nature (timing, causality, material, reflection)
- faces obscured or absent (AI morphs visible faces over 6s)

---

## 2. Pipeline (calibrated against real API behaviour)

```
[concept]
   → HELEN_VIDEO_PROMPT_V1 shot grammar (sibling doc)
   → Soul Standard text-to-image (generate 2–3 seed frames)
   → Higgsfield presigned upload (seed → CDN URL)
   → Seedance Pro image-to-video (6s, 9:16, per-shot anomaly prompt)
   → download .mp4
   → ffmpeg normalise 1080x1920 24fps yuv420p
   → ffmpeg concat 6–8 shots
   → audio (local synth OR operator-supplied song)
   → ffmpeg mux → festival cut
   → ffmpeg re-cut → TikTok derivatives (palindrome loops, captioned)
   → Telegram bot delivery
```

**Real endpoints (Higgsfield, verified 2026-04-19/20):**

| Task | Endpoint | Cost (6s, 9:16, 720p) |
|---|---|---|
| Text-to-image (seed) | `higgsfield-ai/soul/standard` | ~3 credits |
| Image-to-video (premium) | `bytedance/seedance/v1/pro/image-to-video` | ~10 credits |
| Image-to-video (budget) | `higgsfield-ai/dop/standard` | ~9 credits |
| Image-to-video (cinematic) | `kling-video/v2.1/pro/image-to-video` | ~15–25 credits |

**Auth pattern**: `Authorization: Key <HF_API_KEY>:<HF_API_SECRET>` + `User-Agent: higgsfield-client-py/1.0`.

**Base URL**: `https://platform.higgsfield.ai/`.

**Schema (I2V)**: `{image_url, prompt, duration}`. `duration` accepts 5 or 10 only (not arbitrary integers).

**Pre-signed upload**: `POST /files/generate-upload-url` with `{content_type: "image/png"}` returns `{public_url, upload_url}`. PUT bytes to `upload_url`, reference `public_url` in downstream calls. Upload is zero credits.

**Poll**: `GET <status_url>` every 10s. Terminal states: `completed`, `failed`, `canceled`, `nsfw`. Failed/NSFW refund credits.

---

## 3. Seed continuity strategy

**The unlock**: reuse ONE Soul seed for multiple Seedance Pro motion variants. This produces shot-to-shot continuity that makes the sequence read as one world rather than eight disconnected clips.

**Rule of 3**: one 8-shot teaser needs 3 seeds max:
- Seed A — wide establishing (shots 1, 2, 8)
- Seed B — close macro / alternate angle (shots 3, 4)
- Seed C — medium / secondary subject (shots 5, 6, 7)

Each seed drives 2–3 Seedance Pro renders with different motion prompts. Cost savings: 3 Soul × 3 credits = 9 credits vs 8 × 3 = 24 credits for per-shot seeds.

**Seed-prompt alignment** (critical failure mode discovered this session): if the seed is schematic/stylised (e.g., Pillow procedural) but the prompt demands photorealism, the I2V output is "ugly" (operator rated 1/10). The seed aesthetic must match what the prompt describes. If you want photoreal, generate via Soul. If you want stylised, accept a stylised prompt.

---

## 4. HELEN's five anomaly classes

Proven register from the UNRIPPLE session:

1. **Timing stall** — one ripple ring freezes briefly while others continue (Shot 3 / UNRIPPLE).
2. **Causal off-center** — ripples contract inward to a point that is NOT where the drop hit, by ~2–3 cm (Shot 4).
3. **Temporal lag** — reflection shows the same scene as reality but delayed by ~1 second (Shot 5 + Shot 6 bird reflection).
4. **Non-displacement** — object interacts with water/material, but material shows no lasting trace (Shot 7 bird drinks).
5. **Impossible presence** — one point exists in a reflection where it cannot exist in the real world (Shot 8 impossible star).

Every shot: pick exactly one class. Do not stack.

Rejected registers (tried and abandoned in-session):
- Constellation spelling letters (too literal, too nerdy)
- Calligraphy of "HELEN" in reflection (AI hallucinates text, breaks invisible-anomaly principle)
- Different-sky reflection with stars at dawn (reads as compositing, not physics)
- Glowing beak on bird drink (cheapens to VFX)

---

## 5. Dual-output structure

One shoot, two artifacts:

**Primary — festival cut**
- 48s, 8 shots concat, local-synth anomaly soundscape OR operator-supplied score
- No on-screen text
- Audience: AI film festival circuit (WAiFF, LifeArt, OMNI)
- File: `unripple_festival.mp4` (or analogue)

**Secondary — TikTok re-cuts** (zero new renders)
- 3 hero shots (typically shots 3, 5, 7) × 3 register types:
  - Type A — palindrome loop, no text (goal: rewatch)
  - Type B — palindrome + text trigger like "look again" (goal: comments)
  - Type C — palindrome + framing text like "real footage?" (goal: shares)
- 6–8s each, loop-locked via forward+reverse concat
- Text overlay via Pillow PNG (ffmpeg `drawtext` is unreliable across builds; use Pillow transparent PNG + ffmpeg `overlay` filter instead)

**Tertiary — 3-minute music clip** (zero new renders)
- 20-segment recomposition of same 8 shots (forward/reverse/slow 2x combinations)
- Scored against full ~3min of a HELEN-themed song
- Target output ≤50MB to clear Telegram bot upload limit (CRF 26, 2.4 Mbps ceiling)

---

## 6. Audio modes

Two modes, both zero-credit:

**Mode A — Anomaly soundscape** (local numpy synthesis):
- sparse detuned piano tones, irregular timing
- filtered white noise floor (single-pole lowpass)
- slow evolving pad with microtonal drift
- irregular low-frequency pulses
- subtle L/R phase shift (~8 sample delay) for subconscious stereo unease
- Variant B: delayed echo at key anomaly timestamp
- Variant C: single pure high tone at signature moment, no reverb
- No melody, no percussion, no cadence resolution
- Register: Jóhann Jóhannsson / Max Richter minimal

**Mode B — Operator song**:
- Use operator-supplied MP3 (e.g., Suno-composed HELEN anthem)
- Extract window via ffmpeg `afade=t=in:st=0:d=1.5,afade=t=out:st=<end-3>:d=3.0`
- Mux with `-shortest` so video + audio align

Mode A honours invisible-anomaly principle. Mode B carries narrative/vocal register. Both are valid. Produce both from same visuals and let the operator choose.

---

## 7. Budget calibration (measured 2026-04-19/20)

| Phase | Credits | Notes |
|---|---|---|
| 1 Soul seed (720p, 9:16) | ~3 | Text-to-image |
| 1 Seedance Pro I2V (6s, 9:16) | ~10 | Image-to-video premium |
| 1 DoP Standard I2V (6s, 9:16) | ~9 | Cheaper, lower quality |
| Full 8-shot teaser | ~90 | 3 seeds + 8 I2V |
| Full 8-shot with retry buffer | ~120 | 2–3 re-shoots included |
| Audio (local synth) | 0 | numpy + ffmpeg |
| ffmpeg concat + mux + TikTok cuts | 0 | Local |
| 3-min music clip (reuse footage) | 0 | 20-segment recomposition |

**Failed/NSFW requests are refunded automatically** (confirmed by Higgsfield FAQ and observed behaviour).

**Typical full project budget**: 150 credits gets you a 48s festival cut + 9 TikTok derivatives + a 3-minute music clip with retry headroom.

---

## 8. Known failure modes

| Failure | Root cause | Fix |
|---|---|---|
| "Ugly" I2V output | Seed aesthetic contradicts prompt register | Use Soul for photoreal seed when prompt demands photoreal; don't feed Pillow schematic into photoreal prompts |
| Face morphs across 6s | Visible human face in seed | Obscure faces via hoods, blindfolds, backs-to-camera, or omit figures entirely |
| Text garbled / hallucinated | AI video models fail on glyphs | Add overlays in post via Pillow PNG + ffmpeg `overlay` filter |
| Shot discontinuity across sequence | Each shot gets own seed | Use seed continuity: 3 seeds max for 8 shots |
| Seed too stylised | Using Pillow for photoreal register | Use Soul Standard; Pillow only for stylised HELEN-signature work |
| ffmpeg `drawtext` not available | Homebrew build variance | Fallback: Pillow PNG with text, then `overlay` filter |
| Telegram bot rejects upload | >50MB (bot API limit) | Compress to CRF 26, maxrate 2.4 Mbps |
| Schema unknown for new endpoint | Evolving API | Iterate probes with defaults (UUID for `hf-api-key`, string for `image_url`, int for `duration`) and parse 400-error field hints |

---

## 9. Script inventory (this session)

All in `/tmp/helen_temple/` (non-sovereign working dir):

| Script | Purpose |
|---|---|
| `phase1_unripple.py` | Seed A + Shot 1 (static) + Shot 2 (dolly) — first continuity test |
| `phase2a_truth_tests.py` | Seed B + Shot 3 (stall) + Seed C + Shot 5 (lag) — anomaly truth tests |
| `ship_full_teaser.py` | 4 new shots (4, 6, 7, 8) + concat + audio synth + mux + 9 TikTok derivatives + Telegram |
| `resume_ship.py` | Continuation after ffmpeg filter failure (scale:force_original_aspect_ratio typo) |
| `finish_ship.py` | Pillow PNG overlay fallback when `drawtext` unavailable |
| `music_cut.py` | Re-score festival cut with cinematic ambient (numpy synth Dm→F→Am→Gm) |
| `music_clip_3min.py` | 20-segment recomposition to 180s, muxed with full song, compressed for Telegram |

Copy patterns from these when building the next HELEN video project. All use the canonical auth + upload + submit + poll + download pattern documented here.

---

## 10. Governance notes

- All writes under `oracle_town/skills/video/**` are non-sovereign per `~/.claude/CLAUDE.md`. Firewalled paths (`oracle_town/kernel/**`, `helen_os/governance/**`, etc.) must not be touched.
- Video renders burn real money. Validate budget + balance before each phase.
- Ship script must ask operator Y between Phase 1 (truth tests) and Phase 2 (full render) to catch catastrophic register mismatch before spending full credits.
- Artifacts (mp4, png, wav) live in `/tmp/` by default. Only SKILL.md and authored prompts belong in the SOT.
- Credits consumed: log each phase's burn to compare against estimate. Discrepancy > 20% means calibration drift; re-measure.
- Per `NO RECEIPT = NO CLAIM`: any claim that a render was delivered requires visible Bash tool output in the session transcript OR a `helen_say.py` receipt. "Operator said msg X was delivered" is hypothesis until verified.

---

## 11. Proven examples

Session 2026-04-19/20 (UNRIPPLE) shipped:

| Artifact | Telegram msg | Description |
|---|---|---|
| Birth of HELEN v6.1 | 671 | 102s Zephyr-voiced introspective (Pillow, stylised) |
| Shot 1 THE ENTRANCE (DoP Standard) | 674 | First real I2V; operator 1/10 (seed-prompt mismatch) |
| Shot 1 THE ENTRANCE (Soul+Seedance) | 675 | Pivoted to photoreal seed; operator accepted |
| Phase 1 Shot 1/2 continuity | 676, 677 | Static + dolly from same seed |
| Phase 2a Shot 3 stall | 678 | Operator 8/10 — ripple freeze anomaly |
| Phase 2a Shot 5 reflection lag | 679 | Operator 9/10 — core thesis anchor |
| Festival cut ambient soundscape | 681 | 48s, 8 shots, Mode A audio |
| TikTok derivatives (A/B/C × 3, 5, 7) | 682–690 | 9 viral re-cuts |
| Festival cut with Helen Os song | 691 | Mode B audio, operator-accepted |
| 3-minute music clip | 693 | 20-segment recomposition, full song, zero new credits |

Total Higgsfield credit burn across session: ~88 credits (well under 150 target).

---

## 12. Complement — sibling docs

- `oracle_town/skills/video/HELEN_VIDEO_PROMPT_V1.md` — shot grammar (subject/camera/lighting/constraints)
- `oracle_town/skills/video/helen_initiation/HELEN_CHARACTER_V1.md` — HELEN-as-visual-character (parallel aesthetic; use HELEN-as-perception-layer vs HELEN-as-character consciously)
- `oracle_town/skills/video/hyperframes/SKILL.md` — declared but not LIVE; npm allowlist pending

This skill is the production-system layer. HELEN_VIDEO_PROMPT_V1 is the shot-grammar layer. Both are needed.

---

## 13. Admission status

This document is **DOCTRINE**, not INVARIANT. It describes patterns calibrated in one session with real API calls and measured burn. Promotion to INVARIANT requires:

- Second independent session reproduces the same pipeline and produces a teaser of comparable quality with ≤10% budget deviation
- `helen_say.py` receipt binding this document's SHA256 to the ledger
- K2 / Rule 3: the session that promotes must not be the session that authored

Until then: cite as "current working doctrine calibrated from 2026-04-19/20 session."

---

## 14. Signing discipline (tiered)

HELEN video output signs itself three different ways depending on output channel. Governing principle: **sign, don't scream.** Overlay "HELEN" text, centered logos, or stacked branding break the anomaly register and read as cringe on TikTok. Silent signature — HELEN present in the world, not stamped on the screen — is the default.

### Tier A — TikTok anomaly clips

- No big overlay text (title card, bottom-third banner, etc.)
- No centered logo on top of the anomaly
- Silent signature only — HELEN is identified by the anomaly itself
- Optional: subtle wardrobe logo if the shot includes a figure
- Account handle, profile caption, and AI-generated disclosure carry brand identity — not the video frame itself

### Tier B — Partner / premium reels (investor decks, Telegram sends, partner proofs)

- Subtle embedded logo in wardrobe or environment (glitch-font HELEN on tank/jacket is proven, see `HELEN_CHARACTER_V2.md`)
- + 0.5-second end card: minimal plate, "HELEN" typography, optional tiny emblem
- Duration of end card: 0.3–0.7s
- Black screen or minimal plate; no music cue, no fade animation
- Purpose: "wow" presentations where authorship must be unambiguous without sacrificing mystique

### Tier C — Festival / authority cut

- Opening OR closing title allowed (not both)
- Still minimal, elegant, not noisy
- Typography aligned with HELEN_CHARACTER_V2 glitch-font register
- No animation gimmicks, no logo-plus-tagline stacks

### Sharpest single rule for edge cases

If unsure which tier applies: **"HELEN" only at the end, and a tiny HELEN logo on clothing during the shot.** That combination gives brand presence without collapsing the anomaly effect.

### Per-channel blunt verdict

- **TikTok**: almost invisible signature
- **Partner / premium**: tasteful end-card
- **HELEN herself as character**: logo in costume is the cleanest move

### Interaction with HELEN-as-perception-layer shots

When HELEN is NOT visible as a character (pure anomaly shots — water, reflection, causal violation, etc.), **Tier A applies automatically** regardless of output channel. A wardrobe logo cannot be placed on water. Silent signature is the only option.

The tiered signing rule only kicks in when HELEN-as-character is present (HELEN_CHARACTER_V2 shots).
