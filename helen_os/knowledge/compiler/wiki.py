"""
Wiki layer — WikiPage dataclass and WikiManager.

Compiled wiki pages live at helen_os/knowledge/compiled/
  pages/    — one .md file per concept/entity page
  sources/  — one .md file per ingested source summary

Each file uses YAML-style frontmatter (hand-parsed, no PyYAML dep).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

KNOWLEDGE_DIR = Path(__file__).parents[1]
COMPILED_DIR = KNOWLEDGE_DIR / "compiled"
PAGES_DIR = COMPILED_DIR / "pages"
SOURCES_DIR = COMPILED_DIR / "sources"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "_", title.lower().strip())[:80]


def _page_hash(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode()).hexdigest()[:16]


# ── Frontmatter helpers ───────────────────────────────────────────────────────

def _encode_fm(data: Dict[str, Any]) -> str:
    lines = ["---"]
    for k, v in data.items():
        lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def _decode_fm(raw: str) -> tuple[Dict[str, Any], str]:
    """Parse frontmatter + body. Returns (meta, body)."""
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, raw
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, raw
    meta: Dict[str, Any] = {}
    for line in lines[1:end]:
        if ": " in line:
            k, _, v = line.partition(": ")
            try:
                meta[k.strip()] = json.loads(v)
            except Exception:
                meta[k.strip()] = v
    body = "\n".join(lines[end + 2:]).strip()
    return meta, body


# ── WikiPage ──────────────────────────────────────────────────────────────────

@dataclass
class WikiPage:
    title: str
    body: str                              # Markdown body (no frontmatter)
    source_refs: List[str]                 # Source IDs that contributed
    tags: List[str]
    page_type: str = "concept"            # concept | source_summary | relation
    created_at: str = ""
    updated_at: str = ""
    page_hash: str = ""
    backlinks: List[str] = field(default_factory=list)  # Slugs of pages that link here

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = _now()
        if not self.updated_at:
            self.updated_at = _now()
        if not self.page_hash:
            self.page_hash = _page_hash(self.body)

    @property
    def slug(self) -> str:
        return _slug(self.title)

    # Serialisation ─────────────────────────────────────────────────────────

    def to_file_content(self) -> str:
        fm = _encode_fm({
            "title": self.title,
            "type": self.page_type,
            "source_refs": self.source_refs,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "page_hash": self.page_hash,
            "backlinks": self.backlinks,
        })
        return fm + "\n\n" + self.body

    @classmethod
    def from_file_content(cls, raw: str) -> "WikiPage":
        meta, body = _decode_fm(raw)
        return cls(
            title=meta.get("title", "unknown"),
            body=body,
            source_refs=meta.get("source_refs", []),
            tags=meta.get("tags", []),
            page_type=meta.get("type", "concept"),
            created_at=meta.get("created_at", ""),
            updated_at=meta.get("updated_at", ""),
            page_hash=meta.get("page_hash", ""),
            backlinks=meta.get("backlinks", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "slug": self.slug,
            "type": self.page_type,
            "source_refs": self.source_refs,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "page_hash": self.page_hash,
            "backlinks": self.backlinks,
            "body_preview": self.body[:200],
        }


# ── WikiManager ───────────────────────────────────────────────────────────────

class WikiManager:
    """
    Manages the compiled wiki on disk.

    Pages live at:
      PAGES_DIR/<slug>.md    — concept / entity pages
      SOURCES_DIR/<slug>.md  — source summary pages
    """

    def __init__(self) -> None:
        PAGES_DIR.mkdir(parents=True, exist_ok=True)
        SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    # ── File path resolution ─────────────────────────────────────────────────

    def _path(self, slug: str, page_type: str = "concept") -> Path:
        d = SOURCES_DIR if page_type == "source_summary" else PAGES_DIR
        return d / f"{slug}.md"

    def _all_paths(self):
        return list(PAGES_DIR.glob("*.md")) + list(SOURCES_DIR.glob("*.md"))

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create_page(self, page: WikiPage) -> WikiPage:
        path = self._path(page.slug, page.page_type)
        if path.exists():
            existing = self.get_page(page.slug, page.page_type)
            if existing and existing.page_hash == _page_hash(page.body):
                return existing  # identical — no-op
            # Merge: preserve created_at and backlinks
            page.created_at = existing.created_at
            page.backlinks = list(set(existing.backlinks) | set(page.backlinks))
            page.updated_at = _now()
            page.page_hash = _page_hash(page.body)
        path.write_text(page.to_file_content(), encoding="utf-8")
        return page

    def get_page(self, slug: str, page_type: str = "concept") -> Optional[WikiPage]:
        path = self._path(slug, page_type)
        if not path.exists():
            return None
        return WikiPage.from_file_content(path.read_text(encoding="utf-8"))

    def get_page_by_title(self, title: str) -> Optional[WikiPage]:
        """Try concept first, then source_summary."""
        slug = _slug(title)
        p = self.get_page(slug, "concept") or self.get_page(slug, "source_summary")
        return p

    def update_page(self, slug: str, page_type: str, new_body: str,
                    extra_source_refs: Optional[List[str]] = None,
                    extra_tags: Optional[List[str]] = None) -> Optional[WikiPage]:
        page = self.get_page(slug, page_type)
        if not page:
            return None
        page.body = new_body
        page.page_hash = _page_hash(new_body)
        page.updated_at = _now()
        if extra_source_refs:
            page.source_refs = list(set(page.source_refs) | set(extra_source_refs))
        if extra_tags:
            page.tags = list(set(page.tags) | set(extra_tags))
        path = self._path(slug, page_type)
        path.write_text(page.to_file_content(), encoding="utf-8")
        return page

    def add_backlink(self, target_slug: str, source_slug: str,
                     target_type: str = "concept") -> bool:
        """Record that source_slug links to target_slug."""
        page = self.get_page(target_slug, target_type)
        if not page:
            return False
        if source_slug not in page.backlinks:
            page.backlinks.append(source_slug)
            self._path(target_slug, target_type).write_text(
                page.to_file_content(), encoding="utf-8"
            )
        return True

    def delete_page(self, slug: str, page_type: str = "concept") -> bool:
        path = self._path(slug, page_type)
        if path.exists():
            path.unlink()
            return True
        return False

    # ── Listing / search ─────────────────────────────────────────────────────

    def list_pages(self, page_type: Optional[str] = None) -> List[WikiPage]:
        if page_type == "source_summary":
            paths = list(SOURCES_DIR.glob("*.md"))
        elif page_type == "concept":
            paths = list(PAGES_DIR.glob("*.md"))
        else:
            paths = self._all_paths()
        pages = []
        for p in sorted(paths):
            try:
                pages.append(WikiPage.from_file_content(p.read_text(encoding="utf-8")))
            except Exception:
                pass
        return pages

    def search(self, query: str, limit: int = 10) -> List[WikiPage]:
        q = query.lower()
        words = [w for w in q.split() if len(w) > 2]
        results = []
        for page in self.list_pages():
            body_lower = page.body.lower()
            title_lower = page.title.lower()
            score = 0
            # Exact phrase match (highest value)
            if q in title_lower:
                score += 6
            if q in body_lower:
                score += 4
            # Individual word hits
            for w in words:
                if w in title_lower:
                    score += 2
                score += body_lower.count(w)
            # Tag hits
            score += sum(2 for t in page.tags if any(w in t for w in words))
            if score > 0:
                results.append((score, page))
        results.sort(key=lambda x: -x[0])
        return [p for _, p in results[:limit]]

    def stats(self) -> Dict[str, Any]:
        concept_pages = list(PAGES_DIR.glob("*.md"))
        source_pages = list(SOURCES_DIR.glob("*.md"))
        all_tags: List[str] = []
        for p in concept_pages + source_pages:
            try:
                pg = WikiPage.from_file_content(p.read_text(encoding="utf-8"))
                all_tags.extend(pg.tags)
            except Exception:
                pass
        from collections import Counter
        tag_counts = Counter(all_tags)
        return {
            "concept_pages": len(concept_pages),
            "source_summaries": len(source_pages),
            "total_pages": len(concept_pages) + len(source_pages),
            "top_tags": tag_counts.most_common(10),
        }
