"""test_structural_dedup.py — G4 proposal tests for structural same-path marking.

Imports the PATCHED COPY in this directory (autoresearch_scanner_patched_copy.py),
never the real temple/ scanner. autoresearch_policy is imported read-only from
temple/autoresearch. All writes go to pytest tmp_path.

authority=false · ledger_effect=none · no mutation of temple/
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO_ROOT / "temple" / "autoresearch"))  # autoresearch_policy only
sys.path.insert(0, str(HERE))
import autoresearch_scanner_patched_copy as scanner  # noqa: E402

CROSSING_RISK = "risk: this helper writes directly to the ledger and bypasses the reducer."
CROSSING_GAP = "TODO: remove the shim that appends to the ledger bypassing the guard."


def _packet(source_path, lines):
    findings = [{"source_ref": f"{source_path}:{i}", "raw_text": text, "signal": sig}
                for i, (sig, text) in enumerate(lines, 1)]
    return scanner.build_packet(findings, source_path)


def _on_disk(outbox, packet):
    return json.loads((outbox / f"{packet['packet_id']}.json").read_text(encoding="utf-8"))


def _unmarked(packet):
    return "duplicate_of" not in packet and "duplicate_check" not in packet


def test_same_path_twice_second_is_marked(tmp_path):
    outbox = tmp_path / "outbox"
    first = _packet("docs/proposals/a.md", [("risk_marker", CROSSING_RISK)])
    scanner.write_packet(first, outbox)
    second = _packet("docs/proposals/a.md",
                     [("risk_marker", CROSSING_RISK), ("gap_marker", CROSSING_GAP)])
    assert second["packet_id"] != first["packet_id"]
    scanner.write_packet(second, outbox)
    assert second["duplicate_of"] == first["packet_id"]
    assert second["duplicate_check"] == "structural_same_path"
    assert _on_disk(outbox, second)["duplicate_of"] == first["packet_id"]
    assert _unmarked(_on_disk(outbox, first)), "the earlier packet is never edited"


def test_different_paths_neither_marked(tmp_path):
    outbox = tmp_path / "outbox"
    a = _packet("docs/proposals/a.md", [("risk_marker", CROSSING_RISK)])
    b = _packet("docs/proposals/b.md", [("risk_marker", CROSSING_RISK)])  # same text, other path
    scanner.write_packet(a, outbox)
    scanner.write_packet(b, outbox)
    assert _unmarked(a) and _unmarked(b)
    assert _unmarked(_on_disk(outbox, a)) and _unmarked(_on_disk(outbox, b))


def test_unreadable_outbox_no_mark_no_exception(tmp_path):
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    (outbox / "AR-corrupt.json").write_text("{not json", encoding="utf-8")
    first = _packet("docs/proposals/a.md", [("risk_marker", CROSSING_RISK)])
    scanner.write_packet(first, outbox)  # must not raise
    second = _packet("docs/proposals/a.md",
                     [("risk_marker", CROSSING_RISK), ("gap_marker", CROSSING_GAP)])
    path = scanner.write_packet(second, outbox)  # must not raise
    assert _unmarked(second)
    assert path.exists(), "the packet is still written; only the mark is withheld"


def test_outbox_listing_error_no_mark_no_exception(tmp_path, monkeypatch):
    outbox = tmp_path / "outbox"
    scanner.write_packet(_packet("docs/proposals/a.md", [("risk_marker", CROSSING_RISK)]), outbox)

    def _denied(self, pattern):
        raise PermissionError("listing denied (simulated)")

    monkeypatch.setattr(scanner.Path, "glob", _denied)
    second = _packet("docs/proposals/a.md",
                     [("risk_marker", CROSSING_RISK), ("gap_marker", CROSSING_GAP)])
    scanner.write_packet(second, outbox)  # must not raise
    assert _unmarked(second)


def test_missing_outbox_dir_first_write_unmarked(tmp_path):
    outbox = tmp_path / "does_not_exist_yet"
    p = _packet("docs/proposals/a.md", [("risk_marker", CROSSING_RISK)])
    path = scanner.write_packet(p, outbox)
    assert path.exists() and _unmarked(p)


def test_rescan_same_packet_id_is_not_a_twin(tmp_path):
    outbox = tmp_path / "outbox"
    p1 = _packet("docs/proposals/a.md", [("risk_marker", CROSSING_RISK)])
    scanner.write_packet(p1, outbox)
    p2 = _packet("docs/proposals/a.md", [("risk_marker", CROSSING_RISK)])
    assert p2["packet_id"] == p1["packet_id"]
    scanner.write_packet(p2, outbox)  # overwrites the same file in place
    assert _unmarked(p2)


def test_run_end_to_end_second_scan_marked(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs" / "proposals"
    docs.mkdir(parents=True)
    doc = docs / "a.md"
    doc.write_text(CROSSING_RISK + "\n", encoding="utf-8")
    outbox = repo / "temple" / "autoresearch" / "outbox"
    first = scanner.run(docs, outbox, dry_run=False, repo_root=repo)
    assert len(first) == 1 and _unmarked(first[0])
    doc.write_text(CROSSING_RISK + "\n" + CROSSING_GAP + "\n", encoding="utf-8")
    second = scanner.run(docs, outbox, dry_run=False, repo_root=repo)
    assert len(second) == 1
    assert second[0]["packet_id"] != first[0]["packet_id"]
    assert second[0]["duplicate_of"] == first[0]["packet_id"]


def test_run_with_corrupt_outbox_completes_unmarked(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs" / "proposals"
    docs.mkdir(parents=True)
    (docs / "a.md").write_text(CROSSING_RISK + "\n", encoding="utf-8")
    outbox = repo / "temple" / "autoresearch" / "outbox"
    outbox.mkdir(parents=True)
    (outbox / "AR-corrupt.json").write_text("{not json", encoding="utf-8")
    packets = scanner.run(docs, outbox, dry_run=False, repo_root=repo)  # must not raise
    assert len(packets) == 1 and _unmarked(packets[0])
