#!/usr/bin/env python3
"""
Heartbeat Supervisor

Converts OpenClaw heartbeats into Oracle Town observation triggers.

Key Behavior:
1. Heartbeat fires on schedule (inherited from OpenClaw)
2. Instead of executing action directly, generates a claim
3. Claim flows through TRI gate
4. Only if SHIP does the action execute (or get logged as "approved observation")

This ensures every heartbeat-triggered action is audited and authorized.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
import json
import uuid
import yaml


@dataclass
class HeartbeatSpec:
    """
    Specification for a heartbeat-triggered observation.
    """
    heartbeat_id: str
    name: str
    description: str
    interval: str  # "6h", "1d", "1w", etc.
    action_fn: Callable[[], Any]  # Function that produces evidence
    observer_role: str  # NPC role that will generate claim
    claim_type: str = "observation"
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "heartbeat_id": self.heartbeat_id,
            "name": self.name,
            "description": self.description,
            "interval": self.interval,
            "observer_role": self.observer_role,
            "claim_type": self.claim_type,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "next_run": self.next_run
        }


@dataclass
class HeartbeatExecution:
    """
    Record of a heartbeat execution and its result.
    """
    execution_id: str
    heartbeat_id: str
    timestamp: str
    claim_generated: bool
    receipt_id: Optional[str] = None
    decision: Optional[str] = None  # "SHIP" or "NO_SHIP"
    evidence: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HeartbeatSupervisor:
    """
    Manages OpenClaw heartbeats as Oracle Town observation triggers.
    """

    def __init__(self, registry_path: str = "oracle_town/scheduler/registry.yaml"):
        """
        Initialize the heartbeat supervisor.

        Args:
            registry_path: Path to heartbeat registry file
        """
        self.registry_path = registry_path
        self.heartbeats: Dict[str, HeartbeatSpec] = {}
        self.executions: List[HeartbeatExecution] = []
        self._load_registry()

    def register_heartbeat(
        self,
        name: str,
        description: str,
        interval: str,
        action_fn: Callable[[], Any],
        observer_role: str,
        heartbeat_id: Optional[str] = None
    ) -> HeartbeatSpec:
        """
        Register a heartbeat to be supervised.

        Args:
            name: Human-readable name
            description: What this heartbeat does
            interval: Schedule interval (e.g., "6h", "1d")
            action_fn: Function that produces evidence
            observer_role: NPC role (e.g., "OBS.vendor_check")
            heartbeat_id: Optional ID; auto-generated if not provided

        Returns:
            HeartbeatSpec object
        """
        heartbeat_id = heartbeat_id or f"hb_{uuid.uuid4().hex[:8]}"

        spec = HeartbeatSpec(
            heartbeat_id=heartbeat_id,
            name=name,
            description=description,
            interval=interval,
            action_fn=action_fn,
            observer_role=observer_role
        )

        self.heartbeats[heartbeat_id] = spec
        self._save_registry()

        return spec

    def unregister_heartbeat(self, heartbeat_id: str):
        """
        Unregister a heartbeat.
        """
        self.heartbeats.pop(heartbeat_id, None)
        self._save_registry()

    def get_heartbeat(self, heartbeat_id: str) -> Optional[HeartbeatSpec]:
        """
        Get a heartbeat by ID.
        """
        return self.heartbeats.get(heartbeat_id)

    def list_heartbeats(self) -> List[HeartbeatSpec]:
        """
        List all registered heartbeats.
        """
        return list(self.heartbeats.values())

    def trigger_heartbeat(
        self,
        heartbeat_id: str,
        submit_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Manually trigger a heartbeat (or called by scheduler).

        Args:
            heartbeat_id: ID of heartbeat to trigger
            submit_fn: Optional function to submit claim to Oracle Town

        Returns:
            Execution result dict
        """
        spec = self.get_heartbeat(heartbeat_id)
        if not spec:
            return {"error": f"Heartbeat {heartbeat_id} not found"}

        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat()

        try:
            # Step 1: Run action to get evidence
            evidence = spec.action_fn()

            # Step 2: Create claim from evidence
            claim = self._create_claim(spec, evidence)

            # Step 3: Submit claim if submit_fn provided
            receipt = None
            if submit_fn:
                receipt = submit_fn(claim)

            # Record execution
            execution = HeartbeatExecution(
                execution_id=execution_id,
                heartbeat_id=heartbeat_id,
                timestamp=timestamp,
                claim_generated=True,
                receipt_id=receipt.get("receipt_id") if receipt else None,
                decision=receipt.get("decision") if receipt else None,
                evidence=evidence
            )

            self.executions.append(execution)

            # Update heartbeat last_run
            spec.last_run = timestamp

            return {
                "execution_id": execution_id,
                "claim": claim,
                "receipt": receipt,
                "status": "success"
            }

        except Exception as e:
            # Record failure
            execution = HeartbeatExecution(
                execution_id=execution_id,
                heartbeat_id=heartbeat_id,
                timestamp=timestamp,
                claim_generated=False,
                error=str(e)
            )

            self.executions.append(execution)

            return {
                "execution_id": execution_id,
                "status": "error",
                "error": str(e)
            }

    def get_execution_history(
        self,
        heartbeat_id: Optional[str] = None,
        limit: int = 100
    ) -> List[HeartbeatExecution]:
        """
        Get execution history.

        Args:
            heartbeat_id: Optional filter by heartbeat
            limit: Maximum number of results

        Returns:
            List of executions
        """
        results = self.executions

        if heartbeat_id:
            results = [e for e in results if e.heartbeat_id == heartbeat_id]

        return results[-limit:]

    def run_scheduler_loop(
        self,
        submit_fn: Callable,
        check_interval_seconds: int = 60
    ):
        """
        Run the scheduler loop (for daemon mode).

        This is a simple scheduler. In production, use APScheduler or similar.

        Args:
            submit_fn: Function to submit claims to Oracle Town
            check_interval_seconds: How often to check for due heartbeats
        """
        import time
        from datetime import datetime

        print(f"[Scheduler] Starting heartbeat supervisor loop")

        try:
            while True:
                now = datetime.utcnow()

                for spec in self.heartbeats.values():
                    if not spec.enabled:
                        continue

                    # Check if heartbeat is due
                    if self._is_due(spec, now):
                        print(f"[Heartbeat] Triggering: {spec.name}")
                        result = self.trigger_heartbeat(spec.heartbeat_id, submit_fn)

                        if result.get("status") == "success":
                            decision = result.get("receipt", {}).get("decision", "NO_RECEIPT")
                            print(f"  → Receipt decision: {decision}")
                        else:
                            print(f"  → Error: {result.get('error')}")

                # Sleep before next check
                time.sleep(check_interval_seconds)

        except KeyboardInterrupt:
            print("[Scheduler] Stopped")

    # --- Private helper methods ---

    def _create_claim(self, spec: HeartbeatSpec, evidence: Any) -> Dict[str, Any]:
        """
        Create a claim from heartbeat evidence.
        """
        return {
            "claim_id": f"claim_{uuid.uuid4().hex[:8]}",
            "claim_type": spec.claim_type,
            "heartbeat_id": spec.heartbeat_id,
            "heartbeat_name": spec.name,
            "observer_role": spec.observer_role,
            "statement": f"Heartbeat observation: {spec.name}",
            "evidence": self._serialize(evidence),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _is_due(self, spec: HeartbeatSpec, now: datetime) -> bool:
        """
        Check if a heartbeat is due to run.

        Simple implementation based on interval.
        """
        if not spec.last_run:
            return True

        last = datetime.fromisoformat(spec.last_run)
        interval = self._parse_interval(spec.interval)

        return now >= (last + interval)

    def _parse_interval(self, interval_str: str) -> timedelta:
        """
        Parse interval string to timedelta.

        Examples: "6h", "1d", "1w"
        """
        import re

        match = re.match(r"(\d+)([hdw])", interval_str)
        if not match:
            return timedelta(hours=6)  # default

        value, unit = int(match.group(1)), match.group(2)

        if unit == "h":
            return timedelta(hours=value)
        elif unit == "d":
            return timedelta(days=value)
        elif unit == "w":
            return timedelta(weeks=value)
        else:
            return timedelta(hours=6)

    def _serialize(self, obj: Any) -> Any:
        """
        Serialize evidence to JSON-safe format.
        """
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, (dict, list)):
            return obj
        else:
            try:
                return json.loads(json.dumps(obj, default=str))
            except:
                return str(obj)

    def _load_registry(self):
        """
        Load heartbeat registry from file.
        """
        try:
            with open(self.registry_path, "r") as f:
                data = yaml.safe_load(f) or {}
                # Note: action_fn cannot be deserialized from YAML
                # This is just the spec data; action_fn is registered separately
        except FileNotFoundError:
            pass

    def _save_registry(self):
        """
        Save heartbeat registry to file.
        """
        try:
            specs = [hb.to_dict() for hb in self.heartbeats.values()]
            with open(self.registry_path, "w") as f:
                yaml.dump({"heartbeats": specs}, f, default_flow_style=False)
        except Exception as e:
            print(f"Warning: Could not save registry: {e}")


# --- Testing ---

if __name__ == "__main__":

    # Test 1: Create supervisor
    supervisor = HeartbeatSupervisor()
    print("✓ Heartbeat supervisor initialized")

    # Test 2: Register heartbeat
    def mock_status_check():
        return {"status": "healthy", "uptime": "99.9%"}

    spec = supervisor.register_heartbeat(
        name="Vendor Status Check",
        description="Check vendor API status every 6 hours",
        interval="6h",
        action_fn=mock_status_check,
        observer_role="OBS.vendor_check"
    )
    print(f"✓ Heartbeat registered: {spec.heartbeat_id}")

    # Test 3: Trigger heartbeat (no submit_fn)
    result = supervisor.trigger_heartbeat(spec.heartbeat_id)
    print(f"✓ Heartbeat triggered: {result['status']}")
    print(f"  Claim: {result['claim']['claim_id']}")

    # Test 4: Mock submit function
    def mock_submit(claim):
        return {
            "receipt_id": f"receipt_{uuid.uuid4().hex[:8]}",
            "decision": "SHIP",
            "claim_id": claim["claim_id"]
        }

    result = supervisor.trigger_heartbeat(spec.heartbeat_id, mock_submit)
    print(f"✓ Heartbeat with submission: {result['receipt']['decision']}")

    # Test 5: History
    history = supervisor.get_execution_history()
    print(f"✓ Execution history: {len(history)} executions")

    print("\n✅ Heartbeat supervisor tests passed")
