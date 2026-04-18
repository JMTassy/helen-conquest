"""
Oracle Town V2 Kernel

Core infrastructure for deterministic governance.

Modules:
- canonical_json: Bit-for-bit reproducible JSON serialization
- hashing: SHA256 hashing and hashchain verification
- receipt_writer: Receipt generation and artifact management
"""

__version__ = "2.0.0"
__all__ = [
    "canonical_json",
    "hashing",
    "receipt_writer",
]
