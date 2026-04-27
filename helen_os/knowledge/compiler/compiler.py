"""
HELEN_KNOWLEDGE_COMPILER_V1 — main pipeline orchestrator.

Pipeline:  ingest → compile → index → query / audit

Ingest:   Reads raw sources (markdown, code, text, transcripts).
          Stores a lightweight record in raw/manifest.json.
          Does NOT call LLM — purely structural.

Compile:  Takes a source record (or all uncompiled sources) and:
            1. Sends content to Gemini (or falls back to keyword extractor).
            2. LLM returns: summary, concept_list, entities, tags.
            3. Creates/updates wiki pages for each concept.
            4. Creates a source-summary page.
            5. Updates entity index + backlinks.
          Appends a lineage record to governance/lineage.ndjson.

Query:    Keyword search across compiled pages, with optional Gemini Q&A.

Audit:    Delegates to HealthAuditor.

Governance reinsertion rule (from architecture):
  Only source_summary pages can flow back from derived outputs.
  Concept pages are COMPILED from source, not written back from derived.
  The compiler enforces this by refusing to create concept pages whose
  source_refs do not trace to an entry in raw/manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .wiki import WikiManager, WikiPage, _slug
from .indexer import KnowledgeIndexer
from .auditor import HealthAuditor, AuditReport

KNOWLEDGE_DIR = Path(__file__).parents[1]
RAW_DIR = KNOWLEDGE_DIR / "raw"
RAW_MANIFEST = RAW_DIR / "manifest.json"
GOVERNANCE_DIR = KNOWLEDGE_DIR / "governance"
LINEAGE_LOG = GOVERNANCE_DIR / "lineage.ndjson"
CONTRADICTIONS_PATH = GOVERNANCE_DIR / "contradictions.json"

SUPPORTED_EXTENSIONS = {".md", ".txt", ".py", ".js", ".ts", ".json",
                        ".rst", ".csv", ".ndjson", ".yaml", ".yml"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


# ── Raw source record ─────────────────────────────────────────────────────────

@dataclass
class RawSource:
    source_id: str
    source_name: str
    source_path: str
    source_type: str        # document | code | transcript | article
    content_hash: str
    char_count: int
    ingested_at: str
    compiled: bool = False
    compiled_at: str = ""
    dispatch_id: str = ""   # lineage anchor

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


# ── Compilation result ────────────────────────────────────────────────────────

@dataclass
class CompilationResult:
    source_id: str
    pages_created: List[str] = field(default_factory=list)
    pages_updated: List[str] = field(default_factory=list)
    concepts_extracted: List[str] = field(default_factory=list)
    entities_indexed: int = 0
    compiled_at: str = ""
    llm_used: bool = False
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.compiled_at:
            self.compiled_at = _now()

    @property
    def success(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        status = "OK" if self.success else f"ERROR: {self.error}"
        return (f"[{status}] source={self.source_id} "
                f"pages_created={len(self.pages_created)} "
                f"pages_updated={len(self.pages_updated)} "
                f"concepts={len(self.concepts_extracted)} "
                f"llm={'yes' if self.llm_used else 'no'}")


# ── LLM interface (Gemini, with keyword fallback) ─────────────────────────────

_EXTRACTION_PROMPT = """\
You are a knowledge compiler for HELEN OS. Given a source document, extract:

1. A concise summary (2–4 sentences).
2. A list of key concepts (5–15 short noun phrases).
3. A list of named entities (people, systems, places, organisations — skip generic terms).
4. A list of descriptive tags (lowercase, no spaces, 3–10 tags).

Return ONLY valid JSON in this exact format:
{
  "summary": "...",
  "concepts": ["ConceptOne", "ConceptTwo", ...],
  "entities": ["EntityName", ...],
  "tags": ["tag1", "tag2", ...]
}

SOURCE TITLE: {title}
SOURCE TYPE: {source_type}
---
{content}
"""

_QA_PROMPT = """\
You are HELEN's knowledge assistant. Answer the question using only the compiled wiki pages provided.
Be concise and cite the page titles you used.

QUESTION: {question}

WIKI PAGES:
{pages}
"""


def _gemini_extract(content: str, title: str, source_type: str,
                    api_key: str) -> Optional[Dict]:
    """Call Gemini Flash to extract structure from raw content. Returns None on failure."""
    try:
        import sys
        venv = Path(__file__).parents[4] / ".venv" / "lib"
        pyver = next(venv.glob("python3.*"), None)
        if pyver:
            sys.path.insert(0, str(pyver / "site-packages"))
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = _EXTRACTION_PROMPT.format(
            title=title,
            source_type=source_type,
            content=content[:6000],  # cap to avoid token limits
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception as e:
        return None


def _gemini_qa(question: str, pages: List[WikiPage], api_key: str) -> str:
    """Q&A over compiled wiki pages via Gemini."""
    try:
        import sys
        venv = Path(__file__).parents[4] / ".venv" / "lib"
        pyver = next(venv.glob("python3.*"), None)
        if pyver:
            sys.path.insert(0, str(pyver / "site-packages"))
        from google import genai

        client = genai.Client(api_key=api_key)
        pages_text = "\n\n---\n\n".join(
            f"**{p.title}**\n{p.body[:1500]}" for p in pages
        )
        prompt = _QA_PROMPT.format(question=question, pages=pages_text)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"[LLM unavailable: {e}]"


def _keyword_extract(content: str, title: str) -> Dict:
    """
    Fallback extractor when no API key is set.
    Heuristic: capitalised noun phrases + frequent words.
    """
    # Pull title-case phrases as concepts
    concepts = list(dict.fromkeys(
        m for m in re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", content)
        if 3 < len(m) < 60
    ))[:15]

    # Word frequency → tags
    words = re.findall(r"\b[a-z]{4,}\b", content.lower())
    from collections import Counter
    freq = Counter(words)
    stopwords = {"this", "that", "with", "from", "have", "been", "they",
                 "will", "when", "then", "than", "also", "into", "over",
                 "each", "more", "some", "such", "like", "used", "which"}
    tags = [w for w, _ in freq.most_common(30) if w not in stopwords][:10]

    # Summary = first two sentences of content
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())
    summary = " ".join(sentences[:2])[:400]

    return {
        "summary": summary or f"Source: {title}",
        "concepts": concepts or [title],
        "entities": [],
        "tags": tags,
    }


# ── Manifest helpers ──────────────────────────────────────────────────────────

def _load_manifest() -> Dict[str, Any]:
    if RAW_MANIFEST.exists():
        return json.loads(RAW_MANIFEST.read_text(encoding="utf-8"))
    return {"version": 1, "sources": []}


def _save_manifest(data: Dict) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    RAW_MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _append_lineage(record: Dict) -> None:
    GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
    with LINEAGE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── KnowledgeCompiler ─────────────────────────────────────────────────────────

class KnowledgeCompiler:
    """
    The four-layer knowledge compiler.

    Layers:
      Raw        → raw/manifest.json  (source registry)
      Compiled   → compiled/pages/    (wiki concept pages)
                   compiled/sources/  (source summaries)
                   compiled/meta/     (entity + backlink indexes)
      Derived    → caller-driven (briefings, Q&A) — not stored by this class
      Governance → governance/lineage.ndjson
                   governance/contradictions.json
                   governance/last_audit.json
    """

    def __init__(self, gemini_api_key: Optional[str] = None) -> None:
        self._api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self.wiki = WikiManager()
        self.indexer = KnowledgeIndexer()
        self.auditor = HealthAuditor(self.wiki, self.indexer)

    # ── INGEST ────────────────────────────────────────────────────────────────

    def ingest(self, source_path: str,
               source_type: str = "document",
               dispatch_id: Optional[str] = None) -> RawSource:
        """
        Register a raw source in the manifest.

        Reads the file (or directory of files), hashes content, stores metadata.
        Does NOT call LLM — pure structural ingestion.

        Returns: RawSource record (also written to manifest.json).
        """
        path = Path(source_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        manifest = _load_manifest()
        existing_hashes = {s["content_hash"] for s in manifest["sources"]}
        sources_added: List[RawSource] = []

        if path.is_file():
            files = [path]
        else:
            files = [
                f for f in sorted(path.rglob("*"))
                if f.is_file() and f.suffix in SUPPORTED_EXTENSIONS
                and not any(skip in f.parts for skip in
                            {".git", ".venv", "__pycache__", "worktrees", "node_modules"})
            ]

        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if len(content.strip()) < 20:
                continue

            content_hash = _sha256(content)
            if content_hash in existing_hashes:
                continue  # deduplicate

            source_id = f"src_{_short_hash(content_hash + str(f))}"
            rec = RawSource(
                source_id=source_id,
                source_name=f.name,
                source_path=str(f),
                source_type=source_type,
                content_hash=content_hash,
                char_count=len(content),
                ingested_at=_now(),
                dispatch_id=dispatch_id or f"dispatch_{source_id}",
            )
            manifest["sources"].append(rec.to_dict())
            existing_hashes.add(content_hash)
            sources_added.append(rec)

        _save_manifest(manifest)

        if not sources_added:
            # Return existing record for this path if already ingested
            name = path.name
            for s in manifest["sources"]:
                if Path(s["source_path"]).name == name:
                    return RawSource(**{k: v for k, v in s.items()
                                       if k in RawSource.__dataclass_fields__})
            raise ValueError(f"Nothing new to ingest from {source_path}")

        return sources_added[0]

    def ingest_text(self, text: str, title: str,
                    source_type: str = "document",
                    dispatch_id: Optional[str] = None) -> RawSource:
        """
        Ingest raw text directly (no file needed).
        Useful for transcripts, pasted articles, API responses.
        """
        if len(text.strip()) < 20:
            raise ValueError("Content too short to ingest.")

        manifest = _load_manifest()
        existing_hashes = {s["content_hash"] for s in manifest["sources"]}
        content_hash = _sha256(text)

        if content_hash in existing_hashes:
            for s in manifest["sources"]:
                if s["content_hash"] == content_hash:
                    return RawSource(**{k: v for k, v in s.items()
                                       if k in RawSource.__dataclass_fields__})

        source_id = f"src_{_short_hash(content_hash + title)}"
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        raw_file = RAW_DIR / f"{source_id}.txt"
        raw_file.write_text(text, encoding="utf-8")

        rec = RawSource(
            source_id=source_id,
            source_name=title,
            source_path=str(raw_file),
            source_type=source_type,
            content_hash=content_hash,
            char_count=len(text),
            ingested_at=_now(),
            dispatch_id=dispatch_id or f"dispatch_{source_id}",
        )
        manifest["sources"].append(rec.to_dict())
        _save_manifest(manifest)
        return rec

    # ── COMPILE ───────────────────────────────────────────────────────────────

    def compile(self, source_id: str) -> CompilationResult:
        """
        Compile a single raw source into wiki pages.

        Steps:
          1. Load source content from disk.
          2. Extract structure (LLM or keyword fallback).
          3. Create/update concept wiki pages.
          4. Create/update source-summary page.
          5. Update entity index + backlinks.
          6. Append lineage record.
          7. Mark source as compiled in manifest.
        """
        manifest = _load_manifest()
        source_dict = next(
            (s for s in manifest["sources"] if s["source_id"] == source_id), None
        )
        if not source_dict:
            return CompilationResult(
                source_id=source_id,
                error=f"Source '{source_id}' not in manifest. Run ingest first.",
            )

        # Load raw content
        raw_path = Path(source_dict["source_path"])
        if not raw_path.exists():
            return CompilationResult(
                source_id=source_id,
                error=f"Raw file missing: {raw_path}",
            )
        content = raw_path.read_text(encoding="utf-8", errors="ignore")

        # Extract structure
        llm_used = False
        if self._api_key:
            extracted = _gemini_extract(
                content,
                title=source_dict["source_name"],
                source_type=source_dict["source_type"],
                api_key=self._api_key,
            )
            if extracted:
                llm_used = True
        if not llm_used or not extracted:
            extracted = _keyword_extract(content, source_dict["source_name"])

        result = CompilationResult(source_id=source_id, llm_used=llm_used)
        summary = extracted.get("summary", "")
        concepts = extracted.get("concepts", [])
        entities = extracted.get("entities", [])
        tags = extracted.get("tags", [])

        # 1. Source-summary page
        summary_slug = _slug(f"source_{source_dict['source_name']}")
        summary_body = self._build_source_summary_body(
            source_dict, summary, concepts, entities, tags
        )
        summary_page = WikiPage(
            title=f"Source: {source_dict['source_name']}",
            body=summary_body,
            source_refs=[source_id],
            tags=tags,
            page_type="source_summary",
        )
        created = self.wiki.create_page(summary_page)
        if _slug(f"source_{source_dict['source_name']}") not in \
                [_slug(p) for p in result.pages_updated]:
            result.pages_created.append(summary_page.slug)

        self.indexer.index_page(created, extra_entities=entities)
        result.entities_indexed += len(entities)

        # 2. Concept pages
        for concept in concepts[:12]:  # cap at 12 concepts per source
            concept_slug = _slug(concept)
            existing = self.wiki.get_page(concept_slug, "concept")
            if existing:
                # Merge: append source ref and update backlink
                new_body = self._enrich_concept_body(existing, source_id, summary)
                updated = self.wiki.update_page(
                    concept_slug, "concept", new_body,
                    extra_source_refs=[source_id], extra_tags=tags,
                )
                if updated:
                    result.pages_updated.append(concept_slug)
                    self.indexer.index_page(updated, extra_entities=entities)
            else:
                concept_body = self._build_concept_body(
                    concept, source_id, source_dict["source_name"], summary, tags
                )
                concept_page = WikiPage(
                    title=concept,
                    body=concept_body,
                    source_refs=[source_id],
                    tags=tags,
                    page_type="concept",
                )
                self.wiki.create_page(concept_page)
                result.pages_created.append(concept_slug)
                self.indexer.index_page(concept_page, extra_entities=entities)

            # Backlink: summary page → concept page
            self.wiki.add_backlink(concept_slug, summary_page.slug, "concept")

        result.concepts_extracted = concepts

        # 3. Mark compiled
        for s in manifest["sources"]:
            if s["source_id"] == source_id:
                s["compiled"] = True
                s["compiled_at"] = _now()
        _save_manifest(manifest)

        # 4. Lineage record
        _append_lineage({
            "event": "compile",
            "source_id": source_id,
            "source_name": source_dict["source_name"],
            "dispatch_id": source_dict.get("dispatch_id", ""),
            "pages_created": result.pages_created,
            "pages_updated": result.pages_updated,
            "concepts": concepts,
            "entities": entities,
            "llm_used": llm_used,
            "compiled_at": result.compiled_at,
        })

        return result

    def compile_all(self, force: bool = False) -> List[CompilationResult]:
        """Compile all uncompiled (or all if force=True) raw sources."""
        manifest = _load_manifest()
        results = []
        for s in manifest["sources"]:
            if force or not s.get("compiled"):
                results.append(self.compile(s["source_id"]))
        return results

    # ── QUERY ─────────────────────────────────────────────────────────────────

    def query(self, question: str, k: int = 5,
              mode: str = "hybrid") -> Dict[str, Any]:
        """
        Query compiled knowledge.

        mode="keyword"  — fast, no LLM
        mode="hybrid"   — keyword search + Gemini answer synthesis
        mode="entity"   — entity-index lookup

        Returns a dict with: pages, answer (if hybrid), entities_found.
        """
        pages = self.wiki.search(question, limit=k)
        entity_matches = self.indexer.lookup_entity(question)

        result: Dict[str, Any] = {
            "question": question,
            "mode": mode,
            "pages": [p.to_dict() for p in pages],
            "entity_matches": entity_matches,
            "answer": None,
        }

        if mode == "hybrid" and self._api_key and pages:
            result["answer"] = _gemini_qa(question, pages, self._api_key)
        elif mode == "hybrid" and not self._api_key:
            result["answer"] = (
                "[No GEMINI_API_KEY — keyword results above. "
                "Set GEMINI_API_KEY for synthesised answers.]"
            )

        _append_lineage({
            "event": "query",
            "question": question,
            "mode": mode,
            "pages_retrieved": [p["slug"] for p in result["pages"]],
            "llm_used": mode == "hybrid" and bool(self._api_key),
            "queried_at": _now(),
        })

        return result

    # ── AUDIT ─────────────────────────────────────────────────────────────────

    def audit(self) -> AuditReport:
        return self.auditor.run_audit(save=True)

    # ── STATS ─────────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        manifest = _load_manifest()
        sources = manifest.get("sources", [])
        compiled = [s for s in sources if s.get("compiled")]
        return {
            "raw_sources": len(sources),
            "compiled_sources": len(compiled),
            "pending_compilation": len(sources) - len(compiled),
            "wiki": self.wiki.stats(),
            "index": self.indexer.stats(),
            "api_key_set": bool(self._api_key),
        }

    # ── CONTRADICTION TRACKING ────────────────────────────────────────────────

    def flag_contradiction(self, page_slug_a: str, page_slug_b: str,
                           reason: str) -> str:
        """
        Flag a contradiction between two pages for review.
        Stored in governance/contradictions.json.
        Returns the contradiction ID.
        """
        GOVERNANCE_DIR.mkdir(parents=True, exist_ok=True)
        data: Dict[str, Any] = {"open": [], "resolved": []}
        if CONTRADICTIONS_PATH.exists():
            try:
                data = json.loads(CONTRADICTIONS_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass

        contradiction_id = f"contra_{_short_hash(page_slug_a + page_slug_b + reason)}"
        data["open"].append({
            "id": contradiction_id,
            "page_slug": page_slug_a,
            "page_slug_b": page_slug_b,
            "reason": reason,
            "flagged_at": _now(),
        })
        CONTRADICTIONS_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _append_lineage({
            "event": "contradiction_flagged",
            "id": contradiction_id,
            "pages": [page_slug_a, page_slug_b],
            "reason": reason,
            "flagged_at": _now(),
        })
        return contradiction_id

    def resolve_contradiction(self, contradiction_id: str, resolution: str) -> bool:
        if not CONTRADICTIONS_PATH.exists():
            return False
        data = json.loads(CONTRADICTIONS_PATH.read_text(encoding="utf-8"))
        match = next((c for c in data["open"] if c["id"] == contradiction_id), None)
        if not match:
            return False
        match["resolution"] = resolution
        match["resolved_at"] = _now()
        data["open"].remove(match)
        data["resolved"].append(match)
        CONTRADICTIONS_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return True

    # ── Body builders ─────────────────────────────────────────────────────────

    def _build_source_summary_body(self, source: Dict, summary: str,
                                   concepts: List[str], entities: List[str],
                                   tags: List[str]) -> str:
        concept_links = "  ".join(f"[[{c}]]" for c in concepts)
        entity_list = "\n".join(f"- {e}" for e in entities) if entities else "_none detected_"
        tag_list = " ".join(f"`{t}`" for t in tags)
        return f"""\
## Summary

{summary}

## Key Concepts

{concept_links}

## Entities

{entity_list}

## Tags

{tag_list}

## Source Metadata

- **File:** `{source['source_name']}`
- **Type:** {source['source_type']}
- **Size:** {source['char_count']:,} chars
- **Ingested:** {source['ingested_at']}
"""

    def _build_concept_body(self, concept: str, source_id: str,
                            source_name: str, context_summary: str,
                            tags: List[str]) -> str:
        return f"""\
## {concept}

First encountered in [[Source: {source_name}]].

### Context

{context_summary[:400]}

### See Also

_Add related concepts here using [[WikiLinks]]._

### Sources

- `{source_id}` — {source_name}
"""

    def _enrich_concept_body(self, page: WikiPage,
                             new_source_id: str, new_summary: str) -> str:
        body = page.body
        # Append new source ref under "### Sources" section
        src_header = "### Sources"
        entry = f"\n- `{new_source_id}` — via recompilation"
        if src_header in body:
            return body.replace(src_header, src_header + entry, 1)
        return body + f"\n\n{src_header}{entry}\n"
