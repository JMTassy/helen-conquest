import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

class MemoryKernel:
    """
    Dual-channel memory (CONSTITUTION-SAFE):
    1. Conversational (NDJSON): append-only, structured facts only (NO authority tokens)
    2. Structured (SQLite): fast search and retrieval

    RULE: memory.ndjson contains ONLY non-sovereign observations.
    Authority verdicts go to storage/run_trace.ndjson (separate file).
    """

    # Authority tokens that MUST NEVER appear in memory
    FORBIDDEN_TOKENS = {
        "LEDGER", "SEAL", "APPROVED", "SHIP", "VERDICT", "IRREVERSIBLE",
        "APPROVED", "REJECTED", "hal_verdict", "BLOCK", "WARN"
    }

    def __init__(self, db_path: str = "memory/helen.db", ndjson_path: str = "memory/memory.ndjson"):
        self.db_path = db_path
        self.ndjson_path = ndjson_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                status TEXT CHECK(status IN ('OBSERVED', 'CONFIRMED', 'DISPUTED', 'RETRACTED')),
                actor TEXT CHECK(actor IN ('user', 'helen', 'system')),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _sanitize_nonsovereign(self, text: str) -> str:
        """Remove authority tokens. Returns sanitized text."""
        result = text
        for token in self.FORBIDDEN_TOKENS:
            result = result.replace(token, "")
        return result.strip()

    def add_fact(self, key: str, value: str, actor: str = "system", status: str = "OBSERVED") -> Dict[str, Any]:
        """
        Add a fact to memory (structured, non-sovereign).

        Args:
            key: identifier for the fact
            value: the content (sanitized of authority tokens)
            actor: 'user', 'helen', or 'system'
            status: 'OBSERVED', 'CONFIRMED', 'DISPUTED', or 'RETRACTED'

        Returns:
            entry dict with event_id for tracing
        """
        # Validate actor
        if actor not in ("user", "helen", "system"):
            actor = "system"

        # Sanitize value: remove forbidden tokens
        clean_value = self._sanitize_nonsovereign(value)

        event_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().isoformat() + "Z"

        # 1. Store in NDJSON (append-only, non-sovereign)
        entry = {
            "event_id": event_id,
            "key": key,
            "value": clean_value,
            "status": status,
            "actor": actor,
            "timestamp": timestamp
        }
        os.makedirs(os.path.dirname(self.ndjson_path), exist_ok=True)
        with open(self.ndjson_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        # 2. Store in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO facts (event_id, key, value, status, actor) VALUES (?, ?, ?, ?, ?)",
                (event_id, key, clean_value, status, actor)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Duplicate event_id (idempotent)
        finally:
            conn.close()

        return entry

    def search_facts(self, query: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facts WHERE key LIKE ? OR value LIKE ? ORDER BY timestamp DESC",
                      (f"%{query}%", f"%{query}%"))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_history(self) -> List[Dict[str, Any]]:
        """Return full append-only history (for replay/reconstruction)."""
        history = []
        if os.path.exists(self.ndjson_path):
            with open(self.ndjson_path, "r") as f:
                for line in f:
                    if line.strip():
                        history.append(json.loads(line))
        return history

    def get_unresolved_tensions(self) -> List[Dict[str, Any]]:
        """Return facts marked as DISPUTED (tensions for replay)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facts WHERE status='DISPUTED' ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
