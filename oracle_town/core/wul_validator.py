"""
WUL Token Tree Validator

Constitutional gate enforcing:
- No free text (bounded refs only)
- Bounded structure (depth ≤64, nodes ≤512)
- Objective anchoring (R15 root required)
- Known primitives only
- Correct arity
"""
import re
from enum import Enum
from typing import Dict, Any, Tuple
from dataclasses import dataclass


class WULReasonCode(Enum):
    """Typed failure codes for validation rejection"""
    WUL_OK = "WUL_OK"
    WUL_R15_MISSING = "WUL_R15_MISSING"
    WUL_UNKNOWN_SYMBOL = "WUL_UNKNOWN_SYMBOL"
    WUL_BAD_ARITY = "WUL_BAD_ARITY"
    WUL_INVALID = "WUL_INVALID"
    WUL_BOUNDS_VIOLATION = "WUL_BOUNDS_VIOLATION"


@dataclass
class ValidationResult:
    """Result of WUL validation"""
    ok: bool
    code: WULReasonCode
    detail: str
    depth: int = 0
    nodes: int = 0


class WULValidator:
    """
    Validates WUL token trees against constitutional invariants.

    Hard gates:
    - Root must be R15
    - All symbols must exist in kernel registry
    - Arity must match exactly
    - Refs must match pattern ^[A-Z][A-Z0-9_]{0,63}$
    - max_depth ≤ 64, max_nodes ≤ 512
    """

    # WUL-CORE v0 kernel primitives
    PRIMITIVES = {
        "R15": {"arity": 2, "role": "governance", "name": "RETURN_OBJECTIVE"},
        "D01": {"arity": 1, "role": "discourse", "name": "CLAIM"},
        "D02": {"arity": 1, "role": "discourse", "name": "EVIDENCE_FOR"},
        "D03": {"arity": 1, "role": "discourse", "name": "EVIDENCE_AGAINST"},
        "L02": {"arity": 2, "role": "logic", "name": "AND"},
        "L03": {"arity": 2, "role": "logic", "name": "OR"},
        "E01": {"arity": 0, "role": "entity", "name": "PROPOSITION"},
        "E02": {"arity": 0, "role": "entity", "name": "ARTIFACT"},
        "E03": {"arity": 0, "role": "entity", "name": "OBJECTIVE"},
    }

    REF_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
    MAX_DEPTH = 64
    MAX_NODES = 512

    def validate(self, tree: Dict[str, Any]) -> ValidationResult:
        """
        Validate WUL token tree.

        Args:
            tree: Token tree dict

        Returns:
            ValidationResult with ok/code/detail
        """
        # Require R15 root
        if tree.get("id") != "R15":
            return ValidationResult(
                ok=False,
                code=WULReasonCode.WUL_R15_MISSING,
                detail=f"Root must be R15, got {tree.get('id')}"
            )

        # DFS traversal with bounds checking
        stack = [(tree, 1)]  # (node, depth)
        max_depth = 1
        node_count = 0

        while stack:
            node, depth = stack.pop()
            node_count += 1
            max_depth = max(max_depth, depth)

            # Check bounds
            if depth > self.MAX_DEPTH:
                return ValidationResult(
                    ok=False,
                    code=WULReasonCode.WUL_BOUNDS_VIOLATION,
                    detail=f"Depth {depth} exceeds max {self.MAX_DEPTH}"
                )

            if node_count > self.MAX_NODES:
                return ValidationResult(
                    ok=False,
                    code=WULReasonCode.WUL_BOUNDS_VIOLATION,
                    detail=f"Node count {node_count} exceeds max {self.MAX_NODES}"
                )

            # Validate node shape
            result = self._validate_node(node)
            if not result.ok:
                return result

            # Push children to stack
            for arg in node.get("args", []):
                stack.append((arg, depth + 1))

        return ValidationResult(
            ok=True,
            code=WULReasonCode.WUL_OK,
            detail="Valid",
            depth=max_depth,
            nodes=node_count
        )

    def _validate_node(self, node: Dict[str, Any]) -> ValidationResult:
        """
        Validate individual node.

        Checks:
        - Allowed keys only (id, args, ref)
        - Primitive exists in registry
        - Arity matches
        - Ref pattern (if leaf)
        """
        # Check allowed keys
        allowed_keys = {"id", "args", "ref"}
        if not set(node.keys()).issubset(allowed_keys):
            return ValidationResult(
                ok=False,
                code=WULReasonCode.WUL_INVALID,
                detail=f"Invalid keys: {set(node.keys()) - allowed_keys}"
            )

        node_id = node.get("id")
        if not node_id:
            return ValidationResult(
                ok=False,
                code=WULReasonCode.WUL_INVALID,
                detail="Missing 'id' field"
            )

        # Check primitive exists
        if node_id not in self.PRIMITIVES:
            return ValidationResult(
                ok=False,
                code=WULReasonCode.WUL_UNKNOWN_SYMBOL,
                detail=f"Unknown primitive: {node_id}"
            )

        # Check arity
        primitive = self.PRIMITIVES[node_id]
        expected_arity = primitive["arity"]
        actual_args = node.get("args", [])

        if len(actual_args) != expected_arity:
            return ValidationResult(
                ok=False,
                code=WULReasonCode.WUL_BAD_ARITY,
                detail=f"{node_id} expects arity {expected_arity}, got {len(actual_args)}"
            )

        # Check ref pattern (if leaf)
        if expected_arity == 0:
            ref = node.get("ref")
            if not ref:
                return ValidationResult(
                    ok=False,
                    code=WULReasonCode.WUL_INVALID,
                    detail=f"Leaf {node_id} missing 'ref'"
                )

            if not self.REF_PATTERN.match(ref):
                return ValidationResult(
                    ok=False,
                    code=WULReasonCode.WUL_INVALID,
                    detail=f"Invalid ref pattern: {ref}"
                )

        return ValidationResult(ok=True, code=WULReasonCode.WUL_OK, detail="Node valid")
