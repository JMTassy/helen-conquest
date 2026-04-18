"""
Frozen error classes for graph_validator.py

These are machine-checkable diagnostic codes.
No prose. Only codes and minimal context.
"""

from dataclasses import dataclass
from typing import Optional


# Error code constants (frozen vocabulary)
SCHEMA_INVALID = "SCHEMA_INVALID"
DUPLICATE_NODE_ID = "DUPLICATE_NODE_ID"
DUPLICATE_EDGE_ID = "DUPLICATE_EDGE_ID"
UNKNOWN_EDGE_ENDPOINT = "UNKNOWN_EDGE_ENDPOINT"
ILLEGAL_EDGE_TYPE = "ILLEGAL_EDGE_TYPE"
ILLEGAL_DEPENDENCY_CYCLE = "ILLEGAL_DEPENDENCY_CYCLE"
WILD_ROUTING_VIOLATION = "WILD_ROUTING_VIOLATION"
TIER_PROMOTION_VIOLATION = "TIER_PROMOTION_VIOLATION"
MISSING_EVIDENCE_HANDLE_FIELD = "MISSING_EVIDENCE_HANDLE_FIELD"
MISSING_REQUIRED_SUPPORT = "MISSING_REQUIRED_SUPPORT"
UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
POLICY_QUARANTINE_ACTIVE = "POLICY_QUARANTINE_ACTIVE"


@dataclass
class ValidationError:
    """Machine-checkable error record"""
    code: str
    node_id: Optional[str] = None
    edge_id: Optional[str] = None
    field: Optional[str] = None
    message: str = ""

    def to_dict(self):
        """Convert to JSON-serializable dict"""
        return {
            "code": self.code,
            "node_id": self.node_id,
            "edge_id": self.edge_id,
            "field": self.field,
            "message": self.message,
        }


@dataclass
class ValidationWarning:
    """Non-fatal validation observation"""
    code: str
    node_id: Optional[str] = None
    message: str = ""

    def to_dict(self):
        return {
            "code": self.code,
            "node_id": self.node_id,
            "message": self.message,
        }


# Mapping of error codes to human-readable descriptions (for logging only)
ERROR_DESCRIPTIONS = {
    SCHEMA_INVALID: "Graph schema validation failed",
    DUPLICATE_NODE_ID: "Duplicate node ID found",
    DUPLICATE_EDGE_ID: "Duplicate edge ID found",
    UNKNOWN_EDGE_ENDPOINT: "Edge references non-existent node",
    ILLEGAL_EDGE_TYPE: "Edge type not allowed for source/target node kinds",
    ILLEGAL_DEPENDENCY_CYCLE: "Circular dependency detected in claims",
    WILD_ROUTING_VIOLATION: "Wild_text node cannot route to Mayor",
    TIER_PROMOTION_VIOLATION: "Tier classification violates promotion rules",
    MISSING_EVIDENCE_HANDLE_FIELD: "Evidence handle missing required field",
    MISSING_REQUIRED_SUPPORT: "Claim missing required supporting evidence",
    UNRESOLVED_REFERENCE: "Referenced object not found in bundle",
    POLICY_QUARANTINE_ACTIVE: "Claim blocked by active quarantine rule",
}
