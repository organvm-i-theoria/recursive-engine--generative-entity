"""
RE:GE Time Rules Engine - Temporal recursion engine for bloom cycles and charge-based timing.

Based on: RE-GE_ORG_BODY_17_TIME_RULES.md

The Time Rules Engine governs:
- Bloom cycle seasons and transitions
- Charge-based time modification
- Loop repetition and recurrence tracking
- Temporal decay and renewal patterns
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


class BloomSeason(Enum):
    """Symbolic seasons of the bloom cycle."""
    DORMANT = "dormant"        # Rest phase, minimal activity
    SPROUTING = "sprouting"    # Beginning growth, new ideas
    FLOWERING = "flowering"    # Peak activity, full expression
    SEEDING = "seeding"        # Distribution phase, sharing results


@dataclass
class BloomCycleRecord:
    """
    A bloom cycle managing temporal transformation phases.

    Bloom cycles track the seasonal progression of symbolic
    elements through charge-based timing rules.
    """
    cycle_id: str
    season: BloomSeason
    recurrence: int
    charge_threshold: int
    started_at: datetime
    last_transition: datetime
    transition_count: int = 0
    loop_count: int = 0
    decay_rate: float = 0.05
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.cycle_id:
            self.cycle_id = f"BLOOM_{uuid.uuid4().hex[:8].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize bloom cycle to dictionary."""
        return {
            "cycle_id": self.cycle_id,
            "season": self.season.value,
            "recurrence": self.recurrence,
            "charge_threshold": self.charge_threshold,
            "started_at": self.started_at.isoformat(),
            "last_transition": self.last_transition.isoformat(),
            "transition_count": self.transition_count,
            "loop_count": self.loop_count,
            "decay_rate": self.decay_rate,
            "status": self.status,
            "metadata": self.metadata,
        }


# Seasonal charge thresholds and behaviors
SEASON_CONFIG: Dict[str, Dict[str, Any]] = {
    "DORMANT": {
        "charge_range": (0, 25),
        "next_season": "SPROUTING",
        "transition_threshold": 26,
        "decay_multiplier": 0.5,
        "description": "Rest phase - minimal processing, recovery",
    },
    "SPROUTING": {
        "charge_range": (26, 50),
        "next_season": "FLOWERING",
        "transition_threshold": 51,
        "decay_multiplier": 0.75,
        "description": "Growth phase - ideas emerging, building momentum",
    },
    "FLOWERING": {
        "charge_range": (51, 85),
        "next_season": "SEEDING",
        "transition_threshold": 86,
        "decay_multiplier": 1.0,
        "description": "Peak phase - full expression, maximum activity",
    },
    "SEEDING": {
        "charge_range": (86, 100),
        "next_season": "DORMANT",
        "transition_threshold": 25,  # Drops to dormant when energy depletes
        "decay_multiplier": 1.5,
        "description": "Distribution phase - sharing results, preparing for rest",
    },
}


class TimeRulesEngine(OrganHandler):
    """
    Time Rules Engine - Temporal recursion engine for bloom cycles and timing.

    Modes:
    - cycle: Check/advance bloom cycle
    - schedule: Schedule future bloom
    - decay: Apply time-based decay
    - recurrence: Track loop repetition
    - default: Current temporal state
    """

    @property
    def name(self) -> str:
        return "TIME_RULES"

    @property
    def description(self) -> str:
        return "Temporal recursion engine for bloom cycles and charge-based timing"

    def __init__(self):
        super().__init__()
        self._cycles: Dict[str, BloomCycleRecord] = {}
        self._scheduled_blooms: List[Dict[str, Any]] = []
        self._recurrence_tracker: Dict[str, int] = {}
        self._global_decay_rate: float = 0.05

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Time Rules Engine."""
        mode = invocation.mode.lower()

        if mode == "cycle":
            return self._process_cycle(invocation, patch)
        elif mode == "schedule":
            return self._schedule_bloom(invocation, patch)
        elif mode == "decay":
            return self._apply_decay(invocation, patch)
        elif mode == "recurrence":
            return self._track_recurrence(invocation, patch)
        else:
            return self._default_temporal(invocation, patch)

    def _process_cycle(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Check and potentially advance bloom cycle."""
        symbol_key = self._normalize_key(invocation.symbol)

        # Get or create cycle
        if symbol_key not in self._cycles:
            cycle = self._create_cycle(symbol_key, invocation.charge)
            self._cycles[symbol_key] = cycle
            return {
                "status": "cycle_created",
                "cycle": cycle.to_dict(),
                "symbol": symbol_key,
                "initial_season": cycle.season.value,
            }

        cycle = self._cycles[symbol_key]

        # Check for season transition
        current_season = cycle.season
        transition_result = self._check_season_transition(cycle, invocation.charge)

        if transition_result["transitioned"]:
            return {
                "status": "cycle_advanced",
                "cycle": cycle.to_dict(),
                "previous_season": current_season.value,
                "new_season": cycle.season.value,
                "transition_count": cycle.transition_count,
                "charge": invocation.charge,
            }

        return {
            "status": "cycle_checked",
            "cycle": cycle.to_dict(),
            "current_season": cycle.season.value,
            "charge": invocation.charge,
            "next_threshold": transition_result["next_threshold"],
            "charge_needed": max(0, transition_result["next_threshold"] - invocation.charge),
        }

    def _schedule_bloom(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Schedule a future bloom event."""
        symbol_key = self._normalize_key(invocation.symbol)

        # Parse duration from flags or use default
        duration_days = 7  # Default
        for flag in invocation.flags:
            if flag.startswith("DAYS_"):
                try:
                    duration_days = int(flag.replace("DAYS_", ""))
                except ValueError:
                    pass

        scheduled_at = datetime.now() + timedelta(days=duration_days)

        schedule_entry = {
            "schedule_id": f"SCHED_{uuid.uuid4().hex[:8].upper()}",
            "symbol": symbol_key,
            "scheduled_at": scheduled_at.isoformat(),
            "target_season": self._determine_target_season(invocation.charge),
            "charge_at_schedule": invocation.charge,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }

        self._scheduled_blooms.append(schedule_entry)

        return {
            "status": "bloom_scheduled",
            "schedule": schedule_entry,
            "days_until_bloom": duration_days,
            "target_season": schedule_entry["target_season"],
        }

    def _apply_decay(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Apply time-based decay to charge."""
        symbol_key = self._normalize_key(invocation.symbol)

        # Get cycle if exists
        cycle = self._cycles.get(symbol_key)

        # Calculate decay
        base_decay = self._global_decay_rate
        if cycle:
            season_config = SEASON_CONFIG.get(cycle.season.name, {})
            decay_multiplier = season_config.get("decay_multiplier", 1.0)
            effective_decay = base_decay * decay_multiplier
        else:
            effective_decay = base_decay

        # Calculate decayed charge
        original_charge = invocation.charge
        decay_amount = int(original_charge * effective_decay)
        decayed_charge = max(0, original_charge - decay_amount)

        # Check if decay triggers season change
        season_change = None
        if cycle and decayed_charge < SEASON_CONFIG[cycle.season.name]["charge_range"][0]:
            previous_season = cycle.season
            self._check_season_transition(cycle, decayed_charge)
            if cycle.season != previous_season:
                season_change = {
                    "from": previous_season.value,
                    "to": cycle.season.value,
                }

        return {
            "status": "decay_applied",
            "symbol": symbol_key,
            "original_charge": original_charge,
            "decay_amount": decay_amount,
            "decayed_charge": decayed_charge,
            "decay_rate": effective_decay,
            "season_change": season_change,
            "cycle": cycle.to_dict() if cycle else None,
        }

    def _track_recurrence(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Track loop repetition for symbols."""
        symbol_key = self._normalize_key(invocation.symbol)

        # Increment recurrence count
        if symbol_key not in self._recurrence_tracker:
            self._recurrence_tracker[symbol_key] = 0

        self._recurrence_tracker[symbol_key] += 1
        count = self._recurrence_tracker[symbol_key]

        # Update cycle if exists
        if symbol_key in self._cycles:
            self._cycles[symbol_key].loop_count = count
            self._cycles[symbol_key].recurrence = count

        # Determine recurrence type
        recurrence_type = self._classify_recurrence(count)

        return {
            "status": "recurrence_tracked",
            "symbol": symbol_key,
            "recurrence_count": count,
            "recurrence_type": recurrence_type,
            "charge_boost": self._calculate_recurrence_boost(count),
            "is_pattern": count >= 3,
        }

    def _default_temporal(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Return current temporal state."""
        symbol_key = self._normalize_key(invocation.symbol) if invocation.symbol else None

        # Get current season based on charge
        current_season = self._determine_season_from_charge(invocation.charge)

        result = {
            "status": "temporal_state",
            "current_season": current_season,
            "charge": invocation.charge,
            "active_cycles": len(self._cycles),
            "scheduled_blooms": len(self._scheduled_blooms),
            "global_decay_rate": self._global_decay_rate,
        }

        if symbol_key and symbol_key in self._cycles:
            result["symbol_cycle"] = self._cycles[symbol_key].to_dict()
        if symbol_key and symbol_key in self._recurrence_tracker:
            result["symbol_recurrence"] = self._recurrence_tracker[symbol_key]

        return result

    def _create_cycle(self, symbol: str, charge: int) -> BloomCycleRecord:
        """Create a new bloom cycle."""
        season = self._determine_season_from_charge(charge)
        now = datetime.now()

        return BloomCycleRecord(
            cycle_id="",  # Will be auto-generated
            season=BloomSeason(season.lower()),
            recurrence=1,
            charge_threshold=charge,
            started_at=now,
            last_transition=now,
        )

    def _check_season_transition(self, cycle: BloomCycleRecord, charge: int) -> Dict[str, Any]:
        """Check if charge triggers a season transition."""
        current_config = SEASON_CONFIG.get(cycle.season.name, {})
        charge_range = current_config.get("charge_range", (0, 100))
        next_threshold = current_config.get("transition_threshold", 100)

        # Check for forward transition (charge increase)
        if charge >= next_threshold:
            next_season_name = current_config.get("next_season", "DORMANT")
            cycle.season = BloomSeason(next_season_name.lower())
            cycle.transition_count += 1
            cycle.last_transition = datetime.now()
            return {"transitioned": True, "next_threshold": next_threshold}

        # Check for backward transition (charge decrease below range)
        if charge < charge_range[0]:
            # Find appropriate season for current charge
            new_season = self._determine_season_from_charge(charge)
            if new_season.lower() != cycle.season.value:
                cycle.season = BloomSeason(new_season.lower())
                cycle.transition_count += 1
                cycle.last_transition = datetime.now()
                return {"transitioned": True, "next_threshold": next_threshold}

        return {"transitioned": False, "next_threshold": next_threshold}

    def _determine_season_from_charge(self, charge: int) -> str:
        """Determine appropriate season based on charge level."""
        if charge <= 25:
            return "DORMANT"
        elif charge <= 50:
            return "SPROUTING"
        elif charge <= 85:
            return "FLOWERING"
        else:
            return "SEEDING"

    def _determine_target_season(self, charge: int) -> str:
        """Determine target season for scheduling."""
        # Target one season ahead of current
        current = self._determine_season_from_charge(charge)
        next_seasons = {
            "DORMANT": "SPROUTING",
            "SPROUTING": "FLOWERING",
            "FLOWERING": "SEEDING",
            "SEEDING": "DORMANT",
        }
        return next_seasons.get(current, "FLOWERING")

    def _classify_recurrence(self, count: int) -> str:
        """Classify recurrence type based on count."""
        if count == 1:
            return "singular"
        elif count == 2:
            return "echo"
        elif count <= 5:
            return "pattern"
        elif count <= 10:
            return "ritual"
        else:
            return "obsession"

    def _calculate_recurrence_boost(self, count: int) -> int:
        """Calculate charge boost from recurrence."""
        if count <= 1:
            return 0
        elif count <= 3:
            return 5
        elif count <= 7:
            return 10
        else:
            return 15

    def _normalize_key(self, symbol: str) -> str:
        """Normalize symbol to key for tracking."""
        if not symbol:
            return "UNNAMED"
        # Take first 50 chars, uppercase, replace spaces
        return symbol[:50].upper().replace(" ", "_")

    def get_cycle(self, symbol: str) -> Optional[BloomCycleRecord]:
        """Get cycle for a symbol."""
        return self._cycles.get(self._normalize_key(symbol))

    def get_scheduled_blooms(self) -> List[Dict[str, Any]]:
        """Get all scheduled blooms."""
        return self._scheduled_blooms.copy()

    def get_recurrence_count(self, symbol: str) -> int:
        """Get recurrence count for a symbol."""
        return self._recurrence_tracker.get(self._normalize_key(symbol), 0)

    def set_global_decay_rate(self, rate: float) -> None:
        """Set global decay rate (0.0 - 1.0)."""
        self._global_decay_rate = max(0.0, min(1.0, rate))

    def get_valid_modes(self) -> List[str]:
        return ["cycle", "schedule", "decay", "recurrence", "default"]

    def get_output_types(self) -> List[str]:
        return ["cycle_state", "schedule_entry", "decay_result", "recurrence_record", "temporal_state"]

    def get_state(self) -> Dict[str, Any]:
        """Get current organ state for checkpointing."""
        state = super().get_state()
        state["state"].update({
            "cycles": {k: v.to_dict() for k, v in self._cycles.items()},
            "scheduled_blooms": self._scheduled_blooms,
            "recurrence_tracker": self._recurrence_tracker,
            "global_decay_rate": self._global_decay_rate,
        })
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore organ state from checkpoint."""
        super().restore_state(state)
        inner_state = state.get("state", {})
        self._scheduled_blooms = inner_state.get("scheduled_blooms", [])
        self._recurrence_tracker = inner_state.get("recurrence_tracker", {})
        self._global_decay_rate = inner_state.get("global_decay_rate", 0.05)
        # Note: cycles restoration would require BloomCycleRecord deserialization

    def reset(self) -> None:
        """Reset organ to initial state."""
        super().reset()
        self._cycles = {}
        self._scheduled_blooms = []
        self._recurrence_tracker = {}
        self._global_decay_rate = 0.05
