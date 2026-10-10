# HELEN motion showreel · 15 s · provenance

🔵 OBSERVED · NON_SOVEREIGN · authority=false · 0 credits · no generated media.
Every pixel and audio sample is computed by `showreel.py`; no AI model, stock footage, image or sound file.

## Render of 2026-10-10

| Item | Value |
|---|---|
| Script | `showreel.py` sha256 `d9dc3b3de9d8fd6d43c0a1a6a072a873937d470764b4482566af2954e10877f2` (printed, shortened, in the lockup) |
| Frames | 450 @ 30 fps, 1920×1080, drawn at 2× and reduced (Lanczos) |
| Audio | procedural, 48 kHz stereo, 223 timed events from the same timeline; `audio.wav` sha256 `36962029cdcfca86…` |
| MP4 | `HELEN_motion_showreel_15s.mp4`, H.264 CRF 16 + AAC 192k, 2.9 MB, 15.000 s, sha256 `a9c3fc3a2da57603…` |
| Fonts | Cormorant Garamond 5.3.0, IBM Plex Mono 5.3.0 (`@fontsource` via npm, woff2 → ttf); Cormorant numerals with `lnum` |
| Tools | Python 3.11 · Pillow 12.3.0 · numpy 2.4.6 · ffmpeg 6.1.1 |

Encode: `ffmpeg -framerate 30 -i frames/f%04d.png -i audio.wav -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p
-tune animation -c:a aac -b:a 192k -shortest -movflags +faststart HELEN_motion_showreel_15s.mp4`.
The MP4 is not committed (media stays out of the public repo); the script regenerates it.

## Structure

| Time | Scene | What the code shows |
|---|---|---|
| 0.0–1.2 s | 00 OPEN | a plotter rule drawn from the centre, scale ticks, HELEN typed |
| 1.2–3.4 s | 01 TYPE | MOTION set letter by letter (drawn trails), type metrics, italic swap, tracking +10 → +60 |
| 3.4–5.6 s | 02 RULE | a two-pendulum harmonograph plotted live, its equations and sample counter |
| 5.6–7.6 s | 03 FIELD | halftone sphere stamped row by row, light turning 40° → 135° (after Harmon & Knowlton, 1966) |
| 7.6–9.4 s | 04 GRID | 12-column grid, six panels wiped in, then reflowed |
| 9.4–11.2 s | 05 REFUSAL | 150 particles at a frontier: gold admitted, copper rejected and marked — "no receipt, no entry" |
| 11.2–13.0 s | 06 TIME | recap of the five works on twos, collapsing into the centre point |
| 13.0–13.3 s | black | pure black, silence (drone cut dead) |
| 13.3–15.0 s | LOCKUP | HELEN, "every frame is a rule you can read", render receipt |

The gold centre point is the one element that never moves (absent only during the black).

## Checks on the encoded MP4 (decoded, not the source frames)

- 1 frame per second plus frames 392, 398, 399 decoded: content frames peak at 235–253; frames 390–398 are
  uniform black (max 9 after the codec); frame 399 shows only the point.
- Mean luminance is below 25 on most frames (9–28; 124 on the grid scene): this is a dark film by design. The
  "mean > 25" rule of the pipeline guards against black renders and is not met; reported, not tuned.
- Audio: peak 0.85, RMS 0.059 over 0–13 s, 0.000 during the black, 0.035 on the lockup.
