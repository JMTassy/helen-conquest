"""M001-A baseline on a synthetic hand: deep skin, pale nails with shading, texture and a specular highlight."""
import hashlib
import json
import pathlib
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import recolor_nails as rn  # noqa: E402

CORAL = "#E2483B"
NAILS = [(40, 50, 18, 26), (100, 44, 18, 28)]  # ellipse centre x, centre y, half-width, half-height


def synthetic_hand(seed=7):
    rng = np.random.default_rng(seed)
    h, w = 120, 160
    img = np.empty((h, w, 3), dtype=np.float64)
    img[:] = (112, 72, 52)                                        # deep skin
    img += rng.normal(0, 4, (h, w, 1))                            # skin grain
    yy, xx = np.mgrid[0:h, 0:w]
    truth = np.zeros((h, w), dtype=bool)
    for cx, cy, rx, ry in NAILS:
        e = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
        truth |= e
        shade = (yy - cy) / ry * 14                               # top-to-bottom shading
        ridges = 5 * np.sin(xx * 1.3)                             # nail ridges (texture to keep)
        base = np.stack([228 - shade + ridges, 186 - shade + ridges, 184 - shade + ridges], axis=-1)
        img[e] = base[e]
        spot = ((xx - (cx - 5)) ** 2 + (yy - (cy - 10)) ** 2) <= 9  # specular highlight
        img[spot & e] = (252, 252, 250)
    boxes = [[cx - rx - 6, cy - ry - 6, 2 * rx + 13, 2 * ry + 13] for cx, cy, rx, ry in NAILS]
    return np.clip(np.round(img), 0, 255).astype(np.uint8), truth, boxes


def run(mask, src, hexv=CORAL):
    tl = rn.hex_to_lab(hexv)
    out, alpha = rn.recolour(src, mask, tl)
    return out, rn.measure(src, out, mask, alpha, tl), tl


def test_auto_mask_finds_the_nails():
    src, truth, boxes = synthetic_hand()
    mask = rn.auto_mask(rn.srgb_to_lab(src), boxes, "lighter")
    iou = (mask & truth).sum() / (mask | truth).sum()
    assert iou > 0.95, iou


def test_only_nail_pixels_change_and_colour_reaches_target():
    src, truth, boxes = synthetic_hand()
    mask = rn.auto_mask(rn.srgb_to_lab(src), boxes, "lighter")
    out, m, _ = run(mask, src)
    assert m["pixels_changed_outside_mask"] == 0 and m["max_change_outside_mask"] == 0
    ring = rn.feather(mask, 1) > 0
    assert np.array_equal(out[~ring], src[~ring])                 # skin beyond the 1 px feather: bit-identical
    assert m["mean_dE76_to_target_nail_body"] < 8, m              # residual = kept shading/ridges, by design
    assert m["texture_kept_corr_L"] > 0.9, m


def test_highlight_stays_bright_and_near_neutral():
    src, truth, _ = synthetic_hand()
    out, _, tl = run(truth, src)
    cx, cy = NAILS[0][0] - 5, NAILS[0][1] - 10
    lab_src, lab_out = rn.srgb_to_lab(src[cy, cx][None, None])[0, 0], rn.srgb_to_lab(out[cy, cx][None, None])[0, 0]
    assert lab_out[0] > lab_src[0] - 3 and lab_out[0] > tl[0] + 20
    assert np.hypot(lab_out[1], lab_out[2]) < 10                 # not painted coral


def test_painted_mask_mode_and_cli_outputs(tmp_path):
    src, truth, boxes = synthetic_hand()
    Image.fromarray(src).save(tmp_path / "hand.jpg", quality=95)
    Image.fromarray((truth * 255).astype(np.uint8)).save(tmp_path / "mask.png")
    (tmp_path / "boxes.json").write_text(json.dumps(boxes))
    for mode, extra in (("mask", ["--mask", str(tmp_path / "mask.png")]), ("boxes", ["--boxes", str(tmp_path / "boxes.json")])):
        out = tmp_path / mode
        rep = rn.main([str(tmp_path / "hand.jpg"), *extra, "--target", f"coral_approx={CORAL}",
                       "--target", "pistachio_approx=#C8D8A0", "--out", str(out)])
        assert [v["pixels_changed_outside_mask"] for v in rep["variants"]] == [0, 0]
        for f in ("mask.png", "00_original.png", "01_coral_approx.png", "02_pistachio_approx.png",
                  "01_coral_approx_diff.png", "m001a_sheet.png", "report.json"):
            assert (out / f).exists(), f
        decoded = np.asarray(Image.open(tmp_path / "hand.jpg").convert("RGB"))
        variant = np.asarray(Image.open(out / "01_coral_approx.png"))
        zone = rn.feather(np.asarray(Image.open(out / "mask.png")) > 127, 1) > 0
        assert np.array_equal(variant[~zone], decoded[~zone])     # PNG output: invariance survives the save


def test_deterministic_bytes(tmp_path):
    src, _, boxes = synthetic_hand()
    Image.fromarray(src).save(tmp_path / "hand.png")
    (tmp_path / "boxes.json").write_text(json.dumps(boxes))
    digests = []
    for k in (1, 2):
        rn.main([str(tmp_path / "hand.png"), "--boxes", str(tmp_path / "boxes.json"), "--target", f"c={CORAL}",
                 "--out", str(tmp_path / f"r{k}")])
        digests.append(hashlib.sha256((tmp_path / f"r{k}" / "01_c.png").read_bytes()).hexdigest())
    assert digests[0] == digests[1]


def test_empty_mask_is_refused():
    src, _, _ = synthetic_hand()
    try:
        rn.recolour(src, np.zeros(src.shape[:2], dtype=bool), rn.hex_to_lab(CORAL))
    except ValueError as e:
        assert "empty nail mask" in str(e)
    else:
        raise AssertionError("empty mask accepted")
