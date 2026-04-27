"""
Governance layer — health audits for the compiled wiki.

Runs five checks:
  ORPHAN_PAGE          — page has no backlinks and no outgoing links (isolated)
  BROKEN_BACKLINK      — backlink index points to a page that no longer exists
  UNSOURCED_PAGE       — concept page has no source_refs
  EMPTY_PAGE           — body is blank or shorter than a minimum threshold
  STALE_SOURCE         — source summary page references a raw source no longer in manifest

AuditReport is serialisable to JSON for logging.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

KNOWLEDGE_DIR = Path(__file__).parents[1]
RAW_MANIFEST = KNOWLEDGE_DIR / "raw" / "manifest.json"
META_DIR = KNOWLEDGE_DIR / "compiled" / "meta"
ENTITY_INDEX_PATH = META_DIR / "entity_index.json"
BACKLINK_INDEX_PATH = META_DIR / "backlink_index.json"
GOVERNANCE_DIR = KNOWLEDGE_DIR / "governance"

MIN_BODY_CHARS = 80


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ── Finding types ─────────────────────────────────────────────────────────────

class FindingType(str, Enum):
    ORPHAN_PAGE = "orphan_page"
    BROKEN_BACKLINK = "broken_backlink"
    UNSOURCED_PAGE = "unsourced_page"
    EMPTY_PAGE = "empty_page"
    STALE_SOURCE = "stale_source"
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


@dataclass
class Finding:
    finding_type: FindingType
    severity: FindingSeverity
    page_slug: str
    reason: str
    suggested_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.finding_type.value,
            "severity": self.severity.value,
            "page_slug": self.page_slug,
            "reason": self.reason,
            "suggested_action": self.suggested_action,
        }


# ── AuditReport ───────────────────────────────────────────────────────────────

@dataclass
class AuditReport:
    run_at: str = ""
    pages_checked: int = 0
    findings: List[Finding] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.run_at:
            self.run_at = _now()

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.ERROR)

    @property
    def warn_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.WARN)

    @property
    def clean(self) -> bool:
        return self.error_count == 0

    def summary(self) -> str:
        lines = [
            f"Audit run: {self.run_at}",
            f"Pages checked: {self.pages_checked}",
            f"Errors: {self.error_count}  Warnings: {self.warn_count}",
        ]
        by_type: Dict[str, List[Finding]] = {}
        for f in self.findings:
            by_type.setdefault(f.finding_type.value, []).append(f)
        for ftype, items in sorted(by_type.items()):
            lines.append(f"\n  [{ftype}] — {len(items)} finding(s)")
            for item in items[:5]:
                lines.append(f"    • {item.page_slug}: {item.reason}")
            if len(items) > 5:
                lines.append(f"    … and {len(items) - 5} more")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_at": self.run_at,
            "pages_checked": self.pages_checked,
            "error_count": self.error_count,
            "warn_count": self.warn_count,
            "clean": self.clean,
            "findings": [f.to_dict() for f in self.findings],
        }

    def save(self) -> Path:
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        path = GOVERNANCE_DIR / "last_audit.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        return path


# ── HealthAuditor ─────────────────────────────────────────────────────────────

class HealthAuditor:
    """
    Runs all health checks against the compiled wiki and returns an AuditReport.

    Designed to be run after any bulk compilation pass, or on-demand via CLI.
    """

    def __init__(self, wiki_manager, indexer) -> None:
        self._wiki = wiki_manager
        self._idx = indexer

    def run_audit(self, save: bool = True) -> AuditReport:
        pages = self._wiki.list_pages()
        report = AuditReport(pages_checked=len(pages))

        existing_slugs: Set[str] = {p.slug for p in pages}
        raw_source_ids = self._load_raw_source_ids()
        backlink_index: Dict[str, List[str]] = {}
        if BACKLINK_INDEX_PATH.exists():
            backlink_index = json.loads(BACKLINK_INDEX_PATH.read_text(encoding="utf-8"))

        for page in pages:
            report.findings.extend(self._check_empty(page))
            report.findings.extend(self._check_unsourced(page))
            report.findings.extend(self._check_stale_source(page, raw_source_ids))
            report.findings.extend(
                self._check_broken_backlinks(page, backlink_index, existing_slugs)
            )

        report.findings.extend(self._check_orphans(pages, backlink_index, existing_slugs))
        report.findings.extend(self._check_contradictions())

        if save:
            report.save()

        return report

    # ── Individual checks ─────────────────────────────────────────────────────

    def _check_empty(self, page) -> List[Finding]:
        if len(page.body.strip()) < MIN_BODY_CHARS:
            return [Finding(
                FindingType.EMPTY_PAGE, FindingSeverity.WARN, page.slug,
                f"Body is {len(page.body.strip())} chars (min {MIN_BODY_CHARS}).",
                "Recompile or manually expand this page.",
            )]
        return []

    def _check_unsourced(self, page) -> List[Finding]:
        if page.page_type == "concept" and not page.source_refs:
            return [Finding(
                FindingType.UNSOURCED_PAGE, FindingSeverity.WARN, page.slug,
                "Concept page has no source_refs.",
                "Link to at least one raw source via compiler.compile().",
            )]
        return []

    def _check_stale_source(self, page, raw_source_ids: Set[str]) -> List[Finding]:
        if page.page_type != "source_summary" or not raw_source_ids:
            return []
        stale = [r for r in page.source_refs if r not in raw_source_ids]
        if stale:
            return [Finding(
                FindingType.STALE_SOURCE, FindingSeverity.WARN, page.slug,
                f"Source refs not in raw manifest: {stale}",
                "Re-ingest the source or remove the stale ref.",
            )]
        return []

    def _check_broken_backlinks(self, page, backlink_index: Dict,
                                existing_slugs: Set[str]) -> List[Finding]:
        findings = []
        # Check declared backlinks on this page
        for bl in page.backlinks:
            if bl not in existing_slugs:
                findings.append(Finding(
                    FindingType.BROKEN_BACKLINK, FindingSeverity.ERROR, page.slug,
                    f"Backlink '{bl}' points to a non-existent page.",
                    f"Delete the backlink or create the page '{bl}'.",
                ))
        return findings

    def _check_orphans(self, pages, backlink_index: Dict,
                       existing_slugs: Set[str]) -> List[Finding]:
        from .indexer import extract_outgoing_links
        findings = []
        for page in pages:
            has_backlinks = bool(backlink_index.get(page.slug))
            has_outgoing = bool(extract_outgoing_links(page))
            # Source summaries are never orphans — they anchor to raw sources
            if not has_backlinks and not has_outgoing and page.page_type == "concept":
                findings.append(Finding(
                    FindingType.ORPHAN_PAGE, FindingSeverity.INFO, page.slug,
                    "No incoming or outgoing links — fully isolated page.",
                    "Add [[WikiLinks]] to connect this page, or delete it if irrelevant.",
                ))
        return findings

    def _check_contradictions(self) -> List[Finding]:
        contradictions_path = GOVERNANCE_DIR / "contradictions.json"
        if not contradictions_path.exists():
            return []
        try:
            data = json.loads(contradictions_path.read_text(encoding="utf-8"))
            findings = []
            for c in data.get("open", []):
                findings.append(Finding(
                    FindingType.UNRESOLVED_CONTRADICTION, FindingSeverity.ERROR,
                    c.get("page_slug", "unknown"),
                    c.get("reason", "Unresolved contradiction detected."),
                    "Resolve or deprecate one of the conflicting claims.",
                ))
            return findings
        except Exception:
            return []

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_raw_source_ids(self) -> Set[str]:
        if not RAW_MANIFEST.exists():
            return set()
        try:
            data = json.loads(RAW_MANIFEST.read_text(encoding="utf-8"))
            return {s["source_id"] for s in data.get("sources", [])}
        except Exception:
            return set()
