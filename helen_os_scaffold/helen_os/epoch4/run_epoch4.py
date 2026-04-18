"""
helen_os/epoch4/run_epoch4.py — Canonical CLAIM_GRAPH_V1 artifact pipeline.

Spec: "CONQUEST: HELEN↔HAL Hard Mode — Dialogue → Receipt"

Pipeline:
  1. Parse:    ingest_dialogue(text) → ClaimGraphV1
  2. Validate: validate_graph(graph) — structural invariants
  3. Compute:  compute_sets(graph)   — derive G-set / R-set mechanically
  4. Propose:  kernel.propose(...)   — anchor in receipt chain

Output receipt schema (CLAIM_GRAPH_V1):
  type, topic, scenario, node_count, edge_count, g_set, r_set,
  g_set_count, r_set_count, dr_ids, task_ids, source_digest

Logs emitted:
  LOG A: claims extracted count
  LOG B: edge count, G-set size, R-set size
  LOG C: DR depends_on validation result
  LOG D: authority token scan result

"No receipt → no decision."
Non-sovereign: :memory: kernel only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..claim_graph.dialogue_ingest import ingest_dialogue, IngestError
from ..claim_graph.graph_ops       import validate_graph, compute_sets, validate_dr_dependencies
from ..claim_graph.schemas         import ClaimGraphV1
from ..claim_graph.canon           import sha256_canon, sha256_text


# ── Epoch4 result ─────────────────────────────────────────────────────────────

@dataclass
class Epoch4Result:
    """
    Output of run_epoch4().

    Fields:
      graph:          Fully validated + computed ClaimGraphV1
      receipt_id:     Receipt ID from kernel.propose() (anchors graph)
      cum_hash:       Final cum_hash of the governance kernel
      log_a:          Claims extracted count
      log_b:          Edge / G-set / R-set counts
      log_c:          DR depends_on validation status
      log_d:          Authority token scan result
      run_at:         ISO8601 timestamp
    """
    graph:      ClaimGraphV1
    receipt_id: str
    cum_hash:   str
    log_a:      Dict[str, Any]
    log_b:      Dict[str, Any]
    log_c:      Dict[str, Any]
    log_d:      Dict[str, Any]
    run_at:     str

    def to_artifact(self) -> Dict[str, Any]:
        """Serialize as EPOCH4_RUN_V1 artifact dict (for Pattern A sealing)."""
        return {
            "type":             "EPOCH4_RUN_V1",
            "graph":            self.graph.model_dump(),
            "receipt_id":       self.receipt_id,
            "cum_hash":         self.cum_hash,
            "logs": {
                "log_a": self.log_a,
                "log_b": self.log_b,
                "log_c": self.log_c,
                "log_d": self.log_d,
            },
            "run_at":           self.run_at,
        }


# ── Canonical runner ──────────────────────────────────────────────────────────

def run_epoch4(
    dialogue_text: str,
    ledger_path:   str = ":memory:",
) -> Epoch4Result:
    """
    Run the CLAIM_GRAPH_V1 artifact pipeline from a structured dialogue text.

    Args:
        dialogue_text: Raw structured dialogue text (from fixtures/).
        ledger_path:   Kernel path (default: :memory: — non-sovereign).

    Returns:
        Epoch4Result with graph + receipt + logs.

    Raises:
        IngestError: if dialogue_text fails to parse (fail-closed).
        ValueError:  if graph fails structural validation.
    """
    from ..kernel import GovernanceVM

    run_at = datetime.now(timezone.utc).isoformat()
    km     = GovernanceVM(ledger_path=ledger_path)

    # ── Step 1: Parse ─────────────────────────────────────────────────────────
    graph = ingest_dialogue(dialogue_text)

    # LOG A: claims extracted
    log_a = {
        "status":       "PASS",
        "claims_count": len(graph.nodes),
        "edges_count":  len(graph.edges),
        "tasks_count":  len(graph.tasks),
        "dr_count":     len(graph.decision_rules),
        "source_digest":graph.source_digest,
    }
    if len(graph.nodes) < 1:
        log_a["status"] = "FAIL"
        raise IngestError(f"LOG A FAIL: {len(graph.nodes)} claims extracted — expected >= 1")

    # ── Step 2: Structural validation ─────────────────────────────────────────
    validate_graph(graph)

    # LOG B: edge + set counts
    log_b = {
        "status":        "PASS",
        "edge_count":    len(graph.edges),
        "g_set_declared":len(graph.g_set),
        "r_set_declared":len(graph.r_set),
        "objects_to_edges": sum(1 for e in graph.edges if e.type == "OBJECTS_TO"),
    }

    # ── Step 3: Compute G-set / R-set ─────────────────────────────────────────
    graph = compute_sets(graph)

    log_b["g_set_final"] = len(graph.g_set)
    log_b["r_set_final"] = len(graph.r_set)

    # ── Step 4: DR dependency validation ─────────────────────────────────────
    log_c = {"status": "PASS", "dr_ids": [dr.rule_id for dr in graph.decision_rules]}
    try:
        validate_dr_dependencies(graph)
        log_c["message"] = "All DR dependencies are CONSTRAINT or GATE kind"
    except ValueError as e:
        log_c["status"]  = "FAIL"
        log_c["message"] = str(e)
        raise

    # LOG D: no authority tokens (already checked in ingest_dialogue)
    log_d = {
        "status":  "PASS",
        "message": "No forbidden authority tokens (SHIP/SEALED/APPROVED) in node texts",
    }

    # ── Step 5: Emit CLAIM_GRAPH_V1 receipt ───────────────────────────────────
    receipt = km.propose(graph.to_receipt_payload())

    return Epoch4Result(
        graph      = graph,
        receipt_id = receipt.id,
        cum_hash   = receipt.cum_hash,
        log_a      = log_a,
        log_b      = log_b,
        log_c      = log_c,
        log_d      = log_d,
        run_at     = run_at,
    )


def run_epoch4_from_file(
    fixture_path: str = "fixtures/decay_dialogue_v1.txt",
    ledger_path:  str = ":memory:",
) -> Epoch4Result:
    """
    Convenience wrapper: read fixture file → run_epoch4().

    Args:
        fixture_path: Path to the structured dialogue fixture.
        ledger_path:  Kernel path (default: :memory:).
    """
    text = Path(fixture_path).read_text(encoding="utf-8")
    return run_epoch4(text, ledger_path=ledger_path)
