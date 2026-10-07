"""Fixture freeze: the JESTER/RIEMANN oracles cannot drift silently.

Proves: the fixture file is well-formed, every expected outcome is in the
vocabulary, every fixture isolates one declared boundary, and the canonical
digest equals the one frozen at introduction. Any oracle change must ship as a
new version. Proves nothing about whether the oracles are *right*.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "jester_riemann_fixtures_v0.json"
DOC_PATH = Path(__file__).resolve().parents[3] / "docs" / "proposals" / "HELEN_JESTER_RIEMANN_FIXTURES_V0.md"
FROZEN_DIGEST = "05bf8cd6093c01aa88264ae2173d033b45a64b0bd066b1ca434b488412c93a6c"


def _load() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _digest(obj: dict) -> str:
    canon = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canon).hexdigest()


def _all_expected(fx: dict):
    for f in fx["fixtures"]:
        if "variants" in f:
            for v in f["variants"]:
                yield v["id"], v["expected"]
        else:
            yield f["id"], f["expected"]


def test_digest_is_frozen():
    assert _digest(_load()) == FROZEN_DIGEST, "oracles changed: ship a new version with supersedes, do not edit v0"


def test_doc_carries_same_digest():
    assert f"sha256:{FROZEN_DIGEST}" in DOC_PATH.read_text(encoding="utf-8")


def test_non_sovereign_flags():
    fx = _load()
    assert fx["authority"] is False and fx["sovereign"] is False and fx["ledger_effect"] == "none"


def test_every_outcome_in_vocabulary():
    fx = _load()
    vocab = set(fx["outcome_vocabulary"])
    assert vocab == {"ADMIT", "HOLD", "REJECT", "NO_TRANSITION"}
    for fid, exp in _all_expected(fx):
        assert exp["outcome"] in vocab, fid
        assert isinstance(exp["state_transition"], bool), fid
        assert exp["reason"].strip(), fid


def test_only_admit_may_transition():
    for fid, exp in _all_expected(_load()):
        if exp["outcome"] != "ADMIT":
            assert exp["state_transition"] is False, f"{fid}: ΔX must be 0 unless ADMIT (L3)"


def test_fixture_count_and_unique_ids():
    fx = _load()
    assert 6 <= len(fx["fixtures"]) <= 10
    ids = [fid for fid, _ in _all_expected(fx)]
    assert len(ids) == len(set(ids))


def test_each_fixture_declares_one_boundary_and_what_it_isolates():
    for f in _load()["fixtures"]:
        assert f["boundary"].strip() and f["isolates"].strip(), f["id"]
        assert ("given" in f) ^ ("variants" in f), f["id"]


def test_three_hard_laws_kept():
    laws = _load()["laws"]
    assert [l["id"] for l in laws["KEEP"]] == ["L1", "L2", "L3"]
    assert len(laws["REVISE"]) == 5 and len(laws["INVALIDATE"]) == 6
