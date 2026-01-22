"""
RE:GE Heart of Canon - The emotional core of the system.

Based on: RE-GE_ORG_BODY_01_HEART_OF_CANON.md

The Heart of Canon governs:
- Canon Events and timeline convergence
- Mythic truth and memory-blood
- Emotional intensity tracking
- Pattern recurrence detection

It does not care about factuality. It cares about:
- Felt intensity
- Pattern recurrence
- Emotional frequency
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch, CanonEvent
from rege.core.constants import get_tier, is_canonization_eligible, is_critical_emergency


class HeartOfCanon(OrganHandler):
    """
    The Heart of Canon - Emotional core governing Canon Events and mythic truth.

    Modes:
    - mythic: Process as mythic narrative
    - recursive: Process recurring patterns
    - devotional: Sacred/ritualized processing
    - default: Standard processing
    """

    @property
    def name(self) -> str:
        return "HEART_OF_CANON"

    @property
    def description(self) -> str:
        return "The emotional core governing Canon Events, mythic truth, and memory-blood"

    def __init__(self):
        super().__init__()
        self._canon_database: Dict[str, CanonEvent] = {}
        self._recurrence_tracker: Dict[str, int] = {}

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Heart of Canon."""
        mode = invocation.mode.lower()

        if mode == "mythic":
            return self._mythic_process(invocation, patch)
        elif mode == "recursive":
            return self._recursive_process(invocation, patch)
        elif mode == "devotional":
            return self._devotional_process(invocation, patch)
        else:
            return self._default_process(invocation, patch)

    def _mythic_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process as mythic narrative."""
        event = self._create_canon_event(invocation, patch)
        event.event_type = "mythic_narrative"

        # Check for canonization
        if is_canonization_eligible(event.charge):
            event.status = "canon_candidate"
            if is_critical_emergency(event.charge):
                event.status = "emergent_canon"

        return {
            "event": event.to_dict(),
            "tier": get_tier(event.charge),
            "mythic_weight": self._calculate_mythic_weight(event),
            "linked_nodes": event.linked_nodes,
        }

    def _recursive_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process recurring patterns."""
        symbol = invocation.symbol

        # Track recurrence
        self._recurrence_tracker[symbol] = self._recurrence_tracker.get(symbol, 0) + 1
        recurrence = self._recurrence_tracker[symbol]

        event = self._create_canon_event(invocation, patch)
        event.recurrence = recurrence
        event.event_type = "recurring_pattern"

        # Higher charge for recurring patterns
        if recurrence >= 3:
            event.charge = min(100, event.charge + (recurrence * 5))

        return {
            "event": event.to_dict(),
            "recurrence_count": recurrence,
            "pattern_strength": min(1.0, recurrence / 10),
            "recommended_action": "canonize" if recurrence >= 6 else "monitor",
        }

    def _devotional_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Sacred/ritualized processing."""
        event = self._create_canon_event(invocation, patch)
        event.event_type = "devotional_entry"
        event.tags.append("RITUAL+")

        # Devotional entries get boost
        event.charge = min(100, event.charge + 10)

        return {
            "event": event.to_dict(),
            "sacred_weight": event.charge / 100,
            "blessing": self._generate_blessing(event),
        }

    def _default_process(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard processing."""
        return self.pulse_check(invocation.symbol, invocation.charge)

    def canonize_event(self, event: CanonEvent) -> Dict[str, Any]:
        """
        Canonize an event into the sacred database.

        Args:
            event: The event to canonize

        Returns:
            Canonization result
        """
        if not is_canonization_eligible(event.charge):
            return {
                "canonized": False,
                "reason": f"Charge {event.charge} below threshold (71 required)",
            }

        event.status = "canonized"
        event.canonized_at = datetime.now()
        self._canon_database[event.event_id] = event

        return {
            "canonized": True,
            "event_id": event.event_id,
            "canonized_at": event.canonized_at.isoformat(),
            "charge": event.charge,
            "tier": get_tier(event.charge),
        }

    def pulse_check(self, memory: str, charge: int = 50) -> Dict[str, Any]:
        """
        Check the pulse status of a memory.

        Based on charge tier system:
        - CRITICAL (86+): emergent_canon
        - INTENSE (71-85): canon_candidate
        - Below: echo

        Args:
            memory: The memory content
            charge: Emotional charge value

        Returns:
            Pulse check result
        """
        # Check if already canonized
        for event in self._canon_database.values():
            if event.content == memory:
                return {
                    "status": "glowing",
                    "in_canon": True,
                    "event_id": event.event_id,
                    "charge": event.charge,
                }

        # Determine status by charge
        if charge >= 86:
            status = "emergent_canon"
        elif charge >= 71:
            status = "canon_candidate"
        else:
            status = "echo"

        return {
            "status": status,
            "in_canon": False,
            "charge": charge,
            "tier": get_tier(charge),
            "canonization_eligible": is_canonization_eligible(charge),
        }

    def bleed_into_archive(self, event: CanonEvent) -> Dict[str, Any]:
        """
        Bleed an event into the archive.

        Args:
            event: The event to archive

        Returns:
            Archive entry details
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "content": event.content,
            "origin": "HEART_OF_CANON",
            "loop_status": "recurring" if event.recurrence > 1 else "singular",
            "charge": event.charge,
            "tags": event.tags,
        }

    def _create_canon_event(self, invocation: Invocation, patch: Patch) -> CanonEvent:
        """Create a CanonEvent from invocation."""
        return CanonEvent(
            event_id=f"CANON_{uuid.uuid4().hex[:8].upper()}",
            content=invocation.symbol,
            charge=invocation.charge,
            status="pulse",
            linked_nodes=["MIRROR_CABINET", "ARCHIVE_ORDER"],
            event_type="invocation",
            tags=invocation.flags.copy(),
        )

    def _calculate_mythic_weight(self, event: CanonEvent) -> float:
        """Calculate mythic weight of an event (0-1)."""
        base = event.charge / 100
        recurrence_bonus = min(0.3, event.recurrence * 0.05)
        return min(1.0, base + recurrence_bonus)

    def _generate_blessing(self, event: CanonEvent) -> str:
        """Generate a blessing for devotional entries."""
        tier = get_tier(event.charge)
        blessings = {
            "LATENT": "May this seed find light.",
            "PROCESSING": "The work continues in silence.",
            "ACTIVE": "Your attention is witnessed.",
            "INTENSE": "The heart recognizes its own.",
            "CRITICAL": "This becomes canon. So be it.",
        }
        return blessings.get(tier, "The heart hears.")

    def get_valid_modes(self) -> List[str]:
        return ["mythic", "recursive", "devotional", "default"]

    def get_output_types(self) -> List[str]:
        return ["canon_event", "pulse_check", "archive_entry"]

    def get_canon_events(self) -> List[CanonEvent]:
        """Get all canonized events."""
        return list(self._canon_database.values())

    def get_recurrence_stats(self) -> Dict[str, int]:
        """Get recurrence tracking statistics."""
        return self._recurrence_tracker.copy()
