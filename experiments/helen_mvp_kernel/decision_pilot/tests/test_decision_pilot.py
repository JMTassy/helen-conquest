"""No-GPU parts of the decision pilot: synthetic data, split, baselines, metrics, refusals."""
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import decision_pilot as dp  # noqa: E402


def test_synth_is_deterministic_and_in_build_dataset_shape():
    a, b = dp.synth_rows(200, seed=1), dp.synth_rows(200, seed=1)
    assert a == b and len(a) == 200
    for r in a:
        assert set(r) == {"id", "state", "questions", "gold"} and isinstance(r["state"], str)
        assert set(r["gold"]) == set(r["questions"]) == {"motif", "remboursement", "urgence"}
        assert r["gold"]["motif"] in r["questions"]["motif"]["criteria"]
        assert isinstance(r["gold"]["remboursement"], bool)
        assert 0 <= r["gold"]["urgence"] < len(r["questions"]["urgence"]["criteria"])
    assert all(r["gold"]["urgence"] == 2 for r in a if r["gold"]["motif"] == "reaction_cutanee")


def test_split_is_stable_and_disjoint():
    rows = dp.synth_rows(500)
    tr, te = dp.split(rows)
    assert not {r["id"] for r in tr} & {r["id"] for r in te}
    assert 0.12 < len(te) / len(rows) < 0.28
    assert dp.split(rows) == (tr, te)


def test_ece_known_values():
    assert dp.ece([1.0, 1.0], [1, 1]) == 0                     # sure and right
    assert dp.ece([0.9] * 10, [1] * 9 + [0]) == 0                # 90 % sure, right 9 times in 10
    assert dp.ece([0.9] * 10, [1] * 5 + [0] * 5) == 0.4          # overconfident by 40 points


def test_coverage_counts_what_could_be_proposed_automatically():
    cov = dp.coverage([0.95, 0.85, 0.65, 0.55], [1, 1, 0, 0])
    assert cov["0.9"] == {"share_auto": 0.25, "accuracy_auto": 1.0}
    assert cov["0.6"] == {"share_auto": 0.75, "accuracy_auto": 0.667}


def test_baselines_run_and_keywords_beat_majority_on_motif():
    tr, te = dp.split(dp.synth_rows(600))
    res = dp.baselines(tr, te)
    assert res["keyword_rules"]["motif"]["accuracy"] > res["majority"]["motif"]["accuracy"]
    assert "ece" not in res["majority"]["motif"]                 # no confidences, no calibration claimed


def test_norm_gold_accepts_label_dicts_and_strings():
    assert dp.norm_gold("noul", "true") is True and dp.norm_gold("noul", False) is False
    assert dp.norm_gold("score", "2") == 2 and dp.norm_gold("choice", {"label": "billing"}) == "billing"


def test_cli_synth_and_baselines(tmp_path):
    out = tmp_path / "care.jsonl"
    dp.main(["synth", "--out", str(out), "--n", "120"])
    assert len(out.read_text(encoding="utf-8").splitlines()) == 120
    res = dp.main(["baselines", "--data", str(out)])
    assert {"majority", "keyword_rules"} <= set(res)


@pytest.mark.parametrize("argv", [["train", "--data", "x.jsonl", "--out", "o"],
                                  ["train", "--data", "x.jsonl", "--source-kind", "client", "--out", "o"]])
def test_refusals_happen_before_any_model_import(argv):
    with pytest.raises(SystemExit):
        dp.main(argv)
    assert "unsloth" not in sys.modules


def test_nothing_is_ever_uploaded():
    src = (HERE.parent / "decision_pilot.py").read_text(encoding="utf-8")
    assert "push_to_hub" not in src and "HF_TOKEN" not in src
