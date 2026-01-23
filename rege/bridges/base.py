"""
RE:GE Bridge Base - Abstract base class for external bridges.

Based on: RE-GE_OS_INTERFACE_02_EXTERNAL_BRIDGES.md

External bridges connect RE:GE to external tools:
- Obsidian (note-taking)
- Git (version control)
- Max/MSP (audio/visual)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class BridgeStatus(Enum):
    """Status of an external bridge connection."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class BridgeOperation:
    """Record of a bridge operation."""

    operation_id: str
    bridge_type: str
    operation: str  # connect, disconnect, send, receive
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class ExternalBridge(ABC):
    """
    Abstract base class for external bridge connections.

    All external bridges must implement:
    - connect(): Establish connection to external system
    - disconnect(): Close connection
    - send(): Send data to external system
    - receive(): Receive data from external system
    - status(): Get current bridge status
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the bridge.

        Args:
            name: Bridge name/identifier
            config: Optional configuration dictionary
        """
        self._name = name
        self._config = config or {}
        self._status = BridgeStatus.DISCONNECTED
        self._operations_log: List[BridgeOperation] = []
        self._last_error: Optional[str] = None
        self._connected_at: Optional[datetime] = None

    @property
    def name(self) -> str:
        """Get bridge name."""
        return self._name

    @property
    def is_connected(self) -> bool:
        """Check if bridge is connected."""
        return self._status == BridgeStatus.CONNECTED

    @property
    def current_status(self) -> BridgeStatus:
        """Get current bridge status."""
        return self._status

    @property
    def last_error(self) -> Optional[str]:
        """Get last error message."""
        return self._last_error

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to external system.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to external system.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to external system.

        Args:
            data: Data to send

        Returns:
            Result of send operation
        """
        pass

    @abstractmethod
    def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive data from external system.

        Returns:
            Received data, or None if no data available
        """
        pass

    def status(self) -> Dict[str, Any]:
        """
        Get detailed status information.

        Returns:
            Dictionary with status details
        """
        return {
            "name": self._name,
            "status": self._status.value,
            "is_connected": self.is_connected,
            "connected_at": self._connected_at.isoformat() if self._connected_at else None,
            "last_error": self._last_error,
            "operations_count": len(self._operations_log),
            "config": self._get_safe_config(),
        }

    def _get_safe_config(self) -> Dict[str, Any]:
        """Get config with sensitive values masked."""
        safe_config = {}
        sensitive_keys = {"password", "token", "key", "secret", "api_key"}

        for key, value in self._config.items():
            if key.lower() in sensitive_keys:
                safe_config[key] = "***"
            else:
                safe_config[key] = value

        return safe_config

    def _log_operation(
        self,
        operation: str,
        data: Optional[Dict[str, Any]] = None,
        status: str = "pending",
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> BridgeOperation:
        """Log a bridge operation."""
        import uuid

        op = BridgeOperation(
            operation_id=f"OP_{uuid.uuid4().hex[:8].upper()}",
            bridge_type=self.__class__.__name__,
            operation=operation,
            timestamp=datetime.now(),
            status=status,
            data=data,
            error=error,
            duration_ms=duration_ms,
        )
        self._operations_log.append(op)

        # Keep log size manageable
        if len(self._operations_log) > 1000:
            self._operations_log = self._operations_log[-500:]

        return op

    def get_operations_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent operations log.

        Args:
            limit: Maximum entries to return

        Returns:
            List of operation dictionaries
        """
        operations = self._operations_log[-limit:]
        return [
            {
                "operation_id": op.operation_id,
                "operation": op.operation,
                "timestamp": op.timestamp.isoformat(),
                "status": op.status,
                "error": op.error,
                "duration_ms": op.duration_ms,
            }
            for op in operations
        ]

    def _set_status(self, status: BridgeStatus) -> None:
        """Set bridge status."""
        self._status = status
        if status == BridgeStatus.CONNECTED:
            self._connected_at = datetime.now()
        elif status == BridgeStatus.DISCONNECTED:
            self._connected_at = None

    def _set_error(self, error: str) -> None:
        """Set error state."""
        self._last_error = error
        self._status = BridgeStatus.ERROR


class MockBridge(ExternalBridge):
    """
    Mock bridge for testing purposes.

    This bridge simulates connections without actually connecting
    to any external system.
    """

    def __init__(
        self,
        name: str = "MockBridge",
        config: Optional[Dict[str, Any]] = None,
        should_fail: bool = False,
    ):
        """
        Initialize mock bridge.

        Args:
            name: Bridge name
            config: Configuration
            should_fail: If True, operations will fail
        """
        super().__init__(name, config)
        self._should_fail = should_fail
        self._sent_data: List[Dict[str, Any]] = []
        self._receive_queue: List[Dict[str, Any]] = []

    def connect(self) -> bool:
        """Simulate connection."""
        self._log_operation("connect", status="started")

        if self._should_fail:
            self._set_error("Mock connection failure")
            self._log_operation("connect", status="failed", error="Mock failure")
            return False

        self._set_status(BridgeStatus.CONNECTED)
        self._log_operation("connect", status="success")
        return True

    def disconnect(self) -> bool:
        """Simulate disconnection."""
        self._log_operation("disconnect", status="started")

        if self._should_fail:
            self._set_error("Mock disconnection failure")
            self._log_operation("disconnect", status="failed", error="Mock failure")
            return False

        self._set_status(BridgeStatus.DISCONNECTED)
        self._log_operation("disconnect", status="success")
        return True

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate sending data."""
        self._log_operation("send", data=data, status="started")

        if self._should_fail:
            self._set_error("Mock send failure")
            self._log_operation("send", status="failed", error="Mock failure")
            return {"status": "failed", "error": "Mock failure"}

        if not self.is_connected:
            self._log_operation("send", status="failed", error="Not connected")
            return {"status": "failed", "error": "Not connected"}

        self._sent_data.append(data)
        self._log_operation("send", status="success")
        return {"status": "sent", "data": data}

    def receive(self) -> Optional[Dict[str, Any]]:
        """Simulate receiving data."""
        self._log_operation("receive", status="started")

        if self._should_fail:
            self._set_error("Mock receive failure")
            self._log_operation("receive", status="failed", error="Mock failure")
            return None

        if not self.is_connected:
            self._log_operation("receive", status="failed", error="Not connected")
            return None

        if self._receive_queue:
            data = self._receive_queue.pop(0)
            self._log_operation("receive", data=data, status="success")
            return data

        self._log_operation("receive", status="success")
        return None

    def queue_receive_data(self, data: Dict[str, Any]) -> None:
        """Queue data for receive() to return (for testing)."""
        self._receive_queue.append(data)

    def get_sent_data(self) -> List[Dict[str, Any]]:
        """Get all data that was sent (for testing)."""
        return self._sent_data.copy()
