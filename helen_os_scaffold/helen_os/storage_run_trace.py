"""
storage_run_trace.py

Non-sovereign ledger for CWL EMOGLYPH style output.

RULE: This file holds:
- Visual/aesthetic output (CWL lines, emoji, narrative)
- HAL verdicts (informational only, not binding)
- Session mood/context
- Run-specific styling

THIS FILE IS NOT AUTHORITATIVE. It is narrative + telemetry only.
The source of truth for facts is memory.ndjson (non-sovereign structured facts).
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class RunTrace:
    """
    Non-sovereign trace log for CWL EMOGLYPH output.
    Purely for display, narrative, and telemetry.
    """

    def __init__(self, trace_path: str = "storage/run_trace.ndjson"):
        self.trace_path = trace_path
        os.makedirs(os.path.dirname(self.trace_path), exist_ok=True)

    def log_cwl_line(self, line: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a CWL EMOGLYPH ledger line (narrative only).

        Args:
            line: the CWL formatted line (e.g., "[LEDGER 001] 🜃 : ...")
            metadata: optional context (actor, session_id, mood, etc.)
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "cwl_narrative",
            "line": line,
            "metadata": metadata or {}
        }
        with open(self.trace_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_hal_verdict(self, verdict: Dict[str, Any], context: str = ""):
        """
        Log HAL verdict (informational telemetry, NOT binding).

        Args:
            verdict: dict with keys: verdict, reasons, checks
            context: description of what was reviewed
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "hal_telemetry",
            "verdict": verdict.get("verdict", "UNKNOWN"),
            "reasons": verdict.get("reasons", []),
            "context": context,
            "metadata": {"role": "hal", "authority": "informational_only"}
        }
        with open(self.trace_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_session_mood(self, epoch: str, district: str, aesthetic: str, notes: str = ""):
        """
        Log session context (mood, aesthetic, district).
        Pure narrative, non-binding.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "session_mood",
            "epoch": epoch,
            "district": district,
            "aesthetic": aesthetic,
            "notes": notes
        }
        with open(self.trace_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_trace(self) -> list:
        """Return full run trace (for display/debugging)."""
        trace = []
        if os.path.exists(self.trace_path):
            with open(self.trace_path, "r") as f:
                for line in f:
                    if line.strip():
                        trace.append(json.loads(line))
        return trace
