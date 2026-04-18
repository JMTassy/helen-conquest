"""
Integration Hub: JMT Frameworks + ECC Hardening Patterns
========================================================

This module integrates:
1. JMT custom frameworks (ORACLE, RIEMANN, SWARM, CONSENSUS, CHRONOS)
2. Receipt chaining (SHA256 prev_hash + entry_hash + context_hash)
3. Atomic writes (fcntl.flock + fsync)
4. Security redaction (PII, secrets)
5. Runtime flags (HELEN_RETRIEVAL_ENABLED, etc.)

Usage:
    from helen_os.integration_jmt_ecc import HelenWithJMTAndECC

    helen = HelenWithJMTAndECC()
    helen.log_memory_hit(query="What is ORACLE?", hits=[...])
    # Verify chain at end of session:
    helen.verify_receipts()
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from helen_os.plugins.jmt_frameworks import JMTFrameworkLoader, inject_jmt_into_helen_soul
from helen_os.receipts.chain_v1 import ReceiptChain, append_memory_hit, sha256_hex, canonical_json


class SecurityRedactor:
    """Redact sensitive information from logs."""

    # Patterns to redact
    PATTERNS = {
        "openai_key": r"sk-[A-Za-z0-9]{20,}",
        "github_token": r"ghp_[A-Za-z0-9]{36,}",
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "jwt": r"eyJ[A-Za-z0-9_-]{50,}",
        "password_assignment": r"password\s*=\s*['\"][^'\"]+['\"]",
        "private_key": r"-----BEGIN (RSA|DSA|EC|OPENSSH|PGP) PRIVATE KEY-----",
    }

    @staticmethod
    def redact(text: str) -> str:
        """Redact sensitive patterns from text."""
        import re
        redacted = text
        for pattern_name, pattern in SecurityRedactor.PATTERNS.items():
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
        return redacted


class HelenWithJMTAndECC:
    """
    HELEN OS enhanced with JMT frameworks and ECC hardening patterns.
    """

    def __init__(
        self,
        jmt_catalog_path: Optional[str] = None,
        receipt_ledger_path: str = "receipts/memory_hits.jsonl",
        enable_retrieval: bool = True,
        enable_redaction: bool = True,
        fail_closed_on_receipt_error: bool = True,
    ):
        """
        Initialize HELEN with JMT and ECC.

        Args:
            jmt_catalog_path: Path to PLUGINS_JMT_CATALOG.json
            receipt_ledger_path: Path to receipt chain ledger
            enable_retrieval: Log memory hits to receipt chain
            enable_redaction: Redact secrets from logs
            fail_closed_on_receipt_error: If True, raise on receipt write failure
        """
        self.jmt_loader = JMTFrameworkLoader(jmt_catalog_path)
        self.receipt_chain = ReceiptChain(receipt_ledger_path)
        self.ledger_path = receipt_ledger_path

        # Runtime flags (can be overridden by env vars)
        self.enable_retrieval = enable_retrieval or os.getenv("HELEN_RETRIEVAL_ENABLED", "").lower() == "true"
        self.enable_redaction = enable_redaction or os.getenv("HELEN_REDACTION_ENABLED", "").lower() == "true"
        self.fail_closed_on_receipt_error = fail_closed_on_receipt_error
        self.debug_mode = os.getenv("HELEN_DEBUG", "").lower() == "true"

        # Stats
        self.total_queries = 0
        self.total_hits = 0

        if self.debug_mode:
            print("[DEBUG] HELEN initialized with JMT + ECC")

    def get_enhanced_soul_prompt(self, original_soul: str) -> str:
        """
        Get HELEN's system prompt enhanced with JMT frameworks.

        Args:
            original_soul: The base HELEN soul/system prompt

        Returns:
            Enhanced prompt with JMT frameworks injected
        """
        return inject_jmt_into_helen_soul(original_soul)

    def log_memory_hit(
        self,
        query: str,
        hits: List[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Log a memory retrieval hit to the receipt chain.

        Args:
            query: The query string
            hits: List of {id, source, score, text} dicts

        Returns:
            Receipt entry_hash, or None on error
        """
        if not self.enable_retrieval:
            return None

        self.total_queries += 1
        self.total_hits += len(hits)

        # Redact sensitive info
        if self.enable_redaction:
            query = SecurityRedactor.redact(query)
            hits = [
                {
                    "id": h.get("id"),
                    "source": h.get("source"),
                    "score": h.get("score"),
                    "text": SecurityRedactor.redact(h.get("text", "")),
                }
                for h in hits
            ]

        # Log to receipt chain
        try:
            receipt_hash = append_memory_hit(
                query=query,
                hits=hits,
                fail_closed=self.fail_closed_on_receipt_error,
                ledger_path=self.ledger_path,
            )

            if self.debug_mode:
                print(f"[DEBUG] Memory hit logged. Receipt hash: {receipt_hash}")

            return receipt_hash

        except RuntimeError as e:
            print(f"[ERROR] Failed to log memory hit: {e}")
            if self.fail_closed_on_receipt_error:
                raise
            return None

    def log_helen_decision(
        self,
        decision_type: str,
        description: str,
        relevant_frameworks: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Log a HELEN decision (claim, verdict, proposal) to the receipt chain.

        Args:
            decision_type: 'claim', 'verdict', 'proposal', etc.
            description: The decision description
            relevant_frameworks: Which JMT frameworks applied

        Returns:
            Receipt entry_hash, or None on error
        """
        if not self.enable_retrieval:
            return None

        entry = {
            "type": f"helen_{decision_type}",
            "description": SecurityRedactor.redact(description) if self.enable_redaction else description,
            "frameworks_applied": relevant_frameworks or [],
        }

        try:
            entry_hash = self.receipt_chain.append(entry, fail_on_error=self.fail_closed_on_receipt_error)
            if self.debug_mode:
                print(f"[DEBUG] HELEN {decision_type} logged. Receipt hash: {entry_hash}")
            return entry_hash

        except RuntimeError as e:
            print(f"[ERROR] Failed to log HELEN decision: {e}")
            if self.fail_closed_on_receipt_error:
                raise
            return None

    def verify_receipts(self) -> bool:
        """
        Verify the integrity of the receipt chain.

        Returns:
            True if valid, False otherwise
        """
        print(f"\n[AUDIT] Verifying receipt chain: {self.ledger_path}")
        is_valid = self.receipt_chain.verify_chain()

        if is_valid:
            digest = self.receipt_chain.get_digest()
            print(f"[AUDIT] ✅ Chain valid. Cumulative digest: {digest}")
        else:
            print(f"[AUDIT] ❌ Chain INVALID. Tampering may have occurred.")

        print(f"[AUDIT] Stats: {self.total_queries} queries, {self.total_hits} total hits")
        return is_valid

    def get_stats(self) -> Dict[str, Any]:
        """Return session statistics."""
        return {
            "total_queries": self.total_queries,
            "total_hits": self.total_hits,
            "ledger_path": self.ledger_path,
            "enable_retrieval": self.enable_retrieval,
            "enable_redaction": self.enable_redaction,
            "fail_closed": self.fail_closed_on_receipt_error,
        }

    def list_frameworks(self) -> List[str]:
        """List all available JMT frameworks."""
        return self.jmt_loader.list_frameworks()

    def get_framework(self, name: str) -> Optional[Dict]:
        """Get a specific framework by name."""
        return self.jmt_loader.get_framework_by_name(name)

    def retrieve_relevant_frameworks(self, query: str) -> List[tuple]:
        """Retrieve frameworks relevant to a query."""
        return self.jmt_loader.retrieve_relevant_frameworks(query)


# Convenience factory
def create_helen_enhanced() -> HelenWithJMTAndECC:
    """Create a fully enhanced HELEN instance."""
    return HelenWithJMTAndECC(
        enable_retrieval=True,
        enable_redaction=True,
        fail_closed_on_receipt_error=True,
    )


if __name__ == "__main__":
    # Test the integration
    print("Testing HelenWithJMTAndECC integration...\n")

    helen = create_helen_enhanced()

    # Test: Log some memory hits
    print("[TEST] Logging memory hits...")
    hits = [
        {"id": "f1", "source": "oracle_town", "score": 0.95, "text": "Receipt governance system"},
        {"id": "f2", "source": "jmt_framework", "score": 0.87, "text": "ORACLE framework for verdicts"},
    ]
    receipt1 = helen.log_memory_hit("What is ORACLE governance?", hits)
    print(f"  Receipt 1: {receipt1}")

    # Test: Log a HELEN decision
    print("\n[TEST] Logging HELEN decision...")
    receipt2 = helen.log_helen_decision(
        decision_type="claim",
        description="HELEN proposes integrating ORACLE framework for receipt verification",
        relevant_frameworks=["oracle_governance", "riemann_stqm"],
    )
    print(f"  Receipt 2: {receipt2}")

    # Test: Verify chain
    print("\n[TEST] Verifying receipt chain...")
    is_valid = helen.verify_receipts()

    # Test: List frameworks
    print("\n[TEST] Available JMT frameworks:")
    for fw_name in helen.list_frameworks():
        fw = helen.get_framework(fw_name)
        print(f"  - {fw_name}: {fw['title']}")

    # Test: Retrieve frameworks for a query
    print("\n[TEST] Frameworks relevant to 'governance decision':")
    relevant = helen.retrieve_relevant_frameworks("governance decision")
    for name, fw in relevant:
        print(f"  ✓ {name}: {fw['title']}")
