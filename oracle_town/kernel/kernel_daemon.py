#!/usr/bin/env python3
"""
Oracle Town Kernel Daemon

Socket-based safety kernel for agent systems.

Serves requests from external agents (Clawdbot, OpenClaw, etc.):
  - Gate A: Fetch/Shell/Authority detection
  - Gate B: Memory safety (jailbreak/credential/tool injection)
  - Gate C: Invariants (scope/skill/authority escalation)
  - Mayor: Receipt generation
  - Ledger: Immutable decision recording

K24: Daemon Liveness - if unreachable, execution denied (fail-closed)
"""

import json
import socket
import os
import sys
from pathlib import Path

# Import kernel modules
sys.path.insert(0, str(Path(__file__).parent))

from gate_a import gate_a, GateResult as GateAResult
from gate_b_memory import gate_b_memory, MemoryClaim
from gate_c import gate_c
from mayor import MayorReceiptEngine, PolicyRegistry, Claim, Evidence
from ledger import InMemoryLedger


class KernelDaemon:
    """
    Kernel daemon: accepts requests via Unix socket, enforces safety gates.

    K24: Fail-closed on unreachable daemon
    - If client can't reach kernel, execution is denied
    - No retries, no eventual-allow fallback
    """

    def __init__(self, socket_path: str = "~/.openclaw/oracle_town.sock"):
        self.socket_path = Path(socket_path).expanduser()
        self.policy = PolicyRegistry(version="POLICY_v1.0")
        self.mayor = MayorReceiptEngine(self.policy)
        self.ledger = InMemoryLedger()
        self.socket = None

    def start(self):
        """Start the kernel daemon listening on Unix socket"""
        # Remove existing socket if present
        if self.socket_path.exists():
            self.socket_path.unlink()

        # Create parent directory if needed
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Unix domain socket
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(self.socket_path))
        self.socket.listen(1)

        print(f"✅ Kernel daemon listening on {self.socket_path}")
        print("Enforcement: K15, K18, K19, K20, K21, K22, K23, K24")

        try:
            while True:
                connection, _ = self.socket.accept()
                try:
                    self.handle_request(connection)
                except Exception as e:
                    self._send_error(connection, str(e))
                finally:
                    connection.close()
        except KeyboardInterrupt:
            print("\n🛑 Kernel daemon stopped")
        finally:
            self.socket.close()
            self.socket_path.unlink()

    def handle_request(self, connection):
        """Handle incoming request from agent"""
        # Read request
        data = connection.recv(4096).decode()
        request = json.loads(data)

        # Route to appropriate handler
        operation = request.get("operation")

        if operation == "fetch":
            response = self._handle_fetch(request)
        elif operation == "memory":
            response = self._handle_memory(request)
        elif operation == "check_invariants":
            response = self._handle_invariants(request)
        elif operation == "dialog":
            response = self._handle_dialog(request)
        else:
            response = {"error": f"Unknown operation: {operation}"}

        # Send response
        connection.sendall(json.dumps(response).encode())

    def _handle_fetch(self, request):
        """
        Handle fetch operation (Gate A)

        Input: {"operation": "fetch", "content": "..."}
        Output: {"decision": "ACCEPT|REJECT", "receipt_id": "...", "reason": "..."}
        """
        content = request.get("content", "")

        # Run Gate A
        gate_decision = gate_a(content)

        # Create claim
        claim = Claim(
            claim_id=request.get("claim_id", "fetch:unknown"),
            proposer=request.get("proposer", "unknown"),
            intent=request.get("intent", "Fetch operation"),
            timestamp=request.get("timestamp", "2026-01-30T00:00:00Z")
        )

        # Create evidence
        evidence = Evidence(
            content_snapshot=content,
            content_hash=gate_decision.content_hash,
            gates_run={"gate_a": {
                "result": gate_decision.result.value,
                "code": gate_decision.code,
                "reason": gate_decision.reason
            }}
        )

        # Get receipt from Mayor
        receipt = self.mayor.ratify(claim, evidence)

        # Record in ledger
        self.ledger.record("CLAIM", {
            "claim_id": claim.claim_id,
            "proposer": claim.proposer,
            "intent": claim.intent
        })
        self.ledger.record("RECEIPT", {
            "receipt_id": receipt.receipt_id,
            "decision": receipt.decision,
            "policy_version": receipt.policy_version
        })

        return {
            "decision": receipt.decision,
            "receipt_id": receipt.receipt_id,
            "reason": receipt.reason or receipt.reason,
            "gate": gate_decision.code
        }

    def _handle_memory(self, request):
        """
        Handle memory operation (Gate B)

        Input: {"operation": "memory", "content": "...", "category": "...", ...}
        Output: {"decision": "ACCEPT|REJECT", "reason": "..."}
        """
        claim = MemoryClaim(
            claim_id=request.get("claim_id", "memory:unknown"),
            operation=request.get("mem_operation", "store"),
            content=request.get("content", ""),
            category=request.get("category", "fact"),
            scope=request.get("scope", "hostname:local"),
            source=request.get("source", "unknown")
        )

        # Run Gate B
        gate_decision = gate_b_memory(claim)

        # Record in ledger
        self.ledger.record("CLAIM", {
            "claim_id": claim.claim_id,
            "operation": claim.operation,
            "category": claim.category
        })

        return {
            "decision": gate_decision.result.value,
            "reason": gate_decision.reason,
            "gate": gate_decision.code
        }

    def _handle_invariants(self, request):
        """
        Handle invariants check (Gate C)

        Input: {"operation": "check_invariants", "content": "...", "old_scope": {}, "new_scope": {}}
        Output: {"decision": "ACCEPT|REJECT", "reason": "..."}
        """
        # Run Gate C
        gate_decision = gate_c(
            proposal=request.get("content", ""),
            old_scope=request.get("old_scope", {}),
            new_scope=request.get("new_scope", {}),
            claimed_policy=request.get("claimed_policy"),
            actual_policy=request.get("actual_policy")
        )

        # Record in ledger
        self.ledger.record("CLAIM", {
            "claim_id": request.get("claim_id", "invariants:unknown"),
            "type": "invariants_check"
        })

        return {
            "decision": gate_decision.result.value,
            "reason": gate_decision.reason,
            "gate": gate_decision.code
        }

    def _handle_dialog(self, request):
        """
        Handle dialog operation (safe local UI action)

        Input: {"operation": "dialog", "text": "...", "claim_id": "...", "proposer": "helen", ...}
        Output: {"decision": "ACCEPT|REJECT", "receipt_id": "...", "gate": "GATE_DIALOG_..."}
        """
        text = request.get("text", "Dialog")

        # For dialog, we use Gate A (content-based safety check on the dialog text)
        # This prevents injection attacks even in local UI
        gate_decision = gate_a(text)

        # Create claim
        claim = Claim(
            claim_id=request.get("claim_id", "dialog:unknown"),
            proposer=request.get("proposer", "unknown"),
            intent=request.get("intent", "Dialog operation"),
            timestamp=request.get("timestamp", "2026-01-30T00:00:00Z")
        )

        # Create evidence
        evidence = Evidence(
            content_snapshot=text,
            content_hash=gate_decision.content_hash,
            gates_run={"gate_a": {
                "result": gate_decision.result.value,
                "code": gate_decision.code,
                "reason": gate_decision.reason
            }}
        )

        # Get receipt from Mayor
        receipt = self.mayor.ratify(claim, evidence)

        # Record in ledger
        self.ledger.record("CLAIM", {
            "claim_id": claim.claim_id,
            "proposer": claim.proposer,
            "intent": claim.intent,
            "type": "dialog"
        })
        self.ledger.record("RECEIPT", {
            "receipt_id": receipt.receipt_id,
            "decision": receipt.decision,
            "policy_version": receipt.policy_version
        })

        return {
            "decision": receipt.decision,
            "receipt_id": receipt.receipt_id,
            "reason": receipt.reason or gate_decision.reason,
            "gate": gate_decision.code
        }

    def _send_error(self, connection, error_msg):
        """Send error response"""
        response = {
            "error": error_msg,
            "decision": "REJECT",
            "gate": "KERNEL_ERROR"
        }
        connection.sendall(json.dumps(response).encode())


if __name__ == "__main__":
    # Run kernel daemon
    daemon = KernelDaemon()
    daemon.start()
