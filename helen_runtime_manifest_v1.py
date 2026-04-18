"""
HELEN_RUNTIME_MANIFEST_V1: Frozen Bootstrap Configuration

Purpose:
- Single source of truth for session initialization
- All receipts reference manifest_hash
- Deterministic bootstrap (no hidden I/O)
- Capability surface declaration (tools, skills, agents)

Law:
- Manifest is frozen at boot
- All dispatch receipts must reference manifest_ref
- No dispatch without manifest hash present
- Store paths declared explicitly (no implicit discovery)
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class StoreDeclaration:
    """A single declared store."""
    store_id: str
    store_type: str   # local_ndjson | hash_chain | local_json
    path: str
    purpose: str      # context | ledger | transcript | shadow


@dataclass
class CapabilitySurface:
    """Declared capability surface (frozen at boot)."""
    tools_frozen: bool = True
    include_mcp: bool = False
    skill_count: int = 0
    agent_count: int = 0
    known_skills: List[str] = field(default_factory=list)
    known_agents: List[str] = field(default_factory=list)


@dataclass
class RuntimeManifest:
    """
    Frozen bootstrap manifest for HELEN session.

    Invariants:
    - manifest_hash computed at creation, never changes
    - All dispatch receipts reference this hash
    - Stores declared explicitly
    """
    manifest_id: str
    kernel_version: str
    timestamp_created: str

    stores: List[StoreDeclaration] = field(default_factory=list)
    capability_surface: CapabilitySurface = field(default_factory=CapabilitySurface)
    dispatch_layer_version: str = "HELEN_DISPATCH_LAYER_V1"
    pressure_signal_version: str = "HELEN_PRESSURE_SIGNAL_V1"
    affect_translation_version: str = "HELEN_AFFECT_TRANSLATION_V1"
    chain_receipt_version: str = "HELEN_CHAIN_RECEIPT_V1"

    manifest_hash: Optional[str] = None  # Computed at freeze

    def to_dict(self, exclude_hash: bool = False) -> Dict[str, Any]:
        d = {
            "manifest_id": self.manifest_id,
            "kernel_version": self.kernel_version,
            "timestamp_created": self.timestamp_created,
            "dispatch_layer_version": self.dispatch_layer_version,
            "pressure_signal_version": self.pressure_signal_version,
            "affect_translation_version": self.affect_translation_version,
            "chain_receipt_version": self.chain_receipt_version,
            "stores": [
                {
                    "store_id": s.store_id,
                    "store_type": s.store_type,
                    "path": s.path,
                    "purpose": s.purpose,
                }
                for s in self.stores
            ],
            "capability_surface": {
                "tools_frozen": self.capability_surface.tools_frozen,
                "include_mcp": self.capability_surface.include_mcp,
                "skill_count": self.capability_surface.skill_count,
                "agent_count": self.capability_surface.agent_count,
                "known_skills": self.capability_surface.known_skills,
                "known_agents": self.capability_surface.known_agents,
            },
        }
        if not exclude_hash:
            d["manifest_hash"] = self.manifest_hash
        return d

    def freeze(self) -> str:
        """Compute and store manifest_hash. Returns hash."""
        data = self.to_dict(exclude_hash=True)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        self.manifest_hash = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
        return self.manifest_hash

    def to_store_refs(self) -> Dict[str, str]:
        """Return store_refs dict for use in DispatchReceipts."""
        return {s.purpose: f"{s.store_type}://{s.path}" for s in self.stores}


class ManifestBootstrap:
    """Bootstrap HELEN runtime from manifest."""

    @staticmethod
    def create_default(
        session_id: str,
        base_path: str = ".",
        kernel_version: str = "helen_os_v1_dispatch_release",
    ) -> RuntimeManifest:
        """Create a default manifest for a session."""

        manifest = RuntimeManifest(
            manifest_id=f"manifest_{session_id}",
            kernel_version=kernel_version,
            timestamp_created=datetime.utcnow().isoformat() + "Z",
            stores=[
                StoreDeclaration("context_store",  "local_ndjson", f"{base_path}/stores/context.ndjson",    "context"),
                StoreDeclaration("receipt_ledger",  "hash_chain",   f"{base_path}/stores/ledger.ndjson",     "ledger"),
                StoreDeclaration("transcript_store","local_ndjson", f"{base_path}/stores/transcript.ndjson", "transcript"),
                StoreDeclaration("shadow_store",    "local_ndjson", f"{base_path}/stores/shadow.ndjson",     "shadow"),
            ],
            capability_surface=CapabilitySurface(
                tools_frozen=True,
                include_mcp=False,
                skill_count=7,
                agent_count=3,
                known_skills=[
                    "skill.claim_extraction",
                    "skill.knowledge_compilation",
                    "skill.audit",
                    "skill.artifact_generation",
                    "skill.source_ingest",
                    "skill.temple_session",
                    "skill.onboarding",
                ],
                known_agents=[
                    "agent.summarizer",
                    "agent.formatter",
                    "agent.classifier",
                ],
            ),
        )

        manifest.freeze()
        return manifest

    @staticmethod
    def validate_receipt_manifest_ref(receipt_manifest_ref: str, manifest: RuntimeManifest) -> bool:
        """Verify a dispatch receipt references the correct manifest."""
        return receipt_manifest_ref == manifest.manifest_hash
