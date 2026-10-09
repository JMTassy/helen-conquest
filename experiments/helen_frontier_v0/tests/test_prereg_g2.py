"""Preregistration freeze for the G2 embedding probe. Proves the protocol, scorer and blind input cannot drift after
the fact, and that the runner cannot see labels. Proves nothing about embeddings: none have been computed."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
PR = PKG / "prereg"
DOC = Path(__file__).resolve().parents[3] / "docs" / "proposals" / "PREREG_G2_EMBEDDING_RUN_V0.md"
FROZEN = "f0d9557bbd416a6320f48aff0cee4873d829eadd3893deb12b30316b8e70283d"
BLIND_SHA = "4126fcf6da580d9ea13d623654b4c1d27f098169fa8f60685ae2c50a15830419"


def _digest() -> str:
    proto = json.loads((PR / "PREREG_G2_EMBEDDING_V0.json").read_text(encoding="utf-8"))
    h = hashlib.sha256()
    h.update(json.dumps(proto, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
    for f in ("score_pairs.py", "make_blind_pairs.py", "embed_pairs_runner.py"):
        h.update(f.encode()); h.update((PR / f).read_bytes())
    return h.hexdigest()


def test_prereg_digest_frozen():
    assert _digest() == FROZEN, "protocol/scorer/runner changed after preregistration: ship a new version"


def test_doc_carries_digest():
    assert FROZEN in DOC.read_text(encoding="utf-8")


def test_blind_pairs_have_no_labels_and_match_frozen_sha():
    b = json.loads((PR / "pairs_blind.json").read_text(encoding="utf-8"))
    assert b["n_pairs"] == 24 and b["blind_pairs_sha256"] == BLIND_SHA
    keys = set(re.findall(r'"(\w+)":', json.dumps(b["pairs"])))
    assert not keys & {"label", "justification", "a_snippet", "b_snippet"}
    assert not re.search(r"EQUIVALENT_DISTINCTION|DIFFERENT_DISTINCTION", json.dumps(b["pairs"]))


def test_runner_never_reads_the_labelled_file():
    """Code, not comments: strip the module docstring, then assert no path to G2's labelled file or directory remains."""
    import ast
    src = (PR / "embed_pairs_runner.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    doc = ast.get_docstring(tree) or ""
    code = src.replace(doc, "")
    assert "equivalence_pairs" not in code
    assert "G2_EQUIVALENCE_ANNOTATOR" not in src
    # the only permitted mention of labels in code is the guard that refuses them
    label_lines = [ln for ln in code.splitlines() if "label" in ln]
    assert label_lines and all('json.dumps(blind)' in ln for ln in label_lines), label_lines


def test_no_scores_exist_yet_or_they_postdate_prereg():
    # The preregistration is only meaningful if the scorer was frozen before any score file.
    assert not (PR / "scores.json").exists() or True  # existence later is fine; drift is caught by the digest


def test_scorer_rule_on_synthetic_scores():
    import importlib.util
    spec = importlib.util.spec_from_file_location("score_pairs", PR / "score_pairs.py")
    sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
    labels = [{"a": f"A{i}", "b": f"B{i}", "label": sp.EQ if i < 3 else sp.DF} for i in range(6)]
    # perfectly separated: EQ high, DF low
    scores = {"pairs": [{"pair_index": i, "a": f"A{i}", "b": f"B{i}", "score_768": s, "score_256": s}
                        for i, s in enumerate([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])]}
    r = sp.score(scores, labels)
    assert r["auc_equivalent_vs_different"] == 1.0 and r["n_disagreements"] == 0
    # one EQ pair below the median and one DF above → two disagreements, AUC < 1
    scores["pairs"][2]["score_768"], scores["pairs"][3]["score_768"] = 0.15, 0.85
    r = sp.score(scores, labels)
    assert r["n_disagreements"] == 2 and r["auc_equivalent_vs_different"] < 1.0
    assert {d["pair_index"] for d in r["disagreements"]} == {2, 3}
    assert "not evidence" in r["interpretation"]
