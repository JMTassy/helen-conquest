"""
Key Registry utilities: load registry, compute registry hash, and verify attestation bindings.

Deterministic canonicalization is used when computing registry hash.
"""
from __future__ import annotations
import json
import hashlib
import os
from typing import Dict, Any, Tuple, Optional


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def compute_registry_hash(registry: Dict[str, Any]) -> str:
    """Compute SHA256 hash of canonical registry JSON."""
    # Ensure we don't include any manifest fields accidentally
    canonical = canonical_json_bytes(registry)
    digest = hashlib.sha256(canonical).hexdigest()
    return f"sha256:{digest}"


class KeyRegistry:
    def __init__(self, registry_path: str, manifest_path: Optional[str] = None):
        if not os.path.exists(registry_path):
            raise FileNotFoundError(f"Key registry not found: {registry_path}")

        with open(registry_path, 'r') as f:
            self.registry_raw = json.load(f)

        self.registry_path = registry_path
        self.manifest_path = manifest_path

        # Normalize: expect top-level keys: registry_id, registry_version, created_at, keys[]
        keys_list = self.registry_raw.get("keys", [])
        # Build mapping by signing_key_id for fast lookup
        self.registry = {k["signing_key_id"]: k for k in keys_list}

        self.registry_hash = compute_registry_hash(self.registry_raw)

        # Optional: load manifest
        self.manifest = None
        if manifest_path and os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                self.manifest = json.load(f)

    def get_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        return self.registry.get(key_id)

    def verify_key_exists(self, key_id: str) -> bool:
        return key_id in self.registry

    def verify_attestor_binding(
        self,
        attestor_id: str,
        attestor_class: str,
        key_id: str,
        obligation: Optional[str] = None,
        policy_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Verify that key exists, class matches, attestor is allowlisted, key active, and scope matches."""
        if key_id not in self.registry:
            return False, "KEY_UNKNOWN"

        key_info = self.registry[key_id]

        # Status check
        status = key_info.get("status", "ACTIVE")
        if status != "ACTIVE":
            return False, "KEY_REVOKED"

        # Class binding
        if key_info.get("attestor_class") != attestor_class:
            return False, "KEY_CLASS_MISMATCH"

        # Attestor allowlist (optional)
        allow = key_info.get("allow", {})
        obligations_allowed = allow.get("obligations", ["*"])
        policy_ids_allowed = allow.get("policy_ids", ["*"])

        # Obligation scope check
        if obligation and obligations_allowed != ["*"] and obligation not in obligations_allowed:
            return False, "KEY_SCOPE_VIOLATION"

        # Policy id scope check
        if policy_id and policy_ids_allowed != ["*"] and policy_id not in policy_ids_allowed:
            return False, "KEY_POLICY_VIOLATION"

        # Attestor id metadata allowlist (if present)
        allow_attestors = key_info.get("attestor_id_allowlist") or []
        if allow_attestors and attestor_id not in allow_attestors:
            return False, "KEY_ATTESTOR_NOT_ALLOWLISTED"

        return True, "OK"
