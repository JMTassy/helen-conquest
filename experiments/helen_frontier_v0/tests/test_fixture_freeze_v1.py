"""Fixture freeze V1: oracles cannot drift; V0 stays frozen beside it; blind export leaks no outcome."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
V1 = PKG / "fixtures" / "jester_riemann_fixtures_v1.json"
V0 = PKG / "fixtures" / "jester_riemann_fixtures_v0.json"
BLIND = PKG / "swarm_v0" / "inputs" / "fixtures_blind_v1.json"
DOC = REPO / "docs" / "proposals" / "HELEN_JESTER_RIEMANN_FIXTURES_V1.md"
FROZEN_V1 = "5c2bdcfd981e79122463cffe95283dc10d513fe7735fd179867aad8e24b4eb7e"
FROZEN_V0 = "05bf8cd6093c01aa88264ae2173d033b45a64b0bd066b1ca434b488412c93a6c"


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _oracles(fx):
    for f in fx["fixtures"]:
        for v in (f.get("variants") or [f]):
            yield v["id"], v["expected"]


def test_v1_digest_frozen():
    assert _digest(_load(V1)) == FROZEN_V1


def test_v0_still_frozen_and_referenced():
    v1 = _load(V1)
    assert _digest(_load(V0)) == FROZEN_V0
    assert v1["supersedes"]["digest"] == "sha256:" + FROZEN_V0
    assert v1["supersedes"]["kept_untouched"] is True


def test_doc_carries_digests():
    t = DOC.read_text(encoding="utf-8")
    assert f"sha256:{FROZEN_V1}" in t and FROZEN_V0 in t


def test_thirteen_oracles_in_vocabulary_and_only_admit_transitions():
    fx = _load(V1)
    vocab = set(fx["outcome_vocabulary"])
    ids = [i for i, _ in _oracles(fx)]
    assert len(ids) == 13 and len(set(ids)) == 13
    for i, e in _oracles(fx):
        assert e["outcome"] in vocab, i
        assert e["state_transition"] is False or e["outcome"] == "ADMIT", i


def test_f7_split_and_threshold_declared():
    fx = _load(V1)
    f7 = next(f for f in fx["fixtures"] if f["id"] == "F7")
    ids = {v["id"]: v for v in f7["variants"]}
    assert ids["F7a"]["expected"]["outcome"] == "REJECT" and ids["F7b"]["expected"]["outcome"] == "HOLD"
    assert ids["F7a"]["given"]["recovery_threshold"] == 0.70 and ids["F7a"]["given"]["sham_run"]["present"] is True


def test_null_semantics_law_present():
    laws = _load(V1)["laws"]
    assert any(l["id"] == "N1" for l in laws["ADDED"])
    assert "other than the proposer" in next(l["text"] for l in laws["KEEP"] if l["id"] == "L2")
    assert "governed state" in next(l["text"] for l in laws["KEEP"] if l["id"] == "L3")


def test_blind_export_has_no_outcome_words_or_hints():
    b = _load(BLIND)
    fx_txt = json.dumps(b["fixtures"], ensure_ascii=False)
    assert not re.findall(r"\b(ADMIT|HOLD|REJECT|NO_TRANSITION)\b", fx_txt)
    for f in b["fixtures"]:
        assert set(f) <= {"id", "domain", "given", "claim_under_test", "variants"}, f["id"]
        for v in f.get("variants", []):
            assert set(v) == {"id", "given", "claim_under_test"}, v["id"]


def test_no_non_palette_glyph():
    assert "\U0001F7E6" not in V1.read_text(encoding="utf-8")  # 🟦 is not in the CLAUDE.md palette
