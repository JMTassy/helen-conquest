import io
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
    """Grey 30/220 checkerboard: high contrast without pure black or pure white."""
    y, x = np.mgrid[0:h, 0:w]
    return Image.fromarray((30 + ((x // cell + y // cell) % 2) * 190).astype(np.uint8)).convert("RGB")


def run(folder, out, *extra):
    return cs.main([str(folder), "--out", str(out), *extra])


def by_file(r):
    return {i["file"]: i for i in r["images"]}


@pytest.fixture
def folder(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    sharp = checker(1600, 1200)
    sharp.save(d / "a_sharp.jpg", quality=85)
    sharp.filter(ImageFilter.GaussianBlur(6)).save(d / "b_blurry.jpg", quality=85)
    checker(640, 480).save(d / "c_small.jpg", quality=60)
    shutil.copy(d / "a_sharp.jpg", d / "a_sharp (1).jpg")      # exact file copy, like the e-mail's "(1)"
    (d / "notes.txt").write_text("ignored")
    return d


def test_measures_and_candidates(folder, tmp_path):
    r = run(folder, tmp_path / "out")
    b = by_file(r)
    assert (b["a_sharp.jpg"]["width"], b["a_sharp.jpg"]["height"]) == (1600, 1200)
    assert abs(b["a_sharp.jpg"]["compression_index_jpeg_q"] - 85) <= 2
    assert abs(b["c_small.jpg"]["compression_index_jpeg_q"] - 60) <= 2
    assert b["a_sharp.jpg"]["sharpness_global"] > 10 * b["b_blurry.jpg"]["sharpness_global"]
    pair = [b["a_sharp.jpg"], b["a_sharp (1).jpg"]]
    dups = [i for i in pair if "exact_duplicate_of" in i]
    assert len(dups) == 1 and dups[0]["exact_duplicate_kind"] == "file"
    assert len(r["candidates"]) == 1 and r["candidates"][0].startswith("a_sharp")  # blurry and small rejected, copy excluded
    assert any("short side" in x for x in b["c_small.jpg"]["rejection_reasons"])
    assert any("heuristic" in x for x in b["b_blurry.jpg"]["rejection_reasons"])
    assert b["a_sharp.jpg"]["sharpness_nail"] == "not evaluated"
    assert (tmp_path / "out/contact_sheet.jpg").exists() and "Verdict" in (tmp_path / "out/report.md").read_text()


# --- the three targeted cases ------------------------------------------------------------

def test_case1_same_framing_two_polish_colours_are_two_variants(tmp_path):
    """Same framing, two shades of EQUAL luminance: a grey-level hash cannot tell them apart."""
    d = tmp_path / "shades"
    d.mkdir()
    base = np.asarray(checker(1600, 1200)).copy()
    red, green = base.copy(), base.copy()
    red[400:800, 600:1000] = (200, 60, 60)
    green[400:800, 600:1000] = (40, 140, 60)
    Image.fromarray(red).save(d / "nail_red.jpg", quality=92)
    Image.fromarray(green).save(d / "nail_green.jpg", quality=92)
    assert cs.hamming(cs.ahash(Image.fromarray(red)), cs.ahash(Image.fromarray(green))) <= cs.AHASH_NEAR  # the trap is real
    r = run(d, tmp_path / "o")
    b = by_file(r)
    assert all("exact_duplicate_of" not in i and "resembles" not in i for i in b.values())
    assert set(r["candidates"]) == {"nail_red.jpg", "nail_green.jpg"}


def test_case2_same_image_different_metadata_is_a_pixel_duplicate(tmp_path):
    d = tmp_path / "meta"
    d.mkdir()
    img = checker(1600, 1200)
    img.save(d / "orig.png")
    exif = Image.Exif()
    exif[305] = "Some Editor 1.0"
    exif[306] = "2025:05:17 23:14:58"
    img.save(d / "copy_with_exif.png", exif=exif)
    assert (d / "orig.png").read_bytes() != (d / "copy_with_exif.png").read_bytes()   # different files
    r = run(d, tmp_path / "o")
    b = by_file(r)
    dup = b["copy_with_exif.png"] if "exact_duplicate_of" in b["copy_with_exif.png"] else b["orig.png"]
    assert dup["exact_duplicate_kind"] == "pixels (metadata differ)"
    assert len(r["candidates"]) == 1


def low_contrast(w, h, cell=12, a=100, b=140):
    """Fine detail with little contrast, like nail texture: where noise can fake sharpness."""
    y, x = np.mgrid[0:h, 0:w]
    return Image.fromarray((a + ((x // cell + y // cell) % 2) * (b - a)).astype(np.uint8)).convert("RGB")


def test_case3_blurred_then_noised_or_recompressed_does_not_win(tmp_path):
    d = tmp_path / "noise"
    d.mkdir()
    sharp = low_contrast(1600, 1200)
    sharp.save(d / "sharp.png")
    blurred = sharp.filter(ImageFilter.GaussianBlur(4))
    noisy = np.clip(np.asarray(blurred, dtype=np.float64) + np.random.default_rng(1).normal(0, 15, (1200, 1600, 3)), 0, 255)
    Image.fromarray(noisy.astype(np.uint8)).save(d / "blur_noise.png")
    buf = io.BytesIO()
    blurred.save(buf, "JPEG", quality=10)
    Image.open(io.BytesIO(buf.getvalue())).save(d / "blur_recompressed.png")
    r = run(d, tmp_path / "o")
    b = by_file(r)
    for f in ("blur_noise.png", "blur_recompressed.png"):
        assert b[f]["sharpness_global"] < b["sharp.png"]["sharpness_global"], f
        assert f not in r["candidates"][:1]
    assert r["candidates"][0] == "sharp.png"
    assert b["blur_noise.png"]["noise_sigma_est"] > b["sharp.png"]["noise_sigma_est"]


def test_case3_without_denoise_noise_would_win(tmp_path, monkeypatch):
    """Proves case 3 tests the fix: with the raw Laplacian, the noisy blurred image beats the sharp one."""
    sharp = np.asarray(low_contrast(800, 600).convert("L"), dtype=np.float64)
    blurred = np.asarray(low_contrast(800, 600).filter(ImageFilter.GaussianBlur(4)).convert("L"), dtype=np.float64)
    noisy = blurred + np.random.default_rng(1).normal(0, 10, blurred.shape)  # ~ sigma 15 per RGB channel after luma
    assert cs.laplacian_var(sharp) > cs.laplacian_var(noisy)
    monkeypatch.setattr(cs, "denoise", lambda g: g)
    assert cs.laplacian_var(noisy) > cs.laplacian_var(sharp)


def test_heavy_noise_is_flagged_not_trusted(tmp_path):
    d = tmp_path / "heavy"
    d.mkdir()
    blurred = low_contrast(1600, 1200).filter(ImageFilter.GaussianBlur(4))
    noisy = np.clip(np.asarray(blurred, dtype=np.float64) + np.random.default_rng(2).normal(0, 25, (1200, 1600, 3)), 0, 255)
    Image.fromarray(noisy.astype(np.uint8)).save(d / "very_noisy.png")
    r = run(d, tmp_path / "o")
    i = r["images"][0]
    assert i["noise_sigma_est"] > cs.NOISY and "unreliable" in i["caution"]


# --- consolidated behaviours ---------------------------------------------------------------

def test_nail_box_metadata_require_nail_and_source(folder, tmp_path):
    meta = tmp_path / "metadata.json"
    meta.write_text(json.dumps({"a_sharp.jpg": {"nail_roi": [100, 100, 500, 500], "source": "e-mail 2025-05-18"},
                                "b_blurry.jpg": [100, 100, 300, 300]}))
    r = run(folder, tmp_path / "o", "--metadata", str(meta), "--require-nail")
    b = by_file(r)
    assert b["a_sharp.jpg"]["source"] == "e-mail 2025-05-18" and isinstance(b["a_sharp.jpg"]["sharpness_nail"], float)
    assert any("nail box 300px" in x for x in b["b_blurry.jpg"]["rejection_reasons"])
    assert r["candidates"] == ["a_sharp.jpg"]          # the copy has no nail box: --require-nail rejects it
    assert r["coverage"]["nail_boxes_given"] == 2


def test_no_candidate_wording(tmp_path):
    d = tmp_path / "s"
    d.mkdir()
    checker(800, 600).save(d / "x.jpg", quality=80)
    r = run(d, tmp_path / "o")
    assert r["candidates"] == [] and r["verdict"].startswith("no candidate according to these criteria")


def test_corrupted_file_is_listed_not_dropped(folder, tmp_path):
    (folder / "broken.jpg").write_bytes(b"\xff\xd8\xff\xe0 not really a jpeg")
    r = run(folder, tmp_path / "o")
    assert r["coverage"]["unreadable"] == ["broken.jpg"] and "broken.jpg" in (tmp_path / "o/report.md").read_text()


def test_blown_highlights_penalised_on_nail_only(tmp_path):
    d = tmp_path / "light"
    d.mkdir()
    img = np.asarray(checker(1600, 1200)).copy()
    img[:, :800] = 0                                    # black background: never penalised
    burnt = img.copy()
    burnt[400:800, 1000:1400] = 255                     # burnt nail
    Image.fromarray(img).save(d / "ok.png")
    Image.fromarray(burnt).save(d / "burnt_nail.png")
    meta = tmp_path / "m.json"
    meta.write_text(json.dumps({"ok.png": [1000, 400, 400, 400], "burnt_nail.png": [1000, 400, 400, 400]}))
    r = run(d, tmp_path / "o", "--metadata", str(meta))
    b = by_file(r)
    assert b["ok.png"]["deep_shadows"] > 0.4 and "ok.png" in r["candidates"]
    assert any("blown highlights on the nail" in x for x in b["burnt_nail.png"]["rejection_reasons"])


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_still_matched_to_video_with_timestamp(tmp_path):
    d = tmp_path / "v"
    d.mkdir()
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=4:size=1280x720:rate=25",
                    "-pix_fmt", "yuv420p", str(d / "clip.mov")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-ss", "2", "-i", str(d / "clip.mov"), "-frames:v", "1",
                    str(d / "Still_from_clip.jpg")], check=True)
    r = run(d, tmp_path / "o", "--fps", "1")
    assert r["videos"][0]["width"] == 1280 and r["videos"][0]["duration_s"] == 4.0
    nv = r["images"][0]["nearest_video_frame"]
    assert nv["video"] == "clip.mov" and nv["distance"] <= 5 and nv["t_s"] in (1.0, 2.0, 3.0)
    assert "not proof" in nv["meaning"]


def test_noise_does_not_win_sharpness():
    rng = np.random.default_rng(0)
    flat_noisy = 128 + rng.normal(0, 6, (400, 400))
    edges = np.asarray(checker(400, 400, cell=40).convert("L"), dtype=np.float64)
    assert cs.laplacian_var(edges) > cs.laplacian_var(flat_noisy)
