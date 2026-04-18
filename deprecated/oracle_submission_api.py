"""
Oracle Town Submission API
==========================
Production-ready stub for submitting validated proposals to Oracle Town Intake.

This module handles:
- Real HTTP POST submission to Oracle governance endpoint
- Authentication (Bearer token)
- Response parsing (ACCEPT|REJECT|FLAGGED verdicts)
- Error handling and retry logic
- Audit logging of all submissions

Usage:
    api = OracleSubmissionAPI(endpoint="https://oracle-intake.local/submit")
    receipt = api.submit(validated_proposals, auth_token="...")
    print(f"Submission ID: {receipt['submission_id']}")
"""

import json
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class OracleReceipt:
    """Confirmation of submission to Oracle Town Intake."""
    submission_id: str
    timestamp: str
    total_proposals: int
    accepted_count: int
    rejected_count: int
    flagged_count: int
    oracle_intake_url: str
    ledger_entry_hash: str


class OracleSubmissionAPI:
    """Interface for submitting validated proposals to Oracle Town governance."""
    
    def __init__(
        self,
        endpoint: str = "http://localhost:8000/governance/intake",
        timeout: int = 30,
        retry_count: int = 3,
        audit_log: Optional[Path] = None
    ):
        """
        Initialize submission API client.
        
        Args:
            endpoint: Oracle Town Intake HTTP endpoint
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed submissions
            audit_log: Path to append-only audit log of submissions
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self.retry_count = retry_count
        self.audit_log = audit_log or Path("oracle_submissions.jsonl")
        
        logger.info(f"Oracle API initialized: endpoint={endpoint}")
    
    def submit(
        self,
        proposals: List[Dict[str, Any]],
        auth_token: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit validated proposals to Oracle Town Intake.
        
        Args:
            proposals: List of validated proposals (already passed validation gate)
            auth_token: Bearer token for authentication (can be env var ORACLE_AUTH_TOKEN)
            metadata: Additional submission metadata (workflow_id, priority, etc.)
        
        Returns:
            Receipt with submission_id, counts, and ledger hash
        
        Raises:
            OracleSubmissionError: If submission fails after retries
        """
        
        if not proposals:
            logger.warning("No proposals to submit")
            return {"total_submitted": 0, "status": "empty"}
        
        # Prepare submission payload
        submission_payload = {
            "proposals": proposals,
            "submission_timestamp": datetime.utcnow().isoformat(),
            "submission_source": "governance_wrapped_runner",
            "metadata": metadata or {},
            "signature": None  # Will be computed below
        }
        
        # Compute request signature for integrity verification
        payload_json = json.dumps(submission_payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        submission_payload["signature"] = payload_hash
        
        # Get auth token (from parameter, env var, or config)
        if not auth_token:
            auth_token = self._get_auth_token()
        
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "X-Request-ID": self._generate_request_id()
        }
        
        # Attempt submission with retries
        response = None
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Submission attempt {attempt + 1}/{self.retry_count}: {len(proposals)} proposals")
                
                response = requests.post(
                    self.endpoint,
                    json=submission_payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Check response status
                if response.status_code == 200:
                    receipt_data = response.json()
                    receipt = OracleReceipt(
                        submission_id=receipt_data.get("submission_id"),
                        timestamp=datetime.utcnow().isoformat(),
                        total_proposals=len(proposals),
                        accepted_count=receipt_data.get("accepted_count", len(proposals)),
                        rejected_count=receipt_data.get("rejected_count", 0),
                        flagged_count=receipt_data.get("flagged_count", 0),
                        oracle_intake_url=receipt_data.get("intake_url", self.endpoint),
                        ledger_entry_hash=receipt_data.get("ledger_hash", payload_hash)
                    )
                    
                    # Log submission to audit trail
                    self._log_audit_trail({
                        "submission_id": receipt.submission_id,
                        "timestamp": receipt.timestamp,
                        "total_proposals": len(proposals),
                        "response_status": response.status_code,
                        "ledger_hash": receipt.ledger_entry_hash
                    })
                    
                    logger.info(f"✅ Submission successful: ID={receipt.submission_id}")
                    return asdict(receipt)
                
                elif response.status_code == 202:
                    # Accepted for processing
                    logger.info(f"⏳ Submission queued (202): {response.text[:100]}")
                    return {"status": "queued", "response_code": 202}
                
                elif response.status_code >= 400:
                    logger.warning(f"Submission error ({response.status_code}): {response.text[:200]}")
                    if attempt < self.retry_count - 1:
                        continue
                    raise OracleSubmissionError(f"HTTP {response.status_code}: {response.text[:500]}")
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.retry_count - 1:
                    continue
                raise OracleSubmissionError(f"Connection failed after {self.retry_count} retries: {e}")
        
        # All retries exhausted
        raise OracleSubmissionError(f"Submission failed after {self.retry_count} attempts")
    
    def submit_local_ledger(
        self,
        proposals: List[Dict[str, Any]],
        ledger_path: Path
    ) -> Dict[str, Any]:
        """
        For dev/testing: append proposals to local ledger instead of HTTP submission.
        
        Args:
            proposals: Validated proposals
            ledger_path: Path to local JSONL ledger file
        
        Returns:
            Local receipt with file path and line count
        """
        
        logger.info(f"Writing {len(proposals)} proposals to local ledger: {ledger_path}")
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "submission_source": "governance_wrapped_runner",
            "proposals": proposals,
            "entry_hash": hashlib.sha256(
                json.dumps(proposals, sort_keys=True).encode()
            ).hexdigest()
        }
        
        # Append to JSONL ledger
        with open(ledger_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Count total entries
        line_count = sum(1 for _ in open(ledger_path))
        
        logger.info(f"✅ Local ledger write: {ledger_path} (entry #{line_count})")
        
        return {
            "submission_id": f"LOCAL_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "ledger_path": str(ledger_path),
            "entry_number": line_count,
            "total_proposals": len(proposals),
            "status": "ledger_entry_created"
        }
    
    def _get_auth_token(self) -> str:
        """Retrieve authentication token from environment or config."""
        import os
        
        token = os.getenv("ORACLE_AUTH_TOKEN")
        if not token:
            # Fallback: check .env file
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.startswith("ORACLE_AUTH_TOKEN="):
                            token = line.split("=", 1)[1].strip()
                            break
        
        if not token:
            logger.warning("No auth token found; using ANONYMOUS_TOKEN")
            token = "ANONYMOUS_TOKEN"
        
        return token
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracing."""
        import uuid
        return str(uuid.uuid4())
    
    def _log_audit_trail(self, entry: Dict[str, Any]) -> None:
        """Append submission event to immutable audit log."""
        try:
            with open(self.audit_log, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


class OracleSubmissionError(Exception):
    """Exception raised during Oracle submission failures."""
    pass


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example proposals (would come from governance_wrapped_runner)
    example_proposals = [
        {
            "proposal_id": "PRO_20240115_001",
            "category": "divergent_idea",
            "synthesis": "Implement multi-agent reasoning layer for policy decisions",
            "source_claims": ["CLM_20240115_001", "CLM_20240115_002"],
            "num_supporting_agents": 3,
            "validation_status": "passed"
        },
        {
            "proposal_id": "PRO_20240115_002",
            "category": "pattern_mapping",
            "synthesis": "Cross-domain analogy from organizational psychology to governance",
            "source_claims": ["CLM_20240115_003"],
            "num_supporting_agents": 1,
            "validation_status": "passed"
        }
    ]
    
    # Test 1: Local ledger submission (for dev)
    print("\n📝 Test 1: Local ledger submission")
    api = OracleSubmissionAPI()
    receipt = api.submit_local_ledger(
        example_proposals,
        ledger_path=Path("test_oracle_ledger.jsonl")
    )
    print(f"Receipt: {receipt}")
    
    # Test 2: HTTP submission (requires running Oracle Town endpoint)
    print("\n🌐 Test 2: HTTP submission (would connect to real Oracle endpoint)")
    print(f"Endpoint: http://localhost:8000/governance/intake")
    print(f"Proposals: {len(example_proposals)}")
    print("(Skipping actual HTTP call in test mode)")
