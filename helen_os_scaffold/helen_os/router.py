"""
helen/router.py

Minimal router for bridging external input (e.g., AIRI) to HELEN cognitive layer.

Non-sovereign: routes user input to HELEN.speak(), does NOT touch kernel or ledger.
"""

from typing import Optional


# Global HELEN instance (set by integrations)
_helen_instance: Optional[object] = None


def set_helen_instance(helen):
    """Register the HELEN instance for routing."""
    global _helen_instance
    _helen_instance = helen


def route_input(user_text: str) -> str:
    """
    Route user input to HELEN cognitive layer.

    Args:
        user_text: User input (from AIRI or CLI)

    Returns:
        HELEN response (string)

    Raises:
        RuntimeError: If HELEN instance not registered
    """
    if _helen_instance is None:
        raise RuntimeError(
            "HELEN instance not registered. Call set_helen_instance(helen) first."
        )

    # Route to HELEN cognitive layer (non-sovereign)
    # HELEN.speak() returns formatted text (includes headers, context, etc.)
    response = _helen_instance.speak(user_text)

    return response
