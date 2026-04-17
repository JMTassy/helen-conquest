"""
WUL Claim Compiler

Deterministic bridge layer that transforms natural-language claims into valid WUL token trees.

CORE INVARIANTS:
- No free text in hashed payloads (hash-ref leaves only)
- Objective anchoring (R15 root mandatory)
- Determinism (same claim → identical tree)
- Bounded structure (depth ≤64, nodes ≤512)
"""
from __future__ import annotations
import hashlib
import json
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CompilationResult:
    """Result of WUL compilation"""
    success: bool
    token_tree: Optional[Dict[str, Any]]
    proposition_ref: Optional[str]
    tree_hash: Optional[str]
    reason_code: Optional[str]
    injections: int = 0


class WULCompiler:
    """
    Compiles natural language claims into WUL token trees.

    Output trees are:
    - Rooted in R15 (RETURN_OBJECTIVE)
    - Free of embedded text (hash-refs only)
    - Deterministic (byte-for-byte stable)
    - Schema-validated
    """

    def __init__(self, objective_ref: str = "OBJECTIVE_MAIN"):
        self.objective_ref = objective_ref

    def _ref_from_text(self, prefix: str, text: str, n: int = 16) -> str:
        """
        Derive deterministic ref from text.

        Args:
            prefix: Ref type prefix (e.g., "PROP", "OBJ")
            text: Source text
            n: Hex prefix length

        Returns:
            Uppercase ref like "PROP_4F8B2E9C..."
        """
        h = hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
        return f"{prefix}_{h[:n]}"

    def build_token_tree(self, claim_text: str) -> Dict[str, Any]:
        """
        Build minimal canonical WUL token tree from claim.

        Structure:
            R15 (RETURN_OBJECTIVE, arity=2)
            ├─ E03 (OBJECTIVE, leaf, ref=objective_ref)
            └─ D01 (CLAIM, arity=1)
               └─ E01 (PROPOSITION, leaf, ref=proposition_ref)

        Args:
            claim_text: Natural language claim

        Returns:
            WUL token tree dict
        """
        prop_ref = self._ref_from_text("PROP", claim_text)

        return {
            "id": "R15",
            "args": [
                {
                    "id": "E03",
                    "args": [],
                    "ref": self.objective_ref
                },
                {
                    "id": "D01",
                    "args": [
                        {
                            "id": "E01",
                            "args": [],
                            "ref": prop_ref
                        }
                    ]
                }
            ]
        }

    def _compute_tree_hash(self, tree: Dict[str, Any]) -> str:
        """Compute deterministic hash of canonical tree"""
        canonical = json.dumps(tree, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _compute_claim_hash(self, claim_text: str) -> str:
        """Compute hash of original claim text"""
        return hashlib.sha256(claim_text.encode("utf-8")).hexdigest()

    def compile(self, claim_text: str, validate: bool = True) -> CompilationResult:
        """
        Compile natural language claim into WUL token tree.

        Steps:
        1. Derive stable refs (proposition_ref from hash)
        2. Build minimal tree (R15 root)
        3. Validate structure (if enabled)
        4. Emit compilation result + manifest

        Args:
            claim_text: Natural language claim
            validate: Run full validation (default True)

        Returns:
            CompilationResult with tree + metadata
        """
        # Build tree
        tree = self.build_token_tree(claim_text)
        prop_ref = self._ref_from_text("PROP", claim_text)
        tree_hash = self._compute_tree_hash(tree)

        # Optional validation (requires wul_validator)
        if validate:
            from oracle_town.core.wul_validator import WULValidator
            validator = WULValidator()
            result = validator.validate(tree)

            if not result.ok:
                return CompilationResult(
                    success=False,
                    token_tree=None,
                    proposition_ref=None,
                    tree_hash=None,
                    reason_code=result.code.name
                )

        return CompilationResult(
            success=True,
            token_tree=tree,
            proposition_ref=prop_ref,
            tree_hash=tree_hash,
            reason_code=None,
            injections=0
        )

    def create_bridge_manifest(
        self,
        claim_text: str,
        compilation_result: CompilationResult
    ) -> Dict[str, Any]:
        """
        Create bridge manifest documenting compilation.

        Args:
            claim_text: Original claim
            compilation_result: Compilation output

        Returns:
            Bridge manifest dict
        """
        return {
            "claim_text_hash": self._compute_claim_hash(claim_text),
            "proposition_ref": compilation_result.proposition_ref,
            "tree_hash": compilation_result.tree_hash,
            "objective_ref": self.objective_ref,
            "success": compilation_result.success,
            "reason_code": compilation_result.reason_code,
            "injections": compilation_result.injections,
            "tree_depth": self._compute_depth(compilation_result.token_tree) if compilation_result.token_tree else None,
            "tree_nodes": self._count_nodes(compilation_result.token_tree) if compilation_result.token_tree else None
        }

    def _compute_depth(self, tree: Dict[str, Any]) -> int:
        """Compute tree depth"""
        if not tree.get("args"):
            return 1
        return 1 + max(self._compute_depth(arg) for arg in tree["args"])

    def _count_nodes(self, tree: Dict[str, Any]) -> int:
        """Count total nodes"""
        count = 1
        for arg in tree.get("args", []):
            count += self._count_nodes(arg)
        return count


def compile_claim_to_wul(claim_text: str, objective_ref: str = "OBJECTIVE_MAIN") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Convenience function: compile claim and return (tree, manifest).

    Args:
        claim_text: Natural language claim
        objective_ref: Objective anchor ref

    Returns:
        (token_tree, bridge_manifest) tuple
    """
    compiler = WULCompiler(objective_ref=objective_ref)
    result = compiler.compile(claim_text)

    if not result.success:
        raise ValueError(f"Compilation failed: {result.reason_code}")

    manifest = compiler.create_bridge_manifest(claim_text, result)
    return result.token_tree, manifest
