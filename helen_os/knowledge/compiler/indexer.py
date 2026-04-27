"""
Index layer — auto-maintained entity/concept index.

Keeps two JSON files:
  entity_index.json   — entity_name → [page_slugs]
  backlink_index.json — page_slug   → [page_slugs that link to it]

Entity extraction is heuristic (capitalised phrases, #tags, wiki [[links]]).
The LLM compiler layer supplements this with structured entity lists.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

from .wiki import WikiPage

META_DIR = Path(__file__).parents[1] / "compiled" / "meta"
ENTITY_INDEX_PATH = META_DIR / "entity_index.json"
BACKLINK_INDEX_PATH = META_DIR / "backlink_index.json"

# Match [[WikiLinks]], #tags, and Title Case Phrases (2+ words)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TAG_RE = re.compile(r"#([A-Za-z][A-Za-z0-9_]{2,})")
PROPER_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")


def _load(path: Path) -> Dict[str, List[str]]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save(path: Path, data: Dict) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ── Extraction helpers ────────────────────────────────────────────────────────

def extract_entities_from_page(page: WikiPage) -> Set[str]:
    """Pull entity names from a page's body and tags."""
    entities: Set[str] = set()
    text = page.body
    # Explicit wiki links
    for m in WIKILINK_RE.findall(text):
        entities.add(m.strip())
    # Hashtags
    for m in TAG_RE.findall(text):
        entities.add(m)
    # Title-case phrases (2+ words) — heuristic proper-noun detection
    for m in PROPER_RE.findall(text):
        if len(m) < 60:
            entities.add(m)
    # Tags declared in frontmatter
    entities.update(page.tags)
    # The page title itself is an entity
    entities.add(page.title)
    return entities


def extract_outgoing_links(page: WikiPage) -> Set[str]:
    """Extract slugs of pages this page links to (via [[WikiLink]])."""
    from .wiki import _slug
    links: Set[str] = set()
    for m in WIKILINK_RE.findall(page.body):
        links.add(_slug(m.strip()))
    return links


# ── KnowledgeIndexer ──────────────────────────────────────────────────────────

class KnowledgeIndexer:
    """
    Maintains two persistent JSON indexes:
      entity_index   : entity → [page_slugs]
      backlink_index : target_slug → [source_slugs]
    """

    def __init__(self) -> None:
        META_DIR.mkdir(parents=True, exist_ok=True)
        self._entity: Dict[str, List[str]] = _load(ENTITY_INDEX_PATH)
        self._backlinks: Dict[str, List[str]] = _load(BACKLINK_INDEX_PATH)

    # ── Index a page ─────────────────────────────────────────────────────────

    def index_page(self, page: WikiPage, extra_entities: List[str] | None = None) -> None:
        """
        Add/update index entries for a page.

        extra_entities: LLM-extracted entities that supplement heuristic detection.
        """
        entities = extract_entities_from_page(page)
        if extra_entities:
            entities.update(extra_entities)

        slug = page.slug
        for entity in entities:
            key = entity.lower().strip()
            if not key:
                continue
            if key not in self._entity:
                self._entity[key] = []
            if slug not in self._entity[key]:
                self._entity[key].append(slug)

        # Backlinks: find pages this page links to and record them
        for target_slug in extract_outgoing_links(page):
            if target_slug not in self._backlinks:
                self._backlinks[target_slug] = []
            if slug not in self._backlinks[target_slug]:
                self._backlinks[target_slug].append(slug)

        self._persist()

    def remove_page(self, slug: str) -> None:
        """Remove a page from both indexes (call when deleting a page)."""
        # Remove from entity index
        for entity, slugs in list(self._entity.items()):
            if slug in slugs:
                slugs.remove(slug)
            if not slugs:
                del self._entity[entity]
        # Remove from backlink index
        self._backlinks.pop(slug, None)
        for target, sources in list(self._backlinks.items()):
            if slug in sources:
                sources.remove(slug)
        self._persist()

    # ── Lookups ──────────────────────────────────────────────────────────────

    def lookup_entity(self, entity: str) -> List[str]:
        """Return page slugs that mention this entity."""
        return list(self._entity.get(entity.lower().strip(), []))

    def get_backlinks(self, slug: str) -> List[str]:
        """Return page slugs that link to this page."""
        return list(self._backlinks.get(slug, []))

    def all_entities(self) -> Dict[str, List[str]]:
        return dict(self._entity)

    def entity_count(self) -> int:
        return len(self._entity)

    def top_entities(self, n: int = 20) -> List[tuple]:
        """Return entities sorted by number of pages referencing them."""
        ranked = sorted(self._entity.items(), key=lambda x: -len(x[1]))
        return ranked[:n]

    # ── Rebuild ───────────────────────────────────────────────────────────────

    def rebuild_from_wiki(self, wiki_manager) -> int:
        """Full rebuild from the current wiki. Returns page count indexed."""
        self._entity = {}
        self._backlinks = {}
        pages = wiki_manager.list_pages()
        for page in pages:
            self.index_page(page)
        return len(pages)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _persist(self) -> None:
        _save(ENTITY_INDEX_PATH, self._entity)
        _save(BACKLINK_INDEX_PATH, self._backlinks)

    def stats(self) -> Dict:
        return {
            "entities_indexed": len(self._entity),
            "pages_with_backlinks": len(self._backlinks),
            "total_entity_refs": sum(len(v) for v in self._entity.values()),
        }
