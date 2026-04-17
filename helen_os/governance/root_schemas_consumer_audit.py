"""E15 — Root schemas consumer audit (non-sovereign, audit-only).

Classify every file under `schemas/` (repo-root schemas, NOT helen_os/schemas/)
by who references it in the current main tree. This is a diagnostic; it does
not mutate, delete, or move any file.

Classification rules (per schema file):
  - CONSUMED_RUNTIME: at least one `.py` file references the schema path
    (basename or relative path), outside the schema file itself and outside
    `.claude/worktrees/` and `.git/`.
  - DOCUMENTED_ONLY:  zero runtime references, ≥1 `.md` reference.
  - ORPHAN_ZERO_REF:  zero runtime references AND zero doc references.

Scope exclusions (treated as out of main tree):
  - .claude/worktrees/**
  - .git/**
  - schemas/* itself (self-reference) — but references from OTHER schemas in
    the same dir (e.g. $ref) are counted as runtime.

This is an audit tool. It emits a JSON report; it does not decide keep/delete.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
EXCLUDE_DIRS = [".claude/worktrees/", ".git/"]


def _list_schema_files() -> List[Path]:
    return sorted(SCHEMAS_DIR.glob("*.json"))


def _search(needle: str) -> List[str]:
    """Return list of files (repo-relative) that contain `needle`.

    Excludes worktrees, .git, and the schemas/ dir itself (self-reference),
    but INCLUDES references from other schemas (e.g. $ref across schemas/).
    Uses `git grep` for speed and correct .gitignore handling; falls back to
    a pure-Python walk if git is unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "grep", "-l", "--", needle],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode not in (0, 1):  # 1 = no matches
            raise RuntimeError(result.stderr.strip())
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception:
        files = []
        for p in REPO_ROOT.rglob("*"):
            if not p.is_file():
                continue
            rel = str(p.relative_to(REPO_ROOT))
            if any(rel.startswith(ex) for ex in EXCLUDE_DIRS):
                continue
            try:
                if needle in p.read_text(encoding="utf-8", errors="ignore"):
                    files.append(rel)
            except Exception:
                continue

    filtered = []
    for f in files:
        if any(f.startswith(ex) for ex in EXCLUDE_DIRS):
            continue
        filtered.append(f)
    return filtered


def classify_one(schema_path: Path) -> Tuple[str, Dict]:
    """Return (status, detail) for a single schema."""
    basename = schema_path.name
    rel_path = f"schemas/{basename}"

    hits_base = set(_search(basename))
    hits_rel = set(_search(rel_path))
    hits = hits_base | hits_rel
    hits.discard(rel_path)

    runtime_hits = sorted([h for h in hits if h.endswith(".py")])
    doc_hits = sorted([h for h in hits if h.endswith(".md") or h.endswith(".rst") or h.endswith(".txt")])
    schema_hits = sorted([h for h in hits if h.endswith(".json") and h != rel_path])
    other_hits = sorted([h for h in hits if h not in runtime_hits and h not in doc_hits and h not in schema_hits])

    if runtime_hits or schema_hits:
        status = "CONSUMED_RUNTIME"
    elif doc_hits:
        status = "DOCUMENTED_ONLY"
    else:
        status = "ORPHAN_ZERO_REF"

    return status, {
        "file": rel_path,
        "runtime_refs": runtime_hits,
        "schema_refs": schema_hits,
        "doc_refs": doc_hits,
        "other_refs": other_hits,
    }


def audit() -> Dict:
    files = _list_schema_files()
    buckets: Dict[str, List[dict]] = {
        "CONSUMED_RUNTIME": [],
        "DOCUMENTED_ONLY": [],
        "ORPHAN_ZERO_REF": [],
    }
    for f in files:
        status, detail = classify_one(f)
        buckets[status].append(detail)

    return {
        "schemas_dir": str(SCHEMAS_DIR.relative_to(REPO_ROOT)),
        "total_files": len(files),
        "consumed_runtime_count": len(buckets["CONSUMED_RUNTIME"]),
        "documented_only_count": len(buckets["DOCUMENTED_ONLY"]),
        "orphan_zero_ref_count": len(buckets["ORPHAN_ZERO_REF"]),
        "exclude_paths": EXCLUDE_DIRS,
        "buckets": buckets,
    }


def main() -> int:
    print(json.dumps(audit(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
