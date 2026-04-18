"""
JMT Frameworks Retrieval System
================================

Lightweight semantic retrieval: given a query, load only the relevant
framework summaries instead of bloating the soul prompt.

Principle: RETRIEVAL = what is loaded for this turn
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class JMTFrameworkRetriever:
    """Retrieve relevant JMT frameworks based on query keywords."""

    def __init__(self, manifest_path: Path = None):
        """
        Initialize retriever with manifest.

        Args:
            manifest_path: Path to JMT_FRAMEWORKS_MANIFEST.json
                          (defaults to current directory)
        """
        if manifest_path is None:
            manifest_path = Path.cwd() / "JMT_FRAMEWORKS_MANIFEST.json"

        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.frameworks = self.manifest.get("frameworks", [])

    def _load_manifest(self) -> Dict[str, Any]:
        """Load framework manifest."""
        try:
            return json.loads(self.manifest_path.read_text())
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Manifest not found: {self.manifest_path}\n"
                f"Expected: JMT_FRAMEWORKS_MANIFEST.json in project root"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in manifest: {e}")

    def retrieve(
        self,
        query: str,
        max_results: int = 3,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant frameworks based on query.

        Args:
            query: User query or question
            max_results: Maximum frameworks to return
            min_score: Minimum relevance score (0.0-1.0)

        Returns:
            List of framework metadata (ordered by relevance)
        """
        # Normalize query
        query_words = set(query.lower().split())

        # Score each framework
        scored = []
        for framework in self.frameworks:
            score = self._score_framework(framework, query_words)
            if score >= min_score:
                scored.append((score, framework))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top N
        return [fw for _, fw in scored[:max_results]]

    def _score_framework(self, framework: Dict[str, Any], query_words: set) -> float:
        """
        Score a framework against query words.

        Scoring:
        - Exact keyword match: +1.0
        - Domain match: +0.5
        - Name match: +0.3
        """
        score = 0.0

        # Keyword matches (highest weight)
        keywords = set(
            kw.lower() for kw in framework.get("trigger_keywords", [])
        )
        keyword_hits = len(query_words & keywords)
        score += keyword_hits * 1.0

        # Domain match
        domain = framework.get("domain", "").lower()
        if any(dw in domain for dw in query_words):
            score += 0.5

        # Name match
        name = framework.get("name", "").lower()
        if any(nw in name for nw in query_words):
            score += 0.3

        # Normalize by query size (avoid bias toward long queries)
        if len(query_words) > 0:
            score = score / len(query_words)

        return score

    def build_injection_prompt(
        self,
        frameworks: List[Dict[str, Any]],
        context: str = "",
    ) -> str:
        """
        Build a concise injection prompt from retrieved frameworks.

        Args:
            frameworks: List of framework metadata
            context: Optional context to include

        Returns:
            Formatted prompt for injection
        """
        if not frameworks:
            return ""

        lines = []
        lines.append("=== RELEVANT FRAMEWORKS (This Turn) ===\n")

        for fw in frameworks:
            name = fw.get("name", "Unknown")
            purpose = fw.get("purpose", "")
            concepts = fw.get("key_concepts", [])

            lines.append(f"• {name}")
            lines.append(f"  Purpose: {purpose}")
            if concepts:
                lines.append(f"  Key concepts: {', '.join(concepts)}")
            lines.append("")

        if context:
            lines.append(f"Context: {context}\n")

        return "\n".join(lines)

    def get_framework_summary(self, framework_id: str) -> Optional[str]:
        """
        Get a framework by ID (for manual injection if needed).

        Args:
            framework_id: Framework ID (e.g., "oracle-governance")

        Returns:
            Formatted framework summary, or None if not found
        """
        for fw in self.frameworks:
            if fw.get("id") == framework_id:
                return self.build_injection_prompt([fw])

        return None

    def list_frameworks(self) -> List[str]:
        """List all available framework IDs."""
        return [fw.get("id") for fw in self.frameworks]


def retrieve_for_query(query: str, max_results: int = 3) -> str:
    """
    Convenience function: retrieve and inject frameworks for a query.

    Args:
        query: User question
        max_results: How many frameworks to load

    Returns:
        Formatted injection prompt
    """
    retriever = JMTFrameworkRetriever()
    frameworks = retriever.retrieve(query, max_results=max_results)
    return retriever.build_injection_prompt(frameworks, context=f"Query: {query}")


if __name__ == "__main__":
    # Demo: Show retrieval in action
    print("Testing JMT Framework Retrieval\n")

    retriever = JMTFrameworkRetriever()

    # Test queries
    queries = [
        "How should HELEN make decisions with authority separation?",
        "I need to model a timeline of events",
        "How can multiple agents coordinate?",
        "Tell me about games and determinism",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}\n")

        frameworks = retriever.retrieve(query, max_results=2)
        print(f"Retrieved {len(frameworks)} framework(s):\n")

        injection = retriever.build_injection_prompt(frameworks, context=query)
        print(injection)
