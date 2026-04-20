---
name: video/helen-director/HELEN_CHARACTER_V2
description: Character-consistency specification for HELEN as visible protagonist in videos. Locks the proven method (Seedance Pro direct I2V with photo seed) over the failed methods (soul/reference, soul/character). Unifies peer V1 spec with 2026-04-20 validation data.
helen_faculty: RENDER / CHARACTER
helen_status: DOCTRINE (validated 2026-04-20, session-causal; promotion to INVARIANT requires fresh-lane reproduction + receipt)
helen_prerequisite: oracle_town/skills/video/helen-director/SKILL.md, HELEN_VIDEO_PROMPT_V1, Higgsfield credentials
supersedes: partially supersedes oracle_town/skills/video/helen_initiation/HELEN_CHARACTER_V1.md (adds validation data; palette + Kling schema from V1 remain canonical)
---

# HELEN Character — V2

**Scope**: how to put HELEN (as a visible protagonist) into a video with identity preserved across the shot.

**Not scope**: how to build HELEN-as-perception-layer films (see `SKILL.md` for the UNRIPPLE pattern — invisible anomalies, no visible HELEN).

---

## 1. Visual tokens (locked, unified)

| Token | Value | Observed in |
|---|---|---|
| Hair | Flame-orange / copper-red, medium-length, tousled/wavy | grok-image-*, hf_* |
| Hair accessories | Two small **blue teardrop clips** (drift-prone — see §5) | peer V1, grok-image |
| Eyes | Blue / teal-blue | hf_* |
| Skin | Fair, **freckles on nose + cheeks** | peer V1, hf_* |
| Choker | Black studded, blue gem at front | grok-image, T3 validation |
| Necklace | Silver chain + **blue teardrop pendant** | grok-image, T3 |
| Bracelet | Silver chain, both wrists | grok-image, T3 |
| Baseline top | **White ribbed tank** with **"HELEN" glitch-font logo** in blue-purple, orange trim | grok-image |
| Alt costumes | Cyberpunk jacket (neon cyan accents, HELEN patch); robes; streetwear; adapts per scenario | hf_*, peer V1 |
| Style range | Photoreal ↔ anime-cyberpunk; same identity across both | grok-image vs hf_* |

Peer V1 palette (3200K torchlight environment) canonical:
```
Hair lit    (220,  55,  40)   warm-shifted crimson
Hair base   (188,  28,  28)   deep crimson
Hair shadow (120,  15,  15)
Hair clip   ( 55,  95, 210)   blue teardrop
Freckles    (160,  75,  45)   warm amber-brown
```

---

## 2. Proven method — Seedance Pro direct I2V

**Validated 2026-04-20, session 3ae3812adacb.**

```python
POST https://platform.higgsfield.ai/bytedance/seedance/v1/pro/image-to-video
Authorization: Key <HF_API_KEY>:<HF_API_SECRET>
User-Agent: higgsfield-client-py/1.0
Content-Type: application/json

{
  "image_url": "<Higgsfield CDN URL of HELEN reference photo>",
  "prompt":    "<motion-only prompt, NO identity description>",
  "duration":  6
}
```

**Core rule**: the seed image IS the identity. The prompt is ONLY physics / motion / environment.

Do **not** describe HELEN's hair, clothing, face, or freckles in the prompt. Seedance inherits all of that from the seed. Describing identity in the prompt invites drift: the model tries to reconcile "what's in the image" vs "what the text says" and may compromise both.

**Example motion-only prompt** (T3 validated):
```
HELEN stands still, slight natural head tilt and slow blink, very
subtle shoulder movement, no arm or hand motion. Camera completely
locked, zero motion. [0-6s] static portrait with minimal life. Wind
slightly moves her hair. Identity stable: same face, hair color,
clothing throughout. No morph. Photoreal, 35mm, grounded. No camera
motion. No other figures.
```

Result (msg 697): ~95% identity preservation. Hair colour, logo, choker, pendant, bracelets, freckles all held across 6s.

---

## 3. What failed — do not use for character identity

**Tested 2026-04-20:**

| Endpoint | Result | Why it fails |
|---|---|---|
| `higgsfield-ai/soul/reference` | **FAIL** (msg 695) | Mode is scene/aesthetic reference, not character reference. Produced generic dark-haired woman matching only the scene context (desert dawn) — completely lost HELEN's identity. |
| `higgsfield-ai/soul/character` | **FAIL** (msg 696) | Same generic result. Likely requires a pre-registered character ID bound to the account; the bare `image_url` is not treated as identity anchor. |

**Implication**: Soul mode path `{standard, reference, character}` gives scene/aesthetic guidance but does NOT transfer facial/outfit identity from a single image. For character consistency, go **directly to Seedance Pro I2V** — skip the Soul regeneration step entirely when HELEN must appear.

---

## 4. Reference image inventory

`~/Desktop/HELEN_OS_PICS/` (18 stills, 6 videos as of 2026-04-20):

**Photoreal set** — for festival / cinematic work:
- `grok-image-093c18d5-...jpeg` — hero shot, HELEN tank + hair + blue clips + choker + pendant (session hero; validated in T3)
- `grok-image-093c18d5-...jpeg` (dupe; replace filename as needed)
- `grok-image-1efcf428-...jpg`
- `grok-image-73c48009-...jpg`
- `grok-image-aef62133-...jpg`
- `grok-image-9aa0aee0-...jpeg`

**Anime/cyberpunk set** — for streetwear/reel register:
- `hf_20260411_*.png` (5 Higgsfield anime renders, brighter saturation, neon accents)

**Screenshots** — source/reference context:
- `Capture d'écran 2026-04-14 à 02.03.00.png` and four others (raw reference state)

**Existing HELEN videos** (pre-session, may inform motion/identity priors):
- `_users_...generated_video.MP4` (6 MB)
- `grok-video-c59488a7-...mp4` (8 MB)
- 4 × `hf_*.mp4` (Higgsfield video experiments, 2–35 MB)

**Pick-one rule for a new shot**: select the reference whose *costume* + *framing* match what that shot needs. Then feed to Seedance Pro as `image_url`. No re-generation.

---

## 5. Known drift + mitigations

**Confirmed drift (T3, 2026-04-20)**: small blue teardrop hair clips → teal flower clip at t=6s. Accessory-scale items are the weak channel.

Mitigations:

| Problem | Fix |
|---|---|
| Small accessory morphs across 6s | Prefer reference images where clips are visually prominent; keep shots at **5s** not 6s (less frames for accumulation) |
| HELEN logo text garbled | Use photos where logo is large + centred; add `"HELEN tank logo readable, glitch font, do not alter text"` to motion prompt — partial success, AI video still hallucinates glyphs |
| Multi-shot continuity | Use the **same reference image** across all shots of a sequence; different images = different HELEN even when tokens match |
| Face morph under large motion | Keep HELEN motion minimal in character shots; save big action for anomaly/environment shots |

---

## 6. Integration with UNRIPPLE pipeline (80/20 rule)

Per operator direction: **HELEN appears visibly in ~20% of shots, invisibly in 80%.** Rarity is signature.

For an 8-shot teaser:
- **6–7 shots**: UNRIPPLE-style invisible anomaly (world has a glitch, HELEN is the gate detecting it) — use Soul seed + Seedance Pro motion (proven UNRIPPLE pipeline from SKILL.md §2)
- **1–2 shots**: HELEN appears as silent observer (witnesses the anomaly, doesn't intervene) — use **direct HELEN photo as Seedance seed** per §2 above

Recommended positions for HELEN-visible shots:
- Shot 0 / teaser cold-open (establishing the observer)
- Shot 5 or 6 (mid-film witness beat)
- NOT the final shot (save the anomaly closure as HELEN's signature; she does not take curtain call)

---

## 7. Two production paths, per register

**A — Photoreal / festival register** (use grok-image set)
- Seed: `~/Desktop/HELEN_OS_PICS/grok-image-*.jpeg`
- Endpoint: `bytedance/seedance/v1/pro/image-to-video`
- Prompt: motion-only, cinematic vocab
- Output: matches UNRIPPLE festival cut aesthetic

**B — Anime-cyberpunk / reel register** (use hf_* set)
- Seed: `~/Desktop/HELEN_OS_PICS/hf_*.png`
- Endpoint: Kling 2.1 Pro (`kling-video/v2.1/pro/image-to-video`) — peer's choice in V1, higher saturation holds well for anime register. OR Seedance Pro for consistency with the rest of the pipeline.
- Prompt: motion-only, streetwear/neon vocab
- Output: matches Higgsfield anime source aesthetic

Do not mix registers in one teaser. Pick one. Festival audience wants photoreal. TikTok audience arguably tolerates either.

---

## 8. Budget calibration

Per-shot cost when HELEN must appear visibly:
- No Soul regeneration needed (skip the ~3-credit T2I step)
- Direct Seedance Pro I2V: **~10 credits per 6s clip**
- Thus HELEN-visible shots are **cheaper** than anomaly shots (which need Soul seed + Seedance) by ~3 credits

A 20/80 mix on an 8-shot teaser:
- 2 HELEN shots × 10 cr = 20
- 6 anomaly shots × 13 cr (3 Soul + 10 Seedance, with seed reuse across multiple shots) ≈ 60
- Total: ~80 credits (tighter than full-Soul 8-shot which was ~90)

---

## 9. Validation telemetry (session 3ae3812adacb, 2026-04-20)

| Artifact | Telegram msg | Verdict |
|---|---|---|
| T1 soul/reference result | 695 | FAIL — identity lost |
| T2 soul/character result | 696 | FAIL — identity lost |
| T3 Seedance direct I2V result | 697 | PASS — ~95% identity preserved |

Reference used for all three: `grok-image-093c18d5-5c5d-44e0-a359-0f6475d7c391.jpeg`.

Credit burn for validation: ~16 (3 + 3 + 10).

Session-causal provenance: I produced the validation tool calls + the reference upload + the observation of T3 as winner. This document captures the finding before context fades.

---

## 10. What's next (when a fresh lane revisits this)

1. Run a **second fresh-lane validation** of the T3 method with a different HELEN reference image (different costume, different pose). Confirm ≥90% identity hold replicates.
2. Test **Kling 2.1 Pro** as alternate I2V backend with HELEN photo as seed (peer V1 reported success there; we haven't tested it here).
3. Test **longer shots** (Kling supports `duration: 10`) — does identity hold at 10s or does accessory drift compound?
4. Try **multi-reference injection** if Higgsfield adds that API surface. Current probes showed only single `image_url`.
5. When two fresh lanes agree on the method + drift profile, promote this document from DOCTRINE to INVARIANT via `helen_say.py` receipt.

---

## 11. Cross-references

- `SKILL.md` (same directory) — end-to-end video production pipeline; character-consistency method belongs here as the "when HELEN must appear" sub-case
- `HELEN_VIDEO_PROMPT_V1.md` (sibling in `oracle_town/skills/video/`) — shot grammar; motion-only prompt structure
- `helen_initiation/HELEN_CHARACTER_V1.md` (peer session, 2026-04-20) — palette numbers + Kling schema + "adapts to any costume" clause; still valid as complementary spec
- `helen_initiation/` directory — peer's Shot 1 Kling test scripts; reference pattern for Kling schema (`{"type": "image_url", "image_url": <url>}` + `duration: 5|10`)

---

## 12. Status

**DOCTRINE** as of 2026-04-20, session 3ae3812adacb → V2 commit.

Not INVARIANT until:
- Second fresh Claude Code lane reproduces T3 method with ≥90% identity hold on a different reference
- `helen_say.py` receipt issued binding this document's SHA256 to the ledger
- K2 / Rule 3: the session that promotes must not be the session that authored

Until then: cite as "validated character-consistency method per 2026-04-20 session."
