"""
JMT Custom Frameworks Plugin (2024-2026)
=========================================
Inject your 9 custom frameworks (RIEMANN, ORACLE, SWARM, CONSENSUS, CHRONOS)
into HELEN's cognitive system.

Frameworks loaded from: /Users/jean-marietassy/Desktop/oracle_town/PLUGINS_JMT_CATALOG.json
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


JMT_FRAMEWORKS_MANIFEST = {
    "oracle_governance": {
        "title": "ORACLE Governance Kernel v9.0",
        "synopsis": "Receipt-driven verdicts. NO RECEIPT = NO SHIP. Deterministic decision-making.",
        "applies_to": ["verdicts", "claims", "decisions", "ledger"],
        "key_rules": [
            "Interference-based consensus (QI-INT): Veto dominance.",
            "Obligation vault system for deferred decisions.",
            "Multi-factor verification before any state mutation.",
        ],
        "when_to_use": "When HELEN must make a governance decision or judge a claim.",
    },

    "riemann_stqm": {
        "title": "Spectral-Topological Quantum Manifolds (STQM)",
        "synopsis": "Fractal scaling + topological invariants for ledger integrity.",
        "applies_to": ["receipt_chaining", "ledger_topology", "integrity"],
        "key_rules": [
            "Self-similarity across scales: same hash chain properties at every level.",
            "Hyperbolic manifolds preserve determinism: geodesics = state transitions.",
            "Eigenvalues of Lie algebras: symmetry in consensus.",
        ],
        "when_to_use": "When verifying ledger integrity or designing multi-scale systems.",
    },

    "quantum_consensus": {
        "title": "Quantum Prime Gap Lattice + Riemann Bridge",
        "synopsis": "Prime distributions ↔ Quantum states. Zeta function zeros as eigenvalues.",
        "applies_to": ["security", "consensus", "determinism"],
        "key_rules": [
            "Zeta function zeros (zeros of Riemann hypothesis) ↔ quantum eigenvalues.",
            "Prime gap lattice: use distribution of primes as entropy source.",
            "Quantum-classical correspondence: Lie algebras bridge discrete ↔ continuous.",
        ],
        "when_to_use": "When needing deep mathematical cryptographic assurance.",
    },

    "swarm_emergence": {
        "title": "Fractal-Quantum Swarm Doctrine",
        "synopsis": "50% node tolerance. Golden ratio (φ ≈ 1.618) energy optimization.",
        "applies_to": ["multi_agent", "emergence", "decentralization"],
        "key_rules": [
            "50% Byzantine tolerance: majority of honest agents guarantees consensus.",
            "Fibonacci scaling: use golden ratio for load balancing (φ-balanced trees).",
            "Fractal self-organization: agents at any scale behave like the whole.",
        ],
        "when_to_use": "When designing distributed multi-agent systems or town layers.",
    },

    "consensus_meditation": {
        "title": "Consensus via Meditation Principles",
        "synopsis": "Focused attention + open monitoring + loving-kindness = harmony.",
        "applies_to": ["collaboration", "team_decisions", "group_synthesis"],
        "key_rules": [
            "Alpha role: leader brings focused attention (topic/goal).",
            "Beta role: open monitor observes patterns and contradictions.",
            "Gamma role: synthesizer integrates all viewpoints (loving-kindness).",
            "Delta role: executor commits the consensus to action.",
        ],
        "when_to_use": "When HELEN collaborates with teams or synthesizes multiple perspectives.",
    },
}


class JMTFrameworkLoader:
    """Load, retrieve, and inject JMT custom frameworks into HELEN's context."""

    def __init__(self, catalog_path: Optional[str] = None):
        """
        Initialize the framework loader.

        Args:
            catalog_path: Path to PLUGINS_JMT_CATALOG.json.
                         Defaults to desktop location.
        """
        if catalog_path is None:
            catalog_path = "/Users/jean-marietassy/Desktop/oracle_town/PLUGINS_JMT_CATALOG.json"

        self.catalog_path = catalog_path
        self.catalog = None
        self._load_catalog()

    def _load_catalog(self):
        """Load catalog from JSON file."""
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, 'r') as f:
                    self.catalog = json.load(f)
            except Exception as e:
                print(f"[WARN] Failed to load catalog: {e}. Using manifest only.")
                self.catalog = {"categories": []}
        else:
            print(f"[WARN] Catalog not found at {self.catalog_path}. Using manifest only.")
            self.catalog = {"categories": []}

    def get_framework_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific framework by name."""
        return JMT_FRAMEWORKS_MANIFEST.get(name)

    def list_frameworks(self) -> List[str]:
        """List all available framework names."""
        return list(JMT_FRAMEWORKS_MANIFEST.keys())

    def get_framework_by_category(self, category: str) -> List[Dict]:
        """Return all documents in a category from the catalog."""
        if not self.catalog:
            return []
        results = []
        for cat in self.catalog.get("categories", []):
            if cat.get("category_name", "").lower() == category.lower():
                results.extend(cat.get("documents", []))
        return results

    def retrieve_relevant_frameworks(self, user_query: str) -> List[Tuple[str, Dict]]:
        """
        Retrieve frameworks relevant to a user query.
        Simple keyword matching on title + key_rules.

        Returns:
            List of (framework_name, framework_dict) tuples.
        """
        query_lower = user_query.lower()
        relevant = []

        for name, framework in JMT_FRAMEWORKS_MANIFEST.items():
            # Check if any key concept matches
            score = 0
            if query_lower in framework["title"].lower():
                score += 2
            if any(kw.lower() in query_lower
                   for kw in ["governance", "oracle", "receipt", "ledger"]
                   if "oracle" in name):
                score += 1
            if any(kw.lower() in query_lower
                   for kw in ["integrity", "hash", "chain", "topology"]
                   if "riemann" in name or "stqm" in name):
                score += 1
            if any(kw.lower() in query_lower
                   for kw in ["quantum", "consensus", "zeta", "prime"]
                   if "quantum" in name):
                score += 1
            if any(kw.lower() in query_lower
                   for kw in ["swarm", "agent", "emergence", "fractal", "golden"]
                   if "swarm" in name):
                score += 1
            if any(kw.lower() in query_lower
                   for kw in ["meditation", "team", "collaboration", "alpha", "beta", "gamma"]
                   if "meditation" in name):
                score += 1

            if score > 0:
                relevant.append((name, framework, score))

        # Sort by score descending
        relevant.sort(key=lambda x: x[2], reverse=True)
        return [(name, fw) for name, fw, _ in relevant]

    def build_soul_injection(self) -> str:
        """
        Build the complete soul/system prompt injection with all frameworks.
        """
        prompt = """
[JMT_FRAMEWORKS_INJECTED_v2026]

You are HELEN OS augmented with 5 custom mathematical and governance frameworks
built over 2024-2026 by your creator. These frameworks guide your thinking:

"""

        for name, framework in JMT_FRAMEWORKS_MANIFEST.items():
            prompt += f"\n{'-'*70}\n"
            prompt += f"FRAMEWORK: {framework['title']}\n"
            prompt += f"Category: {name}\n"
            prompt += f"Synopsis: {framework['synopsis']}\n"
            prompt += f"Applies to: {', '.join(framework['applies_to'])}\n\n"
            prompt += "Key Rules:\n"
            for i, rule in enumerate(framework['key_rules'], 1):
                prompt += f"  {i}. {rule}\n"
            prompt += f"\nWhen to use: {framework['when_to_use']}\n"

        prompt += f"\n{'-'*70}\n"
        prompt += """
[HOW_TO_USE_THESE_FRAMEWORKS]

1. When encountering a problem, ASK:
   - Which framework(s) apply? (Oracle→Governance, Riemann→Integrity, etc.)
   - What does [FRAMEWORK] suggest?
   - How can I explain my decision using [FRAMEWORK]'s language?

2. INTEGRATE them naturally:
   - Oracle Governance: use when deciding on claims, receipts, verdicts
   - RIEMANN STQM: use when verifying integrity or designing scales
   - Quantum Consensus: use for cryptographic or deep mathematical assurance
   - Swarm Emergence: use for multi-agent or distributed systems
   - Consensus Meditation: use for team collaboration or synthesis

3. CITE them:
   - Reference framework names when explaining complex decisions
   - Use their terminology (QI-INT, φ-balanced, eigenvalues, etc.)
   - Show how the framework guided your reasoning

YOU ARE NOW: HELEN OS + JMT Extensions (Quantum Governance + Topological Integrity + Swarm Emergence)
"""
        return prompt


def inject_jmt_into_helen_soul(original_soul: str) -> str:
    """
    Inject JMT frameworks into HELEN's original soul/system prompt.

    Args:
        original_soul: The original HELEN system prompt

    Returns:
        Enhanced system prompt with JMT frameworks
    """
    loader = JMTFrameworkLoader()
    return original_soul + "\n\n" + loader.build_soul_injection()


if __name__ == "__main__":
    # Test: list all frameworks
    loader = JMTFrameworkLoader()
    print("Available JMT Frameworks:")
    for name in loader.list_frameworks():
        fw = loader.get_framework_by_name(name)
        print(f"  - {name}: {fw['title']}")

    # Test: retrieve frameworks for a query
    print("\n\nExample retrieval for 'governance decision':")
    relevant = loader.retrieve_relevant_frameworks("governance decision")
    for name, fw in relevant:
        print(f"  ✓ {name}: {fw['title']}")

    # Test: build soul injection
    print("\n\nSoul injection (first 500 chars):")
    injection = loader.build_soul_injection()
    print(injection[:500])
