"""
Schema Authority Guard — Seam 1 measurement instrument.

Enforces the Single Authority Rule: helen_os/schemas/ is the exclusive
source of constitutional schemas. Root-level schemas/ is legacy; the
canonical registry and all helen_os/ callers must not resolve to it.

This test is the receipt that Seam 1 (Schema Authority) is actually closed.
While drift exists it FAILS — that is the correct state. A FAIL here is the
honest verdict for the Schema Authority seam; a PASS is the closure condition.

Related:
  - scripts/purge_legacy_schemas.sh: migration tool
  - GOVERNANCE/CLOSURES/SEAM-001-schema-authority-V4.json: the first real closure receipt
  - helen_os/tests/test_no_ghost_closures.py: enforces closure receipts don't lie
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LEGACY_SCHEMAS_DIR = REPO / "schemas"
CANONICAL_SCHEMAS_DIR = REPO / "helen_os" / "schemas"


def test_canonical_schemas_directory_exists():
    assert CANONICAL_SCHEMAS_DIR.is_dir(), (
        f"Canonical schemas directory missing: {CANONICAL_SCHEMAS_DIR}"
    )


def test_canonical_schemas_directory_non_empty():
    jsons = list(CANONICAL_SCHEMAS_DIR.glob("*.json"))
    assert len(jsons) > 0, (
        f"Canonical schemas directory has no schemas: {CANONICAL_SCHEMAS_DIR}"
    )


def test_governance_registry_resolves_to_canonical_schemas():
    """
    helen_os/governance/schema_registry.py::_SCHEMA_DIR must resolve to
    helen_os/schemas/. Tested by import, not regex — importing proves the
    module actually loads and the path is what it claims.
    """
    from helen_os.governance import schema_registry  # noqa: WPS433

    assert schema_registry._SCHEMA_DIR == CANONICAL_SCHEMAS_DIR, (
        f"Governance registry _SCHEMA_DIR points to {schema_registry._SCHEMA_DIR}, "
        f"expected {CANONICAL_SCHEMAS_DIR}"
    )


def test_legacy_schemas_directory_is_purged():
    """
    Seam 1 hard closure condition. This test FAILS while the root-level
    schemas/ directory still contains JSON files.

    To close: run scripts/purge_legacy_schemas.sh --execute after migrating
    the bare SchemaRegistry() callers.
    """
    if not LEGACY_SCHEMAS_DIR.exists():
        return  # Already purged — good.

    remaining = sorted(p.name for p in LEGACY_SCHEMAS_DIR.glob("*.json"))
    assert remaining == [], (
        f"Legacy schemas/ still contains {len(remaining)} JSON schema files. "
        f"Migration required before purge. First 5: {remaining[:5]}"
    )


def test_no_bare_schema_registry_in_helen_os_tree():
    """
    helen_os/schema_registry.py::SchemaRegistry defaults schema_dir to
    Path(__file__).parent.parent / 'schemas' — which resolves to the LEGACY
    root-level schemas/. Any bare SchemaRegistry() call in helen_os/ reads
    legacy schemas, bypassing the Single Authority Rule.

    Exceptions (allowed to contain the literal for self-reference):
      - helen_os/schema_registry.py itself (declares the class)
      - this test file (pattern is in the test body)
      - helen_os/tests/test_schema_authority_guard.py (self)
    """
    pattern = re.compile(r"SchemaRegistry\(\s*\)")
    allowed_files = {
        REPO / "helen_os" / "schema_registry.py",
        Path(__file__).resolve(),
    }
    offenders: list[str] = []
    for py in (REPO / "helen_os").rglob("*.py"):
        if py.resolve() in allowed_files:
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if pattern.search(text):
            offenders.append(str(py.relative_to(REPO)))

    assert offenders == [], (
        "Bare SchemaRegistry() calls resolve to LEGACY root-level schemas/, "
        "bypassing the Single Authority Rule. Pass explicit "
        "schema_dir=Path('helen_os/schemas'). Offenders:\n  "
        + "\n  ".join(offenders)
    )
