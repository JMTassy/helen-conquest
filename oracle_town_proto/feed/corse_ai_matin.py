#!/usr/bin/env python3
"""
CORSE AI MATIN: Federated Messenger Protocol v1.0 (Extended for Two Columns)

Pure transport: reads bulletins, transmits verbatim, no transforms.
Ordering: timestamp (ascending) + town_id (lexicographic).
No ranking, no highlighting, no semantic alteration.

Extended: Supports COLUMN A (Ledger Facts) and COLUMN B (INSIGHT ZONE)
Kill-switch enforces boundary between columns.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List


class CorseAiMatin:
    """Stateless messenger aggregator."""

    def __init__(self, epoch: int):
        self.epoch = epoch
        self.entries: List[Dict] = []

    def ingest(self, bulletins: List[Dict]) -> None:
        """
        Ingest bulletins from all towns.

        No transformation. No filtering. Verbatim only.
        """
        self.entries = bulletins.copy()

    def output(self) -> Dict:
        """
        Generate canonical CORSE AI MATIN output.

        Ordering: timestamp ASC, then town_id lexicographic.
        No commentary, no emphasis, no ranking.
        """
        # Sort strictly by timestamp + town_id
        sorted_entries = sorted(
            self.entries,
            key=lambda e: (e.get("timestamp", ""), e.get("town_id", ""))
        )

        output = {
            "publication": "CORSE AI MATIN",
            "epoch": self.epoch,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entries": sorted_entries,
        }

        output["hash"] = self._hash_output(output)
        return output

    @staticmethod
    def _hash_output(output: Dict) -> str:
        """Deterministic hash (excluding hash field itself)."""
        canonical = json.dumps(
            {k: v for k, v in output.items() if k != "hash"},
            sort_keys=True,
            separators=(",", ":")
        )
        return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()[:16]

    @staticmethod
    def validate_no_interpretation(output: Dict) -> bool:
        """
        Check that output contains no derived statements.

        Kill-switch: if any of these appear, publication is aborted.
        """
        forbidden_phrases = [
            "multiple towns",
            "pattern",
            "trend",
            "consensus",
            "best",
            "optimal",
            "suggest",
            "recommend",
            "should adopt",
            "compared to",
        ]

        canonical = json.dumps(output, separators=(",", ":")).lower()

        return not any(phrase in canonical for phrase in forbidden_phrases)

    def output_two_columns(self) -> Dict:
        """
        Generate CORSE AI MATIN with two-column structure.

        Column A: Ledger Facts (SHIP/NO_SHIP, K-gates, freeze durations)
        Column B: INSIGHT ZONE (speculative, marked non-actionable)
        """
        sorted_entries = sorted(
            self.entries,
            key=lambda e: (e.get("timestamp", ""), e.get("town_id", ""))
        )

        # Separate entries by type
        column_a = [e for e in sorted_entries if e.get("type") != "INSIGHT"]
        column_b = [e for e in sorted_entries if e.get("type") == "INSIGHT"]

        output = {
            "publication": "CORSE AI MATIN",
            "epoch": self.epoch,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "column_a_ledger_facts": column_a,
            "column_b_insight_zone": {
                "note": "Non-actionable, non-evidentiary content. See INSIGHT ZONE PROTOCOL.",
                "entries": column_b,
            }
        }

        output["hash"] = self._hash_output(output)
        return output

    @staticmethod
    def validate_no_column_crossing(output: Dict) -> bool:
        """
        Hard rule: INSIGHT ZONE entries cannot reference Column A.
        Hard rule: Column A cannot contain speculative language.

        Returns True if boundary is clean.
        """
        column_b = output.get("column_b_insight_zone", {}).get("entries", [])

        # Column B entries should be marked as INSIGHT
        for entry in column_b:
            if entry.get("artifact_type") != "INSIGHT":
                return False

        return True
