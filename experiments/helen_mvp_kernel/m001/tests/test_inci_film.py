"""INCI label and film on the synthetic hand (no client image, no fonts needed: falls back to Pillow's font)."""
import json
import pathlib
import sys

import numpy as np
import pytest
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "inci")]
import inci_film as inci  # noqa: E402
from test_recolor_nails import synthetic_hand  # noqa: E402


@pytest.fixture()
def spec(tmp_path):
    src, truth, _ = synthetic_hand()
    Image.fromarray(src).save(tmp_path / "hand.png")
    Image.fromarray((truth * 255).astype(np.uint8)).save(tmp_path / "mask.png")
    s = {"image": str(tmp_path / "hand.png"), "mask": str(tmp_path / "mask.png"), "status": "Test",
         "source": "main synthétique", "source_ref": "synthetic_hand()", "mask_provenance": "masque exact (synthétique)",
         "shades": [{"name": "Corail", "hex": "#E2483B"}, {"name": "Pistache", "hex": "#C8D8A0"}]}
    (tmp_path / "spec.json").write_text(json.dumps(s))
    return tmp_path


def test_labels_and_receipt(spec):
    rec = inci.main([str(spec / "spec.json"), "--fonts", str(spec / "nofonts"), "--out", str(spec / "out"), "--no-film"])
    assert rec["authority"] is False and len(rec["shades"]) == 2
    for s in rec["shades"]:
        assert s["measures"]["pixels_changed_outside_mask"] == 0
        assert Image.open(spec / "out" / s["label"]).size == (1080, 1350)
    src = np.asarray(Image.open(spec / "hand.png")).astype(int)
    out = np.asarray(Image.open(spec / "out" / "shade_01.png")).astype(int)
    zone = inci.rn.feather(np.asarray(Image.open(spec / "mask.png")) > 127, 1) > 0
    assert np.array_equal(out[~zone], src[~zone])                     # saved shade: identical outside nails + ring


def test_film_is_eight_seconds_and_never_draws_on_the_photo(spec):
    inci._FONTS["dir"] = spec / "nofonts"
    s = json.loads((spec / "spec.json").read_text())
    src, mask, shades = inci.prepare(s)
    crop = inci.square_crop(mask, src.shape[:2])
    frames = inci.film_frames(s, src, mask, shades, crop)
    assert len(frames) == 8 * inci.FPS and all(f.size == (inci.W, inci.H) for f in frames)
    photo = np.asarray(frames[5])[inci.IMG_Y:inci.IMG_Y + inci.IMG_S]          # original segment, photo area only
    assert np.array_equal(photo, np.asarray(inci.crop_view(src, crop)))


def test_refuses_output_inside_the_repository(spec):
    with pytest.raises(SystemExit):
        inci.main([str(spec / "spec.json"), "--fonts", "x", "--out", str(HERE / "should_not_exist"), "--no-film"])
    assert not (HERE / "should_not_exist").exists()
