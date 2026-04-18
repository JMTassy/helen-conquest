"""
helen_os/town/validate — Receipt linkage validation tools.

Provides:
  validate_receipt_linkage — combined AUTHZ + CROSS_RECEIPT + ReducedConclusion check.
  ReceiptLinkageReport     — structured pass/fail per check.
  ReceiptLinkageError      — raised on any linkage failure.
"""

from .validate_receipt_linkage import (
    validate_receipt_linkage,
    ReceiptLinkageReport,
    ReceiptLinkageError,
)

__all__ = [
    "validate_receipt_linkage",
    "ReceiptLinkageReport",
    "ReceiptLinkageError",
]
