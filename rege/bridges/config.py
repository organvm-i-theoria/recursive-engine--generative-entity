"""
RE:GE Bridge Configuration - Configuration management for external bridges.

Provides:
- Bridge configuration loading/saving
- Environment variable overrides
- Configuration validation
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BridgeConfigEntry:
    """Configuration for a single bridge."""

    bridge_type: str
    name: str
    enabled: bool = True
    auto_connect: bool = False
    config: Dict[str, Any] = field(default_factory=dict)


class BridgeConfig:
    """
    Configuration manager for external bridges.

    Handles:
    - Loading/saving configuration from JSON files
    - Environment variable overrides
    - Per-bridge configuration sections
    """

    # Default configuration file path
    DEFAULT_CONFIG_PATH = Path.home() / ".rege" / "bridge_config.json"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to configuration file (uses default if not specified)
        """
        self._config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._bridges: Dict[str, BridgeConfigEntry] = {}
        self._loaded = False

    def load(self) -> bool:
        """
        Load configuration from file.

        Returns:
            True if configuration was loaded successfully
        """
        if not self._config_path.exists():
            # Create default configuration
            self._create_default_config()
            return True

        try:
            with open(self._config_path, "r") as f:
                self._config = json.load(f)
            self._parse_bridges()
            self._apply_env_overrides()
            self._loaded = True
            return True
        except (json.JSONDecodeError, OSError) as e:
            self._config = {}
            self._bridges = {}
            return False

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if configuration was saved successfully
        """
        try:
            # Ensure directory exists
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            # Update bridges in config
            self._config["bridges"] = {
                name: {
                    "type": entry.bridge_type,
                    "enabled": entry.enabled,
                    "auto_connect": entry.auto_connect,
                    "config": entry.config,
                }
                for name, entry in self._bridges.items()
            }

            self._config["last_saved"] = datetime.now().isoformat()

            with open(self._config_path, "w") as f:
                json.dump(self._config, f, indent=2)

            return True
        except OSError:
            return False

    def _create_default_config(self) -> None:
        """Create default configuration."""
        self._config = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "bridges": {
                "obsidian": {
                    "type": "obsidian",
                    "enabled": False,
                    "auto_connect": False,
                    "config": {
                        "vault_path": "",
                    },
                },
                "git": {
                    "type": "git",
                    "enabled": False,
                    "auto_connect": False,
                    "config": {
                        "repo_path": "",
                        "install_hooks": False,
                    },
                },
                "maxmsp": {
                    "type": "maxmsp",
                    "enabled": False,
                    "auto_connect": False,
                    "config": {
                        "host": "localhost",
                        "port": 7400,
                    },
                },
            },
        }
        self._parse_bridges()

    def _parse_bridges(self) -> None:
        """Parse bridge configurations from loaded config."""
        self._bridges = {}

        bridges_section = self._config.get("bridges", {})
        for name, bridge_config in bridges_section.items():
            self._bridges[name] = BridgeConfigEntry(
                bridge_type=bridge_config.get("type", name),
                name=name,
                enabled=bridge_config.get("enabled", True),
                auto_connect=bridge_config.get("auto_connect", False),
                config=bridge_config.get("config", {}),
            )

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Environment variable patterns:
        # REGE_BRIDGE_<NAME>_<KEY>=value
        # Example: REGE_BRIDGE_OBSIDIAN_VAULT_PATH=/path/to/vault

        for key, value in os.environ.items():
            if key.startswith("REGE_BRIDGE_"):
                parts = key.replace("REGE_BRIDGE_", "").split("_", 1)
                if len(parts) == 2:
                    bridge_name = parts[0].lower()
                    config_key = parts[1].lower()

                    if bridge_name in self._bridges:
                        self._bridges[bridge_name].config[config_key] = value

    def get_bridge_config(self, name: str) -> Optional[BridgeConfigEntry]:
        """
        Get configuration for a specific bridge.

        Args:
            name: Bridge name

        Returns:
            Bridge configuration entry, or None if not found
        """
        return self._bridges.get(name.lower())

    def set_bridge_config(
        self,
        name: str,
        bridge_type: str,
        enabled: bool = True,
        auto_connect: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Set configuration for a bridge.

        Args:
            name: Bridge name
            bridge_type: Bridge type
            enabled: Whether bridge is enabled
            auto_connect: Whether to auto-connect on startup
            config: Bridge-specific configuration
        """
        self._bridges[name.lower()] = BridgeConfigEntry(
            bridge_type=bridge_type,
            name=name,
            enabled=enabled,
            auto_connect=auto_connect,
            config=config or {},
        )

    def get_enabled_bridges(self) -> List[BridgeConfigEntry]:
        """
        Get list of enabled bridges.

        Returns:
            List of enabled bridge configurations
        """
        return [b for b in self._bridges.values() if b.enabled]

    def get_auto_connect_bridges(self) -> List[BridgeConfigEntry]:
        """
        Get list of bridges that should auto-connect.

        Returns:
            List of auto-connect bridge configurations
        """
        return [b for b in self._bridges.values() if b.enabled and b.auto_connect]

    def list_bridges(self) -> List[str]:
        """
        List all configured bridge names.

        Returns:
            List of bridge names
        """
        return list(self._bridges.keys())

    def remove_bridge(self, name: str) -> bool:
        """
        Remove a bridge configuration.

        Args:
            name: Bridge name

        Returns:
            True if bridge was removed
        """
        if name.lower() in self._bridges:
            del self._bridges[name.lower()]
            return True
        return False

    def validate_config(self, name: str) -> Dict[str, Any]:
        """
        Validate configuration for a bridge.

        Args:
            name: Bridge name

        Returns:
            Validation result with 'valid' bool and 'errors' list
        """
        errors = []

        bridge = self._bridges.get(name.lower())
        if bridge is None:
            return {"valid": False, "errors": ["Bridge not found"]}

        # Type-specific validation
        if bridge.bridge_type == "obsidian":
            vault_path = bridge.config.get("vault_path", "")
            if not vault_path:
                errors.append("vault_path is required")
            elif vault_path and not Path(vault_path).exists():
                errors.append(f"vault_path does not exist: {vault_path}")

        elif bridge.bridge_type == "git":
            repo_path = bridge.config.get("repo_path", "")
            if repo_path and not Path(repo_path).exists():
                errors.append(f"repo_path does not exist: {repo_path}")

        elif bridge.bridge_type == "maxmsp":
            port = bridge.config.get("port", 7400)
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append("port must be a valid port number (1-65535)")

        return {"valid": len(errors) == 0, "errors": errors}

    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return {
            "version": self._config.get("version", "1.0"),
            "bridges": {
                name: {
                    "type": entry.bridge_type,
                    "enabled": entry.enabled,
                    "auto_connect": entry.auto_connect,
                    "config": entry.config,
                }
                for name, entry in self._bridges.items()
            },
        }


# Global configuration instance
_bridge_config: Optional[BridgeConfig] = None


def get_bridge_config() -> BridgeConfig:
    """
    Get or create the global bridge configuration.

    Returns:
        Global BridgeConfig instance
    """
    global _bridge_config
    if _bridge_config is None:
        _bridge_config = BridgeConfig()
        _bridge_config.load()
    return _bridge_config
