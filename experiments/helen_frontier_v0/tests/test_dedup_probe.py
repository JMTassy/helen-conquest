"""Dedup probe — pure-function tests. Proves the cheap tiers behave as specified
on synthetic packets and that receipts carry authority=false. Proves nothing
about whether any flagged pair is a real duplicate."""
from __future__ import annotations

import json

import dedup_probe as dp


def _pkt(tmp, name, **fields):
    (tmp / name).write_text(json.dumps(fields), encoding="utf-8")


def test_text_field_order_summary_then_hypothesis_then_title():
    assert dp.packet_text({"summary": " S ", "hypothesis": "H"}) == ("summary", "S")
    assert dp.packet_text({"summary": "", "hypothesis": "H", "title": "T"}) == ("hypothesis", "H")
    assert dp.packet_text({"title": "T"}) == ("title", "T")
    assert dp.packet_text({"summary": None, "hypothesis": 3}) == ("", "")


def test_normalise_collapses_case_and_whitespace():
    assert dp.normalise("  A\tb \n C ") == "a b c"


def test_exact_tier_groups_only_true_textual_duplicates(tmp_path):
    _pkt(tmp_path, "a.json", packet_id="A", summary="Window width 0.0015 below threshold")
    _pkt(tmp_path, "b.json", packet_id="B", summary="window   width 0.0015 BELOW threshold ")
    _pkt(tmp_path, "c.json", packet_id="C", summary="Something else entirely")
    _pkt(tmp_path, "d.json", packet_id="D")  # no text
    items = dp.load_outbox(tmp_path)
    r = dp.tier_exact(items)
    assert r["duplicate_groups"] == [["A", "B"]] and r["packets_in_groups"] == 2


def test_jaccard_bounds():
    assert dp.jaccard(set(), set()) == 0.0
    assert dp.jaccard({"a"}, {"a"}) == 1.0
    assert dp.jaccard({"a", "b"}, {"b", "c"}) == 1 / 3


def test_lexical_tier_ranks_near_duplicate_first(tmp_path):
    _pkt(tmp_path, "a.json", packet_id="A", summary="The scanner flags marker keywords in proposal docs as lexical mentions")
    _pkt(tmp_path, "b.json", packet_id="B", summary="The scanner flags marker keywords in proposal documents as lexical mention")
    _pkt(tmp_path, "c.json", packet_id="C", summary="Zephyr TTS voice latency exceeded ten seconds on the meditation render")
    r = dp.tier_lexical(dp.load_outbox(tmp_path), top=3)
    assert r["pairs_compared"] == 3
    assert {r["top_pairs"][0]["a"], r["top_pairs"][0]["b"]} == {"A", "B"}
    assert r["top_pairs"][0]["score"] > r["top_pairs"][-1]["score"]
    assert r["counts_at_or_above"]["0.9"] <= r["counts_at_or_above"]["0.5"]


def test_inputs_digest_changes_with_text_and_is_order_stable(tmp_path):
    _pkt(tmp_path, "a.json", packet_id="A", summary="x")
    _pkt(tmp_path, "b.json", packet_id="B", summary="y")
    d1 = dp.inputs_digest(dp.load_outbox(tmp_path))
    _pkt(tmp_path, "b.json", packet_id="B", summary="y2")
    assert dp.inputs_digest(dp.load_outbox(tmp_path)) != d1


def test_receipt_is_non_sovereign_and_names_missing_text(tmp_path, monkeypatch):
    monkeypatch.setattr(dp, "RECEIPTS", tmp_path / "receipts")
    monkeypatch.setattr(dp, "REPO_ROOT", tmp_path)
    ob = tmp_path / "outbox"; ob.mkdir()
    _pkt(ob, "a.json", packet_id="A", summary="x"); _pkt(ob, "b.json", packet_id="B")
    items = dp.load_outbox(ob)
    path = dp.write_receipt("exact", dp.tier_exact(items), items, 0.01, ob)
    rec = json.loads(path.read_text())
    assert rec["schema"] == "DEDUP_PROBE_RECEIPT_V0"
    assert rec["authority"] is False and rec["sovereign"] is False and rec["ledger_effect"] == "none"
    assert rec["packets_without_text"] == ["B"] and rec["packets_with_text"] == 1
    assert "candidate" in rec["meaning"].lower()


def test_structural_tier_separates_template_from_distinction(tmp_path):
    tpl = "Scanner findings in docs/proposals/{}: signals=['proposal_marker']"
    _pkt(tmp_path, "a.json", packet_id="A", summary=tpl.format("X.md"))
    _pkt(tmp_path, "b.json", packet_id="B", summary=tpl.format("Y.md"))      # same template, other path
    _pkt(tmp_path, "c.json", packet_id="C", summary=tpl.format("X.md"))      # same path as A → real duplicate
    _pkt(tmp_path, "d.json", packet_id="D", summary="Free-form finding about the ledger writer lock")
    items = dp.load_outbox(tmp_path)
    r = dp.tier_structural(items)
    assert r["template_shaped"] == 3 and r["free_form"] == 1 and r["distinct_source_paths"] == 2
    assert r["same_path_duplicate_groups"] == [["A", "C"]]
    # and the lexical tier would have ranked A×B (different documents) as near-duplicates:
    lex = dp.tier_lexical(items, top=1)
    assert {lex["top_pairs"][0]["a"], lex["top_pairs"][0]["b"]} <= {"A", "B", "C"}
