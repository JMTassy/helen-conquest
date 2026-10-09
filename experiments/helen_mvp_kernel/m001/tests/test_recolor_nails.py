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


def synthetic_hand(seed=7, nail_rgb=(228, 186, 184)):
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
        base = np.stack([c - shade + ridges for c in nail_rgb], axis=-1)
        img[e] = base[e]
        spot = ((xx - (cx - 5)) ** 2 + (yy - (cy - 10)) ** 2) <= 9  # specular highlight
        img[spot & e] = (252, 252, 250)
    boxes = [[cx - rx - 6, cy - ry - 6, 2 * rx + 13, 2 * ry + 13] for cx, cy, rx, ry in NAILS]
    return np.clip(np.round(img), 0, 255).astype(np.uint8), truth, boxes


def run(mask, src, hexv=CORAL):
    tl = rn.hex_to_lab(hexv)
    out, alpha, info = rn.recolour(src, mask, tl)
    return out, {**rn.measure(src, out, mask, alpha, tl), **info}, tl


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


def test_body_texture_chroma_hit_and_gamut():
    """Section 1.5 of the recap: the pooled texture score drops for coral only because highlights keep their
    lightness while the body moves; on the body alone texture is kept, the target chroma is hit, nothing clips."""
    src, _, boxes = synthetic_hand()
    mask = rn.auto_mask(rn.srgb_to_lab(src), boxes, "lighter")
    _, m, _ = run(mask, src)
    assert m["texture_kept_corr_L"] < 0.95                       # pooled: the jump at the highlights
    assert m["texture_kept_corr_L_body"] > 0.999
    assert m["mean_chroma_error_nail_body"] < 1
    assert m["gamut_clipped_px_body"] == 0                       # coral clips slightly in the highlight blend only
    assert m["feather_ring_pixels_changed"] > 0                  # the ring is edited, and counted apart


def test_bare_nail_close_to_skin_is_flagged_for_inspection():
    """A bare nail barely lighter than the skin (the failure seen on a real still): the mask is flagged."""
    lab = rn.srgb_to_lab
    src, _, boxes = synthetic_hand()
    ok = []
    rn.auto_mask(lab(src), boxes, "lighter", ok)
    assert not any(d["inspect"] for d in ok), ok
    bare, _, boxes = synthetic_hand(nail_rgb=(124, 84, 64))     # nail ~ skin (112, 72, 52)
    flagged = []
    rn.auto_mask(lab(bare), boxes, "lighter", flagged)
    assert all(d["inspect"] for d in flagged), flagged


def side_lit_bare_nail(grad=60, nail_delta=10, seed=3):
    """Bare nail on a finger lit from one side: Otsu splits lit from shaded, not nail from skin."""
    rng = np.random.default_rng(seed)
    h, w = 120, 160
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.array([150, 105, 85], float)[None, None, :] + ((xx - 40) / 80 * grad)[..., None] + rng.normal(0, 3, (h, w, 1))
    cx, cy, rx, ry = 80, 60, 18, 26
    nail = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    img[nail] += nail_delta + np.array([8, 0, 0])
    box = [[cx - rx - 14, cy - ry - 10, 2 * rx + 29, 2 * ry + 21]]
    return np.clip(np.round(img), 0, 255).astype(np.uint8), nail, box


def test_side_lit_failure_passes_separability_but_reaches_the_border():
    """The real failure mode: a well-separated but wrong split (lit skin + nail). Separability does not see it
    (eta is high); the mask reaching the box border does. The reference comparison measures the damage."""
    src, nail, box = side_lit_bare_nail()
    d = []
    mask = rn.auto_mask(rn.srgb_to_lab(src), box, "lighter", d)
    assert d[0]["separability_eta"] > rn.ETA_MIN                 # separability alone would let it through
    assert "mask reaches the box border" in d[0]["reasons"]
    cmp = rn.compare_masks(mask, nail)
    assert cmp["iou"] < 0.6 and cmp["overflow_fraction_of_reference"] > 0.5


def test_good_mask_does_not_touch_the_border_and_matches_reference():
    src, truth, boxes = synthetic_hand()
    d = []
    mask = rn.auto_mask(rn.srgb_to_lab(src), boxes, "lighter", d)
    assert all(x["border_touch"] == 0 and not x["inspect"] for x in d), d
    assert rn.compare_masks(mask, truth)["iou"] > 0.95


def test_cli_reference_mask_report(tmp_path):
    src, nail, box = side_lit_bare_nail()
    Image.fromarray(src).save(tmp_path / "f.png")
    Image.fromarray((nail * 255).astype(np.uint8)).save(tmp_path / "ref.png")
    (tmp_path / "b.json").write_text(json.dumps(box))
    rep = rn.main([str(tmp_path / "f.png"), "--boxes", str(tmp_path / "b.json"), "--target", f"c={CORAL}",
                   "--reference-mask", str(tmp_path / "ref.png"), "--out", str(tmp_path / "o")])
    assert rep["mask_diagnostics"][0]["inspect"] and rep["mask_vs_reference"]["iou"] < 0.6


def pearly_shaded_nail(seed=5):
    """Near-neutral pearly nail lit on top and shaded below (its lower half as dark as the skin), on saturated skin:
    lightness cuts the nail in half; chroma separates it whole (the calvi_04 case, synthetic)."""
    rng = np.random.default_rng(seed)
    h, w = 120, 160
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.array([150, 95, 65], float)[None, None, :] + rng.normal(0, 3, (h, w, 1))
    cx, cy, rx, ry = 80, 60, 18, 26
    nail = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    g = 225 - (yy - (cy - ry)) / (2 * ry) * 135                   # 225 at the top of the nail, 90 at the bottom
    img[nail] = np.stack([g + 6, g, g + 2], axis=-1)[nail]
    box = [[cx - rx - 12, cy - ry - 10, 2 * rx + 25, 2 * ry + 21]]
    return np.clip(np.round(img), 0, 255).astype(np.uint8), nail, box


def test_auto_feature_keeps_a_shaded_pearly_nail_whole():
    src, nail, box = pearly_shaded_nail()
    lab = rn.srgb_to_lab(src)
    by_l = rn.auto_mask(lab, box, "lighter", feature="L")
    d = []
    auto = rn.auto_mask(lab, box, "lighter", d, feature="auto")
    assert rn.compare_masks(by_l, nail)["iou"] < 0.8              # lightness splits the nail by its own shading
    assert d[0]["feature"] == "chroma" and not d[0]["inspect"]
    assert rn.compare_masks(auto, nail)["iou"] > 0.9


def test_auto_feature_still_works_on_the_plain_synthetic_hand():
    src, truth, boxes = synthetic_hand()
    d = []
    mask = rn.auto_mask(rn.srgb_to_lab(src), boxes, "lighter", d, feature="auto")
    assert all(not x["inspect"] for x in d), d
    assert rn.compare_masks(mask, truth)["iou"] > 0.95
