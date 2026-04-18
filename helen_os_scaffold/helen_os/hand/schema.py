"""
HELEN Hand Schema v1.0
======================
Manifest contract for autonomous agent capability packages.

Based on OpenFang's Hand.toml but adapted for HELEN's non-sovereign authority model:
- LLM proposes via Hand
- Reducer validates against gates (G0-G3)
- Ledger commits only after gates pass

Schema is immutable (manifest_hash pinned at registration).
Prompts are immutable (system_prompt_sha256 pinned at registration).
Tools are allowlisted per Hand.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, asdict, field
from pathlib import Path


def sha256_file(path: Path) -> str:
    """Compute SHA256 of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    """Compute SHA256 of text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical_json(obj: Any) -> str:
    """Serialize to canonical JSON for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


# Enums
SettingType = Literal["select", "toggle", "text", "number", "slider"]
MetricFormat = Literal["number", "text", "percent", "json"]
ToolEffect = Literal["observe", "propose", "execute"]  # Reducer classification
RequirementType = Literal["binary", "file", "env", "service"]


@dataclass
class SettingOption:
    """Option for a select/slider setting."""
    value: str
    label: str
    description: Optional[str] = None


@dataclass
class Setting:
    """Configurable setting for a Hand."""
    key: str
    label: str
    description: str
    setting_type: SettingType
    default: Any
    options: List[SettingOption] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "type": self.setting_type,
            "default": self.default,
            "options": [asdict(o) for o in self.options],
        }


@dataclass
class Requirement:
    """System requirement (binary, lib, env var, service)."""
    key: str
    label: str
    requirement_type: RequirementType
    check_value: str
    description: str
    install_instructions: Optional[Dict[str, str]] = None  # macos, windows, linux_apt, etc.
    estimated_time: Optional[str] = None


@dataclass
class AgentConfig:
    """LLM execution config for the Hand."""
    name: str
    description: str
    module: str = "builtin:chat"  # Stringly-typed for now
    provider: str = "default"  # ollama, openai, etc.
    model: str = "default"
    max_tokens: int = 8192
    temperature: float = 0.2
    max_iterations: int = 40
    system_prompt_ref: Optional[str] = None  # File path to prompt
    system_prompt_sha256: Optional[str] = None  # SHA256 of prompt file

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "module": self.module,
            "provider": self.provider,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "max_iterations": self.max_iterations,
            "system_prompt_ref": self.system_prompt_ref,
            "system_prompt_sha256": self.system_prompt_sha256,
        }


@dataclass
class DashboardMetric:
    """Dashboard metric binding."""
    label: str
    memory_key: str
    format: MetricFormat = "number"
    description: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "label": self.label,
            "memory_key": self.memory_key,
            "format": self.format,
            "description": self.description,
        }


@dataclass
class DashboardConfig:
    """Dashboard configuration."""
    metrics: List[DashboardMetric] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "metrics": [m.to_dict() for m in self.metrics],
        }


@dataclass
class Guardrail:
    """Approval gate for sensitive actions."""
    action: str  # e.g., "browser_purchase", "shell_execute", "email_send"
    requires_approval: bool = True
    max_spend: Optional[float] = None  # For financial actions
    forbidden_domains: List[str] = field(default_factory=list)
    allowed_domains: List[str] = field(default_factory=list)  # Allowlist if set, takes precedence
    timeout_seconds: int = 300
    description: str = ""

    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "requires_approval": self.requires_approval,
            "max_spend": self.max_spend,
            "forbidden_domains": self.forbidden_domains,
            "allowed_domains": self.allowed_domains,
            "timeout_seconds": self.timeout_seconds,
            "description": self.description,
        }


@dataclass
class HELENHand:
    """
    HELEN Hand manifest.

    Represents a capability package: tools, settings, execution config, guardrails.
    Immutable after registration (manifest_hash + prompt_sha256 pinned in ledger).
    """

    # Identity
    id: str  # unique, stable (e.g., "helen-researcher", "helen-browser")
    name: str
    description: str
    category: str  # "productivity", "data", "ops", "governance", etc.
    icon: str  # emoji or icon string

    # Execution
    tools: List[str]  # Allowlist of tool names (e.g., ["web_search", "file_read"])

    # Configuration
    settings: List[Setting] = field(default_factory=list)
    requirements: List[Requirement] = field(default_factory=list)

    # Agent
    agent: Optional[AgentConfig] = None

    # Dashboard
    dashboard: Optional[DashboardConfig] = None

    # Safety
    guardrails: List[Guardrail] = field(default_factory=list)

    # Metadata
    version: str = "1.0"
    created_at: Optional[str] = None
    manifest_hash: Optional[str] = None  # Computed at load time; pinned at registration

    def to_dict(self, exclude_hash: bool = False) -> Dict:
        """Convert to dict (for JSON serialization or hashing)."""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "tools": self.tools,
            "settings": [s.to_dict() for s in self.settings],
            "requirements": [r.__dict__ for r in self.requirements],
            "agent": self.agent.to_dict() if self.agent else None,
            "dashboard": self.dashboard.to_dict() if self.dashboard else None,
            "guardrails": [g.to_dict() for g in self.guardrails],
            "version": self.version,
            "created_at": self.created_at,
        }
        if not exclude_hash:
            data["manifest_hash"] = self.manifest_hash
        return data

    def compute_manifest_hash(self) -> str:
        """
        Compute manifest hash (excludes manifest_hash field itself).
        Used for immutability validation.
        """
        data = self.to_dict(exclude_hash=True)
        canon = canonical_json(data)
        return hashlib.sha256(canon.encode('utf-8')).hexdigest()

    def verify_manifest_hash(self) -> bool:
        """Verify that stored hash matches computed hash."""
        if not self.manifest_hash:
            return False
        return self.manifest_hash == self.compute_manifest_hash()

    def verify_prompt_hash(self, prompt_file_path: Path) -> bool:
        """Verify that prompt file hash matches declared sha256."""
        if not self.agent or not self.agent.system_prompt_sha256:
            return True  # No prompt declared

        if not prompt_file_path.exists():
            return False

        actual_hash = sha256_file(prompt_file_path)
        return actual_hash == self.agent.system_prompt_sha256

    @classmethod
    def load_from_dict(cls, data: Dict) -> "HELENHand":
        """Load Hand from dict (e.g., parsed TOML or JSON)."""
        # Parse settings
        settings = [
            Setting(
                key=s["key"],
                label=s["label"],
                description=s["description"],
                setting_type=s["type"],
                default=s["default"],
                options=[SettingOption(**o) for o in s.get("options", [])],
            )
            for s in data.get("settings", [])
        ]

        # Parse requirements
        requirements = [
            Requirement(**r)
            for r in data.get("requirements", [])
        ]

        # Parse agent
        agent_data = data.get("agent")
        agent = None
        if agent_data:
            agent = AgentConfig(**agent_data)

        # Parse dashboard
        dashboard_data = data.get("dashboard")
        dashboard = None
        if dashboard_data:
            metrics = [
                DashboardMetric(**m)
                for m in dashboard_data.get("metrics", [])
            ]
            dashboard = DashboardConfig(metrics=metrics)

        # Parse guardrails
        guardrails = [
            Guardrail(**g)
            for g in data.get("guardrails", [])
        ]

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data["category"],
            icon=data["icon"],
            tools=data["tools"],
            settings=settings,
            requirements=requirements,
            agent=agent,
            dashboard=dashboard,
            guardrails=guardrails,
            version=data.get("version", "1.0"),
            created_at=data.get("created_at"),
            manifest_hash=data.get("manifest_hash"),
        )

    @classmethod
    def load_from_toml_file(cls, path: Path) -> "HELENHand":
        """Load Hand from TOML file."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # Fallback

        data = tomllib.loads(path.read_text())
        hand = cls.load_from_dict(data)
        hand.manifest_hash = hand.compute_manifest_hash()
        return hand

    @classmethod
    def load_from_json_file(cls, path: Path) -> "HELENHand":
        """Load Hand from JSON file."""
        data = json.loads(path.read_text())
        hand = cls.load_from_dict(data)
        hand.manifest_hash = hand.compute_manifest_hash()
        return hand


if __name__ == "__main__":
    # Test: Create a minimal Hand
    print("Testing HELENHand schema...\n")

    hand = HELENHand(
        id="helen-researcher",
        name="HELEN Researcher",
        description="Autonomous research hand",
        category="productivity",
        icon="🧪",
        tools=["web_search", "web_fetch", "file_read", "memory_recall"],
        agent=AgentConfig(
            name="researcher-hand",
            description="Produces research reports",
            system_prompt_ref="prompts/researcher.md",
            system_prompt_sha256="abc123",
        ),
        guardrails=[
            Guardrail(
                action="file_write",
                requires_approval=True,
                description="Writes to disk must be approved",
            ),
        ],
    )

    # Compute manifest hash
    hand.manifest_hash = hand.compute_manifest_hash()
    print(f"Hand ID: {hand.id}")
    print(f"Manifest Hash: {hand.manifest_hash}")
    print(f"Verified: {hand.verify_manifest_hash()}")
    print(f"\nJSON:")
    print(json.dumps(hand.to_dict(), indent=2)[:500])
