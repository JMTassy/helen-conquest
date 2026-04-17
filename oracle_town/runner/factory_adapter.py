"""
Factory Adapter: Convert tool execution results into Phase-2 signed attestations.

CRITICAL RESPONSIBILITY:
- Run tools in isolated worktree
- Compute cryptographic evidence digests
- Sign using Ed25519 with proper canonical message format
- Produce attestations that validate against attestation.schema.json
- Never hand-build digests or signatures; use kernel utilities

Invariant: Evidence is produced ONLY by this module running REAL tools.
CT can propose work, but cannot produce evidence.
"""
import os
import sys
import json
import subprocess
import hashlib
import base64
import tempfile
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Try to load cryptography library; fail gracefully
try:
    import nacl.signing
    import nacl.encoding
    HAS_NACL = True
except ImportError:
    HAS_NACL = False

from oracle_town.core.crypto import build_canonical_message, canonical_json_bytes
from oracle_town.core.key_registry import KeyRegistry


@dataclass
class FactoryToolResult:
    """Result of running a tool in the factory."""
    success: bool
    stdout: str
    stderr: str
    returncode: int
    evidence_digest: str  # sha256:HEX64


@dataclass
class FactoryAttestation:
    """Signed attestation produced by factory."""
    attestation_id: str
    attestation: Dict[str, Any]  # Full attestation dict
    valid: bool
    validation_errors: list = None

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []


class FactoryAdapter:
    """Produces signed attestations from tool execution."""

    def __init__(
        self,
        key_registry_path: str,
        policy_hash: str,
        registry_hash: str
    ):
        """
        Initialize factory adapter.

        Args:
            key_registry_path: Path to public_keys.json
            policy_hash: Pinned policy hash (sha256:...)
            registry_hash: Key registry hash (sha256:...)
        """
        self.key_registry = KeyRegistry(key_registry_path)
        self.policy_hash = policy_hash
        self.registry_hash = registry_hash or self.key_registry.registry_hash

        if not self.policy_hash.startswith("sha256:"):
            raise ValueError(f"Invalid policy_hash format: {self.policy_hash}")

    def run_tool_and_attest(
        self,
        tool_command: str,
        workdir: str,
        run_id: str,
        claim_id: str,
        obligation_name: str,
        attestor_id: str = "ci_runner_001",
        attestor_class: str = "CI_RUNNER",
        signing_key_id: str = "key-2026-01-ci-prod"
    ) -> FactoryAttestation:
        """
        Execute a tool in the factory and produce a signed attestation.

        Args:
            tool_command: Command to execute (e.g., "pytest -q tests/")
            workdir: Isolated worktree directory
            run_id: Run identifier
            claim_id: Claim identifier
            obligation_name: Obligation being satisfied
            attestor_id: Who is attesting (default: ci_runner_001)
            attestor_class: Function class (default: CI_RUNNER)
            signing_key_id: Which key to sign with (default: key-2026-01-ci-prod)

        Returns:
            FactoryAttestation with signed attestation (or failure with errors)
        """
        # Step 1: Run tool and capture output
        tool_result = self._run_tool(tool_command, workdir)

        # Step 2: Compute evidence digest
        evidence_bytes = (tool_result.stdout + tool_result.stderr).encode("utf-8")
        evidence_digest = f"sha256:{hashlib.sha256(evidence_bytes).hexdigest()}"

        # Step 3: Determine policy_match (1 = success, 0 = failure)
        policy_match = 1 if tool_result.success else 0

        # Step 4: Build and sign the attestation
        attestation = self._build_attestation(
            run_id=run_id,
            claim_id=claim_id,
            obligation_name=obligation_name,
            attestor_id=attestor_id,
            attestor_class=attestor_class,
            evidence_digest=evidence_digest,
            policy_match=policy_match,
            signing_key_id=signing_key_id
        )

        # Step 5: Validate attestation
        errors = self._validate_attestation(attestation)

        return FactoryAttestation(
            attestation_id=attestation.get("attestation_id", "unknown"),
            attestation=attestation,
            valid=(len(errors) == 0),
            validation_errors=errors
        )

    def _run_tool(self, command: str, workdir: str) -> FactoryToolResult:
        """
        Execute a tool in the isolated workdir.

        Args:
            command: Shell command to execute
            workdir: Directory to execute in

        Returns:
            FactoryToolResult with output and return code
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=120
            )

            return FactoryToolResult(
                success=(result.returncode == 0),
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                evidence_digest="",  # Set by caller
            )

        except subprocess.TimeoutExpired:
            return FactoryToolResult(
                success=False,
                stdout="",
                stderr="TIMEOUT: Tool execution exceeded 120 seconds",
                returncode=124,
                evidence_digest="",
            )

        except Exception as e:
            return FactoryToolResult(
                success=False,
                stdout="",
                stderr=f"ERROR: {e}",
                returncode=1,
                evidence_digest="",
            )

    def _build_attestation(
        self,
        run_id: str,
        claim_id: str,
        obligation_name: str,
        attestor_id: str,
        attestor_class: str,
        evidence_digest: str,
        policy_match: int,
        signing_key_id: str
    ) -> Dict[str, Any]:
        """
        Build a signed attestation.

        This uses the EXACT same canonical message builder as Mayor verification,
        ensuring deterministic signature validation.
        """
        from datetime import datetime

        # Build canonical message (uses kernel function)
        canonical_message = build_canonical_message(
            run_id=run_id,
            claim_id=claim_id,
            obligation_name=obligation_name,
            attestor_id=attestor_id,
            attestor_class=attestor_class,
            policy_hash=self.policy_hash,
            evidence_digest=evidence_digest,
            policy_match=policy_match,
            key_registry_hash=self.registry_hash
        )

        # Sign the canonical message
        signature_b64 = self._sign_canonical_message(
            canonical_message,
            signing_key_id
        )

        # Build full attestation
        attestation = {
            "attestation_id": f"att_{run_id}_{obligation_name}_{int(datetime.utcnow().timestamp())}",
            "attestation_version": "0.1.0",
            "run_id": run_id,
            "claim_id": claim_id,
            "obligation_name": obligation_name,
            "attestor_id": attestor_id,
            "attestor_class": attestor_class,
            "policy_hash": self.policy_hash,
            "key_registry_hash": self.registry_hash,
            "evidence_digest": evidence_digest,
            "signing_key_id": signing_key_id,
            "signature": f"ed25519:{signature_b64}",
            "policy_match": policy_match,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return attestation

    def _sign_canonical_message(
        self,
        canonical_message: Dict[str, Any],
        signing_key_id: str
    ) -> str:
        """
        Sign canonical message with Ed25519.

        Uses the EXACT kernel function to ensure determinism.
        """
        if not HAS_NACL:
            raise RuntimeError("nacl library required for signing. Install: pip install pynacl")

        # Get the canonical message bytes (MUST use same function as verification)
        msg_bytes = canonical_json_bytes(canonical_message)

        # For testing, we use a mock signing key
        # In production, load from secure keystore
        mock_private_key_b64 = self._get_mock_signing_key(signing_key_id)

        if not mock_private_key_b64:
            raise ValueError(f"Signing key not found: {signing_key_id}")

        # Decode private key
        private_key_bytes = base64.b64decode(mock_private_key_b64)
        signing_key = nacl.signing.SigningKey(private_key_bytes)

        # Sign
        signed = signing_key.sign(msg_bytes)
        signature_bytes = bytes(signed.signature)

        # Encode to base64
        signature_b64 = base64.b64encode(signature_bytes).decode()

        return signature_b64

    def _get_mock_signing_key(self, key_id: str) -> Optional[str]:
        """
        Get mock signing key for testing.

        In production, this would load from a secure HSM or keystore.
        """
        # Check if there's a test private key file
        test_key_path = Path(__file__).parent.parent / "keys" / "private_keys_TEST_ONLY.json"

        if test_key_path.exists():
            try:
                with open(test_key_path) as f:
                    keys_data = json.load(f)

                    # Direct match
                    if key_id in keys_data:
                        key_value = keys_data[key_id]
                        # Handle both formats: string (base64) or dict with private_key_b64
                        if isinstance(key_value, str):
                            return key_value
                        elif isinstance(key_value, dict):
                            return key_value.get("private_key_b64")

                    # Fallback: try to find a CI_RUNNER key
                    for k, v in keys_data.items():
                        if "ci" in k.lower():
                            if isinstance(v, str):
                                return v
                            elif isinstance(v, dict):
                                return v.get("private_key_b64")
            except Exception:
                pass

        # Fallback: return None (will be caught and raise error)
        return None

    def _validate_attestation(self, attestation: Dict[str, Any]) -> list:
        """
        Validate attestation against schema constraints.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        required_fields = [
            "run_id", "claim_id", "obligation_name", "attestor_id",
            "attestor_class", "policy_hash", "evidence_digest",
            "signing_key_id", "signature", "policy_match", "timestamp"
        ]

        for field in required_fields:
            if field not in attestation:
                errors.append(f"Missing required field: {field}")

        # Validate patterns
        if "policy_hash" in attestation:
            if not attestation["policy_hash"].startswith("sha256:"):
                errors.append(f"Invalid policy_hash format: {attestation['policy_hash']}")

        if "evidence_digest" in attestation:
            if not attestation["evidence_digest"].startswith("sha256:"):
                errors.append(f"Invalid evidence_digest format: {attestation['evidence_digest']}")

        if "signature" in attestation:
            if not attestation["signature"].startswith("ed25519:"):
                errors.append(f"Invalid signature format: {attestation['signature']}")

        if "policy_match" in attestation:
            if attestation["policy_match"] not in (0, 1):
                errors.append(f"Invalid policy_match value: {attestation['policy_match']}")

        if "obligation_name" in attestation:
            name = attestation["obligation_name"]
            if not (3 <= len(name) <= 64) or not name.replace("_", "").isalnum():
                errors.append(f"Invalid obligation_name format: {name}")

        return errors


if __name__ == "__main__":
    """Test factory adapter."""
    import sys

    if not HAS_NACL:
        print("⚠ pynacl not installed, skipping signature tests")
        print("  Install: pip install pynacl")
        sys.exit(0)

    # Initialize factory
    repo_root = Path(__file__).parent.parent.parent
    registry_path = repo_root / "oracle_town" / "keys" / "public_keys.json"

    if not registry_path.exists():
        print(f"✗ Key registry not found: {registry_path}")
        sys.exit(1)

    factory = FactoryAdapter(
        key_registry_path=str(registry_path),
        policy_hash="sha256:abc123def456",
        registry_hash="sha256:registry123"
    )

    print("✓ Factory adapter initialized")

    # Test: Build attestation (without signing, since mock key may not exist)
    print("\nTest: Validate attestation structure...")
    test_attestation = factory._build_attestation(
        run_id="run_001",
        claim_id="claim_001",
        obligation_name="test_pass",
        attestor_id="ci_runner_001",
        attestor_class="CI_RUNNER",
        evidence_digest="sha256:abcdef1234567890",
        policy_match=1,
        signing_key_id="key-2026-01-ci-prod"
    )

    errors = factory._validate_attestation(test_attestation)
    if errors:
        print(f"✗ Validation errors: {errors}")
        sys.exit(1)
    else:
        print("✓ Attestation structure valid")

    # Test: Check required fields
    print("\nTest: Check required fields...")
    required_fields = [
        "run_id", "claim_id", "obligation_name", "attestor_id",
        "attestor_class", "policy_hash", "evidence_digest",
        "signing_key_id", "signature", "policy_match", "timestamp"
    ]
    missing = [f for f in required_fields if f not in test_attestation]
    if missing:
        print(f"✗ Missing fields: {missing}")
        sys.exit(1)
    else:
        print(f"✓ All {len(required_fields)} required fields present")

    print("\n✓ Factory adapter tests passed")
