"""
Oracle Town NPC (Non-Player Character / Non-Authority Agent) Module

NPCs are agent bridges that can:
- Observe and analyze
- Generate claims (proposals)
- Read memory

NPCs CANNOT:
- Make decisions
- Modify durable state
- Execute actions without Oracle Town receipt

This module bridges agentic systems (OpenClaw, AutoGPT, etc.) into Oracle Town
governance without compromising authority separation.
"""

from .agent_bridge import (
    AgentBridge,
    NPCObservation,
    NPCRegistry,
    register_npc,
    get_npc,
    list_npcs,
)

__all__ = [
    "AgentBridge",
    "NPCObservation",
    "NPCRegistry",
    "register_npc",
    "get_npc",
    "list_npcs",
]
