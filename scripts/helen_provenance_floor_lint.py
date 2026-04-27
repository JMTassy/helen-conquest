#!/usr/bin/env python3
"""helen_provenance_floor_lint.py — SOURCE_PROVENANCE_FLOOR enforcement.

Defensive lint per SACRED_PATTERN_EXTRACTION_META_ANALYSIS_V1 §12 RULE 8 +
SACRED_INFORMATION_INGESTION_V1 §5.

Rule:
  If a knowledge artifact has parseable frontmatter but lacks BOTH:
    - any field from PROVENANCE_FIELDS family
    - any field from ORIGIN_FIELDS family
  then its declared lifecycle is forced to RAW_SOURCE. The lint emits
  LIFECYCLE_FLOOR_VIOLATED if the file declares a lifecycle past RAW.

  If a file has no parseable frontmatter at all, it is skipped (not flagged).

Scope (default):
  helen_os/knowledge/**/*.md
  temple/subsandbox/aura/grimoire/**/*.md

Optional target args:
  Pass one or more paths (file or directory) to lint that subset instead.
  Useful for ad-hoc checks and synthetic tests.

Read-only. Walks files; never mutates anything.

Exit:
  0  PASS  no violations
  1  FAIL  any violation
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

PROVENANCE_FIELDS = {
    "source_path", "source_path_or_url", "source_url",
    "source_format", "source_id", "source_ref",
    "provenance",
    "parent_scan", "parent_lens", "parent_manifest", "parent_meta",
    "parent_protocol",
    "related_manifest", "related_lens", "related_protocol",
    "sibling_artifact", "sibling_channel", "sibling_protocol",
    "session_seed",
    "samples_used", "filename_survey", "sample_budget",
}

ORIGIN_FIELDS = {
    "origin", "captured_by", "captured_on", "generated_by",
    "witness_class", "source_corpus",
}

NON_RAW_LIFECYCLES = {
    "DRAFT", "DRAFT_READING", "CLASSIFIED_SYMBOL", "CLASSIFIED",
    "RECEIPT_CANDIDATE", "ACTIVE", "ADMITTED", "CANONICAL",
}

DEFAULT_ROOTS = [
    Path("helen_os/knowledge"),
    Path("temple/subsandbox/aura/grimoire"),
]

FRONTMATTER_YAML = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FRONTMATTER_FENCED = re.compile(r"```[a-zA-Z0-9_]*\s*\n(.*?)\n```", re.DOTALL)


def extract_frontmatter(text: str) -> Optional[str]:
    m_yaml = FRONTMATTER_YAML.match(text)
    if m_yaml:
        return m_yaml.group(1)
    head_lines = text.split("\n")[:80]
    head = "\n".join(head_lines)
    m_fenced = FRONTMATTER_FENCED.search(head)
    if m_fenced:
        return m_fenced.group(1)
    return None


def parse_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in block.split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*?)(?:\s+#.*)?$", line)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()
            fields[key] = val
    return fields


def classify(text: str) -> tuple[str, str]:
    """Return (verdict, detail).

    verdict in:
      OK
      NO_FRONTMATTER
      MISSING_PROVENANCE  (declared lifecycle is RAW or absent — informational)
      LIFECYCLE_FLOOR_VIOLATED  (declared lifecycle past RAW + missing fields)
    """
    block = extract_frontmatter(text)
    if block is None:
        return ("NO_FRONTMATTER", "no frontmatter detected (skipped)")
    fields = parse_fields(block)
    keys = set(fields.keys())
    has_provenance = bool(keys & PROVENANCE_FIELDS)
    has_origin = bool(keys & ORIGIN_FIELDS)
    if has_provenance and has_origin:
        return ("OK", "")
    if not has_provenance and not has_origin:
        missing = "both provenance + origin"
    elif not has_provenance:
        missing = "provenance"
    else:
        missing = "origin"
    lifecycle_raw = fields.get("lifecycle") or fields.get("Lifecycle") or ""
    lifecycle_token = lifecycle_raw.split()[0].upper() if lifecycle_raw else ""
    if lifecycle_token in NON_RAW_LIFECYCLES:
        return ("LIFECYCLE_FLOOR_VIOLATED",
                f"declared lifecycle={lifecycle_token} but missing {missing}")
    return ("MISSING_PROVENANCE", missing)


def resolve_targets(repo_root: Path, argv: list[str]) -> list[Path]:
    if argv:
        return [Path(a).expanduser().resolve() for a in argv]
    return [repo_root / r for r in DEFAULT_ROOTS]


def collect_paths(target: Path) -> list[Path]:
    if not target.exists():
        return []
    if target.is_file():
        return [target] if target.suffix == ".md" else []
    return sorted(target.rglob("*.md"))


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    targets = resolve_targets(repo_root, argv)
    ok = skipped = violations = 0
    print(f"helen_provenance_floor_lint @ {repo_root}")
    print("=" * 64)
    for target in targets:
        for path in collect_paths(target):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                violations += 1
                try:
                    rel = path.relative_to(repo_root)
                except ValueError:
                    rel = path
                print(f"  ERROR  {rel}: {exc}")
                continue
            verdict, detail = classify(text)
            try:
                rel = path.relative_to(repo_root)
            except ValueError:
                rel = path
            if verdict == "OK":
                ok += 1
            elif verdict == "NO_FRONTMATTER":
                skipped += 1
            elif verdict == "MISSING_PROVENANCE":
                violations += 1
                print(f"  FAIL   {rel}")
                print(f"         MISSING_PROVENANCE: {detail}")
            elif verdict == "LIFECYCLE_FLOOR_VIOLATED":
                violations += 1
                print(f"  FAIL   {rel}")
                print(f"         LIFECYCLE_FLOOR_VIOLATED: {detail}")
    print("=" * 64)
    print(f"OK={ok}  SKIPPED={skipped}  FAIL={violations}")
    if violations == 0:
        print("VERDICT: PASS  (helen_provenance_floor=PASS)")
        return 0
    print("VERDICT: FAIL  (helen_provenance_floor=FAIL)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
