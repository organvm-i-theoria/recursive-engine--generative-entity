"""
RE:GE Place Protocols - Spatial context engine for location-aware invocations.

Based on: RE-GE_ORG_BODY_16_PLACE_PROTOCOLS.md

The Place Protocols govern:
- Canonical zones and their symbolic rules
- Location state tracking and history
- Zone-specific rule resolution
- Spatial context for ritual processing
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


@dataclass
class RitualPlace:
    """
    A symbolic place with associated rules and behaviors.

    Canonical zones define the spatial context for ritual processing,
    each with unique functions and time behaviors.
    """
    place_id: str
    zone: str
    functions: List[str]
    time_behavior: str
    charge_modifier: int = 0
    access_level: str = "open"
    linked_organs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.place_id:
            self.place_id = f"PLACE_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize place to dictionary."""
        return {
            "place_id": self.place_id,
            "zone": self.zone,
            "functions": self.functions,
            "time_behavior": self.time_behavior,
            "charge_modifier": self.charge_modifier,
            "access_level": self.access_level,
            "linked_organs": self.linked_organs,
            "metadata": self.metadata,
        }


# Canonical zone definitions
CANONICAL_ZONES: Dict[str, Dict[str, Any]] = {
    "HERE": {
        "functions": ["presence", "immediacy", "grounding"],
        "time_behavior": "present_continuous",
        "charge_modifier": 0,
        "access_level": "open",
        "linked_organs": ["HEART_OF_CANON", "MIRROR_CABINET"],
        "description": "The immediate present moment",
    },
    "THERE": {
        "functions": ["distance", "longing", "projection"],
        "time_behavior": "future_possible",
        "charge_modifier": -5,
        "access_level": "open",
        "linked_organs": ["DREAM_COUNCIL", "ECHO_SHELL"],
        "description": "The distant or desired elsewhere",
    },
    "NOWHERE": {
        "functions": ["void", "dissolution", "reset"],
        "time_behavior": "timeless",
        "charge_modifier": -20,
        "access_level": "restricted",
        "linked_organs": ["ECHO_SHELL", "RITUAL_COURT"],
        "description": "The void between states",
    },
    "SOMEWHERE": {
        "functions": ["possibility", "seeking", "emergence"],
        "time_behavior": "indeterminate",
        "charge_modifier": 5,
        "access_level": "open",
        "linked_organs": ["BLOOM_ENGINE", "DREAM_COUNCIL"],
        "description": "The space of potentiality",
    },
    "BACKTHEN": {
        "functions": ["memory", "nostalgia", "reconstruction"],
        "time_behavior": "past_fixed",
        "charge_modifier": 10,
        "access_level": "open",
        "linked_organs": ["ARCHIVE_ORDER", "HEART_OF_CANON"],
        "description": "The remembered past",
    },
    "NEVERW4S": {
        "functions": ["alternate", "counterfactual", "grief"],
        "time_behavior": "impossible_past",
        "charge_modifier": 15,
        "access_level": "restricted",
        "linked_organs": ["MIRROR_CABINET", "RITUAL_COURT"],
        "description": "The path not taken",
    },
    "MAIN_STREET": {
        "functions": ["public", "performance", "commerce"],
        "time_behavior": "social_time",
        "charge_modifier": 0,
        "access_level": "public",
        "linked_organs": ["MASK_ENGINE", "MYTHIC_SENATE"],
        "description": "The public sphere",
    },
    "MULHOLLAND_DRIVE": {
        "functions": ["transformation", "threshold", "risk"],
        "time_behavior": "liminal",
        "charge_modifier": 20,
        "access_level": "conditional",
        "linked_organs": ["BLOOM_ENGINE", "RITUAL_COURT"],
        "description": "The transformative edge",
    },
    "THE_ARCHIVE": {
        "functions": ["storage", "retrieval", "preservation"],
        "time_behavior": "eternal",
        "charge_modifier": 5,
        "access_level": "open",
        "linked_organs": ["ARCHIVE_ORDER", "ECHO_SHELL"],
        "description": "The repository of all records",
    },
    "THE_STAGE": {
        "functions": ["performance", "ritual", "witnessing"],
        "time_behavior": "ritual_time",
        "charge_modifier": 15,
        "access_level": "conditional",
        "linked_organs": ["RITUAL_COURT", "MASK_ENGINE"],
        "description": "The space of witnessed action",
    },
}


class PlaceProtocols(OrganHandler):
    """
    Place Protocols - Spatial context engine for location-aware invocations.

    Modes:
    - enter: Enter a place, apply its rules
    - exit: Leave current place
    - map: Get current location context
    - rules: Query zone-specific rules
    - default: Location status
    """

    @property
    def name(self) -> str:
        return "PLACE_PROTOCOLS"

    @property
    def description(self) -> str:
        return "Spatial context engine for location-aware invocations"

    def __init__(self):
        super().__init__()
        self._current_place: Optional[str] = "HERE"  # Default starting place
        self._place_history: List[Dict[str, Any]] = []
        self._custom_places: Dict[str, RitualPlace] = {}
        self._zone_rules: Dict[str, List[str]] = {}

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Place Protocols."""
        mode = invocation.mode.lower()

        if mode == "enter":
            return self._enter_place(invocation, patch)
        elif mode == "exit":
            return self._exit_place(invocation, patch)
        elif mode == "map":
            return self._map_location(invocation, patch)
        elif mode == "rules":
            return self._get_zone_rules(invocation, patch)
        else:
            return self._default_location(invocation, patch)

    def _enter_place(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Enter a place and apply its rules."""
        zone = invocation.symbol.strip().upper()

        # Check if zone exists
        if zone not in CANONICAL_ZONES and zone not in self._custom_places:
            return {
                "status": "failed",
                "error": f"Unknown zone: {zone}",
                "available_zones": list(CANONICAL_ZONES.keys()) + list(self._custom_places.keys()),
            }

        # Get zone config
        if zone in CANONICAL_ZONES:
            zone_config = CANONICAL_ZONES[zone]
            place = RitualPlace(
                place_id=f"PLACE_{zone}",
                zone=zone,
                functions=zone_config["functions"],
                time_behavior=zone_config["time_behavior"],
                charge_modifier=zone_config["charge_modifier"],
                access_level=zone_config["access_level"],
                linked_organs=zone_config["linked_organs"],
            )
        else:
            place = self._custom_places[zone]
            zone_config = place.to_dict()

        # Check access level
        if zone_config.get("access_level") == "restricted":
            if invocation.charge < 71:  # INTENSE tier required
                return {
                    "status": "access_denied",
                    "zone": zone,
                    "required_charge": 71,
                    "current_charge": invocation.charge,
                    "reason": "Restricted zone requires INTENSE charge level",
                }
        elif zone_config.get("access_level") == "conditional":
            if invocation.charge < 51:  # ACTIVE tier required
                return {
                    "status": "access_denied",
                    "zone": zone,
                    "required_charge": 51,
                    "current_charge": invocation.charge,
                    "reason": "Conditional zone requires ACTIVE charge level",
                }

        # Record transition
        previous_place = self._current_place
        self._place_history.append({
            "from_place": previous_place,
            "to_place": zone,
            "timestamp": datetime.now().isoformat(),
            "charge_at_transition": invocation.charge,
        })

        self._current_place = zone

        # Calculate modified charge
        modified_charge = min(100, max(0, invocation.charge + zone_config.get("charge_modifier", 0)))

        return {
            "status": "entered",
            "zone": zone,
            "previous_zone": previous_place,
            "place": place.to_dict(),
            "time_behavior": zone_config.get("time_behavior"),
            "functions": zone_config.get("functions", []),
            "linked_organs": zone_config.get("linked_organs", []),
            "charge_modifier": zone_config.get("charge_modifier", 0),
            "modified_charge": modified_charge,
            "transition_count": len(self._place_history),
        }

    def _exit_place(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Exit current place, return to HERE."""
        previous_place = self._current_place

        if previous_place == "HERE":
            return {
                "status": "already_here",
                "zone": "HERE",
                "message": "Already at HERE - no exit needed",
            }

        # Record transition
        self._place_history.append({
            "from_place": previous_place,
            "to_place": "HERE",
            "timestamp": datetime.now().isoformat(),
            "charge_at_transition": invocation.charge,
            "exit_type": "explicit",
        })

        self._current_place = "HERE"

        return {
            "status": "exited",
            "previous_zone": previous_place,
            "current_zone": "HERE",
            "transition_count": len(self._place_history),
            "time_spent": self._calculate_time_in_zone(previous_place),
        }

    def _map_location(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Get current location context."""
        current_zone = self._current_place or "HERE"

        if current_zone in CANONICAL_ZONES:
            zone_config = CANONICAL_ZONES[current_zone]
        elif current_zone in self._custom_places:
            zone_config = self._custom_places[current_zone].to_dict()
        else:
            zone_config = CANONICAL_ZONES["HERE"]

        return {
            "status": "mapped",
            "current_zone": current_zone,
            "zone_config": zone_config,
            "history_length": len(self._place_history),
            "recent_transitions": self._place_history[-5:] if self._place_history else [],
            "available_zones": list(CANONICAL_ZONES.keys()),
            "custom_zones": list(self._custom_places.keys()),
        }

    def _get_zone_rules(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Get rules for a specific zone."""
        zone = invocation.symbol.strip().upper() if invocation.symbol else self._current_place

        if zone not in CANONICAL_ZONES and zone not in self._custom_places:
            return {
                "status": "unknown_zone",
                "zone": zone,
                "available_zones": list(CANONICAL_ZONES.keys()),
            }

        if zone in CANONICAL_ZONES:
            zone_config = CANONICAL_ZONES[zone]
        else:
            zone_config = self._custom_places[zone].to_dict()

        # Build rules from zone config
        rules = []
        rules.append(f"Time behaves as: {zone_config.get('time_behavior', 'unknown')}")
        rules.append(f"Charge modifier: {zone_config.get('charge_modifier', 0):+d}")
        rules.append(f"Access level: {zone_config.get('access_level', 'open')}")
        rules.append(f"Functions: {', '.join(zone_config.get('functions', []))}")
        rules.append(f"Linked organs: {', '.join(zone_config.get('linked_organs', []))}")

        # Add custom rules if any
        if zone in self._zone_rules:
            rules.extend(self._zone_rules[zone])

        return {
            "status": "rules_retrieved",
            "zone": zone,
            "rules": rules,
            "zone_config": zone_config,
            "description": zone_config.get("description", "No description"),
        }

    def _default_location(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Default location status."""
        current_zone = self._current_place or "HERE"

        return {
            "status": "location_status",
            "current_zone": current_zone,
            "in_canonical_zone": current_zone in CANONICAL_ZONES,
            "history_length": len(self._place_history),
            "symbol_processed": invocation.symbol[:50] if invocation.symbol else None,
        }

    def _calculate_time_in_zone(self, zone: str) -> Optional[str]:
        """Calculate time spent in a zone based on history."""
        if not self._place_history:
            return None

        # Find last entry to this zone
        for entry in reversed(self._place_history[:-1]):
            if entry.get("to_place") == zone:
                entry_time = datetime.fromisoformat(entry["timestamp"])
                duration = datetime.now() - entry_time
                return str(duration)

        return None

    def register_custom_place(self, place: RitualPlace) -> Dict[str, Any]:
        """Register a custom place."""
        self._custom_places[place.zone.upper()] = place
        return {
            "status": "registered",
            "zone": place.zone,
            "place": place.to_dict(),
        }

    def add_zone_rule(self, zone: str, rule: str) -> Dict[str, Any]:
        """Add a custom rule to a zone."""
        zone = zone.upper()
        if zone not in self._zone_rules:
            self._zone_rules[zone] = []
        self._zone_rules[zone].append(rule)
        return {
            "status": "rule_added",
            "zone": zone,
            "rule": rule,
            "total_rules": len(self._zone_rules[zone]),
        }

    def get_current_place(self) -> Optional[str]:
        """Get current place."""
        return self._current_place

    def get_place_history(self) -> List[Dict[str, Any]]:
        """Get place transition history."""
        return self._place_history.copy()

    def get_valid_modes(self) -> List[str]:
        return ["enter", "exit", "map", "rules", "default"]

    def get_output_types(self) -> List[str]:
        return ["place_state", "transition_record", "zone_rules", "location_map"]

    def get_state(self) -> Dict[str, Any]:
        """Get current organ state for checkpointing."""
        state = super().get_state()
        state["state"].update({
            "current_place": self._current_place,
            "place_history": self._place_history,
            "custom_places": {k: v.to_dict() for k, v in self._custom_places.items()},
            "zone_rules": self._zone_rules,
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore organ state from checkpoint."""
        super().restore_state(state)
        inner_state = state.get("state", {})
        self._current_place = inner_state.get("current_place", "HERE")
        self._place_history = inner_state.get("place_history", [])
        self._zone_rules = inner_state.get("zone_rules", {})
        # Note: custom_places restoration would require RitualPlace deserialization

    def reset(self) -> None:
        """Reset organ to initial state."""
        super().reset()
        self._current_place = "HERE"
        self._place_history = []
        self._custom_places = {}
        self._zone_rules = {}
