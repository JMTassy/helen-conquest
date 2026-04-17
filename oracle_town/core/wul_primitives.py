"""
WUL Primitives for ORACLE TOWN

Defines the minimal token tree structure for governance kernel.
Based on R15-rooted tree with strict arity validation.

Constitutional Rule:
- No free text allowed in WUL tree
- Every node must have valid id, args, ref (pattern-matched)
- Root must be R15
- Validation is fail-closed (unknown symbols → reject)
"""
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum


class WULReasonCode(str, Enum):
    """Deterministic rejection reasons for WUL validation"""
    WUL_R15_MISSING = "WUL_R15_MISSING"
    WUL_UNKNOWN_SYMBOL = "WUL_UNKNOWN_SYMBOL"
    WUL_BAD_ARITY = "WUL_BAD_ARITY"
    WUL_INVALID_REF = "WUL_INVALID_REF"
    WUL_BOUNDS_VIOLATION = "WUL_BOUNDS_VIOLATION"
    WUL_VALID = "WUL_VALID"


@dataclass
class WULPrimitive:
    """WUL token primitive definition"""
    id: str
    arity: int  # Exact number of children required
    description: str


# Frozen primitives table (R15-based minimal kernel)
WUL_PRIMITIVES: Dict[str, WULPrimitive] = {
    # Root (governance anchor)
    "R15": WULPrimitive("R15", 2, "Objective Return - every claim must be rooted here"),

    # Claim structure
    "D01": WULPrimitive("D01", 1, "Claim - contains proposition"),
    "E01": WULPrimitive("E01", 0, "Proposition - leaf with ref to claim hash"),
    "E03": WULPrimitive("E03", 0, "Objective - leaf with ref to objective ID"),

    # Event lifecycle (ORACLE obligations)
    "R10": WULPrimitive("R10", 2, "Intent - obligation declaration"),
    "R25": WULPrimitive("R25", 1, "ALLOW - permission granted (attestation exists)"),
    "R28": WULPrimitive("R28", 1, "INITIATE - execution starts (Factory runs test)"),
    "R29": WULPrimitive("R29", 1, "TERMINATE - execution completes (test passed)"),

    # Safety override
    "R21": WULPrimitive("R21", 1, "PREVENT - permanently forbid event (kill-switch)"),

    # Event reference
    "E_EVENT": WULPrimitive("E_EVENT", 0, "Event ID - leaf with ref to event_X"),
}


@dataclass
class WULNode:
    """
    WUL tree node (strict schema).

    Constitutional rules:
    - id must be in WUL_PRIMITIVES
    - args length must match primitive arity
    - ref (if present) must match ^[A-Z][A-Z0-9_]{0,63}$
    - NO free text allowed
    """
    id: str
    args: List['WULNode'] = None
    ref: Optional[str] = None

    def __post_init__(self):
        if self.args is None:
            self.args = []

    def to_dict(self) -> dict:
        """Canonical JSON representation"""
        result = {"id": self.id}
        if self.args:
            result["args"] = [node.to_dict() for node in self.args]
        if self.ref:
            result["ref"] = self.ref
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'WULNode':
        """Parse from JSON"""
        return cls(
            id=data["id"],
            args=[cls.from_dict(arg) for arg in data.get("args", [])],
            ref=data.get("ref")
        )


class WULValidator:
    """
    Validates WUL tree against minimal kernel rules.

    Fail-closed: any violation → deterministic rejection with reason code.
    """

    def __init__(self, max_depth: int = 10, max_nodes: int = 100):
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.node_count = 0

    def validate(self, tree: WULNode) -> tuple[bool, WULReasonCode, str]:
        """
        Validate WUL tree.

        Returns:
            (is_valid, reason_code, error_message)
        """
        self.node_count = 0

        # Rule 1: Root must be R15
        if tree.id != "R15":
            return False, WULReasonCode.WUL_R15_MISSING, f"Root must be R15, got {tree.id}"

        # Rule 2-6: Recursive validation
        return self._validate_node(tree, depth=0)

    def _validate_node(self, node: WULNode, depth: int) -> tuple[bool, WULReasonCode, str]:
        """Recursive node validation"""

        # Bounds check
        self.node_count += 1
        if depth > self.max_depth:
            return False, WULReasonCode.WUL_BOUNDS_VIOLATION, f"Depth {depth} exceeds max {self.max_depth}"
        if self.node_count > self.max_nodes:
            return False, WULReasonCode.WUL_BOUNDS_VIOLATION, f"Node count {self.node_count} exceeds max {self.max_nodes}"

        # Known symbol check
        if node.id not in WUL_PRIMITIVES:
            return False, WULReasonCode.WUL_UNKNOWN_SYMBOL, f"Unknown symbol: {node.id}"

        primitive = WUL_PRIMITIVES[node.id]

        # Arity check
        if len(node.args) != primitive.arity:
            return False, WULReasonCode.WUL_BAD_ARITY, f"{node.id} expects {primitive.arity} args, got {len(node.args)}"

        # Ref validation (if present)
        if node.ref is not None:
            import re
            if not re.match(r'^[A-Z][A-Z0-9_]{0,63}$', node.ref):
                return False, WULReasonCode.WUL_INVALID_REF, f"Invalid ref pattern: {node.ref}"

        # Recursive validation of children
        for child in node.args:
            valid, code, msg = self._validate_node(child, depth + 1)
            if not valid:
                return valid, code, msg

        return True, WULReasonCode.WUL_VALID, "Valid"


# ORACLE ↔ WUL mapping functions

def obligation_to_wul_event(obligation_name: str) -> str:
    """
    Convert ORACLE obligation name to WUL event ID.

    Example:
        "unit_tests_green" → "EVENT_UNIT_TESTS_GREEN"
    """
    return f"EVENT_{obligation_name.upper()}"


def create_wul_claim(claim_hash: str, objective_id: str = "OBJECTIVE_MAIN") -> WULNode:
    """
    Create minimal WUL tree for ORACLE claim.

    Structure:
        R15(
            E03(ref=objective_id),
            D01(
                E01(ref=claim_hash)
            )
        )
    """
    return WULNode(
        id="R15",
        args=[
            WULNode(id="E03", ref=objective_id),
            WULNode(
                id="D01",
                args=[
                    WULNode(id="E01", ref=f"PROP_{claim_hash}")
                ]
            )
        ]
    )


def create_wul_obligation_intent(obligation_name: str) -> WULNode:
    """
    Create WUL intent token for obligation.

    R10(
        E_EVENT(ref=event_id),
        E01(ref=obligation_name)
    )
    """
    event_id = obligation_to_wul_event(obligation_name)
    return WULNode(
        id="R10",
        args=[
            WULNode(id="E_EVENT", ref=event_id),
            WULNode(id="E01", ref=obligation_name.upper())
        ]
    )


def create_wul_allow(event_id: str) -> WULNode:
    """
    Create ALLOW token (attestation exists).

    R25(E_EVENT(ref=event_id))
    """
    return WULNode(
        id="R25",
        args=[
            WULNode(id="E_EVENT", ref=event_id)
        ]
    )


def create_wul_initiate(event_id: str) -> WULNode:
    """
    Create INITIATE token (Factory starts test).

    R28(E_EVENT(ref=event_id))
    """
    return WULNode(
        id="R28",
        args=[
            WULNode(id="E_EVENT", ref=event_id)
        ]
    )


def create_wul_terminate(event_id: str) -> WULNode:
    """
    Create TERMINATE token (test completes).

    R29(E_EVENT(ref=event_id))
    """
    return WULNode(
        id="R29",
        args=[
            WULNode(id="E_EVENT", ref=event_id)
        ]
    )


def create_wul_prevent(event_id: str) -> WULNode:
    """
    Create PREVENT token (kill-switch).

    R21(E_EVENT(ref=event_id))

    Constitutional rule: Once PREVENT exists for an event_id,
    that event can NEVER be initiated. Event ID is burned.
    """
    return WULNode(
        id="R21",
        args=[
            WULNode(id="E_EVENT", ref=event_id)
        ]
    )


# Test
if __name__ == "__main__":
    import json

    print("=" * 80)
    print("WUL PRIMITIVES TEST")
    print("=" * 80)

    # Test 1: Valid minimal claim
    print("\n1. Valid minimal claim:")
    claim = create_wul_claim("ABCDEF0123456789")
    validator = WULValidator()
    valid, code, msg = validator.validate(claim)
    print(f"   Valid: {valid}, Code: {code}")
    print(f"   Tree: {json.dumps(claim.to_dict(), indent=2)}")

    # Test 2: Invalid root
    print("\n2. Invalid root (not R15):")
    bad_claim = WULNode(id="D01", args=[])
    valid, code, msg = validator.validate(bad_claim)
    print(f"   Valid: {valid}, Code: {code}, Message: {msg}")

    # Test 3: Bad arity
    print("\n3. Bad arity (E01 expects 0 args):")
    bad_arity = WULNode(
        id="R15",
        args=[
            WULNode(id="E03", ref="OBJ"),
            WULNode(id="D01", args=[
                WULNode(id="E01", args=[WULNode(id="E03")], ref="PROP")  # E01 should have 0 args
            ])
        ]
    )
    valid, code, msg = validator.validate(bad_arity)
    print(f"   Valid: {valid}, Code: {code}, Message: {msg}")

    # Test 4: Obligation lifecycle
    print("\n4. Obligation lifecycle (ALLOW → INITIATE → TERMINATE):")
    event_id = obligation_to_wul_event("unit_tests_green")
    print(f"   Event ID: {event_id}")

    allow = create_wul_allow(event_id)
    initiate = create_wul_initiate(event_id)
    terminate = create_wul_terminate(event_id)

    print(f"   ALLOW: {json.dumps(allow.to_dict())}")
    print(f"   INITIATE: {json.dumps(initiate.to_dict())}")
    print(f"   TERMINATE: {json.dumps(terminate.to_dict())}")

    # Test 5: PREVENT (kill-switch)
    print("\n5. PREVENT (kill-switch):")
    prevent = create_wul_prevent(event_id)
    print(f"   PREVENT: {json.dumps(prevent.to_dict())}")
    print(f"   → Event {event_id} is now BURNED (can never be initiated)")

    print("\n✅ All WUL primitives tests completed!")
