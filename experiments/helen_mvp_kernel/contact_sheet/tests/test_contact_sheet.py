import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import contact_sheet as cs  # noqa: E402


def checker(w, h, cell=8):
    y, x = np.mgrid[0:h, 0:w]
    return Image.fromarray((((x // cell + y // cell) % 2) * 255).astype(np.uint8)).convert("RGB")


@pytest.fixture
def folder(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    sharp = checker(1600, 1200)
    sharp.save(d / "a_sharp.jpg", quality=85)
    sharp.filter(ImageFilter.GaussianBlur(6)).save(d / "b_blurry.jpg", quality=85)
    checker(640, 480).save(d / "c_small.jpg", quality=60)
    shutil.copy(d / "a_sharp.jpg", d / "a_sharp (1).jpg")      # exact duplicate, like the e-mail's "(1)"
    (d / "notes.txt").write_text("ignored")
    return d


def test_measures_gates_duplicates_and_candidates(folder, tmp_path):
    r = cs.main([str(folder), "--out", str(tmp_path / "out")])
    by = {i["file"]: i for i in r["images"]}
    assert (by["a_sharp.jpg"]["width"], by["a_sharp.jpg"]["height"]) == (1600, 1200)
    assert abs(by["a_sharp.jpg"]["jpeg_quality_est"] - 85) <= 2
    assert abs(by["c_small.jpg"]["jpeg_quality_est"] - 60) <= 2
    assert by["a_sharp.jpg"]["sharpness_global"] > 10 * by["b_blurry.jpg"]["sharpness_global"]
    assert "a_sharp (1).jpg" in by["a_sharp.jpg"]["duplicates"]
    # the small image fails the 1080 px gate; the duplicate is not counted twice
    assert r["candidates"][0] in ("a_sharp.jpg", "a_sharp (1).jpg")
    assert "c_small.jpg" not in r["candidates"] and "b_blurry.jpg" not in r["candidates"]
    assert len([c for c in r["candidates"] if c.startswith("a_sharp")]) == 1
    assert (tmp_path / "out/contact_sheet.jpg").exists() and "Candidates" in (tmp_path / "out/report.md").read_text()


def test_roi_drives_nail_sharpness_and_size_gate(folder, tmp_path):
    roi = tmp_path / "roi.json"
    roi.write_text(json.dumps({"a_sharp.jpg": [100, 100, 300, 300], "b_blurry.jpg": [100, 100, 600, 600]}))
    r = cs.main([str(folder), "--out", str(tmp_path / "o2"), "--roi", str(roi), "--min-roi-short-side", "400"])
    by = {i["file"]: i for i in r["images"]}
    assert by["a_sharp.jpg"]["roi_short_side_px"] == 300 and not by["a_sharp.jpg"]["passes_gates"]  # nail too small
    assert by["b_blurry.jpg"]["sharpness_roi"] < by["a_sharp.jpg"]["sharpness_roi"]


def test_no_candidate_means_ask_for_hd(tmp_path):
    d = tmp_path / "s"
    d.mkdir()
    checker(800, 600).save(d / "x.jpg", quality=80)
    r = cs.main([str(d), "--out", str(tmp_path / "o")])
    assert r["candidates"] == [] and "HD originals" in r["verdict"]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_still_is_matched_to_its_source_video(tmp_path):
    d = tmp_path / "v"
    d.mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=4:size=1280x720:rate=25",
                    "-pix_fmt", "yuv420p", str(d / "clip.mov")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-ss", "2", "-i", str(d / "clip.mov"), "-frames:v", "1",
                    str(d / "Still_from_clip.jpg")], check=True)
    r = cs.main([str(d), "--out", str(tmp_path / "o"), "--fps", "1"])
    assert r["videos"][0]["width"] == 1280 and r["videos"][0]["duration_s"] == 4.0
    nv = r["images"][0]["nearest_video_frame"]
    assert nv["frame"].startswith("clip_") and nv["ahash_distance"] <= 5


def test_same_framing_different_shade_is_not_a_duplicate(tmp_path):
    """M001 case: same nail framing, two polish shades. They must stay two images."""
    d = tmp_path / "shades"
    d.mkdir()
    base = np.asarray(checker(1600, 1200)).copy()
    red, green = base.copy(), base.copy()
    # two shades with the same luminance (~101): a grey-level hash cannot tell them apart
    red[400:800, 600:1000] = (200, 60, 60)
    green[400:800, 600:1000] = (40, 140, 60)
    Image.fromarray(red).save(d / "nail_red.jpg", quality=92)
    Image.fromarray(green).save(d / "nail_green.jpg", quality=92)
    r = cs.main([str(d), "--out", str(tmp_path / "o")])
    assert all("duplicates" not in i for i in r["images"])
    assert set(r["candidates"]) == {"nail_red.jpg", "nail_green.jpg"}


def test_noise_does_not_win_sharpness():
    rng = np.random.default_rng(0)
    flat_noisy = 128 + rng.normal(0, 6, (400, 400))
    edges = np.asarray(checker(400, 400, cell=40).convert("L"), dtype=np.float64)
    assert cs.laplacian_var(edges) > cs.laplacian_var(flat_noisy)
