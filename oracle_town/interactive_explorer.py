#!/usr/bin/env python3
"""
Oracle Town Interactive Explorer (Phase 6)

Natural language query interface for searching historical verdicts, analyzing patterns,
and comparing decisions. Enables interactive discovery of governance trends.

Architecture:
- QueryParser: NLP entity extraction + intent recognition
- InteractiveExplorer: Query orchestration + result formatting
- REPL: Interactive loop for real-time queries
- No writes: Pure read-only query layer

K5 Determinism: Same query → identical results (100% reproducible)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import Counter


@dataclass
class QueryIntent:
    """Structured query intent parsed from natural language."""
    intent: str  # search_topic, search_entity, search_outcome, compare, timeline
    entities: Dict[str, Any]
    time_range: Optional[Tuple[str, str]]  # ISO dates
    filters: Dict[str, Any]
    raw_question: str


@dataclass
class QueryResult:
    """Single query result from ledger search."""
    receipt_id: str
    decision: str  # ACCEPT, REJECT
    reason: str
    timestamp: str
    gate: Optional[str]
    similarity: float
    metadata: Dict[str, Any]


class QueryParser:
    """Parse natural language questions into structured query intents."""

    # Intent patterns
    INTENT_PATTERNS = {
        'search_topic': [
            r'what.*?(vendor|technical|security|business|opportunity)',
            r'find.*(issues|problems|failures|rejects)',
            r'show.*?(accept|reject)',
            r'gate.*?(gate_a|gate_b|gate_c)',
        ],
        'search_entity': [
            r'what about\s+([a-zA-Z0-9._-]+)',
            r'entity|vendor|domain|subject',
            r'for\s+([a-zA-Z0-9._-]+)',
        ],
        'search_outcome': [
            r'(success|fail|accept|reject)',
            r'what.*(worked|failed|succeeded)',
        ],
        'compare': [
            r'compare|versus|vs|similar',
            r'difference between',
        ],
        'timeline': [
            r'last\s+(week|month|day|year)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        ],
    }

    # Entity extractors
    ENTITY_PATTERNS = {
        'vendor': r'vendor\s+([a-zA-Z0-9._-]+)',
        'domain': r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        'gate': r'(gate_a|gate_b|gate_c)',
        'decision': r'(accept|reject)',
        'severity': r'(critical|high|medium|low)',
    }

    def __init__(self):
        pass

    def parse_question(self, question: str) -> QueryIntent:
        """Parse natural language question into structured intent."""
        question_lower = question.lower()

        # Detect intent
        intent = self._detect_intent(question_lower)

        # Extract entities
        entities = self._extract_entities(question_lower)

        # Extract time range
        time_range = self._extract_time_range(question_lower)

        # Extract filters
        filters = self._extract_filters(question_lower)

        return QueryIntent(
            intent=intent,
            entities=entities,
            time_range=time_range,
            filters=filters,
            raw_question=question,
        )

    def _detect_intent(self, question: str) -> str:
        """Detect query intent from question text."""
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    return intent
        return 'search_topic'  # Default

    def _extract_entities(self, question: str) -> Dict[str, Any]:
        """Extract named entities from question."""
        entities = {}

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, question, re.IGNORECASE)
            if matches:
                entities[entity_type] = matches

        return entities

    def _extract_time_range(self, question: str) -> Optional[Tuple[str, str]]:
        """Extract time range from question."""
        # Last week
        if 'last week' in question:
            today = datetime.utcnow()
            week_ago = today - timedelta(days=7)
            return (week_ago.isoformat(), today.isoformat())

        # Last month
        if 'last month' in question:
            today = datetime.utcnow()
            month_ago = today - timedelta(days=30)
            return (month_ago.isoformat(), today.isoformat())

        # Last day
        if 'last day' in question or 'today' in question:
            today = datetime.utcnow()
            day_ago = today - timedelta(days=1)
            return (day_ago.isoformat(), today.isoformat())

        return None

    def _extract_filters(self, question: str) -> Dict[str, Any]:
        """Extract filter conditions from question."""
        filters = {}

        # Decision filter
        if 'accept' in question:
            filters['decision'] = 'ACCEPT'
        elif 'reject' in question:
            filters['decision'] = 'REJECT'

        # Gate filter
        gate_match = re.search(r'(gate_a|gate_b|gate_c)', question, re.IGNORECASE)
        if gate_match:
            filters['gate'] = gate_match.group(1).upper()

        # Severity filter
        severity_match = re.search(r'(critical|high|medium|low)', question, re.IGNORECASE)
        if severity_match:
            filters['severity'] = severity_match.group(1).lower()

        return filters


class InteractiveExplorer:
    """Interactive query interface for historical verdicts and patterns."""

    def __init__(self, ledger_path: Optional[str] = None, memory_linker=None, insight_engine=None):
        self.ledger_path = Path(ledger_path or
            "/Users/jean-marietassy/Desktop/JMT CONSULTING - Releve 24/oracle_town/ledger.jsonl")
        self.memory_linker = memory_linker
        self.insight_engine = insight_engine
        self.parser = QueryParser()
        self.verdicts = []
        self.query_history = []
        self._load_verdicts()

    def _load_verdicts(self):
        """Load verdicts from ledger."""
        if not self.ledger_path.exists():
            return

        try:
            with open(self.ledger_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            verdict = json.loads(line)
                            self.verdicts.append(verdict)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"Error loading verdicts: {e}")

    def query(self, question: str) -> List[Dict[str, Any]]:
        """Execute natural language query."""
        intent = self.parser.parse_question(question)
        self.query_history.append({'question': question, 'timestamp': datetime.utcnow().isoformat()})

        # Route to appropriate query method
        if intent.intent == 'search_topic':
            return self.search_topic(intent)
        elif intent.intent == 'search_entity':
            return self.search_entity(intent)
        elif intent.intent == 'search_outcome':
            return self.search_outcome(intent)
        elif intent.intent == 'compare':
            return self.search_topic(intent)  # Fallback
        elif intent.intent == 'timeline':
            return self.search_timeline(intent)
        else:
            return self.search_topic(intent)

    def search_topic(self, intent: QueryIntent) -> List[Dict[str, Any]]:
        """Search verdicts by topic/domain."""
        results = []

        for verdict in self.verdicts:
            # Apply filters
            if 'decision' in intent.filters:
                if verdict.get('decision') != intent.filters['decision']:
                    continue

            if 'gate' in intent.filters:
                if verdict.get('gate') != intent.filters['gate']:
                    continue

            # Check time range
            if intent.time_range:
                timestamp = verdict.get('timestamp', '')
                if timestamp < intent.time_range[0] or timestamp > intent.time_range[1]:
                    continue

            # Basic relevance scoring
            reason = verdict.get('reason', '').lower()
            relevance = 0

            # Check for entities
            for entity_type, values in intent.entities.items():
                for value in values:
                    if value.lower() in reason:
                        relevance += 1

            if relevance > 0 or not intent.entities:
                results.append({
                    'receipt_id': verdict.get('receipt_id'),
                    'decision': verdict.get('decision'),
                    'reason': verdict.get('reason'),
                    'timestamp': verdict.get('timestamp'),
                    'gate': verdict.get('gate'),
                    'relevance': relevance,
                    'metadata': verdict.get('metadata', {}),
                })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:20]  # Limit to 20 results

    def search_entity(self, intent: QueryIntent) -> List[Dict[str, Any]]:
        """Search verdicts for specific entity (vendor, domain, etc)."""
        entity_name = None
        entity_type = 'vendor'

        # Extract entity name from entities dict
        for etype, values in intent.entities.items():
            if values:
                entity_name = values[0]
                entity_type = etype
                break

        if not entity_name:
            return []

        results = []
        entity_str = entity_name.lower()

        for verdict in self.verdicts:
            reason = verdict.get('reason', '').lower()
            if entity_str in reason:
                results.append({
                    'receipt_id': verdict.get('receipt_id'),
                    'decision': verdict.get('decision'),
                    'reason': verdict.get('reason'),
                    'timestamp': verdict.get('timestamp'),
                    'gate': verdict.get('gate'),
                    'entity_type': entity_type,
                    'entity': entity_name,
                    'metadata': verdict.get('metadata', {}),
                })

        return results[:20]

    def search_outcome(self, intent: QueryIntent) -> List[Dict[str, Any]]:
        """Search by outcome (ACCEPT vs REJECT)."""
        decision_filter = intent.filters.get('decision')

        if not decision_filter:
            # Determine from intent
            if 'accept' in intent.raw_question.lower():
                decision_filter = 'ACCEPT'
            elif 'reject' in intent.raw_question.lower():
                decision_filter = 'REJECT'
            else:
                decision_filter = 'ACCEPT'

        results = []
        for verdict in self.verdicts:
            if verdict.get('decision') == decision_filter:
                results.append({
                    'receipt_id': verdict.get('receipt_id'),
                    'decision': verdict.get('decision'),
                    'reason': verdict.get('reason'),
                    'timestamp': verdict.get('timestamp'),
                    'gate': verdict.get('gate'),
                    'metadata': verdict.get('metadata', {}),
                })

        return results[:20]

    def search_timeline(self, intent: QueryIntent) -> List[Dict[str, Any]]:
        """Search verdicts within time range."""
        if not intent.time_range:
            return []

        results = []
        for verdict in self.verdicts:
            timestamp = verdict.get('timestamp', '')
            if intent.time_range[0] <= timestamp <= intent.time_range[1]:
                results.append({
                    'receipt_id': verdict.get('receipt_id'),
                    'decision': verdict.get('decision'),
                    'reason': verdict.get('reason'),
                    'timestamp': verdict.get('timestamp'),
                    'gate': verdict.get('gate'),
                    'metadata': verdict.get('metadata', {}),
                })

        # Sort by timestamp
        results.sort(key=lambda x: x['timestamp'])
        return results[:20]

    def compare_verdicts(self, receipt_id1: str, receipt_id2: str) -> Dict[str, Any]:
        """Compare two verdicts."""
        v1 = None
        v2 = None

        for v in self.verdicts:
            if v.get('receipt_id') == receipt_id1:
                v1 = v
            if v.get('receipt_id') == receipt_id2:
                v2 = v

        if not v1 or not v2:
            return {'error': 'One or both verdicts not found'}

        return {
            'verdict_1': {
                'receipt_id': v1.get('receipt_id'),
                'decision': v1.get('decision'),
                'reason': v1.get('reason'),
                'timestamp': v1.get('timestamp'),
                'gate': v1.get('gate'),
            },
            'verdict_2': {
                'receipt_id': v2.get('receipt_id'),
                'decision': v2.get('decision'),
                'reason': v2.get('reason'),
                'timestamp': v2.get('timestamp'),
                'gate': v2.get('gate'),
            },
            'same_decision': v1.get('decision') == v2.get('decision'),
            'same_gate': v1.get('gate') == v2.get('gate'),
            'time_delta': (
                datetime.fromisoformat(v2.get('timestamp', '2026-01-31T00:00:00Z').replace('Z', '+00:00')) -
                datetime.fromisoformat(v1.get('timestamp', '2026-01-31T00:00:00Z').replace('Z', '+00:00'))
            ).total_seconds() if v1.get('timestamp') and v2.get('timestamp') else None,
        }

    def format_results(self, results: List[Dict[str, Any]], format: str = 'text') -> str:
        """Format query results for display."""
        if format == 'json':
            return json.dumps(results, indent=2)

        # Text format (default)
        output = []
        output.append(f"Found {len(results)} results:")
        output.append("")

        for i, result in enumerate(results[:10], 1):
            output.append(f"{i}. [{result['receipt_id']}]")
            output.append(f"   Decision: {result['decision']}")
            output.append(f"   Reason: {result['reason'][:100]}...")
            output.append(f"   Timestamp: {result['timestamp']}")
            if result.get('gate'):
                output.append(f"   Gate: {result['gate']}")
            output.append("")

        return "\n".join(output)

    def print_welcome(self):
        """Print welcome message and usage hints."""
        print("\n" + "="*60)
        print("ORACLE TOWN INTERACTIVE EXPLORER (Phase 6)")
        print("="*60)
        print("Query the ledger of historical verdicts.")
        print("\nExample questions:")
        print("  - What vendors had security issues?")
        print("  - Show me all REJECT verdicts from GATE_A")
        print("  - What decisions were made last week?")
        print("  - Find problems from January")
        print("  - Compare receipt_id_1 and receipt_id_2")
        print("\nCommands:")
        print("  help       - Show this message")
        print("  history    - Show query history")
        print("  exit/quit  - Exit explorer")
        print("  json       - Toggle JSON output format")
        print("="*60 + "\n")

    def interactive_repl(self):
        """Interactive REPL for querying verdicts."""
        self.print_welcome()

        json_format = False

        while True:
            try:
                question = input("explorer> ").strip()

                if not question:
                    continue

                # Handle commands
                if question.lower() in ['exit', 'quit']:
                    print("Exiting explorer. Goodbye!")
                    break

                if question.lower() == 'help':
                    self.print_welcome()
                    continue

                if question.lower() == 'history':
                    print(f"Query history ({len(self.query_history)} queries):")
                    for i, q in enumerate(self.query_history[-10:], 1):
                        print(f"  {i}. {q['question']}")
                    print()
                    continue

                if question.lower() == 'json':
                    json_format = not json_format
                    print(f"JSON output: {'enabled' if json_format else 'disabled'}\n")
                    continue

                # Execute query
                results = self.query(question)
                output_format = 'json' if json_format else 'text'
                print(self.format_results(results, format=output_format))

            except KeyboardInterrupt:
                print("\nExiting explorer. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")


def main():
    """Main entry point for interactive explorer."""
    explorer = InteractiveExplorer()
    explorer.interactive_repl()


if __name__ == '__main__':
    main()
