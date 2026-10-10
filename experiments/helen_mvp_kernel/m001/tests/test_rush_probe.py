"""Rush probe on synthetic clips made by ffmpeg (no client footage)."""
import json
import pathlib
import shutil
import subprocess
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rushes"))
import rush_probe as rp  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


@pytest.fixture(scope="module")
def clips(tmp_path_factory):
    d = tmp_path_factory.mktemp("rushes")
    ff("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25:duration=2", "-f", "lavfi", "-i", "sine=duration=2",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(d / "V1-0001_land.mov"))
    ff("-display_rotation", "90", "-i", str(d / "V1-0001_land.mov"), "-c", "copy", str(d / "V1-0002_rot.mp4"))
    ff("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25:duration=2", "-vf", "gblur=sigma=6",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(d / "V1-0003_soft.mov"))
    (d / "notes.txt").write_text("not a video")
    return d


def test_metadata_rotation_audio_and_sheets(clips, tmp_path):
    rows = {r["file"]: r for r in rp.run(clips, tmp_path / "out", k=4)}
    assert set(rows) == {"V1-0001_land.mov", "V1-0002_rot.mp4", "V1-0003_soft.mov"}   # txt ignored
    land, rot, soft = rows["V1-0001_land.mov"], rows["V1-0002_rot.mp4"], rows["V1-0003_soft.mov"]
    assert land["display_size"] == "320x240" and land["orientation"] == "landscape" and land["audio"]
    assert abs(land["duration_s"] - 2.0) < 0.1 and land["fps"] == 25 and land["hdr"] in {"SDR", "unknown"}
    assert rot["coded_size"] == "320x240" and rot["display_size"] == "240x320" and rot["orientation"] == "portrait"
    assert not soft["audio"] and land["frames_sampled"] == 4
    assert soft["sharpness_max"] < land["sharpness_max"] / 3          # the blurred clip scores lower
    for stem in ("V1-0001_land", "V1-0002_rot", "V1-0003_soft"):
        assert (tmp_path / "out" / f"{stem}_sheet.png").exists()
    assert (tmp_path / "out" / "triage_01.png").exists() and (tmp_path / "out" / "rushes.csv").exists()
    meta = json.loads((tmp_path / "out" / "rushes.json").read_text())
    assert meta["authority"] is False and len(meta["clips"]) == 3


def test_frames_are_display_oriented(clips):
    f = rp.grab(clips / "V1-0002_rot.mp4", 1.0, width=240)
    assert f.shape[0] > f.shape[1]                                      # portrait after rotation


def test_sharpness_orders_detail():
    rng = np.random.default_rng(0)
    sharp = (rng.uniform(0, 255, (64, 64, 3))).astype(np.uint8)
    flat = np.full((64, 64, 3), 128, np.uint8)
    assert rp.sharpness(sharp) > rp.sharpness(flat) == 0


def test_refuses_output_inside_a_repository(clips):
    inside = pathlib.Path(__file__).resolve().parent / "should_not_exist"
    with pytest.raises(SystemExit):
        rp.main([str(clips), "--out", str(inside)])
    assert not inside.exists()
