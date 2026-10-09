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
- `pixels_changed_outside_mask` must be 0, otherwise the run is invalid.
- `mask.png` must be checked by eye at 100 %: a wrong mask is the main failure mode.
- ΔE76 measures the distance to the *parameter* colour, not to a Manucurist product.

Limits: opaque shades only (a translucent shade such as Active Glow depends on skin and coats and is not simulated);
target colours are approximate parameters until tied to a sourced product reference; JPEG export of the outputs
breaks bit-identity. Stills are approved by the operator before any animation; no X-Feed / Seedance spend.

Tests: `python -m pytest tests -q` (synthetic hand: mask IoU, invariance outside the mask, highlight kept,
texture kept, CLI outputs, deterministic bytes, empty mask refused).
