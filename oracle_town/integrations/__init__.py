"""
Oracle Town Integration Modules

Official integrations for agent frameworks:
- Moltbot (Anthropic's Claude-based agent)
- OpenClaw (Autonomous task completion framework)
- Supermemory (Persistent memory with auto-recall)

Each integration provides:
- Before-action hooks (check if action is safe)
- After-action hooks (record outcomes)
- Policy query interface
- Dashboard integration
"""

from .moltbot_kernel import MoltbotKernel

__all__ = ["MoltbotKernel"]
