# HELEN — in-repo character references

Canonical reference images for HELEN character-consistent video generation.
All are 1024px (longest edge), JPEG quality 85. Source files live in the
operator's `~/Desktop/HELEN_OS_PICS/` folder (originals much larger).

These are the seeds fed directly to `bytedance/seedance/v1/pro/image-to-video`
per HELEN_CHARACTER_V2.md §2 — the proven method.

## Files

| File | Register | Source | Use case |
|---|---|---|---|
| `helen_photoreal_front.jpg` | Photoreal modern street | `grok-image-093c18d5-...jpeg` | Festival / cinematic work. Validated hero image (T3, 2026-04-20, ~95% identity hold). |
| `helen_anime_streetwear.jpg` | Anime cyberpunk neon | `hf_20260411_223314_...png` | Streetwear reels / TikTok register. Higgsfield anime source. |
| `helen_steampunk_range.jpg` | Steampunk retro-futurist | `grok-image-1efcf428-...jpg` | Range demonstration — proves HELEN adapts across costume worlds while identity tokens (hair, freckles, pendant, HELEN logo) hold. Not typical shot material. |

## Do not use

- `helen-director/`-external references (peer's `helen_initiation/`) are a parallel
  V1 spec with slightly different aesthetic choices (hooded blindfolded figure).
  Both are valid HELEN, different moods. Don't mix in one teaser.

## How to use

```python
# Direct path per SKILL.md pipeline
seed_path = "oracle_town/skills/video/helen-director/references/helen_photoreal_front.jpg"
# Upload to Higgsfield CDN via POST /files/generate-upload-url
# Feed returned public_url as image_url to Seedance Pro I2V
# Motion-only prompt. Do not describe identity.
```

## Do not

- Do not regenerate these via `soul/reference` or `soul/character` — both modes
  failed to preserve identity in 2026-04-20 validation (see HELEN_CHARACTER_V2.md §3).
- Do not describe HELEN's hair, face, or clothing in the motion prompt — the seed IS
  the identity. Describing invites drift.

## Identity tokens (for reviewer use, not for prompting)

Flame-orange hair · tousled · blue teardrop hair clips · blue/teal eyes · freckles
on nose and cheeks · black studded choker · silver chain + blue pendant · silver
bracelets · HELEN glitch-font logo on tank/jacket · cyberpunk baseline streetwear.
