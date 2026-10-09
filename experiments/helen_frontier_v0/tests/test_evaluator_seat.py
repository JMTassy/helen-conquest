"""Evaluator seat: plumbing, fail-closed parsing, blindness, receipt partitions. No model was called; nothing here is a
result about any provider."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG / "evaluator"))
import contract as c  # noqa: E402
import compare_to_oracles as cmp  # noqa: E402

BLIND_V1 = PKG / "swarm_v0" / "inputs" / "fixtures_blind_v1.json"


@pytest.mark.parametrize("text,expected", [
    ('{"outcome":"HOLD","state_transition":false,"reason":"x","laws_applied":["L1"]}', "HOLD"),
    ('prose before {"outcome":"ADMIT","state_transition":true,"reason":"y"} prose after', "ADMIT"),
    ('{"outcome":"ADMITTED","state_transition":false}', c.UNPARSEABLE),          # not in vocabulary
    ('{"outcome":"HOLD","state_transition":"false"}', c.UNPARSEABLE),            # string bool
    ('{"outcome":"HOLD","state_transition":true}', c.UNPARSEABLE),               # transition without ADMIT
    ("I think it should be rejected.", c.UNPARSEABLE),
    ("", c.UNPARSEABLE),
])
def test_parse_is_fail_closed(text, expected):
    assert c.parse_reply(text)["outcome"] == expected


def test_null_adapter_run_is_plumbing_only(tmp_path):
    po, pr = c.run_blind_evaluation(c.NullAdapter(), BLIND_V1, tmp_path, seat="TEST_NULL")
    out, rec = json.loads(po.read_text()), json.loads(pr.read_text())
    assert out["schema"] == "BLIND_OUTCOMES_V0" and len(out["outcomes"]) == 13
    assert all(o["outcome"] == c.UNPARSEABLE for o in out["outcomes"])
    assert rec["observed"]["unparseable"] == 13 and rec["observed"]["hosts_contacted"] == []
    assert rec["route_diversity"]["provider_differs"] is False


def test_scripted_adapter_produces_g1_shaped_outcomes(tmp_path):
    reply = '{"outcome":"HOLD","state_transition":false,"reason":"scripted","laws_applied":["N1"]}'
    po, pr = c.run_blind_evaluation(c.CallableAdapter(lambda _: reply), BLIND_V1, tmp_path, seat="TEST_SCRIPTED")
    out = json.loads(po.read_text())
    assert {o["id"] for o in out["outcomes"]} == {"F1", "F2", "F3", "F4a", "F4b", "F5a", "F5b", "F5c", "F6", "F7a", "F7b", "F8", "F9"}
    assert set(out["outcomes"][0]) == {"id", "outcome", "state_transition", "reason", "laws_applied"}


def test_receipt_partitions_never_merge(tmp_path):
    _, pr = c.run_blind_evaluation(c.NullAdapter(), BLIND_V1, tmp_path)
    rec = json.loads(pr.read_text())
    assert set(rec) >= {"asserted", "observed", "unverifiable", "route_diversity"}
    assert "model_configured" in rec["asserted"] and "model_configured" not in rec["observed"]
    assert rec["unverifiable"]["runtime_weight_identity"].startswith("UNVERIFIED")
    assert rec["unverifiable"]["lineage_independence_from_oracle_author"] == "UNRESOLVED"
    assert rec["authority"] is False and rec["ledger_effect"] == "none"


def test_evaluator_refuses_non_blind_input(tmp_path):
    with pytest.raises(AssertionError):
        c.run_blind_evaluation(c.NullAdapter(), PKG / "fixtures" / "jester_riemann_fixtures_v1.json", tmp_path)


def test_evaluator_code_never_names_the_oracle_file():
    src = (PKG / "evaluator" / "contract.py").read_text() + (PKG / "evaluator" / "run_blind_eval.py").read_text()
    assert "jester_riemann_fixtures_v1.json" not in src and "jester_riemann_fixtures_v0.json" not in src
    assert '"expected"' in src  # only as the guard that refuses non-blind input


def test_openai_binding_reports_precondition_instead_of_mocking(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    ad = c.ResponsesAPIAdapter()
    assert ad.preconditions()["api_key_present"] is False
    with pytest.raises(RuntimeError, match="precondition failed"):
        ad.generate([{"role": "user", "content": "x"}])


def test_provider_difference_is_route_diversity_not_independence(tmp_path):
    reply = '{"outcome":"HOLD","state_transition":false,"reason":"r"}'
    ad = c.CallableAdapter(lambda _: reply, provider="openai-compatible", model="scripted")
    _, pr = c.run_blind_evaluation(ad, BLIND_V1, tmp_path)
    rd = json.loads(pr.read_text())["route_diversity"]
    assert rd["provider_differs"] is True and "not an independent witness" in rd["meaning"]


def test_comparison_runs_after_and_flags_mismatches(tmp_path):
    reply = '{"outcome":"HOLD","state_transition":false,"reason":"all hold"}'
    po, _ = c.run_blind_evaluation(c.CallableAdapter(lambda _: reply), BLIND_V1, tmp_path)
    rep = cmp.compare(json.loads(po.read_text()), json.loads(cmp.V1.read_text()))
    assert rep["n"] == 13 and 0 < rep["matches"] < 13      # an always-HOLD evaluator matches only the HOLD oracles
    assert "adjudicate" in rep["interpretation"]
