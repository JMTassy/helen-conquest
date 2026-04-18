"""
validate.py

WUL-CORE v0 Token Tree Validator

Implements Paper Section 3: Bounded Symbolic Kernel
- Invariant 3.1: No free text
- Invariant 3.2: Bounded structure (depth, nodes, arity)
"""

import json
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of token tree validation."""
    ok: bool
    reason: Optional[str]
    depth: int
    nodes: int
    has_r15: bool
    has_objective_pair: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "depth": self.depth,
            "nodes": self.nodes,
            "has_r15": self.has_r15,
            "has_objective_pair": self.has_objective_pair
        }


class WULValidator:
    """
    WUL-CORE v0 validator implementing Paper Invariants 3.1 and 3.2.

    Enforcement:
    - No free text (Invariant 3.1)
    - Bounded depth (Invariant 3.2)
    - Bounded node count (Invariant 3.2)
    - Arity checking against kernel
    - Mandatory R15 (objective return)
    """

    def __init__(self, kernel: Dict[str, Any], thresholds: Optional[Dict[str, int]] = None):
        self.kernel = kernel
        self.thresholds = thresholds or {}

        # Load governance constraints
        self.governance = kernel.get("governance", {})
        self.max_depth = self.thresholds.get("max_depth", self.governance.get("max_depth", 64))
        self.max_nodes = self.thresholds.get("max_nodes", self.governance.get("max_nodes", 512))
        self.max_branching = self.thresholds.get("max_branching", self.governance.get("max_branching", 8))
        self.no_free_text = self.governance.get("no_free_text", True)

        # Index primitives by ID
        # Support both old format (discourse/entities/relations) and new format (primitives)
        primitives = kernel.get("primitives", {})

        if primitives:
            # New format: primitives with role-based categorization
            self.discourse_ids = {k for k, v in primitives.items() if v.get("role") == "discourse"}
            self.entity_ids = {k for k, v in primitives.items() if v.get("role") == "entity"}
            self.relation_ids = {k for k, v in primitives.items() if v.get("role") in ("governance", "logic", "relation")}

            # Build arity map from primitives
            self.arity_map = {
                prim_id: prim_def["arity"]
                for prim_id, prim_def in primitives.items()
            }
        else:
            # Old format: separate sections
            self.discourse_ids = set(kernel.get("discourse", {}).keys())
            self.entity_ids = set(kernel.get("entities", {}).keys())
            self.relation_ids = set(kernel.get("relations", {}).keys())

            # Build arity map
            self.arity_map = {
                rel_id: rel_def["arity"]
                for rel_id, rel_def in kernel.get("relations", {}).items()
            }

        # Mandatory relations
        self.mandatory_relations = set(self.governance.get("mandatory_relations", []))

    def validate_token_tree(self, tree: Any) -> ValidationResult:
        """
        Validate token tree against WUL-CORE v0 kernel.

        Returns:
            ValidationResult with ok/reason/stats
        """
        # Check root structure
        if not isinstance(tree, dict):
            return ValidationResult(
                ok=False,
                reason="ROOT_NOT_DICT",
                depth=0,
                nodes=0,
                has_r15=False,
                has_objective_pair=False
            )

        # Initialize counters
        stats = {
            "depth": 0,
            "nodes": 0,
            "has_r15": False,
            "found_relations": set()
        }

        # Recursive validation
        reason = self._validate_node(tree, current_depth=1, stats=stats)

        if reason:
            return ValidationResult(
                ok=False,
                reason=reason,
                depth=stats["depth"],
                nodes=stats["nodes"],
                has_r15=stats["has_r15"],
                has_objective_pair=False
            )

        # Check mandatory R15
        if "R15" in self.mandatory_relations and "R15" not in stats["found_relations"]:
            return ValidationResult(
                ok=False,
                reason="R15_INVALID",
                depth=stats["depth"],
                nodes=stats["nodes"],
                has_r15=False,
                has_objective_pair=False
            )

        # Check for objective_return field (canonical R15 placement)
        has_objective_pair = "objective_return" in tree

        return ValidationResult(
            ok=True,
            reason=None,
            depth=stats["depth"],
            nodes=stats["nodes"],
            has_r15=stats["has_r15"],
            has_objective_pair=has_objective_pair
        )

    def _validate_node(self, node: Any, current_depth: int, stats: Dict) -> Optional[str]:
        """
        Recursively validate node.

        Returns:
            Reason code if invalid, None if valid
        """
        # Update depth
        stats["depth"] = max(stats["depth"], current_depth)
        stats["nodes"] += 1

        # Check depth threshold
        if current_depth > self.max_depth:
            return "DEPTH_EXCEEDED"

        # Check node count threshold
        if stats["nodes"] > self.max_nodes:
            return "NODE_COUNT_EXCEEDED"

        # Free text check (Invariant 3.1)
        if self.no_free_text and isinstance(node, str):
            # Check if it's a known primitive ID
            if not (node in self.discourse_ids or
                    node in self.entity_ids or
                    node in self.relation_ids):
                return "FREE_TEXT_DETECTED"

        # Dict nodes: check structure
        if isinstance(node, dict):
            # Check branching factor
            if len(node) > self.max_branching:
                return "BRANCHING_EXCEEDED"

            for key, value in node.items():
                # Check key is valid primitive
                if key not in self.discourse_ids and \
                   key not in self.entity_ids and \
                   key not in self.relation_ids:
                    if self.no_free_text:
                        return "FREE_TEXT_DETECTED"

                # Track R15
                if key == "R15" or key == "objective_return":
                    stats["has_r15"] = True
                    stats["found_relations"].add("R15")

                # Check relation arity
                if key in self.relation_ids:
                    stats["found_relations"].add(key)
                    expected_arity = self.arity_map.get(key)

                    if expected_arity is not None:
                        if isinstance(value, list):
                            actual_arity = len(value)
                        else:
                            actual_arity = 1

                        if actual_arity != expected_arity:
                            return "ARITY_MISMATCH"

                # Recurse
                if isinstance(value, (dict, list)):
                    reason = self._validate_node(value, current_depth + 1, stats)
                    if reason:
                        return reason

        # List nodes: recurse into elements
        elif isinstance(node, list):
            for item in node:
                reason = self._validate_node(item, current_depth + 1, stats)
                if reason:
                    return reason

        return None


def load_kernel(kernel_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load WUL-CORE kernel from JSON file."""
    if kernel_path is None:
        kernel_path = Path(__file__).parent / "core_kernel.json"

    with open(kernel_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_token_tree(
    tree: Any,
    kernel: Dict[str, Any],
    thresholds: Optional[Dict[str, int]] = None,
    require_r15: bool = True
) -> ValidationResult:
    """
    Convenience function for token tree validation.

    Args:
        tree: Token tree to validate
        kernel: WUL-CORE kernel definition
        thresholds: Optional overrides for max_depth/max_nodes
        require_r15: Whether to require R15 (default: True)

    Returns:
        ValidationResult
    """
    validator = WULValidator(kernel, thresholds)
    return validator.validate_token_tree(tree)


# Example usage
if __name__ == "__main__":
    # Load kernel
    kernel = load_kernel()

    # Valid tree with R15
    valid_tree = {
        "D01": {
            "R15": ["E02", "E03"]
        },
        "objective_return": {
            "R15": ["E02", "E03"]
        }
    }

    # Invalid: free text
    invalid_free_text = {
        "D01": {
            "some_random_text": "this is free text"
        }
    }

    # Invalid: depth exceeded
    def make_deep_tree(depth: int):
        if depth == 0:
            return "E01"
        return {"D01": make_deep_tree(depth - 1)}

    invalid_deep = make_deep_tree(70)

    # Test valid
    result = validate_token_tree(valid_tree, kernel)
    print(f"Valid tree: {result.ok}, R15: {result.has_r15}")

    # Test invalid free text
    result = validate_token_tree(invalid_free_text, kernel)
    print(f"Free text tree: {result.ok}, Reason: {result.reason}")

    # Test invalid depth
    result = validate_token_tree(invalid_deep, kernel)
    print(f"Deep tree: {result.ok}, Reason: {result.reason}, Depth: {result.depth}")
