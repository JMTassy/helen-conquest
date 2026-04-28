# lifecycle: CANDIDATE
"""Frozen v0.1 schema for KNOWLEDGE_ENTRY artifacts. Hard-coded, intentional."""
from __future__ import annotations

# ─── Locked domain whitelist (operator-authored 2026-04-26) ──────────────────
LOCKED_DOMAINS: tuple[str, ...] = (
    "HELEN_OS",
    "RIEMANN_MATH",
    "WUL_SYMBOLIC_LANGUAGE",
    "ORACLE_GOVERNANCE",
    "LEGORACLE_RECEIPTS",
    "AURA_TEMPLE",
    "DIRECTOR_VIDEO",
    "AUTORESEARCH",
    "CONQUEST",
)

# ─── Locked unit-type whitelist ──────────────────────────────────────────────
LOCKED_UNIT_TYPES: tuple[str, ...] = (
    "RAW_NOTE",
    "CLAIM",
    "FRAMEWORK",
    "THEOREM_DRAFT",
    "PROMPT_PATTERN",
    "OPERATING_RULE",
    "OPEN_QUESTION",
    "RECEIPT_CANDIDATE",
)

# ─── Locked lifecycle states (mirrors ARTIFACT_LIFECYCLE_V1 §C) ──────────────
LOCKED_LIFECYCLE_STATES: tuple[str, ...] = (
    "RAW", "DRAFT", "CANDIDATE", "RECEIPTED", "ACTIVE", "CANONICAL",
    "REJECTED", "SUPERSEDED",  # terminals
)

# ─── Sovereign-firewall paths (mirrors global ~/.claude/CLAUDE.md) ───────────
# Refuse to classify any source whose absolute path falls under these prefixes.
SOVEREIGN_PREFIXES: tuple[str, ...] = (
    "oracle_town/kernel/",
    "helen_os/governance/",
    "helen_os/schemas/",
    "town/ledger_v1",
    "GOVERNANCE/CLOSURES/",
    "GOVERNANCE/TRANCHE_RECEIPTS/",
)

# ─── Failure codes (mirrors ARTIFACT_LIFECYCLE_V1 §E) ────────────────────────
class FailureCode:
    MISSING_LIFECYCLE_STATE = "MISSING_LIFECYCLE_STATE"
    DRAFT_CITED_AS_AUTHORITY = "DRAFT_CITED_AS_AUTHORITY"
    SCAFFOLD_INVOKED_LIVE = "SCAFFOLD_INVOKED_LIVE"
    EXECUTE_BELOW_CANDIDATE = "EXECUTE_BELOW_CANDIDATE"
    GOVERN_BELOW_CANONICAL = "GOVERN_BELOW_CANONICAL"
    # helen_claims-specific
    INVALID_DOMAIN = "INVALID_DOMAIN"
    INVALID_UNIT_TYPE = "INVALID_UNIT_TYPE"
    SOVEREIGN_PATH_REFUSED = "SOVEREIGN_PATH_REFUSED"
    PDF_NOT_SUPPORTED_V0_1 = "PDF_NOT_SUPPORTED_V0_1"
    BATCH_LIMIT_EXCEEDED = "BATCH_LIMIT_EXCEEDED"
    TAG_NOT_FOUND = "TAG_NOT_FOUND"

# ─── Frozen scaffold for new KNOWLEDGE_ENTRY artifacts ───────────────────────
SCAFFOLD_TEMPLATE = """\
# KNOWLEDGE_ENTRY: {keyword}

```
lifecycle:        DRAFT
artifact_type:    KNOWLEDGE_ENTRY
authority:        NON_SOVEREIGN
source_corpus:    {source_corpus}
source_path:      {source_path}
source_format:    {source_format}
preserved_tag:    {preserved_tag}
domain:           {domain}
secondary_domains: []
ingest_date:      {ingest_date}
extraction_quality: PENDING
confidence:       PENDING
```

---

## Source-native tag preservation

(operator: confirm `preserved_tag` is exact whitespace + punctuation match to filename)

## Detected domain

Primary: {domain}

## Extracted units

### CLAIM
(operator: fill)

### FRAMEWORK
(operator: fill)

### THEOREM_DRAFT
(operator: fill — preserve LaTeX as raw blocks)

### OPERATING_RULE
(operator: fill)

### OPEN_QUESTION
(operator: fill)

### PROMPT_PATTERN
(operator: fill)

### RECEIPT_CANDIDATE
(operator: fill)

## What should NOT be promoted to canon

(operator: fill — at least one line required for v0.1 lint)

## Suggested future classifier rule

(operator: fill — what would a tool need to do better here?)
"""
