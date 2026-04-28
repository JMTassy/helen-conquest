# lifecycle: CANDIDATE
"""classify subcommand — read source, emit DRAFT KNOWLEDGE_ENTRY scaffold."""
from __future__ import annotations

import datetime as _dt
import re
import sys
from pathlib import Path

from .index import append as index_append
from .schema import (
    LOCKED_DOMAINS,
    SCAFFOLD_TEMPLATE,
    SOVEREIGN_PREFIXES,
    FailureCode,
)

CLASSIFIED_DIR = Path(__file__).parent.parent / "knowledge" / "classified"
PLUGIN_TAG_RE = re.compile(r"^(#plugin[A-Za-z0-9_ ]*?)(\.[A-Za-z0-9]+)?$", re.IGNORECASE)


def _refuse_sovereign(source_path: Path) -> str | None:
    rel = str(source_path)
    for prefix in SOVEREIGN_PREFIXES:
        if prefix in rel:
            return f"{FailureCode.SOVEREIGN_PATH_REFUSED}: {prefix} in {rel}"
    return None


def _extract_keyword(filename: str) -> str:
    """Return the source-native keyword exactly as it appears (whitespace + punct preserved)."""
    stem = filename
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]
    return stem


def _guess_domain(keyword: str) -> str:
    upper = keyword.upper()
    table: list[tuple[str, str]] = [
        ("AURA", "AURA_TEMPLE"),
        ("TEMPLE", "AURA_TEMPLE"),
        ("WUL", "WUL_SYMBOLIC_LANGUAGE"),
        ("LEGORACLE", "LEGORACLE_RECEIPTS"),
        ("ORACLE", "ORACLE_GOVERNANCE"),
        ("RIEMANN", "RIEMANN_MATH"),
        ("DIRECTOR", "DIRECTOR_VIDEO"),
        ("AUTORESEARCH", "AUTORESEARCH"),
        ("CONQUEST", "CONQUEST"),
        ("HELEN", "HELEN_OS"),
        ("AGI", "HELEN_OS"),
    ]
    for needle, dom in table:
        if needle in upper:
            return dom
    return "DOMAIN_MISFIT"


def classify_one(source_path: Path, dry_run: bool = True) -> dict:
    """Classify a single source. Returns metadata dict for index/log."""
    refusal = _refuse_sovereign(source_path)
    if refusal:
        return {"status": "REFUSED", "reason": refusal, "source_path": str(source_path)}

    if not source_path.exists():
        return {"status": "REFUSED", "reason": f"NOT_FOUND: {source_path}"}

    suffix = source_path.suffix.lower()
    if suffix == ".pdf":
        return {
            "status": "REFUSED",
            "reason": f"{FailureCode.PDF_NOT_SUPPORTED_V0_1}: pre-convert {source_path.name} to .txt and re-run",
            "source_path": str(source_path),
        }

    keyword = _extract_keyword(source_path.name)
    domain = _guess_domain(keyword)

    today = _dt.date.today().isoformat()
    safe_keyword = re.sub(r"[^A-Za-z0-9]+", "_", keyword).strip("_")
    out_filename = f"{today}-{safe_keyword}.md"
    out_path = CLASSIFIED_DIR / out_filename

    metadata = {
        "status": "PROPOSED" if dry_run else "WRITTEN",
        "keyword": keyword,
        "preserved_tag": keyword,
        "source_path": str(source_path),
        "source_corpus": "plugins" if "PLUGINS_JMT" in str(source_path) else "unknown",
        "source_format": suffix.lstrip(".") or "unknown",
        "domain": domain,
        "domain_misfit": domain == "DOMAIN_MISFIT",
        "out_path": str(out_path),
        "lifecycle": "DRAFT",
        "ingest_date": today,
    }

    if dry_run:
        return metadata

    if out_path.exists():
        metadata["status"] = "REFUSED"
        metadata["reason"] = f"OUTPUT_EXISTS: {out_path} — refusing to overwrite"
        return metadata

    body = SCAFFOLD_TEMPLATE.format(
        keyword=keyword,
        source_corpus=metadata["source_corpus"],
        source_path=metadata["source_path"],
        source_format=metadata["source_format"],
        preserved_tag=keyword,
        domain=domain if domain in LOCKED_DOMAINS else "DOMAIN_MISFIT",
        ingest_date=today,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    index_append({k: v for k, v in metadata.items() if k != "status"})
    return metadata


def classify(args) -> int:
    sources = [Path(s) for s in args.sources]
    if len(sources) > args.limit:
        print(f"REFUSED: {FailureCode.BATCH_LIMIT_EXCEEDED}: {len(sources)} > --limit {args.limit}", file=sys.stderr)
        return 2
    results = [classify_one(p, dry_run=args.dry_run) for p in sources]
    for r in results:
        line = " | ".join(f"{k}={v}" for k, v in r.items() if k in ("status", "keyword", "domain", "out_path", "reason"))
        print(line)
    refused = sum(1 for r in results if r["status"] == "REFUSED")
    return 1 if refused else 0
