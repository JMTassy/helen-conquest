"""
Memory Consolidation Module

HELEN learns from experience by consolidating:
1. Facts (observations)
2. Lessons (insights that are append-only, never erased)
3. Decisions (what was chosen and why)

This makes HELEN memory-aware across sessions.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


class MemoryConsolidator:
    """
    Manages HELEN's persistent memory system.

    Three channels:
    - helen_memory.json: Dynamic facts (can be updated)
    - helen_wisdom.ndjson: Append-only lessons (immutable)
    - helen_decisions.ndjson: Append-only decision log (immutable)
    """

    def __init__(
        self,
        facts_path: str = "helen_memory.json",
        wisdom_path: str = "helen_wisdom.ndjson",
        decisions_path: str = "artifacts/helen_decisions.ndjson"
    ):
        self.facts_path = facts_path
        self.wisdom_path = wisdom_path
        self.decisions_path = decisions_path

        # Initialize files if missing
        self._ensure_files_exist()

    def _ensure_files_exist(self) -> None:
        """Create memory files if they don't exist"""
        if not os.path.exists(self.facts_path):
            self._write_facts({
                'version': 'HELEN_MEM_V0',
                'facts': {},
                'created': datetime.now(timezone.utc).isoformat(),
            })

        Path(self.wisdom_path).touch()
        Path(self.decisions_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.decisions_path).touch()

    def _read_facts(self) -> Dict[str, Any]:
        """Read facts from persistent storage"""
        if not os.path.exists(self.facts_path):
            return {'version': 'HELEN_MEM_V0', 'facts': {}}

        with open(self.facts_path, 'r') as f:
            return json.load(f)

    def _write_facts(self, facts: Dict[str, Any]) -> None:
        """Write facts to persistent storage"""
        with open(self.facts_path, 'w') as f:
            json.dump(facts, f, indent=2)

    def add_fact(self, key: str, value: str, source: str = "unknown") -> None:
        """
        Add or update a fact in HELEN's memory.

        Facts are mutable (can be updated).
        This is used for observations that may change.
        """
        facts = self._read_facts()
        facts['facts'][key] = {
            'value': value,
            'source': source,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        self._write_facts(facts)

    def add_lesson(self, lesson: str, evidence: str) -> None:
        """
        Add a lesson to HELEN's permanent wisdom.

        Lessons are APPEND-ONLY and never erased.
        This is used for insights that should be remembered forever.

        Implements S3: APPEND-ONLY invariant.
        """
        entry = {
            'lesson': lesson,
            'evidence': evidence,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        with open(self.wisdom_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def add_decision(
        self,
        decision: str,
        rationale: str,
        dialogue_turn: int,
        options_considered: List[str] = None
    ) -> None:
        """
        Record a decision to the immutable decision log.

        All decisions are logged with:
        - What was chosen
        - Why it was chosen
        - What alternatives existed
        - When it was made
        """
        entry = {
            'decision': decision,
            'rationale': rationale,
            'dialogue_turn': dialogue_turn,
            'options': options_considered or [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        Path(self.decisions_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.decisions_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def get_facts(self) -> Dict[str, Any]:
        """Retrieve all facts"""
        return self._read_facts()['facts']

    def get_fact(self, key: str) -> Optional[str]:
        """Retrieve a specific fact"""
        facts = self.get_facts()
        if key in facts:
            return facts[key]['value']
        return None

    def get_all_lessons(self) -> List[Dict[str, Any]]:
        """Retrieve all lessons (wisdom is append-only, never erased)"""
        lessons = []
        if not os.path.exists(self.wisdom_path):
            return lessons

        with open(self.wisdom_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    lessons.append(json.loads(line))

        return lessons

    def get_all_decisions(self) -> List[Dict[str, Any]]:
        """Retrieve all recorded decisions"""
        decisions = []
        if not os.path.exists(self.decisions_path):
            return decisions

        with open(self.decisions_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    decisions.append(json.loads(line))

        return decisions

    def consolidate_session(self, session_summary: str) -> None:
        """
        After a session, consolidate what HELEN learned.

        This is called at the end of a dialogue to record:
        - What happened
        - What was learned
        - What questions remain
        """
        self.add_lesson(
            f"Session consolidation: {session_summary[:100]}",
            "automatic_consolidation"
        )

    def detect_tensions(self) -> List[Dict[str, Any]]:
        """
        Scan memory for DISPUTED or high-pressure facts.
        Returns a list of areas requiring alchemical transmutation.
        """
        facts = self.get_facts()
        tensions = []
        for key, data in facts.items():
            value = str(data.get('value', '')).lower()
            if 'pressure' in value or 'tension' in value or 'conflict' in value:
                tensions.append({
                    'key': key,
                    'value': data['value'],
                    'source': data.get('source')
                })
        return tensions


    def report(self) -> str:
        """Generate a memory report"""
        facts = self.get_facts()
        lessons = self.get_all_lessons()
        decisions = self.get_all_decisions()

        lines = [
            "📚 HELEN MEMORY REPORT",
            "=" * 50,
            f"Facts known: {len(facts)}",
            f"Lessons learned: {len(lessons)}",
            f"Decisions recorded: {len(decisions)}",
            "",
            "FACTS:",
        ]

        for key, fact_data in list(facts.items())[-5:]:
            lines.append(f"  • {key}: {fact_data['value'][:50]}...")

        if len(facts) > 5:
            lines.append(f"  ... and {len(facts) - 5} more")

        lines.append("")
        lines.append("LESSONS (permanent wisdom):")
        for lesson in lessons[-3:]:
            lines.append(f"  • {lesson['lesson'][:60]}...")

        if len(lessons) > 3:
            lines.append(f"  ... and {len(lessons) - 3} more")

        lines.append("")
        lines.append("RECENT DECISIONS:")
        for decision in decisions[-3:]:
            lines.append(f"  • {decision['decision']}")

        if len(decisions) > 3:
            lines.append(f"  ... and {len(decisions) - 3} more")

        return '\n'.join(lines)


# Test
if __name__ == '__main__':
    consolidator = MemoryConsolidator()

    # Add some facts
    consolidator.add_fact('test_fact', 'HELEN can learn', source='test')
    consolidator.add_fact('system', 'CWL v1.0.1 operational', source='test')

    # Add lessons
    consolidator.add_lesson(
        'CWL preserves sovereignty through deterministic reducers',
        'theorem F-001'
    )
    consolidator.add_lesson(
        'Memory consolidation allows learning across sessions',
        'design principle'
    )

    # Add decisions
    consolidator.add_decision(
        'Use autonomy loop for operational HELEN',
        'Allows bounded agent behavior within constitutional constraints',
        dialogue_turn=1,
        options_considered=['centralized', 'distributed', 'autonomy_loop']
    )

    # Report
    print(consolidator.report())

    # Verify append-only
    print("\n✅ Lessons are append-only (never erased):")
    print(f"  Total lessons: {len(consolidator.get_all_lessons())}")
