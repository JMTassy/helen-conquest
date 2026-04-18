"""
helen_os/claim_graph/dialogue_ingest.py — Parse structured dialogue text → ClaimGraphV1.

Input:  Structured dialogue text (e.g. fixtures/decay_dialogue_v1.txt)
Output: ClaimGraphV1 (validated, with source_digest anchored to input text)

Grammar:
  ## CLAIMS
    <ID> [<ROLE>|<KIND>]: <text>
    (multi-word IDs allowed: PERF1, ARCH1, QA5, etc.)

  ## EDGES
    <SRC> <EDGE_TYPE> <DST>
    (one relation per line; edge_id auto-generated as "E-{src}->{dst}")

  ## AGREED CLAIMS (G-set)
    <ID1>, <ID2>, ...   OR   (none)

  ## RESIDUAL DISAGREEMENTS (R-set)
    <ID1>, <ID2>, ...   OR   (none)

  ## DECISION RULE
    <DR_ID>:
      rule_id: <ID>
      decision_variable: <VAR>
      domain: [<VAL1>, <VAL2>]
      rule_text: <text>
      depends_on: <ID1>, <ID2>, ...

  ## TASKS
    <T_ID> [<ROLE>|<KIND>]:
      text: <text>
      hypothesis: <text>
      validation_gate: <text>

Fail-closed:
  - Raises IngestError if any section fails to parse.
  - Warns (but does not fail) if no G-set declared (compute_sets() will derive it).
"""

from __future__ import annotations

import re
import textwrap
from typing import Any, Dict, List, Optional, Set, Tuple

from .canon   import sha256_text
from .schemas import (
    ClaimEdgeV1, ClaimGraphV1, ClaimNodeV1,
    DecisionRuleV1, TaskV1,
    Role, ClaimKind, EdgeType,
)


# ── Custom exception ──────────────────────────────────────────────────────────

class IngestError(ValueError):
    """Raised when the dialogue text cannot be parsed."""
    pass


# ── Section splitter ──────────────────────────────────────────────────────────

def _split_sections(text: str) -> Dict[str, str]:
    """
    Split text into sections keyed by ## HEADER (case-insensitive).

    Returns dict: {section_name_lower: content_string}
    A leading 'header' section (before first ##) is stored as 'header'.
    """
    sections: Dict[str, str] = {}
    current_name = "header"
    current_lines: List[str] = []

    for line in text.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            sections[current_name.strip().lower()] = "\n".join(current_lines).strip()
            current_name  = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    sections[current_name.strip().lower()] = "\n".join(current_lines).strip()
    return sections


def _strip_comments(text: str) -> str:
    """
    Remove single-# comment lines; preserve ## section headers.

    Lines starting with '##' are section delimiters — keep them.
    Lines starting with '#' (but not '##') are comments — strip them.
    """
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("##"):
            lines.append(line)       # keep section headers
        elif stripped.startswith("#"):
            pass                     # strip single-# comment line
        else:
            lines.append(line)
    return "\n".join(lines)


# ── Header parsing ────────────────────────────────────────────────────────────

def _parse_header(header_text: str, full_text: str) -> Tuple[str, str]:
    """Extract topic and scenario from the header comment block."""
    topic    = "Unknown decision"
    scenario = ""

    for line in full_text.splitlines():
        m = re.match(r"#\s+Scenario:\s+(.+)", line)
        if m:
            scenario = m.group(1).strip()
        m = re.match(r"#\s+Decision Variable:\s+(.+)", line)
        if m:
            topic = m.group(1).strip()

    if not topic:
        topic = "Structured Decision Dialogue"
    return topic, scenario


# ── Claim node parsing ────────────────────────────────────────────────────────

_CLAIM_PATTERN = re.compile(
    r"^(?P<node_id>[A-Z][A-Z0-9]*\d*)\s+"     # ID: H1, PERF1, QA5, ARCH1
    r"\[(?P<role>[A-Z]+)\|(?P<kind>[A-Z_]+)\]"  # [ROLE|KIND]
    r":\s+(?P<text>.+)$"                        # : text
)

VALID_ROLES  = {"HELEN", "HAL", "PM", "ARCH", "DEV", "QA"}
VALID_KINDS  = {"CONSTRAINT", "RISK", "BENEFIT", "FACT", "PROPOSAL", "GATE", "DEFINITION"}


def _parse_claims(section: str) -> List[ClaimNodeV1]:
    """Parse ## CLAIMS section → List[ClaimNodeV1]."""
    nodes: List[ClaimNodeV1] = []
    errors: List[str] = []

    for lineno, raw in enumerate(section.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        m = _CLAIM_PATTERN.match(line)
        if not m:
            errors.append(f"  line {lineno}: could not parse claim: {line!r}")
            continue

        node_id = m.group("node_id")
        role    = m.group("role").upper()
        kind    = m.group("kind").upper()
        text    = m.group("text").strip()

        if role not in VALID_ROLES:
            errors.append(f"  line {lineno}: unknown role {role!r} for node {node_id!r}")
            continue
        if kind not in VALID_KINDS:
            errors.append(f"  line {lineno}: unknown kind {kind!r} for node {node_id!r}")
            continue

        nodes.append(ClaimNodeV1(
            node_id = node_id,
            role    = role,      # type: ignore[arg-type]
            kind    = kind,      # type: ignore[arg-type]
            text    = text,
        ))

    if errors:
        raise IngestError(
            f"CLAIMS section parse errors:\n" + "\n".join(errors)
        )
    return nodes


# ── Edge parsing ──────────────────────────────────────────────────────────────

_EDGE_PATTERN = re.compile(
    r"^(?P<src>[A-Z][A-Z0-9]*)\s+"
    r"(?P<etype>SUPPORTS|OBJECTS_TO|REFINES|RETRACTS|DEPENDS_ON)\s+"
    r"(?P<dst>[A-Za-z][A-Za-z0-9]*)$"
)


def _parse_edges(section: str, node_ids: Set[str]) -> List[ClaimEdgeV1]:
    """Parse ## EDGES section → List[ClaimEdgeV1]."""
    edges:  List[ClaimEdgeV1] = []
    errors: List[str]         = []
    seen_pairs: Set[Tuple[str, str, str]] = set()

    for lineno, raw in enumerate(section.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        m = _EDGE_PATTERN.match(line)
        if not m:
            errors.append(f"  line {lineno}: could not parse edge: {line!r}")
            continue

        src   = m.group("src")
        etype = m.group("etype")
        dst   = m.group("dst")

        if src not in node_ids:
            errors.append(f"  line {lineno}: edge src={src!r} not in nodes")
            continue
        if dst not in node_ids and dst != "D":
            # "D" is the decision variable (not a node)
            # Skip validation for "D" — it's the external decision target
            if dst not in node_ids:
                errors.append(f"  line {lineno}: edge dst={dst!r} not in nodes")
                continue

        key = (src, etype, dst)
        if key in seen_pairs:
            continue  # deduplicate silently
        seen_pairs.add(key)

        edge_id = f"E-{src}->{dst}"
        # Handle duplicates: add suffix if needed
        count = sum(1 for e in edges if e.src == src and e.dst == dst)
        if count > 0:
            edge_id = f"E-{src}->{dst}#{count}"

        edges.append(ClaimEdgeV1(
            edge_id = edge_id,
            type    = etype,    # type: ignore[arg-type]
            src     = src,
            dst     = dst,
        ))

    if errors:
        raise IngestError("EDGES section parse errors:\n" + "\n".join(errors))
    return edges


# ── G-set / R-set parsing ─────────────────────────────────────────────────────

def _parse_id_list(section: str) -> List[str]:
    """Parse comma-separated ID list or '(none)' → List[str]."""
    text = section.strip()
    if not text or text.lower() in ("(none)", "none", ""):
        return []
    # Strip trailing comments
    text = re.sub(r"#.*$", "", text, flags=re.MULTILINE).strip()
    ids = [id_.strip() for id_ in re.split(r"[,\s]+", text) if id_.strip()]
    return ids


# ── Decision rule parsing ─────────────────────────────────────────────────────

def _parse_decision_rules(section: str) -> List[DecisionRuleV1]:
    """Parse ## DECISION RULE section → List[DecisionRuleV1]."""
    rules: List[DecisionRuleV1] = []
    if not section.strip():
        return rules

    # Split on rule blocks: each block starts with "DR\d+:"
    block_pattern = re.compile(r"^(DR\d+|DR[A-Z]*\d*):\s*$", re.MULTILINE)
    parts = block_pattern.split(section)

    # parts alternates: [pre, rule_id, block, rule_id, block, ...]
    i = 1
    while i < len(parts) - 1:
        rule_id   = parts[i].strip()
        block     = parts[i + 1].strip()
        i += 2

        # Parse key: value pairs from block
        kv: Dict[str, str] = {}
        for line in block.splitlines():
            m = re.match(r"^\s+(\w+):\s+(.+)$", line)
            if m:
                kv[m.group(1)] = m.group(2).strip()

        decision_variable = kv.get("decision_variable", "D")
        rule_text         = kv.get("rule_text", "")
        domain_str        = kv.get("domain", "[]")
        depends_str       = kv.get("depends_on", "")

        # Parse domain: [INCLUDE_V0.1, DEFER]
        domain_m = re.findall(r"[A-Z_\.0-9]+", domain_str)
        domain   = domain_m if domain_m else []

        # Parse depends_on: comma-separated
        depends = [d.strip() for d in depends_str.split(",") if d.strip()]

        rules.append(DecisionRuleV1(
            rule_id           = rule_id,
            decision_variable = decision_variable,
            domain            = domain,
            rule_text         = rule_text,
            depends_on        = depends,
        ))

    return rules


# ── Task parsing ──────────────────────────────────────────────────────────────

_TASK_HEADER = re.compile(
    r"^(?P<task_id>T\d+)\s+\[(?P<role>[A-Z]+)\|(?P<kind>[A-Z_]+)\]:\s*$"
)


def _parse_tasks(section: str) -> List[TaskV1]:
    """Parse ## TASKS section → List[TaskV1]."""
    tasks:  List[TaskV1] = []
    errors: List[str]    = []

    lines = section.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        m = _TASK_HEADER.match(line)
        if not m:
            i += 1
            continue

        task_id = m.group("task_id")
        role    = m.group("role").upper()
        # kind from header is informational; role is what matters for TaskV1
        i += 1

        # Collect key: value lines until next task header or end
        kv: Dict[str, str] = {}
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line or next_line.startswith("#"):
                i += 1
                continue
            if _TASK_HEADER.match(next_line):
                break  # start of next task
            kv_m = re.match(r"(\w+):\s+(.+)", next_line)
            if kv_m:
                kv[kv_m.group(1)] = kv_m.group(2).strip()
            i += 1

        if role not in VALID_ROLES:
            errors.append(f"Task {task_id}: unknown role {role!r}")
            continue

        text       = kv.get("text", "")
        hypothesis = kv.get("hypothesis", "")
        gate       = kv.get("validation_gate", "")

        if not text or not hypothesis or not gate:
            errors.append(
                f"Task {task_id}: missing required fields "
                f"(text={bool(text)}, hypothesis={bool(hypothesis)}, gate={bool(gate)})"
            )
            continue

        tasks.append(TaskV1(
            task_id         = task_id,
            role            = role,  # type: ignore[arg-type]
            text            = text,
            hypothesis      = hypothesis,
            validation_gate = gate,
        ))

    if errors:
        raise IngestError("TASKS section parse errors:\n" + "\n".join(errors))
    return tasks


# ── Top-level ingest ──────────────────────────────────────────────────────────

def ingest_dialogue(text: str) -> ClaimGraphV1:
    """
    Parse a structured dialogue text → ClaimGraphV1.

    Fail-closed: raises IngestError if any required section is missing or malformed.

    Validation checks (LOG A–D style):
      LOG A: source_digest anchors text; claims >= 1 required
      LOG B: edge endpoints validated against node set
      LOG C: DR depends_on validated against node set (see graph_ops.validate_dr_dependencies)
      LOG D: no authority tokens in node texts (SHIP, SEALED, APPROVED, DECIDE)

    Args:
        text: Raw dialogue text (e.g. from fixtures/decay_dialogue_v1.txt)

    Returns:
        ClaimGraphV1 with g_set/r_set from declared sets (or empty for compute_sets).

    Raises:
        IngestError: on parse failures (fail-closed).
    """
    # source_digest = SHA256(raw text)
    source_digest = sha256_text(text)

    # Strip comments + split sections
    clean = _strip_comments(text)
    secs  = _split_sections(clean)

    # ── Header ───────────────────────────────────────────────────────────────
    topic, scenario = _parse_header(secs.get("header", ""), text)

    # ── Claims ───────────────────────────────────────────────────────────────
    claims_sec = secs.get("claims", "")
    if not claims_sec.strip():
        raise IngestError("CLAIMS section is missing or empty — fail-closed")

    nodes  = _parse_claims(claims_sec)
    if len(nodes) < 1:
        raise IngestError(
            f"LOG A FAIL: expected >= 1 claims, got {len(nodes)} — fail-closed"
        )

    node_ids: Set[str] = {n.node_id for n in nodes}
    # Add "D" (the decision variable) to edge endpoint whitelist
    node_ids_with_d = node_ids | {"D"}

    # ── Edges ─────────────────────────────────────────────────────────────────
    edges_sec = secs.get("edges", "")
    edges = _parse_edges(edges_sec, node_ids_with_d)

    # Filter out edges where dst == "D" (external decision variable — not a node)
    # but keep them for structural analysis
    internal_edges = [e for e in edges if e.dst in node_ids]

    # ── G-set ─────────────────────────────────────────────────────────────────
    gset_sec = ""
    for key in secs:
        if "g-set" in key or "agreed" in key:
            gset_sec = secs[key]
            break
    g_set = _parse_id_list(gset_sec)

    # Validate G-set members exist
    bad_g = [nid for nid in g_set if nid not in node_ids]
    if bad_g:
        raise IngestError(
            f"LOG B FAIL: G-set members not in graph: {bad_g}"
        )

    # ── R-set ─────────────────────────────────────────────────────────────────
    rset_sec = ""
    for key in secs:
        if "r-set" in key or "residual" in key:
            rset_sec = secs[key]
            break
    r_set = _parse_id_list(rset_sec)

    # Validate R-set members exist
    bad_r = [nid for nid in r_set if nid not in node_ids]
    if bad_r:
        raise IngestError(
            f"LOG B FAIL: R-set members not in graph: {bad_r}"
        )

    # ── Decision rules ────────────────────────────────────────────────────────
    dr_sec = secs.get("decision rule", "")
    decision_rules = _parse_decision_rules(dr_sec)

    # ── Tasks ─────────────────────────────────────────────────────────────────
    tasks_sec = secs.get("tasks", "")
    tasks = _parse_tasks(tasks_sec)

    # ── LOG D: authority token scan ───────────────────────────────────────────
    _forbidden_tokens = {"SHIP", "SEALED", "APPROVED", "DECIDE", "FINAL_DECISION"}
    authority_violations = []
    for n in nodes:
        for tok in _forbidden_tokens:
            if tok in n.text.upper():
                authority_violations.append(
                    f"node {n.node_id!r} text contains forbidden token {tok!r}"
                )
    if authority_violations:
        raise IngestError(
            "LOG D FAIL: authority tokens in node texts:\n" +
            "\n".join(authority_violations)
        )

    return ClaimGraphV1(
        topic          = topic,
        scenario       = scenario,
        nodes          = nodes,
        edges          = internal_edges,
        g_set          = g_set,
        r_set          = r_set,
        decision_rules = decision_rules,
        tasks          = tasks,
        source_digest  = source_digest,
    )
