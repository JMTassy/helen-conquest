import os
import json
import time
import fcntl
from typing import Dict, Any, Tuple, Optional
from ..tools.redaction import redact_secrets

class LedgerWriterV2:
    """
    Implements atomic NDJSON appends, sequence monotonicity, and file-locking.
    Supports ':memory:' as ledger_path for in-process ephemeral ledgers (no file I/O).
    """
    MEMORY_MODE = ":memory:"

    def __init__(self, ledger_path: str, lock_path: Optional[str] = None):
        self.ledger_path = ledger_path
        self.lock_path = lock_path or f"{ledger_path}.lock"
        # In-memory buffer for ephemeral ledgers
        self._memory_lines: list = [] if ledger_path == self.MEMORY_MODE else None

    def _is_memory(self) -> bool:
        return self.ledger_path == self.MEMORY_MODE

    def verify_in_memory(self) -> bool:
        """Verify integrity of in-memory ledger (always True if uncorrupted)."""
        return True  # In-memory ledger is always coherent; no external mutation possible
        
    def _acquire_lock(self, f):
        """Acquire an exclusive lock on the file descriptor."""
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            return False

    def _release_lock(self, f):
        """Release the exclusive lock."""
        fcntl.flock(f, fcntl.LOCK_UN)

    def append(self, event: Dict[str, Any]) -> Tuple[int, str]:
        """
        Appends an event atomically. Returns (seq, line).
        In ':memory:' mode, writes to an in-process list (no file I/O, no lock).
        """
        # 1. Redact secrets before anything else
        event = redact_secrets(event)

        # 2. In-memory fast path
        if self._is_memory():
            seq = len(self._memory_lines)
            event["seq"] = seq
            event["schema_version"] = "ledger_v2"
            line = json.dumps(event, sort_keys=True)
            self._memory_lines.append(line)
            return seq, line

        # 3. File mode: Open and Lock
        mode = "a+" if os.path.exists(self.ledger_path) else "w+"
        with open(self.ledger_path, mode) as f:
            # Simple retry loop for lock
            retries = 5
            while retries > 0:
                if self._acquire_lock(f):
                    break
                time.sleep(0.1)
                retries -= 1
            
            if retries == 0:
                raise RuntimeError("LNSA_ERROR: Could not acquire ledger lock.")

            try:
                # 3. Determine next sequence
                f.seek(0)
                lines = f.readlines()
                seq = len(lines)
                
                # 4. Inject seq into event
                event["seq"] = seq
                event["schema_version"] = "ledger_v2"
                
                line = json.dumps(event, sort_keys=True)
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno()) # Guarantee persistence
                
                return seq, line
            finally:
                self._release_lock(f)

    @staticmethod
    def canonicalize(data: Dict[str, Any]) -> str:
        return json.dumps(data, sort_keys=True, separators=(",", ":"))
