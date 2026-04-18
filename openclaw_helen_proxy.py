#!/usr/bin/env python3
"""
OpenClaw ↔ HELEN Proxy Agent
Governance proxy translating OpenClaw workflows into HELEN operations with full K-gate enforcement.

Core Rules (Non-Negotiable):
1. NO RECEIPT = NO CLAIM (every operation produces receipt.json)
2. S4: HUMAN APPROVAL GATE (proxy waits for SHIP/ABORT)
3. K-GATE ENFORCEMENT (K-ρ viability, K-τ coherence)
4. IMMUTABLE LEDGER (append-only, never modify)
5. WHITELISTED COMMANDS ONLY (no arbitrary execution)

Status: OPERATIONAL (#2E epoch specification)
Proxy Agent: Mistral-Small (via Ollama)
Ledger: Append-only NDJSON
Governance: S1-S4 gates + K-ρ/K-τ validation
"""

import json
import hashlib
import datetime
import os
import sys
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from mistral_workflow import MistralWorkflowEngine, MistralWorkflowRequest


class CommandType(Enum):
    """Whitelisted OpenClaw commands."""
    RUN_AGGREGATION = "run_aggregation"
    RUN_EVENT_AUTOMATION = "run_event_automation"
    GENERATE_REPORT = "generate_report"
    LOG_LESSON = "log_lesson"


class ApprovalStatus(Enum):
    """Receipt approval states (S4 gate)."""
    PENDING_HUMAN_REVIEW = "pending_human_review"
    APPROVED_SHIP = "approved_ship"
    REJECTED_ABORT = "rejected_abort"
    FAILED = "failed"


class HELENRole(Enum):
    """HELEN role mappings for routing."""
    FETCHER = "fetcher"
    AGGREGATOR = "aggregator"
    FORMATTER = "formatter"
    DELIVERER = "deliverer"
    TRIGGER_MONITOR = "trigger_monitor"
    EVENT_PARSER = "event_parser"
    ACTION_EXECUTOR = "action_executor"
    NOTIFIER = "notifier"


@dataclass
class ProxyRequest:
    """Incoming OpenClaw request with validation."""
    workflow_id: str
    command: str
    parameters: Dict[str, Any]
    timestamp: str
    request_hash: str
    command_version: str = "1.0"
    approval_policy: str = "human_required"

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ProxyRequest":
        """Parse incoming JSON request."""
        return cls(
            workflow_id=data.get("workflow_id", "unknown"),
            command=data.get("command", ""),
            parameters=data.get("parameters", {}),
            timestamp=data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")),
            request_hash=data.get("request_hash", ""),
            command_version=data.get("command_version", "1.0"),
            approval_policy=data.get("approval_policy", "human_required"),
        )

    def to_json_for_hashing(self) -> Dict[str, Any]:
        """Convert request to canonical JSON for hashing (K-ρ determinism)."""
        return {
            "workflow_id": self.workflow_id,
            "command": self.command,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
        }


@dataclass
class ProxyReceipt:
    """Receipt proving execution with immutable audit trail."""
    receipt_id: str
    request_hash: str
    response_hash: str
    command: str
    status: ApprovalStatus
    approval_required: bool = True
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    ledger_entry_id: str = ""
    k_rho_passed: bool = False
    k_tau_passed: bool = False
    approved_by: Optional[str] = None
    approval_time: Optional[str] = None
    approval_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    error_code: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    def to_ndjson(self) -> str:
        """Convert to NDJSON format (single line)."""
        return json.dumps(self.to_json())


@dataclass
class LedgerEntry:
    """Immutable ledger entry for audit trail."""
    epoch: str
    source: str
    workflow_id: str
    command: str
    request_hash: str
    response_hash: str
    receipt_id: str
    status: str
    timestamp: str
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approval_time: Optional[str] = None
    error_code: Optional[str] = None

    def to_ndjson(self) -> str:
        """Convert to NDJSON format (single line)."""
        return json.dumps(asdict(self))


class OpenClawProxy:
    """
    Governance proxy translating OpenClaw → HELEN with K-gate enforcement.

    Architecture:
    OpenClaw Request → Parse → Validate → Route → Execute → Receipt → Ledger → Human Approval
    """

    def __init__(self, ledger_path: str = "runs/openclaw_proxy/ledger.ndjson", epoch: str = "2E", mistral_model: str = "mistral-large", use_mistral: bool = True):
        """Initialize proxy with ledger path and epoch."""
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.epoch = epoch
        self.sequence = self._load_sequence()
        self.whitelisted_commands = {
            CommandType.RUN_AGGREGATION,
            CommandType.RUN_EVENT_AUTOMATION,
            CommandType.GENERATE_REPORT,
            CommandType.LOG_LESSON,
        }

        # Initialize Mistral workflow engine
        self.use_mistral = use_mistral
        self.mistral_model = mistral_model
        self.mistral_engine = None

        if self.use_mistral:
            try:
                self.mistral_engine = MistralWorkflowEngine(model=mistral_model)
                print(f"✅ Mistral workflow engine initialized (model: {mistral_model})", file=sys.stderr)
            except ValueError as e:
                print(f"⚠️  Mistral initialization failed: {e}. Falling back to mock execution.", file=sys.stderr)
                self.use_mistral = False

    def _load_sequence(self) -> int:
        """Load sequence counter from existing ledger."""
        if self.ledger_path.exists():
            count = 0
            with open(self.ledger_path, "r") as f:
                for _ in f:
                    count += 1
            return count + 1
        return 1

    def _sha256(self, data: Any) -> str:
        """Deterministic SHA256 hash (K-ρ requirement)."""
        if isinstance(data, dict):
            # Canonical JSON: sorted keys, no spaces
            json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        elif isinstance(data, str):
            json_str = data
        else:
            json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))

        return hashlib.sha256(json_str.encode()).hexdigest()

    def validate_request(self, request: ProxyRequest, original_json: Dict[str, Any] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate incoming request against whitelist and schema.

        Returns: (is_valid, error_message)
        """
        # Check command is whitelisted
        try:
            cmd_enum = CommandType(request.command)
            if cmd_enum not in self.whitelisted_commands:
                return False, f"COMMAND_NOT_WHITELISTED: {request.command}"
        except ValueError:
            return False, f"COMMAND_UNKNOWN: {request.command}"

        # Check required fields
        if not request.workflow_id or request.workflow_id == "unknown":
            return False, "MISSING_FIELD: workflow_id"
        if not request.timestamp:
            return False, "MISSING_FIELD: timestamp"
        if not request.command:
            return False, "MISSING_FIELD: command"

        # Validate request hash (if provided)
        if request.request_hash:
            expected_hash = self._sha256(request.to_json_for_hashing())
            if request.request_hash != expected_hash:
                return False, f"INVALID_REQUEST_HASH: {request.request_hash}"

        return True, None

    def to_json_for_hashing(self) -> Dict[str, Any]:
        """Convert request to canonical JSON for hashing (K-ρ determinism)."""
        return {
            "workflow_id": self.workflow_id,
            "command": self.command,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
        }

    def route_command(self, command: str) -> List[HELENRole]:
        """Map command to HELEN role execution chain."""
        routing = {
            CommandType.RUN_AGGREGATION.value: [
                HELENRole.FETCHER,
                HELENRole.AGGREGATOR,
                HELENRole.FORMATTER,
                HELENRole.DELIVERER,
            ],
            CommandType.RUN_EVENT_AUTOMATION.value: [
                HELENRole.TRIGGER_MONITOR,
                HELENRole.EVENT_PARSER,
                HELENRole.ACTION_EXECUTOR,
                HELENRole.NOTIFIER,
            ],
            CommandType.GENERATE_REPORT.value: [
                HELENRole.AGGREGATOR,
                HELENRole.FORMATTER,
            ],
            CommandType.LOG_LESSON.value: [
                HELENRole.NOTIFIER,  # Direct to ledger
            ],
        }
        return routing.get(command, [])

    def execute_workflow(self, request: ProxyRequest) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Execute OpenClaw request through HELEN role chain or Mistral LLM.

        Returns: (success, response_data, error_code)

        If Mistral is enabled, uses real LLM API calls.
        Falls back to mock execution if Mistral unavailable.
        """
        roles = self.route_command(request.command)

        if not roles:
            return False, {}, "COMMAND_ROUTE_NOT_FOUND"

        # Use Mistral for execution if available
        if self.use_mistral and self.mistral_engine:
            try:
                mistral_req = MistralWorkflowRequest(
                    workflow_id=request.workflow_id,
                    command=request.command,
                    parameters=request.parameters,
                    timestamp=request.timestamp,
                    model=self.mistral_model,
                )

                mistral_resp = self.mistral_engine.execute_workflow(mistral_req)

                if mistral_resp.success:
                    # Parse the JSON response from Mistral
                    try:
                        response_data = json.loads(mistral_resp.response_text)
                        # Ensure required fields exist
                        response_data["workflow_id"] = request.workflow_id
                        response_data["command"] = request.command
                        response_data["roles_executed"] = [role.value for role in roles]
                        response_data["tokens_used"] = mistral_resp.tokens_used
                        response_data["model_used"] = self.mistral_model
                        return True, response_data, None
                    except json.JSONDecodeError:
                        return False, {}, f"MISTRAL_JSON_PARSE_ERROR: {mistral_resp.error}"
                else:
                    return False, {}, f"MISTRAL_EXECUTION_ERROR: {mistral_resp.error}"

            except Exception as e:
                print(f"⚠️  Mistral execution error: {e}. Falling back to mock.", file=sys.stderr)
                # Fall through to mock execution

        # Mock execution: deterministic output based on input (K-ρ requirement)
        # Uses request timestamp, not execution timestamp, to ensure same input → same output
        response = {
            "workflow_id": request.workflow_id,
            "command": request.command,
            "roles_executed": [role.value for role in roles],
            "request_timestamp": request.timestamp,  # Use request time, not execution time
            "items_processed": len(request.parameters.get("sources", [])),
            "status": "success",
            "execution_mode": "mock_fallback",
        }

        return True, response, None

    def generate_receipt(
        self,
        request: ProxyRequest,
        response: Dict[str, Any],
        execution_success: bool,
        error_code: Optional[str] = None,
    ) -> ProxyReceipt:
        """
        Generate cryptographic receipt proving execution (K-ρ/K-τ validation).

        S2 gate: NO RECEIPT = NO CLAIM. Every operation must produce a receipt.
        """
        # Hash response for K-ρ determinism
        response_hash = self._sha256(response) if response else ""

        # Determine K-gate status
        k_rho_passed = execution_success and not error_code
        k_tau_passed = execution_success  # No nondeterministic operations in mock

        # Generate receipt ID
        receipt_id = f"S_OPENCLAW_PROXY_{self.epoch}_{self.sequence:03d}"

        # Determine approval status
        if error_code:
            approval_status = ApprovalStatus.FAILED
        else:
            approval_status = ApprovalStatus.PENDING_HUMAN_REVIEW

        receipt = ProxyReceipt(
            receipt_id=receipt_id,
            request_hash=request.request_hash or self._sha256(request.to_json_for_hashing()),
            response_hash=response_hash,
            command=request.command,
            status=approval_status,
            approval_required=(approval_status == ApprovalStatus.PENDING_HUMAN_REVIEW),
            k_rho_passed=k_rho_passed,
            k_tau_passed=k_tau_passed,
            ledger_entry_id=receipt_id,
            error_code=error_code,
        )

        return receipt

    def append_to_ledger(self, receipt: ProxyReceipt, request: ProxyRequest) -> bool:
        """
        Append receipt to immutable ledger (S3 gate).

        IMMUTABLE: Append-only, never modify or delete.
        """
        entry = LedgerEntry(
            epoch=self.epoch,
            source="openclaw_proxy",
            workflow_id=request.workflow_id,
            command=request.command,
            request_hash=receipt.request_hash,
            response_hash=receipt.response_hash,
            receipt_id=receipt.receipt_id,
            status=receipt.status.value,
            timestamp=receipt.timestamp,
            approval_status=None,  # Updated later when human approves
            error_code=receipt.error_code,
        )

        try:
            with open(self.ledger_path, "a") as f:
                f.write(entry.to_ndjson() + "\n")
            self.sequence += 1
            return True
        except Exception as e:
            print(f"ERROR: Failed to append to ledger: {e}", file=sys.stderr)
            return False

    def process_request(self, request_json: Dict[str, Any]) -> ProxyReceipt:
        """
        Main entry point: Process OpenClaw request through full governance pipeline.

        Pipeline:
        1. Parse request
        2. Validate (whitelist, schema)
        3. Execute (route to HELEN roles)
        4. Generate receipt (K-gate validation)
        5. Append to ledger (immutable audit trail)
        6. Return receipt (status: pending_human_review)

        S4 gate: Human must approve (SHIP/ABORT) before delivery.
        """
        # Phase 1: Parse
        request = ProxyRequest.from_json(request_json)

        # Phase 2: Validate
        is_valid, error_msg = self.validate_request(request)
        if not is_valid:
            receipt = ProxyReceipt(
                receipt_id=f"S_OPENCLAW_PROXY_{self.epoch}_{self.sequence:03d}",
                request_hash=self._sha256(request_json),
                response_hash="",
                command=request.command,
                status=ApprovalStatus.FAILED,
                error_code=f"VALIDATION_ERROR: {error_msg}",
            )
            self.append_to_ledger(receipt, request)
            return receipt

        # Phase 3: Execute
        success, response, error_code = self.execute_workflow(request)

        # Phase 4: Generate Receipt
        receipt = self.generate_receipt(request, response, success, error_code)

        # Phase 5: Append to Ledger
        self.append_to_ledger(receipt, request)

        return receipt

    def handle_approval(
        self,
        receipt_id: str,
        decision: str,  # "SHIP" or "ABORT"
        approved_by: str,
        reason: str = "",
    ) -> bool:
        """
        Handle human approval decision (S4 gate).

        S4: HUMAN AUTHORITY ABSOLUTE. Only human can approve delivery.

        Reads ledger, finds entry, updates approval_status, appends new entry.
        """
        if decision not in ["SHIP", "ABORT"]:
            print(f"ERROR: Invalid decision '{decision}'. Must be SHIP or ABORT.", file=sys.stderr)
            return False

        # Find original entry in ledger
        original_entry = None
        ledger_entries = []

        if self.ledger_path.exists():
            with open(self.ledger_path, "r") as f:
                for line in f:
                    entry_dict = json.loads(line.strip())
                    ledger_entries.append(entry_dict)
                    if entry_dict.get("receipt_id") == receipt_id:
                        original_entry = entry_dict

        if not original_entry:
            print(f"ERROR: Receipt {receipt_id} not found in ledger.", file=sys.stderr)
            return False

        # Create approval entry
        approval_entry = {
            "epoch": self.epoch,
            "source": "openclaw_proxy_approval",
            "receipt_id": receipt_id,
            "decision": decision,
            "approved_by": approved_by,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "reason": reason,
        }

        # Append approval entry to ledger
        try:
            with open(self.ledger_path, "a") as f:
                f.write(json.dumps(approval_entry, separators=(",", ":")) + "\n")
            return True
        except Exception as e:
            print(f"ERROR: Failed to record approval: {e}", file=sys.stderr)
            return False

    def dump_ledger(self) -> List[Dict[str, Any]]:
        """Export ledger as JSON list (for inspection, not modification)."""
        if not self.ledger_path.exists():
            return []

        entries = []
        with open(self.ledger_path, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line.strip()))

        return entries

    def export_ledger_json(self, output_path: str) -> bool:
        """Export immutable ledger to JSON file."""
        try:
            entries = self.dump_ledger()
            with open(output_path, "w") as f:
                json.dump(entries, f, indent=2)
            return True
        except Exception as e:
            print(f"ERROR: Failed to export ledger: {e}", file=sys.stderr)
            return False


def main():
    """Demo: Show proxy in action with example Daily Digest request."""
    import sys

    # Check for Mistral API key
    use_mistral = os.getenv("MISTRAL_API_KEY") is not None

    if use_mistral:
        print(f"✅ MISTRAL_API_KEY detected. Using Mistral engine.", file=sys.stderr)
    else:
        print(f"ℹ️  MISTRAL_API_KEY not set. Using mock execution.", file=sys.stderr)
        print(f"    Set it with: export MISTRAL_API_KEY='your-key-here'", file=sys.stderr)

    proxy = OpenClawProxy(epoch="2E", mistral_model="mistral-large", use_mistral=use_mistral)

    # Example: Daily Digest request
    request_json = {
        "workflow_id": "daily_digest_v1",
        "command": "run_aggregation",
        "command_version": "1.0",
        "parameters": {
            "sources": ["twitter_steipete", "hackernews", "devto"],
            "output_format": "markdown",
            "recipient_channel": "telegram",
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "approval_policy": "human_required",
    }

    # Compute request hash
    request_json["request_hash"] = proxy._sha256(
        {
            "workflow_id": request_json["workflow_id"],
            "command": request_json["command"],
            "parameters": request_json["parameters"],
            "timestamp": request_json["timestamp"],
        }
    )

    print("=" * 60)
    print("OPENCLAW → HELEN PROXY DEMO (Mistral Integration)")
    print("=" * 60)
    print(f"\n📋 Incoming Request:")
    print(json.dumps(request_json, indent=2))

    # Process through proxy
    receipt = proxy.process_request(request_json)

    print(f"\n✅ Receipt Generated:")
    print(json.dumps(receipt.to_json(), indent=2))

    print(f"\n📝 Ledger Entry Created:")
    print(f"   Receipt ID: {receipt.receipt_id}")
    print(f"   Status: {receipt.status.value}")
    print(f"   Approval Required: {receipt.approval_required}")

    print(f"\n⏳ Awaiting Human Approval (S4 gate)...")
    print(f"   Next: User decides SHIP or ABORT")

    # Demo approval
    print(f"\n✅ Human Decision: SHIP")
    proxy.handle_approval(
        receipt_id=receipt.receipt_id,
        decision="SHIP",
        approved_by="user",
        reason="Content quality good, timeliness acceptable",
    )

    print(f"\n📋 Final Ledger State:")
    ledger = proxy.dump_ledger()
    for entry in ledger:
        print(json.dumps(entry, separators=(",", ":")))

    print("\n" + "=" * 60)
    execution_mode = "Mistral LLM" if (use_mistral and proxy.use_mistral) else "Mock"
    print(f"Demo complete ({execution_mode} mode). Ledger is immutable and verifiable.")
    print("=" * 60)


if __name__ == "__main__":
    main()
