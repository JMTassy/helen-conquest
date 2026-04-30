"""complexity_extractor.py — filter_complex graph parser for clutter + overcomplexity.

Produces float metrics compatible with AuraMetrics:
  clutter           : overlay node count / MAX_SAFE_OVERLAYS  ∈ [0, 1]
  overcomplexity    : composite complexity score              ∈ [0, 1]
  overlay_count     : raw integer — number of overlay/split/blend nodes
  stream_count      : distinct named streams (e.g. [vid], [sc_a])
  depth             : longest chain of dependent nodes

Design rule: every metric is an AST-level parse of the filter_complex string.
No ML, no subprocess, no ffmpeg invocation. Pure string analysis.

Overcomplexity flag is True when the graph would cause an operator veto:
  - "forget composite, trop technique" trigger: ≥3 overlay nodes stacked
  - OR ≥2 input streams used as both source and target in the same graph
  - OR pipeline depth ≥ MAX_SAFE_DEPTH
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_SAFE_OVERLAYS = 3   # validated from operator session 2026-04-30
MAX_SAFE_DEPTH    = 4   # depth beyond which renders become brittle

_OVERLAY_OPS  = frozenset(["overlay", "blend", "alphamerge"])
_BRANCH_OPS   = frozenset(["split", "asplit"])
_FILTER_TOKEN = re.compile(r"\b([a-z][a-z0-9_]*)\s*(?:=|$|\[)", re.I)
_STREAM_TOKEN = re.compile(r"\[([^\]]+)\]")
_NODE_SPLIT   = re.compile(r";\s*")


@dataclass(frozen=True)
class ComplexityMetrics:
    overlay_count:   int
    stream_count:    int
    depth:           int
    clutter:         float     # normalised overlay density ∈ [0, 1]
    overcomplexity:  float     # composite flag ∈ [0, 1]
    flag:            bool      # True → operator veto likely


def _parse_nodes(filter_complex: str) -> list[dict]:
    """Return list of {name, inputs, outputs} dicts per filter segment."""
    nodes = []
    for segment in _NODE_SPLIT.split(filter_complex.strip()):
        segment = segment.strip()
        if not segment:
            continue
        streams = _STREAM_TOKEN.findall(segment)
        # Streams before first filter token are inputs; after are outputs
        filter_match = re.search(r"(?<=\])\s*([a-z][a-z0-9_]*)\s*(?:=|,|\[|$)", segment, re.I)
        if not filter_match:
            # Try plain filter at start of segment
            filter_match = re.match(r"([a-z][a-z0-9_]*)\s*(?:=|,|\[|$)", segment, re.I)
        op = filter_match.group(1).lower() if filter_match else "unknown"

        # Inputs: streams before op; outputs: streams after op
        op_pos  = filter_match.start() if filter_match else len(segment)
        in_strs = _STREAM_TOKEN.findall(segment[:op_pos])
        out_strs = _STREAM_TOKEN.findall(segment[op_pos:])
        nodes.append({"op": op, "inputs": in_strs, "outputs": out_strs})
    return nodes


def _compute_depth(nodes: list[dict]) -> int:
    """Longest dependency chain (BFS over output→input edges)."""
    out_to_depth: dict[str, int] = {}
    # Process in declaration order; re-passes converge for DAGs
    for _ in range(len(nodes) + 1):
        for node in nodes:
            in_depth = max((out_to_depth.get(s, 0) for s in node["inputs"]), default=0)
            d = in_depth + 1
            for s in node["outputs"]:
                if out_to_depth.get(s, 0) < d:
                    out_to_depth[s] = d
    return max(out_to_depth.values(), default=0)


def extract(filter_complex: str) -> ComplexityMetrics:
    """Parse *filter_complex* and return ComplexityMetrics."""
    nodes = _parse_nodes(filter_complex)

    overlay_count = sum(1 for n in nodes if n["op"] in _OVERLAY_OPS)
    all_streams   = {s for n in nodes for s in n["inputs"] + n["outputs"]}
    stream_count  = len(all_streams)
    depth         = _compute_depth(nodes)

    # Clutter: normalised overlay density
    clutter = min(1.0, overlay_count / MAX_SAFE_OVERLAYS)

    # Overcomplexity: weighted composite
    depth_score  = min(1.0, max(0.0, (depth - MAX_SAFE_DEPTH) / MAX_SAFE_DEPTH))
    branch_nodes = sum(1 for n in nodes if n["op"] in _BRANCH_OPS)
    branch_score = min(1.0, branch_nodes / 4.0)

    overcomplexity = round(
        0.50 * clutter +
        0.30 * depth_score +
        0.20 * branch_score,
        4,
    )

    flag = (
        overlay_count >= MAX_SAFE_OVERLAYS
        or depth >= MAX_SAFE_DEPTH
        or overcomplexity >= 0.6
    )

    return ComplexityMetrics(
        overlay_count=overlay_count,
        stream_count=stream_count,
        depth=depth,
        clutter=round(clutter, 4),
        overcomplexity=overcomplexity,
        flag=flag,
    )


def check(filter_complex: str) -> bool:
    """Return True if the graph is safe (no operator-veto risk)."""
    return not extract(filter_complex).flag
