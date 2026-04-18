"""
HELEN Hand System: Autonomous Agent Capability Packages
========================================================
Based on OpenFang's Hand.toml pattern, adapted for HELEN's non-sovereign authority.

Modules:
  - schema.py: HELENHand manifest contract (tools, settings, agent config, guardrails)
  - reducer_gates.py: Safety gates G0-G3 (allowlist, effect, immutability, prompts)
  - registry.py: Append-only Hand lifecycle events (register, update, activate, pause)

Usage:
    from helen_os.hand import HELENHand, ReducerGates, HandRegistry

    # Load Hand
    hand = HELENHand.load_from_toml_file("helen-researcher.toml")

    # Verify before execution
    all_passed, results = ReducerGates.verify_hand_before_execution(
        hand,
        tool_name="web_search",
        last_committed_manifest_hash=...,
    )

    # Register in ledger
    registry = HandRegistry()
    registry.register_hand(hand.id, hand.manifest_hash, hand.agent.system_prompt_sha256)
"""

from .schema import (
    HELENHand,
    AgentConfig,
    DashboardConfig,
    DashboardMetric,
    Guardrail,
    Setting,
    SettingOption,
    Requirement,
    ToolEffect,
    SettingType,
    MetricFormat,
)

from .reducer_gates import (
    ReducerGates,
    GateResult,
    ToolClassifier,
    verify_hand_before_execution,
)

from .registry import (
    HandRegistry,
    HandRegistryEvent,
)

__all__ = [
    # Schema
    "HELENHand",
    "AgentConfig",
    "DashboardConfig",
    "DashboardMetric",
    "Guardrail",
    "Setting",
    "SettingOption",
    "Requirement",
    "ToolEffect",
    "SettingType",
    "MetricFormat",
    # Gates
    "ReducerGates",
    "GateResult",
    "ToolClassifier",
    "verify_hand_before_execution",
    # Registry
    "HandRegistry",
    "HandRegistryEvent",
]
