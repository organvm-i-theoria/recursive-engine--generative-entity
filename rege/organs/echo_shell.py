"""
RE:GE Echo Shell - Recursion interface for decay and whispered loops.

Based on: RE-GE_ORG_BODY_09_ECHO_SHELL.md

The Echo Shell governs:
- Decay monitoring
- Whispered loops and latent fragments
- Recursion interface
- Background pulse tracking
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch
from rege.core.constants import get_tier, TIER_BOUNDARIES


class Echo:
    """An echo - a fragment that pulses in the background."""

    def __init__(self, content: str, charge: int, source: str):
        self.echo_id = f"ECHO_{uuid.uuid4().hex[:8].upper()}"
        self.content = content
        self.charge = charge
        self.source = source
        self.pulse_count = 0
        self.created_at = datetime.now()
        self.last_pulse = datetime.now()
        self.decay_rate = self._calculate_decay_rate()
        self.status = "active"
        self.whispers: List[str] = []

    def _calculate_decay_rate(self) -> float:
        """Calculate decay rate per day."""
        if self.charge <= 25:
            return 0.2  # Fast decay for LATENT
        elif self.charge <= 50:
            return 0.1  # Moderate decay for PROCESSING
        else:
            return 0.05  # Slow decay for ACTIVE+

    def pulse(self) -> Dict[str, Any]:
        """Record a pulse, slightly refreshing the echo."""
        self.pulse_count += 1
        self.last_pulse = datetime.now()

        # Pulsing adds small charge (max 3 points)
        charge_gain = min(3, 1 + (self.pulse_count % 3))
        self.charge = min(100, self.charge + charge_gain)

        return {
            "echo_id": self.echo_id,
            "pulse_count": self.pulse_count,
            "new_charge": self.charge,
            "status": "pulsed",
        }

    def decay(self, days: int = 1) -> int:
        """Apply decay over time."""
        decay_amount = int(self.decay_rate * days * 10)
        self.charge = max(0, self.charge - decay_amount)

        if self.charge == 0:
            self.status = "faded"

        return self.charge

    def whisper(self, message: str) -> None:
        """Add a whisper to the echo."""
        self.whispers.append(message)
        # Whispers slightly increase charge
        self.charge = min(100, self.charge + 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "echo_id": self.echo_id,
            "content": self.content,
            "charge": self.charge,
            "source": self.source,
            "pulse_count": self.pulse_count,
            "created_at": self.created_at.isoformat(),
            "last_pulse": self.last_pulse.isoformat(),
            "decay_rate": self.decay_rate,
            "status": self.status,
            "whispers": self.whispers[-5:],  # Last 5 whispers
            "tier": get_tier(self.charge),
        }


class EchoShell(OrganHandler):
    """
    The Echo Shell - Recursion interface for decay and whispered loops.

    Modes:
    - decay: Monitor and apply decay
    - whisper: Process whispered fragments
    - pulse: Refresh echoes through pulsing
    - default: Standard echo handling
    """

    @property
    def name(self) -> str:
        return "ECHO_SHELL"

    @property
    def description(self) -> str:
        return "Recursion interface for decay, whispered loops, and latent fragments"

    def __init__(self):
        super().__init__()
        self._echoes: Dict[str, Echo] = {}
        self._latent_pool: List[str] = []  # IDs of LATENT echoes
        self._depth_log: List[Dict] = []

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Echo Shell."""
        mode = invocation.mode.lower()

        if mode == "decay":
            return self._decay_mode(invocation, patch)
        elif mode == "whisper":
            return self._whisper_mode(invocation, patch)
        elif mode == "pulse":
            return self._pulse_mode(invocation, patch)
        else:
            return self._default_mode(invocation, patch)

    def _decay_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Monitor and apply decay."""
        # Apply decay to all echoes
        decayed = self._apply_decay_cycle()

        # Find echoes that have faded
        faded = [e for e in self._echoes.values() if e.status == "faded"]

        return {
            "decay_cycle_applied": True,
            "echoes_affected": len(decayed),
            "faded_count": len(faded),
            "latent_pool_size": len(self._latent_pool),
            "decay_summary": {
                "critical_echoes": len([e for e in self._echoes.values() if e.charge >= 86]),
                "intense_echoes": len([e for e in self._echoes.values() if 71 <= e.charge < 86]),
                "latent_echoes": len([e for e in self._echoes.values() if e.charge <= 25]),
            },
        }

    def _whisper_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process whispered fragments."""
        # Create new echo from whisper
        echo = self._create_echo(invocation)

        # Mark as whisper source
        echo.whisper(invocation.symbol)

        return {
            "echo": echo.to_dict(),
            "whisper_recorded": True,
            "latent_status": echo.charge <= TIER_BOUNDARIES["LATENT_MAX"],
        }

    def _pulse_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Refresh echoes through pulsing."""
        # Find echo to pulse
        target_echo = self._find_echo_by_content(invocation.symbol)

        if target_echo:
            pulse_result = target_echo.pulse()
            return {
                "pulse_result": pulse_result,
                "echo": target_echo.to_dict(),
            }
        else:
            # Create new echo and pulse it
            echo = self._create_echo(invocation)
            pulse_result = echo.pulse()
            return {
                "pulse_result": pulse_result,
                "echo": echo.to_dict(),
                "new_echo_created": True,
            }

    def _default_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard echo handling."""
        echo = self._create_echo(invocation)

        return {
            "echo": echo.to_dict(),
            "status": "echoed",
            "recommendations": self._echo_recommendations(echo),
        }

    def pulse(self, echo_id: str) -> Dict[str, Any]:
        """
        Pulse a specific echo.

        Args:
            echo_id: ID of echo to pulse

        Returns:
            Pulse result
        """
        if echo_id not in self._echoes:
            return {"status": "not_found", "echo_id": echo_id}

        return self._echoes[echo_id].pulse()

    def decay(self, echo_id: str, days: int = 1) -> Dict[str, Any]:
        """
        Apply decay to a specific echo.

        Args:
            echo_id: ID of echo
            days: Number of days of decay

        Returns:
            Decay result
        """
        if echo_id not in self._echoes:
            return {"status": "not_found", "echo_id": echo_id}

        echo = self._echoes[echo_id]
        new_charge = echo.decay(days)

        # Update latent pool
        self._update_latent_pool(echo)

        return {
            "echo_id": echo_id,
            "new_charge": new_charge,
            "status": echo.status,
            "in_latent_pool": echo_id in self._latent_pool,
        }

    def track_depth(self, patch: Patch) -> Dict[str, Any]:
        """
        Track recursion depth for a patch.

        Args:
            patch: The patch to track

        Returns:
            Depth tracking result
        """
        entry = {
            "patch_id": patch.patch_id,
            "depth": patch.depth,
            "timestamp": datetime.now().isoformat(),
            "input": patch.input_node,
            "output": patch.output_node,
        }

        self._depth_log.append(entry)

        return {
            "tracked": True,
            "current_depth": patch.depth,
            "at_risk": patch.depth >= 5,  # Warning threshold
        }

    def _create_echo(self, invocation: Invocation) -> Echo:
        """Create an echo from invocation."""
        echo = Echo(
            content=invocation.symbol,
            charge=invocation.charge,
            source=invocation.organ,
        )

        self._echoes[echo.echo_id] = echo
        self._update_latent_pool(echo)

        return echo

    def _find_echo_by_content(self, content: str) -> Optional[Echo]:
        """Find an echo by content similarity."""
        content_lower = content.lower()

        for echo in self._echoes.values():
            if content_lower in echo.content.lower():
                return echo

        return None

    def _apply_decay_cycle(self) -> List[Echo]:
        """Apply decay to all echoes."""
        decayed = []

        for echo in self._echoes.values():
            if echo.status != "faded":
                old_charge = echo.charge
                echo.decay(1)
                if echo.charge != old_charge:
                    decayed.append(echo)
                    self._update_latent_pool(echo)

        return decayed

    def _update_latent_pool(self, echo: Echo) -> None:
        """Update latent pool membership for echo."""
        if echo.charge <= TIER_BOUNDARIES["LATENT_MAX"]:
            if echo.echo_id not in self._latent_pool:
                self._latent_pool.append(echo.echo_id)
        else:
            if echo.echo_id in self._latent_pool:
                self._latent_pool.remove(echo.echo_id)

    def _echo_recommendations(self, echo: Echo) -> List[str]:
        """Generate recommendations for echo."""
        recommendations = []

        if echo.charge <= 25:
            recommendations.append("Consider pulsing to prevent fade")
        if echo.charge >= 71:
            recommendations.append("Echo strong - consider archival")
        if echo.pulse_count == 0:
            recommendations.append("New echo - monitor for recurrence")

        return recommendations or ["Echo stable"]

    def get_valid_modes(self) -> List[str]:
        return ["decay", "whisper", "pulse", "default"]

    def get_output_types(self) -> List[str]:
        return ["echo_log", "latent_state", "whisper_record"]

    def get_echo(self, echo_id: str) -> Optional[Echo]:
        """Get an echo by ID."""
        return self._echoes.get(echo_id)

    def get_all_echoes(self) -> List[Echo]:
        """Get all echoes."""
        return list(self._echoes.values())

    def get_latent_echoes(self) -> List[Echo]:
        """Get echoes in latent pool."""
        return [self._echoes[eid] for eid in self._latent_pool if eid in self._echoes]
