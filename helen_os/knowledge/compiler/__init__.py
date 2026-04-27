"""
HELEN_KNOWLEDGE_COMPILER_V1

Four-layer knowledge compiler:
  Raw        — raw source ingestion (files, text, transcripts)
  Compiled   — LLM-maintained wiki (concept pages, source summaries, indexes)
  Derived    — query outputs (Q&A, briefings) — produced on demand, not stored
  Governance — lineage log, contradiction tracker, health audits

Entry points:
  from helen_os.knowledge.compiler import KnowledgeCompiler
  compiler = KnowledgeCompiler()
  rec = compiler.ingest("path/to/doc.md")
  result = compiler.compile(rec.source_id)
  answer = compiler.query("what is LEGORACLE?")

CLI:
  python -m helen_os.knowledge.compiler.cli --help
"""

from .compiler import KnowledgeCompiler, CompilationResult, RawSource
from .wiki import WikiPage, WikiManager
from .indexer import KnowledgeIndexer
from .auditor import HealthAuditor, AuditReport, FindingType

__all__ = [
    "KnowledgeCompiler",
    "CompilationResult",
    "RawSource",
    "WikiPage",
    "WikiManager",
    "KnowledgeIndexer",
    "HealthAuditor",
    "AuditReport",
    "FindingType",
]
