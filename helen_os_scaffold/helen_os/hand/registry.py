"""
Hand Registry: Ledger Events for Hand Lifecycle
===============================================
Append-only events tracking Hand registration, updates, activation, pauses.

Events:
  HandRegistered — New Hand registered with manifest_hash + prompt_hash pinned
  HandUpdated — Existing Hand manifest changed (old hash deactivated, new hash registered)
  HandActivated — Hand becomes active for scheduling/execution
  HandPaused — Hand paused (can be resumed)
  HandRemoved — Hand permanently removed (rare; usually just paused)

All events are immutable once appended (receipt chaining from chain_v1).
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from helen_os.receipts.chain_v1 import ReceiptChain, canonical_json, sha256_hex


@dataclass
class HandRegistryEvent:
    """Base class for Hand registry events."""

    event_type: str  # "HandRegistered", "HandUpdated", etc.
    hand_id: str
    timestamp: str  # ISO 8601
    manifest_hash: str  # Current manifest hash
    prompt_hash: Optional[str] = None  # Current system_prompt_sha256
    reason: Optional[str] = None  # Why the event occurred
    actor: str = "helen_reducer"  # Who triggered the event

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "hand_id": self.hand_id,
            "timestamp": self.timestamp,
            "manifest_hash": self.manifest_hash,
            "prompt_hash": self.prompt_hash,
            "reason": self.reason,
            "actor": self.actor,
        }


class HandRegistry:
    """
    Manage Hand lifecycle via append-only ledger.
    Each operation produces a signed ledger entry via receipt chaining.
    """

    def __init__(self, ledger_path: str = "receipts/hand_registry.jsonl"):
        """
        Initialize Hand registry.

        Args:
            ledger_path: Path to Hand registry ledger (NDJSON)
        """
        self.ledger_path = ledger_path
        self.chain = ReceiptChain(ledger_path)

    def register_hand(
        self,
        hand_id: str,
        manifest_hash: str,
        prompt_hash: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        """
        Register a new Hand.

        Args:
            hand_id: Unique Hand ID
            manifest_hash: SHA256 of Hand manifest
            prompt_hash: SHA256 of system prompt (if present)
            reason: Why Hand is being registered

        Returns:
            Receipt entry_hash, or None on error
        """
        event = HandRegistryEvent(
            event_type="HandRegistered",
            hand_id=hand_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            manifest_hash=manifest_hash,
            prompt_hash=prompt_hash,
            reason=reason or f"Registering Hand '{hand_id}'",
        )

        try:
            entry_hash = self.chain.append(event.to_dict(), fail_on_error=True)
            print(f"[REGISTRY] ✅ Hand '{hand_id}' registered. Receipt: {entry_hash}")
            return entry_hash
        except RuntimeError as e:
            print(f"[REGISTRY] ❌ Failed to register Hand '{hand_id}': {e}")
            return None

    def update_hand(
        self,
        hand_id: str,
        new_manifest_hash: str,
        old_manifest_hash: str,
        new_prompt_hash: Optional[str] = None,
    ) -> Optional[str]:
        """
        Update an existing Hand manifest.

        Creates a HandUpdated event (preserves old hash reference for audit).

        Args:
            hand_id: Hand ID
            new_manifest_hash: New manifest SHA256
            old_manifest_hash: Previous manifest SHA256 (for audit trail)
            new_prompt_hash: New prompt SHA256 (if changed)

        Returns:
            Receipt entry_hash, or None on error
        """
        event_dict = {
            "event_type": "HandUpdated",
            "hand_id": hand_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "old_manifest_hash": old_manifest_hash,
            "new_manifest_hash": new_manifest_hash,
            "new_prompt_hash": new_prompt_hash,
            "reason": f"Hand '{hand_id}' manifest updated",
            "actor": "helen_reducer",
        }

        try:
            entry_hash = self.chain.append(event_dict, fail_on_error=True)
            print(f"[REGISTRY] ✅ Hand '{hand_id}' updated. Receipt: {entry_hash}")
            return entry_hash
        except RuntimeError as e:
            print(f"[REGISTRY] ❌ Failed to update Hand '{hand_id}': {e}")
            return None

    def activate_hand(
        self,
        hand_id: str,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        """
        Activate a Hand (schedule-eligible, can be invoked).

        Args:
            hand_id: Hand ID
            reason: Why Hand is being activated

        Returns:
            Receipt entry_hash, or None on error
        """
        event_dict = {
            "event_type": "HandActivated",
            "hand_id": hand_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": reason or f"Hand '{hand_id}' activated for execution",
            "actor": "helen_reducer",
        }

        try:
            entry_hash = self.chain.append(event_dict, fail_on_error=True)
            print(f"[REGISTRY] ✅ Hand '{hand_id}' activated. Receipt: {entry_hash}")
            return entry_hash
        except RuntimeError as e:
            print(f"[REGISTRY] ❌ Failed to activate Hand '{hand_id}': {e}")
            return None

    def pause_hand(
        self,
        hand_id: str,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        """
        Pause a Hand (temporarily disable, can resume).

        Args:
            hand_id: Hand ID
            reason: Why Hand is being paused

        Returns:
            Receipt entry_hash, or None on error
        """
        event_dict = {
            "event_type": "HandPaused",
            "hand_id": hand_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": reason or f"Hand '{hand_id}' paused",
            "actor": "helen_reducer",
        }

        try:
            entry_hash = self.chain.append(event_dict, fail_on_error=True)
            print(f"[REGISTRY] ✅ Hand '{hand_id}' paused. Receipt: {entry_hash}")
            return entry_hash
        except RuntimeError as e:
            print(f"[REGISTRY] ❌ Failed to pause Hand '{hand_id}': {e}")
            return None

    def remove_hand(
        self,
        hand_id: str,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        """
        Permanently remove a Hand.

        Args:
            hand_id: Hand ID
            reason: Why Hand is being removed

        Returns:
            Receipt entry_hash, or None on error
        """
        event_dict = {
            "event_type": "HandRemoved",
            "hand_id": hand_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": reason or f"Hand '{hand_id}' removed",
            "actor": "helen_reducer",
        }

        try:
            entry_hash = self.chain.append(event_dict, fail_on_error=True)
            print(f"[REGISTRY] ✅ Hand '{hand_id}' removed. Receipt: {entry_hash}")
            return entry_hash
        except RuntimeError as e:
            print(f"[REGISTRY] ❌ Failed to remove Hand '{hand_id}': {e}")
            return None

    def get_hand_state(self, hand_id: str) -> Dict[str, Any]:
        """
        Query current state of a Hand from registry.

        Returns latest state: active/paused/removed, current manifest hash, etc.

        Args:
            hand_id: Hand ID

        Returns:
            Dict with {status, manifest_hash, prompt_hash, last_event_timestamp}
            or empty dict if Hand not found
        """
        state = {
            "hand_id": hand_id,
            "status": "unknown",
            "manifest_hash": None,
            "prompt_hash": None,
            "last_event": None,
        }

        # Scan ledger from start to end
        try:
            with open(self.ledger_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    event = json.loads(line)
                    if event.get("hand_id") != hand_id:
                        continue

                    event_type = event.get("event_type")

                    # Update state based on event
                    if event_type == "HandRegistered":
                        state["status"] = "active"  # Default to active on registration
                        state["manifest_hash"] = event.get("manifest_hash")
                        state["prompt_hash"] = event.get("prompt_hash")

                    elif event_type == "HandUpdated":
                        state["manifest_hash"] = event.get("new_manifest_hash")
                        state["prompt_hash"] = event.get("new_prompt_hash") or state["prompt_hash"]
                        state["status"] = "active"

                    elif event_type == "HandActivated":
                        state["status"] = "active"

                    elif event_type == "HandPaused":
                        state["status"] = "paused"

                    elif event_type == "HandRemoved":
                        state["status"] = "removed"

                    state["last_event"] = event.get("timestamp")

        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[WARN] Failed to read registry: {e}")

        return state

    def list_hands(self) -> List[Dict[str, Any]]:
        """
        List all registered Hands (current state).

        Returns:
            List of {hand_id, status, manifest_hash, last_event}
        """
        hands = {}

        try:
            with open(self.ledger_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    event = json.loads(line)
                    hand_id = event.get("hand_id")
                    if not hand_id:
                        continue

                    if hand_id not in hands:
                        hands[hand_id] = {
                            "hand_id": hand_id,
                            "status": "unknown",
                            "manifest_hash": None,
                            "last_event": None,
                        }

                    # Update based on event type
                    event_type = event.get("event_type")
                    if event_type in ["HandRegistered", "HandActivated"]:
                        hands[hand_id]["status"] = "active"
                    elif event_type == "HandPaused":
                        hands[hand_id]["status"] = "paused"
                    elif event_type == "HandRemoved":
                        hands[hand_id]["status"] = "removed"

                    if event_type == "HandRegistered":
                        hands[hand_id]["manifest_hash"] = event.get("manifest_hash")

                    hands[hand_id]["last_event"] = event.get("timestamp")

        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[WARN] Failed to list Hands: {e}")

        return list(hands.values())


if __name__ == "__main__":
    import tempfile
    import os

    # Test: Create and manage Hands via registry
    print("Testing HandRegistry...\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.makedirs("receipts", exist_ok=True)

        registry = HandRegistry("receipts/hand_registry.jsonl")

        # Register Hand
        print("[TEST] Register Hand")
        registry.register_hand(
            hand_id="helen-researcher",
            manifest_hash="abc123",
            prompt_hash="def456",
            reason="Initial registration",
        )

        # Activate Hand
        print("\n[TEST] Activate Hand")
        registry.activate_hand("helen-researcher", "Ready for execution")

        # Update Hand
        print("\n[TEST] Update Hand manifest")
        registry.update_hand(
            hand_id="helen-researcher",
            new_manifest_hash="ghi789",
            old_manifest_hash="abc123",
            new_prompt_hash="jkl012",
        )

        # Query state
        print("\n[TEST] Query Hand state")
        state = registry.get_hand_state("helen-researcher")
        print(f"  {state}")

        # List all Hands
        print("\n[TEST] List all Hands")
        hands = registry.list_hands()
        for hand in hands:
            print(f"  {hand}")
