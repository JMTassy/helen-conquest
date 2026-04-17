"""
K7 Ledger Reader — Policy Pinning Record Analysis

Reads and verifies K7 policy pinning records from the immutable ledger.

K7 Rule: Policy hash fixed per run
- Every map generation creates immutable ledger entry
- Hash locks map state so mid-game changes are detectable
- Ledger is append-only JSONL format
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class LedgerReader:
    """Reads and analyzes K7 policy pinning records from JSONL ledger"""

    def __init__(self, ledger_path: str = "kernel/ledger/map_generation_records.jsonl"):
        """
        Initialize ledger reader.

        Args:
            ledger_path: Path to JSONL ledger file
        """
        self.ledger_path = Path(ledger_path)

    def read_all_entries(self) -> List[Dict]:
        """
        Read all ledger entries (append-only JSONL).

        Returns:
            List of ledger entry dictionaries
        """
        if not self.ledger_path.exists():
            return []

        entries = []
        with open(self.ledger_path, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))

        return entries

    def get_entries_by_game_id(self, game_id: str) -> List[Dict]:
        """
        Get all ledger entries for a specific game.

        K7: All map generation for a game should have same hash (same map).

        Args:
            game_id: Game identifier

        Returns:
            List of entries for this game
        """
        entries = self.read_all_entries()
        return [e for e in entries if e.get("game_id") == game_id]

    def get_entries_by_seed(self, seed: int) -> List[Dict]:
        """
        Get all ledger entries for a specific seed.

        K5 determinism check: Same seed → identical hash (same map).

        Args:
            seed: Map generation seed

        Returns:
            List of entries for this seed
        """
        entries = self.read_all_entries()
        return [e for e in entries if e.get("seed") == seed]

    def verify_hash_consistency(self, game_id: str) -> bool:
        """
        Verify K7: All hashes for a game are identical (no mid-game changes).

        Args:
            game_id: Game to verify

        Returns:
            True if all hashes identical, False otherwise
        """
        entries = self.get_entries_by_game_id(game_id)
        if not entries:
            return True  # No entries = nothing to verify

        hashes = set(e.get("map_hash") for e in entries)
        return len(hashes) == 1  # All identical

    def verify_seed_hash_consistency(self, seed: int) -> bool:
        """
        Verify K5+K7: Same seed produces same hash (determinism locked).

        Args:
            seed: Seed to verify

        Returns:
            True if all hashes for this seed identical, False otherwise
        """
        entries = self.get_entries_by_seed(seed)
        if not entries:
            return True

        hashes = set(e.get("map_hash") for e in entries)
        return len(hashes) == 1

    def get_ledger_stats(self) -> Dict:
        """
        Get statistics about ledger content.

        Returns:
            Dict with ledger stats (entry count, rule distribution, etc.)
        """
        entries = self.read_all_entries()

        if not entries:
            return {
                "total_entries": 0,
                "unique_games": 0,
                "unique_seeds": 0,
                "unique_hashes": 0,
            }

        game_ids = set(e.get("game_id") for e in entries)
        seeds = set(e.get("seed") for e in entries)
        hashes = set(e.get("map_hash") for e in entries)
        rules = set(e.get("rule") for e in entries)

        return {
            "total_entries": len(entries),
            "unique_games": len(game_ids),
            "unique_seeds": len(seeds),
            "unique_hashes": len(hashes),
            "rules_enforced": list(rules),
            "first_entry": entries[0].get("locked_at") if entries else None,
            "last_entry": entries[-1].get("locked_at") if entries else None,
        }

    def verify_append_only(self) -> bool:
        """
        Verify K7: Ledger is append-only (no modifications).

        Checks that timestamps are monotonically increasing.

        Returns:
            True if ledger is append-only, False if tampered
        """
        entries = self.read_all_entries()
        if len(entries) <= 1:
            return True

        prev_time = None
        for entry in entries:
            curr_time = entry.get("locked_at")
            if prev_time and curr_time < prev_time:
                return False  # Timestamp violation
            prev_time = curr_time

        return True

    def get_entry_by_id(self, entry_id: str) -> Optional[Dict]:
        """
        Get a specific ledger entry by ID.

        Args:
            entry_id: Ledger entry ID (e.g., "MAP_POLICY_2026_02_20_120000_game_001")

        Returns:
            Entry dict if found, None otherwise
        """
        entries = self.read_all_entries()
        for entry in entries:
            if entry.get("id") == entry_id:
                return entry
        return None

    def print_ledger_summary(self) -> None:
        """Print human-readable summary of ledger"""
        entries = self.read_all_entries()

        if not entries:
            print("❌ Ledger is empty")
            return

        print(f"✅ Ledger has {len(entries)} entries\n")

        for entry in entries:
            print(f"Entry ID: {entry.get('id')}")
            print(f"  Rule: {entry.get('rule')}")
            print(f"  Game: {entry.get('game_id')}")
            print(f"  Seed: {entry.get('seed')}")
            print(f"  Hash: {entry.get('map_hash')[:16]}...")
            print(f"  Locked At: {entry.get('locked_at')}")
            print()

    def export_to_json(self, output_path: str) -> None:
        """
        Export entire ledger as JSON for analysis.

        Args:
            output_path: Where to save exported JSON
        """
        entries = self.read_all_entries()
        with open(output_path, "w") as f:
            json.dump(entries, f, indent=2)
        print(f"✅ Exported {len(entries)} entries to {output_path}")

    def audit_ledger(self) -> Dict[str, bool]:
        """
        Run full audit of ledger compliance.

        Returns:
            Dict with audit results (all checks should be True)
        """
        return {
            "append_only": self.verify_append_only(),
            "has_entries": len(self.read_all_entries()) > 0,
        }
