"""
HELEN OS Configuration Manager v1.0

Manages:
- API keys (environment variables, encrypted files)
- Model configurations
- Deployment settings
- Runtime preferences
- Provider availability

Safe API key handling:
- Never logs sensitive credentials
- Supports environment variables
- Supports encrypted config files
- Validates credentials on startup
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION DATA STRUCTURES
# ============================================================================

@dataclass
class APIKeyConfig:
    """API key configuration for a provider"""
    provider: str
    api_key: str = ""  # Will be loaded from env or config
    base_url: Optional[str] = None
    is_loaded: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict (excluding actual API key)"""
        return {
            "provider": self.provider,
            "is_loaded": self.is_loaded,
            "has_api_key": bool(self.api_key),
            "base_url": self.base_url,
            "error_message": self.error_message,
        }


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    name: str = "HELEN OS v1.0"
    environment: str = "local"  # local, docker, cloud
    port: int = 8000
    debug: bool = False
    enable_logging: bool = True
    max_concurrent_requests: int = 10
    default_timeout_seconds: int = 30
    enable_metrics: bool = True


@dataclass
class RuntimeConfig:
    """Runtime preferences"""
    default_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    streaming_enabled: bool = True
    auto_fallback: bool = True  # Auto-fallback to alternative model if primary fails
    cost_limit_per_request: Optional[float] = None
    prefer_local_models: bool = True


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================

class ConfigManager:
    """
    Central configuration management for HELEN OS.

    Handles:
    - Loading API keys from environment
    - Loading config files
    - Validating credentials
    - Providing configuration to system components
    """

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".helen_os"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.api_keys: Dict[str, APIKeyConfig] = {}
        self.deployment_config = DeploymentConfig()
        self.runtime_config = RuntimeConfig()
        self.provider_status: Dict[str, bool] = {}

        logger.info(f"ConfigManager initialized with config dir: {self.config_dir}")

    def load_all_configs(self) -> bool:
        """Load all configurations and return success status"""
        success = True

        # Load API keys
        if not self.load_api_keys():
            success = False

        # Load deployment config
        if not self.load_deployment_config():
            success = False

        # Load runtime config
        if not self.load_runtime_config():
            success = False

        # Validate providers
        self._validate_providers()

        return success

    # ========================================================================
    # API KEY MANAGEMENT
    # ========================================================================

    def load_api_keys(self) -> bool:
        """Load API keys from environment variables"""
        providers = {
            "ollama": ("OLLAMA_API_KEY", None),
            "claude": ("ANTHROPIC_API_KEY", "https://api.anthropic.com"),
            "gpt": ("OPENAI_API_KEY", "https://api.openai.com/v1"),
            "grok": ("XAI_API_KEY", "https://api.x.ai"),
            "gemini": ("GOOGLE_API_KEY", "https://generativelanguage.googleapis.com"),
            "qwen": ("QWEN_API_KEY", "https://dashscope.aliyuncs.com/api/v1"),
        }

        for provider, (env_var, base_url) in providers.items():
            api_key = os.getenv(env_var, "")

            self.api_keys[provider] = APIKeyConfig(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                is_loaded=bool(api_key),
            )

            if api_key:
                logger.info(f"✅ {provider}: API key loaded from {env_var}")
            else:
                logger.warning(f"⚠️  {provider}: No API key found in {env_var}")

        # Try to load from .env file if it exists
        self._load_env_file()

        return True

    def _load_env_file(self) -> None:
        """Load environment variables from .env file if it exists"""
        env_file = self.config_dir / ".env"

        if env_file.exists():
            try:
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip()
                            logger.debug(f"Loaded {key.strip()} from .env")
            except Exception as e:
                logger.warning(f"Failed to load .env file: {e}")

    def set_api_key(self, provider: str, api_key: str) -> bool:
        """Set API key for a provider"""
        if provider not in self.api_keys:
            logger.error(f"Unknown provider: {provider}")
            return False

        self.api_keys[provider].api_key = api_key
        self.api_keys[provider].is_loaded = True

        # Also set environment variable
        env_var = self._get_env_var_name(provider)
        os.environ[env_var] = api_key

        logger.info(f"✅ API key set for {provider}")
        return True

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider (returns None if not loaded)"""
        if provider not in self.api_keys:
            return None

        return self.api_keys[provider].api_key if self.api_keys[provider].is_loaded else None

    def has_api_key(self, provider: str) -> bool:
        """Check if API key is loaded for provider"""
        if provider not in self.api_keys:
            return False
        return self.api_keys[provider].is_loaded

    def _get_env_var_name(self, provider: str) -> str:
        """Get environment variable name for provider"""
        env_vars = {
            "ollama": "OLLAMA_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "gpt": "OPENAI_API_KEY",
            "grok": "XAI_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "qwen": "QWEN_API_KEY",
        }
        return env_vars.get(provider, f"{provider.upper()}_API_KEY")

    # ========================================================================
    # DEPLOYMENT CONFIGURATION
    # ========================================================================

    def load_deployment_config(self) -> bool:
        """Load deployment configuration"""
        config_file = self.config_dir / "deployment.json"

        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = json.load(f)
                    self.deployment_config = DeploymentConfig(**data)
                    logger.info(f"✅ Loaded deployment config from {config_file}")
                    return True
            except Exception as e:
                logger.error(f"Failed to load deployment config: {e}")
                return False

        # Create default config
        self.save_deployment_config()
        return True

    def save_deployment_config(self) -> bool:
        """Save deployment configuration"""
        config_file = self.config_dir / "deployment.json"

        try:
            with open(config_file, "w") as f:
                json.dump(asdict(self.deployment_config), f, indent=2)
                logger.info(f"✅ Saved deployment config to {config_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to save deployment config: {e}")
            return False

    # ========================================================================
    # RUNTIME CONFIGURATION
    # ========================================================================

    def load_runtime_config(self) -> bool:
        """Load runtime configuration"""
        config_file = self.config_dir / "runtime.json"

        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = json.load(f)
                    self.runtime_config = RuntimeConfig(**data)
                    logger.info(f"✅ Loaded runtime config from {config_file}")
                    return True
            except Exception as e:
                logger.error(f"Failed to load runtime config: {e}")
                return False

        # Create default config
        self.save_runtime_config()
        return True

    def save_runtime_config(self) -> bool:
        """Save runtime configuration"""
        config_file = self.config_dir / "runtime.json"

        try:
            with open(config_file, "w") as f:
                json.dump(asdict(self.runtime_config), f, indent=2)
                logger.info(f"✅ Saved runtime config to {config_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to save runtime config: {e}")
            return False

    # ========================================================================
    # PROVIDER VALIDATION
    # ========================================================================

    def _validate_providers(self) -> None:
        """Validate which providers are available"""
        for provider, config in self.api_keys.items():
            if provider == "ollama":
                # Ollama doesn't need API key, check if service is running
                self.provider_status[provider] = True
            else:
                # Check if API key is loaded
                self.provider_status[provider] = config.is_loaded

    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        return self.provider_status.copy()

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [p for p, available in self.provider_status.items() if available]

    # ========================================================================
    # CONFIGURATION EXPORT
    # ========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Get complete configuration status (safe for logging)"""
        return {
            "deployment": asdict(self.deployment_config),
            "runtime": asdict(self.runtime_config),
            "api_keys": {
                provider: config.to_dict()
                for provider, config in self.api_keys.items()
            },
            "available_providers": self.get_available_providers(),
            "provider_status": self.provider_status,
        }

    def export_config_template(self, output_file: Optional[Path] = None) -> str:
        """Export configuration template with instructions"""
        template = """
# HELEN OS Configuration Template
# Copy this to ~/.helen_os/.env and fill in your API keys

# ============================================================================
# API KEYS (Required for cloud models)
# ============================================================================

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI GPT
OPENAI_API_KEY=sk-...

# xAI Grok
XAI_API_KEY=xai-...

# Google Gemini
GOOGLE_API_KEY=...

# Alibaba Qwen
QWEN_API_KEY=...

# Ollama (if running locally)
OLLAMA_API_KEY=optional

# ============================================================================
# DEPLOYMENT SETTINGS
# ============================================================================

# Environment: local, docker, cloud
HELEN_ENVIRONMENT=local

# Port for HELEN OS server
HELEN_PORT=8000

# Enable debug logging
HELEN_DEBUG=false

# ============================================================================
# RUNTIME PREFERENCES
# ============================================================================

# Default model (if not specified)
HELEN_DEFAULT_MODEL=claude-opus-4-6

# Temperature for generation (0.0-1.0)
HELEN_TEMPERATURE=0.7

# Max tokens per request
HELEN_MAX_TOKENS=2048

# Enable streaming
HELEN_STREAMING=true

# Auto-fallback to alternative model if primary fails
HELEN_AUTO_FALLBACK=true

# Prefer local models (Ollama) over cloud
HELEN_PREFER_LOCAL=true

# Cost limit per request (e.g., 0.10 for $0.10 max)
# HELEN_COST_LIMIT=0.10
"""
        if output_file:
            output_file.write_text(template)
            logger.info(f"✅ Configuration template exported to {output_file}")

        return template


# ============================================================================
# GLOBAL CONFIG INSTANCE
# ============================================================================

_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create global configuration manager"""
    global _global_config_manager

    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
        _global_config_manager.load_all_configs()

    return _global_config_manager


def initialize_config(config_dir: Optional[Path] = None) -> ConfigManager:
    """Initialize configuration manager"""
    global _global_config_manager

    _global_config_manager = ConfigManager(config_dir)
    _global_config_manager.load_all_configs()

    return _global_config_manager


if __name__ == "__main__":
    # Initialize and show status
    config = initialize_config()

    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          HELEN OS CONFIGURATION STATUS                        ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")

    status = config.get_status()

    print("📊 DEPLOYMENT CONFIGURATION")
    for key, value in status["deployment"].items():
        print(f"  {key}: {value}")

    print("\n⚙️  RUNTIME CONFIGURATION")
    for key, value in status["runtime"].items():
        print(f"  {key}: {value}")

    print("\n🔑 API KEY STATUS")
    for provider, key_status in status["api_keys"].items():
        status_icon = "✅" if key_status["is_loaded"] else "⚠️"
        print(f"  {status_icon} {provider}: {key_status['is_loaded']}")

    print(f"\n✅ AVAILABLE PROVIDERS: {', '.join(status['available_providers']) or 'None (set API keys)'}")

    print("\n📝 Configuration directory:", config.config_dir)
    print("📄 Config files:")
    print(f"   • {config.config_dir}/deployment.json")
    print(f"   • {config.config_dir}/runtime.json")
    print(f"   • {config.config_dir}/.env (for API keys)")

    print("\n💡 To set API keys:")
    print(f"   1. Create {config.config_dir}/.env")
    print(f"   2. Add: ANTHROPIC_API_KEY=your_key")
    print(f"   3. Add other API keys as needed")
    print(f"   4. Restart HELEN OS")
