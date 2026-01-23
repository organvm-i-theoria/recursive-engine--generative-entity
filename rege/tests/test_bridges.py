"""
Tests for the external bridges infrastructure.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from rege.bridges.base import (
    ExternalBridge,
    BridgeStatus,
    BridgeOperation,
    MockBridge,
)
from rege.bridges.registry import BridgeRegistry, get_bridge_registry
from rege.bridges.config import BridgeConfig, BridgeConfigEntry


class TestBridgeStatus:
    """Tests for BridgeStatus enum."""

    def test_status_values(self):
        """Test all status values exist."""
        assert BridgeStatus.DISCONNECTED.value == "disconnected"
        assert BridgeStatus.CONNECTING.value == "connecting"
        assert BridgeStatus.CONNECTED.value == "connected"
        assert BridgeStatus.ERROR.value == "error"
        assert BridgeStatus.MAINTENANCE.value == "maintenance"


class TestMockBridge:
    """Tests for MockBridge class."""

    def test_init_default(self):
        """Test default initialization."""
        bridge = MockBridge()
        assert bridge.name == "MockBridge"
        assert bridge.current_status == BridgeStatus.DISCONNECTED
        assert not bridge.is_connected

    def test_connect_success(self):
        """Test successful connection."""
        bridge = MockBridge()
        result = bridge.connect()
        assert result is True
        assert bridge.is_connected
        assert bridge.current_status == BridgeStatus.CONNECTED

    def test_connect_failure(self):
        """Test connection failure."""
        bridge = MockBridge(should_fail=True)
        result = bridge.connect()
        assert result is False
        assert not bridge.is_connected
        assert bridge.current_status == BridgeStatus.ERROR

    def test_disconnect_success(self):
        """Test successful disconnection."""
        bridge = MockBridge()
        bridge.connect()
        result = bridge.disconnect()
        assert result is True
        assert not bridge.is_connected

    def test_send_success(self):
        """Test successful send."""
        bridge = MockBridge()
        bridge.connect()
        result = bridge.send({"test": "data"})
        assert result["status"] == "sent"
        assert bridge.get_sent_data() == [{"test": "data"}]

    def test_send_not_connected(self):
        """Test send when not connected."""
        bridge = MockBridge()
        result = bridge.send({"test": "data"})
        assert result["status"] == "failed"
        assert "Not connected" in result["error"]

    def test_receive_success(self):
        """Test successful receive."""
        bridge = MockBridge()
        bridge.connect()
        bridge.queue_receive_data({"received": "data"})
        result = bridge.receive()
        assert result == {"received": "data"}

    def test_receive_empty(self):
        """Test receive with no data."""
        bridge = MockBridge()
        bridge.connect()
        result = bridge.receive()
        assert result is None

    def test_status(self):
        """Test status method."""
        bridge = MockBridge(name="TestBridge")
        status = bridge.status()
        assert status["name"] == "TestBridge"
        assert status["status"] == "disconnected"
        assert status["is_connected"] is False

    def test_operations_log(self):
        """Test operations are logged."""
        bridge = MockBridge()
        bridge.connect()
        bridge.disconnect()
        log = bridge.get_operations_log()
        assert len(log) >= 2
        assert any(op["operation"] == "connect" for op in log)
        assert any(op["operation"] == "disconnect" for op in log)


class TestBridgeRegistry:
    """Tests for BridgeRegistry class."""

    def test_init_empty(self):
        """Test empty registry initialization."""
        registry = BridgeRegistry()
        assert registry.list_types() == []
        assert registry.list_active() == []

    def test_register_type(self):
        """Test type registration."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        assert registry.has_type("mock")
        assert "mock" in registry.list_types()

    def test_create_bridge(self):
        """Test bridge creation."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        bridge = registry.create_bridge("mock", instance_name="test_bridge")
        assert bridge is not None
        assert bridge.name == "test_bridge"
        assert "test_bridge" in registry.list_active()

    def test_create_bridge_unknown_type(self):
        """Test creating bridge with unknown type."""
        registry = BridgeRegistry()
        bridge = registry.create_bridge("unknown")
        assert bridge is None

    def test_get_bridge(self):
        """Test getting bridge by name."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        registry.create_bridge("mock", instance_name="my_bridge")
        bridge = registry.get_bridge("my_bridge")
        assert bridge is not None
        assert bridge.name == "my_bridge"

    def test_remove_bridge(self):
        """Test removing bridge."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        registry.create_bridge("mock", instance_name="to_remove")
        result = registry.remove_bridge("to_remove")
        assert result is True
        assert "to_remove" not in registry.list_active()

    def test_remove_bridge_not_found(self):
        """Test removing non-existent bridge."""
        registry = BridgeRegistry()
        result = registry.remove_bridge("nonexistent")
        assert result is False

    def test_connect_all(self):
        """Test connecting all bridges."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        registry.create_bridge("mock", instance_name="bridge1")
        registry.create_bridge("mock", instance_name="bridge2")
        results = registry.connect_all()
        assert results["bridge1"] is True
        assert results["bridge2"] is True

    def test_disconnect_all(self):
        """Test disconnecting all bridges."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        b1 = registry.create_bridge("mock", instance_name="bridge1")
        b2 = registry.create_bridge("mock", instance_name="bridge2")
        b1.connect()
        b2.connect()
        results = registry.disconnect_all()
        assert results["bridge1"] is True
        assert results["bridge2"] is True

    def test_get_connected_count(self):
        """Test counting connected bridges."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        b1 = registry.create_bridge("mock", instance_name="bridge1")
        b2 = registry.create_bridge("mock", instance_name="bridge2")
        assert registry.get_connected_count() == 0
        b1.connect()
        assert registry.get_connected_count() == 1
        b2.connect()
        assert registry.get_connected_count() == 2

    def test_get_all_status(self):
        """Test getting all bridge statuses."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        registry.create_bridge("mock", instance_name="bridge1")
        statuses = registry.get_all_status()
        assert "bridge1" in statuses
        assert statuses["bridge1"]["status"] == "disconnected"

    def test_clear(self):
        """Test clearing all bridges."""
        registry = BridgeRegistry()
        registry.register_type("mock", MockBridge)
        registry.create_bridge("mock", instance_name="bridge1")
        registry.clear()
        assert registry.list_active() == []


class TestBridgeConfig:
    """Tests for BridgeConfig class."""

    def test_init_default(self):
        """Test default initialization."""
        config = BridgeConfig()
        assert config._config_path is not None

    def test_load_nonexistent_creates_default(self, tmp_path):
        """Test loading creates default config if missing."""
        config_path = tmp_path / "config.json"
        config = BridgeConfig(config_path)
        result = config.load()
        assert result is True
        assert len(config.list_bridges()) > 0

    def test_save_and_load(self, tmp_path):
        """Test saving and loading configuration."""
        config_path = tmp_path / "config.json"
        config = BridgeConfig(config_path)
        config.set_bridge_config(
            name="test",
            bridge_type="mock",
            enabled=True,
            auto_connect=True,
            config={"key": "value"},
        )
        config.save()

        # Load in new instance
        config2 = BridgeConfig(config_path)
        config2.load()
        bridge = config2.get_bridge_config("test")
        assert bridge is not None
        assert bridge.bridge_type == "mock"
        assert bridge.enabled is True
        assert bridge.auto_connect is True
        assert bridge.config["key"] == "value"

    def test_get_enabled_bridges(self, tmp_path):
        """Test getting enabled bridges."""
        config = BridgeConfig(tmp_path / "config.json")
        config.set_bridge_config("enabled", "mock", enabled=True)
        config.set_bridge_config("disabled", "mock", enabled=False)
        enabled = config.get_enabled_bridges()
        assert len([b for b in enabled if b.name == "enabled"]) == 1
        assert len([b for b in enabled if b.name == "disabled"]) == 0

    def test_get_auto_connect_bridges(self, tmp_path):
        """Test getting auto-connect bridges."""
        config = BridgeConfig(tmp_path / "config.json")
        config.set_bridge_config("auto", "mock", enabled=True, auto_connect=True)
        config.set_bridge_config("manual", "mock", enabled=True, auto_connect=False)
        auto = config.get_auto_connect_bridges()
        assert len([b for b in auto if b.name == "auto"]) == 1
        assert len([b for b in auto if b.name == "manual"]) == 0

    def test_remove_bridge(self, tmp_path):
        """Test removing bridge configuration."""
        config = BridgeConfig(tmp_path / "config.json")
        config.set_bridge_config("to_remove", "mock")
        result = config.remove_bridge("to_remove")
        assert result is True
        assert config.get_bridge_config("to_remove") is None

    def test_validate_config_valid(self, tmp_path):
        """Test validation of valid config."""
        config = BridgeConfig(tmp_path / "config.json")
        config.set_bridge_config("test", "mock")
        result = config.validate_config("test")
        assert result["valid"] is True

    def test_validate_config_obsidian_missing_path(self, tmp_path):
        """Test Obsidian validation with missing vault path."""
        config = BridgeConfig(tmp_path / "config.json")
        config.set_bridge_config("obs", "obsidian", config={})
        result = config.validate_config("obs")
        assert result["valid"] is False
        assert "vault_path" in result["errors"][0]

    def test_validate_config_maxmsp_invalid_port(self, tmp_path):
        """Test Max/MSP validation with invalid port."""
        config = BridgeConfig(tmp_path / "config.json")
        config.set_bridge_config("max", "maxmsp", config={"port": -1})
        result = config.validate_config("max")
        assert result["valid"] is False

    def test_to_dict(self, tmp_path):
        """Test exporting as dictionary."""
        config = BridgeConfig(tmp_path / "config.json")
        config.set_bridge_config("test", "mock")
        data = config.to_dict()
        assert "version" in data
        assert "bridges" in data
        assert "test" in data["bridges"]


class TestObsidianBridge:
    """Tests for Obsidian bridge."""

    def test_connect_no_path(self):
        """Test connect with no vault path."""
        from rege.bridges.obsidian import ObsidianBridge

        bridge = ObsidianBridge()
        result = bridge.connect()
        assert result is False
        assert "vault_path" in bridge.last_error.lower()

    def test_connect_path_not_exists(self, tmp_path):
        """Test connect with non-existent path."""
        from rege.bridges.obsidian import ObsidianBridge

        bridge = ObsidianBridge(config={"vault_path": str(tmp_path / "nonexistent")})
        result = bridge.connect()
        assert result is False

    def test_connect_not_obsidian_vault(self, tmp_path):
        """Test connect with directory that's not an Obsidian vault."""
        from rege.bridges.obsidian import ObsidianBridge

        vault_path = tmp_path / "not_vault"
        vault_path.mkdir()
        bridge = ObsidianBridge(config={"vault_path": str(vault_path)})
        result = bridge.connect()
        assert result is False
        assert "obsidian" in bridge.last_error.lower()

    def test_connect_success(self, tmp_path):
        """Test successful connection to vault."""
        from rege.bridges.obsidian import ObsidianBridge

        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()

        bridge = ObsidianBridge(config={"vault_path": str(vault_path)})
        result = bridge.connect()
        assert result is True
        assert bridge.is_connected

        # Check folders were created
        assert (vault_path / "FRAGMENTS").exists()
        assert (vault_path / "CANON").exists()

    def test_export_fragment(self, tmp_path):
        """Test exporting a fragment."""
        from rege.bridges.obsidian import ObsidianBridge

        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()

        bridge = ObsidianBridge(config={"vault_path": str(vault_path)})
        bridge.connect()

        fragment = {
            "id": "FRAG_001",
            "name": "Test Fragment",
            "charge": 75,
            "tags": ["CANON+"],
            "status": "active",
        }
        result = bridge.send({"fragment": fragment})
        assert result["status"] == "exported"
        assert (vault_path / "FRAGMENTS").glob("*.md")

    def test_fragment_to_markdown(self, tmp_path):
        """Test markdown conversion."""
        from rege.bridges.obsidian import ObsidianBridge

        bridge = ObsidianBridge()
        fragment = {
            "id": "FRAG_001",
            "name": "Test",
            "charge": 50,
            "tags": ["TAG+"],
        }
        md = bridge._fragment_to_markdown(fragment)
        assert "---" in md
        assert "id: FRAG_001" in md
        assert "charge: 50" in md


class TestGitBridge:
    """Tests for Git bridge."""

    def test_connect_no_repo(self, tmp_path):
        """Test connect with non-git directory."""
        from rege.bridges.git import GitBridge

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        result = bridge.connect()
        assert result is False
        assert "git" in bridge.last_error.lower()

    def test_connect_success(self, tmp_path):
        """Test successful connection to git repo."""
        from rege.bridges.git import GitBridge

        # Create fake git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        bridge = GitBridge(config={"repo_path": str(tmp_path)})
        result = bridge.connect()
        assert result is True
        assert bridge.is_connected

    def test_validate_branch_name_valid(self):
        """Test branch name validation with valid names."""
        from rege.bridges.git import GitBridge

        bridge = GitBridge()
        assert bridge.validate_branch_name("main")["valid"] is True
        assert bridge.validate_branch_name("bloom/spring")["valid"] is True
        assert bridge.validate_branch_name("ritual/test")["valid"] is True

    def test_validate_branch_name_invalid(self):
        """Test branch name validation with invalid names."""
        from rege.bridges.git import GitBridge

        bridge = GitBridge()
        result = bridge.validate_branch_name("bad-name")
        assert result["valid"] is False

    def test_pre_commit_hook_content(self):
        """Test pre-commit hook generation."""
        from rege.bridges.git import GitBridge

        bridge = GitBridge()
        content = bridge._get_pre_commit_hook()
        assert "#!/bin/bash" in content
        assert "RE:GE" in content

    def test_post_commit_hook_content(self):
        """Test post-commit hook generation."""
        from rege.bridges.git import GitBridge

        bridge = GitBridge()
        content = bridge._get_post_commit_hook()
        assert "#!/bin/bash" in content
        assert "SYSTEM_EVENT_LOG" in content


class TestMaxMSPBridge:
    """Tests for Max/MSP bridge."""

    def test_connect_mock_mode(self):
        """Test connection in mock mode (no pythonosc)."""
        from rege.bridges.maxmsp import MaxMSPBridge

        bridge = MaxMSPBridge()
        result = bridge.connect()
        assert result is True
        assert bridge.is_connected

    def test_send_fragment(self):
        """Test sending a fragment."""
        from rege.bridges.maxmsp import MaxMSPBridge

        bridge = MaxMSPBridge()
        bridge.connect()
        result = bridge.send_fragment({
            "id": "FRAG_001",
            "name": "Test",
            "charge": 75,
        })
        assert result["status"] == "sent"

    def test_send_charge(self):
        """Test sending charge value."""
        from rege.bridges.maxmsp import MaxMSPBridge

        bridge = MaxMSPBridge()
        bridge.connect()
        result = bridge.send_charge(85)
        assert result["status"] == "sent"
        assert result["charge"] == 85

    def test_send_bloom_phase(self):
        """Test sending bloom phase."""
        from rege.bridges.maxmsp import MaxMSPBridge

        bridge = MaxMSPBridge()
        bridge.connect()
        result = bridge.send_bloom_phase("spring")
        assert result["status"] == "sent"
        assert result["phase"] == "spring"

    def test_osc_addresses_defined(self):
        """Test OSC address patterns are defined."""
        from rege.bridges.maxmsp import MaxMSPBridge

        assert MaxMSPBridge.OSC_ADDRESSES["fragment"] == "/rege/fragment"
        assert MaxMSPBridge.OSC_ADDRESSES["charge"] == "/rege/charge"
        assert MaxMSPBridge.OSC_ADDRESSES["bloom_phase"] == "/rege/bloom/phase"


class TestGlobalRegistry:
    """Tests for global bridge registry."""

    def test_get_bridge_registry_singleton(self):
        """Test global registry is singleton."""
        reg1 = get_bridge_registry()
        reg2 = get_bridge_registry()
        assert reg1 is reg2

    def test_registry_has_mock_type(self):
        """Test mock type is registered by default."""
        registry = get_bridge_registry()
        assert registry.has_type("mock")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
