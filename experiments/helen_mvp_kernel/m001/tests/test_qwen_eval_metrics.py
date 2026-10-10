"""Measurement side of qwen_eval/qwen_turbo_eval.py, exercised with fake edits (no GPU, no model, no download)."""
import json
import pathlib
import sys

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "qwen_eval"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import qwen_turbo_eval as qe  # noqa: E402
import recolor_nails as rn  # noqa: E402
from test_recolor_nails import CORAL, synthetic_hand  # noqa: E402


def test_preset_follows_source_aspect():
    assert qe.preset_for(720, 1280) == ("9:16", (1536, 2752))
    assert qe.preset_for(2993, 4724)[0] == "2:3"
    assert qe.preset_for(1000, 1000)[0] == "1:1"


def test_baseline_measures_zero_outside_the_band():
    src, truth, _ = synthetic_hand()
    tl = rn.hex_to_lab(CORAL)
    out, _, _ = rn.recolour(src, truth, tl)
    m = qe.evaluate(src, out, truth, tl)
    assert m["outside_mask_excluding_3px_band"]["mean"] == 0 and m["outside_mask_excluding_3px_band"]["share_above_jnd"] == 0
    assert m["global_shift_px"] == (0, 0)
    assert m["nail_body"]["mean_chroma_error_nail_body"] < 1


def regenerated(src, truth, tl, shift=(2, 3), tint=4.0, seed=0):
    """A fake 're-rendered' edit: correct nail colour, but the whole frame moves and drifts in colour."""
    out, _, _ = rn.recolour(src, truth, tl)
    rng = np.random.default_rng(seed)
    out = np.roll(out.astype(np.float64), shift, axis=(0, 1)) + np.array([tint, 0, -tint]) + rng.normal(0, 2, out.shape)
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def test_regenerated_frame_is_caught_outside_the_nail():
    src, truth, _ = synthetic_hand()
    tl = rn.hex_to_lab(CORAL)
    m = qe.evaluate(src, regenerated(src, truth, tl), truth, tl)
    assert m["global_shift_px"] == (2, 3)
    assert m["outside_mask_excluding_3px_band"]["share_above_jnd"] > 0.3
    assert m["pixels_identical_outside_mask"] < 0.05


def test_resize_floor_is_small_but_not_zero():
    src, truth, _ = synthetic_hand()
    tl = rn.hex_to_lab(CORAL)
    f = qe.evaluate(src, qe.resize_floor(src, (1536, 2752)), truth, tl)["outside_mask_excluding_3px_band"]
    assert 0 < f["mean"] < 3


def _write_case(tmp_path):
    src, truth, _ = synthetic_hand()
    Image.fromarray(src).save(tmp_path / "hand.png")
    Image.fromarray((truth * 255).astype(np.uint8)).save(tmp_path / "mask.png")
    return src, truth


def test_run_with_fake_edit_writes_report_and_sheet(tmp_path):
    src, truth = _write_case(tmp_path)
    tl = rn.hex_to_lab(CORAL)
    fake = lambda rgb, s: regenerated(rgb, truth, tl, seed=s)  # noqa: E731
    rep = qe.main([str(tmp_path / "hand.png"), "--mask", str(tmp_path / "mask.png"), "--target", f"coral_approx={CORAL}",
                   "--source-kind", "synthetic", "--accept-research-license", "--seeds", "0", "1",
                   "--out", str(tmp_path / "run")], edit_fn=fake)
    assert rep["authority"] is False and "non-commercial" in rep["licence"]
    assert [r["seed"] for r in rep["runs"]] == [0, 1]
    assert json.loads((tmp_path / "run" / "report.json").read_text())["source"]["kind"] == "synthetic"
    assert (tmp_path / "run" / "qwen_eval_sheet.png").exists()


@pytest.mark.parametrize("extra", [[], ["--source-kind", "client"]])
def test_refusals_happen_before_any_model_code(tmp_path, extra):
    _write_case(tmp_path)
    base = [str(tmp_path / "hand.png"), "--mask", str(tmp_path / "mask.png"), "--target", f"c={CORAL}", "--out", str(tmp_path / "r")]
    with pytest.raises(SystemExit):
        if extra:                                   # client photo without --allow-client-image
            qe.main(base + extra + ["--accept-research-license"], edit_fn=lambda rgb, s: rgb)
        else:                                       # licence not acknowledged
            qe.main(base + ["--source-kind", "synthetic"], edit_fn=lambda rgb, s: rgb)
    assert not (tmp_path / "r" / "report.json").exists()


def test_quantized_run_is_labelled_and_preflight_names_bitsandbytes(tmp_path):
    src, truth = _write_case(tmp_path)
    rep = qe.main([str(tmp_path / "hand.png"), "--mask", str(tmp_path / "mask.png"), "--target", f"c={CORAL}",
                   "--source-kind", "synthetic", "--accept-research-license", "--seeds", "0", "--quantize", "nf4",
                   "--out", str(tmp_path / "q")], edit_fn=lambda rgb, s: rgb)
    assert rep["model"]["quantize"] == "nf4" and rep["model"]["label"].startswith("Turbo 4-bit")
    info = qe.preflight("nf4")
    assert info["quantize"] == "nf4" and ("bitsandbytes" in info or any("bitsandbytes" in p for p in info["problems"]))
    assert rep["model"]["vae_tiling"] is True and rep["run_status"] == "complete: 1 of 1 seeds"


def test_interrupted_run_keeps_the_seeds_it_finished(tmp_path):
    """HAL-WITNESS run 1 was stopped during seed 1 and left no report: the report now follows every seed."""
    _write_case(tmp_path)

    def stops_on_seed_1(rgb, s):
        if s == 1:
            raise KeyboardInterrupt  # stands in for the external SIGTERM
        return rgb

    with pytest.raises(KeyboardInterrupt):
        qe.main([str(tmp_path / "hand.png"), "--mask", str(tmp_path / "mask.png"), "--target", f"c={CORAL}",
                 "--source-kind", "synthetic", "--accept-research-license", "--seeds", "0", "1", "2",
                 "--out", str(tmp_path / "cut")], edit_fn=stops_on_seed_1)
    rep = json.loads((tmp_path / "cut" / "report.json").read_text())
    assert [r["seed"] for r in rep["runs"]] == [0] and rep["run_status"] == "in progress: 1 of 3 seeds done"


def test_one_process_per_seed_keeps_every_seed(tmp_path):
    """HAL-WITNESS ran seeds as separate processes after the OOM kill: a rerun must add, never overwrite."""
    _write_case(tmp_path)
    base = [str(tmp_path / "hand.png"), "--mask", str(tmp_path / "mask.png"), "--target", f"c={CORAL}",
            "--source-kind", "synthetic", "--accept-research-license", "--out", str(tmp_path / "p")]
    qe.main(base + ["--seeds", "0"], edit_fn=lambda rgb, s: rgb)
    with pytest.raises(SystemExit):                                   # plain rerun would wipe seed 0: refused
        qe.main(base + ["--seeds", "1"], edit_fn=lambda rgb, s: rgb)
    rep = qe.main(base + ["--seeds", "1", "2", "--resume"], edit_fn=lambda rgb, s: rgb)
    assert [r["seed"] for r in rep["runs"]] == [0, 1, 2] and rep["run_status"] == "complete: 3 of 3 seeds"
    with pytest.raises(SystemExit):                                   # another target cannot join this report
        qe.main([a if a != f"c={CORAL}" else "c=#00FF00" for a in base] + ["--seeds", "3", "--resume"],
                edit_fn=lambda rgb, s: rgb)
