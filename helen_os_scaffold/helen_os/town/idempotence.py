import hashlib
import json
import os
from typing import Dict, Any, Optional

class IdempotenceManager:
    """
    Manages input-based idempotence to ensure a single input-hash leads to a single outcome.
    """
    def __init__(self, index_path: str = "town/idempotence_index_v1.ndjson"):
        self.index_path = index_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

    def compute_input_hash(self, text: str, mode: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Computes a stable hash for a user input.
        """
        payload = {
            "text": text,
            "mode": mode,
            "context": context or {}
        }
        canon = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(canon.encode()).hexdigest()

    def reserve_input(self, input_hash: str) -> Dict[str, Any]:
        """
        Checks if an input is already reserved or sealed.
        """
        if not os.path.exists(self.index_path):
            return {"reserved": True, "existing_outcome": None}

        # Scan index (simple scan for prototype)
        with open(self.index_path, "r") as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if data.get("input_hash") == input_hash:
                    return {"reserved": False, "existing_outcome": data}
        
        return {"reserved": True, "existing_outcome": None}

    def finalize_input(self, input_hash: str, outcome_ref: Dict[str, Any]):
        """
        Records the outcome of an input hash.
        """
        record = {
            "input_hash": input_hash,
            "status": "sealed",
            "outcome_seq": outcome_ref.get("seq"),
            "outcome_hash": outcome_ref.get("hash"),
            "timestamp": outcome_ref.get("timestamp")
        }
        with open(self.index_path, "a") as f:
            f.write(json.dumps(record) + "\n")
