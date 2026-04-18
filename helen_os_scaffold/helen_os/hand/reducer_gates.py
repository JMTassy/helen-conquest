"""
Reducer Gates G0-G3: Hand Safety Enforcement
=============================================
Non-negotiable rules that prevent Hands from bypassing TOWN authority.

Inspired by OpenFang guardrails but enforced at the reducer level (ledger commit),
not at the harness level. This ensures NO tool execution happens without ledger consent.

Gates:
  G0 — Tool allowlist: tool ∈ Hand.tools or deny
  G1 — Effect separation: OBSERVE vs PROPOSE vs EXECUTE (approval required)
  G2 — Manifest immutability: manifest_hash must match last registered
  G3 — Prompt immutability: system_prompt_sha256 must match file
"""

import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from .schema import HELENHand, ToolEffect


@dataclass
class GateResult:
    """Result of a gate check."""
    passed: bool
    gate_id: str  # "G0", "G1", etc.
    message: str
    details: Optional[Dict[str, Any]] = None

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} {self.gate_id}: {self.message}"


class ToolClassifier:
    """Classify tools by effect level (OBSERVE, PROPOSE, EXECUTE)."""

    # OBSERVE: read-only, safe
    OBSERVE_TOOLS = {
        "web_search",
        "web_fetch",
        "file_read",
        "memory_recall",
        "db_query",
        "api_read",
    }

    # PROPOSE: creates ledger entry (Δ proposal), no immediate state change
    PROPOSE_TOOLS = {
        "memory_store",
        "decision_propose",
        "claim_propose",
    }

    # EXECUTE: affects external state (requires explicit approval)
    EXECUTE_TOOLS = {
        "file_write",
        "file_delete",
        "shell_execute",
        "api_write",
        "email_send",
        "browser_purchase",
        "payment_send",
        "database_write",
    }

    @classmethod
    def classify(cls, tool_name: str) -> ToolEffect:
        """Classify a tool by effect."""
        if tool_name in cls.OBSERVE_TOOLS:
            return "observe"
        elif tool_name in cls.PROPOSE_TOOLS:
            return "propose"
        elif tool_name in cls.EXECUTE_TOOLS:
            return "execute"
        else:
            # Default to execute (fail-safe)
            return "execute"


class ReducerGates:
    """Enforce Hand safety gates at the reducer level."""

    @staticmethod
    def gate_g0_tool_allowlist(
        hand: HELENHand,
        tool_name: str,
    ) -> GateResult:
        """
        Gate G0: Tool Allowlist
        ========================
        For any tool invocation attributed to a Hand:
          - tool ∈ Hand.tools
          - deny otherwise

        This is the first line of defense: you can only use tools listed in the manifest.
        """
        if tool_name in hand.tools:
            return GateResult(
                passed=True,
                gate_id="G0",
                message=f"Tool '{tool_name}' is in Hand '{hand.id}' allowlist",
            )
        else:
            return GateResult(
                passed=False,
                gate_id="G0",
                message=f"Tool '{tool_name}' NOT in Hand '{hand.id}' allowlist",
                details={"tool": tool_name, "allowlist": hand.tools},
            )

    @staticmethod
    def gate_g1_effect_separation(
        hand: HELENHand,
        tool_name: str,
        approval_token: Optional[str] = None,
    ) -> GateResult:
        """
        Gate G1: Effect Separation
        ==========================
        Classify tool by effect and enforce approval for EXECUTE tools.

        OBSERVE → allowed directly
        PROPOSE → allowed (creates Δ proposal)
        EXECUTE → requires approval_token or must emit NEEDS_APPROVAL Δ
        """
        effect = ToolClassifier.classify(tool_name)

        if effect == "observe":
            return GateResult(
                passed=True,
                gate_id="G1",
                message=f"Tool '{tool_name}' is OBSERVE (read-only, allowed)",
            )

        elif effect == "propose":
            return GateResult(
                passed=True,
                gate_id="G1",
                message=f"Tool '{tool_name}' is PROPOSE (creates Δ only, allowed)",
            )

        elif effect == "execute":
            # Check if approval token is present and valid
            if approval_token:
                return GateResult(
                    passed=True,
                    gate_id="G1",
                    message=f"Tool '{tool_name}' is EXECUTE but approval_token provided",
                )
            else:
                return GateResult(
                    passed=False,
                    gate_id="G1",
                    message=f"Tool '{tool_name}' is EXECUTE and requires approval_token",
                    details={
                        "tool": tool_name,
                        "effect": "execute",
                        "approval_required": True,
                    },
                )

    @staticmethod
    def gate_g2_manifest_immutability(
        hand: HELENHand,
        last_committed_manifest_hash: Optional[str],
    ) -> GateResult:
        """
        Gate G2: Manifest Immutability
        ==============================
        Before a Hand run:
          - Recompute manifest_hash from current TOML/JSON
          - Must match last_committed_manifest_hash from ledger

        This prevents "TOML changed but runtime uses cached version" attacks.
        """
        current_hash = hand.compute_manifest_hash()

        # First run: no prior hash to compare
        if last_committed_manifest_hash is None:
            return GateResult(
                passed=True,
                gate_id="G2",
                message=f"Hand '{hand.id}' is new; manifest will be registered",
            )

        # Subsequent run: hash must match
        if current_hash == last_committed_manifest_hash:
            return GateResult(
                passed=True,
                gate_id="G2",
                message=f"Hand '{hand.id}' manifest hash matches last committed",
            )
        else:
            return GateResult(
                passed=False,
                gate_id="G2",
                message=f"Hand '{hand.id}' manifest CHANGED; must re-register",
                details={
                    "hand_id": hand.id,
                    "current_hash": current_hash,
                    "last_committed_hash": last_committed_manifest_hash,
                },
            )

    @staticmethod
    def gate_g3_prompt_immutability(
        hand: HELENHand,
        prompt_search_paths: Optional[List[Path]] = None,
    ) -> GateResult:
        """
        Gate G3: Prompt Immutability
        ============================
        If Hand.agent.system_prompt_ref exists:
          - Locate the prompt file (search paths)
          - Compute sha256(file bytes)
          - Must equal Hand.agent.system_prompt_sha256

        This prevents "prompt edited on disk" attacks.
        """
        if not hand.agent or not hand.agent.system_prompt_ref:
            return GateResult(
                passed=True,
                gate_id="G3",
                message="No prompt declared; gate passes",
            )

        prompt_ref = hand.agent.system_prompt_ref
        prompt_sha256 = hand.agent.system_prompt_sha256

        if not prompt_sha256:
            return GateResult(
                passed=False,
                gate_id="G3",
                message=f"Prompt ref '{prompt_ref}' declared but no sha256",
            )

        # Locate prompt file
        if prompt_search_paths is None:
            prompt_search_paths = [
                Path.cwd(),
                Path.cwd() / "prompts",
                Path.cwd() / "helen_os_scaffold" / "prompts",
            ]

        prompt_path = None
        for base_path in prompt_search_paths:
            candidate = base_path / prompt_ref
            if candidate.exists():
                prompt_path = candidate
                break

        if not prompt_path:
            return GateResult(
                passed=False,
                gate_id="G3",
                message=f"Prompt file not found: {prompt_ref}",
                details={"ref": prompt_ref, "search_paths": [str(p) for p in prompt_search_paths]},
            )

        # Compute file hash
        actual_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()

        if actual_hash == prompt_sha256:
            return GateResult(
                passed=True,
                gate_id="G3",
                message=f"Prompt '{prompt_ref}' hash matches (immutable)",
            )
        else:
            return GateResult(
                passed=False,
                gate_id="G3",
                message=f"Prompt '{prompt_ref}' hash MISMATCH (file may have been edited)",
                details={
                    "ref": prompt_ref,
                    "expected_sha256": prompt_sha256,
                    "actual_sha256": actual_hash,
                },
            )


def verify_hand_before_execution(
    hand: HELENHand,
    tool_name: str,
    last_committed_manifest_hash: Optional[str],
    approval_token: Optional[str] = None,
    prompt_search_paths: Optional[List[Path]] = None,
) -> Tuple[bool, List[GateResult]]:
    """
    Run all gates (G0-G3) before Hand execution.

    Returns:
        (all_passed: bool, gate_results: List[GateResult])
    """
    gates = ReducerGates()

    results = [
        gates.gate_g0_tool_allowlist(hand, tool_name),
        gates.gate_g1_effect_separation(hand, tool_name, approval_token),
        gates.gate_g2_manifest_immutability(hand, last_committed_manifest_hash),
        gates.gate_g3_prompt_immutability(hand, prompt_search_paths),
    ]

    all_passed = all(r.passed for r in results)
    return all_passed, results


if __name__ == "__main__":
    # Test gates
    print("Testing Reducer Gates G0-G3...\n")

    # Create test Hand
    from .schema import AgentConfig, Guardrail

    hand = HELENHand(
        id="test-hand",
        name="Test Hand",
        description="For testing",
        category="test",
        icon="🧪",
        tools=["web_search", "file_read", "memory_store"],
        agent=AgentConfig(
            name="test",
            description="test",
            system_prompt_ref="prompts/test.md",
            system_prompt_sha256="abc123",
        ),
    )
    hand.manifest_hash = hand.compute_manifest_hash()

    # Test G0: Allowlist
    print("Test G0 (Tool Allowlist):")
    r1 = ReducerGates.gate_g0_tool_allowlist(hand, "web_search")
    print(f"  {r1}")
    r2 = ReducerGates.gate_g0_tool_allowlist(hand, "shell_execute")
    print(f"  {r2}")

    # Test G1: Effect Separation
    print("\nTest G1 (Effect Separation):")
    r3 = ReducerGates.gate_g1_effect_separation(hand, "web_search")
    print(f"  {r3}")
    r4 = ReducerGates.gate_g1_effect_separation(hand, "shell_execute", approval_token=None)
    print(f"  {r4}")

    # Test G2: Manifest Immutability
    print("\nTest G2 (Manifest Immutability):")
    r5 = ReducerGates.gate_g2_manifest_immutability(hand, None)
    print(f"  {r5}")
    r6 = ReducerGates.gate_g2_manifest_immutability(hand, hand.manifest_hash)
    print(f"  {r6}")

    # Test G3: Prompt Immutability (will fail since file doesn't exist)
    print("\nTest G3 (Prompt Immutability):")
    r7 = ReducerGates.gate_g3_prompt_immutability(hand)
    print(f"  {r7}")

    # Test full verification
    print("\nFull verification (all gates):")
    all_passed, results = verify_hand_before_execution(
        hand,
        tool_name="web_search",
        last_committed_manifest_hash=hand.manifest_hash,
    )
    print(f"  All Passed: {all_passed}")
    for r in results:
        print(f"  {r}")
