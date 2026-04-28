# lifecycle: CANDIDATE
"""validate subcommand — lint a classified .md against the frozen schema."""
from __future__ import annotations

import re
from pathlib import Path

from .schema import (
    LOCKED_DOMAINS,
    LOCKED_LIFECYCLE_STATES,
    LOCKED_UNIT_TYPES,
    FailureCode,
)

CLASSIFIED_DIR = Path(__file__).parent.parent / "knowledge" / "classified"

REQUIRED_SECTIONS = (
    "## Source-native tag preservation",
    "## Detected domain",
    "## Extracted units",
    "## What should NOT be promoted to canon",
    "## Suggested future classifier rule",
)

KV_RE = re.compile(r"^([a-z_]+):\s*(.+)$")


def validate_file(path: Path) -> list[tuple[str, str]]:
    """Return list of (FAILURE_CODE, message). Empty list = PASS."""
    issues: list[tuple[str, str]] = []
    if not path.exists():
        return [("NOT_FOUND", str(path))]
    text = path.read_text(encoding="utf-8")

    # Required sections present?
    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(("MISSING_SECTION", f"{path.name}: {section}"))

    # Lifecycle declared?
    m = re.search(r"^lifecycle:\s*([A-Z_]+)$", text, re.MULTILINE)
    if not m:
        issues.append((FailureCode.MISSING_LIFECYCLE_STATE, str(path)))
    else:
        state = m.group(1)
        if state not in LOCKED_LIFECYCLE_STATES:
            issues.append((FailureCode.MISSING_LIFECYCLE_STATE, f"{path.name}: invalid state '{state}'"))

    # Domain valid?
    m = re.search(r"^domain:\s*(\S+)$", text, re.MULTILINE)
    if m:
        dom = m.group(1)
        if dom not in LOCKED_DOMAINS and dom != "DOMAIN_MISFIT":
            issues.append((FailureCode.INVALID_DOMAIN, f"{path.name}: '{dom}' not in locked domain list"))

    # Authority NON_SOVEREIGN?
    if "authority:" in text and "NON_SOVEREIGN" not in text:
        issues.append(("AUTHORITY_NOT_NON_SOVEREIGN", str(path)))

    # Unit-type subheadings, if present, must be in locked set
    unit_headers = re.findall(r"^### ([A-Z_]+)\s*$", text, re.MULTILINE)
    for h in unit_headers:
        if h not in LOCKED_UNIT_TYPES:
            issues.append((FailureCode.INVALID_UNIT_TYPE, f"{path.name}: '### {h}' not a locked unit type"))

    return issues


def validate(args) -> int:
    if args.path:
        targets = [Path(args.path)]
    else:
        targets = sorted(CLASSIFIED_DIR.glob("*.md"))
    if not targets:
        print("(no classified entries found)")
        return 0
    total_issues = 0
    for t in targets:
        issues = validate_file(t)
        if issues:
            total_issues += len(issues)
            for code, msg in issues:
                print(f"{t.name}: {code}: {msg}")
        else:
            print(f"{t.name}: PASS")
    if total_issues:
        print(f"--- {total_issues} issue(s) across {len(targets)} file(s)")
        return 1
    print(f"--- {len(targets)} file(s) PASS")
    return 0
