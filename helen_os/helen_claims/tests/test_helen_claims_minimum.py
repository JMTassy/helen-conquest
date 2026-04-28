# lifecycle: CANDIDATE
"""Minimum 3-fixture test suite for helen_claims v0.1.

Asserts:
  1. Tag preservation — whitespace and `$` punctuation kept exactly.
  2. Domain whitelist — unrecognized keyword maps to DOMAIN_MISFIT, never invents.
  3. Dry-run default — no file written, no index entry appended.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `helen_os` importable without installing the package
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from helen_os.helen_claims import classify as classify_mod
from helen_os.helen_claims import index as index_mod


def test_tag_preservation_keeps_whitespace_and_dollar(tmp_path):
    """Filename '#pluginAGI LEGORACLE $.txt' must yield preserved_tag with the '$' kept."""
    fake = tmp_path / "#pluginAGI LEGORACLE $.txt"
    fake.write_text("any content")
    result = classify_mod.classify_one(fake, dry_run=True)
    assert result["status"] == "PROPOSED"
    assert result["preserved_tag"] == "#pluginAGI LEGORACLE $", (
        f"expected exact whitespace + $, got {result['preserved_tag']!r}"
    )


def test_domain_whitelist_misfit_does_not_invent(tmp_path):
    """A keyword with no domain match must yield DOMAIN_MISFIT, never a fabricated domain."""
    fake = tmp_path / "#pluginXYZGIBBERISH.txt"
    fake.write_text("any content")
    result = classify_mod.classify_one(fake, dry_run=True)
    assert result["domain"] == "DOMAIN_MISFIT", (
        f"expected DOMAIN_MISFIT for unrecognized keyword, got {result['domain']!r}"
    )
    assert result["domain_misfit"] is True


def test_dry_run_writes_nothing(tmp_path, monkeypatch):
    """Dry-run must not create the output file and must not append to index.jsonl."""
    fake = tmp_path / "#pluginHELEN.txt"
    fake.write_text("any content")

    # Redirect index.jsonl to a tmp path so we don't touch the real one
    tmp_index = tmp_path / "index.jsonl"
    monkeypatch.setattr(index_mod, "INDEX_PATH", tmp_index)

    result = classify_mod.classify_one(fake, dry_run=True)
    assert result["status"] == "PROPOSED"
    assert not Path(result["out_path"]).exists(), "dry-run must not write the output .md"
    assert not tmp_index.exists(), "dry-run must not append to index.jsonl"
