"""
RE:GE External Bridges - Integration with external tools and systems.

Provides:
- Base bridge interface
- Bridge registry for managing connections
- Bridge configuration system
- Logging infrastructure for bridge operations
"""

from rege.bridges.base import ExternalBridge, BridgeStatus
from rege.bridges.registry import BridgeRegistry, get_bridge_registry
from rege.bridges.config import BridgeConfig, get_bridge_config

__all__ = [
    "ExternalBridge",
    "BridgeStatus",
    "BridgeRegistry",
    "get_bridge_registry",
    "BridgeConfig",
    "get_bridge_config",
]
