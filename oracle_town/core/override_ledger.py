#!/usr/bin/env python3
"""Override Ledger - Immutable record of conscious speculations"""

import json
from pathlib import Path
from datetime import datetime

class OverrideLedger:
    def __init__(self, ledger_path="oracle_town/ledger/overrides.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    def append(self, record_dict):
        try:
            with open(self.ledger_path, "a") as f:
                f.write(json.dumps(record_dict) + "\n")
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    def summary(self):
        return f"Override ledger at {self.ledger_path}"
