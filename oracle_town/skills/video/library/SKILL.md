---
name: video/library
description: HELEN asset library — stills, audio, and effects — harvested from already-paid output. Three-layer system (keyframe harvester, effects registry, audio catalog) that turns existing renders into a reusable production pool. Scales video productivity at marginal cost by editing the library instead of regenerating pixels.
helen_faculty: VIDEO / ASSET MANAGEMENT
helen_status: DOCTRINE (calibrated 2026-04-21)
helen_prerequisite: video/math_to_face (consumer of the library at render time)
---

# HELEN Library — asset pool for marginal-cost video production

**Class**: Non-sovereign asset management. No kernel authority. No ledger write. Harvests already-paid outputs into a tagged, queryable pool so subsequent videos can be assembled from the library instead of freshly generated.

> *"Create a real digital clone of HELEN and metaverse for the marginal price of a video edit."* — operator directive 2026-04-21.

## 1. The thesis

HELEN has spent credits. Seedance videos from msg 708-720 contain ~30-60 frame-seconds of canonical HELEN each. Today they exist as monolithic `.mp4` blobs; tomorrow they become a library of tagged stills, recipes, and phrases that cost **zero** to reuse.

```
Credit spent once         →   asset pool
Pool (stills + effects)   →   N future videos at marginal cost
```

The target state: producing a 30s teaser costs the compute of `ffmpeg` filtering the library, not the credits of regenerating HELEN.

## 2. Three-layer architecture

### 2.1 Keyframe library

Harvested HELEN stills, tagged by taxonomy, stored under `/tmp/helen_temple/library/stills/<source>/`. Each frame carries source provenance (which video, which timestamp) so regeneration is repeatable and identity lineage is traceable.

Taxonomy categories (see `taxonomy.md`):
- **portrait** — shoulder-up, face dominant
- **half_body** — torso-up
- **full_body** — whole figure
- **green_screen** — flat neutral bg (target category, currently empty — requires real-backend generation)
- **ritual** — stylized / ceremonial
- **cinematic** — narrative scene context

### 2.2 Effects registry

Named ffmpeg filter recipes (ken-burns variants, xfade patterns, mood-grade curves) exposed as JSON. `assemble_video.py` already implements the primitives; `effects_registry.json` makes them **named and reusable** instead of inlined. Same pattern as WULmoji: palette locked, callers reference by name.

### 2.3 Audio catalog

Indexes existing `/tmp/helen_temple/*.wav` Zephyr outputs with duration + SHA + transcript-if-known. Reuse first, generate-fresh only when phrasing matters (Gemini TTS is free tier per `project_conquest_day_one_teaser.md`).

## 3. Scripts

| Script | Input | Output |
|---|---|---|
| `harvest_keyframes.py` | dir of mp4s | per-video frame dumps + `library_manifest.json` |
| `audio_catalog.py` | dir of wavs | `audio_catalog.json` (paths + durations + hashes) |
| `effects_registry.json` | (static doc) | callable recipe dictionary for assemble_video |

All stdlib + ffmpeg. No PIL ops (stills stay in source colorspace). No numpy.

## 4. Usage

```bash
# harvest every 2s frame from every mp4 in /tmp/helen_temple/
python3 oracle_town/skills/video/library/harvest_keyframes.py \
    --src /tmp/helen_temple --every 2.0 \
    --out /tmp/helen_temple/library

# catalog all wavs
python3 oracle_town/skills/video/library/audio_catalog.py \
    --src /tmp/helen_temple \
    --out /tmp/helen_temple/library/audio_catalog.json

# effects registry is consumed directly as JSON (no CLI)
cat oracle_town/skills/video/library/effects_registry.json | jq '.effects[].name'
```

## 5. Design decisions

- **Assets stay outside the repo.** `/tmp/helen_temple/library/` is ephemeral by convention; the harvester is repeatable from the source videos (also in /tmp). Committing ~500 PNGs would bloat the repo and conflict with git. The library lives on disk; the **skill** lives in the repo.
- **Tagging is shallow at v1.** Source + timestamp only. No ArcFace identity scoring (backend not wired). No mood classifier. No green-screen detector. v2 can add auto-tagging when an image embedder is available.
- **Effects are named, not parameterized by caller.** Once a recipe is in the registry, callers reference it by key. If a new variant is needed, amend the registry — don't inline.
- **Read-only contract at v1.** The library is a consumer pool, not a generator. Generation (fresh HELEN via backends) is a separate thread.

## 6. Consumers

- `video/math_to_face/scripts/render_keyframes.py` — `select_ref()` will eventually read from the library manifest instead of a flat `refs/real/` directory
- `video/math_to_face/scripts/assemble_video.py` — will eventually consume effects by name (`"effect": "ken_burns_slow_in"`) instead of inline zoom expressions
- Future `video/helen_manga/**` or `video/motion_manga/**` skills — same pattern

## 7. Gaps (honest)

- **Green-screen HELEN**: zero frames in current source material. Requires fresh real-backend generation with a green-bg prompt. Target: 5-10 full-body green-screen stills across pose variations.
- **3D / metaverse avatar**: out of scope at v1. Requires different tooling (not ffmpeg/PIL).
- **Identity scoring on harvested frames**: pending ArcFace wiring (MIA v2 promotion path).
- **Lip-sync**: pending a real lip-sync model. Today the pipeline does still keyframes + voice, not synced mouths.

## 8. Status

**DOCTRINE (operational)**. Initial harvest + catalog + registry shipped 2026-04-21. Promotion to INVARIANT requires:
- First consumer script reads from the library manifest instead of `refs/real/`
- K-tau `mu_DETERMINISM` passes on a harvest+assemble replay
- Library reaches 100+ tagged frames across at least 3 taxonomy categories

Until then: cite as "HELEN library v1, operator-calibrated 2026-04-21."

## 9. One-line summary

> Harvest what you already paid for; assemble from the pool; generate only the gaps.
