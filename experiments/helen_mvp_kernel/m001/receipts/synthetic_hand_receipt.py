#!/usr/bin/env python3
"""Regenerate the measured figures quoted in the session recap (section 1.5) on the test's synthetic hand.

    python receipts/synthetic_hand_receipt.py > receipts/synthetic_hand_receipt.json

Synthetic data only. Not evidence about any real image.
"""
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE.parent / "tests")]
import recolor_nails as rn  # noqa: E402
from test_recolor_nails import synthetic_hand  # noqa: E402

src, _, boxes = synthetic_hand()
diag = []
mask = rn.auto_mask(rn.srgb_to_lab(src), boxes, "lighter", diag)
rows = {}
for name, hexv in (("coral_approx", "#E2483B"), ("pistachio_approx", "#C8D8A0")):
    tl = rn.hex_to_lab(hexv)
    out, alpha, info = rn.recolour(src, mask, tl)
    rows[name] = {"target_hex": hexv, "output_sha256": hashlib.sha256(out.tobytes()).hexdigest()[:16],
                  **rn.measure(src, out, mask, alpha, tl), **info}
print(json.dumps({"data": "synthetic hand from tests/test_recolor_nails.py (seed 7, 120x160)",
                  "source_sha256": hashlib.sha256(src.tobytes()).hexdigest()[:16],
                  "mask_diagnostics": diag, "variants": rows}, indent=1))
