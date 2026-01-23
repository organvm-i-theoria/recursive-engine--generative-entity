"""
RE:GE Bridge Registry - Management of external bridge connections.

Provides:
- Bridge registration and lookup
- Bridge type mapping
- Global registry singleton
"""

from typing import Any, Dict, List, Optional, Type
from rege.bridges.base import ExternalBridge, BridgeStatus


class BridgeRegistry:
    """
    Registry for managing external bridge instances.

    The registry handles:
    - Registration of bridge types
    - Creation of bridge instances
    - Lookup of active bridges
    - Status tracking across all bridges
    """

    def __init__(self):
        """Initialize the bridge registry."""
        self._bridge_types: Dict[str, Type[ExternalBridge]] = {}
        self._active_bridges: Dict[str, ExternalBridge] = {}

    def register_type(self, name: str, bridge_class: Type[ExternalBridge]) -> None:
        """
        Register a bridge type.

        Args:
            name: Bridge type name (e.g., "obsidian", "git", "maxmsp")
            bridge_class: Bridge class to register
        """
        self._bridge_types[name.lower()] = bridge_class

    def create_bridge(
        self,
        bridge_type: str,
        instance_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[ExternalBridge]:
        """
        Create a bridge instance of the specified type.

        Args:
            bridge_type: Type of bridge to create
            instance_name: Optional instance name (defaults to type name)
            config: Optional configuration dictionary

        Returns:
            Created bridge instance, or None if type not found
        """
        bridge_class = self._bridge_types.get(bridge_type.lower())
        if bridge_class is None:
            return None

        name = instance_name or bridge_type
        bridge = bridge_class(name=name, config=config)
        self._active_bridges[name] = bridge
        return bridge

    def get_bridge(self, name: str) -> Optional[ExternalBridge]:
        """
        Get an active bridge by name.

        Args:
            name: Bridge instance name

        Returns:
            Bridge instance, or None if not found
        """
        return self._active_bridges.get(name)

    def remove_bridge(self, name: str) -> bool:
        """
        Remove a bridge from the registry.

        Disconnects the bridge if connected before removing.

        Args:
            name: Bridge instance name

        Returns:
            True if bridge was removed, False if not found
        """
        bridge = self._active_bridges.get(name)
        if bridge is None:
            return False

        # Disconnect if connected
        if bridge.is_connected:
            bridge.disconnect()

        del self._active_bridges[name]
        return True

    def list_types(self) -> List[str]:
        """
        List available bridge types.

        Returns:
            List of registered bridge type names
        """
        return list(self._bridge_types.keys())

    def list_active(self) -> List[str]:
        """
        List active bridge instances.

        Returns:
            List of active bridge instance names
        """
        return list(self._active_bridges.keys())

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all active bridges.

        Returns:
            Dictionary mapping bridge names to status dicts
        """
        return {name: bridge.status() for name, bridge in self._active_bridges.items()}

    def connect_all(self) -> Dict[str, bool]:
        """
        Attempt to connect all active bridges.

        Returns:
            Dictionary mapping bridge names to connection success
        """
        results = {}
        for name, bridge in self._active_bridges.items():
            if not bridge.is_connected:
                results[name] = bridge.connect()
            else:
                results[name] = True
        return results

    def disconnect_all(self) -> Dict[str, bool]:
        """
        Disconnect all active bridges.

        Returns:
            Dictionary mapping bridge names to disconnection success
        """
        results = {}
        for name, bridge in self._active_bridges.items():
            if bridge.is_connected:
                results[name] = bridge.disconnect()
            else:
                results[name] = True
        return results

    def get_connected_count(self) -> int:
        """
        Get count of connected bridges.

        Returns:
            Number of bridges with CONNECTED status
        """
        return sum(1 for bridge in self._active_bridges.values() if bridge.is_connected)

    def has_type(self, bridge_type: str) -> bool:
        """
        Check if a bridge type is registered.

        Args:
            bridge_type: Bridge type name

        Returns:
            True if type is registered
        """
        return bridge_type.lower() in self._bridge_types

    def clear(self) -> None:
        """
        Clear all bridges from registry.

        Disconnects all bridges before clearing.
        """
        self.disconnect_all()
        self._active_bridges.clear()


# Global bridge registry instance
_bridge_registry: Optional[BridgeRegistry] = None


def get_bridge_registry() -> BridgeRegistry:
    """
    Get or create the global bridge registry.

    Returns:
        Global BridgeRegistry instance
    """
    global _bridge_registry
    if _bridge_registry is None:
        _bridge_registry = BridgeRegistry()

        # Register default bridge types
        _register_default_types(_bridge_registry)

    return _bridge_registry


def _register_default_types(registry: BridgeRegistry) -> None:
    """
    Register default bridge types.

    This registers the built-in bridge types when the registry is first created.
    """
    from rege.bridges.base import MockBridge

    # Register mock bridge for testing
    registry.register_type("mock", MockBridge)

    # Note: Actual bridges (obsidian, git, maxmsp) are registered
    # in their respective modules when imported
