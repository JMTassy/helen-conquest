"""Corpus manifest candidate: deterministic from rules + revision + seed; split integrity; no branch-authored documents;
provenance honestly marked. Proves nothing about labels or scanner performance (none exist)."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PKG / "scanner_pilot"))
import build_corpus_manifest as bcm  # noqa: E402

MANIFEST = PKG / "scanner_pilot" / "corpus_manifest_candidate.json"
COMMITTED_SHA = "46111de2ae838750aa001672f02f8f4a30877ce7e5cb0d0934a22952d78bce73"


def _m():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_rebuilds_identically_from_pinned_revision():
    m = _m()
    rebuilt = bcm.build(m["pinned_revision"])
    assert rebuilt["manifest_sha256"] == m["manifest_sha256"] == COMMITTED_SHA


def test_split_sizes_and_no_group_straddling():
    m = _m()
    assert m["counts"]["selected"] == 40 and m["counts"]["development"] == 25 and m["counts"]["holdout"] == 15
    by_group = defaultdict(set)
    for d in m["documents"]:
        by_group[d["source_group"]].add(d["split"])
    assert all(len(s) == 1 for s in by_group.values()), "a source group straddles the split"


def test_no_branch_authored_document_selected():
    main_paths = set(subprocess.run(["git", "-C", str(REPO), "ls-tree", "--name-only", "origin/main", "docs/proposals/"],
                                    capture_output=True, text=True, check=True).stdout.split())
    for d in _m()["documents"]:
        assert d["path"] in main_paths, d["path"]
    assert all(e["reason"].startswith("E2") for e in _m()["excluded"] if "FIXTURES" in e["path"])


def test_every_document_hashed_at_revision_and_provenance_marked():
    m = _m()
    for d in m["documents"]:
        assert len(d["sha256_at_revision"]) == 64 and len(d["blob"]) == 40
        assert d["historical_scanned_bytes"].startswith("UNVERIFIED")
        blob = subprocess.run(["git", "-C", str(REPO), "rev-parse", f"{m['pinned_revision']}:{d['path']}"],
                              capture_output=True, text=True, check=True).stdout.strip()
        assert blob == d["blob"], d["path"]


def test_sampling_declared_independent_of_predictions_and_covariate_present():
    m = _m()
    assert m["sampling"]["independent_of_scanner_predictions"] is True
    assert all("covariate_packet_appearances" in d for d in m["documents"])
    assert m["status"].startswith("CANDIDATE") and m["authority"] is False
    assert "labels" in m["not_bound_yet"] and "scorer" in m["not_bound_yet"]


def test_grouping_rule_strips_versions():
    assert bcm.group_of("docs/proposals/HELEN_OS_V2_INTERACTION_GRAMMAR.md") == bcm.group_of("docs/proposals/HELEN_OS_V2_VISUAL_CANON_LOCK.md")
    assert bcm.group_of("docs/proposals/MANIFEST_GATE_V1.md") == "MANIFEST_GATE"
