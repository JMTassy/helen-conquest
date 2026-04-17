---
name: video/hyperframes
description: Render HELEN's narrative artifacts (manifestos, epoch summaries, ledger replays, district outcomes) as MP4 video using HeyGen's HyperFrames framework. HTML/CSS/GSAP/Lottie/Three.js compositions → MP4. NEVER renders HELEN-as-speaker (Rule 3).
fused_from: heygen-com/hyperframes (Apache 2.0)
helen_faculty: VIDEO
helen_witness: R-20260416-0006 (chained)
helen_prerequisite: NPM_REGISTRY_ALLOWLIST + ARTIFACTS_MEDIA_PATH
---

# HyperFrames (HELEN video)

Programmable video. Compositions are HTML files; the framework records them via Chromium and muxes audio with FFmpeg. No package install — runs via `npx hyperframes`.

## Invocation

```bash
npx hyperframes preview        # studio in browser
npx hyperframes render         # composition → MP4
npx hyperframes lint           # report composition issues
```

Default render path is repo-relative. **HELEN-side override:** all renders must land under `artifacts/media/` (allowlisted), never the repo root.

## Reference project

`heygen-com/hyperframes-launch-video` is a 49.77s worked example (1920×1080@30, 17 sub-compositions). Cloned **reference-only** — do not import its compositions into HELEN's render queue.

## HELEN conditions (from witness audit, 2026-04-16)

1. **HELEN self-portraits ARE accepted** *(operator erratum 2026-04-16, supersedes pre-witness audit)*. Video may depict HELEN as a speaking avatar including narrating her own verdicts. The pre-witness audit treated this as a Rule 3 self-witness loop; operator override notes that depicting a *recorded* ledger event ≠ live self-approval, so Property 1 is not violated as long as the video renders past sealed receipts, not pending claims.

   Video may depict:
   - Ledger event sequences
   - District / Conquest run outcomes
   - Manifesto text animations
   - Architectural diagrams in motion
   - HELEN as a speaking avatar (post-erratum)

   Video may **NOT** depict:
   - Future predictions presented as observed outcomes
   - Composites that imply consensus where the ledger shows contradiction
   - Live (unsealed) HAL claims as if they were settled — only sealed receipts may be voiced/animated by an on-screen HELEN
2. **Allowlist npm registry** before first `npx` invocation.
3. **Media path:** all output goes to `artifacts/media/<YYYY-MM-DD>__<topic>.mp4`. Retention policy: 90 days unless promoted by ledger entry.
4. **Composition provenance:** every rendered MP4 ships with `<basename>.provenance.json` listing source HTML composition SHA, ledger entries depicted, and (if any) LLM-generated copy hashes (K8 wrap).

## Prerequisites

- Node.js >= 22
- FFmpeg
- Network egress to npm registry (gated)

## Output

- `artifacts/media/<basename>.mp4` — the render
- `artifacts/media/<basename>.provenance.json` — what was depicted, from where
- `artifacts/media/<basename>.composition_sha` — SHA of source HTML at render time

## Provenance

See `.provenance.md`.
