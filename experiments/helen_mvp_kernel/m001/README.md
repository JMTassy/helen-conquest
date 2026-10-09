# M001-A · COLOR CONSTANCY baseline (NON_SOVEREIGN · authority=false · budget 0)

Same master image, **only the nail colour changes**. Deterministic CIELAB recolour: no generative AI, no credits,
no network. It is also the reference any generative attempt must match on invariance (0 pixel changed outside the nail).

```bash
pip install pillow numpy
python recolor_nails.py I0006.jpeg --boxes boxes_I0006.json \
    --target "coral_approx=#E2483B" --target "pistachio_approx=#C8D8A0" --out m001a_I0006
# or, if the automatic split misses: --mask mask_I0006.png   (white = nail, painted by a person)
```

`boxes_I0006.json` = `[[x, y, w, h], ...]`, one box per visible nail with a few px of skin around it.
`--nail lighter|darker`: is the nail lighter or darker than the surrounding skin inside the box (default lighter).

Outputs (PNG, lossless): `mask.png`, `00_original.png`, `NN_<name>.png`, `NN_<name>_diff.png`, `m001a_sheet.png`,
`report.json` (source sha256, per variant: pixels changed, changes outside the mask, ΔE76 to target, texture kept).

Read the result:
- `mask.png` decides, checked by eye at 100 %. A wrong mask is the main failure mode, and **no number in the report
  validates the mask**: a mask that bleeds onto skin still gives 0 changes outside it and a small ΔE76. On a real
  still, an automatic mask on a bare nail was wrong and scored the *better* ΔE76.
- Draw each box with **skin all around the nail**. `mask_diagnostics` (box mode) flags a box for inspection when the
  mask reaches the box border (`border_touch` > 5 %), when Otsu separability η < 0.6, or when the area is outside
  15–85 % of the box; `reasons` says which. Then fix the box, try `--nail darker`, or paint a mask.
  **Not flagged does not mean correct.** A real bare-nail case passed the first version of these flags (η 0.611,
  IoU 0.55 against a hand-traced mask). Separability cannot see a split by illumination: on a side-lit synthetic
  finger the wrong mask has η 0.73–0.83, while the border check flags all 14 swept cases and none of the good ones.
  That is synthetic evidence; the thresholds are uncalibrated on real stills.
- `--reference-mask ref.png` (traced by a person) adds `mask_vs_reference`: IoU, overflow onto skin, missed nail.
  This is how to calibrate the flags on real cases. Keep client images and masks out of this public repository.
- `pixels_changed_outside_mask` (outside the nail + 1 px feather ring) must be 0; ring changes are counted apart.
- `mean_chroma_error_nail_body`: did the body reach the target a*, b*. `mean_dE76_to_target_nail_body`: mostly the
  kept shading, not a target-hit score. `texture_kept_corr_L_body`: texture on the body; the pooled
  `texture_kept_corr_L` drops when highlights keep their lightness while the body moves (intended).
- `gamut_clipped_px_body` / `_highlight_blend`: target colours the screen cannot show exactly.
- ΔE76 and chroma error measure the distance to the *parameter* colour, not to a Manucurist product.

`receipts/synthetic_hand_receipt.json` regenerates the synthetic figures quoted in the session recap
(`python receipts/synthetic_hand_receipt.py`).

Limits: opaque shades only (a translucent shade such as Active Glow depends on skin and coats and is not simulated);
target colours are approximate parameters until tied to a sourced product reference; JPEG export of the outputs
breaks bit-identity. Stills are approved by the operator before any animation; no X-Feed / Seedance spend.

Tests: `python -m pytest tests -q` (synthetic hand: mask IoU, invariance outside the mask, highlight kept,
texture kept, CLI outputs, deterministic bytes, empty mask refused, body-only texture and chroma hit,
bare nail close to skin flagged, side-lit failure flagged by the border check, reference comparison).
