"""
RE:GE Max/MSP Bridge - Integration with Max/MSP audio/visual software.

Based on: RE-GE_OS_INTERFACE_02_EXTERNAL_BRIDGES.md

Provides:
- OSC (Open Sound Control) communication
- Fragment data transmission
- Bloom phase triggers
- Real-time charge monitoring
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from rege.bridges.base import ExternalBridge, BridgeStatus


class MaxMSPBridge(ExternalBridge):
    """
    Bridge to Max/MSP audio/visual software via OSC.

    Connects RE:GE to Max/MSP for:
    - Sending fragment data as OSC messages
    - Triggering bloom phase changes
    - Real-time charge value streaming
    - Audio/visual response generation
    """

    # Default OSC port for Max/MSP
    DEFAULT_PORT = 7400

    # OSC address patterns
    OSC_ADDRESSES = {
        "fragment": "/rege/fragment",
        "charge": "/rege/charge",
        "bloom_phase": "/rege/bloom/phase",
        "canon_event": "/rege/canon",
        "status": "/rege/status",
        "depth": "/rege/depth",
        "queue": "/rege/queue",
    }

    def __init__(
        self,
        name: str = "MaxMSP",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Max/MSP bridge.

        Args:
            name: Bridge name
            config: Configuration with 'host' and 'port' keys
        """
        super().__init__(name, config)
        self._host = (config or {}).get("host", "localhost")
        self._port = (config or {}).get("port", self.DEFAULT_PORT)
        self._osc_client = None

    def connect(self) -> bool:
        """
        Connect to Max/MSP via OSC.

        Attempts to create OSC client connection.
        """
        self._log_operation("connect", status="started")

        try:
            # Try to import pythonosc
            from pythonosc import udp_client

            self._osc_client = udp_client.SimpleUDPClient(self._host, self._port)

            # Send test message
            self._osc_client.send_message("/rege/connect", [1])

            self._set_status(BridgeStatus.CONNECTED)
            self._log_operation("connect", status="success")
            return True

        except ImportError:
            # pythonosc not installed - use mock mode
            self._osc_client = None
            self._set_status(BridgeStatus.CONNECTED)
            self._log_operation(
                "connect",
                status="success",
                error="pythonosc not installed - mock mode",
            )
            return True

        except Exception as e:
            self._set_error(f"OSC connection failed: {e}")
            self._log_operation("connect", status="failed", error=str(e))
            return False

    def disconnect(self) -> bool:
        """Disconnect from Max/MSP."""
        self._log_operation("disconnect", status="started")

        if self._osc_client:
            try:
                self._osc_client.send_message("/rege/disconnect", [1])
            except Exception:
                pass  # Best effort disconnect message

        self._osc_client = None
        self._set_status(BridgeStatus.DISCONNECTED)
        self._log_operation("disconnect", status="success")
        return True

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to Max/MSP as OSC messages.

        Args:
            data: Data to send with 'type' key determining format

        Returns:
            Result of send operation
        """
        start_time = datetime.now()
        self._log_operation("send", data={"type": data.get("type")}, status="started")

        if not self.is_connected:
            self._log_operation("send", status="failed", error="Not connected")
            return {"status": "failed", "error": "Not connected"}

        data_type = data.get("type", "generic")

        if data_type == "fragment":
            result = self._send_fragment(data.get("fragment", {}))
        elif data_type == "charge":
            result = self._send_charge(data.get("charge", 50))
        elif data_type == "bloom_phase":
            result = self._send_bloom_phase(data.get("phase", "dormant"))
        elif data_type == "canon_event":
            result = self._send_canon_event(data.get("event", {}))
        elif data_type == "batch":
            result = self._send_batch(data.get("messages", []))
        else:
            result = self._send_generic(data)

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        self._log_operation(
            "send",
            status=result.get("status"),
            duration_ms=duration_ms,
        )
        return result

    def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive data from Max/MSP.

        Note: OSC is primarily one-way in this implementation.
        Returns current bridge state.
        """
        self._log_operation("receive", status="started")

        if not self.is_connected:
            return None

        # Return current state (OSC doesn't support true receive)
        state = {
            "connected": self.is_connected,
            "host": self._host,
            "port": self._port,
            "mock_mode": self._osc_client is None,
        }

        self._log_operation("receive", status="success")
        return state

    def _send_osc(self, address: str, args: List[Any]) -> bool:
        """
        Send OSC message.

        Args:
            address: OSC address pattern
            args: Message arguments

        Returns:
            True if sent successfully
        """
        if self._osc_client:
            try:
                self._osc_client.send_message(address, args)
                return True
            except Exception:
                return False
        else:
            # Mock mode - just log
            return True

    def _send_fragment(self, fragment: Dict[str, Any]) -> Dict[str, Any]:
        """Send fragment data as OSC."""
        address = self.OSC_ADDRESSES["fragment"]

        # Convert fragment to OSC-friendly format
        args = [
            fragment.get("id", "UNKNOWN"),
            fragment.get("name", "unnamed"),
            fragment.get("charge", 50),
            ",".join(fragment.get("tags", [])),
            fragment.get("status", "active"),
        ]

        if self._send_osc(address, args):
            return {"status": "sent", "address": address}
        return {"status": "failed", "error": "OSC send failed"}

    def _send_charge(self, charge: int) -> Dict[str, Any]:
        """Send charge value as OSC."""
        address = self.OSC_ADDRESSES["charge"]

        if self._send_osc(address, [charge]):
            return {"status": "sent", "address": address, "charge": charge}
        return {"status": "failed", "error": "OSC send failed"}

    def _send_bloom_phase(self, phase: str) -> Dict[str, Any]:
        """Send bloom phase as OSC."""
        address = self.OSC_ADDRESSES["bloom_phase"]

        # Map phase to numeric value for Max/MSP
        phase_values = {
            "dormant": 0,
            "spring": 1,
            "growth": 2,
            "peak": 3,
            "wilt": 4,
            "decay": 5,
        }
        phase_num = phase_values.get(phase.lower(), 0)

        if self._send_osc(address, [phase, phase_num]):
            return {"status": "sent", "address": address, "phase": phase}
        return {"status": "failed", "error": "OSC send failed"}

    def _send_canon_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Send canon event as OSC."""
        address = self.OSC_ADDRESSES["canon_event"]

        args = [
            event.get("event_id", "UNKNOWN"),
            event.get("charge", 75),
            event.get("status", "glowing"),
        ]

        if self._send_osc(address, args):
            return {"status": "sent", "address": address}
        return {"status": "failed", "error": "OSC send failed"}

    def _send_batch(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send batch of messages."""
        sent = 0
        failed = 0

        for msg in messages:
            msg_type = msg.get("type", "generic")
            result = self.send(msg)
            if result.get("status") == "sent":
                sent += 1
            else:
                failed += 1

        return {
            "status": "sent" if failed == 0 else "partial",
            "sent": sent,
            "failed": failed,
        }

    def _send_generic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send generic data as OSC."""
        address = self.OSC_ADDRESSES["status"]

        # Flatten data to simple types
        args = []
        for key, value in data.items():
            if key != "type":
                args.append(str(key))
                args.append(str(value))

        if self._send_osc(address, args):
            return {"status": "sent", "address": address}
        return {"status": "failed", "error": "OSC send failed"}

    def send_fragment(self, fragment: Dict[str, Any]) -> Dict[str, Any]:
        """Convenience method to send a fragment."""
        return self.send({"type": "fragment", "fragment": fragment})

    def send_charge(self, charge: int) -> Dict[str, Any]:
        """Convenience method to send charge value."""
        return self.send({"type": "charge", "charge": charge})

    def send_bloom_phase(self, phase: str) -> Dict[str, Any]:
        """Convenience method to send bloom phase."""
        return self.send({"type": "bloom_phase", "phase": phase})

    def get_host(self) -> str:
        """Get configured host."""
        return self._host

    def get_port(self) -> int:
        """Get configured port."""
        return self._port

    def set_connection(self, host: str, port: int) -> None:
        """Set host and port."""
        self._host = host
        self._port = port
        self._config["host"] = host
        self._config["port"] = port


# Register with bridge registry when imported
def register_maxmsp_bridge():
    """Register Max/MSP bridge with the global registry."""
    from rege.bridges.registry import get_bridge_registry

    registry = get_bridge_registry()
    registry.register_type("maxmsp", MaxMSPBridge)


# Auto-register on import
try:
    register_maxmsp_bridge()
except ImportError:
    pass  # Registry not available yet
