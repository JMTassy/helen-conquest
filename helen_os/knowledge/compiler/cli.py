"""
HELEN Knowledge Compiler — CLI entry point.

Usage:
  hkc ingest <path> [--type document|code|transcript|article]
  hkc ingest-text "<text>" --title "My Source"
  hkc compile <source_id>
  hkc compile-all [--force]
  hkc query "<question>" [--mode keyword|hybrid|entity] [-k 5]
  hkc audit
  hkc stats
  hkc list-pages [--type concept|source_summary]
  hkc list-sources [--pending]
  hkc search "<term>"
  hkc contradict <slug_a> <slug_b> "<reason>"
  hkc resolve <contradiction_id> "<resolution>"
  hkc index-rebuild

Run from repo root:
  python -m helen_os.knowledge.compiler.cli <command>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is on the path
_ROOT = Path(__file__).parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from .compiler import KnowledgeCompiler


def _make_compiler() -> KnowledgeCompiler:
    return KnowledgeCompiler(gemini_api_key=os.environ.get("GEMINI_API_KEY"))


# ── Sub-commands ──────────────────────────────────────────────────────────────

def cmd_ingest(args, compiler: KnowledgeCompiler) -> int:
    try:
        rec = compiler.ingest(args.path, source_type=args.type)
        print(f"[INGESTED]  {rec.source_id}")
        print(f"  name:     {rec.source_name}")
        print(f"  type:     {rec.source_type}")
        print(f"  chars:    {rec.char_count:,}")
        print(f"  hash:     {rec.content_hash[:30]}…")
        print(f"\nNext: hkc compile {rec.source_id}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_ingest_text(args, compiler: KnowledgeCompiler) -> int:
    try:
        rec = compiler.ingest_text(args.text, title=args.title,
                                   source_type=args.type)
        print(f"[INGESTED]  {rec.source_id}")
        print(f"  name:     {rec.source_name}")
        print(f"\nNext: hkc compile {rec.source_id}")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


def cmd_compile(args, compiler: KnowledgeCompiler) -> int:
    print(f"Compiling {args.source_id} …")
    result = compiler.compile(args.source_id)
    print(result.summary())
    if result.pages_created:
        print(f"  pages created: {', '.join(result.pages_created)}")
    if result.pages_updated:
        print(f"  pages updated: {', '.join(result.pages_updated)}")
    if result.concepts_extracted:
        print(f"  concepts: {', '.join(result.concepts_extracted[:8])}")
    return 0 if result.success else 1


def cmd_compile_all(args, compiler: KnowledgeCompiler) -> int:
    results = compiler.compile_all(force=getattr(args, "force", False))
    if not results:
        print("Nothing to compile (all sources already compiled). Use --force to recompile.")
        return 0
    ok = sum(1 for r in results if r.success)
    fail = len(results) - ok
    print(f"Compiled {ok}/{len(results)} sources. Failures: {fail}")
    for r in results:
        print(f"  {r.summary()}")
    return 0 if fail == 0 else 1


def cmd_query(args, compiler: KnowledgeCompiler) -> int:
    result = compiler.query(args.question, k=args.k, mode=args.mode)
    print(f"Query: {result['question']!r}  mode={result['mode']}\n")
    if result.get("answer"):
        print("── Answer ───────────────────────────────────────")
        print(result["answer"])
        print()
    if result["pages"]:
        print(f"── Top {len(result['pages'])} wiki pages ──────────────────────────")
        for p in result["pages"]:
            print(f"  [{p['type']}] {p['title']}")
            if p.get("body_preview"):
                print(f"    {p['body_preview'][:100].strip()}")
    else:
        print("No matching pages found. Try ingesting and compiling some sources first.")
    if result["entity_matches"]:
        print(f"\nEntity index matched: {result['entity_matches']}")
    return 0


def cmd_audit(args, compiler: KnowledgeCompiler) -> int:
    print("Running health audit …")
    report = compiler.audit()
    print(report.summary())
    print(f"\nReport saved to governance/last_audit.json")
    return 0 if report.clean else 1


def cmd_stats(args, compiler: KnowledgeCompiler) -> int:
    stats = compiler.stats()
    print("── HELEN Knowledge Compiler ─────────────────────")
    print(f"  Raw sources:       {stats['raw_sources']}")
    print(f"  Compiled:          {stats['compiled_sources']}")
    print(f"  Pending:           {stats['pending_compilation']}")
    print(f"  API key set:       {'yes (Gemini)' if stats['api_key_set'] else 'no (keyword mode)'}")
    w = stats["wiki"]
    print(f"\n  Wiki pages:        {w['total_pages']} "
          f"({w['concept_pages']} concepts, {w['source_summaries']} summaries)")
    idx = stats["index"]
    print(f"  Entities indexed:  {idx['entities_indexed']}")
    print(f"  Entity refs total: {idx['total_entity_refs']}")
    if w.get("top_tags"):
        top = ", ".join(f"{t}({n})" for t, n in w["top_tags"][:6])
        print(f"  Top tags:          {top}")
    return 0


def cmd_list_pages(args, compiler: KnowledgeCompiler) -> int:
    page_type = getattr(args, "type", None)
    pages = compiler.wiki.list_pages(page_type=page_type)
    if not pages:
        print("No pages yet. Run `hkc compile-all` to populate the wiki.")
        return 0
    print(f"{'SLUG':<40} {'TYPE':<16} {'SOURCES':<8} TAGS")
    print("─" * 80)
    for p in pages:
        tags = ",".join(p.tags[:3])
        srcs = len(p.source_refs)
        print(f"{p.slug:<40} {p.page_type:<16} {srcs:<8} {tags}")
    print(f"\n{len(pages)} pages total.")
    return 0


def cmd_list_sources(args, compiler: KnowledgeCompiler) -> int:
    from .compiler import _load_manifest
    manifest = _load_manifest()
    sources = manifest.get("sources", [])
    pending_only = getattr(args, "pending", False)
    if pending_only:
        sources = [s for s in sources if not s.get("compiled")]
    if not sources:
        print("No sources found." if not pending_only else "No pending sources.")
        return 0
    print(f"{'SOURCE_ID':<20} {'NAME':<35} {'TYPE':<12} COMPILED")
    print("─" * 80)
    for s in sources:
        compiled = "✓" if s.get("compiled") else "–"
        print(f"{s['source_id']:<20} {s['source_name']:<35} {s['source_type']:<12} {compiled}")
    print(f"\n{len(sources)} source(s).")
    return 0


def cmd_search(args, compiler: KnowledgeCompiler) -> int:
    pages = compiler.wiki.search(args.term, limit=10)
    if not pages:
        print(f"No pages matched '{args.term}'.")
        return 0
    print(f"Search results for '{args.term}':\n")
    for p in pages:
        print(f"  [{p.page_type}] {p.title}")
        print(f"    {p.body[:120].strip()}")
        print()
    return 0


def cmd_contradict(args, compiler: KnowledgeCompiler) -> int:
    cid = compiler.flag_contradiction(args.slug_a, args.slug_b, args.reason)
    print(f"[FLAGGED] Contradiction ID: {cid}")
    print(f"  Pages: {args.slug_a} ↔ {args.slug_b}")
    print(f"  Reason: {args.reason}")
    return 0


def cmd_resolve(args, compiler: KnowledgeCompiler) -> int:
    ok = compiler.resolve_contradiction(args.contradiction_id, args.resolution)
    if ok:
        print(f"[RESOLVED] {args.contradiction_id}")
    else:
        print(f"[ERROR] Contradiction not found: {args.contradiction_id}", file=sys.stderr)
        return 1
    return 0


def cmd_index_rebuild(args, compiler: KnowledgeCompiler) -> int:
    print("Rebuilding entity index from wiki …")
    n = compiler.indexer.rebuild_from_wiki(compiler.wiki)
    print(f"Indexed {n} pages.")
    s = compiler.indexer.stats()
    print(f"  Entities: {s['entities_indexed']}")
    print(f"  Entity refs: {s['total_entity_refs']}")
    return 0


# ── Parser ────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hkc",
        description="HELEN Knowledge Compiler — ingest, compile, query, audit.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # ingest
    sp = sub.add_parser("ingest", help="Register a file or directory as a raw source")
    sp.add_argument("path", help="File or directory to ingest")
    sp.add_argument("--type", default="document",
                    choices=["document", "code", "transcript", "article"],
                    help="Source type (default: document)")

    # ingest-text
    sp = sub.add_parser("ingest-text", help="Ingest raw text directly")
    sp.add_argument("text", help="Text content to ingest")
    sp.add_argument("--title", required=True, help="Human-readable title for this source")
    sp.add_argument("--type", default="document",
                    choices=["document", "code", "transcript", "article"])

    # compile
    sp = sub.add_parser("compile", help="Compile a raw source into wiki pages")
    sp.add_argument("source_id", help="Source ID from the manifest (src_...)")

    # compile-all
    sp = sub.add_parser("compile-all", help="Compile all pending sources")
    sp.add_argument("--force", action="store_true",
                    help="Recompile already-compiled sources")

    # query
    sp = sub.add_parser("query", help="Query compiled knowledge")
    sp.add_argument("question", help="Question or search term")
    sp.add_argument("--mode", default="hybrid",
                    choices=["keyword", "hybrid", "entity"],
                    help="Query mode (default: hybrid)")
    sp.add_argument("-k", type=int, default=5, help="Number of pages to retrieve")

    # audit
    sub.add_parser("audit", help="Run health audit")

    # stats
    sub.add_parser("stats", help="Show compiler statistics")

    # list-pages
    sp = sub.add_parser("list-pages", help="List compiled wiki pages")
    sp.add_argument("--type", default=None,
                    choices=["concept", "source_summary"],
                    help="Filter by page type")

    # list-sources
    sp = sub.add_parser("list-sources", help="List raw sources")
    sp.add_argument("--pending", action="store_true",
                    help="Show only uncompiled sources")

    # search
    sp = sub.add_parser("search", help="Full-text search the wiki")
    sp.add_argument("term", help="Search term")

    # contradict
    sp = sub.add_parser("contradict",
                        help="Flag a contradiction between two wiki pages")
    sp.add_argument("slug_a")
    sp.add_argument("slug_b")
    sp.add_argument("reason")

    # resolve
    sp = sub.add_parser("resolve", help="Resolve a flagged contradiction")
    sp.add_argument("contradiction_id")
    sp.add_argument("resolution")

    # index-rebuild
    sub.add_parser("index-rebuild", help="Rebuild entity/backlink indexes from wiki")

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    compiler = _make_compiler()

    dispatch = {
        "ingest": cmd_ingest,
        "ingest-text": cmd_ingest_text,
        "compile": cmd_compile,
        "compile-all": cmd_compile_all,
        "query": cmd_query,
        "audit": cmd_audit,
        "stats": cmd_stats,
        "list-pages": cmd_list_pages,
        "list-sources": cmd_list_sources,
        "search": cmd_search,
        "contradict": cmd_contradict,
        "resolve": cmd_resolve,
        "index-rebuild": cmd_index_rebuild,
    }

    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        return 1
    return fn(args, compiler)


if __name__ == "__main__":
    sys.exit(main())
